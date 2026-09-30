using BritanniaRenaissance.Content;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class StarterCombatIssuanceTests
{
    [Fact]
    public void WarriorTacticsAndSwordsGrantsKeepOneKatanaAndOneShield()
    {
        // Stock: Tactics equips a Katana, Swords packs a second; Parry equips a shield.
        var gear = new (Type Type, bool Equipped)[]
        {
            (typeof(Katana), true),
            (typeof(WoodenShield), true),
            (typeof(Katana), false)
        };

        Assert.Equal([2], StarterCombatIssuance.SelectDuplicateGear(gear));
    }

    [Fact]
    public void EquippedCopyIsKeptOverAnEarlierPackedCopy()
    {
        var gear = new (Type Type, bool Equipped)[]
        {
            (typeof(Katana), false),
            (typeof(Katana), true)
        };

        Assert.Equal([0], StarterCombatIssuance.SelectDuplicateGear(gear));
    }

    [Fact]
    public void DifferentWeaponTypesAreAllKept()
    {
        var gear = new (Type Type, bool Equipped)[]
        {
            (typeof(Katana), true),
            (typeof(Club), false),
            (typeof(Bow), false)
        };

        Assert.Empty(StarterCombatIssuance.SelectDuplicateGear(gear));
    }

    [Fact]
    public void SameTypeHueAndLootTypeStacksFoldIntoTheFirst()
    {
        var stacks = new (Type Type, int Hue, int LootType)[]
        {
            (typeof(IronIngot), 0, 2),
            (typeof(Cloth), 0, 2),
            (typeof(IronIngot), 0, 2),
            (typeof(IronIngot), 0, 0),
            (typeof(IronIngot), 0, 2)
        };

        Assert.Equal([(0, 2), (0, 4)], StarterCraftMaterialIssuance.SelectStackMerges(stacks));
    }
}
