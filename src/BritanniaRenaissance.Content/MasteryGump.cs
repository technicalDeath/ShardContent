using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// [Mastery: the Mastery cycle and every skill in Mastery range, in the shard's style. One row per skill with where it stands between
/// 80.0 and 100.0, the guaranteed allowance it has left, whether it has claimed this cycle's allowance, and how far it has to go. Pages of
/// six. Staff may open it for another player by serial; it then says whose it is.
/// </summary>
public sealed class MasteryGump : DynamicGump
{
    public const int RowsPerPage = 6;

    private const int ButtonPrevious = 1;
    private const int ButtonNext = 2;
    private const int ButtonGuide = 3;
    private const int ButtonSpeeds = 4;

    private const int HeaderY = 150;
    private const int RowsTop = 174;
    private const int RowHeight = 34;
    private const int InnerWidth = GumpStyle.Width - 2 * GumpStyle.Margin;

    // The columns, left to right, none overlapping: skill, now, the bar from 80 to 100, allowance, this cycle, to go.
    private const int ColSkill = GumpStyle.Margin;
    private const int ColNow = 184;
    private const int ColBar = 258;
    private const int ColAllowance = 392;
    private const int ColCycle = 484;
    private const int ColLeft = 566;

    private readonly MasteryProgression.MasteryView _view;
    private readonly PlayerMobile _subject;
    private readonly int _page;

    private MasteryGump(MasteryProgression.MasteryView view, PlayerMobile subject, int page) : base(GumpStyle.LargeX, GumpStyle.LargeY)
    {
        _view = view;
        _subject = subject;
        _page = page;
    }

    public override bool Singleton => true;

    public static int PageCount(int rows) => Math.Max(1, (rows + RowsPerPage - 1) / RowsPerPage);

    public static void Open(Mobile viewer, Mobile subject, int page = 0)
    {
        if (viewer.NetState is null)
        {
            return;
        }

        if (subject is not PlayerMobile player || MasteryProgression.BuildView(viewer, subject) is not { } view)
        {
            viewer.SendMessage("Mastery applies to player characters.");
            return;
        }

        viewer.SendGump(new MasteryGump(view, player, Math.Clamp(page, 0, PageCount(view.Rows.Count) - 1)));
    }

    /// <summary>The line at the top of the window: when the next cycle begins, or why it has not.</summary>
    public static string DescribeCycle(MasteryProgression.MasteryView view) => view.Phase switch
    {
        MasteryProgression.MasteryPhase.Active =>
            $"Your next cycle begins in {GumpStyle.Colored(MasteryEngine.FormatDuration(view.NextCycleIn), GumpStyle.Gold)}.",
        MasteryProgression.MasteryPhase.Waiting =>
            $"Your first cycle begins with your next successful use of a skill at {MasteryEngine.ThresholdText} or above.",
        _ => $"No skill is in Mastery yet. Mastery begins at {MasteryEngine.ThresholdText}."
    };

    /// <summary>What the window says when no skill is in Mastery: what is empty, why, and what to do.</summary>
    public static string DescribeEmpty() =>
        $"No skill is in Mastery yet.<BR>A skill at {MasteryEngine.ThresholdText} or above is listed here with its allowance, once you have used it.";

    /// <summary>The line under the title.</summary>
    public static string Subtitle() => $"From {MasteryEngine.ThresholdText} a skill has guaranteed daily gains, and still gains by chance";

    /// <summary>The two lines under the cycle line: what claims the allowance and what it buys.</summary>
    public static string Explanation(int cycleHours) =>
        $"A skill's first valid, successful use in a cycle ({cycleHours} hours) claims its allowance. " +
        "While it lasts, each valid use is a guaranteed +0.1; after it, by chance.";

    /// <summary>The two lines under the table.</summary>
    public static string Footnote(int bankCycles) =>
        $"Allowance is what a skill is still guaranteed to gain; it keeps up to {bankCycles} cycles' worth. " +
        "A cycle you miss gives no allowance but takes nothing away.";

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        builder.AddPage();
        GumpStyle.Frame(
            ref builder,
            _view.OwnerName is null ? "Mastery" : $"Mastery: {_view.OwnerName}",
            Subtitle()
        );

        builder.AddHtml(GumpStyle.Margin, 84, InnerWidth, 20, DescribeCycle(_view), GumpStyle.Text);
        builder.AddHtml(GumpStyle.Margin, 108, InnerWidth, 36, Explanation(_view.CycleHours), GumpStyle.Muted);

