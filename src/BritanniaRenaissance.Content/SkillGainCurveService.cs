using System.Globalization;
using Server;
using Server.Misc;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Beta 1 sub-95 skill-gain curve, behind <c>featureFlags.skillGainCurve</c>. Every skill belongs to a class
/// (<c>skillGain.skills</c>); a class is a list of bands (<c>skillGain.classes</c>) that multiply the stock gain
/// probability for a player's skill by the band's multiplier, so 1.0 is exactly stock ModernUO. The hook
/// (<see cref="SkillEvents.GainChanceMultiplier"/>) is consulted only on the stock gain roll, after
/// <see cref="SkillEvents.SkillGainOverride"/>, so Skill Bank restoration and Mastery are untouched, the stock
/// unconditional gain below 10.0 is untouched, and Mastery owns 95.0 and above.
/// </summary>
public static class SkillGainCurveService
{
    /// <summary>Ordinary gain ends here; Mastery owns the skill from this value up.</summary>
    public const double MasteryThreshold = 95.0;

    /// <summary>Below this the stock gain is unconditional and never rolls, so no multiplier applies.</summary>
    public const double UnconditionalGainCeiling = 10.0;

    public const int LastUorSkillId = (int)SkillName.RemoveTrap;

    private static readonly string[] ClassNames = ["easy", "standard", "hard", "veryHard"];

    private static bool _configured;
    private static ShardRules? _cacheKey;
    private static Band[][]? _bySkill;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.SkillGainCurve == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        var previous = SkillEvents.GainChanceMultiplier;
        SkillEvents.GainChanceMultiplier = (from, skill) =>
            (previous?.Invoke(from, skill) ?? 1.0) * GetMultiplier(from, skill);

