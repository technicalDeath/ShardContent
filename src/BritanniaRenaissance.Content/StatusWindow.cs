using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A medium window for one thing and what to do about it (Gump-Style-Guide.md): a banner saying where it stands (a gem, in the state's
/// colour), a few sentences, a purple game-action oval that changes it, and the footer with a hint and a blue Close. [IntentStatus,
/// [TravelWarning and a Backpack Ward's double-click use it.
/// </summary>
public sealed class StatusWindow : DynamicGump
{
    public sealed record WindowButton(string Label, int ButtonId);

    private const int Width = GumpStyle.MediumWidth;
    private const int LineHeight = 18;
    private const int TextWidth = Width - 2 * GumpStyle.Margin;
    private const int TextTop = 126;
    private const int ButtonHeight = 36;

    private readonly string _title;
    private readonly string _subtitle;
    private readonly string _headline;
    private readonly string _headlineColor;
    private readonly IReadOnlyList<string> _paragraphs;
    private readonly IReadOnlyList<WindowButton> _buttons;
    private readonly string _footerHint;
    private readonly Action<PlayerMobile, int>? _onButton;

    public StatusWindow(
        string title, string subtitle, string headline, string headlineColor, IReadOnlyList<string> paragraphs,
        IReadOnlyList<WindowButton> buttons, string footerHint, Action<PlayerMobile, int>? onButton
    ) : base(GumpStyle.MediumX, GumpStyle.MediumY)
    {
        _title = title;
        _subtitle = subtitle;
        _headline = headline;
        _headlineColor = headlineColor;
        _paragraphs = paragraphs;
        _buttons = buttons;
        _footerHint = footerHint;
        _onButton = onButton;
    }

    public override bool Singleton => true;

    /// <summary>Lines the paragraphs need, with a blank line between them, a little on the generous side.</summary>
    public static int EstimateLines(IReadOnlyList<string> paragraphs) =>
        paragraphs.Sum(p => GumpStyle.LinesFor(StripTags(p), TextWidth)) + Math.Max(0, paragraphs.Count - 1);

    /// <summary>The window is as tall as its text and buttons need, never taller than the other windows.</summary>
    public static int HeightFor(IReadOnlyList<string> paragraphs, int buttons) =>
        Math.Clamp(TextTop + EstimateLines(paragraphs) * LineHeight + 12 + buttons * ButtonHeight + GumpStyle.FooterRoom, 280, GumpStyle.Height);

    private static string StripTags(string text) => System.Text.RegularExpressions.Regex.Replace(text, "<[^>]*>", string.Empty);

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        var height = HeightFor(_paragraphs, _buttons.Count);

        builder.AddPage();
        GumpStyle.Frame(ref builder, _title, _subtitle, Width, height);

        // The headline's colour says where it stands: green protected, red exposed, anything else a plain note. Its words say it too.
        GumpStyle.Banner(ref builder, GumpStyle.KindOf(_headlineColor), _headline, word: false, color: _headlineColor, width: TextWidth - 38);

        var buttonsRoom = _buttons.Count * ButtonHeight;
        var textHeight = height - TextTop - buttonsRoom - GumpStyle.FooterRoom;
        var body = string.Join("<BR><BR>", _paragraphs.Select(p => WelcomeGuide.Highlight(p, false)));
        builder.AddHtml(GumpStyle.Margin, TextTop, TextWidth, textHeight, body, GumpStyle.Text, scrollbar: EstimateLines(_paragraphs) * LineHeight > textHeight);

        for (var i = 0; i < _buttons.Count; i++)
        {
            GumpStyle.GameAction(ref builder, GumpStyle.Margin, height - GumpStyle.FooterRoom - buttonsRoom + i * ButtonHeight + 6, _buttons[i].Label, _buttons[i].ButtonId);
        }

        GumpStyle.Footer(ref builder, _footerHint, Width, height, hintWidth: GumpStyle.CloseX(Width) - 2 * GumpStyle.Margin);
    }

    public override void OnResponse(NetState sender, in RelayInfo info)
    {
        if (info.ButtonID != 0 && sender.Mobile is PlayerMobile player)
        {
            _onButton?.Invoke(player, info.ButtonID);
        }
    }
}
