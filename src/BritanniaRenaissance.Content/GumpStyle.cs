using Server;
using Server.Gumps;

namespace BritanniaRenaissance.Content;

/// <summary>What a banner line says it is: an action that worked, a refusal or a risk, or a plain fact. Each has a gem and a word.</summary>
public enum BannerKind
{
    Done,
    Danger,
    Note
}

/// <summary>
/// The one look the shard's windows share (ShardContent/docs/Gump-Style-Guide.md, approved by the owner 2026-10-07): a dark panel in a stone
/// frame, a gold title and a muted line under it, a gold rule, white text, gems with a word for status, and a footer with a hint on the left and
/// a blue Close oval on the right. Every button is the same oval, and its colour says what it does: green OKAY accepts and red CANCEL declines a
/// question, blue moves around the windows, purple changes the game, and a purple dot is the chosen one of a pick-one group.
/// Colours are always given as #RRGGBB (unset text renders near black); text is never bold, italic or `fontStyle` (the client draws bold as solid
/// blocks and ignores `fontStyle`); nothing is half transparent (`AddAlphaRegion` fades the whole panel). StyleGuideTests fails the build when a
/// window breaks these.
/// </summary>
public static class GumpStyle
{
    // ---- colours

    /// <summary>Titles, headings, numbers that matter. Never "selected".</summary>
    public const string Gold = "#FFD060";

    public const string Text = "#FFFFFF";

    /// <summary>Subtitles, secondary lines, column headers, the labels of the choices not chosen.</summary>
    public const string Muted = "#BBBBBB";

    /// <summary>Footer hints and footnotes: the dimmest text allowed on the dark panel.</summary>
    public const string Dim = "#999999";

    /// <summary>[Commands and the Note banner.</summary>
    public const string Command = "#8FD3FF";

    /// <summary>Protected, saved, ready, claimed.</summary>
    public const string Good = "#8FE08F";

    /// <summary>Exposed, refused, destructive.</summary>
    public const string Danger = "#FF7B7B";

    /// <summary>The label of the chosen radio.</summary>
    public const string Chosen = "#D9B8FF";

    /// <summary>The unfilled part of a bar.</summary>
    public const string BarEmpty = "#555555";

    /// <summary>The ink of the dark emboss behind a white oval label.</summary>
    private const string EmbossInk = "#101010";

    // ---- window classes: each has one size family and one first-open position

    /// <summary>Large (the guide, Skill Bank, Mastery): 640 x 500.</summary>
    public const int Width = 640;

    public const int Height = 500;
    public const int LargeX = 40;
    public const int LargeY = 30;

    /// <summary>Medium (status windows, the camp list): 480 wide, as tall as the content, never past <see cref="Height"/>.</summary>
    public const int MediumWidth = 480;

    public const int MediumX = 80;
    public const int MediumY = 60;

    /// <summary>Dialog (confirmations): 440 wide.</summary>
    public const int DialogWidth = 440;

    public const int DialogX = 100;
    public const int DialogY = 70;

    // ---- the grid

    /// <summary>Where text and buttons start from the left edge, and stop from the right edge.</summary>
    public const int Margin = 34;

    /// <summary>Rules run from this far in from each side.</summary>
    public const int RuleInset = 28;

    public const int HeaderRuleY = 70;

    /// <summary>The banner line and everything under the header starts here.</summary>
    public const int ContentTop = 82;

    /// <summary>The footer rule is this far above the bottom edge.</summary>
    public const int FooterRoom = 62;

    // ---- art

    public const int FrameArt = 9200;
    public const int FrameTile = 2624;
    public const int RuleArt = 2700;
    public const int RowRuleArt = 96;
    public const int WellArt = 2524;
    public const int TickOff = 210;
    public const int TickOn = 211;
    public const int GemDone = 5826;
    public const int GemDanger = 5830;
    public const int GemNote = 2151;

    /// <summary>The classic green OKAY (2450, pressed 2451) and red CANCEL (2453, pressed 2454), the words in the art.</summary>
    public const int OkayArt = 2450;

    public const int CancelArt = 2453;

    /// <summary>
    /// The shard's own oval art (data/client/gumps, made by tools/gump-art/make_window_buttons.py): for width k of <see cref="OvalWidths"/>,
    /// base + 2k is the normal picture and base + 2k + 1 the pressed one. Blue is a menu action, purple a game action.
    /// </summary>
    public const int BlueOvalArt = 62010;

