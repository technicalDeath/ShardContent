using System.Globalization;
using BritanniaRenaissance.Content;
using Server;
using Server.Gumps;
using Server.Network;

namespace Alpha3TestOnlyTools;

// Test-only: draws a gump from a small text script, so a window design can be tried in the real client by editing a file and re-running
// the command, with no rebuild or restart. [TestOnlyGump <player-serial> <script-name>] reads <scripts folder>\<script-name>.gs.
// One command per line; "#" starts a comment; text arguments are quoted; options after the text are key=value.
//   pos X Y                       where the window opens (first line)
//   frame "Title" "Subtitle" [W H]   the shard's current frame (GumpStyle.Frame)
//   page N
//   bg X Y W H ID                 AddBackground (a 9-piece frame from art ID to ID+8)
//   tile X Y W H ID               AddImageTiled
//   img X Y ID [HUE]              AddImage
//   html X Y W H "text" [color=#RRGGBB] [size=N] [style=N] [align=left|center|right] [scroll=1]
//   label X Y HUE "text"          AddLabel (a hued unicode label)
//   button X Y NORMAL PRESSED ID [page=N]   a reply button (or a page button with page=N)
//   check X Y OFF ON SELECTED SWITCH, radio X Y OFF ON SELECTED SWITCH
// Nothing here ships.
public sealed class GumpScriptProbe : DynamicGump
{
    public static readonly string ScriptsFolder = Environment.GetEnvironmentVariable("QOL_GUMP_SCRIPTS")
                                                 ?? @"C:\Users\brend\Documents\Britannia Renaissance\work\qol\gump-scripts";

    private readonly string[] _lines;

    public GumpScriptProbe(string[] lines, int x, int y) : base(x, y) => _lines = lines;

    public override bool Singleton => true;

    public static GumpScriptProbe? Load(string name, out string error)
    {
        error = "";
        var path = Path.Combine(ScriptsFolder, name + ".gs");

        if (!File.Exists(path))
        {
            error = $"No script {path}";
            return null;
        }

        var lines = File.ReadAllLines(path);
        int x = 40, y = 30;

        foreach (var line in lines)
        {
            var tokens = Tokenize(line);

            if (tokens.Count >= 3 && tokens[0] == "pos")
            {
                x = int.Parse(tokens[1], CultureInfo.InvariantCulture);
                y = int.Parse(tokens[2], CultureInfo.InvariantCulture);
            }
        }

        return new GumpScriptProbe(lines, x, y);
    }

    public static List<string> Tokenize(string line)
    {
        var tokens = new List<string>();
        var i = 0;

        while (i < line.Length)
        {
            if (char.IsWhiteSpace(line[i]))
            {
                i++;
                continue;
            }

            if (line[i] == '#')
            {
                break;
            }

            if (line[i] == '"')
            {
                var end = line.IndexOf('"', i + 1);
                end = end < 0 ? line.Length : end;
                tokens.Add(line[(i + 1)..end].Replace("\\n", "<BR>"));
                i = end + 1;
                continue;
            }

            var start = i;

            while (i < line.Length && !char.IsWhiteSpace(line[i]))
            {
                // key="quoted value" keeps the quotes out
                if (line[i] == '"')
                {
                    var end = line.IndexOf('"', i + 1);
                    i = end < 0 ? line.Length : end;
                }

                i++;
            }

            tokens.Add(line[start..i]);
        }

        return tokens;
    }

    private static int N(List<string> t, int index) => int.Parse(t[index], CultureInfo.InvariantCulture);

    // Options come after the positional arguments (the quoted text is among them), so a sample text that looks like key=value is not read as one.
    private static string Option(List<string> t, string key, string fallback = "", int from = 6)
    {
        for (var i = from; i < t.Count; i++)
        {
            if (t[i].StartsWith(key + "=", StringComparison.Ordinal))
            {
                return t[i][(key.Length + 1)..].Trim('"');
            }
        }

        return fallback;
    }

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        foreach (var line in _lines)
        {
            var t = Tokenize(line);

            if (t.Count == 0)
            {
                continue;
            }

            switch (t[0])
            {
                case "page":
                    builder.AddPage(N(t, 1));
                    break;
                case "frame":
                    GumpStyle.Frame(ref builder, t[1], t.Count > 2 ? t[2] : "", t.Count > 4 ? N(t, 3) : GumpStyle.Width, t.Count > 4 ? N(t, 4) : GumpStyle.Height);
                    break;
                case "bg":
                    builder.AddBackground(N(t, 1), N(t, 2), N(t, 3), N(t, 4), N(t, 5));
                    break;
                case "tile":
                    builder.AddImageTiled(N(t, 1), N(t, 2), N(t, 3), N(t, 4), N(t, 5));
                    break;
                case "img":
                    builder.AddImage(N(t, 1), N(t, 2), N(t, 3), t.Count > 4 ? N(t, 4) : 0);
                    break;
                case "html":
                {
                    var align = Option(t, "align", "left") switch { "center" => TextAlignment.Center, "right" => TextAlignment.Right, _ => TextAlignment.Left };
                    var size = int.Parse(Option(t, "size", "-1"), CultureInfo.InvariantCulture);
                    var style = byte.Parse(Option(t, "style", "0"), CultureInfo.InvariantCulture);
                    builder.AddHtml(N(t, 1), N(t, 2), N(t, 3), N(t, 4), t[5], Option(t, "color", GumpStyle.Text), size, style, align, Option(t, "bg") == "1", Option(t, "scroll") == "1");
                    break;
                }
                case "label":
                    builder.AddLabel(N(t, 1), N(t, 2), N(t, 3), t[4]);
                    break;
                case "button":
                    if (Option(t, "page", "", 6) is { Length: > 0 } page)
                    {
                        builder.AddButton(N(t, 1), N(t, 2), N(t, 3), N(t, 4), N(t, 5), GumpButtonType.Page, int.Parse(page, CultureInfo.InvariantCulture));
                    }
                    else
                    {
                        builder.AddButton(N(t, 1), N(t, 2), N(t, 3), N(t, 4), N(t, 5));
                    }

                    break;
                case "check":
                    builder.AddCheckbox(N(t, 1), N(t, 2), N(t, 3), N(t, 4), N(t, 5) != 0, N(t, 6));
                    break;
                case "radio":
                    builder.AddRadio(N(t, 1), N(t, 2), N(t, 3), N(t, 4), N(t, 5) != 0, N(t, 6));
                    break;
            }
        }
    }

    public override void OnResponse(NetState sender, in RelayInfo info) =>
        sender.Mobile?.SendMessage($"gump script button {info.ButtonID}, {info.Switches.Length} switches");
}
