using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Tinker vendors sell Backpack Wards for gold, so a character who has used up the free starter Ward can get another
/// (docs/BACKPACK-WARD-DESIGN.md Section 1). The price is a ceiling for the crafted Ward to undercut, and the
/// shelf is deep enough that clearing it costs far more gold than a launch-week character has: stock vendors double a
/// shelf that sells out and halve one that sells under half, so the engine already pushes back on hoarding.
/// Tinkers also buy an unused Ward back for a small fixed price, a little above what its ingots cost, so a crafter who
/// overestimated the player market still comes out slightly ahead. They do not re-list what they buy: stock vendors
/// resell at 1.9 times what they paid, which would put a cheap Ward back on the shelf and undercut crafters again.
/// Follows the theft protection flag and is configured by <c>wardVendor</c> in shard-rules.json.
/// </summary>
public static class BackpackWardVendor
{
    /// <summary>The engine's own ceiling for a vendor shelf (<c>GenericBuyInfo.OnRestock</c>).</summary>
    public const int MaxStock = 999;

    public const int MaxPrice = 1_000_000;

    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        BaseVendor.BuyInfoLoaded += OnBuyInfoLoaded;
        BaseVendor.SellInfoLoaded += OnSellInfoLoaded;
        BaseVendor.ItemsBought += OnItemsBought;
        BaseVendor.ItemsSold += OnItemsSold;
    }

    public static void Validate(WardVendorRules rules, List<string> errors)
    {
        if (rules.Price < 1 || rules.Price > MaxPrice)
        {
            errors.Add($"wardVendor.price must be between 1 and {MaxPrice}, but was {rules.Price}.");
        }

        if (rules.StockPerVendor < 0 || rules.StockPerVendor > MaxStock)
        {
            errors.Add($"wardVendor.stockPerVendor must be between 0 and {MaxStock}, but was {rules.StockPerVendor}.");
        }

        if (rules.BuyBackPrice < 0 || rules.BuyBackPrice > MaxPrice)
        {
            errors.Add($"wardVendor.buyBackPrice must be between 0 and {MaxPrice}, but was {rules.BuyBackPrice}.");
        }
        else if (rules.BuyBackPrice > 0 && rules.BuyBackPrice >= rules.Price)
        {
            // A vendor that buys at or above what it sells for would pay out gold for nothing.
            errors.Add(
                $"wardVendor.buyBackPrice ({rules.BuyBackPrice}) must be below wardVendor.price ({rules.Price})."
            );
        }
    }

    /// <summary>Only plain Tinkers: the Mondain's Legacy quest tinkers derive from <see cref="Tinker"/> and are not shops.</summary>
    public static bool Sells(Type vendorType) => vendorType == typeof(Tinker);

    /// <summary>The shelf entry for the Ward, or null while the Ward is off sale.</summary>
    public static GenericBuyInfo? CreateEntry(WardVendorRules rules, bool theftProtectionEnabled) =>
        theftProtectionEnabled && rules.StockPerVendor > 0
            ? new GenericBuyInfo(
                "backpack ward",
                typeof(BackpackWard),
                rules.Price,
                rules.StockPerVendor,
                BackpackWard.DefaultItemId,
                0
            )
            : null;

    /// <summary>What a Tinker pays for an unused Ward, or null while the buy-back is off.</summary>
    public static IShopSellInfo? CreateBuyBack(WardVendorRules rules, bool theftProtectionEnabled) =>
        theftProtectionEnabled && rules.BuyBackPrice > 0 ? new WardBuyBackSellInfo(rules.BuyBackPrice) : null;

    private static void OnBuyInfoLoaded(BaseVendor vendor, List<IBuyItemInfo> buyInfo)
    {
        var rules = ShardRulesConfiguration.Settings?.WardVendor;

        if (rules is null || !Sells(vendor.GetType()))
        {
            return;
        }

        var entry = CreateEntry(rules, TheftProtectionService.Enabled);

        if (entry is not null)
        {
            buyInfo.Add(entry);
        }
    }

    private static void OnSellInfoLoaded(BaseVendor vendor, List<IShopSellInfo> sellInfo)
    {
        var rules = ShardRulesConfiguration.Settings?.WardVendor;

        if (rules is null || !Sells(vendor.GetType()))
        {
            return;
        }

        var buyBack = CreateBuyBack(rules, TheftProtectionService.Enabled);

        if (buyBack is not null)
        {
            sellInfo.Add(buyBack);
        }
    }

    private static void OnItemsBought(BaseVendor vendor, Mobile buyer, GenericBuyInfo info, int amount)
    {
        if (info.Type != typeof(BackpackWard))
        {
            return;
        }

        ShardAuditLog.Record(
            "theft",
            "ward-bought",
            buyer,
            details: $"vendor={vendor.Serial.Value}; count={amount}; unitPrice={info.Price}"
        );
    }

    private static void OnItemsSold(BaseVendor vendor, Mobile seller, Item item, int amount, int gold)
    {
        if (item is not BackpackWard)
        {
            return;
        }

        ShardAuditLog.Record(
            "theft",
            "ward-sold",
            seller,
            details: $"vendor={vendor.Serial.Value}; count={amount}; paid={gold}"
        );
    }
}

/// <summary>
/// What a Tinker pays for a Backpack Ward. Only an Unprimed regular Ward qualifies (the starter Ward and one that is
/// tracking thieves are bound to their character), and the vendor never re-lists it, so a bought-back Ward is gone.
/// </summary>
public sealed class WardBuyBackSellInfo(int price) : IShopSellInfo
{
    private static readonly Type[] WardTypes = [typeof(BackpackWard)];

    public int Price { get; } = price;

    public Type[] Types => WardTypes;

    public string GetNameFor(Item item) => "backpack ward";

    public int GetSellPriceFor(Item item) => Price;

    // Never asked for: the Ward is not resellable, so it is never on the vendor's shelf.
    public int GetBuyPriceFor(Item item) => Price;

    public bool IsSellable(Item item) =>
        item is BackpackWard { IsStarterIssued: false } ward &&
        !ward.State.IsTracking &&
        !item.Nontransferable &&
        item.LootType == LootType.Regular;

    public bool IsResellable(Item item) => false;
}
