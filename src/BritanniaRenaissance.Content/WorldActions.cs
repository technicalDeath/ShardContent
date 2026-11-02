using System.Buffers;
using System.Text;
using Server;
using Server.Engines.Harvest;
using Server.Items;
using Server.Mobiles;
using Server.Network;
using Server.Targeting;
using Server.Targets;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Actions on a left click (owner, 2026-11-01: "every item that has an action that can be performed with it gives that action as a left click in a context
/// menu"; an action that cannot be done goes to the bottom with a tooltip saying why), behind <c>featureFlags.worldActions</c>. Map statics and ground
/// tiles have no serial, so the stock context menu cannot reach them; the client asks with extended command 0xB1 (mode 0, the tile's place, graphic and
/// whether it is ground), the server answers with the actions and, for each one that cannot be done, the reason, and the client shows them as a menu.
/// Choosing one sends mode 1 and the server does it the stock way, so skills, yields, messages and the gathering repeat are stock:
/// <list type="bullet">
/// <item>a tree: Chop wood (the axe goes into the hands first: "The axe must be equipped for any serious wood chopping") and Cut kindling (a knife or
/// sword, the stock bladed-item use);</item>
/// <item>mountainside, cave floor and cave rock: Mine (a pickaxe or shovel, carried or worn);</item>
/// <item>water: Fish (a fishing pole, carried or worn).</item>
/// </list>
/// The actions never walk the player (owner, 2026-11-01): too far is a reason, not a path.
/// </summary>
public static partial class WorldActions
{
    public const int Command = 0xB1;
    public const byte Ask = 0;
    public const byte Do = 1;

    public const byte ChopId = 1;
    public const byte KindlingId = 2;
    public const byte MineId = 3;
    public const byte FishId = 4;

    public const string ChopLabel = "Chop wood";
    public const string KindlingLabel = "Cut kindling";
    public const string MineLabel = "Mine";
    public const string FishLabel = "Fish";

    public const string NoAxe = "Requires an axe.";
    public const string NoBlade = "Requires a knife, dagger or sword.";
    public const string NoMiningTool = "Requires a pickaxe or shovel.";
    public const string NoPole = "Requires a fishing pole.";

    public const string TooFar = "Too far away. Stand next to the tree.";
    public const string TooFarToMine = "Too far away. Stand next to where you want to dig.";
    public const string TooFarToFish = "Too far away. Stand within 4 tiles of the water.";

    public const string MountedMining = "You can't mine while riding.";
    public const string MountedFishing = "You can't fish while riding.";

    public const string NoWood = "There's not enough wood here to harvest.";
    public const string NoMetal = "There is no metal here to mine.";
    public const string NoFish = "The fish aren't biting here. Try water at least 8 tiles away.";


    /// <summary>A knife or sword takes this much wood from the tree for one Kindling (BladedItemTarget).</summary>
    public const int WoodPerKindling = 5;

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.WorldActions == true;

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        IncomingExtendedCommandPackets.RegisterExtended(Command, true, &OnRequest);
        ConfigureItemMenu();
        ConfigureMobileMenu();
    }

    /// <summary>One action for the menu: its id, its text, and why it cannot be done (null when it can).</summary>
    public readonly record struct WorldAction(byte Id, string Label, string? Reason)
    {
        public bool Available => Reason is null;
    }

    /// <summary>The clicked place resolved to what the engine harvests: its location, tile id and whether it is ground.</summary>
    private readonly record struct Spot(Point3D Location, int TileId, bool IsLand)
    {
        public object Target(Map map) => IsLand ? new LandTarget(Location, map) : new StaticTarget(Location, TileId);
    }

    // ---- the reasons, in the order a player would fix them: the tool first, then the mount, then getting close, then a place with something left

    public static string? ChopReason(bool hasAxe, bool inRange, bool woodLeft) =>
        !hasAxe ? NoAxe : !inRange ? TooFar : !woodLeft ? NoWood : null;

    public static string? KindlingReason(bool hasBlade, bool inRange, bool woodLeft) =>
        !hasBlade ? NoBlade : !inRange ? TooFar : !woodLeft ? NoWood : null;

    public static string? MineReason(bool hasTool, bool mounted, bool inRange, bool oreLeft) =>
        !hasTool ? NoMiningTool : mounted ? MountedMining : !inRange ? TooFarToMine : !oreLeft ? NoMetal : null;

    public static string? FishReason(bool hasPole, bool mounted, bool inRange, bool fishLeft) =>
        !hasPole ? NoPole : mounted ? MountedFishing : !inRange ? TooFarToFish : !fishLeft ? NoFish : null;

    // ---- the tools: one in the hands first, then the first in the pack

    /// <summary>
    /// The axe a chop would use: an axe or a pole arm (BasePoleArm chops as an axe does, wave 5). A pickaxe mines and a war axe harvests nothing, so neither
    /// counts.
    /// </summary>
    public static Item? FindAxe(Mobile m) =>
        Held(m) is { } held && IsChopper(held) ? held : m.Backpack?.FindItemByType<Item>(predicate: static item => IsChopper(item));

    public static bool IsChopper(Item item) => item is BaseAxe { HarvestSystem: Lumberjacking } or BasePoleArm { HarvestSystem: Lumberjacking };

    /// <summary>A pickaxe or a shovel: either mines from the pack or the hands.</summary>
    public static Item? FindMiningTool(Mobile m) =>
        Held(m) is { } held && IsMiningTool(held) ? held : m.Backpack?.FindItemByType<Item>(predicate: static item => IsMiningTool(item));

    public static FishingPole? FindPole(Mobile m) => Held(m) as FishingPole ?? m.Backpack?.FindItemByType<FishingPole>();

    private static bool IsMiningTool(Item item) => item is BaseAxe { HarvestSystem: Mining } or BaseHarvestTool { HarvestSystem: Mining };

    private static Item? Held(Mobile m) => m.FindItemOnLayer(Layer.TwoHanded) ?? m.FindItemOnLayer(Layer.OneHanded);

    // ---- the request

    private static void OnRequest(NetState state, SpanReader reader)
    {
        if (!Enabled || state.Mobile is not PlayerMobile { Alive: true, Deleted: false } player || reader.Remaining < 9)
        {
            return;
        }

        int x = reader.ReadUInt16();
        int y = reader.ReadUInt16();
        int z = reader.ReadSByte();
        int graphic = reader.ReadUInt16();
        var mode = reader.ReadByte();
        var action = reader.Remaining > 0 ? reader.ReadByte() : (byte)0;
        var isLand = reader.Remaining > 0 && reader.ReadByte() != 0;

        if (player.Map is not { } map || map == Map.Internal)
        {
            return;
        }

        if (mode == Do)
        {
            Perform(player, map, x, y, z, graphic, isLand, action);
            return;
        }

        state.Send(Reply(x, y, graphic, ActionsFor(player, map, x, y, z, graphic, isLand)));
    }

    private static List<WorldAction> ActionsFor(PlayerMobile player, Map map, int x, int y, int z, int graphic, bool isLand)
    {
        var actions = new List<WorldAction>();

        if (FindTree(map, x, y, z, graphic, isLand) is { } tree)
        {
            actions.Add(new WorldAction(ChopId, ChopLabel, ChopReason(player, tree)));
            actions.Add(new WorldAction(KindlingId, KindlingLabel, KindlingReason(player, tree)));
        }

        if (FindOre(map, x, y, z, graphic, isLand) is { } ore)
        {
            actions.Add(new WorldAction(MineId, MineLabel, MineReason(player, ore)));
        }

        if (FindWater(map, x, y, z, graphic, isLand) is { } water)
        {
            actions.Add(new WorldAction(FishId, FishLabel, FishReason(player, water)));
        }

        // an oven, fireplace, forge or anvil built into the map
        if (!isLand && StaticStation(map, x, y, z, graphic) is { } station)
        {
            AddStationActions(player, station, actions);
        }

        return actions;
    }

    private static void Perform(PlayerMobile player, Map map, int x, int y, int z, int graphic, bool isLand, byte action)
    {
        switch (action)
        {
            case ChopId when FindTree(map, x, y, z, graphic, isLand) is { } tree:
                {
                    Chop(player, tree);
                    break;
                }
            case KindlingId when FindTree(map, x, y, z, graphic, isLand) is { } tree:
                {
                    // the stock bladed-item use has no direct method: answer its cursor, which runs the range check and gives the Kindling
                    if (!Refused(player, KindlingReason(player, tree)))
                    {
                        new BladedItemTarget(CorpseCarveButton.FindBlade(player)!).Invoke(player, tree.Target(map));
                    }

                    break;
                }
            case MineId when FindOre(map, x, y, z, graphic, isLand) is { } ore:
                {
                    if (!Refused(player, MineReason(player, ore)))
                    {
                        Mining.System.StartHarvesting(player, FindMiningTool(player), ore.Target(map));
                    }

                    break;
                }
            case FishId when FindWater(map, x, y, z, graphic, isLand) is { } water:
                {
                    if (!Refused(player, FishReason(player, water)))
                    {
                        Fishing.System.StartHarvesting(player, FindPole(player), water.Target(map));
                    }

                    break;
                }
            case >= SmeltId when !isLand && StaticStation(map, x, y, z, graphic) is { } station:
                {
                    PerformStation(player, station, action);
                    break;
                }
        }
    }

    private static bool Refused(PlayerMobile player, string? reason)
    {
        if (reason is null)
        {
            return false;
        }

        player.SendMessage(reason);
        return true;
    }

    // ---- what was clicked; nothing counts unless the client's tile is really there

    /// <summary>
    /// The tree the clicked static belongs to: the static itself when Lumberjacking takes it, else one on the same tile (a tree is a trunk and leaves).
    /// </summary>
    private static Spot? FindTree(Map map, int x, int y, int z, int graphic, bool isLand)
    {
        if (isLand)
        {
            return null;
        }

        var clicked = false;
        Spot? tree = null;

        foreach (var tile in map.Tiles.GetStaticTiles(x, y))
        {
            if (tile.ID == graphic && tile.Z == z)
            {
                clicked = true;
            }

            if (Lumberjacking.System.GetDefinition(tile.ID, false) is not null && (tree is null || tile.ID == graphic))
            {
                tree = new Spot(new Point3D(x, y, tile.Z), tile.ID, false);
            }
        }

        return clicked ? tree : null;
    }

    /// <summary>Mountainside or cave floor (ground) or cave rock (static) that Mining takes for ore. Sand needs a Mining book and stays off the menu.</summary>
    private static Spot? FindOre(Map map, int x, int y, int z, int graphic, bool isLand) =>
        Clicked(map, x, y, z, graphic, isLand) is { } spot && Mining.System.OreAndStone.Validate(spot.TileId, spot.IsLand) ? spot : null;

    private static Spot? FindWater(Map map, int x, int y, int z, int graphic, bool isLand) =>
        Clicked(map, x, y, z, graphic, isLand) is { } spot && Fishing.System.GetDefinition(spot.TileId, spot.IsLand) is not null ? spot : null;

    private static Spot? Clicked(Map map, int x, int y, int z, int graphic, bool isLand)
    {
        if (isLand)
        {
            // the client draws ground at a smoothed height, so only the tile id has to match
            var land = map.Tiles.GetLandTile(x, y);

            return land.ID == graphic ? new Spot(new Point3D(x, y, land.Z), land.ID, true) : null;
        }

        foreach (var tile in map.Tiles.GetStaticTiles(x, y))
        {
            if (tile.ID == graphic && tile.Z == z)
            {
                return new Spot(new Point3D(x, y, z), graphic, false);
            }
        }

        return null;
    }

    // ---- each action's state

    private static bool HasResources(HarvestDefinition def, Map map, Point3D loc, int needed) => def.GetBank(map, loc.X, loc.Y)?.Current >= needed;

    private static string? ChopReason(PlayerMobile player, Spot tree)
    {
        var def = Lumberjacking.System.GetDefinition(tree.TileId, false);

        return ChopReason(
            FindAxe(player) is not null, player.InRange(tree.Location, def.MaxRange), HasResources(def, player.Map, tree.Location, def.ConsumedPerHarvest)
        );
    }

    private static string? KindlingReason(PlayerMobile player, Spot tree)
    {
        var def = Lumberjacking.System.GetDefinition(tree.TileId, false);

        // the bladed-item cursor reaches 2 tiles
        return KindlingReason(
            CorpseCarveButton.FindBlade(player) is not null, player.InRange(tree.Location, 2), HasResources(def, player.Map, tree.Location, WoodPerKindling)
        );
    }

    private static string? MineReason(PlayerMobile player, Spot ore)
    {
        var def = Mining.System.OreAndStone;

        return MineReason(
            FindMiningTool(player) is not null, player.Mounted, player.InRange(ore.Location, def.MaxRange),
            HasResources(def, player.Map, ore.Location, def.ConsumedPerHarvest)
        );
    }

    private static string? FishReason(PlayerMobile player, Spot water)
    {
        var def = Fishing.System.GetDefinition(water.TileId, water.IsLand);
        var fishLeft = HasResources(def, player.Map, water.Location, def.ConsumedPerHarvest) || NearOwnSos(player);

        return FishReason(FindPole(player) is not null, player.Mounted, player.InRange(water.Location, def.MaxRange), fishLeft);
    }

    /// <summary>Stock fishing ignores an empty bank within 60 tiles of the target of an SOS the player carries (Fishing.CheckResources).</summary>
    private static bool NearOwnSos(PlayerMobile player) =>
        player.Backpack?.FindItemByType<SOS>(predicate: sos => player.Map == sos.TargetMap && player.InRange(sos.TargetLocation, 60)) is not null;

    private static void Chop(PlayerMobile player, Spot tree)
    {
        if (Refused(player, ChopReason(player, tree)))
        {
            return;
        }

        var axe = FindAxe(player)!;

        if (axe.Parent != player && !TakeUp(player, axe))
        {
            return;
        }

        Lumberjacking.System.StartHarvesting(player, axe, tree.Target(player.Map));
    }

    /// <summary>Puts a tool or wand in the hands as a player would: whatever is in the way goes into the pack first.</summary>
    private static bool TakeUp(PlayerMobile player, Item item) => Equip(player, item);

    // ---- the answer

    /// <summary>
    /// 0xBF, the length, the command, the tile's x, y and graphic, the number of actions, then for each its id, 1 when it can be done, and its text and
    /// reason as a length byte and UTF-8.
    /// </summary>
    public static byte[] Reply(int x, int y, int graphic, IReadOnlyList<WorldAction> actions)
    {
        var bytes = new List<byte>
        {
            0xBF, 0, 0, Command >> 8, Command & 0xFF, (byte)(x >> 8), (byte)x, (byte)(y >> 8), (byte)y, (byte)(graphic >> 8), (byte)graphic,
            (byte)actions.Count
        };

        foreach (var action in actions)
        {
            bytes.Add(action.Id);
            bytes.Add(action.Available ? (byte)1 : (byte)0);
            AddText(bytes, action.Label);
            AddText(bytes, action.Reason ?? "");
        }

        bytes[1] = (byte)(bytes.Count >> 8);
        bytes[2] = (byte)bytes.Count;

        return bytes.ToArray();
    }

    private static void AddText(List<byte> bytes, string text)
    {
        var encoded = Encoding.UTF8.GetBytes(text);
        var length = Math.Min(encoded.Length, 255);

        bytes.Add((byte)length);

        for (var i = 0; i < length; i++)
        {
            bytes.Add(encoded[i]);
        }
    }
}
