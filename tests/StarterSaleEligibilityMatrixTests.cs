using System.Reflection;
using System.Runtime.CompilerServices;
using BritanniaRenaissance.Content;
using Server;
using Server.Items;
using Server.Mobiles;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class StarterSaleEligibilityMatrixTests
{
    [Fact]
    public void UnmarkedBackpackWardRemainsEligibleForNpcSaleAndResale()
    {
        var ward = (BackpackWard)RuntimeHelpers.GetUninitializedObject(typeof(BackpackWard));
        var sellInfo = new GenericSellInfo();
        sellInfo.Add(typeof(BackpackWard), 1);

        Assert.False(ward.IsStarterIssued);
        Assert.False(ward.Nontransferable);
        Assert.True(sellInfo.IsSellable(ward));
        Assert.True(sellInfo.IsResellable(ward));
    }

    [Fact]
    public void EveryBoundStarterTypeIsIneligibleForNpcSaleAndResale()
    {
        var types = new[]
        {
            typeof(StarterScissors), typeof(StarterIronIngot), typeof(BackpackWard),
            typeof(StarterKatana), typeof(StarterClub), typeof(StarterKryss), typeof(StarterBow),
            typeof(StarterDagger), typeof(StarterStuddedChest), typeof(StarterStuddedLegs),
            typeof(StarterLeatherChest), typeof(StarterLeatherLegs), typeof(StarterWoodenShield),
            typeof(StarterSpellbook), typeof(StarterBandage), typeof(StarterArrow),
            typeof(StarterTongs), typeof(StarterPickaxe), typeof(StarterTinkerTools), typeof(StarterSewingKit),
            typeof(StarterSaw), typeof(StarterFletcherTools), typeof(StarterScribesPen), typeof(StarterMortarPestle),
            typeof(StarterRawFishSteak), typeof(StarterKindling), typeof(StarterBoard), typeof(StarterFeather),
            typeof(StarterCloth), typeof(StarterLeather), typeof(StarterBlankScroll), typeof(StarterBottle),
            typeof(StarterBlackPearl), typeof(StarterBloodmoss), typeof(StarterGarlic), typeof(StarterGinseng),
            typeof(StarterMandrakeRoot), typeof(StarterNightshade), typeof(StarterSulfurousAsh),
            typeof(StarterSpidersSilk)
        };

        var wardStarterMarker = typeof(BackpackWard).GetField("_starterIssued", BindingFlags.Instance | BindingFlags.NonPublic);
        Assert.NotNull(wardStarterMarker);
        var sellInfo = new GenericSellInfo();

        foreach (var type in types)
        {
            var item = (Item)RuntimeHelpers.GetUninitializedObject(type);
            if (type == typeof(BackpackWard))
            {
                wardStarterMarker.SetValue(item, true);
            }
            else
            {
                Assert.True(typeof(IStarterIssued).IsAssignableFrom(type), type.Name);
            }

            sellInfo.Add(type, 1);
            Assert.True(item.Nontransferable, type.Name);
            Assert.False(sellInfo.IsSellable(item), type.Name);
            Assert.False(sellInfo.IsResellable(item), type.Name);
        }

        Assert.Equal(40, types.Length);
    }
}
