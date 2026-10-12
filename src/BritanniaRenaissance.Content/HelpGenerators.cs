using Server;
using Server.Engines.Craft;
using Server.Items;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Blocks of help text that are read from the game's own tables when the page is opened, so the numbers on a skill page can never drift from the game: each craft
/// skill's recipes with the skill they need and what they are made from. The help data asks for one with <c>{"generate": "craft:Alchemy"}</c>.
/// </summary>
public static class HelpGenerators
{
    private static readonly (string Name, Func<CraftSystem?> System)[] Crafts =
    [
        ("craft:Alchemy", () => DefAlchemy.CraftSystem),
        ("craft:Blacksmithing", () => DefBlacksmithy.CraftSystem),
        ("craft:Bowcraft", () => DefBowFletching.CraftSystem),
        ("craft:Carpentry", () => DefCarpentry.CraftSystem),
        ("craft:Cartography", () => DefCartography.CraftSystem),
        ("craft:Inscription", () => DefInscription.CraftSystem),
        ("craft:Tailoring", () => DefTailoring.CraftSystem),
        ("craft:Tinkering", () => DefTinkering.CraftSystem)
    ];

    /// <summary>The blocks that read a skill's own numbers: how it trains here, and the stats it uses.</summary>
    public const string Gain = "gain";

    public const string Stats = "stats";

    /// <summary>How a recipe's name number becomes text. The game's client text in play; a test that has no client files swaps in its own.</summary>
    public static Func<int, string?> ClilocText { get; set; } = static number => Localization.GetText(number);

    public static IReadOnlyCollection<string> Names { get; } = Crafts.Select(static c => c.Name).Concat([Gain, Stats]).ToArray();

    /// <summary>The paragraphs of a generated block; empty when the game has not built that table (a test that never started the crafts).</summary>
    public static IReadOnlyList<string> Generate(string name, SkillName? skill = null)
    {
        if (name == Gain)
        {
            return skill is { } gained ? GainText(gained) : [];
        }

        if (name == Stats)
        {
            return skill is { } stat ? StatsText(stat) : [];
        }

        foreach (var (craft, system) in Crafts)
        {
            if (craft == name)
            {
                return system() is { } built ? CraftTable(built, ClilocText, craft) : [];
            }
        }

        return [];
    }

    /// <summary>
    /// A heading for each group of the craft and under it one line for each recipe: its name, the skill range, and what it is made from. The range is the skill
    /// at which a beginner can first make it and the skill at which it rarely fails; a recipe whose first number is below 0 can be tried at once.
    /// </summary>
    /// <summary>
    /// Recipes the craft system holds (and the era allows) that the era's packet craft menus never offer, so a player cannot make them: dragon and bone armor, the orc
    /// helm, bolts of cloth and oil cloth, the cooking tools and pens, bolas, the faction traps and the second, off-menu clock-part and sextant-part recipes. Found by
    /// reading each Menu class under <c>Engines/Craft/T2A</c>; <c>HelpCatalogTests</c> checks that the names still exist in the craft system, so a change there is noticed.
    /// </summary>
    public static readonly IReadOnlyDictionary<string, string[]> OffMenuRecipes = new Dictionary<string, string[]>
    {
        ["craft:Blacksmithing"] = ["DragonGloves", "DragonHelm", "DragonLegs", "DragonArms", "DragonChest"],
        ["craft:Tailoring"] = ["BoltOfCloth", "OilCloth", "BoneHelm", "BoneGloves", "BoneArms", "BoneLegs", "BoneChest", "OrcHelm"],
        ["craft:Tinkering"] =
        [
            "Skillet", "FlourSifter", "FletcherTools", "MapmakersPen", "ScribesPen", "BolaBall", "Bola", "FactionGasTrapDeed", "FactionExplosionTrapDeed",
            "FactionSawTrapDeed", "FactionSpikeTrapDeed", "FactionTrapRemovalKit"
        ]
    };

    /// <summary>Tinkering lists the clock parts and the sextant parts twice; the second recipe (made from axle gears and springs or a hinge) is not on the menu.</summary>
    private static readonly string[] TwiceListed = ["ClockParts", "SextantParts"];

    public static bool IsOffMenu(string? craft, CraftItem item)
    {
        if (craft is not null && OffMenuRecipes.TryGetValue(craft, out var names) && names.Contains(item.ItemType.Name))
        {
            return true;
        }

        return craft == "craft:Tinkering" && TwiceListed.Contains(item.ItemType.Name) && item.Resources.Any(static r => r.ItemType.Name == "AxleGears");
    }

