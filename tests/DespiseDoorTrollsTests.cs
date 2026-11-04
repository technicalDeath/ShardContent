using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The troll camp at Despise's door, halved (owner 2026-11-04: "Halve the trolls", with Despise the bot ladder's beginner dungeon): the stock
/// Outdoors spawner at 1325,1071 (10 trolls, home 30, 29 tiles from the door at 1296,1081) is overridden by a custom file with its own guid and
/// place, so the generator's later-file-wins rule (Prepare-Alpha2bWorldData.ps1: one spawner per guid and per place) keeps 5. Evidence:
/// docs/Cove-Spawn-Areas-Evidence.md, last section.
/// </summary>
public class DespiseDoorTrollsTests
{
    private static readonly string Root = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "world-generation", "alpha2b");
    private const string StockGuid = "409e129c-f95e-4a05-aff8-e2d577aede77";

    private static JsonElement Manifest() => JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "world-generation.json"))).RootElement;

    [Fact]
    public void TheOverrideKeepsTheStockSpawnersGuidAndPlaceWithHalfItsTrolls()
    {
        var all = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "despise-door-trolls.json"))).RootElement.EnumerateArray().ToList();
        var s = Assert.Single(all);
        Assert.Equal(StockGuid, s.GetProperty("guid").GetString());
        Assert.Equal(new[] { 1325, 1071, 0 }, s.GetProperty("location").EnumerateArray().Select(e => e.GetInt32()).ToArray());
        Assert.Equal("Felucca", s.GetProperty("map").GetString());
        Assert.Equal(5, s.GetProperty("count").GetInt32());
        var entry = Assert.Single(s.GetProperty("entries").EnumerateArray().ToList());
        Assert.Equal("Troll", entry.GetProperty("name").GetString());
        Assert.Equal(5, entry.GetProperty("maxCount").GetInt32());
        Assert.Equal(30, s.GetProperty("homeRange").GetInt32());
    }

    [Fact]
    public void TheManifestListsItAsACustomFileAndNoOtherCustomFileTakesItsGuidOrPlace()
    {
        var files = Manifest().GetProperty("customSpawnerFiles").EnumerateArray().Select(e => e.GetString()!).ToList();
        Assert.Contains("despise-door-trolls.json", files);
        foreach (var f in files.Where(f => f != "despise-door-trolls.json"))
        {
            foreach (var s in JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, f))).RootElement.EnumerateArray())
            {
                Assert.NotEqual(StockGuid, s.GetProperty("guid").GetString());
                var loc = s.GetProperty("location").EnumerateArray().Select(e => e.GetInt32()).ToArray();
                Assert.False(loc[0] == 1325 && loc[1] == 1071, $"{f} has a spawner on the troll camp's place");
            }
        }
    }
}
