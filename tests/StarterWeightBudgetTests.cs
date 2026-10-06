using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class StarterWeightBudgetTests
{
    private static readonly StarterWeightRules Rules = new();
    private const int Body = 11;

    private static StarterWeightBudget.Stack S(double unit, int amount) => new(unit, amount);

    private static List<string> Errors(StarterWeightRules rules)
    {
        var errors = new List<string>();
        StarterWeightBudget.Validate(rules, errors);
        return errors;
    }

    private static ShardRules Shipped()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- within budget, or switched off: nothing moves

    [Fact]
    public void ALoadWithinTheBudgetIsLeftAlone()
    {
        // STR 54 limit 229, 85% is 194; a Blacksmith's 450 ingots at 0.1 each and 110 carried is far inside it.
        var plan = StarterWeightBudget.Plan(Rules, 229, Body, 110.0, [S(0.1, 450)]);

        Assert.Equal([450], plan);
    }

    [Fact]
    public void ALoadExactlyAtTheBudgetIsLeftAlone()
    {
        // 187 x 0.85 = 158.95, so the budget is 158; body 11 plus 147 carried is exactly it.
        var plan = StarterWeightBudget.Plan(Rules, 187, Body, 147.0, [S(1.0, 75)]);

        Assert.Equal([75], plan);
    }

    [Fact]
    public void TurningTheBudgetOffRestoresTheListedQuantities()
    {
        var off = new StarterWeightRules { Enabled = false };

        Assert.Equal([200, 100], StarterWeightBudget.Plan(off, 229, Body, 295.0, [S(1.0, 200), S(0.1, 100)]));
    }

    [Fact]
    public void NoBulkSuppliesMeansNothingToTrim()
    {
        Assert.Empty(StarterWeightBudget.Plan(Rules, 187, Body, 400.0, []));
        Assert.Equal([0], StarterWeightBudget.Plan(Rules, 187, Body, 400.0, [S(1.0, 0)]));
    }

    // ---- the measured cases

    [Fact]
    public void AnArcherKeepsAboutNinetyBoardsAndFortySixFeathers()
    {
        // Archer template: STR 54, limit 229, carried 295 (200 Boards at 1, 100 Feathers at 0.1).
        var plan = StarterWeightBudget.Plan(Rules, 229, Body, 295.0, [S(1.0, 200), S(0.1, 100)]);

        Assert.Equal([93, 46], plan);
    }

    [Fact]
    public void ACarpenterKeepsAboutOneHundredTwentyBoards()
    {
        // Carpenter template: carried 332 with 264 Boards and 100 Feathers.
        var plan = StarterWeightBudget.Plan(Rules, 229, Body, 332.0, [S(1.0, 264), S(0.1, 100)]);

        Assert.Equal([120, 45], plan);
    }

    [Fact]
    public void AlchemyWithCookingKeepsRoughlyHalfAndEveryStackKeepsItsFloor()
    {
        // Advanced Alchemy + Cooking at STR 42 (limit 187): carried 236 with 75 Bottles, 8 reagent stacks of 50,
        // 20 lamb legs (2 each), 20 chicken legs and 20 fish steaks (0.1 each).
        var stacks = new List<StarterWeightBudget.Stack> { S(1.0, 75) };
        for (var i = 0; i < 8; i++)
        {
            stacks.Add(S(0.1, 50));
        }

        stacks.AddRange([S(2.0, 20), S(1.0, 20), S(0.1, 20)]);

        var plan = StarterWeightBudget.Plan(Rules, 187, Body, 236.0, stacks);

        Assert.Equal(33, plan[0]);                                  // Bottles
        Assert.All(plan.Skip(1).Take(8), amount => Assert.Equal(22, amount));
        Assert.Equal([10, 10, 10], plan.Skip(9).ToArray());         // meats held at the floor of 10
    }

    [Fact]
    public void ReagentStacksAreWeighedRoundedUpSoTheLoadReallyFits()
    {
        // 21 reagents at 0.1 stones weigh 3 in the engine, not 2.1. With the kit's extra 10 stones, Advanced Alchemy + Cooking
        // is at carried 246; a plain proportional cut ends 8 stones above its budget, the rounding-aware plan does not.
        var stacks = new List<StarterWeightBudget.Stack> { S(1.0, 75) };
        for (var i = 0; i < 8; i++)
        {
            stacks.Add(S(0.1, 50));
        }

        stacks.AddRange([S(2.0, 20), S(1.0, 20), S(0.1, 20)]);

        var plan = StarterWeightBudget.Plan(Rules, 187, Body, 246.0, stacks);

        double Ceil(double unit, int amount) => Math.Ceiling(unit * amount - 1e-9);
        var before = stacks.Sum(s => Ceil(s.UnitWeight, s.Amount));
        var after = stacks.Select((s, i) => Ceil(s.UnitWeight, plan[i])).Sum();
        var load = Body + 246.0 - (before - after);

        Assert.True(load <= 158.0, $"load {load} should be within the 158 budget");
        Assert.Equal([10, 10, 10], plan.Skip(9).ToArray());
    }

    // ---- invariants

    [Theory]
    [InlineData(229, 295.0)]
    [InlineData(187, 316.0)]
    [InlineData(187, 275.0)]
    public void NoStackGrowsAndTheLoadEndsWithinTheBudgetWhenTheFloorsAllowIt(int max, double carried)
    {
        var stacks = new List<StarterWeightBudget.Stack> { S(1.0, 250), S(0.1, 100) };
        var plan = StarterWeightBudget.Plan(Rules, max, Body, carried, stacks);

        for (var i = 0; i < plan.Length; i++)
        {
            Assert.InRange(plan[i], 0, stacks[i].Amount);
        }

        // the engine rounds each stack's weight up, so weigh them that way
        double Ceil(double unit, int amount) => Math.Ceiling(unit * amount - 1e-9);
        var removed = stacks.Select((s, i) => Ceil(s.UnitWeight, s.Amount) - Ceil(s.UnitWeight, plan[i])).Sum();
        var budget = Math.Floor(max * 0.85);

        Assert.True(Body + carried - removed <= budget + 0.0001, $"{Body + carried - removed} should fit {budget}");
    }

    [Fact]
    public void AStackSmallerThanTheFloorKeepsAllOfItself()
    {
        var plan = StarterWeightBudget.Plan(Rules, 187, Body, 300.0, [S(1.0, 5), S(1.0, 200)]);

        Assert.Equal(5, plan[0]);
        Assert.True(plan[1] < 200);
    }

    [Fact]
    public void IfTheFloorsAloneKeepTheLoadOverBudgetTheyStillHold()
    {
        // Almost all of the weight is something else, so the supplies shrink to their floors and the load stays over.
        var plan = StarterWeightBudget.Plan(Rules, 187, Body, 400.0, [S(1.0, 100), S(1.0, 100)]);

        Assert.Equal([10, 10], plan);
    }

    [Fact]
    public void AHigherBudgetPercentTrimsLess()
    {
        var loose = new StarterWeightRules { MaxLoadPercent = 100 };
        var archerLoose = StarterWeightBudget.Plan(loose, 229, Body, 295.0, [S(1.0, 200), S(0.1, 100)]);
        var archerDefault = StarterWeightBudget.Plan(Rules, 229, Body, 295.0, [S(1.0, 200), S(0.1, 100)]);

        Assert.True(archerLoose[0] > archerDefault[0]);
    }

    // ---- configuration

    [Fact]
    public void TheDefaultsAreTheApprovedBudget()
    {
        Assert.True(Rules.Enabled);
        Assert.Equal(85, Rules.MaxLoadPercent);
        Assert.Equal(10, Rules.MinimumUnits);
        Assert.Empty(Errors(Rules));
    }

    [Theory]
    [InlineData(19)]
    [InlineData(101)]
    public void AnAbsurdLoadPercentIsRejected(int percent) =>
        Assert.Single(Errors(new StarterWeightRules { MaxLoadPercent = percent }));

    [Theory]
    [InlineData(-1)]
    [InlineData(51)]
    public void AnAbsurdFloorIsRejected(int units) =>
        Assert.Single(Errors(new StarterWeightRules { MinimumUnits = units }));

    [Fact]
    public void TheShippedFileCarriesTheApprovedBudgetAndValidates()
    {
        var rules = Shipped();

        Assert.True(rules.StarterWeight.Enabled);
        Assert.Equal(85, rules.StarterWeight.MaxLoadPercent);
        Assert.Equal(10, rules.StarterWeight.MinimumUnits);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }
}
