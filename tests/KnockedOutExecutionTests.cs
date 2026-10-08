using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The Execute countdown, the recovery countdown, the guard-call text and the [Intent] tag (owner rulings 2026-10-07): an Execute takes five
/// seconds next to the victim, every check is made before it starts, walking away cancels it, and everyone nearby can read the countdowns.
/// </summary>
public sealed class KnockedOutExecutionTests
{
    private static ExecuteFacts Good() => new(
        Enabled: true,
        SamePlayer: false,
        VictimKnockedOut: true,
        ExecutorCriminalOrMurderer: true,
        DamageRecordRights: true,
        ExecutorBusy: false,
        VictimBusy: false,
        Adjacent: true,
        VictimRemaining: TimeSpan.FromSeconds(20)
    );

    // ---- the checks made before the countdown starts

    [Fact]
    public void AnEligibleExecutorNextToAVictimWithTimeLeftMayStart() =>
        Assert.Equal(ExecuteRefusal.None, KnockedOutExecution.Check(Good()));

    [Fact]
    public void EachCheckRefusesAtOnceWithItsOwnReason()
    {
        Assert.Equal(ExecuteRefusal.Disabled, KnockedOutExecution.Check(Good() with { Enabled = false }));
        Assert.Equal(ExecuteRefusal.Yourself, KnockedOutExecution.Check(Good() with { SamePlayer = true }));
        Assert.Equal(ExecuteRefusal.NotKnockedOut, KnockedOutExecution.Check(Good() with { VictimKnockedOut = false }));
        Assert.Equal(ExecuteRefusal.NotCriminalOrMurderer, KnockedOutExecution.Check(Good() with { ExecutorCriminalOrMurderer = false }));
        Assert.Equal(ExecuteRefusal.NoRightToExecute, KnockedOutExecution.Check(Good() with { DamageRecordRights = false }));
        Assert.Equal(ExecuteRefusal.ExecutorBusy, KnockedOutExecution.Check(Good() with { ExecutorBusy = true }));
        Assert.Equal(ExecuteRefusal.VictimBusy, KnockedOutExecution.Check(Good() with { VictimBusy = true }));
        Assert.Equal(ExecuteRefusal.NotAdjacent, KnockedOutExecution.Check(Good() with { Adjacent = false }));
        Assert.Equal(ExecuteRefusal.WakesTooSoon, KnockedOutExecution.Check(Good() with { VictimRemaining = TimeSpan.FromSeconds(4) }));
    }

    [Fact]
    public void AVictimWhoWakesExactlyWhenTheCountdownEndsIsRefusedToo() =>
        Assert.Equal(ExecuteRefusal.WakesTooSoon, KnockedOutExecution.Check(Good() with { VictimRemaining = KnockedOutExecution.ChannelTime }));

    [Fact]
    public void ThePlayerHearsAboutWhatComesFirst()
    {
        // A blue far from a victim who is not Knocked Out hears about the victim first, not the distance.
        var everythingWrong = new ExecuteFacts(true, false, false, false, false, true, true, false, TimeSpan.Zero);

        Assert.Equal(ExecuteRefusal.NotKnockedOut, KnockedOutExecution.Check(everythingWrong));
        Assert.Equal(ExecuteRefusal.NotCriminalOrMurderer, KnockedOutExecution.Check(everythingWrong with { VictimKnockedOut = true }));
        Assert.Equal(ExecuteRefusal.NotAdjacent, KnockedOutExecution.Check(Good() with { Adjacent = false, VictimRemaining = TimeSpan.Zero }));
    }

    [Fact]
    public void EveryRefusalHasText()
    {
        foreach (var refusal in Enum.GetValues<ExecuteRefusal>().Where(static r => r != ExecuteRefusal.None))
        {
            Assert.False(string.IsNullOrWhiteSpace(KnockedOutExecution.RefusalText(refusal)), refusal.ToString());
        }

        Assert.Equal("You must stand next to them to execute them.", KnockedOutExecution.RefusalText(ExecuteRefusal.NotAdjacent));
    }

    // ---- the countdown

    [Fact]
    public void ItTakesFiveSeconds() => Assert.Equal(TimeSpan.FromSeconds(5), KnockedOutExecution.ChannelTime);

