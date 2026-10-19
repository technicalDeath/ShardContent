using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CorpseCarveButtonTests
{
    [Theory]
    [InlineData(false, true, false, true, 3, false, false, false, true)]   // a deer with meat and hides
    [InlineData(true, true, false, true, 3, false, false, false, false)]   // already carved
    [InlineData(false, true, false, true, 0, false, false, false, false)]  // nothing to carve (an orc)
    [InlineData(false, true, false, true, 3, true, false, false, false)]   // a summon
    [InlineData(false, true, false, true, 3, false, true, false, false)]   // a bonded pet
    [InlineData(false, true, true, false, 0, false, false, false, true)]   // a human body carves into parts
    [InlineData(false, false, false, false, 0, false, false, false, false)] // no owner
    public void CarvableFollowsTheStockCarveRules(bool carved, bool owner, bool human, bool creature, int yields, bool summoned, bool bonded, bool animated, bool expected) =>
        Assert.Equal(expected, CorpseCarveButton.Carvable(carved, owner, human, creature, yields, summoned, bonded, animated));

    [Fact]
    public void TheReplyCarriesTheCorpseAndTheAnswer() =>
        Assert.Equal(new byte[] { 0xBF, 0, 10, 0x00, 0xB0, 0x40, 0x01, 0x02, 0x03, 1 }, CorpseCarveButton.Reply(0x40010203, true));

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().CorpseCarveButton);
}
