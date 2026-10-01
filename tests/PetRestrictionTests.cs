using Server.Mobiles;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class PetRestrictionTests
{
    [Theory]
    [InlineData(typeof(Horse), true, false, true)]       // a tamed mount counts (a ridden one is never in the world)
    [InlineData(typeof(Dragon), true, false, true)]
    [InlineData(typeof(Dog), true, false, true)]
    [InlineData(typeof(Dragon), false, false, false)]    // wild
    [InlineData(typeof(Dragon), true, true, false)]      // spell-summoned
    [InlineData(typeof(PackLlama), true, false, false)]  // pack animals stay allowed
    [InlineData(typeof(PackHorse), true, false, false)]
    [InlineData(typeof(HireFighter), true, false, false)] // hirelings
    [InlineData(typeof(BaseFamiliar), true, false, false)]
    [InlineData(typeof(BaseEscortable), true, false, false)]
    public void RestrictedKindMatchesTheApprovedTest(Type type, bool controlled, bool summoned, bool expected)
    {
        Assert.Equal(expected, PetRestrictionService.IsRestrictedKind(type, controlled, summoned));
    }

    [Fact]
    public void EveryHirelingAndFamiliarSubclassIsExempt()
    {
        foreach (var type in typeof(BaseHire).Assembly.GetTypes())
        {
            if (typeof(BaseHire).IsAssignableFrom(type) || typeof(BaseFamiliar).IsAssignableFrom(type))
            {
                Assert.False(PetRestrictionService.IsRestrictedKind(type, true, false), type.Name);
            }
        }
    }

    [Fact]
    public void FeatureFlagDefaultsOffAndIsListedWhenOn()
    {
        var flags = new DeferredFeatureFlags();

        Assert.False(flags.PetRestrictions);
        Assert.DoesNotContain(nameof(DeferredFeatureFlags.PetRestrictions), flags.EnabledNames());

        flags.PetRestrictions = true;
        Assert.Contains(nameof(DeferredFeatureFlags.PetRestrictions), flags.EnabledNames());
        Assert.DoesNotContain("none", flags.EnabledNames());
    }
}
