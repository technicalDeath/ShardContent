using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// [SkillBank: the player's Skill Bank as a window in the guide's style. Shows Faint Memories while a new character still has some,
/// how full the bank is, each banked skill with the skill now, what is banked and its setting, a pair of tick-boxes per skill to
/// switch it between Locked (safe) and Down (may be replaced when the bank is full), and a Discard button that opens
/// <see cref="SkillBankDiscardGump"/>. Pages of six (four while Faint Memories shows); each press saves at once and reopens the
/// window with a line saying what changed.
/// </summary>
public sealed class SkillBankGump : DynamicGump
{
    public const int RowsPerPage = 6;
    public const int RowsPerPageWithBanner = 4;

    private const int ButtonPrevious = 1;
    private const int ButtonNext = 2;
    private const int ButtonGuide = 3;
    private const int LockedBase = 1000;
    private const int DownBase = 2000;
    private const int DiscardBase = 3000;

    private const int BannerShift = 58;
    private const int RowHeight = 34;

    private readonly SkillBankService.SkillBankView _view;
    private readonly int _page;
    private readonly string? _notice;
    private readonly string _noticeColor;

    private SkillBankGump(SkillBankService.SkillBankView view, int page, string? notice, string noticeColor) : base(40, 30)
    {
        _view = view;
        _page = page;
        _notice = notice;
        _noticeColor = noticeColor;
    }

    public override bool Singleton => true;

    private bool HasBanner => _view.FaintMemories is not null;

    private int Shift => HasBanner ? BannerShift : 0;

    private int RowsHere => RowsFor(HasBanner);

    public static int RowsFor(bool banner) => banner ? RowsPerPageWithBanner : RowsPerPage;

    public static int PageCount(int rows, bool banner = false) => Math.Max(1, (rows + RowsFor(banner) - 1) / RowsFor(banner));

    /// <summary>The setting a button id asks for, or null for a button that is not a setting.</summary>
    public static (int SkillId, BankRetention Retention)? ParseRetentionButton(int buttonId) => buttonId switch
    {
        >= DiscardBase => null,
        >= DownBase and < DownBase + 1000 => (buttonId - DownBase, BankRetention.Down),
        >= LockedBase and < LockedBase + 1000 => (buttonId - LockedBase, BankRetention.Locked),
        _ => null
    };

    /// <summary>The skill a Discard button is for, or null for a button that is not one.</summary>
    public static int? ParseDiscardButton(int buttonId) =>
        buttonId is >= DiscardBase and < DiscardBase + 1000 ? buttonId - DiscardBase : null;

    public static void Open(PlayerMobile player, int page = 0, string? notice = null, string noticeColor = GumpStyle.Good)
    {
        if (player.NetState is null)
        {
            return;
        }

        var view = SkillBankService.GetView(player);

        if (view is null)
        {
            player.SendMessage(SkillBankService.Enabled ? "Your Skill Bank needs staff review." : "The Skill Bank is not enabled.");
            return;
        }

        var fullness = SkillBankService.DescribeFullness(view.TotalTenths, view.CapacityTenths, view.HasDown);

        if (notice is null && fullness.Length > 0)
        {
            notice = fullness;
            noticeColor = GumpStyle.Warning;
        }

        var pages = PageCount(view.Rows.Count, view.FaintMemories is not null);
        player.SendGump(new SkillBankGump(view, Math.Clamp(page, 0, pages - 1), notice, noticeColor));
    }

    /// <summary>What the Faint Memories banner says, worked out apart from the drawing so it can be tested.</summary>
    public sealed record Banner(string Points, string Theme, string Label, double Fraction, string FillColor);

