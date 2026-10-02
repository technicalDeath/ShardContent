using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class HythlothHotZoneTests
{
    private static readonly OutdoorHotRegionDefinition[] Outdoor =
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

    private static readonly HotZoneDungeonRegion[] Hythloth = [new() { Name = "Hythloth", Map = "Felucca" }];

    // ---- membership

    [Theory]
    [InlineData("Hythloth", 5905, 22, "Hythloth")]
    [InlineData("hythloth", 6000, 200, "Hythloth")]
    // The neighbouring dungeons, a few tiles away, are separate stock regions and stay ordinary.
    [InlineData("Shame", 5890, 50, null)]
    [InlineData("Ice", 5880, 200, null)]
    [InlineData("Sanctuary", 6150, 10, null)]
    [InlineData("Fire", 5760, 1350, null)]
    // A nameless dungeon region is still a dungeon: never Hot, even under an outdoor polygon.
    [InlineData("", 150, 150, null)]
    public void OnlyTheListedDungeonIsHotAndTheWholeRegionIs(string dungeon, int x, int y, string? expected)
    {
        Assert.Equal(expected, OutdoorHotZonePolicy.FindHotRegionName("Felucca", x, y, dungeon, Outdoor, Hythloth));
    }

    [Fact]
    public void TheListedDungeonIsHotOnlyOnItsOwnMap()
    {
        Assert.Null(OutdoorHotZonePolicy.FindHotRegionName("Trammel", 5905, 22, "Hythloth", Outdoor, Hythloth));
    }

    [Fact]
    public void WithTheFlagOffNoDungeonIsHot()
    {
        // GetRegionName passes an empty dungeon list when hythlothHotZone is off.
        Assert.Null(OutdoorHotZonePolicy.FindHotRegionName("Felucca", 5905, 22, "Hythloth", Outdoor, []));
    }

    [Fact]
    public void OutdoorsThePolygonsStillDecide()
    {
        Assert.Equal("FireIsland", OutdoorHotZonePolicy.FindHotRegionName("Felucca", 150, 150, null, Outdoor, Hythloth));
        Assert.Null(OutdoorHotZonePolicy.FindHotRegionName("Felucca", 250, 150, null, Outdoor, Hythloth));
        Assert.Null(OutdoorHotZonePolicy.FindHotRegionName(null, 150, 150, null, Outdoor, Hythloth));
    }

    [Fact]
    public void FightsMayOnlyBeginInsideTheSameHotRegion()
    {
        Assert.True(PvpIntentService.IsOutdoorHotInitiationAllowed(true, true, "Hythloth", "Hythloth"));
        Assert.False(PvpIntentService.IsOutdoorHotInitiationAllowed(true, true, "Hythloth", "FireIsland"));
        Assert.False(PvpIntentService.IsOutdoorHotInitiationAllowed(true, true, "Hythloth", null));
        Assert.False(PvpIntentService.IsOutdoorHotInitiationAllowed(false, true, "Hythloth", "Hythloth"));
    }

    // ---- messages

    private static bool IsDungeon(string name) => name == "Hythloth";

    [Fact]
    public void EnteringHythlothNamesItAPvpHotZone()
    {
        var lines = OutdoorHotZoneBoundaryService.DescribeTransition(null, "Hythloth", IsDungeon).ToArray();

        var line = Assert.Single(lines);
        Assert.Contains("You have entered Hythloth, a PvP Hot Zone.", line);
        Assert.Contains("initiate combat freely", line);
        Assert.DoesNotContain("outdoor", line);
        Assert.DoesNotContain("Hot Dungeon", line);
    }

    [Fact]
    public void WalkingOutOfHythlothOntoFireIslandDoesNotSayHotRulesStopped()
    {
        var lines = OutdoorHotZoneBoundaryService.DescribeTransition("Hythloth", "FireIsland", IsDungeon).ToArray();

        Assert.Equal(2, lines.Length);
        Assert.Equal("You have left Hythloth.", lines[0]);
        Assert.Contains("entered Fire Island, an outdoor PvP Hot Zone", lines[1]);
    }

    [Fact]
    public void LeavingAHotZoneForOrdinaryLandStillSaysSo()
    {
        var line = Assert.Single(OutdoorHotZoneBoundaryService.DescribeTransition("Hythloth", null, IsDungeon));

        Assert.Contains("no longer applies here", line);
    }

    // ---- configuration

    private static ShardRules Shipped() => JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(
        AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
    )))!;

    [Fact]
    public void TheShippedConfigurationListsHythlothOnFeluccaOnly()
    {
        var rules = Shipped();

        var dungeon = Assert.Single(rules.HotZones.DungeonRegions);
        Assert.Equal("Hythloth", dungeon.Name);
        Assert.Equal("Felucca", dungeon.Map);
        Assert.DoesNotContain(ShardRulesConfiguration.Validate(rules), e => e.Contains("dungeonRegions") || e.Contains("hythloth"));
    }

    [Fact]
    public void TheFlagNeedsHotZonesAndAHythlothEntry()
    {
        var rules = Shipped();
        rules.FeatureFlags.HythlothHotZone = true;
        rules.FeatureFlags.HotZones = false;
        rules.HotZones.DungeonRegions.Clear();

        var errors = ShardRulesConfiguration.Validate(rules);

        Assert.Contains(errors, e => e.Contains("hythlothHotZone requires hotZones"));
        Assert.Contains(errors, e => e.Contains("requires a Hythloth entry"));
    }

    [Fact]
    public void DungeonRegionNamesMustBeUniqueAndOnAnEnabledMap()
    {
        var rules = Shipped();
        rules.HotZones.DungeonRegions.Add(new HotZoneDungeonRegion { Name = "FireIsland", Map = "Felucca" });
        rules.HotZones.DungeonRegions.Add(new HotZoneDungeonRegion { Name = "Deceit", Map = "Trammel" });

        var errors = ShardRulesConfiguration.Validate(rules);

        Assert.Contains(errors, e => e.Contains("unique among all Hot Zone regions"));
        Assert.Contains(errors, e => e.Contains("'Deceit' must be on an enabled map"));
    }

    [Fact]
    public void TheFlagIsReportedByName()
    {
        Assert.Equal(["HythlothHotZone"], new DeferredFeatureFlags { HythlothHotZone = true }.EnabledNames());
    }

    // ---- boot check

    [Fact]
    public void TheBootCheckFindsAMissingOrMisspeltRegion()
    {
        var existing = new (string?, string?)[] { ("Hythloth", "Felucca"), ("Hythloth", "Trammel"), ("Shame", "Felucca") };

        Assert.Empty(OutdoorHotZonePolicy.MissingDungeonRegions(Hythloth, existing));
        Assert.Equal(
            ["Hytholth (Felucca)"],
            OutdoorHotZonePolicy.MissingDungeonRegions([new HotZoneDungeonRegion { Name = "Hytholth", Map = "Felucca" }], existing)
        );
    }

    [Fact]
    public void TheShippedNameMatchesTheStockRegionData()
    {
        var path = Path.GetFullPath(Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "..", "ModernUO", "Distribution", "Data", "regions.json"
        ));
        Assert.True(File.Exists(path), path);

        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        var stock = doc.RootElement.EnumerateArray()
            .Where(r => r.TryGetProperty("$type", out var t) && t.GetString() == "DungeonRegion")
            .Select(r => ((string?)r.GetProperty("Name").GetString(), (string?)r.GetProperty("Map").GetString()));

        Assert.Empty(OutdoorHotZonePolicy.MissingDungeonRegions(Shipped().HotZones.DungeonRegions, stock));
    }
}
