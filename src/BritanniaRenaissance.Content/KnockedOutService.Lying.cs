using Server;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A Knocked Out player lies on the ground like a corpse (owner ruling 2026-10-07). The server marks the player with a packet-flag bit the
/// protocol leaves unused for mobiles (0x20) and the shard's client fork draws a marked human lying down, so the look survives every re-send,
/// range entry, login and teleport with nothing to refresh. A stock client ignores the bit and shows the player standing.
/// </summary>
public static partial class KnockedOutService
{
    /// <summary>The mobile packet-flag bit the shard's client reads as "lying down". Stock flags use 0x01 to 0x10, 0x40 and 0x80.</summary>
    public const int LyingFlag = 0x20;

    private static readonly HashSet<PlayerMobile> Lying = [];
    private static bool _lyingConfigured;

    public static bool IsLyingDown(PlayerMobile player) => Lying.Contains(player);

    /// <summary>The bits a player adds to the packet flags the engine sends. It runs for every observer on every move, so it stays O(1).</summary>
    public static int PacketFlagsFor(PlayerMobile player) => Lying.Contains(player) ? LyingFlag : 0;

    /// <summary>
    /// How long a player knocked off a mount cannot remount: what is left of the Knocked Out, at least one second.
    /// </summary>
    public static TimeSpan MountBlockDuration(DateTime? untilUtc, DateTime nowUtc) =>
        untilUtc is { } until && until - nowUtc > TimeSpan.FromSeconds(1) ? until - nowUtc : TimeSpan.FromSeconds(1);

    private static void ConfigureLying()
    {
        if (_lyingConfigured)
        {
            return;
        }

        _lyingConfigured = true;
        PlayerMobile.ExtraPacketFlagsHandler = PacketFlagsFor;
    }

    private static void StartLying(PlayerMobile player)
    {
        DropFromMount(player);

        if (Lying.Add(player))
        {
            player.Delta(MobileDelta.Flags);
        }
    }

    private static void StopLying(PlayerMobile player)
    {
        if (Lying.Remove(player) && !player.Deleted)
        {
            player.Delta(MobileDelta.Flags);
        }
    }

    /// <summary>A rider falls off: the lying look is drawn for the human alone, and a mount drawn under it would look wrong.</summary>
    private static void DropFromMount(PlayerMobile player)
    {
        if (player.Mount is null)
        {
            return;
        }

        player.SetMountBlock(BlockMountType.Dazed, MountBlockDuration(GetUntilUtc(player), Core.Now.ToUniversalTime()), true);
        player.SendLocalizedMessage(1040023); // You have been knocked off of your mount!
    }
}
