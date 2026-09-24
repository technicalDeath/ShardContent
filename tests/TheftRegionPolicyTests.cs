using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class TheftRegionPolicyTests
{
    private static readonly TheftPoint[] Square =
    [
        new() { X = 0, Y = 0 },
        new() { X = 10, Y = 0 },
        new() { X = 10, Y = 10 },
        new() { X = 0, Y = 10 }
    ];

    [Fact]
    public void PolygonContainsInteriorAndRejectsExterior()
    {
        Assert.True(TheftRegionPolicy.Contains(Square, 5, 5));
        Assert.False(TheftRegionPolicy.Contains(Square, 15, 5));
    }

    [Fact]
    public void DegeneratePolygonsNeverProtect()
    {
        Assert.False(TheftRegionPolicy.Contains(Square[..2], 1, 1));
    }

    [Fact]
    public void RegionMatchingIsMapAware()
    {
        var polygons = new[]
        {
            new TheftPolygonDefinition { Map = "Felucca", Points = [.. Square] }
        };

        Assert.True(TheftRegionPolicy.IsWithin("Felucca", 5, 5, polygons));
        Assert.False(TheftRegionPolicy.IsWithin("Trammel", 5, 5, polygons));
        Assert.False(TheftRegionPolicy.IsWithin("Felucca", 15, 5, polygons));
    }

    [Fact]
    public void ProtectedAttemptMustConsiderEitherParticipant()
    {
        var polygons = new[]
        {
            new TheftPolygonDefinition { Map = "Felucca", Points = [.. Square] }
        };

        Assert.True(TheftRegionPolicy.IsWithinEither("Felucca", 15, 5, "Felucca", 5, 5, polygons));
        Assert.True(TheftRegionPolicy.IsWithinEither("Felucca", 5, 5, "Felucca", 15, 5, polygons));
        Assert.False(TheftRegionPolicy.IsWithinEither("Felucca", 15, 5, "Felucca", 15, 5, polygons));
    }
}
