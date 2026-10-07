using Server;
using Server.Gumps;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The look the shard's windows share with the [Welcome guide: a dark panel in a stone frame, the shard name in gold with its
/// tagline beneath, gold headings, white text, arrow buttons, and the same fixed size so a player moving between windows sees
/// one place. [SkillClasses, [SkillBank and [Mastery are built from these pieces.
/// </summary>
public static class GumpStyle
{
    public const string Gold = "#FFD060";
    public const string Text = "#FFFFFF";
    public const string Muted = "#BBBBBB";
    public const string Dim = "#999999";
    public const string Command = "#8FD3FF";
    public const string Good = "#8FE08F";
    public const string Warning = "#FFB347";

    public const int Width = 640;
    public const int Height = 500;

    /// <summary>Art for an arrow button (normal and pressed) and the round choice buttons (off and on).</summary>
    public const int ArrowNormal = 4005;
    public const int ArrowPressed = 4007;
    public const int ChoiceOff = 210;
    public const int ChoiceOn = 211;

    /// <summary>The panel, the shard name and a line under it saying what this window is.</summary>
    public static void Frame(ref DynamicGumpBuilder builder, string title, string subtitle, int width = Width, int height = Height)
    {
        builder.AddBackground(0, 0, width, height, 9200);
        builder.AddImageTiled(10, 10, width - 20, height - 20, 2624);
        builder.AddHtml(20, 18, width - 40, 24, title, Gold, size: 5, align: TextAlignment.Center);
        builder.AddHtml(20, 44, width - 40, 20, subtitle, Muted, align: TextAlignment.Center);
    }

    /// <summary>A labelled arrow button that sends a reply, as in the guide's footer.</summary>
    public static void FooterButton(ref DynamicGumpBuilder builder, int x, string label, int buttonId, int labelWidth = 110, int height = Height)
    {
        builder.AddButton(x, height - 44, ArrowNormal, ArrowPressed, buttonId);
        builder.AddHtml(x + 40, height - 42, labelWidth, 20, label, Text);
    }

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

    /// <summary>A progress bar drawn with text: a run of filled bars then a run of empty ones. A bold bar is about three pixels wide, so 100 segments is about 300 pixels.</summary>
    public static void Bar(ref DynamicGumpBuilder builder, int x, int y, double fraction, string fillColor, int segments = 80)
    {
        var filled = FilledSegments(fraction, segments);
        // Bold, so the thin strokes carry enough weight to read as a bar at normal size.
        var text = $"<B>{Colored(new string('|', filled), fillColor)}{Colored(new string('|', segments - filled), "#555555")}</B>";
        builder.AddHtml(x, y, segments * 4 + 20, 18, text, Text);
    }

    /// <summary>A number of tenths of a skill point as players read it: 123 is "12.3".</summary>
    public static string Points(int tenths) =>
        (tenths / 10.0).ToString("0.0", System.Globalization.CultureInfo.InvariantCulture);
}
