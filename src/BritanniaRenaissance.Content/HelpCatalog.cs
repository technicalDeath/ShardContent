using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using Server;
using Server.Items;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The help text (docs/Help-Gumps-Plan.md): one page for each skill of the era, grouped in categories that become the tabs of the skill guide, and one topic for
/// each kind of item a player can hold. It is data (<c>data/help/skills.json</c> and <c>items.json</c>, deployed to <c>Configuration/help</c>), so the wording can
/// change without a build, and it is validated whenever it is loaded: every link must resolve, every skill must have exactly one page, every item type that can
/// be held must reach a topic, and no page may name a feature the shard does not have.
/// </summary>
public sealed class HelpCatalog
{
    public const int SchemaVersion = 1;

    /// <summary>The skill guide has six tabs and each skill is a blue oval down the left: about this many fit under a tab.</summary>
    public const int MaxSkillsPerCategory = 10;

    public const int MaxCategories = 6;

    /// <summary>The key of the general topic every item that has no better one falls back to.</summary>
    public const string CatchAllKey = "other-item";

    /// <summary>The links on an item page (skills and related items) all sit in the left column under the picture, with Back, so this many fit.</summary>
    public const int MaxLinks = 4;

    /// <summary>One paragraph: plain text (a "# " start makes it a heading), a generated block, or text shown only while a feature flag is on.</summary>
    public sealed record Paragraph(string? Text, string? Generate, string? Requires);

    public sealed record Category(string Key, string Title, IReadOnlyList<SkillName> Skills);

    public sealed record SkillPage(SkillName Skill, IReadOnlyList<Paragraph> Paragraphs, IReadOnlyList<string> Items);

    public sealed record ItemTopic(
        string Key, string Title, int Art, IReadOnlyList<string> Types, IReadOnlyList<string> Inherits, IReadOnlyList<Paragraph> Paragraphs,
        IReadOnlyList<SkillName> Skills, IReadOnlyList<string> Related
    );

    public IReadOnlyList<Category> Categories { get; init; } = [];

    public IReadOnlyList<SkillPage> Skills { get; init; } = [];

    public IReadOnlyList<ItemTopic> Items { get; init; } = [];

    // ---- the files

    private static readonly JsonSerializerOptions Options = new()
    {
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
        PropertyNameCaseInsensitive = true,
        Converters = { new ParagraphConverter() }
    };

    private sealed class ParagraphConverter : JsonConverter<ParagraphDto>
    {
        public override ParagraphDto Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
        {
            if (reader.TokenType == JsonTokenType.String)
            {
                return new ParagraphDto { Text = reader.GetString() };
            }

            using var document = JsonDocument.ParseValue(ref reader);
            var root = document.RootElement;

            return new ParagraphDto
            {
                Text = root.TryGetProperty("text", out var text) ? text.GetString() : null,
                Generate = root.TryGetProperty("generate", out var generate) ? generate.GetString() : null,
                Requires = root.TryGetProperty("requires", out var requires) ? requires.GetString() : null
            };
        }

        public override void Write(Utf8JsonWriter writer, ParagraphDto value, JsonSerializerOptions options) => throw new NotSupportedException();
    }

    private sealed class ParagraphDto
    {
        public string? Text { get; set; }

        public string? Generate { get; set; }

        public string? Requires { get; set; }
    }

