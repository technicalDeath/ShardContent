using System.Globalization;
using ModernUO.CodeGeneratedEvents;
using Server;
using Server.Accounting;
using Server.Items;
using Server.Mobiles;
using Server.SkillHandlers;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Safe-world Knocked Out state boundary. The feature is deliberately gated until the complete
/// encounter-rights, looting, execution, and Hot/Cool region policy is ready for live enablement.
/// </summary>
public static class KnockedOutService
{
    public static readonly TimeSpan Duration = TimeSpan.FromSeconds(90);

    private const string UntilPrefix = "BritanniaRenaissance.KnockedOut.UntilUtc.";
    private const string AttackerPrefix = "BritanniaRenaissance.KnockedOut.Attacker.";
    private const string CompletedPrefix = "BritanniaRenaissance.KnockedOut.Completed.";

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.KnockedOut == true;

    public static void Configure()
    {
        Mobile.LethalDamageHandler = TryInterceptLethalDamage;
        Mobile.CanBeDamagedHandler = mobile => !IsKnockedOut(mobile);
        Stealing.KnockedOutLoot = CanLootKnockedOut;
    }

    [OnEvent(nameof(PlayerMobile.PlayerLoginEvent))]
    public static void OnPlayerLogin(PlayerMobile player)
    {
        if (!Enabled || !IsKnockedOut(player))
        {
            return;
        }

        player.Hits = Math.Max(player.Hits, 1);
        player.Warmode = false;
        player.Combatant = null;
        player.Target = null;
        player.SendMessage("You are Knocked Out and cannot be harmed for a short time.");
        ScheduleRecovery(player);
    }

    public static bool TryInterceptLethalDamage(Mobile victim, Mobile from, int amount)
    {
        if (victim is not PlayerMobile player)
        {
            return false;
        }

        var decision = Classify(
            Enabled,
            player: true,
            ordinaryBlue: IsQualifyingVictim(player),
            hotZone: ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true
        );

        if (!decision.Qualifies)
        {
            return false;
        }

        var until = Core.Now.ToUniversalTime().Add(Duration);
        if (player.Account is Account account)
        {
            account.SetTag(UntilPrefix + SerialKey(player), until.ToString("O", CultureInfo.InvariantCulture));
            if (from is PlayerMobile attacker)
            {
                account.SetTag(AttackerPrefix + SerialKey(player), attacker.Serial.Value.ToString(CultureInfo.InvariantCulture));
                account.SetTag(
                    CompletedPrefix + SerialKey(player),
                    $"{until:O}|{attacker.Serial.Value.ToString(CultureInfo.InvariantCulture)}"
                );
            }
            else
            {
                account.SetTag(CompletedPrefix + SerialKey(player), $"{until:O}|none");
            }
        }

        player.Hits = 1;
        player.Stam = 0;
        player.Mana = 0;
        player.Warmode = false;
        player.Combatant = null;
        player.Target = null;
        ClearAggression(player);
        player.SendMessage("You have been Knocked Out for 90 seconds.");
        ShardAuditLog.Record("knocked-out", "entered", player, from, "90-second damage-immune state");
        ScheduleRecovery(player);
        return true;
    }

    public static bool IsQualifyingVictim(PlayerMobile player) =>
        player.Alive && !player.Criminal && !player.Murderer;

    public static bool CanLootKnockedOut(Mobile thief, Item item, Mobile victim)
    {
        if (thief is not PlayerMobile playerThief || victim is not PlayerMobile playerVictim ||
            playerThief == playerVictim ||
            item.RootParent != playerVictim || !IsKnockedOut(playerVictim))
        {
            return false;
        }

        var isRed = playerThief.Criminal || playerThief.Murderer;
        var hotZone = ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true;
        var recordedAttacker = GetRecordedAttackerSerial(playerVictim);
        var hasRights = recordedAttacker == playerThief.Serial;
        var decision = ClassifyLoot(Enabled, hotZone, isRed, hasRights);

        if (decision.Qualifies)
        {
            ShardAuditLog.Record("knocked-out-loot", "authorized", playerThief, playerVictim);
        }

        return decision.Qualifies;
    }

    public static KnockedOutLootDecision ClassifyLoot(
        bool featureEnabled, bool hotZone, bool actorIsCriminalOrMurderer, bool recordedTargetRights
    ) => !featureEnabled ? new(false, "feature-disabled") :
        !actorIsCriminalOrMurderer ? new(false, "actor-not-criminal-or-murderer") :
        hotZone ? new(true, "hot-zone-red-looting") :
        recordedTargetRights ? new(true, "recorded-target-rights") :
        new(false, "missing-target-rights");

