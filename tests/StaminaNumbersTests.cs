using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>Stamina numbers over your head: lost to a hit, restored by a refresh potion (docs/Stamina-Numbers-Evidence.md).</summary>
public class StaminaNumbersTests
{
    [Fact]
    public void ThePacketCarriesTheSerialTheKindAndTheAmount()
    {
        Assert.Equal(
            new byte[] { 0xBF, 0, 12, 0x00, 0xAD, 0x00, 0x01, 0x02, 0x03, StaminaNumbersService.Lost, 0x00, 0x05 },
            StaminaNumbersService.Packet(0x00010203, StaminaNumbersService.Lost, 5)
        );
        Assert.Equal(1, StaminaNumbersService.Packet(1, StaminaNumbersService.Restored, 8)[9]);
        Assert.Equal(12, StaminaNumbersService.Packet(1, StaminaNumbersService.Lost, 1).Length);
    }

    [Fact]
    public void OnlyARealChangeToAPlayerWithAClientIsShownWhileTheFlagIsOn()
    {
        Assert.True(StaminaNumbersService.Shows(true, true, 3));
        Assert.False(StaminaNumbersService.Shows(false, true, 3));
        Assert.False(StaminaNumbersService.Shows(true, false, 3)); // a creature, or a player without a client
        Assert.False(StaminaNumbersService.Shows(true, true, 0));  // the bar was already empty, or already full
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().StaminaNumbers);

    [Fact]
    public void TheScreenPageNamesTheStaminaNumbersOnlyWhileTheyAreOn()
    {
        string Screen(WelcomeGuide.Context c) =>
            string.Join(" ", WelcomeGuide.Topics(c, new CampTravelRules(), camping: new CampingRules()).SelectMany(t => t.Paragraphs));

        var on = Screen(new WelcomeGuide.Context(false, false, false, false, false, StaminaNumbers: true));

        Assert.Contains("The stamina a hit takes from you floats up over you in blue, such as -3 stam (a mace or a staff takes 3 to 5 more)", on);
        Assert.Contains("the stamina a refresh potion gives back, such as +8 stam; each has its own switch.", on);
        Assert.DoesNotContain("-3 stam", Screen(new WelcomeGuide.Context(false, false, false, false, false, DamageNumbers: true)));
    }
}
