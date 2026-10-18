using Server;
using Server.Items;
using Server.Misc;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Stamina numbers over your head (docs/Stamina-Numbers-Evidence.md), behind <c>featureFlags.staminaNumbers</c>. The owner (2026-10-16): "stamina lost should
/// show up alongside hitpoint floaty damage with an option for players to turn it off. And also stamina from refresh potions should have floaty text, also with
/// an option to turn it off", "This way players can see their stamina loss when they fight vs maces". There is no stamina packet, so the shard sends extended
/// command 0xAD to the player whose stamina changed, and to nobody else:
/// <list type="bullet">
/// <item><b>Lost to a hit</b>: the hit's fatigue (<see cref="StaminaSystem.DamageFatigueApplied"/>) and a mace's or staff's drain
/// (<see cref="BaseWeapon.HitDrainedStamina"/>), added up over the game tick the hit lands in, so one hit shows one number.</item>
/// <item><b>Restored by a refresh potion</b> (<see cref="BaseRefreshPotion.StaminaRestored"/>).</item>
/// </list>
/// The amounts are what really changed, after the bar's ends. The client draws them in blue beside the damage numbers, with a switch for each in Options.
/// </summary>
public static class StaminaNumbersService
{
    public const int Command = 0xAD;
    public const byte Lost = 0;
    public const byte Restored = 1;

    private static bool _configured;
    private static bool _flushQueued;
    private static readonly Dictionary<Mobile, int> PendingLoss = [];

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.StaminaNumbers == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        StaminaSystem.DamageFatigueApplied += (m, amount) => OnLost(m, amount);
        BaseWeapon.HitDrainedStamina += (_, defender, amount) => OnLost(defender, amount);
        BaseRefreshPotion.StaminaRestored += OnRestored;
    }

    /// <summary>The change as raw bytes: 0xBF, the length, the command, the serial, the kind (0 lost to a hit, 1 restored by a potion), the amount (two bytes).</summary>
    public static byte[] Packet(uint serial, byte kind, int amount)
    {
        var value = Math.Clamp(amount, 0, ushort.MaxValue);

        return
        [
            0xBF, 0, 12, Command >> 8, Command & 0xFF,
            (byte)(serial >> 24), (byte)(serial >> 16), (byte)(serial >> 8), (byte)serial,
            kind, (byte)(value >> 8), (byte)value
        ];
    }

    /// <summary>Whether a change is shown: the flag is on, it is a player with a client, and something changed.</summary>
    public static bool Shows(bool enabled, bool isPlayerWithClient, int amount) => enabled && isPlayerWithClient && amount > 0;

    private static void OnLost(Mobile m, int amount)
    {
        if (!Shows(Enabled, m is PlayerMobile { NetState: not null }, amount))
        {
            return;
        }

        PendingLoss[m] = PendingLoss.GetValueOrDefault(m) + amount;

        if (!_flushQueued)
        {
            _flushQueued = true;
            Server.Timer.DelayCall(Flush);
        }
    }

    private static void Flush()
    {
        _flushQueued = false;

        foreach (var (m, amount) in PendingLoss)
        {
            if (!m.Deleted && m.Alive)
            {
                m.NetState?.Send(Packet(m.Serial.Value, Lost, amount));
            }
        }

        PendingLoss.Clear();
    }

    private static void OnRestored(Mobile m, int amount)
    {
        if (Shows(Enabled, m is PlayerMobile { NetState: not null }, amount))
        {
            m.NetState.Send(Packet(m.Serial.Value, Restored, amount));
        }
    }
}