    public const int PurpleOvalArt = 62020;

    /// <summary>The radio: a 22 x 21 oval, purple when chosen (a picture) and dull stone otherwise (a button, art and pressed art).</summary>
    public const int ChosenRadioArt = 62030;

    public const int StoneRadioArt = 62040;
    public const int RadioWidth = 22;

    public const int OvalHeight = 21;
    public static readonly int[] OvalWidths = [56, 88, 128, 176, 232];

    // ---- text size: the client's font is about this many pixels a letter, so a line holds width / 6.9 letters

    private const double PixelsPerLetter = 6.9;

    /// <summary>The letters a line of <paramref name="widthPixels"/> holds.</summary>
    public static int CharsPerLine(int widthPixels) => (int)Math.Round(widthPixels / PixelsPerLetter);

    /// <summary>The lines <paramref name="plainText"/> (no markup) takes in a box <paramref name="widthPixels"/> wide.</summary>
    public static int LinesFor(string plainText, int widthPixels) => Math.Max(1, (plainText.Length + CharsPerLine(widthPixels) - 1) / CharsPerLine(widthPixels));

    /// <summary>The narrowest oval width that holds <paramref name="label"/> with room for the rim and the gloss at each end.</summary>
    public static int OvalWidth(string label)
    {
        var needed = (int)Math.Ceiling(label.Length * 6.3) + 20;

        return OvalWidths.FirstOrDefault(w => w >= needed, OvalWidths[^1]);
    }

    private static int OvalArtFor(int baseArt, int width) => baseArt + 2 * Array.IndexOf(OvalWidths, width);

    // ---- the frame, header and footer

    /// <summary>The panel, the title (gold, display font) and a muted line under it saying what the window is for, and the gold rule.</summary>
    public static void Frame(ref DynamicGumpBuilder builder, string title, string subtitle, int width = Width, int height = Height)
    {
        builder.AddBackground(0, 0, width, height, FrameArt);
        builder.AddImageTiled(10, 10, width - 20, height - 20, FrameTile);
        builder.AddHtml(20, 16, width - 40, 24, title, Gold, size: 5, align: TextAlignment.Center);
        builder.AddHtml(20, 46, width - 40, 18, subtitle, Muted, align: TextAlignment.Center);
        Rule(ref builder, RuleInset, HeaderRuleY, width - 2 * RuleInset);
    }

    /// <summary>A gold rule, 4 pixels tall, as under the header and above the footer.</summary>
    public static void Rule(ref DynamicGumpBuilder builder, int x, int y, int width) => builder.AddImageTiled(x, y, width, 4, RuleArt);

    /// <summary>A thin rule under a heading or a table row.</summary>
    public static void RowRule(ref DynamicGumpBuilder builder, int x, int y, int width) => builder.AddImageTiled(x, y, width, 3, RowRuleArt);

    /// <summary>The y of the footer's buttons.</summary>
    public static int FooterButtonsY(int height) => height - 48;

    /// <summary>Where the Close oval starts: its right edge is <see cref="Margin"/> in from the edge.</summary>
    public static int CloseX(int width) => width - Margin - OvalWidths[0];

    /// <summary>
    /// The rule, the hint (dim, plain) at the left and, unless a window has its own, the blue Close oval at the right. Button 0 is Close; a
    /// right-click on a gump sends 0 too, so it always closes.
    /// </summary>
    public static void Footer(ref DynamicGumpBuilder builder, string hint, int width, int height, bool close = true, int hintWidth = 300)
    {
        Rule(ref builder, RuleInset, height - FooterRoom, width - 2 * RuleInset);

        if (hint.Length > 0)
        {
            builder.AddHtml(Margin, height - 44, hintWidth, 20, hint, Dim);
        }

        if (close)
        {
            MenuAction(ref builder, CloseX(width), FooterButtonsY(height), "Close", 0);
        }
    }

    // ---- buttons: one oval, told apart by colour

