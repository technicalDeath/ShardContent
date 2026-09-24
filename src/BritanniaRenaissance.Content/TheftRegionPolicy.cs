using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Data-driven theft-region checks. Empty polygon lists intentionally disable region rules.</summary>
public static class TheftRegionPolicy
{
    public static bool IsBankProtectionRegion(Mobile mobile) =>
        IsWithin(mobile, ShardRulesConfiguration.Settings?.TheftRegions.BankProtectionPolygons);

    public static bool IsCoolDungeonRegion(Mobile mobile) =>
        IsWithin(mobile, ShardRulesConfiguration.Settings?.TheftRegions.CoolDungeonPolygons);

    public static bool IsWithin(Mobile mobile, IReadOnlyList<TheftPolygonDefinition>? polygons)
    {
        if (mobile.Map is null || polygons is null)
        {
            return false;
        }

        foreach (var polygon in polygons)
        {
            if (!string.Equals(polygon.Map, mobile.Map.Name, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (Contains(polygon.Points, mobile.X, mobile.Y))
            {
                return true;
            }
        }

        return false;
    }

    public static bool Contains(IReadOnlyList<TheftPoint> points, int x, int y)
    {
        if (points is null || points.Count < 3)
        {
            return false;
        }

        var inside = false;
        for (var i = 0; i < points.Count; i++)
        {
            var current = points[i];
            var previous = points[(i + points.Count - 1) % points.Count];

            if (((current.Y > y) != (previous.Y > y)) &&
                x < (long)(previous.X - current.X) * (y - current.Y) / (previous.Y - current.Y) + current.X)
            {
                inside = !inside;
            }
        }

        return inside;
    }

    public static IEnumerable<string> Describe()
    {
        var rules = ShardRulesConfiguration.Settings?.TheftRegions;
        yield return $"Bank protection polygons configured: {rules?.BankProtectionPolygons.Count ?? 0}.";
        yield return $"Cool Dungeon polygons configured: {rules?.CoolDungeonPolygons.Count ?? 0}.";
    }
}
