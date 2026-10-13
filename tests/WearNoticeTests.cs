using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The "your item is wearing out" notice (docs/To-Do-List.md).</summary>
public class WearNoticeTests
{
    [Theory]
    [InlineData(100, 100, false)]
    [InlineData(26, 100, false)]
    [InlineData(25, 100, true)]
    [InlineData(10, 40, true)]
    [InlineData(11, 40, false)]
    [InlineData(0, 40, true)]
    [InlineData(0, 0, false)]   // an item without durability
    public void TheLineIsAQuarterOfTheMaximum(int hits, int max, bool low) => Assert.Equal(low, WearNoticeService.IsLow(hits, max));

    [Fact]
    public void TheMessageNamesTheItemInLowerCase() =>
        Assert.Equal("Your long sword is badly worn: about a quarter of its durability is left.", WearNoticeService.Message("Long Sword"));

    [Fact]
    public void TheMessageHasAFallbackName() => Assert.StartsWith("Your equipment is badly worn", WearNoticeService.Message(" "));

    [Fact]
    public void TheNoticeIsOnInTheShippedRulesSinceTheOwnerActivatedIt()
    {
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            System.IO.File.ReadAllText(System.IO.Path.Combine(System.AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        Assert.True(rules.FeatureFlags.WearNotice);   // activated 2026-10-12 on the owner's explicit "activate"
    }
}
