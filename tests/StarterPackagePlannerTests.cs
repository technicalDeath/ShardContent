using Server;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class StarterPackagePlannerTests
{
    [Fact]
    public void ActiveWarriorTemplateSelectsSwordPackageAndNoCraftMaterials()
    {
        var plan = StarterPackagePlanner.Select([
            (SkillName.Tactics, 50), (SkillName.Healing, 45), (SkillName.Swords, 5)
        ]);

        Assert.Equal(StarterCombatPackage.Melee, plan.Combat);
        Assert.Equal(SkillName.Swords, plan.PrimaryCombatSkill);
        Assert.False(plan.Shield);
        Assert.Empty(plan.CraftPackages);
    }

    [Fact]
    public void ActiveMageTemplateSelectsMagePackage()
    {
        var plan = StarterPackagePlanner.Select([
            (SkillName.Magery, 50), (SkillName.Meditation, 50), (SkillName.Wrestling, 0)
        ]);

        Assert.Equal(StarterCombatPackage.Mage, plan.Combat);
        Assert.Equal(SkillName.Magery, plan.PrimaryCombatSkill);
        Assert.Empty(plan.CraftPackages);
    }

    [Fact]
    public void ActiveBlacksmithTemplateClaimsBothSelectedCraftCategories()
    {
        var plan = StarterPackagePlanner.Select([
            (SkillName.Blacksmith, 50), (SkillName.Tinkering, 45), (SkillName.Mining, 5)
        ]);

        Assert.Equal(StarterCombatPackage.None, plan.Combat);
        Assert.Equal([StarterCraftPackage.Blacksmith, StarterCraftPackage.Tinker], plan.CraftPackages);
    }

    [Fact]
    public void AdvancedHybridUsesStrongestCombatSkillAndKeepsIndependentCraftSelection()
    {
        var plan = StarterPackagePlanner.Select([
            (SkillName.Archery, 40), (SkillName.Magery, 50), (SkillName.Fletching, 30),
            (SkillName.Parry, 10), (SkillName.Fletching, 30)
        ]);

        Assert.Equal(StarterCombatPackage.Mage, plan.Combat);
        Assert.Equal(SkillName.Magery, plan.PrimaryCombatSkill);
        Assert.False(plan.Shield);
        Assert.Equal([StarterCraftPackage.Bowyer], plan.CraftPackages);
    }

    [Fact]
    public void EqualCombatSkillsFollowSelectedSkillOrder()
    {
        var plan = StarterPackagePlanner.Select([
            (SkillName.Archery, 50), (SkillName.Magery, 50)
        ]);

        Assert.Equal(StarterCombatPackage.Archer, plan.Combat);
        Assert.Equal(SkillName.Archery, plan.PrimaryCombatSkill);
    }

    [Fact]
    public void MeleeWithParrySelectsOrdinaryShield()
    {
        var plan = StarterPackagePlanner.Select([
            (SkillName.Macing, 45), (SkillName.Parry, 40)
        ]);

        Assert.Equal(StarterCombatPackage.Melee, plan.Combat);
        Assert.Equal(SkillName.Macing, plan.PrimaryCombatSkill);
        Assert.True(plan.Shield);
    }
}
