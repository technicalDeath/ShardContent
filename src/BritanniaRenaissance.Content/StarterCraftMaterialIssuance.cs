using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

public static class StarterCraftMaterialIssuance
{
    private const string EntitlementTagPrefix = "BritanniaRenaissance.StarterCraftMaterials.v1.";
    private const string ProcessedTagPrefix = "BritanniaRenaissance.StarterCraftProcessed.v1.";
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

        var processedTag = $"{ProcessedTagPrefix}{player.Serial.Value}";
        if (account.GetTag(processedTag) is not null)
        {
            return;
        }

        var selectedSkills = ProfessionInfo.GetProfession(args.Profession, out var profession)
            ? profession.Skills
            : args.Skills;
        var selection = StarterPackagePlanner.Select(selectedSkills);
        var hasBlacksmith = selection.CraftPackages.Contains(StarterCraftPackage.Blacksmith) &&
                            player.Skills[SkillName.Blacksmith].BaseFixedPoint > 0;
        var hasTinker = selection.CraftPackages.Contains(StarterCraftPackage.Tinker) &&
                        player.Skills[SkillName.Tinkering].BaseFixedPoint > 0;
        var hasTailor = selection.CraftPackages.Contains(StarterCraftPackage.Tailor) &&
                        player.Skills[SkillName.Tailoring].BaseFixedPoint > 0;
        var hasCarpenter = selection.CraftPackages.Contains(StarterCraftPackage.Carpenter) &&
                           player.Skills[SkillName.Carpentry].BaseFixedPoint > 0;
        var hasBowyer = selection.CraftPackages.Contains(StarterCraftPackage.Bowyer) &&
                        player.Skills[SkillName.Fletching].BaseFixedPoint > 0;
        var hasScribe = selection.CraftPackages.Contains(StarterCraftPackage.Scribe) &&
                        player.Skills[SkillName.Inscribe].BaseFixedPoint > 0;
        var hasAlchemist = selection.CraftPackages.Contains(StarterCraftPackage.Alchemist) &&
                           player.Skills[SkillName.Alchemy].BaseFixedPoint > 0;
        var hasCook = selection.CraftPackages.Contains(StarterCraftPackage.Cook) &&
                      player.Skills[SkillName.Cooking].BaseFixedPoint > 0;

        if (hasBlacksmith)
        {
            // Stock Blacksmith supplies include an unrestricted 50-ingot stack.
            RemoveStock(player.Backpack, typeof(IronIngot));
            ReplaceStockTools(player, [typeof(Tongs), typeof(Pickaxe)],
                new StarterTongs(player), new StarterPickaxe(player));
            Claim(account, player, StarterCraftPackage.Blacksmith,
                () => [new StarterIronIngot(player, 250)]);
        }

        if (hasTinker)
        {
            // Stock UOR creation adds three transferable random parts per Tinkering pick.
            RemoveStock(player.Backpack, typeof(Axle), typeof(Gears), typeof(Hinge), typeof(Springs));
            ReplaceStockTools(player, [typeof(TinkerTools)], new StarterTinkerTools(player));
            Claim(account, player, StarterCraftPackage.Tinker,
                () => [new StarterIronIngot(player, 200)]);
        }

        if (hasTailor)
        {
            RemoveStock(player.Backpack, typeof(BoltOfCloth));
            ReplaceStockTools(player, [typeof(SewingKit)], new StarterSewingKit(player));
            Claim(account, player, StarterCraftPackage.Tailor,
                () => [new StarterCloth(player, 300), new StarterLeather(player, 50)]);
        }

        if (hasCarpenter || hasBowyer)
        {
            RemoveStock(player.Backpack, typeof(Board));
        }

        if (hasCarpenter)
        {
            ReplaceStockTools(player, [typeof(Saw)], new StarterSaw(player));
            Claim(account, player, StarterCraftPackage.Carpenter,
                () => [new StarterBoard(player, 250)]);
        }

        if (hasBowyer)
        {
            RemoveStock(player.Backpack, typeof(Feather), typeof(Shaft));
            ReplaceStockTools(player, [typeof(FletcherTools)], new StarterFletcherTools(player));
            Claim(account, player, StarterCraftPackage.Bowyer,
                () => [new StarterBoard(player, 200), new StarterFeather(player, 100)]);
        }

        if (hasScribe)
        {
            RemoveStock(player.Backpack, typeof(BlankScroll));
            ReplaceStockTools(player, [typeof(ScribesPen)], new StarterScribesPen(player));
            Claim(account, player, StarterCraftPackage.Scribe,
                () => [new StarterBlankScroll(player, 75), .. CreateReagents(player)]);
        }

        if (hasAlchemist)
        {
            RemoveStock(player.Backpack, typeof(Bottle));
            ReplaceStockTools(player, [typeof(MortarPestle)], new StarterMortarPestle(player));
            Claim(account, player, StarterCraftPackage.Alchemist,
                () => [new StarterBottle(player, 75), .. CreateReagents(player)]);
        }

        if (hasCook)
        {
            RemoveStock(player.Backpack, typeof(Kindling), typeof(RawLambLeg),
                typeof(RawChickenLeg), typeof(RawFishSteak), typeof(SackFlour), typeof(Pitcher));
            Claim(account, player, StarterCraftPackage.Cook,
                () => [new StarterRawFishSteak(player, 60), new StarterKindling(player, 2)]);
        }

        account.SetTag(processedTag, "processed");
    }

    private static void RemoveStock(Container pack, params Type[] types)
    {
        var stock = new List<Item>();
        foreach (var item in pack.Items)
        {
            if (types.Contains(item.GetType()))
            {
                stock.Add(item);
            }
        }

        foreach (var item in stock)
        {
            item.Delete();
        }
    }

    private static void ReplaceStockTools(PlayerMobile player, Type[] stockTypes, params Item[] tools)
    {
        RemoveStock(player.Backpack, stockTypes);
        foreach (var tool in tools)
        {
            player.Backpack.DropItem(tool);
        }
    }

    private static void Claim(Account account, PlayerMobile player, StarterCraftPackage craft,
        Func<Item[]> createItems)
    {
        var tag = $"{EntitlementTagPrefix}{craft}";
        if (account.GetTag(tag) is not null)
        {
            return;
        }

        foreach (var item in createItems())
        {
            player.Backpack.DropItem(item);
        }

        account.SetTag(tag, "issued");
    }

    internal static Item[] CreateReagents(PlayerMobile player) =>
    [
        new StarterBlackPearl(player, 50),
        new StarterBloodmoss(player, 50),
        new StarterGarlic(player, 50),
        new StarterGinseng(player, 50),
        new StarterMandrakeRoot(player, 50),
        new StarterNightshade(player, 50),
        new StarterSulfurousAsh(player, 50),
        new StarterSpidersSilk(player, 50)
    ];
}