    public static Banner DescribeBanner(FaintMemoriesView view, int stepTenths)
    {
        var points = view.RemainingTenths == view.PointsTenths
            ? $"{GumpStyle.Points(view.RemainingTenths)} points"
            : $"{GumpStyle.Points(view.RemainingTenths)} of {GumpStyle.Points(view.PointsTenths)} left";

        return view.Phase == FaintMemoriesPhase.Locked
            ? new Banner(
                points, FaintMemoriesPolicy.Theme,
                $"Unlocks in {FaintMemoriesPolicy.DescribeUnlockIn(view.UnlockIn)}", view.UnlockFraction, GumpStyle.Gold
            )
            : new Banner(
                points, FaintMemoriesPolicy.Theme,
                $"Train a skill set to Up: {GumpStyle.Points(stepTenths)} per use",
                view.PointsTenths == 0 ? 0 : (double)view.RemainingTenths / view.PointsTenths, GumpStyle.Good
            );
    }

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        builder.AddPage();
        GumpStyle.Frame(ref builder, "Skill Bank", "Skill points a Down skill gave up, saved so you can earn them back");

        var o = Shift;
        var total = _view.TotalTenths;
        var capacity = _view.CapacityTenths;

        if (_view.FaintMemories is { } memories)
        {
            BuildBanner(ref builder, memories);
        }

        builder.AddHtml(30, 76 + o, 330, 22, $"Banked: {GumpStyle.Colored(GumpStyle.Points(total), GumpStyle.Gold)} of {GumpStyle.Points(capacity)} points", GumpStyle.Text);
        GumpStyle.Bar(ref builder, 30, 100 + o, capacity == 0 ? 0 : (double)total / capacity, GumpStyle.Gold, 100);

        builder.AddHtml(
            372, 74 + o, 250, 74,
            $"Set a skill to Up and train it: every use brings back {GumpStyle.Points(SkillBankService.RestoreStepTenths)} from the bank. " +
            "Discard throws a skill's banked points away for good.",
            GumpStyle.Muted
        );

        if (_notice is not null)
        {
            builder.AddHtml(30, 128 + o, 580, 38, _notice, _noticeColor);
        }

        if (_view.Rows.Count == 0)
        {
            builder.AddHtml(
                60, 200 + o, 520, 110,
                $"{GumpStyle.Colored("Nothing is banked yet.", GumpStyle.Gold)}<BR><BR>" +
                "Whenever a skill you have set to Down loses points because another skill gained, those points are saved here, " +
                "and you earn them back by training that skill again. You do not need to be at the skill cap for that.",
                GumpStyle.Text
            );
        }
        else
        {
            BuildTable(ref builder);
        }

