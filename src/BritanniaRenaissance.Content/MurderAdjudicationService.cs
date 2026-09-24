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
/// The replacement remains feature-gated. ModernUO's report-based murder system is disabled only
/// when the custom flag is enabled, and execution callbacks use the same event boundary to avoid
/// double-counting.
/// </summary>
public static class MurderAdjudicationService
{
    public static readonly TimeSpan RedDuration = TimeSpan.FromHours(24);

    private const string CountPrefix = "BritanniaRenaissance.Murder.AutomaticCount.";
    private const string RedUntilPrefix = "BritanniaRenaissance.Murder.RedUntilUtc.";
    private const string DeathMarkerPrefix = "BritanniaRenaissance.Murder.LastDeathUtc.";
    private const int MaxMigrationDetailRows = 100;
    private static readonly Dictionary<Serial, PlayerMobile> PendingExecutions = new();

    public static bool Enabled =>
        ShardRulesConfiguration.Settings?.FeatureFlags.AutomaticMurderAdjudication == true;

    public static void Configure()
    {
        Mobile.AdditionalMurdererHandler = IsAutomaticallyRed;
        Mobile.LegacyMurdererCountsEnabled = !Enabled;
        PlayerMurderSystem.SetLegacyReportingEnabled(!Enabled);
    }

    public static bool IsAutomaticallyRed(Mobile mobile) =>
        mobile is PlayerMobile player && IsAutomaticRedAt(Enabled, GetRedUntilUtc(player), Core.Now);

    /// <summary>
    /// Keeps the custom red source completely inert while Alpha 2 is disabled. This matters when
    /// an account retains custom tags from a staging rehearsal or a later feature rollback.
    /// </summary>
    public static bool IsAutomaticRedAt(bool enabled, DateTime? redUntilUtc, DateTime nowUtc) =>
        enabled && redUntilUtc is { } expiry && expiry.ToUniversalTime() > nowUtc.ToUniversalTime();

    [OnEvent(nameof(PlayerMobile.PlayerDeathEvent))]
    public static void OnPlayerDeath(PlayerMobile victim)
    {
        if (!Enabled || victim.Criminal || victim.Murderer)
        {
            return;
        }

        var execution = PendingExecutions.Remove(victim.Serial, out var executionKiller);
        var killer = execution ? executionKiller : victim.FindMostRecentDamager(false);
        if (killer is BaseCreature creature)
        {
            killer = creature.GetMaster();
        }

        if (killer is not PlayerMobile playerKiller || playerKiller == victim ||
            !TryRecordAutomaticCount(
                playerKiller,
                victim,
                Core.Now,
                execution ? false : PvpIntentService.WasIntentClassified(playerKiller, victim)
            ))
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

    public static void RegisterExecution(PlayerMobile executor, PlayerMobile victim)
    {
        PendingExecutions[victim.Serial] = executor;
    }

    public static void CancelExecution(PlayerMobile victim) => PendingExecutions.Remove(victim.Serial);

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
        yield return Enabled
            ? "Stock murder reports, five-count threshold and decay are disabled; the custom UTC ledger is authoritative."
            : "Stock murder reports, five-count threshold and decay remain authoritative until replacement enablement.";

        if (mobile is PlayerMobile player)
        {
            yield return $"Automatic counts: {GetAutomaticCount(player)}.";
            yield return $"Cumulative red until UTC: {GetRedUntilUtc(player)?.ToString("O", CultureInfo.InvariantCulture) ?? "none"}.";
            yield return $"Legacy Kills value: {player.Kills}; legacy red-count source enabled: {Mobile.LegacyMurdererCountsEnabled}.";
        }

        yield return $"Legacy murder reporting enabled: {PlayerMurderSystem.LegacyReportingEnabled}.";
    }

    public static IEnumerable<string> DescribeMigrationAudit()
    {
        var players = 0;
        var legacyThreshold = 0;
        var customLedger = 0;
        var customRed = 0;
        var legacyOnly = 0;
        var customOnly = 0;
        var overlapping = 0;
        var detailRows = new List<string>();

        foreach (var mobile in World.Mobiles.Values)
        {
            if (mobile is not PlayerMobile player)
            {
                continue;
            }

            players++;
            var hasLegacyThreshold = player.Kills >= 5;
            if (hasLegacyThreshold)
            {
                legacyThreshold++;
            }

            if (GetAutomaticCount(player) > 0)
            {
                customLedger++;
            }

            var hasCustomRed = IsAutomaticallyRed(player);
            if (hasCustomRed)
            {
                customRed++;
            }

            var migrationState = ClassifyMigrationState(hasLegacyThreshold, hasCustomRed);
            switch (migrationState)
            {
                case MigrationState.LegacyOnly:
                    legacyOnly++;
                    break;
                case MigrationState.CustomOnly:
                    customOnly++;
                    break;
                case MigrationState.Overlapping:
                    overlapping++;
                    break;
            }

            if (migrationState != MigrationState.Neither && detailRows.Count < MaxMigrationDetailRows)
            {
                detailRows.Add(
                    $"{migrationState}: {player.Name} serial=0x{player.Serial.Value:X8}; legacyKills={player.Kills}; " +
                    $"customCount={GetAutomaticCount(player)}; customRedUntil={GetRedUntilUtc(player)?.ToString("O", CultureInfo.InvariantCulture) ?? "none"}."
                );
            }
        }

        yield return $"Migration audit UTC: {Core.Now:O}.";
        yield return $"Player mobiles scanned: {players}.";
        yield return $"Legacy Kills >= 5: {legacyThreshold}.";
        yield return $"Custom murder ledgers present: {customLedger}; custom red currently active: {customRed}.";
        yield return $"Migration state: legacy-only={legacyOnly}; custom-only={customOnly}; overlapping={overlapping}.";
        foreach (var detail in detailRows)
        {
            yield return detail;
        }

        var totalDetailRows = legacyOnly + customOnly + overlapping;
        if (totalDetailRows > detailRows.Count)
        {
            yield return $"Migration detail rows truncated at {MaxMigrationDetailRows}; total non-neutral rows: {totalDetailRows}.";
        }

        yield return $"Legacy reporting enabled: {PlayerMurderSystem.LegacyReportingEnabled}; legacy threshold source enabled: {Mobile.LegacyMurdererCountsEnabled}.";
        yield return "No migration mutation was performed.";
    }

    public static MigrationState ClassifyMigrationState(bool hasLegacyThreshold, bool hasCustomRed) =>
        (hasLegacyThreshold, hasCustomRed) switch
        {
            (true, true) => MigrationState.Overlapping,
            (true, false) => MigrationState.LegacyOnly,
            (false, true) => MigrationState.CustomOnly,
            _ => MigrationState.Neither
        };

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
        ShardAuditLog.Record("murder", "automatic-count", killer, victim, $"count={count}; redUntil={redUntil:O}");
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

public enum MigrationState
{
    Neither,
    LegacyOnly,
    CustomOnly,
    Overlapping
}
