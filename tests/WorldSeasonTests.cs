using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Felucca's season (owner, 2026-10-18: leaves on the trees, pre-Trammel Felucca): WorldSeason.cs.</summary>
public class WorldSeasonTests
{
    private static readonly string Rules = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");

    [Fact]
    public void FeluccaIsSummerInTheShardRules()
    {
        var felucca = JsonDocument.Parse(File.ReadAllText(Rules)).RootElement.GetProperty("worldSeason").GetProperty("felucca").GetInt32();
        Assert.Equal(1, felucca);
        Assert.Equal("summer", WorldSeason.Name(felucca));
    }

    [Theory]
    [InlineData(-1, 4, 4)] // -1 keeps the map definition's desolation
    [InlineData(1, 4, 1)]
    [InlineData(0, 4, 0)]
    [InlineData(9, 4, 4)]
    public void ResolveKeepsTheMapsSeasonUnlessOneIsSet(int configured, int stock, int expected) =>
        Assert.Equal(expected, WorldSeason.Resolve(configured, stock));

    [Fact]
    public void ValidateRejectsAnUnknownSeason()
    {
        var errors = new List<string>();
        WorldSeason.Validate(new WorldSeasonRules { Felucca = 5 }, errors);
        Assert.Single(errors);
        errors.Clear();
        WorldSeason.Validate(new WorldSeasonRules { Felucca = 1 }, errors);
        Assert.Empty(errors);
    }
}
