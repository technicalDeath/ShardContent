using Server;
using Server.Engines.Craft;
using Server.Engines.Craft.T2A;
using Server.Items;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A Tinkering recipe for the Backpack Ward (docs/BACKPACK-WARD-DESIGN.md Section 1), so crafters can undercut the 2,000 gp
/// vendor price. Once the server has started it adds the recipe through stock Tinkering's public <c>AddCraft</c> (the menu
/// the later eras use) and lists the Ward in the Miscellaneous list of the legacy item-list menu this era shows, whose
/// categories are fixed type lists. It sits with Key, Lantern and Scales and costs iron ingots only. A Ward has no quality
/// grades, so the recipe offers no exceptional or maker's mark. The ingot count sets the market's price floor (NPCs sell
/// iron ingots for 5 gp); the vendor's buy-back price sits a little above it. Follows the theft protection flag and
/// <c>wardCraft</c> in shard-rules.json.
/// </summary>
public static class BackpackWardCraft
{
    public const int MaxIngots = 200;
    public const double MaxSkill = 120.0;

    /// <summary>The stock Tinkering group Key, Lantern and Scales are in.</summary>
    private const int UtilityGroup = 1044050;

    private const int IronIngotLabel = 1044036;
    private const int NotEnoughIngots = 1044037;

    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        EventSink.ServerStarted += OnServerStarted;
    }

    public static void Validate(WardCraftRules rules, List<string> errors)
    {
        if (rules.MinSkill < 0.0 || rules.MinSkill >= rules.MaxSkill || rules.MaxSkill > MaxSkill)
        {
            errors.Add(
                $"wardCraft needs 0 <= minSkill < maxSkill <= {MaxSkill}, but minSkill was {rules.MinSkill} and maxSkill {rules.MaxSkill}."
            );
        }

        if (rules.Ingots < 1 || rules.Ingots > MaxIngots)
        {
            errors.Add($"wardCraft.ingots must be between 1 and {MaxIngots}, but was {rules.Ingots}.");
        }
    }

    /// <summary>Adds the recipe to a Tinkering menu and returns its index.</summary>
    public static int AddRecipe(CraftSystem system, WardCraftRules rules)
    {
        var index = system.AddCraft(
            typeof(BackpackWard),
            UtilityGroup,
            "backpack ward",
            BackpackWard.DefaultItemId,
            rules.MinSkill,
            rules.MaxSkill,
            typeof(IronIngot),
            IronIngotLabel,
            rules.Ingots,
            NotEnoughIngots
        );

        system.CraftItems[index].ForceNonExceptional = true;
        return index;
    }

    private static void OnServerStarted()
    {
        var rules = ShardRulesConfiguration.Settings?.WardCraft;

        if (rules is { Enabled: true } && TheftProtectionService.Enabled && DefTinkering.CraftSystem is { } system)
        {
            AddRecipe(system, rules);
            TinkeringMenu.AddMiscType(typeof(BackpackWard));
        }
    }
}
