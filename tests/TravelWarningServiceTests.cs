using System.Text.Json;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class TravelWarningServiceTests
{
    private static ShardRules Shipped()
    {
        var path = Path.Combine(
            AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json"
        );
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    [Fact]
    public void ABluePlayerGoingIntoAHotZoneFromOutsideIsWarned() =>
        Assert.True(TravelWarningService.ShouldWarn(true, true, false, true, false));

    [Theory]
    [InlineData(false, true, false, true, false)] // feature off
    [InlineData(true, false, false, true, false)] // destination is not Hot
    [InlineData(true, true, true, true, false)]   // already in a Hot Zone: nothing new to be warned of
    [InlineData(true, true, false, false, false)] // not blue (criminal, murderer or staff)
    [InlineData(true, true, false, true, true)]   // switched the warning off
    public void EachOtherCaseIsNotWarned(bool on, bool destinationHot, bool originHot, bool innocent, bool suppressed) =>
        Assert.False(TravelWarningService.ShouldWarn(on, destinationHot, originHot, innocent, suppressed));

    [Theory]
    [InlineData("off", true)]
    [InlineData("OFF", true)]
    [InlineData("on", false)]
    [InlineData("", false)]
    [InlineData(null, false)]
    public void TheSavedChoiceIsReadFromTheAccountTag(string? tag, bool suppressed) =>
        Assert.Equal(suppressed, TravelWarningService.IsSuppressed(tag));

    [Fact]
    public void TheStatusTellsThePlayerHowToChangeIt()
    {
        Assert.Contains("[TravelWarning on", TravelWarningService.StatusText(true));
        Assert.Contains("[TravelWarning off", TravelWarningService.StatusText(false));
    }

    [Fact]
    public void TheWarningSaysWhatTheRiskIsAndTheCheckboxIsWorded()
    {
        Assert.Contains("Hot Zone", TravelWarningService.Headline);
        Assert.Contains("attack", TravelWarningService.Risk);
        Assert.Contains("Wards", TravelWarningService.Risk);
        Assert.Equal("Do not show me this warning again when traveling", TravelWarningService.CheckboxLabel);
    }

    [Fact]
    public void TheFlagIsOnInTheShippedFileAndNeedsHotZones()
    {
        var rules = Shipped();

        Assert.True(rules.FeatureFlags.HotZoneTravelWarning);

        rules.FeatureFlags.HotZones = false;

        Assert.Contains("hotZoneTravelWarning requires hotZones.", ShardRulesConfiguration.Validate(rules));

        rules.FeatureFlags.HotZones = true;

        Assert.DoesNotContain("hotZoneTravelWarning requires hotZones.", ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void TheFlagIsListedWhenOn()
    {
        var flags = new DeferredFeatureFlags { HotZoneTravelWarning = true };

        Assert.Contains("HotZoneTravelWarning", flags.EnabledNames());
        Assert.DoesNotContain("none", flags.EnabledNames());
    }
}
