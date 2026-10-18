using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class MetalSkillNoticeTests
{
    [Theory]
    [InlineData("DullCopperIngot", "dull copper")]
    [InlineData("ShadowIronIngot", "shadow iron")]
    [InlineData("ValoriteIngot", "valorite")]
    public void TheMetalIsNamedAsPlayersSayIt(string type, string name) => Assert.Equal(name, MetalSkillNoticeService.MetalName(type));

    [Fact]
    public void TheLineNamesTheSkillAndPointsToIron() =>
        Assert.Equal(
            "You need Blacksmithy 65 to work dull copper. Target iron ingots to make things now.",
            MetalSkillNoticeService.Text("DullCopperIngot", 65.0)
        );

    [Fact]
    public void ARareMetalIsNamedOnItsTooltip() => Assert.Equal("Metal: Dull Copper", ItemTooltipService.MetalLine("Dull Copper"));

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().MetalSkillNotice);
}
