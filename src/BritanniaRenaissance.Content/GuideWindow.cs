using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The topic window the [Welcome guide and [SkillClasses share: a list of topics on the left, the selected topic's text on the right,
/// "Next topic" and Close below. A window may start on any topic and may add buttons under the list that do something else
/// (open another window).
/// </summary>
public sealed class GuideWindow : DynamicGump
{
    public sealed record WindowAction(string Label, int ButtonId);

    private const int NavWidth = 190;
    private const int ContentTop = 108;
    private const int ContentHeight = GumpStyle.Height - 178;

    private readonly string _title;
    private readonly string _subtitle;
    private readonly string _footerHint;
    private readonly IReadOnlyList<WelcomeGuide.Topic> _topics;
    private readonly int _first;
    private readonly IReadOnlyList<WindowAction> _actions;
    private readonly Action<PlayerMobile, int>? _onAction;

    public GuideWindow(
        string title, string subtitle, string footerHint, IReadOnlyList<WelcomeGuide.Topic> topics, int firstTopic = 0,
        IReadOnlyList<WindowAction>? actions = null, Action<PlayerMobile, int>? onAction = null
    ) : base(40, 30)
    {
        _title = title;
        _subtitle = subtitle;
        _footerHint = footerHint;
        _topics = topics;
        _first = Math.Clamp(firstTopic, 0, Math.Max(0, topics.Count - 1));
        _actions = actions ?? [];
        _onAction = onAction;
    }

    public override bool Singleton => true;

    /// <summary>The client-side page of topic <paramref name="topic"/>: the window opens on page 1, so the first topic shown takes it.</summary>
    public static int PageOf(int topic, int first, int count) => (topic - first + count) % count + 1;

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        var count = _topics.Count;

        builder.AddPage();
        GumpStyle.Frame(ref builder, _title, _subtitle);
        builder.AddImageTiled(NavWidth + 14, 72, 2, GumpStyle.Height - 130, 2701);

        builder.AddButton(GumpStyle.Width - 120, GumpStyle.Height - 44, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, 0);
        builder.AddHtml(GumpStyle.Width - 80, GumpStyle.Height - 42, 60, 20, "Close", GumpStyle.Text);
        builder.AddHtml(24, GumpStyle.Height - 42, 300, 20, _footerHint, GumpStyle.Dim);

        // 44 pixels between topics, squeezed when there are many so the last one stays above the footer.
        var step = Math.Min(44, (GumpStyle.Height - 170) / count);

        for (var topic = 0; topic < count; topic++)
        {
            builder.AddPage(PageOf(topic, _first, count));

            for (var i = 0; i < count; i++)
            {
                var y = 80 + i * step;
                var selected = i == topic;

                builder.AddButton(22, y, selected ? GumpStyle.ArrowPressed : GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, 0, GumpButtonType.Page, PageOf(i, _first, count));
                builder.AddHtml(62, y + 2, NavWidth - 52, 24, _topics[i].Title, selected ? GumpStyle.Gold : GumpStyle.Text, fontStyle: (byte)(selected ? 1 : 0));
            }

            for (var a = 0; a < _actions.Count; a++)
            {
                var y = GumpStyle.Height - 150 + a * 36;
                builder.AddButton(22, y, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, _actions[a].ButtonId);
                builder.AddHtml(62, y + 2, NavWidth - 52, 24, _actions[a].Label, GumpStyle.Command);
            }

            var current = _topics[topic];

            builder.AddHtml(NavWidth + 30, 76, GumpStyle.Width - NavWidth - 50, 26, current.Title, GumpStyle.Gold, size: 4);
            builder.AddHtml(
                NavWidth + 30, ContentTop, GumpStyle.Width - NavWidth - 50, ContentHeight, WelcomeGuide.Body(current), GumpStyle.Text,
                scrollbar: WelcomeGuide.NeedsScroll(current)
            );

            if (topic + 1 < count)
            {
                builder.AddButton(GumpStyle.Width - 290, GumpStyle.Height - 44, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, 0, GumpButtonType.Page, PageOf(topic + 1, _first, count));
                builder.AddHtml(GumpStyle.Width - 250, GumpStyle.Height - 42, 110, 20, "Next topic", GumpStyle.Text);
            }
        }
    }

    public override void OnResponse(NetState sender, in RelayInfo info)
    {
        if (info.ButtonID != 0 && sender.Mobile is PlayerMobile player)
        {
            _onAction?.Invoke(player, info.ButtonID);
        }
    }
}
