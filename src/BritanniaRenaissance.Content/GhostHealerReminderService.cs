using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The war-mode reminder for ghosts near a healer (docs/Ghost-Healer-Reminder-Evidence.md), behind <c>featureFlags.ghostHealerReminder</c>. The owner (2026-10-16):
/// "we should just remind players to enter war mode to get ressurected when they are near a healer", "The warning should be if you're not in war mode".
/// Stock: a living mobile sees a ghost only in war mode (<c>Mobile.CanSee</c>), and a healer offers a resurrection only when a ghost it can see steps into its
/// 4-tile range from outside it (<c>BaseHealer.OnMovement</c>), so a ghost in peace mode beside a healer waits forever, and one that turns war mode on while
/// already beside it must still step back and walk up. The rules stay stock; the ghost is told, at most every <see cref="Interval"/>, while it stays in peace
/// mode within <see cref="Range"/> tiles of a healer: when it moves, and once a few seconds after it dies.
/// </summary>
public static class GhostHealerReminderService
{
    public const int Range = 8;

    public const string Text =
        "A healer cannot see a ghost in peace mode. Press Tab for war mode, then walk up to the healer from a few steps away to be offered a resurrection.";

    public static readonly TimeSpan Interval = TimeSpan.FromSeconds(30);

    /// <summary>After a death the client shows the death screen first; a line sent at once would scroll past unread.</summary>
    public static readonly TimeSpan AfterDeath = TimeSpan.FromSeconds(4);

    private static bool _configured;
    private static readonly Dictionary<PlayerMobile, DateTime> LastReminded = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.GhostHealerReminder == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.PositionChanged += player => Check(player);
        PlayerMobile.PlayerDeathHandler += player => Server.Timer.DelayCall(AfterDeath, () => Check(player));
        EventSink.Logout += m =>
        {
            if (m is PlayerMobile player)
            {
                LastReminded.Remove(player);
            }
        };
    }

    /// <summary>The rule, free of the game: a ghost in peace mode near a healer, not reminded within the interval.</summary>
    public static bool ShouldRemind(bool enabled, bool dead, bool warMode, bool healerNearby, DateTime? last, DateTime now) =>
        enabled && dead && !warMode && healerNearby && (last is null || now - last.Value >= Interval);

    private static void Check(PlayerMobile player)
    {
        if (!Enabled || player.Deleted || player.Alive || player.Warmode || player.NetState is null || player.Map is null || player.Map == Map.Internal)
        {
            return;
        }

        var now = Core.Now;
        var last = LastReminded.TryGetValue(player, out var at) ? at : (DateTime?)null;

        if (ShouldRemind(true, true, false, HealerNearby(player), last, now))
        {
            LastReminded[player] = now;
            player.SendMessage(0x35, Text);
        }
    }

    private static bool HealerNearby(PlayerMobile ghost)
    {
        foreach (var healer in ghost.GetMobilesInRange<BaseHealer>(Range))
        {
            if (healer.Alive && !healer.Deleted)
            {
                return true;
            }
        }

        return false;
    }
}
