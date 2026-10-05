using Server;
using Server.Engines.Harvest;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Behind <c>featureFlags.harvestAutoRepeat</c>: mining, lumberjacking and fishing keep going on the target the
/// player chose, one stock attempt after another, until the resource bank runs out or the player does something
/// else. Every attempt is the stock one (same delay, skill check, yield and messages), so nothing speeds up; only
/// the re-targeting is automatic. One loop per player: starting another harvest system ends the old loop.
/// </summary>
public static class HarvestRepeatService
{
    /// <summary>What the player was doing when an attempt began; any difference at its end means they did something else.</summary>
    public readonly record struct Snapshot(
        long LastMoveTime, long NextSkillTime, long NextSpellTime, Point3D Location, Map? Map, int Hits);

    public enum StopReason
    {
        None,
        Dead,
        Disconnected,
        Moved,
        UsedSkill,
        Cast,
        WarMode,
        Disturbed,
        Retargeting
    }

    private sealed class Loop(HarvestSystem system, Snapshot start, object target)
    {
        public HarvestSystem System { get; } = system;
        public Snapshot Start { get; } = start;
        public object Target { get; } = target;
        public bool Disturbed { get; set; }
        public Item? RetargetTool { get; set; }
        public object? RetargetTarget { get; set; }
    }

    private static readonly Dictionary<Mobile, Loop> Loops = [];
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.HarvestAutoRepeat == true;

    public static int ActiveLoops => Loops.Count;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        HarvestSystem.StageChanged += OnStageChanged;
        EventSink.AggressiveAction += OnAggressiveAction;
        EventSink.Disconnected += from => Loops.Remove(from);
    }

    /// <summary>
    /// The player's own choices that end a loop. Walking, casting, using another skill, entering war mode, fighting
    /// or being hurt, or opening a fresh harvest cursor all mean the player has moved on. Opening containers, using
    /// items and talking do not.
    /// </summary>
    public static StopReason CheckCancel(
        in Snapshot start, in Snapshot now, bool alive, bool connected, bool casting, bool warMode,
        bool disturbed, bool harvestCursorOpen)
    {
        if (!alive)
        {
            return StopReason.Dead;
        }

        if (!connected)
        {
            return StopReason.Disconnected;
        }

        if (now.LastMoveTime != start.LastMoveTime || now.Location != start.Location || now.Map != start.Map)
        {
            return StopReason.Moved;
        }

        if (now.NextSkillTime != start.NextSkillTime)
        {
            return StopReason.UsedSkill;
        }

        if (casting || now.NextSpellTime != start.NextSpellTime)
        {
            return StopReason.Cast;
        }

        if (warMode)
        {
            return StopReason.WarMode;
        }

        if (disturbed || now.Hits < start.Hits)
        {
            return StopReason.Disturbed;
        }

        return harvestCursorOpen ? StopReason.Retargeting : StopReason.None;
    }

    /// <summary>
    /// A full pack loses the harvested item (stock), so the loop stops there; a broken tool has already told the
    /// player so. A skill-check miss repeats, as a manual player would.
    /// </summary>
    public static bool StageAllowsRepeat(HarvestStage stage, bool toolUsable) =>
        stage is HarvestStage.Harvested or HarvestStage.Failed && toolUsable;

    private static Snapshot Capture(Mobile from) =>
        new(from.LastMoveTime, from.NextSkillTime, from.NextSpellTime, from.Location, from.Map, from.Hits);

    private static bool ToolUsable(Item tool) =>
        !tool.Deleted && (tool is not IUsesRemaining uses || uses.UsesRemaining > 0);

    private static void OnStageChanged(HarvestSystem system, Mobile from, Item tool, object target, HarvestStage stage)
    {
        if (!Enabled || from is not PlayerMobile)
        {
            return;
        }

        switch (stage)
        {
            case HarvestStage.Started:
                Loops[from] = new Loop(system, Capture(from), target);
                break;

            case HarvestStage.Concurrent:
                if (Loops.TryGetValue(from, out var running) && running.System == system)
                {
                    // The player picked a new target mid-attempt; stock refuses it. Carry it out when this one ends.
                    running.RetargetTool = tool;
                    running.RetargetTarget = target;
                }

                break;

            default:
                Continue(system, from, tool, target, stage);
                break;
        }
    }

    private static void Continue(HarvestSystem system, Mobile from, Item tool, object target, HarvestStage stage)
    {
        if (!Loops.TryGetValue(from, out var loop) || loop.System != system)
        {
            return;
        }

        Loops.Remove(from);

        var cancel = CheckCancel(
            loop.Start,
            Capture(from),
            from.Alive,
            from.NetState is not null,
            from.Spell is not null,
            from.Warmode,
            loop.Disturbed,
            from.Target is HarvestTarget
        );

        if (cancel is StopReason.Dead or StopReason.Disconnected)
        {
            return;
        }

        // An explicit retarget is the player's own new command, so earlier movement does not cancel it.
        if (loop.RetargetTool is { } newTool && loop.RetargetTarget is { } newTarget)
        {
            if (stage != HarvestStage.PackFull && ToolUsable(newTool))
            {
                system.StartHarvesting(from, newTool, newTarget);
            }

            return;
        }

        if (cancel == StopReason.None && StageAllowsRepeat(stage, ToolUsable(tool)))
        {
            system.StartHarvesting(from, tool, target);
        }
    }

    private static void OnAggressiveAction(AggressiveActionEventArgs e)
    {
        if (Loops.Count == 0)
        {
            return;
        }

        if (e.Aggressed is { } aggressed && Loops.TryGetValue(aggressed, out var hurt))
        {
            hurt.Disturbed = true;
        }

        if (e.Aggressor is { } aggressor && Loops.TryGetValue(aggressor, out var attacker))
        {
            attacker.Disturbed = true;
        }
    }

    public static IEnumerable<string> DescribeStatus(Mobile viewer)
    {
        yield return $"Harvest auto-repeat (harvestAutoRepeat): {(Enabled ? "on" : "off")}.";
        yield return $"Loops in flight: {Loops.Count}.";

        foreach (var (mobile, loop) in Loops)
        {
            var where = loop.Target is IPoint3D point ? $"{point.X},{point.Y},{point.Z}" : "unknown";

            yield return $"Loop: {mobile.Name} {loop.System.GetType().Name} at {where}; disturbed: {loop.Disturbed}; " +
                         $"retarget pending: {loop.RetargetTarget is not null}.";
        }
    }
}
