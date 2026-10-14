using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The "Your screen" page of the Welcome guide: it describes only the bars the shard has switched on.</summary>
public class GuideScreenTopicTests
{
    private static string Page(WelcomeGuide.Context c, string key) =>
        string.Join(" ", WelcomeGuide.Topics(c, new CampTravelRules(), camping: new CampingRules()).Single(t => t.Key == key).Paragraphs);

    private static string Screen(WelcomeGuide.Context c) => Page(c, "screen");

    /// <summary>The Bars and numbers page: health bars, damage and heal numbers, buff icons and item tooltips.</summary>
    private static string Seen(WelcomeGuide.Context c) => Page(c, "seen");

    private static WelcomeGuide.Context On() =>
        new(true, true, true, true, true, MenuBar: true, PotionBar: true, CombatBar: true, WearNotice: true, GuildChat: true, AutoUse: true, DamageNumbers: true, HealNumbers: true, BuffBar: true, ItemTooltips: true);

    [Fact]
    public void ThePageIsInTheStartChapterAfterYourFirstHour() =>
        Assert.Equal(
            ["welcome", "firsthour", "screen", "seen", "locks"],
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
    public void TheBarsAndNumbersPageDescribesWhatTheGameDrawsWhenItIsOn()
    {
        var text = Seen(On() with { CampingFires = true, FaintMemories = true });

        Assert.Contains("Health bars", text);
        Assert.Contains("The buff icons", text);
        Assert.Contains("Criminal Intent, a Backpack Ward, Faint Memories, a Hot Zone and a secure camp", text);
        Assert.Contains("Numbers over heads", text);
        Assert.Contains("floats up over the one hit", text);
        Assert.Contains("green plus sign", text);
        Assert.Contains("Item tooltips", text);
    }

    [Fact]
    public void TheNumbersAndTheBuffIconsAreDescribedOnlyWhileTheirSwitchesAreOn()
    {
        var damageOnly = Seen(On() with { HealNumbers = false, BuffBar = false });

        Assert.Contains("floats up over the one hit", damageOnly);
        Assert.DoesNotContain("green plus sign", damageOnly);
        Assert.DoesNotContain("The buff icons", damageOnly);

        var healOnly = Seen(On() with { DamageNumbers = false });

        Assert.DoesNotContain("floats up over the one hit", healOnly);
        Assert.Contains("green plus sign", healOnly);

        var none = Seen(On() with { DamageNumbers = false, HealNumbers = false });

        Assert.DoesNotContain("Combat-Spells", none);
    }

    [Fact]
    public void TheItemTooltipsParagraphAppearsOnlyWhileTheyAreOnAndSaysMagicNeedsIdentification()
    {
        var on = Seen(On());

        Assert.Contains("Item tooltips", on);
        Assert.Contains("only after Item Identification has been used on it", on);

        var off = Seen(On() with { ItemTooltips = false });

        Assert.DoesNotContain("Item tooltips", off);
        Assert.DoesNotContain("tooltip", off);
    }

    [Fact]
    public void TheBarsAndNumbersPageExplainsThatNoHealthBarMeansFullHealthAndHowAThreatsBarLooks()
    {
        var text = Seen(On());

        Assert.Contains("no bar means full health", text);
        Assert.Contains("a wider bar with an amber fill", text);
    }

    [Fact]
    public void TheBuffIconListLeavesOutWhatTheShardDoesNotHave()
    {
        var text = Seen(On() with { Theft = false, HotZones = false, CampingFires = true });

        Assert.Contains("Criminal Intent and a secure camp", text);
        Assert.DoesNotContain("Backpack Ward", text);
        Assert.DoesNotContain("a Hot Zone", text);
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
    public void ThePagesNameTheShardNotTheOldName()
    {
        Assert.DoesNotContain("Britannia Renaissance", Screen(On()));
        Assert.DoesNotContain("Britannia Renaissance", Seen(On()));
    }
}
