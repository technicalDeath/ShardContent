using System.Text.Json;
using Xunit;
using static BritanniaRenaissance.Content.PoisonReliefService;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// Poison relief (docs/Poison-Relief-Plan.md): the grace-window decision, the once-per-character hint, the starter potion count, the
/// settings and the flag, as pure rules. The engine hook is tested in UOContent (PlayerMobileShardHookTests) and the whole path live.
/// </summary>
public class PoisonReliefTests
{
    private static readonly PoisonReliefRules Shipped = new();

    private static ShardRules ShippedConfiguration()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "shard-rules.json");
        return JsonSerializer.Deserialize<ShardRules>(File.ReadAllText(path))!;
    }

    // ---- the grace window

    [Theory]
    [InlineData(0.0)]
    [InlineData(5.0)]
    [InlineData(29.9)]
    public void LesserPoisonFromAMonsterIsRefusedInsideTheWindow(double secondsSinceEnded) =>
        Assert.True(Refuses(Shipped, true, true, false, 0, secondsSinceEnded));

    [Theory]
    [InlineData(30.0)]
    [InlineData(31.0)]
    [InlineData(600.0)]
    public void ItLandsOnceTheWindowHasRunOut(double secondsSinceEnded) =>
        Assert.False(Refuses(Shipped, true, true, false, 0, secondsSinceEnded));

    [Fact]
    public void ItLandsWhenThePlayerHasNeverHadAPoisonEnd() =>
        Assert.False(Refuses(Shipped, true, true, false, 0, null));

    [Fact]
    public void AClockThatRanBackwardsRefusesNothing() =>
        Assert.False(Refuses(Shipped, true, true, false, 0, -1.0));

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(4)]
    public void AStrongerPoisonThanTheCapIsStock(int level) =>
        Assert.False(Refuses(Shipped, true, true, false, level, 5.0));

    [Fact]
    public void RaisingTheCapCoversRegularButNotGreater()
    {
        var rules = new PoisonReliefRules { GraceMaxLevel = 1 };

        Assert.True(Refuses(rules, true, true, false, 1, 5.0));
        Assert.False(Refuses(rules, true, true, false, 2, 5.0));
    }

    [Fact]
    public void PoisonFromAPlayerIsNeverRefused() =>
        Assert.False(Refuses(Shipped, true, true, true, 0, 5.0));

    [Fact]
    public void OnlyAnOrdinaryPlayerIsHelped() =>
        Assert.False(Refuses(Shipped, true, false, false, 0, 5.0));

    [Fact]
    public void WithTheFlagOffNothingIsRefused() =>
        Assert.False(Refuses(Shipped, false, true, false, 0, 5.0));

    [Fact]
    public void AWindowOfZeroSecondsSwitchesTheGraceOff() =>
        Assert.False(Refuses(new PoisonReliefRules { GraceSeconds = 0.0 }, true, true, false, 0, 0.0));

    // ---- the hint

    [Theory]
    [InlineData(0.0, 0.0)]
    [InlineData(59.9, 80.0)]
    [InlineData(80.0, 59.9)]
    [InlineData(30.0, 100.0)]
    public void ACharacterWhoseBandageCannotCureIsToldOnce(double healing, double anatomy) =>
        Assert.True(ShouldHint(true, true, healing, anatomy, false));

    [Theory]
    [InlineData(60.0, 60.0)]
    [InlineData(100.0, 100.0)]
    public void ACharacterWhoseBandageCanCureIsNotTold(double healing, double anatomy) =>
        Assert.False(ShouldHint(true, true, healing, anatomy, false));

    [Fact]
    public void ItIsNeverRepeated() =>
        Assert.False(ShouldHint(true, true, 0.0, 0.0, true));

    [Fact]
    public void StaffAndAFlagOffAreNeverTold()
    {
        Assert.False(ShouldHint(true, false, 0.0, 0.0, false));
        Assert.False(ShouldHint(false, true, 0.0, 0.0, false));
    }

    [Fact]
    public void TheHintNamesWhatEndsThePoisonAndWhatABandageNeeds()
    {
        Assert.Contains("bandage", HintText);
        Assert.Contains("60", HintText);
        Assert.Contains("Cure potion", HintText);
        Assert.Contains("15 gold", HintText);
        Assert.Contains("Cure spell", HintText);
        Assert.DoesNotContain("Britannia Renaissance", HintText, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public void ThePoisonTooltipShowsTheBandageLineOnlyWhileReliefIsOn()
    {
        var text = BuffIconRulesLoader.Parse(
                File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "configuration", "buff-icons.json"))
            )
            .States["poison"];

        var off = BuffIconRulesLoader.Render(text, name => name == "level" ? "Lesser" : null);
        var on = BuffIconRulesLoader.Render(text, name => name is "level" ? "Lesser" : name is "relief" ? "" : null);

        Assert.DoesNotContain("bandage", off);
        Assert.Contains("A bandage only tries to cure you, and that needs Healing and Anatomy 60.", on);
        Assert.StartsWith("Poisoned<br>Lesser poison.", on);
    }

    // ---- the potions

    [Fact]
    public void ANewCharacterGetsTheConfiguredNumberOfPotionsOnlyWhileTheFlagIsOn()
    {
        Assert.Equal(5, PotionCount(Shipped, true));
        Assert.Equal(0, PotionCount(Shipped, false));
        Assert.Equal(0, PotionCount(new PoisonReliefRules { CurePotions = -3 }, true));
        Assert.Equal(2, PotionCount(new PoisonReliefRules { CurePotions = 2 }, true));
    }

    // ---- settings and the flag

    [Fact]
    public void TheDefaultsAreTheOwnersChoices()
    {
        Assert.Equal(5, Shipped.CurePotions);
        Assert.Equal(30.0, Shipped.GraceSeconds);
        Assert.Equal(0, Shipped.GraceMaxLevel);
    }

    [Fact]
    public void TheDefaultsAreValid()
    {
        var errors = new List<string>();
        Validate(Shipped, errors);
        Assert.Empty(errors);
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(21)]
    public void APotionCountOutsideZeroToTwentyIsRejected(int count)
    {
        var errors = new List<string>();
        Validate(new PoisonReliefRules { CurePotions = count }, errors);
        Assert.Contains(errors, e => e.Contains("curePotions"));
    }

    [Theory]
    [InlineData(-1.0)]
    [InlineData(301.0)]
    [InlineData(double.NaN)]
    public void AWindowOutsideZeroToThreeHundredSecondsIsRejected(double seconds)
    {
        var errors = new List<string>();
        Validate(new PoisonReliefRules { GraceSeconds = seconds }, errors);
        Assert.Contains(errors, e => e.Contains("graceSeconds"));
    }

    [Theory]
    [InlineData(-1)]
    [InlineData(5)]
    public void ALevelOutsideZeroToFourIsRejected(int level)
    {
        var errors = new List<string>();
        Validate(new PoisonReliefRules { GraceMaxLevel = level }, errors);
        Assert.Contains(errors, e => e.Contains("graceMaxLevel"));
    }

    [Fact]
    public void TheShippedConfigurationHasTheFlagOnSinceTheOwnerActivatedItAndTheOwnersNumbers()
    {
        var rules = ShippedConfiguration();

        Assert.True(rules.FeatureFlags.PoisonRelief);
        Assert.Equal(5, rules.PoisonRelief.CurePotions);
        Assert.Equal(30.0, rules.PoisonRelief.GraceSeconds);
        Assert.Equal(0, rules.PoisonRelief.GraceMaxLevel);
        Assert.Empty(ShardRulesConfiguration.Validate(rules).Where(e => e.Contains("poisonRelief", StringComparison.OrdinalIgnoreCase)));
        Assert.Contains(nameof(DeferredFeatureFlags.PoisonRelief), rules.FeatureFlags.EnabledNames());
    }

    [Fact]
    public void TheFlagIsListedWhenOn() =>
        Assert.Contains(nameof(DeferredFeatureFlags.PoisonRelief), new DeferredFeatureFlags { PoisonRelief = true }.EnabledNames());
}
