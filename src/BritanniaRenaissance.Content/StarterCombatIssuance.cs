using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Owner ruling (2026-09-28): starter combat gear and consumables are newbied only, not bound.
/// This shard's UOR era already stamps every stock creation grant Newbied with no shard code
/// (CharacterCreation.EquipItem/PackItem, gated on !Core.AOS), so this observer only tops up
/// quantities stock under-grants and patches gaps stock leaves empty. It never deletes or
/// replaces anything stock already issued. See Alpha-3-Contract-Review.md G-1 through G-3.
/// </summary>
public static class StarterCombatIssuance
{
    private const string ProcessedTagPrefix = "BritanniaRenaissance.StarterCombatProcessed.v2.";
    private const int ArrowTarget = 100;
    private const int ReagentTarget = 50;
    private const int BandageTarget = 50;

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

        var pack = player.Backpack;
        var selectedSkills = ProfessionInfo.GetProfession(args.Profession, out var profession)
            ? profession.Skills
            : args.Skills;
        var selection = StarterPackagePlanner.Select(selectedSkills);

        bool Selected(SkillName skill) =>
            selectedSkills.Any(entry => entry.Item1 == skill && entry.Item2 > 0) &&
            player.Skills[skill].BaseFixedPoint > 0;

        // Stock grants 25 arrows for Archery regardless of whether it is the character's
        // strongest selected combat skill; raise that stack to the approved quantity the same way.
        if (Selected(SkillName.Archery))
        {
            TopUpOrGrant(pack, ArrowTarget, () => new Arrow(ArrowTarget));
        }

        if (Selected(SkillName.Magery))
        {
            // Stock's reagent grant is a nested BagOfReagents with 30 of each classic reagent;
            // leave that container structure alone and just raise each stack inside it.
            if (pack.FindItemByType<BagOfReagents>() is { } reagentBag)
            {
                TopUp<BlackPearl>(reagentBag, ReagentTarget);
                TopUp<Bloodmoss>(reagentBag, ReagentTarget);
                TopUp<Garlic>(reagentBag, ReagentTarget);
                TopUp<Ginseng>(reagentBag, ReagentTarget);
                TopUp<MandrakeRoot>(reagentBag, ReagentTarget);
                TopUp<Nightshade>(reagentBag, ReagentTarget);
                TopUp<SulfurousAsh>(reagentBag, ReagentTarget);
                TopUp<SpidersSilk>(reagentBag, ReagentTarget);
            }

            // Stock's Spellbook constructor unconditionally sets LootType.Blessed, which stays:
            // spellbooks are conventionally blessed. The vendor-sale guard (Newbied/Nontransferable
            // only) doesn't cover Blessed, so this one item remains vendor-sellable — an accepted,
            // minor residual alongside the rest of G-3's few-gold resale tradeoff.
        }

        if (selection.Combat is StarterCombatPackage.Melee or StarterCombatPackage.Archer)
        {
            // Stock grants archers no armor at all (only a bow and arrows); melee professions
            // that do match a stock profession branch already have their own armor and don't
            // need this patch.
            if (selection.Combat == StarterCombatPackage.Archer)
            {
                EquipOrPack(player, Newbied(new LeatherChest()));
                EquipOrPack(player, Newbied(new LeatherLegs()));
            }

            // Stock never grants a shield to anyone, even with Parry selected.
            if (selection.Shield)
            {
                EquipOrPack(player, Newbied(new WoodenShield()));
            }

            // Stock only grants bandages via Healing (50), Veterinary (5) or Anatomy (3); top up
            // to the approved quantity regardless of which of those, if any, was selected.
            TopUpOrGrant(pack, BandageTarget, () => new Bandage(BandageTarget));
        }

        account.SetTag(processedTag, "processed");
    }

    private static void TopUp<T>(Container container, int target) where T : Item
    {
        var item = container.FindItemByType<T>();
        if (item is not null && item.Amount < target)
        {
            item.Amount = target;
        }
    }

    private static void TopUpOrGrant<T>(Container container, int target, Func<T> create) where T : Item
    {
        var item = container.FindItemByType<T>();
        if (item is not null)
        {
            if (item.Amount < target)
            {
                item.Amount = target;
            }
        }
        else
        {
            container.DropItem(Newbied(create()));
        }
    }

    private static T Newbied<T>(T item) where T : Item
    {
        item.LootType = LootType.Newbied;
        return item;
    }

    private static void EquipOrPack(PlayerMobile player, Item item)
    {
        if (!player.EquipItem(item))
        {
            player.Backpack!.DropItem(item);
        }
    }
}
