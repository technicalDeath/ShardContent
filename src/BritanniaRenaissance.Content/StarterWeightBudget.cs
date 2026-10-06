using Server;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Keeps a new character able to move. The Alpha 3 Phase H supplies (boards, bottles, reagents, raw meat and the like) were
/// chosen as practice quantities without a weight check, and several starts (the Archer and Carpenter templates, Advanced
/// Carpentry, Fletching, Alchemy with Cooking) began far over their carry limit, where every step drains stamina and
/// movement stops at zero. After every starter issuer has run, a character whose load is above a share of its limit has its
/// bulk supply stacks scaled down together until it fits (docs/Starter-Weight-Budget.md). Nothing else is touched, a
/// character already within the budget is untouched, and no stack grows or disappears.
/// </summary>
public static class StarterWeightBudget
{
    /// <summary>One bulk stack: what one unit weighs and how many there are.</summary>
    public readonly record struct Stack(double UnitWeight, int Amount);

    private static readonly Type[] BulkTypes =
    [
        typeof(Board), typeof(Bottle), typeof(BlankScroll), typeof(RawLambLeg), typeof(RawChickenLeg),
        typeof(RawFishSteak), typeof(Cloth), typeof(Leather), typeof(Feather), typeof(IronIngot), typeof(BaseReagent)
    ];

    private static bool _configured;

    private static StarterWeightRules Rules => ShardRulesConfiguration.Settings?.StarterWeight ?? new StarterWeightRules();

    /// <summary>Named Register, not Configure, so ModernUO's own Configure discovery cannot run it before the issuers.</summary>
    public static void Register()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Apply;
    }

    // ---- the planner, free of game objects so it can be tested directly

    /// <summary>
    /// The amounts the stacks should hold. Unchanged when the budget is off or the load is within it; otherwise one factor
    /// scales every stack, and each keeps at least <c>minimumUnits</c> (or what it had, if less).
    /// </summary>
    public static int[] Plan(StarterWeightRules rules, int maxWeight, int bodyWeight, double carried, IReadOnlyList<Stack> stacks)
    {
        var amounts = new int[stacks.Count];

        for (var i = 0; i < stacks.Count; i++)
        {
            amounts[i] = stacks[i].Amount;
        }

        var budget = Math.Floor(maxWeight * rules.MaxLoadPercent / 100.0);
        var over = bodyWeight + carried - budget;
        var bulk = 0.0;

        foreach (var stack in stacks)
        {
            bulk += stack.UnitWeight * stack.Amount;
        }

        if (!rules.Enabled || over <= 0.0 || bulk <= 0.0)
        {
            return amounts;
        }

        var factor = Math.Clamp(1.0 - over / bulk, 0.0, 1.0);

        for (var i = 0; i < stacks.Count; i++)
        {
            var floor = Math.Min(stacks[i].Amount, rules.MinimumUnits);
            amounts[i] = Math.Max(floor, (int)Math.Floor(stacks[i].Amount * factor));
        }

        return amounts;
    }

    public static void Validate(StarterWeightRules rules, List<string> errors)
    {
        if (rules.MaxLoadPercent is < 20 or > 100)
        {
            errors.Add($"starterWeight.maxLoadPercent must be between 20 and 100, but was {rules.MaxLoadPercent}.");
        }

        if (rules.MinimumUnits is < 0 or > 50)
        {
            errors.Add($"starterWeight.minimumUnits must be between 0 and 50, but was {rules.MinimumUnits}.");
        }
    }

    // ---- in the game

    public static void Apply(CharacterCreatedEventArgs args)
    {
        var rules = Rules;

        if (!rules.Enabled || args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player)
        {
            return;
        }

        var items = new List<Item>();
        Collect(player.Backpack, items);

        var stacks = new List<Stack>(items.Count);

        foreach (var item in items)
        {
            stacks.Add(new Stack(item.Weight, item.Amount));
        }

        var before = Mobile.BodyWeight + player.TotalWeight;
        var amounts = Plan(rules, player.MaxWeight, Mobile.BodyWeight, player.TotalWeight, stacks);
        var trimmed = 0;

        for (var i = 0; i < items.Count; i++)
        {
            if (amounts[i] < items[i].Amount)
            {
                items[i].Amount = amounts[i];
                trimmed++;
            }
        }

        if (trimmed > 0)
        {
            ShardAuditLog.Record(
                "starter",
                "weight-budget",
                player,
                details: $"{trimmed} supply stack(s) trimmed; load {before} -> {Mobile.BodyWeight + player.TotalWeight} of limit {player.MaxWeight}"
            );
        }
    }

    private static void Collect(Container container, List<Item> items)
    {
        foreach (var item in container.Items)
        {
            if (item is Container child)
            {
                Collect(child, items);
            }
            else if (item.Stackable && IsBulk(item))
            {
                items.Add(item);
            }
        }
    }

    private static bool IsBulk(Item item)
    {
        foreach (var type in BulkTypes)
        {
            if (type.IsInstanceOfType(item))
            {
                return true;
            }
        }

        return false;
    }
}
