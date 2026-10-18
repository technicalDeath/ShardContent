using System.Text.Json;
using Server.Mobiles;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Death recovery: longer player corpses, the corpse compass, blue self-loot, the killer going home, materializing (docs/Death-Recovery-Plan.md).</summary>
public class DeathRecoveryTests
{
    private static readonly DateTime Now = new(2026, 10, 17, 12, 0, 0);
    private static readonly DeathRecoveryRules Rules = new();

    private static ShardRules Shipped() =>
        JsonSerializer.Deserialize<ShardRules>(
            File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"))
        )!;

    // ---- the corpse time

    [Fact]
    public void APlayerCorpseLastsTenMinutesAndAMonsterCorpseKeepsTheStockTime()
    {
        Assert.Equal(TimeSpan.FromMinutes(10), LongerPlayerCorpses.DecayTime(true, true, 10));
        Assert.Null(LongerPlayerCorpses.DecayTime(true, false, 10));
        Assert.Null(LongerPlayerCorpses.DecayTime(false, true, 10));
    }

    [Fact]
    public void TheNoticeQuotesTheTenMinutes() =>
        Assert.StartsWith("Your corpse will turn to bones in 10 minutes,", CorpseTimerNoticeService.Text(TimeSpan.FromMinutes(10), TimeSpan.FromMinutes(7)));

    // ---- the compass

    [Theory]
    [InlineData(true, false, true, 30, true)]   // the corpse is gone
    [InlineData(false, true, true, 30, true)]   // emptied
    [InlineData(false, false, true, 2, true)]   // the owner is beside it
    [InlineData(false, false, true, 3, false)]
    [InlineData(false, false, false, 1, false)] // another map: still pointing
    public void TheArrowStopsAtTheCorpseOrWhenItIsGoneOrEmpty(bool gone, bool empty, bool sameMap, int distance, bool stops) =>
        Assert.Equal(stops, CorpseCompass.Stops(gone, empty, sameMap, distance, Rules.CompassStopRange));

    // ---- blue self-loot

    [Fact]
    public void OnlyABlueOwnerSelfLoots()
    {
        Assert.True(BlueSelfLoot.Allowed(true, true, false, false));
        Assert.False(BlueSelfLoot.Allowed(true, true, true, false));  // a murderer
        Assert.False(BlueSelfLoot.Allowed(true, true, false, true));  // a criminal
        Assert.False(BlueSelfLoot.Allowed(true, false, false, false)); // someone else's corpse
        Assert.False(BlueSelfLoot.Allowed(false, true, false, false));
    }

    // ---- the killer goes home

    [Fact]
    public void TheKillerGoesHomeOnlyWhenItFightsNobodyElse()
    {
        Assert.True(KillerGoesHome.GoesHome(true, true, 0));
        Assert.False(KillerGoesHome.GoesHome(true, true, 1)); // the owner: "only if the monster is not engaged in combat with someone else"
        Assert.False(KillerGoesHome.GoesHome(true, false, 0)); // a pet, a summons, or dead
        Assert.False(KillerGoesHome.GoesHome(false, true, 0));
    }

    [Fact]
    public void TheSpareTimeCountsFromWhenTheKillerFirstSeesThePlayerAgain()
    {
        var spare = TimeSpan.FromSeconds(Rules.KillerSpareSeconds);

        Assert.True(KillerGoesHome.StillSpared(null, Now, spare));
        Assert.True(KillerGoesHome.StillSpared(Now.AddSeconds(-119), Now, spare));
        Assert.False(KillerGoesHome.StillSpared(Now.AddSeconds(-120), Now, spare));
    }

    // ---- materializing

    [Fact]
    public void MaterializingLastsTenMinutesOrSixtySecondsAfterTheCorpseIsOpened()
    {
        Assert.Equal(Now.AddMinutes(10), Materializing.Until(Now, null, Rules));
        Assert.Equal(Now.AddMinutes(3).AddSeconds(60), Materializing.Until(Now, Now.AddMinutes(3), Rules));
        Assert.Equal(Now.AddMinutes(10), Materializing.Until(Now, Now.AddMinutes(9.5), Rules));
    }

