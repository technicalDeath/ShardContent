using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class KnockedOutTests
{
    [Theory]
    [InlineData(false, true, true, false, false, "feature-disabled")]
    [InlineData(true, false, true, false, false, "not-player")]
    [InlineData(true, true, false, false, false, "not-ordinary-blue")]
    [InlineData(true, true, true, true, false, "hot-zone-resolution-deferred")]
    [InlineData(true, true, true, false, true, "ordinary-blue-safe-world")]
    public void ClassificationKeepsHotZoneResolutionDeferred(
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
    public void DurationMatchesAlphaTwoPolicy()
    {
        Assert.Equal(TimeSpan.FromSeconds(90), KnockedOutService.Duration);
    }

    [Theory]
    [InlineData(false, false, true, true, false, "feature-disabled")]
    [InlineData(true, false, false, true, false, "actor-not-criminal-or-murderer")]
    [InlineData(true, true, true, false, true, "hot-zone-red-looting")]
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
}
