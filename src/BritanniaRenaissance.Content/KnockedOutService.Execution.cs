using Server;
using Server.Collections;
using Server.ContextMenus;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Why an Execute cannot start, in the order the player should hear about it.</summary>
public enum ExecuteRefusal
{
    None,
    Disabled,
    Yourself,
    NotKnockedOut,
    NotCriminalOrMurderer,
    NoRightToExecute,
    ExecutorBusy,
    VictimBusy,
    NotAdjacent,
    WakesTooSoon
}

/// <summary>Everything the start of an Execute depends on, gathered once so the decision is a plain function.</summary>
public readonly record struct ExecuteFacts(
    bool Enabled,
    bool SamePlayer,
    bool VictimKnockedOut,
    bool ExecutorCriminalOrMurderer,
    bool DamageRecordRights,
    bool ExecutorBusy,
    bool VictimBusy,
    bool Adjacent,
    TimeSpan VictimRemaining
);

public enum ExecutionStep
{
    Continue,
    Complete,
    StoppedMoved,
    StoppedVictimGone,
    StoppedExecutorGone
}

/// <summary>
/// The rules of an Execute (owner rulings 2026-10-07): it takes five seconds, the executor stands next to the Knocked Out player the whole
/// time, every eligibility check is made before the countdown starts so a refusal comes at once, and walking away cancels it.
/// </summary>
public static class KnockedOutExecution
{
    public static readonly TimeSpan ChannelTime = TimeSpan.FromSeconds(5);

    /// <summary>The context menu entry's text number: 3,050,001 is above every number the stock client has (it ends at 3,011,032), and the shard's <c>Clilocs.txt</c> says "Execute".</summary>
    public const int ContextEntryNumber = 3050001;

    public static ExecuteRefusal Check(in ExecuteFacts f) =>
        !f.Enabled ? ExecuteRefusal.Disabled :
        f.SamePlayer ? ExecuteRefusal.Yourself :
        !f.VictimKnockedOut ? ExecuteRefusal.NotKnockedOut :
        !f.ExecutorCriminalOrMurderer ? ExecuteRefusal.NotCriminalOrMurderer :
        !f.DamageRecordRights ? ExecuteRefusal.NoRightToExecute :
        f.ExecutorBusy ? ExecuteRefusal.ExecutorBusy :
        f.VictimBusy ? ExecuteRefusal.VictimBusy :
        !f.Adjacent ? ExecuteRefusal.NotAdjacent :
        f.VictimRemaining <= ChannelTime ? ExecuteRefusal.WakesTooSoon :
        ExecuteRefusal.None;

    public static string RefusalText(ExecuteRefusal refusal) => refusal switch
    {
        ExecuteRefusal.Disabled => "Knocked Out is not switched on, so there is nothing to execute.",
        ExecuteRefusal.Yourself => "You cannot execute yourself.",
        ExecuteRefusal.NotKnockedOut => "They are not Knocked Out.",
        ExecuteRefusal.NotCriminalOrMurderer => "Only a criminal or a murderer can execute a Knocked Out player.",
        ExecuteRefusal.NoRightToExecute => "You can only execute a player you have been fighting.",
        ExecuteRefusal.ExecutorBusy => "You are already executing someone.",
        ExecuteRefusal.VictimBusy => "Someone is already executing them.",
        ExecuteRefusal.NotAdjacent => "You must stand next to them to execute them.",
        ExecuteRefusal.WakesTooSoon => "They will get up before you could finish.",
        _ => ""
    };

    /// <summary>What the countdown does next. The victim wakes, the executor leaves or falls, or the five seconds pass.</summary>
    public static ExecutionStep Step(bool executorAlive, bool executorConnected, bool adjacent, bool victimKnockedOut, TimeSpan elapsed) =>
        !executorAlive || !executorConnected ? ExecutionStep.StoppedExecutorGone :
        !victimKnockedOut ? ExecutionStep.StoppedVictimGone :
        !adjacent ? ExecutionStep.StoppedMoved :
        elapsed >= ChannelTime ? ExecutionStep.Complete :
        ExecutionStep.Continue;

    /// <summary>The whole seconds left, 5 down to 1, for the label over the victim.</summary>
    public static int SecondsLeft(TimeSpan elapsed) =>
        Math.Clamp((int)Math.Ceiling((ChannelTime - elapsed).TotalSeconds), 1, (int)ChannelTime.TotalSeconds);

