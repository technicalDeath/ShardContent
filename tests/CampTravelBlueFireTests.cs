using System.Text.Json;
using Xunit;
using static BritanniaRenaissance.Content.CampTravelService;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The blue travel fire (docs/Camp-Travel-Blue-Fire-Proposal.md): the rule that decides which fire is a lighter's travel fire, what the
/// lighter is told, the refusal for an ordinary fire, the guide page and the configuration. The parts that need game objects (the claim
/// table, the hue and the name on the fire) are checked live on a disposable host.
/// </summary>
public class CampTravelBlueFireTests
{
    private static readonly CampTravelRules Rules = new();

    private static ShardRules Shipped()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- which fire is the travel fire

    [Theory]
    [InlineData(0, false, false, false, FireClass.LowCamping)] // Camping under 50: no places, so no travel fire
    [InlineData(0, false, true, false, FireClass.LowCamping)] // a claim holder whose Camping fell below 50 loses it
    [InlineData(1, false, false, false, FireClass.Travel)] // the first fire a lighter with a place lights takes the claim
    [InlineData(6, false, false, false, FireClass.Travel)]
    [InlineData(1, false, true, false, FireClass.Travel)] // the holder stays the travel fire
    [InlineData(1, false, false, true, FireClass.AlreadyHave)] // a second fire while another is burning is ordinary
    [InlineData(1, true, false, false, FireClass.Embers)] // embers never hold or take the claim
    [InlineData(1, true, true, false, FireClass.Embers)]
    [InlineData(1, true, false, true, FireClass.Embers)]
    public void TheClassFollowsCampingTheClaimAndTheEmbers(int capacity, bool embers, bool holdsThis, bool holdsOther, FireClass expected) =>
        Assert.Equal(expected, Classify(new FireClassFacts(capacity, embers, holdsThis, holdsOther)));

    [Fact]
    public void TheFirstFireKeepsTheClaimWhileItBurns()
    {
        // Two fires of one lighter: the older holds the claim, so the newer is ordinary (the order the service evaluates them in).
        var older = Classify(new FireClassFacts(3, false, false, false));
        var newer = Classify(new FireClassFacts(3, false, false, true));

        Assert.Equal(FireClass.Travel, older);
        Assert.Equal(FireClass.AlreadyHave, newer);
    }

    [Fact]
    public void WhenTheTravelFireGoesToEmbersTheNextFireTakesTheClaim()
    {
        // The embers fire is Embers (the claim is released); a burning fire of the same lighter then finds nobody holding it.
        Assert.Equal(FireClass.Embers, Classify(new FireClassFacts(3, true, true, false)));
        Assert.Equal(FireClass.Travel, Classify(new FireClassFacts(3, false, false, false)));
    }

    [Fact]
    public void ARelitEmbersFireIsOrdinaryWhenAnotherFireNowHoldsTheClaim()
    {
        Assert.Equal(FireClass.AlreadyHave, Classify(new FireClassFacts(3, false, false, true)));
        Assert.Equal(FireClass.Travel, Classify(new FireClassFacts(3, false, false, false)));
    }

    [Fact]
    public void ATravelFireIsNamedForItsLighter()
    {
        Assert.Equal("Rowan's travel campfire", TravelFireName("Rowan"));
        Assert.Equal("someone's travel campfire", TravelFireName(null));
    }

    // ---- the refusal for an ordinary fire

    [Fact]
    public void AnOrdinaryFireIsRefusedWithItsOwnWords()
    {
        var facts = new TravelFacts { FireIsTravel = false };

        Assert.Equal(Refusal.NotTravelFire, Plan(Rules, facts));
        Assert.Contains("ordinary campfire", Describe(Refusal.NotTravelFire, Rules, facts));
        Assert.Contains("blue travel fire", Describe(Refusal.NotTravelFire, Rules, facts));
        Assert.Equal("ordinary fire", ShortLabel(Refusal.NotTravelFire));
    }

