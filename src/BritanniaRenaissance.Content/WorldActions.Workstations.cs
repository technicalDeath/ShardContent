using Server;
using Server.Collections;
using Server.ContextMenus;
using Server.Engines.Craft;
using Server.Items;
using Server.Mobiles;
using Server.Network;
using Server.Targeting;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Wave 2 of the left-click actions (owner, 2026-11-01: "go ahead and do wave 2"): workstations. A forge smelts ore, an anvil with a forge near opens the
/// smithing menu, a fire, oven or forge cooks each kind of raw food carried, a spinning wheel spins wool, cotton or flax, and a loom weaves yarn or thread.
/// Britain's workstations are items (forges, anvils, ovens, wheels and looms are placed as items and addons), so their actions go into the stock context menu
/// that a left click already opens, and the labels and reasons travel beside it in command 0xB2 for the client to show; a workstation that is a map static
/// (an oven or fireplace built into the map) uses the 0xB1 menu. Each action runs the stock use of the material or tool and answers its cursor with the
/// workstation, so every stock rule, skill check and message applies.
/// </summary>
public static partial class WorldActions
{
    public const int ItemTextsCommand = 0xB2;

    /// <summary>The client text the shard's menu entries carry until the client puts in the label from 0xB2 ("Action", data/client/Clilocs.txt).</summary>
    public const int EntryNumber = 3050003;

    public const byte SmeltId = 5;
    public const byte SmithId = 6;
    public const byte WeaveId = 7;
    public const byte SpinId = 9;
    public const byte SpinWoolId = 10;
    public const byte SpinCottonId = 11;
    public const byte SpinFlaxId = 12;
    public const byte CookId = 19;
    public const byte FirstCookKindId = 20;

    public const string SmeltLabel = "Smelt ore";
    public const string SmithLabel = "Smith";
    public const string CookLabel = "Cook";
    public const string SpinLabel = "Spin";
    public const string WeaveLabel = "Weave";

    public const string NoOre = "Requires ore.";
    public const string NoSmeltSkill = "You need more Mining to smelt this ore.";
    public const string TooFarFromForge = "Too far away. Stand next to the forge.";
    public const string NoSmithTool = "Requires a smith's hammer or tongs.";
    public const string TooFarFromAnvil = "Too far away. Stand next to the anvil.";
    public const string NoForgeNear = "You need a forge nearby as well.";
    public const string NoFood = "Requires raw food.";
    public const string TooFarFromFire = "Too far away. Stand next to the fire.";
    public const string NoFibre = "Requires wool, cotton or flax.";
    public const string WheelBusy = "That spinning wheel is being used.";
    public const string TooFarFromWheel = "Too far away. Stand next to the spinning wheel.";
    public const string NoYarn = "Requires yarn or thread.";
    public const string TooFarFromLoom = "Too far away. Stand next to the loom.";

    /// <summary>Each kind of raw food, in the menu's order, with what cooking it says. A menu entry's id is <see cref="FirstCookKindId"/> plus its place here.</summary>
    public static readonly (Type Type, string Label)[] CookKinds =
    [
        (typeof(RawRibs), "Cook raw ribs"),
        (typeof(RawLambLeg), "Cook a raw leg of lamb"),
        (typeof(RawChickenLeg), "Cook a raw chicken leg"),
        (typeof(RawBird), "Cook a raw bird"),
        (typeof(RawFishSteak), "Cook a raw fish steak"),
        (typeof(Eggs), "Fry eggs"),
        (typeof(UnbakedMeatPie), "Bake a meat pie"),
        (typeof(UnbakedFruitPie), "Bake a fruit pie"),
        (typeof(UnbakedApplePie), "Bake an apple pie"),
        (typeof(UnbakedPeachCobbler), "Bake a peach cobbler"),
        (typeof(UnbakedPumpkinPie), "Bake a pumpkin pie"),
        (typeof(UnbakedQuiche), "Bake a quiche"),
        (typeof(UncookedCheesePizza), "Bake a cheese pizza"),
        (typeof(UncookedSausagePizza), "Bake a sausage pizza"),
        (typeof(CookieMix), "Bake cookies"),
        (typeof(CakeMix), "Bake a cake")
    ];

