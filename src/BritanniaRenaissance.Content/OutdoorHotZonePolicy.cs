using Server;
using Server.Items;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>Authoritative outdoor Hot membership; dungeon interiors remain ordinary until Beta 2.</summary>
public static class OutdoorHotZonePolicy
{
    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.HotZones == true;

    public static bool IsHot(Mobile mobile) => GetRegionName(mobile) is not null;

    public static bool ShareRegion(Mobile first, Mobile second)
    {
        var firstName = GetRegionName(first);
        return firstName is not null &&
               string.Equals(firstName, GetRegionName(second), StringComparison.OrdinalIgnoreCase);
    }

    public static string? GetRegionName(Mobile mobile) =>
        !Enabled ? null : FindRegionName(
            mobile.Map?.Name,
            mobile.X,
            mobile.Y,
            mobile.Region.IsPartOf<DungeonRegion>(),
            ShardRulesConfiguration.Settings.HotZones.PermanentOutdoorRegions
        );

    public static bool IsHot(Item item)
    {
        if (!Enabled || item.Map is null)
        {
            return false;
        }

        var location = item.GetWorldLocation();
        return FindRegionName(
            item.Map.Name,
            location.X,
            location.Y,
            Region.Find(location, item.Map).IsPartOf<DungeonRegion>(),
            ShardRulesConfiguration.Settings.HotZones.PermanentOutdoorRegions
        ) is not null;
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

        yield return $"Current location: {mobile.Map?.Name ?? "none"} ({mobile.X}, {mobile.Y}); outdoor Hot region: {GetRegionName(mobile) ?? "none"}.";
    }
}
