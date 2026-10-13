using Server;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Damage and heal numbers over heads (docs/Combat-Numbers-Evidence.md). Pure display: neither changes a rule, and neither goes to anyone who could not already see the result.
/// <list type="bullet">
/// <item><b>Damage</b> (<c>featureFlags.damageNumbers</c>). ModernUO has a stock switch for the damage packet (<c>Mobile.VisibleDamageType</c>) that is on only for AOS servers. With the flag
/// on it is set to <c>Related</c>: the number goes to the client of whoever took the damage and the client of whoever dealt it (or of the master of a pet that did either), nobody else.</item>
/// <item><b>Heal</b> (<c>featureFlags.healNumbers</c>). There is no heal packet in the protocol, so the shard sends extended command 0xAB when <c>Mobile.HealApplied</c> fires (a bandage, a
/// potion or a spell): the mobile healed, and the hit points really restored. It goes to the healed player and to the healer, the same two parties as for damage.</item>
/// </list>
/// The client draws the damage in red (yellow on yourself) and the heal in green, and has a switch for both in Options.
/// </summary>
public static class CombatNumbersService
{
    public const int HealCommand = 0xAB;

    private static bool _configured;

    public static bool DamageEnabled => ShardRulesConfiguration.Settings?.FeatureFlags.DamageNumbers == true;

    public static bool HealEnabled => ShardRulesConfiguration.Settings?.FeatureFlags.HealNumbers == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Mobile.HealApplied += OnHealApplied;

        // ExpansionConfiguration sets the stock value while the server configures; the shard's word comes after it
        EventSink.ServerStarted += ApplyDamageSetting;
    }

    private static void ApplyDamageSetting()
    {
        if (DamageEnabled)
        {
            Mobile.VisibleDamageType = VisibleDamageType.Related;
        }
    }

    /// <summary>The heal as raw bytes: 0xBF, the length, the command, the serial of the mobile healed, the hit points restored (two bytes).</summary>
    public static byte[] HealPacket(uint serial, int amount)
    {
        var restored = Math.Clamp(amount, 0, ushort.MaxValue);

        return
        [
            0xBF, 0, 11, HealCommand >> 8, HealCommand & 0xFF,
            (byte)(serial >> 24), (byte)(serial >> 16), (byte)(serial >> 8), (byte)serial,
            (byte)(restored >> 8), (byte)restored
        ];
    }

    private static void OnHealApplied(Mobile patient, Mobile? healer, int amount)
    {
        if (!HealEnabled || amount <= 0)
        {
            return;
        }

        var patientState = patient.NetState;
        var healerState = healer?.NetState;

        // a pet's master sees the heal as the healed pet's: the healer is usually that master already
        if (patientState is null && patient is BaseCreature { ControlMaster.NetState: { } masterState })
        {
            patientState = masterState;
        }

        if (patientState is null && healerState is null)
        {
            return;
        }

        var packet = HealPacket(patient.Serial.Value, amount);

        patientState?.Send(packet);

        if (healerState is not null && !ReferenceEquals(healerState, patientState))
        {
            healerState.Send(packet);
        }
    }
}
