using Server;
using Server.Multis;

namespace BritanniaRenaissance.Content;

/// <summary>Shard-owned geographic checks for every occupied house-placement tile.</summary>
public static class HousingGeographyPolicy
{
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        HousePlacement.PlacementTileAllowed = CanPlaceTile;
        HousePlacement.PlacementPremium = QuotePremium;
    }

    private static bool CanPlaceTile(Mobile from, Map map, Point3D point) =>
        ShardRulesConfiguration.Settings?.FeatureFlags.HousingGeography != true ||
        ClassifyTile(map.Name, point.X, point.Y,
            ShardRulesConfiguration.Settings.HotZones.PermanentOutdoorRegions,
            ShardRulesConfiguration.Settings.Housing) != HousingLandClass.Protected;

    private static int? QuotePremium(Mobile from, int multiID, Point3D center, int normalCost)
    {
        if (ShardRulesConfiguration.Settings?.FeatureFlags.HousingGeography != true ||
            from.AccessLevel >= AccessLevel.GameMaster)
        {
            return 0;
        }

        var map = from.Map;
        if (map is null || !string.Equals(map.Name, "Felucca", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        var regions = ShardRulesConfiguration.Settings.HotZones.PermanentOutdoorRegions;
        var housing = ShardRulesConfiguration.Settings.Housing;
        var landClass = ClassifyTile(map.Name, center.X, center.Y, regions, housing);
        if (landClass == HousingLandClass.Protected)
        {
            return null;
        }

        var components = MultiData.GetComponents(multiID);
        if (multiID >= 0x13EC && multiID < 0x1D00)
        {
            HouseFoundation.AddStairsTo(ref components);
        }

        for (var x = 0; x < components.Width; x++)
        {
            for (var y = 0; y < components.Height; y++)
            {
                if (components.Tiles[x][y].Length == 0)
                {
                    continue;
                }

                var tileClass = ClassifyTile(
                    map.Name, center.X + components.Min.X + x, center.Y + components.Min.Y + y, regions, housing
                );
                if (tileClass == HousingLandClass.Protected)
                {
                    return null;
                }

                if (tileClass == HousingLandClass.Rural)
                {
                    landClass = HousingLandClass.Rural;
                }
            }
        }

        return HousingPlacementEconomics.TryQuote(
            landClass, normalCost, false, out var quote, housing.RuralCostMultiplier
        )
            ? quote.RuralPremium
            : null;
    }

    public static HousingLandClass ClassifyTile(
        string? mapName, int x, int y, IReadOnlyList<OutdoorHotRegionDefinition> regions,
        HousingLandRules housing
    )
    {
        if (!string.Equals(mapName, "Felucca", StringComparison.OrdinalIgnoreCase))
        {
            return HousingLandClass.Protected;
        }

        var regionName = OutdoorHotZonePolicy.FindRegionName(mapName, x, y, insideDungeon: false, regions: regions);
        if (string.Equals(regionName, "BuccaneersDenIsland", StringComparison.OrdinalIgnoreCase))
        {
            return HousingLandClass.Protected;
        }

        foreach (var protectedRegion in housing.ProtectedRegions)
        {
            if (Contains(protectedRegion.Map, protectedRegion.Points, mapName, x, y))
            {
                return HousingLandClass.Protected;
            }
        }

        if (string.Equals(regionName, "FireIsland", StringComparison.OrdinalIgnoreCase))
        {
            foreach (var residentialRegion in housing.FireIslandResidentialRegions)
            {
                if (Contains(residentialRegion.Map, residentialRegion.Points, mapName, x, y))
                {
                    return HousingLandClass.FireIslandResidential;
                }
            }

            return HousingLandClass.Protected;
        }

        var openDistrictFound = false;
        foreach (var district in housing.ResidentialDistricts)
        {
            if (Contains(district.Map, district.Points, mapName, x, y))
            {
                if (!district.Open)
                {
                    return HousingLandClass.Protected;
                }

                openDistrictFound = true;
            }
        }

        return openDistrictFound ? HousingLandClass.Residential : HousingLandClass.Rural;
    }

    private static bool Contains(
        string regionMap, IReadOnlyList<TheftPoint> points, string? mapName, int x, int y
    ) => string.Equals(regionMap, mapName, StringComparison.OrdinalIgnoreCase) &&
         TheftRegionPolicy.Contains(points, x, y);

    public static bool IsBuccaneersDenTile(
        string? mapName,
        int x,
        int y,
        IReadOnlyList<OutdoorHotRegionDefinition> regions
    ) => string.Equals(
        OutdoorHotZonePolicy.FindRegionName(mapName, x, y, insideDungeon: false, regions: regions),
        "BuccaneersDenIsland",
        StringComparison.OrdinalIgnoreCase
    );
}
