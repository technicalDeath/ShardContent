using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Faint Memories: the free pool every new character starts with (owner request 2026-10-07). The rules are pure, so they are pinned here.</summary>
public class FaintMemoriesTests
{
    private static readonly FaintMemoriesRules Rules = new();
    private static readonly DateTime Created = new(2026, 10, 7, 12, 0, 0, DateTimeKind.Utc);

    private static FaintMemoriesState State(int remaining = 50) => new(Created, remaining);

    // ---- the configuration

    [Fact]
    public void TheShippedNumbersAreFivePointsTwentyFourHoursAndTenToEighty()
    {
        Assert.Equal(50, FaintMemoriesPolicy.PointsTenths(Rules));
        Assert.Equal(24.0, Rules.UnlockHours);
        Assert.Equal(100, FaintMemoriesPolicy.FloorTenths(Rules));
        Assert.Equal(800, FaintMemoriesPolicy.CeilingTenths(Rules));
        Assert.Equal(MasteryEngine.ThresholdFixedPoint, FaintMemoriesPolicy.CeilingTenths(Rules));
    }

    private static List<string> Errors(Action<FaintMemoriesRules> change)
    {
        var rules = new FaintMemoriesRules();
        change(rules);
        var errors = new List<string>();
        FaintMemoriesPolicy.Validate(rules, errors);
        return errors;
    }

    [Fact]
    public void TheDefaultsAreValid() => Assert.Empty(Errors(_ => { }));

    [Theory]
    [InlineData(0.0)]
    [InlineData(50.1)]
    [InlineData(5.05)]
    public void PointsMustBeWholeTenthsFromOneTenthToFifty(double points) =>
        Assert.Contains(Errors(r => r.Points = points), e => e.Contains("faintMemories.points"));

    [Theory]
    [InlineData(-1.0)]
    [InlineData(721.0)]
    public void UnlockHoursMustBeBetweenNoneAndThirtyDays(double hours) =>
        Assert.Contains(Errors(r => r.UnlockHours = hours), e => e.Contains("faintMemories.unlockHours"));

    [Fact]
    public void ZeroUnlockHoursIsAllowedSoATestHostCanSkipTheWait() => Assert.Empty(Errors(r => r.UnlockHours = 0.0));

    [Fact]
    public void TheCeilingCannotPassWhereMasteryBeginsOrFallBelowTheFloor()
    {
        Assert.Contains(Errors(r => r.Ceiling = 95.0), e => e.Contains("faintMemories.ceiling"));
        Assert.Contains(Errors(r => r.Ceiling = 80.1), e => e.Contains("no higher than 80.0"));
        Assert.Contains(Errors(r => r.Ceiling = 10.0), e => e.Contains("faintMemories.ceiling"));
        Assert.Empty(Errors(r => r.Ceiling = 80.0));
    }

    // ---- the saved state

    [Fact]
    public void TheStateSurvivesBeingSavedAndLoaded()
    {
        var saved = FaintMemoriesPolicy.Serialize(State(34));

        Assert.True(FaintMemoriesPolicy.TryParse(saved, out var loaded));
        Assert.Equal(Created, loaded.GrantedUtc);
        Assert.Equal(DateTimeKind.Utc, loaded.GrantedUtc.Kind);
        Assert.Equal(34, loaded.RemainingTenths);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("garbage")]
    [InlineData("2|1|5")]
    [InlineData("1|abc|5")]
    [InlineData("1|638000000000000000|-1")]
    [InlineData("1|638000000000000000|99999")]
    [InlineData("1|638000000000000000")]
    public void AnythingElseIsNotAState(string? tag) => Assert.False(FaintMemoriesPolicy.TryParse(tag, out _));

    [Fact]
    public void AUsedUpPoolIsStillAStateSoItCanNeverBeGrantedTwice()
    {
        Assert.True(FaintMemoriesPolicy.TryParse(FaintMemoriesPolicy.Serialize(State(0)), out var loaded));
        Assert.Equal(0, loaded.RemainingTenths);
    }

