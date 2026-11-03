using Server.Engines.Craft;
using Server.Engines.Harvest;
using Server.Items;
using Server.SkillHandlers;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>A progress bar over your own character while a timed action runs (docs/Action-Progress-Bars-Evidence.md, plan docs/Action-Progress-Bars-Plan.md).</summary>
public class ActionProgressBarsTests
{
    [Fact]
    public void ThePacketCarriesTheSerialTheLengthTheLabelAndTheTheme()
    {
        Assert.Equal(
            new byte[]
            {
                0xBF, 0, 21, 0x00, 0xB4, 0x00, 0x01, 0x02, 0x03, 0x09, 0xC4, 8, (byte)'C', (byte)'h', (byte)'o', (byte)'p', (byte)'p', (byte)'i', (byte)'n', (byte)'g',
                (byte)ActionProgressBars.Theme.Gathering
            },
            ActionProgressBars.Packet(0x00010203, TimeSpan.FromMilliseconds(2500), "Chopping", ActionProgressBars.Theme.Gathering)
        );
    }

    [Fact]
    public void TheThemeIsTheLastByte()
    {
        var packet = ActionProgressBars.Packet(1, TimeSpan.FromSeconds(3), "Bandaging", ActionProgressBars.Theme.Healing);

        Assert.Equal(3, packet[^1]);
        Assert.Equal(packet.Length, packet[1] << 8 | packet[2]);
    }

    [Fact]
    public void TheThemesAreTheEightTheOwnerApproved()
    {
        Assert.Equal(
            new[] { 1, 2, 3, 4, 5, 6, 7, 8 },
            Enum.GetValues<ActionProgressBars.Theme>().Select(theme => (int)theme).ToArray()
        );
    }

    [Fact]
    public void ALengthOfZeroClearsTheBar()
    {
        var packet = ActionProgressBars.Packet(1, TimeSpan.Zero, "Chopping");

        Assert.Equal(0, packet[9]);
        Assert.Equal(0, packet[10]);
    }

    [Fact]
    public void TheLabelIsShortAndPlainText()
    {
        var packet = ActionProgressBars.Packet(1, TimeSpan.FromSeconds(1), new string('x', 40) + "é");

        Assert.Equal(ActionProgressBars.MaxLabelLength, packet[11]);
        Assert.Equal(13 + ActionProgressBars.MaxLabelLength, packet.Length);
        Assert.Equal(packet.Length, packet[1] << 8 | packet[2]);
        Assert.Equal((byte)'?', ActionProgressBars.Packet(1, TimeSpan.FromSeconds(1), "é")[12]);
    }

    [Fact]
    public void ALongActionIsCappedAtTheTwoByteLength()
    {
        var packet = ActionProgressBars.Packet(1, TimeSpan.FromMinutes(5), "Chopping");

        Assert.Equal(ushort.MaxValue, packet[9] << 8 | packet[10]);
    }

    [Fact]
    public void EveryGatheringSystemHasABar()
    {
        Assert.Equal("Chopping", ActionProgressBars.LabelFor(Lumberjacking.System));
        Assert.Equal("Mining", ActionProgressBars.LabelFor(Mining.System, Mining.System.OreAndStone));
        Assert.Equal("Digging sand", ActionProgressBars.LabelFor(Mining.System, Mining.System.Sand));
        Assert.Equal("Fishing", ActionProgressBars.LabelFor(Fishing.System));
    }

    [Fact]
    public void TheBarsLastAsLongAsTheStockActions()
    {
        // the stock lengths the shard reads from the engine, not copies of them
        Assert.Equal(TimeSpan.FromSeconds(3), Lockpick.AttemptDelay);
        Assert.Equal(TimeSpan.FromSeconds(5), CookableFood.CookDelay);
        Assert.Equal(TimeSpan.FromSeconds(3), SpinningWheelEvents.SpinDelay);
    }

    [Fact]
    public void PhaseTwoBarsLastAsLongAsTheStockActions()
    {
        // every craft system waits one tick interval (1.25 s) between its two ticks; a mill 5 s; a taming step 3 s; a poison 2 s
        DefBlacksmithy.Initialize();
        DefTailoring.Initialize();
        Assert.Equal(TimeSpan.FromSeconds(1.25), CraftEvents.CraftDuration(DefBlacksmithy.CraftSystem, 2));
        Assert.Equal(TimeSpan.FromSeconds(1.25), CraftEvents.CraftDuration(DefTailoring.CraftSystem, 2));
        Assert.Equal(TimeSpan.FromSeconds(5), FlourMillEvents.GrindDelay);
        Assert.Equal(TimeSpan.FromSeconds(3), AnimalTaming.StepDelay);
        Assert.Equal(TimeSpan.FromSeconds(2), Poisoning.PoisonDelay);
    }

    [Fact]
    public void EachCraftSaysWhatItIsDoing()
    {
        DefBlacksmithy.Initialize();
        DefTailoring.Initialize();
        DefCarpentry.Initialize();
        DefBowFletching.Initialize();
        DefTinkering.Initialize();
        DefAlchemy.Initialize();
        DefInscription.Initialize();
        DefCartography.Initialize();
        DefCooking.Initialize();

        Assert.Equal("Smithing", ActionProgressBars.CraftLabel(DefBlacksmithy.CraftSystem));
        Assert.Equal("Tailoring", ActionProgressBars.CraftLabel(DefTailoring.CraftSystem));
        Assert.Equal("Carpentry", ActionProgressBars.CraftLabel(DefCarpentry.CraftSystem));
        Assert.Equal("Fletching", ActionProgressBars.CraftLabel(DefBowFletching.CraftSystem));
        Assert.Equal("Tinkering", ActionProgressBars.CraftLabel(DefTinkering.CraftSystem));
        Assert.Equal("Grinding", ActionProgressBars.CraftLabel(DefAlchemy.CraftSystem));
        Assert.Equal("Inscribing", ActionProgressBars.CraftLabel(DefInscription.CraftSystem));
        Assert.Equal("Drawing a map", ActionProgressBars.CraftLabel(DefCartography.CraftSystem));
        Assert.Equal("Cooking", ActionProgressBars.CraftLabel(DefCooking.CraftSystem));
    }

