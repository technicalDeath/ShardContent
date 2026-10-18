using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// Beginner hunting around Britain (docs/Britain-Beginner-Hunting-Evidence.md): stock Felucca data has no wild spawner within 140 tiles of
/// Britain, only town animals, and the nearest monsters (the graveyard's spectres and wraiths, orc, troll and ettin camps, gargoyles and
/// gazers) are beyond a new character. These spawners put the era's weakest creatures in Britain's own woods and fields.
/// </summary>
public class BritainBeginnerHuntingSpawnTests
{
    private static readonly string Root = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "world-generation", "alpha2b");

    // a new character has about 77 hit points; every beginner type has at most 60 hit points and hits for at most 10 (the classes' SetHits/SetDamage)
    private static readonly HashSet<string> Beginner = new(StringComparer.Ordinal)
    {
        "Rabbit", "Hind", "GreatHart", "Eagle", "Snake", "Slime", "Mongbat", "GiantRat",
        "GreyWolf", "HeadlessOne", "Skeleton", "Zombie", "BlackBear"
    };

    // the owner's "mongbats, ratmen and lizardmen, and the weaker orc variants": 58-72 hit points hitting for 4-7 (Ratman, Lizardman, Orc), a Greater
    // Mongbat (34-48, 5-7) and the Orcish Mage (70-90, casts). Not the Ratman archer and mage or the Orcish Lord (88-123 hit points).
    private static readonly HashSet<string> StepUp = new(StringComparer.Ordinal)
    {
        "Ratman", "Lizardman", "Orc", "OrcishMage", "GreaterMongbat"
    };

    private static List<JsonElement> Spawners() =>
        JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "britain-beginner-hunting.json"))).RootElement.EnumerateArray().Select(e => e.Clone()).ToList();

    private static int[] At(JsonElement s) => s.GetProperty("location").EnumerateArray().Select(v => v.GetInt32()).ToArray();

    [Fact]
    public void OnlyBeginnerAndStepUpCreaturesAreSpawned()
    {
        foreach (var s in Spawners())
        {
            foreach (var e in s.GetProperty("entries").EnumerateArray())
            {
                var name = e.GetProperty("name").GetString()!;
                Assert.True(Beginner.Contains(name) || StepUp.Contains(name), $"{name} is not a beginner creature");
            }
        }
    }

    [Fact]
    public void StepUpCreaturesAreAMinorityEverywhere()
    {
        // ratmen, lizardmen and orcs are sprinkled in: at every site most of what can spawn is a beginner creature, and there is never more than one orcish mage
        foreach (var s in Spawners())
        {
            var entries = s.GetProperty("entries").EnumerateArray().Select(e => (Name: e.GetProperty("name").GetString()!, Max: e.GetProperty("maxCount").GetInt32())).ToList();
            var stepUp = entries.Where(e => StepUp.Contains(e.Name)).Sum(e => e.Max);
            Assert.True(stepUp * 2 < entries.Sum(e => e.Max), $"{s.GetProperty("name").GetString()} is mostly step-up creatures");
            Assert.True(entries.Where(e => e.Name == "OrcishMage").Sum(e => e.Max) <= 1);
        }
    }

    [Fact]
    public void EverySpawnerIsInBritainsTownRegionOnFelucca()
    {
        // the Britain TownRegion's rectangles (Data/regions.json): the city and the woods and fields around it
        (int X0, int Y0, int X1, int Y1)[] britain =
        [
            (1416, 1498, 1740, 1777), (1500, 1408, 1546, 1498), (1385, 1538, 1416, 1777),
            (1416, 1777, 1740, 1837), (1385, 1777, 1416, 1907), (1093, 1538, 1385, 1907)
        ];

        foreach (var s in Spawners())
        {
            var at = At(s);
            Assert.Equal("Felucca", s.GetProperty("map").GetString());
            Assert.Contains(britain, r => at[0] >= r.X0 && at[0] < r.X1 && at[1] >= r.Y0 && at[1] < r.Y1);
        }
    }

    [Fact]
    public void SpawnersStayAwayFromTheCityStreets()
    {
        // the bank, the healer and the main shops: no beginner spawner within 60 tiles of the town centre
        foreach (var s in Spawners())
        {
            var at = At(s);
            Assert.True(Math.Max(Math.Abs(at[0] - 1470), Math.Abs(at[1] - 1620)) >= 60, $"{s.GetProperty("name").GetString()} is too close to the city");
        }
    }

    [Fact]
    public void GuidsAndPlacesAreUniqueSoGenerationKeepsEverySpawner()
    {
        var all = Spawners();
        var vendors = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "britain-vendor-overrides.json"))).RootElement.EnumerateArray().ToList();
        var guids = all.Concat(vendors).Select(s => s.GetProperty("guid").GetString()).ToList();
        var places = all.Select(s => string.Join(",", At(s))).ToList();

        Assert.Equal(guids.Count, guids.Distinct(StringComparer.OrdinalIgnoreCase).Count());
        Assert.Equal(places.Count, places.Distinct().Count());
    }

    [Fact]
    public void NoSpawnerUsesATypeTheEraExcludes()
    {
        var manifest = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "world-generation.json"))).RootElement;
        var excluded = manifest.GetProperty("excludedSpawnerTypes").EnumerateArray().Select(e => e.GetString()!).ToHashSet(StringComparer.OrdinalIgnoreCase);

        Assert.DoesNotContain(
            Spawners().SelectMany(s => s.GetProperty("entries").EnumerateArray()),
            e => excluded.Contains(e.GetProperty("name").GetString()!)
        );
    }

    [Fact]
    public void TheFileIsListedInTheGenerationManifest()
    {
        var manifest = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "world-generation.json"))).RootElement;

        Assert.Contains("britain-beginner-hunting.json", manifest.GetProperty("customSpawnerFiles").EnumerateArray().Select(e => e.GetString()));
    }
}
