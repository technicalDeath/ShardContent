using BritanniaRenaissance.Content;
using Server;
using Server.Accounting;
using Server.Commands;
using Server.Engines.Craft;
using Server.Engines.Craft.T2A;
using Server.Items;
using Server.Mobiles;

namespace Alpha3StarterEconomyProbe;

public static class StarterEconomyProbe
{
    private const string TestBlacksmithName = "A3 test blacksmith";
    private const string TestTinkerName = "A3 test tinker";
    private const string TestTailorName = "A3 test tailor";
    private static readonly List<Item> SeededItems = [];
    private static PlayerVendor? _vendor;
    private static Bag? _nestedBag;
    private static IronIngot? _nestedIron;

    public static void Configure() => CommandSystem.Register("StarterEconomyProbe", AccessLevel.Administrator, OnCommand);

    private static void OnCommand(CommandEventArgs e)
    {
        var action = e.GetString(0).ToLowerInvariant();
        if (action == "cleanup")
        {
            Cleanup(e.Mobile);
            return;
        }

        if (action == "trim")
        {
            Trim(e.GetString(1), e.Mobile);
            return;
        }

        if (action == "delete")
        {
            DeleteItem(e.GetString(1), e.Mobile);
            return;
        }

        if (action == "item")
        {
            VerifyItem(e.GetString(1), e.Mobile);
            return;
        }

        if (action == "inspectward")
        {
            InspectWardSalePath(e.GetString(1), e.Mobile);
            return;
        }

        if (action == "wardscan")
        {
            ScanWards(e.Mobile);
            return;
        }

        if (!TryPlayer(e.GetString(1), out var player))
        {
            e.Mobile.SendMessage("Starter economy probe could not find that player serial.");
            return;
        }

        switch (action)
        {
            case "seed":
                Seed(player!, e.Mobile);
                break;
            case "vendor":
                CreateVendor(player!, e.Mobile);
                break;
            case "tinkernpc":
                var tinker = new Tinker { Name = TestTinkerName };
                tinker.MoveToWorld(new Point3D(player!.X + 1, player.Y, player.Z), player.Map);
                e.Mobile.SendMessage($"Starter economy Tinker NPC: serial={tinker.Serial}; location={tinker.Location}; map={tinker.Map}; owner={player.Serial}.");
                break;
            case "tailornpc":
                var tailor = new Tailor { Name = TestTailorName };
                tailor.MoveToWorld(new Point3D(player!.X + 1, player.Y, player.Z), player.Map);
                e.Mobile.SendMessage($"Starter economy Tailor NPC: serial={tailor.Serial}; location={tailor.Location}; map={tailor.Map}; owner={player.Serial}.");
                break;
            case "legacyward":
                SeedUnmarkedWard(player!, e.Mobile);
                break;
            case "place":
                player!.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
                e.Mobile.SendMessage($"Starter economy paired client placed: player={player.Serial}; location={player.Location}; map={player.Map}.");
                break;
            case "salvage":
                SeedSalvageTargets(player!, e.Mobile);
                break;
            case "npc":
                SeedNpcSaleTargets(player!, e.Mobile);
                break;
            case "npcward":
                SeedLegacyWardNpcSaleTargets(player!, e.Mobile);
                break;
            case "transfers":
                SeedTransferMatrix(player!, e.Mobile);
                break;
            case "craft":
                SeedCraftingInputs(player!, e.Mobile);
                break;
            case "make":
                CraftDaggerFromStarterIngots(player!, e.Mobile);
                break;
            case "craftwood":
                SeedCarpentryInputs(player!, e.Mobile);
                break;
            case "makewood":
                CraftChairFromBoards(player!, e.Mobile);
                break;
            case "craftcloth":
                SeedTailoringInputs(player!, e.Mobile);
                break;
            case "makecloth":
                CraftShirtFromCloth(player!, e.Mobile);
                break;
            case "crafttinker":
                SeedTinkeringInputs(player!, e.Mobile);
                break;
            case "maketinker":
                CraftGearsFromStarterIngots(player!, e.Mobile);
                break;
            case "crafttinkerscissors":
                SeedTinkeringScissorsInputs(player!, e.Mobile);
                break;
            case "maketinkerscissors":
                CraftScissorsFromStarterIngots(player!, e.Mobile);
                break;
            case "craftleather":
                SeedTailoringLeather(player!, e.Mobile);
                break;
            case "makeleather":
                CraftLeatherCapFromLeather(player!, e.Mobile);
                break;
            case "craftbowyer":
                SeedBowyerInputs(player!, e.Mobile);
                break;
            case "makebowyer":
                CraftShaftFromBoard(player!, e.Mobile);
                break;
            case "makearrow":
                CraftArrowFromFeather(player!, e.Mobile);
                break;
            case "craftscribe":
                SeedInscriptionInputs(player!, e.Mobile);
                break;
            case "makescribe":
                CraftRunebookFromStarterScrolls(player!, e.Mobile);
                break;
            case "craftalchemy":
                SeedAlchemyInputs(player!, e.Mobile);
                break;
            case "makealchemy":
                CraftHealPotionFromStarterInputs(player!, e.Mobile);
                break;
            case "craftcook":
                SeedCookingInputs(player!, e.Mobile);
                break;
            case "makecook":
                CookFishFromStarterFish(player!, e.Mobile);
                break;
            case "verify":
                Verify(player!, e.Mobile);
                break;
            default:
                e.Mobile.SendMessage("Usage: [StarterEconomyProbe seed|salvage|npc|transfers|craft|make|craftwood|makewood|craftcloth|makecloth|crafttinker|maketinker|crafttinkerscissors|maketinkerscissors|craftleather|makeleather|craftbowyer|makebowyer|makearrow|craftscribe|makescribe|craftalchemy|makealchemy|craftcook|makecook|vendor|tinkernpc|tailornpc|legacyward|place|verify <player-serial> | wardscan | item <item-serial> | trim <item-serial> | delete <item-serial> | cleanup");
                break;
        }
    }

