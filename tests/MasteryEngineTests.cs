using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class MasteryEngineTests
{
    private static readonly DateTime Anchor = new(2026, 10, 2, 20, 0, 0, DateTimeKind.Utc);
    private static readonly TimeSpan Cycle = TimeSpan.FromHours(24);

    private static long CycleAt(double hoursAfterAnchor) => MasteryEngine.CycleId(Anchor, Anchor.AddHours(hoursAfterAnchor), Cycle);

    // ---- cycles

    [Theory]
    [InlineData(0, 0)]
    [InlineData(23.99, 0)]
    [InlineData(24, 1)]
    [InlineData(47.5, 1)]
    [InlineData(24 * 9 + 1, 9)]
    public void CyclesCountFromTheCharacterAnchorEveryTwentyFourHours(double hours, long expected)
    {
        Assert.Equal(expected, CycleAt(hours));
    }

    [Fact]
    public void ACycleBeforeTheAnchorDoesNotExist()
    {
        Assert.Equal(-1, CycleAt(-0.5));
    }

    [Fact]
    public void TheNextRefreshIsTheNextAnchorMultiple()
    {
        Assert.Equal(Anchor.AddHours(24), MasteryEngine.NextRefresh(Anchor, Anchor.AddHours(5), Cycle));
        Assert.Equal(Anchor.AddHours(48), MasteryEngine.NextRefresh(Anchor, Anchor.AddHours(24), Cycle));
    }

    // ---- claiming

    [Fact]
    public void TheFirstUseInACycleClaimsTheAllowanceOnce()
    {
        var skill = new MasterySkillState();

        Assert.True(MasteryEngine.TryClaim(skill, 0, 5, 15));
        Assert.False(MasteryEngine.TryClaim(skill, 0, 5, 15));
        Assert.Equal(5, skill.AllowanceTenths);
        Assert.True(MasteryEngine.HasClaimed(skill, 0));
        Assert.False(MasteryEngine.HasClaimed(skill, 1));
    }

    [Fact]
    public void ACycleThatIsNotClaimedIsLostAndNeverBanked()
    {
        var skill = new MasterySkillState();
        MasteryEngine.TryClaim(skill, 0, 5, 15);

        // Two whole cycles pass with no valid use, then the skill is used in cycle 3.
        Assert.True(MasteryEngine.TryClaim(skill, 3, 5, 15));

        Assert.Equal(10, skill.AllowanceTenths);
    }

    [Fact]
    public void TheBankHoldsAtMostThreeCyclesOfAllowance()
    {
        var skill = new MasterySkillState();

        for (var cycle = 0; cycle < 6; cycle++)
        {
            MasteryEngine.TryClaim(skill, cycle, 5, 15);
        }

        Assert.Equal(15, skill.AllowanceTenths);
    }

    [Fact]
    public void AClockThatGoesBackwardsCannotClaimAgain()
    {
        var skill = new MasterySkillState();
        MasteryEngine.TryClaim(skill, 4, 5, 15);

        Assert.False(MasteryEngine.TryClaim(skill, 3, 5, 15));
        Assert.False(MasteryEngine.TryClaim(skill, -1, 5, 15));
        Assert.Equal(5, skill.AllowanceTenths);
    }

    [Fact]
    public void LoweringAndRestoringASkillWithinACycleCannotClaimItTwice()
    {
        // The claim is recorded on the skill's state, which survives the skill dropping below the threshold.
        var skill = new MasterySkillState();
        MasteryEngine.TryClaim(skill, 2, 10, 30);

        Assert.False(MasteryEngine.TryClaim(skill, 2, 10, 30));
        Assert.Equal(10, skill.AllowanceTenths);
    }

    // ---- spending

    [Fact]
    public void EachUseSpendsOneTenthUntilTheBankIsEmpty()
    {
        var skill = new MasterySkillState { AllowanceTenths = 2 };

        Assert.True(MasteryEngine.TrySpend(skill));
        Assert.True(MasteryEngine.TrySpend(skill));
        Assert.False(MasteryEngine.TrySpend(skill));
        Assert.Equal(0, skill.AllowanceTenths);
    }

    [Theory]
    [InlineData("easy", 20, 10)]
    [InlineData("standard", 14, 15)]
    [InlineData("hard", 10, 20)]
    [InlineData("veryHard", 8, 25)]
    public void TheTwoHundredValidUsesFromEightyNeedTheApprovedNumberOfClaimedCycles(string _, int allowanceTenths, int expectedCycles)
    {
        var skill = new MasterySkillState();
        var gains = 0;
        var cycles = 0;

        while (gains < 200)
        {
            MasteryEngine.TryClaim(skill, cycles, allowanceTenths, allowanceTenths * 3);
            cycles++;

            while (gains < 200 && MasteryEngine.TrySpend(skill))
            {
                gains++;
            }
        }

        Assert.Equal(expectedCycles, cycles);
        Assert.Equal(expectedCycles, MasteryEngine.MinimumCycles(allowanceTenths));
    }

    [Theory]
    [InlineData(20, 10)]
    [InlineData(14, 15)]
    [InlineData(13, 16)]
    [InlineData(10, 20)]
    [InlineData(8, 25)]
    [InlineData(200, 1)]
    [InlineData(0, 0)]
    public void TheFewestCyclesFromEightyToAHundredFollowTheAllowance(int tenths, int cycles) =>
        Assert.Equal(cycles, MasteryEngine.MinimumCycles(tenths));

    [Fact]
    public void MasteryBeginsAtEightyAndRunsToAHundred()
    {
        Assert.Equal(800, MasteryEngine.ThresholdFixedPoint);
        Assert.Equal("80.0", MasteryEngine.ThresholdText);
        Assert.Equal(1000, MasteryEngine.GrandmasterFixedPoint);
    }

    // ---- the layered rule: a guaranteed gain, or a handed-back roll

    private static MasteryEngine.UseOutcome Decide(
        int value = 850, bool valid = true, bool claimed = true, int stored = 0, int allowance = 14, int bankCap = 42
    ) => MasteryEngine.Decide(value, valid, claimed, stored, allowance, bankCap);

    [Theory]
    [InlineData(0)]
    [InlineData(500)]
    [InlineData(799)]
    public void BelowEightyOrdinaryGainIsAllThereIs(int value) =>
        Assert.Equal(MasteryEngine.UseOutcome.NotMastery, Decide(value: value, stored: 99, claimed: false));

    [Theory]
    [InlineData(1000)]
    [InlineData(1100)]
    public void AtAHundredThereIsNothingLeftToGain(int value) =>
        Assert.Equal(MasteryEngine.UseOutcome.Finished, Decide(value: value, stored: 99));

    [Fact]
    public void AValidUseWithAllowanceInHandIsAGuaranteedGain()
    {
        Assert.Equal(MasteryEngine.UseOutcome.Guaranteed, Decide(value: 800, stored: 5));
        Assert.Equal(MasteryEngine.UseOutcome.Guaranteed, Decide(value: 999, stored: 1));
    }

    [Fact]
    public void TheFirstValidUseInACycleClaimsAndThenGainsForCertain() =>
        Assert.Equal(MasteryEngine.UseOutcome.Guaranteed, Decide(claimed: false, stored: 0));

    [Fact]
    public void AValidUseWithTheStoreEmptyAfterClaimingGainsByChanceInstead() =>
        Assert.Equal(MasteryEngine.UseOutcome.ChanceRoll, Decide(claimed: true, stored: 0));

    [Fact]
    public void AnInvalidUseSpendsNothingAndGainsByChanceEvenWithAllowanceStored()
    {
        Assert.Equal(MasteryEngine.UseOutcome.ChanceRoll, Decide(valid: false, claimed: false, stored: 14));
        Assert.Equal(MasteryEngine.UseOutcome.ChanceRoll, Decide(valid: false, claimed: true, stored: 14));
    }

    [Fact]
    public void ABankAlreadyFullStillGainsOnAClaimAndAZeroAllowanceNeverGuaranteesAnything()
    {
        Assert.Equal(MasteryEngine.UseOutcome.Guaranteed, Decide(claimed: false, stored: 42, allowance: 14, bankCap: 42));
        Assert.Equal(MasteryEngine.UseOutcome.ChanceRoll, Decide(claimed: false, stored: 0, allowance: 0, bankCap: 0));
    }

    [Theory]
    [InlineData(20, 10)]
    [InlineData(14, 15)]
    [InlineData(10, 20)]
    [InlineData(8, 25)]
    public void DrivenOneDayAtATimeOnlyTheAllowanceGainsWhenChanceGivesNothing(int allowanceTenths, int expectedDays)
    {
        // Sixty valid, successful uses a day (more than any allowance), chance gain switched off: only guaranteed gains count.
        var skill = new MasterySkillState();
        var value = MasteryEngine.ThresholdFixedPoint;
        var days = 0;

        while (value < MasteryEngine.GrandmasterFixedPoint && days < 1000)
        {
            for (var use = 0; use < 60 && value < MasteryEngine.GrandmasterFixedPoint; use++)
            {
                var outcome = MasteryEngine.Decide(
                    value, true, MasteryEngine.HasClaimed(skill, days), skill.AllowanceTenths, allowanceTenths, allowanceTenths * 3
                );

                if (outcome != MasteryEngine.UseOutcome.Guaranteed)
                {
                    continue;
                }

                MasteryEngine.TryClaim(skill, days, allowanceTenths, allowanceTenths * 3);
                Assert.True(MasteryEngine.TrySpend(skill));
                value += MasteryEngine.AwardTenths;
            }

            days++;
        }

        Assert.Equal(expectedDays, days);
        Assert.Equal(MasteryEngine.GrandmasterFixedPoint, value);
    }

    [Fact]
    public void AMissedDayIsNeverMadeUpSoTheScheduleStretchesByExactlyTheDaysSkipped()
    {
        // Standard (1.4) with two days skipped (a skipped day gives no allowance) still needs fifteen played days.
        var skill = new MasterySkillState();
        var value = MasteryEngine.ThresholdFixedPoint;
        var played = 0;

        for (var day = 0; value < MasteryEngine.GrandmasterFixedPoint; day++)
        {
            if (day is 3 or 9)
            {
                continue;
            }

            played++;

            while (value < MasteryEngine.GrandmasterFixedPoint &&
                   MasteryEngine.Decide(value, true, MasteryEngine.HasClaimed(skill, day), skill.AllowanceTenths, 14, 42) ==
                   MasteryEngine.UseOutcome.Guaranteed)
            {
                MasteryEngine.TryClaim(skill, day, 14, 42);
                MasteryEngine.TrySpend(skill);
                value++;
            }
        }

        Assert.Equal(15, played);
    }

    [Fact]
    public void GainsLeftCountsTenthsToGrandmaster()
    {
        Assert.Equal(200, MasteryEngine.GainsLeft(800));
        Assert.Equal(100, MasteryEngine.GainsLeft(900));
        Assert.Equal(50, MasteryEngine.GainsLeft(950));
        Assert.Equal(1, MasteryEngine.GainsLeft(999));
        Assert.Equal(0, MasteryEngine.GainsLeft(1000));
        Assert.Equal(0, MasteryEngine.GainsLeft(1100));
    }

    // ---- persistence

    [Fact]
    public void StateRoundTripsThroughItsSavedForm()
    {
        var state = new MasteryCharacterState { AnchorUtc = Anchor };
        state.Skills[7] = new MasterySkillState { LastClaimedCycle = 3, AllowanceTenths = 8 };

        var loaded = MasteryEngine.Parse(MasteryEngine.Serialize(state), out var discarded);

        Assert.False(discarded);
        Assert.Equal(Anchor, loaded.AnchorUtc);
        Assert.Equal(3, loaded.Skills[7].LastClaimedCycle);
        Assert.Equal(8, loaded.Skills[7].AllowanceTenths);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void NoSavedStateIsAFreshStateNotADiscard(string? json)
    {
        var state = MasteryEngine.Parse(json, out var discarded);

        Assert.False(discarded);
        Assert.Null(state.AnchorUtc);
        Assert.Empty(state.Skills);
    }

    [Theory]
    [InlineData("{\"version\":1,\"qualifiedDays\":[100,101],\"skills\":{\"7\":{\"lastProcessedPeriodId\":5,\"pendingTenths\":4}}}")]
    [InlineData("not json")]
    [InlineData("{\"version\":99}")]
    public void StateFromTheEarlierMechanicOrGarbageIsDiscarded(string json)
    {
        var state = MasteryEngine.Parse(json, out var discarded);

        Assert.True(discarded);
        Assert.Null(state.AnchorUtc);
        Assert.Empty(state.Skills);
    }

    // ---- settings

    [Fact]
    public void DefaultSettingsAreValid()
    {
        var errors = new List<string>();

        MasteryRules.Validate(new MasteryRules(), errors);

        Assert.Empty(errors);
    }

    [Fact]
    public void ValidationRejectsOutOfRangeAndMissingValues()
    {
        var rules = new MasteryRules { CycleHours = 0, BankCycles = 11 };
        rules.AllowanceTenths.Remove("hard");
        rules.AllowanceTenths["easy"] = 0;
        rules.AllowanceTenths["mythic"] = 3;
        var errors = new List<string>();

        MasteryRules.Validate(rules, errors);

        Assert.Contains(errors, e => e.Contains("cycleHours"));
        Assert.Contains(errors, e => e.Contains("bankCycles"));
        Assert.Contains(errors, e => e.Contains("'hard'"));
        Assert.Contains(errors, e => e.Contains("'easy'"));
        Assert.Contains(errors, e => e.Contains("mythic"));
    }

    [Fact]
    public void TheCommittedConfigurationHasTheApprovedAllowances()
    {
        var path = Path.GetFullPath(Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        ));
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;

        Assert.Equal(24, rules.Mastery.CycleHours);
        Assert.Equal(3, rules.Mastery.BankCycles);
        Assert.Equal(20, rules.Mastery.AllowanceTenths["easy"]);
        Assert.Equal(14, rules.Mastery.AllowanceTenths["standard"]);
        Assert.Equal(10, rules.Mastery.AllowanceTenths["hard"]);
        Assert.Equal(8, rules.Mastery.AllowanceTenths["veryHard"]);

        // The owner's schedule: casual Grandmaster in 10 / 15 / 20 / 25 days from 80.
        Assert.Equal(10, MasteryEngine.MinimumCycles(rules.Mastery.AllowanceTenths["easy"]));
        Assert.Equal(15, MasteryEngine.MinimumCycles(rules.Mastery.AllowanceTenths["standard"]));
        Assert.Equal(20, MasteryEngine.MinimumCycles(rules.Mastery.AllowanceTenths["hard"]));
        Assert.Equal(25, MasteryEngine.MinimumCycles(rules.Mastery.AllowanceTenths["veryHard"]));
        Assert.Equal(80.0, rules.FaintMemories.Ceiling);
        Assert.Empty(ShardRulesConfiguration.Validate(rules).Where(e => e.Contains("mastery", StringComparison.OrdinalIgnoreCase)));
    }

    [Theory]
    [InlineData(0, "1m")]
    [InlineData(59, "1m")]
    [InlineData(60 * 5 + 20, "6m")]
    [InlineData(3600, "1h 0m")]
    [InlineData(3600 * 5 + 60 * 12, "5h 12m")]
    public void DurationsReadAsHoursAndMinutes(int seconds, string expected)
    {
        Assert.Equal(expected, MasteryEngine.FormatDuration(TimeSpan.FromSeconds(seconds)));
    }
}
