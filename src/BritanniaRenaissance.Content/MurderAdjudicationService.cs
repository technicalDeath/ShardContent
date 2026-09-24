using System.Globalization;
using ModernUO.CodeGeneratedEvents;
using Server;
using Server.Accounting;
using Server.Engines.PlayerMurderSystem;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Alpha 2's automatic-murder policy and durable ledger boundary.
///
/// This is intentionally not wired to PlayerDeathEvent yet. ModernUO's report-based murder
/// system must be disabled and encounter snapshots must be available before this ledger can be
/// enabled; keeping the policy and persistence code separate prevents accidental double-counting.
/// </summary>
public static class MurderAdjudicationService
{
    public static readonly TimeSpan RedDuration = TimeSpan.FromHours(24);

    private const string CountPrefix = "BritanniaRenaissance.Murder.AutomaticCount.";
    private const string RedUntilPrefix = "BritanniaRenaissance.Murder.RedUntilUtc.";
    private const string DeathMarkerPrefix = "BritanniaRenaissance.Murder.LastDeathUtc.";

    public static bool Enabled =>
        ShardRulesConfiguration.Settings?.FeatureFlags.AutomaticMurderAdjudication == true;

    public static void Configure()
    {
        Mobile.AdditionalMurdererHandler = IsAutomaticallyRed;
        Mobile.LegacyMurdererCountsEnabled = !Enabled;
        PlayerMurderSystem.SetLegacyReportingEnabled(!Enabled);
    }

    public static bool IsAutomaticallyRed(Mobile mobile) =>
        mobile is PlayerMobile player && GetRedUntilUtc(player) is { } redUntil && redUntil > Core.Now;

    [OnEvent(nameof(PlayerMobile.PlayerDeathEvent))]
    public static void OnPlayerDeath(PlayerMobile victim)
    {
        if (!Enabled || victim.Criminal || victim.Murderer)
        {
            return;
        }

        var killer = victim.FindMostRecentDamager(false);
        if (killer is BaseCreature creature)
        {
            killer = creature.GetMaster();
        }

        if (killer is not PlayerMobile playerKiller || playerKiller == victim ||
            !TryRecordAutomaticCount(playerKiller, victim, Core.Now))
        {
            return;
        }

        playerKiller.Delta(MobileDelta.Noto);
        playerKiller.InvalidateProperties();
        playerKiller.SendMessage(
            $"You have received an automatic murder count. Red status now expires at {GetRedUntilUtc(playerKiller):O} UTC."
        );
        ScheduleRedExpiryRefresh(playerKiller);
    }

    [OnEvent(nameof(PlayerMobile.PlayerLoginEvent))]
    public static void OnPlayerLogin(PlayerMobile player) => ScheduleRedExpiryRefresh(player);

    /// <summary>
    /// Classifies the victim independently from the attacker's legality. An ordinary blue victim
    /// remains murder-protected even when the killer had retaliation rights or the death occurred
    /// in a future Hot Zone. An encounter already classified as Intent-exposed is the explicit
    /// exception approved by the shard plan.
    /// </summary>
    public static MurderDecision ClassifyDeath(
        bool victimIsCriminal,
        bool victimIsMurderer,
        bool victimWasIntentClassified,
        bool killerIsPlayer,
        bool killerIsVictim)
    {
        if (!killerIsPlayer)
        {
            return new(false, "killer-not-player");
        }

        if (killerIsVictim)
        {
            return new(false, "self-damage");
        }

        if (victimIsCriminal || victimIsMurderer)
        {
            return new(false, "victim-not-ordinary-blue");
        }

        if (victimWasIntentClassified)
        {
            return new(false, "intent-classified-encounter");
        }

        return new(true, "ordinary-blue-victim");
    }

    /// <summary>Extends a cumulative UTC red timer from whichever is later: now or its prior end.</summary>
    public static DateTime ExtendRedUntilUtc(DateTime nowUtc, DateTime priorRedUntilUtc) =>
        (priorRedUntilUtc > nowUtc ? priorRedUntilUtc : nowUtc).Add(RedDuration);

