using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A criminal ghost is told how long to wait (docs/Criminal-Ghost-Notice-Evidence.md), behind <c>featureFlags.criminalGhostNotice</c>. Stock, a healer
/// refuses a criminal with only "Thou art a criminal. I shall not resurrect thee." and nothing says the flag ends <see cref="Mobile.ExpireCriminalDelay"/>
/// (2 minutes) after the last criminal act. The owner (2026-10-17) chose both: the refusal adds the time left (<see cref="BaseHealer.RefusedCriminal"/>),
/// and a ghost is told when the flag ends (<see cref="PlayerMobile.CriminalChanged"/>). Every player, not only new ones.
/// </summary>
public static class CriminalGhostNotice
{
    /// <summary>A healer refuses again on every step the ghost takes into its reach, so the wait line is said at most this often.</summary>
    public static readonly TimeSpan Interval = TimeSpan.FromSeconds(10);

    public const string Ended = "You are no longer a criminal. A healer will bring you back now.";

    private static bool _configured;
    private static readonly Dictionary<PlayerMobile, DateTime> LastTold = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CriminalGhostNotice == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        BaseHealer.RefusedCriminal += OnRefused;
        PlayerMobile.CriminalChanged += OnCriminalChanged;
        EventSink.Logout += m =>
        {
            if (m is PlayerMobile player)
            {
                LastTold.Remove(player);
            }
        };
    }

    /// <summary>The time left, rounded up to the next 10 seconds so it never promises too soon: "1 minute 40 seconds", "30 seconds".</summary>
    public static string Remaining(TimeSpan left)
    {
        var seconds = Math.Max(10, (int)Math.Ceiling(left.TotalSeconds / 10.0) * 10);
        var minutes = seconds / 60;
        var rest = seconds % 60;
        var m = minutes == 1 ? "1 minute" : $"{minutes} minutes";
        return minutes == 0 ? $"{rest} seconds" : rest == 0 ? m : $"{m} {rest} seconds";
    }

    public static string WaitText(TimeSpan left) =>
        $"You will be a criminal for about {Remaining(left)} more. Come back then, and a healer will bring you back.";

    public static TimeSpan Left(DateTime since, DateTime now, TimeSpan delay) => since + delay - now;

    private static void OnRefused(BaseHealer healer, Mobile m)
    {
        if (!Enabled || m is not PlayerMobile { Alive: false, NetState: not null } ghost || !ghost.Criminal)
        {
            return;
        }

        var now = Core.Now;

        if (LastTold.TryGetValue(ghost, out var last) && now - last < Interval)
        {
            return;
        }

        LastTold[ghost] = now;
        ghost.SendMessage(0x35, WaitText(Left(ghost.CriminalSince, now, Mobile.ExpireCriminalDelay)));
    }

    private static void OnCriminalChanged(PlayerMobile player, bool criminal)
    {
        if (Enabled && !criminal && !player.Alive && !player.Deleted && player.NetState is not null)
        {
            player.SendMessage(0x35, Ended);
        }
    }
}
