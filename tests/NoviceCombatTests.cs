using System.Text.Json;
using Xunit;
using static BritanniaRenaissance.Content.NoviceCombatService;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The novice combat assist (docs/Novice-Combat-Assist-Plan.md): the hit-chance lift, the Tactics floor and the stamina floor as pure rules,
/// the properties that make the lift safe (the top end is untouched, hit chance never falls as skill rises), the settings and the flag. The
/// engine hooks are tested in UOContent (WeaponShardHookTests) and the whole path is measured live.
/// </summary>
public class NoviceCombatTests
{
    private static readonly NoviceCombatRules Shipped = new();
    private static readonly Attacker Player = new(true, true);

    /// <summary>The pre-AOS stock hit chance, as BaseWeapon.CheckHit computes it.</summary>
    private static double Stock(double attackerSkill, double defenderSkill) => (attackerSkill + 50.0) / ((defenderSkill + 50.0) * 2.0);

    private static ShardRules ShippedConfiguration()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- the lift

    [Theory]
    [InlineData(0, 91, 0.2943)]
    [InlineData(0, 100, 0.2767)]
    [InlineData(50, 60, 0.6045)]
    [InlineData(50, 91, 0.4716)]
    [InlineData(70, 60, 0.6535)]
    [InlineData(100, 91, 0.5319)]
    [InlineData(100, 60, 0.6818)]
    public void TheLiftIsTheStockChanceTimesOnePlusStrengthTimesTheMissingSkill(double skill, double defender, double expected) =>
        Assert.Equal(expected, LiftedChance(Player, Shipped, Stock(skill, defender), skill), tolerance: 0.0001);

    [Theory]
    [InlineData(100)]
    [InlineData(110)]
    [InlineData(120)]
    public void AtGrandmasterAndAboveTheTopEndIsExactlyStock(double skill)
    {
        for (var defender = 0; defender <= 200; defender += 5)
        {
            var stock = Stock(skill, defender);
            Assert.Equal(stock, LiftedChance(Player, Shipped, stock, skill));
        }
    }

    [Fact]
    public void ALiftNeverRaisesAChanceAlreadyAtOrAboveOne()
    {
        Assert.Equal(1.0, LiftedChance(Player, Shipped, 1.0, 0));
        Assert.Equal(1.5, LiftedChance(Player, Shipped, 1.5, 0));
    }

    [Fact]
    public void TheLiftNeverExceedsOne()
    {
        for (var skill = 0; skill <= 100; skill += 10)
        {
            for (var defender = 0; defender <= 200; defender += 10)
            {
                Assert.InRange(LiftedChance(Player, Shipped, Math.Min(0.999, Stock(skill, defender)), skill), 0.0, 1.0);
            }
        }
    }

    [Fact]
    public void LowestHitChanceAnywhereRisesFromAboutSeventeenToAboutTwentyEightPercent()
    {
        double stockLow = 1, liftedLow = 1;

        for (var skill = 0; skill <= 100; skill++)
        {
            for (var defender = 0; defender <= 100; defender++)
            {
                var stock = Stock(skill, defender);
                stockLow = Math.Min(stockLow, stock);
                liftedLow = Math.Min(liftedLow, LiftedChance(Player, Shipped, stock, skill));
            }
        }

        Assert.Equal(0.1667, stockLow, tolerance: 0.0001);
        Assert.Equal(0.2767, liftedLow, tolerance: 0.0001);
    }

    [Theory]
    [InlineData(0.20)]
    [InlineData(0.40)]
    [InlineData(0.55)]
    [InlineData(0.66)]
    [InlineData(MaxHitLiftStrength)]
    public void HitChanceNeverFallsAsSkillRisesForAnyDefenderWhileStrengthIsWithinTheLimit(double strength)
    {
        var rules = new NoviceCombatRules { HitLiftStrength = strength };

        for (var defender = 0; defender <= 200; defender++)
        {
            var previous = -1.0;
            for (var skill = 0; skill <= 100; skill++)
            {
                var chance = LiftedChance(Player, rules, Stock(skill, defender), skill);
                Assert.True(chance >= previous - 1e-12, $"fell at defender {defender}, skill {skill} with strength {strength}");
                previous = chance;
            }
        }
    }

