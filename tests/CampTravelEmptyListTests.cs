using BritanniaRenaissance.Content;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The camp list opens even when there is no camp to list, with the reason in the window (owner, 2026-10-13).</summary>
public class CampTravelEmptyListTests
{
    [Fact]
    public void AnEmptyListIsAsTallAsATwoCampList() => Assert.Equal(CampTravelService.ListHeight(2), CampTravelService.ListHeight(0));

    [Fact]
    public void TheListGrowsWithItsCamps() => Assert.True(CampTravelService.ListHeight(5) > CampTravelService.ListHeight(0));

    [Fact]
    public void NoCampTextSaysWhyAndWhatToDo()
    {
        var inParty = CampTravelService.NoCampText(true);
        var alone = CampTravelService.NoCampText(false);

        Assert.Contains("None of your party has a campfire burning", inParty);
        Assert.Contains("[CampTravel", inParty);
        Assert.Contains("not in a party", alone);
        Assert.Contains("[CampTravel", alone);
        Assert.DoesNotContain("Britannia Renaissance", inParty + alone);
    }
}
