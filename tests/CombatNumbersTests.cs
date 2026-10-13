using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CombatNumbersTests
{
    [Fact]
    public void TheHealPacketCarriesTheSerialAndTheAmount()
    {
        Assert.Equal(
            new byte[] { 0xBF, 0, 11, 0, 0xAB, 0x12, 0x34, 0x56, 0x78, 0x00, 25 },
            CombatNumbersService.HealPacket(0x12345678, 25)
        );
    }

    [Fact]
    public void TheAmountIsKeptInTwoBytes()
    {
        var big = CombatNumbersService.HealPacket(1, 70000);
        var negative = CombatNumbersService.HealPacket(1, -5);

        Assert.Equal(new byte[] { 0xFF, 0xFF }, big[9..11]);
        Assert.Equal(new byte[] { 0x00, 0x00 }, negative[9..11]);
    }

    [Fact]
    public void ThePacketIsAnExtendedCommandOfTheRightLength()
    {
        var packet = CombatNumbersService.HealPacket(0xABCDEF01, 300);

        Assert.Equal(0xBF, packet[0]);
        Assert.Equal(packet.Length, (packet[1] << 8) | packet[2]);
        Assert.Equal(CombatNumbersService.HealCommand, (packet[3] << 8) | packet[4]);
        Assert.Equal(0x012C, (packet[9] << 8) | packet[10]);
    }

    [Fact]
    public void TheCommandDoesNotClashWithTheOtherShardChannels()
    {
        // 0xA7 potion strengths, 0xA8 menu mask, 0xA9 durability, 0xAA auto-use cure
        Assert.DoesNotContain(CombatNumbersService.HealCommand, new[] { 0xA7, 0xA8, 0xA9, 0xAA });
    }

    [Fact]
    public void BothSwitchesAreOffWhenNoRulesAreLoaded()
    {
        Assert.False(new DeferredFeatureFlags().DamageNumbers);
        Assert.False(new DeferredFeatureFlags().HealNumbers);
    }
}
