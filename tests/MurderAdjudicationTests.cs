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
}
