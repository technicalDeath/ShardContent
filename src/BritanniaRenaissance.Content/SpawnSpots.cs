using System;
using Server;
using Server.Engines.Spawners;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Where a spawner may put a creature, beyond the stock walkability check (owner, 2026-10-18: "there is a zombie that spawned on the roof of a
/// building in the brit graveyard"). Stock spawners take any walkable surface in range, and a flat roof is walkable, so a building inside a
/// spawner's range could get creatures on its roof. A spot standing on a roof is refused and the spawner draws another (falling back to its own
/// spot). Roof art is known by the tile data's Roof flag or its name: Britain's slate roofs are plain surfaces named "slate roof".
/// Chained onto <c>BaseSpawner.MobileSpawnPositionAllowed</c> at Initialize, after <see cref="TownGuardsService"/> sets it in Configure, so both rules apply.
/// </summary>
public static class SpawnSpots
{
    private static bool _initialized;

    // in Initialize, after every Configure (ModernUO's own discovery may call Configure methods in any order, and TownGuardsService
    // sets the hook with a plain assignment that would erase a chain made before it)
    public static void Initialize()
    {
        if (_initialized)
        {
            return;
        }

        _initialized = true;
        var previous = BaseSpawner.MobileSpawnPositionAllowed;
        BaseSpawner.MobileSpawnPositionAllowed = (spawner, m, map, spot) =>
            !OnRoof(map, spot) && (previous == null || previous(spawner, m, map, spot));
    }

    /// <summary>The spot stands on a roof tile: a static or multi surface whose top is the spot's height.</summary>
    public static bool OnRoof(Map map, Point3D spot)
    {
        if (map == null || map == Map.Internal)
        {
            return false;
        }

        foreach (var tile in map.Tiles.GetStaticAndMultiTiles(spot.X, spot.Y))
        {
            var id = TileData.ItemTable[tile.ID & TileData.MaxItemValue];

            if (id.Surface && tile.Z + id.CalcHeight == spot.Z && IsRoof(id.Name, (id.Flags & TileFlag.Roof) != 0))
            {
                return true;
            }
        }

        return false;
    }

    public static bool IsRoof(string name, bool roofFlag) =>
        roofFlag || name?.Contains("roof", StringComparison.OrdinalIgnoreCase) == true;
}
