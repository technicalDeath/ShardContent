using Server;
using Server.Gumps;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Asks before a criminal act on a corpse (QoL item 32, docs/Bot-Farm-QoL-Findings.md), behind <c>featureFlags.criminalCorpseConfirm</c>. The owner
/// (2026-10-15): every criminal act must come with a warning and a confirmation, and one without is a bug. Attacking an innocent, harming one with a
/// spell and helping a criminal already ask in the client; looting, using an item in, carving and stealing from a corpse that is not yours to loot
/// flagged you with at most a line of text. Now the first such act on a corpse opens a window; "OKAY" lets every act on that corpse go ahead for this
/// character (a carve happens at once; anything else is done again), and nothing changes how being a criminal works.
/// </summary>
public static class CriminalCorpseConfirm
{
    public const string Title = "Criminal act";

    public const string Kept = "You leave it alone.";

    private static readonly Dictionary<(Serial Player, Serial Corpse), bool> Confirmed = [];
    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.CriminalCorpseConfirm == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        var previous = Corpse.CriminalActAllowed;
        Corpse.CriminalActAllowed = (from, corpse, act, replay) => Allowed(from, corpse, act, replay) && previous?.Invoke(from, corpse, act, replay) != false;
        EventSink.Disconnected += m => Forget(m.Serial);
    }

    /// <summary>What the window says, by act and by whose corpse it is.</summary>
    public static string Warning(CriminalCorpseAct act, bool playerCorpse)
    {
        var whose = playerCorpse ? "This corpse is not yours to loot" : "This is not your kill";
        var what = act switch
        {
            CriminalCorpseAct.Carve => "carving it",
            CriminalCorpseAct.Steal => "stealing from it",
            CriminalCorpseAct.Use => "using what is in it",
            _ => "taking from it"
        };

        return $"{whose}: {what} is a criminal act. You will be a criminal for about 2 minutes, guards will attack you in town and anyone may attack you.";
    }

    /// <summary>What to do after OKAY when the act cannot simply be done again for the player.</summary>
    public static string Again(CriminalCorpseAct act) =>
        act switch
        {
            CriminalCorpseAct.Steal => "Use Stealing on it again.",
            CriminalCorpseAct.Use => "Use it again.",
            _ => "Pick it up again."
        };

    private static bool Allowed(Mobile from, Corpse corpse, CriminalCorpseAct act, Action replay)
    {
        if (!Enabled || from is not PlayerMobile player || player.AccessLevel != AccessLevel.Player ||
            Confirmed.ContainsKey((player.Serial, corpse.Serial)))
        {
            return true;
        }

        if (!player.HasGump<ConfirmGump>())
        {
            player.SendGump(new ConfirmGump(corpse, act, replay));
        }

        return false;
    }

    private static void Forget(Serial player)
    {
        foreach (var key in Confirmed.Keys.Where(k => k.Player == player).ToList())
        {
            Confirmed.Remove(key);
        }
    }

    public sealed class ConfirmGump : DynamicGump
    {
        public const int Height = 230;
        private const int TextWidth = GumpStyle.DialogWidth - 2 * GumpStyle.Margin;

        private readonly Corpse _corpse;
        private readonly CriminalCorpseAct _act;
        private readonly Action _replay;

        public override bool Singleton => true;

        public ConfirmGump(Corpse corpse, CriminalCorpseAct act, Action replay) : base(GumpStyle.DialogX, GumpStyle.DialogY)
        {
            _corpse = corpse;
            _act = act;
            _replay = replay;
        }

        protected override void BuildLayout(ref DynamicGumpBuilder builder)
        {
            builder.AddPage();
            GumpStyle.Frame(ref builder, Title, "Do it anyway?", GumpStyle.DialogWidth, Height);
            GumpStyle.Banner(ref builder, BannerKind.Danger, Warning(_act, _corpse.Owner?.Player == true), width: TextWidth - 38, height: 64);
            GumpStyle.Rule(ref builder, GumpStyle.RuleInset, Height - GumpStyle.FooterRoom, GumpStyle.DialogWidth - 2 * GumpStyle.RuleInset);
            GumpStyle.OkayCancel(
                ref builder, GumpStyle.Margin, GumpStyle.DialogWidth - GumpStyle.Margin - GumpStyle.OvalWidths[0], GumpStyle.FooterButtonsY(Height), 1, 0
            );
        }

        public override void OnResponse(NetState sender, in RelayInfo info)
        {
            if (sender.Mobile is not PlayerMobile player)
            {
                return;
            }

            if (info.ButtonID != 1 || _corpse.Deleted)
            {
                player.SendMessage(0x35, Kept);
                return;
            }

            Confirmed[(player.Serial, _corpse.Serial)] = true;

            if (_replay is not null)
            {
                _replay();
            }
            else
            {
                player.SendMessage(0x35, Again(_act));
            }
        }
    }
}
