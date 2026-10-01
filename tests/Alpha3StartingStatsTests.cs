using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class Alpha3StartingStatsTests
{
    [Theory]
    [InlineData("Archer", 50, 15, 15, 54, 33, 33)]
    [InlineData("Pure Mage", 40, 15, 25, 48, 33, 39)]
    [InlineData("Blacksmith", 50, 15, 15, 54, 33, 33)]
    public void TemplatesSpreadTheirOwnProportionsOverOneHundredAndTwentyPoints(
        string profession, byte str, byte dex, byte intel, int strength, int dexterity, int intelligence
    )
    {
        Assert.Equal(
            (strength, dexterity, intelligence),
            Alpha3StartingStats.Allocate(profession, [str, dex, intel])
        );
    }

    [Theory]
    [InlineData(60, 30, 30)]
    [InlineData(40, 40, 40)]
    [InlineData(30, 30, 60)]
    [InlineData(31, 30, 59)]
    [InlineData(45, 45, 30)]
    public void AnExactOneHundredAndTwentyPointChoiceIsKeptAsChosen(byte strength, byte dexterity, byte intelligence)
    {
        Assert.Equal(
            (strength, dexterity, intelligence),
            Alpha3StartingStats.Allocate(null, [strength, dexterity, intelligence])
        );
    }

    [Theory]
    [InlineData(61, 30, 29)] // total 120 but a stat above 60 and one below 30
    [InlineData(70, 25, 25)] // total 120 but out of range
    [InlineData(60, 15, 15)] // the old 90-point Advanced screen
    [InlineData(40, 40, 30)] // 110
    public void AChoiceThatIsNotAValidOneHundredAndTwentyIsRescaledToOne(byte strength, byte dexterity, byte intelligence)
    {
        var actual = Alpha3StartingStats.Allocate(null, [strength, dexterity, intelligence]);

        Assert.Equal(120, actual.Strength + actual.Dexterity + actual.Intelligence);
        Assert.All([actual.Strength, actual.Dexterity, actual.Intelligence], s => Assert.InRange(s, 30, 60));
    }

    [Theory]
    [InlineData(60, 10, 10, 60, 30, 30)]
    [InlineData(10, 10, 60, 30, 30, 60)]
    [InlineData(35, 35, 10, 45, 45, 30)]
    [InlineData(30, 30, 30, 40, 40, 40)]
    [InlineData(10, 10, 10, 40, 40, 40)]
    public void AdvancedPreservesPreferencesWithExactTotalAndMinimum(
        byte requestedStrength,
        byte requestedDexterity,
        byte requestedIntelligence,
        int strength,
        int dexterity,
        int intelligence
    )
    {
        var actual = Alpha3StartingStats.Allocate(
            null,
            [requestedStrength, requestedDexterity, requestedIntelligence]
        );

        Assert.Equal((strength, dexterity, intelligence), actual);
        Assert.Equal(120, actual.Strength + actual.Dexterity + actual.Intelligence);
        Assert.True(actual.Strength >= 30 && actual.Dexterity >= 30 && actual.Intelligence >= 30);
    }
}