    [Fact]
    public void ABiggerStrengthCanMakeAccuracyFallAsSkillRisesWhichIsWhyTheValidatorStopsAtTwoThirds()
    {
        var rules = new NoviceCombatRules { HitLiftStrength = 0.9 };
        var fell = false;

        for (var defender = 0; defender <= 200 && !fell; defender++)
        {
            for (var skill = 1; skill <= 100 && !fell; skill++)
            {
                fell = LiftedChance(Player, rules, Stock(skill, defender), skill) <
                       LiftedChance(Player, rules, Stock(skill - 1, defender), skill - 1) - 1e-12;
            }
        }

        Assert.True(fell);
    }

    [Fact]
    public void TheTwoRollProcessTheEngineRunsGivesTheLiftedChanceAndSoSkillGainOddsAreUntouched()
    {
        // The engine rolls the stock chance first (the skill check, which feeds skill gain) and, only after a miss, rolls
        // (lifted - stock) / (1 - stock). The overall hit rate must be the lifted chance.
        var random = new Random(12345);

        foreach (var (skill, stock) in new[] { (0.0, 0.2), (50.0, 0.3), (50.0, 0.45), (80.0, 0.6) })
        {
            var lifted = LiftedChance(Player, Shipped, stock, skill);
            var second = (lifted - stock) / (1.0 - stock);
            const int trials = 400_000;
            var firstHits = 0;
            var hits = 0;

            for (var i = 0; i < trials; i++)
            {
                if (random.NextDouble() < stock)
                {
                    firstHits++;
                    hits++;
                }
                else if (random.NextDouble() < second)
                {
                    hits++;
                }
            }

            // The stock roll keeps its own odds exactly; the total reaches the lifted chance (about 0.0008 sigma at this size).
            Assert.InRange((double)firstHits / trials, stock - 0.004, stock + 0.004);
            Assert.InRange((double)hits / trials, lifted - 0.004, lifted + 0.004);
        }
    }

    // ---- who it is for

    [Fact]
    public void OnlyAnOrdinaryPlayerWithTheFlagOnIsHelped()
    {
        var stock = Stock(50, 60);

        Assert.True(LiftedChance(Player, Shipped, stock, 50) > stock);
        Assert.Equal(stock, LiftedChance(new Attacker(false, true), Shipped, stock, 50));   // flag off
        Assert.Equal(stock, LiftedChance(new Attacker(true, false), Shipped, stock, 50));   // staff, monster, pet
        Assert.Equal(0.0, TacticsForDamage(new Attacker(false, true), Shipped, 0.0));
        Assert.Equal(0.0, TacticsForDamage(new Attacker(true, false), Shipped, 0.0));
        Assert.Equal(33, StaminaForSwing(new Attacker(false, true), Shipped, 33));
        Assert.Equal(33, StaminaForSwing(new Attacker(true, false), Shipped, 33));
    }

    // ---- the floors

    [Theory]
    [InlineData(0.0, 30.0)]
    [InlineData(29.9, 30.0)]
    [InlineData(30.0, 30.0)]
    [InlineData(31.0, 31.0)]
    [InlineData(100.0, 100.0)]
    public void TacticsCountsAsAtLeastTheFloor(double tactics, double expected) =>
        Assert.Equal(expected, TacticsForDamage(Player, Shipped, tactics));

    [Theory]
    [InlineData(1, 60)]
    [InlineData(33, 60)]
    [InlineData(60, 60)]
    [InlineData(61, 61)]
    [InlineData(100, 100)]
    public void StaminaCountsAsAtLeastTheFloor(int stamina, int expected) =>
        Assert.Equal(expected, StaminaForSwing(Player, Shipped, stamina));

