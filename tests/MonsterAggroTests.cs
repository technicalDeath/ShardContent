using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class MonsterAggroTests
{
    [Fact]
    public void BothStockRangesLoseTheConfiguredTiles()
    {
        Assert.Equal(14, MonsterAggro.Reduced(16, 2));                 // RangePerception's default: the periodic scan
        Assert.Equal(8, MonsterAggro.Reduced(10, 2));                  // AcquireOnApproachRange: the reaction to an enemy moving near
        Assert.Equal(16, MonsterAggro.Reduced(18, 2));                 // a creature that sets 18 scans 16
        Assert.Equal(20, MonsterAggro.Reduced(22, 2));
    }

    [Fact]
    public void ZeroKeepsStockAndNoRangeFallsBelowTheMinimum()
    {
        Assert.Equal(16, MonsterAggro.Reduced(16, 0));
        Assert.Equal(MonsterAggro.MinimumRange, MonsterAggro.Reduced(3, 2));
        Assert.Equal(MonsterAggro.MinimumRange, MonsterAggro.Reduced(10, 8));
        Assert.Equal(1, MonsterAggro.Reduced(1, 2));                   // already tighter than the minimum: left as it is
    }

    [Fact]
    public void NoCreatureMeansTheStockRange()
    {
        Assert.Equal(16, MonsterAggro.Range(null, 16, 2));
    }

    [Fact]
    public void ValidationRejectsNegativeAndOversizedReductions()
    {
        var errors = new List<string>();
        MonsterAggro.Validate(new MonsterAggroRules { RangeReduction = 0 }, errors);
        MonsterAggro.Validate(new MonsterAggroRules { RangeReduction = 2 }, errors);
        MonsterAggro.Validate(new MonsterAggroRules { RangeReduction = MonsterAggro.MaximumReduction }, errors);
        Assert.Empty(errors);
        MonsterAggro.Validate(new MonsterAggroRules { RangeReduction = -1 }, errors);
        MonsterAggro.Validate(new MonsterAggroRules { RangeReduction = MonsterAggro.MaximumReduction + 1 }, errors);
        Assert.Equal(2, errors.Count);
    }

    [Fact]
    public void TheShardConfigTakesTwoTilesOff()
    {
        var dir = new DirectoryInfo(System.AppContext.BaseDirectory);
        while (dir != null && !File.Exists(Path.Combine(dir.FullName, "data", "configuration", "shard-rules.json")))
        {
            dir = dir.Parent;
        }

        Assert.NotNull(dir);
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(dir!.FullName, "data", "configuration", "shard-rules.json")));
        Assert.Equal(2, rules!.MonsterAggro.RangeReduction);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }
}
