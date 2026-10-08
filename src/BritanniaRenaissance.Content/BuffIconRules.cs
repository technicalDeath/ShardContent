using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using Server.Engines.BuffIcons;

namespace BritanniaRenaissance.Content;

/// <summary>
/// What the buff bar says, as data (Configuration/buff-icons.json). Stock spells add their own icons with the later eras' text
/// (percentages, resistances), so the shard rewrites each one from this table, and shows the effects stock has no icon for
/// (UOR's Protection, Reactive Armor, Poison, the shard's own states) from the same table. Texts hold named values such as
/// <c>{buff.Str}</c>, filled in from the effect actually applied, so a tooltip always agrees with what happened.
/// </summary>
public sealed class BuffIconRules
{
    [JsonPropertyName("schemaVersion")]
    public int SchemaVersion { get; set; }

    /// <summary>"hide": a stock icon that is not in <see cref="Stock"/> is never shown (a later era's effect cannot leak in). "show": it keeps its stock text.</summary>
    [JsonPropertyName("unlistedStockIcons")]
    public string UnlistedStockIcons { get; set; } = "hide";

    [JsonPropertyName("customIcons")]
    public List<BuffCustomIcon> CustomIcons { get; set; } = [];

    /// <summary>Icons the engine's own spells and skills add, by <see cref="BuffIcon"/> name, with the text to show instead.</summary>
    [JsonPropertyName("stock")]
    public Dictionary<string, BuffText> Stock { get; set; } = [];

    /// <summary>Icons the shard adds while a state holds, by state name (see <see cref="BuffIconCatalog.StateValueNames"/>).</summary>
    [JsonPropertyName("states")]
    public Dictionary<string, BuffStateText> States { get; set; } = [];
}

/// <summary>An icon the stock list does not have: its server-side id is <see cref="BuffIconCatalog.FirstCustomIconId"/> plus the slot, its picture is gump art <see cref="Art"/>.</summary>
public sealed class BuffCustomIcon
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("slot")]
    public int Slot { get; set; }

    [JsonPropertyName("art")]
    public int Art { get; set; }
}

public class BuffText
{
    [JsonPropertyName("title")]
    public string Title { get; set; } = "";

    [JsonPropertyName("lines")]
    public List<string> Lines { get; set; } = [];
}

public sealed class BuffStateText : BuffText
{
    [JsonPropertyName("icon")]
    public string Icon { get; set; } = "";

    /// <summary>The state knows when it ends, so the icon shows a countdown.</summary>
    [JsonPropertyName("countdown")]
    public bool Countdown { get; set; }
}

/// <summary>The fixed vocabulary the data may use: which states exist and which named values each one offers.</summary>
public static class BuffIconCatalog
{
    /// <summary>The client's generic text ("~1_NOTHING~"): the text we send is shown as given, title and lines in one tooltip.</summary>
    public const int GenericTitleCliloc = 1042971;

    /// <summary>The first id after the last stock icon the client's table knows (0x4A5); custom icons take the next ids in order.</summary>
    public const int FirstCustomIconId = 0x4A6;

    public const int MaxCustomIcons = 16;

    public const int MinCustomArt = 50000;

    public const int MaxCustomArt = 50999;

    /// <summary>The named values a stock icon's text may use, read from the stat mods the spell applied.</summary>
    public static readonly IReadOnlyList<string> StockValueNames = ["buff.Str", "buff.Dex", "buff.Int", "curse.Str", "curse.Dex", "curse.Int"];

    /// <summary>Each state the shard can show, with the named values its text may use.</summary>
    public static readonly IReadOnlyDictionary<string, IReadOnlyList<string>> StateValueNames = new Dictionary<string, IReadOnlyList<string>>
    {
        ["protection"] = ["chance"],
        ["archProtection"] = ["bonus"],
        ["reactiveArmor"] = ["points"],
        ["magicReflect"] = ["points"],
        ["poison"] = ["level"],
        ["polymorph"] = [],
        ["knockedOut"] = [],
        ["criminal"] = [],
        ["intent"] = [],
        ["wardPrimed"] = ["minutes", "caught"],
        ["wardActivated"] = ["minutes", "caught"],
        ["faintMemoriesLocked"] = ["points", "unlock"],
        ["faintMemoriesReady"] = ["points"]
    };
}

