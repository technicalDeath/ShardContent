using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CorpseLootExtensionTests
{
    private static TimeSpan S(int seconds) => TimeSpan.FromSeconds(seconds);

    [Fact]
    public void ACorpseAboutToVanishGetsOneMoreMinute() => Assert.Equal(S(90 + 60), CorpseLootExtension.Extend(true, S(90), false));

    [Fact]
    public void OnlyOnce() => Assert.Null(CorpseLootExtension.Extend(true, S(30), true));

    [Fact]
    public void NotWithTwoMinutesOrMoreLeft() => Assert.Null(CorpseLootExtension.Extend(true, S(120), false));

    [Fact]
    public void NotWhenTheNextStepOnlyTurnsItToBones() => Assert.Null(CorpseLootExtension.Extend(false, S(30), false));

    [Fact]
    public void TheFlagIsOffInTheClassDefault() => Assert.False(new DeferredFeatureFlags().CorpseLootExtension);
}
