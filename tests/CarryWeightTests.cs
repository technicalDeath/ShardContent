using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CarryWeightTests
{
    private static readonly CarryWeightRules Shard = new() { Base = 100, PerStrength = 3.5, PlayerBackpackMaxWeight = 550 };

    private static List<string> Errors(CarryWeightRules rules)
    {
        var errors = new List<string>();
        CarryWeight.Validate(rules, errors);
        return errors;
    }

    [Theory]
    [InlineData(10, 75, 135)]
    [InlineData(40, 180, 240)]
    [InlineData(50, 215, 275)]
    [InlineData(55, 232, 292)]
    [InlineData(100, 390, 450)]
    public void TheLimitIsBasePlusStrengthRoundedDownAsStock(int str, int stock, int shard)
    {
        Assert.Equal(stock, CarryWeight.Limit(new CarryWeightRules(), str));
        Assert.Equal(shard, CarryWeight.Limit(Shard, str));
    }

    [Fact]
    public void TheDefaultsAreStock()
    {
        var rules = new CarryWeightRules();

        Assert.Equal(40, rules.Base);
        Assert.Equal(3.5, rules.PerStrength);
        Assert.Equal(400, CarryWeight.BackpackLimit(rules, 400));
    }

    [Fact]
    public void TheWornBackpackTakesTheConfiguredMostOrStock()
    {
        Assert.Equal(550, CarryWeight.BackpackLimit(Shard, 400));
        Assert.Equal(400, CarryWeight.BackpackLimit(new CarryWeightRules { PlayerBackpackMaxWeight = 0 }, 400));
    }

    [Fact]
    public void ValidationAcceptsStockAndTheShardValues()
    {
        Assert.Empty(Errors(new CarryWeightRules()));
        Assert.Empty(Errors(Shard));
        Assert.Empty(Errors(null));
    }

    [Fact]
    public void ValidationRejectsOutOfRangeValues()
    {
        Assert.Single(Errors(new CarryWeightRules { Base = -1 }));
        Assert.Single(Errors(new CarryWeightRules { Base = 401 }));
        Assert.Single(Errors(new CarryWeightRules { PerStrength = -0.5 }));
        Assert.Single(Errors(new CarryWeightRules { PerStrength = 11 }));
        Assert.Single(Errors(new CarryWeightRules { PerStrength = double.NaN }));
        Assert.Single(Errors(new CarryWeightRules { PerStrength = 3.55 }));
        Assert.Single(Errors(new CarryWeightRules { PlayerBackpackMaxWeight = 399 }));
        Assert.Single(Errors(new CarryWeightRules { PlayerBackpackMaxWeight = 1601 }));
    }

    [Fact]
    public void TheClientIsToldTheBaseAndTheStonesPerStrengthInTenths()
    {
        Assert.Equal(new byte[] { 0xBF, 0, 9, 0x00, 0xB3, 0, 100, 0, 35 }, CarryWeight.Packet(Shard));
        Assert.Equal(new byte[] { 0xBF, 0, 9, 0x00, 0xB3, 0, 40, 0, 35 }, CarryWeight.Packet(new CarryWeightRules()));
    }

    [Theory]
    [InlineData(10)]
    [InlineData(51)]
    [InlineData(100)]
    public void TheClientsSumMatchesTheServersLimit(int str)
    {
        // the client works it out as base + tenths x Str / 10 in whole numbers
        Assert.Equal(CarryWeight.Limit(Shard, str), Shard.Base + CarryWeight.PerStrengthTenths(Shard) * str / 10);
    }

    [Fact]
    public void TheShardConfigSetsBase100AndA550StoneBackpack()
    {
        var dir = new DirectoryInfo(System.AppContext.BaseDirectory);
        while (dir != null && !File.Exists(Path.Combine(dir.FullName, "data", "configuration", "shard-rules.json")))
        {
            dir = dir.Parent;
        }

        Assert.NotNull(dir);
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(dir.FullName, "data", "configuration", "shard-rules.json")))!;

        Assert.Equal(100, rules.CarryWeight.Base);
        Assert.Equal(3.5, rules.CarryWeight.PerStrength);
        Assert.Equal(550, rules.CarryWeight.PlayerBackpackMaxWeight);
        Assert.Empty(Errors(rules.CarryWeight));
    }
}
