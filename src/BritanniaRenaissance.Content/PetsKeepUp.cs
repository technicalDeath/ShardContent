using Server.Mobiles;
using CalcMoves = Server.Movement.Movement;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Following pets keep up with a running master (docs/Pack-Animals-Evidence.md), behind <c>featureFlags.petsKeepUp</c>. Every animal a UOR tamer can
/// own is in the "Medium" speed tier (npc-speeds.json: 0.45 s a step), slower than a player walking (0.4 s) or running on foot (0.2 s), and before AOS
/// a following pet has no catch-up pace (<see cref="BaseCreature.FollowMoveSpeed" /> is 0). Once more than <c>RangePerception</c> (16) tiles behind,
/// a following pet stands still for good (BaseAI FollowTarget), so a pack horse or a tamer's pets were left behind on any walk. The AOS-only pace
/// came from RunUO, with no publish behind it. The owner chose this on 2026-11-01: a pet closing on its master steps at the run-on-foot pace
/// (<c>movement.delay.runFoot</c>). A pet that is faster already, or the AOS cap, is left alone; nothing changes outside the follow order.
/// </summary>
public static class PetsKeepUp
{
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.PetsKeepUp == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        var previous = BaseCreature.FollowMoveSpeedFilter;
        BaseCreature.FollowMoveSpeedFilter = (creature, stock) =>
        {
            var pace = previous?.Invoke(creature, stock) ?? stock;
            return Pace(Enabled, pace, CalcMoves.RunFootDelay);
        };
    }

    /// <summary>The follow pace in seconds a step: the stock one when it has a cap already (AOS) or the flag is off, else the run-on-foot delay.</summary>
    public static double Pace(bool enabled, double stock, int runFootMs) => !enabled || stock > 0 || runFootMs <= 0 ? stock : runFootMs / 1000.0;
}
