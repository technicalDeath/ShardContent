using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class BackpackWardStateTests
{
    private static readonly DateTime T0 = new(2026, 10, 2, 19, 0, 0, DateTimeKind.Utc);

    private static WardState Primed(uint victim = 0x100, DateTime? at = null)
    {
        var state = new WardState();
        state.Prime(victim, at ?? T0);
        return state;
    }

    private static WardState Activated(string caughtThief, uint victim = 0x100)
    {
        var state = Primed(victim);
        state.Activate(T0);
        state.MarkCaught(caughtThief);
        return state;
    }

    // ---- state transitions

    [Fact]
    public void ANewWardIsUnprimedAndTracksNothing()
    {
        var state = new WardState();

        Assert.Equal(WardPhase.Unprimed, state.Phase);
        Assert.False(state.IsTracking);
        Assert.Equal(0u, state.ProtectedSerial);
        Assert.Equal(WardExpiry.None, state.CheckExpiry(T0.AddDays(1)));
    }

    [Fact]
    public void PrimingRecordsTheProtectedCharacterAndStartsTheWindow()
    {
        var state = new WardState();

        Assert.True(state.Prime(0x100, T0));
        Assert.Equal(WardPhase.Primed, state.Phase);
        Assert.Equal(0x100u, state.ProtectedSerial);
        Assert.Equal(T0.AddMinutes(30), state.DeadlineUtc);
    }

    [Fact]
    public void AWardThatIsAlreadyTrackingCannotBePrimedForSomeoneElse()
    {
        var state = Primed(0x100);

        Assert.False(state.Prime(0x200, T0.AddMinutes(1)));
        Assert.Equal(0x100u, state.ProtectedSerial);
    }

    [Fact]
    public void ActivatingAPrimedWardMakesItActivatedAndActivatingAgainChangesNothing()
    {
        var state = Primed();

        state.Activate(T0.AddMinutes(2));
        state.Activate(T0.AddMinutes(3));

        Assert.Equal(WardPhase.Activated, state.Phase);
        Assert.Equal(T0.AddMinutes(33), state.DeadlineUtc);
    }

    [Fact]
    public void AnUnprimedWardCannotBeActivatedOrRefreshed()
    {
        var state = new WardState();

        state.Activate(T0);
        state.Refresh(T0);

        Assert.Equal(WardPhase.Unprimed, state.Phase);
    }

    // ---- the thirty-minute window

    [Fact]
    public void APrimedWardResetsAfterThirtyQuietMinutesAndAnActivatedOneIsConsumed()
    {
        var primed = Primed();
        var activated = Primed();
        activated.Activate(T0);

        Assert.Equal(WardExpiry.None, primed.CheckExpiry(T0.AddMinutes(29).AddSeconds(59)));
        Assert.Equal(WardExpiry.Reset, primed.CheckExpiry(T0.AddMinutes(30)));
        Assert.Equal(WardExpiry.None, activated.CheckExpiry(T0.AddMinutes(29).AddSeconds(59)));
        Assert.Equal(WardExpiry.Consume, activated.CheckExpiry(T0.AddMinutes(30)));
    }

    [Fact]
    public void AGenuineAttemptRestartsTheWindowEachTime()
    {
        var state = Primed();
        state.Activate(T0);

        state.Refresh(T0.AddMinutes(20));
        Assert.Equal(T0.AddMinutes(50), state.DeadlineUtc);

        state.Refresh(T0.AddMinutes(45));
        Assert.Equal(T0.AddMinutes(75), state.DeadlineUtc);
        Assert.Equal(WardExpiry.None, state.CheckExpiry(T0.AddMinutes(74)));
        Assert.Equal(WardExpiry.Consume, state.CheckExpiry(T0.AddMinutes(75)));
    }

    [Fact]
    public void RemainingTimeCountsDownAndNeverGoesNegative()
    {
        var state = Primed();

        Assert.Equal(TimeSpan.FromMinutes(20), state.Remaining(T0.AddMinutes(10)));
        Assert.Equal(TimeSpan.Zero, state.Remaining(T0.AddHours(2)));
        Assert.Equal(TimeSpan.Zero, new WardState().Remaining(T0));
    }

    // ---- escalating detection per thief account

    [Fact]
    public void SuccessfulUndetectedTheftsCountPerThiefAccountAndSharedAcrossItsCharacters()
    {
        var state = Primed();

        Assert.Equal(1, state.RecordUndetectedSuccess("alpha", T0));
        Assert.Equal(2, state.RecordUndetectedSuccess("ALPHA", T0));
        Assert.Equal(1, state.RecordUndetectedSuccess("bravo", T0));
        Assert.Equal(3, state.RecordUndetectedSuccess("Alpha", T0));
    }

    [Theory]
    [InlineData(0, 0.0)]
    [InlineData(1, 0.25)]
    [InlineData(2, 0.50)]
    [InlineData(3, 1.0)]
    [InlineData(9, 1.0)]
    public void ExtraDetectionEscalatesTwentyFiveFiftyThenGuaranteed(int successes, double expected)
    {
        Assert.Equal(expected, TheftProtectionService.AdditionalDetectionChance(successes));
    }

    [Fact]
    public void AnUndetectedSuccessKeepsTheWindowAlive()
    {
        var state = Primed();

        state.RecordUndetectedSuccess("alpha", T0.AddMinutes(10));

        Assert.Equal(T0.AddMinutes(40), state.DeadlineUtc);
    }

    // ---- caught thieves are blocked

    [Fact]
    public void AThiefCaughtByAnActivatedWardIsBlocked()
    {
        var state = Activated("bob");

        Assert.True(state.IsBlocked("bob"));
        Assert.True(state.IsBlocked("BOB"));
    }

    [Fact]
    public void AThiefTheWardHasNotCaughtIsNotBlockedEvenWhileActivated()
    {
        var state = Activated("bob");

        Assert.False(state.IsBlocked("carol"));
    }

    [Fact]
    public void EachCaughtThiefIsBlockedAndAnUncaughtOneIsNot()
    {
        var state = Activated("bob");
        state.MarkCaught("carol");

        Assert.True(state.IsBlocked("bob"));
        Assert.True(state.IsBlocked("carol"));
        Assert.False(state.IsBlocked("dave"));
    }

    [Fact]
    public void ADetectedFailedAttemptActivatesTheWardButDoesNotBlockTheThief()
    {
        // Stock detected a failed theft: the service activates the Ward and never marks the thief caught.
        var state = Primed();
        state.Activate(T0);

        Assert.Equal(WardPhase.Activated, state.Phase);
        Assert.False(state.IsBlocked("bob"));
    }

    [Fact]
    public void ACaughtThiefStaysBlockedForTheWholeWindowAndNotAfterTheWardIsGone()
    {
        var state = Activated("bob");

        Assert.True(state.IsBlocked("bob"));
        Assert.Equal(WardExpiry.Consume, state.CheckExpiry(T0.AddMinutes(30)));

        state.Reset();

        Assert.False(state.IsBlocked("bob"));
        Assert.Empty(state.Caught);
    }

    [Fact]
    public void ABlockOnlyAppliesWhileTheWardIsActivated()
    {
        var state = Primed();
        state.MarkCaught("bob");

        Assert.False(state.IsBlocked("bob"));

        state.Activate(T0);

        Assert.True(state.IsBlocked("bob"));
    }

    // ---- reset

    [Fact]
    public void ResettingForgetsEverything()
    {
        var state = Activated("bob");
        state.RecordUndetectedSuccess("carol", T0);

        state.Reset();

        Assert.Equal(WardPhase.Unprimed, state.Phase);
        Assert.Equal(0u, state.ProtectedSerial);
        Assert.Empty(state.Successes);
        Assert.Empty(state.Caught);
        Assert.False(state.IsBlocked("bob"));
    }

    // ---- persistence

    [Fact]
    public void RestoringRebuildsTheStateExactly()
    {
        var saved = Activated("bob");
        saved.RecordUndetectedSuccess("carol", T0.AddMinutes(5));
        saved.RecordUndetectedSuccess("carol", T0.AddMinutes(6));

        var loaded = new WardState();
        loaded.Restore(saved.Phase, saved.ProtectedSerial, saved.LastActivityUtc, saved.Successes, saved.Caught);

        Assert.Equal(saved.Phase, loaded.Phase);
        Assert.Equal(saved.ProtectedSerial, loaded.ProtectedSerial);
        Assert.Equal(saved.LastActivityUtc, loaded.LastActivityUtc);
        Assert.Equal(2, loaded.Successes["carol"]);
        Assert.True(loaded.IsBlocked("bob"));
        Assert.Equal(saved.DeadlineUtc, loaded.DeadlineUtc);
    }

    [Fact]
    public void RestoringFromItsOwnCollectionsKeepsThem()
    {
        var state = Activated("bob");
        state.RecordUndetectedSuccess("carol", T0);

        state.Restore(state.Phase, state.ProtectedSerial, state.LastActivityUtc.AddMinutes(-5), state.Successes, state.Caught);

        Assert.Equal(1, state.Successes["carol"]);
        Assert.True(state.IsBlocked("bob"));
        Assert.Equal(T0.AddMinutes(-5), state.LastActivityUtc);
    }

    [Fact]
    public void RestoringAnUnprimedWardDiscardsAnyStrayData()
    {
        var loaded = new WardState();

        loaded.Restore(
            WardPhase.Unprimed, 0x100, T0, new Dictionary<string, int> { ["bob"] = 3 }, new[] { "bob" }
        );

        Assert.Equal(WardPhase.Unprimed, loaded.Phase);
        Assert.Empty(loaded.Successes);
        Assert.Empty(loaded.Caught);
    }

    [Fact]
    public void ARestoredWardKeepsItsAbsoluteDeadlineAcrossARestart()
    {
        var saved = Primed();
        saved.Activate(T0.AddMinutes(10));

        var loaded = new WardState();
        loaded.Restore(saved.Phase, saved.ProtectedSerial, saved.LastActivityUtc, saved.Successes, saved.Caught);

        // The server was down for 25 minutes: the Ward's window ran out while it was off.
        Assert.Equal(WardExpiry.Consume, loaded.CheckExpiry(T0.AddMinutes(40)));
        Assert.Equal(WardExpiry.None, loaded.CheckExpiry(T0.AddMinutes(39)));
    }

    [Fact]
    public void RestoringIgnoresBlankAccountsAndZeroCounts()
    {
        var loaded = new WardState();

        loaded.Restore(
            WardPhase.Primed, 0x100, T0,
            new Dictionary<string, int> { [""] = 2, ["bob"] = 0, ["carol"] = 1 },
            new[] { "", "dave" }
        );

        Assert.Single(loaded.Successes);
        Assert.Single(loaded.Caught);
    }

    // ---- the Welcome text

    [Fact]
    public void TheWelcomeTextDescribesTheBlockAndNoLongerMentionsTheOldRules()
    {
        var text = string.Join(" ", StarterOnboarding.DescribeRules());

        Assert.Contains("cannot steal from you again", text);
        Assert.Contains("30 minutes", text);
        Assert.Contains("25%", text);
        Assert.Contains("ten minutes", text);
        Assert.Contains("Hot Zone", text);
        Assert.DoesNotContain("two minutes", text);
        Assert.DoesNotContain("entitlement", text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void TheCreationPromptPointsAtTheWelcomeCommand()
    {
        Assert.Contains("[Welcome", StarterOnboarding.CreationPrompt);
        Assert.Equal(5, StarterOnboarding.DescribeRules().Count());
    }
}
