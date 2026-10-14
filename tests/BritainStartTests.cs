using BritanniaRenaissance.Content;
using Server;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>New characters start in Britain only (docs/Britain-Start-Evidence.md).</summary>
public class BritainStartTests
{
    private static CityInfo City(string name, int x) => new(name, "An Inn", x, 0, 0, null);

    private static CityInfo[] Nine() => [City("Yew", 633), City("Minoc", 2476), City("Britain", 1496), City("Moonglow", 4408), City("Trinsic", 1845), City("Magincia", 3734), City("Jhelom", 1374), City("Skara Brae", 618), City("Vesper", 2771)];

    [Fact]
    public void OnlyBritainIsLeftOfTheNineStockTowns()
    {
        var left = BritainStartService.Only(Nine(), "Britain");

        Assert.Single(left);
        Assert.Equal("Britain", left[0].City);
        Assert.Equal(1496, left[0].Location.X);
    }

    [Fact]
    public void TheNameIsMatchedWithoutRegardToCase() => Assert.Equal("Britain", BritainStartService.Only(Nine(), "BRITAIN")[0].City);

    [Fact]
    public void AListWithoutBritainIsLeftAlone()
    {
        var yewOnly = new[] { City("Yew", 633), City("Minoc", 2476) };

        Assert.Same(yewOnly, BritainStartService.Only(yewOnly, "Britain"));
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysSoAndOnInTheShippedRules()
    {
        Assert.False(new DeferredFeatureFlags().StartInBritainOnly);

        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            System.IO.File.ReadAllText(System.IO.Path.Combine(System.AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        Assert.True(rules.FeatureFlags.StartInBritainOnly);   // the owner chose "Offer only Britain" on 2026-10-13
        Assert.Contains(nameof(DeferredFeatureFlags.StartInBritainOnly), rules.FeatureFlags.EnabledNames());
    }
}
