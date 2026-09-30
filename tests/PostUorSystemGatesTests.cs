using BritanniaRenaissance.Content;
using Server.Engines.ConPVP;
using Server.Engines.Virtues;
using Server.Gumps;
using Server.Items;
using Xunit;

namespace BritanniaRenaissance.Content.Tests;

public class PostUorSystemGatesTests
{
    [Fact]
    public void ConfigureDisablesEveryGatedStockSystem()
    {
        VirtueGump.Enabled = true;
        BaseWeapon.PoisonCorrosionEnabled = true;
        DuelContext.DuelingEnabled = true;
        ResurrectGump.StatLossEnabled = true;

        PostUorSystemGates.Configure();

        Assert.False(VirtueGump.Enabled);
        Assert.False(BaseWeapon.PoisonCorrosionEnabled);
        Assert.False(DuelContext.DuelingEnabled);
        Assert.False(ResurrectGump.StatLossEnabled);
    }
}