    public static string CountdownText(int secondsLeft) => $"Execution: {secondsLeft}";

    public static string StoppedText(ExecutionStep step) => step switch
    {
        ExecutionStep.StoppedMoved => "You step away, and the execution is cancelled.",
        ExecutionStep.StoppedVictimGone => "They are no longer Knocked Out, and the execution is cancelled.",
        _ => ""
    };
}

/// <summary>
/// The recovery countdown over a Knocked Out player, which everyone nearby can read (owner ruling 2026-10-07): every five seconds, then every
/// second for the last five.
/// </summary>
public static class KnockedOutCountdown
{
    public static bool LabelDue(int secondsLeft) => secondsLeft > 0 && (secondsLeft <= 5 || secondsLeft % 5 == 0);

    public static string Text(int secondsLeft) => $"Knocked Out: {secondsLeft}";
}

public static partial class KnockedOutService
{
    private const int LabelHue = 0x3B2;
    private const int WarningHue = 0x22;

    private sealed class ExecutionChannel(PlayerMobile executor, PlayerMobile victim)
    {
        public readonly PlayerMobile Executor = executor;
        public readonly PlayerMobile Victim = victim;
        public readonly DateTime Started = Core.Now;
        public int LastLabel;
        public TimerExecutionToken Token;
    }

    private static readonly HashSet<PlayerMobile> Watching = [];
    private static readonly Dictionary<PlayerMobile, int> LastLabelled = [];
    private static readonly Dictionary<PlayerMobile, ExecutionChannel> ByExecutor = [];
    private static readonly Dictionary<PlayerMobile, ExecutionChannel> ByVictim = [];
    private static bool _executionConfigured;

    private static void ConfigureExecution()
    {
        if (_executionConfigured)
        {
            return;
        }

        _executionConfigured = true;
        PlayerMobile.ContextMenuEntriesHandler += AddExecuteEntry;
    }

    // ---- the recovery countdown

    private static void TickCountdowns()
    {
        if (Watching.Count == 0)
        {
            return;
        }

        var now = Core.Now.ToUniversalTime();

        foreach (var player in Watching.ToArray())
        {
            if (player.Deleted || !IsKnockedOut(player) || GetUntilUtc(player) is not { } until)
            {
                Watching.Remove(player);
                LastLabelled.Remove(player);
                StopLying(player);
                continue;
            }

            var left = (int)Math.Ceiling((until - now).TotalSeconds);

            if (left <= 0 || LastLabelled.GetValueOrDefault(player) == left)
            {
                continue;
            }

            LastLabelled[player] = left;

            // While someone executes them the label over them is the execution's.
            if (player.Map is not null && KnockedOutCountdown.LabelDue(left) && !ByVictim.ContainsKey(player))
            {
                player.PublicOverheadMessage(MessageType.Label, LabelHue, false, KnockedOutCountdown.Text(left));
            }
        }
    }

    // ---- Execute

    /// <summary>Every check an Execute needs, made now. None means it may start.</summary>
    public static ExecuteRefusal PlanExecution(PlayerMobile executor, PlayerMobile victim)
    {
        var until = GetUntilUtc(victim);

        return KnockedOutExecution.Check(
            new ExecuteFacts(
                Enabled,
                executor == victim,
                IsKnockedOut(victim),
                executor.Criminal || executor.Murderer,
                HasDamageRecordRights(victim, executor),
                ByExecutor.ContainsKey(executor),
                ByVictim.ContainsKey(victim),
                IsAdjacent(executor, victim),
                until is { } end ? end - Core.Now.ToUniversalTime() : TimeSpan.Zero
            )
        );
    }

    private static bool IsAdjacent(PlayerMobile executor, PlayerMobile victim) =>
        executor.Map is not null && executor.Map == victim.Map && executor.InRange(victim.Location, 1);

    public static bool IsBeingExecuted(PlayerMobile victim) => ByVictim.ContainsKey(victim);

