using System.Buffers;
using Server;
using Server.Accounting;
using Server.Engines.CharacterCreation;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The server half of the potion bar (docs/Potion-Bar-Evidence.md), behind <c>featureFlags.potionBar</c>.
/// <list type="bullet">
/// <item>The client cannot tell a lesser potion from a greater one (they share graphic and hue), so it asks, with extended command 0xA7 and the serials of the potions it
/// found in its pack, and gets the same command back with a code for each: 10 x the kind (1 heal, 2 cure, 3 refresh, 4 agility, 5 strength) plus the strength (0 lesser,
/// 1 regular, 2 greater). A potion that is not one of those, or not in the asker's own backpack, gets no answer.</item>
/// <item>Every new character starts with three Lesser Heal and three Refresh potions (the weakest refresh there is), newbied like the other starter items, once per character.</item>
/// </list>
/// </summary>
public static class PotionBarService
{
    public const int Command = 0xA7;
    public const int StarterHeal = 3;
    public const int StarterRefresh = 3;
    public const int MaxRequest = 64;

    private const string StarterTagPrefix = "BritanniaRenaissance.PotionBar.Starter.v1.";

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.PotionBar == true;

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        IncomingExtendedCommandPackets.RegisterExtended(Command, true, &OnRequest);
        CharacterCreation.CharacterCreatedHandler += IssueStarterPotions;
    }

    private static readonly Dictionary<Type, byte> Codes = new()
    {
        [typeof(LesserHealPotion)] = 10,
        [typeof(HealPotion)] = 11,
        [typeof(GreaterHealPotion)] = 12,
        [typeof(LesserCurePotion)] = 20,
        [typeof(CurePotion)] = 21,
        [typeof(GreaterCurePotion)] = 22,
        [typeof(RefreshPotion)] = 31,
        [typeof(TotalRefreshPotion)] = 32,
        [typeof(AgilityPotion)] = 41,
        [typeof(GreaterAgilityPotion)] = 42,
        [typeof(StrengthPotion)] = 51,
        [typeof(GreaterStrengthPotion)] = 52
    };

    /// <summary>The potion's code, or 0 when the bar does not show it. The exact type decides: a later potion that derives from one of these is not one of these.</summary>
    public static byte CodeOf(Type type) => Codes.GetValueOrDefault(type);

    public static byte CodeOf(Item item) => CodeOf(item.GetType());

    private static void OnRequest(NetState state, SpanReader reader)
    {
        if (!Enabled || state.Mobile is not PlayerMobile { Backpack: { } pack } player)
        {
            return;
        }

        int count = Math.Min((int)reader.ReadByte(), MaxRequest);
        var found = new List<(uint Serial, byte Code)>(count);

        for (var i = 0; i < count && reader.Remaining >= 4; i++)
        {
            var serial = reader.ReadUInt32();

            if (World.FindItem((Serial)serial) is { Deleted: false } item && item.IsChildOf(pack) && CodeOf(item) is var code and not 0)
            {
                found.Add((serial, code));
            }
        }

        if (found.Count > 0)
        {
            state.Send(Reply(found));
        }
    }

    /// <summary>The reply as raw bytes: 0xBF, the length, the command, the count, then a serial and a code for each.</summary>
    public static byte[] Reply(IReadOnlyList<(uint Serial, byte Code)> potions)
    {
        var length = 6 + potions.Count * 5;
        var buffer = new byte[length];

        buffer[0] = 0xBF;
        buffer[1] = (byte)(length >> 8);
        buffer[2] = (byte)length;
        buffer[3] = (byte)(Command >> 8);
        buffer[4] = (byte)Command;
        buffer[5] = (byte)potions.Count;

        var at = 6;

        foreach (var (serial, code) in potions)
        {
            buffer[at++] = (byte)(serial >> 24);
            buffer[at++] = (byte)(serial >> 16);
            buffer[at++] = (byte)(serial >> 8);
            buffer[at++] = (byte)serial;
            buffer[at++] = code;
        }

        return buffer;
    }

    private static void IssueStarterPotions(CharacterCreatedEventArgs args)
    {
        if (!Enabled || args.Mobile is not PlayerMobile { AccessLevel: AccessLevel.Player, Backpack: not null } player || player.Account is not Account account)
        {
            return;
        }

        var tag = $"{StarterTagPrefix}{player.Serial.Value}";

        if (account.GetTag(tag) is not null)
        {
            return;
        }

        for (var i = 0; i < StarterHeal; i++)
        {
            player.Backpack.DropItem(new LesserHealPotion { LootType = LootType.Newbied });
        }

        for (var i = 0; i < StarterRefresh; i++)
        {
            player.Backpack.DropItem(new RefreshPotion { LootType = LootType.Newbied });
        }

        account.SetTag(tag, "issued");
    }
}
