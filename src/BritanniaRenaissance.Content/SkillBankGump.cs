using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// [SkillBank: the player's Skill Bank as a window in the shard's style. Shows Faint Memories while a new character still has some,
/// how full the bank is, each banked skill with the skill now, what is banked and its setting (a pick-one: Locked, which keeps the points
/// safe, or Down, which lets them be replaced when the bank is full), and a purple Discard button that opens
/// <see cref="SkillBankDiscardGump"/>. Pages of six (four while Faint Memories shows); each press saves at once and reopens the
/// window with a banner saying what changed.
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
    private const int RowHeight = 30;
    private const int InnerWidth = GumpStyle.Width - 2 * GumpStyle.Margin;

    private readonly SkillBankService.SkillBankView _view;
    private readonly int _page;
    private readonly string? _notice;
    private readonly BannerKind _noticeKind;

    private SkillBankGump(SkillBankService.SkillBankView view, int page, string? notice, BannerKind noticeKind) : base(GumpStyle.LargeX, GumpStyle.LargeY)
    {
        _view = view;
        _page = page;
        _notice = notice;
        _noticeKind = noticeKind;
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

    public static void Open(PlayerMobile player, int page = 0, string? notice = null, BannerKind noticeKind = BannerKind.Done)
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
            noticeKind = BannerKind.Note;
        }

        var pages = PageCount(view.Rows.Count, view.FaintMemories is not null);
        player.SendGump(new SkillBankGump(view, Math.Clamp(page, 0, pages - 1), notice, noticeKind));
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

        // The banner line is always at the same place, so the window does not jump when a result comes back.
        if (_notice is not null)
        {
            GumpStyle.Banner(ref builder, _noticeKind, _notice, width: InnerWidth - 38, height: 36);
        }

        if (_view.FaintMemories is { } memories)
        {
            BuildMemories(ref builder, memories);
        }

        builder.AddHtml(GumpStyle.Margin, 124 + o, 230, 20, $"Banked: {GumpStyle.Colored(GumpStyle.Points(total), GumpStyle.Gold)} of {GumpStyle.Points(capacity)} points", GumpStyle.Text);
        GumpStyle.Bar(ref builder, 270, 124 + o, capacity == 0 ? 0 : (double)total / capacity, GumpStyle.Gold, 80);

        builder.AddHtml(
            GumpStyle.Margin, 148 + o, InnerWidth, 36,
            $"Set a skill to Up and train it: every use brings back {GumpStyle.Points(SkillBankService.RestoreStepTenths)} from the bank. " +
            "Discard throws a skill's banked points away for good.",
            GumpStyle.Muted
        );

        if (_view.Rows.Count == 0)
        {
            GumpStyle.EmptyState(
                ref builder, 60, 220 + o, GumpStyle.Width - 120, 110,
                $"{GumpStyle.Colored("Nothing is banked yet.", GumpStyle.Gold)}<BR><BR>" +
                "Whenever a skill you have set to Down loses points because another skill gained, those points are saved here, " +
                "and you earn them back by training that skill again. You do not need to be at the skill cap for that."
            );
        }
        else
        {
            BuildTable(ref builder);
        }

        BuildFooter(ref builder);
    }

    private static void BuildMemories(ref DynamicGumpBuilder builder, FaintMemoriesView memories)
    {
        var banner = DescribeBanner(memories, SkillBankService.RestoreStepTenths);

        builder.AddHtml(GumpStyle.Margin, 124, 330, 20, FaintMemoriesPolicy.Name, GumpStyle.Gold);
        builder.AddHtml(380, 124, 226, 20, banner.Points, GumpStyle.Gold, align: TextAlignment.Right);
        builder.AddHtml(GumpStyle.Margin, 144, InnerWidth, 20, banner.Theme, GumpStyle.Muted);
        GumpStyle.Bar(ref builder, GumpStyle.Margin, 164, banner.Fraction, banner.FillColor, 80);
        builder.AddHtml(
            370, 164, 236, 20, banner.Label, memories.Phase == FaintMemoriesPhase.Locked ? GumpStyle.Command : GumpStyle.Good, align: TextAlignment.Right
        );
    }

    private void BuildTable(ref DynamicGumpBuilder builder)
    {
        var o = Shift;
        var headerY = 188 + o;
        var rowsTop = 212 + o;

        GumpStyle.TableHeader(
            ref builder, headerY, GumpStyle.Width,
            (GumpStyle.Margin, 156, "Skill", TextAlignment.Left),
            (190, 60, "Now", TextAlignment.Right),
            (256, 60, "Banked", TextAlignment.Right),
            (330, 100, "Setting", TextAlignment.Left)
        );

        var rows = _view.Rows.Skip(_page * RowsHere).Take(RowsHere).ToArray();

        for (var i = 0; i < rows.Length; i++)
        {
            var row = rows[i];
            var y = rowsTop + i * RowHeight;
            var locked = row.Retention == BankRetention.Locked;

            GumpStyle.Cell(ref builder, GumpStyle.Margin, y + 5, 156, row.Name, GumpStyle.Text);
            GumpStyle.Cell(ref builder, 190, y + 5, 60, GumpStyle.Points(row.ActiveTenths), GumpStyle.Muted, TextAlignment.Right);
            GumpStyle.Cell(ref builder, 256, y + 5, 60, GumpStyle.Points(row.BankedTenths), GumpStyle.Gold, TextAlignment.Right);

            GumpStyle.RadioChoice(ref builder, 330, y + 3, "Locked", locked, LockedBase + row.SkillId, 60);
            GumpStyle.RadioChoice(ref builder, 426, y + 3, "Down", !locked, DownBase + row.SkillId, 50);

            GumpStyle.GameAction(ref builder, GumpStyle.Width - GumpStyle.Margin - GumpStyle.OvalWidths[1], y + 3, "Discard", DiscardBase + row.SkillId);
            GumpStyle.RowRule(ref builder, GumpStyle.RuleInset, y + RowHeight - 3, GumpStyle.Width - 2 * GumpStyle.RuleInset);
        }

        var legendY = rowsTop + RowsHere * RowHeight + 6;
        builder.AddHtml(
            GumpStyle.Margin, legendY, InnerWidth, 36,
            $"{GumpStyle.Colored("Locked", GumpStyle.Text)}: the banked points are safe (the default).  " +
            $"{GumpStyle.Colored("Down", GumpStyle.Text)}: they can be replaced when the bank has no room for new points.",
            GumpStyle.Muted
        );
    }

    private void BuildFooter(ref DynamicGumpBuilder builder)
    {
        var pages = PageCount(_view.Rows.Count, HasBanner);

        GumpStyle.Footer(ref builder, string.Empty, GumpStyle.Width, GumpStyle.Height);
        GumpStyle.MenuAction(ref builder, GumpStyle.Margin, GumpStyle.FooterButtonsY(GumpStyle.Height), "How it works", ButtonGuide);
        GumpStyle.Pager(ref builder, GumpStyle.Width, GumpStyle.Height, _page, pages, ButtonPrevious, ButtonNext);
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
                done ? BannerKind.Done : BannerKind.Danger
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
