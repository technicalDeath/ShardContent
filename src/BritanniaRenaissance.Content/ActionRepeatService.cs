using Server;
using Server.Items;
using Server.Mobiles;
using Server.Network;
using Server.SkillHandlers;
using Snapshot = BritanniaRenaissance.Content.HarvestRepeatService.Snapshot;
using StopReason = BritanniaRenaissance.Content.HarvestRepeatService.StopReason;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Behind <c>featureFlags.actionAutoRepeat</c>: four more loops under the gathering rule (<see cref="HarvestRepeatService"/>).
/// Animal Taming retries the same creature after a plain failure; Lockpicking retries the same lock while picks last; a
/// spinning wheel spins the whole stack one stock spin at a time; cooking cooks the whole stack one stock attempt at a
/// time; and the loom takes the whole stack on one use (stock has no timer there, so there is nothing to pace). Every
/// attempt is the stock one, restarted the way a macro would: the skill or item is used again and the same target is
/// answered, so every stock range, sight and refusal check runs with its own message. One loop per player.
/// </summary>
public static class ActionRepeatService
{
    public enum Kind
    {
        Taming,
        Lockpicking,
        Spinning,
        Cooking
    }

    private sealed class Loop(Kind kind, object target, Snapshot start)
    {
        public Kind Kind { get; } = kind;
        public object Target { get; } = target;
        public Snapshot Start { get; } = start;
        public bool Disturbed { get; set; }
    }

    private static readonly Dictionary<Mobile, Loop> Loops = [];
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.ActionAutoRepeat == true;

    public static int ActiveLoops => Loops.Count;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        AnimalTaming.AttemptStarted += (from, creature) => Begin(from, Kind.Taming, creature);
        AnimalTaming.AttemptEnded += OnTamingEnded;
        Lockpick.AttemptStarted += (from, lockable, _) => Begin(from, Kind.Lockpicking, lockable);
        Lockpick.AttemptEnded += OnLockpickEnded;
        SpinningWheelEvents.SpinStarted += (_, wheel, from) => Begin(from, Kind.Spinning, wheel);
        SpinningWheelEvents.Spun += OnSpun;
        CookableFood.CookStarted += (from, _, heat) => Begin(from, Kind.Cooking, heat);
        CookableFood.CookFinished += OnCooked;

        var previousFeed = BaseClothMaterial.FeedAmount;
        BaseClothMaterial.FeedAmount = (from, material) =>
            Enabled && from is PlayerMobile ? material.Amount : previousFeed?.Invoke(from, material) ?? 1;

