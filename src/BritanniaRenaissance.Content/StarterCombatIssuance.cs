using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public static class StarterCombatIssuance
{
    private const string ProcessedTagPrefix = "BritanniaRenaissance.StarterCombatProcessed.v1.";
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        CharacterCreation.CharacterCreatedHandler += Issue;
    }

    public static void Issue(CharacterCreatedEventArgs args)
    {
        if (ShardRulesConfiguration.Settings?.FeatureFlags.Alpha3StarterCombatGear != true ||
            args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player ||
            player.Account is not Account account)
        {
            return;
        }

        var processedTag = $"{ProcessedTagPrefix}{player.Serial.Value}";
        if (account.GetTag(processedTag) is not null)
        {
            return;
        }

        var selectedSkills = ProfessionInfo.GetProfession(args.Profession, out var profession)
            ? profession.Skills
            : args.Skills;
        var selection = StarterPackagePlanner.Select(selectedSkills);
        var combat = selection.PrimaryCombatSkill is { } primary &&
                     player.Skills[primary].BaseFixedPoint > 0
            ? selection.Combat
            : StarterCombatPackage.None;
        var magerySelected = Selected(SkillName.Magery);
        var healingSelected = Selected(SkillName.Healing);
        var archerySelected = Selected(SkillName.Archery);

        bool Selected(SkillName skill) =>
            selectedSkills.Any(entry => entry.Item1 == skill && entry.Item2 > 0) &&
            player.Skills[skill].BaseFixedPoint > 0;

        // Stock creation grants an unrestricted dagger to everyone. Keep that useful
        // fallback, but prevent character recreation from extracting it for resale.
        RemoveExact(player, typeof(Dagger));
        player.Backpack.DropItem(new StarterDagger(player));

        if (combat != StarterCombatPackage.None)
        {
            RemoveExact(player, typeof(Katana), typeof(Club), typeof(Kryss),
                typeof(Bow), typeof(Crossbow));
        }

        if (combat is StarterCombatPackage.Melee or StarterCombatPackage.Archer)
        {
            RemoveArmor(player);
            if (combat == StarterCombatPackage.Melee)
            {
                EquipOrPack(player, new StarterStuddedChest(player));
                EquipOrPack(player, new StarterStuddedLegs(player));
                Item weapon = selection.PrimaryCombatSkill switch
                {
                    SkillName.Macing => new StarterClub(player),
                    SkillName.Fencing => new StarterKryss(player),
                    _ => new StarterKatana(player)
                };
                EquipOrPack(player, weapon);
                if (selection.Shield)
                {
                    EquipOrPack(player, new StarterWoodenShield(player));
                }
            }
            else
            {
                EquipOrPack(player, new StarterLeatherChest(player));
                EquipOrPack(player, new StarterLeatherLegs(player));
                EquipOrPack(player, new StarterBow(player));
            }
        }

        if (healingSelected || combat is StarterCombatPackage.Melee or StarterCombatPackage.Archer)
        {
            RemoveExact(player, typeof(Bandage));
            player.Backpack.DropItem(new StarterBandage(player, 50));
        }

        if (archerySelected)
        {
            RemoveExact(player, typeof(Arrow));
            if (combat == StarterCombatPackage.Archer)
            {
                player.Backpack.DropItem(new StarterArrow(player, 100));
            }
        }

        if (magerySelected)
        {
            RemoveExact(player, typeof(BagOfReagents), typeof(Spellbook));
            RemoveStockScrolls(player);
            var book = new StarterSpellbook(player);
            if (combat == StarterCombatPackage.Mage)
            {
                EquipOrPack(player, book);
            }
            else
            {
                player.Backpack.DropItem(book);
            }

            foreach (var reagent in StarterCraftMaterialIssuance.CreateReagents(player))
            {
                player.Backpack.DropItem(reagent);
            }
        }

        account.SetTag(processedTag, "processed");
    }

    private static void EquipOrPack(PlayerMobile player, Item item)
    {
        if (!player.EquipItem(item))
        {
            player.Backpack.DropItem(item);
        }
    }

    private static void RemoveArmor(PlayerMobile player)
    {
        foreach (var item in player.Items.ToArray())
        {
            if (item is BaseArmor)
            {
                item.Delete();
            }
        }

        foreach (var item in player.Backpack.Items.ToArray())
        {
            if (item is BaseArmor)
            {
                item.Delete();
            }
        }
    }

    private static void RemoveExact(PlayerMobile player, params Type[] types)
    {
        foreach (var item in player.Items.ToArray())
        {
            if (types.Contains(item.GetType()))
            {
                item.Delete();
            }
        }

        foreach (var item in player.Backpack.Items.ToArray())
        {
            if (types.Contains(item.GetType()))
            {
                item.Delete();
            }
        }
    }

    private static void RemoveStockScrolls(PlayerMobile player)
    {
        foreach (var item in player.Backpack.Items.ToArray())
        {
            if (item is SpellScroll && item is not IStarterIssued)
            {
                item.Delete();
            }
        }
    }
}