    [Fact]
    public void AFloorOfZeroAndAStrengthOfZeroSwitchTheirPartOff()
    {
        var off = new NoviceCombatRules { HitLiftStrength = 0.0, TacticsFloor = 0.0, StaminaFloor = 0 };

        Assert.Equal(0.45, LiftedChance(Player, off, 0.45, 50));
        Assert.Equal(0.0, TacticsForDamage(Player, off, 0.0));
        Assert.Equal(33, StaminaForSwing(Player, off, 33));
    }

    [Fact]
    public void ThePrincipalNumbersGiveTheDamageAndSpeedTheOwnerChose()
    {
        // Tactics 0 is -50% damage; counted as 30 it is -20%, a 1.6x increase. A Dex 33 archer's Bow delay falls from 5.64 s to 4.69 s.
        Assert.Equal(1.6, (1 + (TacticsForDamage(Player, Shipped, 0) - 50) / 100) / (1 + (0 - 50) / 100.0), 6);
        Assert.Equal(5.639, 15000.0 / ((33 + 100) * 20), tolerance: 0.001);
        Assert.Equal(4.6875, 15000.0 / ((StaminaForSwing(Player, Shipped, 33) + 100) * 20), tolerance: 0.0001);
    }

    // ---- settings and the flag

    [Fact]
    public void TheDefaultsAreTheOwnersChoices()
    {
        Assert.Equal(0.66, Shipped.HitLiftStrength);
        Assert.Equal(30.0, Shipped.TacticsFloor);
        Assert.Equal(60, Shipped.StaminaFloor);
    }

    [Fact]
    public void TheDefaultsAreValid()
    {
        var errors = new List<string>();
        Validate(Shipped, errors);
        Assert.Empty(errors);
    }

    [Theory]
    [InlineData(-0.01)]
    [InlineData(0.67)]
    [InlineData(1.0)]
    [InlineData(double.NaN)]
    public void AStrengthOutsideZeroToTwoThirdsIsRejected(double strength)
    {
        var errors = new List<string>();
        Validate(new NoviceCombatRules { HitLiftStrength = strength }, errors);
        Assert.Contains(errors, e => e.Contains("hitLiftStrength"));
    }

    [Theory]
    [InlineData(-1.0)]
    [InlineData(50.1)]
    public void ATacticsFloorOutsideZeroToFiftyIsRejected(double floor)
    {
        var errors = new List<string>();
        Validate(new NoviceCombatRules { TacticsFloor = floor }, errors);
        Assert.Contains(errors, e => e.Contains("tacticsFloor"));
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(101)]
    public void AStaminaFloorOutsideZeroToOneHundredIsRejected(int floor)
    {
        var errors = new List<string>();
        Validate(new NoviceCombatRules { StaminaFloor = floor }, errors);
        Assert.Contains(errors, e => e.Contains("staminaFloor"));
    }

    [Fact]
    public void TheShippedConfigurationHasTheFlagOffAndTheOwnersNumbers()
    {
        var rules = ShippedConfiguration();

        Assert.False(rules.FeatureFlags.NoviceCombat);
        Assert.Equal(0.66, rules.NoviceCombat.HitLiftStrength);
        Assert.Equal(30.0, rules.NoviceCombat.TacticsFloor);
        Assert.Equal(60, rules.NoviceCombat.StaminaFloor);
        Assert.Empty(ShardRulesConfiguration.Validate(rules).Where(e => e.Contains("noviceCombat", StringComparison.OrdinalIgnoreCase)));
        Assert.DoesNotContain(nameof(DeferredFeatureFlags.NoviceCombat), rules.FeatureFlags.EnabledNames());
    }

    [Fact]
    public void TheFlagIsListedWhenOn()
    {
        Assert.Contains(nameof(DeferredFeatureFlags.NoviceCombat), new DeferredFeatureFlags { NoviceCombat = true }.EnabledNames());
        Assert.Contains("none", new DeferredFeatureFlags().EnabledNames());
    }
}
