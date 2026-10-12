using System.Text.Json;
using Server;
using Server.Engines.Craft;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The help text (docs/Help-Gumps-Plan.md): the shipped data files must validate (every era skill has a page and one category, every link resolves, every item that can
/// be held reaches a topic, no page names a feature the shard does not have), a topic is found by the item's own type before its base types, and the generated blocks
/// read the game's own tables.
/// </summary>
public class HelpCatalogTests
{
    static HelpCatalogTests()
    {
        // The skill table and the recipe names are loaded from client and data files at server start; the tests load the same skills file and use the type names.
        if (SkillInfo.Table.Length == 0)
        {
            SkillInfo.Table = Server.Json.JsonConfig.Deserialize<SkillInfo[]>(FindSkillsFile());
        }

        // The few client texts the Alchemy table reads, as the game's client file has them (plural and lower case, as in its craft window).
        HelpGenerators.ClilocText = static number => number switch
        {
            1044529 => "empty bottles",
            1044353 => "black pearl",
            1044356 => "ginseng",
            1044533 => "Heal",
            1044543 => "lesser heal",
            _       => null
        };
    }

    private static string FindSkillsFile()
    {
        for (var folder = new DirectoryInfo(AppContext.BaseDirectory); folder is not null; folder = folder.Parent)
        {
            var candidate = Path.Combine(folder.FullName, "ModernUO", "Distribution", "Data", "skills.json");

            if (File.Exists(candidate))
            {
                return candidate;
            }
        }

        throw new FileNotFoundException("ModernUO/Distribution/Data/skills.json was not found above " + AppContext.BaseDirectory);
    }

    private static readonly string DataFolder = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "help");

    private static (HelpCatalog Catalog, List<string> ParseErrors) Shipped()
    {
        var errors = new List<string>();
        var catalog = HelpCatalog.Parse(File.ReadAllText(Path.Combine(DataFolder, "skills.json")), File.ReadAllText(Path.Combine(DataFolder, "items.json")), errors);

        return (catalog, errors);
    }

    private static readonly System.Reflection.Assembly[] ItemAssemblies = [typeof(Item).Assembly, typeof(Bottle).Assembly, typeof(HelpCatalog).Assembly];

    private static ShardRules ShippedRules() =>
        JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json")))!;

    // ---- the shipped files

    [Fact]
    public void TheShippedFilesParse() => Assert.Empty(Shipped().ParseErrors);

    [Fact]
    public void TheShippedHelpTextValidates()
    {
        var (catalog, parseErrors) = Shipped();
        var errors = parseErrors.Concat(catalog.Validate(HelpCatalog.TypeLookup(ItemAssemblies), HelpCatalog.HoldableTypes(ItemAssemblies))).ToList();

        Assert.True(errors.Count == 0, string.Join(Environment.NewLine, errors.Take(30)));
    }

    [Fact]
    public void TheSkillGuideHasSixTabsHoldingAllFortyNineEraSkillsOnce()
    {
        var (catalog, _) = Shipped();

        Assert.Equal(6, catalog.Categories.Count);
        Assert.Equal(49, HelpCatalog.EraSkills.Count);
        Assert.Equal(49, catalog.Categories.SelectMany(static c => c.Skills).Distinct().Count());
        Assert.All(catalog.Categories, static c => Assert.InRange(c.Skills.Count, 1, HelpCatalog.MaxSkillsPerCategory));
        Assert.All(catalog.Categories, static c => Assert.True(GuideWindow.TabTitleFits(c.Title), c.Title));
    }

    [Fact]
    public void NoAgeOfShadowsSkillIsInTheEraList() =>
        Assert.DoesNotContain(HelpCatalog.EraSkills, static s => s is SkillName.Necromancy or SkillName.Chivalry or SkillName.Focus or SkillName.Bushido);

    // ---- which topic shows an item

    [Fact]
    public void AnItemFindsItsOwnTopicBeforeAGroupTopic()
    {
        var (catalog, _) = Shipped();

        Assert.Equal("empty-bottle", catalog.TopicFor(typeof(Bottle))!.Key);
        Assert.Equal("mortar-pestle", catalog.TopicFor(typeof(MortarPestle))!.Key);
        Assert.Equal("potion-keg", catalog.TopicFor(typeof(PotionKeg))!.Key);
        Assert.Equal("potion-heal", catalog.TopicFor(typeof(GreaterHealPotion))!.Key);
        Assert.Equal("potion-cure", catalog.TopicFor(typeof(LesserCurePotion))!.Key);
        Assert.Equal("potion-explosion", catalog.TopicFor(typeof(LesserExplosionPotion))!.Key);
    }

    [Fact]
    public void AllEightReagentsShareOneTopic()
    {
        var (catalog, _) = Shipped();

        foreach (var reagent in new[] { typeof(BlackPearl), typeof(Bloodmoss), typeof(Garlic), typeof(Ginseng), typeof(MandrakeRoot), typeof(Nightshade), typeof(SulfurousAsh), typeof(SpidersSilk) })
        {
            Assert.Equal("reagents", catalog.TopicFor(reagent)!.Key);
        }
    }

    [Fact]
    public void APotionWithNoTopicOfItsOwnFallsToTheGeneralPotionPageAndAnythingElseToTheGeneralItemPage()
    {
        var (catalog, _) = Shipped();

        Assert.Equal("potion", catalog.TopicFor(typeof(InvisibilityPotion))!.Key);
        Assert.Equal(HelpCatalog.CatchAllKey, catalog.TopicFor(typeof(AdminRobe))!.Key);   // a staff item has no page of its own
    }

    [Fact]
    public void TheHoldableTypesAreFoundAndLeaveOutWorldFurniture()
    {
        var types = HelpCatalog.HoldableTypes(ItemAssemblies);

        Assert.Contains(typeof(Bottle), types);
        Assert.Contains(typeof(Longsword), types);
        Assert.DoesNotContain(typeof(Static), types);
        Assert.DoesNotContain(types, static t => typeof(BaseDoor).IsAssignableFrom(t));
    }

    // ---- coverage: what a player meets has a page of its own

    /// <summary>The item types that reach only the general page are mostly later-era, decorative or staff items; the count must not grow (lower it as pages are added).</summary>
    private const int GeneralPageCeiling = 1100;

    private static readonly string[] EverydayItems =
    [
        "Dagger", "Longsword", "Bow", "Crossbow", "Arrow", "Bolt", "PlateChest", "ChainChest", "Buckler", "WoodenShield", "LeatherChest", "Bandage", "Lockpick", "Pickaxe",
        "Hatchet", "Shovel", "SewingKit", "TinkerTools", "SmithHammer", "Backpack", "Bag", "Spellbook", "ReactiveArmorScroll", "Apple", "IronOre", "IronIngot", "Log", "Board",
        "Leather", "Cloth", "Gold", "Torch", "Lantern", "Scissors", "Runebook", "FishingPole", "Shirt", "Robe", "Boots", "Fish", "Bedroll", "Key", "BlankScroll", "Feather"
    ];

    [Fact]
    public void TheTypesThatReachOnlyTheGeneralPageStayWithinTheCeiling()
    {
        var (catalog, _) = Shipped();
        var general = catalog.GeneralPageTypes(HelpCatalog.HoldableTypes(ItemAssemblies));

        Assert.True(general.Count <= GeneralPageCeiling, $"{general.Count} item types reach only the general page; the ceiling is {GeneralPageCeiling}.");
    }

    [Fact]
    public void EverydayItemsHaveATopicOfTheirOwn()
    {
        var (catalog, _) = Shipped();
        var byName = HelpCatalog.TypeLookup(ItemAssemblies);
        var problems = new List<string>();

        foreach (var name in EverydayItems)
        {
            var type = byName(name);

            if (type is null)
            {
                problems.Add($"{name}: not exactly one item type");
            }
            else if (catalog.TopicFor(type) is not { } topic || topic.Key == HelpCatalog.CatchAllKey)
            {
                problems.Add($"{name}: reaches only the general page");
            }
        }

        Assert.True(problems.Count == 0, string.Join(Environment.NewLine, problems));
    }

    // ---- validation catches mistakes

    private static HelpCatalog.Paragraph Text(string text, string? requires = null) => new(text, null, requires);

    private static List<string> Check(HelpCatalog catalog) => catalog.Validate(HelpCatalog.TypeLookup(ItemAssemblies), []);

    private static HelpCatalog.ItemTopic Topic(string key, string title = "Thing", int art = 3854, string[]? types = null, string[]? related = null, params HelpCatalog.Paragraph[] paragraphs) =>
        new(key, title, art, types ?? ["Bottle"], [], paragraphs.Length > 0 ? paragraphs : [Text("# What it is"), Text("A thing.")], [], related ?? []);

    [Fact]
    public void ABrokenLinkAMissingArtAnUnknownGateAndABannedNameAreAllReported()
    {
        var (shipped, _) = Shipped();
        var broken = new HelpCatalog
        {
            Categories = shipped.Categories,
            Skills = shipped.Skills,
            Items =
            [
                Topic("a", related: ["nowhere"]),
                Topic("b", art: 0),
                Topic("c", paragraphs: Text("hello", "noSuchFlag")),
                Topic("d", paragraphs: Text("Welcome to Britannia Renaissance")),
                Topic("e", types: ["NoSuchItemType"])
            ]
        };

        var errors = Check(broken);

        Assert.Contains(errors, static e => e.Contains("\"nowhere\"", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("needs an art number", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("not a feature flag", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("Britannia Renaissance", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("NoSuchItemType", StringComparison.Ordinal));
    }

    private static HelpCatalog.SkillPage Page(SkillName skill, params HelpCatalog.Paragraph[] paragraphs) => new(skill, paragraphs, []);

    private static HelpCatalog.Paragraph Generated(string name) => new(null, name, null);

    private static HelpCatalog.Paragraph Long() => Text(new string('x', 300));

    [Fact]
    public void ASkillPageNeedsTheStatsAndGainBlocksItsCraftTableAndRealLength()
    {
        var (shipped, _) = Shipped();
        var stub = new HelpCatalog { Categories = shipped.Categories, Items = shipped.Items, Skills = [Page(SkillName.Alchemy, Text("# One"), Text("short"))] };
        var errors = Check(stub);

        Assert.Contains(errors, static e => e.Contains("Alchemy", StringComparison.Ordinal) && e.Contains("\"stats\"", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("Alchemy", StringComparison.Ordinal) && e.Contains("\"gain\"", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("Alchemy", StringComparison.Ordinal) && e.Contains("craft:Alchemy", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("Alchemy", StringComparison.Ordinal) && e.Contains("stub", StringComparison.Ordinal));

        var good = new HelpCatalog
        {
            Categories = shipped.Categories,
            Items = shipped.Items,
            Skills = [Page(SkillName.Swords, Text("# One"), Text("# Two"), Text("# Three"), Long(), Long(), Long(), Generated("stats"), Generated("gain"))]
        };

        Assert.DoesNotContain(Check(good), static e => e.Contains("skill Swords", StringComparison.Ordinal));
    }

    [Fact]
    public void TwoTopicsClaimingTheSameTypeNameAreReported()
    {
        var (shipped, _) = Shipped();
        var twice = new HelpCatalog
        {
            Categories = shipped.Categories,
            Skills = shipped.Skills,
            Items = [.. shipped.Items, Topic("dup-a", types: ["Longsword"]), Topic("dup-b", types: ["Longsword"]), Topic("dup-c", types: ["Dagger"]), Topic("dup-d", types: ["Dagger"])]
        };

        var errors = Check(twice);

        Assert.Contains(errors, static e => e.Contains("\"Longsword\"", StringComparison.Ordinal) && e.Contains("more than one topic", StringComparison.Ordinal));
        Assert.Contains(errors, static e => e.Contains("\"Dagger\"", StringComparison.Ordinal) && e.Contains("more than one topic", StringComparison.Ordinal));
    }

    [Fact]
    public void TheGeneralPageMustExist()
    {
        var (shipped, _) = Shipped();
        var without = new HelpCatalog { Categories = shipped.Categories, Skills = shipped.Skills, Items = shipped.Items.Where(static i => i.Key != HelpCatalog.CatchAllKey).ToArray() };

        Assert.Contains(Check(without), static e => e.Contains("general item page", StringComparison.Ordinal));
    }

    [Fact]
    public void ASkillPageListsTheTopicsThatNameTheSkillAndNeverTheGeneralPage()
    {
        var (catalog, _) = Shipped();
        var keys = catalog.ItemsFor(SkillName.Alchemy).Select(static i => i.Key).ToList();

        Assert.Contains("potion-heal", keys);
        Assert.Contains("mortar-pestle", keys);
        Assert.DoesNotContain(HelpCatalog.CatchAllKey, keys);
        Assert.InRange(keys.Count, 1, HelpCatalog.MaxRelatedItems);
        Assert.Equal(keys.Distinct().Count(), keys.Count);
        Assert.Empty(catalog.ItemsFor(SkillName.RemoveTrap).Where(static i => i.Key == "potion-heal"));
    }

    [Fact]
    public void ATypeNameThatMatchesTwoItemTypesIsRefusedAsAmbiguous()
    {
        var byName = HelpCatalog.TypeLookup(ItemAssemblies);

        Assert.NotNull(byName("Bottle"));
        Assert.Null(byName("NoSuchItemType"));
    }

    [Fact]
    public void AGatedParagraphMustNameARealFeatureFlag()
    {
        Assert.Contains("SkillBank", HelpCatalog.GateNames);
        Assert.Contains("HelpGumps", HelpCatalog.GateNames);
        Assert.DoesNotContain("Nonsense", HelpCatalog.GateNames);
    }

    // ---- the generated blocks

    private static void WithUor(Action action)
    {
        var previous = Core.Expansion;

        try
        {
            Core.Expansion = Expansion.UOR;
            action();
        }
        finally
        {
            Core.Expansion = previous;
        }
    }

    [Fact]
    public void TheAlchemyTableListsTheEraPotionsWithTheirSkillRangeAndWhatTheyAreMadeFrom()
    {
        WithUor(() =>
        {
            DefAlchemy.Initialize();
            var paragraphs = HelpGenerators.Generate("craft:Alchemy");
            var text = string.Join("\n", paragraphs);

            Assert.NotEmpty(paragraphs);
            Assert.Contains("Lesser heal, skill -25 to 25", text);   // the game's own name, capitalised, and the range as the game has it
            Assert.Contains("from 3 ginseng", text.ToLowerInvariant());
            Assert.Contains("1 empty bottle", text);          // one of a plural material reads singular
            Assert.DoesNotContain("1 empty bottles", text);
            Assert.DoesNotContain("Conflagration", text);     // after the era
            Assert.DoesNotContain("Smoke Bomb", text);
        });
    }

    [Fact]
    public void TheRecipeTablesLeaveOutWhatTheEraCraftMenusNeverOffer()
    {
        WithUor(() =>
        {
            DefBlacksmithy.Initialize();
            DefTailoring.Initialize();
            DefTinkering.Initialize();

            var systems = new Dictionary<string, CraftSystem>
            {
                ["craft:Blacksmithing"] = DefBlacksmithy.CraftSystem,
                ["craft:Tailoring"] = DefTailoring.CraftSystem,
                ["craft:Tinkering"] = DefTinkering.CraftSystem
            };

            foreach (var (craft, names) in HelpGenerators.OffMenuRecipes)
            {
                var system = systems[craft];
                var text = string.Join("\n", HelpGenerators.Generate(craft));

                foreach (var name in names)
                {
                    // The name must still be a recipe of the craft (else the list is stale), and must not be in the table.
                    Assert.Contains(system.CraftItems, i => i.ItemType.Name == name);
                    Assert.DoesNotContain(HelpGenerators.Spaced(name) + ",", text);
                }
            }

            // Clock parts and sextant parts are listed twice by Tinkering; only the recipe made from ingots is on the menu.
            var tinkering = string.Join("\n", HelpGenerators.Generate("craft:Tinkering"));

            Assert.Equal(1, tinkering.Split("Clock Parts,").Length - 1);
            Assert.Equal(1, tinkering.Split("Sextant Parts,").Length - 1);
        });
    }

    [Fact]
    public void ThePageEstimateCountsALineBreakInsideAParagraphAsALine()
    {
        var plain = new WelcomeGuide.Topic("t", "T", ["a short line"]);
        var list = new WelcomeGuide.Topic("t", "T", ["one<BR>two<BR>three<BR>four"]);

        Assert.Equal(1, WelcomeGuide.EstimateLines(plain));
        Assert.Equal(4, WelcomeGuide.EstimateLines(list));
    }

    [Fact]
    public void TheGainBlockReadsTheShardRulesAndNamesTheClassTheCurveAndTheMasteryDays()
    {
        var text = string.Join(" ", HelpGenerators.GainText(SkillName.Alchemy, ShippedRules()));

        Assert.Contains("Alchemy is a Hard skill", text);
        Assert.Contains("1.5 times the usual rate", text);
        Assert.Contains("from 70 at the usual rate", text);
        Assert.Contains("from 80 at 7.5% of the usual rate", text);
        Assert.Contains("about 20 days", text);
        Assert.Contains("[SkillClasses", text);
        Assert.Contains("[Mastery", text);
    }

    [Theory]
    [InlineData(1, "Empty Bottles", "empty bottle")]
    [InlineData(3, "Empty Bottles", "empty bottles")]
    [InlineData(1, "Glass", "glass")]
    [InlineData(5, "Ginseng", "ginseng")]
    [InlineData(1, "Ginseng", "ginseng")]
    public void AMaterialNameIsSingularOnlyForExactlyOne(int amount, string name, string expected) => Assert.Equal(expected, HelpGenerators.ResourceName(amount, name));

    [Fact]
    public void TheStatsBlockNamesTheMainStatAndWhatTrainingRaises()
    {
        var text = string.Join(" ", HelpGenerators.StatsText(SkillName.Alchemy));

        Assert.Contains("Dexterity and Intelligence add to how well it works", text);
        Assert.Contains("10% of the gap", text);
        Assert.Contains("at 50.0 that is 5 extra", text);
        Assert.Contains("can also raise Dexterity and Intelligence", text);
    }

    [Fact]
    public void ASkillWithNoStatScaleOrGainSaysSoInsteadOfClaimingABonus()
    {
        var text = string.Join(" ", HelpGenerators.StatsText(SkillName.Peacemaking));

        Assert.Contains("Your stats do not change how well this skill works.", text);
        Assert.Contains("does not raise any stat", text);
        Assert.DoesNotContain("add to how well", text);
    }

    [Theory]
    [InlineData("alchemy", SkillName.Alchemy)]
    [InlineData("Animal Taming", SkillName.AnimalTaming)]
    [InlineData("taming", SkillName.AnimalTaming)]
    [InlineData("mace", SkillName.Macing)]
    [InlineData("eval", SkillName.EvalInt)]
    public void ATypedSkillNameFindsTheRightSkill(string typed, SkillName expected) => Assert.Equal(expected, HelpService.FindSkill(typed));

    [Theory]
    [InlineData("")]
    [InlineData("zzz")]
    [InlineData("a")]
    public void ANameThatMatchesNoSkillOrManyFindsNothing(string typed) => Assert.Null(HelpService.FindSkill(typed));
}
