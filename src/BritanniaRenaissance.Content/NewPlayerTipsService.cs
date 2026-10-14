using Server;
using Server.Accounting;
using Server.Commands;
using Server.Items;
using Server.Misc;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// One-time tips for new players (docs/New-Player-Help-Messages.md, Tier B), behind <c>featureFlags.newPlayerTips</c>. Each tip is said once per character, at the moment
/// it matters, and says what to do. A player can switch them all off with <c>[Tips off</c>. The decisions are pure so they can be tested without game objects; the poll
/// reads the situation once a second, as the poison hint does.
/// </summary>
public static class NewPlayerTipsService
{
    public const string OutOfArrows = "outOfArrows";
    public const string BadlyHurt = "badlyHurt";
    public const string BadlyHurtPotion = "badlyHurtPotion";
    public const string FirstDeath = "firstDeath";
    public const string FirstResurrection = "firstResurrection";
    public const string Tired = "tired";
    public const string GoldInPack = "goldInPack";
    public const string FirstPet = "firstPet";
    public const string Overloaded = "overloaded";

    /// <summary>Gold in the pack at which the bank tip is said.</summary>
    public const int GoldTipThreshold = 2000;

    public static readonly IReadOnlyDictionary<string, string> Texts = new Dictionary<string, string>
    {
        [OutOfArrows] = "You are out of ammunition. Ammunition that misses falls to the ground near the target, so pick it up, or buy more from a bowyer.",
        [BadlyHurt] = "You are badly hurt. Double-click a bandage, then click yourself to heal. It works better the higher your Healing skill is.",
        [BadlyHurtPotion] = "You are badly hurt and have no bandages. Double-click a Heal potion in your pack to drink it, or buy bandages from a healer or provisioner.",
        [Overloaded] = "You are carrying too much, so you tire quickly when you run. Drop or store heavy things: the bank is at any banker, and a pack animal or a house keeps more.",
        [FirstDeath] = "You have died. Find a healer in town, or ask another player to resurrect you, then take your things from your corpse. Your starting gear stays with you.",
        [Tired] = "You are tired, so you swing more slowly. Stand still for a moment to get your wind back.",
        [GoldInPack] = "Gold in your pack can be stolen; gold in your bank box cannot. Say bank next to a banker to put it away.",
        [FirstPet] = "Your new pet gets hungry. Feed it food it likes now and then (double-click the food, then click the pet), or it will wander off after about ten hours.",
        [FirstResurrection] = "Your belongings are on your corpse. Go back for it soon: it turns to bones after a few minutes and is gone not long after.",
    };

    /// <summary>Said once, after the first tip of any kind: system lines fade in a few seconds and the Journal keeps them.</summary>
    public const string JournalNote = "Messages fade quickly. The Journal button at the top keeps them.";

    private const string TagPrefix = "BritanniaRenaissance.NewPlayerTip.v1.";
    private const string OffTagPrefix = "BritanniaRenaissance.NewPlayerTipsOff.v1.";

