using System.Text.RegularExpressions;
using Server;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class ShardProfessionsTests
{
    private sealed class Block
    {
        public string Name = "";
        public string TrueName = "";
        public string Type = "";
        public bool TopLevel;
        public int Id;
        public int Gump;
        public string? DescText;
        public List<string> Children = [];
        public List<(string Skill, int Value)> Skills = [];
        public List<(string Stat, int Value)> Stats = [];
        public List<string> Keys = [];
    }

    /// <summary>Names the file uses for skills whose profession name differs from the SkillName enum.</summary>
    private static readonly Dictionary<string, SkillName> Aliases = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Swordsmanship"] = SkillName.Swords,
        ["Parrying"] = SkillName.Parry,
        ["MaceFighting"] = SkillName.Macing,
        ["Evaluate Intelligence"] = SkillName.EvalInt,
        ["ResistingSpells"] = SkillName.MagicResist,
        ["Bowcraft"] = SkillName.Fletching,
        ["Inscription"] = SkillName.Inscribe
    };

    private static List<Block> Load()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "professions", "Prof.txt");
        var blocks = new List<Block>();
        Block? current = null;

        foreach (var raw in File.ReadAllLines(path))
        {
            var line = raw.Trim();
            if (line.Length == 0 || line.StartsWith('#'))
            {
                continue;
            }

            if (line.Equals("Begin", StringComparison.OrdinalIgnoreCase))
            {
                current = new Block();
                continue;
            }

            if (line.Equals("End", StringComparison.OrdinalIgnoreCase))
            {
                blocks.Add(current!);
                current = null;
                continue;
            }

            Assert.NotNull(current);

            // The server's parser splits on tabs only, so every field must be tab-separated.
            var cols = raw.Split('\t', StringSplitOptions.RemoveEmptyEntries);
            Assert.True(cols.Length >= 2, $"not tab-separated: {line}");
            var key = cols[0].Trim().ToLowerInvariant();
            var value = cols[1].Trim().Trim('"');
            current!.Keys.Add(key);

            switch (key)
            {
                case "name": current.Name = value; break;
                case "truename": current.TrueName = value; break;
                case "type": current.Type = value; break;
                case "toplevel": current.TopLevel = value.Equals("true", StringComparison.OrdinalIgnoreCase); break;
                case "desc": current.Id = int.Parse(value); break;
                case "gump": current.Gump = int.Parse(value); break;
                case "desctext": current.DescText = value; break;
                case "children":
                    current.Children = Regex.Matches(cols[1], "\"([^\"]+)\"").Select(m => m.Groups[1].Value).ToList();
                    break;
                case "skill": current.Skills.Add((value, int.Parse(cols[2].Trim()))); break;
                case "stat": current.Stats.Add((value, int.Parse(cols[2].Trim()))); break;
            }
        }

        return blocks;
    }

    private static List<Block> Professions() => Load().Where(b => b.Type == "Profession").ToList();

    private static List<Block> Folders() => Load().Where(b => b.Type == "Category").ToList();

    private static SkillName Resolve(string skill) =>
        Aliases.TryGetValue(skill, out var aliased) ? aliased : Enum.Parse<SkillName>(skill, true);

    /// <summary>The era profession values (UO Second Age forum reconstruction of the August 1999 Prof.txt), with the era's 100 skill points scaled proportionally to 120 and no skill above 50.</summary>
    private static readonly Dictionary<string, ((string Skill, int Value)[] Skills, int[] Stats)> Expected = new()
    {
        ["Archer"] = ([("Archery", 50), ("Bowcraft", 35), ("Lumberjacking", 35)], [50, 15, 15]),
        ["Bard"] = ([("Musicianship", 50), ("Provocation", 50), ("Archery", 20)], [50, 15, 15]),
        ["Ranger"] = ([("Archery", 50), ("Tracking", 35), ("AnimalTaming", 35)], [50, 15, 15]),
        ["Pure Mage"] = ([("Magery", 50), ("Evaluate Intelligence", 35), ("ResistingSpells", 35)], [40, 15, 25]),
        ["Warlock"] = ([("Swordsmanship", 48), ("Magery", 48), ("ResistingSpells", 24)], [40, 15, 25]),
        ["Mace Fighter"] = ([("MaceFighting", 50), ("Parrying", 35), ("Anatomy", 35)], [50, 15, 15]),
        ["Fencer"] = ([("Fencing", 50), ("Parrying", 35), ("Anatomy", 35)], [50, 15, 15]),
        ["Swordsman"] = ([("Swordsmanship", 50), ("Parrying", 35), ("Anatomy", 35)], [50, 15, 15]),
        ["Blacksmith"] = ([("Blacksmith", 50), ("Mining", 50), ("Tinkering", 20)], [50, 15, 15]),
        ["Carpenter"] = ([("Carpentry", 50), ("Lumberjacking", 50), ("Bowcraft", 20)], [50, 15, 15]),
        ["Tailor"] = ([("Tailoring", 50), ("Tracking", 50), ("Healing", 20)], [50, 15, 15]),
        ["Tinker"] = ([("Tinkering", 50), ("Mining", 35), ("Lumberjacking", 35)], [50, 15, 15]),
        ["Animal Tamer"] = ([("AnimalTaming", 50), ("Tracking", 35), ("AnimalLore", 35)], [50, 15, 15]),
        ["Fisherman"] = ([("Fishing", 50), ("Cooking", 50), ("Camping", 20)], [50, 15, 15]),
        ["Prospector"] = ([("Mining", 48), ("Lumberjacking", 48), ("Hiding", 24)], [55, 15, 10]),
        ["Sorcerer"] = ([("Alchemy", 42), ("Inscription", 42), ("Magery", 36)], [40, 15, 25])
    };

    [Fact]
    public void TheFileDefinesExactlyTheApprovedProfessionsAtIdsEightToTwentyThree()
    {
        var professions = Professions();

        Assert.Equal(ShardProfessions.TemplateIds, professions.Select(p => p.Id).Order());
        Assert.Equal(ShardProfessions.Names, professions.OrderBy(p => p.Id).Select(p => p.TrueName));
        Assert.Empty(professions.Select(p => p.Id).Intersect(ShardProfessions.UndefinedIds));
    }

    [Fact]
    public void FieldMedicAndBattleMageAreLeftOutByTheOwnersDecision()
    {
        var names = Load().Select(b => b.TrueName).ToList();

        Assert.DoesNotContain("Field Medic", names);
        Assert.DoesNotContain("Battle Mage", names);
        Assert.Equal(16, Professions().Count);
    }

    [Fact]
    public void EveryProfessionHasTheEraSkillsAndStats()
    {
        foreach (var profession in Professions())
        {
            var (skills, stats) = Expected[profession.TrueName];
            Assert.Equal(skills, profession.Skills.ToArray());
            Assert.Equal(stats, profession.Stats.Select(s => s.Value).ToArray());
        }
    }

    [Fact]
    public void EveryProfessionIsThreeUorSkillsTotallingOneHundredAndTwentyPointsAndEightyStatPoints()
    {
        foreach (var profession in Professions())
        {
            Assert.Equal(3, profession.Skills.Count);
            Assert.Equal(120, profession.Skills.Sum(s => s.Value));
            Assert.All(profession.Skills, s => Assert.InRange(s.Value, 1, 50));
            Assert.Equal(80, profession.Stats.Sum(s => s.Value));

            var resolved = profession.Skills.Select(s => Resolve(s.Skill)).ToList();
            Assert.Equal(3, resolved.Distinct().Count());
            Assert.All(resolved, s => Assert.True((int)s <= SkillGainCurveService.LastUorSkillId, $"{profession.Name}: {s}"));
        }
    }

    [Fact]
    public void TheTreeIsAdventurerAndMerchantFoldersWithTheEraSubFolders()
    {
        var folders = Folders().ToDictionary(f => f.TrueName);
        var topLevel = folders.Values.Where(f => f.TopLevel).Select(f => f.TrueName).Order().ToList();

        Assert.Equal(["Adventurer", "Merchant"], topLevel);
        Assert.Equal(["ArcherCategory", "MagicianCategory", "WarriorCategory"], folders["Adventurer"].Children);
        Assert.Equal(["CraftsmanCategory", "TradesmanCategory"], folders["Merchant"].Children);
        Assert.Equal(["Archer", "Bard", "Ranger"], folders["ArcherCategory"].Children);
        Assert.Equal(["Pure Mage", "Warlock"], folders["MagicianCategory"].Children);
        Assert.Equal(["Mace Fighter", "Fencer", "Swordsman"], folders["WarriorCategory"].Children);
        Assert.Equal(["Blacksmith", "Carpenter", "Tailor", "Tinker"], folders["CraftsmanCategory"].Children);
        Assert.Equal(["Animal Tamer", "Fisherman", "Prospector", "Sorcerer"], folders["TradesmanCategory"].Children);
    }

    [Fact]
    public void EveryProfessionIsReachableThroughExactlyOneFolderAndParentsComeFirst()
    {
        var blocks = Load();
        var order = blocks.Select((b, i) => (b.TrueName, i)).ToDictionary(x => x.TrueName, x => x.i);
        var reached = new List<string>();

        foreach (var folder in Folders())
        {
            foreach (var child in folder.Children)
            {
                Assert.True(order.ContainsKey(child), $"{folder.TrueName} lists unknown {child}");
                // The client attaches a child to a folder defined earlier in the file.
                Assert.True(order[folder.TrueName] < order[child], $"{child} comes before its folder {folder.TrueName}");
                reached.Add(child);
            }
        }

        Assert.Equal(
            Professions().Select(p => p.TrueName).Order(),
            reached.Where(n => Professions().Any(p => p.TrueName == n)).Order()
        );
        Assert.Equal(reached.Count, reached.Distinct().Count());
    }

    [Fact]
    public void FoldersAreInvisibleToTheServerParser()
    {
        // The server stops reading a block at a Type that is not Profession, so a folder's Type must come before any
        // key (such as Desc) that would otherwise register an ID.
        foreach (var folder in Folders())
        {
            Assert.DoesNotContain("desc", folder.Keys);
            Assert.True(folder.Keys.IndexOf("type") < folder.Keys.IndexOf("children"), folder.TrueName);
        }
    }

    [Fact]
    public void EveryCardCarriesTheTextAndArtTheClientShows()
    {
        foreach (var block in Load())
        {
            Assert.False(string.IsNullOrWhiteSpace(block.DescText), block.TrueName);
            Assert.True(block.Gump > 0, block.TrueName);
            Assert.False(string.IsNullOrWhiteSpace(block.Name), block.TrueName);
        }
    }

    [Fact]
    public void EveryTemplateSpreadsOneHundredAndTwentyPointsWithAThirtyMinimum()
    {
        foreach (var profession in Professions())
        {
            var source = profession.Stats.Select(s => (byte)s.Value).ToArray();
            var stats = Alpha3StartingStats.Allocate(profession.TrueName, source);

            Assert.Equal(120, stats.Strength + stats.Dexterity + stats.Intelligence);
            Assert.All([stats.Strength, stats.Dexterity, stats.Intelligence], s => Assert.InRange(s, 30, 60));
        }
    }

    [Theory]
    [InlineData("Archer", 50, 15, 15, 54, 33, 33)]
    [InlineData("Pure Mage", 40, 15, 25, 48, 33, 39)]
    [InlineData("Prospector", 55, 15, 10, 57, 33, 30)]
    public void AnEraTemplateKeepsItsOwnProportions(
        string name, byte str, byte dex, byte intel, int expectedStr, int expectedDex, int expectedInt
    )
    {
        Assert.Equal((expectedStr, expectedDex, expectedInt), Alpha3StartingStats.Allocate(name, [str, dex, intel]));
    }
}
