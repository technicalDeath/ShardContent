using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The confirmation before a player throws a skill's banked points away (owner request 2026-10-07): it says exactly what will go and
/// asks them to type the word <see cref="ConfirmWord"/> in a box. Anything else, Keep them, or closing the window leaves the bank alone.
/// Faint Memories has no Discard: it is not in the bank.
/// </summary>
public sealed class SkillBankDiscardGump : DynamicGump
{
    /// <summary>The word that has to be typed to confirm.</summary>
    public const string ConfirmWord = "discard";

    private const int Width = 480;
    private const int Height = 330;
    private const int ButtonDiscard = 1;
    private const int ButtonKeep = 2;
    private const int EntryWord = 1;

    private readonly int _skillId;
    private readonly int _page;
    private readonly string _skillName;
    private readonly int _bankedTenths;
    private readonly int _skillTenths;

    private SkillBankDiscardGump(int skillId, int page, string skillName, int bankedTenths, int skillTenths) : base(80, 60)
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
            SkillBankGump.Open(player, page, "Nothing is banked for that skill.", GumpStyle.Warning);
            return;
        }

        player.SendGump(new SkillBankDiscardGump(skillId, page, row.Name, row.BankedTenths, row.ActiveTenths));
    }

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        builder.AddPage();
        GumpStyle.Frame(ref builder, "Discard banked points", "This cannot be undone", Width, Height);

        builder.AddHtml(30, 80, Width - 60, 28, DescribeQuestion(_skillName), GumpStyle.Warning, size: 4);
        builder.AddHtml(30, 118, Width - 60, 60, DescribeConsequence(_skillName, _bankedTenths, _skillTenths), GumpStyle.Text);

        builder.AddHtml(30, 190, Width - 60, 20, DescribePrompt(), GumpStyle.Gold);
        builder.AddImageTiled(30, 214, 200, 26, 2524);
        builder.AddTextEntryLimited(34, 217, 192, 20, 0, EntryWord, "", ConfirmWord.Length + 4);

        builder.AddButton(30, 252, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, ButtonDiscard);
        builder.AddHtml(72, 256, 180, 22, "Discard the points", GumpStyle.Warning, fontStyle: 1);

        builder.AddButton(260, 252, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, ButtonKeep);
        builder.AddHtml(302, 256, 150, 22, "Keep them", GumpStyle.Good, fontStyle: 1);
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
                    SkillBankGump.Open(player, _page, result.Message, result.Discarded ? GumpStyle.Good : GumpStyle.Warning);
                    break;
                }
            case ButtonDiscard:
                SkillBankGump.Open(player, _page, $"Nothing was discarded: {ConfirmWord} was not typed.", GumpStyle.Warning);
                break;
            case ButtonKeep:
                SkillBankGump.Open(player, _page, $"Nothing was discarded. {_skillName} keeps its {GumpStyle.Points(_bankedTenths)} banked points.", GumpStyle.Good);
                break;
        }
    }
}