public static class BuffIconRulesLoader
{
    public const string RelativePath = "Configuration/buff-icons.json";

    private const int MaxTitle = 40;
    private const int MaxLine = 120;
    private const int MaxLines = 6;
    private const int MaxText = 480;

    private static readonly Regex Placeholder = new(@"\{([^{}]*)\}", RegexOptions.Compiled);

    private static readonly JsonSerializerOptions Options = new()
    {
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true
    };

    public static BuffIconRules Parse(string json) =>
        JsonSerializer.Deserialize<BuffIconRules>(json, Options) ?? throw new InvalidOperationException("The buff icon rules are empty.");

    public static BuffIconRules Load()
    {
        var path = Path.Combine(Server.Core.BaseDirectory, RelativePath);

        if (!File.Exists(path))
        {
            throw new InvalidOperationException($"Buff icon rules are missing: {path}");
        }

        var rules = Parse(File.ReadAllText(path));
        var errors = Validate(rules);

        if (errors.Count > 0)
        {
            throw new InvalidOperationException(
                $"Buff icon rules failed validation:{Environment.NewLine}- {string.Join(Environment.NewLine + "- ", errors)}"
            );
        }

        return rules;
    }

    public static IReadOnlyList<string> Validate(BuffIconRules rules)
    {
        var errors = new List<string>();

        if (rules.SchemaVersion != 1)
        {
            errors.Add($"schemaVersion must be 1, but was {rules.SchemaVersion}.");
        }

        if (rules.UnlistedStockIcons is not ("hide" or "show"))
        {
            errors.Add($"unlistedStockIcons must be \"hide\" or \"show\", but was \"{rules.UnlistedStockIcons}\".");
        }

        ValidateCustomIcons(rules, errors);

        foreach (var (name, text) in rules.Stock)
        {
            if (!IsStockIconName(name))
            {
                errors.Add($"stock.{name} is not a stock buff icon.");
            }

            ValidateText($"stock.{name}", text, BuffIconCatalog.StockValueNames, errors);
        }

        foreach (var (state, text) in rules.States)
        {
            if (!BuffIconCatalog.StateValueNames.TryGetValue(state, out var values))
            {
                errors.Add($"states.{state} is not a state the shard can show ({string.Join(", ", BuffIconCatalog.StateValueNames.Keys)}).");
                continue;
            }

            if (!TryResolveIcon(rules, text.Icon, out _))
            {
                errors.Add($"states.{state}.icon \"{text.Icon}\" is neither a stock icon nor one of customIcons.");
            }

            ValidateText($"states.{state}", text, values, errors);
        }

        return errors;
    }

    private static void ValidateCustomIcons(BuffIconRules rules, List<string> errors)
    {
        var names = new HashSet<string>();
        var slots = new HashSet<int>();
        var arts = new HashSet<int>();

        foreach (var icon in rules.CustomIcons)
        {
            if (icon.Name.Length == 0 || !icon.Name.All(char.IsLetter))
            {
                errors.Add($"customIcons name \"{icon.Name}\" must be letters only.");
            }
            else if (IsStockIconName(icon.Name))
            {
                errors.Add($"customIcons name \"{icon.Name}\" is already a stock icon.");
            }
            else if (!names.Add(icon.Name))
            {
                errors.Add($"customIcons name \"{icon.Name}\" is used twice.");
            }

            if (icon.Slot is < 0 or >= BuffIconCatalog.MaxCustomIcons)
            {
                errors.Add($"customIcons \"{icon.Name}\" slot {icon.Slot} must be 0 to {BuffIconCatalog.MaxCustomIcons - 1}.");
            }
            else if (!slots.Add(icon.Slot))
            {
                errors.Add($"customIcons slot {icon.Slot} is used twice.");
            }

            if (icon.Art is < BuffIconCatalog.MinCustomArt or > BuffIconCatalog.MaxCustomArt)
            {
                errors.Add($"customIcons \"{icon.Name}\" art {icon.Art} must be {BuffIconCatalog.MinCustomArt} to {BuffIconCatalog.MaxCustomArt}.");
            }
            else if (!arts.Add(icon.Art))
            {
                errors.Add($"customIcons art {icon.Art} is used twice.");
            }
        }
    }

