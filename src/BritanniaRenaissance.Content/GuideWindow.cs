using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The topic window the [Welcome guide and [SkillClasses share: a list of topics on the left (blue ovals, the one you are on pressed and in
/// gold), the selected topic's text on the right, "Next topic" and Close below. A window may start on any topic, may add blue ovals under the
/// list that open another window, and may group its topics into chapters shown as tabs across the top: then the list holds only the topics of
/// the chapter being read, so a guide with many pages does not crowd the list.
/// </summary>
public sealed class GuideWindow : DynamicGump
{
    public sealed record WindowAction(string Label, int ButtonId);

    private const int NavWidth = 190;
    private const int ListX = 16;

    /// <summary>The topic ovals all share the 176 px width, so a title of up to about 25 letters fits.</summary>
    public const int TopicOvalWidth = 176;

    private const int FooterRule = GumpStyle.Height - GumpStyle.FooterRoom;

    // Without tabs the text starts just under the header; with tabs, under the tab row.
    private const int PlainTitleY = 84;
    private const int PlainListTop = 90;
    private const int PlainTextTop = 112;
    private const int TabsY = 80;
    private const int TabListTop = 118;
    private const int TabTitleY = 114;
    private const int TabContentTop = 142;

    public const int ContentHeight = FooterRule - PlainTextTop - 10;

    private readonly string _title;
    private readonly string _subtitle;
    private readonly string _footerHint;
    private readonly IReadOnlyList<WelcomeGuide.Topic> _topics;
    private readonly int _first;
    private readonly IReadOnlyList<WindowAction> _actions;
    private readonly Action<PlayerMobile, int>? _onAction;
    private readonly IReadOnlyList<WelcomeGuide.Chapter>? _chapters;

    public GuideWindow(
        string title, string subtitle, string footerHint, IReadOnlyList<WelcomeGuide.Topic> topics, int firstTopic = 0,
        IReadOnlyList<WindowAction>? actions = null, Action<PlayerMobile, int>? onAction = null,
        IReadOnlyList<WelcomeGuide.Chapter>? chapters = null
    ) : base(GumpStyle.LargeX, GumpStyle.LargeY)
    {
        _title = title;
        _subtitle = subtitle;
        _footerHint = footerHint;
        _topics = topics;
        _first = Math.Clamp(firstTopic, 0, Math.Max(0, topics.Count - 1));
        _actions = actions ?? [];
        _onAction = onAction;
        _chapters = chapters;
    }

    public override bool Singleton => true;

    /// <summary>The height of the text box when the window has tabs.</summary>
    public const int TabbedContentHeight = FooterRule - TabContentTop - 10;

    /// <summary>The client-side page of topic <paramref name="topic"/>: the window opens on page 1, so the first topic shown takes it.</summary>
    public static int PageOf(int topic, int first, int count) => (topic - first + count) % count + 1;

    // The chapter tabs are stone tabs, the same stone as the window's frame: art 5007 for a chapter that can be opened, and 5006 (the tab
    // sitting on its ledge) for the open one, tinted amber so it is plain which one you are in. Both pieces are 88 pixels wide, so six
    // tabs and their gaps fit the 640-pixel window.
    public const int TabArtOff = 5007;
    public const int TabArtOn = 5006;
    public const int TabOnHue = 47;
    public const int TabWidth = 88;
    public const int TabGap = 4;
    private const string TabInk = "#202020";
    private const string TabInkOn = "#000000";

    /// <summary>The width of a row of <paramref name="count"/> tabs.</summary>
    public static int TabRowWidth(int count) => count * TabWidth + Math.Max(0, count - 1) * TabGap;

    /// <summary>Whether a chapter title fits its tab: about 7.5 pixels a letter, with 8 pixels of margin.</summary>
    public static bool TabTitleFits(string title) => Math.Ceiling(title.Length * 7.5) + 8 <= TabWidth;

    /// <summary>Whether a topic title fits the blue oval of the list: the narrow label room inside the rim and gloss.</summary>
    public static bool TopicTitleFits(string title) => GumpStyle.OvalWidth(title) <= TopicOvalWidth;

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        var count = _topics.Count;

        builder.AddPage();
        GumpStyle.Frame(ref builder, _title, _subtitle);

        var tabbed = _chapters is { Count: > 1 };
        var dividerTop = tabbed ? TabListTop - 6 : PlainListTop - 6;
        builder.AddImageTiled(NavWidth + 14, dividerTop, 2, FooterRule - dividerTop - 8, 2701);

        // Close is button 0, so it also answers a right-click.
        GumpStyle.Footer(ref builder, _footerHint, GumpStyle.Width, GumpStyle.Height);

        var keyIndex = _topics.Select((t, i) => (t.Key, i)).ToDictionary(p => p.Key, p => p.i);

        for (var topic = 0; topic < count; topic++)
        {
            builder.AddPage(PageOf(topic, _first, count));

            // The topics shown in the list: all of them, or only those of this topic's chapter.
            var chapter = tabbed ? _chapters!.First(c => c.TopicKeys.Contains(_topics[topic].Key)) : null;
            var shown = chapter is null
                ? Enumerable.Range(0, count).ToArray()
                : chapter.TopicKeys.Select(k => keyIndex[k]).ToArray();

            if (chapter is not null)
            {
                var x = 24;

                foreach (var other in _chapters!)
                {
                    var here = other == chapter;
                    var target = keyIndex[other.TopicKeys[0]];

                    if (here)
                    {
                        builder.AddImage(x, TabsY, TabArtOn, TabOnHue);
                    }
                    else
                    {
                        builder.AddButton(x, TabsY, TabArtOff, TabArtOff, 0, GumpButtonType.Page, PageOf(target, _first, count));
                    }

                    // A click on the label reaches the tab under it. The open tab's ledge takes the bottom of its art, so its label sits higher.
                    builder.AddHtml(x, TabsY + (here ? 0 : 2), TabWidth, 18, other.Title, here ? TabInkOn : TabInk, align: TextAlignment.Center);
                    x += TabWidth + TabGap;
                }

                // The tabs' ledge: the open tab joins it, the others sit above it.
                builder.AddImageTiled(GumpStyle.RuleInset, TabsY + 23, GumpStyle.Width - 2 * GumpStyle.RuleInset, 4, GumpStyle.RuleArt);
            }

            // The topics are blue ovals 40 pixels apart, squeezed when there are many so the last one stays above the buttons under the list.
            var listTop = tabbed ? TabListTop : PlainListTop;
            var actionsTop = FooterRule - 10 - _actions.Count * 36;
            var step = Math.Min(40, (actionsTop - listTop) / Math.Max(1, shown.Length));

            for (var i = 0; i < shown.Length; i++)
            {
                var y = listTop + i * step;
                var title = _topics[shown[i]].Title;

                if (shown[i] == topic)
                {
                    GumpStyle.MenuActionHere(ref builder, ListX, y, title, TopicOvalWidth, GumpStyle.Gold);
                }
                else
                {
                    GumpStyle.MenuAction(ref builder, ListX, y, title, 0, GumpButtonType.Page, PageOf(shown[i], _first, count), TopicOvalWidth);
                }
            }

            for (var a = 0; a < _actions.Count; a++)
            {
                GumpStyle.MenuAction(ref builder, ListX, actionsTop + 6 + a * 36, _actions[a].Label, _actions[a].ButtonId, width: TopicOvalWidth);
            }

            var current = _topics[topic];
            var titleY = tabbed ? TabTitleY : PlainTitleY;
            var textTop = tabbed ? TabContentTop : PlainTextTop;
            var textHeight = tabbed ? TabbedContentHeight : ContentHeight;
            var textWidth = GumpStyle.Width - NavWidth - 50;

            builder.AddHtml(NavWidth + 30, titleY, textWidth, 26, current.Title, GumpStyle.Gold);
            builder.AddHtml(
                NavWidth + 30, textTop, textWidth, textHeight, WelcomeGuide.Body(current), GumpStyle.Text,
                scrollbar: WelcomeGuide.NeedsScroll(current, textHeight)
            );

            if (topic + 1 < count)
            {
                GumpStyle.MenuAction(
                    ref builder, GumpStyle.CloseX(GumpStyle.Width) - 8 - GumpStyle.OvalWidth("Next topic"), GumpStyle.FooterButtonsY(GumpStyle.Height),
                    "Next topic", 0, GumpButtonType.Page, PageOf(topic + 1, _first, count)
                );
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
