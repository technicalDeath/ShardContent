using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Owner ruling (2026-09-28): starter craft materials and tools are newbied only, not bound,
/// matching Feature G. Stock creation grants stay as-is; this observer only tops up quantities
/// stock under-grants and adds what stock is missing entirely (Tinker iron, Tailor cloth/leather,
/// Bowyer/Scribe tools, Scribe/Alchemist reagents), gated once per account per category (H-1) -
/// which also fixes H-2: a second same-profession character keeps its own ordinary stock grant
/// instead of losing it to a deletion that used to run before the entitlement check.
/// See Alpha-3-Contract-Review.md H-1 through H-6.
/// </summary>
public static class StarterCraftMaterialIssuance
{
    private const string EntitlementTagPrefix = "BritanniaRenaissance.StarterCraftMaterials.v2.";

    // Owner ruling (2026-09-28): a fixed, predictable tool life for every starter crafter, rather
    // than stock's own random 25-75 uses (BaseTool(int) : this(Utility.RandomMinMax(25, 75), ...)).
    private const int ToolUses = 50;

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
        if (ShardRulesConfiguration.Settings?.FeatureFlags.Alpha3StarterCraftMaterials != true ||
            args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player ||
            player.Account is not Account account)
        {
            return;
        }

        var pack = player.Backpack;
        var selectedSkills = ProfessionInfo.GetProfession(args.Profession, out var profession)
            ? profession.Skills
            : args.Skills;
        var selection = StarterPackagePlanner.Select(selectedSkills);

        bool Has(StarterCraftPackage craft, SkillName skill) =>
            selection.CraftPackages.Contains(craft) && player.Skills[skill].BaseFixedPoint > 0;

        if (Has(StarterCraftPackage.Blacksmith, SkillName.Blacksmith))
        {
            ClaimOnce(account, StarterCraftPackage.Blacksmith, () =>
            {
                TopUp<IronIngot>(pack, 250);
                SetToolUses<Tongs>(pack);
                SetToolUses<Pickaxe>(pack);
            });
        }

        if (Has(StarterCraftPackage.Tinker, SkillName.Tinkering))
        {
            ClaimOnce(account, StarterCraftPackage.Tinker, () =>
            {
                // Stock Tinkering never grants ingots, in any era - only three random tinker
                // parts. Tinkering's own recipes (Gears, Scissors, ...) consume ingots though, so
                // add them; this merges with any ingots Blacksmith/Mining already granted.
                pack.DropItem(Newbied(new IronIngot(200)));
                SetToolUses<TinkerTools>(pack);
            });
        }

        if (Has(StarterCraftPackage.Tailor, SkillName.Tailoring))
        {
            ClaimOnce(account, StarterCraftPackage.Tailor, () =>
            {
                // Stock grants a BoltOfCloth, which Tailoring recipes cannot consume as a Cloth
                // resource, and no Leather at all; add the actual resource types instead of
                // "topping up" a stock grant that crafting can't use.
                pack.DropItem(Newbied(new Cloth(300)));
                pack.DropItem(Newbied(new Leather(50)));
                SetToolUses<SewingKit>(pack);
            });
        }

        if (Has(StarterCraftPackage.Carpenter, SkillName.Carpentry))
        {
            ClaimOnce(account, StarterCraftPackage.Carpenter, () =>
            {
                TopUp<Board>(pack, 250);
                SetToolUses<Saw>(pack);
            });
        }

        if (Has(StarterCraftPackage.Bowyer, SkillName.Fletching))
        {
            ClaimOnce(account, StarterCraftPackage.Bowyer, () =>
            {
                TopUp<Board>(pack, 200);
                TopUp<Feather>(pack, 100);
                // Stock grants no tool at all for Fletching.
                pack.DropItem(Newbied(new FletcherTools(ToolUses)));
            });
        }

        if (Has(StarterCraftPackage.Scribe, SkillName.Inscribe))
        {
            ClaimOnce(account, StarterCraftPackage.Scribe, () =>
            {
                TopUp<BlankScroll>(pack, 75);
                // Stock grants no reagents at all for Inscription; the stock BagOfReagents
                // constructor already gives 50 of each classic reagent, matching the target.
                pack.DropItem(Newbied(new BagOfReagents(50)));
                // Stock grants no tool at all for Inscription.
                pack.DropItem(Newbied(new ScribesPen(ToolUses)));
            });
        }

        if (Has(StarterCraftPackage.Alchemist, SkillName.Alchemy))
        {
            ClaimOnce(account, StarterCraftPackage.Alchemist, () =>
            {
                TopUp<Bottle>(pack, 75);
                pack.DropItem(Newbied(new BagOfReagents(50)));
                SetToolUses<MortarPestle>(pack);
            });
        }

        if (Has(StarterCraftPackage.Cook, SkillName.Cooking))
        {
            ClaimOnce(account, StarterCraftPackage.Cook, () =>
            {
                // Stock grants one each of lamb, chicken and fish (plus kindling and a fixed
                // 20-use flour sack/pitcher, both left untouched); top up the three stackable
                // proteins so a new cook can actually practice more than a single recipe.
                TopUp<RawLambLeg>(pack, 20);
                TopUp<RawChickenLeg>(pack, 20);
                TopUp<RawFishSteak>(pack, 20);
            });
        }
    }

    private static void ClaimOnce(Account account, StarterCraftPackage craft, Action grant)
    {
        var tag = $"{EntitlementTagPrefix}{craft}";
        if (account.GetTag(tag) is not null)
        {
            return;
        }

        grant();
        account.SetTag(tag, "issued");
    }

    private static void TopUp<T>(Container container, int target) where T : Item
    {
        var item = container.FindItemByType<T>();
        if (item is not null && item.Amount < target)
        {
            item.Amount = target;
        }
    }

    private static void SetToolUses<T>(Container container) where T : Item, IUsesRemaining
    {
        foreach (var tool in container.FindItemsByType<T>())
        {
            tool.UsesRemaining = ToolUses;
        }
    }

    private static T Newbied<T>(T item) where T : Item
    {
        item.LootType = LootType.Newbied;
        return item;
    }
}
