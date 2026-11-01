using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class PetsKeepUpTests
{
    [Fact]
    public void PreAosAFollowingPetGetsTheRunOnFootPace() => Assert.Equal(0.2, PetsKeepUp.Pace(true, 0, 200), 6);

    [Fact]
    public void OffKeepsTheStockPace() => Assert.Equal(0, PetsKeepUp.Pace(false, 0, 200));

    [Fact]
    public void AnAosCapIsLeftAlone() => Assert.Equal(0.1, PetsKeepUp.Pace(true, 0.1, 200), 6);

    [Fact]
    public void NoRunDelayMeansNoCap() => Assert.Equal(0, PetsKeepUp.Pace(true, 0, 0));

    [Fact]
    public void TheFlagIsOffInTheClassDefault() => Assert.False(new DeferredFeatureFlags().PetsKeepUp);
}
