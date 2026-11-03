using Server;
using Server.Collections;
using Server.ContextMenus;
using Server.Engines.Craft;
using Server.Engines.Craft.T2A;
using Server.Engines.Harvest;
using Server.Items;
using Server.Mobiles;
using Server.Multis;
using Server.Multis.Deeds;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 3b, resources and other things (owner, 2026-11-01): materials open the craft menu of the tool they go with (ingots, cloth and leather, logs,
/// shafts, reagents and bottles, blank scrolls, blank maps), and logs are cut into boards with an axe (2026-11-02); a bedroll on the ground is unrolled or rolled up (which offers the safe logout in a secure camp);
/// a message in a bottle is opened and its SOS read; a fishing net cast; a house or addon deed placed; a training dummy, pickpocket dip or archery butte
/// practised on; food fed to one of your pets; and the stock treasure map entries say why they are greyed.
/// </summary>
public static partial class WorldActions
{
    public const byte CraftFromId = 120;
    public const byte BedrollId = 121;
    public const byte OpenBottleId = 122;
    public const byte ReadSosId = 123;
    public const byte CastNetId = 124;
    public const byte PlaceHouseId = 125;
    public const byte PlaceAddonId = 126;
    public const byte TrainId = 127;
    public const byte GatherArrowsId = 128;
    public const byte FeedPetId = 129;
    public const byte CartographyId = 130;
    public const byte FletchFromId = 131;
    public const byte BoardsId = 132;

    public const string BedrollOnGround = "Put the bedroll on the ground first.";
    public const string AlreadyOwnHouse = "You already own a house, you may not place another!";
    public const string NoPetHere = "You have no pet near you.";
    public const string NoPetEatsThis = "None of your pets near you eats this.";
    public const string RangedOnDummy = "You can't practise ranged weapons on this.";
    public const string NeedRangedWeapon = "You must practise with a bow or crossbow on this.";
    public const string MountedPractice = "You can't practise on this while riding.";
    public const string DummyCapped = "Your skill cannot improve any further by practising on this.";
    public const string ButteDistance = "Stand 5 or 6 tiles away, straight in front of it.";
    public const string NoDiggingTool = "Requires a shovel or pickaxe in your pack.";

    /// <summary>The Cartography a treasure map of a level needs to be decoded (TreasureMap.GetMinSkillLevel).</summary>
    public static double MapDecodeSkill(int level) =>
        level switch
        {
            1 => -3.0,
            2 => 41.0,
            3 => 51.0,
            4 => 61.0,
            5 or 6 => 70.0,
            _ => 0.0
        };

    /// <summary>What a training object would refuse: the weapon, riding, the reach, then the skill cap.</summary>
    public static string? PracticeReason(string? weaponProblem, bool mounted, bool inRange, bool capped, string tooFar) =>
        weaponProblem ?? (mounted ? MountedPractice : !inRange ? tooFar : capped ? DummyCapped : null);

    private static void AddMiscActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        var carried = item.IsChildOf(player.Backpack);

        switch (item)
        {
            case BaseIngot when carried:
                {
                    AddCraftFrom(player, actions, DefBlacksmithy.CraftSystem, "Smith with these", "Requires a smith's hammer or tongs.");
                    break;
                }
            case Cloth or UncutCloth or BoltOfCloth or BaseLeather when carried:
                {
                    AddCraftFrom(player, actions, DefTailoring.CraftSystem, "Tailor with this", "Requires a sewing kit.");
                    break;
                }
            case Log or Board when carried:
                {
                    // owner, 2026-11-02: logs offer the stock axe-on-logs (Log.Axe), as a player who targets them with an axe would
                    if (item is Log)
                    {
                        actions.Add(new WorldAction(BoardsId, "Cut into boards", FindBoardAxe(player) is null ? NoAxe : null));
                    }

                    AddCraftFrom(player, actions, DefCarpentry.CraftSystem, "Carpentry with these", "Requires a carpentry tool, such as a saw.");
                    AddCraftFrom(player, actions, DefBowFletching.CraftSystem, "Make bows and arrows", "Requires fletching tools.", id: FletchFromId);
                    break;
                }
            case Shaft or Feather when carried:
                {
                    AddCraftFrom(player, actions, DefBowFletching.CraftSystem, "Make arrows and bolts", "Requires fletching tools.");
                    break;
                }
            case BaseReagent or Bottle when carried:
                {
                    var other = item is Bottle ? player.Backpack?.FindItemByType<BaseReagent>() is null ? "Requires reagents." : null :
                        player.Backpack?.FindItemByType<Bottle>() is null ? "Requires an empty bottle." : null;
                    AddCraftFrom(player, actions, DefAlchemy.CraftSystem, "Make potions", "Requires a mortar and pestle.", other);
                    break;
                }
            case BlankScroll when carried:
                {
                    // inscription needs no pen in the T2A menus: the skill takes the scroll
                    actions.Add(new WorldAction(CraftFromId, "Inscribe", Core.TickCount - player.NextSkillTime < 0 ? SkillResting : null));
                    break;
                }
            case BlankMap when carried:
                {
                    actions.Add(new WorldAction(CartographyId, "Make a map", Core.TickCount - player.NextSkillTime < 0 ? SkillResting : null));
                    break;
                }
            case Bedroll bedroll:
                {
                    var rolled = bedroll.ItemID == 0xA57;
                    var label = rolled ? "Unroll" : Campfire.GetEntry(player)?.Safe == true ? "Roll up and log out safely" : "Roll up";
                    var reason = bedroll.Parent is not null ? BedrollOnGround : !player.InRange(bedroll.GetWorldLocation(), 2) ? "Too far away. Stand next to it." : null;
                    actions.Add(new WorldAction(BedrollId, label, reason));
                    break;
                }
            case MessageInABottle when carried:
                {
                    actions.Add(new WorldAction(OpenBottleId, "Open the bottle", null));
                    break;
                }
            case SOS when carried:
                {
                    actions.Add(new WorldAction(ReadSosId, "Read the message", null));
                    break;
                }
            case SpecialFishingNet when carried:
                {
                    actions.Add(new WorldAction(CastNetId, "Cast the net", null));
                    break;
                }
            case HouseDeed when carried:
                {
                    var owns = player.AccessLevel == AccessLevel.Player && BaseHouse.HasAccountHouse(player);
                    actions.Add(new WorldAction(PlaceHouseId, "Place the house", owns ? AlreadyOwnHouse : null));
                    break;
                }
            case BaseAddonDeed when carried:
                {
                    actions.Add(new WorldAction(PlaceAddonId, "Place it", null));
                    break;
                }
            case TrainingDummy dummy:
                {
                    var weapon = player.Weapon as BaseWeapon;
                    var reason = PracticeReason(
                        weapon is BaseRanged ? RangedOnDummy : null, player.Mounted, weapon is not null && player.InRange(dummy.GetWorldLocation(), weapon.MaxRange),
                        weapon is not null && player.Skills[weapon.Skill].Base >= dummy.MaxSkill, "Too far away. Stand next to it."
                    );
                    actions.Add(new WorldAction(TrainId, "Practise", reason));
                    break;
                }
            case PickpocketDip dip:
                {
                    var reason = PracticeReason(
                        null, player.Mounted, player.InRange(dip.GetWorldLocation(), 1), player.Skills.Stealing.Base >= dip.MaxSkill, "Too far away. Stand next to it."
                    );
                    actions.Add(new WorldAction(TrainId, "Practise stealing", reason));
                    break;
                }
            case ArcheryButte butte:
                {
                    var location = butte.GetWorldLocation();

                    if ((butte.Arrows > 0 || butte.Bolts > 0) && player.InRange(location, 1))
                    {
                        actions.Add(new WorldAction(GatherArrowsId, "Gather the arrows", null));
                    }

                    var distance = Math.Max(Math.Abs(player.X - location.X), Math.Abs(player.Y - location.Y));
                    var ranged = player.Weapon as BaseRanged;
                    var reason = PracticeReason(
                        ranged is null ? NeedRangedWeapon : null, false, distance is >= 5 and <= 6,
                        ranged is not null && player.Skills[ranged.Skill].Base >= butte.MaxSkill, ButteDistance
                    );
                    actions.Add(new WorldAction(TrainId, "Shoot at it", reason));
                    break;
                }
            case Food food when carried && !food.Deleted:
                {
                    var pets = PetsNear(player);
                    var reason = pets.Count == 0 ? NoPetHere : PetFor(pets, food) is null ? NoPetEatsThis : null;
                    actions.Add(new WorldAction(FeedPetId, food.Amount > 1 ? $"Feed your pet (all {food.Amount})" : "Feed your pet", reason));
                    break;
                }
        }
    }

    private static void AddCraftFrom(
        PlayerMobile player, List<WorldAction> actions, CraftSystem system, string label, string noTool, string? other = null, byte id = CraftFromId
    )
    {
        var tool = CraftTool(player, system);
        var reason = tool is null ? noTool : tool.UsesRemaining <= 0 ? WornOut : other;

        if (reason is null && system == DefBlacksmithy.CraftSystem)
        {
            DefBlacksmithy.CheckAnvilAndForge(player, 2, out var anvil, out var forge);
            reason = anvil && forge ? null : NeedSmithy;
        }

        actions.Add(new WorldAction(id, label, reason));
    }

    private static BaseTool? CraftTool(PlayerMobile player, CraftSystem system) =>
        Held(player) is BaseTool held && held.CraftSystem == system
            ? held
            : player.Backpack?.FindItemByType<BaseTool>(predicate: tool => tool.CraftSystem == system && tool.UsesRemaining > 0) ??
              player.Backpack?.FindItemByType<BaseTool>(predicate: tool => tool.CraftSystem == system);

    private static List<BaseCreature> PetsNear(PlayerMobile player)
    {
        var pets = new List<BaseCreature>();

        foreach (var m in player.GetMobilesInRange(2))
        {
            if (m is BaseCreature { Controlled: true, Alive: true } pet && pet.ControlMaster == player)
            {
                pets.Add(pet);
            }
        }

        return pets;
    }

    private static BaseCreature? PetFor(List<BaseCreature> pets, Item food)
    {
        foreach (var pet in pets)
        {
            if (pet.CheckFoodPreference(food))
            {
                return pet;
            }
        }

        return null;
    }

    /// <summary>An axe that cuts logs: in the hands first, else in the pack (a pole arm chops trees but is no axe to the logs).</summary>
    private static BaseAxe? FindBoardAxe(Mobile m) =>
        Held(m) is BaseAxe { HarvestSystem: Lumberjacking } held ? held :
            m.Backpack?.FindItemByType<BaseAxe>(predicate: static axe => axe.HarvestSystem is Lumberjacking);

    private static bool PerformMisc(PlayerMobile player, Item item, byte action)
    {
        switch (action)
        {
            case CraftFromId when item is BlankScroll:
                {
                    // the Inscription skill asks for the scroll to use: answer it with this one
                    player.UseSkill(SkillName.Inscribe);
                    AnswerCursor(player, item);
                    return true;
                }
            case CartographyId:
                {
                    player.UseSkill(SkillName.Cartography);
                    return true;
                }
            case BoardsId when item is Log log && FindBoardAxe(player) is { } axe:
                {
                    // stock needs the axe in hand to raise its cursor; the target then runs Log.Axe (HarvestTarget)
                    if ((axe.Parent == player || TakeUp(player, axe)) && log.Axe(player, axe))
                    {
                        player.PlaySound(0x13E);
                    }

                    return true;
                }
            case CraftFromId or FletchFromId:
                {
                    var system = item switch
                    {
                        _ when action == FletchFromId => DefBowFletching.CraftSystem,
                        Log or Board => DefCarpentry.CraftSystem,
                        BaseIngot => DefBlacksmithy.CraftSystem,
                        Cloth or UncutCloth or BoltOfCloth or BaseLeather => DefTailoring.CraftSystem,
                        Shaft or Feather => DefBowFletching.CraftSystem,
                        BaseReagent or Bottle => DefAlchemy.CraftSystem,
                        _ => null
                    };

                    if (system is not null && CraftTool(player, system) is { } tool)
                    {
                        OpenCraft(player, tool, item);
                    }

                    return true;
                }
            case BedrollId or OpenBottleId or ReadSosId or CastNetId or PlaceHouseId or PlaceAddonId or TrainId or GatherArrowsId:
                {
                    // the stock use, which does it or asks with a cursor or a window
                    item.OnDoubleClick(player);
                    return true;
                }
            case FeedPetId when PetFor(PetsNear(player), item) is { } pet:
                {
                    pet.CheckFeed(player, item);
                    return true;
                }
        }

        return false;
    }

    /// <summary>Opens the craft menu with the material chosen, as targeting the material with the tool would.</summary>
    private static void OpenCraft(PlayerMobile player, BaseTool tool, Item material)
    {
        if (T2ACraftSystem.Enabled && tool.CraftSystem.CanCraft(player, tool, null) == 0)
        {
            T2ACraftSystem.ShowMenu(player, tool.CraftSystem, tool, material);
        }
        else
        {
            tool.OnDoubleClick(player);
        }
    }

    private static void AnswerCursor(PlayerMobile player, object target)
    {
        if (player.Target is not { } cursor)
        {
            return;
        }

        cursor.Invoke(player, target);

        if (player.Target is null)
        {
            player.NetState?.SendCancelTarget();
        }
    }

    // ---- the stock treasure map entries: say why Decode and Dig are greyed

    private static void AdjustTreasureMapEntries(PlayerMobile player, Item item, ref PooledRefList<ContextMenuEntry> list, List<(int Index, WorldAction Action)> texts)
    {
        if (item is not TreasureMap map)
        {
            return;
        }

        for (var i = 0; i < list.Count; i++)
        {
            switch (list[i].Number)
            {
                case 3006147 when map.Decoder is null && player.Skills.Cartography.Value < MapDecodeSkill(map.Level):
                    {
                        list[i].Enabled = false;
                        texts.Add((i, new WorldAction(0, "Decode map", $"You need {MapDecodeSkill(map.Level):0} Cartography to decode this map.")));
                        break;
                    }
                case 3006148 when !TreasureMap.HasDiggingTool(player):
                    {
                        list[i].Enabled = false;
                        texts.Add((i, new WorldAction(0, "Dig for treasure", NoDiggingTool)));
                        break;
                    }
            }
        }
    }
}
