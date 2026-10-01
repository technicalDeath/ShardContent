using Server;
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

    [Theory]
    [InlineData(true, false, false, true)]    // a lone mount, owner on foot: stays
    [InlineData(true, true, false, false)]    // owner riding another mount: no
    [InlineData(true, false, true, false)]    // another mount already standing in the dungeon: no
    [InlineData(false, false, false, false)]  // not a mount: never
    public void OnlyOneMountMayStayAndOnlyWhileTheOwnerIsOnFoot(bool isMount, bool ownerMounted, bool another, bool expected)
    {
        Assert.Equal(expected, PetRestrictionService.MountMayStay(isMount, ownerMounted, another));
    }

    [Theory]
    [InlineData(true, false, false, false, false, true)]   // outside a dungeon: always
    [InlineData(false, true, false, false, false, true)]   // rules off: always
    [InlineData(true, true, true, false, false, true)]     // inside: a lone mount, owner on foot
    [InlineData(true, true, true, true, false, false)]     // inside: owner riding
    [InlineData(true, true, true, false, true, false)]     // inside: another mount already standing
    [InlineData(true, true, false, false, false, false)]   // inside: not a mount
    public void ReleaseInsideADungeonFollowsTheMountRule(
        bool enabled, bool inDungeon, bool isMount, bool ownerMounted, bool another, bool expected)
    {
        Assert.Equal(expected, PetRestrictionService.MayReleaseInDungeon(enabled, inDungeon, isMount, ownerMounted, another));
    }

    [Fact]
    public void NearestEntranceIsChosenByTheInsideDestination()
    {
        var entries = new[]
        {
            (new Point3D(100, 100, 0), new Point3D(5000, 600, 0)),
            (new Point3D(900, 900, 0), new Point3D(5500, 1900, 0)),
            (new Point3D(300, 300, 0), new Point3D(5506, 1906, 0)),
        };

        Assert.True(DungeonEntrances.TryNearest(entries, new Point3D(5505, 1905, 0), out var outside));
        Assert.Equal(new Point3D(300, 300, 0), outside);
        Assert.False(DungeonEntrances.TryNearest([], new Point3D(0, 0, 0), out _));
    }
}