    private static void Oval(ref DynamicGumpBuilder builder, int baseArt, int x, int y, string label, int buttonId, GumpButtonType type, int param, int width, bool pressed = false, string labelColor = Text)
    {
        width = width == 0 ? OvalWidth(label) : width;
        var art = OvalArtFor(baseArt, width);

        // A picture of the pressed oval (not a button) stands for "the one you are on", as the chosen topic of the guide's list.
        if (pressed)
        {
            builder.AddImage(x, y, art + 1);
        }
        else
        {
            builder.AddButton(x, y, art, art + 1, buttonId, type, param);
        }

        // White on the oval over a dark shadow one pixel down and right; a click on the words reaches the oval under them.
        builder.AddHtml(x + 1, y + 3, width, 18, label, EmbossInk, align: TextAlignment.Center);
        builder.AddHtml(x, y + 2, width, 18, label, labelColor, align: TextAlignment.Center);
    }

    /// <summary>
    /// A blue oval: moving around the windows (Close, Back, Next, a link to another window). Never changes the game. The width is the
    /// narrowest that holds the label, unless one of <see cref="OvalWidths"/> is given (a list of ovals shares one width).
    /// </summary>
    public static void MenuAction(
        ref DynamicGumpBuilder builder, int x, int y, string label, int buttonId, GumpButtonType type = GumpButtonType.Reply, int param = 0, int width = 0
    ) => Oval(ref builder, BlueOvalArt, x, y, label, buttonId, type, param, width);

    /// <summary>The blue oval of the topic the reader is on: its pressed picture (not a button), with the label in the colour given.</summary>
    public static void MenuActionHere(ref DynamicGumpBuilder builder, int x, int y, string label, int width, string labelColor)
    {
        Oval(ref builder, BlueOvalArt, x, y, label, 0, GumpButtonType.Reply, 0, width, pressed: true, labelColor);
    }

    /// <summary>A purple oval: something that changes the world or the character. At most one or two to a window; the left-most is the main one.</summary>
    public static void GameAction(ref DynamicGumpBuilder builder, int x, int y, string label, int buttonId) =>
        Oval(ref builder, PurpleOvalArt, x, y, label, buttonId, GumpButtonType.Reply, 0, 0);

    /// <summary>The classic green OKAY and red CANCEL, for answering a question the window asked: OKAY at one end, CANCEL at the other.</summary>
    public static void OkayCancel(ref DynamicGumpBuilder builder, int okayX, int cancelX, int y, int okayId, int cancelId)
    {
        builder.AddButton(okayX, y, OkayArt, OkayArt + 1, okayId);
        builder.AddButton(cancelX, y, CancelArt, CancelArt + 1, cancelId);
    }

    /// <summary>
    /// One choice of a pick-one group: a small oval with its label beside it. The chosen one is a purple picture that does nothing when
    /// clicked, with a lavender label; the others are dull stone buttons with a muted label.
    /// </summary>
    public static void RadioChoice(ref DynamicGumpBuilder builder, int x, int y, string label, bool chosen, int buttonId, int labelWidth = 80)
    {
        if (chosen)
        {
            builder.AddImage(x, y, ChosenRadioArt);
        }
        else
        {
            builder.AddButton(x, y, StoneRadioArt, StoneRadioArt + 1, buttonId);
        }

        builder.AddHtml(x + RadioWidth + 8, y + 2, labelWidth, 18, label, chosen ? Chosen : Muted);
    }

    /// <summary>An independent yes or no: a tick box with its label beside it.</summary>
    public static void Tick(ref DynamicGumpBuilder builder, int x, int y, string label, int switchId, int labelWidth, bool ticked = false)
    {
        builder.AddCheckbox(x, y, TickOff, TickOn, ticked, switchId);
        builder.AddHtml(x + 32, y + 2, labelWidth, 18, label, Muted);
    }

    // ---- status: a gem and a word, never colour alone

    public static string BannerWord(BannerKind kind) => kind switch
    {
        BannerKind.Done => "Done:",
        BannerKind.Danger => "Danger:",
        _ => "Note:"
    };

    public static string BannerColor(BannerKind kind) => kind switch
    {
        BannerKind.Done => Good,
        BannerKind.Danger => Danger,
        _ => Command
    };

    /// <summary>The kind a status colour stands for: green is Done, red is Danger, anything else a Note.</summary>
    public static BannerKind KindOf(string color) => color switch
    {
        Good => BannerKind.Done,
        Danger => BannerKind.Danger,
        _ => BannerKind.Note
    };