    [Fact]
    public void EmbersAreReportedBeforeAnOrdinaryFireAndAPartyBeforeBoth()
    {
        Assert.Equal(Refusal.Embers, Plan(Rules, new TravelFacts { FireIsTravel = false, FireEmbers = true }));
        Assert.Equal(Refusal.NotInParty, Plan(Rules, new TravelFacts { FireIsTravel = false, LighterInParty = false }));
        Assert.Equal(Refusal.None, Plan(Rules, new TravelFacts()));
    }

    // ---- what the lighter is told

    [Fact]
    public void ATravelFireIsToldItBurnsBlueAndThatThereIsOnlyOne()
    {
        var text = NoticeText(Rules, FireNotice.Lit, new NoticeContext(3, 0, false, FireClass.Travel))!;

        Assert.Contains("burns blue", text);
        Assert.Contains(Command, text);
        Assert.Contains("30 seconds", text);
        Assert.Contains("3 places", text);
        Assert.Contains("one travel fire at a time", text);
    }

    [Fact]
    public void ASecondFireIsToldItIsOrdinaryAndWhereTheTravelFireIs()
    {
        var text = NoticeText(Rules, FireNotice.Lit, new NoticeContext(3, 0, false, FireClass.AlreadyHave, OtherPlace: "Britain"))!;

        Assert.Contains("ordinary campfire", text);
        Assert.Contains("travel fire is still burning near Britain", text);
        Assert.DoesNotContain(Command, text);
        Assert.Null(NoticeText(Rules, FireNotice.Secure, new NoticeContext(3, 0, false, FireClass.AlreadyHave)));
    }

    [Fact]
    public void ALighterUnderCampingFiftyKeepsTheStockLitNotice()
    {
        var text = NoticeText(Rules, FireNotice.Lit, new NoticeContext(0, 0, false, FireClass.LowCamping))!;

        Assert.Contains("Camping skill is 50", text);
        Assert.DoesNotContain("blue", text);
    }

    [Fact]
    public void ATravelFireInEmbersTellsTheLighterHowToGetTheBlueBack()
    {
        var travel = NoticeText(Rules, FireNotice.Embers, new NoticeContext(3, 0, false, FireClass.Embers, WasTravel: true))!;
        var ordinary = NoticeText(Rules, FireNotice.Embers, new NoticeContext(3, 0, false, FireClass.Embers))!;

        Assert.Contains("travel fire is down to embers", travel);
        Assert.Contains("Feed it with Kindling", travel);
        Assert.Contains("next fire you light will burn blue", travel);
        Assert.Contains("Use Kindling beside it to relight it", ordinary);
        Assert.DoesNotContain("blue", ordinary);
    }

    [Fact]
    public void AnOrdinaryFireIsNeverAdvertisedAfterARelightOrAtItsEnd()
    {
        Assert.Null(NoticeText(Rules, FireNotice.Relit, new NoticeContext(3, 0, true, FireClass.AlreadyHave)));
        Assert.DoesNotContain(Command, NoticeText(Rules, FireNotice.Relit, new NoticeContext(3, 0, false, FireClass.AlreadyHave))!);
        Assert.Equal("Your campfire has burned out.", NoticeText(Rules, FireNotice.Out, new NoticeContext(3, 0, false, FireClass.AlreadyHave)));
        Assert.Contains("will burn blue", NoticeText(Rules, FireNotice.Out, new NoticeContext(3, 0, false, FireClass.Travel))!);
    }

    [Fact]
    public void WithTheFlagOffEveryNoticeIsTheStockOne()
    {
        // The default class is Stock: the texts of the shipped feature, word for word.
        Assert.Contains("Your campfire is lit", NoticeText(Rules, FireNotice.Lit, new NoticeContext(3, 0, false))!);
        Assert.DoesNotContain("blue", NoticeText(Rules, FireNotice.Lit, new NoticeContext(3, 0, false))!);
        Assert.Contains("cannot travel", NoticeText(Rules, FireNotice.Embers, new NoticeContext(3, 0, false))!);
        Assert.Equal("Your campfire has burned out.", NoticeText(Rules, FireNotice.Out, new NoticeContext(3, 0, false)));
    }

