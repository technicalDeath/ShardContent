using Server;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The server half of the potion bar (docs/Potion-Bar-Evidence.md).</summary>
public class PotionBarTests
{
    [Theory]
    [InlineData(typeof(LesserHealPotion), 10)]
    [InlineData(typeof(HealPotion), 11)]
    [InlineData(typeof(GreaterHealPotion), 12)]
    [InlineData(typeof(LesserCurePotion), 20)]
    [InlineData(typeof(CurePotion), 21)]
    [InlineData(typeof(GreaterCurePotion), 22)]
    [InlineData(typeof(RefreshPotion), 31)]
    [InlineData(typeof(TotalRefreshPotion), 32)]
    [InlineData(typeof(AgilityPotion), 41)]
    [InlineData(typeof(GreaterAgilityPotion), 42)]
    [InlineData(typeof(StrengthPotion), 51)]
    [InlineData(typeof(GreaterStrengthPotion), 52)]
    public void EveryPotionOfTheBarHasItsOwnCode(Type type, int expected)
    {
        Assert.Equal(expected, PotionBarService.CodeOf(type));
    }

    [Fact]
    public void PotionsAndOtherItemsTheBarDoesNotShowHaveNoCode()
    {
        foreach (var type in new[] { typeof(NightSightPotion), typeof(LesserExplosionPotion), typeof(LesserPoisonPotion), typeof(Bottle), typeof(Bandage), typeof(BasePotion), typeof(Item) })
        {
            Assert.Equal(0, PotionBarService.CodeOf(type));
        }
    }

    [Fact]
    public void TheCodesAreUniqueAndSplitIntoKindAndStrength()
    {
        var codes = new[] { 10, 11, 12, 20, 21, 22, 31, 32, 41, 42, 51, 52 };

        Assert.Equal(codes.Length, codes.Distinct().Count());
        Assert.All(codes, static c => Assert.InRange(c / 10, 1, 5));
        Assert.All(codes, static c => Assert.InRange(c % 10, 0, 2));
    }

    [Fact]
    public void TheReplyIsOneExtendedCommandWithASerialAndACodeForEachPotion()
    {
        var reply = PotionBarService.Reply([(0x40001234u, (byte)12), (0x40005678u, (byte)21)]);

        Assert.Equal(6 + 2 * 5, reply.Length);
        Assert.Equal(0xBF, reply[0]);
        Assert.Equal(reply.Length, (reply[1] << 8) | reply[2]);
        Assert.Equal(0xA7, (reply[3] << 8) | reply[4]);
        Assert.Equal(2, reply[5]);
        Assert.Equal(new byte[] { 0x40, 0x00, 0x12, 0x34, 12 }, reply[6..11]);
        Assert.Equal(new byte[] { 0x40, 0x00, 0x56, 0x78, 21 }, reply[11..16]);
    }

    [Fact]
    public void TheBarIsOnInTheShippedRulesSinceTheOwnerActivatedItAndStartsThreeHealAndThreeRefresh()
    {
        var rules = System.Text.Json.JsonSerializer.Deserialize<ShardRules>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

        Assert.True(rules.FeatureFlags.PotionBar);   // activated 2026-10-12 on the owner's explicit "Activate"
        Assert.Equal(3, PotionBarService.StarterHeal);
        Assert.Equal(3, PotionBarService.StarterRefresh);
    }
}
