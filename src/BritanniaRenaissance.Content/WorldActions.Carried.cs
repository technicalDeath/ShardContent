using Server;
using Server.Collections;
using Server.ContextMenus;
using Server.Items;
using Server.Mobiles;
using Server.Regions;
using Server.Targeting;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 3 of the left-click actions (owner, 2026-11-01: "Yes to items in backpack", then "you can work on wave 3 now"): the things a player carries, and
/// locks. A bandage heals yourself or someone; a heal, cure, refresh or other drinkable potion is drunk; food is eaten (the stock Eat entry, greyed when
/// full); kindling lights or feeds a fire; something scissors cut is cut; ore is smelted and raw food cooked when a forge or fire is close; a locked
/// container or door is unlocked with its key or picked with a lockpick, and locked again with its key. Each runs the stock use of the item, so every stock
/// rule and message applies; the menu only says in advance what the stock use would refuse.
/// </summary>
public static partial class WorldActions
{
    public const byte HealSelfId = 40;
    public const byte HealOtherId = 41;
    public const byte DrinkId = 42;
    public const byte LightFireId = 43;
    public const byte FeedFireId = 44;
    public const byte CutId = 45;
    public const byte SmeltHereId = 46;
    public const byte CookHereId = 47;
    public const byte UnlockId = 48;
    public const byte LockId = 49;
    public const byte PickLockId = 50;

    public const string NotHurt = "You are not hurt.";
    public const string FullHealth = "You are already at full health.";
    public const string PoisonedNoHeal = "You are poisoned. Cure the poison first.";
    public const string HealPotionWait = "You must wait 10 seconds before drinking another heal potion.";
    public const string NotPoisoned = "You are not poisoned.";
    public const string FullStamina = "You are already at full stamina.";
    public const string NoFreeHand = "You must have a free hand to drink a potion.";
    public const string TooFull = "You are simply too full to eat any more!";
    public const string NoFireInDungeon = "You cannot light a fire in a dungeon.";
    public const string NoScissors = "Requires scissors.";
    public const string NoForgeClose = "Needs a forge within 2 tiles.";
    public const string NoFireClose = "Needs a fire, oven or forge next to you.";
    public const string NoKey = "Requires its key.";
    public const string NoLockpick = "Requires a lockpick.";
    public const string CannotPick = "That lock can't be picked.";
    public const string LockBeyondSkill = "This lock is beyond your Lockpicking skill.";
    public const string TooFarFromLock = "Too far away. Stand next to it.";

    /// <summary>What a heal potion would refuse, in the stock order (BaseHealPotion.CanDrink), with the free hand last.</summary>
    public static string? HealPotionReason(bool fullHealth, bool poisoned, bool waiting, bool freeHand) =>
        fullHealth ? FullHealth : poisoned ? PoisonedNoHeal : waiting ? HealPotionWait : !freeHand ? NoFreeHand : null;

    public static string? CurePotionReason(bool poisoned, bool freeHand) => !poisoned ? NotPoisoned : !freeHand ? NoFreeHand : null;

    public static string? RefreshPotionReason(bool fullStamina, bool freeHand) => fullStamina ? FullStamina : !freeHand ? NoFreeHand : null;

    public static string? PickReason(bool hasLockpick, bool pickable, bool skillEnough, bool inRange) =>
        !hasLockpick ? NoLockpick : !pickable ? CannotPick : !skillEnough ? LockBeyondSkill : !inRange ? TooFarFromLock : null;

    public static string? KeyReason(bool hasKey, bool inRange) => !hasKey ? NoKey : !inRange ? TooFarFromLock : null;

    // ---- what a carried item or a lock offers

    private static List<WorldAction> ItemActions(PlayerMobile player, Item item)
    {
        var actions = new List<WorldAction>();

        if (item.Parent is null)
        {
            AddStationActions(player, ItemStation(item), actions);
        }

        var carried = item.IsChildOf(player.Backpack);

        if (carried)
        {
            AddCarriedActions(player, item, actions);
        }

        if (carried || item.Parent == player)
        {
            AddToolActions(player, item, actions);
            AddMagicActions(player, item, actions);
        }

        AddGearActions(player, item, actions);
        AddMiscActions(player, item, actions);
        AddEverydayActions(player, item, actions);

        if (item is ILockable lockable)
        {
            AddLockActions(player, item, lockable, actions);
        }

        return actions;
    }

