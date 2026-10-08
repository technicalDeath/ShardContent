using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The confirmation before a player throws a skill's banked points away (owner request 2026-10-07): it says exactly what will go and
/// asks them to type the word <see cref="ConfirmWord"/> in a box. Anything else, Cancel, a right-click, or closing the window leaves the bank
/// alone. Faint Memories has no Discard: it is not in the bank. A dialog in the shard's style (Gump-Style-Guide.md 3.4): a Danger banner
/// naming the action, the consequence, the typed confirmation, a purple verb button and a red CANCEL at opposite ends.
/// </summary>
public sealed class SkillBankDiscardGump : DynamicGump
{
    /// <summary>The word that has to be typed to confirm.</summary>
    public const string ConfirmWord = "discard";

    private const int Width = GumpStyle.DialogWidth;
    private const int Height = 320;
    private const int ButtonDiscard = 1;
    private const int ButtonKeep = 2;
    private const int EntryWord = 1;
    private const int TextWidth = Width - 2 * GumpStyle.Margin;

    private readonly int _skillId;
    private readonly int _page;
    private readonly string _skillName;
    private readonly int _bankedTenths;
    private readonly int _skillTenths;

    private SkillBankDiscardGump(int skillId, int page, string skillName, int bankedTenths, int skillTenths) : base(GumpStyle.DialogX, GumpStyle.DialogY)
    {
        _skillId = skillId;
        _page = page;
        _skillName = skillName;
        _bankedTenths = bankedTenths;
        _skillTenths = skillTenths;
    }

    public override bool Singleton => true;

    /// <summary>True when what was typed is the confirmation word, ignoring case and spaces around it.</summary>
    public static bool IsConfirmed(string? typed) =>
        string.Equals(typed?.Trim(), ConfirmWord, StringComparison.OrdinalIgnoreCase);

    public static string DescribeQuestion(string skillName) => $"Discard the banked points of {skillName}?";

    public static string DescribeConsequence(string skillName, int bankedTenths, int skillTenths) =>
        $"{GumpStyle.Points(bankedTenths)} banked points will be deleted for good. They do not go back to {skillName}, " +
        $"and {skillName} stays at {GumpStyle.Points(skillTenths)}.";

    public static string DescribePrompt() => $"Type {ConfirmWord} in the box to confirm:";

    public static void Open(PlayerMobile player, int skillId, int page)
    {
        if (player.NetState is null)
        {
            return;
        }

        var view = SkillBankService.GetView(player);
        var row = view?.Rows.FirstOrDefault(r => r.SkillId == skillId);

        if (row is null)
        {
            SkillBankGump.Open(player, page, "Nothing is banked for that skill.", BannerKind.Note);
            return;
        }

        player.SendGump(new SkillBankDiscardGump(skillId, page, row.Name, row.BankedTenths, row.ActiveTenths));
    }

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        builder.AddPage();
        GumpStyle.Frame(ref builder, "Discard banked points", "This cannot be undone", Width, Height);

        // The question is the Danger line; the consequence says exactly what goes.
        var question = DescribeQuestion(_skillName);
        var questionHeight = GumpStyle.LinesFor("Danger: " + question, TextWidth - 38) * 18 + 6;
        GumpStyle.Banner(ref builder, BannerKind.Danger, question, width: TextWidth - 38, height: questionHeight);

        var consequence = DescribeConsequence(_skillName, _bankedTenths, _skillTenths);
        var consequenceY = GumpStyle.ContentTop + Math.Max(24, questionHeight) + 8;
        builder.AddHtml(GumpStyle.Margin, consequenceY, TextWidth, 58, consequence, GumpStyle.Text);

        var promptY = consequenceY + 62;
        builder.AddHtml(GumpStyle.Margin, promptY, TextWidth, 20, DescribePrompt(), GumpStyle.Muted);
        builder.AddImageTiled(GumpStyle.Margin, promptY + 24, 200, 26, GumpStyle.WellArt);
        builder.AddTextEntryLimited(GumpStyle.Margin + 4, promptY + 27, 192, 20, 0, EntryWord, "", ConfirmWord.Length + 4);

        GumpStyle.Rule(ref builder, GumpStyle.RuleInset, Height - GumpStyle.FooterRoom, Width - 2 * GumpStyle.RuleInset);

        // The verb is a game action (it changes the bank), purple; CANCEL is the red oval at the other end.
        var y = GumpStyle.FooterButtonsY(Height);
        GumpStyle.GameAction(ref builder, GumpStyle.Margin, y, "Discard points", ButtonDiscard);
        builder.AddButton(Width - GumpStyle.Margin - GumpStyle.OvalWidths[0], y, GumpStyle.CancelArt, GumpStyle.CancelArt + 1, ButtonKeep);
    }

    public override void OnResponse(NetState sender, in RelayInfo info)
    {
        if (sender.Mobile is not PlayerMobile player)
        {
            return;
        }

        switch (info.ButtonID)
        {
            case ButtonDiscard when IsConfirmed(info.GetTextEntry(EntryWord)):
                {
                    var result = SkillBankService.Discard(player, _skillId);
                    SkillBankGump.Open(player, _page, result.Message, result.Discarded ? BannerKind.Done : BannerKind.Danger);
                    break;
                }
            case ButtonDiscard:
                SkillBankGump.Open(player, _page, $"Nothing was discarded: {ConfirmWord} was not typed.", BannerKind.Danger);
                break;
            case ButtonKeep:
                SkillBankGump.Open(player, _page, $"Nothing was discarded. {_skillName} keeps its {GumpStyle.Points(_bankedTenths)} banked points.", BannerKind.Note);
                break;
            default:
                // A right-click: the same as Cancel, without a word, so closing the dialog takes the player back to the bank.
                SkillBankGump.Open(player, _page);
                break;
        }
    }
}
