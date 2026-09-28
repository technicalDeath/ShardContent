using Server;
using Server.Multis;

namespace BritanniaRenaissance.Content;

/// <summary>Read-only occupancy and expansion report for the configured housing geography.</summary>
public static class HousingStatusCommands
{
    public static void Register() =>
        CommandSystem.Register("HousingStatus", AccessLevel.Administrator, OnStatus);

    [Usage("HousingStatus")]
    [Description("Shows configured housing districts, occupancy, and decay status.")]
    private static void OnStatus(CommandEventArgs e)
    {
        var rules = ShardRulesConfiguration.Settings;
        if (rules is null)
        {
            e.Mobile.SendMessage("Housing rules are not loaded.");
            return;
        }

        var districts = rules.Housing.ResidentialDistricts.OrderBy(district => district.Sequence).ToArray();
        var districtCounts = new int[districts.Length];
        var fireIsland = 0;
        var rural = 0;
        var protectedCount = 0;
        var otherMaps = 0;
        var decayRisk = 0;
        var missingOwner = 0;
        var total = 0;

        foreach (var house in BaseHouse.AllHouses)
        {
            if (house.Deleted)
            {
                continue;
            }

            total++;
            if (house.Owner is null || house.Owner.Deleted)
            {
                missingOwner++;
            }

            if (house.CanDecay)
            {
                decayRisk++;
            }

            var mapName = house.Map?.Name;
            if (!string.Equals(mapName, "Felucca", StringComparison.OrdinalIgnoreCase))
            {
                otherMaps++;
                continue;
            }

            var districtIndex = Array.FindIndex(districts, district =>
                string.Equals(district.Map, mapName, StringComparison.OrdinalIgnoreCase) &&
                TheftRegionPolicy.Contains(district.Points, house.X, house.Y));
            if (districtIndex >= 0)
            {
                districtCounts[districtIndex]++;
                continue;
            }

            switch (HousingGeographyPolicy.ClassifyTile(mapName, house.X, house.Y,
                        rules.HotZones.PermanentOutdoorRegions, rules.Housing))
            {
                case HousingLandClass.FireIslandResidential:
                    fireIsland++;
                    break;
                case HousingLandClass.Protected:
                    protectedCount++;
                    break;
                default:
                    rural++;
                    break;
            }
        }

        e.Mobile.SendMessage($"Housing geography: {(rules.FeatureFlags.HousingGeography ? "enabled" : "disabled")}; {total} houses; {decayRisk} decay-eligible; {missingOwner} with missing owner.");
        for (var i = 0; i < districts.Length; i++)
        {
            var district = districts[i];
            e.Mobile.SendMessage($"District {district.Sequence} {district.Name}: {(district.Open ? "open" : "closed")}, {districtCounts[i]}/{district.SoftCapacity} center occupancy/soft capacity.");
        }

        e.Mobile.SendMessage($"Other center locations: Fire Island residential {fireIsland}; rural {rural}; protected {protectedCount}; other maps {otherMaps}.");
        e.Mobile.SendMessage("Occupancy is by house center; soft capacity is an observation threshold, not a placement limit. Review full footprints before expansion.");
    }
}
