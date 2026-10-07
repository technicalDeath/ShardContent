using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// [Mastery: the Mastery cycle and every skill in Mastery range, in the guide's style. One row per skill with where it stands between
/// 90.0 and 100.0, the allowance it has stored, whether it has claimed this cycle's allowance, and how far it has to go. Pages of
/// six. Staff may open it for another player by serial; it then says whose it is.
/// </summary>
public sealed class MasteryGump : DynamicGump
{
    public const int RowsPerPage = 6;

    private const int ButtonPrevious = 1;
    private const int ButtonNext = 2;
    private const int ButtonGuide = 3;
    private const int ButtonSpeeds = 4;

    private const int RowsTop = 176;
    private const int RowHeight = 40;

    private readonly MasteryProgression.MasteryView _view;
    private readonly PlayerMobile _subject;
    private readonly int _page;

    private MasteryGump(MasteryProgression.MasteryView view, PlayerMobile subject, int page) : base(40, 30)
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

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        builder.AddPage();
        GumpStyle.Frame(
            ref builder,
            _view.OwnerName is null ? "Mastery" : $"Mastery: {_view.OwnerName}",
            $"From {MasteryEngine.ThresholdText} a skill grows by a daily allowance, not by chance"
        );

        builder.AddHtml(30, 76, 580, 22, DescribeCycle(_view), GumpStyle.Text);
        builder.AddHtml(
            30, 102, 580, 40,
            $"A skill claims its allowance with its first valid, successful use in a cycle ({_view.CycleHours} hours). " +
            "While it has allowance, each valid use gives +0.1, up to 100.0.",
            GumpStyle.Muted
        );

        if (_view.Rows.Count > 0)
        {
            BuildTable(ref builder);
        }

        BuildFooter(ref builder);
    }

    private void BuildTable(ref DynamicGumpBuilder builder)
    {
        builder.AddHtml(36, 152, 150, 20, "Skill", GumpStyle.Dim);
        builder.AddHtml(180, 152, 60, 20, "Now", GumpStyle.Dim, align: TextAlignment.Right);
        builder.AddHtml(262, 152, 130, 20, $"{MasteryEngine.ThresholdText} to 100", GumpStyle.Dim);
        builder.AddHtml(396, 152, 110, 20, "Allowance", GumpStyle.Dim, align: TextAlignment.Center);
        builder.AddHtml(508, 152, 66, 20, "This cycle", GumpStyle.Dim, align: TextAlignment.Center);
        builder.AddHtml(572, 152, 44, 20, "To go", GumpStyle.Dim, align: TextAlignment.Right);

        var rows = _view.Rows.Skip(_page * RowsPerPage).Take(RowsPerPage).ToArray();

        for (var i = 0; i < rows.Length; i++)
        {
            var row = rows[i];
            var y = RowsTop + i * RowHeight;
            var progress = (row.ValueTenths - MasteryEngine.ThresholdFixedPoint) /
                           (double)(MasteryEngine.GrandmasterFixedPoint - MasteryEngine.ThresholdFixedPoint);

            builder.AddHtml(36, y + 4, 150, 20, row.Name, GumpStyle.Text);
            builder.AddHtml(36, y + 21, 150, 16, $"{MasteryProgression.ClassLabel(row.ClassName)}, {GumpStyle.Points(row.AllowanceTenths)} a cycle", GumpStyle.Dim);
            builder.AddHtml(180, y + 11, 60, 20, GumpStyle.Points(row.ValueTenths), GumpStyle.Gold, align: TextAlignment.Right);
            GumpStyle.Bar(ref builder, 262, y + 11, progress, GumpStyle.Gold, 44);
            builder.AddHtml(
                396, y + 11, 110, 20,
                $"{GumpStyle.Points(row.StoredTenths)} of {GumpStyle.Points(row.StoredMaxTenths)}",
                row.StoredTenths > 0 ? GumpStyle.Text : GumpStyle.Muted,
                align: TextAlignment.Center
            );
            builder.AddHtml(
                508, y + 11, 66, 20,
                row.Claimed ? "Claimed" : "Not yet",
                row.Claimed ? GumpStyle.Good : GumpStyle.Warning,
                align: TextAlignment.Center
            );
            builder.AddHtml(572, y + 11, 44, 20, GumpStyle.Points(row.LeftTenths), GumpStyle.Muted, align: TextAlignment.Right);
        }

        builder.AddHtml(
            30, RowsTop + RowsPerPage * RowHeight + 6, 580, 40,
            $"Allowance is what a skill can still gain; it holds up to {_view.BankCycles} cycles' worth. " +
            "Missing a cycle never takes anything away: that cycle simply gives no allowance.",
            GumpStyle.Muted
        );
    }

    private void BuildFooter(ref DynamicGumpBuilder builder)
    {
        var pages = PageCount(_view.Rows.Count);

        builder.AddButton(24, GumpStyle.Height - 44, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, ButtonGuide);
        builder.AddHtml(64, GumpStyle.Height - 42, 110, 20, "How it works", GumpStyle.Text);

        if (SkillGainCurveService.Enabled)
        {
            builder.AddButton(186, GumpStyle.Height - 44, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, ButtonSpeeds);
            builder.AddHtml(226, GumpStyle.Height - 42, 110, 20, "Skill speeds", GumpStyle.Text);
        }

        if (pages > 1)
        {
            if (_page > 0)
            {
                builder.AddButton(346, GumpStyle.Height - 44, 4014, 4016, ButtonPrevious);
            }

            builder.AddHtml(380, GumpStyle.Height - 42, 80, 20, $"{_page + 1} of {pages}", GumpStyle.Muted, align: TextAlignment.Center);

            if (_page + 1 < pages)
            {
                builder.AddButton(462, GumpStyle.Height - 44, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, ButtonNext);
            }
        }

        GumpStyle.FooterButton(ref builder, GumpStyle.Width - 120, "Close", 0, 60);
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