    // ---- the unlock clock: twenty-four hours from the character's creation

    [Fact]
    public void ItUnlocksExactlyTwentyFourHoursAfterTheCharacterWasCreated()
    {
        var state = State();

        Assert.False(FaintMemoriesPolicy.IsUnlocked(state, Created.AddHours(24).AddTicks(-1), Rules));
        Assert.True(FaintMemoriesPolicy.IsUnlocked(state, Created.AddHours(24), Rules));
        Assert.True(FaintMemoriesPolicy.IsUnlocked(state, Created.AddDays(30), Rules));
    }

    [Fact]
    public void TheCountdownAndTheBarFollowTheClockAndNeverGoOutOfRange()
    {
        var state = State();
        var now = Created.AddHours(15).AddMinutes(46);

        Assert.Equal(TimeSpan.FromHours(8).Add(TimeSpan.FromMinutes(14)), FaintMemoriesPolicy.UnlockIn(state, now, Rules));
        Assert.Equal((15 * 60 + 46) / (24.0 * 60), FaintMemoriesPolicy.UnlockFraction(state, now, Rules), 6);
        Assert.Equal(TimeSpan.Zero, FaintMemoriesPolicy.UnlockIn(state, Created.AddDays(2), Rules));
        Assert.Equal(1.0, FaintMemoriesPolicy.UnlockFraction(state, Created.AddDays(2), Rules));
        Assert.Equal(0.0, FaintMemoriesPolicy.UnlockFraction(state, Created.AddHours(-1), Rules));
    }

    [Theory]
    [InlineData(0, "under a minute")]
    [InlineData(30, "under a minute")]
    [InlineData(61, "2 minutes")]
    [InlineData(60 * 60, "1 hour")]
    [InlineData(60 * 60 + 60, "1 hour 1 minute")]
    [InlineData(8 * 3600 + 14 * 60, "8 hours 14 minutes")]
    [InlineData(24 * 3600, "24 hours")]
    public void TheTimeLeftReadsAsAPlayerWouldSayIt(int seconds, string expected) =>
        Assert.Equal(expected, FaintMemoriesPolicy.DescribeUnlockIn(TimeSpan.FromSeconds(seconds)));

    // ---- using it

    private static int Plan(int remaining = 50, int skill = 400, int cap = 1000, int total = 1000, int totalCap = 7000, int step = 2) =>
        FaintMemoriesPolicy.PlanRestore(remaining, skill, cap, Rules, total, totalCap, step);

    [Fact]
    public void ItComesBackTwoTenthsAtATime() => Assert.Equal(2, Plan());

    [Fact]
    public void OneTenthIsAllThatComesBackWhenOneTenthIsAllThatIsLeft() => Assert.Equal(1, Plan(remaining: 1));

    [Fact]
    public void TheLastTenthBeforeTheCeilingComesAloneAndTheCeilingIsNeverPassed()
    {
        Assert.Equal(1, Plan(skill: 799));
        Assert.Equal(2, Plan(skill: 798));
        Assert.Equal(0, Plan(skill: 800));
        Assert.Equal(0, Plan(skill: 950));
    }

    [Fact]
    public void ASkillBelowTheFloorIsLeftToTheStockGainWhichIsAlreadyFasterThere()
    {
        Assert.Equal(0, Plan(skill: 99));
        Assert.Equal(0, Plan(skill: 0));
        Assert.Equal(2, Plan(skill: 100));
    }

    [Fact]
    public void ASkillWhoseOwnCapIsLowerThanTheCeilingStopsAtItsCap()
    {
        Assert.Equal(1, Plan(skill: 799, cap: 800));
        Assert.Equal(0, Plan(skill: 800, cap: 800));
    }

    [Fact]
    public void FreePointsNeverPassTheTotalSkillCapBecauseTheyCannotMakeRoom()
    {
        Assert.Equal(2, Plan(total: 6998));
        Assert.Equal(1, Plan(total: 6999));
        Assert.Equal(0, Plan(total: 7000));
        Assert.Equal(0, Plan(total: 7003));
    }

