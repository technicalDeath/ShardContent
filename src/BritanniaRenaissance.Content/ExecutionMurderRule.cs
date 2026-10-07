using System.Globalization;
using Server.Collections;
using Server.Guilds;
using Server.Misc;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// When an Execute counts as murder (owner ruling 2026-10-06, amending K-5). Attacking is one thing and killing another: a blue
/// may lawfully attack a criminal, a murderer or a player with Criminal Intent on, and that player may fight back and Knock the
/// blue out, but executing the blue is still murder. The only things that make an Execute lawful are the victim's Criminal
/// Intent being on and a guild war between the two (duels are switched off on this shard; a victim who was a criminal or a murderer is never Knocked Out, so the
/// question does not come up for them). Whoever struck an ordinary blue without a right to, as stock reports it, stays reportable.
/// The record is made when the victim is Knocked Out, because Knocked Out clears the aggressor lists.
/// </summary>
public static class ExecutionMurderRule
{
    /// <summary>
    /// <paramref name="unlawfulFirstStrike"/>: stock's report flag, the executor struck a victim they had no right to attack.
    /// <paramref name="victimHadIntentOn"/>: the victim had Criminal Intent on when the executor last struck them.
    /// <paramref name="atGuildWar"/>: the two were enemies in a guild war.
    /// </summary>
    public static bool IsMurder(bool unlawfulFirstStrike, bool victimHadIntentOn, bool atGuildWar) =>
        unlawfulFirstStrike || (!victimHadIntentOn && !atGuildWar);

    /// <summary>Enemy guilds only: guildmates and allies are not at war, so executing one still counts.</summary>
    private static bool AtGuildWar(PlayerMobile attacker, PlayerMobile victim)
    {
        var attackerGuild = NotorietyHandlers.GetGuildFor(attacker.Guild as Guild, attacker);
        var victimGuild = NotorietyHandlers.GetGuildFor(victim.Guild as Guild, victim);
        return attackerGuild is not null && victimGuild is not null && attackerGuild.IsEnemy(victimGuild);
    }

    /// <summary>
    /// The serials of every player who could Execute this victim (the one whose blow Knocked them out, everyone in their aggressor
    /// list, everyone with a recent damage record) and for whom the Execute would be murder, as "none" or "serial,serial".
    /// Stock's report flag alone misses a blue who attacked a criminal first, because that makes the criminal's hits lawful.
    /// </summary>
    public static string DescribeReportableAttackers(PlayerMobile victim, PlayerMobile? knockoutAttacker)
    {
        var candidates = new Dictionary<uint, PlayerMobile>();
        var unlawful = new HashSet<uint>();

        void Consider(PlayerMobile? player)
        {
            if (player is not null && player != victim)
            {
                candidates[player.Serial.Value] = player;
            }
        }

        foreach (var info in victim.Aggressors)
        {
            if (KnockedOutService.ResolvePlayerAttacker(info.Attacker) is { } attacker)
            {
                Consider(attacker);

                if (info.CanReportMurder)
                {
                    unlawful.Add(attacker.Serial.Value);
                }
            }
        }

        foreach (var entry in victim.DamageEntries)
        {
            if (!entry.HasExpired && entry.Damager != victim)
            {
                Consider(KnockedOutService.ResolvePlayerAttacker(entry.Damager));
            }
        }

        Consider(knockoutAttacker);

        var serials = candidates.Values
            .Where(attacker => IsMurder(
                unlawful.Contains(attacker.Serial.Value),
                PvpIntentService.WasIntentClassified(attacker, victim),
                AtGuildWar(attacker, victim)
            ))
            .Select(attacker => attacker.Serial.Value.ToString(CultureInfo.InvariantCulture))
            .ToArray();

        return serials.Length == 0 ? "none" : string.Join(',', serials);
    }
}
