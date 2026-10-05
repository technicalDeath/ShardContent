using System.Reflection;
using System.Text.Json;
using Server.Engines.MLQuests.Definitions;
using Server.Mobiles;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class BackpackWardVendorTests
{
    private static WardVendorRules Rules(int price = 2000, int stock = 20, int buyBack = 0) =>
        new() { Price = price, StockPerVendor = stock, BuyBackPrice = buyBack };

    private static List<string> Errors(WardVendorRules rules)
    {
        var errors = new List<string>();
        BackpackWardVendor.Validate(rules, errors);
        return errors;
    }

    // ---- configuration

    [Fact]
    public void TheDefaultsAndTheDeployedValuesAreAPriceCeilingAndADeepShelf()
    {
        var defaults = new WardVendorRules();

        Assert.Equal(2000, defaults.Price);
        Assert.Equal(20, defaults.StockPerVendor);
        Assert.Equal(110, defaults.BuyBackPrice);
        Assert.Empty(Errors(defaults));
    }

    [Theory]
    [InlineData(0)]
    [InlineData(1)]
    [InlineData(1999)]
    public void ABuyBackPriceBelowTheSalePriceOrZeroIsAccepted(int buyBack)
    {
        Assert.Empty(Errors(Rules(price: 2000, buyBack: buyBack)));
    }

    [Theory]
    [InlineData(2000)]
    [InlineData(2500)]
    public void ABuyBackAtOrAboveTheSalePriceIsRejectedBecauseItWouldPayGoldForNothing(int buyBack)
    {
        var error = Assert.Single(Errors(Rules(price: 2000, buyBack: buyBack)));

        Assert.Contains("wardVendor.buyBackPrice", error);
        Assert.Contains("below wardVendor.price", error);
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(1_000_001)]
    public void AnOutOfRangeBuyBackIsRejectedByName(int buyBack)
    {
        var error = Assert.Single(Errors(Rules(price: 1_000_000, buyBack: buyBack)));

        Assert.Contains("wardVendor.buyBackPrice", error);
    }

    [Theory]
    [InlineData(1, 0)]
    [InlineData(1_000_000, 999)]
    [InlineData(2000, 20)]
    public void ThePriceAndStockLimitsAreInclusive(int price, int stock)
    {
        Assert.Empty(Errors(Rules(price, stock)));
    }

    [Theory]
    [InlineData(0, 20, "price")]
    [InlineData(-5, 20, "price")]
    [InlineData(1_000_001, 20, "price")]
    [InlineData(2000, -1, "stockPerVendor")]
    [InlineData(2000, 1000, "stockPerVendor")]
    public void AnOutOfRangeValueIsRejectedByName(int price, int stock, string name)
    {
        var errors = Errors(Rules(price, stock));

        var error = Assert.Single(errors);
        Assert.Contains($"wardVendor.{name}", error);
    }

    [Fact]
    public void ABadPriceAndABadStockAreBothReported()
    {
        Assert.Equal(2, Errors(Rules(0, -1)).Count);
    }

    [Fact]
    public void TheShippedShardRulesFileCarriesTheApprovedPriceAndShelf()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;

        Assert.Equal(2000, rules.WardVendor.Price);
        Assert.Equal(20, rules.WardVendor.StockPerVendor);
        Assert.Equal(110, rules.WardVendor.BuyBackPrice);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void TheBuyBackSitsAboveWhatTheIngotsCostAndBelowTheStockLockpickRate()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;

        // NPCs sell iron ingots for 5 gp, so a Ward costs 5 gp per ingot. Stock pays 6 gp for a Lockpick that takes one
        // ingot, so 6 gp per ingot is the most a tinker-made item earns from an NPC today. A buy-back inside that band is
        // a small guaranteed profit that adds no faucet stock lacks; if the ingot count changes, this price moves with it.
        Assert.InRange(rules.WardVendor.BuyBackPrice, rules.WardCraft.Ingots * 5 + 1, rules.WardCraft.Ingots * 6 - 1);
    }

    [Fact]
    public void TheShardRulesValidatorRunsTheWardVendorChecks()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
        rules.WardVendor.Price = 0;

        Assert.Contains(ShardRulesConfiguration.Validate(rules), e => e.Contains("wardVendor.price"));
    }

    // ---- who sells it

    [Fact]
    public void OnlyPlainTinkersSellTheWard()
    {
        Assert.True(BackpackWardVendor.Sells(typeof(Tinker)));
        Assert.False(BackpackWardVendor.Sells(typeof(AmeliaYoungstone)));
        Assert.False(BackpackWardVendor.Sells(typeof(Alchemist)));
        Assert.False(BackpackWardVendor.Sells(typeof(Mage)));
        Assert.False(BackpackWardVendor.Sells(typeof(Provisioner)));
    }

    // ---- the shelf entry

    [Fact]
    public void TheEntryOffersABackpackWardAtTheConfiguredPriceAndStock()
    {
        var entry = BackpackWardVendor.CreateEntry(Rules(price: 2500, stock: 12), theftProtectionEnabled: true);

        Assert.NotNull(entry);
        Assert.Equal(typeof(BackpackWard), entry!.Type);
        Assert.Equal(2500, entry.Price);
        Assert.Equal(12, entry.Amount);
        Assert.Equal(12, entry.MaxAmount);
        Assert.Equal(BackpackWard.DefaultItemId, entry.ItemID);
        Assert.Equal("backpack ward", entry.Name);
    }

    [Fact]
    public void TheWardIsOffSaleWhenTheftProtectionIsOff()
    {
        Assert.Null(BackpackWardVendor.CreateEntry(Rules(), theftProtectionEnabled: false));
    }

    [Fact]
    public void AStockOfZeroTakesTheWardOffSale()
    {
        Assert.Null(BackpackWardVendor.CreateEntry(Rules(stock: 0), theftProtectionEnabled: true));
    }

    // ---- the buy-back

    [Fact]
    public void TheBuyBackPaysTheConfiguredPriceAndIsNeverRelisted()
    {
        var buyBack = BackpackWardVendor.CreateBuyBack(Rules(buyBack: 110), theftProtectionEnabled: true);

        Assert.NotNull(buyBack);
        Assert.Equal(110, buyBack!.GetSellPriceFor(null!));
        Assert.False(buyBack.IsResellable(null!));
        Assert.Equal(new[] { typeof(BackpackWard) }, buyBack.Types);
        Assert.Equal("backpack ward", buyBack.GetNameFor(null!));
    }

    [Fact]
    public void TheBuyBackIsOffWhenTheftProtectionIsOffOrThePriceIsZero()
    {
        Assert.Null(BackpackWardVendor.CreateBuyBack(Rules(buyBack: 110), theftProtectionEnabled: false));
        Assert.Null(BackpackWardVendor.CreateBuyBack(Rules(buyBack: 0), theftProtectionEnabled: true));
    }

    [Fact]
    public void TheBuyBackAndTheStockedWardAreSeparateSwitches()
    {
        var noStock = Rules(stock: 0, buyBack: 110);
        var noBuyBack = Rules(stock: 20, buyBack: 0);

        Assert.Null(BackpackWardVendor.CreateEntry(noStock, true));
        Assert.NotNull(BackpackWardVendor.CreateBuyBack(noStock, true));
        Assert.NotNull(BackpackWardVendor.CreateEntry(noBuyBack, true));
        Assert.Null(BackpackWardVendor.CreateBuyBack(noBuyBack, true));
    }

    // ---- the engine's own shelf behavior, with this entry

    private static GenericBuyInfo Entry(int stock = 20) =>
        BackpackWardVendor.CreateEntry(Rules(stock: stock), theftProtectionEnabled: true)!;

    [Fact]
    public void ANeverBoughtShelfStaysAtItsStartingDepth()
    {
        var entry = Entry(20);

        entry.OnRestock();
        entry.OnRestock();

        Assert.Equal(20, entry.Amount);
        Assert.Equal(20, entry.MaxAmount);
    }

    [Fact]
    public void ASoldOutShelfDoublesAtTheNextRestockAndStopsAtTheEngineCeiling()
    {
        var entry = Entry(20);

        entry.Amount = 0;
        entry.OnRestock();
        Assert.Equal(40, entry.Amount);

        var restocks = 0;
        while (entry.MaxAmount < BackpackWardVendor.MaxStock && restocks++ < 20)
        {
            entry.Amount = 0;
            entry.OnRestock();
        }

        Assert.Equal(BackpackWardVendor.MaxStock, entry.MaxAmount);
        Assert.Equal(BackpackWardVendor.MaxStock, entry.Amount);
    }

    [Fact]
    public void ADoubledShelfShrinksBackWhenLessThanHalfIsBought()
    {
        var entry = Entry(20);
        entry.Amount = 0;
        entry.OnRestock();

        // 40 on the shelf, 5 bought: 35 left is at least half, so the maximum halves back to 20.
        entry.Amount = 35;
        entry.OnRestock();

        Assert.Equal(20, entry.MaxAmount);
        Assert.Equal(20, entry.Amount);
    }

    // ---- registration

    [Fact]
    public void ConfigureRegistersEachVendorHookExactlyOnce()
    {
        BackpackWardVendor.Configure();
        BackpackWardVendor.Configure();

        Assert.Equal(1, HandlersFrom("BuyInfoLoaded"));
        Assert.Equal(1, HandlersFrom("SellInfoLoaded"));
        Assert.Equal(1, HandlersFrom("ItemsBought"));
        Assert.Equal(1, HandlersFrom("ItemsSold"));
    }

    private static int HandlersFrom(string eventName)
    {
        var field = typeof(BaseVendor).GetField(eventName, BindingFlags.Static | BindingFlags.NonPublic);
        var handler = (Delegate?)field?.GetValue(null);

        return handler?.GetInvocationList().Count(static d => d.Method.DeclaringType == typeof(BackpackWardVendor)) ?? 0;
    }
}
