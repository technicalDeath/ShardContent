using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class TheftProtectionTests
{
    [Theory]
    [InlineData(-1, 0.0)]
    [InlineData(0, 0.0)]
    [InlineData(1, 0.25)]
    [InlineData(2, 0.50)]
    [InlineData(3, 1.0)]
    [InlineData(20, 1.0)]
    public void DetectionEscalatesPerThiefAccount(int successes, double expected)
    {
        Assert.Equal(expected, TheftProtectionService.AdditionalDetectionChance(successes));
    }

    [Fact]
    public void ProtectionWindowUsesUtcExpiry()
    {
        var now = new DateTime(2026, 9, 23, 12, 0, 0, DateTimeKind.Utc);

        Assert.True(TheftProtectionService.IsProtectionWindowActive(now, now.AddSeconds(1)));
        Assert.False(TheftProtectionService.IsProtectionWindowActive(now, now));
        Assert.False(TheftProtectionService.IsProtectionWindowActive(now, now.AddSeconds(-1)));
    }

    [Fact]
    public void LootProtectionUsesTheApprovedTenMinuteWindow()
    {
        Assert.Equal(TimeSpan.FromMinutes(10), TheftProtectionService.LootProtectionDuration);
    }

    [Theory]
    [InlineData(null, false)]
    [InlineData("", false)]
    [InlineData("0", false)]
    [InlineData("1", true)]
    [InlineData("2", false)]
    public void LootProtectionEntitlementVersionIsIdempotent(string? value, bool expected)
    {
        Assert.Equal(expected, TheftProtectionService.IsLootProtectionEntitlementCurrent(value));
    }
}
