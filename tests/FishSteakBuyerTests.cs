using System.IO;
using System.Linq;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The Cook buys cooked fish steaks at 3 gold (owner, 2026-10-19: "Yes: add the Cook buying cooked fish steaks at 3 gold"). Stock UO:R has no buyer for
/// them; the Fisherman sells raw steaks at 3 and buys them at 1, so cooking a bought steak only breaks even and the buy-to-resell audit still holds.
/// </summary>
public class FishSteakBuyerTests
{
    [Fact]
    public void TheShardConfigHasTheCookBuyingFishSteaksAtThree()
    {
        var dir = new DirectoryInfo(System.AppContext.BaseDirectory);
        while (dir != null && !File.Exists(Path.Combine(dir.FullName, "data", "configuration", "shard-rules.json")))
        {
            dir = dir.Parent;
        }

        Assert.NotNull(dir);
        var rules = JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(Path.Combine(dir!.FullName, "data", "configuration", "shard-rules.json")));
        var steak = rules!.ExtraVendorBuyers.Loot.Single(l => l.Item == "FishSteak");
        Assert.Equal(3, steak.Price);
        Assert.Equal(new[] { "Cook" }, steak.Vendors);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }
}
