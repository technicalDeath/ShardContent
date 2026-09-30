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

        Assert.Contains(errors, error => error.Contains("hotZones requires alpha3EnablementAcknowledged", StringComparison.Ordinal));
        Assert.Contains(errors, error => error.Contains("knockedOut requires", StringComparison.Ordinal));
        Assert.Contains(errors, error => error.Contains("alpha2EnablementAcknowledged", StringComparison.Ordinal));
    }

    [Fact]
    public void StartingStatsRequireExplicitAlphaThreeAcknowledgment()
    {
        var rules = Baseline();
        rules.FeatureFlags.Alpha3StartingStats = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("alpha3EnablementAcknowledged", StringComparison.Ordinal)
        );

        rules.Alpha3EnablementAcknowledged = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void StarterScissorsRequireExplicitAlphaThreeAcknowledgment()
    {
        var rules = Baseline();
        rules.FeatureFlags.Alpha3StarterScissors = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("alpha3EnablementAcknowledged", StringComparison.Ordinal)
        );

        rules.Alpha3EnablementAcknowledged = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void StarterBagRequiresExplicitAlphaThreeAcknowledgment()
    {
        var rules = Baseline();
        rules.FeatureFlags.Alpha3StarterBag = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("alpha3EnablementAcknowledged", StringComparison.Ordinal)
        );

        rules.Alpha3EnablementAcknowledged = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void StarterGoldRequiresExplicitAlphaThreeAcknowledgment()
    {
        var rules = Baseline();
        rules.FeatureFlags.Alpha3StarterGold = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("alpha3EnablementAcknowledged", StringComparison.Ordinal)
        );

        rules.Alpha3EnablementAcknowledged = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void StarterCraftMaterialsRequireExplicitAlphaThreeAcknowledgment()
    {
        var rules = Baseline();
        rules.FeatureFlags.Alpha3StarterCraftMaterials = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("alpha3EnablementAcknowledged", StringComparison.Ordinal)
        );

        rules.Alpha3EnablementAcknowledged = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void StarterCombatGearRequiresExplicitAlphaThreeAcknowledgment()
    {
        var rules = Baseline();
        rules.FeatureFlags.Alpha3StarterCombatGear = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("alpha3EnablementAcknowledged", StringComparison.Ordinal)
        );

        rules.Alpha3EnablementAcknowledged = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void SkillBankCapacityIsTypedAndBounded()
    {
        var rules = Baseline();
        rules.SkillBank.CapacityTenths = 60001;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("skillBank.capacityTenths", StringComparison.Ordinal)
        );

        rules.SkillBank.CapacityTenths = 3000;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void SkillBankRequiresAlphaThreeAcknowledgment()
    {
        var rules = Baseline();
        rules.FeatureFlags.SkillBank = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("skillBank requires alpha3EnablementAcknowledged", StringComparison.Ordinal)
        );

        rules.Alpha3EnablementAcknowledged = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void CoolDungeonFlagCannotBeEnabledBeforeBetaTwoRotationExists()
    {
        var rules = Baseline();
        rules.FeatureFlags.CoolZones = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("Beta 2", StringComparison.Ordinal)
        );
    }

    [Fact]
    public void HotZonesRequireSurveyedNamedOutdoorBoundaries()
    {
        var rules = Baseline();
        rules.FeatureFlags.HotZones = true;

        Assert.Contains(ShardRulesConfiguration.Validate(rules), error => error.Contains("surveyed FireIsland", StringComparison.Ordinal));

        rules.HotZones.PermanentOutdoorRegions.Add(new OutdoorHotRegionDefinition
        {
            Name = "FireIsland",
            Map = "Trammel",
            Points = [new TheftPoint { X = 1, Y = 1 }, new TheftPoint { X = 2, Y = 1 }]
        });

        var errors = ShardRulesConfiguration.Validate(rules);
        Assert.Contains(errors, error => error.Contains("enabled map", StringComparison.Ordinal));
        Assert.Contains(errors, error => error.Contains("BuccaneersDenIsland", StringComparison.Ordinal));
    }

    [Fact]
    public void HotZonesCanBeRehearsedWithAcknowledgmentAndNamedBoundaries()
    {
        var rules = Baseline();
        rules.Alpha3EnablementAcknowledged = true;
        rules.FeatureFlags.HotZones = true;
        foreach (var name in new[] { "FireIsland", "BuccaneersDenIsland" })
        {
            rules.HotZones.PermanentOutdoorRegions.Add(new OutdoorHotRegionDefinition
            {
                Name = name,
                Map = "Felucca",
                Points =
                [
                    new TheftPoint { X = 1, Y = 1 },
                    new TheftPoint { X = 2, Y = 1 },
                    new TheftPoint { X = 1, Y = 2 }
                ]
            });
        }

        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void HousingGeographyRequiresBuccaneersDenNoHousingBoundary()
    {
        var rules = Baseline();
        rules.FeatureFlags.HousingGeography = true;

        Assert.Contains(
            ShardRulesConfiguration.Validate(rules),
            error => error.Contains("BuccaneersDenIsland no-housing polygon", StringComparison.Ordinal)
        );
    }

    [Fact]
    public void HousingDistrictSequenceCannotOpenPastALockedDistrict()
    {
        var rules = Baseline();
        rules.Housing.ResidentialDistricts.Add(District("GreaterBritainA", 1, false));
        rules.Housing.ResidentialDistricts.Add(District("GreaterBritainB", 2, true));

        Assert.Contains(ShardRulesConfiguration.Validate(rules),
            error => error.Contains("open only an initial prefix", StringComparison.Ordinal));

        rules.Housing.ResidentialDistricts[0].Open = true;
        Assert.Empty(ShardRulesConfiguration.Validate(rules));
    }

    [Fact]
    public void HousingRegionsRequireDistinctNamesAndFeluccaPolygons()
    {
        var rules = Baseline();
        rules.Housing.ResidentialDistricts.Add(District("GreaterBritainA", 1, true));
        rules.Housing.ProtectedRegions.Add(new OutdoorHotRegionDefinition
        {
            Name = "GreaterBritainA", Map = "Trammel",
            Points = [new TheftPoint { X = 1, Y = 1 }, new TheftPoint { X = 2, Y = 2 }]
        });

        Assert.Contains(ShardRulesConfiguration.Validate(rules),
            error => error.Contains("housing.protectedRegions", StringComparison.Ordinal));
    }

    [Fact]
    public void RuralMultiplierIsBoundedAndDefaultsToDoubleCost()
    {
        var rules = Baseline();
        Assert.Equal(2m, rules.Housing.RuralCostMultiplier);
        Assert.Empty(ShardRulesConfiguration.Validate(rules));

        rules.Housing.RuralCostMultiplier = 1.5m;
        Assert.Contains(ShardRulesConfiguration.Validate(rules),
            error => error.Contains("housing.ruralCostMultiplier", StringComparison.Ordinal));
    }

    [Fact]
    public void TheftRegionsRequireNamedMapsAndThreePoints()
    {
        var rules = Baseline();
        rules.TheftRegions.BankProtectionPolygons.Add(new TheftPolygonDefinition
        {
            Map = string.Empty,
            Points = [new TheftPoint { X = 1, Y = 1 }, new TheftPoint { X = 2, Y = 2 }]
        });

        var errors = ShardRulesConfiguration.Validate(rules);

        Assert.Contains(errors, error => error.Contains("bankProtectionPolygons", StringComparison.Ordinal));
    }

    [Fact]
    public void TheftRegionsCannotReferenceDisabledMaps()
    {
        var rules = Baseline();
        rules.TheftRegions.CoolDungeonPolygons.Add(new TheftPolygonDefinition
        {
            Map = "Trammel",
            Points =
            [
                new TheftPoint { X = 1, Y = 1 },
                new TheftPoint { X = 2, Y = 1 },
                new TheftPoint { X = 2, Y = 2 }
            ]
        });

        var errors = ShardRulesConfiguration.Validate(rules);

        Assert.Contains(errors, error => error.Contains("not enabled", StringComparison.Ordinal));
    }

    private static ShardRules Baseline() => new()
    {
        SchemaVersion = 1,
        PinnedModernUoCommit = new string('a', 40),
        World = new WorldRules { Era = "UOR", EnabledMaps = ["Felucca"] },
        Character = new CharacterRules { TotalSkillCap = 700, IndividualSkillCap = 100, StatCap = 225 },
        Combat = new CombatRules()
    };

    private static HousingDistrictDefinition District(string name, int sequence, bool open) => new()
    {
        Name = name,
        Map = "Felucca",
        Points =
        [
            new TheftPoint { X = 1, Y = 1 },
            new TheftPoint { X = 2, Y = 1 },
            new TheftPoint { X = 2, Y = 2 }
        ],
        Sequence = sequence,
        SoftCapacity = 10,
        Open = open
    };
}