        BuildFooter(ref builder);
    }

    private static void BuildBanner(ref DynamicGumpBuilder builder, FaintMemoriesView memories)
    {
        var banner = DescribeBanner(memories, SkillBankService.RestoreStepTenths);

        builder.AddHtml(30, 72, 330, 22, FaintMemoriesPolicy.Name, GumpStyle.Gold, size: 4);
        builder.AddHtml(380, 74, 230, 22, banner.Points, GumpStyle.Gold, align: TextAlignment.Right);
        builder.AddHtml(30, 92, 580, 20, banner.Theme, GumpStyle.Muted);
        GumpStyle.Bar(ref builder, 30, 112, banner.Fraction, banner.FillColor, 100);
        builder.AddHtml(348, 112, 262, 20, banner.Label, memories.Phase == FaintMemoriesPhase.Locked ? GumpStyle.Warning : GumpStyle.Good);
    }

    private void BuildTable(ref DynamicGumpBuilder builder)
    {
        var o = Shift;
        var headerY = 166 + o;
        var rowsTop = 190 + o;

        builder.AddHtml(36, headerY, 150, 20, "Skill", GumpStyle.Dim);
        builder.AddHtml(186, headerY, 60, 20, "Now", GumpStyle.Dim, align: TextAlignment.Right);
        builder.AddHtml(256, headerY, 60, 20, "Banked", GumpStyle.Dim, align: TextAlignment.Right);
        builder.AddHtml(334, headerY, 180, 20, "Setting", GumpStyle.Dim);

        var rows = _view.Rows.Skip(_page * RowsHere).Take(RowsHere).ToArray();

        for (var i = 0; i < rows.Length; i++)
        {
            var row = rows[i];
            var y = rowsTop + i * RowHeight;
            var locked = row.Retention == BankRetention.Locked;

            builder.AddHtml(36, y + 8, 150, 20, row.Name, GumpStyle.Text);
            builder.AddHtml(186, y + 8, 60, 20, GumpStyle.Points(row.ActiveTenths), GumpStyle.Muted, align: TextAlignment.Right);
            builder.AddHtml(256, y + 8, 60, 20, GumpStyle.Points(row.BankedTenths), GumpStyle.Gold, align: TextAlignment.Right);

            AddChoice(ref builder, 334, y, "Locked", GumpStyle.Good, locked, LockedBase + row.SkillId);
            AddChoice(ref builder, 430, y, "Down", GumpStyle.Warning, !locked, DownBase + row.SkillId);

            builder.AddButton(528, y + 3, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, DiscardBase + row.SkillId);
            builder.AddHtml(564, y + 8, 60, 20, "Discard", GumpStyle.Text);
        }

        var legendY = rowsTop + RowsHere * RowHeight + 8;
        builder.AddHtml(
            30, legendY, 580, 40,
            $"{GumpStyle.Colored("Locked", GumpStyle.Good)}: the banked points are safe (the default).  " +
            $"{GumpStyle.Colored("Down", GumpStyle.Warning)}: they can be replaced when the bank has no room for new points.",
            GumpStyle.Muted
        );
    }

    private static void AddChoice(ref DynamicGumpBuilder builder, int x, int rowY, string label, string color, bool selected, int buttonId)
    {
        if (selected)
        {
            builder.AddImage(x, rowY + 7, GumpStyle.ChoiceOn);
        }
        else
        {
            builder.AddButton(x, rowY + 7, GumpStyle.ChoiceOff, GumpStyle.ChoiceOn, buttonId);
        }

        builder.AddHtml(x + 28, rowY + 8, 66, 20, label, selected ? color : GumpStyle.Muted, fontStyle: (byte)(selected ? 1 : 0));
    }

    private void BuildFooter(ref DynamicGumpBuilder builder)
    {
        var pages = PageCount(_view.Rows.Count, HasBanner);

        builder.AddButton(24, GumpStyle.Height - 44, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, ButtonGuide);
        builder.AddHtml(64, GumpStyle.Height - 42, 110, 20, "How it works", GumpStyle.Text);

        if (pages > 1)
        {
            if (_page > 0)
            {
                builder.AddButton(196, GumpStyle.Height - 44, 4014, 4016, ButtonPrevious);
            }

            builder.AddHtml(232, GumpStyle.Height - 42, 120, 20, $"Page {_page + 1} of {pages}", GumpStyle.Muted, align: TextAlignment.Center);

            if (_page + 1 < pages)
            {
                builder.AddButton(362, GumpStyle.Height - 44, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, ButtonNext);
            }
        }

        GumpStyle.FooterButton(ref builder, GumpStyle.Width - 120, "Close", 0, 60);
    }

    public override void OnResponse(NetState sender, in RelayInfo info)
    {
        if (sender.Mobile is not PlayerMobile player)
        {
            return;
        }

        var id = info.ButtonID;

        if (ParseDiscardButton(id) is { } discardSkill)
        {
            SkillBankDiscardGump.Open(player, discardSkill, _page);
            return;
        }

        if (ParseRetentionButton(id) is { } change)
        {
            var message = SkillBankService.SetRetention(player, change.SkillId, change.Retention);
            var name = player.Skills[change.SkillId].Info.Name;
            var done = message.EndsWith($"set to {change.Retention}.", StringComparison.Ordinal);
            Open(
                player,
                _page,
                done ? DescribeChange(name, change.Retention) : message,
                done ? GumpStyle.Good : GumpStyle.Warning
            );
            return;
        }

        switch (id)
        {
            case ButtonPrevious:
                Open(player, _page - 1);
                break;
            case ButtonNext:
                Open(player, _page + 1);
                break;
            case ButtonGuide:
                WelcomeGuide.Open(player, "skillbank");
                break;
        }
    }

    public static string DescribeChange(string skillName, BankRetention retention) => retention == BankRetention.Locked
        ? $"{skillName} is now Locked: its banked points are safe."
        : $"{skillName} is now Down: its banked points can be replaced when the bank is full.";
}
