using BritanniaRenaissance.Content;
using Xunit;
using static BritanniaRenaissance.Content.SellPriceTooltips;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The sell-price line of an item's tooltip (docs/Tooltip-Sell-Price-Plan.md).</summary>
public class SellPriceTooltipsTests
{
    [Fact]
    public void NoQuoteMeansNoLine() => Assert.Null(Describe([], 1));

    [Fact]
    public void OneShopIsNamedWithItsPrice() => Assert.Equal("Value: 3gp at Butcher", Describe([new Quote("Butcher", 3)], 1));

    [Fact]
    public void TheBestPriceWinsAndNoOtherShopIsMentioned() =>
        Assert.Equal("Value: 22gp at Blacksmith", Describe([new Quote("Armorer", 18), new Quote("Blacksmith", 22), new Quote("Weaponsmith", 20)], 1));

    [Fact]
    public void EqualBestPricesGoToTheShopThatComesFirstAlphabetically() =>
        Assert.Equal("Value: 5gp at Alchemist", Describe([new Quote("Mage", 5), new Quote("Alchemist", 5)], 1));

    [Fact]
    public void AStackSaysEach() => Assert.Equal("Value: 2gp each at Provisioner", Describe([new Quote("Provisioner", 2)], 20));

    [Fact]
    public void TheSameShopTwiceCountsOnce() =>
        Assert.Equal("Value: 7gp at Tailor", Describe([new Quote("Tailor", 7), new Quote("Tailor", 5)], 1));

    [Theory]
    [InlineData("Butcher", "Butcher")]
    [InlineData("AnimalTrainer", "Animal Trainer")]
    [InlineData("InnKeeper", "Inn Keeper")]
    public void AShopIsNamedAsAPlayerKnowsIt(string type, string shop) => Assert.Equal(shop, ShopName(type));

    [Fact]
    public void TheFlagIsOnInTheShippedRulesOnTheOwnersWord()
    {
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            System.IO.File.ReadAllText(System.IO.Path.Combine(System.AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        Assert.True(rules.FeatureFlags.SellPriceTooltips);
        Assert.Contains(nameof(DeferredFeatureFlags.SellPriceTooltips), rules.FeatureFlags.EnabledNames());
    }

    [Fact]
    public void TheGuidePageForShopsMentionsItOnlyWhenItIsOn()
    {
        var off = WelcomeGuide.Topics(new WelcomeGuide.Context(false, false, false, false, false), new CampTravelRules()).Single(t => t.Key == "shops");
        var on = WelcomeGuide.Topics(new WelcomeGuide.Context(false, false, false, false, false, SellPriceTooltips: true), new CampTravelRules()).Single(t => t.Key == "shops");

        Assert.DoesNotContain(off.Paragraphs, p => p.Contains("Value: 3gp at Butcher"));
        Assert.Contains(on.Paragraphs, p => p.Contains("Value: 3gp at Butcher"));
    }
}
