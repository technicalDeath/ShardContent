using System.Buffers;
using Server;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The corpse window's Carve button (owner, 2026-10-18: "for any corpse that can be carved, put a carve button right in the corpse grid view", and "have the
/// carve button find a suitable tool in the players pack automatically"), behind <c>featureFlags.corpseCarveButton</c>. The client's grid window for a corpse
/// asks with extended command 0xB0 (mode 0) whether the corpse can be carved, and shows the button when the answer is yes; the button sends mode 1 and the
/// server carves with the first blade it finds (a knife or sword in the hands, then one in the pack) exactly as using that blade on the corpse would, so the
/// criminal-act window, the messages and the yields are stock. The answer is sent again after a carve, so the button goes away.
/// </summary>
public static class CorpseCarveButton
{
    public const int Command = 0xB0;
    public const byte Ask = 0;
    public const byte Carve = 1;

    public const string NoBlade = "You need a knife or a sword in your pack to carve.";

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CorpseCarveButton == true;

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        IncomingExtendedCommandPackets.RegisterExtended(Command, true, &OnRequest);
    }

    /// <summary>
    /// Whether carving would yield anything, the stock rules of <c>Corpse.Carve</c> and <c>BaseCreature.OnCarve</c>: not carved yet, and either a body that
    /// carves into parts or a creature (not summoned, not a bonded pet, not animated) with feathers, wool, meat, hides or scales.
    /// </summary>
    public static bool Carvable(bool carved, bool hasOwner, bool humanBody, bool creature, int yields, bool summoned, bool bonded, bool animated) =>
        !carved && hasOwner && (humanBody || creature && yields > 0 && !summoned && !bonded && !animated);

    public static bool Carvable(Corpse corpse)
    {
        var owner = corpse.Owner;
        var bc = owner as BaseCreature;
        var yields = bc is null ? 0 : bc.Feathers + bc.Wool + bc.Meat + bc.Hides + bc.Scales;

        return Carvable(
            corpse.Carved, owner is not null, ((Body)corpse.Amount).IsHuman && corpse.ItemID == 0x2006, bc is not null, yields, bc?.Summoned == true,
            bc?.IsBonded == true, corpse.Animated
        );
    }

    /// <summary>A knife or sword in the hands first, then the first one in the pack.</summary>
    public static Item? FindBlade(Mobile m)
    {
        foreach (var layer in new[] { Layer.OneHanded, Layer.TwoHanded })
        {
            var held = m.FindItemOnLayer(layer);

            if (held is BaseKnife or BaseSword)
            {
                return held;
            }
        }

        return m.Backpack?.FindItemByType<BaseKnife>() ?? (Item?)m.Backpack?.FindItemByType<BaseSword>();
    }

    private static void OnRequest(NetState state, SpanReader reader)
    {
        if (!Enabled || state.Mobile is not PlayerMobile player || reader.Remaining < 5)
        {
            return;
        }

        var serial = reader.ReadUInt32();
        var mode = reader.ReadByte();

        if (World.FindItem((Serial)serial) is not Corpse { Deleted: false } corpse || corpse.Map != player.Map)
        {
            return;
        }

        if (mode == Carve && Carvable(corpse))
        {
            if (!player.InRange(corpse.GetWorldLocation(), 2))
            {
                player.SendLocalizedMessage(500446); // That is too far away.
            }
            else if (FindBlade(player) is not { } blade)
            {
                player.SendMessage(NoBlade);
            }
            else
            {
                corpse.Carve(player, blade);
            }
        }

        state.Send(Reply(serial, Carvable(corpse)));
    }

    /// <summary>0xBF, the length, the command, the corpse serial, and 1 when it can be carved.</summary>
    public static byte[] Reply(uint serial, bool carvable) =>
    [
        0xBF, 0, 10, Command >> 8, Command & 0xFF, (byte)(serial >> 24), (byte)(serial >> 16), (byte)(serial >> 8), (byte)serial, carvable ? (byte)1 : (byte)0
    ];
}
