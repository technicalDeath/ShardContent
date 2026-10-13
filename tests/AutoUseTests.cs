using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The server half of the bars' auto-use options (docs/Auto-Use-Evidence.md).</summary>
public class AutoUseTests
{
    private const AutoUseService.Cure Lesser = AutoUseService.Cure.Lesser;
    private const AutoUseService.Cure Regular = AutoUseService.Cure.Regular;
    private const AutoUseService.Cure Greater = AutoUseService.Cure.Greater;

    [Theory]
    [InlineData(0, true, true, true, AutoUseService.Cure.Regular)]    // a lesser poison: the regular cure is certain, the lesser one is only 75%
    [InlineData(0, true, false, true, AutoUseService.Cure.Greater)]   // no regular cure: the greater one is certain
    [InlineData(0, true, false, false, AutoUseService.Cure.Lesser)]   // only the lesser: 75% is the best there is
    [InlineData(1, true, true, true, AutoUseService.Cure.Greater)]    // a regular poison: only the greater cure is certain
    [InlineData(1, true, true, false, AutoUseService.Cure.Regular)]   // 75% beats 50%
    [InlineData(2, true, true, true, AutoUseService.Cure.Greater)]
    [InlineData(2, true, true, false, AutoUseService.Cure.Regular)]
    [InlineData(3, true, true, true, AutoUseService.Cure.Greater)]    // a deadly poison: 75% with the greater cure
    [InlineData(3, true, true, false, AutoUseService.Cure.Regular)]   // 15% is still a chance
    [InlineData(4, true, true, true, AutoUseService.Cure.Greater)]    // a lethal poison: 25%
    public void TheCureIsTheWeakestCertainOneElseTheBest(int level, bool lesser, bool regular, bool greater, AutoUseService.Cure expected) =>
        Assert.Equal(expected, AutoUseService.Choose(level, lesser, regular, greater));

    [Theory]
    [InlineData(3, true, false, false)]    // a lesser cure cannot touch a deadly poison
    [InlineData(4, true, true, false)]     // nor can a regular one a lethal poison
    [InlineData(0, false, false, false)]
    public void NoCureThatCouldWorkMeansNone(int level, bool lesser, bool regular, bool greater) =>
        Assert.Null(AutoUseService.Choose(level, lesser, regular, greater));

    [Fact]
    public void TheChancesAreTheEraTable()
    {
        Assert.Equal(75, AutoUseService.ChanceOf(Lesser, 0));
        Assert.Equal(15, AutoUseService.ChanceOf(Lesser, 2));
        Assert.Equal(0, AutoUseService.ChanceOf(Lesser, 3));
        Assert.Equal(100, AutoUseService.ChanceOf(Regular, 0));
        Assert.Equal(15, AutoUseService.ChanceOf(Regular, 3));
        Assert.Equal(100, AutoUseService.ChanceOf(Greater, 2));
        Assert.Equal(75, AutoUseService.ChanceOf(Greater, 3));
        Assert.Equal(25, AutoUseService.ChanceOf(Greater, 4));
        Assert.Equal(0, AutoUseService.ChanceOf(Greater, 9));
    }

    [Fact]
    public void ReplyBytes()
    {
        var none = AutoUseService.Reply(null, 0);
        var one = AutoUseService.Reply(0x40001234u, 75);

        Assert.Equal(new byte[] { 0xBF, 0, 6, 0, 0xAA, 0 }, none);
        Assert.Equal(new byte[] { 0xBF, 0, 11, 0, 0xAA, 1, 0x40, 0x00, 0x12, 0x34, 75 }, one);
    }

    [Fact]
    public void TheMaskCarriesTheFlag()
    {
        Assert.Equal(MenuBarService.ShardBar | MenuBarService.About | MenuBarService.AutoUse, MenuBarService.MaskFor(new DeferredFeatureFlags { MenuBar = true, AutoUse = true }));
        Assert.Equal(0, MenuBarService.MaskFor(new DeferredFeatureFlags { AutoUse = true }) & MenuBarService.AutoUse);
    }

    [Fact]
    public void TheFlagIsOnSinceTheOwnerActivatedIt()
    {
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            System.IO.File.ReadAllText(System.IO.Path.Combine(System.AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        // activated 2026-10-13 on the owner's explicit "Commit, activate"
        Assert.True(rules.FeatureFlags.AutoUse);
    }
}
