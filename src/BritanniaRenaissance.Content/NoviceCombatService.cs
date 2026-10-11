using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Novice combat assist (docs/Novice-Combat-Assist-Plan.md), behind <c>featureFlags.noviceCombat</c>. Three floors that help a player
/// whose own skills are low and vanish as they train, for every weapon and every target, whenever the attacker is an ordinary
/// player: a share of missed swings are converted to hits (<see cref="LiftedChance"/>), Tactics counts as at least a floor for the
/// damage modifier, and stamina counts as at least a floor for the swing delay. Monsters, pets and staff are never touched, and at
/// skill 100 with Tactics and stamina above their floors nothing differs from stock. The engine side is
/// <see cref="WeaponEvents"/>; the rule here is pure so it can be tested without game objects.
/// </summary>
public static class NoviceCombatService
{
    /// <summary>Above this the lift could make hit chance fall as skill rises, for some defender; configuration is validated below it.</summary>
    public const double MaxHitLiftStrength = 2.0 / 3.0;

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.NoviceCombat == true;

    private static NoviceCombatRules Rules => ShardRulesConfiguration.Settings?.NoviceCombat ?? new NoviceCombatRules();

    /// <summary>Who the assist is for, as the rule sees them.</summary>
    public readonly record struct Attacker(bool Enabled, bool IsOrdinaryPlayer)
    {
        public bool Applies => Enabled && IsOrdinaryPlayer;
    }

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        var previousHit = WeaponEvents.HitChance;
        WeaponEvents.HitChance = (attacker, skill, chance) =>
            LiftedChance(Who(attacker), Rules, previousHit?.Invoke(attacker, skill, chance) ?? chance, skill);

        var previousTactics = WeaponEvents.TacticsForDamage;
        WeaponEvents.TacticsForDamage = (attacker, tactics) =>
            TacticsForDamage(Who(attacker), Rules, previousTactics?.Invoke(attacker, tactics) ?? tactics);

        var previousStamina = WeaponEvents.StaminaForSwingDelay;
        WeaponEvents.StaminaForSwingDelay = (swinger, stamina) =>
            StaminaForSwing(Who(swinger), Rules, previousStamina?.Invoke(swinger, stamina) ?? stamina);

        CommandSystem.Register("NoviceCombatStatus", AccessLevel.GameMaster, OnStatus);
    }

    private static Attacker Who(Mobile mobile) => new(Enabled, mobile is PlayerMobile { AccessLevel: AccessLevel.Player });

    /// <summary>
    /// The hit chance after the lift: <c>chance x (1 + strength x (1 - skill / 100))</c>, capped at 1. The stock chance is returned
    /// unchanged when the assist does not apply, at skill 100 and above, and when it is already 1 or more.
    /// </summary>
    public static double LiftedChance(Attacker who, NoviceCombatRules rules, double chance, double skill)
    {
        if (!who.Applies || chance >= 1.0 || rules.HitLiftStrength <= 0.0)
        {
            return chance;
        }

        var fade = Math.Max(0.0, 1.0 - skill / 100.0);
        return Math.Min(1.0, chance * (1.0 + rules.HitLiftStrength * fade));
    }

    /// <summary>The Tactics the damage modifier uses: at least the floor, for an ordinary player.</summary>
    public static double TacticsForDamage(Attacker who, NoviceCombatRules rules, double tactics) =>
        who.Applies ? Math.Max(tactics, rules.TacticsFloor) : tactics;

    /// <summary>The stamina the swing delay uses: at least the floor, for an ordinary player.</summary>
    public static int StaminaForSwing(Attacker who, NoviceCombatRules rules, int stamina) =>
        who.Applies ? Math.Max(stamina, rules.StaminaFloor) : stamina;

    public static void Validate(NoviceCombatRules rules, List<string> errors)
    {
        if (double.IsNaN(rules.HitLiftStrength) || rules.HitLiftStrength is < 0.0 or > MaxHitLiftStrength)
        {
            errors.Add("noviceCombat.hitLiftStrength must be between 0 and 2/3 (0.6667): above that hit chance could fall as skill rises.");
        }

        if (double.IsNaN(rules.TacticsFloor) || rules.TacticsFloor is < 0.0 or > 50.0)
        {
            errors.Add("noviceCombat.tacticsFloor must be between 0 and 50 (50 is no damage penalty at all).");
        }

        if (rules.StaminaFloor is < 0 or > 100)
        {
            errors.Add("noviceCombat.staminaFloor must be between 0 and 100.");
        }
    }

    [Usage("NoviceCombatStatus")]
    [Description("Shows whether the novice combat assist is on, its three numbers, and what they do at a few skill levels.")]
    private static void OnStatus(CommandEventArgs e)
    {
        var rules = Rules;
        var who = new Attacker(true, true);
        e.Mobile.SendMessage(
            $"Novice combat assist: {(Enabled ? "ON" : "off (flag featureFlags.noviceCombat)")}. Hit lift {rules.HitLiftStrength:0.###}, " +
            $"Tactics counts as at least {rules.TacticsFloor:0.#}, stamina counts as at least {rules.StaminaFloor}."
        );

        foreach (var skill in new[] { 0.0, 25.0, 50.0, 75.0, 100.0 })
        {
            var stock = (skill + 50.0) / ((60.0 + 50.0) * 2.0);
            e.Mobile.SendMessage(
                $"Weapon skill {skill:0}: against a defender at 60 the hit chance is {stock * 100:0}% stock, {LiftedChance(who, rules, stock, skill) * 100:0}% with the assist."
            );
        }
    }
}

/// <summary>Novice combat assist settings from shard-rules.json (<c>noviceCombat</c>).</summary>
public sealed class NoviceCombatRules
{
    /// <summary>Accuracy up to this much better than the formula at weapon skill 0, fading in a straight line to nothing at skill 100.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("hitLiftStrength")]
    public double HitLiftStrength { get; set; } = 0.66;

    /// <summary>Tactics counts as at least this for the damage modifier (0 is a 50% damage penalty, 50 none).</summary>
    [System.Text.Json.Serialization.JsonPropertyName("tacticsFloor")]
    public double TacticsFloor { get; set; } = 30.0;

    /// <summary>Stamina counts as at least this for the swing delay.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("staminaFloor")]
    public int StaminaFloor { get; set; } = 60;
}
