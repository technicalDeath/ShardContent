using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// Spawn spots (SpawnSpots.cs and the Britain vendor data): no creature on a roof (the graveyard zombie, owner 2026-10-18), and the Sage Advice
/// mage shop's spawner at its floor height so its mage, alchemist and guildmaster stand on the floor, not 15 below it.
/// </summary>
public class SpawnSpotsTests
{
    private static readonly string Overrides = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "world-generation", "alpha2b", "britain-vendor-overrides.json");

    [Theory]
    [InlineData("slate roof", false, true)]
    [InlineData("thatch roof", false, true)]
    [InlineData("wooden shingles", true, true)]
    [InlineData("wooden boards", false, false)]
    [InlineData("stone pavers", false, false)]
    [InlineData(null, false, false)]
    public void RoofArtIsKnownByFlagOrName(string name, bool roofFlag, bool expected) =>
        Assert.Equal(expected, SpawnSpots.IsRoof(name, roofFlag));

    [Fact]
    public void TheMageShopSpawnerStandsOnItsFloor()
    {
        // the shop's floor at 1575,1703 is the land at 35; the spawner stood at 20, so everything it spawned stood sunk in the floor
        var shop = JsonDocument.Parse(File.ReadAllText(Overrides)).RootElement.EnumerateArray()
            .Single(s => s.GetProperty("guid").GetString()!.StartsWith("81a9449b", StringComparison.Ordinal));
        Assert.Equal(new[] { 1575, 1703, 35 }, shop.GetProperty("location").EnumerateArray().Select(v => v.GetInt32()).ToArray());
    }
}
