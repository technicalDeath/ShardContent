using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Server.Multis.Deeds;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class HousePricingTests
{
    [Fact]
    public void TheSixSmallHousesTakeTheConfiguredPrice()
    {
        foreach (var type in new[]
                 {
                     typeof(SmallBrickHouseDeed), typeof(FieldStoneHouseDeed), typeof(StonePlasterHouseDeed), typeof(WoodHouseDeed),
                     typeof(WoodPlasterHouseDeed), typeof(ThatchedRoofCottageDeed)
                 })
        {
            Assert.Equal(16000, HousePricing.Adjust(type, 43800, 16000));
        }
    }

    [Fact]
    public void LargerHousesAndOtherItemsKeepTheirPrice()
    {
        Assert.Equal(144500, HousePricing.Adjust(typeof(BrickHouseDeed), 144500, 16000));
        Assert.Equal(1022800, HousePricing.Adjust(typeof(CastleDeed), 1022800, 16000));
        Assert.Equal(12, HousePricing.Adjust(typeof(Server.Items.Bandage), 12, 16000));
        Assert.Equal(43800, HousePricing.Adjust(null, 43800, 16000));
    }

    [Fact]
    public void ZeroKeepsTheStockPrice()
    {
        Assert.Equal(43800, HousePricing.Adjust(typeof(SmallBrickHouseDeed), 43800, 0));
        Assert.Equal(43800, HousePricing.Price(0, HousePricing.StockSmallHousePrice));
        Assert.Equal(16000, HousePricing.Price(16000, HousePricing.StockSmallHousePrice));
    }

    [Fact]
    public void ValidationRejectsNegativeAndAbsurdPrices()
    {
        var errors = new List<string>();
        HousePricing.Validate(new HousePricingRules { SmallHouses = 16000 }, errors);
        HousePricing.Validate(new HousePricingRules { SmallHouses = 0 }, errors);
        Assert.Empty(errors);
        HousePricing.Validate(new HousePricingRules { SmallHouses = -1 }, errors);
        HousePricing.Validate(new HousePricingRules { SmallHouses = 2_000_000 }, errors);
        Assert.Equal(2, errors.Count);
    }

    [Fact]
    public void TheShardConfigSetsSmallHousesTo16000()
    {
        var dir = new DirectoryInfo(System.AppContext.BaseDirectory);
        while (dir != null && !File.Exists(Path.Combine(dir.FullName, "data", "configuration", "shard-rules.json")))
        {
            dir = dir.Parent;
        }

        Assert.NotNull(dir);
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(dir!.FullName, "data", "configuration", "shard-rules.json")));
        Assert.Equal(16000, rules!.HousePricing.SmallHouses);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }
}
