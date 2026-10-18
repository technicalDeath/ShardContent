using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>A ghost in peace mode near a healer is reminded to use war mode (docs/Ghost-Healer-Reminder-Evidence.md).</summary>
public class GhostHealerReminderTests
{
    private static readonly DateTime Now = new(2026, 10, 16, 12, 0, 0);

    private static bool Remind(bool enabled = true, bool dead = true, bool warMode = false, bool healer = true, DateTime? last = null) =>
        GhostHealerReminderService.ShouldRemind(enabled, dead, warMode, healer, last, Now);

    [Fact]
    public void AGhostInPeaceModeNearAHealerIsReminded() => Assert.True(Remind());

    [Fact]
    public void AGhostInWarModeIsNotReminded() => Assert.False(Remind(warMode: true)); // the owner: "The warning should be if you're not in war mode"

    [Fact]
    public void TheLivingAGhostFarFromAHealerAndTheFlagOffAreLeftAlone()
    {
        Assert.False(Remind(dead: false));
        Assert.False(Remind(healer: false));
        Assert.False(Remind(enabled: false));
    }

    [Fact]
    public void TheReminderComesAtMostEveryThirtySeconds()
    {
        Assert.False(Remind(last: Now.AddSeconds(-10)));
        Assert.True(Remind(last: Now.AddSeconds(-30)));
    }

    [Fact]
    public void TheLineSaysWarModeAndToWalkUp()
    {
        Assert.Contains("Press Tab for war mode", GhostHealerReminderService.Text);
        Assert.Contains("walk up to the healer from a few steps away", GhostHealerReminderService.Text);
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().GhostHealerReminder);
}