    private sealed class SkillsFile
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }

        [JsonPropertyName("categories")] public List<CategoryDto> Categories { get; set; } = [];

        [JsonPropertyName("skills")] public List<SkillDto> Skills { get; set; } = [];
    }

    private sealed class CategoryDto
    {
        public string Key { get; set; } = "";

        public string Title { get; set; } = "";

        public List<string> Skills { get; set; } = [];
    }

    private sealed class SkillDto
    {
        public string Skill { get; set; } = "";

        public List<ParagraphDto> Paragraphs { get; set; } = [];

        public List<string> Items { get; set; } = [];
    }

    private sealed class ItemsFile
    {
        [JsonPropertyName("schemaVersion")] public int SchemaVersion { get; set; }

        [JsonPropertyName("items")] public List<ItemDto> Items { get; set; } = [];
    }

    private sealed class ItemDto
    {
        public string Key { get; set; } = "";

        public string Title { get; set; } = "";

        public int Art { get; set; }

        public List<string> Types { get; set; } = [];

        public List<string> Inherits { get; set; } = [];

        public List<ParagraphDto> Paragraphs { get; set; } = [];

        public List<string> Skills { get; set; } = [];

        public List<string> Related { get; set; } = [];
    }

    /// <summary>Parses the two files. A name that is not a skill is kept out and reported by <see cref="Validate"/> through <see cref="ParseErrors"/>.</summary>
    public static HelpCatalog Parse(string skillsJson, string itemsJson, List<string> errors)
    {
        var skills = JsonSerializer.Deserialize<SkillsFile>(skillsJson, Options) ?? new SkillsFile();
        var items = JsonSerializer.Deserialize<ItemsFile>(itemsJson, Options) ?? new ItemsFile();

        if (skills.SchemaVersion != SchemaVersion)
        {
            errors.Add($"skills.json schemaVersion must be {SchemaVersion}, but was {skills.SchemaVersion}.");
        }

        if (items.SchemaVersion != SchemaVersion)
        {
            errors.Add($"items.json schemaVersion must be {SchemaVersion}, but was {items.SchemaVersion}.");
        }

        SkillName? Skill(string name, string where)
        {
            if (Enum.TryParse<SkillName>(name, true, out var skill) && Enum.IsDefined(skill))
            {
                return skill;
            }

            errors.Add($"{where}: \"{name}\" is not a skill.");
            return null;
        }

        Paragraph Convert(ParagraphDto p) => new(p.Text, p.Generate, p.Requires);

        return new HelpCatalog
        {
            Categories = skills.Categories.Select(c => new Category(
                c.Key, c.Title, c.Skills.Select(s => Skill(s, $"category {c.Key}")).OfType<SkillName>().ToArray()
            )).ToArray(),
            Skills = skills.Skills
                .Select(s => (Name: Skill(s.Skill, "skills"), Dto: s))
                .Where(p => p.Name is not null)
                .Select(p => new SkillPage(p.Name!.Value, p.Dto.Paragraphs.Select(Convert).ToArray(), p.Dto.Items))
                .ToArray(),
            Items = items.Items.Select(i => new ItemTopic(
                i.Key, i.Title, i.Art, i.Types, i.Inherits, i.Paragraphs.Select(Convert).ToArray(),
                i.Skills.Select(s => Skill(s, $"item {i.Key}")).OfType<SkillName>().ToArray(), i.Related
            )).ToArray()
        };
    }

    // ---- validation

    /// <summary>The skills of the era: the Age of Shadows and later skills are not in this shard, so they have no page.</summary>
    public static IReadOnlyList<SkillName> EraSkills { get; } =
        Enum.GetValues<SkillName>().Where(static s => (int)s <= (int)SkillName.RemoveTrap).ToArray();

    private static readonly string[] BannedWords = ["Britannia " + "Renaissance", "Age of Shadows", "Trammel"];

    /// <summary>The feature flags a paragraph may be gated on.</summary>
    public static IReadOnlyCollection<string> GateNames { get; } = typeof(DeferredFeatureFlags)
        .GetProperties(BindingFlags.Public | BindingFlags.Instance)
        .Where(static p => p.PropertyType == typeof(bool) && p.CanWrite)
        .Select(static p => p.Name)
        .ToArray();

    /// <summary>Every generated block the help text may ask for.</summary>
    public static IReadOnlyCollection<string> GeneratorNames { get; } = HelpGenerators.Names;

    public List<string> Validate(Func<string, Type?> typeOf, IReadOnlyCollection<Type> holdableTypes)
    {
        var errors = new List<string>();
        var skillKeys = new HashSet<SkillName>();
        var categoryKeys = new HashSet<string>();

        if (Categories.Count is 0 or > MaxCategories)
        {
            errors.Add($"the skill guide needs between 1 and {MaxCategories} categories, but has {Categories.Count}.");
        }

        foreach (var category in Categories)
        {
            if (!categoryKeys.Add(category.Key))
            {
                errors.Add($"category key \"{category.Key}\" appears twice.");
            }

            if (!GuideWindow.TabTitleFits(category.Title))
            {
                errors.Add($"category \"{category.Title}\" does not fit a tab.");
            }

            if (category.Skills.Count is 0 or > MaxSkillsPerCategory)
            {
                errors.Add($"category \"{category.Title}\" must hold 1 to {MaxSkillsPerCategory} skills, but holds {category.Skills.Count}.");
            }

            foreach (var skill in category.Skills)
            {
                if (!skillKeys.Add(skill))
                {
                    errors.Add($"{skill} is in more than one category.");
                }

                if (!EraSkills.Contains(skill))
                {
                    errors.Add($"{skill} is not a skill of this era.");
                }
            }
        }

        foreach (var skill in EraSkills.Where(s => !skillKeys.Contains(s)))
        {
            errors.Add($"{skill} is in no category.");
        }

        var pageSkills = new HashSet<SkillName>();
        var itemKeys = Items.Select(static i => i.Key).ToList();

        if (itemKeys.Distinct().Count() != itemKeys.Count)
        {
            errors.Add("an item topic key appears twice.");
        }

        var itemKeySet = new HashSet<string>(itemKeys);

        foreach (var page in Skills)
        {
            if (!pageSkills.Add(page.Skill))
            {
                errors.Add($"{page.Skill} has two pages.");
            }

            CheckParagraphs($"skill {page.Skill}", page.Paragraphs, errors);
            CheckSkillPage(page, errors);

            foreach (var key in page.Items.Where(k => !itemKeySet.Contains(k)))
            {
                errors.Add($"skill {page.Skill} lists an item topic \"{key}\" that does not exist.");
            }
        }

        foreach (var skill in EraSkills.Where(s => !pageSkills.Contains(s)))
        {
            errors.Add($"{skill} has no page.");
        }

        foreach (var topic in Items)
        {
            if (string.IsNullOrWhiteSpace(topic.Title) || !GuideWindow.TopicTitleFits(topic.Title))
            {
                errors.Add($"item topic \"{topic.Key}\": the title is empty or too long for the oval.");
            }

            CheckParagraphs($"item topic {topic.Key}", topic.Paragraphs, errors);

            if (topic.Art <= 0)
            {
                errors.Add($"item topic \"{topic.Key}\" needs an art number: the picture shown when it is opened from a link.");
            }

            if (topic.Types.Count == 0 && topic.Inherits.Count == 0 && topic.Key != CatchAllKey)
            {
                // A topic reached only by links is fine.
            }

            foreach (var name in topic.Types.Concat(topic.Inherits))
            {
                if (typeOf(name) is null)
                {
                    errors.Add($"item topic \"{topic.Key}\": \"{name}\" is not exactly one item type (it is missing or the name is ambiguous).");
                }
            }

            foreach (var key in topic.Related.Where(k => !itemKeySet.Contains(k)))
            {
                errors.Add($"item topic \"{topic.Key}\" is related to \"{key}\", which does not exist.");
            }

            if (topic.Skills.Any(s => !EraSkills.Contains(s)))
            {
                errors.Add($"item topic \"{topic.Key}\" links to a skill that is not of this era.");
            }

            if (topic.Skills.Count + topic.Related.Count > MaxLinks)
            {
                errors.Add($"item topic \"{topic.Key}\" has more than {MaxLinks} links, which is all the left column holds.");
            }
        }

        // A type name belongs to one topic: the writers work in parts, and the first claim would otherwise win without a word.
        foreach (var (kind, names) in new[]
                 {
                     ("types", Items.SelectMany(static i => i.Types.Select(t => (Name: t, i.Key)))),
                     ("inherits", Items.SelectMany(static i => i.Inherits.Select(t => (Name: t, i.Key))))
                 })
        {
            foreach (var group in names.GroupBy(static n => n.Name).Where(static g => g.Select(static n => n.Key).Distinct().Count() > 1))
            {
                errors.Add($"\"{group.Key}\" is listed under {kind} by more than one topic: {string.Join(", ", group.Select(static n => n.Key).Distinct())}.");
            }
        }

        // The general item page is the safety net that lets every item answer Help; it must exist, and it must be the base type's.
        if (!Items.Any(static i => i.Key == CatchAllKey && i.Inherits.Contains("Item")))
        {
            errors.Add($"the general item page \"{CatchAllKey}\" (inherits Item) is missing, so an item with no topic of its own would have no help.");
        }

        return errors;
    }

    private static void CheckSkillPage(SkillPage page, List<string> errors)
    {
        var generated = page.Paragraphs.Where(static p => p.Generate is not null).Select(static p => p.Generate!).ToHashSet();
        var text = page.Paragraphs.Where(static p => p.Text is not null).Select(static p => p.Text!).ToArray();

        foreach (var need in new[] { HelpGenerators.Stats, HelpGenerators.Gain })
        {
            if (!generated.Contains(need))
            {
                errors.Add($"skill {page.Skill}: the page must carry the generated \"{need}\" block, which reads the stats and the gain rules from the game.");
            }
        }

        if (CraftTables.TryGetValue(page.Skill, out var table) && !generated.Contains(table))
        {
            errors.Add($"skill {page.Skill}: the page must carry the generated \"{table}\" recipe table.");
        }

        if (text.Count(static t => t.StartsWith(WelcomeGuide.HeadingMark, StringComparison.Ordinal)) < MinSkillPageHeadings || text.Sum(static t => t.Length) < MinSkillPageCharacters)
        {
            errors.Add($"skill {page.Skill}: the page is a stub (it needs at least {MinSkillPageHeadings} headings and {MinSkillPageCharacters} characters of its own text).");
        }
    }

    private static void CheckParagraphs(string where, IReadOnlyList<Paragraph> paragraphs, List<string> errors)
    {
        if (paragraphs.Sum(static p => p.Text?.Length ?? 0) > MaxPageCharacters)
        {
            errors.Add($"{where} is longer than {MaxPageCharacters} characters.");
        }

        if (paragraphs.Count == 0)
        {
            errors.Add($"{where} has no text.");
        }

        foreach (var paragraph in paragraphs)
        {
            if ((paragraph.Text is null) == (paragraph.Generate is null))
            {
                errors.Add($"{where}: a paragraph needs exactly one of text and generate.");
                continue;
            }

            if (paragraph.Requires is { } gate && !GateNames.Contains(gate))
            {
                errors.Add($"{where}: \"{gate}\" is not a feature flag.");
            }

            if (paragraph.Generate is { } generate && !GeneratorNames.Contains(generate))
            {
                errors.Add($"{where}: \"{generate}\" is not a generated block (known: {string.Join(", ", GeneratorNames)}).");
            }

            if (paragraph.Text is { } text)
            {
                if (string.IsNullOrWhiteSpace(text))
                {
                    errors.Add($"{where} has an empty paragraph.");
                }

                foreach (var word in BannedWords.Where(w => text.Contains(w, StringComparison.OrdinalIgnoreCase)))
                {
                    errors.Add($"{where} says \"{word}\".");
                }
            }
        }
    }

    // ---- which topic shows an item

    private Dictionary<string, ItemTopic>? _byType;
    private Dictionary<string, ItemTopic>? _byBase;

    /// <summary>The topic for an item of this type: the first topic naming the type, or a base type, going up from the item's own type.</summary>
    public ItemTopic? TopicFor(Type type)
    {
        _byType ??= Items.SelectMany(i => i.Types.Select(t => (t, i))).GroupBy(p => p.t).ToDictionary(g => g.Key, g => g.First().i);
        _byBase ??= Items.SelectMany(i => i.Inherits.Select(t => (t, i))).GroupBy(p => p.t).ToDictionary(g => g.Key, g => g.First().i);

        for (var current = type; current is not null; current = current.BaseType)
        {
            if (_byType.TryGetValue(current.Name, out var exact))
            {
                return exact;
            }

            if (_byBase.TryGetValue(current.Name, out var inherited))
            {
                return inherited;
            }
        }

        return null;
    }

    /// <summary>The item types that reach only the general item page. The goal is to keep this short: every kind of item a player meets has a topic of its own or a group's.</summary>
    public IReadOnlyList<Type> GeneralPageTypes(IEnumerable<Type> holdableTypes) =>
        holdableTypes.Where(t => TopicFor(t)?.Key == CatchAllKey).ToArray();

    public ItemTopic? ItemByKey(string key) => Items.FirstOrDefault(i => i.Key == key);

    /// <summary>The most related items a skill page lists.</summary>
    public const int MaxRelatedItems = 16;

    /// <summary>
    /// The item topics a skill page points to: the ones the page names itself, then every topic that names the skill, so the skill pages and the item topics can be
    /// written separately and still meet. The general item page is never one of them.
    /// </summary>
    public IReadOnlyList<ItemTopic> ItemsFor(SkillName skill)
    {
        var named = PageOf(skill)?.Items.Select(ItemByKey).OfType<ItemTopic>() ?? [];

        return named.Concat(Items.Where(i => i.Skills.Contains(skill)))
            .Where(static i => i.Key != CatchAllKey)
            .Distinct()
            .Take(MaxRelatedItems)
            .ToArray();
    }

    /// <summary>The recipe table a craft skill's page must carry: the table is read from the game, so it can never disagree with what the craft menu offers.</summary>
    public static readonly IReadOnlyDictionary<SkillName, string> CraftTables = new Dictionary<SkillName, string>
    {
        [SkillName.Alchemy] = "craft:Alchemy",
        [SkillName.Blacksmith] = "craft:Blacksmithing",
        [SkillName.Fletching] = "craft:Bowcraft",
        [SkillName.Carpentry] = "craft:Carpentry",
        [SkillName.Cartography] = "craft:Cartography",
        [SkillName.Inscribe] = "craft:Inscription",
        [SkillName.Tailoring] = "craft:Tailoring",
        [SkillName.Tinkering] = "craft:Tinkering"
    };

    /// <summary>The least a skill page may say: a page with less is a stub.</summary>
    public const int MinSkillPageHeadings = 3;

    public const int MinSkillPageCharacters = 900;

    /// <summary>The most own text a page may hold: the whole page goes to the client in one text field, and the longest page tested in the real client is below this.</summary>
    public const int MaxPageCharacters = 24000;

    public SkillPage? PageOf(SkillName skill) => Skills.FirstOrDefault(p => p.Skill == skill);

    public Category? CategoryOf(SkillName skill) => Categories.FirstOrDefault(c => c.Skills.Contains(skill));

    // ---- the item types that can be held

    /// <summary>
    /// The concrete item types a player can pick up and carry: public, not abstract, with a public constructor that needs no argument, and not a type that is never
    /// carried (statics, doors, signs, spawners, teleporters and the other world furniture listed here). Used to count how many fall to the general item page.
    /// </summary>
    public static IReadOnlyList<Type> HoldableTypes(IEnumerable<Assembly> assemblies) =>
        assemblies.SelectMany(static a => SafeTypes(a))
            .Where(static t => t.IsClass && !t.IsAbstract && t.IsPublic && typeof(Item).IsAssignableFrom(t) && CanBeCreatedWithNoArguments(t))
            .Where(static t => !NeverCarried.Any(b => b.IsAssignableFrom(t)) && !NeverCarriedNamespaces.Any(n => (t.Namespace ?? "").StartsWith(n, StringComparison.Ordinal)) && !IsSpawner(t))
            .OrderBy(static t => t.FullName, StringComparer.Ordinal)
            .ToArray();

    /// <summary>A public constructor that needs no argument: none at all, or only optional ones (a stack of items takes an optional amount).</summary>
    private static bool CanBeCreatedWithNoArguments(Type type) =>
        type.GetConstructors(BindingFlags.Public | BindingFlags.Instance).Any(static c => c.GetParameters().All(static p => p.IsOptional));

    private static bool IsSpawner(Type type)
    {
        for (var current = type; current is not null; current = current.BaseType)
        {
            if (current.Name is "Spawner" or "BaseSpawner")
            {
                return true;
            }
        }

        return false;
    }

    private static Type[] SafeTypes(Assembly assembly)
    {
        try
        {
            return assembly.GetTypes();
        }
        catch (ReflectionTypeLoadException e)
        {
            return e.Types.OfType<Type>().ToArray();
        }
    }

    /// <summary>Base types of items that stand in the world and are never picked up.</summary>
    private static readonly Type[] NeverCarried = [typeof(Static), typeof(BaseDoor), typeof(BaseSign), typeof(Teleporter), typeof(BaseAddon)];

    private static readonly string[] NeverCarriedNamespaces = ["Server.Engines.ConPVP", "Server.Misc.Test", "Server.Engines.Quests"];

    /// <summary>The name-to-type lookup for the topics: a simple name must match exactly one holdable-or-base type.</summary>
    public static Func<string, Type?> TypeLookup(IEnumerable<Assembly> assemblies)
    {
        var byName = assemblies.SelectMany(static a => SafeTypes(a))
            .Where(static t => t.IsClass && t.IsPublic && typeof(Item).IsAssignableFrom(t))
            .GroupBy(static t => t.Name)
            .ToDictionary(static g => g.Key, static g => g.ToArray());

        return name => byName.TryGetValue(name, out var found) && found.Length == 1 ? found[0] : null;
    }
}
