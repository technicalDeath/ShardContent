using Server;
using Server.Accounting;
using Server.Commands;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Poison relief for new characters (docs/Poison-Relief-Plan.md), behind <c>featureFlags.poisonRelief</c>. Wraiths and Spectres cast Poison,
/// always Lesser, and a new character cannot heal (a bandage on a poisoned patient only tries a cure, which needs Healing and Anatomy 60),
/// cure, or tell why. Three parts: every new character carries Lesser Cure potions, the first poisoning of a character who cannot cure with a
/// bandage is explained once, and after a poison ends or is cured, monster poison of Lesser strength cannot land again for a while (the
/// engine side is <c>PlayerMobile.PoisonImmunityHandler</c>). Player-sourced poison and stronger poison are stock. The decisions are pure
/// so they can be tested without game objects.
/// </summary>
public static class PoisonReliefService
{
    /// <summary>The Healing and Anatomy a bandage needs before it can cure (<c>BandageContext</c>), read from the engine's own check.</summary>
    public const double BandageCureSkill = 60.0;

    private const string PotionsTagPrefix = "BritanniaRenaissance.PoisonReliefPotions.v1.";
    private const string HintTagPrefix = "BritanniaRenaissance.PoisonReliefHint.v1.";

    public const string HintText =
        "You are poisoned. While you are poisoned a bandage only tries to cure you, and that takes Healing and Anatomy of 60 or more, so it will not heal you. " +
        "A Cure potion (alchemists sell Lesser Cure for 15 gold), the Cure spell, or waiting it out will end the poison.";

    public const string GraceText = "You are still shaking off the last poison, and this one finds no hold.";

    private static readonly Dictionary<Serial, TrackedPlayer> Tracked = [];
    private static readonly List<NetState> Online = [];

    private static bool _configured;
    private static int _ticks;

    private sealed class TrackedPlayer
    {
        public bool WasPoisoned;
        public DateTime? EndedUtc;
    }

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.PoisonRelief == true;

    private static PoisonReliefRules Rules => ShardRulesConfiguration.Settings?.PoisonRelief ?? new PoisonReliefRules();

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        CharacterCreation.CharacterCreatedHandler += IssuePotions;

        var previous = PlayerMobile.PoisonImmunityHandler;
        PlayerMobile.PoisonImmunityHandler = (target, from, poison) => previous?.Invoke(target, from, poison) == true || GraceRefuses(target, from, poison);