    /// <summary>
    /// The banner line: a gem, the word of its kind (unless <paramref name="word"/> is false, for a status whose text already says ON or OFF)
    /// and the sentence, in the kind's colour. One line at <see cref="ContentTop"/> in every window; a dialog's may take several.
    /// </summary>
    public static void Banner(
        ref DynamicGumpBuilder builder, BannerKind kind, string text, int x = Margin, int y = ContentTop, int width = Width - 2 * Margin - 38,
        int height = 24, bool word = true, string? color = null
    )
    {
        builder.AddImage(x, y, kind switch { BannerKind.Done => GemDone, BannerKind.Danger => GemDanger, _ => GemNote });
        builder.AddHtml(x + 38, y + 4, width, height, word ? $"{BannerWord(kind)} {text}" : text, color ?? BannerColor(kind));
    }

    // ---- headings and tables

    /// <summary>A gold heading with a thin rule under it.</summary>
    public static void SectionHeading(ref DynamicGumpBuilder builder, int x, int y, int width, string text)
    {
        builder.AddHtml(x, y, width, 20, text, Gold);
        RowRule(ref builder, x, y + 22, width);
    }

    /// <summary>One cell of a table: text at a fixed x, wide enough for its column, right-aligned for numbers.</summary>
    public static void Cell(ref DynamicGumpBuilder builder, int x, int y, int width, string text, string color, TextAlignment align = TextAlignment.Left) =>
        builder.AddHtml(x, y, width, 20, text, color, align: align);

    /// <summary>The muted column headings of a table, and the rule under them.</summary>
    public static void TableHeader(ref DynamicGumpBuilder builder, int y, int width, params (int X, int Width, string Text, TextAlignment Align)[] columns)
    {
        foreach (var (x, w, text, align) in columns)
        {
            Cell(ref builder, x, y, w, text, Muted, align);
        }

        RowRule(ref builder, RuleInset, y + 20, width - 2 * RuleInset);
    }

    /// <summary>What a list says when it is empty: what is empty, why, and what to do. Muted, centred.</summary>
    public static void EmptyState(ref DynamicGumpBuilder builder, int x, int y, int width, int height, string text) =>
        builder.AddHtml(x, y, width, height, text, Muted, align: TextAlignment.Center);

    // ---- paging

    /// <summary>"Back", "Page n of m" and "Next" left of the Close oval: the same words and places in every window that pages.</summary>
    public static void Pager(ref DynamicGumpBuilder builder, int width, int height, int page, int pages, int previousId, int nextId)
    {
        if (pages <= 1)
        {
            return;
        }

        var y = FooterButtonsY(height);
        var nextX = CloseX(width) - 8 - OvalWidths[0];
        var labelX = nextX - 88;
        var backX = labelX - 8 - OvalWidths[0];

        if (page > 0)
        {
            MenuAction(ref builder, backX, y, "Back", previousId);
        }

        builder.AddHtml(labelX, y + 4, 80, 20, $"Page {page + 1} of {pages}", Muted, align: TextAlignment.Center);

        if (page + 1 < pages)
        {
            MenuAction(ref builder, nextX, y, "Next", nextId);
        }
    }

    // ---- text and numbers

    public static string Colored(string text, string color) => $"<BASEFONT COLOR={color}>{text}</BASEFONT>";

    /// <summary>How many of <paramref name="segments"/> a fraction fills, never none for a start and never full before the end.</summary>
    public static int FilledSegments(double fraction, int segments)
    {
        if (fraction <= 0.0)
        {
            return 0;
        }

        if (fraction >= 1.0)
        {
            return segments;
        }

        return Math.Clamp((int)Math.Round(fraction * segments), 1, segments - 1);
    }

    /// <summary>
    /// A progress bar drawn with text: a run of filled bars then a run of empty ones. A bold bar is about three pixels wide, so 100 segments is
    /// about 300 pixels. The bar is the one place bold is used: thin strokes need the weight to read as a bar.
    /// </summary>
    public static void Bar(ref DynamicGumpBuilder builder, int x, int y, double fraction, string fillColor, int segments = 80)
    {
        var filled = FilledSegments(fraction, segments);
        var text = $"<B>{Colored(new string('|', filled), fillColor)}{Colored(new string('|', segments - filled), BarEmpty)}</B>";
        builder.AddHtml(x, y, segments * 4 + 20, 18, text, Text);
    }

    /// <summary>A number of tenths of a skill point as players read it: 123 is "12.3".</summary>
    public static string Points(int tenths) =>
        (tenths / 10.0).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture);
}
