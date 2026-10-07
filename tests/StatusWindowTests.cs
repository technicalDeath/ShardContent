using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The logic behind [SkillClasses, [SkillBank, [Mastery and [IntentStatus: what each window lists and says, in what order, with which
/// button ids. The drawing itself is checked in the real client (docs/Status-Windows.md).
/// </summary>
public class StatusWindowTests
{
    // ---- the shared style

    [Theory]
    [InlineData(0.0, 40, 0)]
    [InlineData(-1.0, 40, 0)]
    [InlineData(1.0, 40, 40)]
    [InlineData(2.0, 40, 40)]
    [InlineData(0.5, 40, 20)]
    [InlineData(0.001, 40, 1)]
    [InlineData(0.999, 40, 39)]
    public void ABarShowsSomethingOnceStartedAndIsNeverFullBeforeTheEnd(double fraction, int segments, int filled) =>
        Assert.Equal(filled, GumpStyle.FilledSegments(fraction, segments));

    [Theory]
    [InlineData(0, "0.0")]
    [InlineData(5, "0.5")]
    [InlineData(123, "12.3")]
    [InlineData(3000, "300.0")]
    public void PointsAreShownInTenths(int tenths, string text) => Assert.Equal(text, GumpStyle.Points(tenths));

    // ---- [SkillClasses

    private static SkillGainRules Rules() => SkillGainCurveTests.ValidRules();

    private static MasteryRules MasteryNumbers() => new();

    private static IReadOnlyList<SkillClassesGump.SkillClassView> Views() =>
        SkillClassesGump.BuildViews(Rules(), MasteryNumbers(), name => name);

    [Fact]
    public void TheClassesAreListedQuickestFirstAndOnlyWhenTheyHaveSkills()
    {
        var views = Views();

        Assert.Equal(["easy", "standard", "hard"], views.Select(v => v.Key));
        Assert.Equal(["Easy skills", "Standard skills", "Hard skills"], views.Select(v => v.Title));
        Assert.Equal([19, 26, 4], views.Select(v => v.Skills.Count));
    }

    [Fact]
    public void TheSkillsOfAClassAreAlphabeticalAndAnUnknownSkillIsSkipped()
    {
        var views = SkillClassesGump.BuildViews(Rules(), MasteryNumbers(), name => name == "Anatomy" || name == "Alchemy" ? name : null);

        Assert.Equal(["Anatomy"], views.Single(v => v.Key == "easy").Skills);
        Assert.Equal(["Alchemy"], views.Single(v => v.Key == "hard").Skills);
        Assert.DoesNotContain(views, v => v.Key == "standard");

        var easy = Views().Single(v => v.Key == "easy").Skills;
        Assert.Equal(easy.OrderBy(n => n, StringComparer.OrdinalIgnoreCase), easy);
    }

    [Theory]
    [InlineData(1.0, "stock speed")]
    [InlineData(1.5, "1.5x stock speed")]
    [InlineData(0.75, "0.75x stock speed")]
    [InlineData(2.0, "2x stock speed")]
    public void ASpeedIsStockSpeedOrAMultipleOfIt(double multiplier, string text) =>
        Assert.Equal(text, SkillGainCurveService.SpeedText(multiplier));

    [Fact]
    public void TheSpeedsRunFromSkillTenToTheMasteryThreshold()
    {
        var views = Views();

        Assert.Equal(["Skill 10 to 90: 1.5x stock speed"], views.Single(v => v.Key == "easy").Speeds);
        Assert.Equal(["Skill 10 to 70: 1.5x stock speed", "Skill 70 to 90: stock speed"], views.Single(v => v.Key == "standard").Speeds);
        Assert.Equal(
            ["Skill 10 to 70: 1.5x stock speed", "Skill 70 to 80: stock speed", "Skill 80 to 90: 0.75x stock speed"],
            views.Single(v => v.Key == "hard").Speeds
        );
        Assert.Equal("1.5x stock speed from 10 to 70, stock speed from 70 to 90", views.Single(v => v.Key == "standard").Summary);
    }

    [Fact]
    public void TheMasteryLineQuotesTheClassAllowance()
    {
        var views = Views();

        Assert.Contains("an allowance of 2.0 each cycle, about 20 successful uses", views.Single(v => v.Key == "easy").Mastery);
        Assert.Contains("an allowance of 1.0 each cycle, about 10 successful uses", views.Single(v => v.Key == "standard").Mastery);
        Assert.Contains("an allowance of 0.6 each cycle, about 6 successful uses", views.Single(v => v.Key == "hard").Mastery);
    }

    [Fact]
    public void TheWindowHasAnOverviewThenAPagePerClass()
    {
        var topics = SkillClassesGump.BuildTopics(Views());

        Assert.Equal(["overview", "easy", "standard", "hard"], topics.Select(t => t.Key));

        var overview = string.Join(" ", topics[0].Paragraphs);
        Assert.Contains("[Mastery shows yours.", overview);
        Assert.Contains("Easy skills (19)", overview);
        Assert.Contains("Standard skills (26)", overview);
        Assert.Contains("Hard skills (4)", overview);

        var standard = string.Join(" ", topics[2].Paragraphs);
        Assert.Contains("# Training speed", topics[2].Paragraphs);
        Assert.Contains("Skill 10 to 70: 1.5x stock speed<BR>Skill 70 to 90: stock speed", standard);
        Assert.Contains("# The 26 skills", topics[2].Paragraphs);
    }

    // ---- [SkillBank

    [Theory]
    [InlineData(0, 1)]
    [InlineData(1, 1)]
    [InlineData(6, 1)]
    [InlineData(7, 2)]
    [InlineData(13, 3)]
    public void TheSkillBankListsSixSkillsToAPage(int rows, int pages) => Assert.Equal(pages, SkillBankGump.PageCount(rows));

    [Fact]
    public void ARetentionButtonNamesTheSkillAndTheSetting()
    {
        Assert.Equal((17, BankRetention.Locked), SkillBankGump.ParseRetentionButton(1017));
        Assert.Equal((17, BankRetention.Down), SkillBankGump.ParseRetentionButton(2017));
        Assert.Equal((0, BankRetention.Locked), SkillBankGump.ParseRetentionButton(1000));
        Assert.Null(SkillBankGump.ParseRetentionButton(0));
        Assert.Null(SkillBankGump.ParseRetentionButton(1));
        Assert.Null(SkillBankGump.ParseRetentionButton(3));
        Assert.Null(SkillBankGump.ParseRetentionButton(3000));
    }

    [Fact]
    public void ChangingASettingIsConfirmedInPlainWords()
    {
        Assert.Equal("Anatomy is now Locked: its banked points are safe.", SkillBankGump.DescribeChange("Anatomy", BankRetention.Locked));
        Assert.Equal("Hiding is now Down: its banked points can be replaced when the bank is full.", SkillBankGump.DescribeChange("Hiding", BankRetention.Down));
    }

    // ---- [Mastery

    [Theory]
    [InlineData("easy", "Easy")]
    [InlineData("standard", "Standard")]
    [InlineData("hard", "Hard")]
    [InlineData("veryHard", "Very hard")]
    public void AClassIsNamedForPlayers(string key, string label) => Assert.Equal(label, MasteryProgression.ClassLabel(key));

    [Theory]
    [InlineData(1, 1)]
    [InlineData(6, 1)]
    [InlineData(7, 2)]
    public void MasteryListsSixSkillsToAPage(int rows, int pages) => Assert.Equal(pages, MasteryGump.PageCount(rows));

    private static MasteryProgression.MasteryView View(MasteryProgression.MasteryPhase phase, TimeSpan next = default) =>
        new(null, phase, next, 24, 3, []);

    [Fact]
    public void TheTopLineSaysWhenTheNextCycleBeginsOrWhyThereIsNone()
    {
        Assert.Contains(
            "Your next cycle begins in",
            MasteryGump.DescribeCycle(View(MasteryProgression.MasteryPhase.Active, TimeSpan.FromHours(5.5)))
        );
        Assert.Contains("5h 30m", MasteryGump.DescribeCycle(View(MasteryProgression.MasteryPhase.Active, TimeSpan.FromHours(5.5))));
        Assert.Equal(
            "Your first cycle begins with your next successful use of a skill at 90.0 or above.",
            MasteryGump.DescribeCycle(View(MasteryProgression.MasteryPhase.Waiting))
        );
        Assert.Equal(
            "No skill is in Mastery yet. Mastery begins at 90.0.",
            MasteryGump.DescribeCycle(View(MasteryProgression.MasteryPhase.NoSkills))
        );
    }

    // ---- [IntentStatus

    [Fact]
    public void APlayerIsToldTheirOwnIntentAndWhatToDoAboutIt()
    {
        var off = string.Join(" ", PvpIntentService.DescribeForPlayer(true, true, false, false));
        var on = string.Join(" ", PvpIntentService.DescribeForPlayer(true, true, true, false));

        Assert.Contains("Criminal Intent is off: other players cannot attack you unless you break the law or are already fighting them, except in a Hot Zone.", off);
        Assert.Contains("Type [Intent to turn it on.", off);
        Assert.Contains("Criminal Intent is on: you appear grey and other players may attack you. Killing you is not murder.", on);
        Assert.Contains("Type [Intent to turn it off.", on);
        Assert.Contains(PvpIntentService.NotACriminalNote, off);
        Assert.Contains(PvpIntentService.NotACriminalNote, on);
    }

    [Fact]
    public void TheNotACriminalNoteSaysGuardsWillNotAttackUntilACriminalActIsCommitted()
    {
        Assert.Equal(
            "Criminal Intent does not make you a criminal: guards will not attack you, and you can still use Recall and gates, until you commit a criminal act such as stealing.",
            PvpIntentService.NotACriminalNote
        );
    }

    [Fact]
    public void ACriminalIsToldTheyCannotChangeIt()
    {
        var text = string.Join(" ", PvpIntentService.DescribeForPlayer(true, true, false, true));

        Assert.Contains("You cannot change it while you are a criminal or a murderer.", text);
        Assert.DoesNotContain("Type [Intent", text);
        Assert.DoesNotContain("does not make you a criminal", text);
    }

    [Fact]
    public void WithoutTheSafeWorldRulesThereIsNothingToTell()
    {
        Assert.Equal(["Criminal Intent is not used on this shard."], PvpIntentService.DescribeForPlayer(false, true, false, false));
    }

    [Fact]
    public void WithoutHotZonesTheOffLineHasNoException()
    {
        var text = string.Join(" ", PvpIntentService.DescribeForPlayer(true, false, false, false));

        Assert.Contains("or are already fighting them.", text);
        Assert.DoesNotContain("Hot Zone", text);
    }

    [Fact]
    public void NoLineOfTheStatusCarriesDeveloperDetail()
    {
        foreach (var intent in new[] { true, false })
        {
            foreach (var criminal in new[] { true, false })
            {
                var text = string.Join(" ", PvpIntentService.DescribeForPlayer(true, true, intent, criminal));

                Assert.DoesNotContain("handler", text, StringComparison.OrdinalIgnoreCase);
                Assert.DoesNotContain("policy", text, StringComparison.OrdinalIgnoreCase);
                Assert.DoesNotContain("Nearby notoriety", text);
                Assert.DoesNotContain("BritanniaRenaissance", text);
                Assert.DoesNotContain("True", text);
                Assert.DoesNotContain("False", text);
            }
        }
    }
}
