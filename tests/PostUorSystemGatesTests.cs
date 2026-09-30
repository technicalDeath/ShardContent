using BritanniaRenaissance.Content;
using Server.Engines.ConPVP;
using Server.Engines.Virtues;
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

        PostUorSystemGates.Configure();

        Assert.False(VirtueGump.Enabled);
        Assert.False(BaseWeapon.PoisonCorrosionEnabled);
        Assert.False(DuelContext.DuelingEnabled);
    }
}
