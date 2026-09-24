using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class MurderAdjudicationTests
{
    [Theory]
    [InlineData(false, false, false, true, false, true, "ordinary-blue-victim")]
    [InlineData(true, false, false, true, false, false, "victim-not-ordinary-blue")]
    [InlineData(false, true, false, true, false, false, "victim-not-ordinary-blue")]
    [InlineData(false, false, true, true, false, false, "intent-classified-encounter")]
    [InlineData(false, false, false, false, false, false, "killer-not-player")]
    [InlineData(false, false, false, true, true, false, "self-damage")]
    public void DeathClassificationIsIndependentOfAttackLegality(
        bool victimIsCriminal,
        bool victimIsMurderer,
        bool victimWasIntentClassified,
        bool killerIsPlayer,
        bool killerIsVictim,
        bool qualifies,
        string reason)
    {
        var decision = MurderAdjudicationService.ClassifyDeath(
            victimIsCriminal,
            victimIsMurderer,
            victimWasIntentClassified,
            killerIsPlayer,
            killerIsVictim
        );

        Assert.Equal(qualifies, decision.Qualifies);
        Assert.Equal(reason, decision.Reason);
    }

    [Fact]
    public void RedTimerAccumulatesFromTheLaterOfNowOrExistingExpiry()
    {
        var now = new DateTime(2026, 9, 23, 12, 0, 0, DateTimeKind.Utc);

        Assert.Equal(
            now.AddHours(24),
            MurderAdjudicationService.ExtendRedUntilUtc(now, now.AddHours(-1))
        );

        Assert.Equal(
            now.AddHours(36),
            MurderAdjudicationService.ExtendRedUntilUtc(now, now.AddHours(12))
        );
    }

    [Theory]
    [InlineData(false, true, true, false)]
    [InlineData(true, false, true, false)]
    [InlineData(true, true, false, false)]
    [InlineData(true, true, true, true)]
    public void AutomaticRedSourceHonorsFeatureGateAndExpiry(
        bool enabled,
        bool hasExpiry,
        bool expiryIsFuture,
        bool expected
    )
    {
        var now = new DateTime(2026, 9, 24, 0, 0, 0, DateTimeKind.Utc);
        DateTime? expiry = hasExpiry ? now.AddHours(expiryIsFuture ? 1 : -1) : null;

        Assert.Equal(expected, MurderAdjudicationService.IsAutomaticRedAt(enabled, expiry, now));
    }

    [Theory]
    [InlineData(false, false, MigrationState.Neither)]
    [InlineData(true, false, MigrationState.LegacyOnly)]
    [InlineData(false, true, MigrationState.CustomOnly)]
    [InlineData(true, true, MigrationState.Overlapping)]
    public void MigrationAuditSeparatesLegacyAndCustomRedSources(
        bool hasLegacyThreshold,
        bool hasCustomRed,
        MigrationState expected
    )
    {
        Assert.Equal(expected, MurderAdjudicationService.ClassifyMigrationState(hasLegacyThreshold, hasCustomRed));
    }

    [Theory]
    [InlineData("2026-09-24T00:00:00.0000000Z", true)]
    [InlineData("2026-09-23T20:00:00-04:00", true)]
    [InlineData("2026-09-24T00:00:01.0000000Z", false)]
    [InlineData(null, false)]
    public void DeathMarkerDeduplicationUsesUtcInstant(
        string? marker,
        bool expected
    )
    {
        var death = new DateTime(2026, 9, 24, 0, 0, 0, DateTimeKind.Utc);

        Assert.Equal(expected, MurderAdjudicationService.DeathMarkerMatches(marker, death));
    }
}