    private static bool TryPlayer(string value, out PlayerMobile? player)
    {
        player = null;
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        var raw = value.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? value[2..] : value;
        if (!uint.TryParse(raw, System.Globalization.NumberStyles.HexNumber, null, out var serial))
        {
            return false;
        }

        player = World.FindMobile((Serial)serial) as PlayerMobile;
        return player is { Player: true, Backpack: not null };
    }

    private static void Seed(PlayerMobile owner, Mobile requester)
    {
        var pack = owner.Backpack!;
        var scissors = pack.FindItemByType<StarterScissors>() ?? Add(pack, new StarterScissors(owner));
        var ingots = pack.FindItemByType<IronIngot>() ?? Add(pack, Newbied(new IronIngot(10)));
        var tools = pack.FindItemByType<TinkerTools>() ?? Add(pack, Newbied(new TinkerTools()));
        BackpackWard? ward = null;
        foreach (var candidate in pack.FindItemsByType<BackpackWard>())
        {
            if (candidate.IsStarterIssued)
            {
                ward = candidate;
                break;
            }
        }
        var wardMarked = ward?.IsStarterIssued == true;
        if (ward is null)
        {
            ward = new BackpackWard();
            wardMarked = ward.MarkStarterIssued(owner);
            pack.DropItem(ward);
        }

        var ordinary = pack.Items.OfType<Katana>().FirstOrDefault(item => item.GetType() == typeof(Katana) && item.Name == "A3 ordinary Katana control");
        if (ordinary is null)
        {
            ordinary = new Katana { Name = "A3 ordinary Katana control" };
            pack.DropItem(ordinary);
        }

        _nestedBag = pack.Items.OfType<Bag>().FirstOrDefault(item => item.Name == "A3 nested transfer wrapper");
        if (_nestedBag is null)
        {
            _nestedBag = new Bag { Name = "A3 nested transfer wrapper" };
            _nestedIron = Newbied(new IronIngot(1));
            _nestedBag.DropItem(_nestedIron);
            pack.DropItem(_nestedBag);
        }
        else
        {
            _nestedIron = _nestedBag.FindItemByType<IronIngot>();
        }

        SeededItems.Clear();
        SeededItems.AddRange([scissors, ingots, tools, ward, ordinary, _nestedBag]);
        if (_nestedIron is not null)
        {
            SeededItems.Add(_nestedIron);
        }

        requester.SendMessage($"Starter economy seed owner={owner.Serial}; scissors={scissors.Serial}; ingots={ingots.Serial} amount={ingots.Amount}; tools={tools.Serial}; ward={ward.Serial} wardMarked={wardMarked}; ordinary={ordinary.Serial}; nestedBag={_nestedBag.Serial}; nestedIron={_nestedIron?.Serial}.");
    }

    private static T Add<T>(Container pack, T item) where T : Item
    {
        pack.DropItem(item);
        return item;
    }

    // Feature H (2026-09-28): craft materials/tools are plain stock types, newbied only (no more
    // owner-serial bound subclasses), matching Feature G's combat gear. Vendor sale is blocked by
    // the shared Newbied guard; trade, drop, banking and salvage are not.
    private static T Newbied<T>(T item) where T : Item
    {
        item.LootType = LootType.Newbied;
        return item;
    }

    private static void CreateVendor(PlayerMobile owner, Mobile requester)
    {
        if (_vendor is null || _vendor.Deleted)
        {
            _vendor = World.FindMobile((Serial)0x0001C59B) as PlayerVendor;
        }

        if (_vendor is null || _vendor.Deleted)
        {
            _vendor = new PlayerVendor(owner, null!);
            _vendor.MoveToWorld(owner.Location, owner.Map);
        }

        requester.SendMessage($"Starter economy player vendor: vendor={_vendor.Serial}; owner={owner.Serial}; location={_vendor.Location}.");
    }

    private static void SeedSalvageTargets(PlayerMobile player, Mobile requester)
    {
        // Feature H (2026-09-28): newbied Cloth is no longer Nontransferable, so it (unlike the
        // still-bound Scissors) is expected to salvage/scissor exactly like the ordinary control.
        var cloth = Newbied(new Cloth(2));
        var ordinaryCloth = new Cloth(2);
        var salvageBag = new SalvageBag();
        var scissors = new StarterScissors(player);
        var tongs = new Tongs();
        var nestedCloth = Newbied(new Cloth(2));
        var ordinaryKatana = new Katana();
        salvageBag.DropItem(nestedCloth);
        salvageBag.DropItem(ordinaryKatana);
        player.Backpack.DropItem(cloth);
        player.Backpack.DropItem(ordinaryCloth);
        player.Backpack.DropItem(salvageBag);
        player.Backpack.DropItem(scissors);
        player.Backpack.DropItem(tongs);
        player.MoveToWorld(new Point3D(1354, 1778, 15), Map.Felucca);
        SeededItems.AddRange([cloth, ordinaryCloth, salvageBag, scissors, tongs, nestedCloth, ordinaryKatana]);
        requester.SendMessage($"Starter economy salvage targets: cloth={cloth.Serial}; ordinaryCloth={ordinaryCloth.Serial}; bag={salvageBag.Serial}; scissors={scissors.Serial}; tongs={tongs.Serial}; nestedCloth={nestedCloth.Serial}; ordinaryKatana={ordinaryKatana.Serial}; owner={player.Serial}; location={player.Location}.");
    }

