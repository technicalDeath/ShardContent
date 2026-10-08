using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Notifies players when their settled position crosses a Hot Zone boundary (outdoor or dungeon).</summary>
public static class OutdoorHotZoneBoundaryService
{
    private static readonly Dictionary<Serial, string?> ObservedRegions = new();
    private static readonly HashSet<Serial> Pending = [];
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        PlayerMobile.PositionChanged += ScheduleObservation;
        EventSink.Connected += OnConnected;
        EventSink.Disconnected += OnDisconnected;
    }

    public static readonly TimeSpan LoginObservationDelay = TimeSpan.FromSeconds(3);

    private static void OnConnected(Mobile mobile)
    {
        // The client drops system messages that arrive before it has entered the world.
        if (mobile is PlayerMobile player)
        {
            ScheduleObservation(player, LoginObservationDelay);
        }
    }

    private static void OnDisconnected(Mobile mobile)
    {
        if (mobile is PlayerMobile player)
        {
            ObservedRegions.Remove(player.Serial);
        }
    }

    private static void ScheduleObservation(PlayerMobile player) => ScheduleObservation(player, TimeSpan.Zero);

    private static void ScheduleObservation(PlayerMobile player, TimeSpan delay)
    {
        if (player.Deleted || player.NetState is null || player.AccessLevel != AccessLevel.Player ||
            !Pending.Add(player.Serial))
        {
            return;
        }

        // Location and map callbacks can run during one teleport or house-design relocation.
        // Observe after those callbacks settle so only the final position produces a message.
        Server.Timer.DelayCall(delay, () => Observe(player));
    }

    private static void Observe(PlayerMobile player)
    {
        Pending.Remove(player.Serial);
        if (player.Deleted || player.NetState is null)
        {
            ObservedRegions.Remove(player.Serial);
            return;
        }

        if (!OutdoorHotZonePolicy.Enabled)
        {
            ObservedRegions.Remove(player.Serial);
            return;
        }

        var current = OutdoorHotZonePolicy.GetRegionName(player);
        ObservedRegions.TryGetValue(player.Serial, out var previous);
        foreach (var message in DescribeTransition(previous, current))
        {
            player.SendMessage(message);
        }

        ObservedRegions[player.Serial] = current;
    }

    public static IEnumerable<string> DescribeTransition(string? previous, string? current) =>
        DescribeTransition(previous, current, OutdoorHotZonePolicy.IsDungeonRegion);

    public static IEnumerable<string> DescribeTransition(string? previous, string? current, Func<string, bool> isDungeon)
    {
        if (string.Equals(previous, current, StringComparison.OrdinalIgnoreCase))
        {
            yield break;
        }

        if (previous is not null)
        {
            // Moving straight into another Hot Zone (Hythloth's entrance onto Fire Island) keeps Hot rules in force.
            yield return current is null
                ? $"You have left {DisplayName(previous)}. Hot Zone initiation no longer applies here; existing lawful fights continue."
                : $"You have left {DisplayName(previous)}.";
        }

        if (current is not null)
        {
            var kind = isDungeon(current) ? "a PvP Hot Zone" : "an outdoor PvP Hot Zone";
            yield return $"You have entered {DisplayName(current)}, {kind}. Players may initiate combat freely here. Killing an ordinary blue is still murder: the victim can report you for a murder count.";
        }
    }

    public static string DisplayName(string region) => region switch
    {
        "FireIsland" => "Fire Island",
        "BuccaneersDenIsland" => "Buccaneer's Den island",
        _ => region
    };
}
