using Server;
using Server.Engines.Craft;
using Server.Items;
using Server.Mobiles;
using Server.Multis;
using Server.Targets;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 6 (owner, 2026-11-02, from the gap sweep in docs/World-Actions-Evidence.md, items 1, 2, 5-16): stock uses that had no entry. A loose item in your
/// house is locked down or secured and a locked-down or secure one released; a weapon or armour is repaired or melted down at a smithy; the lore skills are
/// used on what they read (Item Identification, Arms Lore, Taste Identification, Remove Trap; Animal Lore on a creature); an explosion potion is thrown; a
/// house addon, strongbox or trash barrel is taken down with an axe; fish are cut into steaks and a sheep shorn with a blade; a player's ghost is resurrected
/// with a bandage; a beverage is drunk, poured or filled from another; a potion keg fills a bottle or takes your potions; a poison potion poisons a weapon or
/// food; a boat deed places its boat; wheat goes into a flour mill; a sextant and a clock are read. Each runs the stock use (its cursor answered with the
/// thing clicked), so every stock rule and message applies; the menu only says in advance what the stock use would refuse.
/// </summary>
public static partial class WorldActions
{
    public const byte RepairId = 180;
    public const byte MeltId = 181;
    public const byte IdentifyId = 182;
    public const byte ArmsLoreId = 183;
    public const byte TasteId = 184;
    public const byte DisarmTrapId = 185;
    public const byte ThrowId = 186;
    public const byte TakeDownId = 187;
    public const byte FishSteaksId = 188;
    public const byte DrinkBeverageId = 189;
    public const byte PourId = 190;
    public const byte FillFromId = 191;
    public const byte KegFillId = 192;
    public const byte KegPourId = 193;
    public const byte PoisonId = 194;
    public const byte PlaceBoatId = 195;
    public const byte MillId = 196;
    public const byte SextantId = 197;
    public const byte ClockId = 198;
    public const byte LockDownId = 199;
    public const byte ReleaseId = 200;
    public const byte SecureId = 201;
    public const byte UnsecureId = 202;
    public const byte AnimalLoreId = 203;
    public const byte ShearId = 204;
    public const byte ResurrectId = 205;

    public const string NotShornYet = "This sheep is not yet ready to be shorn.";
    public const string TooFarToReach = "Too far away. Stand within 2 tiles.";
    public const string KegEmpty = "The keg is empty.";
    public const string NoEmptyBottle = "Requires an empty bottle.";
    public const string KegFull = "The keg will not hold any more!";
    public const string NoMillNear = "Needs a flour mill within 4 tiles.";
    public const string NotCoOwner = "You must be a co-owner of this house.";
    public const string NotOwnerTakeDown = "Only the house owner can take this down.";
    public const string NoResSkill = "You need 80 Healing and 80 Anatomy to resurrect.";
    public const string StandInHouse = "You must be inside your house to do this.";

    /// <summary>A bandage resurrects before AOS at 80 Healing and 80 Anatomy (BandageContext.OnTick).</summary>
    public static bool CanResurrect(double healing, double anatomy) => healing >= 80.0 && anatomy >= 80.0;

    /// <summary>A lore skill is offered only to someone who has it: at 0 the check can never succeed.</summary>
    public static bool HasSkill(double baseValue) => baseValue > 0;

    private static string? SkillReason(PlayerMobile player) => Core.TickCount - player.NextSkillTime < 0 ? SkillResting : null;

    private static void AddWave6Actions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        var carried = item.IsChildOf(player.Backpack);

        if (carried && item is BaseWeapon or BaseArmor)
        {
            AddSmithyActions(player, item, actions);
        }

        if (item is BaseWeapon or BaseArmor && (carried || item.Parent == player))
        {
            if (HasSkill(player.Skills.ItemID.Base))
            {
                actions.Add(new WorldAction(IdentifyId, "Identify", SkillReason(player)));
            }

            if (HasSkill(player.Skills.ArmsLore.Base))
            {
                actions.Add(new WorldAction(ArmsLoreId, "Examine the workmanship", SkillReason(player)));
            }
        }