    private static void SeedNpcSaleTargets(PlayerMobile player, Mobile requester)
    {
        // Feature H (2026-09-28): "bound" here means newbied-only (vendor-blocked by LootType, not
        // Nontransferable); the ordinary control has Regular loot type and stays sellable.
        var bound = Newbied(new IronIngot(2));
        var ordinary = new IronIngot(2);
        player.Backpack.DropItem(bound);
        player.Backpack.DropItem(ordinary);
        var blacksmith = new Blacksmith { Name = TestBlacksmithName };
        blacksmith.MoveToWorld(new Point3D(player.X + 1, player.Y, player.Z), player.Map);
        SeededItems.AddRange([bound, ordinary]);
        requester.SendMessage($"Starter economy NPC targets: bound={bound.Serial}; ordinary={ordinary.Serial}; vendor={blacksmith.Serial}; owner={player.Serial}; location={player.Location}.");
    }

    private static void SeedLegacyWardNpcSaleTargets(PlayerMobile player, Mobile requester)
    {
        var legacyWard = new BackpackWard { Name = "A3 legacy Ward sale control" };
        var starterWard = new BackpackWard { Name = "A3 marked Ward sale control" };
        if (!starterWard.MarkStarterIssued(player))
        {
            legacyWard.Delete();
            starterWard.Delete();
            requester.SendMessage("Starter economy Ward NPC fixture could not mark the starter control.");
            return;
        }

        player.Backpack!.DropItem(legacyWard);
        player.Backpack.DropItem(starterWard);
        var blacksmith = new Blacksmith { Name = TestBlacksmithName };
        blacksmith.MoveToWorld(new Point3D(player.X + 1, player.Y, player.Z), player.Map);
        var sellInfos = blacksmith.GetSellInfo().OfType<GenericSellInfo>().ToArray();
        if (sellInfos.Length == 0)
        {
            legacyWard.Delete();
            starterWard.Delete();
            blacksmith.Delete();
            requester.SendMessage("Starter economy Ward NPC fixture found no generic Blacksmith sell list.");
            return;
        }

        foreach (var sellInfo in sellInfos)
        {
            sellInfo.Add(typeof(BackpackWard), 10);
        }

        var vendorSellInfo = blacksmith.GetSellInfo();
        var legacyTypeListed = vendorSellInfo.Any(info => legacyWard.InTypeList(info.Types));
        var legacyEligible = vendorSellInfo.Any(info => legacyWard.InTypeList(info.Types) &&
                                                         legacyWard.IsStandardLoot() && legacyWard.Movable &&
                                                         info.IsSellable(legacyWard));
        var legacyInBackpack = legacyWard.RootParent == player;
        SeededItems.AddRange([legacyWard, starterWard]);
        requester.SendMessage($"Starter economy legacy Ward NPC targets: legacy={legacyWard.Serial}; starter={starterWard.Serial}; vendor={blacksmith.Serial}; price=10; owner={player.Serial}; location={player.Location}; genericSellLists={sellInfos.Length}; legacyStandardLoot={legacyWard.IsStandardLoot()}; legacyMovable={legacyWard.Movable}; legacyNontransferable={legacyWard.Nontransferable}; legacyListed={sellInfos.Any(info => info.IsInList(typeof(BackpackWard)))}; legacySellable={sellInfos.Any(info => info.IsSellable(legacyWard))}; legacyTypeListed={legacyTypeListed}; legacyInBackpack={legacyInBackpack}; legacyVendorCandidate={legacyEligible}; starterSellable={sellInfos.Any(info => info.IsSellable(starterWard))}.");
    }

    private static void SeedCraftingInputs(PlayerMobile player, Mobile requester)
    {
        var pack = player.Backpack!;
        if (!player.Alive)
        {
            player.Resurrect();
        }

        var ingots = Newbied(new IronIngot(100));
        var tongs = Newbied(new Tongs());
        pack.DropItem(ingots);
        pack.DropItem(tongs);
        // The newly created disposable character starts at 10 Strength and has stock kit weight.
        // Raise carry capacity only in this test fixture so the seeded resources can be exercised.
        player.Str = 100;
        player.Skills[SkillName.Blacksmith].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        DefBlacksmithy.CheckAnvilAndForge(player, 2, out var anvil, out var forge);
        SeededItems.AddRange([ingots, tongs]);
        requester.SendMessage($"Starter economy craft targets: ingots={ingots.Serial}; amount={ingots.Amount}; tongs={tongs.Serial}; blacksmith={player.Skills[SkillName.Blacksmith].Base}; owner={player.Serial}; location={player.Location}; anvil={anvil}; forge={forge};.");
    }

