using System.Text.Json;
using Server;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Where the real dungeon entrances are, derived from the shard's own teleporter data: a teleporter standing
/// outside every dungeon whose destination is inside one. Used to put a pet back outside the dungeon it was in.
/// </summary>
public static class DungeonEntrances
{
    private static List<(Point3D Outside, Point3D Inside)>? _entries;

    /// <summary>The outside point of the entry whose inside destination is nearest to <paramref name="from"/>.</summary>
    public static bool TryNearest(IEnumerable<(Point3D Outside, Point3D Inside)> entries, Point3D from, out Point3D outside)
    {
        var best = long.MaxValue;
        outside = default;
        foreach (var (o, i) in entries)
        {
            long dx = i.X - from.X, dy = i.Y - from.Y;
            var distance = dx * dx + dy * dy;
            if (distance < best)
            {
                best = distance;
                outside = o;
            }
        }

        return best != long.MaxValue;
    }

    public static bool TryFindOutside(Map map, Point3D from, out Point3D outside)
    {
        _entries ??= Load(map);
        if (!TryNearest(_entries, from, out var entrance))
        {
            outside = default;
            return false;
        }

        outside = NearbyOpenSpot(map, entrance);
        return true;
    }

    private static List<(Point3D, Point3D)> Load(Map map)
    {
        var list = new List<(Point3D, Point3D)>();
        var path = Path.Combine(Core.BaseDirectory, "Data", "teleporters.json");
        if (!File.Exists(path))
        {
            return list;
        }

        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        foreach (var entry in doc.RootElement.EnumerateArray())
        {
            var src = entry.GetProperty("src");
            var dst = entry.GetProperty("dst");
            if (src.GetProperty("map").GetString() != map.Name || dst.GetProperty("map").GetString() != map.Name)
            {
                continue;
            }

            var s = ToPoint(src.GetProperty("loc"));
            var d = ToPoint(dst.GetProperty("loc"));
            if (!InDungeon(s, map) && InDungeon(d, map))
            {
                list.Add((s, d));
            }
        }

        return list;
    }

    private static Point3D ToPoint(JsonElement loc) => new(loc[0].GetInt32(), loc[1].GetInt32(), loc[2].GetInt32());

    private static bool InDungeon(Point3D p, Map map) => Region.Find(p, map).IsPartOf<DungeonRegion>();

    // Not on the teleporter tile itself, and never back inside a dungeon.
    private static Point3D NearbyOpenSpot(Map map, Point3D entrance)
    {
        for (var radius = 2; radius <= 4; radius++)
        {
            for (var dx = -radius; dx <= radius; dx++)
            {
                for (var dy = -radius; dy <= radius; dy++)
                {
                    var x = entrance.X + dx;
                    var y = entrance.Y + dy;
                    var candidate = new Point3D(x, y, map.GetAverageZ(x, y));
                    if (map.CanSpawnMobile(candidate) && !InDungeon(candidate, map))
                    {
                        return candidate;
                    }
                }
            }
        }

        return entrance;
    }
}