        if (item is Food or BasePotion or PotionKeg && HasSkill(player.Skills.TasteID.Base) && (carried || player.InRange(item.GetWorldLocation(), 2)))
        {
            actions.Add(new WorldAction(TasteId, "Taste to identify", SkillReason(player)));
        }

        // offered on any trappable container, trapped or not, so the menu never gives a hidden trap away
        if (item is TrappableContainer && HasSkill(player.Skills.RemoveTrap.Base) && (carried || player.InRange(item.GetWorldLocation(), 2)))
        {
            actions.Add(new WorldAction(DisarmTrapId, "Disarm a trap", SkillReason(player)));
        }

        switch (item)
        {
            case BaseExplosionPotion potion when carried:
                {
                    actions.Add(new WorldAction(ThrowId, "Throw", !potion.RequireFreeHand || BasePotion.HasFreeHand(player) ? null : "You must have a free hand to throw it."));
                    break;
                }
            case BasePoisonPotion when carried:
                {
                    actions.Add(new WorldAction(PoisonId, "Poison a weapon or food", SkillReason(player)));
                    break;
                }
            case Fish when carried:
                {
                    actions.Add(new WorldAction(FishSteaksId, "Cut into fish steaks", CorpseCarveButton.FindBlade(player) is null ? NoBlade : null));
                    break;
                }
            case BaseBeverage { IsEmpty: false, Pourable: true } beverage when carried:
                {
                    actions.Add(new WorldAction(DrinkBeverageId, "Drink", null));

                    if (EmptyVessel(player, except: beverage) is { } vessel)
                    {
                        actions.Add(new WorldAction(PourId, $"Pour into the empty {VesselName(vessel)}", null));
                    }

                    break;
                }
            case BaseBeverage { IsEmpty: true, Fillable: true } beverage when carried && FullBeverage(player, except: beverage) is { } full:
                {
                    actions.Add(new WorldAction(FillFromId, $"Fill with {full.Content.ToString().ToLowerInvariant()}", null));
                    break;
                }
            case PotionKeg keg when carried || item.Parent is null:
                {
                    var far = !carried && !player.InRange(keg.GetWorldLocation(), 2) ? TooFarToReach : null;
                    var bottle = player.Backpack?.FindItemByType<Bottle>() is not null;
                    actions.Add(new WorldAction(KegFillId, "Fill a bottle", keg.Held <= 0 ? KegEmpty : !bottle ? NoEmptyBottle : far));

                    if (keg.Held > 0 && KegPotion(player, keg) is { } potion)
                    {
                        actions.Add(new WorldAction(KegPourId, $"Pour in your {VesselName(potion)}s", keg.Held >= 100 ? KegFull : far));
                    }

                    break;
                }
            case BaseBoatDeed:
                {
                    actions.Add(new WorldAction(PlaceBoatId, "Place the boat", carried ? null : CheckInPack));
                    break;
                }
            case WheatSheaf when carried:
                {
                    actions.Add(new WorldAction(MillId, "Put in the flour mill", MillNear(player) is null ? NoMillNear : null));
                    break;
                }
            case Sextant when carried:
                {
                    actions.Add(new WorldAction(SextantId, "Find your position", null));
                    break;
                }
            case Clock when carried || player.InRange(item.GetWorldLocation(), 2):
                {
                    actions.Add(new WorldAction(ClockId, "Check the time", null));
                    break;
                }
        }

