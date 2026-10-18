using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Gain and make chances on the craft menus (docs/Craft-Chances-Evidence.md).</summary>
public class CraftChancesTests
{
    // a tailor at 55 with 400 of 700 points used, Tailoring cap 100, gain factor 1, no curve
    private static double Gain(double value, double min, double max, double baseValue = 55, bool canRise = true, double multiplier = 1.0) =>
        CraftChancesService.GainChance(value, baseValue, 100, 4000, 7000, min, max, 1.0, multiplier, canRise);

    [Fact]
    public void AnItemYouAlwaysMakeTeachesNothing() => Assert.Equal(0, Gain(55, -20, 30)); // a shirt: the check is no challenge

    [Fact]
    public void AnItemOutOfReachTeachesNothing() => Assert.Equal(0, Gain(55, 60, 110));

    [Fact]
    public void AChallengingItemTeachesAndHarderTeachesMore()
    {
        var cloak = Gain(55, 40, 90);  // check chance 0.3
        var easier = Gain(55, 10, 60); // check chance 0.9
        Assert.True(cloak > 0 && easier > 0);
        Assert.True(cloak > easier);
    }

    [Fact]
    public void TheChanceMatchesTheStockRoll()
    {
        // check chance c = 0.3; base = ((7000 - 4000) / 7000 + (100 - 55) / 100) / 2 = 0.43929
        // success roll (base + 0.7 * 0.5) / 2 = 0.39464, failure roll (base + 0.7 * 0.2) / 2 = 0.28964
        var expected = 0.3 * 0.39464 + 0.7 * 0.28964;
        Assert.Equal(expected, Gain(55, 40, 90), 4);
    }

    [Fact]
    public void BelowTenItAlwaysGains() => Assert.Equal(1.0, Gain(5, 0, 30, baseValue: 5));

    [Fact]
    public void ALockedOrCappedSkillCannotGain() => Assert.Equal(0, Gain(55, 40, 90, canRise: false));

    [Fact]
    public void TheShardCurveScalesIt() => Assert.Equal(Gain(55, 40, 90) * 0.5, Gain(55, 40, 90, multiplier: 0.5), 6);

    [Theory]
    [InlineData(0.001, true, 1)]  // a real gain chance never shows as 0
    [InlineData(0.123, true, 13)]
    [InlineData(0.999, false, 99)] // a make chance never shows as certain when it is not
    [InlineData(1.4, false, 100)]
    public void PercentRounding(double chance, bool up, byte shown) => Assert.Equal(shown, CraftChancesService.Percent(chance, up));

    [Fact]
    public void ThePacketCarriesTheMenuAndTwoBytesAnEntry()
    {
        var p = CraftChancesService.Packet(0x01020304, [12, CraftChancesService.None], [80, CraftChancesService.None]);
        Assert.Equal(new byte[] { 0xBF, 0, 15, 0x00, 0xAE, 1, 2, 3, 4, 0, 2, 12, 80, 255, 255 }, p);
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().CraftChances);

    [Fact]
    public void SpellPacketNumbersSpellsFromOne() =>
        Assert.Equal(
            new byte[] { 0xBF, 0, 15, 0x00, 0xAF, 0, 2, 0, 1, 7, 100, 0, 2, CraftChancesService.None, CraftChancesService.None },
            SpellChancesService.Packet([7, CraftChancesService.None], [100, CraftChancesService.None])
        );

    [Fact]
    public void TheSpellFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().SpellChances);
}
