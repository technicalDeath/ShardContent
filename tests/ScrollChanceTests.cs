using Server;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The percent a single click on a spell scroll shows (docs/Scroll-Success-Chance-Evidence.md): the same even rise between the cast range's ends that the cast rolls.</summary>
public class ScrollChanceTests
{
    [Theory]
    [InlineData(0.0, 0.0, 40.0, 0)]       // first circle by scroll starts at 0 skill: nothing yet at the very start
    [InlineData(10.0, 0.0, 40.0, 25)]
    [InlineData(20.0, 0.0, 40.0, 50)]
    [InlineData(39.9, 0.0, 40.0, 99)]     // rounded down: 100 means certain
    [InlineData(40.0, 0.0, 40.0, 100)]
    [InlineData(90.0, 0.0, 40.0, 100)]
    [InlineData(-1.0, 0.0, 40.0, 0)]      // below the start the cast always fizzles
    [InlineData(25.0, 40.0, 80.0, 0)]
    [InlineData(60.0, 40.0, 80.0, 50)]
    public void ThePercentRisesEvenlyBetweenTheEndsOfTheCastRange(double skill, double min, double max, int expected) =>
        Assert.Equal(expected, ScrollChanceService.Percent(skill, min, max));

    [Fact]
    public void ARangeWithNoWidthIsCertainOnceReached()
    {
        Assert.Equal(100, ScrollChanceService.Percent(30.0, 30.0, 30.0));
        Assert.Equal(0, ScrollChanceService.Percent(29.9, 30.0, 30.0));
    }

    [Fact]
    public void ThePageFlagIsOnSinceTheOwnerActivatedIt()
    {
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        // activated 2026-10-13 on the owner's "activate anything that hasn't been yet"
        Assert.True(rules.FeatureFlags.ScrollSuccessChance);
    }
}
