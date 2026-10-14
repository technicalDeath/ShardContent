using Server;
using Server.Accounting;
using Server.Commands;
using Server.Items;
using Server.Misc;
using Server.Mobiles;
using Server.Multis;
using Server.Network;
using System.Buffers;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Auto-pickup of ammunition and reagents (docs/Ammo-Reagent-Auto-Pickup-Plan.md), behind <c>featureFlags.autoPickup</c>. Arrows and bolts lying loose within one tile of an
/// ordinary player who has Archery, and reagents for a player with Magery, Alchemy or Inscription, are put in the pack, one pile a second, unless the pack would pass the weight
/// the shard treats as comfortable. Stock UOR has nothing like it (the engine's ammunition recovery is SE only). The client says which of arrows, bolts and reagents the player wants (extended command 0xAC, from its Options page and the combat bar's gear panel); a client that never says
/// (an unmodified one) gets all three. The decisions are pure so they can be tested without game objects.
/// </summary>
public static class AutoPickupService
{
    public const double SkillThreshold = 30.0;

    /// <summary>The share of the carrying limit a pickup may not pass.</summary>
    public const double WeightShare = 0.85;

    public enum Kind
    {
        None,
        Arrow,
        Bolt,
        Reagent,
    }

    public const int CommandId = 0xAC;

    /// <summary>The kinds a player wants when the client never said: all three.</summary>
    public const byte AllKinds = 7;

    private const string TellTagPrefix = "BritanniaRenaissance.AutoPickupTold.v1.";

    private static readonly List<NetState> Online = [];
    private static readonly Dictionary<Serial, byte> Wanted = [];

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.AutoPickup == true;

    public static unsafe void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        Server.Timer.StartTimer(TimeSpan.FromSeconds(1.0), TimeSpan.FromSeconds(1.0), Poll);
        IncomingExtendedCommandPackets.RegisterExtended(CommandId, true, &OnMask);
        EventSink.Disconnected += static mobile => Wanted.Remove(mobile.Serial);
        CommandSystem.Register("AutoPickupStatus", AccessLevel.GameMaster, OnStatus);
    }

    /// <summary>The client's choice of kinds: one byte, bit 0 arrows, bit 1 bolts, bit 2 reagents.</summary>
    private static void OnMask(NetState state, SpanReader reader)
    {
        if (state.Mobile is PlayerMobile player && reader.Remaining >= 1)
        {
            Wanted[player.Serial] = (byte)(reader.ReadByte() & AllKinds);
        }
    }

    // ---- the decisions

    public static Kind KindOf(Item item) => item switch
    {
        Arrow => Kind.Arrow,
        Bolt => Kind.Bolt,
        BaseReagent => Kind.Reagent,
        _ => Kind.None,
    };

    /// <summary>Whether a character uses a kind of pickup: Archery for ammunition, any of the three reagent skills for reagents.</summary>
    public static bool Uses(Kind kind, double archery, double magery, double alchemy, double inscription) => kind switch
    {
        Kind.Arrow or Kind.Bolt => archery >= SkillThreshold,
        Kind.Reagent => magery >= SkillThreshold || alchemy >= SkillThreshold || inscription >= SkillThreshold,
        _ => false,
    };

    /// <summary>"4 arrows", "1 bolt", "5 black pearl": the type name in lower case words, with an s only for ammunition.</summary>
    public static string PileName(string typeName, int amount)
    {
        var words = System.Text.RegularExpressions.Regex.Replace(typeName, "(?<=[a-z])(?=[A-Z])", " ").ToLowerInvariant();
        var plural = amount != 1 && typeName is "Arrow" or "Bolt";

        return $"{amount} {words}{(plural ? "s" : "")}";
    }

    /// <summary>Whether the player's switches ask for a kind (bit 0 arrows, bit 1 bolts, bit 2 reagents).</summary>
    public static bool Wants(Kind kind, byte mask) => kind switch
    {
        Kind.Arrow => (mask & 1) != 0,
        Kind.Bolt => (mask & 2) != 0,
        Kind.Reagent => (mask & 4) != 0,
        _ => false,
    };

    /// <summary>Whether the pile fits under the comfortable share of the carrying limit.</summary>
    public static bool FitsInWeight(int carried, int pileWeight, int maxWeight) => carried + pileWeight <= (int)(maxWeight * WeightShare);

    // ---- the watch

    private static void Poll()
    {
        if (!Enabled)
        {
            return;
        }

        Online.Clear();
        Online.AddRange(NetState.Instances);

        foreach (var ns in Online)
        {
            if (ns.Mobile is PlayerMobile { Deleted: false, Alive: true, AccessLevel: AccessLevel.Player, Backpack: not null, Map: not null } player && player.Account is Account account)
            {
                var mask = Wanted.TryGetValue(player.Serial, out var chosen) ? chosen : AllKinds;

                if (mask != 0)
                {
                    TryPickUp(player, account, mask);
                }
            }
        }
    }

    private static void TryPickUp(PlayerMobile player, Account account, byte mask)
    {
        var skills = player.Skills;
        var archery = skills[SkillName.Archery].Value;
        var magery = skills[SkillName.Magery].Value;
        var alchemy = skills[SkillName.Alchemy].Value;
        var inscription = skills[SkillName.Inscribe].Value;

        if (!Uses(Kind.Arrow, archery, magery, alchemy, inscription) && !Uses(Kind.Reagent, archery, magery, alchemy, inscription))
        {
            return;
        }

        Item? found = null;

        foreach (var item in player.Map.GetItemsInRange(player.Location, 1))
        {
            if (item.Parent == null && item.Movable && item.Visible && !item.IsLockedDown && !item.IsSecure && player.CanSee(item) && !InForeignHouse(player, item) &&
                KindOf(item) is var kind && Wants(kind, mask) && Uses(kind, archery, magery, alchemy, inscription))
            {
                found = item;
                break;
            }
        }

        if (found == null)
        {
            return;
        }

        var maxWeight = StaminaSystem.GetMaxWeight(player);

        if (!FitsInWeight(Mobile.BodyWeight + player.TotalWeight, found.TotalWeight + found.PileWeight, maxWeight))
        {
            return;
        }

        var name = PileName(found.GetType().Name, found.Amount);

        if (!player.Backpack!.TryDropItem(player, found, false))
        {
            return;
        }

        var tellTag = $"{TellTagPrefix}{player.Serial.Value}";

        if (account.GetTag(tellTag) is null)
        {
            account.SetTag(tellTag, "told");
            player.SendMessage(0x35, $"You pick up {name}. Auto-pickup is on: change it in Options, Auto pickup, or on the combat bar's gear button.");
        }
    }

    private static bool InForeignHouse(PlayerMobile player, Item item) =>
        BaseHouse.FindHouseAt(item) is { } house && !house.IsFriend(player) && !house.IsCoOwner(player);

    [Usage("AutoPickupStatus")]
    [Description("Shows whether automatic pickup is on and the rules it uses.")]
    private static void OnStatus(CommandEventArgs e) =>
        e.Mobile.SendMessage(
            $"Auto-pickup: {(Enabled ? "ON" : "off (flag featureFlags.autoPickup)")}. Skill threshold {SkillThreshold:0}, weight share {WeightShare:0.##}, one pile a second within 1 tile."
        );
}