    /// <summary>A clicked workstation: what a cursor would be answered with, where it is, and its art.</summary>
    private readonly record struct Station(object Target, Point3D Location, Item? Item, int ItemId);

    // ---- the reasons

    public static string? SmeltReason(bool hasOre, bool canSmeltAny, bool inRange) =>
        !hasOre ? NoOre : !canSmeltAny ? NoSmeltSkill : !inRange ? TooFarFromForge : null;

    public static string? SmithReason(bool hasTool, bool inRange, bool forgeNear) =>
        !hasTool ? NoSmithTool : !inRange ? TooFarFromAnvil : !forgeNear ? NoForgeNear : null;

    public static string? SpinReason(bool busy, bool inRange) => busy ? WheelBusy : !inRange ? TooFarFromWheel : null;

    public static string? WeaveReason(bool hasYarn, bool inRange) => !hasYarn ? NoYarn : !inRange ? TooFarFromLoom : null;

    /// <summary>How much Mining a pile of ore needs to be smelted (Ore.cs): iron any, the coloured ores from 65 (dull copper) to 99 (valorite).</summary>
    public static double OreDifficulty(CraftResource resource) =>
        resource switch
        {
            CraftResource.DullCopper => 65.0,
            CraftResource.ShadowIron => 70.0,
            CraftResource.Copper     => 75.0,
            CraftResource.Bronze     => 80.0,
            CraftResource.Gold       => 85.0,
            CraftResource.Agapite    => 90.0,
            CraftResource.Verite     => 95.0,
            CraftResource.Valorite   => 99.0,
            _                        => 50.0
        };

    public static bool CanSmelt(double difficulty, double mining) => difficulty <= 50.0 || mining >= difficulty;

    /// <summary>A cook entry's text: the kind and how many the player carries.</summary>
    public static string CookEntryLabel(int kind, int count) => $"{CookKinds[kind].Label} ({count})";

    // ---- what a workstation is (the same tests the stock code uses)

    private static bool IsForge(Station s) =>
        s.Item?.GetType().IsDefined(typeof(ForgeAttribute), false) == true || s.ItemId is 4017 or >= 6522 and <= 6569 or 11736;

    private static bool IsAnvil(Station s) =>
        s.Item?.GetType().IsDefined(typeof(AnvilAttribute), false) == true || s.ItemId is 4015 or 4016 or 11733 or 11734;

    private static ISpinningWheel? Wheel(Station s) => s.Item as ISpinningWheel ?? (s.Item as AddonComponent)?.Addon as ISpinningWheel;

    private static ILoom? Loom(Station s) => s.Item as ILoom ?? (s.Item as AddonComponent)?.Addon as ILoom;

    private static Station ItemStation(Item item) => new(item, item.GetWorldLocation(), item, item.ItemID);

    private static Station? StaticStation(Map map, int x, int y, int z, int graphic) =>
        Clicked(map, x, y, z, graphic, false) is { } spot ? new Station(new StaticTarget(spot.Location, spot.TileId), spot.Location, null, spot.TileId) : null;

    // ---- the actions a workstation offers

