using System;
using System.Collections.Generic;
using System.Linq;
using Server;
using Server.Commands;
using Server.Engines.Craft;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Crafted-goods pricing, behind <c>featureFlags.craftedGoodsPricing</c> (owner, 2026-10-14: "tune the shard's vendor buy prices and sell prices so that crafters
/// can make a small profit on crafted items"; docs/Crafted-Goods-Pricing.md). A vendor that buys a crafted item pays at least its material cost times
/// <see cref="Margin"/>, and a vendor that sells one charges at least <see cref="Spread"/> times that, so buying from a vendor to sell back never pays.
/// A vendor's resale of goods players sold it already costs 1.9 times what it paid (stock rule). The material cost comes from the server's own craft
/// recipes (blacksmithing, tailoring, tinkering, carpentry, bowcraft) priced at what vendors charge for the material (<see cref="MaterialPrices"/>), and,
/// since the owner's "Crafted pricing for scrolls" (2026-10-18), the spell scrolls of inscription, priced from the blank scroll and the spell's reagents
/// (<see cref="ExtraVendorBuyers.ExtraMaterialPrices"/>); a vendor's own scroll shelf then charges at least 1.5 times what it pays, so no loop opens.
/// Prices are only ever raised to the floors, never lowered, and an item no vendor buys stays unbuyable. Engine hooks: <c>GenericSellInfo.SellPriceAdjust</c>
/// and <c>GenericBuyInfo.BuyPriceAdjust</c>; the flag is read on every price, so switching it takes effect at once.
/// </summary>
public static class CraftedGoodsPricing
{
    /// <summary>What a vendor pays over the material cost of a successful craft: 25 percent.</summary>
    public const double Margin = 1.25;

    /// <summary>A vendor's own price for a crafted item, over what it pays for one.</summary>
    public const double Spread = 1.5;

    /// <summary>What a material costs at the shard's vendors (their stock prices: ModernUO SBInfo lists).</summary>
    public static readonly IReadOnlyDictionary<Type, int> MaterialPrices = new Dictionary<Type, int>
    {
        [typeof(IronIngot)] = 5,      // Blacksmith, Tinker: 5 (some 6)
        [typeof(Cloth)] = 2,          // Tailor: cut cloth 2
        [typeof(UncutCloth)] = 2,     // Tailor: cloth 2 to 3
        [typeof(BoltOfCloth)] = 100,  // Tailor: 100 for 50 cloth
        [typeof(Leather)] = 6,        // Tanner / Leatherworker: 6
        [typeof(Hides)] = 4,          // Tanner: 3 to 4
        [typeof(Board)] = 3,          // Carpenter, Tinker: 3
        [typeof(Log)] = 2,            // not stocked; priced under a board
        [typeof(Feather)] = 2,        // Bowyer: 2
        [typeof(Shaft)] = 3            // Bowyer: 3
    };

    /// <summary>
    /// Crafted, but kept at stock prices: the tools a crafter wears out and must replace (raising them would eat the crafter's profit and hurt new players), and the
    /// consumables everyone buys by the hundred (arrows, bolts, bandages, kindling). Pay and charge both stay stock, so there is nothing to exploit.
    /// </summary>
    public static readonly Type[] KeptAtStock =
    {
        typeof(BaseTool), typeof(BaseHarvestTool), typeof(Pickaxe), typeof(Hatchet), typeof(Scissors), typeof(Arrow), typeof(Bolt), typeof(Bandage), typeof(Kindling)
    };

    public static bool IsKeptAtStock(Type type)
    {
        foreach (var kept in KeptAtStock)
        {
            if (kept.IsAssignableFrom(type))
            {
                return true;
            }
        }

        return false;
    }

    private static bool _configured;
    private static Dictionary<Type, int> _costs;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CraftedGoodsPricing == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        GenericSellInfo.SellPriceAdjust = (type, price) => Enabled ? VendorPays(price, CostOf(type)) : price;
        // the one buy-price hook carries both shard price rules: crafted goods (behind its flag) and the house prices (data only, HousePricing)
        GenericBuyInfo.BuyPriceAdjust = (type, price) => HousePricing.Adjust(type, Enabled ? VendorCharges(price, CostOf(type)) : price);
        CommandSystem.Register("CraftPricingStatus", AccessLevel.GameMaster, OnStatus);
    }

    // ---- the arithmetic (pure, tested)

    /// <summary>The material cost of one craft: each resource's amount at its vendor price; a resource with no known price adds nothing.</summary>
    public static int MaterialCost(IEnumerable<(Type Type, int Amount)> resources, IReadOnlyDictionary<Type, int> prices)
    {
        var cost = 0;
        foreach (var (type, amount) in resources)
        {
            if (type != null && prices.TryGetValue(type, out var each))
            {
                cost += each * Math.Max(0, amount);
            }
        }

        return cost;
    }

    /// <summary>The least a vendor pays for an item whose materials cost <paramref name="materialCost"/>; 0 when the cost is unknown.</summary>
    public static int PayFloor(int materialCost) => materialCost <= 0 ? 0 : (int)Math.Ceiling(materialCost * Margin);

    /// <summary>What a vendor pays: its stock price, raised to the floor if that is lower.</summary>
    public static int VendorPays(int stockPrice, int materialCost) => Math.Max(stockPrice, PayFloor(materialCost));

    /// <summary>What a vendor charges for its own stock: its stock price, raised to <see cref="Spread"/> times what it would pay if that is lower.</summary>
    public static int VendorCharges(int stockPrice, int materialCost) =>
        materialCost <= 0 ? stockPrice : Math.Max(stockPrice, (int)Math.Ceiling(PayFloor(materialCost) * Spread));

    // ---- the cost table, from the craft recipes

    public static int CostOf(Type type)
    {
        var costs = _costs ??= BuildCosts();
        return type != null && costs.TryGetValue(type, out var c) ? c : 0;
    }

    /// <summary>The material cost of every priced crafted item, from the loaded craft recipes (the buy-to-resell audit test uses it).</summary>
    public static Dictionary<Type, int> BuildCosts()
    {
        var costs = new Dictionary<Type, int>();
        var prices = new Dictionary<Type, int>(ExtraVendorBuyers.ExtraMaterialPrices);
        foreach (var (type, price) in MaterialPrices)
        {
            prices[type] = price;
        }

        foreach (var system in new[] { DefBlacksmithy.CraftSystem, DefTailoring.CraftSystem, DefTinkering.CraftSystem, DefCarpentry.CraftSystem, DefBowFletching.CraftSystem, DefInscription.CraftSystem })
        {
            if (system?.CraftItems == null)
            {
                continue;
            }

            foreach (var item in system.CraftItems)
            {
                // a material made from another (boards from logs, cloth cut from a bolt) is a conversion, not a product; of inscription only the spell scrolls
                // are priced (runebooks and books keep their stock prices)
                if (item?.ItemType == null || prices.ContainsKey(item.ItemType) || IsKeptAtStock(item.ItemType) ||
                    system == DefInscription.CraftSystem && !typeof(SpellScroll).IsAssignableFrom(item.ItemType))
                {
                    continue;
                }

                var cost = MaterialCost(item.Resources.Select(r => (r.ItemType, r.Amount)), prices);
                if (cost > 0 && (!costs.TryGetValue(item.ItemType, out var known) || cost < known))
                {
                    costs[item.ItemType] = cost;
                }
            }
        }

        return costs;
    }

    // ---- staff diagnostics

    [Usage("CraftPricingStatus [item type name]")]
    [Description("Crafted-goods pricing: whether it is on, how many crafted items have a cost, and the floors for one item type.")]
    private static void OnStatus(CommandEventArgs e)
    {
        var costs = _costs ??= BuildCosts();
        e.Mobile.SendMessage($"Crafted-goods pricing is {(Enabled ? "ON" : "off")}: {costs.Count} crafted item types priced (margin {Margin:0.00}, spread {Spread:0.0}).");
        if (e.Length > 0)
        {
            var name = e.GetString(0);
            var entry = costs.FirstOrDefault(kv => kv.Key.Name.Equals(name, StringComparison.OrdinalIgnoreCase));
            if (entry.Key == null)
            {
                e.Mobile.SendMessage($"No crafted item type named {name}.");
                return;
            }

            e.Mobile.SendMessage($"{entry.Key.Name}: materials {entry.Value} gold; a vendor pays at least {PayFloor(entry.Value)} and sells at least {VendorCharges(0, entry.Value)}.");
        }
    }
}
