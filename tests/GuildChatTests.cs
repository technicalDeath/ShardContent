using System.Text.Json;
using Xunit;
using static BritanniaRenaissance.Content.GuildChatService;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// Guild chat (docs/Guild-Chat-Plan.md): the rule that decides what happens to a Guild or Alliance line, the words the speaker reads, the
/// colour, the guide's command line and the flag. Routing to the guild's members, the staff monitoring and the log are checked live.
/// </summary>
public class GuildChatTests
{
    private static readonly Facts Ready = new(true, false, true, false, true, "hello guild");

    private static ShardRules Shipped()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- the rule

    [Fact]
    public void AGuildMemberWhoCanSpeakSendsToTheGuild() => Assert.Equal(Outcome.Send, Decide(Ready));

    [Fact]
    public void WithTheFlagOffTheStockPathRunsForEveryKindOfLine()
    {
        var off = Ready with { Enabled = false };

        Assert.Equal(Outcome.Stock, Decide(off));
        Assert.Equal(Outcome.Stock, Decide(off with { IsAlliance = true }));
        Assert.Equal(Outcome.Stock, Decide(off with { HasGuild = false }));
        Assert.Equal(Outcome.Stock, Decide(off with { Squelched = true, CanAct = false, Text = "" }));
    }

    [Fact]
    public void ALineWithNoGuildIsRefusedAndNeverSaidAloud() => Assert.Equal(Outcome.NotInGuild, Decide(Ready with { HasGuild = false }));

    [Fact]
    public void AnAllianceLineIsAnsweredNotAvailableWhateverElseIsTrue()
    {
        Assert.Equal(Outcome.AllianceUnavailable, Decide(Ready with { IsAlliance = true }));
        Assert.Equal(Outcome.AllianceUnavailable, Decide(Ready with { IsAlliance = true, HasGuild = false }));
        Assert.Equal(Outcome.AllianceUnavailable, Decide(Ready with { IsAlliance = true, Squelched = true }));
    }

    [Fact]
    public void AMutedSpeakerCannotUseIt() => Assert.Equal(Outcome.Muted, Decide(Ready with { Squelched = true }));

    [Fact]
    public void AKnockedOutSpeakerCannotUseIt() => Assert.Equal(Outcome.KnockedOut, Decide(Ready with { CanAct = false }));

