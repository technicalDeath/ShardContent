using System.Globalization;
using Server;
using Server.Accounting;
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
        Mobile.CanBeDamagedHandler = mobile => !IsKnockedOut(mobile);
        Mobile.CanTargetHandler = CanTarget;
        Mobile.HealHandler = BlockHeal;
        Mobile.CurePoisonHandler = BlockCurePoison;
        Stealing.KnockedOutLoot = CanLootKnockedOut;
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
        Mobile.CanBeDamagedHandler = mobile => !IsKnockedOut(mobile);
        Mobile.CanTargetHandler = CanTarget;
        Mobile.HealHandler = BlockHeal;
        Mobile.CurePoisonHandler = BlockCurePoison;
        Stealing.KnockedOutLoot = CanLootKnockedOut;
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
        if (victim is not PlayerMobile player)
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
            hotZone: ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true,
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

    public static KnockedOutExecutionDecision ClassifyExecution(
        bool featureEnabled, bool hotZone, bool actorIsCriminalOrMurderer, bool recordedTargetRights
    ) => !featureEnabled ? new(false, "feature-disabled") :
        hotZone ? new(false, "hot-zone-execution-deferred") :
        !actorIsCriminalOrMurderer ? new(false, "actor-not-criminal-or-murderer") :
        recordedTargetRights ? new(true, "recorded-target-rights") :
        new(false, "missing-target-rights");

    public static bool Execute(PlayerMobile executor, PlayerMobile victim)
    {
        if (MurderAdjudicationService.Enabled == false || victim == executor || !IsKnockedOut(victim))
        {
            return false;
        }

        var decision = ClassifyExecution(
            Enabled,
            ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true,
            executor.Criminal || executor.Murderer,
            GetRecordedAttackerSerial(victim) == executor.Serial
        );

        if (!decision.Qualifies)
        {
            return false;
        }

        ClearActiveState(victim);
        MurderAdjudicationService.RegisterExecution(executor, victim);
        victim.Hits = 0;
        victim.Kill();
        if (victim.Alive)
        {
            MurderAdjudicationService.CancelExecution(victim);
            return false;
        }

        ShardAuditLog.Record("knocked-out", "executed", executor, victim, decision.Reason);
        return true;
    }

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
                ? "Encounter-authorized no-skill looting and execution are active outside Hot Zones; Hot-Zone execution remains deferred."
                : "Encounter-authorized no-skill looting and execution are feature-gated; Hot-Zone execution remains deferred.";
        }
    }

    public static KnockedOutDecision Classify(bool featureEnabled, bool player, bool ordinaryBlue, bool hotZone) =>
        !featureEnabled ? new(false, "feature-disabled") :
        !player ? new(false, "not-player") :
        !ordinaryBlue ? new(false, "not-ordinary-blue") :
        hotZone ? new(false, "hot-zone-resolution-deferred") :
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
        hotZone ? new(false, "hot-zone-resolution-deferred") :
        !attributablePlayerDamage ? new(false, "damage-not-attributable-to-player") :
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
        if (IsKnockedOut(target))
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

    private static bool BlockHeal(Mobile target, Mobile from, int amount) => IsKnockedOut(target);

    private static bool BlockCurePoison(Mobile target, Mobile from) => IsKnockedOut(target);

    private static bool CanTarget(Mobile mobile) => !IsKnockedOut(mobile);

    private static void ClearActiveState(PlayerMobile player)
    {
        if (player.Account is Account account)
        {
            account.RemoveTag(UntilPrefix + SerialKey(player));
            account.RemoveTag(AttackerPrefix + SerialKey(player));
        }
    }

    private static string SerialKey(PlayerMobile player) =>
        player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

    private static PlayerMobile? ResolvePlayerAttacker(Mobile from) =>
        from as PlayerMobile ?? (from as BaseCreature)?.GetMaster() as PlayerMobile;

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
