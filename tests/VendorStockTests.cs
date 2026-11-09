using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Server.Items;
using Server.Mobiles;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The owner (2026-11-02): "Increase the number of potions at shops, and any other provisions preventing a bot from going to dungeons, and have
/// shops restock every 30 minutes instead of 60."</summary>
public class VendorStockTests
{
    private static VendorStockRules SourceRules()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        return doc.RootElement.GetProperty("vendorStock").Deserialize<VendorStockRules>()!;
    }

    [Fact]
    public void TheSourceRestocksEveryThirtyMinutesAndRaisesTheDungeonKit()
    {
        var rules = SourceRules();
        Assert.Equal(30, rules.RestockMinutes);
        Assert.Equal(40, VendorStock.Adjust(typeof(LesserCurePotion), 10, rules));
        Assert.Equal(30, VendorStock.Adjust(typeof(LesserHealPotion), 10, rules));
        Assert.Equal(40, VendorStock.Adjust(typeof(RefreshPotion), 20, rules));
        Assert.Equal(200, VendorStock.Adjust(typeof(Bandage), 20, rules));
        Assert.Equal(100, VendorStock.Adjust(typeof(Arrow), 20, rules));
        Assert.Equal(100, VendorStock.Adjust(typeof(Bolt), 20, rules));
    }

    [Fact]
    public void EveryConfiguredNameIsAnItemTypeName()
    {
        var known = new HashSet<string>
        {
            nameof(LesserCurePotion), nameof(LesserHealPotion), nameof(RefreshPotion), nameof(Bandage), nameof(Arrow), nameof(Bolt),
            nameof(BlackPearl), nameof(Bloodmoss), nameof(Garlic), nameof(Ginseng), nameof(MandrakeRoot), nameof(Nightshade), nameof(SpidersSilk), nameof(SulfurousAsh)
        };
        foreach (var name in SourceRules().StockMultipliers.Keys)
        {
            Assert.Contains(name, known);       // a misspelt name would silently leave its line on stock
        }
    }

    [Fact]
    public void OtherLinesAndTheCeilingStayStock()
    {
        var rules = SourceRules();
        Assert.Equal(10, VendorStock.Adjust(typeof(NightSightPotion), 10, rules));
        Assert.Equal(10, VendorStock.Adjust(null, 10, rules));
        Assert.Equal(999, VendorStock.Adjust(typeof(Bandage), 500, rules));
        Assert.Equal(20, VendorStock.Adjust(typeof(Bandage), 20, new VendorStockRules()));
    }

    [Fact]
    public void TheSourceSectionValidatesAndBadValuesDoNot()
    {
        var errors = new List<string>();
        VendorStock.Validate(SourceRules(), errors);
        Assert.Empty(errors);
        VendorStock.Validate(new VendorStockRules { RestockMinutes = -1, StockMultipliers = { ["Lesser Cure"] = 0 } }, errors);
        Assert.Equal(3, errors.Count);
    }

    [Fact]
    public void ARaisedLineDoublesWhenItSellsOutAndNeverHalvesBelowItsRaisedStock()
    {
        var old = GenericBuyInfo.StockAmountAdjust;
        try
        {
            GenericBuyInfo.StockAmountAdjust = (type, amount) => type == typeof(LesserCurePotion) ? amount * 4 : amount;
            var cure = new GenericBuyInfo(typeof(LesserCurePotion), 15, 10, 0xF07, 0);
            Assert.Equal(40, cure.Amount);
            Assert.Equal(40, cure.MinAmount);
            cure.Amount = 0;
            cure.OnRestock();
            Assert.Equal(80, cure.MaxAmount);            // sold out: doubled, as stock
            cure.OnRestock();                            // nothing bought: halved, but not below 40
            cure.OnRestock();
            Assert.Equal(40, cure.MaxAmount);
            var plain = new GenericBuyInfo(typeof(NightSightPotion), 15, 10, 0xF06, 0);
            Assert.Equal(10, plain.Amount);
            Assert.Equal(0, plain.MinAmount);            // an unraised line keeps the stock behaviour
        }
        finally
        {
            GenericBuyInfo.StockAmountAdjust = old;
        }
    }
}
