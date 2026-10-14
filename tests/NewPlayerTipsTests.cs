using BritanniaRenaissance.Content;
using Xunit;
using static BritanniaRenaissance.Content.NewPlayerTipsService;

namespace BritanniaRenaissance.Content.Tests;

public class NewPlayerTipsTests
{
    [Theory]
    [InlineData(30, 100, true, true, true)]
    [InlineData(33, 100, true, true, true)]
    [InlineData(34, 100, true, true, false)]   // a third or more is not "badly hurt"
    [InlineData(30, 100, false, true, false)]  // not in a fight
    [InlineData(30, 100, true, false, false)]  // no bandage to point at
    [InlineData(0, 100, true, true, false)]    // dead
    [InlineData(10, 0, true, true, false)]
    public void BadlyHurtNeedsAFightABandageAndUnderAThird(int hits, int max, bool combat, bool bandage, bool expected) =>
        Assert.Equal(expected, IsBadlyHurt(hits, max, combat, bandage));

    [Theory]
    [InlineData(true, true, false, true)]
    [InlineData(true, false, false, false)]   // not fighting
    [InlineData(true, true, true, false)]     // still has ammunition
    [InlineData(false, true, false, false)]   // no ranged weapon
    public void OutOfAmmunitionNeedsARangedWeaponInWarModeAndNoAmmunition(bool ranged, bool war, bool ammo, bool expected) =>
        Assert.Equal(expected, IsOutOfAmmunition(ranged, war, ammo));

    [Theory]
    [InlineData(true, true, false, false, true)]
    [InlineData(false, true, false, false, false)]  // flag off
    [InlineData(true, false, false, false, false)]  // staff
    [InlineData(true, true, true, false, false)]    // [Tips off
    [InlineData(true, true, false, true, false)]    // already said
    public void ATipIsSaidOnceToAnOrdinaryPlayerWhoHasNotSwitchedThemOff(bool enabled, bool ordinary, bool off, bool shown, bool expected) =>
        Assert.Equal(expected, ShouldShow(enabled, ordinary, off, shown));

    [Fact]
    public void EveryTipHasPlainShortWordingWithoutTheOldName()
    {
        foreach (var id in new[] { OutOfArrows, BadlyHurt, FirstDeath, FirstResurrection, Tired, GoldInPack, FirstPet, BadlyHurtPotion, Overloaded })
        {
            Assert.True(Texts.TryGetValue(id, out var text), id);
            Assert.InRange(text.Length, 40, 220);
            Assert.DoesNotContain("Britannia Renaissance", text, StringComparison.OrdinalIgnoreCase);
        }
    }

    [Theory]
    [InlineData(20, 100, true, true)]
    [InlineData(25, 100, true, false)]
    [InlineData(20, 100, false, false)]
    [InlineData(0, 0, true, false)]
    public void TiredNeedsUnderAQuarterStaminaInAFight(int stam, int max, bool combat, bool expected) => Assert.Equal(expected, IsTired(stam, max, combat));

    [Theory]
    [InlineData(1999, false)]
    [InlineData(2000, true)]
    public void TheGoldTipComesAtTheThreshold(int gold, bool expected) => Assert.Equal(expected, CarriesALotOfGold(gold));

    [Theory]
    [InlineData(0, 1, true, true)]
    [InlineData(1, 1, true, false)]   // nothing new
    [InlineData(0, 1, false, false)]  // a summon, not a tamed pet
    public void AFirstPetNeedsANewTamedFollower(int before, int after, bool tamed, bool expected) => Assert.Equal(expected, GainedAPet(before, after, tamed));

    [Fact]
    public void TheJournalNoteIsShortAndNamesTheJournal()
    {
        Assert.Contains("Journal", JournalNote);
        Assert.InRange(JournalNote.Length, 20, 100);
    }

    [Fact]
    public void TheCommandsPageListsTipsOnlyWhenTheyAreOn()
    {
        var off = WelcomeGuide.Commands(new WelcomeGuide.Context(false, false, false, false, false));
        var on = WelcomeGuide.Commands(new WelcomeGuide.Context(false, false, false, false, false, NewPlayerTips: true, AutoPickup: true));

        Assert.DoesNotContain(off, l => l.StartsWith("[Tips", StringComparison.Ordinal));
        Assert.Contains(on, l => l.StartsWith("[Tips - ", StringComparison.Ordinal));
        Assert.DoesNotContain(on, l => l.StartsWith("[Pickup", StringComparison.Ordinal));   // automatic pickup is switched in Options and on the combat bar, not by a command
    }

    [Fact]
    public void TheFlagShipsOffAndIsListedWhenOn()
    {
        Assert.False(new DeferredFeatureFlags().NewPlayerTips);
        Assert.Contains(nameof(DeferredFeatureFlags.NewPlayerTips), new DeferredFeatureFlags { NewPlayerTips = true }.EnabledNames());
    }
}
