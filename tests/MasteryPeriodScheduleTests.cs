using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class MasteryPeriodScheduleTests
{
    [Theory]
    [InlineData("2026-09-23T00:00:00Z", 0)]
    [InlineData("2026-09-23T03:59:59Z", 0)]
    [InlineData("2026-09-23T04:00:00Z", 1)]
    [InlineData("2026-09-23T20:00:00Z", 5)]
    public void PeriodsAreAlignedToFourHourUtcBoundaries(string timestamp, long expectedOffset)
    {
        var instant = DateTime.Parse(timestamp, null, System.Globalization.DateTimeStyles.RoundtripKind);
        var basePeriod = MasteryProgression.GetPeriodId(DateTime.UnixEpoch);

        Assert.Equal(basePeriod + expectedOffset +
                     (instant.Date - DateTime.UnixEpoch.Date).Days * 6,
            MasteryProgression.GetPeriodId(instant));
    }

    [Fact]
    public void NextBoundaryIsSharedAndUtcBased()
    {
        var now = new DateTime(2026, 9, 23, 3, 59, 59, DateTimeKind.Utc);

        Assert.Equal(new DateTime(2026, 9, 23, 4, 0, 0, DateTimeKind.Utc), MasteryProgression.GetNextBoundary(now));
        Assert.Equal(4, (int)MasteryProgression.PeriodLength.TotalHours);
        Assert.Equal(1, MasteryProgression.AwardTenths);
        Assert.Equal(6, MasteryProgression.PendingCapTenths);
    }

    [Fact]
    public void MasteryPathUsesFiftyTenthsAcrossTwoHundredHours()
    {
        var periods = (int)(TimeSpan.FromHours(200).Ticks / MasteryProgression.PeriodLength.Ticks);

        Assert.Equal(50, periods);
        Assert.Equal(0.1, MasteryProgression.AwardTenths / 10.0);
        Assert.Equal(0.6, MasteryProgression.PendingCapTenths / 10.0);
    }
}