        if (_view.Rows.Count > 0)
        {
            BuildTable(ref builder);
        }
        else
        {
            GumpStyle.EmptyState(ref builder, 60, 220, GumpStyle.Width - 120, 80, DescribeEmpty());
        }

        BuildFooter(ref builder);
    }

    private void BuildTable(ref DynamicGumpBuilder builder)
    {
        GumpStyle.TableHeader(
            ref builder, HeaderY, GumpStyle.Width,
            (ColSkill, 150, "Skill", TextAlignment.Left),
            (ColNow, 60, "Now", TextAlignment.Right),
            (ColBar, 130, $"{MasteryEngine.ThresholdText} to 100", TextAlignment.Left),
            (ColAllowance, 92, "Allowance", TextAlignment.Center),
            (ColCycle, 80, "This cycle", TextAlignment.Center),
            (ColLeft, 40, "To go", TextAlignment.Right)
        );

        var rows = _view.Rows.Skip(_page * RowsPerPage).Take(RowsPerPage).ToArray();

        for (var i = 0; i < rows.Length; i++)
        {
            var row = rows[i];
            var y = RowsTop + i * RowHeight;
            var progress = (row.ValueTenths - MasteryEngine.ThresholdFixedPoint) /
                           (double)(MasteryEngine.GrandmasterFixedPoint - MasteryEngine.ThresholdFixedPoint);

            builder.AddHtml(ColSkill, y, 150, 20, row.Name, GumpStyle.Text);
            builder.AddHtml(ColSkill, y + 15, 150, 16, $"{MasteryProgression.ClassLabel(row.ClassName)}, {GumpStyle.Points(row.AllowanceTenths)} a cycle", GumpStyle.Dim);
            GumpStyle.Cell(ref builder, ColNow, y + 7, 60, GumpStyle.Points(row.ValueTenths), GumpStyle.Gold, TextAlignment.Right);
            GumpStyle.Bar(ref builder, ColBar, y + 7, progress, GumpStyle.Gold, 44);
            GumpStyle.Cell(
                ref builder, ColAllowance, y + 7, 92, $"{GumpStyle.Points(row.StoredTenths)} of {GumpStyle.Points(row.StoredMaxTenths)}",
                row.StoredTenths > 0 ? GumpStyle.Text : GumpStyle.Muted, TextAlignment.Center
            );
            GumpStyle.Cell(ref builder, ColCycle, y + 7, 80, row.Claimed ? "Claimed" : "Not yet", row.Claimed ? GumpStyle.Good : GumpStyle.Muted, TextAlignment.Center);
            GumpStyle.Cell(ref builder, ColLeft, y + 7, 40, GumpStyle.Points(row.LeftTenths), GumpStyle.Muted, TextAlignment.Right);
            GumpStyle.RowRule(ref builder, GumpStyle.RuleInset, y + RowHeight - 3, GumpStyle.Width - 2 * GumpStyle.RuleInset);
        }

        builder.AddHtml(GumpStyle.Margin, RowsTop + RowsPerPage * RowHeight + 6, InnerWidth, 36, Footnote(_view.BankCycles), GumpStyle.Dim);
    }

    private void BuildFooter(ref DynamicGumpBuilder builder)
    {
        var pages = PageCount(_view.Rows.Count);
        var y = GumpStyle.FooterButtonsY(GumpStyle.Height);

        GumpStyle.Footer(ref builder, string.Empty, GumpStyle.Width, GumpStyle.Height);
        GumpStyle.MenuAction(ref builder, GumpStyle.Margin, y, "How it works", ButtonGuide);

        if (SkillGainCurveService.Enabled)
        {
            GumpStyle.MenuAction(ref builder, GumpStyle.Margin + GumpStyle.OvalWidth("How it works") + 8, y, "Skill speeds", ButtonSpeeds);
        }

        GumpStyle.Pager(ref builder, GumpStyle.Width, GumpStyle.Height, _page, pages, ButtonPrevious, ButtonNext);
    }

    public override void OnResponse(NetState sender, in RelayInfo info)
    {
        if (sender.Mobile is not PlayerMobile viewer)
        {
            return;
        }

        switch (info.ButtonID)
        {
            case ButtonPrevious:
                Open(viewer, _subject, _page - 1);
                break;
            case ButtonNext:
                Open(viewer, _subject, _page + 1);
                break;
            case ButtonGuide:
                WelcomeGuide.Open(viewer, "mastery");
                break;
            case ButtonSpeeds:
                SkillClassesGump.Open(viewer);
                break;
        }
    }
}