    [Theory]
    [InlineData(PlayerAction.UseItem, Materializing.Target.Door, true)]
    [InlineData(PlayerAction.UseItem, Materializing.Target.OwnContainer, true)] // looking in your pack, bank or a bag on your corpse
    [InlineData(PlayerAction.UseItem, Materializing.Target.OwnCorpse, true)]
    [InlineData(PlayerAction.UseItem, Materializing.Target.OwnGear, true)]      // the owner: equipping from your own pack keeps it
    [InlineData(PlayerAction.UseItem, Materializing.Target.OwnItem, false)]     // a potion or bandage
    [InlineData(PlayerAction.UseItem, Materializing.Target.Other, false)]
    [InlineData(PlayerAction.Lift, Materializing.Target.CorpseItem, true)]      // the owner: only items from their corpse
    [InlineData(PlayerAction.Lift, Materializing.Target.OwnItem, true)]         // sorting your own pack
    [InlineData(PlayerAction.Lift, Materializing.Target.OwnGear, true)]         // putting on or taking off your gear
    [InlineData(PlayerAction.Lift, Materializing.Target.BankItem, false)]       // the bank could arm you for the walk
    [InlineData(PlayerAction.UseItem, Materializing.Target.BankItem, false)]
    [InlineData(PlayerAction.Lift, Materializing.Target.Other, false)]
    [InlineData(PlayerAction.UseSkill, Materializing.Target.Other, false)]
    [InlineData(PlayerAction.CastSpell, Materializing.Target.Other, false)]
    [InlineData(PlayerAction.Attack, Materializing.Target.Other, false)]
    [InlineData(PlayerAction.Buy, Materializing.Target.Other, false)]
    [InlineData(PlayerAction.Sell, Materializing.Target.Other, false)]
    public void OnlyTakingFromYourCorpseKeepsYouBetweenWorlds(PlayerAction action, Materializing.Target target, bool keeps) =>
        Assert.Equal(keeps, Materializing.Keeps(action, target));

    [Fact]
    public void AnEndingActionAsksInADialogFirst()
    {
        // the owner: "The materializing warning should be a dialog like the criminal action warning"
        Assert.Equal("This will bring you fully back from Between Worlds, and monsters will be able to see you again.", Materializing.Warning);
        Assert.Equal("Between Worlds", Materializing.Name); // the owner: "Rename materializing to between worlds with the b and in the w capitalized"
        Assert.True(Materializing.ConfirmGump.Height <= 500);
        Assert.Contains("any other action asks you first", Materializing.StartText(Rules));
    }

    [Fact]
    public void TheStartLineGivesBothTimes() =>
        Assert.Contains("for up to 10 minutes, or until 60 seconds after you open your corpse", Materializing.StartText(Rules));

    // ---- the guide

    [Fact]
    public void TheDyingPageDescribesEachPartOnlyWhileItIsOn()
    {
        string Dying(WelcomeGuide.Context c) =>
            string.Join(" ", WelcomeGuide.Topics(c, new CampTravelRules(), camping: new CampingRules()).Single(t => t.Key == "dying").Paragraphs);

        var off = Dying(new WelcomeGuide.Context(false, false, false, false, false));
        var on = Dying(
            new WelcomeGuide.Context(
                false, false, false, false, false, LongerPlayerCorpses: true, CorpseCompass: true, BlueSelfLoot: true, KillerGoesHome: true, Materializing: true
            )
        );

        Assert.Contains("A healer can see a ghost only in war mode (Tab)", off);
        Assert.Contains("after about seven minutes", off);
        Assert.DoesNotContain("Between Worlds", off);
        Assert.Contains("after about 10 minutes", on);
        Assert.Contains("up to 10 minutes, or until a minute after you open your body", on);
        Assert.Contains("leaves you alone for 2 minutes after it next sees you", on);
        Assert.Contains("An arrow on your screen points to your body", on);
        Assert.Contains("When you come back you are Between Worlds", on);
        Assert.DoesNotContain("aterializ", on);
        Assert.Contains("goes back to where it lives", on);
        Assert.Contains("double-clicking your own body takes everything back", on);
    }

    [Fact]
    public void BetweenWorldsHidesFromMonstersButNotFromTownsfolk()
    {
        Assert.True(DeathRecovery.Monster(false, false, false));
        Assert.False(DeathRecovery.Monster(true, false, false));  // a vendor: the banker, the healer
        Assert.False(DeathRecovery.Monster(false, true, false));  // a guard
        Assert.False(DeathRecovery.Monster(false, false, true));  // a blue-named NPC
    }

    // ---- the flags and numbers

    [Fact]
    public void EveryFlagIsOffUntilTheOwnerSaysActivate()
    {
        var flags = new DeferredFeatureFlags();
        Assert.False(flags.LongerPlayerCorpses || flags.CorpseCompass || flags.BlueSelfLoot || flags.KillerGoesHome || flags.Materializing);
    }

    [Fact]
    public void TheShippedNumbersAreTheOwnersAndValidate()
    {
        var rules = Shipped().DeathRecovery;
        var errors = new List<string>();
        DeathRecoveryRules.Validate(rules, errors);

        Assert.Empty(errors);
        Assert.Equal(10, rules.PlayerCorpseMinutes);
        Assert.Equal(10, rules.MaterializingMinutes);
        Assert.Equal(60, rules.MaterializingAfterOpenSeconds);
        Assert.Equal(120, rules.KillerSpareSeconds);
        Assert.Equal(0x047E, rules.MaterializingHue);
    }
}
