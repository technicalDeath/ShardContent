using System.Text.Json;
using Server.Items;
using Xunit;
using static BritanniaRenaissance.Content.CampTravelService;

namespace BritanniaRenaissance.Content.Tests;

public class CampTravelServiceTests
{
    private static readonly CampTravelRules Rules = new();

    private static readonly TravelFacts Clear = new();

    private static List<string> Errors(CampTravelRules rules)
    {
        var errors = new List<string>();
        Validate(rules, errors);
        return errors;
    }

    private static ShardRules Shipped()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- places a fire takes (the owner's table: 1 at 50, 2 at 60, 3 at 70, 4 at 80, 5 at 90, 6 at grandmaster)

    [Theory]
    [InlineData(0.0, 0)]
    [InlineData(30.0, 0)]
    [InlineData(49.9, 0)]
    [InlineData(50.0, 1)]
    [InlineData(59.9, 1)]
    [InlineData(60.0, 2)]
    [InlineData(69.9, 2)]
    [InlineData(70.0, 3)]
    [InlineData(80.0, 4)]
    [InlineData(89.9, 4)]
    [InlineData(90.0, 5)]
    [InlineData(99.9, 5)]
    [InlineData(100.0, 6)]
    [InlineData(120.0, 6)]
    public void CapacityFollowsTheLightersRealCampingInTens(double skill, int places) =>
        Assert.Equal(places, Capacity(Rules, skill));

    [Fact]
    public void CapacityNumbersComeFromTheConfig()
    {
        var rules = new CampTravelRules { CapacityBaseSkill = 20.0, SkillPerArrival = 20.0, MaxArrivals = 3 };

        Assert.Equal(0, Capacity(rules, 39.9));
        Assert.Equal(1, Capacity(rules, 40.0));
        Assert.Equal(2, Capacity(rules, 60.0));
        Assert.Equal(3, Capacity(rules, 80.0));
        Assert.Equal(3, Capacity(rules, 100.0));
        Assert.Equal(40.0, SkillForFirstPlace(rules));
    }

    [Fact]
    public void TheFirstPlaceNeedsCampingFifty() => Assert.Equal(50.0, SkillForFirstPlace(Rules));

    // ---- the planner

    [Fact]
    public void ATripWithNothingInTheWayIsAllowed() => Assert.Equal(Refusal.None, Plan(Rules, Clear));

    public static TheoryData<string, Refusal> EachRefusal => new()
    {
        { nameof(TravelFacts.Enabled), Refusal.Disabled },
        { nameof(TravelFacts.TravelerAlive), Refusal.NotAlive },
        { nameof(TravelFacts.FireExists), Refusal.FireGone },
        { nameof(TravelFacts.FireIsOwn), Refusal.OwnFire },
        { nameof(TravelFacts.LighterInParty), Refusal.NotInParty },
        { nameof(TravelFacts.SameMap), Refusal.WrongMap },
        { nameof(TravelFacts.FireEmbers), Refusal.Embers },
        { nameof(TravelFacts.FireSecure), Refusal.NotSecure },
        { nameof(TravelFacts.AlreadyThere), Refusal.AlreadyThere },
        { nameof(TravelFacts.KnockedOut), Refusal.KnockedOut },
        { nameof(TravelFacts.InCombat), Refusal.Combat },
        { nameof(TravelFacts.Frozen), Refusal.Frozen },
        { nameof(TravelFacts.Overloaded), Refusal.Overloaded },
        { nameof(TravelFacts.CarriesSigil), Refusal.CarriesSigil },
        { nameof(TravelFacts.InHotZone), Refusal.FromHotZone },
        { nameof(TravelFacts.LeaveAllowed), Refusal.LeaveBlocked },
        { nameof(TravelFacts.DestinationAllowed), Refusal.DestinationBlocked },
        { nameof(TravelFacts.HasArrivalTile), Refusal.NoArrivalTile }
    };

    [Theory]
    [MemberData(nameof(EachRefusal))]
    public void EachConditionRefusesTheTripOnItsOwn(string property, Refusal expected)
    {
        var info = typeof(TravelFacts).GetProperty(property)!;
        var facts = Clear with { };

        info.SetValue(facts, !(bool)info.GetValue(Clear)!);

        Assert.Equal(expected, Plan(Rules, facts));
    }

    [Fact]
    public void ALighterBelowTheFirstPlaceTakesNobody() =>
        Assert.Equal(Refusal.LighterTooLow, Plan(Rules, Clear with { Capacity = 0 }));

    [Fact]
    public void AFireTakesExactlyItsCapacity()
    {
        Assert.Equal(Refusal.None, Plan(Rules, Clear with { Capacity = 2, Arrivals = 1 }));
        Assert.Equal(Refusal.Full, Plan(Rules, Clear with { Capacity = 2, Arrivals = 2 }));
        Assert.Equal(Refusal.Full, Plan(Rules, Clear with { Capacity = 2, Arrivals = 3 }));
    }

    [Fact]
    public void TheCooldownAndTheKindlingCostRefuse()
    {
        Assert.Equal(Refusal.Cooldown, Plan(Rules, Clear with { CooldownRemaining = TimeSpan.FromMinutes(12) }));
        Assert.Equal(Refusal.NoKindling, Plan(Rules, Clear with { Kindling = 1 }));
        Assert.Equal(Refusal.None, Plan(Rules, Clear with { Kindling = 2 }));
        Assert.Equal(Refusal.None, Plan(new CampTravelRules { KindlingCost = 0 }, Clear with { Kindling = 0 }));
    }

    [Fact]
    public void TheFirstThingInTheWayIsTheOneReported()
    {
        var everything = new TravelFacts
        {
            Enabled = false,
            TravelerAlive = false,
            FireExists = false,
            InCombat = true,
            InHotZone = true,
            Kindling = 0,
            CooldownRemaining = TimeSpan.FromMinutes(5)
        };

        Assert.Equal(Refusal.Disabled, Plan(Rules, everything));
        Assert.Equal(Refusal.NotAlive, Plan(Rules, everything with { Enabled = true }));
        Assert.Equal(Refusal.FireGone, Plan(Rules, everything with { Enabled = true, TravelerAlive = true }));
        Assert.Equal(
            Refusal.Combat,
            Plan(Rules, everything with { Enabled = true, TravelerAlive = true, FireExists = true })
        );
        Assert.Equal(
            Refusal.FromHotZone,
            Plan(Rules, everything with { Enabled = true, TravelerAlive = true, FireExists = true, InCombat = false })
        );
    }

    [Fact]
    public void CriminalsAndMurderersAreNotRefusedForWhatTheyAre()
    {
        // Owner ruling (2026-10-06): they may use camp travel; recent player combat is what stops them, as for anyone.
        Assert.DoesNotContain(Enum.GetNames<Refusal>(), name => name is "Criminal" or "Murderer");
        Assert.Equal(Refusal.None, Plan(Rules, Clear));
        Assert.Equal(Refusal.Combat, Plan(Rules, Clear with { InCombat = true }));
    }

    [Fact]
    public void OnlyLeavingAHotZoneIsRefused()
    {
        // Going to a Hot Zone camp is allowed once warned (the plan has no fact for it); leaving one by camp travel is not.
        Assert.Equal(Refusal.None, Plan(Rules, Clear with { InHotZone = false }));
        Assert.Equal(Refusal.FromHotZone, Plan(Rules, Clear with { InHotZone = true }));
    }

    // ---- what the player reads

    [Fact]
    public void EveryRefusalHasWords()
    {
        foreach (var refusal in Enum.GetValues<Refusal>().Where(r => r != Refusal.None))
        {
            Assert.False(string.IsNullOrWhiteSpace(Describe(refusal, Rules, Clear)), refusal.ToString());
        }

        Assert.Equal(string.Empty, Describe(Refusal.None, Rules, Clear));
    }

    [Fact]
    public void RefusalsNameTheNumbersTheyDependOn()
    {
        Assert.Contains("30 seconds", Describe(Refusal.NotSecure, Rules, Clear));
        Assert.Contains("Camping 50", Describe(Refusal.LighterTooLow, Rules, Clear));
        Assert.Contains("2 of 2", Describe(Refusal.Full, Rules, Clear with { Capacity = 2, Arrivals = 2 }));
        Assert.Contains("2 Kindling", Describe(Refusal.NoKindling, Rules, Clear));
        Assert.Contains(
            "23 minutes",
            Describe(Refusal.Cooldown, Rules, Clear with { CooldownRemaining = TimeSpan.FromMinutes(22.5) })
        );
    }

    [Fact]
    public void TheListLabelsAreShort()
    {
        Assert.Equal("ready", ShortLabel(Refusal.None));
        Assert.Equal("securing", ShortLabel(Refusal.NotSecure));
        Assert.Equal("full", ShortLabel(Refusal.Full));
        Assert.Equal("embers", ShortLabel(Refusal.Embers));
        Assert.Equal("not now", ShortLabel(Refusal.Combat));
    }

    [Theory]
    [InlineData(1800.0, "30 minutes")]
    [InlineData(61.0, "2 minutes")]
    [InlineData(60.0, "60 seconds")]
    [InlineData(40.2, "41 seconds")]
    [InlineData(0.2, "1 second")]
    public void SpanReadsInTheUnitAPlayerWouldUse(double seconds, string expected) =>
        Assert.Equal(expected, Span(TimeSpan.FromSeconds(seconds)));

    [Fact]
    public void TheHotZoneWarningSaysWhatTheRiskIs()
    {
        Assert.Contains("Hot Zone", HotZoneWarning);
        Assert.Contains("attack", HotZoneWarning);
    }

    // ---- cooldown

    [Fact]
    public void ACooldownReadsBackFromItsTag()
    {
        var now = new DateTime(2026, 10, 6, 12, 0, 0, DateTimeKind.Utc);
        var ready = now.AddMinutes(30).ToString("O", System.Globalization.CultureInfo.InvariantCulture);

        Assert.Equal(TimeSpan.FromMinutes(30), CooldownRemaining(ready, now));
        Assert.Equal(TimeSpan.FromMinutes(10), CooldownRemaining(ready, now.AddMinutes(20)));
        Assert.Equal(TimeSpan.Zero, CooldownRemaining(ready, now.AddMinutes(30)));
        Assert.Equal(TimeSpan.Zero, CooldownRemaining(ready, now.AddHours(5)));
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("not a time")]
    public void NoTagOrAGarbledTagMeansNoCooldown(string? tag) =>
        Assert.Equal(TimeSpan.Zero, CooldownRemaining(tag, DateTime.UtcNow));

    // ---- secure

    [Fact]
    public void AFireIsSecureAfterItsSecureTimeUnlessItIsEmbers()
    {
        Assert.False(IsSecure(Rules, TimeSpan.FromSeconds(29.9), false));
        Assert.True(IsSecure(Rules, TimeSpan.FromSeconds(30.0), false));
        Assert.True(IsSecure(Rules, TimeSpan.FromMinutes(10), false));
        Assert.False(IsSecure(Rules, TimeSpan.FromMinutes(10), true));
    }

    // ---- keeping the lighter informed

    private static FireView Seen(CampfireStatus status = CampfireStatus.Burning, bool secure = false, bool gone = false) =>
        new(gone, status, secure);

    [Fact]
    public void ANewFireTellsTheLighterOnceThatItIsLit()
    {
        var tracker = new NoticeTracker();

        Assert.Equal([FireNotice.Lit], tracker.Advance(Seen()));
        Assert.Empty(tracker.Advance(Seen()));
        Assert.Empty(tracker.Advance(Seen()));
    }

    [Fact]
    public void AFiresWholeLifeIsToldOncePerMoment()
    {
        var tracker = new NoticeTracker();
        var told = new List<FireNotice>();

        told.AddRange(tracker.Advance(Seen()));
        told.AddRange(tracker.Advance(Seen(secure: true)));
        told.AddRange(tracker.Advance(Seen(secure: true)));
        told.AddRange(tracker.Advance(Seen(CampfireStatus.Extinguishing, true)));
        told.AddRange(tracker.Advance(Seen(CampfireStatus.Extinguishing, true)));
        told.AddRange(tracker.Advance(Seen(CampfireStatus.Off)));
        told.AddRange(tracker.Advance(Seen(CampfireStatus.Off)));
        told.AddRange(tracker.Advance(Seen(gone: true)));
        told.AddRange(tracker.Advance(Seen(gone: true)));

        Assert.Equal(
            [FireNotice.Lit, FireNotice.Secure, FireNotice.Dimming, FireNotice.Embers, FireNotice.Out],
            told
        );
    }

    [Fact]
    public void FeedingAFireAnnouncesItBurningAgain()
    {
        var tracker = new NoticeTracker();

        tracker.Advance(Seen(secure: true));

        Assert.Equal([FireNotice.Dimming], tracker.Advance(Seen(CampfireStatus.Extinguishing, true)));
        Assert.Equal([FireNotice.Relit], tracker.Advance(Seen(secure: true)));
        Assert.Equal([FireNotice.Embers], tracker.Advance(Seen(CampfireStatus.Off)));
        Assert.Equal([FireNotice.Relit], tracker.Advance(Seen(secure: true)));
    }

    [Fact]
    public void AFireThatDropsStraightToEmbersIsToldAsEmbers()
    {
        var tracker = new NoticeTracker();

        tracker.Advance(Seen(secure: true));

        Assert.Equal([FireNotice.Embers], tracker.Advance(Seen(CampfireStatus.Off)));
    }

    [Fact]
    public void EmbersAreNeverToldAsSecure()
    {
        var tracker = new NoticeTracker();

        Assert.Equal([FireNotice.Lit, FireNotice.Embers], tracker.Advance(Seen(CampfireStatus.Off)));
        Assert.DoesNotContain(FireNotice.Secure, tracker.Advance(Seen(CampfireStatus.Off)));
    }

    [Fact]
    public void ANoticeAfterTheFireIsGoneIsNeverSent()
    {
        var tracker = new NoticeTracker();

        tracker.Advance(Seen());
        tracker.Advance(Seen(gone: true));

        Assert.Empty(tracker.Advance(Seen(secure: true)));
    }

    [Fact]
    public void TheLitNoticeNamesTheCommandAndWhatTheLightersSkillGives()
    {
        var text = NoticeText(Rules, FireNotice.Lit, new NoticeContext(3, 0, false))!;

        Assert.Contains(Command, text);
        Assert.Contains("3 places", text);
        Assert.Contains("30 seconds", text);
    }

    [Fact]
    public void ALighterWithTooLittleCampingIsToldWhatItTakes()
    {
        var text = NoticeText(Rules, FireNotice.Lit, new NoticeContext(0, 0, false))!;

        Assert.Contains(Command, text);
        Assert.Contains("Camping skill is 50", text);
        Assert.Null(NoticeText(Rules, FireNotice.Secure, new NoticeContext(0, 0, false)));
    }

    [Fact]
    public void TheSecureNoticeCountsThePlacesLeft()
    {
        var text = NoticeText(Rules, FireNotice.Secure, new NoticeContext(3, 1, false))!;

        Assert.Contains(Command, text);
        Assert.Contains("2 of 3 places left", text);
    }

    [Fact]
    public void AFullFireIsNotAdvertised()
    {
        Assert.Null(NoticeText(Rules, FireNotice.Secure, new NoticeContext(2, 2, false)));
        Assert.DoesNotContain(Command, NoticeText(Rules, FireNotice.Relit, new NoticeContext(2, 2, false))!);
    }

    [Fact]
    public void TheDimAndEmberNoticesTellTheLighterToFeedTheFire()
    {
        Assert.Contains("Kindling", NoticeText(Rules, FireNotice.Dimming, new NoticeContext(3, 0, false))!);
        Assert.Contains("cannot travel", NoticeText(Rules, FireNotice.Embers, new NoticeContext(3, 0, false))!);
        Assert.Contains("Kindling", NoticeText(Rules, FireNotice.Embers, new NoticeContext(3, 0, false))!);
        Assert.DoesNotContain("cannot travel", NoticeText(Rules, FireNotice.Embers, new NoticeContext(0, 0, false))!);
    }

    [Fact]
    public void FeedingYourOwnFireIsNotToldBackToYouButTheTravelNewsIs()
    {
        var own = NoticeText(Rules, FireNotice.Relit, new NoticeContext(3, 1, true))!;
        var other = NoticeText(Rules, FireNotice.Relit, new NoticeContext(3, 1, false))!;

        Assert.DoesNotContain("burns brightly again", own);
        Assert.Contains("2 of 3 places left", own);
        Assert.Contains("burns brightly again", other);
        Assert.Null(NoticeText(Rules, FireNotice.Relit, new NoticeContext(0, 0, true)));
    }

    [Fact]
    public void TheOutNoticeCountsTheArrivals()
    {
        Assert.Equal("Your campfire has burned out.", NoticeText(Rules, FireNotice.Out, new NoticeContext(3, 0, false)));
        Assert.Contains("1 party member travelled", NoticeText(Rules, FireNotice.Out, new NoticeContext(3, 1, false))!);
        Assert.Contains("2 party members travelled", NoticeText(Rules, FireNotice.Out, new NoticeContext(3, 2, false))!);
    }

    [Fact]
    public void AnArrivalIsToldToTheLighterWithTheCountAndWhenTheCampIsFull()
    {
        var some = ArrivalNoticeText("Sir Robin", 1, 3);
        var full = ArrivalNoticeText("Sir Robin", 3, 3);

        Assert.Contains("Sir Robin", some);
        Assert.Contains("1 of 3 places used", some);
        Assert.DoesNotContain("no places left", some);
        Assert.Contains("3 of 3 places used", full);
        Assert.Contains("no places left", full);
        Assert.Contains("1 of 1 place used", ArrivalNoticeText("Sir Robin", 1, 1));
    }

    // ---- where a camp is

    [Fact]
    public void ACampIsNamedByTownThenHotZoneThenSextantThenTheWilderness()
    {
        Assert.Equal("Britain", PlaceLabel("Britain", "Fire Island", "1\u00b0 2'N, 3\u00b0 4'E"));
        Assert.Equal("Fire Island", PlaceLabel(null, "Fire Island", "1\u00b0 2'N, 3\u00b0 4'E"));
        Assert.Equal("Fire Island", PlaceLabel("  ", "Fire Island", null));
        Assert.Equal("1\u00b0 2'N, 3\u00b0 4'E", PlaceLabel("", null, "1\u00b0 2'N, 3\u00b0 4'E"));
        Assert.Equal("the wilderness", PlaceLabel(null, null, null));
    }

    [Fact]
    public void SextantTextReadsLatitudeThenLongitude()
    {
        Assert.Equal("12\u00b0 30'S, 45\u00b0 10'E", SextantText(12, 30, true, 45, 10, true));
        Assert.Equal("0\u00b0 5'N, 100\u00b0 59'W", SextantText(0, 5, false, 100, 59, false));
    }

    // ---- what the [Welcome guide tells a player

    [Fact]
    public void TheGuidePageExplainsCampTravelWithTheConfiguredNumbers()
    {
        var paragraphs = GuideParagraphs(Rules);
        var text = string.Join(" ", paragraphs);

        Assert.Equal(4, paragraphs.Count);
        Assert.All(paragraphs, p => Assert.InRange(p.Length, 10, 600));
        Assert.Contains(Command, text);
        Assert.Contains("30 seconds", text);
        Assert.Contains("5 seconds", text);
        Assert.Contains("Bonded pets next to you come with you.", text);
        Assert.Contains("on your account", text);
        Assert.Contains("counted over the fire's whole life", text);
        Assert.Contains("leave a Hot Zone or a dungeon", text);
        Assert.Contains("Knocked Out or overloaded", text);
        Assert.Contains("2 Kindling", text);
        Assert.Contains("30 minutes", text);
        Assert.Contains("1 at Camping 50", text);
        Assert.Contains("one more for each 10 points, up to 6", text);
    }

    [Fact]
    public void TheGuidePageSaysCriminalsMayTravelButNotAfterCombat()
    {
        var text = string.Join(" ", GuideParagraphs(Rules));

        Assert.Contains("Criminals and murderers may use it, but nobody who attacked a player in the last 30 seconds can.", text);
        Assert.DoesNotContain("Criminals, murderers and", text);
    }

    [Fact]
    public void TheGuidePageFollowsTheConfiguredNumbers()
    {
        var rules = new CampTravelRules { SecureSeconds = 45, KindlingCost = 3, CooldownMinutes = 60, CapacityBaseSkill = 30, SkillPerArrival = 20, MaxArrivals = 4 };
        var text = string.Join(" ", GuideParagraphs(rules));

        Assert.Contains("45 seconds", text);
        Assert.Contains("3 Kindling", text);
        Assert.Contains("60 minutes", text);
        Assert.Contains("1 at Camping 50", text);
        Assert.Contains("one more for each 20 points, up to 4", text);
    }

    [Fact]
    public void TheHotZoneWarningHelpNamesBothWaysToStopIt()
    {
        Assert.Contains("[TravelWarning off", HotZoneWarningHelp);
        Assert.Contains("[TravelWarning on", HotZoneWarningHelp);
    }

    // ---- config

    [Fact]
    public void TheShippedNumbersAreTheSignedOffOnes()
    {
        Assert.Equal(5.0, Rules.ChannelSeconds);
        Assert.Equal(30.0, Rules.CooldownMinutes);
        Assert.Equal(2, Rules.KindlingCost);
        Assert.Equal(40.0, Rules.CapacityBaseSkill);
        Assert.Equal(10.0, Rules.SkillPerArrival);
        Assert.Equal(6, Rules.MaxArrivals);
        Assert.Equal(30.0, Rules.SecureSeconds);
        Assert.Equal(2, Rules.ArrivalRange);
        Assert.Empty(Errors(Rules));
    }

    [Theory]
    [InlineData(nameof(CampTravelRules.ChannelSeconds), 0.5)]
    [InlineData(nameof(CampTravelRules.ChannelSeconds), 31.0)]
    [InlineData(nameof(CampTravelRules.CooldownMinutes), -1.0)]
    [InlineData(nameof(CampTravelRules.CooldownMinutes), 1441.0)]
    [InlineData(nameof(CampTravelRules.CapacityBaseSkill), -1.0)]
    [InlineData(nameof(CampTravelRules.CapacityBaseSkill), 101.0)]
    [InlineData(nameof(CampTravelRules.SkillPerArrival), 0.0)]
    [InlineData(nameof(CampTravelRules.SkillPerArrival), 51.0)]
    [InlineData(nameof(CampTravelRules.SecureSeconds), -1.0)]
    [InlineData(nameof(CampTravelRules.SecureSeconds), 601.0)]
    public void AbsurdDecimalNumbersAreRejected(string property, double value)
    {
        var rules = new CampTravelRules();

        typeof(CampTravelRules).GetProperty(property)!.SetValue(rules, value);

        Assert.Single(Errors(rules));
    }

    [Theory]
    [InlineData(nameof(CampTravelRules.KindlingCost), -1)]
    [InlineData(nameof(CampTravelRules.KindlingCost), 21)]
    [InlineData(nameof(CampTravelRules.MaxArrivals), 0)]
    [InlineData(nameof(CampTravelRules.MaxArrivals), 21)]
    [InlineData(nameof(CampTravelRules.ArrivalRange), 0)]
    [InlineData(nameof(CampTravelRules.ArrivalRange), 6)]
    public void AbsurdWholeNumbersAreRejected(string property, int value)
    {
        var rules = new CampTravelRules();

        typeof(CampTravelRules).GetProperty(property)!.SetValue(rules, value);

        Assert.Single(Errors(rules));
    }

    [Fact]
    public void TheShippedFileCarriesTheDefaultsAndTurnsTheFlagOn()
    {
        var rules = Shipped();

        Assert.Equal(Rules.ChannelSeconds, rules.CampTravel.ChannelSeconds);
        Assert.Equal(Rules.CooldownMinutes, rules.CampTravel.CooldownMinutes);
        Assert.Equal(Rules.KindlingCost, rules.CampTravel.KindlingCost);
        Assert.Equal(Rules.CapacityBaseSkill, rules.CampTravel.CapacityBaseSkill);
        Assert.Equal(Rules.SkillPerArrival, rules.CampTravel.SkillPerArrival);
        Assert.Equal(Rules.MaxArrivals, rules.CampTravel.MaxArrivals);
        Assert.Equal(Rules.SecureSeconds, rules.CampTravel.SecureSeconds);
        Assert.Equal(Rules.ArrivalRange, rules.CampTravel.ArrivalRange);
        Assert.True(rules.FeatureFlags.CampingTravel);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void TravelNeedsTheCampingFires()
    {
        var rules = Shipped();

        rules.FeatureFlags.CampingTravel = true;
        rules.FeatureFlags.CampingFires = false;

        Assert.Contains("campingTravel requires campingFires.", ShardRulesConfiguration.Validate(rules));

        rules.FeatureFlags.CampingFires = true;

        Assert.DoesNotContain("campingTravel requires campingFires.", ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void TheFlagIsListedWhenOn()
    {
        var flags = new DeferredFeatureFlags { CampingTravel = true };

        Assert.Contains("CampingTravel", flags.EnabledNames());
        Assert.DoesNotContain("none", flags.EnabledNames());
    }
}
