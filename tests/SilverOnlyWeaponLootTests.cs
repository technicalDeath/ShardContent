using BritanniaRenaissance.Content;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Monster-dropped weapons keep only the Silver slayer (docs/Slayer-Loot-Evidence.md).</summary>
public class SilverOnlyWeaponLootTests
{
    [Fact]
    public void SilverIsTheOnlySlayerAMonsterDroppedWeaponMayCarry() => Assert.True(SilverOnlyWeaponLoot.Allowed(SlayerName.Silver));

    [Theory]
    [InlineData(SlayerName.OrcSlaying)]
    [InlineData(SlayerName.TrollSlaughter)]
    [InlineData(SlayerName.OgreTrashing)]
    [InlineData(SlayerName.Repond)]
    [InlineData(SlayerName.DragonSlaying)]
    [InlineData(SlayerName.Exorcism)]
    [InlineData(SlayerName.None)]
    public void EveryOtherSlayerIsRefused(SlayerName slayer) => Assert.False(SilverOnlyWeaponLoot.Allowed(slayer));

    [Fact]
    public void EverySlayerNameExceptSilverIsRefused()
    {
        foreach (var name in System.Enum.GetValues<SlayerName>())
        {
            Assert.Equal(name == SlayerName.Silver, SilverOnlyWeaponLoot.Allowed(name));
        }
    }
}
