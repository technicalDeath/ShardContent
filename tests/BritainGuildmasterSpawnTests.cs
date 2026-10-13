using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The guildmasters and trade vendors the stock Britain spawn data lacks (docs/Britain-Guildmasters-Evidence.md): the Thieves', Rangers' and Fishermen's Guildmasters, which stock
/// ModernUO places only in other towns, and a plain Tinker and Miner, which it never places in Britain. They live in the shard's own override file, which world generation reads.
/// </summary>
public class BritainGuildmasterSpawnTests
{
    private static readonly string Root = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "world-generation", "alpha2b");

    private static List<JsonElement> Overrides() =>
        JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "britain-vendor-overrides.json"))).RootElement.EnumerateArray().Select(e => e.Clone()).ToList();

    private static IEnumerable<(string Type, int X, int Y, int Z)> Placed() =>
        Overrides().SelectMany(
            s => s.GetProperty("entries").EnumerateArray().Select(
                e =>
                {
                    var at = s.GetProperty("location").EnumerateArray().Select(v => v.GetInt32()).ToArray();

                    return (e.GetProperty("name").GetString()!, at[0], at[1], at[2]);
                }
            )
        );

    [Theory]
    [InlineData("ThiefGuildmaster")]
    [InlineData("RangerGuildmaster")]
    [InlineData("FisherGuildmaster")]
    [InlineData("Tinker")]
    [InlineData("Miner")]
    public void EachMissingTypeIsSpawnedExactlyOnceInBritain(string type) =>
        Assert.Single(Placed().Where(p => p.Type == type));

    [Fact]
    public void EveryOverrideIsInsideGreaterBritainOnFelucca()
    {
        foreach (var spawner in Overrides())
        {
            var at = spawner.GetProperty("location").EnumerateArray().Select(v => v.GetInt32()).ToArray();

            Assert.InRange(at[0], 1280, 1750);
            Assert.InRange(at[1], 1400, 1900);
            Assert.Equal("Felucca", spawner.GetProperty("map").GetString());
        }
    }

    [Fact]
    public void GuidsAndPlacesAreUniqueSoGenerationKeepsEverySpawner()
    {
        var all = Overrides();
        var guids = all.Select(s => s.GetProperty("guid").GetString()).ToList();
        var places = all.Select(s => string.Join(",", s.GetProperty("location").EnumerateArray().Select(v => v.GetInt32()))).ToList();

        Assert.Equal(guids.Count, guids.Distinct(StringComparer.OrdinalIgnoreCase).Count());
        Assert.Equal(places.Count, places.Distinct().Count());
    }

    [Fact]
    public void ANewSpawnerHoldsOneNpcThatStaysPutLikeTheStockVendors()
    {
        foreach (var spawner in Overrides().Where(s => s.GetProperty("entries").GetArrayLength() == 1))
        {
            Assert.Equal(1, spawner.GetProperty("count").GetInt32());
            Assert.Equal(0, spawner.GetProperty("homeRange").GetInt32());
            Assert.Equal(5, spawner.GetProperty("walkingRange").GetInt32());
            Assert.Equal(1, spawner.GetProperty("entries")[0].GetProperty("maxCount").GetInt32());
        }
    }

    [Fact]
    public void NoOverrideSpawnsATypeTheEraExcludes()
    {
        var manifest = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "world-generation.json"))).RootElement;
        var excluded = manifest.GetProperty("excludedSpawnerTypes").EnumerateArray().Select(e => e.GetString()!).ToHashSet(StringComparer.OrdinalIgnoreCase);

        Assert.DoesNotContain(Placed(), p => excluded.Contains(p.Type));
    }

    [Fact]
    public void TheOverrideFileIsStillListedInTheGenerationManifest()
    {
        var manifest = JsonDocument.Parse(File.ReadAllText(Path.Combine(Root, "world-generation.json"))).RootElement;

        Assert.Contains("britain-vendor-overrides.json", manifest.GetProperty("customSpawnerFiles").EnumerateArray().Select(e => e.GetString()));
    }
}
