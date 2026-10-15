using System;
using System.Collections.Generic;
using BritanniaRenaissance.Content;
using Server.Items;
using Xunit;
using static BritanniaRenaissance.Content.CraftedGoodsPricing;

namespace BritanniaRenaissance.Content.Tests;

public class CraftedGoodsPricingTests
{
    [Fact]
    public void MaterialCostPricesKnownResourcesOnly()
    {
        var prices = new Dictionary<Type, int> { [typeof(IronIngot)] = 5, [typeof(Cloth)] = 2 };
        Assert.Equal(40, MaterialCost(new[] { (typeof(IronIngot), 8) }, prices));                          // a katana: 8 ingots
        Assert.Equal(28, MaterialCost(new[] { (typeof(Cloth), 14), (typeof(Gears), 3) }, prices));         // an unpriced part adds nothing
        Assert.Equal(0, MaterialCost(Array.Empty<(Type, int)>(), prices));
    }

    [Theory]
    [InlineData(28, 35)]   // a cloak: 14 cut cloth at 2
    [InlineData(40, 50)]   // a katana: 8 ingots at 5
    [InlineData(1, 2)]     // rounds up
    [InlineData(0, 0)]     // unknown cost: no floor
    public void TheFloorIsMaterialCostPlusAQuarter(int cost, int floor) => Assert.Equal(floor, PayFloor(cost));

    [Fact]
    public void PricesAreRaisedToTheFloorsAndNeverLowered()
    {
        Assert.Equal(35, VendorPays(4, 28));      // the Tailor paid 4 for a cloak
        Assert.Equal(60, VendorPays(60, 28));     // a stock price above the floor stays
        Assert.Equal(4, VendorPays(4, 0));        // not a crafted item
        Assert.Equal(53, VendorCharges(8, 28));   // the Tailor sold cloaks for 8
        Assert.Equal(90, VendorCharges(90, 28));
        Assert.Equal(8, VendorCharges(8, 0));
    }

    [Theory]
    [InlineData(1)]
    [InlineData(6)]
    [InlineData(28)]
    [InlineData(125)]
    [InlineData(999)]
    public void BuyingFromAVendorToSellBackNeverPays(int cost)
    {
        // whatever the stock prices, once both are adjusted the vendor charges more than it pays
        foreach (var (stockPay, stockCharge) in new[] { (1, 2), (4, 8), (50, 100), (300, 500) })
        {
            if (stockPay >= stockCharge)
            {
                continue;
            }

            Assert.True(VendorCharges(stockCharge, cost) > VendorPays(stockPay, cost));
        }
    }

    [Fact]
    public void AMaterialIsNotAProduct()
    {
        Assert.Contains(typeof(Board), MaterialPrices.Keys);   // boards from logs and cut cloth from a bolt are conversions, so their prices stay stock
        Assert.Contains(typeof(Cloth), MaterialPrices.Keys);
        Assert.True(MaterialPrices[typeof(IronIngot)] > 0);
    }

    [Theory]
    [InlineData(typeof(SewingKit))]       // a BaseTool
    [InlineData(typeof(TinkerTools))]
    [InlineData(typeof(Pickaxe))]         // a weapon class in ModernUO, but a miner's tool
    [InlineData(typeof(Hatchet))]
    [InlineData(typeof(Shovel))]          // a BaseHarvestTool
    [InlineData(typeof(Scissors))]
    [InlineData(typeof(Arrow))]
    [InlineData(typeof(Bolt))]
    [InlineData(typeof(Bandage))]
    [InlineData(typeof(Kindling))]
    public void ToolsAndConsumablesKeepStockPrices(Type type) => Assert.True(IsKeptAtStock(type));

    [Theory]
    [InlineData(typeof(Cloak))]
    [InlineData(typeof(Katana))]
    [InlineData(typeof(PlateChest))]
    public void ProductsGetTheFloors(Type type) => Assert.False(IsKeptAtStock(type));

    [Fact]
    public void TheFlagIsOffUntilSwitchedOn() => Assert.False(new DeferredFeatureFlags().CraftedGoodsPricing);
}
