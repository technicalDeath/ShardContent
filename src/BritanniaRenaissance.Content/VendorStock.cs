using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Server;
using Server.Commands;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Settings for <see cref="VendorStock"/> (<c>vendorStock</c> in shard-rules.json).</summary>
public sealed class VendorStockRules
{
    /// <summary>Minutes between a vendor's restocks; 0 keeps the stock hour.</summary>
    [JsonPropertyName("restockMinutes")]
    public int RestockMinutes { get; set; }

    /// <summary>Item type name (as <c>LesserCurePotion</c>) to the factor its vendor lines start with (the stock list's amount times this); missing types keep stock.</summary>
    [JsonPropertyName("stockMultipliers")]
    public Dictionary<string, int> StockMultipliers { get; set; } = new();
}

/// <summary>
/// The shard's vendor stock (owner, 2026-11-02: "Increase the number of potions at shops, and any other provisions preventing a bot from going to
/// dungeons, and have shops restock every 30 minutes instead of 60"). Every vendor restocks after <see cref="VendorStockRules.RestockMinutes"/>, and each
/// listed type's lines start at its multiplier times the stock list's amount and never halve below that (stock lines still double when they sell out).
/// The dungeon kit is Heal, Cure and Refresh potions and bandages, and an archer's trip needs arrows or bolts. Engine hooks:
/// <c>BaseVendor.RestockDelayOverride</c> and <c>GenericBuyInfo.StockAmountAdjust</c>; vendors build their lines at world load, so a change takes
/// effect at the next server start.
/// </summary>
public static class VendorStock
{
    private static bool _configured;

    public static VendorStockRules Rules => ShardRulesConfiguration.Settings?.VendorStock ?? new VendorStockRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        var minutes = Rules.RestockMinutes;
        BaseVendor.RestockDelayOverride = minutes > 0 ? TimeSpan.FromMinutes(minutes) : null;
        GenericBuyInfo.StockAmountAdjust = (type, amount) => Adjust(type, amount, Rules);
        CommandSystem.Register("VendorStockStatus", AccessLevel.GameMaster, e =>
        {
            var r = Rules;
            var list = string.Join(", ", r.StockMultipliers.OrderBy(kv => kv.Key).Select(kv => $"{kv.Key} x{kv.Value}"));
            e.Mobile.SendMessage($"Vendor stock: restock every {(r.RestockMinutes > 0 ? r.RestockMinutes : 60)} minutes; stock multipliers: {(list.Length > 0 ? list : "none")}.");
        });
    }

    /// <summary>A vendor line's starting stock: the stock amount times the type's multiplier (at most 999, the engine's ceiling), else the stock amount.</summary>
    public static int Adjust(Type type, int amount, VendorStockRules rules) =>
        type != null && rules?.StockMultipliers != null && rules.StockMultipliers.TryGetValue(type.Name, out var m) && m > 1
            ? Math.Min(999, amount * m)
            : amount;

    public static void Validate(VendorStockRules rules, List<string> errors)
    {
        if (rules == null)
        {
            return;
        }

        if (rules.RestockMinutes < 0 || rules.RestockMinutes > 24 * 60)
        {
            errors.Add("vendorStock.restockMinutes must be 0 (the stock hour) or 1 to 1440 minutes.");
        }

        foreach (var (name, m) in rules.StockMultipliers ?? new Dictionary<string, int>())
        {
            if (m < 1 || m > 50)
            {
                errors.Add($"vendorStock.stockMultipliers.{name} must be 1 to 50.");
            }

            if (string.IsNullOrWhiteSpace(name) || !name.All(char.IsLetterOrDigit))
            {
                errors.Add($"vendorStock.stockMultipliers: \"{name}\" is not a type name (as LesserCurePotion).");
            }
        }
    }
}
