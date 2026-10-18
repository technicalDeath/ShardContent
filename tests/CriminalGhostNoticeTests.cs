using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>A criminal ghost is told how long to wait, and when the flag ends (docs/Criminal-Ghost-Notice-Evidence.md).</summary>
public class CriminalGhostNoticeTests
{
    [Theory]
    [InlineData(100, "1 minute 40 seconds")]
    [InlineData(95, "1 minute 40 seconds")] // rounded up: never promises too soon
    [InlineData(120, "2 minutes")]
    [InlineData(30, "30 seconds")]
    [InlineData(3, "10 seconds")]
    [InlineData(-5, "10 seconds")]          // the timer is about to fire
    public void TheTimeLeftReadsPlainly(int seconds, string text) => Assert.Equal(text, CriminalGhostNotice.Remaining(TimeSpan.FromSeconds(seconds)));

    [Fact]
    public void TheWaitLineSaysWhenToComeBack() =>
        Assert.Equal(
            "You will be a criminal for about 1 minute 40 seconds more. Come back then, and a healer will bring you back.",
            CriminalGhostNotice.WaitText(TimeSpan.FromSeconds(100))
        );

    [Fact]
    public void TheTimeLeftCountsFromTheLastCriminalAct()
    {
        var since = new DateTime(2026, 10, 17, 12, 0, 0);
        Assert.Equal(TimeSpan.FromSeconds(90), CriminalGhostNotice.Left(since, since.AddSeconds(30), TimeSpan.FromMinutes(2)));
    }

    [Fact]
    public void TheEndLineSaysAHealerWillHelpNow() => Assert.Contains("A healer will bring you back now", CriminalGhostNotice.Ended);

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().CriminalGhostNotice);
}
