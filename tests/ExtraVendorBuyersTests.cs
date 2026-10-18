using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class ExtraVendorBuyersTests
{
    [Theory]
    [InlineData(0, 1)]
    [InlineData(8, 10)]
    [InlineData(40, 50)]
    public void ACraftedItemPaysTheCraftedGoodsFloor(int materialCost, int price) => Assert.Equal(price, ExtraVendorBuyers.CraftedPrice(materialCost));

    [Fact]
    public void AnUnknownCraftIsRefused()
    {
        var errors = new List<string>();
        ExtraVendorBuyers.Validate(new ExtraVendorBuyerRules { Crafted = [new ExtraCraftedBuyer { CraftSystem = "cooking", Vendors = ["Cook"] }] }, errors);
        Assert.NotEmpty(errors);
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().ExtraVendorBuyers);

    [Fact]
    public void TheDeedFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().OrdinaryAddonDeeds);
}