        Server.Timer.StartTimer(TimeSpan.FromSeconds(1.0), TimeSpan.FromSeconds(1.0), Poll);
        CommandSystem.Register("PoisonReliefStatus", AccessLevel.GameMaster, OnStatus);
    }

    // ---- the decisions

    /// <summary>
    /// Whether a poison about to land is refused. Only an ordinary player is helped, only against a source that is not a player (a trap, a
    /// field, a monster), only up to the configured level, and only within the configured seconds after their last poison ended.
    /// </summary>
    public static bool Refuses(PoisonReliefRules rules, bool enabled, bool targetIsOrdinaryPlayer, bool sourceIsPlayer, int poisonLevel, double? secondsSincePoisonEnded) =>
        enabled && targetIsOrdinaryPlayer && !sourceIsPlayer && rules.GraceSeconds > 0 && poisonLevel <= rules.GraceMaxLevel &&
        secondsSincePoisonEnded is { } seconds && seconds >= 0.0 && seconds < rules.GraceSeconds;

    /// <summary>Whether a poisoning is explained: once per character, to someone whose bandage could not cure.</summary>
    public static bool ShouldHint(bool enabled, bool ordinaryPlayer, double healing, double anatomy, bool alreadyHinted) =>
        enabled && ordinaryPlayer && !alreadyHinted && (healing < BandageCureSkill || anatomy < BandageCureSkill);

    /// <summary>How many Lesser Cure potions a new character is given.</summary>
    public static int PotionCount(PoisonReliefRules rules, bool enabled) => enabled ? Math.Max(0, rules.CurePotions) : 0;

    /// <summary>A poison from a player, or from a pet or summon a player controls, is never softened.</summary>
    public static bool IsPlayerSource(Mobile? from) =>
        from is PlayerMobile || from is BaseCreature { Controlled: true } || from is BaseCreature { Summoned: true };

    public static void Validate(PoisonReliefRules rules, List<string> errors)
    {
        if (rules.CurePotions is < 0 or > 20)
        {
            errors.Add("poisonRelief.curePotions must be between 0 and 20.");
        }

        if (double.IsNaN(rules.GraceSeconds) || rules.GraceSeconds is < 0.0 or > 300.0)
        {
            errors.Add("poisonRelief.graceSeconds must be between 0 and 300 (0 switches the grace window off).");
        }

        if (rules.GraceMaxLevel is < 0 or > 4)
        {
            errors.Add("poisonRelief.graceMaxLevel must be between 0 (Lesser) and 4 (Lethal).");
        }
    }

    // ---- starter potions

    private static void IssuePotions(CharacterCreatedEventArgs args)
    {
        var count = PotionCount(Rules, Enabled);

        if (count == 0 || args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player || player.Account is not Account account)
        {
            return;
        }

        var tag = $"{PotionsTagPrefix}{player.Serial.Value}";

        if (account.GetTag(tag) is not null)
        {
            return;
        }

        for (var i = 0; i < count; i++)
        {
            player.Backpack.DropItem(new LesserCurePotion { LootType = LootType.Newbied });
        }

        account.SetTag(tag, "issued");
    }

    // ---- the watch: a poison landing (the hint) and a poison ending (the start of the grace window)

    private static void Poll()
    {
        if (!Enabled)
        {
            return;
        }

        var now = DateTime.UtcNow;
        Online.Clear();
        Online.AddRange(NetState.Instances);

        foreach (var ns in Online)
        {
            if (ns.Mobile is PlayerMobile { Deleted: false, AccessLevel: AccessLevel.Player } player)
            {
                Watch(player, now);
            }
        }

        if (++_ticks % 60 == 0)
        {
            Forget(now);
        }
    }

    private static void Watch(PlayerMobile player, DateTime now)
    {
        if (!Tracked.TryGetValue(player.Serial, out var state))
        {
            Tracked[player.Serial] = state = new TrackedPlayer { WasPoisoned = player.Poisoned };
            return;
        }

        var poisoned = player.Poisoned;

        if (poisoned && !state.WasPoisoned)
        {
            Hint(player);
        }
        else if (!poisoned && state.WasPoisoned)
        {
            state.EndedUtc = now;
        }

        state.WasPoisoned = poisoned;
    }

    private static void Hint(PlayerMobile player)
    {
        if (player.Account is not Account account)
        {
            return;
        }

        var tag = $"{HintTagPrefix}{player.Serial.Value}";

        if (!ShouldHint(Enabled, true, player.Skills[SkillName.Healing].Value, player.Skills[SkillName.Anatomy].Value, account.GetTag(tag) is not null))
        {
            return;
        }

        account.SetTag(tag, "shown");
        player.SendMessage(0x35, HintText);
    }

    private static void Forget(DateTime now)
    {
        var window = TimeSpan.FromSeconds(Math.Max(Rules.GraceSeconds, 1.0) + 60.0);
        List<Serial>? stale = null;

        foreach (var (serial, state) in Tracked)
        {
            if (!state.WasPoisoned && (state.EndedUtc is null || now - state.EndedUtc > window) && World.FindMobile(serial) is not PlayerMobile { NetState: not null })
            {
                (stale ??= []).Add(serial);
            }
        }

        if (stale is not null)
        {
            foreach (var serial in stale)
            {
                Tracked.Remove(serial);
            }
        }
    }

    // ---- the engine hook

    private static bool GraceRefuses(PlayerMobile target, Mobile from, Poison poison)
    {
        var enabled = Enabled;

        if (!enabled || !Tracked.TryGetValue(target.Serial, out var state) || state.EndedUtc is not { } ended)
        {
            return false;
        }

        var refused = Refuses(Rules, enabled, target.AccessLevel == AccessLevel.Player, IsPlayerSource(from), poison.Level, (DateTime.UtcNow - ended).TotalSeconds);

        if (refused)
        {
            target.SendMessage(0x35, GraceText);
        }

        return refused;
    }

    [Usage("PoisonReliefStatus")]
    [Description("Shows whether poison relief is on, its settings, and your own grace window and hint state.")]
    private static void OnStatus(CommandEventArgs e)
    {
        var rules = Rules;
        e.Mobile.SendMessage(
            $"Poison relief: {(Enabled ? "ON" : "off (flag featureFlags.poisonRelief)")}. New characters get {rules.CurePotions} Lesser Cure potions; after a poison ends, " +
            $"poison up to level {rules.GraceMaxLevel} from a non-player is refused for {rules.GraceSeconds:0.#} s."
        );

        if (e.Mobile is PlayerMobile player)
        {
            var left = Tracked.TryGetValue(player.Serial, out var state) && state.EndedUtc is { } ended
                ? Math.Max(0.0, rules.GraceSeconds - (DateTime.UtcNow - ended).TotalSeconds)
                : 0.0;
            var hinted = (player.Account as Account)?.GetTag($"{HintTagPrefix}{player.Serial.Value}") is not null;
            e.Mobile.SendMessage($"You: grace window {left:0.#} s left, hint {(hinted ? "already shown" : "not shown yet")}, poisoned {player.Poisoned}.");
        }
    }
}

/// <summary>Poison relief settings from shard-rules.json (<c>poisonRelief</c>).</summary>
public sealed class PoisonReliefRules
{
    /// <summary>Lesser Cure potions every new character is given (newbied, once per character).</summary>
    [System.Text.Json.Serialization.JsonPropertyName("curePotions")]
    public int CurePotions { get; set; } = 5;

    /// <summary>Seconds after a poison ends or is cured during which poison from a non-player is refused; 0 switches it off.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("graceSeconds")]
    public double GraceSeconds { get; set; } = 30.0;

    /// <summary>The strongest poison level the grace window refuses: 0 Lesser, 1 Regular, 2 Greater, 3 Deadly, 4 Lethal.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("graceMaxLevel")]
    public int GraceMaxLevel { get; set; } = 0;
}
