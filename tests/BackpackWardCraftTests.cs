using System.Text.Json;
using Server;
using Server.Engines.Craft;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class BackpackWardCraftTests
{
    private static WardCraftRules Rules(double min = 45.0, double max = 95.0, int ingots = 20) =>
        new() { Enabled = true, MinSkill = min, MaxSkill = max, Ingots = ingots };

    private static List<string> Errors(WardCraftRules rules)
    {
        var errors = new List<string>();
        BackpackWardCraft.Validate(rules, errors);
        return errors;
    }

    private static ShardRules Shipped()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- configuration

    [Fact]
    public void TheDefaultsAreTheApprovedLockpickTierRecipe()
    {
        var defaults = new WardCraftRules();

        Assert.True(defaults.Enabled);
        Assert.Equal(45.0, defaults.MinSkill);
        Assert.Equal(95.0, defaults.MaxSkill);
        Assert.Equal(20, defaults.Ingots);
        Assert.Empty(Errors(defaults));
    }

    [Fact]
    public void TheShippedFileCarriesTheApprovedRecipeAndIsValid()
    {
        var rules = Shipped();

        Assert.True(rules.WardCraft.Enabled);
        Assert.Equal(45.0, rules.WardCraft.MinSkill);
        Assert.Equal(95.0, rules.WardCraft.MaxSkill);
        Assert.Equal(20, rules.WardCraft.Ingots);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Theory]
    [InlineData(0.0, 50.0, 1)]
    [InlineData(45.0, 120.0, 200)]
    [InlineData(0.0, 0.1, 20)]
    public void TheSkillRangeAndIngotLimitsAreInclusive(double min, double max, int ingots)
    {
        Assert.Empty(Errors(Rules(min, max, ingots)));
    }

    [Theory]
    [InlineData(-1.0, 95.0, 20)]
    [InlineData(95.0, 95.0, 20)]
    [InlineData(96.0, 95.0, 20)]
    [InlineData(45.0, 120.1, 20)]
    public void ABadSkillRangeIsRejected(double min, double max, int ingots)
    {
        var error = Assert.Single(Errors(Rules(min, max, ingots)));

        Assert.Contains("wardCraft", error);
        Assert.Contains("minSkill", error);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(201)]
    public void ABadIngotCountIsRejectedByName(int ingots)
    {
        var error = Assert.Single(Errors(Rules(ingots: ingots)));

        Assert.Contains("wardCraft.ingots", error);
    }

    [Fact]
    public void TheShardRulesValidatorRunsTheWardCraftChecks()
    {
        var rules = Shipped();
        rules.WardCraft.Ingots = 0;

        Assert.Contains(ShardRulesConfiguration.Validate(rules), e => e.Contains("wardCraft.ingots"));
    }

    // ---- the recipe, added to a real Tinkering-shaped craft system

    private sealed class TestTinkering : CraftSystem
    {
        public TestTinkering() : base(1, 1, 1.25)
        {
        }

        public override SkillName MainSkill => SkillName.Tinkering;

        public override double GetChanceAtMin(CraftItem item) => 0.0;

        public override void InitCraftList()
        {
        }

        public override void PlayCraftEffect(Mobile from)
        {
        }

        public override int PlayEndingEffect(
            Mobile from, bool failed, bool lostMaterial, bool toolBroken, int quality, bool makersMark, CraftItem item
        ) => 0;

        public override int CanCraft(Mobile from, BaseTool tool, Type itemType) => 0;
    }

    [Fact]
    public void TheRecipeMakesAWardFromIronIngotsAcrossTheConfiguredSkillRange()
    {
        var system = new TestTinkering();

        var index = BackpackWardCraft.AddRecipe(system, Rules(min: 40.0, max: 90.0, ingots: 24));
        var item = system.CraftItems[index];

        Assert.Equal(typeof(BackpackWard), item.ItemType);
        var resource = Assert.Single(item.Resources);
        Assert.Equal(typeof(IronIngot), resource.ItemType);
        Assert.Equal(24, resource.Amount);
        var skill = Assert.Single(item.Skills);
        Assert.Equal(40.0, skill.MinSkill);
        Assert.Equal(90.0, skill.MaxSkill);
    }

    [Fact]
    public void TheRecipeSitsInTheSameGroupAsKeyLanternAndScales()
    {
        var system = new TestTinkering();

        var index = BackpackWardCraft.AddRecipe(system, Rules());

        Assert.Equal(1044050, system.CraftItems[index].GroupNameNumber);
        Assert.Single(system.CraftGroups);
        Assert.Single(system.CraftGroups[0].CraftItems);
    }

    [Fact]
    public void TheRecipeOffersNoExceptionalOrMakersMarkBecauseAWardHasNoQualityGrades()
    {
        var system = new TestTinkering();

        var index = BackpackWardCraft.AddRecipe(system, Rules());

        Assert.True(system.CraftItems[index].ForceNonExceptional);
    }

    [Fact]
    public void ConfigureRegistersTheServerStartHookExactlyOnce()
    {
        BackpackWardCraft.Configure();
        BackpackWardCraft.Configure();

        Assert.Equal(1, HandlersFrom());
    }

    private static int HandlersFrom()
    {
        var field = typeof(EventSink).GetField("ServerStarted", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic);
        var handler = (Delegate?)field?.GetValue(null);

        return handler?.GetInvocationList().Count(static d => d.Method.DeclaringType == typeof(BackpackWardCraft)) ?? 0;
    }
}
