using System.Text.Json;
using Server;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class SkillGainCurveTests
{
    private static readonly string[] EasyNames =
    [
        "Anatomy", "AnimalLore", "Archery", "ArmsLore", "Begging", "Camping", "Cartography", "Cooking",
        "DetectHidden", "EvalInt", "Fishing", "Forensics", "Hiding", "ItemID", "Lumberjacking", "Mining",
        "SpiritSpeak", "TasteID", "Tracking"
    ];

    private static readonly string[] HardNames = ["Alchemy", "AnimalTaming", "Blacksmith", "Poisoning"];

    /// <summary>The approved class table, built independently of the shipped JSON so a drift fails a test.</summary>
    public static SkillGainRules ValidRules()
    {
        var rules = new SkillGainRules();
        rules.Classes["easy"] = [Band(0, 1.5)];
        rules.Classes["standard"] = [Band(0, 1.5), Band(70, 1.0)];
        rules.Classes["hard"] = [Band(0, 1.5), Band(70, 1.0), Band(80, 0.75)];
        rules.Classes["veryHard"] = [Band(0, 1.5), Band(70, 1.0), Band(80, 0.75)];

        for (var i = 0; i <= SkillGainCurveService.LastUorSkillId; i++)
        {
            var name = ((SkillName)i).ToString();
            rules.Skills[name] = EasyNames.Contains(name) ? "easy" : HardNames.Contains(name) ? "hard" : "standard";
        }

        return rules;
    }

    private static SkillGainBand Band(double from, double multiplier) => new() { From = from, Multiplier = multiplier };

    private static ShardRules Shipped()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    [Fact]
    public void ShippedConfigurationIsValidAndMatchesTheApprovedClassTable()
    {
        var rules = Shipped();

        Assert.Empty(ShardRulesConfiguration.Validate(rules));

        var approved = ValidRules();
        foreach (var (skill, className) in approved.Skills)
        {
            Assert.Equal(className, rules.SkillGain.Skills[skill]);
        }

        Assert.Equal(approved.Skills.Count, rules.SkillGain.Skills.Count);
        Assert.Equal(19, rules.SkillGain.Skills.Values.Count(v => v == "easy"));
        Assert.Equal(26, rules.SkillGain.Skills.Values.Count(v => v == "standard"));
        Assert.Equal(4, rules.SkillGain.Skills.Values.Count(v => v == "hard"));
        Assert.Equal(0, rules.SkillGain.Skills.Values.Count(v => v == "veryHard"));

        foreach (var (name, bands) in approved.Classes)
        {
            Assert.Equal(
                bands.Select(b => (b.From, b.Multiplier)),
                rules.SkillGain.Classes[name].Select(b => (b.From, b.Multiplier))
            );
        }
    }

    [Fact]
    public void FlagDefaultsOffAndIsListedWhenOn()
    {
        Assert.False(new DeferredFeatureFlags().SkillGainCurve);
        Assert.Contains(
            nameof(DeferredFeatureFlags.SkillGainCurve),
            new DeferredFeatureFlags { SkillGainCurve = true }.EnabledNames()
        );
    }

    [Theory]
    // Easy: 1.5x from 10 to 90 (where Mastery begins).
    [InlineData(SkillName.Archery, 10.0, 1.5)]
    [InlineData(SkillName.Archery, 69.9, 1.5)]
    [InlineData(SkillName.Archery, 70.0, 1.5)]
    [InlineData(SkillName.Archery, 89.9, 1.5)]
    // Standard: 1.5x to 70, then stock.
    [InlineData(SkillName.Swords, 10.0, 1.5)]
    [InlineData(SkillName.Swords, 69.9, 1.5)]
    [InlineData(SkillName.Swords, 70.0, 1.0)]
    [InlineData(SkillName.Swords, 89.9, 1.0)]
    // Hard: 1.5x to 70, stock 70 to 80, 0.75x from 80.
    [InlineData(SkillName.Blacksmith, 69.9, 1.5)]
    [InlineData(SkillName.Blacksmith, 70.0, 1.0)]
    [InlineData(SkillName.Blacksmith, 79.9, 1.0)]
    [InlineData(SkillName.Blacksmith, 80.0, 0.75)]
    [InlineData(SkillName.Blacksmith, 89.9, 0.75)]
    // Outside the curve range every skill is stock: below 10 gain is unconditional, 90+ is Mastery.
    [InlineData(SkillName.Archery, 9.9, 1.0)]
    [InlineData(SkillName.Swords, 0.0, 1.0)]
    [InlineData(SkillName.Blacksmith, 90.0, 1.0)]
    [InlineData(SkillName.Swords, 94.9, 1.0)]
    [InlineData(SkillName.Archery, 99.9, 1.0)]
    public void MultiplierFollowsTheClassBands(SkillName skill, double value, double expected)
    {
        Assert.Equal(expected, SkillGainCurveService.MultiplierFor(ValidRules(), skill, value));
    }

    [Fact]
    public void EveryUorSkillHasAClassAndTheFirstBandIsFaster()
    {
        var rules = ValidRules();

        for (var i = 0; i <= SkillGainCurveService.LastUorSkillId; i++)
        {
            Assert.NotNull(SkillGainCurveService.ClassOf(rules, (SkillName)i));
            Assert.Equal(1.5, SkillGainCurveService.MultiplierFor(rules, (SkillName)i, 10.0));
        }
    }

    [Fact]
    public void ASkillTheConfigurationDoesNotListIsStock()
    {
        var rules = ValidRules();
        rules.Skills.Remove("Swords");

        Assert.Equal(1.0, SkillGainCurveService.MultiplierFor(rules, SkillName.Swords, 40.0));
    }

    [Fact]
    public void CurveRangeEndsExactlyWhereMasteryBegins()
    {
        Assert.Equal(MasteryProgression.ThresholdFixedPoint / 10.0, SkillGainCurveService.MasteryThreshold);
    }

    [Fact]
    public void ValidationRejectsAnIncompleteOrMalformedTable()
    {
        var rules = ValidRules();
        rules.Skills.Remove("Magery");
        rules.Skills["Tactics"] = "legendary";
        rules.Skills["Imbuing"] = "easy";
        rules.Classes["hard"] = [Band(10, 1.0)];
        rules.Classes["standard"] = [Band(0, 1.5), Band(70, 0.0), Band(60, 1.0)];
        rules.Classes.Remove("veryHard");

        var errors = new List<string>();
        SkillGainCurveService.Validate(rules, errors);

        Assert.Contains(errors, e => e.Contains("must assign Magery", StringComparison.Ordinal));
        Assert.Contains(errors, e => e.Contains("unknown class 'legendary'", StringComparison.Ordinal));
        Assert.Contains(errors, e => e.Contains("'Imbuing' is not a UOR skill", StringComparison.Ordinal));
        Assert.Contains(errors, e => e.Contains("'hard' must start with a band from 0", StringComparison.Ordinal));
        Assert.Contains(errors, e => e.Contains("multipliers must be above 0", StringComparison.Ordinal));
        Assert.Contains(errors, e => e.Contains("bands must ascend", StringComparison.Ordinal));
        Assert.Contains(errors, e => e.Contains("must define 'veryHard'", StringComparison.Ordinal));
    }

    [Fact]
    public void ValidationAcceptsTheApprovedTable()
    {
        var errors = new List<string>();
        SkillGainCurveService.Validate(ValidRules(), errors);

        Assert.Empty(errors);
    }

    [Fact]
    public void DescribeReportsTheBandsPlayersSee()
    {
        var rules = ValidRules();

        Assert.Equal("Easy: 1.5x from 10 to 90", SkillGainCurveService.Describe("easy", rules.Classes["easy"]));
        Assert.Equal(
            "Hard: 1.5x from 10 to 70, 1x from 70 to 80, 0.75x from 80 to 90",
            SkillGainCurveService.Describe("hard", rules.Classes["hard"])
        );
    }
}
