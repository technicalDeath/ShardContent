using System.Text.RegularExpressions;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The shard's window style (Gump-Style-Guide.md, approved 2026-10-07) as tests. They read the window source files and fail when a window
/// goes back to what the client cannot draw well or what the guide retired: bold, italics, `fontStyle`, half-transparent panels, the small
/// curved arrow and the stone plates, text colours outside <see cref="GumpStyle"/>, and a window taller or wider than its class.
/// </summary>
public sealed class StyleGuideTests
{
    private static readonly string SourceFolder = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "src", "BritanniaRenaissance.Content");

    /// <summary>The files that build a window: any source file that draws with a gump builder.</summary>
    private static IEnumerable<(string Name, string Text)> WindowFiles() =>
        Directory.EnumerateFiles(SourceFolder, "*.cs")
            .Select(static path => (Name: Path.GetFileName(path), Text: File.ReadAllText(path)))
            .Where(static f => f.Text.Contains("DynamicGumpBuilder", StringComparison.Ordinal));

    private static string WithoutComments(string text) => Regex.Replace(text, @"^\s*///?.*$", string.Empty, RegexOptions.Multiline);

    [Fact]
    public void ThereAreWindowFilesToCheck() => Assert.True(WindowFiles().Count() >= 8);

    [Fact]
    public void NoWindowUsesFontStyleOrItalicsOrUnderline()
    {
        foreach (var (name, text) in WindowFiles())
        {
            var code = WithoutComments(text);

            Assert.False(Regex.IsMatch(code, @"fontStyle\s*:"), $"{name} uses fontStyle, which the client ignores");
            Assert.False(Regex.IsMatch(code, @"<\s*[IiUu]\s*>"), $"{name} uses italics or underline");
        }
    }

    [Fact]
    public void BoldIsOnlyInTheProgressBar()
    {
        foreach (var (name, text) in WindowFiles())
        {
            var code = WithoutComments(text);
            var bold = Regex.IsMatch(code, @"<\s*[Bb]\s*>");

            Assert.True(!bold || name == "GumpStyle.cs", $"{name} uses bold, which the client draws as solid blocks");
        }
    }

    [Fact]
    public void NoWindowUsesTheAlphaRegionThatFadesTheWholePanel()
    {
        foreach (var (name, text) in WindowFiles())
        {
            Assert.DoesNotContain("AddAlphaRegion", WithoutComments(text));
        }
    }

    [Fact]
    public void NoWindowUsesTheRetiredButtonArt()
    {
        foreach (var (name, text) in WindowFiles())
        {
            var code = WithoutComments(text);

            Assert.False(Regex.IsMatch(code, @"\b400[57]\b"), $"{name} draws the retired arrow button (4005/4007)");
            Assert.False(Regex.IsMatch(code, @"\b244[34]\b"), $"{name} draws the retired stone plates (2443/2444)");
            Assert.False(Regex.IsMatch(code, @"\b620[0-9]{2}\b") && name != "GumpStyle.cs", $"{name} names shard button art itself: use GumpStyle");
            Assert.DoesNotContain("ArrowNormal", code);
            Assert.DoesNotContain("ArrowPressed", code);
        }
    }

    [Fact]
    public void ColoursComeFromGumpStyleAndNoWindowNamesOne()
    {
        // The only #RRGGBB in a window file is in GumpStyle itself (and the chapter tabs' ink, which sits on stone art, not the dark panel).
        var allowed = new[] { "#202020", "#000000", "#101010" };

        foreach (var (name, text) in WindowFiles())
        {
            if (name == "GumpStyle.cs")
            {
                continue;
            }

            foreach (Match m in Regex.Matches(WithoutComments(text), "\"#[0-9A-Fa-f]{6}\""))
            {
                Assert.True(allowed.Contains(m.Value.Trim('"')), $"{name} names the colour {m.Value}: use a GumpStyle colour");
            }
        }
    }

    [Fact]
    public void TheWarningColourIsGoneAndTheRulesColoursAreDistinct()
    {
        var colours = new[] { GumpStyle.Gold, GumpStyle.Text, GumpStyle.Muted, GumpStyle.Dim, GumpStyle.Command, GumpStyle.Good, GumpStyle.Danger, GumpStyle.Chosen };

        Assert.Equal(colours.Length, colours.Distinct().Count());
        Assert.DoesNotContain("#FFB347", File.ReadAllText(Path.Combine(SourceFolder, "GumpStyle.cs")));
    }

    [Fact]
    public void NothingIsDimmerThanTheFootnoteColourOnThePanel()
    {
        foreach (var colour in new[] { GumpStyle.Gold, GumpStyle.Text, GumpStyle.Muted, GumpStyle.Dim, GumpStyle.Command, GumpStyle.Good, GumpStyle.Danger, GumpStyle.Chosen })
        {
            var channels = new[] { Convert.ToInt32(colour[1..3], 16), Convert.ToInt32(colour[3..5], 16), Convert.ToInt32(colour[5..7], 16) };

            Assert.True(channels.Max() >= 0x99, $"{colour} is too dim for the dark panel");
        }
    }

    // ---- the window classes

    [Fact]
    public void TheWindowClassesNeverExceedTheLargeWindow()
    {
        Assert.Equal(640, GumpStyle.Width);
        Assert.Equal(500, GumpStyle.Height);
        Assert.True(GumpStyle.MediumWidth < GumpStyle.Width);
        Assert.True(GumpStyle.DialogWidth <= GumpStyle.MediumWidth);
        Assert.True(CampTravelService.ListHeight(8) <= GumpStyle.Height, "the camp list at its limit of eight camps");
        Assert.True(CampTravelService.ConfirmHeight(true) <= GumpStyle.Height);
        Assert.True(StatusWindow.HeightFor([new string('x', 20000)], 3) <= GumpStyle.Height);
    }

    // ---- the buttons

    [Theory]
    [InlineData("Close")]
    [InlineData("Back")]
    [InlineData("Next")]
    [InlineData("Next topic")]
    [InlineData("How it works")]
    [InlineData("Skill speeds")]
    [InlineData("Open Mastery")]
    [InlineData("Select")]
    [InlineData("Discard")]
    [InlineData("Discard points")]
    [InlineData("Turn Criminal Intent on")]
    [InlineData("Turn Criminal Intent off")]
    [InlineData("Turn the warning on")]
    [InlineData("Turn the warning off")]
    public void EveryButtonLabelFitsAnOvalOfTheSizeItGets(string label)
    {
        var width = GumpStyle.OvalWidth(label);

        Assert.Contains(width, GumpStyle.OvalWidths);
        Assert.True(Math.Ceiling(label.Length * 6.3) + 20 <= width || width == GumpStyle.OvalWidths[^1], label);
    }

    [Fact]
    public void ThePageWordsTheOvalsAndTheWidthsAreTheOnesTheGuideSays()
    {
        Assert.Equal(56, GumpStyle.OvalWidth("Close"));
        Assert.Equal(56, GumpStyle.OvalWidth("Back"));
        Assert.Equal(56, GumpStyle.OvalWidth("Next"));
        Assert.Equal(88, GumpStyle.OvalWidth("Discard"));
        Assert.Equal(128, GumpStyle.OvalWidth("How it works"));
        Assert.Equal(176, GumpStyle.OvalWidth("Turn Criminal Intent on"));
    }

    [Fact]
    public void EveryGuideTopicTitleFitsTheOvalOfTheList()
    {
        var everything = new WelcomeGuide.Context(
            Theft: true, SkillBank: true, SkillClasses: true, CampTravel: true, TravelWarning: true, SafeWorld: true, KnockedOut: true,
            HotZones: true, CampingKit: true, CampingFires: true, FaintMemories: true, HarvestRepeat: true, ActionRepeat: true,
            PetRestrictions: true, StarterPackage: true, StarterGold: true
        );
        var topics = WelcomeGuide.Topics(everything, new CampTravelRules(), camping: new CampingRules());

        Assert.NotEmpty(topics);
        Assert.All(topics, topic => Assert.True(GuideWindow.TopicTitleFits(topic.Title), topic.Title));

        foreach (var title in new[] { "Overview", "Easy skills", "Standard skills", "Hard skills" })
        {
            Assert.True(GuideWindow.TopicTitleFits(title), title);
        }
    }

    [Fact]
    public void TheBannerAndTheStatusColoursPairAGemWithAWord()
    {
        Assert.Equal("Done:", GumpStyle.BannerWord(BannerKind.Done));
        Assert.Equal("Danger:", GumpStyle.BannerWord(BannerKind.Danger));
        Assert.Equal("Note:", GumpStyle.BannerWord(BannerKind.Note));
        Assert.Equal(BannerKind.Done, GumpStyle.KindOf(GumpStyle.Good));
        Assert.Equal(BannerKind.Danger, GumpStyle.KindOf(GumpStyle.Danger));
        Assert.Equal(BannerKind.Note, GumpStyle.KindOf(GumpStyle.Muted));
        Assert.Equal(BannerKind.Note, GumpStyle.KindOf(GumpStyle.Command));
    }

    [Fact]
    public void TheTextEstimatorAgreesWithTheGuidesRuleOfAboutSixPointNinePixelsALetter()
    {
        Assert.Equal(58, GumpStyle.CharsPerLine(400));
        Assert.Equal(1, GumpStyle.LinesFor("short", 400));
        Assert.Equal(2, GumpStyle.LinesFor(new string('x', 59), 400));
    }
}
