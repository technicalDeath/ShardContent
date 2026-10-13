using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The server half of the combat bar's durability gauge (docs/Combat-Bar-Evidence.md).</summary>
public class CombatBarTests
{
    [Fact]
    public void ReplyBytes()
    {
        var reply = CombatBarService.Reply([(0x40001234u, (ushort)37, (ushort)50), (0x40005678u, (ushort)1, (ushort)30)]);

        Assert.Equal(6 + 2 * 8, reply.Length);
        Assert.Equal(0xBF, reply[0]);
        Assert.Equal(reply.Length, (reply[1] << 8) | reply[2]);
        Assert.Equal(0xA9, (reply[3] << 8) | reply[4]);
        Assert.Equal(2, reply[5]);
        Assert.Equal(new byte[] { 0x40, 0x00, 0x12, 0x34, 0, 37, 0, 50 }, reply[6..14]);
        Assert.Equal(new byte[] { 0x40, 0x00, 0x56, 0x78, 0, 1, 0, 30 }, reply[14..22]);
    }

    [Fact]
    public void TheFlagIsOnInTheShippedRulesSinceTheOwnerActivatedIt()
    {
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            System.IO.File.ReadAllText(System.IO.Path.Combine(System.AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        Assert.True(rules.FeatureFlags.CombatBar);   // activated 2026-10-12 on the owner's explicit "activate"
    }
}