    private static void AddCarriedActions(PlayerMobile player, Item item, List<WorldAction> actions)
    {
        switch (item)
        {
            case Bandage:
                {
                    var hurt = player.Hits < player.HitsMax || player.Poisoned;
                    actions.Add(new WorldAction(HealSelfId, "Heal yourself", hurt ? null : NotHurt));
                    actions.Add(new WorldAction(HealOtherId, "Heal someone", null));
                    break;
                }
            case BasePotion potion when DrinkReason(player, potion) is { } reason:
                {
                    actions.Add(new WorldAction(DrinkId, "Drink", reason.Length == 0 ? null : reason));
                    break;
                }
            case Kindling:
                {
                    if (NearbyCampfire(player) is not null)
                    {
                        actions.Add(new WorldAction(FeedFireId, "Feed the fire", null));
                    }
                    else
                    {
                        actions.Add(new WorldAction(LightFireId, "Light a fire", player.Region.IsPartOf<DungeonRegion>() ? NoFireInDungeon : null));
                    }

                    break;
                }
            case BaseOre ore:
                {
                    var reason = !CanSmelt(OreDifficulty(ore.Resource), player.Skills.Mining.Value) ? NoSmeltSkill :
                        Nearby(player, 2, IsForge) is null ? NoForgeClose : null;
                    actions.Add(new WorldAction(SmeltHereId, SmeltLabel, reason));
                    break;
                }
            case CookableFood:
                {
                    actions.Add(new WorldAction(CookHereId, CookLabel, Nearby(player, 1, static s => CookableFood.IsHeatSource(s.Target)) is null ? NoFireClose : null));
                    break;
                }
        }

        if (item is IScissorable && item is not Scissors)
        {
            actions.Add(new WorldAction(CutId, "Cut with scissors", FindScissors(player) is null ? NoScissors : null));
        }
    }

    /// <summary>"" when the potion can be drunk now, the reason when not, null for a potion that is not for drinking (thrown, or poison).</summary>
    private static string? DrinkReason(PlayerMobile player, BasePotion potion)
    {
        var freeHand = !potion.RequireFreeHand || BasePotion.HasFreeHand(player);

        var reason = potion switch
        {
            _ when potion.IsThrowablePotion => null,
            BasePoisonPotion => null,
            BaseHealPotion => HealPotionReason(player.Hits >= player.HitsMax, player.Poisoned, !player.CanBeginAction<BaseHealPotion>(), freeHand) ?? "",
            BaseCurePotion => CurePotionReason(player.Poisoned, freeHand) ?? "",
            BaseRefreshPotion => RefreshPotionReason(player.Stam >= player.StamMax, freeHand) ?? "",
            _ => freeHand ? "" : NoFreeHand
        };

        return reason;
    }

    private static void AddLockActions(PlayerMobile player, Item item, ILockable lockable, List<WorldAction> actions)
    {
        // a key reaches 3 tiles and a lockpick 1 (Key, LockPick)
        var hasKey = lockable.KeyValue != 0 && FindKey(player, lockable.KeyValue) is not null;
        var location = item.GetWorldLocation();

        if (lockable.Locked)
        {
            actions.Add(new WorldAction(UnlockId, "Unlock", KeyReason(hasKey, player.InRange(location, 3))));

            if (item is ILockpickable pickable)
            {
                var canPick = pickable.LockLevel is not (ILockpickable.CannotPick or ILockpickable.MagicLock);
                var reason = PickReason(
                    FindLockpick(player) is not null, canPick, player.Skills.Lockpicking.Value >= pickable.RequiredSkill, player.InRange(location, 1)
                );
                actions.Add(new WorldAction(PickLockId, "Pick the lock", reason));
            }
        }
        else if (hasKey)
        {
            actions.Add(new WorldAction(LockId, "Lock", KeyReason(true, player.InRange(location, 3))));
        }
    }

    // ---- doing them