    [Theory]
    [InlineData(0.0, 5)]
    [InlineData(0.9, 5)]
    [InlineData(1.0, 4)]
    [InlineData(2.5, 3)]
    [InlineData(4.0, 1)]
    [InlineData(4.9, 1)]
    public void TheLabelCountsFiveToOne(double elapsedSeconds, int expected) =>
        Assert.Equal(expected, KnockedOutExecution.SecondsLeft(TimeSpan.FromSeconds(elapsedSeconds)));

    [Fact]
    public void WalkingAwayCancelsAtAnyTimeButStandingStillCompletesAtFiveSeconds()
    {
        for (var seconds = 0.0; seconds < 5.0; seconds += 0.25)
        {
            var elapsed = TimeSpan.FromSeconds(seconds);

            Assert.Equal(ExecutionStep.StoppedMoved, KnockedOutExecution.Step(true, true, false, true, elapsed));
            Assert.Equal(ExecutionStep.Continue, KnockedOutExecution.Step(true, true, true, true, elapsed));
        }

        Assert.Equal(ExecutionStep.Complete, KnockedOutExecution.Step(true, true, true, true, TimeSpan.FromSeconds(5)));
    }

    [Fact]
    public void ItStopsWhenTheVictimWakesOrTheExecutorFallsOrLeaves()
    {
        var mid = TimeSpan.FromSeconds(2);

        Assert.Equal(ExecutionStep.StoppedVictimGone, KnockedOutExecution.Step(true, true, true, false, mid));
        Assert.Equal(ExecutionStep.StoppedExecutorGone, KnockedOutExecution.Step(false, true, true, true, mid));
        Assert.Equal(ExecutionStep.StoppedExecutorGone, KnockedOutExecution.Step(true, false, true, true, mid));
        Assert.Equal(ExecutionStep.StoppedExecutorGone, KnockedOutExecution.Step(false, true, false, false, mid));
    }

    [Fact]
    public void TheTextsSayWhatHappened()
    {
        Assert.Equal("Execution: 3", KnockedOutExecution.CountdownText(3));
        Assert.Equal("You step away, and the execution is cancelled.", KnockedOutExecution.StoppedText(ExecutionStep.StoppedMoved));
        Assert.Contains("no longer Knocked Out", KnockedOutExecution.StoppedText(ExecutionStep.StoppedVictimGone));
    }

    // ---- the recovery countdown everyone can read

    [Fact]
    public void TheRecoveryLabelComesEveryFiveSecondsThenEverySecondForTheLastFive()
    {
        var shown = Enumerable.Range(1, 30).Where(KnockedOutCountdown.LabelDue).OrderByDescending(static s => s).ToArray();

        Assert.Equal([30, 25, 20, 15, 10, 5, 4, 3, 2, 1], shown);
        Assert.Equal("Knocked Out: 25", KnockedOutCountdown.Text(25));
    }

    // ---- the guard-call text and the tag

    [Fact]
    public void ThePlayerWhoCallsGuardsIsToldAboutEachIntentPlayerNearbyAndNobodyElse()
    {
        Assert.True(GuardCallNotice.ShouldMark(true, true, true, true, false, true));
        Assert.False(GuardCallNotice.ShouldMark(false, true, true, true, false, true));
        Assert.False(GuardCallNotice.ShouldMark(true, false, true, true, false, true));
        Assert.False(GuardCallNotice.ShouldMark(true, true, false, true, false, true));
        Assert.False(GuardCallNotice.ShouldMark(true, true, true, false, false, true));
        Assert.False(GuardCallNotice.ShouldMark(true, true, true, true, true, true));
        Assert.False(GuardCallNotice.ShouldMark(true, true, true, true, false, false));
        Assert.Equal("This player has not yet performed a criminal act.", GuardCallNotice.Text);
        Assert.Equal(14, GuardCallNotice.CallRange);
    }

    [Fact]
    public void TheIntentTagComesAfterTheNameAndAnyTitle()
    {
        Assert.Equal("[Intent]", PvpIntentService.AddNameTag(""));
        Assert.Equal("(Young) [Intent]", PvpIntentService.AddNameTag("(Young)"));
    }

    // ---- the client's menu text

    [Fact]
    public void TheClientTextFileNamesTheExecuteMenuEntry()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "client", "Clilocs.txt");
        var lines = File.ReadAllLines(path).Where(static l => l.Length > 0 && l[0] != '#').ToArray();

        Assert.Contains($"{KnockedOutExecution.ContextEntryNumber}\tExecute", lines);

        // Above every number the stock client has, and inside the range the older menu packet can carry.
        Assert.InRange(KnockedOutExecution.ContextEntryNumber, 3011033, 3065535);
    }
}
