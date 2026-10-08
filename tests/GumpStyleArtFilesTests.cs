using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The shard's own window buttons (owner rulings 2026-10-07), as gump files the client reads from <c>Data/Gumps</c>: blank purple ovals for
/// game actions, blank blue ovals for menu actions, and the small purple and dull stone ovals of a pick-one group (a radio button with its label beside it), each as a normal and a
/// pressed picture. A window that names art the player's client
/// lacks draws no button, so these files are a deploy requirement.
/// </summary>
public sealed class GumpStyleArtFilesTests
{
    private static readonly string GumpFolder = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "data", "client", "gumps");

    /// <summary>Menu-action ovals: width k is art <c>OvalBase + 2k</c> (normal) and <c>+ 1</c> (pressed).</summary>
    public const int OvalBase = 62010;
    public const int PurpleOvalBase = 62020;
    public const int ChosenOvalBase = 62030;
    public const int StoneOvalBase = 62040;

    private const int OvalHeight = 21;

    private static readonly int[] OvalWidths = [56, 88, 128, 176, 232];
    private static readonly int[] PillWidths = [22];

    private static byte[] Read(int art) => File.ReadAllBytes(Path.Combine(GumpFolder, $"{art}.gump"));

    [Fact]
    public void EachWidthHasANormalAndAPressedPictureOfTheRightSize()
    {
        foreach (var (baseId, widths, height) in new[]
                 {
                     (OvalBase, OvalWidths, OvalHeight), (PurpleOvalBase, OvalWidths, OvalHeight),
                     (ChosenOvalBase, PillWidths, OvalHeight), (StoneOvalBase, PillWidths, OvalHeight)
                 })
        {
            for (var k = 0; k < widths.Length; k++)
            {
                foreach (var art in new[] { baseId + 2 * k, baseId + 2 * k + 1 })
                {
                    var data = Read(art);

                    Assert.Equal((uint)widths[k], BitConverter.ToUInt32(data, 0));
                    Assert.Equal((uint)height, BitConverter.ToUInt32(data, 4));
                }
            }
        }
    }

    [Fact]
    public void EveryRowCoversItsWholeWidth()
    {
        var arts = new[] { OvalBase, PurpleOvalBase }.SelectMany(static b => Enumerable.Range(b, OvalWidths.Length * 2))
            .Concat(new[] { ChosenOvalBase, StoneOvalBase }.SelectMany(static b => Enumerable.Range(b, PillWidths.Length * 2)));

        foreach (var art in arts)
        {
            var data = Read(art);
            var width = (int)BitConverter.ToUInt32(data, 0);
            var rows = (int)BitConverter.ToUInt32(data, 4);
            const int table = 8;

            for (var y = 0; y < rows; y++)
            {
                var start = table + BitConverter.ToInt32(data, table + y * 4) * 4;
                var end = y + 1 < rows ? table + BitConverter.ToInt32(data, table + (y + 1) * 4) * 4 : data.Length;
                var covered = 0;

                for (var at = start; at < end; at += 4)
                {
                    covered += BitConverter.ToUInt16(data, at + 2);
                }

                Assert.True(covered == width, $"art {art} row {y} covers {covered} of {width} pixels");
            }
        }
    }

    [Fact]
    public void TheButtonArtSitsAboveTheStockArchiveAndAwayFromTheBuffIconRange()
    {
        // The stock archive ends at 61728; the buff icons use 50000 to 50999; the client reads ids below 0x10000.
        Assert.InRange(OvalBase, 61729, 0xFFFF);
        Assert.InRange(StoneOvalBase + PillWidths.Length * 2 - 1, 61729, 0xFFFF);
        Assert.True(PurpleOvalBase >= OvalBase + OvalWidths.Length * 2, "the purple ids must not overlap the blue ones");
        Assert.True(ChosenOvalBase >= PurpleOvalBase + OvalWidths.Length * 2, "the chosen ids must not overlap the purple ones");
        Assert.True(StoneOvalBase >= ChosenOvalBase + PillWidths.Length * 2, "the stone ids must not overlap the chosen ones");
    }
}
