using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The killer goes home (<c>featureFlags.killerGoesHome</c>, docs/Death-Recovery-Plan.md). When a wild monster kills a player and is not fighting anyone else
/// (the owner, 2026-10-17: "only if the monster is not engaged in combat with someone else"), it drops the fight, wanders back toward its spawn home, and
/// leaves that player alone for <see cref="DeathRecoveryRules.KillerSpareSeconds"/> counted from when it first sees them alive again ("2 minutes after
/// first seeing them again"). So a corpse is no longer camped by what made it.
/// </summary>
public static class KillerGoesHome
{
    /// <summary>A spare that never started (the player never came back near the killer) is dropped after this.</summary>
    public static readonly TimeSpan Forget = TimeSpan.FromMinutes(30);

    private static bool _configured;
    private static readonly Dictionary<(BaseCreature Killer, PlayerMobile Player), Spare> Spared = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.KillerGoesHome == true;

    private sealed class Spare
    {
        public DateTime Made;
        public DateTime? FirstSeen;
    }

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.PlayerDeathHandler += OnPlayerDeath;
    }

    /// <summary>
    /// Whether the killer goes home: the flag is on, the killer is a wild creature that is still alive, and it has no foe but the one it killed (no other
    /// living combatant, attacker or target it is still fighting).
    /// </summary>
    public static bool GoesHome(bool enabled, bool wildAndAlive, int otherFoes) => enabled && wildAndAlive && otherFoes == 0;

    /// <summary>Whether the killer still leaves the player alone: before it first sees them, or within the spare time after that.</summary>
    public static bool StillSpared(DateTime? firstSeen, DateTime now, TimeSpan spare) => firstSeen is null || now - firstSeen.Value < spare;

    private static void OnPlayerDeath(PlayerMobile player)
    {
        // a new death replaces any spare the player had
        foreach (var key in Spared.Keys.Where(k => k.Player == player).ToList())
        {
            Spared.Remove(key);
        }

        if (player.LastKiller is not BaseCreature killer ||
            !GoesHome(Enabled, DeathRecovery.IsWild(killer) && killer.Alive && !killer.Deleted, OtherFoes(killer, player)))
        {
            return;
        }

        killer.Combatant = null;
        killer.FocusMob = null;
        killer.Warmode = false;

        if (killer.AIObject is { } ai)
        {
            ai.Action = ActionType.Wander; // wandering walks a creature that is out of its home range back toward home
        }

        Spared[(killer, player)] = new Spare { Made = Core.Now };
    }

    private static int OtherFoes(BaseCreature killer, PlayerMobile victim)
    {
        var foes = 0;

        if (killer.Combatant is { Alive: true } combatant && combatant != victim)
        {
            foes++;
        }

        foreach (var info in killer.Aggressors)
        {
            if (!info.Expired && info.Attacker != victim && info.Attacker.Alive && !info.Attacker.Deleted)
            {
                foes++;
            }
        }

        foreach (var info in killer.Aggressed)
        {
            if (!info.Expired && info.Defender != victim && info.Defender.Alive && !info.Defender.Deleted)
            {
                foes++;
            }
        }

        return foes;
    }

    /// <summary>The sight hook: true hides the player from the creature that killed them.</summary>
    public static bool Hides(BaseCreature creature, PlayerMobile player)
    {
        if (Spared.Count == 0 || !Spared.TryGetValue((creature, player), out var spare))
        {
            return false;
        }

        var now = Core.Now;

        if (!Enabled || creature.Deleted || player.Deleted || spare.FirstSeen is null && now - spare.Made > Forget)
        {
            Spared.Remove((creature, player));
            return false;
        }

        if (!player.Alive)
        {
            return true;
        }

        spare.FirstSeen ??= now;

        if (StillSpared(spare.FirstSeen, now, TimeSpan.FromSeconds(DeathRecovery.Rules.KillerSpareSeconds)))
        {
            return true;
        }

        Spared.Remove((creature, player));
        return false;
    }
}
