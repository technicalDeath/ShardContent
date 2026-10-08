using Server;
using Server.Items;
using Server.SkillHandlers;
using Xunit;
using Kind = BritanniaRenaissance.Content.ActionRepeatService.Kind;
using Snapshot = BritanniaRenaissance.Content.HarvestRepeatService.Snapshot;
using StopReason = BritanniaRenaissance.Content.HarvestRepeatService.StopReason;

namespace BritanniaRenaissance.Content.Tests;

public class ActionRepeatTests
{
    private static readonly Snapshot Start = new(100, 200, 300, new Point3D(10, 20, 0), null, 50);

    private static StopReason Cancel(Kind kind, Snapshot now) =>
        ActionRepeatService.Cancel(kind, Start, now, true, true, false, false, false, false);

    [Theory]
    [InlineData(TameResult.Failed, true)]   // a plain miss: try again, as a manual tamer would
    [InlineData(TameResult.Tamed, false)]
    [InlineData(TameResult.Aborted, false)] // too far, no path, angered, dead, someone else's pet: the stock message ends it
    public void TamingRepeatsOnlyAfterAPlainMiss(TameResult result, bool expected) =>
        Assert.Equal(expected, ActionRepeatService.TamingContinues(result));

    [Theory]
    [InlineData(LockpickResult.Failed, true, true, true)]
    [InlineData(LockpickResult.Failed, false, true, false)]  // the last pick broke
    [InlineData(LockpickResult.Failed, true, false, false)]  // someone else opened it
    [InlineData(LockpickResult.Picked, true, true, false)]
    [InlineData(LockpickResult.OutOfRange, true, true, false)]
    [InlineData(LockpickResult.CannotPick, true, true, false)]
    [InlineData(LockpickResult.NoSkill, true, true, false)]
    public void LockpickingRepeatsWhilePicksAndLockRemain(LockpickResult result, bool pickUsable, bool locked, bool expected) =>
        Assert.Equal(expected, ActionRepeatService.LockpickingContinues(result, pickUsable, locked));

    [Theory]
    [InlineData(true, false, true)]
    [InlineData(false, false, false)] // the stack is gone
    [InlineData(true, true, false)]   // someone else took the wheel
    public void SpinningRepeatsWhileMaterialRemainsAndTheWheelIsFree(bool left, bool busy, bool expected) =>
        Assert.Equal(expected, ActionRepeatService.SpinningContinues(left, busy));

    [Fact]
    public void CookingRepeatsWhileFoodRemainsWhetherOrNotTheLastOneBurned()
    {
        Assert.True(ActionRepeatService.CookingContinues(true));
        Assert.False(ActionRepeatService.CookingContinues(false));
    }

    [Fact]
    public void TamingIgnoresTheSkillTimerBecauseTheAttemptResetsItItself()
    {
        var now = Start with { NextSkillTime = 999 };

        Assert.Equal(StopReason.None, Cancel(Kind.Taming, now));
        Assert.Equal(StopReason.UsedSkill, Cancel(Kind.Lockpicking, now));
        Assert.Equal(StopReason.UsedSkill, Cancel(Kind.Spinning, now));
        Assert.Equal(StopReason.UsedSkill, Cancel(Kind.Cooking, now));
    }

    [Fact]
    public void TheOtherGatheringCancelsStillApplyToTaming()
    {
        Assert.Equal(StopReason.Moved, Cancel(Kind.Taming, Start with { LastMoveTime = 101 }));
        Assert.Equal(StopReason.Cast, Cancel(Kind.Taming, Start with { NextSpellTime = 301 }));
        Assert.Equal(StopReason.Disturbed, Cancel(Kind.Taming, Start with { Hits = 40 }));
        Assert.Equal(StopReason.Retargeting, ActionRepeatService.Cancel(Kind.Taming, Start, Start, true, true, false, false, false, true));
    }

    [Fact]
    public void FeatureFlagDefaultsOffAndIsListedWhenOn()
    {
        var flags = new DeferredFeatureFlags();

        Assert.False(flags.ActionAutoRepeat);
        Assert.DoesNotContain(nameof(DeferredFeatureFlags.ActionAutoRepeat), flags.EnabledNames());

        flags.ActionAutoRepeat = true;
        Assert.Contains(nameof(DeferredFeatureFlags.ActionAutoRepeat), flags.EnabledNames());
        Assert.DoesNotContain("none", flags.EnabledNames());
    }

    [Fact]
    public void SourceConfigurationEnablesTheFlag()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        Assert.True(File.Exists(path), path);

        using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(path));
        Assert.True(doc.RootElement.GetProperty("featureFlags").GetProperty("actionAutoRepeat").GetBoolean());
    }
}
