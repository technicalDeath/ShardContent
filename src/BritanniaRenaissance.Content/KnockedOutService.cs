using System.Globalization;
using Server;
using Server.Accounting;
using Server.Collections;
using Server.Items;
using Server.Mobiles;
using Server.SkillHandlers;
using Server.Targeting;

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
    private const string ReportablePrefix = "BritanniaRenaissance.KnockedOut.Reportable.";
    private static AllowBeneficialHandler? _stockAllowBeneficial;
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.KnockedOut == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        _stockAllowBeneficial = Mobile.AllowBeneficialHandler;
        Mobile.AllowBeneficialHandler = AllowBeneficial;
        Mobile.LethalDamageHandler = TryInterceptLethalDamage;
        Mobile.CanBeDamagedHandler = mobile => IsStaff(mobile) || !IsKnockedOut(mobile);
        Mobile.CanTargetHandler = CanTarget;
        Mobile.HealHandler = BlockHeal;
        Mobile.CurePoisonHandler = BlockCurePoison;
        Mobile.ActionCheckHandler = CanPerformAction;
        RegisterLootHooks();
        EventSink.Connected += OnConnected;
    }

    public static void Initialize()
    {
        if (!_configured)
        {
            return;
        }

        if (Mobile.AllowBeneficialHandler != AllowBeneficial)
        {
            _stockAllowBeneficial = Mobile.AllowBeneficialHandler;
            Mobile.AllowBeneficialHandler = AllowBeneficial;
        }

        if (Mobile.CanTargetHandler != CanTarget)
        {
            Mobile.CanTargetHandler = CanTarget;
        }
    }

    /// <summary>
    /// Rebinds the safe-world guards after stock UOContent initialization. The stock Notoriety
    /// initializer owns AllowBeneficialHandler and can run after this assembly's normal
    /// CallPriority boundary, so ServerStarted is the final lifecycle point at which the custom
    /// guard is restored while preserving the stock delegate for ordinary beneficial checks.
    /// </summary>
    public static void RebindAfterStockHandlers()
    {
        if (!_configured)
        {
            return;
        }

        if (Mobile.AllowBeneficialHandler?.Method.DeclaringType != typeof(KnockedOutService))
        {
            _stockAllowBeneficial = Mobile.AllowBeneficialHandler;
            Mobile.AllowBeneficialHandler = AllowBeneficial;
        }

        Mobile.LethalDamageHandler = TryInterceptLethalDamage;
        Mobile.CanBeDamagedHandler = mobile => IsStaff(mobile) || !IsKnockedOut(mobile);
        Mobile.CanTargetHandler = CanTarget;
        Mobile.HealHandler = BlockHeal;
        Mobile.CurePoisonHandler = BlockCurePoison;
        Mobile.ActionCheckHandler = CanPerformAction;
        RegisterLootHooks();
    }

    public static void OnPlayerLogin(PlayerMobile player)
    {
        if (!Enabled)
        {
            return;
        }

        var until = GetUntilUtc(player);
        if (until is null)
        {
            return;
        }

        if (IsStaff(player))
        {
            ClearActiveState(player);
            WakePlayer(player, "Staff characters are exempt from Knocked Out restrictions.");
            return;
        }

        if (until <= Core.Now.ToUniversalTime())
        {
            ClearActiveState(player);
            WakePlayer(player, "You recover from being Knocked Out.");
            return;
        }

        if (!IsKnockedOut(player))
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

    private static void OnConnected(Mobile mobile)
    {
        if (mobile is PlayerMobile player)
        {
            OnPlayerLogin(player);
        }
    }

    public static bool TryInterceptLethalDamage(Mobile victim, Mobile from, int amount)
    {
        if (victim is not PlayerMobile player || IsStaff(player))
        {
            return false;
        }

        var responsibleAttacker = ResolvePlayerAttacker(from);
        var hasActiveEncounter = responsibleAttacker is not null &&
                                 (!PvpIntentService.SafeWorldEnabled ||
                                  PvpIntentService.HasActiveEncounter(responsibleAttacker, player));
        var decision = ClassifyDamage(
            Enabled,
            player: true,
            ordinaryBlue: IsQualifyingVictim(player),
            hotZone: OutdoorHotZonePolicy.IsHot(player),
            attributablePlayerDamage: responsibleAttacker is not null,
            activeEncounter: hasActiveEncounter
        );

        if (!decision.Qualifies)
        {
            return false;
        }

        var until = Core.Now.ToUniversalTime().Add(Duration);
        if (player.Account is Account account)
        {
            account.SetTag(UntilPrefix + SerialKey(player), until.ToString("O", CultureInfo.InvariantCulture));
            if (responsibleAttacker is not null)
            {
                account.SetTag(
                    AttackerPrefix + SerialKey(player),
                    responsibleAttacker.Serial.Value.ToString(CultureInfo.InvariantCulture)
                );
                account.SetTag(
                    CompletedPrefix + SerialKey(player),
                    $"{until:O}|{responsibleAttacker.Serial.Value.ToString(CultureInfo.InvariantCulture)}"
                );
            }
            else
            {
                account.SetTag(CompletedPrefix + SerialKey(player), $"{until:O}|none");
            }
        }

        if (player.Account is Account reportableAccount)
        {
            reportableAccount.SetTag(ReportablePrefix + SerialKey(player), DescribeReportableAttackers(player));
        }

        player.Hits = 1;
        player.Stam = 0;
        player.Mana = 0;
        ClearCombatEffects(player);
        player.Warmode = false;
        player.Combatant = null;
        player.Target = null;
        ClearAggression(player);
        player.SendMessage("You have been Knocked Out for 90 seconds.");
        ShardAuditLog.Record(
            "knocked-out",
            "entered",
            player,
            responsibleAttacker ?? from,
            responsibleAttacker is null ? "90-second damage-immune state" : "90-second state; attacker resolved to player master"
        );
        ScheduleRecovery(player);
        return true;
    }

    public static bool IsQualifyingVictim(PlayerMobile player) =>
        player.Alive && !player.Criminal && !player.Murderer;

    private static void RegisterLootHooks()
    {
        Snooping.KnockedOutOpen = CanOpenKnockedOutPack;
        PlayerMobile.NonlocalLiftHandler = CanLiftFromKnockedOut;
        PlayerMobile.ItemLiftedHandler = OnItemLiftedFromKnockedOut;
    }

    /// <summary>
    /// An eligible looter opens a Knocked Out player's backpack and lifts items like a corpse: no
    /// Snooping or Stealing roll. Equipped items stay on the player.
    /// </summary>
    public static bool CanOpenKnockedOutPack(Mobile looter, Container pack, Mobile victim) =>
        victim is PlayerMobile playerVictim && playerVictim.Backpack is { } root &&
        (pack == root || pack.IsChildOf(root)) && IsEligibleLooter(looter, playerVictim);

    public static bool CanLiftFromKnockedOut(Mobile looter, PlayerMobile victim, Item item) =>
        victim.Backpack is { } pack && item != pack && item.IsChildOf(pack) &&
        !IsProtectedFromLooting(item) && IsEligibleLooter(looter, victim);

    private static void OnItemLiftedFromKnockedOut(Mobile looter, PlayerMobile victim, Item item)
    {
        if (!IsKnockedOut(victim))
        {
            return;
        }

        ShardAuditLog.Record("knocked-out-loot", "authorized", looter, victim);
        OnKnockedOutLootResolved(looter, victim, item);
    }

    private static bool IsEligibleLooter(Mobile looter, PlayerMobile victim)
    {
        if (looter is not PlayerMobile playerLooter || !playerLooter.Alive || playerLooter == victim ||
            !IsKnockedOut(victim))
        {
            return false;
        }

        var hasRights = GetRecordedAttackerSerial(victim) == playerLooter.Serial;
        return ClassifyLoot(
            Enabled,
            OutdoorHotZonePolicy.IsHot(victim),
            playerLooter.Criminal || playerLooter.Murderer,
            hasRights
        ).Qualifies;
    }

    // A corpse never holds these, so a Knocked Out pack does not give them up either.
    private static bool IsProtectedFromLooting(Item item)
    {
        if (item.Nontransferable || item.LootType is LootType.Newbied or LootType.Blessed)
        {
            return true;
        }

        foreach (var child in item.Items)
        {
            if (IsProtectedFromLooting(child))
            {
                return true;
            }
        }

        return false;
    }

    public static KnockedOutLootDecision ClassifyLoot(
        bool featureEnabled, bool hotZone, bool actorIsCriminalOrMurderer, bool recordedTargetRights
    ) => !featureEnabled ? new(false, "feature-disabled") :
        hotZone ? new(true, actorIsCriminalOrMurderer ? "hot-zone-red-looting" : "hot-zone-blue-looting") :
        !actorIsCriminalOrMurderer ? new(false, "actor-not-criminal-or-murderer") :
        recordedTargetRights ? new(true, "recorded-target-rights") :
        new(false, "missing-target-rights");

    /// <summary>
    /// A blue who takes an item from a Knocked Out player in a Hot Zone becomes criminal. Looting
    /// a Knocked Out pack never rolls detection, so nothing else would flag the looter.
    /// </summary>
    public static void OnKnockedOutLootResolved(Mobile thief, Mobile victim, Item? stolen)
    {
        if (stolen is null || thief is not PlayerMobile playerThief || victim is not PlayerMobile playerVictim ||
            !IsKnockedOut(playerVictim) || !OutdoorHotZonePolicy.IsHot(playerVictim) ||
            playerThief.Criminal || playerThief.Murderer)
        {
            return;
        }

        playerThief.CriminalAction(true);
        ShardAuditLog.Record("knocked-out-loot", "blue-flagged-criminal", playerThief, playerVictim);
    }

    public static KnockedOutExecutionDecision ClassifyExecution(
        bool featureEnabled, bool actorIsCriminalOrMurderer, bool damageRecordRights
    ) => !featureEnabled ? new(false, "feature-disabled") :
        !actorIsCriminalOrMurderer ? new(false, "actor-not-criminal-or-murderer") :
        damageRecordRights ? new(true, "damage-record-rights") :
        new(false, "missing-damage-record-rights");

    private static bool HasDamageRecordRights(PlayerMobile victim, PlayerMobile actor)
    {
        if (GetRecordedAttackerSerial(victim) == actor.Serial)
        {
            return true;
        }

        foreach (var entry in victim.DamageEntries)
        {
            if (!entry.HasExpired && entry.Damager != victim && ResolvePlayerAttacker(entry.Damager) == actor)
            {
                return true;
            }
        }

        return false;
    }

    public static bool Execute(PlayerMobile executor, PlayerMobile victim)
    {
        if (victim == executor || !IsKnockedOut(victim))
        {
            return false;
        }

        var decision = ClassifyExecution(
            Enabled,
            executor.Criminal || executor.Murderer,
            HasDamageRecordRights(victim, executor)
        );

        if (!decision.Qualifies)
        {
            return false;
        }

        var countsAsMurder = ExecutionCountsAsMurder(GetReportableAttackers(victim), executor.Serial.Value);
        ClearActiveState(victim);
        MurderAdjudicationService.RegisterExecution(executor, victim, countsAsMurder);
        RecordExecutorAsAggressor(executor, victim);
        // Under stock murder reporting the victim's report gump decides the count, so an Execute that
        // counts must be reportable.
        if (countsAsMurder && !MurderAdjudicationService.Enabled)
        {
            MarkExecutionReportable(executor, victim);
        }

        victim.Hits = 0;
        victim.Kill();
        if (victim.Alive)
        {
            MurderAdjudicationService.CancelExecution(victim);
            victim.RemoveAggressor(executor);
            executor.RemoveAggressed(victim);
            return false;
        }

        ClearExecutionAggression(executor, victim);

        ShardAuditLog.Record(
            "knocked-out",
            "executed",
            executor,
            victim,
            countsAsMurder ? decision.Reason : $"{decision.Reason}; victim aggressed first, no murder count"
        );
        return true;
    }

    // Mirrors stock murder reporting: only a player whose aggression against the victim was reportable
    // (they attacked an innocent first) can be a murderer. Captured before Knocked Out clears the lists.
    private static string DescribeReportableAttackers(PlayerMobile victim)
    {
        var serials = new HashSet<uint>();
        foreach (var info in victim.Aggressors)
        {
            if (info.CanReportMurder && ResolvePlayerAttacker(info.Attacker) is { } attacker)
            {
                serials.Add(attacker.Serial.Value);
            }
        }

        return serials.Count == 0
            ? "none"
            : string.Join(',', serials.Select(s => s.ToString(CultureInfo.InvariantCulture)));
    }

    private static string? GetReportableAttackers(PlayerMobile victim) =>
        victim.Account is Account account ? account.GetTag(ReportablePrefix + SerialKey(victim)) : null;

    // A missing record (state predating it) keeps the strict behavior: the Execute counts.
    public static bool ExecutionCountsAsMurder(string? reportableAttackers, uint executorSerial) =>
        reportableAttackers is null ||
        reportableAttackers.Split(',').Contains(executorSerial.ToString(CultureInfo.InvariantCulture));

    // The corpse has already copied the aggressors. A leftover non-criminal Aggressed entry would make the victim read as
    // an enemy to the executor (stock Notoriety.CheckAggressed), so a later kill of the same victim would not be a
    // reportable murder.
    // Stock Remove* drops one match, and combat already left a criminal entry ahead of the one added here, so loop.
    public static void ClearExecutionAggression(Mobile executor, Mobile victim)
    {
        while (victim.Aggressors.Exists(info => info.Attacker == executor))
        {
            victim.RemoveAggressor(executor);
        }

        while (executor.Aggressed.Exists(info => info.Defender == victim))
        {
            executor.RemoveAggressed(victim);
        }
    }

    private static void MarkExecutionReportable(Mobile executor, Mobile victim)
    {
        foreach (var info in victim.Aggressors)
        {
            if (info.Attacker == executor)
            {
                info.CanReportMurder = true;
            }
        }
    }

    // Knocking out clears the victim's aggressor lists; the corpse copies them at death, so restore the executor.
    public static void RecordExecutorAsAggressor(Mobile executor, Mobile victim)
    {
        foreach (var info in victim.Aggressors)
        {
            if (info.Attacker == executor)
            {
                info.Refresh();
                return;
            }
        }

        victim.Aggressors.Add(AggressorInfo.Create(executor, victim, false));
        executor.Aggressed.Add(AggressorInfo.Create(executor, victim, false));
    }

    public static bool IsKnockedOut(Mobile mobile)
    {
        if (!Enabled || mobile is not PlayerMobile player || player.Account is not Account account)
        {
            return false;
        }

        if (IsStaff(player))
        {
            ClearActiveState(player);
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

        ClearActiveState(player);
        WakePlayer(player, "You recover from being Knocked Out.");
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
        if (player.Account is not Account)
        {
            return false;
        }

        var wasKnockedOut = GetUntilUtc(player) is not null;
        ClearActiveState(player);

        if (wasKnockedOut)
        {
            WakePlayer(player, "A staff member has recovered you from Knocked Out.");
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
            yield return Enabled
                ? "Outside Hot Zones, only a criminal/red with recorded encounter rights may loot a Knocked Out player. In Hot Zones anyone may, and a blue who does becomes criminal. Execution needs a criminal/red actor with damage-record rights everywhere."
                : "Knocked Out looting and execution are feature-gated.";
        }
    }

    public static KnockedOutDecision Classify(bool featureEnabled, bool player, bool ordinaryBlue, bool hotZone) =>
        !featureEnabled ? new(false, "feature-disabled") :
        !player ? new(false, "not-player") :
        !ordinaryBlue ? new(false, "not-ordinary-blue") :
        hotZone ? new(true, "ordinary-blue-hot-zone") :
        new(true, "ordinary-blue-safe-world");

    public static KnockedOutDecision ClassifyDamage(
        bool featureEnabled,
        bool player,
        bool ordinaryBlue,
        bool hotZone,
        bool attributablePlayerDamage,
        bool activeEncounter
    ) => !featureEnabled ? new(false, "feature-disabled") :
        !player ? new(false, "not-player") :
        !ordinaryBlue ? new(false, "not-ordinary-blue") :
        !attributablePlayerDamage ? new(false, "damage-not-attributable-to-player") :
        hotZone ? new(true, "ordinary-blue-hot-zone-player-damage") :
        !activeEncounter ? new(false, "missing-active-encounter") :
        new(true, "ordinary-blue-player-encounter");

    private static void ScheduleRecovery(PlayerMobile player)
    {
        var until = GetUntilUtc(player);
        if (until is not { } expiry || expiry <= Core.Now)
        {
            return;
        }

        Server.Timer.DelayCall(expiry - Core.Now, static pm =>
        {
            if (pm.Deleted || pm.Account is not Account)
            {
                return;
            }

            ClearActiveState(pm);
            WakePlayer(pm, "You recover from being Knocked Out.");
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

    private static void ClearCombatEffects(PlayerMobile player)
    {
        BandageContext.GetContext(player)?.StopHeal();
        player.Poison = null;
        player.Paralyzed = false;
        player.Frozen = false;
        BleedAttack.EndBleed(player, false);
        MortalStrike.EndWound(player);
        player.Spell?.OnCasterKilled();
    }

    private static void WakePlayer(PlayerMobile player, string message)
    {
        player.Hits = Math.Max(1, player.HitsMax / 2);
        player.Stam = Math.Max(1, player.StamMax / 2);
        player.Mana = Math.Max(0, player.ManaMax / 2);
        player.Warmode = false;
        player.Combatant = null;
        player.Target = null;
        player.SendMessage(message);
    }

    private static bool AllowBeneficial(Mobile from, Mobile target)
    {
        if (!IsStaff(target) && IsKnockedOut(target))
        {
            return false;
        }

        if (_stockAllowBeneficial is null)
        {
            return true;
        }

        var current = Mobile.AllowBeneficialHandler;
        Mobile.AllowBeneficialHandler = _stockAllowBeneficial;
        try
        {
            return _stockAllowBeneficial(from, target);
        }
        finally
        {
            Mobile.AllowBeneficialHandler = current;
        }
    }

    private static bool BlockHeal(Mobile target, Mobile from, int amount) => !IsStaff(target) && IsKnockedOut(target);

    private static bool BlockCurePoison(Mobile target, Mobile from) => !IsStaff(target) && IsKnockedOut(target);

    private static bool CanTarget(Mobile mobile) => IsStaff(mobile) || !IsKnockedOut(mobile);

    public static bool CanPerformAction(Mobile mobile) => !ShouldBlockActions(Enabled, IsKnockedOut(mobile), IsStaff(mobile));

    public static bool ShouldBlockActions(bool featureEnabled, bool knockedOut) => featureEnabled && knockedOut;

    public static bool ShouldBlockActions(bool featureEnabled, bool knockedOut, bool staff) =>
        featureEnabled && knockedOut && !staff;

    private static bool IsStaff(Mobile mobile) => mobile.AccessLevel > AccessLevel.Player;

    private static void ClearActiveState(PlayerMobile player)
    {
        if (player.Account is Account account)
        {
            account.RemoveTag(UntilPrefix + SerialKey(player));
            account.RemoveTag(AttackerPrefix + SerialKey(player));
            account.RemoveTag(ReportablePrefix + SerialKey(player));
        }
    }

    private static string SerialKey(PlayerMobile player) =>
        player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

    /// <summary>
    /// Resolves a damage source to a player only when ownership is explicit. Independent monsters,
    /// hazards, and other unowned sources intentionally return null. Nested controlled/summoned
    /// creatures are followed until their player owner is found.
    /// </summary>
    public static PlayerMobile? ResolvePlayerAttacker(Mobile? from)
    {
        var current = from;

        for (var depth = 0; current is not null && depth < 8; depth++)
        {
            if (current is PlayerMobile player)
            {
                return player;
            }

            if (current is not BaseCreature creature)
            {
                return null;
            }

            var master = creature.GetMaster();
            if (master is null || master == current)
            {
                return null;
            }

            current = master;
        }

        return null;
    }

    /// <summary>Returns the player recorded when this victim entered Knocked Out, if still online.</summary>
    public static PlayerMobile? GetRecordedAttacker(PlayerMobile player)
    {
        var serial = GetRecordedAttackerSerial(player);
        return serial.IsValid ? World.FindMobile(serial) as PlayerMobile : null;
    }

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
public readonly record struct KnockedOutExecutionDecision(bool Qualifies, string Reason);
