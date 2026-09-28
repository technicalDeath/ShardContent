using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class StarterGoldPolicyTests
{
    [Theory]
    [InlineData(false, true, false, false, false, 1000)]
    [InlineData(true, false, false, false, false, 1000)]
    [InlineData(true, true, false, false, false, 500)]
    [InlineData(true, true, true, false, false, 0)]
    [InlineData(true, true, false, true, false, 0)]
    [InlineData(true, true, false, false, true, 0)]
    public void StarterGoldRequiresAnUnusedAccountEntitlement(
        bool enabled, bool ordinaryPlayer, bool recorded, bool otherCharacter,
        bool priorGameTime, int expected
    ) =>
        Assert.Equal(expected, StarterGoldPolicy.SelectAmount(
            enabled, ordinaryPlayer, recorded, otherCharacter, priorGameTime));
}
