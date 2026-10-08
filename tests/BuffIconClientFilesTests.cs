using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>The files the player's client needs for the shard's own buff icons: the art, and the table that tells the client which art is which icon.</summary>
public sealed class BuffIconClientFilesTests
{
    private static readonly string DataRoot = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data");

    private static BuffIconRules Rules() =>
        BuffIconRulesLoader.Parse(File.ReadAllText(Path.Combine(DataRoot, "configuration", "buff-icons.json")));

    [Fact]
    public void TheClientTableListsTheCustomArtInSlotOrder()
    {
        var file = File.ReadAllLines(Path.Combine(DataRoot, "client", "buff-extra.txt"))
            .Select(static l => l.Trim())
            .Where(static l => l.Length > 0 && l[0] != '#')
            .Select(int.Parse)
            .ToArray();

        Assert.Equal(Rules().CustomIcons.OrderBy(static i => i.Slot).Select(static i => i.Art), file);
        Assert.Equal(Enumerable.Range(0, file.Length), Rules().CustomIcons.OrderBy(static i => i.Slot).Select(static i => i.Slot));
    }

    [Fact]
    public void EveryCustomIconHasA28By28PictureThatReadsBackWhole()
    {
        foreach (var icon in Rules().CustomIcons)
        {
            var data = File.ReadAllBytes(Path.Combine(DataRoot, "client", "gumps", $"{icon.Art}.gump"));
            var width = BitConverter.ToUInt32(data, 0);
            var height = BitConverter.ToUInt32(data, 4);

            Assert.Equal(28u, width);
            Assert.Equal(28u, height);

            // After the two sizes: one row offset per row (in 4-byte units from the start of that table), then (colour, run) pairs per row.
            var table = 8;
            var rows = (int)height;

            for (var y = 0; y < rows; y++)
            {
                var start = table + BitConverter.ToInt32(data, table + y * 4) * 4;
                var end = y + 1 < rows ? table + BitConverter.ToInt32(data, table + (y + 1) * 4) * 4 : data.Length;
                var covered = 0;

                for (var at = start; at < end; at += 4)
                {
                    covered += BitConverter.ToUInt16(data, at + 2);
                }

                Assert.True(covered == (int)width, $"{icon.Name} row {y} covers {covered} of {width} pixels");
            }
        }
    }
}
