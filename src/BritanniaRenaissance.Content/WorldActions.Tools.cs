using Server;
using Server.Engines.Craft;
using Server.Engines.Craft.T2A;
using Server.Engines.Harvest;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 3b, tools (owner, 2026-11-01): a crafting tool opens its craft menu, a harvest tool asks what to harvest, a knife or sword what to carve or cut,
/// scissors what to cut, a lockpick what to pick, a key what to lock or unlock. Greyed with the reason when the tool is worn out, the smithy is not near, or
/// the materials the craft needs are not in the pack. The cooking tools (skillet, rolling pin, flour sifter) have no craft menu in this era and are left out.
/// </summary>
public static partial class WorldActions
{
    public const byte CraftId = 60;
    public const byte ChopToolId = 61;
    public const byte MineToolId = 62;
    public const byte FishToolId = 63;
    public const byte BladeId = 64;
    public const byte ScissorsId = 65;
    public const byte LockpickId = 66;
    public const byte KeyId = 67;
    public const byte CopyKeyId = 68;

    public const string WornOut = "This tool is worn out.";
    public const string NeedSmithy = "You must be near an anvil and a forge to smith.";

    /// <summary>The craft menu's name, the materials it needs (any one of them), and what the reason says when none is carried.</summary>
    private static readonly (Func<CraftSystem> System, string Label, Type[] Materials, string Missing)[] Crafts =
    [
        (static () => DefBlacksmithy.CraftSystem, "Smith", [typeof(BaseIngot)], "Requires ingots."),
        (static () => DefTailoring.CraftSystem, "Tailor", [typeof(Cloth), typeof(UncutCloth), typeof(BoltOfCloth), typeof(BaseLeather)], "Requires cloth or leather."),
        (static () => DefTinkering.CraftSystem, "Tinker", [typeof(BaseIngot), typeof(Log)], "Requires ingots or logs."),
        (static () => DefCarpentry.CraftSystem, "Carpentry", [typeof(Log), typeof(Board)], "Requires logs."),
        (static () => DefBowFletching.CraftSystem, "Make bows and arrows", [typeof(Log), typeof(Shaft)], "Requires logs, or shafts and feathers."),
        (static () => DefAlchemy.CraftSystem, "Make potions", [typeof(BaseReagent)], "Requires reagents and an empty bottle."),
        (static () => DefInscription.CraftSystem, "Inscribe", [typeof(BlankScroll)], "Requires blank scrolls."),
        (static () => DefCartography.CraftSystem, "Make a map", [typeof(BlankMap)], "Requires a blank map.")
    ];

    /// <summary>Why a craft tool cannot be used now: worn out, then (smithing) the anvil and forge, then the materials.</summary>
    public static string? CraftReason(bool wornOut, bool smithyNeededButMissing, bool hasMaterials, string missing) =>
        wornOut ? WornOut : smithyNeededButMissing ? NeedSmithy : !hasMaterials ? missing : null;

    private static void AddToolActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        switch (item)
        {
            case BaseTool tool when CraftFor(tool) is var (system, label, materials, missing):
                {
                    var smithyMissing = false;

                    if (system == DefBlacksmithy.CraftSystem)
                    {
                        DefBlacksmithy.CheckAnvilAndForge(player, 2, out var anvil, out var forge);
                        smithyMissing = !(anvil && forge);
                    }

                    var hasMaterials = HasAny(player, materials) && (system != DefAlchemy.CraftSystem || player.Backpack?.FindItemByType<Bottle>() is not null);
                    actions.Add(new WorldAction(CraftId, label, CraftReason(tool.UsesRemaining <= 0, smithyMissing, hasMaterials, missing)));
                    break;
                }
            case BaseAxe { HarvestSystem: Lumberjacking } or BasePoleArm { HarvestSystem: Lumberjacking }:
                {
                    actions.Add(new WorldAction(ChopToolId, "Chop a tree", null));
                    break;
                }
            case BaseAxe { HarvestSystem: Mining } or BaseHarvestTool { HarvestSystem: Mining }:
                {
                    var worn = item is IUsesRemaining { UsesRemaining: <= 0 } ? WornOut : null;
                    actions.Add(new WorldAction(MineToolId, "Mine", worn ?? (player.Mounted ? MountedMining : null)));
                    break;
                }
            case FishingPole:
                {
                    actions.Add(new WorldAction(FishToolId, "Fish", player.Mounted ? MountedFishing : null));
                    break;
                }
            case BaseKnife or BaseSword:
                {
                    // a blade asks what to use it on: a corpse to carve, a tree for kindling
                    actions.Add(new WorldAction(BladeId, "Carve or cut kindling", null));
                    break;
                }
            case Scissors:
                {
                    actions.Add(new WorldAction(ScissorsId, "Cut something", null));
                    break;
                }
            case Lockpick:
                {
                    actions.Add(new WorldAction(LockpickId, "Pick a lock", null));
                    break;
                }
            case Key { KeyValue: 0 }:
                {
                    actions.Add(new WorldAction(CopyKeyId, "Copy a key onto this blank", null));
                    break;
                }
            case Key or KeyRing:
                {
                    actions.Add(new WorldAction(KeyId, "Lock or unlock", null));
                    break;
                }
        }
    }

    private static (CraftSystem System, string Label, Type[] Materials, string Missing)? CraftFor(BaseTool tool)
    {
        foreach (var (system, label, materials, missing) in Crafts)
        {
            if (tool.CraftSystem == system())
            {
                return (system(), label, materials, missing);
            }
        }

        return null;
    }

    private static bool HasAny(PlayerMobile player, Type[] types)
    {
        foreach (var type in types)
        {
            if (player.Backpack?.FindItemByType(type) is not null)
            {
                return true;
            }
        }

        return false;
    }

    private static bool PerformTool(PlayerMobile player, Item item, byte action)
    {
        switch (action)
        {
            case CraftId when item is BaseTool tool:
                {
                    // the craft menu straight away (T2A menus), as the tool's cursor would open it on any target; the stock check still speaks first
                    if (T2ACraftSystem.Enabled && tool.CraftSystem.CanCraft(player, tool, null) == 0)
                    {
                        T2ACraftSystem.ShowMenu(player, tool.CraftSystem, tool);
                    }
                    else
                    {
                        tool.OnDoubleClick(player);
                    }

                    return true;
                }
            case ChopToolId:
                {
                    // the axe or pole arm must be in the hands for any serious wood chopping
                    if (item.Parent != player && !Equip(player, item))
                    {
                        return true;
                    }

                    item.OnDoubleClick(player);
                    return true;
                }
            case MineToolId or FishToolId or BladeId or ScissorsId or LockpickId or KeyId or CopyKeyId:
                {
                    // the stock use: each asks with a cursor what to use it on
                    item.OnDoubleClick(player);
                    return true;
                }
        }

        return false;
    }
}
