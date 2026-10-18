using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>A player who dies is told how long the corpse lasts (docs/Corpse-Timer-Notice-Evidence.md).</summary>
public class CorpseTimerNoticeTests
{
    [Fact]
    public void TheLineGivesBothStagesInMinutes() =>
        Assert.Equal(
            "Your corpse will turn to bones in 7 minutes, and the bones and everything in them will be gone 7 minutes after that.",
            CorpseTimerNoticeService.Text(TimeSpan.FromMinutes(7), TimeSpan.FromMinutes(7))
        );

    [Fact]
    public void OneMinuteIsSingular() => Assert.Contains("in 1 minute,", CorpseTimerNoticeService.Text(TimeSpan.FromSeconds(50), TimeSpan.FromMinutes(7)));

    [Fact]
    public void TheEngineTimesAreTheStockSevenAndSeven()
    {
        // the line quotes these through Corpse.DefaultDecayTime and Corpse.BoneDecayTime, so it follows any change to them
        Assert.Equal(TimeSpan.FromMinutes(7), Corpse.DefaultDecayTime);
        Assert.Equal(TimeSpan.FromMinutes(7), Corpse.BoneDecayTime);
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().CorpseTimerNotice);
}
