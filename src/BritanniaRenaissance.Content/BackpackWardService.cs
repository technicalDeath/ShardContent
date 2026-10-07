using Server;
using Server.Accounting;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Runs Backpack Wards in the game (docs/BACKPACK-WARD-DESIGN.md): picks the one Ward that acts for a victim, primes and
/// activates it from theft outcomes, blocks thieves it has caught, and ends it after 30 quiet minutes. The rules themselves
/// are <see cref="WardState"/>. Nothing here changes stock Stealing; it observes theft outcomes through the shard hooks.
/// </summary>
public static class BackpackWardService
{
    private static readonly HashSet<BackpackWard> Tracking = [];
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        EventSink.ServerStarted += Rebuild;
        Server.Timer.StartTimer(TimeSpan.FromSeconds(30), TimeSpan.FromSeconds(30), Sweep);
        BackpackWardVendor.Configure();
        BackpackWardCraft.Configure();
    }

    private static bool Enabled => TheftProtectionService.Enabled;

    /// <summary>After a load, find every Ward that was tracking thieves and apply any time that passed while the server was down.</summary>
    private static void Rebuild()
    {
        Tracking.Clear();

        foreach (var ward in World.Items.Values.OfType<BackpackWard>())
        {
            if (!ward.Deleted && ward.State.IsTracking)
            {
                Tracking.Add(ward);
            }
        }

        Sweep();
    }

    private static void Sweep()
    {
        var now = Core.Now;

        foreach (var ward in Tracking.ToArray())
        {
            if (ward.Deleted)
            {
                Tracking.Remove(ward);
                continue;
            }

            ward.EnforceHolder();
            ApplyExpiry(ward, now);
        }
    }

    /// <summary>The thirty-minute window: a Primed Ward resets, an Activated one is consumed. True when the Ward was consumed.</summary>
    private static bool ApplyExpiry(BackpackWard ward, DateTime now)
    {
        var protectedPlayer = ward.ProtectedCharacter as PlayerMobile;

        switch (ward.State.CheckExpiry(now))
        {
            case WardExpiry.Reset:
                ward.ResetAll();
                Tracking.Remove(ward);
                ShardAuditLog.Record("theft", "ward-reset", protectedPlayer, details: "30 minutes without theft activity");
                return false;

            case WardExpiry.Consume:
                Tracking.Remove(ward);
                protectedPlayer?.SendMessage("Your backpack ward has run its course and is spent.");
                ShardAuditLog.Record("theft", "ward-consumed", protectedPlayer, details: "30 minutes without theft activity");
                ward.Delete();
                return true;

            default:
                return false;
        }
    }

    /// <summary>
    /// The Ward that acts for this victim: one in the equipped backpack (nested containers included), an Activated one first,
    /// then a Primed one, then the lowest-serial Unprimed one. Time that has run out is applied first, and a Ward held by a
    /// different character than the one it protects is reset.
    /// </summary>
    public static BackpackWard? FindWard(PlayerMobile victim)
    {
        if (victim.Backpack is null)
        {
            return null;
        }

        var wards = new List<BackpackWard>();
        Collect(victim.Backpack, wards);

        var now = Core.Now;
        BackpackWard? best = null;

        foreach (var ward in wards.OrderBy(static w => w.Serial.Value))
        {
            ward.EnforceHolder();

            if (ApplyExpiry(ward, now))
            {
                continue;
            }

            if (best is null || Rank(ward) > Rank(best))
            {
                best = ward;
            }
        }

        return best;
    }

    private static int Rank(BackpackWard ward) => ward.State.Phase switch
    {
        WardPhase.Activated => 2,
        WardPhase.Primed => 1,
        _ => 0
    };

    private static void Collect(Container container, List<BackpackWard> wards)
    {
        foreach (var item in container.Items)
        {
            if (item is BackpackWard ward && !ward.Deleted)
            {
                wards.Add(ward);
            }

            if (item is Container child)
            {
                Collect(child, wards);
            }
        }
    }

    /// <summary>True when the victim's Activated Ward has caught this thief's account and the attempt must be rejected.</summary>
    public static bool IsBlocked(PlayerMobile victim, Mobile thief)
    {
        if (thief.Account is not Account account)
        {
            return false;
        }

        var ward = FindWard(victim);
        return ward?.State.IsBlocked(account.Username) == true;
    }

    /// <summary>
    /// Called after stock Stealing has resolved a genuine attempt on a player outside any Hot Zone. A detected theft primes
    /// and activates the Ward (and catches the thief if it succeeded); an undetected success is counted and may be detected by
    /// the Ward's extra roll (25%, 50%, then guaranteed); an undetected failure primes nothing but keeps a tracking Ward awake.
    /// </summary>
    public static void OnTheftResolved(PlayerMobile thief, PlayerMobile victim, bool success, bool detected)
    {
        if (thief.Account is not Account account)
        {
            return;
        }

        var ward = FindWard(victim);
        if (ward is null)
        {
            return;
        }

        var now = Core.Now;
        var name = account.Username;

        if (detected)
        {
            ward.Prime(victim);
            ward.Activate();

            if (success)
            {
                ward.State.MarkCaught(name);
            }

            Tracking.Add(ward);
            ShardAuditLog.Record("theft", "ward-activated", thief, victim, $"stock detection, success={success}");
            return;
        }

        if (!success)
        {
            ward.State.Refresh(now);
            return;
        }

        ward.Prime(victim);
        Tracking.Add(ward);
        var count = ward.State.RecordUndetectedSuccess(name, now);

        if (TheftProtectionService.AdditionalDetectionChance(count) >= Utility.RandomDouble())
        {
            victim.SendMessage("You detect a theft from your backpack.");
            ApplyDetectedTheftConsequences(thief, victim);
            ward.Activate();
            ward.State.MarkCaught(name);
            ShardAuditLog.Record("theft", "ward-detected", thief, victim, $"undetectedSuccesses={count}; thief caught");
        }
    }

    /// <summary>What stock does when a victim notices a theft: the thief turns criminal and bystanders are told.</summary>
    private static void ApplyDetectedTheftConsequences(PlayerMobile thief, PlayerMobile victim)
    {
        thief.CriminalAction(false);
        thief.SendMessage("You have been caught stealing!");

        var message = $"You notice {thief.Name} trying to steal from {victim.Name}.";

        foreach (var ns in thief.GetClientsInRange(8))
        {
            if (ns.Mobile != thief)
            {
                ns.Mobile.SendMessage(message);
            }
        }
    }

    /// <summary>
    /// Double-click feedback: what the Ward is and where it stands. Time that has run out is applied first, so a Ward never
    /// reports a window it no longer has.
    /// </summary>
    public static void Inspect(Mobile from, BackpackWard ward)
    {
        var protectedCharacter = ward.ProtectedCharacter;
        ward.EnforceHolder();

        if (ApplyExpiry(ward, Core.Now))
        {
            if (protectedCharacter != from)
            {
                from.SendMessage("The backpack ward has run its course and is spent.");
            }

            return;
        }

        var state = ward.State;
        var lines = WardDescription.Lines(
            Enabled,
            ward.IsStarterIssued,
            state.Phase,
            state.ProtectedSerial == from.Serial.Value,
            ward.IsChildOf(from.Backpack),
            OutdoorHotZonePolicy.IsHot(from),
            state.Remaining(Core.Now)
        );

        if (from is PlayerMobile { NetState: not null } player)
        {
            StatusWindows.OpenWard(player, Enabled, state.Phase, lines);
            return;
        }

        foreach (var line in lines)
        {
            from.SendMessage(line);
        }
    }

    /// <summary>Lines for [TheftStatus about the Wards in this player's backpack.</summary>
    public static IEnumerable<string> Describe(PlayerMobile player)
    {
        var wards = new List<BackpackWard>();

        if (player.Backpack is not null)
        {
            Collect(player.Backpack, wards);
        }

        if (wards.Count == 0)
        {
            yield return "No Backpack Ward in your backpack.";
            yield break;
        }

        var now = Core.Now;

        foreach (var ward in wards.OrderBy(static w => w.Serial.Value))
        {
            var state = ward.State;
            yield return state.IsTracking
                ? $"Backpack Ward: {state.Phase}, {Math.Ceiling(state.Remaining(now).TotalMinutes)} minute(s) left, {state.Caught.Count} thief account(s) caught."
                : "Backpack Ward: Unprimed.";
        }
    }
}
