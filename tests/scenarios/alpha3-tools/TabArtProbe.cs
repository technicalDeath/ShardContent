using BritanniaRenaissance.Content;
using Server;
using Server.Gumps;
using Server.Network;

namespace Alpha3TestOnlyTools;

// Test-only: the guide's frame with the chapter tabs drawn in the stone tab art with the selected tab in different hues, to pick the best
// look in the real client. Each tab is a Reply button (ids 100 + row * 10 + index).
public sealed class TabArtProbe : DynamicGump
{
    private static readonly string[] Labels = ["Start here", "Rules", "Skills", "Work", "Travel", "Commands"];

    // (selected hue, selected label ink, unselected label ink)
    private static readonly (int Hue, string InkOn, string Ink)[] Rows =
    [
        (0, "#000000", "#202020"),
        (41, "#000000", "#202020"),
        (44, "#000000", "#202020"),
        (47, "#000000", "#202020"),
        (50, "#000000", "#202020"),
        (53, "#000000", "#202020"),
        (56, "#000000", "#202020"),
    ];

    public TabArtProbe() : base(40, 30)
    {
    }

    public override bool Singleton => true;

    protected override void BuildLayout(ref DynamicGumpBuilder builder)
    {
        builder.AddPage();
        GumpStyle.Frame(ref builder, "Tab art probe", "stone tabs, selected tab hued");

        for (var r = 0; r < Rows.Length; r++)
        {
            var row = Rows[r];
            var y = 84 + r * 50;
            var x = 24;
            builder.AddHtml(24, y - 16, 300, 16, $"selected hue {row.Hue}", GumpStyle.Dim);

            for (var i = 0; i < Labels.Length; i++)
            {
                var selected = i == 1;

                if (selected)
                {
                    builder.AddImage(x, y, 5006, row.Hue);
                }
                else
                {
                    builder.AddButton(x, y, 5007, 5007, 100 + r * 10 + i);
                }

                builder.AddHtml(x, y + (selected ? 0 : 2), 88, 18, Labels[i], selected ? row.InkOn : row.Ink, size: 3, align: TextAlignment.Center, fontStyle: (byte)(selected ? 1 : 0));
                x += 88 + 4;
            }
        }
    }

    public override void OnResponse(NetState sender, in RelayInfo info)
    {
        if (info.ButtonID >= 100)
        {
            sender.Mobile?.SendMessage($"tab row {(info.ButtonID - 100) / 10} index {(info.ButtonID - 100) % 10}");
        }
    }
}