        AddHouseActions(player, item, actions);
    }

    private static void AddSmithyActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        var tool = CraftTool(player, DefBlacksmithy.CraftSystem);
        DefBlacksmithy.CheckAnvilAndForge(player, 2, out var anvil, out var forge);
        var reason = tool is null ? NoSmithTool : tool.UsesRemaining <= 0 ? WornOut : !(anvil && forge) ? NeedSmithy : null;

        actions.Add(new WorldAction(RepairId, "Repair", reason));

        var metal = item switch
        {
            BaseWeapon w => CraftResources.GetType(w.Resource) == CraftResourceType.Metal,
            BaseArmor a  => CraftResources.GetType(a.Resource) == CraftResourceType.Metal,
            _            => false
        };

        if (metal)
        {
            actions.Add(new WorldAction(MeltId, "Melt down", reason));
        }
    }

    /// <summary>Lock down, release, secure and unsecure, for a co-owner standing in the house (the stock house words; HouseRegion.OnSpeech).</summary>
    private static void AddHouseActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        if (item.Parent is not null || BaseHouse.FindHouseAt(item) is not { } house || !house.IsInside(item) || !house.IsFriend(player))
        {
            return;
        }

        if (item is IChoppable or AddonComponent { Addon: IChoppable })
        {
            // the stock axe use (HarvestTarget: IChoppable.OnChop): an addon goes back into its deed, a strongbox or trash barrel is taken away
            var owner = item is TrashBarrel ? house.IsCoOwner(player) : house.IsOwner(player);
            var reason = !owner ? NotOwnerTakeDown : FindAxe(player) is null ? NoAxe : !player.InRange(item.GetWorldLocation(), 3) ? "Too far away. Stand within 3 tiles." : null;
            actions.Add(new WorldAction(TakeDownId, "Take down", reason));
        }

        if (!item.Movable && !item.IsLockedDown && !item.IsSecure || item is AddonComponent or BaseAddon)
        {
            return;
        }

        var coOwner = house.IsCoOwner(player) ? house.IsInside(player) ? null : StandInHouse : NotCoOwner;

        if (item.IsSecure)
        {
            actions.Add(new WorldAction(UnsecureId, "Unsecure", coOwner));
        }
        else if (item.IsLockedDown)
        {
            actions.Add(new WorldAction(ReleaseId, "Release", coOwner));
        }
        else
        {
            actions.Add(new WorldAction(LockDownId, "Lock down", coOwner));

            if (item is Container)
            {
                actions.Add(new WorldAction(SecureId, "Secure", coOwner));
            }
        }
    }

    private static string VesselName(Item item) => HelpService.ItemName(item).ToLowerInvariant();

    private static BaseBeverage? EmptyVessel(PlayerMobile player, BaseBeverage except) =>
        player.Backpack?.FindItemByType<BaseBeverage>(predicate: bev => bev != except && bev is { IsEmpty: true, Fillable: true });

    private static BaseBeverage? FullBeverage(PlayerMobile player, BaseBeverage except) =>
        player.Backpack?.FindItemByType<BaseBeverage>(predicate: bev => bev != except && bev is { IsEmpty: false, Pourable: true });

    private static BasePotion? KegPotion(PlayerMobile player, PotionKeg keg) =>
        player.Backpack?.FindItemByType<BasePotion>(predicate: potion => potion.PotionEffect == keg.Type);

    private static Item? MillNear(PlayerMobile player)
    {
        foreach (var item in player.Map.GetItemsInRange(player.Location, 4))
        {
            if (item is IFlourMill or AddonComponent { Addon: IFlourMill })
            {
                return item;
            }
        }

        return null;
    }

    private static bool PerformWave6(PlayerMobile player, Item item, byte action)
    {
        switch (action)
        {
            case RepairId or MeltId when CraftTool(player, DefBlacksmithy.CraftSystem) is { } tool:
                {
                    if (action == RepairId)
                    {
                        Repair.Do(player, DefBlacksmithy.CraftSystem, tool);
                    }
                    else
                    {
                        Resmelt.Do(player, DefBlacksmithy.CraftSystem, tool);
                    }

                    AnswerCursor(player, item);
                    return true;
                }
            case IdentifyId or ArmsLoreId or TasteId or DisarmTrapId or PoisonId:
                {
                    // the skill asks with a cursor what to use it on: answer it with this (poison then asks for the weapon or food)
                    player.UseSkill(action switch
                    {
                        IdentifyId   => SkillName.ItemID,
                        ArmsLoreId   => SkillName.ArmsLore,
                        TasteId      => SkillName.TasteID,
                        DisarmTrapId => SkillName.RemoveTrap,
                        _            => SkillName.Poisoning
                    });
                    AnswerCursor(player, item);
                    return true;
                }
            case FishSteaksId when CorpseCarveButton.FindBlade(player) is { } blade:
                {
                    new BladedItemTarget(blade).Invoke(player, item);
                    return true;
                }
            case DrinkBeverageId when item is BaseBeverage beverage:
                {
                    beverage.Pour_OnTarget(player, player);
                    return true;
                }
            case PourId when item is BaseBeverage beverage && EmptyVessel(player, beverage) is { } vessel:
                {
                    beverage.Pour_OnTarget(player, vessel);
                    return true;
                }
            case FillFromId when item is BaseBeverage beverage && FullBeverage(player, beverage) is { } full:
                {
                    beverage.Fill_OnTarget(player, full);
                    return true;
                }
            case KegPourId when item is PotionKeg keg && KegPotion(player, keg) is { } potion:
                {
                    keg.OnDragDrop(player, potion);
                    return true;
                }
            case MillId when MillNear(player) is { } mill:
                {
                    AnswerUse(player, item, mill);
                    return true;
                }
            case TakeDownId when FindAxe(player) is { } axe:
                {
                    // the axe must be in hand for the stock cursor; the chop itself runs the stock OnChop with every owner check
                    if (axe.Parent != player && !Equip(player, axe))
                    {
                        return true;
                    }

                    (item as IChoppable ?? (item as AddonComponent)?.Addon as IChoppable)?.OnChop(player);
                    return true;
                }
            case LockDownId or ReleaseId when BaseHouse.FindHouseAt(item) is { } house:
                {
                    new LockdownTarget(action == ReleaseId, house).Invoke(player, item);
                    return true;
                }
            case SecureId or UnsecureId when BaseHouse.FindHouseAt(item) is { } house:
                {
                    new SecureTarget(action == UnsecureId, house).Invoke(player, item);
                    return true;
                }
            case ThrowId or KegFillId or PlaceBoatId or SextantId or ClockId:
                {
                    // the stock use: the potion's throw cursor, the keg's bottle, the boat's placing cursor, the reading
                    item.OnDoubleClick(player);
                    return true;
                }
        }

        return false;
    }

    /// <summary>Double-clicks the item and answers the cursor it raises with the target.</summary>
    private static void AnswerUse(PlayerMobile player, Item item, object target)
    {
        item.OnDoubleClick(player);
        AnswerCursor(player, target);
    }

    // ---- creatures: shear a sheep, Animal Lore, resurrect a ghost

    private static void AddWave6MobileActions(PlayerMobile player, Mobile mobile, List<WorldAction> actions)
    {
        if (mobile is Sheep sheep && sheep.Alive)
        {
            var reason = CorpseCarveButton.FindBlade(player) is null ? NoBlade :
                sheep.NextWoolTime > Core.Now ? NotShornYet : !player.InRange(sheep, 2) ? TooFarToReach : null;
            actions.Add(new WorldAction(ShearId, "Shear", reason));
        }

        if (mobile is BaseCreature { Alive: true } && HasSkill(player.Skills.AnimalLore.Base))
        {
            actions.Add(new WorldAction(AnimalLoreId, "Study this animal", SkillReason(player)));
        }
    }

    private static WorldAction ResurrectAction(PlayerMobile player, PlayerMobile ghost) =>
        new(
            ResurrectId, "Resurrect with a bandage",
            FindBandage(player) is null ? NoBandages :
            !CanResurrect(player.Skills.Healing.Value, player.Skills.Anatomy.Value) ? NoResSkill :
            !player.InRange(ghost, Bandage.Range) ? TooFarToBandage : null
        );

    private static bool PerformWave6Mobile(PlayerMobile player, Mobile mobile, byte action)
    {
        switch (action)
        {
            case ShearId when CorpseCarveButton.FindBlade(player) is { } blade:
                {
                    new BladedItemTarget(blade).Invoke(player, mobile);
                    return true;
                }
            case AnimalLoreId:
                {
                    player.UseSkill(SkillName.AnimalLore);
                    AnswerCursor(player, mobile);
                    return true;
                }
            case ResurrectId when FindBandage(player) is { } bandage:
                {
                    Bandage.BandageTargetRequest(player, bandage, mobile);
                    return true;
                }
        }

        return false;
    }
}
