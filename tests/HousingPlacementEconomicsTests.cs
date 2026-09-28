using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class HousingPlacementEconomicsTests
{
    [Theory]
    [InlineData(HousingLandClass.Residential, false, 37000, 0, 37000, 37000)]
    [InlineData(HousingLandClass.Rural, false, 37000, 37000, 74000, 74000)]
    [InlineData(HousingLandClass.Residential, true, 43800, 0, 0, 43800)]
    [InlineData(HousingLandClass.Rural, true, 43800, 43800, 43800, 87600)]
    public void QuoteUsesRouteSpecificNormalValueAndChargesOnlyWhatRemainsDue(
        HousingLandClass landClass, bool prepaid, int normalValue, int premium, int due, int total
    )
    {
        Assert.True(HousingPlacementEconomics.TryQuote(landClass, normalValue, prepaid, out var quote));
        Assert.Equal(normalValue, quote.NormalValue);
        Assert.Equal(premium, quote.RuralPremium);
        Assert.Equal(due, quote.DueAtPlacement);
        Assert.Equal(total, quote.TotalEconomicCost);
    }

    [Theory]
    [InlineData(HousingLandClass.Protected, 43800)]
    [InlineData(HousingLandClass.Rural, 0)]
    [InlineData(HousingLandClass.Rural, int.MaxValue)]
    [InlineData((HousingLandClass)999, 37000)]
    public void ProtectedInvalidAndOverflowedQuotesAreRejected(HousingLandClass landClass, int normalValue)
    {
        Assert.False(HousingPlacementEconomics.TryQuote(landClass, normalValue, false, out var quote));
        Assert.Equal(default, quote);
    }

    [Fact]
    public void ConfiguredHigherRuralMultiplierAffectsOnlyNewQuote()
    {
        Assert.True(HousingPlacementEconomics.TryQuote(
            HousingLandClass.Rural, 43800, true, out var quote, 2.5m
        ));
        Assert.Equal(65700, quote.RuralPremium);
        Assert.Equal(65700, quote.DueAtPlacement);
        Assert.Equal(109500, quote.TotalEconomicCost);

        Assert.True(HousingPlacementEconomics.TryQuote(
            HousingLandClass.FireIslandResidential, 43800, true, out var fireQuote, 2.5m
        ));
        Assert.Equal(0, fireQuote.RuralPremium);
        Assert.False(HousingPlacementEconomics.TryQuote(
            HousingLandClass.Rural, 43800, true, out _, 1.5m
        ));
    }
}