    [Fact]
    public void NothingComesBackOnceThePoolIsEmptyOrTheStepIsNone()
    {
        Assert.Equal(0, Plan(remaining: 0));
        Assert.Equal(0, Plan(step: 0));
    }

    [Fact]
    public void FiveFullPointsAreExactlyTwentyFiveUses()
    {
        var remaining = FaintMemoriesPolicy.PointsTenths(Rules);
        var uses = 0;
        var skill = 400;

        while (Plan(remaining: remaining, skill: skill) is var amount and > 0)
        {
            remaining -= amount;
            skill += amount;
            uses++;
        }

        Assert.Equal(25, uses);
        Assert.Equal(0, remaining);
        Assert.Equal(450, skill);
    }

    // ---- what the window shows

    [Fact]
    public void ThereIsNothingToShowForACharacterWithoutOneOrOnceItIsUsedUp()
    {
        Assert.Null(FaintMemoriesPolicy.BuildView(null, Created, Rules));
        Assert.Null(FaintMemoriesPolicy.BuildView(State(0), Created.AddDays(2), Rules));
    }

    [Fact]
    public void ALockedPoolShowsItsCountdownAndAReadyOneShowsWhatIsLeft()
    {
        var locked = FaintMemoriesPolicy.BuildView(State(), Created.AddHours(6), Rules)!;
        var ready = FaintMemoriesPolicy.BuildView(State(34), Created.AddHours(25), Rules)!;

        Assert.Equal(FaintMemoriesPhase.Locked, locked.Phase);
        Assert.Equal(TimeSpan.FromHours(18), locked.UnlockIn);
        Assert.Equal(0.25, locked.UnlockFraction, 6);
        Assert.Equal(FaintMemoriesPhase.Ready, ready.Phase);
        Assert.Equal(34, ready.RemainingTenths);
        Assert.Equal(50, ready.PointsTenths);
    }

    [Fact]
    public void TheBannerSaysHowLongIsLeftWhileLockedAndHowToUseItOnceReady()
    {
        var locked = SkillBankGump.DescribeBanner(FaintMemoriesPolicy.BuildView(State(), Created.AddHours(15).AddMinutes(46), Rules)!, 2);
        var ready = SkillBankGump.DescribeBanner(FaintMemoriesPolicy.BuildView(State(50), Created.AddHours(30), Rules)!, 2);
        var partial = SkillBankGump.DescribeBanner(FaintMemoriesPolicy.BuildView(State(34), Created.AddHours(30), Rules)!, 2);

        Assert.Equal("5.0 points", locked.Points);
        Assert.Equal("Unlocks in 8 hours 14 minutes", locked.Label);
        Assert.Equal(GumpStyle.Gold, locked.FillColor);
        Assert.Equal(FaintMemoriesPolicy.Theme, locked.Theme);

        Assert.Equal("5.0 points", ready.Points);
        Assert.Equal("Train a skill set to Up: 0.2 per use", ready.Label);
        Assert.Equal(GumpStyle.Good, ready.FillColor);
        Assert.Equal(1.0, ready.Fraction);

        Assert.Equal("3.4 of 5.0 left", partial.Points);
        Assert.Equal(0.68, partial.Fraction, 6);
    }

    [Fact]
    public void TheThemeIsTheOwnersLine() =>
        Assert.Equal("Faint memories of a past in Britannia linger, and skills of the past come back to you.", FaintMemoriesPolicy.Theme);

    [Fact]
    public void TheMessagesNameTheFeatureAndSayWhatToDo()
    {
        Assert.Equal(
            "Faint Memories: 5.0 points are ready. Train a skill you have set to Up and they come back to you, 0.2 at a time. [SkillBank shows what is left.",
            FaintMemoriesPolicy.UnlockedMessage(50, 2)
        );
        Assert.Equal(
            "Faint Memories: the last of them has come back to you, into Swords. There is nothing left to remember.",
            FaintMemoriesPolicy.UsedUpMessage("Swords")
        );
    }
}
