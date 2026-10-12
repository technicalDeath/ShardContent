using System.Buffers;
using Server;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The server half of the shard's top bar (docs/Menu-Bar-Evidence.md), behind <c>featureFlags.menuBar</c>.
/// At login the server sends extended command 0xA8 with a two-byte mask. Bit 15 says "use the shard bar" (the client keeps the stock bar until it sees it); the other bits
/// say which shard buttons to show, one per live feature, so a button never appears for a feature that is off.
/// </summary>
public static class MenuBarService
{
    public const int Command = 0xA8;

    public const ushort ShardBar = 1 << 15;
    public const ushort Camp = 1 << 1;
    public const ushort GuildChat = 1 << 2;
    public const ushort About = 1 << 3;

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.MenuBar == true;

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        EventSink.Connected += OnConnected;
        IncomingExtendedCommandPackets.RegisterExtended(Command, true, &OnRequest);
    }

    /// <summary>The client asks once its top bar is made; the answer is the same as at login.</summary>
    private static void OnRequest(NetState state, SpanReader reader) => Send(state.Mobile);

    /// <summary>The mask for a set of flags: 0 when the bar is off (nothing is sent), else the shard bar bit plus one bit per live feature.</summary>
    public static ushort MaskFor(DeferredFeatureFlags flags)
    {
        if (!flags.MenuBar)
        {
            return 0;
        }

        ushort mask = ShardBar;

        if (flags.CampingTravel)
        {
            mask |= Camp;
        }

        if (flags.GuildChat)
        {
            mask |= GuildChat;
        }

        if (flags.HelpGumps)
        {
            mask |= About;
        }

        return mask;
    }

    /// <summary>The command as raw bytes: 0xBF, the length, the command, then the mask.</summary>
    public static byte[] Packet(ushort mask) =>
    [
        0xBF, 0, 7, (byte)(Command >> 8), (byte)Command, (byte)(mask >> 8), (byte)mask
    ];

    private static void OnConnected(Mobile mobile) => Send(mobile);

    private static void Send(Mobile mobile)
    {
        if (!Enabled || mobile is not PlayerMobile { NetState: { } state } || ShardRulesConfiguration.Settings is not { } rules)
        {
            return;
        }

        state.Send(Packet(MaskFor(rules.FeatureFlags)));
    }
}
