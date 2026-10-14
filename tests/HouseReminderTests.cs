using BritanniaRenaissance.Content;
using Xunit;
using static BritanniaRenaissance.Content.HouseReminderService;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>House lockdown reminder (docs/House-Lockdown-Reminder-Plan.md).</summary>
public class HouseReminderTests
{
    private static readonly DateTime Now = new(2026, 10, 14, 12, 0, 0, DateTimeKind.Utc);

    [Theory]
    [InlineData(true, true, true, false, true)]
    [InlineData(false, true, true, false, false)]   // flag off
    [InlineData(true, false, true, false, false)]   // staff
    [InlineData(true, true, false, false, false)]   // not the owner or a co-owner
    [InlineData(true, true, true, true, false)]     // [HouseReminder off
    public void OnlyAnOwnerWhoHasNotSwitchedItOffIsWatched(bool enabled, bool ordinary, bool owner, bool off, bool expected) =>
        Assert.Equal(expected, ShouldWatch(enabled, ordinary, owner, off));

    [Fact]
    public void ALooseItemIsReminded()
    {
        Assert.True(ShouldRemind(true, true, null, Now));
    }

    [Fact]
    public void AnItemLockedDownOrPickedUpIsNotReminded()
    {
        Assert.False(ShouldRemind(false, true, null, Now));
    }

    [Fact]
    public void AnItemThatLeftTheHouseIsNotReminded()
    {
        Assert.False(ShouldRemind(true, false, null, Now));
    }

    [Theory]
    [InlineData(23, false)]
    [InlineData(24, true)]
    [InlineData(48, true)]
    public void TheReminderComesAtMostOnceADay(int hoursAgo, bool expected) =>
        Assert.Equal(expected, ShouldRemind(true, true, Now.AddHours(-hoursAgo), Now));

    [Fact]
    public void TheTextNamesTheCommandsAndNotTheOldName()
    {
        Assert.Contains("lock this down", Text);
        Assert.Contains("[HouseReminder off", Text);
        Assert.DoesNotContain("Britannia Renaissance", Text, StringComparison.OrdinalIgnoreCase);
        Assert.Equal(TimeSpan.FromSeconds(10), Wait);
    }

    [Fact]
    public void TheFlagShipsOffAndIsListedWhenOn()
    {
        Assert.False(new DeferredFeatureFlags().HouseReminder);
        Assert.Contains(nameof(DeferredFeatureFlags.HouseReminder), new DeferredFeatureFlags { HouseReminder = true }.EnabledNames());
    }
}
