using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>Notifies players when their settled position crosses an outdoor Hot boundary.</summary>
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

    private static void OnConnected(Mobile mobile)
    {
        if (mobile is PlayerMobile player)
        {
            ScheduleObservation(player);
        }
    }

    private static void OnDisconnected(Mobile mobile)
    {
        if (mobile is PlayerMobile player)
        {
            ObservedRegions.Remove(player.Serial);
        }
    }

    private static void ScheduleObservation(PlayerMobile player)
    {
        if (player.Deleted || player.NetState is null || player.AccessLevel != AccessLevel.Player ||
            !Pending.Add(player.Serial))
        {
            return;
        }

        // Location and map callbacks can run during one teleport or house-design relocation.
        // Observe after those callbacks settle so only the final position produces a message.
        Server.Timer.DelayCall(TimeSpan.Zero, () => Observe(player));
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

    public static IEnumerable<string> DescribeTransition(string? previous, string? current)
    {
        if (string.Equals(previous, current, StringComparison.OrdinalIgnoreCase))
        {
            yield break;
        }

        if (previous is not null)
        {
            yield return $"You have left {DisplayName(previous)}. Hot Zone initiation no longer applies here; existing lawful fights continue.";
        }

        if (current is not null)
        {
            yield return $"You have entered {DisplayName(current)}, an outdoor PvP Hot Zone. Players may initiate combat freely here. Murdering an ordinary blue still adds a murder count and 24 hours of red time.";
        }
    }

    private static string DisplayName(string region) => region switch
    {
        "FireIsland" => "Fire Island",
        "BuccaneersDenIsland" => "Buccaneer's Den island",
        _ => region
    };
}
