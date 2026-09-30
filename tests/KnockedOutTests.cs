using Server;
using Server.Misc;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class KnockedOutTests
{
    [Theory]
    [InlineData(false, true, true, false, false, "feature-disabled")]
    [InlineData(true, false, true, false, false, "not-player")]
    [InlineData(true, true, false, false, false, "not-ordinary-blue")]
    [InlineData(true, true, true, true, true, "ordinary-blue-hot-zone")]
    [InlineData(true, true, true, false, true, "ordinary-blue-safe-world")]
    public void ClassificationKeepsBlueKnockoutInHotZones(
        bool featureEnabled,
        bool player,
        bool ordinaryBlue,
        bool hotZone,
        bool qualifies,
        string reason)
    {
        var decision = KnockedOutService.Classify(featureEnabled, player, ordinaryBlue, hotZone);

        Assert.Equal(qualifies, decision.Qualifies);
        Assert.Equal(reason, decision.Reason);
    }

    [Fact]
    public void ExecutionLeavesNoLawfulFightRecordSoARepeatKillStillCountsAsMurder()
    {
        Server.Timer.Init(Core.TickCount);
        Map.Maps[0x7F] ??= new Map(0x7F, 0x7F, 0x7F, Map.SectorSize, Map.SectorSize, 1, "Internal", MapRules.Internal);

        var executor = new Mobile((Serial)0x7A000001);
        var victim = new Mobile((Serial)0x7A000002);

        // Combat leaves a criminal record first; Execute then adds a second, non-criminal one.
        victim.Aggressors.Add(AggressorInfo.Create(executor, victim, true));
        executor.Aggressed.Add(AggressorInfo.Create(executor, victim, true));
        victim.Aggressors.Clear();
        KnockedOutService.RecordExecutorAsAggressor(executor, victim);

        // The record the execution needs for the corpse's aggressor list makes the victim a non-innocent
        // target for the executor (a lawful fight), which would make a later attack not a reportable murder.
        Assert.True(NotorietyHandlers.CheckAggressed(executor.Aggressed, victim));

        KnockedOutService.ClearExecutionAggression(executor, victim);

        Assert.False(NotorietyHandlers.CheckAggressed(executor.Aggressed, victim));
        Assert.Empty(executor.Aggressed);
        Assert.Empty(victim.Aggressors);
    }

    [Fact]
    public void DurationMatchesAlphaTwoPolicy()
    {
        Assert.Equal(TimeSpan.FromSeconds(90), KnockedOutService.Duration);
    }

    [Theory]
    [InlineData(false, false, false)]
    [InlineData(false, true, false)]
    [InlineData(true, false, false)]
    [InlineData(true, true, true)]
    public void ActionLockoutAppliesOnlyToActiveKnockedOutPlayers(
        bool featureEnabled,
        bool knockedOut,
        bool expectedBlocked
    )
    {
        Assert.Equal(expectedBlocked, KnockedOutService.ShouldBlockActions(featureEnabled, knockedOut));
    }

    [Theory]
    [InlineData(false, true, true, false)]
    [InlineData(true, false, true, false)]
    [InlineData(true, true, false, true)]
    [InlineData(true, true, true, false)]
    public void StaffBypassKnockedOutActionLockout(
        bool featureEnabled,
        bool knockedOut,
        bool staff,
        bool expectedBlocked
    )
    {
        Assert.Equal(expectedBlocked, KnockedOutService.ShouldBlockActions(featureEnabled, knockedOut, staff));
    }

    [Theory]
    [InlineData(false, true, true, false, true, true, false, "feature-disabled")]
    [InlineData(true, true, true, false, false, true, false, "damage-not-attributable-to-player")]
    [InlineData(true, true, true, false, true, false, false, "missing-active-encounter")]
    [InlineData(true, true, true, false, true, true, true, "ordinary-blue-player-encounter")]
    [InlineData(true, true, true, true, false, false, false, "damage-not-attributable-to-player")]
    [InlineData(true, true, true, true, true, false, true, "ordinary-blue-hot-zone-player-damage")]
    public void LethalDamageRequiresAttributablePlayerEncounter(
        bool featureEnabled,
        bool player,
        bool ordinaryBlue,
        bool hotZone,
        bool attributablePlayerDamage,
        bool activeEncounter,
        bool qualifies,
        string reason)
    {
        var decision = KnockedOutService.ClassifyDamage(
            featureEnabled,
            player,
            ordinaryBlue,
            hotZone,
            attributablePlayerDamage,
            activeEncounter
        );

        Assert.Equal(qualifies, decision.Qualifies);
        Assert.Equal(reason, decision.Reason);
    }

    [Theory]
    [InlineData(false, false, true, true, false, "feature-disabled")]
    [InlineData(true, false, false, true, false, "actor-not-criminal-or-murderer")]
    [InlineData(true, true, true, false, true, "hot-zone-red-looting")]
    [InlineData(true, true, false, false, true, "hot-zone-blue-looting")]
    [InlineData(true, false, true, true, true, "recorded-target-rights")]
    [InlineData(true, false, true, false, false, "missing-target-rights")]
    public void LootRequiresRedIdentityAndRecordedRightsOutsideHotZones(
        bool featureEnabled,
        bool hotZone,
        bool actorIsCriminalOrMurderer,
        bool recordedTargetRights,
        bool qualifies,
        string reason)
    {
        var decision = KnockedOutService.ClassifyLoot(
            featureEnabled,
            hotZone,
            actorIsCriminalOrMurderer,
            recordedTargetRights
        );

        Assert.Equal(qualifies, decision.Qualifies);
        Assert.Equal(reason, decision.Reason);
    }

    [Theory]
    [InlineData(null, 5u, true)]
    [InlineData("none", 5u, false)]
    [InlineData("7", 5u, false)]
    [InlineData("7,5", 5u, true)]
    [InlineData("5", 5u, true)]
    [InlineData("55", 5u, false)]
    public void ExecutionCountsAsMurderOnlyForReportableAttackers(string? reportable, uint executor, bool counts)
    {
        Assert.Equal(counts, KnockedOutService.ExecutionCountsAsMurder(reportable, executor));
    }

    [Theory]
    [InlineData(false, true, true, false, "feature-disabled")]
    [InlineData(true, false, true, false, "actor-not-criminal-or-murderer")]
    [InlineData(true, false, false, false, "actor-not-criminal-or-murderer")]
    [InlineData(true, true, false, false, "missing-damage-record-rights")]
    [InlineData(true, true, true, true, "damage-record-rights")]
    public void ExecutionRequiresRedActorWithDamageRecordRights(
        bool featureEnabled,
        bool actorIsCriminalOrMurderer,
        bool damageRecordRights,
        bool qualifies,
        string reason)
    {
        var decision = KnockedOutService.ClassifyExecution(
            featureEnabled,
            actorIsCriminalOrMurderer,
            damageRecordRights
        );

        Assert.Equal(qualifies, decision.Qualifies);
        Assert.Equal(reason, decision.Reason);
    }
}