    [Fact]
    public void MutedIsToldBeforeKnockedOutAndBothBeforeNoGuild()
    {
        Assert.Equal(Outcome.Muted, Decide(Ready with { Squelched = true, CanAct = false }));
        Assert.Equal(Outcome.Muted, Decide(Ready with { Squelched = true, HasGuild = false }));
        Assert.Equal(Outcome.KnockedOut, Decide(Ready with { CanAct = false, HasGuild = false }));
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    public void AnEmptyLineSendsNothingAndSaysNothing(string? text)
    {
        var outcome = Decide(Ready with { Text = text });

        Assert.Equal(Outcome.Empty, outcome);
        Assert.Null(RefusalText(outcome));
    }

    [Fact]
    public void AnEmptyLineFromSomeoneWithNoGuildIsStillEmptyNotARefusal() =>
        Assert.Equal(Outcome.Empty, Decide(Ready with { HasGuild = false, Text = " " }));

    [Fact]
    public void ADeadOrHiddenSpeakerIsNotAnInputToTheRule()
    {
        // The rule has no fact for either: a ghost may use guild chat and a hidden speaker is not revealed by it (it never reaches the speech path).
        Assert.DoesNotContain(typeof(Facts).GetProperties(), p => p.Name.Contains("Dead") || p.Name.Contains("Alive") || p.Name.Contains("Hidden"));
        Assert.Equal(Outcome.Send, Decide(Ready));
    }

    // ---- the words

    [Fact]
    public void EveryRefusalHasItsOwnWords()
    {
        Assert.Equal("You are not in a guild.", RefusalText(Outcome.NotInGuild));
        Assert.Equal("You can not say anything, you have been squelched.", RefusalText(Outcome.Muted));
        Assert.Equal("You cannot speak while you are Knocked Out.", RefusalText(Outcome.KnockedOut));
        Assert.Equal("Alliance chat is not available here.", RefusalText(Outcome.AllianceUnavailable));
        Assert.Null(RefusalText(Outcome.Send));
        Assert.Null(RefusalText(Outcome.Stock));
        Assert.Null(RefusalText(Outcome.Empty));
    }

    [Fact]
    public void TheUsageLineNamesBothWaysAndSaysItIsLogged()
    {
        Assert.Contains("[g", UsageText);
        Assert.Contains("\\", UsageText);
        Assert.Contains(LoggedNotice, UsageText);
        Assert.Equal("Guild chat is logged for moderation.", LoggedNotice);
    }

    [Fact]
    public void TheStaffMonitorShowsTheLineTheWayTheEnginesOwnChatDoes() => Assert.Equal("[Guild]: need a res at the bridge", StaffText("need a res at the bridge"));

    // ---- colour and the log line

    [Theory]
    [InlineData(0x44, 0x99, 0x44)]
    [InlineData(0, 0x99, 0x99)]
    [InlineData(0, 0, 0x3B2)]
    [InlineData(0x1, 0, 0x1)]
    public void TheColourIsTheClientsThenTheRememberedThenTheJournals(int requested, int remembered, int expected) =>
        Assert.Equal(expected, HueFor(requested, remembered));

    [Fact]
    public void ALogEntryIsOneLine()
    {
        Assert.Equal("one two  three", OneLine("one\ntwo\r\nthree"));
        Assert.DoesNotContain('\n', OneLine("one\ntwo\r\nthree"));
        Assert.DoesNotContain('\r', OneLine("one\ntwo\r\nthree"));
        Assert.Equal("plain text", OneLine("plain text"));
    }

    // ---- the guide

    [Fact]
    public void TheCommandsPageListsTheCommandOnlyWhenGuildChatIsOn()
    {
        var on = string.Join("\n", WelcomeGuide.Commands(new WelcomeGuide.Context(Theft: false, SkillBank: false, SkillClasses: false, CampTravel: false, TravelWarning: false, GuildChat: true)));
        var off = string.Join("\n", WelcomeGuide.Commands(new WelcomeGuide.Context(Theft: false, SkillBank: false, SkillClasses: false, CampTravel: false, TravelWarning: false)));

        Assert.Contains("[g - ", on);
        Assert.Contains("\\ key", on);
        Assert.Contains(LoggedNotice, on);
        Assert.DoesNotContain("<", on);
        Assert.DoesNotContain("[g", off);
    }

    [Fact]
    public void TheCommandLineIsPickedOutInColourAndItsMeaningFollows()
    {
        var line = WelcomeGuide.Commands(new WelcomeGuide.Context(Theft: false, SkillBank: false, SkillClasses: false, CampTravel: false, TravelWarning: false, GuildChat: true))
            .Single(l => l.StartsWith("[g ", StringComparison.Ordinal));

        Assert.StartsWith("<BASEFONT COLOR=#8FD3FF>[g</BASEFONT> - ", WelcomeGuide.Highlight(line, true));
    }

    // ---- config

    [Fact]
    public void TheShippedFileTurnsGuildChatOnAndTheFileStillValidates()
    {
        // Enabled 2026-10-08 on the owner's explicit "activate".
        var rules = Shipped();

        Assert.True(rules.FeatureFlags.GuildChat);
        Assert.Contains(nameof(DeferredFeatureFlags.GuildChat), rules.FeatureFlags.EnabledNames());
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void GuildChatNeedsNoOtherFlagAndShowsWhenOn()
    {
        var rules = Shipped();

        rules.FeatureFlags.GuildChat = true;

        Assert.Empty(ShardRulesConfiguration.Validate(rules));
        Assert.Contains(nameof(DeferredFeatureFlags.GuildChat), rules.FeatureFlags.EnabledNames());
    }

    [Fact]
    public void WithoutLoadedSettingsGuildChatIsOff() => Assert.False(Enabled);
}