        CommandSystem.Register("SkillClasses", AccessLevel.Player, OnSkillClasses);
    }

    /// <summary>The multiplier for this check: 1.0 for anything that is not a player's own skill in the curve range.</summary>
    public static double GetMultiplier(Mobile from, Skill skill)
    {
        if (!Enabled || from is not PlayerMobile { AccessLevel: AccessLevel.Player })
        {
            return 1.0;
        }

        return MultiplierFor(ShardRulesConfiguration.Settings.SkillGain, skill.SkillName, skill.Base);
    }

    /// <summary>
    /// The class multiplier for a skill at a given value, from the configured bands. 1.0 outside
    /// 10.0 (inclusive) to 95.0 (exclusive), and 1.0 for a skill the configuration does not list.
    /// </summary>
    public static double MultiplierFor(SkillGainRules rules, SkillName skill, double value)
    {
        if (value < UnconditionalGainCeiling || value >= MasteryThreshold)
        {
            return 1.0;
        }

        var bands = BandsFor(rules, skill);
        for (var i = bands.Length - 1; i >= 0; i--)
        {
            if (value >= bands[i].From)
            {
                return bands[i].Multiplier;
            }
        }

        return 1.0;
    }

    public static string? ClassOf(SkillGainRules rules, SkillName skill) =>
        rules.Skills.TryGetValue(skill.ToString(), out var name) ? name : null;

    private static Band[] BandsFor(SkillGainRules rules, SkillName skill)
    {
        var settings = ShardRulesConfiguration.Settings;
        if (_bySkill is null || !ReferenceEquals(_cacheKey, settings) || _cachedRules != rules)
        {
            Rebuild(settings, rules);
        }

        var id = (int)skill;
        return id >= 0 && id < _bySkill!.Length ? _bySkill[id] : [];
    }

    private static SkillGainRules? _cachedRules;

    private static void Rebuild(ShardRules? settings, SkillGainRules rules)
    {
        var table = new Band[LastUorSkillId + 1][];
        for (var i = 0; i < table.Length; i++)
        {
            table[i] = [];
        }

        foreach (var (skillName, className) in rules.Skills)
        {
            if (!Enum.TryParse<SkillName>(skillName, true, out var id) || (int)id > LastUorSkillId ||
                !rules.Classes.TryGetValue(className, out var list))
            {
                continue;
            }

            table[(int)id] = list.OrderBy(b => b.From).Select(b => new Band(b.From, b.Multiplier)).ToArray();
        }

        _bySkill = table;
        _cacheKey = settings;
        _cachedRules = rules;
    }

    private readonly record struct Band(double From, double Multiplier);

    public static void Validate(SkillGainRules rules, List<string> errors)
    {
        foreach (var name in ClassNames)
        {
            if (!rules.Classes.ContainsKey(name))
            {
                errors.Add($"skillGain.classes must define '{name}'.");
            }
        }

        foreach (var (name, bands) in rules.Classes)
        {
            if (!ClassNames.Contains(name, StringComparer.OrdinalIgnoreCase))
            {
                errors.Add($"skillGain.classes '{name}' is not one of {string.Join(", ", ClassNames)}.");
            }

            if (bands.Count == 0 || bands[0].From != 0)
            {
                errors.Add($"skillGain.classes '{name}' must start with a band from 0.");
            }

            for (var i = 0; i < bands.Count; i++)
            {
                var band = bands[i];
                if (band.From < 0 || band.From >= MasteryThreshold || i > 0 && band.From <= bands[i - 1].From)
                {
                    errors.Add($"skillGain.classes '{name}' bands must ascend and start below {MasteryThreshold:0}.");
                }

                if (band.Multiplier is <= 0 or > 5 || double.IsNaN(band.Multiplier))
                {
                    errors.Add($"skillGain.classes '{name}' multipliers must be above 0 and at most 5.");
                }
            }
        }

        var seen = new HashSet<SkillName>();
        foreach (var (skillName, className) in rules.Skills)
        {
            if (!Enum.TryParse<SkillName>(skillName, false, out var id) || (int)id > LastUorSkillId)
            {
                errors.Add($"skillGain.skills '{skillName}' is not a UOR skill name.");
                continue;
            }

            seen.Add(id);

            if (!rules.Classes.ContainsKey(className))
            {
                errors.Add($"skillGain.skills '{skillName}' names unknown class '{className}'.");
            }
        }

        for (var i = 0; i <= LastUorSkillId; i++)
        {
            if (!seen.Contains((SkillName)i))
            {
                errors.Add($"skillGain.skills must assign {(SkillName)i} to a class.");
            }
        }
    }

    [Usage("SkillClasses")]
    [Description("Lists each skill's training class and how fast it gains.")]
    private static void OnSkillClasses(CommandEventArgs e)
    {
        var from = e.Mobile;
        var rules = ShardRulesConfiguration.Settings?.SkillGain;

        if (rules is null || !Enabled)
        {
            from.SendMessage("Skills gain at the stock rate on this shard.");
            return;
        }

        from.SendMessage("Skill gain speed, compared with stock, from skill 10 up to 95:");

        foreach (var name in ClassNames)
        {
            var members = rules.Skills
                .Where(kv => string.Equals(kv.Value, name, StringComparison.OrdinalIgnoreCase) &&
                             Enum.TryParse<SkillName>(kv.Key, false, out _))
                .Select(kv => SkillInfo.Table[(int)Enum.Parse<SkillName>(kv.Key)].Name)
                .OrderBy(n => n, StringComparer.OrdinalIgnoreCase)
                .ToArray();

            if (members.Length == 0 || !rules.Classes.TryGetValue(name, out var bands))
            {
                continue;
            }

            from.SendMessage(Describe(name, bands));
            foreach (var line in Wrap(members, 70))
            {
                from.SendMessage(line);
            }
        }
    }

    public static string Describe(string className, IReadOnlyList<SkillGainBand> bands)
    {
        var ordered = bands.OrderBy(b => b.From).ToArray();
        var parts = new List<string>();

        for (var i = 0; i < ordered.Length; i++)
        {
            var upper = i + 1 < ordered.Length ? ordered[i + 1].From : MasteryThreshold;
            var lower = Math.Max(ordered[i].From, UnconditionalGainCeiling);
            if (upper <= lower)
            {
                continue;
            }

            parts.Add(
                string.Create(CultureInfo.InvariantCulture, $"{ordered[i].Multiplier:0.##}x from {lower:0} to {upper:0}")
            );
        }

        return $"{char.ToUpperInvariant(className[0])}{className[1..]}: {string.Join(", ", parts)}";
    }

    private static IEnumerable<string> Wrap(IEnumerable<string> names, int width)
    {
        var line = "  ";
        foreach (var name in names)
        {
            if (line.Length + name.Length + 2 > width && line.Trim().Length > 0)
            {
                yield return line.TrimEnd(',', ' ');
                line = "  ";
            }

            line += name + ", ";
        }

        if (line.Trim().Length > 0)
        {
            yield return line.TrimEnd(',', ' ');
        }
    }
}
