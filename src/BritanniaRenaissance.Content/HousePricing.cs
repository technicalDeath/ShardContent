using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Server;
using Server.Commands;
using Server.Multis.Deeds;

namespace BritanniaRenaissance.Content;

/// <summary>Settings for <see cref="HousePricing"/> (<c>housePricing</c> in shard-rules.json).</summary>
public sealed class HousePricingRules
{
    /// <summary>What a small house deed costs at the Real Estate Broker, in gold; 0 keeps the stock price (43,800).</summary>
    [JsonPropertyName("smallHouses")]
    public int SmallHouses { get; set; }
}

/// <summary>
/// The shard's house prices (owner, 2026-10-18: "modify the shard so that small houses only cost 16,000 gold"). The six small houses that stock sells at
/// 43,800 (small brick, field stone, stone plaster, wood, wood plaster, thatched cottage) cost <see cref="HousePricingRules.SmallHouses"/> instead, and the
/// same value is the deed's house value for placement and what the Real Estate Broker's buy-back is figured from (80% of it, stock), so buying a deed and
/// selling it back never pays. Larger houses keep their stock prices. Engine hooks: <c>GenericBuyInfo.BuyPriceAdjust</c> (the deed shop, chained through
/// <see cref="CraftedGoodsPricing"/>) and <c>HouseDeed.ValueAdjust</c> (placement value and buy-back).
/// </summary>
public static class HousePricing
{
    public const int StockSmallHousePrice = 43800;

    public static readonly IReadOnlySet<Type> SmallHouseDeeds = new HashSet<Type>
    {
        typeof(SmallBrickHouseDeed), typeof(FieldStoneHouseDeed), typeof(StonePlasterHouseDeed), typeof(WoodHouseDeed), typeof(WoodPlasterHouseDeed),
        typeof(ThatchedRoofCottageDeed)
    };

    private static bool _configured;

    public static HousePricingRules Rules => ShardRulesConfiguration.Settings?.HousePricing ?? new HousePricingRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        HouseDeed.ValueAdjust = (deed, value) => Adjust(deed.GetType(), value);
        CommandSystem.Register("HousePriceStatus", AccessLevel.GameMaster, e =>
            e.Mobile.SendMessage($"House pricing: small houses {Price(Rules.SmallHouses, StockSmallHousePrice):N0} gold (stock {StockSmallHousePrice:N0})."));
    }

    /// <summary>A deed type's price: the configured small-house price for the six small houses, else the stock price unchanged.</summary>
    public static int Adjust(Type type, int price) => Adjust(type, price, Rules.SmallHouses);

    public static int Adjust(Type type, int price, int smallHouses) =>
        smallHouses > 0 && type != null && SmallHouseDeeds.Contains(type) ? smallHouses : price;

    public static int Price(int smallHouses, int stock) => smallHouses > 0 ? smallHouses : stock;

    public static void Validate(HousePricingRules rules, List<string> errors)
    {
        if (rules == null)
        {
            return;
        }

        if (rules.SmallHouses < 0 || rules.SmallHouses > 1_000_000)
        {
            errors.Add("housePricing.smallHouses must be 0 (stock) or a price from 1 to 1,000,000 gold.");
        }
    }
}