    public static bool IsKnockedOut(Mobile mobile)
    {
        if (!Enabled || mobile is not PlayerMobile player || player.Account is not Account account)
        {
            return false;
        }

        if (!DateTime.TryParse(
                account.GetTag(UntilPrefix + SerialKey(player)),
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var until
            ))
        {
            return false;
        }

        until = until.ToUniversalTime();
        if (until > Core.Now.ToUniversalTime())
        {
            return true;
        }

        account.RemoveTag(UntilPrefix + SerialKey(player));
        account.RemoveTag(AttackerPrefix + SerialKey(player));
        return false;
    }

    public static DateTime? GetUntilUtc(PlayerMobile player)
    {
        if (player.Account is not Account account ||
            !DateTime.TryParse(
                account.GetTag(UntilPrefix + SerialKey(player)),
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var until
            ))
        {
            return null;
        }

        return until.ToUniversalTime();
    }

    public static bool Recover(PlayerMobile player)
    {
        if (player.Account is not Account account)
        {
            return false;
        }

        var wasKnockedOut = GetUntilUtc(player) is not null;
        account.RemoveTag(UntilPrefix + SerialKey(player));
        account.RemoveTag(AttackerPrefix + SerialKey(player));

        if (wasKnockedOut)
        {
            player.Hits = Math.Max(player.Hits, 1);
            player.Warmode = false;
            player.Combatant = null;
            player.Target = null;
            player.SendMessage("A staff member has recovered you from Knocked Out.");
            ShardAuditLog.Record("knocked-out", "staff-recovered", player);
        }

        return wasKnockedOut;
    }

    public static IEnumerable<string> DescribeStatus(Mobile mobile)
    {
        yield return $"Knocked Out enabled: {Enabled}.";

        if (mobile is PlayerMobile player)
        {
            yield return $"Knocked Out until UTC: {GetUntilUtc(player)?.ToString("O", CultureInfo.InvariantCulture) ?? "none"}.";
            yield return $"Completed encounter record: {GetCompletedEncounter(player) ?? "none"}.";
            yield return "Encounter-authorized no-skill looting and execution are not yet enabled.";
        }
    }

    public static KnockedOutDecision Classify(bool featureEnabled, bool player, bool ordinaryBlue, bool hotZone) =>
        !featureEnabled ? new(false, "feature-disabled") :
        !player ? new(false, "not-player") :
        !ordinaryBlue ? new(false, "not-ordinary-blue") :
        hotZone ? new(false, "hot-zone-resolution-deferred") :
        new(true, "ordinary-blue-safe-world");

    private static void ScheduleRecovery(PlayerMobile player)
    {
        var until = GetUntilUtc(player);
        if (until is not { } expiry || expiry <= Core.Now)
        {
            return;
        }

        Server.Timer.DelayCall(expiry - Core.Now, static pm =>
        {
            if (pm.Deleted || pm.Account is not Account account)
            {
                return;
            }

            account.RemoveTag(UntilPrefix + SerialKey(pm));
            account.RemoveTag(AttackerPrefix + SerialKey(pm));
            pm.Hits = Math.Max(pm.Hits, 1);
            pm.SendMessage("You recover from being Knocked Out.");
            ShardAuditLog.Record("knocked-out", "recovered", pm);
        }, player);
    }

    private static void ClearAggression(PlayerMobile player)
    {
        foreach (var info in player.Aggressors.ToArray())
        {
            player.RemoveAggressor(info.Attacker);
        }

        foreach (var info in player.Aggressed.ToArray())
        {
            player.RemoveAggressed(info.Defender);
        }
    }

    private static string SerialKey(PlayerMobile player) =>
        player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

    private static string? GetCompletedEncounter(PlayerMobile player) =>
        player.Account is Account account ? account.GetTag(CompletedPrefix + SerialKey(player)) : null;

    private static Serial GetRecordedAttackerSerial(PlayerMobile player)
    {
        if (player.Account is not Account account ||
            !uint.TryParse(account.GetTag(AttackerPrefix + SerialKey(player)), out var serial))
        {
            return Serial.Zero;
        }

        return (Serial)serial;
    }
}

public readonly record struct KnockedOutDecision(bool Qualifies, string Reason);
public readonly record struct KnockedOutLootDecision(bool Qualifies, string Reason);
