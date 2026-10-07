using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>What the Criminal Intent, Hot Zone travel warning and Backpack Ward windows say, and how tall a window is for its text.</summary>
public class StatusWindowsViewTests
{
    // ---- Criminal Intent

    [Fact]
    public void IntentOffSaysSoAndOffersToTurnItOn()
    {
        var view = StatusWindows.DescribeIntent(true, true, false, false);

        Assert.Equal("Criminal Intent is OFF", view.Headline);
        Assert.Equal(GumpStyle.Good, view.HeadlineColor);
        Assert.Equal("Turn Criminal Intent on", view.ButtonLabel);
        Assert.Equal(
            [
                "Other players cannot attack you unless you break the law or are already fighting them, except in a Hot Zone.",
                PvpIntentService.NotACriminalNote
            ],
            view.Paragraphs
        );
    }

    [Fact]
    public void IntentOnWarnsThatOthersMayAttackAndOffersToTurnItOff()
    {
        var view = StatusWindows.DescribeIntent(true, true, true, false);

        Assert.Equal("Criminal Intent is ON", view.Headline);
        Assert.Equal(GumpStyle.Warning, view.HeadlineColor);
        Assert.Equal("Turn Criminal Intent off", view.ButtonLabel);
        Assert.Equal(
            ["You appear grey and other players may attack you. Killing you is not murder.", PvpIntentService.NotACriminalNote],
            view.Paragraphs
        );
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void IntentIsNeverTheSameAsBeingACriminalAndTheWindowSaysSo(bool intentOn)
    {
        var view = StatusWindows.DescribeIntent(true, true, intentOn, false);
        var text = string.Join(" ", view.Paragraphs);

        Assert.Contains("does not make you a criminal", text);
        Assert.Contains("guards will not attack you", text);
        Assert.Contains("until you commit a criminal act", text);
    }

    [Fact]
    public void ACriminalOrMurdererCannotChangeItSoThereIsNoButton()
    {
        var view = StatusWindows.DescribeIntent(true, true, false, true);

        Assert.Null(view.ButtonLabel);
        Assert.Contains("You cannot change it while you are a criminal or a murderer.", view.Paragraphs);
        Assert.DoesNotContain(PvpIntentService.NotACriminalNote, view.Paragraphs);
    }

    [Fact]
    public void WithoutTheSafeWorldRulesThereIsNothingToSwitch()
    {
        var view = StatusWindows.DescribeIntent(false, true, false, false);

        Assert.Equal("Not used here", view.Headline);
        Assert.Null(view.ButtonLabel);
        Assert.Equal(["Criminal Intent is not used on this shard."], view.Paragraphs);
    }

    // ---- the travel warning

    [Fact]
    public void TheTravelWarningWindowSaysWhichWayItIsSetAndOffersTheOtherWay()
    {
        var on = StatusWindows.DescribeTravelWarning(true, false);
        var off = StatusWindows.DescribeTravelWarning(true, true);

        Assert.Equal("The warning is ON", on.Headline);
        Assert.Equal("Turn the warning off", on.ButtonLabel);
        Assert.Contains("Only blue players are asked.", on.Paragraphs[0]);
        Assert.Contains("Do not show me this warning again when traveling", on.Paragraphs[1]);

        Assert.Equal("The warning is OFF", off.Headline);
        Assert.Equal(GumpStyle.Warning, off.HeadlineColor);
        Assert.Equal("Turn the warning on", off.ButtonLabel);
        Assert.Contains("You will not be asked.", off.Paragraphs[1]);
    }

    [Fact]
    public void TheTravelWarningWindowOffersNothingWhenNeitherFeatureIsOn()
    {
        var view = StatusWindows.DescribeTravelWarning(false, false);

        Assert.Null(view.ButtonLabel);
        Assert.Equal(["The Hot Zone travel warning is not in use on this shard right now."], view.Paragraphs);
    }

    // ---- a Backpack Ward

    [Fact]
    public void TheWardHeadlineIsItsPhaseAndTheStatusPrefixIsNotRepeatedInTheText()
    {
        var lines = WardDescription.Lines(true, false, WardPhase.Primed, true, true, false, TimeSpan.FromMinutes(23));
        var view = StatusWindows.DescribeWard(true, WardPhase.Primed, lines);

        Assert.Equal("Primed", view.Headline);
        Assert.Equal(GumpStyle.Gold, view.HeadlineColor);
        Assert.DoesNotContain(view.Paragraphs, p => p.StartsWith("Status:", StringComparison.Ordinal));
        Assert.Contains(view.Paragraphs, p => p.StartsWith("It is tracking thieves who steal from you", StringComparison.Ordinal));
        Assert.Contains("23 more quiet minutes", string.Join(" ", view.Paragraphs));
        Assert.Null(view.ButtonLabel);
    }

    [Theory]
    [InlineData(WardPhase.Unprimed, GumpStyle.Muted)]
    [InlineData(WardPhase.Primed, GumpStyle.Gold)]
    [InlineData(WardPhase.Activated, GumpStyle.Good)]
    public void EachWardPhaseHasItsOwnColor(WardPhase phase, string color) =>
        Assert.Equal(color, StatusWindows.DescribeWard(true, phase, ["A Ward."]).HeadlineColor);

    [Fact]
    public void AWardOnAShardWithTheftProtectionOffSaysItIsSwitchedOff()
    {
        var lines = WardDescription.Lines(false, true, WardPhase.Unprimed, true, true, false, TimeSpan.Zero);
        var view = StatusWindows.DescribeWard(false, WardPhase.Unprimed, lines);

        Assert.Equal("Switched off", view.Headline);
        Assert.Contains("wards do nothing", string.Join(" ", view.Paragraphs));
    }

    // ---- the window's height

    [Fact]
    public void TheWindowIsTallEnoughForItsTextAndNeverTallerThanTheOthers()
    {
        var short1 = StatusWindow.HeightFor(["One line."], 0);
        var long1 = StatusWindow.HeightFor([new string('x', 400), new string('y', 400)], 1);
        var huge = StatusWindow.HeightFor([new string('z', 5000)], 2);

        Assert.Equal(260, short1);
        Assert.True(long1 > short1);
        Assert.Equal(GumpStyle.Height, huge);
    }

    [Fact]
    public void TagsDoNotCountTowardTheLengthOfAParagraph() =>
        Assert.Equal(StatusWindow.EstimateLines(["abc def"]), StatusWindow.EstimateLines(["<BASEFONT COLOR=#8FD3FF>abc</BASEFONT> def"]));
}
