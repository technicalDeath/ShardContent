using Server.Engines.ConPVP;
using Server.Engines.Virtues;
using Server.Items;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Alpha 3 Phase L rulings (2026-09-30, <c>Alpha-3-Stock-Default-Audit.md</c> items 3/4/9) that turn
/// off stock ModernUO systems the owner ruled out for this shard, at each system's own narrowest
/// gameplay choke point rather than duplicating its logic here.
/// </summary>
public static class PostUorSystemGates
{
    public static void Configure()
    {
        VirtueGump.Enabled = false;
        BaseWeapon.PoisonCorrosionEnabled = false;
        DuelContext.DuelingEnabled = false;
    }
}
