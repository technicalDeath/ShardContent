using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// A small window in the guide's style for one thing and what to do about it: a headline saying where it stands, a few sentences,
/// and buttons that change it. [IntentStatus, [TravelWarning and a Backpack Ward's double-click use it.
/// </summary>
public sealed class StatusWindow : DynamicGump
{
    public sealed record WindowButton(string Label, int ButtonId);

    private const int Width = 480;
    private const int CharactersPerLine = 52;
    private const int LineHeight = 18;
    private const int TextTop = 120;
    private const int ButtonHeight = 40;
    private const int FooterRoom = 70;

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
    ) : base(80, 60)
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
        paragraphs.Sum(p => (StripTags(p).Length + CharactersPerLine - 1) / CharactersPerLine) + Math.Max(0, paragraphs.Count - 1);

    /// <summary>The window is as tall as its text and buttons need, never taller than the other windows.</summary>
    public static int HeightFor(IReadOnlyList<string> paragraphs, int buttons) =>
        Math.Clamp(TextTop + EstimateLines(paragraphs) * LineHeight + buttons * ButtonHeight + FooterRoom, 260, GumpStyle.Height);

    private static string StripTags(string text) => System.Text.RegularExpressions.Regex.Replace(text, "<[^>]*>", string.Empty);

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        var height = HeightFor(_paragraphs, _buttons.Count);

        builder.AddPage();
        GumpStyle.Frame(ref builder, _title, _subtitle, Width, height);

        builder.AddHtml(30, 80, Width - 60, 28, _headline, _headlineColor, size: 4);

        var textHeight = height - TextTop - _buttons.Count * ButtonHeight - FooterRoom + 20;
        var body = string.Join("<BR><BR>", _paragraphs.Select(p => WelcomeGuide.Highlight(p, false)));
        builder.AddHtml(30, TextTop, Width - 60, textHeight, body, GumpStyle.Text, scrollbar: EstimateLines(_paragraphs) * LineHeight > textHeight);

        for (var i = 0; i < _buttons.Count; i++)
        {
            var y = height - FooterRoom - (_buttons.Count - i) * ButtonHeight + 24;

            builder.AddButton(30, y, GumpStyle.ArrowNormal, GumpStyle.ArrowPressed, _buttons[i].ButtonId);
            builder.AddHtml(72, y + 4, Width - 120, 22, _buttons[i].Label, GumpStyle.Gold, fontStyle: 1);
        }

        builder.AddHtml(24, height - 42, Width - 180, 20, _footerHint, GumpStyle.Dim);
        GumpStyle.FooterButton(ref builder, Width - 120, "Close", 0, 60, height);
    }

    public override void OnResponse(NetState sender, in RelayInfo info)
    {
        if (info.ButtonID != 0 && sender.Mobile is PlayerMobile player)
        {
            _onButton?.Invoke(player, info.ButtonID);
        }
    }
}
