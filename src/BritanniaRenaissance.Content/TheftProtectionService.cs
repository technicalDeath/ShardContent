using System.Globalization;
using Server;
using Server.Accounting;
using Server.Items;
using Server.Mobiles;
using Server.SkillHandlers;
using Server.Engines.CharacterCreation;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Feature-gated Backpack Ward, invisible monster-corpse Loot Protection Ward, and explicit
/// bank/Cool-Dungeon boundary feedback layered around stock Stealing.
/// </summary>
public static class TheftProtectionService
{
    private const string LootProtectionTagPrefix = "BritanniaRenaissance.LootWard.";
    private const string StarterWardTagPrefix = "BritanniaRenaissance.StarterWard.v1.";
    private static bool _configured;
    private static readonly Dictionary<Serial, TheftRegionState> RegionStates = new();

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
        EventSink.Connected += OnConnected;
        EventSink.Disconnected += OnDisconnected;
        EventSink.Movement += OnMovement;
        CharacterCreation.CharacterCreatedHandler += IssueStarterWard;
        BackpackWardService.Configure();
    }

    public static void IssueStarterWard(CharacterCreatedEventArgs args)
    {
        if (!Enabled || args.Mobile is not PlayerMobile player)
        {
            return;
        }

        if (player.Backpack is null || player.Account is not Account account)
        {
            return;
        }

        var issuanceTag = $"{StarterWardTagPrefix}{player.Serial.Value}";
        if (account.GetTag(issuanceTag) is not null)
        {
            return;
        }

        var ward = new BackpackWard();
        if (!ward.MarkStarterIssued(player))
        {
            ward.Delete();
            return;
        }

        player.Backpack.DropItem(ward);
        account.SetTag(issuanceTag, "issued");
        ShardAuditLog.Record("theft", "starter-ward-issued", player, details: "bound to character");
    }

    private static void OnConnected(Mobile mobile)
    {
        if (mobile is PlayerMobile player)
        {
            ObserveTheftRegions(player, notify: false);
        }
    }

    private static void OnDisconnected(Mobile mobile)
    {
        if (mobile is PlayerMobile player)
        {
            RegionStates.Remove(player.Serial);
        }
    }

    private static void OnMovement(MovementEventArgs args)
    {
        if (!Enabled || args.Mobile is not PlayerMobile player || player.Deleted)
        {
            return;
        }

        // Movement is raised before the step is applied. Observe on the next server tick so a
        // blocked step does not produce a false boundary notification.
        Server.Timer.DelayCall(TimeSpan.Zero, () =>
        {
            if (!player.Deleted)
            {
                ObserveTheftRegions(player, notify: true);
            }
        });
    }

    private static void ObserveTheftRegions(PlayerMobile player, bool notify)
    {
        var current = new TheftRegionState(
            TheftRegionPolicy.IsBankProtectionRegion(player),
            TheftRegionPolicy.IsCoolDungeonRegion(player)
        );

        if (RegionStates.TryGetValue(player.Serial, out var previous))
        {
            if (notify)
            {
                foreach (var message in DescribeRegionTransitions(previous, current))
                {
                    player.SendMessage(message);
                }
            }
        }

        RegionStates[player.Serial] = current;
    }

    public static IEnumerable<string> DescribeRegionTransitions(
        bool wasBankProtected,
        bool isBankProtected,
        bool wasCoolDungeon,
        bool isCoolDungeon
    ) => DescribeRegionTransitions(
        new TheftRegionState(wasBankProtected, wasCoolDungeon),
        new TheftRegionState(isBankProtected, isCoolDungeon)
    );

    private static IEnumerable<string> DescribeRegionTransitions(
        TheftRegionState previous,
        TheftRegionState current
    )
    {
        if (!previous.BankProtected && current.BankProtected)
        {
            yield return "You are now protected from theft by the bank guards";
        }
        else if (previous.BankProtected && !current.BankProtected)
        {
            yield return "You are outside bank guard protection from theft";
        }

        if (!previous.CoolDungeon && current.CoolDungeon)
        {
            yield return "You are entering a protected dungeon: direct player stealing is disabled here";
        }
        else if (previous.CoolDungeon && !current.CoolDungeon)
        {
            yield return "You have left the protected dungeon: normal player stealing rules now apply";
        }
    }

    private readonly record struct TheftRegionState(bool BankProtected, bool CoolDungeon);

    public static bool IsProtectionWindowActive(DateTime nowUtc, DateTime protectedUntilUtc) =>
        protectedUntilUtc.ToUniversalTime() > nowUtc.ToUniversalTime();

    /// <summary>
    /// Returns whether the offender-specific monster-corpse repeat ward is active for a lift.
    /// Keeping the policy decision separate from the stock corpse callback makes the feature-gate
    /// and expiry matrix testable without constructing a live world item or account.
    /// </summary>
    public static bool IsCorpseLootProtectionActive(
        bool enabled,
        bool hotZonesEnabled,
        bool monsterCorpse,
        bool criminalAction,
        string? protectionMarker,
        DateTime nowUtc
    )
    {
        if (!enabled || hotZonesEnabled || !monsterCorpse || !criminalAction ||
            !DateTime.TryParse(
                protectionMarker,
                CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind,
                out var protectedUntil
            ))
        {
            return false;
        }

        return IsProtectionWindowActive(nowUtc, protectedUntil);
    }

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
        yield return "A thief caught by your Ward on a successful theft cannot steal from you again until the Ward has run its course (30 quiet minutes). Wards do nothing in a Hot Zone (Fire Island, Buccaneer's Den island, Hythloth).";
        foreach (var line in TheftRegionPolicy.Describe())
        {
            yield return line;
        }

        if (mobile is PlayerMobile player)
        {
            foreach (var line in BackpackWardService.Describe(player))
            {
                yield return line;
            }
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

        if (item is BackpackWard || item.Nontransferable)
        {
            thief.SendMessage("That protected item cannot be stolen.");
            ShardAuditLog.Record("theft", "item-binding-denied", thief, victim, "nontransferable item");
            return false;
        }

        if (OutdoorHotZonePolicy.IsHot(playerVictim))
        {
            return true;
        }

        if (BackpackWardService.IsBlocked(playerVictim, thief))
        {
            thief.SendMessage("You cannot steal from that person right now.");
            ShardAuditLog.Record("theft", "ward-blocked", thief, playerVictim, "caught by backpack ward");
            return false;
        }

        return true;
    }

    private static void ResolveTheft(Mobile thief, Item item, Mobile victim, Item stolen, bool caught, bool rolled)
    {
        KnockedOutService.OnKnockedOutLootResolved(thief, victim, stolen);

        if (!Enabled || victim is not PlayerMobile playerVictim || thief is not PlayerMobile playerThief ||
            playerVictim == playerThief || OutdoorHotZonePolicy.IsHot(playerVictim) || !rolled)
        {
            return;
        }

        // A genuine attempt: stock ran the skill check. Attempts it refused first (including ones this Ward blocked)
        // arrive with rolled false and are ignored, so they cannot restart a Ward's window. A successful transfer
        // leaves a stolen item; a detected one is "caught".
        BackpackWardService.OnTheftResolved(playerThief, playerVictim, stolen is not null, caught);
    }

    private static bool CanLiftCorpseItem(Mobile looter, Corpse corpse, Item item)
    {
        if (!Enabled || OutdoorHotZonePolicy.IsHot(corpse) ||
            corpse.OwnerWasBaseCreature != true || !corpse.IsCriminalAction(looter) ||
            looter.Account is not Account account)
        {
            return true;
        }

        var criminalAction = corpse.IsCriminalAction(looter);
        var hotZonesEnabled = OutdoorHotZonePolicy.IsHot(corpse);
        var hasActiveWard = false;

        foreach (var victim in GetMonsterLootRights(corpse))
        {
            if (IsCorpseLootProtectionActive(
                    Enabled,
                    hotZonesEnabled,
                    corpse.OwnerWasBaseCreature,
                    criminalAction,
                    account.GetTag(LootProtectionTag(victim, account)),
                    Core.Now
                ))
            {
                hasActiveWard = true;
                break;
            }
        }

        if (!hasActiveWard)
        {
            return true;
        }

        looter.SendMessage("You cannot repeatedly loot this monster's corpse right now.");
        ShardAuditLog.Record("corpse-loot", "repeat-denied", looter, corpse.Owner, "10-minute offender protection");
        return false;
    }

    private static void RecordCorpseTransfer(Mobile looter, Corpse corpse, Item item)
    {
        if (!Enabled || OutdoorHotZonePolicy.IsHot(corpse) ||
            corpse.OwnerWasBaseCreature != true || !corpse.IsCriminalAction(looter) ||
            looter.Account is not Account account)
        {
            return;
        }

        var expiry = Core.Now.Add(LootProtectionDuration).ToString("O", CultureInfo.InvariantCulture);
        var protectedVictims = 0;

        foreach (var victim in GetMonsterLootRights(corpse))
        {
            account.SetTag(LootProtectionTag(victim, account), expiry);
            protectedVictims++;
        }

        if (protectedVictims > 0)
        {
            ShardAuditLog.Record(
                "corpse-loot",
                "first-transfer",
                looter,
                corpse.Owner,
                $"10-minute offender protection armed for {protectedVictims} rights holder(s)"
            );
        }
    }

    private static IEnumerable<PlayerMobile> GetMonsterLootRights(Corpse corpse)
    {
        var seen = new HashSet<Serial>();

        foreach (var mobile in corpse.MonsterLootRights)
        {
            if (mobile is PlayerMobile player && !player.Deleted && player.Account is Account && seen.Add(player.Serial))
            {
                yield return player;
            }
        }
    }

    private static string LootProtectionTag(PlayerMobile victim, Account account) =>
        LootProtectionTagPrefix + victim.Serial.Value.ToString("X8", CultureInfo.InvariantCulture) + "." +
        account.Username;
}