    [Fact]
    public void PhaseThreeBarsLastAsLongAsTheStockWaits()
    {
        // a camp is secure 30 s after its entry; a treasure chest is up 25 s after the dig starts; a bow to beg takes 2 s
        Assert.Equal(TimeSpan.FromSeconds(30), Campfire.SecureDelay);
        Assert.Equal(TimeSpan.FromSeconds(25), TreasureMap.DigDuration);
        Assert.Equal(TimeSpan.FromSeconds(2), Begging.BegDelay);
    }

    [Fact]
    public void TheCampBarMatchesTheShardsOwnSecureCampText() =>
        Assert.Equal(WelcomeGuide.SecureCampSeconds, Campfire.SecureDelay.TotalSeconds);

    [Fact]
    public void AClearTakesAwayOnlyTheBarOfTheActionThatStopped()
    {
        var now = new DateTime(2026, 11, 3, 12, 0, 0, DateTimeKind.Utc);

        // a player chopping while the camp is made has both bars; the camp left half made clears the camp's bar, which is up, and nothing else
        var chopping = new Dictionary<string, DateTime> { ["Chopping"] = now.AddSeconds(2) };
        var both = new Dictionary<string, DateTime> { ["Chopping"] = now.AddSeconds(2), [ActionProgressBars.MakingCampLabel] = now.AddSeconds(20) };

        Assert.False(ActionProgressBars.Clears(chopping, ActionProgressBars.MakingCampLabel, now));
        Assert.True(ActionProgressBars.Clears(both, ActionProgressBars.MakingCampLabel, now));

        // a bar that has already run out is not cleared again, and no bar at all is nothing to clear
        var ranOut = new Dictionary<string, DateTime> { [ActionProgressBars.DiggingLabel] = now.AddSeconds(-1) };

        Assert.False(ActionProgressBars.Clears(ranOut, ActionProgressBars.DiggingLabel, now));
        Assert.False(ActionProgressBars.Clears(null, ActionProgressBars.DiggingLabel, now));
    }

    [Fact]
    public void AClearNamesTheBarItTakesAway()
    {
        // the client keeps a bar for each label and stacks them, so the clear carries the label of the bar that goes
        var packet = ActionProgressBars.Packet(7, TimeSpan.Zero, ActionProgressBars.MakingCampLabel, ActionProgressBars.Theme.CampAndRest);

        Assert.Equal(0, packet[9] << 8 | packet[10]);
        Assert.Equal(ActionProgressBars.MakingCampLabel, System.Text.Encoding.ASCII.GetString(packet, 12, packet[11]));
    }

    [Fact]
    public void TheOtherLabelsReadPlainly()
    {
        Assert.Equal("Bandaging", ActionProgressBars.BandagingLabel);
        Assert.Equal("Picking lock", ActionProgressBars.LockpickingLabel);
        Assert.Equal("Cooking", ActionProgressBars.CookingLabel);
        Assert.Equal("Spinning", ActionProgressBars.SpinningLabel);
        Assert.Equal("Making camp", ActionProgressBars.MakingCampLabel);
        Assert.Equal("Digging", ActionProgressBars.DiggingLabel);
        Assert.Equal("Begging", ActionProgressBars.BeggingLabel);
    }

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().ActionProgressBars);
}

/// <summary>What a harvest gave floats up from your character with its picture (plan docs/Action-Progress-Bars-Plan.md, phase 1).</summary>
public class GatheredItemPopupsTests
{
    [Fact]
    public void ThePacketCarriesTheArtTheHueTheAmountAndTheName()
    {
        Assert.Equal(
            new byte[] { 0xBF, 0, 20, 0x00, 0xB5, 0x00, 0x01, 0x02, 0x03, 0x1B, 0xE0, 0x00, 0x00, 0x00, 0x05, 4, (byte)'L', (byte)'o', (byte)'g', (byte)'s' },
            GatheredItemPopups.Packet(0x00010203, 0x1BE0, 0, 5, "Logs")
        );
    }

    [Fact]
    public void TheNameIsShortAndPlainText()
    {
        var packet = GatheredItemPopups.Packet(1, 1, 0, 1, new string('x', 40));

        Assert.Equal(GatheredItemPopups.MaxNameLength, packet[15]);
        Assert.Equal(packet.Length, packet[1] << 8 | packet[2]);
    }

    [Theory]
    [InlineData(typeof(Log), "Logs")]
    [InlineData(typeof(IronOre), "Iron ore")]
    [InlineData(typeof(DullCopperOre), "Dull copper ore")]
    [InlineData(typeof(Fish), "Fish")]
    [InlineData(typeof(BigFish), "Big fish")]
    [InlineData(typeof(Sand), "Sand")]
    [InlineData(typeof(WoodenShield), "Wooden shield")]
    [InlineData(typeof(SackFlour), "Sack flour")]
    public void GatheredItemsHaveShortNames(Type type, string name) => Assert.Equal(name, GatheredItemPopups.NameFor(type));

    [Fact]
    public void TheFlagIsOffUntilTheOwnerSaysActivate() => Assert.False(new DeferredFeatureFlags().GatheredItemPopups);
}