    private static void AddStationActions(PlayerMobile player, Station s, List<WorldAction> actions)
    {
        if (IsForge(s))
        {
            var hasOre = player.Backpack?.FindItemByType<BaseOre>() is not null;
            actions.Add(new WorldAction(SmeltId, SmeltLabel, SmeltReason(hasOre, SmeltableOre(player) is not null, player.InRange(s.Location, 2))));
        }

        if (IsAnvil(s))
        {
            DefBlacksmithy.CheckAnvilAndForge(player, 2, out _, out var forgeNear);
            actions.Add(new WorldAction(SmithId, SmithLabel, SmithReason(SmithTool(player) is not null, player.InRange(s.Location, 2), forgeNear)));
        }

        if (CookableFood.IsHeatSource(s.Target))
        {
            AddCookActions(player, s, actions);
        }

        if (Wheel(s) is { } wheel)
        {
            AddSpinActions(player, s, wheel, actions);
        }

        if (Loom(s) is not null)
        {
            var hasYarn = player.Backpack?.FindItemByType<BaseClothMaterial>() is not null;
            actions.Add(new WorldAction(WeaveId, WeaveLabel, WeaveReason(hasYarn, player.InRange(s.Location, 3))));
        }
    }

    private static void AddCookActions(PlayerMobile player, Station s, List<WorldAction> actions)
    {
        // the cooking cursor reaches 1 tile
        var reason = player.InRange(s.Location, 1) ? null : TooFarFromFire;
        var any = false;

        for (var kind = 0; kind < CookKinds.Length; kind++)
        {
            var count = Count(player, CookKinds[kind].Type);

            if (count > 0)
            {
                any = true;
                actions.Add(new WorldAction((byte)(FirstCookKindId + kind), CookEntryLabel(kind, count), reason));
            }
        }

        if (!any)
        {
            actions.Add(new WorldAction(CookId, CookLabel, NoFood));
        }
    }

    private static void AddSpinActions(PlayerMobile player, Station s, ISpinningWheel wheel, List<WorldAction> actions)
    {
        var reason = SpinReason(wheel.Spinning, player.InRange(s.Location, 3));
        var wool = Count(player, typeof(Wool));
        var cotton = Count(player, typeof(Cotton));
        var flax = Count(player, typeof(Flax));

        if (wool > 0)
        {
            actions.Add(new WorldAction(SpinWoolId, $"Spin wool ({wool})", reason));
        }

        if (cotton > 0)
        {
            actions.Add(new WorldAction(SpinCottonId, $"Spin cotton ({cotton})", reason));
        }

        if (flax > 0)
        {
            actions.Add(new WorldAction(SpinFlaxId, $"Spin flax ({flax})", reason));
        }

        if (wool + cotton + flax == 0)
        {
            actions.Add(new WorldAction(SpinId, SpinLabel, NoFibre));
        }
    }

    // ---- doing them

    private static void PerformStation(PlayerMobile player, Station s, byte action)
    {
        var actions = new List<WorldAction>();
        AddStationActions(player, s, actions);

        // the menu may be stale: the action must still be offered, and its reason is said if it cannot be done now
        WorldAction? chosen = null;

        foreach (var a in actions)
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

        switch (action)
        {
            case SmeltId:
                {
                    Use(player, SmeltableOre(player), s.Target);
                    break;
                }
            case SmithId:
                {
                    // the tool's own use opens the smithing menu, or (T2A menus) a cursor that any target answers to begin crafting
                    Use(player, SmithTool(player), s.Target);
                    break;
                }
            case WeaveId:
                {
                    Use(player, player.Backpack?.FindItemByType<BaseClothMaterial>(), s.Target);
                    break;
                }
            case SpinWoolId or SpinCottonId or SpinFlaxId when Wheel(s) is { } wheel:
                {
                    switch (action == SpinWoolId ? player.Backpack?.FindItemByType<Wool>() :
                            action == SpinCottonId ? player.Backpack?.FindItemByType<Cotton>() : (Item?)player.Backpack?.FindItemByType<Flax>())
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

                    break;
                }
            case >= FirstCookKindId when action - FirstCookKindId < CookKinds.Length:
                {
                    var type = CookKinds[action - FirstCookKindId].Type;
                    Use(player, player.Backpack?.FindItemByType<CookableFood>(predicate: food => food.GetType() == type), s.Target);
                    break;
                }
        }
    }