    public static IReadOnlyList<string> CraftTable(CraftSystem system, Func<int, string?> cliloc, string? craft = null)
    {
        var paragraphs = new List<string>();
        var shown = new HashSet<CraftItem>();
        var first = system.CraftItems.FirstOrDefault(static i => IsOfTheEra(i));

        if (first is not null && system.GetChanceAtMin(first) is var atMin and > 0.0)
        {
            paragraphs.Add($"In this craft you already succeed {atMin * 100:0.#}% of the time at a recipe's lower number, and the chance rises evenly to certain at its upper number.");
        }

        foreach (var group in system.CraftGroups)
        {
            var lines = group.CraftItems.Where(i => IsOfTheEra(i) && !IsOffMenu(craft, i)).Select(i => Line(system, i, cliloc)).ToList();

            if (lines.Count == 0)
            {
                continue;
            }

            foreach (var item in group.CraftItems)
            {
                shown.Add(item);
            }

            paragraphs.Add(WelcomeGuide.HeadingMark + Text(group.NameNumber, group.NameString, cliloc, ""));
            paragraphs.Add(string.Join("<BR>", lines));
        }

        var rest = system.CraftItems.Where(i => !shown.Contains(i) && IsOfTheEra(i) && !IsOffMenu(craft, i)).Select(i => Line(system, i, cliloc)).ToList();

        if (rest.Count > 0)
        {
            paragraphs.Add(string.Join("<BR>", rest));
        }

        return paragraphs;
    }

    private static bool IsOfTheEra(CraftItem item) => item.RequiredExpansion <= Core.Expansion;

    private static string Line(CraftSystem system, CraftItem item, Func<int, string?> cliloc)
    {
        var name = Capitalised(Text(item.NameNumber, item.NameString, cliloc, Spaced(item.ItemType.Name)));
        var main = item.Skills.FirstOrDefault(s => s.SkillToMake == system.MainSkill) ?? item.Skills.FirstOrDefault();
        var range = main is null ? "" : $", skill {main.MinSkill:0.#} to {main.MaxSkill:0.#}";
        var made = item.Resources.Count == 0
            ? ""
            : ", from " + string.Join(" and ", item.Resources.Select(r => $"{r.Amount} {ResourceName(r.Amount, Text(r.Name.Number, r.Name.String, cliloc, Spaced(r.ItemType.Name)))}"));

        return $"{name}{range}{made}";
    }

    /// <summary>The game's name of a material is a plural noun ("empty bottles"); for exactly one the singular reads right.</summary>
    public static string ResourceName(int amount, string name)
    {
        var lower = name.Trim().ToLowerInvariant();

        return amount == 1 && lower.Length > 3 && lower.EndsWith('s') && !lower.EndsWith("ss", StringComparison.Ordinal) ? lower[..^1] : lower;
    }

    public static string Capitalised(string text) => text.Length == 0 ? text : char.ToUpperInvariant(text[0]) + text[1..];

    private static string Text(int number, string? text, Func<int, string?> cliloc, string fallback)
    {
        if (!string.IsNullOrWhiteSpace(text))
        {
            return text;
        }

        return number > 0 && cliloc(number) is { Length: > 0 } found ? found.Trim() : fallback;
    }

    /// <summary>"LesserHealPotion" as "Lesser Heal Potion", for a recipe whose name text the game's tables do not carry.</summary>
    public static string Spaced(string typeName) => System.Text.RegularExpressions.Regex.Replace(typeName, "(?<=[a-z0-9])(?=[A-Z])", " ");

    // ---- how a skill trains on this shard

    private static string StatName(Stat stat) => stat switch
    {
        Stat.Str => "Strength",
        Stat.Dex => "Dexterity",
        _        => "Intelligence"
    };

