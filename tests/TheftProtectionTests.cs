using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class TheftProtectionTests
{
    [Fact]
    public void BackpackWardIsAvailableToAdministrativeItemCreation()
    {
        var constructor = typeof(BackpackWard).GetConstructor(Type.EmptyTypes);

        Assert.NotNull(constructor);
        Assert.Contains(
            constructor!.GetCustomAttributes(inherit: false),
            attribute => string.Equals(attribute.GetType().Name, "ConstructibleAttribute", StringComparison.Ordinal)
        );
    }

    [Theory]
    [InlineData(-1, 0.0)]
    [InlineData(0, 0.0)]
    [InlineData(1, 0.25)]
    [InlineData(2, 0.50)]
    [InlineData(3, 1.0)]
    [InlineData(20, 1.0)]
    public void DetectionEscalatesPerThiefAccount(int successes, double expected)
    {
        Assert.Equal(expected, TheftProtectionService.AdditionalDetectionChance(successes));
    }

    [Fact]
    public void ProtectionWindowUsesUtcExpiry()
    {
        var now = new DateTime(2026, 9, 23, 12, 0, 0, DateTimeKind.Utc);

        Assert.True(TheftProtectionService.IsProtectionWindowActive(now, now.AddSeconds(1)));
        Assert.False(TheftProtectionService.IsProtectionWindowActive(now, now));
        Assert.False(TheftProtectionService.IsProtectionWindowActive(now, now.AddSeconds(-1)));
    }

    [Fact]
    public void LootProtectionUsesTheApprovedTenMinuteWindow()
    {
        Assert.Equal(TimeSpan.FromMinutes(10), TheftProtectionService.LootProtectionDuration);
    }

    [Theory]
    [InlineData(false, false, true, true, "active", false)]
    [InlineData(true, true, true, true, "active", false)]
    [InlineData(true, false, false, true, "active", false)]
    [InlineData(true, false, true, false, "active", false)]
    [InlineData(true, false, true, true, "missing", false)]
    [InlineData(true, false, true, true, "expired", false)]
    [InlineData(true, false, true, true, "malformed", false)]
    [InlineData(true, false, true, true, "active", true)]
    public void CorpseRepeatWardRequiresAllPolicyPredicatesAndActiveMarker(
        bool enabled,
        bool hotZonesEnabled,
        bool monsterCorpse,
        bool criminalAction,
        string markerKind,
        bool expected
    )
    {
        var now = new DateTime(2026, 9, 24, 12, 0, 0, DateTimeKind.Utc);
        var marker = markerKind switch
        {
            "active" => now.AddMinutes(5).ToString("O", System.Globalization.CultureInfo.InvariantCulture),
            "expired" => now.AddMinutes(-1).ToString("O", System.Globalization.CultureInfo.InvariantCulture),
            "malformed" => "not-a-timestamp",
            _ => null
        };

        Assert.Equal(
            expected,
            TheftProtectionService.IsCorpseLootProtectionActive(
                enabled,
                hotZonesEnabled,
                monsterCorpse,
                criminalAction,
                marker,
                now
            )
        );
    }

    [Theory]
    [InlineData(null, false)]
    [InlineData("", false)]
    [InlineData("0", false)]
    [InlineData("1", true)]
    [InlineData("2", false)]
    public void LootProtectionEntitlementVersionIsIdempotent(string? value, bool expected)
    {
        Assert.Equal(expected, TheftProtectionService.IsLootProtectionEntitlementCurrent(value));
    }

    [Fact]
    public void RegionEntryAndExitMessagesArePlayerFacingAndTransitionOnly()
    {
        Assert.Equal(
            new[] { "You are now protected from theft by the bank guards" },
            TheftProtectionService.DescribeRegionTransitions(false, true, false, false)
        );
        Assert.Equal(
            new[] { "You are outside bank guard protection from theft" },
            TheftProtectionService.DescribeRegionTransitions(true, false, false, false)
        );
        Assert.Equal(
            new[] { "You are entering a protected dungeon: direct player stealing is disabled here" },
            TheftProtectionService.DescribeRegionTransitions(false, false, false, true)
        );
        Assert.Equal(
            new[] { "You have left the protected dungeon: normal player stealing rules now apply" },
            TheftProtectionService.DescribeRegionTransitions(false, false, true, false)
        );
        Assert.Empty(TheftProtectionService.DescribeRegionTransitions(true, true, true, true));
    }
}