    public static int GetAutomaticCount(PlayerMobile player)
    {
        if (player.Account is not Account account)
        {
            return 0;
        }

        return int.TryParse(
            account.GetTag(CountPrefix + SerialKey(player)),
            NumberStyles.Integer,
            CultureInfo.InvariantCulture,
            out var count
        ) ? Math.Max(count, 0) : 0;
    }

    public static DateTime? GetRedUntilUtc(PlayerMobile player)
    {
        if (player.Account is not Account account ||
            !DateTime.TryParse(
                account.GetTag(RedUntilPrefix + SerialKey(player)),
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var expiry
            ))
        {
            return null;
        }

        return expiry.ToUniversalTime();
    }

    public static IEnumerable<string> DescribeStatus(Mobile mobile)
    {
        yield return $"Automatic murder adjudication enabled: {Enabled}.";
        yield return "Stock murder reports, five-count threshold and decay remain authoritative until replacement enablement.";

        if (mobile is PlayerMobile player)
        {
            yield return $"Automatic counts: {GetAutomaticCount(player)}.";
            yield return $"Cumulative red until UTC: {GetRedUntilUtc(player)?.ToString("O", CultureInfo.InvariantCulture) ?? "none"}.";
            yield return $"Legacy Kills value: {player.Kills}; legacy red-count source enabled: {Mobile.LegacyMurdererCountsEnabled}.";
        }

        yield return $"Legacy murder reporting enabled: {PlayerMurderSystem.LegacyReportingEnabled}.";
    }

    /// <summary>
    /// Records one automatic count for a qualifying death. Calls are idempotent for a victim and
    /// death timestamp, which protects the event boundary from duplicate callbacks and replayed
    /// recovery notifications. The operation is single-threaded with the ModernUO game loop.
    /// </summary>
    public static bool TryRecordAutomaticCount(
        PlayerMobile? killer,
        PlayerMobile victim,
        DateTime deathUtc,
        bool victimWasIntentClassified)
    {
        var decision = ClassifyDeath(
            victim.Criminal,
            victim.Murderer,
            victimWasIntentClassified,
            killer != null,
            killer == victim
        );

        if (!Enabled || !decision.Qualifies || killer is null || killer.Account is not Account account)
        {
            return false;
        }

        deathUtc = deathUtc.ToUniversalTime();
        var markerKey = DeathMarkerPrefix + SerialKey(victim);
        if (DateTime.TryParse(
                account.GetTag(markerKey),
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var previousDeath
            ) && previousDeath.ToUniversalTime() == deathUtc)
        {
            return false;
        }

        var count = GetAutomaticCount(killer) + 1;
        var priorExpiry = GetRedUntilUtc(killer) ?? deathUtc;
        var redUntil = ExtendRedUntilUtc(deathUtc, priorExpiry);

        account.SetTag(CountPrefix + SerialKey(killer), count.ToString(CultureInfo.InvariantCulture));
        account.SetTag(RedUntilPrefix + SerialKey(killer), redUntil.ToString("O", CultureInfo.InvariantCulture));
        account.SetTag(markerKey, deathUtc.ToString("O", CultureInfo.InvariantCulture));
        return true;
    }

    public static bool TryRecordAutomaticCount(PlayerMobile? killer, PlayerMobile victim, DateTime deathUtc) =>
        TryRecordAutomaticCount(
            killer,
            victim,
            deathUtc,
            killer is not null && PvpIntentService.WasIntentClassified(killer, victim)
        );

    private static void ScheduleRedExpiryRefresh(PlayerMobile player)
    {
        var redUntil = GetRedUntilUtc(player);
        if (redUntil is not { } expiry || expiry <= Core.Now)
        {
            return;
        }

        Server.Timer.DelayCall(expiry - Core.Now, static pm =>
        {
            if (!pm.Deleted)
            {
                pm.Delta(MobileDelta.Noto);
                pm.InvalidateProperties();
            }
        }, player);
    }

    private static string SerialKey(PlayerMobile player) =>
        player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);
}

public readonly record struct MurderDecision(bool Qualifies, string Reason);