    private static void ValidateText(string where, BuffText text, IReadOnlyCollection<string> values, List<string> errors)
    {
        if (text.Title.Length is 0 or > MaxTitle)
        {
            errors.Add($"{where}.title must be 1 to {MaxTitle} characters.");
        }
        else if (BadCharacters(text.Title) || text.Title.Contains('{'))
        {
            errors.Add($"{where}.title may not contain tabs, line breaks, < > or values.");
        }

        if (text.Lines.Count > MaxLines)
        {
            errors.Add($"{where}.lines may hold at most {MaxLines} lines.");
        }

        var total = text.Title.Length;

        foreach (var line in text.Lines)
        {
            total += line.Length;

            if (line.Length is 0 or > MaxLine)
            {
                errors.Add($"{where} has a line of {line.Length} characters; each must be 1 to {MaxLine}.");
                continue;
            }

            if (BadCharacters(line))
            {
                errors.Add($"{where} line \"{line}\" contains a tab, a line break, < or >.");
            }

            foreach (Match match in Placeholder.Matches(line))
            {
                if (!values.Contains(match.Groups[1].Value))
                {
                    errors.Add($"{where} line \"{line}\" uses {{{match.Groups[1].Value}}}, which is not one of: {string.Join(", ", values)}.");
                }
            }

            if (Placeholder.Replace(line, "").AsSpan().IndexOfAny('{', '}') >= 0)
            {
                errors.Add($"{where} line \"{line}\" has an unbalanced brace.");
            }
        }

        if (total > MaxText)
        {
            errors.Add($"{where} is {total} characters; the whole text may be {MaxText}.");
        }
    }

    private static readonly char[] Forbidden = ['\t', '\r', '\n', '<', '>'];

    private static bool BadCharacters(string text) => text.IndexOfAny(Forbidden) >= 0;

    private static bool IsStockIconName(string name) =>
        name.Length > 0 && name.All(char.IsLetter) && Enum.TryParse<BuffIcon>(name, false, out var icon) && Enum.IsDefined(icon);

    /// <summary>A stock icon by its <see cref="BuffIcon"/> name, or a custom one by its name: the id the server sends.</summary>
    public static bool TryResolveIcon(BuffIconRules rules, string name, out BuffIcon icon)
    {
        foreach (var custom in rules.CustomIcons)
        {
            if (custom.Name == name)
            {
                icon = (BuffIcon)(BuffIconCatalog.FirstCustomIconId + custom.Slot);
                return true;
            }
        }

        if (IsStockIconName(name))
        {
            icon = Enum.Parse<BuffIcon>(name, false);
            return true;
        }

        icon = default;
        return false;
    }

    /// <summary>
    /// The text the client shows: the title, then each line on its own line. A line whose named value is not known (the effect is not
    /// on the player, so it has nothing to say) is left out instead of showing a hole.
    /// </summary>
    public static string Render(BuffText text, Func<string, string?> value)
    {
        var builder = new StringBuilder(text.Title);

        foreach (var line in text.Lines)
        {
            var filled = Fill(line, value);

            if (filled is not null)
            {
                builder.Append("<br>").Append(filled);
            }
        }

        return builder.ToString();
    }

    private static string? Fill(string line, Func<string, string?> value)
    {
        var missing = false;

        var filled = Placeholder.Replace(
            line,
            match =>
            {
                var found = value(match.Groups[1].Value);
                missing |= found is null;
                return found ?? "";
            }
        );

        return missing ? null : filled;
    }
}
