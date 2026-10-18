using Server;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>A player's corpse lasts <see cref="DeathRecoveryRules.PlayerCorpseMinutes"/> before it turns to bones (<c>featureFlags.longerPlayerCorpses</c>;
/// the owner, 2026-10-17: "the timer for a corpse turning to bones should be raised to 10 minutes"). Monster corpses keep the stock 7.</summary>
public static class LongerPlayerCorpses
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.LongerPlayerCorpses == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Corpse.DecayTimeOverride = corpse => DecayTime(Enabled, corpse.Owner is PlayerMobile, DeathRecovery.Rules.PlayerCorpseMinutes);
    }

    public static TimeSpan? DecayTime(bool enabled, bool playerCorpse, int minutes) => enabled && playerCorpse ? TimeSpan.FromMinutes(minutes) : null;
}

/// <summary>
/// The corpse compass (<c>featureFlags.corpseCompass</c>): an on-screen arrow, the one Tracking draws, points a ghost or a resurrected player to their own
/// corpse until it is opened by them, emptied, gone, or they are within <see cref="DeathRecoveryRules.CompassStopRange"/> tiles of it.
/// </summary>
public static class CorpseCompass
{
    public static readonly TimeSpan AfterDeath = TimeSpan.FromSeconds(3);

    private static bool _configured;
    private static readonly Dictionary<PlayerMobile, Corpse> Pointing = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CorpseCompass == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.PlayerDeathHandler += player => Server.Timer.DelayCall(AfterDeath, () => Start(player));
        Corpse.OwnerOpened += (owner, corpse) =>
        {
            if (owner is PlayerMobile player && Pointing.TryGetValue(player, out var pointed) && pointed == corpse)
            {
                Stop(player);
            }
        };
        EventSink.Connected += m =>
        {
            // a relog clears the client's arrow
            if (m is PlayerMobile player && Pointing.TryGetValue(player, out var corpse))
            {
                Server.Timer.DelayCall(AfterDeath, () => Send(player, corpse));
            }
        };
        Server.Timer.StartTimer(TimeSpan.FromSeconds(2), TimeSpan.FromSeconds(2), Poll);
    }

    /// <summary>Whether the arrow stops: the corpse is gone or empty, or its owner is beside it on the same map.</summary>
    public static bool Stops(bool corpseGone, bool corpseEmpty, bool sameMap, int distance, int stopRange) =>
        corpseGone || corpseEmpty || sameMap && distance <= stopRange;

    private static void Start(PlayerMobile player)
    {
        if (!Enabled || player.Deleted || player.Corpse is not Corpse { Deleted: false } corpse || corpse.Items.Count == 0)
        {
            return;
        }

        if (Pointing.TryGetValue(player, out var old) && old != corpse)
        {
            Stop(player);
        }

        Pointing[player] = corpse;
        Send(player, corpse);
    }

    private static void Send(PlayerMobile player, Corpse corpse) => player.NetState?.SendSetArrow(corpse.X, corpse.Y, corpse.Serial);

    private static void Stop(PlayerMobile player)
    {
        if (Pointing.Remove(player, out var corpse) && player.QuestArrow is null)
        {
            player.NetState?.SendCancelArrow(corpse.X, corpse.Y, corpse.Serial);
        }
    }

    private static void Poll()
    {
        if (Pointing.Count == 0)
        {
            return;
        }

        using var done = Server.Collections.PooledRefList<PlayerMobile>.Create();

        foreach (var (player, corpse) in Pointing)
        {
            if (player.Deleted || Stops(
                    corpse.Deleted,
                    corpse.Items.Count == 0,
                    player.Map == corpse.Map,
                    (int)player.GetDistanceToSqrt(corpse.Location),
                    DeathRecovery.Rules.CompassStopRange
                ))
            {
                done.Add(player);
            }
        }

        foreach (var player in done)
        {
            Stop(player);
        }
    }
}

/// <summary>
/// One-click self-loot for blue players (<c>featureFlags.blueSelfLoot</c>): the engine's Age of Shadows behaviour, switched on for this era. Double-clicking your own
/// corpse takes everything back where it was and puts worn gear on again, while you are blue: not a murderer and not a criminal (Criminal Intent counts as blue,
/// the owner, 2026-10-17). Anyone else opens a corpse item by item as before.
/// </summary>
public static class BlueSelfLoot
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.BlueSelfLoot == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Corpse.RecordsRestore = _ => Enabled;
        Corpse.SelfLootAllowed = (from, corpse) => Allowed(Enabled, from is PlayerMobile && corpse.Owner == from, from.Murderer, from.Criminal);
    }

    public static bool Allowed(bool enabled, bool ownCorpse, bool murderer, bool criminal) => enabled && ownCorpse && !murderer && !criminal;
}

/// <summary>Shared by the death-recovery parts: the rules, and the one creature-sight hook that materializing and the killer going home both use.</summary>
public static class DeathRecovery
{
    private static bool _configured;

    public static DeathRecoveryRules Rules => ShardRulesConfiguration.Settings?.DeathRecovery ?? new DeathRecoveryRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        LongerPlayerCorpses.Configure();
        CorpseCompass.Configure();
        BlueSelfLoot.Configure();
        KillerGoesHome.Configure();
        Materializing.Configure();

        // materializing first: while it lasts the killer's "first sees you again" clock must not start
        BaseCreature.SightFilter = (creature, m) =>
            m is not PlayerMobile player || !Materializing.Hides(creature, player) && !KillerGoesHome.Hides(creature, player);
    }

    /// <summary>A wild creature: not anyone's pet or summons.</summary>
    public static bool IsWild(BaseCreature creature) => !creature.Controlled && !creature.Summoned && creature.ControlMaster is null;

    /// <summary>A wild creature that is not a townsperson: no vendor (healers and bankers are vendors), guard or blue-named NPC. Hiding a player from
    /// townsfolk would stop a banker answering "bank" and a healer seeing them.</summary>
    public static bool IsMonster(BaseCreature creature) =>
        IsWild(creature) && Monster(creature is BaseVendor, creature is BaseShieldGuard, creature.InitialInnocent);

    /// <summary>The rule, free of the game: not a vendor, not a guard, not blue.</summary>
    public static bool Monster(bool vendor, bool guard, bool blue) => !vendor && !guard && !blue;
}
