using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Data-driven theft-region checks. Empty polygon lists intentionally disable region rules.</summary>
public static class TheftRegionPolicy
{
    public static bool IsBankProtectionRegion(Mobile mobile) =>
        IsWithin(mobile, ShardRulesConfiguration.Settings?.TheftRegions.BankProtectionPolygons);

    public static bool IsBankProtectionRegion(string? mapName, int x, int y) =>
        IsWithin(mapName, x, y, ShardRulesConfiguration.Settings?.TheftRegions.BankProtectionPolygons);

    public static bool IsBankProtectionRegionForEither(Mobile first, Mobile second) =>
        IsWithinEither(first.Map?.Name, first.X, first.Y, second.Map?.Name, second.X, second.Y,
            ShardRulesConfiguration.Settings?.TheftRegions.BankProtectionPolygons);

    public static bool IsCoolDungeonRegion(Mobile mobile) =>
        IsCoolDungeonRegion(
            mobile.Map?.Name, mobile.X, mobile.Y,
            ShardRulesConfiguration.Settings?.FeatureFlags.CoolZones == true,
            ShardRulesConfiguration.Settings?.TheftRegions.CoolDungeonPolygons
        );

    public static bool IsCoolDungeonRegionForEither(Mobile first, Mobile second) =>
        ShardRulesConfiguration.Settings?.FeatureFlags.CoolZones == true &&
        IsWithinEither(first.Map?.Name, first.X, first.Y, second.Map?.Name, second.X, second.Y,
            ShardRulesConfiguration.Settings.TheftRegions.CoolDungeonPolygons);

    public static bool IsCoolDungeonRegion(
        string? mapName, int x, int y, bool coolZonesEnabled,
        IReadOnlyList<TheftPolygonDefinition>? polygons
    ) => coolZonesEnabled && IsWithin(mapName, x, y, polygons);

    public static bool IsWithinEither(
        string? firstMap,
        int firstX,
        int firstY,
        string? secondMap,
        int secondX,
        int secondY,
        IReadOnlyList<TheftPolygonDefinition>? polygons
    ) => IsWithin(firstMap, firstX, firstY, polygons) || IsWithin(secondMap, secondX, secondY, polygons);

    public static bool IsWithin(Mobile mobile, IReadOnlyList<TheftPolygonDefinition>? polygons)
        => IsWithin(mobile.Map?.Name, mobile.X, mobile.Y, polygons);

    public static bool IsWithin(
        string? mapName,
        int x,
        int y,
        IReadOnlyList<TheftPolygonDefinition>? polygons
    )
    {
        if (string.IsNullOrWhiteSpace(mapName) || polygons is null)
        {
            return false;
        }

        foreach (var polygon in polygons)
        {
            if (!string.Equals(polygon.Map, mapName, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (Contains(polygon.Points, x, y))
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
        yield return $"Cool Dungeon candidate polygons configured: {rules?.CoolDungeonPolygons.Count ?? 0}; Beta 2 rule enabled: {ShardRulesConfiguration.Settings?.FeatureFlags.CoolZones == true}.";
    }
}
