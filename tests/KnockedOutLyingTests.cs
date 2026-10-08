using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// A Knocked Out player is drawn lying on the ground (owner ruling 2026-10-07): the server sets a packet-flag bit the shard's client reads,
/// and a rider is knocked off first so the mount is not drawn under a lying human.
/// </summary>
public sealed class KnockedOutLyingTests
{
    // The bits the stock protocol already uses on a mobile: frozen, female, poisoned/flying, yellow bar, ignore mobiles, war mode, hidden.
    private const int StockMobileFlagBits = 0x01 | 0x02 | 0x04 | 0x08 | 0x10 | 0x40 | 0x80;

    [Fact]
    public void TheLyingBitIsOneTheProtocolLeavesFreeForMobiles()
    {
        Assert.Equal(0x20, KnockedOutService.LyingFlag);
        Assert.Equal(0, KnockedOutService.LyingFlag & StockMobileFlagBits);
    }

    [Fact]
    public void AnOlderRecoveryTimerDoesNotEndANewerKnockOut()
    {
        var now = new DateTime(2026, 10, 7, 20, 0, 0, DateTimeKind.Utc);

        // A staff recovery, then a new Knocked Out 20 s from now: the first timer fires into it.
        Assert.True(KnockedOutService.SupersededRecovery(now.AddSeconds(20), now));

        // The state's own timer, firing at its end, still recovers; so does one that finds the state gone.
        Assert.False(KnockedOutService.SupersededRecovery(now.AddSeconds(0.2), now));
        Assert.False(KnockedOutService.SupersededRecovery(now.AddSeconds(-1), now));
        Assert.False(KnockedOutService.SupersededRecovery(null, now));
    }

    [Fact]
    public void ARiderCannotRemountForTheRestOfTheKnockOutButAtLeastASecond()
    {
        var now = new DateTime(2026, 10, 7, 20, 0, 0, DateTimeKind.Utc);

        Assert.Equal(TimeSpan.FromSeconds(30), KnockedOutService.MountBlockDuration(now.AddSeconds(30), now));
        Assert.Equal(TimeSpan.FromSeconds(12), KnockedOutService.MountBlockDuration(now.AddSeconds(12), now));
        Assert.Equal(TimeSpan.FromSeconds(1), KnockedOutService.MountBlockDuration(now.AddSeconds(0.4), now));
        Assert.Equal(TimeSpan.FromSeconds(1), KnockedOutService.MountBlockDuration(now.AddSeconds(-5), now));
        Assert.Equal(TimeSpan.FromSeconds(1), KnockedOutService.MountBlockDuration(null, now));
    }
}
