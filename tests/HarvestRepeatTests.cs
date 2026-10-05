using Server;
using Server.Engines.Harvest;
using Xunit;
using Snapshot = BritanniaRenaissance.Content.HarvestRepeatService.Snapshot;
using StopReason = BritanniaRenaissance.Content.HarvestRepeatService.StopReason;

namespace BritanniaRenaissance.Content.Tests;

public class HarvestRepeatTests
{
    private static readonly Snapshot Start = new(100, 200, 300, new Point3D(10, 20, 0), null, 50);

    private static StopReason Check(
        Snapshot? now = null, bool alive = true, bool connected = true, bool casting = false,
        bool warMode = false, bool disturbed = false, bool cursorOpen = false) =>
        HarvestRepeatService.CheckCancel(Start, now ?? Start, alive, connected, casting, warMode, disturbed, cursorOpen);

    [Fact]
    public void NothingChangedKeepsLooping() => Assert.Equal(StopReason.None, Check());

    [Fact]
    public void WalkingEndsTheLoopEvenIfThePlayerStepsBack()
    {
        Assert.Equal(StopReason.Moved, Check(Start with { LastMoveTime = 101 }));
        Assert.Equal(StopReason.Moved, Check(Start with { Location = new Point3D(11, 20, 0) }));
    }

    [Fact]
    public void UsingAnotherSkillEndsTheLoop() =>
        Assert.Equal(StopReason.UsedSkill, Check(Start with { NextSkillTime = 201 }));

    [Fact]
    public void CastingEndsTheLoopWhetherInProgressOrFinished()
    {
        Assert.Equal(StopReason.Cast, Check(casting: true));
        Assert.Equal(StopReason.Cast, Check(Start with { NextSpellTime = 301 }));
    }

    [Fact]
    public void WarModeAndBeingDisturbedEndTheLoop()
    {
        Assert.Equal(StopReason.WarMode, Check(warMode: true));
        Assert.Equal(StopReason.Disturbed, Check(disturbed: true));
    }

    [Fact]
    public void LosingHitPointsEndsTheLoopButRecoveringDoesNot()
    {
        Assert.Equal(StopReason.Disturbed, Check(Start with { Hits = 49 }));
        Assert.Equal(StopReason.None, Check(Start with { Hits = 80 }));
    }

    [Fact]
    public void OpeningAFreshHarvestCursorEndsTheLoop() =>
        Assert.Equal(StopReason.Retargeting, Check(cursorOpen: true));

    [Fact]
    public void DeathAndDisconnectWinOverEverythingElse()
    {
        Assert.Equal(StopReason.Dead, Check(Start with { LastMoveTime = 1 }, alive: false));
        Assert.Equal(StopReason.Disconnected, Check(Start with { LastMoveTime = 1 }, connected: false));
    }

    [Theory]
    [InlineData(HarvestStage.Harvested, true, true)]
    [InlineData(HarvestStage.Failed, true, true)]      // a missed skill check repeats, as a manual player would
    [InlineData(HarvestStage.PackFull, true, false)]   // stock loses the item; stop rather than lose more
    [InlineData(HarvestStage.Harvested, false, false)] // the tool broke and the player was already told
    [InlineData(HarvestStage.Started, true, false)]
    [InlineData(HarvestStage.Concurrent, true, false)]
    public void OnlyAFinishedAttemptWithAUsableToolRepeats(HarvestStage stage, bool toolUsable, bool expected) =>
        Assert.Equal(expected, HarvestRepeatService.StageAllowsRepeat(stage, toolUsable));

    [Fact]
    public void FeatureFlagDefaultsOffAndIsListedWhenOn()
    {
        var flags = new DeferredFeatureFlags();

        Assert.False(flags.HarvestAutoRepeat);
        Assert.DoesNotContain(nameof(DeferredFeatureFlags.HarvestAutoRepeat), flags.EnabledNames());

        flags.HarvestAutoRepeat = true;
        Assert.Contains(nameof(DeferredFeatureFlags.HarvestAutoRepeat), flags.EnabledNames());
        Assert.DoesNotContain("none", flags.EnabledNames());
    }

    [Fact]
    public void SourceConfigurationEnablesTheFlag()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        Assert.True(File.Exists(path), path);

        using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(path));
        Assert.True(doc.RootElement.GetProperty("featureFlags").GetProperty("harvestAutoRepeat").GetBoolean());
    }
}
