using Server;
using Server.Items;
using Server.Misc;
using Server.Mobiles;
using Server.Network;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Gain and cast chances in the spell tooltips (docs/Craft-Chances-Evidence.md), behind <c>featureFlags.spellChances</c>. The owner (2026-10-17), after
/// the craft menu tooltips: "Also add this info to spell tooltips". Extended command 0xAF carries, for each Magery spell, the chance one cast from a
/// book raises Magery and the chance it succeeds; the client adds them to the spell's tooltip in the spellbook and on a spell icon dragged out of
/// it. It is sent at login, when a spellbook opens, and after a Magery check changes the numbers. Nothing changes how casting works.
/// </summary>
public static class SpellChancesService
{
    public const int Command = 0xAF;

    /// <summary>The Magery spells, server ids 0 to 63; the packet numbers them as the client does, from 1.</summary>
    public const int MagerySpells = 64;

    /// <summary>How long after login the numbers are sent, so the hotbar and loose spell icons have them from the start.</summary>
    public static readonly TimeSpan LoginDelay = TimeSpan.FromSeconds(3);

    private static readonly Dictionary<Serial, byte[]> LastSent = [];
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.SpellChances == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Spellbook.Displayed += (to, _) => Send(to, true);
        // at the moment of connection the client is still entering the world and drops the command: send once it is in
        EventSink.Connected += m => Server.Timer.DelayCall(LoginDelay, () => Send(m, true));
        EventSink.Disconnected += m => LastSent.Remove(m.Serial);
        SkillEvents.SkillUsed += OnSkillUsed;
    }

    /// <summary>0xBF, the length, the command, the count, then per spell its client number (2 bytes), a gain byte and a cast byte.</summary>
    public static byte[] Packet(byte[] gains, byte[] casts)
    {
        var count = gains.Length;
        var length = 7 + 4 * count;
        var packet = new byte[length];
        packet[0] = 0xBF;
        packet[1] = (byte)(length >> 8);
        packet[2] = (byte)length;
        packet[3] = Command >> 8;
        packet[4] = Command & 0xFF;
        packet[5] = (byte)(count >> 8);
        packet[6] = (byte)count;

        for (var i = 0; i < count; i++)
        {
            var at = 7 + 4 * i;
            var number = i + 1;
            packet[at] = (byte)(number >> 8);
            packet[at + 1] = (byte)number;
            packet[at + 2] = gains[i];
            packet[at + 3] = casts[i];
        }

        return packet;
    }

    // a Magery check may have moved a number: send after the gain is applied, and only when something changed
    private static void OnSkillUsed(Mobile m, Skill skill, bool success)
    {
        if (Enabled && m is PlayerMobile && skill.SkillName == SkillName.Magery)
        {
            Server.Timer.DelayCall(() => Send(m, false));
        }
    }

    private static void Send(Mobile m, bool always)
    {
        if (!Enabled || m is not PlayerMobile player || player.NetState is not { } state || state.CannotSendPackets())
        {
            return;
        }

        var gains = new byte[MagerySpells];
        var casts = new byte[MagerySpells];

        for (var id = 0; id < MagerySpells; id++)
        {
            if (SpellRegistry.NewSpell(id, player, null) is not { } spell)
            {
                gains[id] = casts[id] = CraftChancesService.None;
                continue;
            }

            spell.GetCastSkills(out var min, out var max);
            casts[id] = (byte)ScrollChanceService.Percent(player.Skills[spell.CastSkill].Value, min, max);
            gains[id] = CraftChancesService.Percent(CraftChancesService.GainChanceFor(player, spell.CastSkill, min, max), true);
        }

        var packet = Packet(gains, casts);

        if (!always && LastSent.TryGetValue(player.Serial, out var last) && last.AsSpan().SequenceEqual(packet))
        {
            return;
        }

        LastSent[player.Serial] = packet;
        state.Send(packet);
    }
}
