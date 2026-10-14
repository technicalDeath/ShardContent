using BritanniaRenaissance.Content;
using Xunit;
using static BritanniaRenaissance.Content.AutoPickupService;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Auto-pickup of ammunition and reagents (docs/Ammo-Reagent-Auto-Pickup-Plan.md).</summary>
public class AutoPickupTests
{
    [Theory]
    [InlineData(Kind.Arrow, 30, 0, 0, 0, true)]
    [InlineData(Kind.Bolt, 30, 0, 0, 0, true)]
    [InlineData(Kind.Arrow, 29.9, 100, 100, 100, false)]   // casters do not collect arrows
    [InlineData(Kind.Bolt, 29.9, 100, 100, 100, false)]
    [InlineData(Kind.Reagent, 100, 0, 0, 0, false)]             // archers do not collect reagents
    [InlineData(Kind.Reagent, 0, 30, 0, 0, true)]
    [InlineData(Kind.Reagent, 0, 0, 30, 0, true)]
    [InlineData(Kind.Reagent, 0, 0, 0, 30, true)]
    [InlineData(Kind.Reagent, 0, 29, 29, 29, false)]
    [InlineData(Kind.None, 100, 100, 100, 100, false)]
    public void AKindIsUsedOnlyByTheSkillsThatUseIt(Kind kind, double archery, double magery, double alchemy, double inscription, bool expected) =>
        Assert.Equal(expected, Uses(kind, archery, magery, alchemy, inscription));

    [Theory]
    [InlineData(100, 5, 200, true)]
    [InlineData(165, 5, 200, true)]     // exactly the 170 share
    [InlineData(166, 5, 200, false)]
    [InlineData(0, 300, 200, false)]
    public void ThePileMustFitUnderTheComfortableShare(int carried, int pile, int max, bool expected) => Assert.Equal(expected, FitsInWeight(carried, pile, max));

    [Theory]
    [InlineData("Arrow", 4, "4 arrows")]
    [InlineData("Bolt", 1, "1 bolt")]
    [InlineData("BlackPearl", 5, "5 black pearl")]
    [InlineData("Garlic", 1, "1 garlic")]
    public void ThePickupLineNamesThePile(string type, int amount, string expected) => Assert.Equal(expected, PileName(type, amount));

    [Theory]
    [InlineData(Kind.Arrow, 1, true)]
    [InlineData(Kind.Arrow, 6, false)]
    [InlineData(Kind.Bolt, 2, true)]
    [InlineData(Kind.Bolt, 5, false)]
    [InlineData(Kind.Reagent, 4, true)]
    [InlineData(Kind.Reagent, 3, false)]
    [InlineData(Kind.None, 7, false)]
    [InlineData(Kind.Reagent, 0, false)]
    public void ThePlayersSwitchesChooseTheKinds(Kind kind, byte mask, bool expected) => Assert.Equal(expected, Wants(kind, mask));

    [Fact]
    public void AClientThatNeverSaysGetsAllThreeKinds()
    {
        Assert.Equal(7, AllKinds);
        Assert.True(Wants(Kind.Arrow, AllKinds) && Wants(Kind.Bolt, AllKinds) && Wants(Kind.Reagent, AllKinds));
    }

    [Fact]
    public void TheMenuMaskCarriesTheAutoPickupBitWithOrWithoutTheShardBar()
    {
        Assert.Equal(MenuBarService.AutoPickup, MenuBarService.MaskFor(new DeferredFeatureFlags { AutoPickup = true }));
        Assert.Equal(0, MenuBarService.MaskFor(new DeferredFeatureFlags()) & MenuBarService.AutoPickup);
    }

    [Fact]
    public void TheFlagShipsOffAndIsListedWhenOn()
    {
        Assert.False(new DeferredFeatureFlags().AutoPickup);
        Assert.Contains(nameof(DeferredFeatureFlags.AutoPickup), new DeferredFeatureFlags { AutoPickup = true }.EnabledNames());
    }
}
