using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class HousingGeographyPolicyTests
{
    [Fact]
    public void BuccaneersDenLandIsProtectedFromHousingIndependentOfHotFlag()
    {
        var path = Path.GetFullPath(Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        ));
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path));
        Assert.NotNull(rules);

        var regions = rules.HotZones.PermanentOutdoorRegions;
        Assert.True(HousingGeographyPolicy.IsBuccaneersDenTile("Felucca", 2706, 2163, regions));
        Assert.True(HousingGeographyPolicy.IsBuccaneersDenTile("Felucca", 2840, 2260, regions));
        Assert.False(HousingGeographyPolicy.IsBuccaneersDenTile("Felucca", 4900, 3800, regions));
        Assert.False(HousingGeographyPolicy.IsBuccaneersDenTile("Felucca", 4722, 3814, regions));
        Assert.False(HousingGeographyPolicy.IsBuccaneersDenTile("Trammel", 2706, 2163, regions));
        Assert.Equal(HousingLandClass.Protected, HousingGeographyPolicy.ClassifyTile("Felucca", 2706, 2163, regions, rules.Housing));
        Assert.Equal(HousingLandClass.Protected, HousingGeographyPolicy.ClassifyTile("Felucca", 4722, 3814, regions, rules.Housing));
        Assert.Equal(HousingLandClass.Rural, HousingGeographyPolicy.ClassifyTile("Felucca", 1800, 1500, regions, rules.Housing));
        Assert.Equal(HousingLandClass.Protected, HousingGeographyPolicy.ClassifyTile("Trammel", 1800, 1500, regions, rules.Housing));
    }

    [Fact]
    public void OnlySurveyedOpenDistrictsAndFireHousingAreasReceiveNormalPrice()
    {
        var regions = new List<OutdoorHotRegionDefinition>
        {
            Region("FireIsland", 100, 100, 200, 200),
            Region("BuccaneersDenIsland", 300, 300, 400, 400)
        };
        var housing = new HousingLandRules();
        housing.ResidentialDistricts.Add(new HousingDistrictDefinition
        {
            Name = "GreaterBritainA", Map = "Felucca", Points = Square(1000, 1000, 1100, 1100),
            Sequence = 1, SoftCapacity = 10, Open = true
        });
        housing.ResidentialDistricts.Add(new HousingDistrictDefinition
        {
            Name = "GreaterBritainB", Map = "Felucca", Points = Square(1200, 1000, 1300, 1100),
            Sequence = 2, SoftCapacity = 10, Open = false
        });
        housing.ResidentialDistricts.Add(new HousingDistrictDefinition
        {
            Name = "GreaterBritainC", Map = "Felucca", Points = Square(1080, 1080, 1090, 1090),
            Sequence = 3, SoftCapacity = 10, Open = false
        });
        housing.FireIslandResidentialRegions.Add(Region("FireIslandResidential", 120, 120, 150, 150));
        housing.ProtectedRegions.Add(Region("RoadBuffer", 1010, 1010, 1020, 1020));

        Assert.Equal(HousingLandClass.Residential,
            HousingGeographyPolicy.ClassifyTile("Felucca", 1050, 1050, regions, housing));
        Assert.Equal(HousingLandClass.Protected,
            HousingGeographyPolicy.ClassifyTile("Felucca", 1015, 1015, regions, housing));
        Assert.Equal(HousingLandClass.Protected,
            HousingGeographyPolicy.ClassifyTile("Felucca", 1250, 1050, regions, housing));
        Assert.Equal(HousingLandClass.Protected,
            HousingGeographyPolicy.ClassifyTile("Felucca", 1085, 1085, regions, housing));
        Assert.Equal(HousingLandClass.FireIslandResidential,
            HousingGeographyPolicy.ClassifyTile("Felucca", 130, 130, regions, housing));
        Assert.Equal(HousingLandClass.Protected,
            HousingGeographyPolicy.ClassifyTile("Felucca", 170, 170, regions, housing));
        Assert.Equal(HousingLandClass.Protected,
            HousingGeographyPolicy.ClassifyTile("Felucca", 350, 350, regions, housing));
        Assert.Equal(HousingLandClass.Rural,
            HousingGeographyPolicy.ClassifyTile("Felucca", 1500, 1500, regions, housing));
    }

    private static OutdoorHotRegionDefinition Region(string name, int xMin, int yMin, int xMax, int yMax) =>
        new() { Name = name, Map = "Felucca", Points = Square(xMin, yMin, xMax, yMax) };

    private static List<TheftPoint> Square(int xMin, int yMin, int xMax, int yMax) =>
    [
        new() { X = xMin, Y = yMin }, new() { X = xMax, Y = yMin },
        new() { X = xMax, Y = yMax }, new() { X = xMin, Y = yMax }
    ];
}
