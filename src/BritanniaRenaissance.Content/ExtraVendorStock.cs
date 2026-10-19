using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Server;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Goods a shop sells beyond its stock list, from data (<c>extraVendorStock</c> in shard-rules.json; an empty list sells nothing extra, no flag).
/// The owner (2026-10-18) chose "Mage shops sell Recall/Mark": stock ModernUO's Mage sells the scrolls of circles 1 to 3 only, so no one could buy a
/// Recall or a Mark scroll, and a scribe cannot inscribe a spell its book lacks. Each entry adds one shelf (item type, price, stock) to the named vendor
/// classes when their buy list loads, unless the vendor already sells that type. The price goes through the shard's buy-price hook like any shelf
/// (crafted-goods pricing raises it to its floor when that is higher).
/// </summary>
public static class ExtraVendorStock
{
    public const int MaxStock = 999;

    public const int MaxPrice = 1_000_000;

    private static bool _configured;

    public static List<ExtraVendorStockEntry> Entries => ShardRulesConfiguration.Settings?.ExtraVendorStock ?? [];

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        BaseVendor.BuyInfoLoaded += OnBuyInfoLoaded;
    }

    public static void Validate(List<ExtraVendorStockEntry> entries, List<string> errors)
    {
        foreach (var e in entries)
        {
            if (string.IsNullOrWhiteSpace(e.Item) || ItemType(e.Item) is null)
            {
                errors.Add($"extraVendorStock: '{e.Item}' is not an item type.");
            }

            if (e.Price is < 1 or > MaxPrice || e.Amount is < 1 or > MaxStock || e.Vendors.Count == 0 || e.ItemId is < 1 or > 0xFFFF)
            {
                errors.Add($"extraVendorStock '{e.Item}' needs a price of 1 to {MaxPrice}, a stock of 1 to {MaxStock}, an item id and at least one vendor.");
            }
        }
    }

    /// <summary>The shelves one vendor class gets: (type, price, amount, item id) for every entry that names it.</summary>
    public static List<(Type Type, int Price, int Amount, int ItemId)> ShelvesFor(string vendorType, IEnumerable<ExtraVendorStockEntry> entries)
    {
        var shelves = new List<(Type, int, int, int)>();

        foreach (var e in entries)
        {
            if (e.Vendors.Contains(vendorType) && ItemType(e.Item) is { } type && !shelves.Exists(s => s.Item1 == type))
            {
                shelves.Add((type, e.Price, e.Amount, e.ItemId));
            }
        }

        return shelves;
    }

    private static void OnBuyInfoLoaded(BaseVendor vendor, List<IBuyItemInfo> buyInfo)
    {
        foreach (var (type, price, amount, itemId) in ShelvesFor(vendor.GetType().Name, Entries))
        {
            if (buyInfo.Exists(b => b is GenericBuyInfo g && g.Type == type))
            {
                continue;
            }

            buyInfo.Add(new GenericBuyInfo(type, price, amount, itemId, 0));
        }
    }

    // item types live in the content assembly beside the vendors; looked up there so the tests need no running server
    public static Type? ItemType(string name)
    {
        foreach (var type in typeof(BaseVendor).Assembly.GetTypes())
        {
            if (type.Name == name && typeof(Item).IsAssignableFrom(type) && !type.IsAbstract)
            {
                return type;
            }
        }

        return null;
    }
}

public sealed class ExtraVendorStockEntry
{
    /// <summary>The item's type name (RecallScroll, MarkScroll...).</summary>
    [JsonPropertyName("item")]
    public string Item { get; set; } = "";

    [JsonPropertyName("price")]
    public int Price { get; set; }

    /// <summary>The shelf's stock; it restocks like any vendor shelf.</summary>
    [JsonPropertyName("amount")]
    public int Amount { get; set; } = 20;

    /// <summary>The graphic the shop list shows (the item's own: a Recall scroll 0x1F4C).</summary>
    [JsonPropertyName("itemId")]
    public int ItemId { get; set; }

    /// <summary>Vendor class names (Mage...).</summary>
    [JsonPropertyName("vendors")]
    public List<string> Vendors { get; set; } = [];
}
