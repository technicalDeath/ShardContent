using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Server;
using Server.Commands;

namespace BritanniaRenaissance.Content;

/// <summary>One item's shop prices in <c>shopPrices</c> (shard-rules.json): what every vendor that sells it asks, and what every vendor that buys it pays.</summary>
public sealed class ShopPriceRule
{
    /// <summary>The shelf price in gold; 0 keeps the stock price.</summary>
    [JsonPropertyName("shelf")]
    public int Shelf { get; set; }

    /// <summary>What a vendor pays for one; 0 keeps the stock price.</summary>
    [JsonPropertyName("buyBack")]
    public int BuyBack { get; set; }
}

/// <summary>
/// Per-item shop prices set in data, keyed by the item's type name (owner, 2026-10-31: the pickaxe priced like a shovel). A pickaxe digs exactly as a
/// shovel does (Mining, 50 uses, 4 iron ingots at Tinkering, 100 uses when exceptional) and is the weakest axe as a weapon (1-15 damage at speed 35, 11
/// stones, below a 16-gold club), yet stock asks 25 gold against the shovel's 12: a tax on new miners who do not know better. Applied on top of the
/// other price rules through the engine hooks <c>GenericBuyInfo.BuyPriceAdjust</c> and <c>GenericSellInfo.SellPriceAdjust</c> (chained in
/// <see cref="CraftedGoodsPricing"/>). No flag: the table is the switch, and an empty table is stock.
/// </summary>
public static class ShopPrices
{
    private static readonly IReadOnlyDictionary<string, ShopPriceRule> Empty = new Dictionary<string, ShopPriceRule>();

    private static bool _configured;

    public static IReadOnlyDictionary<string, ShopPriceRule> Rules => ShardRulesConfiguration.Settings?.ShopPrices ?? Empty;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CommandSystem.Register("ShopPriceStatus", AccessLevel.GameMaster, e =>
        {
            if (Rules.Count == 0)
            {
                e.Mobile.SendMessage("Shop prices: none set in data (stock prices).");
                return;
            }

            foreach (var (name, rule) in Rules)
            {
                e.Mobile.SendMessage($"Shop prices: {name} shelf {Describe(rule.Shelf)}, buy-back {Describe(rule.BuyBack)}.");
            }
        });
    }

    private static string Describe(int price) => price > 0 ? $"{price} gold" : "stock";

    /// <summary>The shelf price of a type: the table's when it sets one, else the price unchanged.</summary>
    public static int Shelf(Type type, int price) => Shelf(type, price, Rules);

    public static int Shelf(Type type, int price, IReadOnlyDictionary<string, ShopPriceRule> rules) =>
        type != null && rules.TryGetValue(type.Name, out var rule) && rule.Shelf > 0 ? rule.Shelf : price;

    /// <summary>What a vendor pays for a type: the table's when it sets one, else the price unchanged.</summary>
    public static int BuyBack(Type type, int price) => BuyBack(type, price, Rules);

    public static int BuyBack(Type type, int price, IReadOnlyDictionary<string, ShopPriceRule> rules) =>
        type != null && rules.TryGetValue(type.Name, out var rule) && rule.BuyBack > 0 ? rule.BuyBack : price;

    public static void Validate(IReadOnlyDictionary<string, ShopPriceRule> rules, List<string> errors)
    {
        if (rules == null)
        {
            return;
        }

        foreach (var (name, rule) in rules.Where(kv => kv.Value != null))
        {
            if (string.IsNullOrWhiteSpace(name))
            {
                errors.Add("shopPrices: an entry has no item type name.");
            }

            if (rule.Shelf < 0 || rule.Shelf > 1_000_000 || rule.BuyBack < 0 || rule.BuyBack > 1_000_000)
            {
                errors.Add($"shopPrices.{name}: prices must be 0 (stock) or 1 to 1,000,000 gold.");
            }

            if (rule.Shelf > 0 && rule.BuyBack >= rule.Shelf)
            {
                errors.Add($"shopPrices.{name}: buyBack must be below shelf, or buying and selling back pays.");
            }
        }
    }
}
