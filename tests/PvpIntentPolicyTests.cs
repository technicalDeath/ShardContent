using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class PvpIntentPolicyTests
{
    [Fact]
    public void IntentBridgeInitializesAfterStockNotorietyHandlers()
    {
        var method = typeof(ShardBootstrap).GetMethod(nameof(ShardBootstrap.Initialize));
        var attributes = method!.CustomAttributes
            .Where(attribute => attribute.AttributeType.FullName == "Server.CallPriorityAttribute")
            .ToArray();

        var attribute = Assert.Single(attributes);
        Assert.Equal(1000, (int)attribute.ConstructorArguments[0].Value!);
    }

    [Theory]
    [InlineData(true, true, false, false, false, true)]
    [InlineData(true, false, true, false, false, true)]
    [InlineData(true, false, false, true, false, false)]
    [InlineData(true, false, false, false, true, true)]
    [InlineData(true, false, false, false, false, false)]
    [InlineData(false, true, false, false, false, false)]
    [InlineData(false, false, false, false, true, false)]
    public void SafeWorldIntentPolicyAllowsOnlyExplicitLegalReasons(
        bool stockAllowed,
        bool targetIsCriminalOrMurderer,
        bool targetHasIntent,
        bool attackerHasIntent,
        bool existingRetaliation,
        bool expected)
    {
        Assert.Equal(
            expected,
            PvpIntentService.IsSafeWorldPlayerAttackAllowed(
                stockAllowed,
                targetIsCriminalOrMurderer,
                targetHasIntent,
                attackerHasIntent,
                existingRetaliation
            )
        );
    }

    [Theory]
    [InlineData(true, false, false, 1, 3)]
    [InlineData(true, true, false, 1, 1)]
    [InlineData(true, false, true, 6, 6)]
    [InlineData(false, false, false, 6, 6)]
    public void IntentUsesGreyNotorietyWithoutOverridingRealCrime(
        bool intentEnabled,
        bool targetIsCriminal,
        bool targetIsMurderer,
        int stockNotoriety,
        int expected)
    {
        Assert.Equal(
            expected,
            PvpIntentService.GetIntentNotoriety(intentEnabled, targetIsCriminal, targetIsMurderer, stockNotoriety)
        );
    }
}
