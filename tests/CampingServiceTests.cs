using System.Text.Json;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CampingServiceTests
{
    private static readonly CampingRules Rules = new();

    private static List<string> Errors(CampingRules rules)
    {
        var errors = new List<string>();
        CampingService.Validate(rules, errors);
        return errors;
    }

    private static ShardRules Shipped()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- ignition

    [Theory]
    [InlineData(0.0, 0.5)]
    [InlineData(20.0, 0.5)]
    [InlineData(50.0, 0.5)]
    [InlineData(80.0, 0.8)]
    [InlineData(100.0, 1.0)]
    public void EveryoneLightsAtTheFloorAndSkillAboveItRaisesTheChance(double skill, double chance) =>
        Assert.Equal(chance, CampingService.IgniteChance(Rules, skill), 6);

    [Fact]
    public void AFloorOfZeroLeavesTheStockSkillPercent()
    {
        var stock = new CampingRules { SkillFloor = 0.0 };

        Assert.Equal(0.0, CampingService.IgniteChance(stock, 0.0));
        Assert.Equal(0.35, CampingService.IgniteChance(stock, 35.0), 6);
    }

    // ---- how long a fire lives

    [Fact]
    public void AFireLitAtSkillZeroBurnsAboutAsLongAsStockAndSmouldersAMinute()
    {
        var timing = CampingService.TimingFor(Rules, 0.0);

        Assert.Equal(100.0, timing.Out.TotalSeconds, 6);
        Assert.Equal(100.0 * 2.0 / 3.0, timing.Dim.TotalSeconds, 6);
        Assert.Equal(160.0, timing.Expire.TotalSeconds, 6);
    }

    [Fact]
    public void AFiftyPointCamperBurnsTwoHundredSecondsDimsForTheLastThirdAndSmouldersTwoMinutes()
    {
        var timing = CampingService.TimingFor(Rules, 50.0);

        Assert.Equal(200.0, timing.Out.TotalSeconds, 6);
        Assert.Equal(200.0 * 2.0 / 3.0, timing.Dim.TotalSeconds, 6);
        Assert.Equal(320.0, timing.Expire.TotalSeconds, 6);
    }

    [Fact]
    public void AGrandmasterFireBurnsFiveMinutesAndSmoulders180Seconds()
    {
        var timing = CampingService.TimingFor(Rules, 100.0);

        Assert.Equal(300.0, timing.Out.TotalSeconds, 6);
        Assert.Equal(200.0, timing.Dim.TotalSeconds, 6);
        Assert.Equal(480.0, timing.Expire.TotalSeconds, 6);
    }

    [Theory]
    [InlineData(0.0, 25.0)]
    [InlineData(25.0, 49.9)]
    public void TheIgnitionFloorDoesNotFlattenTheFireBelowIt(double lower, double higher) =>
        Assert.True(CampingService.TimingFor(Rules, higher).Expire > CampingService.TimingFor(Rules, lower).Expire);

    [Fact]
    public void SkillIsClampedToTheZeroToHundredScale()
    {
        Assert.Equal(CampingService.TimingFor(Rules, 0.0), CampingService.TimingFor(Rules, -5.0));
        Assert.Equal(CampingService.TimingFor(Rules, 100.0), CampingService.TimingFor(Rules, 130.0));
    }

    [Fact]
    public void MoreSkillAlwaysLengthensAFireAndEveryFireOutlastsTheStockOne()
    {
        var previous = TimeSpan.Zero;

        for (var skill = 0.0; skill <= 100.0; skill += 5.0)
        {
            var timing = CampingService.TimingFor(Rules, skill);

            Assert.True(timing.Expire > previous);
            Assert.True(timing.Dim < timing.Out && timing.Out < timing.Expire);
            Assert.True(timing.Out > CampfireTiming.Stock.Out && timing.Expire > CampfireTiming.Stock.Expire);
            previous = timing.Expire;
        }
    }

    [Fact]
    public void ASlowerSetOfNumbersScalesTheSameWay()
    {
        var quick = new CampingRules
        {
            LitBaseSeconds = 20.0,
            LitPerSkillSeconds = 0.3,
            EmberBaseSeconds = 15.0,
            EmberPerSkillSeconds = 0.2,
            DimShare = 0.5
        };

        var timing = CampingService.TimingFor(quick, 100.0);

        Assert.Equal(50.0, timing.Out.TotalSeconds, 6);
        Assert.Equal(25.0, timing.Dim.TotalSeconds, 6);
        Assert.Equal(85.0, timing.Expire.TotalSeconds, 6);
    }

    // ---- the starter kit

    [Theory]
    [InlineData(0, 0, true, 3)]    // a new character with no camping grant
    [InlineData(0, 2, true, 1)]    // a cook: stock Cooking gives two Kindling
    [InlineData(1, 5, false, 0)]   // a camper: stock Camping gives a Bedroll and five Kindling
    [InlineData(1, 7, false, 0)]   // a camper who is also a cook already has more than enough
    [InlineData(2, 3, false, 0)]
    public void TheKitTopsUpWhatStockGrantedInsteadOfDoubling(int bedrolls, int kindling, bool addBedroll, int addKindling)
    {
        var plan = CampingService.PlanKit(Rules, bedrolls, kindling);

        Assert.Equal(addBedroll, plan.AddBedroll);
        Assert.Equal(addKindling, plan.AddKindling);
    }

    // ---- configuration

    [Fact]
    public void TheDefaultsAreTheApprovedNumbers()
    {
        Assert.Equal(50.0, Rules.SkillFloor);
        Assert.Equal(100.0, Rules.LitBaseSeconds);
        Assert.Equal(2.0, Rules.LitPerSkillSeconds);
        Assert.Equal(60.0, Rules.EmberBaseSeconds);
        Assert.Equal(1.2, Rules.EmberPerSkillSeconds);
        Assert.Equal(3, Rules.StarterKindling);
        Assert.Equal(5.0, Rules.FeedCooldownSeconds);
        Assert.Empty(Errors(Rules));
    }

    [Theory]
    [InlineData("SkillFloor", -1.0)]
    [InlineData("SkillFloor", 101.0)]
    [InlineData("LitBaseSeconds", 1.0)]
    [InlineData("LitPerSkillSeconds", -0.1)]
    [InlineData("DimShare", 0.0)]
    [InlineData("DimShare", 1.0)]
    [InlineData("EmberBaseSeconds", -1.0)]
    [InlineData("EmberPerSkillSeconds", 31.0)]
    [InlineData("FeedCooldownSeconds", 61.0)]
    public void OutOfRangeNumbersAreRejected(string property, double value)
    {
        var rules = new CampingRules();
        typeof(CampingRules).GetProperty(property)!.SetValue(rules, value);

        Assert.Single(Errors(rules));
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(21)]
    public void AnAbsurdStarterKindlingIsRejected(int amount) =>
        Assert.Single(Errors(new CampingRules { StarterKindling = amount }));

    [Fact]
    public void TheShippedFileCarriesTheDefaultNumbersAndValidates()
    {
        var rules = Shipped();

        Assert.Equal(Rules.SkillFloor, rules.Camping.SkillFloor);
        Assert.Equal(Rules.LitBaseSeconds, rules.Camping.LitBaseSeconds);
        Assert.Equal(Rules.LitPerSkillSeconds, rules.Camping.LitPerSkillSeconds);
        Assert.Equal(Rules.DimShare, rules.Camping.DimShare, 6);
        Assert.Equal(Rules.EmberBaseSeconds, rules.Camping.EmberBaseSeconds);
        Assert.Equal(Rules.EmberPerSkillSeconds, rules.Camping.EmberPerSkillSeconds);
        Assert.Equal(Rules.FeedCooldownSeconds, rules.Camping.FeedCooldownSeconds);
        Assert.Equal(Rules.StarterKindling, rules.Camping.StarterKindling);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void TheFlagsAreListedWhenOn()
    {
        var flags = new DeferredFeatureFlags { CampingStarterKit = true, CampingFires = true };

        Assert.Contains("CampingStarterKit", flags.EnabledNames());
        Assert.Contains("CampingFires", flags.EnabledNames());
        Assert.DoesNotContain("none", flags.EnabledNames());
    }
}