    /// <summary>Uses the material or tool as a double click would, then answers the cursor it raised with the workstation.</summary>
    private static void Use(PlayerMobile player, Item? item, object? workstation)
    {
        if (item is null || workstation is null)
        {
            return;
        }

        item.OnDoubleClick(player);

        if (player.Target is not { } cursor)
        {
            return;
        }

        cursor.Invoke(player, workstation);

        // the cursor already went to the client: when it is used up here, take it back there too
        if (player.Target is null)
        {
            player.NetState?.SendCancelTarget();
        }
    }

    private static BaseOre? SmeltableOre(PlayerMobile player) =>
        player.Backpack?.FindItemByType<BaseOre>(predicate: ore => CanSmelt(OreDifficulty(ore.Resource), player.Skills.Mining.Value));

    private static BaseTool? SmithTool(PlayerMobile player) =>
        Held(player) is BaseTool held && held.CraftSystem == DefBlacksmithy.CraftSystem
            ? held
            : player.Backpack?.FindItemByType<BaseTool>(predicate: static tool => tool.CraftSystem == DefBlacksmithy.CraftSystem);

    private static int Count(PlayerMobile player, Type type) => player.Backpack?.GetAmount(type) ?? 0;

    // ---- the stock context menu of an item in the world

    private static void ConfigureItemMenu()
    {
        var previous = ContextMenuSystem.ItemEntriesHandler;
        ContextMenuSystem.ItemEntriesHandler = (Item item, Mobile from, ref PooledRefList<ContextMenuEntry> list) =>
        {
            AddItemEntries(item, from, ref list);
            previous?.Invoke(item, from, ref list);
        };
    }

    private static void AddItemEntries(Item item, Mobile from, ref PooledRefList<ContextMenuEntry> list)
    {
        if (!Enabled || from is not PlayerMobile { Alive: true } player || player.NetState is not { } state)
        {
            return;
        }

        var texts = new List<(int Index, WorldAction Action)>();
        AdjustStockEntries(player, item, ref list, texts);

        foreach (var action in ItemActions(player, item))
        {
            texts.Add((list.Count, action));
            list.Add(new ActionEntry(item, action.Id) { Enabled = action.Available });
        }

        if (texts.Count == 0)
        {
            return;
        }

        // sent before the menu itself, so the client has the labels and reasons when the menu arrives
        state.Send(ItemTexts(item.Serial.Value, texts));
    }

    private sealed class ActionEntry : ContextMenuEntry
    {
        private readonly Item _item;
        private readonly byte _action;

        public ActionEntry(Item item, byte action) : base(EntryNumber)
        {
            _item = item;
            _action = action;
        }

        public override void OnClick(Mobile from, IEntity target)
        {
            if (Enabled && from is PlayerMobile { Alive: true } player && !_item.Deleted && player.Map == _item.Map)
            {
                PerformItem(player, _item, _action);
            }
        }
    }

    /// <summary>
    /// 0xBF, the length, the command 0xB2, the item's serial, the number of entries, then for each its place in the menu (2 bytes) and its text and reason
    /// as a length byte and UTF-8.
    /// </summary>
    public static byte[] ItemTexts(uint serial, IReadOnlyList<(int Index, WorldAction Action)> entries)
    {
        var bytes = new List<byte>
        {
            0xBF, 0, 0, ItemTextsCommand >> 8, ItemTextsCommand & 0xFF, (byte)(serial >> 24), (byte)(serial >> 16), (byte)(serial >> 8), (byte)serial,
            (byte)entries.Count
        };

        foreach (var (index, action) in entries)
        {
            bytes.Add((byte)(index >> 8));
            bytes.Add((byte)index);
            AddText(bytes, action.Label);
            AddText(bytes, action.Reason ?? "");
        }

        bytes[1] = (byte)(bytes.Count >> 8);
        bytes[2] = (byte)bytes.Count;

        return bytes.ToArray();
    }
}
