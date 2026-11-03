using Server;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Dragging something into full hands swaps it in (docs/Drag-Into-Hands-Evidence.md).</summary>
public class DragIntoHandsTests
{
    [Theory]
    [InlineData(Layer.OneHanded)]
    [InlineData(Layer.TwoHanded)]
    public void AHandItemOnYourOwnPaperdollSwaps(Layer layer) => Assert.True(DragIntoHands.Applies(true, true, layer));

    [Theory]
    [InlineData(Layer.InnerTorso)]
    [InlineData(Layer.Helm)]
    [InlineData(Layer.Ring)]
    public void ArmorClothingAndJewelleryKeepTheStockRule(Layer layer) => Assert.False(DragIntoHands.Applies(true, true, layer));

    [Fact]
    public void AnotherOnesPaperdollAndTheFlagOffKeepTheStockRule()
    {
        Assert.False(DragIntoHands.Applies(true, false, Layer.OneHanded));
        Assert.False(DragIntoHands.Applies(false, true, Layer.OneHanded));
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().DragIntoHands);
}
