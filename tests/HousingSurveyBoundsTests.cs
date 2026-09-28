using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class HousingSurveyBoundsTests
{
    [Fact]
    public void BoundedRectangleCountsEverySampledCenter()
    {
        Assert.True(HousingSurveyBounds.TryCreate(
            1200, 1300, 1250, 1350, 5, 7168, 4096, 4096, out var bounds
        ));
        Assert.Equal(121, bounds.SampleCount);
    }

    [Theory]
    [InlineData(-1, 1300, 1250, 1350, 5)]
    [InlineData(1200, 1300, 7168, 1350, 5)]
    [InlineData(1200, 1300, 1250, 4096, 5)]
    [InlineData(1250, 1300, 1200, 1350, 5)]
    [InlineData(1200, 1300, 1250, 1350, 0)]
    [InlineData(1200, 1300, 1250, 1350, 17)]
    public void InvalidBoundsCannotStartSurvey(int xMin, int yMin, int xMax, int yMax, int step)
    {
        Assert.False(HousingSurveyBounds.TryCreate(
            xMin, yMin, xMax, yMax, step, 7168, 4096, 4096, out _
        ));
    }

    [Fact]
    public void SurveyLimitPreventsLargeGameLoopScan()
    {
        Assert.False(HousingSurveyBounds.TryCreate(
            1000, 1000, 1100, 1100, 1, 7168, 4096, 4096, out _
        ));
    }

    [Fact]
    public void SpawnAreaConflictUsesInclusiveFoundationAndSpawnBounds()
    {
        Assert.True(HousingSpawnOverlap.Intersects(10, 10, 20, 20, 20, 18, 25, 24));
        Assert.False(HousingSpawnOverlap.Intersects(10, 10, 20, 20, 21, 18, 25, 24));
        Assert.False(HousingSpawnOverlap.Intersects(10, 10, 20, 20, 12, 21, 18, 25));
    }
}
