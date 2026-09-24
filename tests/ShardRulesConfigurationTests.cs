using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class ShardRulesConfigurationTests
{
    [Fact]
    public void AlphaTwoFlagsAreValidWhenTheirDependenciesAreExplicit()
    {
        var rules = Baseline();
        rules.Alpha2EnablementAcknowledged = true;
        rules.FeatureFlags.SafeWorld = true;
        rules.FeatureFlags.AutomaticMurderAdjudication = true;
        rules.FeatureFlags.TheftProtection = true;
        rules.FeatureFlags.KnockedOut = true;

        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void AlphaThreeFlagsAndMissingDependenciesRemainRejected()
    {
        var rules = Baseline();
        rules.FeatureFlags.KnockedOut = true;
        rules.FeatureFlags.HotZones = true;

        var errors = ShardRulesConfiguration.Validate(rules);

        Assert.Contains(errors, error => error.Contains("Alpha 3+", StringComparison.Ordinal));
        Assert.Contains(errors, error => error.Contains("knockedOut requires", StringComparison.Ordinal));
        Assert.Contains(errors, error => error.Contains("alpha2EnablementAcknowledged", StringComparison.Ordinal));
    }

    private static ShardRules Baseline() => new()
    {
        SchemaVersion = 1,
        PinnedModernUoCommit = new string('a', 40),
        World = new WorldRules { Era = "UOR", EnabledMaps = ["Felucca"] },
        Character = new CharacterRules { TotalSkillCap = 700, IndividualSkillCap = 100, StatCap = 225 },
        Combat = new CombatRules()
    };
}
