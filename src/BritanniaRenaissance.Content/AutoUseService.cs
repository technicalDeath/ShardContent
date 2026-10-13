using System.Buffers;
using Server;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The server half of the bars' auto-use options (docs/Auto-Use-Evidence.md), behind <c>featureFlags.autoUse</c>. The client is not told how strong a poison is (only that the
/// player is poisoned), so for the auto-cure it asks, with extended command 0xAA and nothing else, and the server answers with the cure potion to drink: the weakest cure potion
/// in the asker's backpack that is certain to cure this poison, or failing that the one with the best chance. The answer carries the potion's serial and the chance in percent,
/// or a count of 0 when the asker is not poisoned, has no cure potion that could work, or the flag is off. The heal, refresh and bandage rules need nothing from the server.
/// </summary>
public static class AutoUseService
{
    public const int Command = 0xAA;

    /// <summary>The three cure potions, weakest first.</summary>
    public enum Cure { Lesser, Regular, Greater }

    /// <summary>
    /// The chance, in percent, that each cure cures a poison of each level (0 lesser, 1 regular, 2 greater, 3 deadly, 4 lethal). These are the era's values, the ones
    /// LesserCurePotion, CurePotion and GreaterCurePotion carry for a server that is not an AOS one.
    /// </summary>
    private static readonly int[][] Chances =
    [
        [75, 50, 15, 0, 0],      // Lesser Cure Potion
        [100, 75, 50, 15, 0],    // Cure Potion
        [100, 100, 100, 75, 25]  // Greater Cure Potion
    ];

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.AutoUse == true;

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        IncomingExtendedCommandPackets.RegisterExtended(Command, true, &OnRequest);
    }

    public static int ChanceOf(Cure cure, int poisonLevel) =>
        poisonLevel is >= 0 and <= 4 ? Chances[(int)cure][poisonLevel] : 0;

    /// <summary>The cure to drink for a poison of this level from the ones the player has: the weakest that is certain, else the best chance, else none (nothing here could work).</summary>
    public static Cure? Choose(int poisonLevel, bool hasLesser, bool hasRegular, bool hasGreater)
    {
        var have = new[] { hasLesser, hasRegular, hasGreater };

        for (var i = 0; i < 3; i++)
        {
            if (have[i] && Chances[i][Math.Clamp(poisonLevel, 0, 4)] >= 100)
            {
                return (Cure)i;
            }
        }

        Cure? best = null;
        var bestChance = 0;

        for (var i = 0; i < 3; i++)
        {
            var chance = Chances[i][Math.Clamp(poisonLevel, 0, 4)];

            if (have[i] && chance > bestChance)
            {
                best = (Cure)i;
                bestChance = chance;
            }
        }

        return best;
    }

    private static void OnRequest(NetState state, SpanReader reader)
    {
        if (state.Mobile is not PlayerMobile { Poisoned: true, Poison: { } poison, Backpack: { } pack } || !Enabled)
        {
            state.Send(Reply(null, 0));
            return;
        }

        Item? lesser = null, regular = null, greater = null;

        foreach (var item in pack.FindItemsByType<BaseCurePotion>(true))
        {
            switch (item)
            {
                case LesserCurePotion: lesser ??= item; break;
                case GreaterCurePotion: greater ??= item; break;
                case CurePotion: regular ??= item; break;
            }
        }

        var choice = Choose(poison.Level, lesser is not null, regular is not null, greater is not null);
        var chosen = choice switch { Cure.Lesser => lesser, Cure.Regular => regular, Cure.Greater => greater, _ => null };

        state.Send(Reply(chosen?.Serial.Value, choice is { } c ? ChanceOf(c, poison.Level) : 0));
    }

    /// <summary>The reply as raw bytes: 0xBF, the length, the command, the count (0 or 1), then, for a count of 1, the potion's serial and the chance in percent.</summary>
    public static byte[] Reply(uint? serial, int chancePercent)
    {
        var length = serial is null ? 6 : 11;
        var buffer = new byte[length];

        buffer[0] = 0xBF;
        buffer[1] = (byte)(length >> 8);
        buffer[2] = (byte)length;
        buffer[3] = (byte)(Command >> 8);
        buffer[4] = (byte)Command;

        if (serial is { } s)
        {
            buffer[5] = 1;
            buffer[6] = (byte)(s >> 24);
            buffer[7] = (byte)(s >> 16);
            buffer[8] = (byte)(s >> 8);
            buffer[9] = (byte)s;
            buffer[10] = (byte)Math.Clamp(chancePercent, 0, 100);
        }

        return buffer;
    }
}