    /// <summary>
    /// What the stats do for a skill, read from the skill's own table: the stats whose points add to how well it works (the bonus is a share of the gap between the trained
    /// skill and 100, at most the sum of the scales when each of those stats is 100) and the stats a successful use can raise (the legacy stat gain this era uses).
    /// </summary>
    public static IReadOnlyList<string> StatsText(SkillName skill)
    {
        var info = SkillInfo.Table[(int)skill];
        var helps = new List<string>();
        var raised = new List<string>();

        if (info.StrScale > 0)
        {
            helps.Add("Strength");
        }

        if (info.DexScale > 0)
        {
            helps.Add("Dexterity");
        }

        if (info.IntScale > 0)
        {
            helps.Add("Intelligence");
        }

        if (info.StrGain > 0)
        {
            raised.Add("Strength");
        }

        if (info.DexGain > 0)
        {
            raised.Add("Dexterity");
        }

        if (info.IntGain > 0)
        {
            raised.Add("Intelligence");
        }

        var paragraphs = new List<string> { WelcomeGuide.HeadingMark + "Stats" };

        if (helps.Count == 0)
        {
            paragraphs.Add("Your stats do not change how well this skill works.");
        }
        else
        {
            var fraction = 100.0 * (info.StrScale + info.DexScale + info.IntScale);
            paragraphs.Add(
                $"{JoinAnd(helps)} add to how well it works. With 100 in each, the skill counts for {fraction * 100.0:0.#}% of the gap between the skill you have trained and 100 " +
                $"(at 50.0 that is {50.0 * fraction:0.#} extra). The bonus fades as the skill nears 100."
            );
        }

        paragraphs.Add(
            raised.Count == 0
                ? "Using it does not raise any stat."
                : $"A successful use can also raise {JoinAnd(raised)} a little, unless you have locked that stat or reached the stat limit."
        );

        return paragraphs;
    }

    private static string JoinAnd(IReadOnlyList<string> names) =>
        names.Count == 1 ? names[0] : string.Join(", ", names.Take(names.Count - 1)) + " and " + names[^1];

    /// <summary>
    /// The skill's class and what it means here: the multipliers of its gain curve (while the curve is on), the rule that every use gains below 10.0, and the Mastery allowance
    /// from 80.0. Everything comes from <c>shard-rules.json</c>, so a change to the numbers changes the page.
    /// </summary>
    public static IReadOnlyList<string> GainText(SkillName skill) => GainText(skill, ShardRulesConfiguration.Settings);

    public static IReadOnlyList<string> GainText(SkillName skill, ShardRules? settings)
    {
        if (settings is null || !settings.SkillGain.Skills.TryGetValue(skill.ToString(), out var className) || !settings.SkillGain.Classes.TryGetValue(className, out var bands))
        {
            return [];
        }

        var paragraphs = new List<string> { WelcomeGuide.HeadingMark + "How it trains here" };
        var label = className switch
        {
            "veryHard" => "Very Hard",
            _          => char.ToUpperInvariant(className[0]) + className[1..]
        };

        if (settings.FeatureFlags.SkillGainCurve)
        {
            var steps = bands.OrderBy(static b => b.From)
                .Select((b, i) => $"{(i == 0 ? "from " + Math.Max(b.From, SkillGainCurveService.UnconditionalGainCeiling).ToString("0.#") + " it gains" : "from " + b.From.ToString("0.#"))} {Pace(b.Multiplier)}")
                .ToList();
            paragraphs.Add(
                $"{SkillTitle(skill)} is a {label} skill. Below {SkillGainCurveService.UnconditionalGainCeiling:0.#} every use gains; then, " +
                $"{string.Join(", ", steps.Take(steps.Count - 1))}{(steps.Count > 1 ? " and " : "")}{steps[^1]}. [SkillClasses lists every skill's class."
            );
        }
        else
        {
            paragraphs.Add($"{SkillTitle(skill)} trains at the usual rate. Below {SkillGainCurveService.UnconditionalGainCeiling:0.#} every use gains.");
        }

        if (settings.Mastery.AllowanceTenths.TryGetValue(className, out var tenths) && tenths > 0)
        {
            var days = (int)Math.Ceiling((SkillGainCurveService.CurveCeiling - SkillGainCurveService.MasteryThreshold) * 10.0 / tenths);
            paragraphs.Add(
                $"From {SkillGainCurveService.MasteryThreshold:0.#} Mastery adds a guaranteed gain of {tenths / 10.0:0.#} a day, so about {days} days of use take it from " +
                $"{SkillGainCurveService.MasteryThreshold:0.#} to {SkillGainCurveService.CurveCeiling:0.#}. [Mastery shows where you are."
            );
        }

        return paragraphs;
    }

    /// <summary>A gain multiplier in words: 1 is the usual rate, more is "times", less is a share of it.</summary>
    private static string Pace(double multiplier) => Math.Abs(multiplier - 1.0) < 0.0005
        ? "at the usual rate"
        : multiplier > 1.0
            ? $"at {multiplier:0.###} times the usual rate"
            : $"at {multiplier * 100.0:0.#}% of the usual rate";

    private static string SkillTitle(SkillName skill) => SkillInfo.Table[(int)skill].Name;
}
