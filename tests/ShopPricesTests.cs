using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class ShopPricesTests
{
    private static readonly Dictionary<string, ShopPriceRule> Table = new()
    {
        ["Pickaxe"] = new ShopPriceRule { Shelf = 12, BuyBack = 6 }
    };

    [Fact]
    public void APickaxeIsPricedFromTheTable()
    {
        Assert.Equal(12, ShopPrices.Shelf(typeof(Pickaxe), 25, Table));
        Assert.Equal(6, ShopPrices.BuyBack(typeof(Pickaxe), 16, Table));
    }

    [Fact]
    public void OtherItemsAndZeroKeepTheirPrice()
    {
        Assert.Equal(12, ShopPrices.Shelf(typeof(Shovel), 12, Table));
        Assert.Equal(6, ShopPrices.BuyBack(typeof(Shovel), 6, Table));
        Assert.Equal(25, ShopPrices.Shelf(null, 25, Table));
        var stock = new Dictionary<string, ShopPriceRule> { ["Pickaxe"] = new ShopPriceRule() };
        Assert.Equal(25, ShopPrices.Shelf(typeof(Pickaxe), 25, stock));
        Assert.Equal(16, ShopPrices.BuyBack(typeof(Pickaxe), 16, stock));
    }

    [Fact]
    public void ABuyBackAtOrAboveTheShelfIsRefused()
    {
        var errors = new List<string>();
        ShopPrices.Validate(new Dictionary<string, ShopPriceRule> { ["Pickaxe"] = new ShopPriceRule { Shelf = 12, BuyBack = 12 } }, errors);
        Assert.Single(errors);
        errors.Clear();
        ShopPrices.Validate(new Dictionary<string, ShopPriceRule> { ["Pickaxe"] = new ShopPriceRule { Shelf = -1 } }, errors);
        Assert.NotEmpty(errors);
        errors.Clear();
        ShopPrices.Validate(Table, errors);
        Assert.Empty(errors);
    }

    [Fact]
    public void TheShardPricesThePickaxeLikeAShovel()
    {
        var path = Path.Combine(System.AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        var pick = doc.RootElement.GetProperty("shopPrices").GetProperty("Pickaxe");
        Assert.Equal(12, pick.GetProperty("shelf").GetInt32());
        Assert.Equal(6, pick.GetProperty("buyBack").GetInt32());
    }
}