    private static void PerformItem(PlayerMobile player, Item item, byte action)
    {
        // the menu may be stale: the action must still be offered, and its reason is said if it cannot be done now
        WorldAction? chosen = null;

        foreach (var a in ItemActions(player, item))
        {
            if (a.Id == action)
            {
                chosen = a;
            }
        }

        if (chosen is not { } offered || Refused(player, offered.Reason))
        {
            return;
        }

        if (action >= CraftId && (PerformTool(player, item, action) || PerformGear(player, item, action) || PerformMagic(player, item, action) ||
                                  PerformMisc(player, item, action) || PerformEveryday(player, item, action)))
        {
            return;
        }

        switch (action)
        {
            case < HealSelfId:
                {
                    PerformStation(player, ItemStation(item), action);
                    break;
                }
            case HealSelfId:
                {
                    Bandage.BandageTargetRequest(player, item, player);
                    break;
                }
            case HealOtherId or DrinkId or LightFireId or FeedFireId:
                {
                    // the stock use: the bandage asks whom to heal, the potion is drunk, the kindling lights or feeds the fire
                    item.OnDoubleClick(player);
                    break;
                }
            case CutId:
                {
                    Use(player, FindScissors(player), item);
                    break;
                }
            case SmeltHereId:
                {
                    Use(player, item, Nearby(player, 2, IsForge)?.Target);
                    break;
                }
            case CookHereId:
                {
                    Use(player, item, Nearby(player, 1, static s => CookableFood.IsHeatSource(s.Target))?.Target);
                    break;
                }
            case UnlockId or LockId:
                {
                    Use(player, FindKey(player, ((ILockable)item).KeyValue), item);
                    break;
                }
            case PickLockId:
                {
                    Use(player, FindLockpick(player), item);
                    break;
                }
        }
    }

    // ---- finding things

    private static Scissors? FindScissors(PlayerMobile player) => player.Backpack?.FindItemByType<Scissors>();

    private static Lockpick? FindLockpick(PlayerMobile player) => player.Backpack?.FindItemByType<Lockpick>();

    /// <summary>A key for this lock in the pack, or a key ring holding one.</summary>
    private static Item? FindKey(PlayerMobile player, uint keyValue) =>
        player.Backpack?.FindItemByType<Key>(predicate: key => key.KeyValue == keyValue) ??
        (Item?)player.Backpack?.FindItemByType<KeyRing>(predicate: ring => ring.ContainsKey(keyValue));

    private static Campfire? NearbyCampfire(PlayerMobile player)
    {
        foreach (var fire in player.Map.GetItemsInRange<Campfire>(player.Location, 1))
        {
            return fire;
        }

        return null;
    }

    /// <summary>A workstation within reach: an item first, then a static built into the map.</summary>
    private static Station? Nearby(PlayerMobile player, int range, Func<Station, bool> test)
    {
        var map = player.Map;

        if (map is null || map == Map.Internal)
        {
            return null;
        }

        foreach (var item in map.GetItemsInRange(player.Location, range))
        {
            if (item.Parent is null && test(ItemStation(item)))
            {
                return ItemStation(item);
            }
        }

        for (var x = player.X - range; x <= player.X + range; x++)
        {
            for (var y = player.Y - range; y <= player.Y + range; y++)
            {
                foreach (var tile in map.Tiles.GetStaticTiles(x, y))
                {
                    var location = new Point3D(x, y, tile.Z);
                    var station = new Station(new StaticTarget(location, tile.ID), location, null, tile.ID);

                    if (test(station))
                    {
                        return station;
                    }
                }
            }
        }

        return null;
    }

    // ---- the stock Eat entry: greyed when the player is too full

    private static void AdjustStockEntries(PlayerMobile player, Item item, ref PooledRefList<ContextMenuEntry> list, List<(int Index, WorldAction Action)> texts)
    {
        AdjustTreasureMapEntries(player, item, ref list, texts);

        for (var i = 0; i < list.Count; i++)
        {
            if (list[i] is EatEntry eat && player.Hunger >= 20)
            {
                eat.Enabled = false;
                texts.Add((i, new WorldAction(0, "Eat", TooFull)));
            }
        }
    }
}
