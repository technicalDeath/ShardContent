using Server;
using Server.Items;
using Server.Logging;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Authoritative Hot Zone membership: the permanent outdoor polygons, and (behind <c>hythlothHotZone</c>) whole stock
/// dungeon regions listed in <c>hotZones.dungeonRegions</c>. Every other dungeon interior stays ordinary, including
/// dungeons whose entrances stand inside an outdoor Hot Zone. Every Hot rule (initiation, Knocked Out loot and Execute,
/// murder counts, the Ward and corpse-loot exemptions) asks this one check.
/// </summary>
public static class OutdoorHotZonePolicy
{
    private static readonly ILogger Logger = LogFactory.GetLogger(typeof(OutdoorHotZonePolicy));

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true;

    public static bool DungeonRegionsEnabled =>
        Enabled && ShardRulesConfiguration.Settings.FeatureFlags.HythlothHotZone;

    private static IReadOnlyList<HotZoneDungeonRegion> ActiveDungeonRegions =>
        DungeonRegionsEnabled ? ShardRulesConfiguration.Settings.HotZones.DungeonRegions : [];

    public static bool IsHot(Mobile mobile) => GetRegionName(mobile) is not null;

    public static bool ShareRegion(Mobile first, Mobile second)
    {
        var firstName = GetRegionName(first);
        return firstName is not null &&
               string.Equals(firstName, GetRegionName(second), StringComparison.OrdinalIgnoreCase);
    }

    public static string? GetRegionName(Mobile mobile) =>
        !Enabled ? null : FindHotRegionName(
            mobile.Map?.Name,
            mobile.X,
            mobile.Y,
            DungeonNameOf(mobile.Region),
            ShardRulesConfiguration.Settings.HotZones.PermanentOutdoorRegions,
            ActiveDungeonRegions
        );

    /// <summary>The stock dungeon region a region belongs to (the region itself or a parent), or null outside dungeons.</summary>
    private static string? DungeonNameOf(Region? region)
    {
        if (region?.GetRegion<DungeonRegion>() is not { } dungeon)
        {
            return null;
        }

        // A nameless dungeon region is still a dungeon: never Hot, but not outdoors either.
        return string.IsNullOrEmpty(dungeon.Name) ? string.Empty : dungeon.Name;
    }

    public static bool IsHot(Item item) => item.Map is not null && IsHot(item.Map, item.GetWorldLocation());

    /// <summary>Whether a point on a map is Hot, for places nobody stands yet (a tile a traveler would arrive on).</summary>
    public static bool IsHot(Map map, Point3D location)
    {
        if (!Enabled || map is null)
        {
            return false;
        }

        return FindHotRegionName(
            map.Name,
            location.X,
            location.Y,
            DungeonNameOf(Region.Find(location, map)),
            ShardRulesConfiguration.Settings.HotZones.PermanentOutdoorRegions,
            ActiveDungeonRegions
        ) is not null;
    }

    /// <summary>
    /// The Hot region at a point. Inside a stock dungeon (<paramref name="dungeonName"/> not null) only a listed dungeon
    /// region on the same map is Hot, and the whole region is; outdoors the permanent polygons decide.
    /// </summary>
    public static string? FindHotRegionName(
        string? mapName,
        int x,
        int y,
        string? dungeonName,
        IReadOnlyList<OutdoorHotRegionDefinition> outdoorRegions,
        IReadOnlyList<HotZoneDungeonRegion> dungeonRegions
    )
    {
        if (string.IsNullOrWhiteSpace(mapName))
        {
            return null;
        }

        if (dungeonName is not null)
        {
            foreach (var dungeon in dungeonRegions)
            {
                if (dungeonName.Length > 0 &&
                    string.Equals(dungeon.Name, dungeonName, StringComparison.OrdinalIgnoreCase) &&
                    string.Equals(dungeon.Map, mapName, StringComparison.OrdinalIgnoreCase))
                {
                    return dungeon.Name;
                }
            }

            return null;
        }

        return FindRegionName(mapName, x, y, false, outdoorRegions);
    }

    public static bool IsDungeonRegion(string? name) =>
        name is not null && ShardRulesConfiguration.Settings?.HotZones.DungeonRegions
            .Any(d => string.Equals(d.Name, name, StringComparison.OrdinalIgnoreCase)) == true;

    /// <summary>
    /// After startup: every listed dungeon region must exist as a stock dungeon region on its map. A misspelt name would
    /// otherwise make nothing Hot without any sign, so with the flag on the server stops.
    /// </summary>
    public static void ValidatePostBootDungeonRegions()
    {
        if (!DungeonRegionsEnabled)
        {
            return;
        }

        var missing = MissingDungeonRegions(
            ShardRulesConfiguration.Settings.HotZones.DungeonRegions,
            Region.Regions.OfType<DungeonRegion>().Select(r => (r.Name, r.Map?.Name))
        );

        if (missing.Count == 0)
        {
            Logger.Information("Validated Hot Zone dungeon regions: {Regions}.",
                string.Join(", ", ShardRulesConfiguration.Settings.HotZones.DungeonRegions.Select(d => $"{d.Name} ({d.Map})")));
            return;
        }

        Logger.Error("Hot Zone dungeon regions are not stock dungeon regions, so the server is stopping: {Missing}",
            string.Join(", ", missing));
        Core.Kill();
    }

    public static List<string> MissingDungeonRegions(
        IEnumerable<HotZoneDungeonRegion> configured, IEnumerable<(string? Name, string? Map)> existing
    )
    {
        var known = existing.ToList();
        return configured
            .Where(d => !known.Any(k =>
                string.Equals(k.Name, d.Name, StringComparison.OrdinalIgnoreCase) &&
                string.Equals(k.Map, d.Map, StringComparison.OrdinalIgnoreCase)))
            .Select(d => $"{d.Name} ({d.Map})")
            .ToList();
    }

    public static string? FindRegionName(
        string? mapName,
        int x,
        int y,
        bool insideDungeon,
        IReadOnlyList<OutdoorHotRegionDefinition> regions
    )
    {
        if (insideDungeon || string.IsNullOrWhiteSpace(mapName))
        {
            return null;
        }

        foreach (var region in regions)
        {
            if (string.Equals(region.Map, mapName, StringComparison.OrdinalIgnoreCase) &&
                TheftRegionPolicy.Contains(region.Points, x, y))
            {
                return region.Name;
            }
        }

        return null;
    }

    public static IEnumerable<string> Describe(Mobile mobile)
    {
        yield return $"Outdoor Hot Zones enabled: {Enabled}.";
        var regions = ShardRulesConfiguration.Settings?.HotZones.PermanentOutdoorRegions;
        yield return $"Permanent outdoor regions configured: {regions?.Count ?? 0}.";
        if (regions is not null)
        {
            foreach (var region in regions)
            {
                yield return $"{region.Name}: {region.Map}, {region.Points.Count} polygon points.";
            }
        }

        var dungeons = ShardRulesConfiguration.Settings?.HotZones.DungeonRegions;
        yield return $"Dungeon Hot Zones (hythlothHotZone): {DungeonRegionsEnabled}; configured: {(dungeons is { Count: > 0 } ? string.Join(", ", dungeons.Select(d => $"{d.Name} ({d.Map})")) : "none")}.";
        yield return $"Current location: {mobile.Map?.Name ?? "none"} ({mobile.X}, {mobile.Y}); stock region: {(string.IsNullOrEmpty(mobile.Region?.Name) ? "none" : mobile.Region.Name)}; Hot region: {GetRegionName(mobile) ?? "none"}.";
    }
}