    private static void CraftDaggerFromStarterIngots(PlayerMobile player, Mobile requester)
    {
        var ingots = player.Backpack!.FindItemByType<IronIngot>();
        var tongs = player.Backpack.FindItemByType<Tongs>();
        var system = DefBlacksmithy.CraftSystem;
        var craftItem = system.CraftItems.SearchFor(typeof(Dagger));
        if (ingots is null || tongs is null || craftItem is null)
        {
            requester.SendMessage("Starter economy craft fixture is missing its ingots, tongs or dagger recipe.");
            return;
        }

        BlacksmithMenu.ResourceSelection(player, tongs, (from, tool) =>
        {
            var context = system.GetContext(from);
            var resource = context is { LastResourceIndex: >= 0 } && context.LastResourceIndex < system.CraftSubRes.Count
                ? system.CraftSubRes[context.LastResourceIndex].ItemType
                : null;
            requester.SendMessage($"Starter economy craft selection: selectedResource={resource?.Name ?? "<default>"}; recipe={craftItem.ItemType.Name}; ingotBefore={ingots.Amount}.");
            system.CreateItem(from, craftItem.ItemType, resource, tool, craftItem);
        }, ingots);
    }

    private static void SeedCarpentryInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive)
        {
            player.Resurrect();
        }

        var boards = Newbied(new Board(100));
        var saw = Newbied(new Saw());
        player.Backpack!.DropItem(boards);
        player.Backpack.DropItem(saw);
        player.Str = 100;
        player.Skills[SkillName.Carpentry].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        SeededItems.AddRange([boards, saw]);
        requester.SendMessage($"Starter economy carpentry targets: boards={boards.Serial}; amount={boards.Amount}; saw={saw.Serial}; carpentry={player.Skills[SkillName.Carpentry].Base}; owner={player.Serial}; location={player.Location}.");
    }

    private static void CraftChairFromBoards(PlayerMobile player, Mobile requester)
    {
        var boards = player.Backpack!.FindItemByType<Board>();
        var saw = player.Backpack.FindItemByType<Saw>();
        var system = DefCarpentry.CraftSystem;
        var craftItem = system.CraftItems.SearchFor(typeof(WoodenChair));
        if (boards is null || saw is null || craftItem is null)
        {
            requester.SendMessage("Starter economy carpentry fixture is missing its boards, saw or chair recipe.");
            return;
        }

        requester.SendMessage($"Starter economy carpentry selection: recipe={craftItem.ItemType.Name}; resource=Log/Board; boardsBefore={boards.Amount}.");
        system.CreateItem(player, craftItem.ItemType, null, saw, craftItem);
    }

    private static void SeedTailoringInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive)
        {
            player.Resurrect();
        }

        var cloth = Newbied(new Cloth(100));
        var kit = Newbied(new SewingKit());
        player.Backpack!.DropItem(cloth);
        player.Backpack.DropItem(kit);
        player.Str = 100;
        player.Skills[SkillName.Tailoring].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        SeededItems.AddRange([cloth, kit]);
        requester.SendMessage($"Starter economy tailoring targets: cloth={cloth.Serial}; amount={cloth.Amount}; kit={kit.Serial}; tailoring={player.Skills[SkillName.Tailoring].Base}; owner={player.Serial}; location={player.Location}.");
    }

    private static void CraftShirtFromCloth(PlayerMobile player, Mobile requester)
    {
        var cloth = player.Backpack!.FindItemByType<Cloth>();
        var kit = player.Backpack.FindItemByType<SewingKit>();
        var system = DefTailoring.CraftSystem;
        var craftItem = system.CraftItems.SearchFor(typeof(Shirt));
        if (cloth is null || kit is null || craftItem is null)
        {
            requester.SendMessage("Starter economy tailoring fixture is missing its cloth, sewing kit or shirt recipe.");
            return;
        }

        TailoringMenu.ResourceSelection(player, kit, cloth);
        requester.SendMessage($"Starter economy tailoring selection: recipe={craftItem.ItemType.Name}; resource=Cloth; clothBefore={cloth.Amount}.");
        system.CreateItem(player, craftItem.ItemType, null, kit, craftItem, cloth.Hue);
    }

    private static void SeedTinkeringInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive)
        {
            player.Resurrect();
        }

        var ingots = Newbied(new IronIngot(100));
        var tools = Newbied(new TinkerTools());
        player.Backpack!.DropItem(ingots);
        player.Backpack.DropItem(tools);
        player.Str = 100;
        player.Skills[SkillName.Tinkering].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        SeededItems.AddRange([ingots, tools]);
        requester.SendMessage($"Starter economy tinkering targets: ingots={ingots.Serial}; amount={ingots.Amount}; tools={tools.Serial}; tinkering={player.Skills[SkillName.Tinkering].Base}; owner={player.Serial}; location={player.Location}.");
    }

    private static void CraftGearsFromStarterIngots(PlayerMobile player, Mobile requester)
    {
        var ingots = player.Backpack!.FindItemByType<IronIngot>();
        var tools = player.Backpack.FindItemByType<TinkerTools>();
        var system = DefTinkering.CraftSystem;
        var craftItem = system.CraftItems.SearchFor(typeof(Gears));
        if (ingots is null || tools is null || craftItem is null)
        {
            requester.SendMessage("Starter economy tinkering fixture is missing its ingots, tools or Gears recipe.");
            return;
        }

        TinkeringMenu.ResourceSelection(player, tools, ingots);
        requester.SendMessage($"Starter economy tinkering selection: recipe={craftItem.ItemType.Name}; resource=IronIngot; ingotsBefore={ingots.Amount}.");
        system.CreateItem(player, craftItem.ItemType, null, tools, craftItem, ingots.Hue);
    }

    private static void SeedTinkeringScissorsInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive)
        {
            player.Resurrect();
        }

        var ingots = Newbied(new IronIngot(6));
        var tools = Newbied(new TinkerTools());
        var cloth = Newbied(new Cloth(5));
        player.Backpack!.DropItem(ingots);
        player.Backpack.DropItem(tools);
        player.Backpack.DropItem(cloth);
        player.Str = 100;
        player.Skills[SkillName.Tinkering].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        SeededItems.AddRange([ingots, tools, cloth]);
        requester.SendMessage($"Starter economy Tinkering scissors targets: ingots={ingots.Serial}; amount={ingots.Amount}; tools={tools.Serial}; cloth={cloth.Serial}; clothAmount={cloth.Amount}; owner={player.Serial}; location={player.Location}.");
    }

    private static void CraftScissorsFromStarterIngots(PlayerMobile player, Mobile requester)
    {
        var ingots = player.Backpack!.FindItemByType<IronIngot>();
        var tools = player.Backpack.FindItemByType<TinkerTools>();
        var system = DefTinkering.CraftSystem;
        var craftItem = system.CraftItems.SearchFor(typeof(Scissors));
        if (ingots is null || tools is null || craftItem is null)
        {
            requester.SendMessage("Starter economy Tinkering scissors fixture is missing ingots, tools or stock Scissors recipe.");
            return;
        }

        T2ACraftSystem.ShowMenu(player, system, tools, ingots);
        requester.SendMessage($"Starter economy Tinkering scissors selection: recipe={craftItem.ItemType.Name}; resource=IronIngot; ingotsBefore={ingots.Amount}.");
        system.CreateItem(player, craftItem.ItemType, null, tools, craftItem, ingots.Hue);
    }

    private static void SeedTailoringLeather(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive) player.Resurrect();
        var leather = Newbied(new Leather(20));
        var kit = Newbied(new SewingKit());
        player.Backpack!.DropItem(leather);
        player.Backpack.DropItem(kit);
        player.Str = 100;
        player.Skills[SkillName.Tailoring].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        SeededItems.AddRange([leather, kit]);
        requester.SendMessage($"Starter economy leather tailoring targets: leather={leather.Serial}; amount={leather.Amount}; kit={kit.Serial}; owner={player.Serial}.");
    }

    private static void CraftLeatherCapFromLeather(PlayerMobile player, Mobile requester)
    {
        var leather = player.Backpack!.FindItemByType<Leather>();
        var kit = player.Backpack.FindItemByType<SewingKit>();
        var system = DefTailoring.CraftSystem;
        var craftItem = system.CraftItems.SearchFor(typeof(LeatherCap));
        if (leather is null || kit is null || craftItem is null)
        {
            requester.SendMessage("Starter economy leather tailoring fixture is missing its Leather, sewing kit or LeatherCap recipe.");
            return;
        }

        TailoringMenu.ResourceSelection(player, kit, leather);
        requester.SendMessage($"Starter economy leather tailoring selection: recipe={craftItem.ItemType.Name}; resource=Leather; leatherBefore={leather.Amount}.");
        system.CreateItem(player, craftItem.ItemType, leather.GetType(), kit, craftItem, leather.Hue);
    }

    private static void SeedBowyerInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive) player.Resurrect();
        var boards = Newbied(new Board(1));
        var feathers = Newbied(new Feather(1));
        var tools = Newbied(new FletcherTools());
        player.Backpack!.DropItem(boards);
        player.Backpack.DropItem(feathers);
        player.Backpack.DropItem(tools);
        player.Str = 100;
        player.Skills[SkillName.Fletching].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        SeededItems.AddRange([boards, feathers, tools]);
        requester.SendMessage($"Starter economy bowyer targets: boards={boards.Serial}; amount={boards.Amount}; feathers={feathers.Serial}; featherAmount={feathers.Amount}; tools={tools.Serial}; owner={player.Serial}.");
    }

    private static void CraftShaftFromBoard(PlayerMobile player, Mobile requester)
    {
        var boards = player.Backpack!.FindItemByType<Board>();
        var tools = player.Backpack.FindItemByType<FletcherTools>();
        var system = DefBowFletching.CraftSystem;
        var shaftRecipe = system.CraftItems.SearchFor(typeof(Shaft));
        if (boards is null || tools is null || shaftRecipe is null)
        {
            requester.SendMessage("Starter economy bowyer fixture is missing boards, Fletcher Tools or stock Shaft recipe.");
            return;
        }

        T2ACraftSystem.ShowMenu(player, system, tools, boards);
        system.CreateItem(player, shaftRecipe.ItemType, typeof(Board), tools, shaftRecipe, boards.Hue);
        requester.SendMessage($"Starter economy bowyer selection: recipe=Shaft; resource=Board/Log; boardBefore={boards.Amount}.");
    }

    private static void CraftArrowFromFeather(PlayerMobile player, Mobile requester)
    {
        var feathers = player.Backpack!.FindItemByType<Feather>();
        var shaft = player.Backpack.FindItemByType<Shaft>();
        var tools = player.Backpack.FindItemByType<FletcherTools>();
        var system = DefBowFletching.CraftSystem;
        var recipe = system.CraftItems.SearchFor(typeof(Arrow));
        if (feathers is null || shaft is null || tools is null || recipe is null)
        {
            requester.SendMessage("Starter economy bowyer fixture is missing Feather, stock Shaft, Fletcher Tools or Arrow recipe.");
            return;
        }

        system.CreateItem(player, recipe.ItemType, null, tools, recipe, feathers.Hue);
        requester.SendMessage($"Starter economy bowyer selection: intermediate=Shaft; featherBefore={feathers.Amount}; recipe={recipe.ItemType.Name}.");
    }

    private static void SeedInscriptionInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive) player.Resurrect();
        var scrolls = Newbied(new BlankScroll(8));
        var pen = Newbied(new ScribesPen());
        var recall = new RecallScroll();
        var gate = new GateTravelScroll();
        var blankRune = new RecallRune();
        player.Backpack!.DropItem(scrolls);
        player.Backpack.DropItem(pen);
        player.Backpack.DropItem(recall);
        player.Backpack.DropItem(gate);
        player.Backpack.DropItem(blankRune);
        player.Str = 100;
        player.Skills[SkillName.Inscribe].Base = 100.0;
        player.Blessed = true;
        SeededItems.AddRange([scrolls, pen, recall, gate, blankRune]);
        requester.SendMessage($"Starter economy inscription targets: blank={scrolls.Serial}; amount={scrolls.Amount}; pen={pen.Serial}; recall={recall.Serial}; gate={gate.Serial}; blankRune={blankRune.Serial}; owner={player.Serial}.");
    }

    private static void CraftRunebookFromStarterScrolls(PlayerMobile player, Mobile requester)
    {
        var scrolls = player.Backpack!.FindItemByType<BlankScroll>();
        var pen = player.Backpack.FindItemByType<ScribesPen>();
        var system = DefInscription.CraftSystem;
        var recipe = system.CraftItems.SearchFor(typeof(Runebook));
        if (scrolls is null || pen is null || recipe is null)
        {
            requester.SendMessage("Starter economy inscription fixture is missing blank scrolls, pen or stock Runebook recipe.");
            return;
        }

        _ = new InscriptionMenu(player, pen);
        system.CreateItem(player, recipe.ItemType, null, pen, recipe);
        requester.SendMessage($"Starter economy inscription selection: recipe={recipe.ItemType.Name}; blankBefore={scrolls.Amount}; blankRequired=8.");
    }

    private static void SeedAlchemyInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive) player.Resurrect();
        var bottles = Newbied(new Bottle(1));
        var ginseng = Newbied(new Ginseng(3));
        var tool = Newbied(new MortarPestle());
        player.Backpack!.DropItem(bottles);
        player.Backpack.DropItem(ginseng);
        player.Backpack.DropItem(tool);
        player.Str = 100;
        player.Skills[SkillName.Alchemy].Base = 100.0;
        player.Blessed = true;
        SeededItems.AddRange([bottles, ginseng, tool]);
        requester.SendMessage($"Starter economy alchemy targets: bottle={bottles.Serial}; amount={bottles.Amount}; ginseng={ginseng.Serial}; ginsengAmount={ginseng.Amount}; tool={tool.Serial}; owner={player.Serial}.");
    }

    private static void CraftHealPotionFromStarterInputs(PlayerMobile player, Mobile requester)
    {
        var bottles = player.Backpack!.FindItemByType<Bottle>();
        var ginseng = player.Backpack.FindItemByType<Ginseng>();
        var tool = player.Backpack.FindItemByType<MortarPestle>();
        var system = DefAlchemy.CraftSystem;
        var recipe = system.CraftItems.SearchFor(typeof(LesserHealPotion));
        if (bottles is null || ginseng is null || tool is null || recipe is null)
        {
            requester.SendMessage("Starter economy alchemy fixture is missing bottle, ginseng, mortar and pestle or potion recipe.");
            return;
        }

        _ = new AlchemyMenu(player, tool);
        system.CreateItem(player, recipe.ItemType, typeof(Ginseng), tool, recipe);
        requester.SendMessage($"Starter economy alchemy selection: recipe={recipe.ItemType.Name}; bottleBefore={bottles.Amount}; ginsengBefore={ginseng.Amount}.");
    }

    private static void SeedCookingInputs(PlayerMobile player, Mobile requester)
    {
        if (!player.Alive) player.Resurrect();
        var fish = Newbied(new RawFishSteak(1));
        var kindling = Newbied(new Kindling(1));
        var skillet = new Skillet(50);
        player.Backpack!.DropItem(fish);
        player.Backpack.DropItem(kindling);
        player.Backpack.DropItem(skillet);
        player.Str = 100;
        player.Skills[SkillName.Cooking].Base = 100.0;
        player.Blessed = true;
        player.MoveToWorld(new Point3D(3704, 2245, 20), Map.Felucca);
        SeededItems.AddRange([fish, kindling, skillet]);
        requester.SendMessage($"Starter economy cooking targets: fish={fish.Serial}; amount={fish.Amount}; kindling={kindling.Serial}; kindlingAmount={kindling.Amount}; skillet={skillet.Serial}; owner={player.Serial}; location={player.Location}.");
    }

    private static void CookFishFromStarterFish(PlayerMobile player, Mobile requester)
    {
        var fish = player.Backpack!.FindItemByType<RawFishSteak>();
        var skillet = player.Backpack.FindItemByType<Skillet>();
        var system = DefCooking.CraftSystem;
        var recipe = system.CraftItems.SearchFor(typeof(FishSteak));
        if (fish is null || skillet is null || recipe is null)
        {
            requester.SendMessage("Starter economy cooking fixture is missing raw fish, Skillet or stock FishSteak recipe.");
            return;
        }

        system.CreateItem(player, recipe.ItemType, null, skillet, recipe);
        requester.SendMessage($"Starter economy cooking selection: recipe={recipe.ItemType.Name}; rawFishBefore={fish.Amount}; heatStation=(3704,2245,20); kindlingPresent={player.Backpack.FindItemByType<Kindling>() is not null}; tool=Skillet.");
    }

    private static void SeedTransferMatrix(PlayerMobile player, Mobile requester)
    {
        // Keep the disposable ordinary character's inventory below its carry limit during the matrix.
        if (player.Str < 55)
        {
            player.Str = 55;
        }

        var ward = new BackpackWard();
        ward.MarkStarterIssued(player);
        // Feature H (2026-09-28): only StarterScissors and the marked Ward are still bound
        // (Nontransferable) here - "stays with owner" no longer holds for the rest via secure
        // trade/drop, only via the vendor-sale guard (Newbied). Kept in one matrix so `verify`
        // reports both kinds side by side; a live drop/trade attempt on the newbied items is
        // expected to succeed, unlike the two still-bound ones.
        Item[] items =
        [
            new StarterScissors(player), Newbied(new IronIngot(2)), ward,
            Newbied(new Tongs()), Newbied(new Pickaxe()), Newbied(new TinkerTools()),
            Newbied(new SewingKit()), Newbied(new Saw()), Newbied(new FletcherTools()),
            Newbied(new ScribesPen()), Newbied(new MortarPestle()),
            Newbied(new RawFishSteak(1)), Newbied(new Kindling(1)),
            Newbied(new Board(1)), Newbied(new Feather(1)), Newbied(new Cloth(1)),
            Newbied(new Leather(1)), Newbied(new BlankScroll(1)), Newbied(new Bottle(1)),
            Newbied(new BlackPearl(1)), Newbied(new Bloodmoss(1)), Newbied(new Garlic(1)),
            Newbied(new Ginseng(1)), Newbied(new MandrakeRoot(1)), Newbied(new Nightshade(1)),
            Newbied(new SulfurousAsh(1)), Newbied(new SpidersSilk(1))
        ];

        foreach (var item in items)
        {
            player.Backpack.DropItem(item);
        }

        SeededItems.AddRange(items);
        CreateVendor(player, requester);
        foreach (var item in items)
        {
            requester.SendMessage($"Starter economy transfer target: {item.GetType().Name}={item.Serial}; owner={player.Serial}.");
        }
        requester.SendMessage($"Starter economy transfer matrix ready: count={items.Length}; vendor={_vendor?.Serial}; owner={player.Serial}; str={player.Str}; maxWeight={player.MaxWeight}.");
    }

    private static void Verify(PlayerMobile owner, Mobile requester)
    {
        requester.SendMessage($"Starter economy verify player={owner.Serial} backpack={owner.Backpack?.Serial} vendor={_vendor?.Serial}.");
        foreach (var item in SeededItems)
        {
            if (!item.Deleted)
            {
                requester.SendMessage($"{item.GetType().Name} {item.Serial}: parent={item.Parent?.GetType().Name ?? "world/none"}; ownerBackpack={item.Parent == owner.Backpack}; vendorStock={_vendor?.GetVendorItem(item) is not null}; inTrade={item.InSecureTrade}.");
            }
        }
    }

    private static void VerifyItem(string value, Mobile requester)
    {
        var raw = value.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? value[2..] : value;
        if (!uint.TryParse(raw, System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindItem((Serial)serial) is not { Deleted: false } item)
        {
            requester.SendMessage("Starter economy item verification requires an existing item serial.");
            return;
        }

        var vendor = World.Mobiles.Values.OfType<PlayerVendor>().FirstOrDefault(v => v.GetVendorItem(item) is not null);
        requester.SendMessage($"Starter economy output verify: type={item.GetType().Name}; serial={item.Serial}; parent={item.Parent?.GetType().Name ?? "world/none"}; root={item.RootParent?.GetType().Name ?? "none"}; nontransferable={item.Nontransferable}; vendor={vendor?.Serial}; vendorStock={vendor is not null}; inTrade={item.InSecureTrade}.");
    }

    private static void InspectWardSalePath(string value, Mobile requester)
    {
        if (!TryPlayer(value, out var player) || player!.Backpack is not { } pack)
        {
            requester.SendMessage("Starter economy Ward inspection requires a live player serial with a backpack.");
            return;
        }

        var smith = World.Mobiles.Values.OfType<Blacksmith>()
            .FirstOrDefault(v => string.Equals(v.Name, TestBlacksmithName, StringComparison.Ordinal));
        var wardItems = new List<Item>();
        var itemCount = 0;
        foreach (var item in pack.FindItems())
        {
            itemCount++;
            if (item is BackpackWard)
            {
                wardItems.Add(item);
            }
        }

        requester.SendMessage($"Ward sale runtime inspection: player={player.Serial}; backpack={pack.Serial}; enumeratedItems={itemCount}; containsWard={wardItems.Count > 0}; smith={smith?.Serial}; sellInfoCount={smith?.GetSellInfo().Length ?? 0};");
        foreach (var item in wardItems)
        {
            IEnumerable<string> details = smith is null
                ? Array.Empty<string>()
                : smith.GetSellInfo().Select((info, index) =>
                    $"list{index}:typeListed={item.InTypeList(info.Types)},standard={item.IsStandardLoot()},movable={item.Movable},sellable={info.IsSellable(item)},price={info.GetSellPriceFor(item)}");
            requester.SendMessage($"Ward sale enumerated item: serial={item.Serial}; parent={item.Parent?.GetType().Name}; root={item.RootParent?.GetType().Name}; {string.Join(";", details)}.");
        }
    }

    private static void ScanWards(Mobile requester)
    {
        var wards = World.Items.Values.OfType<BackpackWard>().Where(w => !w.Deleted).ToArray();
        var marked = wards.Count(w => w.IsStarterIssued);
        var unmarked = wards.Where(w => !w.IsStarterIssued).ToArray();
        var inContainers = unmarked.Count(w => w.Parent is Container);
        var inWorld = unmarked.Length - inContainers;
        requester.SendMessage($"Backpack Ward population scan: total={wards.Length}; starterMarked={marked}; legacyUnmarked={unmarked.Length}; unmarkedInContainers={inContainers}; unmarkedInWorld={inWorld}.");
    }

    private static void SeedUnmarkedWard(PlayerMobile owner, Mobile requester)
    {
        var ward = new BackpackWard();
        owner.Backpack!.DropItem(ward);
        SeededItems.Add(ward);
        requester.SendMessage($"Starter economy legacy Ward fixture: serial={ward.Serial}; starterIssued={ward.IsStarterIssued}; nontransferable={ward.Nontransferable}; owner={owner.Serial}.");
    }

    private static void Trim(string value, Mobile requester)
    {
        var raw = value.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? value[2..] : value;
        if (!uint.TryParse(raw, System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindItem((Serial)serial) is not IronIngot item)
        {
            requester.SendMessage("Starter economy trim requires a IronIngot serial.");
            return;
        }

        item.Delete();
        SeededItems.Remove(item);
        requester.SendMessage($"Starter economy test stack {serial:X8} removed for the ordinary transfer control.");
    }

    private static void DeleteItem(string value, Mobile requester)
    {
        var raw = value.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? value[2..] : value;
        if (!uint.TryParse(raw, System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindItem((Serial)serial) is not { Deleted: false } item)
        {
            requester.SendMessage("Starter economy delete requires an existing item serial.");
            return;
        }

        item.Delete();
        requester.SendMessage($"Starter economy fixture item {serial:X8} deleted.");
    }

    private static void Cleanup(Mobile requester)
    {
        var fixturePlayers = World.Mobiles.Values.OfType<PlayerMobile>()
            .Where(p => p.Serial == (Serial)0x0001C599 || p.Serial == (Serial)0x0001C59A ||
                        string.Equals(p.Name, "StarterSalvage", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterMatrixA", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterMatrixB", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterCraft", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterCarpenter", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterTailor", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterTinker", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterBuyer", StringComparison.Ordinal) ||
                        string.Equals(p.Name, "StarterWardSale", StringComparison.Ordinal))
            .ToArray();

        _vendor ??= World.FindMobile((Serial)0x0001C59B) as PlayerVendor;
        _vendor?.Delete();
        _vendor = null;
        foreach (var blacksmith in World.Mobiles.Values.OfType<Blacksmith>()
                     .Where(v => string.Equals(v.Name, TestBlacksmithName, StringComparison.Ordinal)).ToArray())
        {
            blacksmith.Delete();
        }
        foreach (var tinker in World.Mobiles.Values.OfType<Tinker>()
                     .Where(v => string.Equals(v.Name, TestTinkerName, StringComparison.Ordinal)).ToArray())
        {
            tinker.Delete();
        }
        foreach (var tailor in World.Mobiles.Values.OfType<Tailor>()
                     .Where(v => string.Equals(v.Name, TestTailorName, StringComparison.Ordinal)).ToArray())
        {
            tailor.Delete();
        }
        foreach (var vendor in World.Mobiles.Values.OfType<PlayerVendor>()
                     .Where(v => fixturePlayers.Any(p => p.Serial == v.Owner?.Serial))
                     .ToArray())
        {
            vendor.Delete();
        }

        foreach (var serial in new Serial[] { (Serial)0x40079EA8, (Serial)0x40079F7E, (Serial)0x4007A13D })
        {
            if (World.FindItem(serial) is { Deleted: false } fixture)
            {
                fixture.Delete();
            }
        }

        foreach (var item in SeededItems)
        {
            if (!item.Deleted)
            {
                item.Delete();
            }
        }
        SeededItems.Clear();

        foreach (var player in fixturePlayers)
        {
            var account = player.Account as Account;
            player.Delete();
            if (account is null)
            {
                continue;
            }

            for (var i = 0; i < account.Length; i++)
            {
                if (account[i] == player)
                {
                    account[i] = null;
                }
            }
            account.Delete();
        }

            requester.SendMessage("Starter economy probe items, vendor, test players, and their accounts removed.");
    }
}