    private static readonly Dictionary<Serial, bool> WasAlive = [];
    private static readonly Dictionary<Serial, int> FollowerCount = [];
    private static readonly List<NetState> Online = [];

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.NewPlayerTips == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        Server.Timer.StartTimer(TimeSpan.FromSeconds(1.0), TimeSpan.FromSeconds(1.0), Poll);
        CommandSystem.Register("Tips", AccessLevel.Player, OnTips);
    }

    // ---- the decisions

    /// <summary>Hurt badly enough to be told: under a third of the hits, in a fight, with a bandage to use.</summary>
    public static bool IsBadlyHurt(int hits, int hitsMax, bool inCombat, bool hasBandage) =>
        inCombat && hasBandage && hitsMax > 0 && hits > 0 && hits * 3 < hitsMax;

    /// <summary>Out of ammunition: a ranged weapon in hand, war mode on, and none in the pack or quiver.</summary>
    public static bool IsOutOfAmmunition(bool holdsRangedWeapon, bool warMode, bool hasAmmunition) => holdsRangedWeapon && warMode && !hasAmmunition;

    /// <summary>Stamina under a quarter in a fight.</summary>
    public static bool IsTired(int stam, int stamMax, bool inCombat) => inCombat && stamMax > 0 && stam * 4 < stamMax;

    /// <summary>A follower was added and one of them is a tamed (not summoned) creature.</summary>
    public static bool GainedAPet(int before, int after, bool anyTamed) => after > before && anyTamed;

    public static bool CarriesALotOfGold(int gold) => gold >= GoldTipThreshold;

    /// <summary>Whether a tip is said now: the flag on, an ordinary player, tips not switched off and this one not shown before.</summary>
    public static bool ShouldShow(bool enabled, bool ordinaryPlayer, bool tipsOff, bool alreadyShown) => enabled && ordinaryPlayer && !tipsOff && !alreadyShown;

    // ---- the watch

    private static void Poll()
    {
        if (!Enabled)
        {
            return;
        }

        Online.Clear();
        Online.AddRange(NetState.Instances);

        foreach (var ns in Online)
        {
            if (ns.Mobile is PlayerMobile { Deleted: false, AccessLevel: AccessLevel.Player } player)
            {
                Watch(player);
            }
        }
    }

    private static void Watch(PlayerMobile player)
    {
        var alive = player.Alive;

        if (!WasAlive.TryGetValue(player.Serial, out var wasAlive))
        {
            WasAlive[player.Serial] = alive;
            return;
        }

        WasAlive[player.Serial] = alive;

        if (wasAlive && !alive)
        {
            Show(player, FirstDeath);
            return;
        }

        if (!wasAlive && alive)
        {
            Show(player, FirstResurrection);
        }

        if (!alive)
        {
            return;
        }

        if (IsBadlyHurt(player.Hits, player.HitsMax, player.Combatant != null, HasBandage(player)))
        {
            Show(player, BadlyHurt);
        }

        var followers = player.AllFollowers?.Count ?? 0;

        if (FollowerCount.TryGetValue(player.Serial, out var before) && followers > before && !Pending(player, FirstPet) && GainedAPet(before, followers, HasTamedPet(player)))
        {
            Show(player, FirstPet);
        }

        FollowerCount[player.Serial] = followers;

        if (IsBadlyHurt(player.Hits, player.HitsMax, player.Combatant != null, true) && !HasBandage(player) && HasHealPotion(player))
        {
            Show(player, BadlyHurtPotion);
        }

        if (!Pending(player, Overloaded) && StaminaSystem.IsOverloaded(player))
        {
            Show(player, Overloaded);
        }

        if (IsTired(player.Stam, player.StamMax, player.Combatant != null))
        {
            Show(player, Tired);
        }

        if (!Pending(player, GoldInPack) && CarriesALotOfGold(player.Backpack?.GetAmount(typeof(Gold)) ?? 0))
        {
            Show(player, GoldInPack);
        }

        if (player.Weapon is BaseRanged ranged && IsOutOfAmmunition(true, player.Warmode, HasAmmunition(player, ranged)))
        {
            Show(player, OutOfArrows);
        }
    }

    private static bool Pending(PlayerMobile player, string id) =>
        player.Account is not Account account || account.GetTag($"{TagPrefix}{player.Serial.Value}.{id}") is not null;

    private static bool HasTamedPet(PlayerMobile player)
    {
        if (player.AllFollowers is { } all)
        {
            foreach (var follower in all)
            {
                if (follower is BaseCreature { Controlled: true, Summoned: false })
                {
                    return true;
                }
            }
        }

        return false;
    }

    private static bool HasHealPotion(PlayerMobile player) => player.Backpack?.FindItemByType<BaseHealPotion>() != null;

    private static bool HasBandage(PlayerMobile player) => player.Backpack?.FindItemByType<Bandage>() != null;

    private static bool HasAmmunition(PlayerMobile player, BaseRanged weapon)
    {
        var type = weapon.AmmoType;
        var quiver = player.FindItemOnLayer<BaseQuiver>(Layer.Cloak);

        return player.Backpack?.FindItemByType(type) != null || quiver?.FindItemByType(type) != null;
    }

    private static void Show(PlayerMobile player, string id)
    {
        if (player.Account is not Account account)
        {
            return;
        }

        var tag = $"{TagPrefix}{player.Serial.Value}.{id}";

        if (!ShouldShow(Enabled, true, account.GetTag($"{OffTagPrefix}{player.Serial.Value}") is not null, account.GetTag(tag) is not null))
        {
            return;
        }

        account.SetTag(tag, "shown");
        player.SendMessage(0x35, Texts[id]);

        var noteTag = $"{TagPrefix}{player.Serial.Value}.journalNote";

        if (account.GetTag(noteTag) is null)
        {
            account.SetTag(noteTag, "shown");
            player.SendMessage(0x35, JournalNote);
        }
    }

    [Usage("Tips [on|off]")]
    [Description("Turns the one-time tips for this character on or off.")]
    private static void OnTips(CommandEventArgs e)
    {
        if (!Enabled)
        {
            e.Mobile.SendMessage("There are no tips to switch.");
            return;
        }

        if (e.Mobile is not PlayerMobile { Account: Account account } player)
        {
            return;
        }

        var tag = $"{OffTagPrefix}{player.Serial.Value}";
        var word = e.Length > 0 ? e.GetString(0).Trim().ToLowerInvariant() : "";

        switch (word)
        {
            case "off":
                account.SetTag(tag, "off");
                player.SendMessage("Tips are off for this character. Type [Tips on to turn them back on.");
                break;
            case "on":
                account.RemoveTag(tag);
                player.SendMessage("Tips are on for this character. Each is said once, when it matters.");
                break;
            default:
                player.SendMessage($"Tips are {(account.GetTag(tag) is null ? "on" : "off")} for this character. Type [Tips off or [Tips on.");
                break;
        }
    }
}
