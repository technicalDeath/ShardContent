using System.Text.Json.Serialization;
using Server;
using Server.Engines.Craft;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Buyers for goods no vendor buys (docs/Bot-Farm-QoL-Findings.md, the watcher's vendor-wont-buy list), behind <c>featureFlags.extraVendorBuyers</c>.
/// The owner (2026-10-17) chose "Crafted goods, all" and "Loot: bone, feathers, big fish". When a vendor's buy list loads, each craft's shop also buys
/// every item of that craft it did not already buy, at crafted-goods pricing (material cost plus 25 percent; tools and consumables stay out), and the
/// configured loot buyers buy their items at the configured prices. Items a vendor already buys keep their stock price.
/// </summary>
public static class ExtraVendorBuyers
{
    /// <summary>Material prices beyond crafted-goods pricing's, for alchemy and inscription (stock Alchemist, Mage and Scribe prices).</summary>
    public static readonly IReadOnlyDictionary<Type, int> ExtraMaterialPrices = new Dictionary<Type, int>
    {
        [typeof(Bottle)] = 5,
        [typeof(BlankScroll)] = 5,
        [typeof(BlackPearl)] = 5,
        [typeof(Bloodmoss)] = 5,
        [typeof(Garlic)] = 3,
        [typeof(Ginseng)] = 3,
        [typeof(MandrakeRoot)] = 3,
        [typeof(Nightshade)] = 3,
        [typeof(SpidersSilk)] = 3,
        [typeof(SulfurousAsh)] = 3,
    };

    private static bool _configured;
    private static Dictionary<string, List<(Type Type, int Price)>>? _byVendor;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.ExtraVendorBuyers == true;

    public static ExtraVendorBuyerRules Rules => ShardRulesConfiguration.Settings?.ExtraVendorBuyers ?? new ExtraVendorBuyerRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        BaseVendor.SellInfoLoaded += OnSellInfoLoaded;
    }

    public static CraftSystem? SystemNamed(string name) =>
        name.ToLowerInvariant() switch
        {
            "alchemy" => DefAlchemy.CraftSystem,
            "blacksmithy" => DefBlacksmithy.CraftSystem,
            "bowcraft" => DefBowFletching.CraftSystem,
            "carpentry" => DefCarpentry.CraftSystem,
            "inscription" => DefInscription.CraftSystem,
            "tailoring" => DefTailoring.CraftSystem,
            "tinkering" => DefTinkering.CraftSystem,
            _ => null,
        };

    /// <summary>What a shop pays for a crafted item it did not buy before: the crafted-goods floor, and at least 1 gold.</summary>
    public static int CraftedPrice(int materialCost) => Math.Max(1, CraftedGoodsPricing.PayFloor(materialCost));

    // Vendors load with the world, before the craft systems exist (they are built in Initialize), so the list is filled on first use.
    private static void OnSellInfoLoaded(BaseVendor vendor, List<IShopSellInfo> sellInfo)
    {
        if (Enabled)
        {
            sellInfo.Add(new LazySellInfo(vendor.GetType().Name, sellInfo));
        }
    }

    private static GenericSellInfo BuildFor(string vendorType, List<IShopSellInfo> sellInfo, LazySellInfo self)
    {
        var added = new GenericSellInfo();

        if (CraftSystemsReady(Rules))
        {
            _byVendor ??= Build(Rules);
        }

        var table = _byVendor ?? Build(Rules);

        if (table.TryGetValue(vendorType, out var extras))
        {
            foreach (var (type, price) in extras)
            {
                if (!AlreadyBuys(sellInfo, type, self))
                {
                    added.Add(type, price);
                }
            }
        }

        return added;
    }

    private static bool CraftSystemsReady(ExtraVendorBuyerRules rules)
    {
        foreach (var craft in rules.Crafted)
        {
            if (SystemNamed(craft.CraftSystem)?.CraftItems is not { Count: > 0 })
            {
                return false;
            }
        }

        return true;
    }

    /// <summary>The extra buys for one vendor, worked out the first time a player sells to it.</summary>
    private sealed class LazySellInfo : IShopSellInfo
    {
        private readonly string _vendorType;
        private readonly List<IShopSellInfo> _others;
        private GenericSellInfo? _inner;

        public LazySellInfo(string vendorType, List<IShopSellInfo> others)
        {
            _vendorType = vendorType;
            _others = others;
        }

        private GenericSellInfo Inner => _inner ??= BuildFor(_vendorType, _others, this);

        public Type[] Types => Inner.Types;

        public string GetNameFor(Item item) => Inner.GetNameFor(item);

        public int GetSellPriceFor(Item item) => Inner.GetSellPriceFor(item);

        public int GetBuyPriceFor(Item item) => Inner.GetBuyPriceFor(item);

        public bool IsSellable(Item item) => Inner.IsSellable(item);

        public bool IsResellable(Item item) => Inner.IsResellable(item);
    }

    private static bool AlreadyBuys(List<IShopSellInfo> sellInfo, Type type, IShopSellInfo self)
    {
        foreach (var info in sellInfo)
        {
            if (info != self && Array.IndexOf(info.Types, type) >= 0)
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>Vendor class name to what it buys beyond stock, from the loaded craft recipes and the config (the buy-to-resell audit test uses it).</summary>
    public static Dictionary<string, List<(Type, int)>> Build(ExtraVendorBuyerRules rules)
    {
        var prices = new Dictionary<Type, int>(ExtraMaterialPrices);

        foreach (var (type, price) in CraftedGoodsPricing.MaterialPrices)
        {
            prices[type] = price;
        }

        var result = new Dictionary<string, List<(Type, int)>>();
        var boughtSomewhere = StockBoughtTypes();

        void AddFor(IEnumerable<string> vendors, Type type, int price)
        {
            foreach (var vendor in vendors)
            {
                if (!result.TryGetValue(vendor, out var list))
                {
                    result[vendor] = list = [];
                }

                if (!list.Exists(e => e.Item1 == type))
                {
                    list.Add((type, price));
                }
            }
        }

        foreach (var craft in rules.Crafted)
        {
            if (SystemNamed(craft.CraftSystem)?.CraftItems is not { } items)
            {
                continue;
            }

            foreach (var item in items)
            {
                // a material made from another (boards, cloth, shafts) is a conversion, tools and consumables stay at stock, and an item some stock
                // vendor already buys has its market (a second buyer at crafted prices could pay more than another shop charges: spell scrolls)
                if (item?.ItemType is not { IsAbstract: false } type || prices.ContainsKey(type) || CraftedGoodsPricing.IsKeptAtStock(type) ||
                    boughtSomewhere.Contains(type))
                {
                    continue;
                }

                var cost = CraftedGoodsPricing.MaterialCost(item.Resources.Select(r => (r.ItemType, r.Amount)), prices);
                AddFor(craft.Vendors, type, CraftedPrice(cost));
            }
        }

        foreach (var loot in rules.Loot)
        {
            if (ItemType(loot.Item) is { } type)
            {
                AddFor(loot.Vendors, type, loot.Price);
            }
        }

        return result;
    }

    /// <summary>Every item type some stock shop list (SBInfo) buys, wherever that vendor stands.</summary>
    public static HashSet<Type> StockBoughtTypes()
    {
        var bought = new HashSet<Type>();

        foreach (var type in typeof(SBInfo).Assembly.GetTypes())
        {
            if (!typeof(SBInfo).IsAssignableFrom(type) || type.IsAbstract || type.GetConstructor(Type.EmptyTypes) is null)
            {
                continue;
            }

            try
            {
                if (Activator.CreateInstance(type) is SBInfo { SellInfo: { } sell })
                {
                    bought.UnionWith(sell.Types);
                }
            }
            catch (Exception)
            {
                // a shop list that cannot be built outside a vendor buys nothing here
            }
        }

        return bought;
    }

    // every item type lives in the content assembly beside the vendors; looked up there so the audit test needs no running server
    private static Type? ItemType(string name)
    {
        foreach (var type in typeof(BaseVendor).Assembly.GetTypes())
        {
            if (type.Name == name && typeof(Item).IsAssignableFrom(type))
            {
                return type;
            }
        }

        return null;
    }

    public static void Validate(ExtraVendorBuyerRules rules, List<string> errors)
    {
        foreach (var craft in rules.Crafted)
        {
            if (craft.CraftSystem.ToLowerInvariant() is not ("alchemy" or "blacksmithy" or "bowcraft" or "carpentry" or "inscription" or "tailoring" or "tinkering"))
            {
                errors.Add($"extraVendorBuyers.crafted: unknown craft system '{craft.CraftSystem}'.");
            }

            if (craft.Vendors.Count == 0)
            {
                errors.Add($"extraVendorBuyers.crafted '{craft.CraftSystem}' names no vendors.");
            }
        }

        foreach (var loot in rules.Loot)
        {
            if (string.IsNullOrWhiteSpace(loot.Item) || loot.Price is < 1 or > 10000 || loot.Vendors.Count == 0)
            {
                errors.Add($"extraVendorBuyers.loot '{loot.Item}' needs an item, a price of 1 to 10000 and at least one vendor.");
            }
        }
    }
}

public sealed class ExtraVendorBuyerRules
{
    [JsonPropertyName("crafted")]
    public List<ExtraCraftedBuyer> Crafted { get; set; } = [];

    [JsonPropertyName("loot")]
    public List<ExtraLootBuyer> Loot { get; set; } = [];
}

public sealed class ExtraCraftedBuyer
{
    /// <summary>alchemy, blacksmithy, bowcraft, carpentry, inscription, tailoring or tinkering.</summary>
    [JsonPropertyName("craftSystem")]
    public string CraftSystem { get; set; } = "";

    /// <summary>Vendor class names (Alchemist, Carpenter, TinkerGuildmaster...).</summary>
    [JsonPropertyName("vendors")]
    public List<string> Vendors { get; set; } = [];
}

public sealed class ExtraLootBuyer
{
    /// <summary>The item's type name (BoneChest, Feather, BigFish...).</summary>
    [JsonPropertyName("item")]
    public string Item { get; set; } = "";

    [JsonPropertyName("price")]
    public int Price { get; set; }

    [JsonPropertyName("vendors")]
    public List<string> Vendors { get; set; } = [];
}
