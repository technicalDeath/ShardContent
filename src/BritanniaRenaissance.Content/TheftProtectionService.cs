using System.Globalization;
using System.Diagnostics;
using ModernUO.CodeGeneratedEvents;
using Server;
using Server.Accounting;
using Server.Items;
using Server.Mobiles;
using Server.SkillHandlers;
using Server.Engines.CharacterCreation;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Feature-gated Backpack Ward and invisible monster-corpse Loot Protection Ward behavior layered
/// around stock Stealing. Bank polygons and the Cool Dungeon remain separate region work.
/// </summary>
public static class TheftProtectionService
{
    private const string ProtectionTagPrefix = "BritanniaRenaissance.BackpackWard.ProtectedUntil.";
    private const string LootProtectionTagPrefix = "BritanniaRenaissance.LootWard.";
    private const string LootEntitlementTagPrefix = "BritanniaRenaissance.LootWard.Entitlement.";
    private const string LootEntitlementVersion = "1";
    private const int EntitlementMigrationBatchSize = 64;
    private static bool _configured;
    private static Queue<PlayerMobile>? _entitlementMigration;
    private static bool _entitlementMigrationScheduled;

    public static readonly TimeSpan LootProtectionDuration = TimeSpan.FromMinutes(10);

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.TheftProtection == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Stealing.TheftEligibility = CanAttemptTheft;
        Stealing.TheftResolved = ResolveTheft;
        Corpse.LootEligibility = CanLiftCorpseItem;
        Corpse.LootResolved = RecordCorpseTransfer;
        EventSink.WorldLoad += BeginEntitlementMigration;
    }

    [OnEvent(nameof(PlayerMobile.PlayerLoginEvent))]
    public static void OnPlayerLogin(PlayerMobile player) => EnsureLootProtectionEntitlement(player, "login");

    [OnEvent(nameof(CharacterCreation.CharacterCreatedEvent))]
    public static void IssueStarterWard(CharacterCreatedEventArgs args)
    {
        if (!Enabled || args.Mobile is not PlayerMobile player)
        {
            return;
        }

        // The invisible entitlement is independent of the physical starter item and must not be
        // skipped merely because the new character already has a backpack ward or a delayed bag.
        EnsureLootProtectionEntitlement(player, "character-creation");

        if (player.Backpack is null || FindEligibleWard(player) is not null)
        {
            return;
        }

        var ward = new BackpackWard();
        ward.TryBindTo(player);
        player.Backpack.DropItem(ward);
        ShardAuditLog.Record("theft", "starter-ward-issued", player, details: "bound to character account");
    }

    public static bool IsProtectionWindowActive(DateTime nowUtc, DateTime protectedUntilUtc) =>
        protectedUntilUtc.ToUniversalTime() > nowUtc.ToUniversalTime();

    public static double AdditionalDetectionChance(int successfulUndetectedThefts) =>
        successfulUndetectedThefts switch
        {
            <= 0 => 0.0,
            1 => 0.25,
            2 => 0.50,
            _ => 1.0
        };

    public static IEnumerable<string> DescribeStatus(Mobile mobile)
    {
        yield return $"Backpack Ward protection enabled: {Enabled}.";
        yield return "Stock stealing success, criminality and snooping remain authoritative.";
        yield return Enabled
            ? "Starter wards bind to the character account; configured bank/Cool polygon checks are active; corpse repeat protection is enabled outside Hot Zones."
            : "Starter wards bind to the character account; bank polygons and Cool Dungeon restrictions remain deferred; corpse repeat protection is enabled with this gate outside Hot Zones.";
        foreach (var line in TheftRegionPolicy.Describe())
        {
            yield return line;
        }

        yield return $"Loot entitlement migration pending: {_entitlementMigration?.Count ?? 0}; scheduled: {_entitlementMigrationScheduled}.";

        if (mobile is PlayerMobile player)
        {
            yield return $"Equipped-backpack wards present: {(FindEligibleWard(player) is not null ? "yes" : "no")}.";
            yield return $"Loot Protection entitlement: {(HasLootProtectionEntitlement(player) ? "present" : Enabled ? "pending migration" : "not active")}.";
        }
    }

    private static bool CanAttemptTheft(Mobile thief, Item item, Mobile victim)
    {
        if (!Enabled || victim is not PlayerMobile playerVictim)
        {
            return true;
        }

        if (TheftRegionPolicy.IsBankProtectionRegionForEither(thief, playerVictim))
        {
            thief.SendMessage("You cannot steal from players in this bank protection area.");
            ShardAuditLog.Record("theft", "bank-region-denied", thief, playerVictim);
            return false;
        }

        if (TheftRegionPolicy.IsCoolDungeonRegionForEither(thief, playerVictim))
        {
            thief.SendMessage("Direct player stealing is disabled in this dungeon.");
            ShardAuditLog.Record("theft", "cool-region-denied", thief, playerVictim);
            return false;
        }

        if (item is BackpackWard)
        {
            thief.SendMessage("That ward cannot be stolen.");
            ShardAuditLog.Record("theft", "ward-denied", thief, victim, "ward item");
            return false;
        }

        if (IsProtectionActive(playerVictim))
        {
            thief.SendMessage("That backpack is protected from stealing for a short time.");
            ShardAuditLog.Record("theft", "protected-denied", thief, playerVictim, "120-second backpack ward");
            return false;
        }

        return true;
    }

    private static void ResolveTheft(Mobile thief, Item item, Mobile victim, Item stolen, bool caught)
    {
        if (!Enabled || victim is not PlayerMobile playerVictim || thief is not PlayerMobile playerThief ||
            playerVictim == playerThief)
        {
            return;
        }

        var ward = FindEligibleWard(playerVictim);
        if (ward is null)
        {
            return;
        }

        // Ordinary victim detection, including a detected failure, consumes one physical ward
        // after the stock outcome has resolved.
        if (caught)
        {
            ActivateProtection(playerVictim, ward);
            ShardAuditLog.Record("theft", "ward-consumed", playerThief, playerVictim, "stock detection");
            return;
        }

        // Only an undetected successful transfer advances the per-thief account counter.
        if (stolen is null || playerThief.Account is not Account account)
        {
            return;
        }

        var successes = ward.RecordSuccessfulTheft(account.Username);
        if (AdditionalDetectionChance(successes) >= Utility.RandomDouble())
        {
            playerVictim.SendMessage("You detect a theft from your backpack.");
            ActivateProtection(playerVictim, ward);
            ShardAuditLog.Record("theft", "ward-triggered", playerThief, playerVictim, $"undetectedSuccesses={successes}");
        }
    }

    private static bool CanLiftCorpseItem(Mobile looter, Corpse corpse, Item item)
    {
        if (!Enabled || ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true ||
            corpse.OwnerWasBaseCreature != true || !corpse.IsCriminalAction(looter) ||
            looter.Account is not Account account)
        {
            return true;
        }

        if (looter is PlayerMobile player)
        {
            EnsureLootProtectionEntitlement(player, "corpse-loot");
        }

        var tag = LootProtectionTag(corpse, account);
        if (!DateTime.TryParse(
                account.GetTag(tag),
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var protectedUntil
            ) || !IsProtectionWindowActive(Core.Now, protectedUntil))
        {
            return true;
        }

        looter.SendMessage("You cannot repeatedly loot this monster's corpse right now.");
        ShardAuditLog.Record("corpse-loot", "repeat-denied", looter, corpse.Owner, "10-minute offender protection");
        return false;
    }

    private static void RecordCorpseTransfer(Mobile looter, Corpse corpse, Item item)
    {
        if (!Enabled || ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true ||
            corpse.OwnerWasBaseCreature != true || !corpse.IsCriminalAction(looter) ||
            looter.Account is not Account account)
        {
            return;
        }

        if (looter is PlayerMobile player)
        {
            EnsureLootProtectionEntitlement(player, "corpse-transfer");
        }

        account.SetTag(
            LootProtectionTag(corpse, account),
            Core.Now.Add(LootProtectionDuration).ToString("O", CultureInfo.InvariantCulture)
        );
        ShardAuditLog.Record("corpse-loot", "first-transfer", looter, corpse.Owner, "10-minute offender protection armed");
    }

    private static BackpackWard? FindEligibleWard(PlayerMobile victim)
    {
        var backpack = victim.Backpack;
        if (backpack is null)
        {
            return null;
        }

        var wards = new List<BackpackWard>();
        CollectWards(backpack, wards, victim);
        wards.Sort(static (left, right) => left.Serial.Value.CompareTo(right.Serial.Value));
        return wards.Count == 0 ? null : wards[0];
    }

    private static void CollectWards(Container container, List<BackpackWard> wards, PlayerMobile owner)
    {
        foreach (var item in container.Items)
        {
            if (item is BackpackWard ward && !ward.Deleted && ward.TryBindTo(owner))
            {
                wards.Add(ward);
            }

            if (item is Container child)
            {
                CollectWards(child, wards, owner);
            }
        }
    }

    private static bool IsProtectionActive(PlayerMobile victim)
    {
        if (victim.Account is not Account account ||
            !DateTime.TryParse(
                account.GetTag(ProtectionTag(victim)),
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var protectedUntil
            ))
        {
            return false;
        }

        return IsProtectionWindowActive(Core.Now, protectedUntil);
    }

    private static void ActivateProtection(PlayerMobile victim, BackpackWard ward)
    {
        if (victim.Account is Account account)
        {
            account.SetTag(
                ProtectionTag(victim),
                Core.Now.AddSeconds(120).ToString("O", CultureInfo.InvariantCulture)
            );
        }

        victim.SendMessage("Your backpack ward activates and protects you from stealing for two minutes.");
        ward.Delete();
    }

    private static string ProtectionTag(PlayerMobile victim) =>
        ProtectionTagPrefix + victim.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

    public static bool IsLootProtectionEntitlementCurrent(string? value) =>
        string.Equals(value, LootEntitlementVersion, StringComparison.Ordinal);

    public static bool HasLootProtectionEntitlement(PlayerMobile player) =>
        player.Account is Account account &&
        IsLootProtectionEntitlementCurrent(account.GetTag(LootEntitlementTag(player)));

    private static bool EnsureLootProtectionEntitlement(PlayerMobile player, string reason)
    {
        if (!Enabled || player.Account is not Account account || HasLootProtectionEntitlement(player))
        {
            return false;
        }

        account.SetTag(LootEntitlementTag(player), LootEntitlementVersion);
        ShardAuditLog.Record("corpse-loot", "entitlement-migrated", player, details: reason);
        return true;
    }

    private static void BeginEntitlementMigration()
    {
        if (!Enabled || _entitlementMigrationScheduled)
        {
            return;
        }

        _entitlementMigration = new Queue<PlayerMobile>(World.Mobiles.Values.OfType<PlayerMobile>());
        _entitlementMigrationScheduled = true;
        Server.Timer.DelayCall(TimeSpan.Zero, ProcessEntitlementMigration);
    }

    private static void ProcessEntitlementMigration()
    {
        _entitlementMigrationScheduled = false;

        if (!Enabled || _entitlementMigration is null)
        {
            _entitlementMigration = null;
            return;
        }

        var startedAt = Stopwatch.GetTimestamp();
        var processed = 0;
        while (_entitlementMigration.Count > 0 && processed < EntitlementMigrationBatchSize &&
               (processed == 0 || Stopwatch.GetElapsedTime(startedAt).TotalMilliseconds < 2))
        {
            var player = _entitlementMigration.Dequeue();
            processed++;
            if (!player.Deleted)
            {
                EnsureLootProtectionEntitlement(player, "world-load-migration");
            }
        }

        if (_entitlementMigration.Count > 0)
        {
            _entitlementMigrationScheduled = true;
            Server.Timer.DelayCall(TimeSpan.Zero, ProcessEntitlementMigration);
        }
        else
        {
            _entitlementMigration = null;
        }
    }

    private static string LootEntitlementTag(PlayerMobile player) =>
        LootEntitlementTagPrefix + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture);

    private static string LootProtectionTag(Corpse corpse, Account account) =>
        LootProtectionTagPrefix + corpse.Serial.Value.ToString("X8", CultureInfo.InvariantCulture) + "." +
        account.Username;
}
