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
}
