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
}
