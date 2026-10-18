using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class FastSkillStartTests
{
    [Theory]
    [InlineData(0, 50, 100)]
    [InlineData(199, 50, 100)]
    [InlineData(200, 10, 50)]
    [InlineData(399, 10, 50)]
    public void TheBandFollowsTheOwnersNumbers(int baseTenths, int min, int max)
    {
        var band = FastSkillStart.BandFor(new FastSkillStartRules(), baseTenths);
        Assert.NotNull(band);
        Assert.Equal(min, band!.MinTenths);
        Assert.Equal(max, band.MaxTenths);
    }

    [Fact]
    public void FromFortyStockGainTakesOver() => Assert.Null(FastSkillStart.BandFor(new FastSkillStartRules(), 400));

    [Fact]
    public void TheDefaultBandsValidate()
    {
        var errors = new List<string>();
        FastSkillStart.Validate("fastHealing", new FastSkillStartRules(), errors);
        Assert.Empty(errors);
    }

    [Fact]
    public void ABandWithItsAmountsBackwardsIsRefused()
    {
        var errors = new List<string>();
        FastSkillStart.Validate("fastHealing", new FastSkillStartRules { Bands = [new FastSkillStartBand { BelowTenths = 200, MinTenths = 6, MaxTenths = 2 }] }, errors);
        Assert.NotEmpty(errors);
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().FastHealing);

    [Theory]
    [InlineData(null, 1000L, true)]
    [InlineData(0L, 599_999L, false)]
    [InlineData(0L, 600_000L, true)]
    [InlineData(long.MaxValue - 100, long.MinValue + 700_000, true)] // the tick count wrapped
    public void TheMeditationTipWaitsTenMinutes(long? last, long now, bool due) =>
        Assert.Equal(due, MeditationTipService.Due(last, now, MeditationTipService.CooldownMilliseconds));

    [Fact]
    public void TheMeditationFlagsAreOffUntilTheOwnerSaysActivate()
    {
        Assert.False(new DeferredFeatureFlags().FastMeditation);
        Assert.False(new DeferredFeatureFlags().MeditationTip);
    }
}
