using Server;
using Server.Accounting;
using Server.Items;
using Server.Mobiles;
using Server.Multis;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 5 (owner, 2026-11-01: "fill for containers that hold liquid, chop for pole arms, wool/cotton/flax/yarn, moongates, docked boat (launch), bank
/// check, shepherd's crook, cow (milk)"): an empty pitcher, mug or goblet is filled at a trough, tub, barrel or bucket of water, or with milk from a cow; wool,
/// cotton and flax are spun on a wheel and yarn and thread woven on a loom straight from the pack; a public moongate is travelled through and a spell's gate
/// entered; a docked boat is launched; a bank check is cashed; a shepherd's crook herds an animal; and a cow is milked into an empty vessel. Pole arms chop
/// trees as axes do (FindAxe and the tool actions). Each runs the stock use, so every stock rule and message applies; the menu only says in advance what the
/// stock use would refuse.
/// </summary>
public static partial class WorldActions
{
    public const byte FillWaterId = 160;
    public const byte FillMilkId = 161;
    public const byte FillId = 162;
    public const byte SpinHereId = 163;
    public const byte WeaveHereId = 164;
    public const byte TravelId = 165;
    public const byte EnterGateId = 166;
    public const byte LaunchId = 167;
    public const byte CashCheckId = 168;
    public const byte HerdId = 169;
    public const byte MilkId = 170;

    /// <summary>A vessel is filled from 2 tiles, in sight (BaseBeverage.Fill_OnTarget, Cow.TryMilk).</summary>
    public const int FillRange = 2;

    /// <summary>Wool, cotton and flax reach a wheel 3 tiles away (Cotton.WheelRange), yarn and thread a loom 3 tiles away (PickLoomTarget).</summary>
    public const int SpinRange = 3;

    public const string NoLiquidNear = "Stand next to a trough, tub, barrel or bucket of water, or a cow.";
    public const string NoWheelNear = "Needs a spinning wheel within 3 tiles.";
    public const string NoLoomNear = "Needs a loom within 3 tiles.";
    public const string CriminalAtGate = "Criminals cannot use the moongate.";
    public const string FightingAtGate = "You cannot use the moongate during a fight.";
    public const string CastingAtGate = "You are too busy casting to use the moongate.";
    public const string TooFarFromGate = "Too far away. Stand next to the gate.";
    public const string GateGoesNowhere = "This moongate does not seem to go anywhere.";
    public const string CheckInBank = "Put it in your bank box first.";
    public const string CheckInPack = "Put it in your backpack first.";
    public const string NoEmptyVessel = "Requires an empty pitcher, mug or goblet.";
    public const string NotYourCow = "This is someone else's cow.";
    public const string CowMilkedOut = "This cow has no milk left. Try again in a day.";
    public const string TooFarToMilk = "Too far away. Stand within 2 tiles.";

    /// <summary>What a public moongate would refuse, in the stock order (PublicMoongate.UseGate), with the reach last.</summary>
    public static string? TravelReason(bool criminal, bool fighting, bool casting, bool inRange) =>
        criminal ? CriminalAtGate : fighting ? FightingAtGate : casting ? CastingAtGate : !inRange ? TooFarFromGate : null;

    /// <summary>What milking would refuse: the vessel first, then whose cow it is, then the milk, then the reach (Cow.TryMilk).</summary>
    public static string? MilkReason(bool hasVessel, bool someoneElses, bool milkedOut, bool inRange) =>
        !hasVessel ? NoEmptyVessel : someoneElses ? NotYourCow : milkedOut ? CowMilkedOut : !inRange ? TooFarToMilk : null;

    /// <summary>A cow gives 4 milkings, then none until a day after the last (Cow.TryMilk).</summary>
    public static bool MilkedOut(int milk, DateTime milkedOn, DateTime now) => milk == 0 && milkedOn + TimeSpan.FromDays(1) > now;

    private static void AddEverydayActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        var carried = item.IsChildOf(player.Backpack);

        switch (item)
        {
            case BaseBeverage { IsEmpty: true, Fillable: true } when carried:
                {
                    var water = WaterNear(player);
                    var cow = MilkableCowNear(player);

                    if (water is not null)
                    {
                        actions.Add(new WorldAction(FillWaterId, "Fill with water", null));
                    }

                    if (cow is not null)
                    {
                        actions.Add(new WorldAction(FillMilkId, "Fill with milk", null));
                    }

                    // a full beverage in the pack fills it too (wave 6, Fill with ...)
                    if (water is null && cow is null && FullBeverage(player, (BaseBeverage)item) is null)
                    {
                        actions.Add(new WorldAction(FillId, "Fill", NoLiquidNear));
                    }

                    break;
                }
            case Wool or Cotton or Flax when carried:
                {
                    var wheel = WheelNear(player);
                    actions.Add(new WorldAction(SpinHereId, "Spin on the wheel", wheel is null ? NoWheelNear : wheel.Spinning ? WheelBusy : null));
                    break;
                }
            case BaseClothMaterial when carried:
                {
                    actions.Add(new WorldAction(WeaveHereId, "Weave on the loom", LoomNear(player) is null ? NoLoomNear : null));
                    break;
                }
            case PublicMoongate gate:
                {
                    var reason = TravelReason(
                        player.Criminal, SpellHelper.CheckCombat(player), player.Spell is not null, player.InRange(gate.GetWorldLocation(), 1)
                    );
                    actions.Add(new WorldAction(TravelId, "Travel", reason));
                    break;
                }
            case Moongate gate:
                {
                    var reason = gate.TargetMap is null || gate.TargetMap == Map.Internal ? GateGoesNowhere :
                        player.Spell is not null ? CastingAtGate : !player.InRange(gate.GetWorldLocation(), 1) ? TooFarFromGate : null;
                    actions.Add(new WorldAction(EnterGateId, "Enter the gate", reason));
                    break;
                }
            case BaseDockedBoat when carried:
                {
                    actions.Add(new WorldAction(LaunchId, "Launch the boat", null));
                    break;
                }
            case BankCheck check:
                {
                    // without account gold a check is cashed from the bank box (BankCheck.OnDoubleClick)
                    var reason = AccountGold.Enabled ? carried ? null : CheckInPack :
                        player.FindBankNoCreate() is { } bank && check.IsChildOf(bank) ? null : CheckInBank;
                    actions.Add(new WorldAction(CashCheckId, $"Cash it ({check.Worth:N0} gold)", reason));
                    break;
                }
            case ShepherdsCrook when carried || item.Parent == player:
                {
                    actions.Add(new WorldAction(HerdId, "Herd an animal", null));
                    break;
                }
        }
    }

    private static bool PerformEveryday(PlayerMobile player, Item item, byte action)
    {
        switch (action)
        {
            case FillWaterId when item is BaseBeverage vessel && WaterNear(player) is { } water:
                {
                    vessel.Fill_OnTarget(player, water);
                    return true;
                }
            case FillMilkId when item is BaseBeverage vessel && MilkableCowNear(player) is { } cow:
                {
                    vessel.Fill_OnTarget(player, cow);
                    return true;
                }
            case SpinHereId when WheelNear(player) is { } wheel:
                {
                    switch (item)
                    {
                        case Wool wool:
                            {
                                wool.SpinOn(player, wheel);
                                break;
                            }
                        case Cotton cotton:
                            {
                                cotton.SpinOn(player, wheel);
                                break;
                            }
                        case Flax flax:
                            {
                                flax.SpinOn(player, wheel);
                                break;
                            }
                    }

                    return true;
                }
            case WeaveHereId:
                {
                    Use(player, item, LoomNear(player));
                    return true;
                }
            case TravelId or EnterGateId or LaunchId or CashCheckId or HerdId:
                {
                    // the stock use: the moongate's list or the gate's confirmation, the boat's placing cursor, the deposit, the herding cursor
                    item.OnDoubleClick(player);
                    return true;
                }
        }

        return false;
    }

    // ---- the cow's own menu

    private static WorldAction MilkAction(PlayerMobile player, Cow cow) =>
        new(
            MilkId, "Milk",
            MilkReason(
                EmptyVessel(player) is not null, cow.Controlled && cow.ControlMaster != player, MilkedOut(cow.Milk, cow.MilkedOn, Core.Now),
                player.InRange(cow.Location, FillRange) && player.InLOS(cow)
            )
        );

    private static void Milk(PlayerMobile player, Cow cow) => EmptyVessel(player)?.Fill_OnTarget(player, cow);

    // ---- finding things

    private static BaseBeverage? EmptyVessel(PlayerMobile player) =>
        player.Backpack?.FindItemByType<BaseBeverage>(predicate: static bev => bev is { IsEmpty: true, Fillable: true });

    /// <summary>Water a vessel fills from: a trough (an addon), tub, barrel or bucket with water in it, in reach and in sight.</summary>
    private static Item? WaterNear(PlayerMobile player)
    {
        foreach (var item in player.Map.GetItemsInRange(player.Location, FillRange))
        {
            var hasWater = item switch
            {
                BaseWaterContainer container => !container.IsEmpty,
                IWaterSource source          => source.Quantity > 0,
                AddonComponent { Addon: IWaterSource source } => source.Quantity > 0,
                _                            => false
            };

            if (hasWater && player.InLOS(item))
            {
                return item;
            }
        }

        return null;
    }

    private static Cow? MilkableCowNear(PlayerMobile player)
    {
        foreach (var m in player.GetMobilesInRange(FillRange))
        {
            if (m is Cow { Alive: true } cow && !(cow.Controlled && cow.ControlMaster != player) && !MilkedOut(cow.Milk, cow.MilkedOn, Core.Now) &&
                player.InLOS(cow))
            {
                return cow;
            }
        }

        return null;
    }

    /// <summary>A free wheel first, else a busy one (so the reason can say it is being used).</summary>
    private static ISpinningWheel? WheelNear(PlayerMobile player) =>
        (Nearby(player, SpinRange, static s => Wheel(s) is { Spinning: false }) ?? Nearby(player, SpinRange, static s => Wheel(s) is not null)) is { } station
            ? Wheel(station)
            : null;

    private static Item? LoomNear(PlayerMobile player) => Nearby(player, SpinRange, static s => Loom(s) is not null)?.Item;
}