    /// <summary>Starts an Execute after checking it all. A refusal is told to the executor at once; nothing is left running.</summary>
    public static bool BeginExecution(PlayerMobile executor, PlayerMobile victim)
    {
        var refusal = PlanExecution(executor, victim);

        if (refusal != ExecuteRefusal.None)
        {
            executor.SendMessage(WarningHue, KnockedOutExecution.RefusalText(refusal));
            ShardAuditLog.Record("knocked-out", "execute-refused", executor, victim, refusal.ToString());

            return false;
        }

        var channel = new ExecutionChannel(executor, victim);
        ByExecutor[executor] = channel;
        ByVictim[victim] = channel;

        executor.SendMessage($"You begin to execute {victim.Name}. Stay next to them for {(int)KnockedOutExecution.ChannelTime.TotalSeconds} seconds.");
        victim.SendMessage(WarningHue, $"{executor.Name} is executing you!");
        ShardAuditLog.Record("knocked-out", "execute-started", executor, victim);

        Server.Timer.StartTimer(TimeSpan.FromMilliseconds(250), TimeSpan.FromMilliseconds(250), () => TickExecution(channel), out channel.Token);
        TickExecution(channel);

        return true;
    }

    private static void TickExecution(ExecutionChannel channel)
    {
        var executor = channel.Executor;
        var victim = channel.Victim;

        if (ByExecutor.GetValueOrDefault(executor) != channel)
        {
            channel.Token.Cancel();

            return;
        }

        var elapsed = Core.Now - channel.Started;
        var step = KnockedOutExecution.Step(
            executor.Alive && !executor.Deleted,
            executor.NetState is not null,
            IsAdjacent(executor, victim),
            IsKnockedOut(victim),
            elapsed
        );

        switch (step)
        {
            case ExecutionStep.Continue:
                var seconds = KnockedOutExecution.SecondsLeft(elapsed);

                if (seconds != channel.LastLabel)
                {
                    channel.LastLabel = seconds;
                    victim.PublicOverheadMessage(MessageType.Label, WarningHue, false, KnockedOutExecution.CountdownText(seconds));
                }

                return;

            case ExecutionStep.Complete:
                EndExecution(channel);

                if (Execute(executor, victim))
                {
                    executor.SendMessage("The Knocked Out player has been executed.");
                }
                else
                {
                    executor.SendMessage(WarningHue, "They can no longer be executed.");
                }

                return;

            default:
                EndExecution(channel);

                if (KnockedOutExecution.StoppedText(step) is { Length: > 0 } text)
                {
                    executor.SendMessage(WarningHue, text);
                }

                victim.SendMessage($"{executor.Name} stops executing you.");
                ShardAuditLog.Record("knocked-out", "execute-cancelled", executor, victim, step.ToString());

                return;
        }
    }

    private static void EndExecution(ExecutionChannel channel)
    {
        channel.Token.Cancel();
        ByExecutor.Remove(channel.Executor);
        ByVictim.Remove(channel.Victim);
    }

    // ---- the context menu entry

    private static void AddExecuteEntry(PlayerMobile target, Mobile from, ref PooledRefList<ContextMenuEntry> list)
    {
        // Offered only to someone who could carry it out (the rest is checked, and told, when they use it); greyed until they stand next to the victim.
        if (from is PlayerMobile executor && executor != target && Enabled && IsKnockedOut(target) &&
            (executor.Criminal || executor.Murderer) && HasDamageRecordRights(target, executor))
        {
            list.Add(new ExecuteEntry());
        }
    }

    private sealed class ExecuteEntry() : ContextMenuEntry(KnockedOutExecution.ContextEntryNumber, 1)
    {
        public override void OnClick(Mobile from, IEntity target)
        {
            if (from is PlayerMobile executor && target is PlayerMobile victim)
            {
                BeginExecution(executor, victim);
            }
        }
    }

    /// <summary>Staff diagnostics: the executions in progress.</summary>
    public static IEnumerable<string> DescribeExecutions()
    {
        yield return $"Executions in progress: {ByExecutor.Count}. Execute takes {(int)KnockedOutExecution.ChannelTime.TotalSeconds} s next to the victim; Knocked Out lasts {(int)Duration.TotalSeconds} s.";

        foreach (var channel in ByExecutor.Values)
        {
            yield return $"{channel.Executor.Name} is executing {channel.Victim.Name}, {(Core.Now - channel.Started).TotalSeconds:0.0} s in.";
        }
    }
}
