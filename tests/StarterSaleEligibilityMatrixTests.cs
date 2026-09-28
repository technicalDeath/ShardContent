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
        // Only D's scissors and F's Ward remain bound after G (2026-09-28) and H (2026-09-28)
        // moved their respective ~20 combat/craft bound types to newbied-only.
        var types = new[]
        {
            typeof(StarterScissors), typeof(BackpackWard)
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

        Assert.Equal(2, types.Length);
    }

    [Fact]
    public void NewbiedStarterItemsAreIneligibleForVendorSaleButNotNontransferable()
    {
        // Feature G (2026-09-28) and Feature H (2026-09-28): starter combat gear/consumables and
        // craft materials/tools are plain stock types, newbied only. A Newbied item is blocked
        // from vendor sale (alongside Nontransferable ones) so repeated character creation can't
        // be turned into gold, but it is not otherwise bound.
        var types = new[]
        {
            typeof(Katana), typeof(Club), typeof(Kryss), typeof(Bow), typeof(Dagger),
            typeof(StuddedChest), typeof(StuddedLegs), typeof(LeatherChest), typeof(LeatherLegs),
            typeof(WoodenShield), typeof(Spellbook), typeof(Bandage), typeof(Arrow),
            typeof(IronIngot), typeof(Tongs), typeof(Pickaxe), typeof(TinkerTools),
            typeof(Cloth), typeof(Leather), typeof(SewingKit), typeof(Board), typeof(Saw),
            typeof(Feather), typeof(FletcherTools), typeof(BlankScroll), typeof(ScribesPen),
            typeof(Bottle), typeof(MortarPestle), typeof(BagOfReagents),
            typeof(RawLambLeg), typeof(RawChickenLeg), typeof(RawFishSteak)
        };

        var sellInfo = new GenericSellInfo();

        foreach (var type in types)
        {
            var item = (Item)RuntimeHelpers.GetUninitializedObject(type);
            item.LootType = LootType.Newbied;
            sellInfo.Add(type, 1);

            Assert.False(item.Nontransferable, type.Name);
            Assert.False(sellInfo.IsSellable(item), type.Name);
            Assert.False(sellInfo.IsResellable(item), type.Name);
        }
    }

    [Fact]
    public void OrdinaryRegularLootItemsRemainSellable()
    {
        var item = (Item)RuntimeHelpers.GetUninitializedObject(typeof(Katana));
        var sellInfo = new GenericSellInfo();
        sellInfo.Add(typeof(Katana), 1);

        Assert.Equal(LootType.Regular, item.LootType);
        Assert.False(item.Nontransferable);
        Assert.True(sellInfo.IsSellable(item));
        Assert.True(sellInfo.IsResellable(item));
    }
}
