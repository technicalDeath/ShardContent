using System.Reflection;
using System.Text.Json;
using Server;
using Server.Engines.Craft;
using Server.Mobiles;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The owner (2026-10-17) chose an audit over marking vendor-bought items: no item may be bought from one vendor and sold to another for more than it
/// cost. Every stock shop list (SBInfo) is read with the shard's crafted-goods pricing applied, plus the extra buyers from the source config; a vendor
/// that pays more than another charges fails the build. Paying exactly the price (arrows, beeswax) is a wash, not a loop.
/// </summary>
public class VendorResaleAuditTests
{
    /// <summary>Shop lists of vendors that never spawn in this world (none in the generated spawn data): their stock quirks cannot be used here.
    /// SBStoneCrafter pays 24 for the Blacksmith's 22-gold black staff; SBHolyMage sells first-circle scrolls for 12.</summary>
    private static readonly HashSet<string> NotInThisWorld = ["SBStoneCrafter", "SBHolyMage"];

    [Fact]
    public void NoItemCanBeBoughtFromOneVendorAndSoldToAnotherForMore()
    {
        var previous = Core.Expansion;

        try
        {
            Core.Expansion = Expansion.UOR;
            DefAlchemy.Initialize();
            DefBlacksmithy.Initialize();
            DefTailoring.Initialize();
            DefTinkering.Initialize();
            DefCarpentry.Initialize();
            DefBowFletching.Initialize();
            DefInscription.Initialize();

            var costs = CraftedGoodsPricing.BuildCosts();
            int Cost(Type t) => costs.TryGetValue(t, out var c) ? c : 0;

            var minCharge = new Dictionary<Type, (int Price, string Where)>();
            var maxPay = new Dictionary<Type, (int Price, string Where)>();

            void Charge(Type t, int price, string where)
            {
                if (!minCharge.TryGetValue(t, out var known) || price < known.Price)
                {
                    minCharge[t] = (price, where);
                }
            }

            void Pay(Type t, int price, string where)
            {
                if (!maxPay.TryGetValue(t, out var known) || price > known.Price)
                {
                    maxPay[t] = (price, where);
                }
            }

            var priceField = typeof(GenericBuyInfo).GetField("m_Price", BindingFlags.Instance | BindingFlags.NonPublic)!;
            var tableField = typeof(GenericSellInfo).GetField("m_Table", BindingFlags.Instance | BindingFlags.NonPublic)!;
            var shops = 0;

            foreach (var type in typeof(SBInfo).Assembly.GetTypes())
            {
                if (!typeof(SBInfo).IsAssignableFrom(type) || type.IsAbstract || type.GetConstructor(Type.EmptyTypes) is null ||
                    NotInThisWorld.Contains(type.Name))
                {
                    continue;
                }

                SBInfo shop;

                try
                {
                    shop = (SBInfo)Activator.CreateInstance(type)!;
                }
                catch
                {
                    continue;
                }

                shops++;

                foreach (var buy in shop.BuyInfo)
                {
                    if (buy.Type is { } t)
                    {
                        Charge(t, CraftedGoodsPricing.VendorCharges((int)priceField.GetValue(buy)!, Cost(t)), type.Name);
                    }
                }

                if (shop.SellInfo is GenericSellInfo sell)
                {
                    foreach (var (t, price) in (Dictionary<Type, int>)tableField.GetValue(sell)!)
                    {
                        Pay(t, CraftedGoodsPricing.VendorPays(price, Cost(t)), type.Name);
                    }
                }
            }

            var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var rules = doc.RootElement.GetProperty("extraVendorBuyers").Deserialize<ExtraVendorBuyerRules>()!;

            foreach (var (vendor, list) in ExtraVendorBuyers.Build(rules))
            {
                foreach (var (t, price) in list)
                {
                    Pay(t, price, vendor + " (extra)");
                }
            }

            // the extra shelves from data (extraVendorStock: the Mage's Recall and Mark scrolls) charge through the same buy-price hook
            var stock = doc.RootElement.GetProperty("extraVendorStock").Deserialize<List<ExtraVendorStockEntry>>()!;
            foreach (var e in stock)
            {
                if (ExtraVendorStock.ItemType(e.Item) is { } t)
                {
                    Charge(t, CraftedGoodsPricing.VendorCharges(e.Price, Cost(t)), string.Join("/", e.Vendors) + " (extra stock)");
                }
            }

            Assert.True(shops > 50, $"only {shops} shop lists loaded");

            var loops = maxPay
                .Where(p => minCharge.TryGetValue(p.Key, out var c) && p.Value.Price > c.Price)
                .Select(p => $"{p.Key.Name}: {minCharge[p.Key].Where} sells for {minCharge[p.Key].Price}, {p.Value.Where} pays {p.Value.Price}")
                .OrderBy(s => s)
                .ToList();

            Assert.True(loops.Count == 0, "Buy-to-resell loops: " + string.Join("; ", loops));
        }
        finally
        {
            Core.Expansion = previous;
        }
    }
}