    [Fact]
    public void AClassChangeIsToldOnlyWhenBlueIsGainedOrLost()
    {
        Assert.Equal(BurnsBlueText(), ClassChangeText(FireClass.AlreadyHave, FireClass.Travel, Rules));
        Assert.Equal(BurnsBlueText(), ClassChangeText(FireClass.LowCamping, FireClass.Travel, Rules));
        Assert.Contains("Camping 50", ClassChangeText(FireClass.Travel, FireClass.LowCamping, Rules));
        Assert.Null(ClassChangeText(FireClass.Embers, FireClass.Travel, Rules));
        Assert.Null(ClassChangeText(FireClass.Travel, FireClass.Embers, Rules));
        Assert.Null(ClassChangeText(FireClass.Travel, FireClass.Travel, Rules));
        Assert.Contains("one travel fire at a time", BurnsBlueText());
    }

    // ---- the guide

    [Fact]
    public void TheGuidePageDescribesTheBlueFireOnlyWhenItIsOn()
    {
        var blue = string.Join(" ", GuideParagraphs(Rules, blueFire: true));
        var stock = string.Join(" ", GuideParagraphs(Rules));

        Assert.Contains("burns blue", blue);
        Assert.Contains("one blue fire at a time", blue);
        Assert.Contains("Camping 50 or more", blue);
        Assert.Contains("burns down to embers", blue);
        Assert.DoesNotContain("blue", stock);
        Assert.Equal(GuideParagraphs(Rules).Count, GuideParagraphs(Rules, blueFire: true).Count);
    }

    [Fact]
    public void TheWelcomeGuideCarriesTheBlueFireWording()
    {
        var context = new WelcomeGuide.Context(Theft: false, SkillBank: false, SkillClasses: false, CampTravel: true, TravelWarning: false, CampingKit: true, CampingFires: true, CampTravelBlueFire: true);
        var page = WelcomeGuide.Topics(context, Rules, camping: new CampingRules()).Single(t => t.Key == "camp");
        var off = WelcomeGuide.Topics(context with { CampTravelBlueFire = false }, Rules, camping: new CampingRules()).Single(t => t.Key == "camp");

        Assert.Contains("burns blue", string.Join(" ", page.Paragraphs));
        Assert.DoesNotContain("blue", string.Join(" ", off.Paragraphs));
    }

    // ---- config

    [Fact]
    public void TheShippedFileTurnsTheBlueFireOnWithTheOwnersFrostbiteHue()
    {
        // Enabled 2026-10-08 on the owner's explicit "activate"; he chose client hue 2796 (Frostbite) from the sheet of candidates.
        var rules = Shipped();

        Assert.True(rules.FeatureFlags.CampTravelBlueFire);
        Assert.True(rules.FeatureFlags.CampingTravel);
        Assert.Equal(2796, rules.CampTravel.FireHue);
        Assert.Equal(2796, Rules.FireHue);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
        Assert.Contains(nameof(DeferredFeatureFlags.CampTravelBlueFire), rules.FeatureFlags.EnabledNames());
    }

    [Fact]
    public void TheBlueFireNeedsCampTravel()
    {
        var rules = Shipped();

        rules.FeatureFlags.CampTravelBlueFire = true;
        rules.FeatureFlags.CampingTravel = false;

        Assert.Contains("campTravelBlueFire requires campingTravel.", ShardRulesConfiguration.Validate(rules));

        rules.FeatureFlags.CampingTravel = true;

        Assert.DoesNotContain("campTravelBlueFire requires campingTravel.", ShardRulesConfiguration.Validate(rules));
        Assert.Contains(nameof(DeferredFeatureFlags.CampTravelBlueFire), rules.FeatureFlags.EnabledNames());
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-5)]
    [InlineData(3001)]
    public void AHueOutsideTheClientTableIsRejected(int hue)
    {
        var errors = new List<string>();

        Validate(new CampTravelRules { FireHue = hue }, errors);

        Assert.Single(errors);
        Assert.Contains("campTravel.fireHue", errors[0]);
    }

    [Fact]
    public void TheDefaultHueIsInTheClientTable()
    {
        var errors = new List<string>();

        Validate(Rules, errors);

        Assert.Empty(errors);
        Assert.InRange(Rules.FireHue, 1, 3000);
    }

    [Fact]
    public void WithoutLoadedSettingsTheBlueFireIsOff() => Assert.False(BlueFireEnabled);
}
