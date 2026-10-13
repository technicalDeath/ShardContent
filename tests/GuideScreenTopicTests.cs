using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The "Your screen" page of the Welcome guide: it describes only the bars the shard has switched on.</summary>
public class GuideScreenTopicTests
{
    private static string Screen(WelcomeGuide.Context c) =>
        string.Join(" ", WelcomeGuide.Topics(c, new CampTravelRules(), camping: new CampingRules()).Single(t => t.Key == "screen").Paragraphs);

    private static WelcomeGuide.Context On() =>
        new(true, true, true, true, true, MenuBar: true, PotionBar: true, CombatBar: true, WearNotice: true, GuildChat: true, AutoUse: true);

    [Fact]
    public void ThePageIsInTheStartChapterAfterYourFirstHour() =>
        Assert.Equal(
            ["welcome", "firsthour", "screen", "locks"],
            WelcomeGuide.Chapters(WelcomeGuide.Topics(On(), new CampTravelRules(), camping: new CampingRules())).First(c => c.Key == "start").TopicKeys
        );

    [Fact]
    public void EveryBarIsDescribedWhenItIsOn()
    {
        var text = Screen(On());

        Assert.Contains("The top bar", text);
        Assert.Contains("The potion bar", text);
        Assert.Contains("The combat bar", text);
        Assert.Contains("Item shortcuts", text);
        Assert.Contains("If you die", text);
        Assert.Contains("Auto options", text);
        Assert.Contains("The spell bar", text);
        Assert.Contains("one circle of spells at a time", text);
        Assert.Contains("Camp is camp travel", text);
        Assert.Contains("Guild chat", text);
        Assert.Contains("how worn it is", text);
        Assert.Contains("a quarter of its durability", text);
    }

    [Fact]
    public void NothingIsDescribedThatIsOff()
    {
        var text = Screen(new WelcomeGuide.Context(true, true, true, false, false));

        Assert.DoesNotContain("The top bar", text);
        Assert.DoesNotContain("The potion bar", text);
        Assert.DoesNotContain("how worn it is", text);
        Assert.DoesNotContain("Auto options", text);
        Assert.DoesNotContain("a quarter of its durability", text);
        Assert.DoesNotContain("Camp is camp travel", text);
        Assert.DoesNotContain("Guild chat", text);
        Assert.Contains("Item shortcuts", text);   // the item shortcut bar is a client default, not a flag
    }

    [Fact]
    public void ThePageNamesTheShardNotTheOldName() => Assert.DoesNotContain("Britannia Renaissance", Screen(On()));
}
