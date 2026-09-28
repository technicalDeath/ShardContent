using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class Alpha3StartingStatsTests
{
    [Theory]
    [InlineData("Warrior", 50, 40, 30)]
    [InlineData("Mage", 30, 30, 60)]
    [InlineData("Blacksmith", 60, 30, 30)]
    public void UorTemplatesHavePlaystyleAllocations(string profession, int strength, int dexterity, int intelligence)
    {
        Assert.Equal(
            (strength, dexterity, intelligence),
            Alpha3StartingStats.Allocate(profession, [35, 35, 10])
        );
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
