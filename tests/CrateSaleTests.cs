using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class CrateSaleTests
{
    [Fact]
    public void AnEmptyContainerIsNotThisRulesBusiness() => Assert.False(CrateSaleService.OnlyItsOwnKeys(1234, []));

    [Fact]
    public void AnUnlockableContainerNeverCounts() => Assert.False(CrateSaleService.OnlyItsOwnKeys(0, []));

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().SellCratesWithKeys);
}
