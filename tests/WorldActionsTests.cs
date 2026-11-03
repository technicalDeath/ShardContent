using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class WorldActionsTests
{
    [Theory]
    [InlineData(true, true, true, null)]
    [InlineData(false, true, true, WorldActions.NoAxe)]
    [InlineData(false, false, false, WorldActions.NoAxe)]   // the axe comes first: it is the first thing to fix
    [InlineData(true, false, true, WorldActions.TooFar)]
    [InlineData(true, false, false, WorldActions.TooFar)]
    [InlineData(true, true, false, WorldActions.NoWood)]
    public void AChopSaysWhyItCannotBeDone(bool hasAxe, bool inRange, bool woodLeft, string? expected) =>
        Assert.Equal(expected, WorldActions.ChopReason(hasAxe, inRange, woodLeft));

    [Theory]
    [InlineData(true, true, true, null)]
    [InlineData(false, true, true, WorldActions.NoBlade)]
    [InlineData(true, false, true, WorldActions.TooFar)]
    [InlineData(true, true, false, WorldActions.NoWood)]
    public void CuttingKindlingSaysWhyItCannotBeDone(bool hasBlade, bool inRange, bool woodLeft, string? expected) =>
        Assert.Equal(expected, WorldActions.KindlingReason(hasBlade, inRange, woodLeft));

    [Theory]
    [InlineData(true, false, true, true, null)]
    [InlineData(false, true, false, false, WorldActions.NoMiningTool)]  // the tool comes first
    [InlineData(true, true, true, true, WorldActions.MountedMining)]
    [InlineData(true, true, false, true, WorldActions.MountedMining)]   // getting off the horse before walking up
    [InlineData(true, false, false, true, WorldActions.TooFarToMine)]
    [InlineData(true, false, true, false, WorldActions.NoMetal)]
    public void MiningSaysWhyItCannotBeDone(bool hasTool, bool mounted, bool inRange, bool oreLeft, string? expected) =>
        Assert.Equal(expected, WorldActions.MineReason(hasTool, mounted, inRange, oreLeft));

    [Theory]
    [InlineData(true, false, true, true, null)]
    [InlineData(false, false, true, true, WorldActions.NoPole)]
    [InlineData(true, true, true, true, WorldActions.MountedFishing)]
    [InlineData(true, false, false, true, WorldActions.TooFarToFish)]
    [InlineData(true, false, true, false, WorldActions.NoFish)]
    public void FishingSaysWhyItCannotBeDone(bool hasPole, bool mounted, bool inRange, bool fishLeft, string? expected) =>
        Assert.Equal(expected, WorldActions.FishReason(hasPole, mounted, inRange, fishLeft));

    [Fact]
    public void AFishedOutSpotSaysHowFarToMove() => Assert.Contains("8 tiles", WorldActions.NoFish);

    [Fact]
    public void TheNoAxeReasonIsTheOwnersWording() => Assert.Equal("Requires an axe.", WorldActions.NoAxe);

    [Fact]
    public void TheReplyCarriesTheTileAndEachActionWithItsReason()
    {
        var reply = WorldActions.Reply(0x0102, 0x0304, 0x0CCA, [new WorldActions.WorldAction(WorldActions.ChopId, "Chop", "No")]);

        Assert.Equal(
            new byte[] { 0xBF, 0, 22, 0x00, 0xB1, 0x01, 0x02, 0x03, 0x04, 0x0C, 0xCA, 1, 1, 0, 4, (byte)'C', (byte)'h', (byte)'o', (byte)'p', 2, (byte)'N', (byte)'o' },
            reply
        );
        Assert.Equal(22, reply[1] << 8 | reply[2]);
    }

    [Fact]
    public void AnAvailableActionHasAnEmptyReason()
    {
        var reply = WorldActions.Reply(1, 1, 1, [new WorldActions.WorldAction(WorldActions.ChopId, "Chop", null)]);

        Assert.Equal(1, reply[13]);  // can be done
        Assert.Equal(0, reply[^1]);  // no reason
    }

    [Fact]
    public void TheActionsBitTravelsWithoutTheShardBar()
    {
        Assert.Equal(MenuBarService.Actions, MenuBarService.MaskFor(new DeferredFeatureFlags { WorldActions = true }));
        Assert.Equal(0, MenuBarService.MaskFor(new DeferredFeatureFlags()) & MenuBarService.Actions);
    }

    [Theory]
    [InlineData(true, true, true, null)]
    [InlineData(false, false, false, WorldActions.NoOre)]
    [InlineData(true, false, true, WorldActions.NoSmeltSkill)]
    [InlineData(true, true, false, WorldActions.TooFarFromForge)]
    public void SmeltingSaysWhyItCannotBeDone(bool hasOre, bool canSmelt, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.SmeltReason(hasOre, canSmelt, inRange));

    [Theory]
    [InlineData(Server.Items.CraftResource.Iron, 0.0, true)]
    [InlineData(Server.Items.CraftResource.DullCopper, 64.9, false)]
    [InlineData(Server.Items.CraftResource.DullCopper, 65.0, true)]
    [InlineData(Server.Items.CraftResource.Valorite, 98.9, false)]
    [InlineData(Server.Items.CraftResource.Valorite, 99.0, true)]
    public void ColouredOreNeedsItsMining(Server.Items.CraftResource ore, double mining, bool expected) =>
        Assert.Equal(expected, WorldActions.CanSmelt(WorldActions.OreDifficulty(ore), mining));

    [Theory]
    [InlineData(true, true, true, null)]
    [InlineData(false, true, true, WorldActions.NoSmithTool)]
    [InlineData(true, false, true, WorldActions.TooFarFromAnvil)]
    [InlineData(true, true, false, WorldActions.NoForgeNear)]
    public void SmithingSaysWhyItCannotBeDone(bool hasTool, bool inRange, bool forgeNear, string? expected) =>
        Assert.Equal(expected, WorldActions.SmithReason(hasTool, inRange, forgeNear));

    [Theory]
    [InlineData(false, true, null)]
    [InlineData(true, true, WorldActions.WheelBusy)]
    [InlineData(false, false, WorldActions.TooFarFromWheel)]
    public void SpinningSaysWhyItCannotBeDone(bool busy, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.SpinReason(busy, inRange));

    [Theory]
    [InlineData(true, true, null)]
    [InlineData(false, true, WorldActions.NoYarn)]
    [InlineData(true, false, WorldActions.TooFarFromLoom)]
    public void WeavingSaysWhyItCannotBeDone(bool hasYarn, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.WeaveReason(hasYarn, inRange));

    [Fact]
    public void ACookEntrySaysTheKindAndHowMany() => Assert.Equal("Cook raw ribs (3)", WorldActions.CookEntryLabel(0, 3));

    [Fact]
    public void EveryCookKindHasItsOwnId()
    {
        Assert.Equal(WorldActions.CookKinds.Length, WorldActions.CookKinds.Select(static k => k.Type).Distinct().Count());
        Assert.True(WorldActions.FirstCookKindId + WorldActions.CookKinds.Length <= 255);
    }

    [Fact]
    public void TheItemTextsCarryEachEntrysPlaceTextAndReason()
    {
        var bytes = WorldActions.ItemTexts(0x40000001, [(2, new WorldActions.WorldAction(WorldActions.SmeltId, "Go", "No"))]);

        Assert.Equal(
            new byte[] { 0xBF, 0, 18, 0x00, 0xB2, 0x40, 0x00, 0x00, 0x01, 1, 0, 2, 2, (byte)'G', (byte)'o', 2, (byte)'N', (byte)'o' },
            bytes
        );
    }

    [Fact]
    public void TheShardClientTextHasTheActionPlaceholder()
    {
        var root = AppContext.BaseDirectory;

        while (root is not null && !File.Exists(Path.Combine(root, "data", "client", "Clilocs.txt")))
        {
            root = Path.GetDirectoryName(root);
        }

        Assert.NotNull(root);
        Assert.Contains($"{WorldActions.EntryNumber}\tAction",File.ReadAllLines(Path.Combine(root!, "data", "client", "Clilocs.txt")));
    }

    [Theory]
    [InlineData(false, false, false, true, null)]
    [InlineData(true, true, true, false, WorldActions.FullHealth)]       // full health first, as stock says it first
    [InlineData(false, true, true, false, WorldActions.PoisonedNoHeal)]
    [InlineData(false, false, true, true, WorldActions.HealPotionWait)]
    [InlineData(false, false, false, false, WorldActions.NoFreeHand)]
    public void AHealPotionSaysWhyItCannotBeDrunk(bool fullHealth, bool poisoned, bool waiting, bool freeHand, string? expected) =>
        Assert.Equal(expected, WorldActions.HealPotionReason(fullHealth, poisoned, waiting, freeHand));

    [Theory]
    [InlineData(true, true, null)]
    [InlineData(false, true, WorldActions.NotPoisoned)]
    [InlineData(true, false, WorldActions.NoFreeHand)]
    public void ACurePotionSaysWhyItCannotBeDrunk(bool poisoned, bool freeHand, string? expected) =>
        Assert.Equal(expected, WorldActions.CurePotionReason(poisoned, freeHand));

    [Theory]
    [InlineData(false, true, null)]
    [InlineData(true, true, WorldActions.FullStamina)]
    [InlineData(false, false, WorldActions.NoFreeHand)]
    public void ARefreshPotionSaysWhyItCannotBeDrunk(bool fullStamina, bool freeHand, string? expected) =>
        Assert.Equal(expected, WorldActions.RefreshPotionReason(fullStamina, freeHand));

    [Theory]
    [InlineData(true, true, true, true, null)]
    [InlineData(false, true, true, true, WorldActions.NoLockpick)]
    [InlineData(true, false, true, true, WorldActions.CannotPick)]
    [InlineData(true, true, false, true, WorldActions.LockBeyondSkill)]
    [InlineData(true, true, true, false, WorldActions.TooFarFromLock)]
    public void PickingALockSaysWhyItCannotBeDone(bool hasLockpick, bool pickable, bool skill, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.PickReason(hasLockpick, pickable, skill, inRange));

    [Theory]
    [InlineData(true, true, null)]
    [InlineData(false, true, WorldActions.NoKey)]
    [InlineData(true, false, WorldActions.TooFarFromLock)]
    public void AKeySaysWhyItCannotBeUsed(bool hasKey, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.KeyReason(hasKey, inRange));

    [Fact]
    public void EveryActionHasItsOwnId()
    {
        var ids = typeof(WorldActions).GetFields(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static)
            .Where(static f => f.IsLiteral && f.FieldType == typeof(byte) && f.Name.EndsWith("Id", StringComparison.Ordinal) && f.Name != nameof(WorldActions.FirstCookKindId))
            .Select(static f => (byte)f.GetRawConstantValue()!)
            .ToList();

        Assert.Equal(ids.Count, ids.Distinct().Count());
        Assert.DoesNotContain(ids, static id => id >= WorldActions.FirstCookKindId && id < WorldActions.FirstCookKindId + WorldActions.CookKinds.Length);
    }

    [Theory]
    [InlineData(false, false, true, null)]
    [InlineData(true, true, false, WorldActions.WornOut)]
    [InlineData(false, true, false, WorldActions.NeedSmithy)]
    [InlineData(false, false, false, "Requires ingots.")]
    public void ACraftToolSaysWhyItCannotBeUsed(bool wornOut, bool smithyMissing, bool hasMaterials, string? expected) =>
        Assert.Equal(expected, WorldActions.CraftReason(wornOut, smithyMissing, hasMaterials, "Requires ingots."));

    [Theory]
    [InlineData(100, 95, 10, 0, 10, 0, null)]
    [InlineData(50, 95, 10, 0, 10, 0, "You are not strong enough to wear that: it needs 95 Strength.")]
    [InlineData(100, 0, 10, 80, 10, 0, "You are not nimble enough to wear that: it needs 80 Dexterity.")]
    [InlineData(100, 0, 100, 0, 5, 20, "You are not smart enough to wear that: it needs 20 Intelligence.")]
    public void GearSaysTheStatItNeeds(int str, int strReq, int dex, int dexReq, int intel, int intReq, string? expected) =>
        Assert.Equal(expected, WorldActions.WearReason(null, str, strReq, dex, dexReq, intel, intReq, false));

    [Fact]
    public void GearForTheOtherSexSaysSo() =>
        Assert.Equal("Only females can wear this.", WorldActions.WearReason("Only females can wear this.", 100, 0, 100, 0, 100, 0, true));

    [Theory]
    [InlineData(false, false, 20, 11, null)]
    [InlineData(true, false, 20, 11, WorldActions.AlreadyCasting)]
    [InlineData(false, true, 20, 11, WorldActions.Frozen)]
    [InlineData(false, false, 10, 11, "Not enough mana: Recall needs 11.")]
    public void CastingSaysWhyItCannotBeDone(bool casting, bool frozen, int mana, int cost, string? expected) =>
        Assert.Equal(expected, WorldActions.CastReason(casting, frozen, mana, cost, "Recall"));

    [Fact]
    public void TravelReasonsComeInTheStockOrder()
    {
        Assert.Equal(WorldActions.RuneNotMarked, WorldActions.TravelReason(false, false, WorldActions.NoRecallMeans, null, null, true, true, true));
        Assert.Equal(WorldActions.NoRecallMeans, WorldActions.TravelReason(true, false, WorldActions.NoRecallMeans, null, null, true, true, true));
        Assert.Equal("Requires black pearl.", WorldActions.TravelReason(true, true, WorldActions.NoRecallMeans, "Requires black pearl.", null, true, true, true));
        Assert.Equal(WorldActions.CriminalCannotTravel, WorldActions.TravelReason(true, true, WorldActions.NoRecallMeans, "", null, true, true, true));
        Assert.Equal(WorldActions.InCombatCannotTravel, WorldActions.TravelReason(true, true, WorldActions.NoRecallMeans, null, null, false, true, true));
        Assert.Equal(WorldActions.TooHeavyToTravel, WorldActions.TravelReason(true, true, WorldActions.NoRecallMeans, null, null, false, false, true));
        Assert.Null(WorldActions.TravelReason(true, true, WorldActions.NoRecallMeans, null, null, false, false, false));
    }

    [Fact]
    public void MissingReagentsAreNamedPlainly()
    {
        Assert.Equal("black pearl", WorldActions.ReagentName(typeof(Server.Items.BlackPearl)));
        Assert.Equal("Requires black pearl, bloodmoss and mandrake root.", WorldActions.NeedsReagents(["black pearl", "bloodmoss", "mandrake root"]));
        Assert.Equal("Requires bloodmoss.", WorldActions.NeedsReagents(["bloodmoss"]));
    }

    [Theory]
    [InlineData(1, -3.0)]
    [InlineData(2, 41.0)]
    [InlineData(4, 61.0)]
    [InlineData(6, 70.0)]
    public void ATreasureMapNeedsItsCartography(int level, double skill) => Assert.Equal(skill, WorldActions.MapDecodeSkill(level));

    [Theory]
    [InlineData(null, false, true, false, null)]
    [InlineData(WorldActions.RangedOnDummy, true, false, true, WorldActions.RangedOnDummy)]
    [InlineData(null, true, true, false, WorldActions.MountedPractice)]
    [InlineData(null, false, false, false, "far")]
    [InlineData(null, false, true, true, WorldActions.DummyCapped)]
    public void PractisingSaysWhyItCannotBeDone(string? weapon, bool mounted, bool inRange, bool capped, string? expected) =>
        Assert.Equal(expected, WorldActions.PracticeReason(weapon, mounted, inRange, capped, "far"));

    [Fact]
    public void TamingSaysWhyItCannotBeDoneInTheStockOrder()
    {
        string? tame(bool tamable = true, bool tameAlready = false, string? sex = null, bool followers = false, string? refusal = null, bool owners = false,
            bool subdue = false, double skill = 50, double min = 30, bool inRange = true, bool resting = false) =>
            WorldActions.TameReason(tamable, tameAlready, sex, followers, refusal, owners, subdue, skill, min, inRange, resting);

        Assert.Null(tame());
        Assert.Equal(WorldActions.CannotBeTamed, tame(tamable: false, skill: 0, inRange: false));
        Assert.Equal(WorldActions.LooksTame, tame(tameAlready: true));
        Assert.Equal(WorldActions.OnlyFemalesTame, tame(sex: WorldActions.OnlyFemalesTame, followers: true));
        Assert.Equal(WorldActions.TooManyFollowers, tame(followers: true, skill: 0));
        Assert.Equal("No pets in dungeons.", tame(refusal: "No pets in dungeons.", skill: 0));
        Assert.Equal(WorldActions.TooManyOwners, tame(owners: true));
        Assert.Equal(WorldActions.MustSubdue, tame(subdue: true));
        Assert.Equal("You need 35.1 Animal Taming to tame this.", tame(skill: 20, min: 35.1, inRange: false));
        Assert.Equal(WorldActions.TooFarToTame, tame(inRange: false, resting: true));
        Assert.Equal(WorldActions.SkillResting, tame(resting: true));
    }

    [Fact]
    public void TheStockTameEntryIsFoundByTheNumberTheEngineStores() =>
        // BaseCreature.TameEntry passes 6130; the engine keeps numbers below 0x8000 as 3000000 + n, and the menu is searched by that
        Assert.Equal(WorldActions.StockTameNumber, new Server.ContextMenus.ContextMenuEntry(6130).Number);

    [Fact]
    public void ThePetFriendEntriesSayWhatAFriendMayDo()
    {
        // the stock entries pass these numbers as they are (BaseAI ContextMenu.cs), so the menu is searched by them
        Assert.Equal(WorldActions.StockAddFriendNumber, new Server.ContextMenus.ContextMenuEntry(3006110).Number);
        Assert.Equal(WorldActions.StockRemoveFriendNumber, new Server.ContextMenus.ContextMenuEntry(3006099).Number);

        Assert.Equal(
            "Choose another player who may also tell it to follow, stop and stay, and feed it. It stays yours.",
            WorldActions.FriendTooltip(true, false)
        );
        Assert.Contains("and feed it and open its pack.", WorldActions.FriendTooltip(true, true));
        Assert.Equal("Choose one of its friends to take that back.", WorldActions.FriendTooltip(false, false));
    }

    [Theory]
    [InlineData(false, true, false, false, true, null)]
    [InlineData(true, false, true, true, false, WorldActions.Polymorphed)]
    [InlineData(false, false, true, false, true, WorldActions.CannotRideNow)]
    [InlineData(false, true, true, false, true, WorldActions.DismountFirst)]
    [InlineData(false, true, false, true, false, WorldActions.TooFarToRide)]
    [InlineData(false, true, false, true, true, WorldActions.MountTooIll)]
    public void RidingSaysWhyItCannotBeDone(bool polymorphed, bool allowed, bool mounted, bool poisoned, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.RideReason(polymorphed, allowed, mounted, poisoned, inRange));

    [Theory]
    [InlineData(true, true, null)]
    [InlineData(false, false, WorldActions.NoFoodItEats)]
    [InlineData(true, false, WorldActions.TooFarToFeed)]
    public void FeedingAPetSaysWhyItCannotBeDone(bool hasFood, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.FeedReason(hasFood, inRange));

    [Theory]
    [InlineData(true, true, false, true, null)]
    [InlineData(false, false, true, false, WorldActions.NoBandages)]
    [InlineData(true, false, true, false, WorldActions.ItIsNotHurt)]
    [InlineData(true, true, true, false, WorldActions.YoungCannotHeal)]
    [InlineData(true, true, false, false, WorldActions.TooFarToBandage)]
    public void BandagingSomeoneSaysWhyItCannotBeDone(bool hasBandage, bool hurt, bool young, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.BandageReason(hasBandage, hurt, WorldActions.ItIsNotHurt, young, inRange));

    [Theory]
    [InlineData(false, false, false, true, null)]
    [InlineData(true, true, true, false, WorldActions.CriminalAtGate)]
    [InlineData(false, true, true, false, WorldActions.FightingAtGate)]
    [InlineData(false, false, true, false, WorldActions.CastingAtGate)]
    [InlineData(false, false, false, false, WorldActions.TooFarFromGate)]
    public void APublicMoongateSaysWhyItCannotBeUsed(bool criminal, bool fighting, bool casting, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.TravelReason(criminal, fighting, casting, inRange));

    [Theory]
    [InlineData(true, false, false, true, null)]
    [InlineData(false, true, true, false, WorldActions.NoEmptyVessel)]
    [InlineData(true, true, true, false, WorldActions.NotYourCow)]
    [InlineData(true, false, true, false, WorldActions.CowMilkedOut)]
    [InlineData(true, false, false, false, WorldActions.TooFarToMilk)]
    public void MilkingACowSaysWhyItCannotBeDone(bool hasVessel, bool someoneElses, bool milkedOut, bool inRange, string? expected) =>
        Assert.Equal(expected, WorldActions.MilkReason(hasVessel, someoneElses, milkedOut, inRange));

    [Fact]
    public void ACowHasMilkAgainADayAfterItRanDry()
    {
        var now = new DateTime(2026, 11, 1, 12, 0, 0);

        Assert.True(WorldActions.MilkedOut(0, now.AddHours(-23), now));
        Assert.False(WorldActions.MilkedOut(0, now.AddHours(-25), now));
        Assert.False(WorldActions.MilkedOut(2, now, now));
    }

    [Theory]
    [InlineData(80.0, 80.0, true)]
    [InlineData(79.9, 100.0, false)]
    [InlineData(100.0, 79.9, false)]
    public void ABandageResurrectsAt80HealingAnd80Anatomy(double healing, double anatomy, bool expected) =>
        Assert.Equal(expected, WorldActions.CanResurrect(healing, anatomy));

    [Fact]
    public void ALoreSkillIsOfferedOnlyToSomeoneWhoHasIt()
    {
        Assert.False(WorldActions.HasSkill(0.0));
        Assert.True(WorldActions.HasSkill(0.1));
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate()
    {
        Assert.False(new DeferredFeatureFlags().WorldActions);
        Assert.Contains(nameof(DeferredFeatureFlags.WorldActions), new DeferredFeatureFlags { WorldActions = true }.EnabledNames());
    }
}
