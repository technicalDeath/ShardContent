using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class MonsterSpellWordsTests
{
    [Theory]
    [InlineData(true, true, true)]
    [InlineData(true, false, false)]
    [InlineData(false, true, false)]
    public void OnlyCreatureCastersAndOnlyWhenOn(bool enabled, bool creature, bool speaks) =>
        Assert.Equal(speaks, MonsterSpellWords.Speaks(enabled, creature));

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().MonsterSpellWords);
}
