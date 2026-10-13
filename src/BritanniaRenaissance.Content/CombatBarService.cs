using System.Buffers;
using Server;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The server half of the combat bar's durability gauge (docs/Combat-Bar-Evidence.md), behind <c>featureFlags.combatBar</c>. The era server sends no item properties, so the
/// client cannot know how worn a weapon or shield is: it asks with extended command 0xA9 and the serials of the items in its three equipment slots, and gets the same command
/// back with the hit points and maximum hit points of each one that has them. An item that is not the asker's, or has no durability, gets no answer.
/// </summary>
public static class CombatBarService
{
    public const int Command = 0xA9;
    public const int MaxRequest = 8;

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CombatBar == true;

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        IncomingExtendedCommandPackets.RegisterExtended(Command, true, &OnRequest);
    }

    /// <summary>The hit points and maximum of a weapon, armor or shield; (0, 0) for anything else.</summary>
    public static (int Hits, int Max) DurabilityOf(Item item) => item switch
    {
        BaseWeapon weapon => (weapon.HitPoints, weapon.MaxHitPoints),
        BaseArmor armor => (armor.HitPoints, armor.MaxHitPoints),
        _ => (0, 0)
    };

    private static void OnRequest(NetState state, SpanReader reader)
    {
        if (!Enabled || state.Mobile is not PlayerMobile player)
        {
            return;
        }

        var count = Math.Min((int)reader.ReadByte(), MaxRequest);
        var found = new List<(uint Serial, ushort Hits, ushort Max)>(count);

        for (var i = 0; i < count && reader.Remaining >= 4; i++)
        {
            var serial = reader.ReadUInt32();

            if (World.FindItem((Serial)serial) is { Deleted: false } item && item.IsChildOf(player) && DurabilityOf(item) is var (hits, max) && max > 0)
            {
                found.Add((serial, (ushort)Math.Clamp(hits, 0, ushort.MaxValue), (ushort)Math.Clamp(max, 0, ushort.MaxValue)));
            }
        }

        if (found.Count > 0)
        {
            state.Send(Reply(found));
        }
    }

    /// <summary>The reply as raw bytes: 0xBF, the length, the command, the count, then a serial, the hit points and the maximum for each.</summary>
    public static byte[] Reply(IReadOnlyList<(uint Serial, ushort Hits, ushort Max)> items)
    {
        var length = 6 + items.Count * 8;
        var buffer = new byte[length];

        buffer[0] = 0xBF;
        buffer[1] = (byte)(length >> 8);
        buffer[2] = (byte)length;
        buffer[3] = (byte)(Command >> 8);
        buffer[4] = (byte)Command;
        buffer[5] = (byte)items.Count;

        var at = 6;

        foreach (var (serial, hits, max) in items)
        {
            buffer[at++] = (byte)(serial >> 24);
            buffer[at++] = (byte)(serial >> 16);
            buffer[at++] = (byte)(serial >> 8);
            buffer[at++] = (byte)serial;
            buffer[at++] = (byte)(hits >> 8);
            buffer[at++] = (byte)hits;
            buffer[at++] = (byte)(max >> 8);
            buffer[at++] = (byte)max;
        }

        return buffer;
    }
}
