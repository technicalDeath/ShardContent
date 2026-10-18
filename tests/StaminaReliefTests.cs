using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>A hit takes at most 3 stamina from a player, and running with none left says walking still works (docs/Stamina-Relief-Evidence.md).</summary>
public class StaminaReliefTests
{
    private static ShardRules Shipped() =>
        JsonSerializer.Deserialize<ShardRules>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

    // the stock pre-AOS drain, StaminaSystem.FatigueOnDamage (Standard): damage x (100 / hit points before the hit) x (stamina / 100) - 5
    private static int Stock(int damage, int hits, int stamina) => Math.Max(0, (int)(damage * (100.0 / hits) * (stamina / 100.0) - 5.0));

    [Theory]
    [InlineData(12, 60, 30, 1, 1)]   // healthy: the stock loss is already under the cap
    [InlineData(12, 30, 30, 7, 3)]
    [InlineData(12, 15, 30, 19, 3)]  // badly hurt: stock takes most of what is left
    [InlineData(25, 20, 33, 36, 3)]
    public void APlayerLosesAtMostThreeStaminaAHit(int damage, int hits, int stamina, int stock, int capped)
    {
        Assert.Equal(stock, Stock(damage, hits, stamina));
        Assert.Equal(capped, StaminaReliefService.LossPerHit(true, true, Stock(damage, hits, stamina), 3));
    }

    [Fact]
    public void CreaturesAndTheFlagOffKeepTheStockLoss()
    {
        Assert.Equal(19, StaminaReliefService.LossPerHit(true, false, 19, 3));
        Assert.Equal(19, StaminaReliefService.LossPerHit(false, true, 19, 3));
    }

    [Fact]
    public void TheTooTiredLineSaysWalkingStillWorks()
    {
        Assert.Contains("too tired to run", StaminaReliefService.TooTiredToRunText);
        Assert.Contains("you can still walk", StaminaReliefService.TooTiredToRunText);
    }

    [Fact]
    public void TheLineIsSaidAtMostEveryFiveSeconds()
    {
        var now = new DateTime(2026, 10, 16, 12, 0, 0);

        Assert.True(StaminaReliefService.NoticeDue(null, now, StaminaReliefService.NoticeInterval));
        Assert.False(StaminaReliefService.NoticeDue(now.AddSeconds(-2), now, StaminaReliefService.NoticeInterval));
        Assert.True(StaminaReliefService.NoticeDue(now.AddSeconds(-5), now, StaminaReliefService.NoticeInterval));
    }

    [Theory]
    [InlineData(2, true)]   // this step leaves 1 or less: ClassicUO walks from the next step on, silently
    [InlineData(1, true)]
    [InlineData(3, false)]
    public void ARunningStepThatLeavesTheClientWalkingSaysTheLine(int before, bool says) =>
        Assert.Equal(says, StaminaReliefService.RunningOutOfBreath(true, true, true, before));

    [Fact]
    public void WalkingAndTheFlagOffSayNothing()
    {
        Assert.False(StaminaReliefService.RunningOutOfBreath(true, true, false, 1));
        Assert.False(StaminaReliefService.RunningOutOfBreath(false, true, true, 1));
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().StaminaRelief);

    [Fact]
    public void TheShippedCapIsThreeAndValidates()
    {
        var errors = new List<string>();
        StaminaReliefService.Validate(Shipped().StaminaRelief, errors);

        Assert.Empty(errors);
        Assert.Equal(3, Shipped().StaminaRelief.MaxLossPerHit);
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(31)]
    public void ACapOutsideZeroToThirtyIsRefused(int cap)
    {
        var errors = new List<string>();
        StaminaReliefService.Validate(new StaminaReliefRules { MaxLossPerHit = cap }, errors);

        Assert.Single(errors);
    }
}
