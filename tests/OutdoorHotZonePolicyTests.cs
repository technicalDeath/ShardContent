using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class OutdoorHotZonePolicyTests
{
    private static readonly OutdoorHotRegionDefinition[] Regions =
    [
        new()
        {
            Name = "FireIsland",
            Map = "Felucca",
            Points =
            [
                new TheftPoint { X = 100, Y = 100 },
                new TheftPoint { X = 200, Y = 100 },
                new TheftPoint { X = 200, Y = 200 },
                new TheftPoint { X = 100, Y = 200 }
            ]
        }
    ];

    [Theory]
    [InlineData("Felucca", 150, 150, false, "FireIsland")]
    [InlineData("Felucca", 100, 150, false, "FireIsland")]
    [InlineData("Felucca", 200, 150, false, null)]
    [InlineData("Felucca", 99, 150, false, null)]
    [InlineData("Trammel", 150, 150, false, null)]
    [InlineData("Felucca", 150, 150, true, null)]
    public void OutdoorMembershipRespectsBoundaryMapAndDungeonExclusion(
        string map, int x, int y, bool insideDungeon, string? expected
    )
    {
        Assert.Equal(expected, OutdoorHotZonePolicy.FindRegionName(map, x, y, insideDungeon, Regions));
    }

    [Fact]
    public void SourceIslandPolygonsCoverKnownLandmarksAndExcludeOceanAndDungeons()
    {
        var path = Path.GetFullPath(Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        ));
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path));
        Assert.NotNull(rules);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
        var regions = rules.HotZones.PermanentOutdoorRegions;
        Assert.Equal(["FireIsland", "BuccaneersDenIsland"], regions.Select(region => region.Name));

        Assert.Equal("FireIsland", OutdoorHotZonePolicy.FindRegionName("Felucca", 4722, 3814, false, regions));
        Assert.Equal("FireIsland", OutdoorHotZonePolicy.FindRegionName("Felucca", 4600, 3500, false, regions));
        Assert.Equal("BuccaneersDenIsland", OutdoorHotZonePolicy.FindRegionName("Felucca", 2706, 2163, false, regions));
        Assert.Equal("BuccaneersDenIsland", OutdoorHotZonePolicy.FindRegionName("Felucca", 2840, 2260, false, regions));

        Assert.Null(OutdoorHotZonePolicy.FindRegionName("Felucca", 4900, 3800, false, regions));
        Assert.Null(OutdoorHotZonePolicy.FindRegionName("Felucca", 2900, 2200, false, regions));
        Assert.Null(OutdoorHotZonePolicy.FindRegionName("Trammel", 2706, 2163, false, regions));
        Assert.Null(OutdoorHotZonePolicy.FindRegionName("Felucca", 4722, 3814, true, regions));
    }

    [Fact]
    public void BoundaryMessagesCoverEntryExitLoginAndDirectTravel()
    {
        var login = OutdoorHotZoneBoundaryService.DescribeTransition(null, "FireIsland").ToArray();
        Assert.Single(login);
        Assert.Contains("Fire Island", login[0]);
        Assert.Contains("initiate combat freely", login[0]);
        Assert.Contains("murder count and 24 hours", login[0]);

        Assert.Empty(OutdoorHotZoneBoundaryService.DescribeTransition("FireIsland", "FireIsland"));

        var exit = OutdoorHotZoneBoundaryService.DescribeTransition("FireIsland", null).ToArray();
        Assert.Single(exit);
        Assert.Contains("existing lawful fights continue", exit[0]);

        var directTravel = OutdoorHotZoneBoundaryService.DescribeTransition(
            "FireIsland", "BuccaneersDenIsland"
        ).ToArray();
        Assert.Equal(2, directTravel.Length);
        Assert.Contains("left Fire Island", directTravel[0]);
        Assert.Contains("entered Buccaneer's Den island", directTravel[1]);
    }

    [Theory]
    [InlineData(true, true, "FireIsland", "FireIsland", true)]
    [InlineData(true, true, "FireIsland", null, false)]
    [InlineData(true, true, null, "FireIsland", false)]
    [InlineData(true, true, "FireIsland", "BuccaneersDenIsland", false)]
    [InlineData(false, true, "FireIsland", "FireIsland", false)]
    [InlineData(true, false, "FireIsland", "FireIsland", false)]
    public void NewHotZoneHostilityRequiresDirectPlayerSourceStockPermissionAndSharedRegion(
        bool directPlayerSource, bool stockAllowed, string? attackerRegion,
        string? defenderRegion, bool expected
    )
    {
        Assert.Equal(expected, PvpIntentService.IsOutdoorHotInitiationAllowed(
            directPlayerSource, stockAllowed, attackerRegion, defenderRegion
        ));
    }

    [Fact]
    public void LeavingHotZoneDoesNotEraseAnExistingFightOrAuthorizeAnUnrelatedAttack()
    {
        Assert.False(PvpIntentService.IsOutdoorHotInitiationAllowed(true, true, null, "FireIsland"));
        Assert.True(PvpIntentService.IsSafeWorldPlayerAttackAllowed(true, false, false, false, true));
        Assert.False(PvpIntentService.IsSafeWorldPlayerAttackAllowed(true, false, false, false, false));
    }
}
