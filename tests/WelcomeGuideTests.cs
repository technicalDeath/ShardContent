using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class WelcomeGuideTests
{
    private static readonly CampTravelRules Rules = new();

    private static WelcomeGuide.Context Context(
        bool theft = true, bool skillBank = true, bool skillClasses = true, bool camp = false, bool warning = false
    ) => new(theft, skillBank, skillClasses, camp, warning);

    private static string[] Keys(WelcomeGuide.Context c) => WelcomeGuide.Topics(c, Rules).Select(t => t.Key).ToArray();

    [Fact]
    public void TheDeployedShardGetsTheCoreTopicsInReadingOrder() =>
        Assert.Equal(["welcome", "fighting", "hotzones", "ward", "loot", "commands"], Keys(Context()));

    [Fact]
    public void CampTravelAddsItsOwnTopicBeforeTheCommands() =>
        Assert.Equal(["welcome", "fighting", "hotzones", "ward", "loot", "camp", "commands"], Keys(Context(camp: true)));

    [Fact]
    public void WithoutTheWardsTheWardTopicsAreLeftOut() =>
        Assert.Equal(["welcome", "fighting", "hotzones", "commands"], Keys(Context(theft: false)));

    [Fact]
    public void TheNavigationStaysShortEnoughToFitTheWindow() =>
        Assert.True(Keys(Context(camp: true, warning: true)).Length <= 8);

    [Fact]
    public void EveryTopicHasATitleAndReadableParagraphs()
    {
        foreach (var topic in WelcomeGuide.Topics(Context(camp: true, warning: true), Rules))
        {
            Assert.False(string.IsNullOrWhiteSpace(topic.Title), topic.Key);
            Assert.NotEmpty(topic.Paragraphs);
            Assert.All(topic.Paragraphs, p => Assert.InRange(p.Length, 10, 600));
        }
    }

    [Fact]
    public void NoTopicSendsPlayersToAStaffCommand()
    {
        var all = string.Join(" ", WelcomeGuide.Topics(Context(camp: true, warning: true), Rules).SelectMany(t => t.Paragraphs));

        Assert.DoesNotContain("[TheftStatus", all);
        Assert.Contains("Double-click your Backpack Ward", all);
    }

    [Fact]
    public void TheHotZoneTopicMentionsTheTravelWarningOnlyWhenItIsOn()
    {
        string Hot(WelcomeGuide.Context c) =>
            string.Join(" ", WelcomeGuide.Topics(c, Rules).Single(t => t.Key == "hotzones").Paragraphs);

        Assert.DoesNotContain("[TravelWarning", Hot(Context()));
        Assert.Contains("[TravelWarning off", Hot(Context(warning: true)));
        Assert.Contains("[TravelWarning on", Hot(Context(camp: true)));
    }

    [Fact]
    public void TheHotZoneTopicSaysWhereTheZonesAreAndWhatTheyDo()
    {
        var text = string.Join(" ", WelcomeGuide.Topics(Context(), Rules).Single(t => t.Key == "hotzones").Paragraphs);

        Assert.Contains("Fire Island", text);
        Assert.Contains("Buccaneer's Den", text);
        Assert.Contains("Hythloth", text);
        Assert.Contains("Knocked Out", text);
    }

    [Fact]
    public void TheCommandListHasOnlyCommandsThatAreOn()
    {
        var core = string.Join("\n", WelcomeGuide.Commands(Context(skillBank: false, skillClasses: false)));

        Assert.Contains("[Welcome", core);
        Assert.Contains("[Intent", core);
        Assert.DoesNotContain("[SkillBank", core);
        Assert.DoesNotContain("[SkillClasses", core);
        Assert.DoesNotContain("[CampTravel", core);
        Assert.DoesNotContain("[TravelWarning", core);

        var all = string.Join("\n", WelcomeGuide.Commands(Context(camp: true)));

        Assert.Contains("[SkillBank", all);
        Assert.Contains("[SkillClasses", all);
        Assert.Contains("[CampTravel", all);
        Assert.Contains("[TravelWarning", all);
    }

    [Fact]
    public void ACommandIsPickedOutInColorAndItsMeaningFollows()
    {
        var line = WelcomeGuide.Highlight("[Intent - Turn Criminal Intent on or off.", true);

        Assert.StartsWith("<BASEFONT COLOR=#8FD3FF>[Intent</BASEFONT> - ", line);
        Assert.Contains("Turn Criminal Intent on or off.", line);
    }

    [Fact]
    public void CommandsInsideAParagraphAreColoredToo()
    {
        var text = WelcomeGuide.Highlight("[Intent turns on Criminal Intent. [IntentStatus shows your state.", false);

        Assert.Contains("<BASEFONT COLOR=#8FD3FF>[Intent</BASEFONT> turns on", text);
        Assert.Contains("<BASEFONT COLOR=#8FD3FF>[IntentStatus</BASEFONT> shows", text);
    }

    [Fact]
    public void ParagraphsAreSeparatedByABlankLine()
    {
        var body = WelcomeGuide.Body(new WelcomeGuide.Topic("x", "X", ["First paragraph here.", "Second paragraph here."]));

        Assert.Contains("here.<BR><BR>Second", body);
    }

    [Fact]
    public void ACommandListIsOneLinePerCommandAndTopicsAreSpacedOut()
    {
        var commands = WelcomeGuide.Body(new WelcomeGuide.Topic("commands", "Commands", ["[A - one.", "[B - two."]));
        var topic = WelcomeGuide.Body(new WelcomeGuide.Topic("ward", "Ward", ["First paragraph here.", "Second paragraph here."]));

        Assert.DoesNotContain("<BR><BR>", commands);
        Assert.Contains("<BR>", commands);
        Assert.Contains("<BR><BR>", topic);
    }

    [Fact]
    public void ShortPagesHaveNoScrollbarAndLongOnesDo()
    {
        var topics = WelcomeGuide.Topics(Context(camp: true, warning: true), Rules).ToDictionary(t => t.Key);

        Assert.False(WelcomeGuide.NeedsScroll(topics["welcome"]));
        Assert.False(WelcomeGuide.NeedsScroll(topics["loot"]));
        Assert.False(WelcomeGuide.NeedsScroll(topics["camp"]));
        Assert.False(WelcomeGuide.NeedsScroll(topics["commands"]));
        Assert.True(WelcomeGuide.NeedsScroll(topics["fighting"]));
        Assert.True(WelcomeGuide.NeedsScroll(new WelcomeGuide.Topic("x", "X", [new string('a', 2000)])));
    }

    [Fact]
    public void TheLineEstimateCountsWrappedLinesAndTheBlankLinesBetweenParagraphs()
    {
        var two = new WelcomeGuide.Topic("x", "X", [new string('a', 58), new string('a', 59)]);

        Assert.Equal(1 + 2 + 1, WelcomeGuide.EstimateLines(two));
        Assert.Equal(1 + 2, WelcomeGuide.EstimateLines(new WelcomeGuide.Topic("commands", "C", [new string('a', 58), new string('a', 59)])));
    }

    [Fact]
    public void WardTextIsTheSameAsTheLegacyRulesSoNothingDrifts()
    {
        var legacy = StarterOnboarding.DescribeRules().ToList();

        Assert.Equal(5, legacy.Count);
        Assert.Contains(StarterOnboarding.WardWhat, legacy);
        Assert.Contains(StarterOnboarding.WardAlert, legacy);
        Assert.Contains(StarterOnboarding.LootProtection, legacy);
        Assert.DoesNotContain(legacy, line => line.Contains("[TheftStatus"));
    }

    [Fact]
    public void TheCreationPromptPointsBackToTheGuide() =>
        Assert.Contains("[Welcome", StarterOnboarding.CreationPrompt);
}