        EventSink.AggressiveAction += OnAggressiveAction;
        EventSink.Disconnected += from => Loops.Remove(from);
    }

    // The decision tables. Natural ends (tamed, picked, no picks, nothing left) stop; a plain miss repeats, as a manual
    // player would.
    public static bool TamingContinues(TameResult result) => result == TameResult.Failed;

    public static bool LockpickingContinues(LockpickResult result, bool pickUsable, bool stillLocked) =>
        result == LockpickResult.Failed && pickUsable && stillLocked;

    public static bool SpinningContinues(bool materialLeft, bool wheelBusy) => materialLeft && !wheelBusy;

    public static bool CookingContinues(bool foodLeft) => foodLeft;

    /// <summary>
    /// Gathering's cancel rules. A taming attempt resets the player's skill timer itself as it ends (stock), and no other
    /// skill can be used while one runs, so that signal is ignored for taming.
    /// </summary>
    public static StopReason Cancel(
        Kind kind, in Snapshot start, in Snapshot now, bool alive, bool connected, bool casting, bool warMode,
        bool disturbed, bool cursorOpen)
    {
        var baseline = kind == Kind.Taming ? start with { NextSkillTime = now.NextSkillTime } : start;
        return HarvestRepeatService.CheckCancel(baseline, now, alive, connected, casting, warMode, disturbed, cursorOpen);
    }

    /// <summary>
    /// Answers the cursor the stock skill or item just raised, as a macro's "last target" would. Setting the cursor
    /// already sent it to the client and consuming it server-side does not take it back, so the stock cancel follows
    /// in the same flush; otherwise the player would be left holding a cursor nothing is asking for.
    /// </summary>
    private static void AnswerCursor(Mobile from, object target)
    {
        var cursor = from.Target;

        if (cursor is null)
        {
            return;
        }

        cursor.Invoke(from, target);

        if (from.Target is null)
        {
            from.NetState.SendCancelTarget();
        }
    }

    private static Snapshot Capture(Mobile from) =>
        new(from.LastMoveTime, from.NextSkillTime, from.NextSpellTime, from.Location, from.Map, from.Hits);

    private static void Begin(Mobile from, Kind kind, object target)
    {
        if (!Enabled || from is not PlayerMobile)
        {
            return;
        }

        Loops[from] = new Loop(kind, target, Capture(from));
    }

    /// <summary>The player's loop, if it is this kind, on this target, and nothing cancels it. Either way the entry is gone.</summary>
    private static bool Continues(Mobile from, Kind kind, object target)
    {
        if (!Loops.Remove(from, out var loop) || loop.Kind != kind || loop.Target != target)
        {
            return false;
        }

        var cancel = Cancel(
            kind,
            loop.Start,
            Capture(from),
            from.Alive,
            from.NetState is not null,
            from.Spell is not null,
            from.Warmode,
            loop.Disturbed,
            from.Target is not null
        );

        return cancel == StopReason.None;
    }

    private static void OnTamingEnded(Mobile from, BaseCreature creature, TameResult result)
    {
        if (!Continues(from, Kind.Taming, creature) || !TamingContinues(result))
        {
            return;
        }

        // The stock skill use, with its cursor answered at once; the "Tame which animal?" prompt would repeat every try.
        var quiet = AnimalTaming.DisableMessage;
        AnimalTaming.DisableMessage = true;

        try
        {
            if (from.UseSkill(SkillName.AnimalTaming))
            {
                AnswerCursor(from, creature);
            }
        }
        finally
        {
            AnimalTaming.DisableMessage = quiet;
        }
    }

    private static void OnLockpickEnded(Mobile from, ILockpickable lockable, Lockpick pick, LockpickResult result)
    {
        if (!Continues(from, Kind.Lockpicking, lockable))
        {
            return;
        }

        var pickUsable = !pick.Deleted && pick.IsChildOf(from.Backpack);

        if (LockpickingContinues(result, pickUsable, lockable.Locked))
        {
            pick.BeginPick(from, lockable);
        }
    }

    private static void OnSpun(Item material, ISpinningWheel wheel, Mobile from)
    {
        if (!Continues(from, Kind.Spinning, wheel))
        {
            return;
        }

        var left = !material.Deleted && material.Amount > 0 && material.IsChildOf(from.Backpack);

        if (!SpinningContinues(left, wheel.Spinning))
        {
            return;
        }

        switch (material)
        {
            case Wool wool:
                wool.SpinOn(from, wheel);
                break;
            case Cotton cotton:
                cotton.SpinOn(from, wheel);
                break;
            case Flax flax:
                flax.SpinOn(from, wheel);
                break;
        }
    }

    private static void OnCooked(Mobile from, CookableFood food, object heatSource, CookableFood.CookResult result)
    {
        if (!Continues(from, Kind.Cooking, heatSource))
        {
            return;
        }

        if (!CookingContinues(!food.Deleted && food.Amount > 0 && food.IsChildOf(from.Backpack)))
        {
            return;
        }

        // The stock double-click raises the cursor without a prompt; answering it runs the stock heat-source checks.
        from.Use(food);
        AnswerCursor(from, heatSource);
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

    public static IEnumerable<string> DescribeStatus()
    {
        yield return $"Action auto-repeat (actionAutoRepeat): {(Enabled ? "on" : "off")}; taming, lockpicking, spinning, loom, cooking.";
        yield return $"Loops in flight: {Loops.Count}.";

        foreach (var (mobile, loop) in Loops)
        {
            var where = loop.Target switch
            {
                Mobile m => $"{m.Name} ({m.Serial})",
                Item i => $"{i.GetType().Name} ({i.Serial})",
                IPoint3D p => $"{p.X},{p.Y},{p.Z}",
                _ => "unknown"
            };

            yield return $"Loop: {mobile.Name} {loop.Kind} on {where}; disturbed: {loop.Disturbed}.";
        }
    }
}
