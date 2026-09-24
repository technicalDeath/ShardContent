using System.Globalization;
using Server;
using Server.Accounting;
using Server.Engines.ConPVP;
using Server.Guilds;
using Server.Mobiles;
using Server.Misc;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Alpha 2's first safe-world foundation: persistent blue-player PvP Intent and one central
/// decision point for direct player hostility. The feature remains disabled until the shard policy
/// enables SafeWorld; while disabled, the pinned ModernUO notoriety handler remains authoritative.
/// </summary>
public static class PvpIntentService
{
    private const string TagPrefix = "BritanniaRenaissance.PvpIntent.";
    private const string EncounterTagPrefix = TagPrefix + "Encounter.";
    private static readonly Dictionary<int, bool> IntentByCharacter = new();
    private static readonly Dictionary<EncounterKey, EncounterSnapshot> Encounters = new();
    private static AllowHarmfulHandler? _stockAllowHarmful;
    private static NotorietyHandler? _stockNotoriety;
    private static bool _configured;

    public static bool SafeWorldEnabled => ShardRulesConfiguration.Settings?.FeatureFlags.SafeWorld == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        _stockAllowHarmful = Mobile.AllowHarmfulHandler;
        _stockNotoriety = Notoriety.Handler;
        Mobile.AllowHarmfulHandler = AllowHarmful;
        Notoriety.Handler = ComputeNotoriety;
        EventSink.AggressiveAction += CaptureEncounter;
    }

    /// <summary>
    /// Rebinds the presentation delegate after ModernUO's stock Initialize handlers have run.
    /// Some hosts invoke external assembly Initialize methods before the stock UOContent
    /// assembly, so the server-started lifecycle callback is the authoritative final boundary.
    /// </summary>
    public static void RebindAfterStockHandlers()
    {
        Configure();

        if (Notoriety.Handler?.Method.DeclaringType == typeof(PvpIntentService))
        {
            return;
        }

        _stockNotoriety = Notoriety.Handler;
        Notoriety.Handler = ComputeNotoriety;
    }

    public static bool IsIntentEnabled(PlayerMobile player)
    {
        var serial = unchecked((int)player.Serial.Value);
        if (IntentByCharacter.TryGetValue(serial, out var enabled))
        {
            return enabled;
        }

        enabled = LoadIntent(player);
        IntentByCharacter[serial] = enabled;
        return enabled;
    }

    public static bool ToggleIntent(PlayerMobile player)
    {
        if (!SafeWorldEnabled)
        {
            player.SendMessage("PvP Intent is not enabled on this shard yet.");
            return false;
        }

        if (player.Criminal || player.Murderer)
        {
            player.SendMessage("Criminals and murderers cannot change PvP Intent.");
            return IsIntentEnabled(player);
        }

        var enabled = !IsIntentEnabled(player);
        IntentByCharacter[unchecked((int)player.Serial.Value)] = enabled;
        SaveIntent(player, enabled);
        ShardAuditLog.Record("intent", enabled ? "enabled" : "disabled", player);

        // Intent changes alter the notoriety that every nearby client must use for this
        // character.  Re-send the normal mobile-incoming packet so clients refresh the
        // target's hue/notoriety immediately instead of retaining a stale Innocent flag
        // until the next movement or relog.
        player.SendIncomingPacket();

        player.SendMessage(enabled ? "PvP Intent enabled: other players may challenge you." :
            "PvP Intent disabled for new opponents.");
        return enabled;
    }

    public static IEnumerable<string> DescribeStatus(Mobile mobile)
    {
        yield return $"Safe-world PvP policy enabled: {SafeWorldEnabled}.";

        if (mobile is PlayerMobile player)
        {
            yield return $"PvP Intent: {(IsIntentEnabled(player) ? "enabled ([Intent])" : "disabled")}.";
            yield return $"Notoriety handler: {Notoriety.Handler?.Method.DeclaringType?.FullName}.{Notoriety.Handler?.Method.Name ?? "<none>"}.";
            if (player.Criminal || player.Murderer)
            {
                yield return "Intent changes are unavailable while criminal or murderer status is active.";
            }

            // Keep the policy decision observable while Alpha 2 is being validated. This is
            // deliberately limited to nearby player mobiles and reports the same value that the
            // outgoing mobile packet uses, so staff can distinguish a server-policy result from
            // a stale client presentation without enabling any additional combat behavior.
            var nearbyLines = new List<string>();
            foreach (var nearbyMobile in player.GetMobilesInRange(18))
            {
                if (nearbyMobile is not PlayerMobile nearby || nearby == player || !player.CanSee(nearby))
                {
                    continue;
                }

                nearbyLines.Add(
                    $"Nearby notoriety: {nearby.Name} = {DescribeNotoriety(Notoriety.Compute(player, nearby))}."
                );
            }

            foreach (var nearbyLine in nearbyLines)
            {
                yield return nearbyLine;
            }
        }
    }

    private static string DescribeNotoriety(int notoriety) => notoriety switch
    {
        Notoriety.Innocent => "Innocent",
        Notoriety.Ally => "Ally",
        Notoriety.CanBeAttacked => "CanBeAttacked",
        Notoriety.Criminal => "Criminal",
        Notoriety.Enemy => "Enemy",
        Notoriety.Murderer => "Murderer",
        Notoriety.Invulnerable => "Invulnerable",
        _ => notoriety.ToString(CultureInfo.InvariantCulture)
    };

    /// <summary>
    /// Pure policy rule used by regression tests and the live handler. A target who has opted into
    /// Intent is exposed; two opted-in blues may duel; existing aggression relationships persist.
    /// Criminal/murderer targets remain lawful everywhere. The attacker must still pass the stock
    /// blessedness, life, region and visibility checks before this rule is reached.
    /// </summary>
    public static bool IsSafeWorldPlayerAttackAllowed(
        bool targetIsCriminalOrMurderer,
        bool targetHasIntent,
        bool attackerHasIntent,
        bool existingRetaliation)
    {
        return targetIsCriminalOrMurderer || targetHasIntent || attackerHasIntent && targetHasIntent ||
               existingRetaliation;
    }

    public static int GetIntentNotoriety(bool intentEnabled, bool targetIsCriminal, bool targetIsMurderer,
        int stockNotoriety) =>
        intentEnabled && !targetIsCriminal && !targetIsMurderer ? Notoriety.CanBeAttacked : stockNotoriety;

    public static bool WasIntentClassified(PlayerMobile killer, PlayerMobile victim)
    {
        var key = new EncounterKey(killer, victim);
        return TryGetActiveEncounter(killer, victim, key, out var snapshot) && snapshot.VictimWasIntentClassified;
    }

    /// <summary>Returns whether a target-specific direct encounter is still active.</summary>
    public static bool HasActiveEncounter(PlayerMobile attacker, PlayerMobile victim)
    {
        var key = new EncounterKey(attacker, victim);
        return TryGetActiveEncounter(attacker, victim, key, out _);
    }

    private static void CaptureEncounter(AggressiveActionEventArgs e)
    {
        if (!SafeWorldEnabled || e.Aggressed is not PlayerMobile defender)
        {
            return;
        }

        var attacker = e.Aggressor as PlayerMobile;
        if (attacker is null && e.Aggressor is BaseCreature creature)
        {
            attacker = creature.GetMaster() as PlayerMobile;
        }

        if (attacker is null || attacker == defender)
        {
            return;
        }

        var snapshot = new EncounterSnapshot(
            IsIntentEnabled(defender) && !defender.Criminal && !defender.Murderer,
            Core.Now.AddMinutes(2)
        );

        Encounters[new EncounterKey(attacker, defender)] = snapshot;
        SaveEncounterSnapshot(attacker, defender, snapshot);
        ShardAuditLog.Record(
            "encounter",
            snapshot.VictimWasIntentClassified ? "intent-classified" : "ordinary",
            attacker,
            defender,
            "AggressiveAction snapshot"
        );
    }

    private static int ComputeNotoriety(Mobile source, Mobile target)
    {
        var stockNotoriety = _stockNotoriety?.Invoke(source, target) ?? Notoriety.CanBeAttacked;

        if (!SafeWorldEnabled || target is not PlayerMobile player)
        {
            return stockNotoriety;
        }

        return GetIntentNotoriety(
            IsIntentEnabled(player),
            player.Criminal,
            player.Murderer,
            stockNotoriety
        );
    }

    private static bool AllowHarmful(Mobile from, Mobile target)
    {
        if (KnockedOutService.IsKnockedOut(target))
        {
            return false;
        }

        if (!SafeWorldEnabled || target is not PlayerMobile defender)
        {
            return InvokeStock(from, target);
        }

        var attacker = from as PlayerMobile;
        if (attacker is null && from is BaseCreature creature)
        {
            attacker = creature.GetMaster() as PlayerMobile;
        }

        if (attacker is null || attacker == defender)
        {
            return InvokeStock(from, target);
        }

        // Preserve the stock safe-zone, duel, guild, design and region decisions. On an unrestricted
        // Felucca map the stock handler intentionally returns true for every player pair, so the
        // Alpha 2 policy must run before accepting that result; otherwise SafeWorld would be a no-op.
        if (from.Region.IsPartOf<SafeZone>() || target.Region.IsPartOf<SafeZone>())
        {
            return false;
        }

        var mapHasHarmfulRestrictions = (from.Map?.Rules & MapRules.HarmfulRestrictions) != 0;
        var stockAllowed = InvokeStock(from, target);

        if (mapHasHarmfulRestrictions && stockAllowed)
        {
            return true;
        }

        var targetIsCriminalOrMurderer = defender.Criminal || defender.Murderer;
        var targetHasIntent = IsIntentEnabled(defender) && !defender.Criminal && !defender.Murderer;
        var attackerHasIntent = IsIntentEnabled(attacker) && !attacker.Criminal && !attacker.Murderer;
        var existingRetaliation = HasExistingRelationship(attacker, defender);

        if (IsGuildWarOrDuel(attacker, defender))
        {
            return true;
        }

        var allowed = IsSafeWorldPlayerAttackAllowed(
            targetIsCriminalOrMurderer,
            targetHasIntent,
            attackerHasIntent,
            existingRetaliation
        );

        if (!allowed)
        {
            ShardAuditLog.Record("hostility", "denied", attacker, defender, "ordinary-blue safe-world policy");
        }

        return allowed;
    }

    private static bool IsGuildWarOrDuel(PlayerMobile attacker, PlayerMobile defender)
    {
        if (attacker.DuelContext?.Started == true && attacker.DuelContext == defender.DuelContext)
        {
            return true;
        }

        if (attacker.DuelContext?.Started == true || defender.DuelContext?.Started == true)
        {
            return false;
        }

        var attackerGuild = NotorietyHandlers.GetGuildFor(attacker.Guild as Guild, attacker);
        var defenderGuild = NotorietyHandlers.GetGuildFor(defender.Guild as Guild, defender);

        return attackerGuild != null && defenderGuild != null &&
               (attackerGuild == defenderGuild || attackerGuild.IsAlly(defenderGuild) ||
                attackerGuild.IsEnemy(defenderGuild));
    }

    private static bool InvokeStock(Mobile from, Mobile target)
    {
        if (_stockAllowHarmful is null)
        {
            return true;
        }

        // Region.AllowHarmful consults Mobile.AllowHarmfulHandler again. Temporarily restore the
        // captured stock delegate so the fallback remains recursive-safe and preserves all stock
        // UOR/duel/guild restrictions.
        var current = Mobile.AllowHarmfulHandler;
        Mobile.AllowHarmfulHandler = _stockAllowHarmful;
        try
        {
            return _stockAllowHarmful(from, target);
        }
        finally
        {
            Mobile.AllowHarmfulHandler = current;
        }
    }

    private static bool HasExistingRelationship(Mobile attacker, Mobile defender)
    {
        foreach (var info in attacker.Aggressors)
        {
            if (!info.Expired && info.Attacker == defender)
            {
                return true;
            }
        }

        foreach (var info in attacker.Aggressed)
        {
            if (!info.Expired && info.Defender == defender)
            {
                return true;
            }
        }

        return false;
    }

    private static bool LoadIntent(PlayerMobile player)
    {
        if (player.Account is not Account account)
        {
            return false;
        }

        return string.Equals(
            account.GetTag(TagPrefix + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture)),
            "1",
            StringComparison.Ordinal
        );
    }

    private static void SaveIntent(PlayerMobile player, bool enabled)
    {
        if (player.Account is Account account)
        {
            account.SetTag(
                TagPrefix + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture),
                enabled ? "1" : "0"
            );
        }
    }

    private static void SaveEncounterSnapshot(
        PlayerMobile attacker,
        PlayerMobile defender,
        EncounterSnapshot snapshot)
    {
        if (attacker.Account is Account account)
        {
            account.SetTag(
                EncounterTag(attacker, defender),
                $"{(snapshot.VictimWasIntentClassified ? '1' : '0')}|{snapshot.ExpiresUtc:O}"
            );
        }
    }

    private static bool LoadEncounterSnapshot(
        PlayerMobile attacker,
        PlayerMobile defender,
        out EncounterSnapshot snapshot)
    {
        snapshot = default;
        if (attacker.Account is not Account account)
        {
            return false;
        }

        var value = account.GetTag(EncounterTag(attacker, defender));
        var parts = value?.Split('|', 2);
        if (parts?.Length != 2 || (parts[0] != "0" && parts[0] != "1") ||
            !DateTime.TryParse(
                parts[1],
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var expiresUtc
            ))
        {
            return false;
        }

        snapshot = new EncounterSnapshot(parts[0] == "1", expiresUtc.ToUniversalTime());
        return true;
    }

    private static bool TryGetActiveEncounter(
        PlayerMobile attacker,
        PlayerMobile defender,
        EncounterKey key,
        out EncounterSnapshot snapshot)
    {
        if (Encounters.TryGetValue(key, out snapshot))
        {
            return snapshot.ExpiresUtc > Core.Now;
        }

        if (LoadEncounterSnapshot(attacker, defender, out snapshot) && snapshot.ExpiresUtc > Core.Now)
        {
            Encounters[key] = snapshot;
            return true;
        }

        snapshot = default;
        return false;
    }

    private static string EncounterTag(PlayerMobile attacker, PlayerMobile defender) =>
        EncounterTagPrefix + unchecked((int)attacker.Serial.Value).ToString("X8", CultureInfo.InvariantCulture) + "." +
        unchecked((int)defender.Serial.Value).ToString("X8", CultureInfo.InvariantCulture);
}

internal readonly record struct EncounterKey(int AttackerSerial, int DefenderSerial)
{
    public EncounterKey(PlayerMobile attacker, PlayerMobile defender) : this(
        unchecked((int)attacker.Serial.Value),
        unchecked((int)defender.Serial.Value))
    {
    }
}

internal readonly record struct EncounterSnapshot(bool VictimWasIntentClassified, DateTime ExpiresUtc);
