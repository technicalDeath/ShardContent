using Server;
using Server.Engines.Craft;
using Server.Engines.Harvest;
using Server.Items;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// What you gathered floats up from your character (docs/Action-Progress-Bars-Plan.md, phase 1), behind <c>featureFlags.gatheredItemPopups</c>. The owner
/// (2026-11-02): "For gathering, lets add a little floaty text with the icon of the item that was acquired and a count like "Logs +5" but with an icon".
/// When a harvest puts an item in your pack or at your feet (<see cref="HarvestSystem.ResourceGained"/>), the shard sends extended command 0xB5 to you
/// alone: the item's art and hue, the amount and a short name. The client draws the picture and the count, "+10", rising and fading; the picture takes
/// the place of the word (owner: "Why does it say logs, its supposed to be an icon"), and the name shows only for an item the client has no picture for.
/// The same goes for what you make (owner, 2026-11-02, asked whether crafting should show "Shield +1" too: "yes"): a crafted item as it goes into your
/// pack (<see cref="CraftEvents.Crafted"/>), and a sack of flour from a mill.
/// </summary>
public static class GatheredItemPopups
{
    public const int Command = 0xB5;
    public const int MaxNameLength = 24;

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.GatheredItemPopups == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        HarvestSystem.ResourceGained += OnResourceGained;
        CraftEvents.Crafted += (from, _, item) => Send(from, item.ItemID, item.Hue, item.Amount, item.GetType());
        FlourMillEvents.FlourGiven += (from, flour) => Send(from, flour.ItemID, flour.Hue, flour.Amount, flour.GetType());
    }

    /// <summary>The short name a gathered item pops up with: a few by hand, the rest from the type ("IronOre" is "Iron ore").</summary>
    public static string NameFor(Type type)
    {
        if (type == typeof(Log))
        {
            return "Logs";
        }

        var spaced = HelpGenerators.Spaced(type.Name);
        return spaced[..1] + spaced[1..].ToLowerInvariant();
    }

    /// <summary>0xBF, the length, the command, the serial, the art number, the hue, the amount (two bytes each), then the name as a length byte and ASCII.</summary>
    public static byte[] Packet(uint serial, int itemId, int hue, int amount, string name)
    {
        var text = name.Length > MaxNameLength ? name[..MaxNameLength] : name;
        var packet = new byte[16 + text.Length];
        var count = Math.Clamp(amount, 0, ushort.MaxValue);

        packet[0] = 0xBF;
        packet[1] = (byte)(packet.Length >> 8);
        packet[2] = (byte)packet.Length;
        packet[3] = Command >> 8;
        packet[4] = Command & 0xFF;
        packet[5] = (byte)(serial >> 24);
        packet[6] = (byte)(serial >> 16);
        packet[7] = (byte)(serial >> 8);
        packet[8] = (byte)serial;
        packet[9] = (byte)(itemId >> 8);
        packet[10] = (byte)itemId;
        packet[11] = (byte)(hue >> 8);
        packet[12] = (byte)hue;
        packet[13] = (byte)(count >> 8);
        packet[14] = (byte)count;
        packet[15] = (byte)text.Length;

        for (var i = 0; i < text.Length; i++)
        {
            packet[16 + i] = text[i] is >= ' ' and <= '~' ? (byte)text[i] : (byte)'?';
        }

        return packet;
    }

    private static void OnResourceGained(HarvestSystem system, Mobile from, HarvestedItem gained) =>
        Send(from, gained.ItemId, gained.Hue, gained.Amount, gained.Type);

    private static void Send(Mobile from, int itemId, int hue, int amount, Type type)
    {
        if (Enabled && amount > 0 && from is PlayerMobile { NetState: { } state })
        {
            state.Send(Packet(from.Serial.Value, itemId, hue, amount, NameFor(type)));
        }
    }
}
