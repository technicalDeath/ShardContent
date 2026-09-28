using Server;

namespace BritanniaRenaissance.Content;

public enum StarterCombatPackage
{
    None,
    Melee,
    Archer,
    Mage
}

public enum StarterCraftPackage
{
    Blacksmith,
    Tinker,
    Tailor,
    Carpenter,
    Bowyer,
    Scribe,
    Alchemist,
    Cook
}

public sealed record StarterPackageSelection(
    StarterCombatPackage Combat,
    SkillName? PrimaryCombatSkill,
    bool Shield,
    IReadOnlyList<StarterCraftPackage> CraftPackages
);

public static class StarterPackagePlanner
{
    public static StarterPackageSelection Select(ReadOnlySpan<(SkillName Skill, byte Value)> startingSkills)
    {
        var combat = StarterCombatPackage.None;
        SkillName? primarySkill = null;
        var bestValue = 0;
        var shield = false;
        var crafts = new List<StarterCraftPackage>();

        foreach (var (skill, value) in startingSkills)
        {
            if (value == 0)
            {
                continue;
            }

            if (skill == SkillName.Parry)
            {
                shield = true;
            }

            var candidate = skill switch
            {
                SkillName.Swords or SkillName.Macing or SkillName.Fencing => StarterCombatPackage.Melee,
                SkillName.Archery => StarterCombatPackage.Archer,
                SkillName.Magery => StarterCombatPackage.Mage,
                _ => StarterCombatPackage.None
            };
            if (candidate != StarterCombatPackage.None && value > bestValue)
            {
                combat = candidate;
                primarySkill = skill;
                bestValue = value;
            }

            var craft = skill switch
            {
                SkillName.Blacksmith => StarterCraftPackage.Blacksmith,
                SkillName.Tinkering => StarterCraftPackage.Tinker,
                SkillName.Tailoring => StarterCraftPackage.Tailor,
                SkillName.Carpentry => StarterCraftPackage.Carpenter,
                SkillName.Fletching => StarterCraftPackage.Bowyer,
                SkillName.Inscribe => StarterCraftPackage.Scribe,
                SkillName.Alchemy => StarterCraftPackage.Alchemist,
                SkillName.Cooking => StarterCraftPackage.Cook,
                _ => (StarterCraftPackage?)null
            };
            if (craft is { } package && !crafts.Contains(package))
            {
                crafts.Add(package);
            }
        }

        return new StarterPackageSelection(combat, primarySkill,
            combat == StarterCombatPackage.Melee && shield, crafts);
    }
}
