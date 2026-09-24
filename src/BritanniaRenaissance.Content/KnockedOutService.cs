using System.Globalization;
using ModernUO.CodeGeneratedEvents;
using Server;
using Server.Accounting;
using Server.Mobiles;

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

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.KnockedOut == true;

    public static void Configure()
    {
        Mobile.LethalDamageHandler = TryInterceptLethalDamage;
        Mobile.CanBeDamagedHandler = mobile => !IsKnockedOut(mobile);
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

    public static IEnumerable<string> DescribeStatus(Mobile mobile)
    {
        yield return $"Knocked Out enabled: {Enabled}.";

        if (mobile is PlayerMobile player)
        {
            yield return $"Knocked Out until UTC: {GetUntilUtc(player)?.ToString("O", CultureInfo.InvariantCulture) ?? "none"}.";
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
}

public readonly record struct KnockedOutDecision(bool Qualifies, string Reason);
