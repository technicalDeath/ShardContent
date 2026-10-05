using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Tinker vendors sell Backpack Wards for gold, so a character who has used up the free starter Ward can get another
/// (docs/BACKPACK-WARD-DESIGN.md Section 1). The price is a ceiling for the later crafted Ward to undercut, and the
/// shelf is deep enough that clearing it costs far more gold than a launch-week character has: stock vendors double a
/// shelf that sells out and halve one that sells under half, so the engine already pushes back on hoarding. Vendors never
/// buy a Ward back, because no stock sell list names it. Follows the theft protection flag and is configured by
/// <c>wardVendor</c> in shard-rules.json.
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
        BaseVendor.ItemsBought += OnItemsBought;
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
}
