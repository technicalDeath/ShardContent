using System.Globalization;
using System.Text.Json;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace CosmeticCatalogTools;

// Test-only, disposable-host-only. [TestOnlyDecor <player-serial> <layout-name>] lays the items of a catalog gallery page on the ground around
// that player, for the real-client screenshots of the cosmetic reward catalog (ShardContent/docs/cosmetic-rewards). The layout is
// work/cosmetics/layouts/<layout-name>.json (override the folder with COSMETIC_LAYOUTS): {"items":[{"id":4660,"x":3,"y":-2,"z":0,"hue":0}, ...]}
// with x/y/z relative to the player. [TestOnlyDecor <player-serial> clear] removes what the last call created. Items are plain Static
// graphics, immovable, never saved on purpose (the host is thrown away with -NoSave).
public static class DecorProbe
{
    private static readonly List<Item> Placed = [];

    public static void Configure()
    {
        CommandSystem.Register("TestOnlyDecor", AccessLevel.Administrator, OnDecorCommand);
        CommandSystem.Register("TestOnlyWalkGrid", AccessLevel.Administrator, OnWalkGridCommand);
    }

    // [TestOnlyWalkGrid <x> <y> <w> <h>] writes work/cosmetics/walkgrid.json: for each tile in the rectangle on the caller's map, the z a
    // mobile can stand at (null when it cannot), plus every server item in the rectangle (doors, decoration), so a showroom layout can be
    // planned against what the server itself treats as walkable floor.
    private static void OnWalkGridCommand(CommandEventArgs e)
    {
        if (e.Length < 4)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyWalkGrid <x> <y> <w> <h>");
            return;
        }

        var x0 = e.GetInt32(0);
        var y0 = e.GetInt32(1);
        var w = e.GetInt32(2);
        var h = e.GetInt32(3);
        var map = e.Mobile.Map;
        var rows = new List<List<int?>>();
        for (var y = y0; y < y0 + h; y++)
        {
            var row = new List<int?>();
            for (var x = x0; x < x0 + w; x++)
            {
                row.Add(map.CanSpawnMobile(x, y, -20, 127, false, false, out var z) ? z : null);
            }

            rows.Add(row);
        }

        var items = new List<object>();
        foreach (var item in map.GetItemsInBounds(new Rectangle2D(x0, y0, w, h)))
        {
            items.Add(new { type = item.GetType().Name, name = item.Name, id = item.ItemID, x = item.X, y = item.Y, z = item.Z, movable = item.Movable });
        }

        var folder = Path.GetDirectoryName(Path.GetFullPath(LayoutFolder)) ?? LayoutFolder;
        File.WriteAllText(Path.Combine(folder, "walkgrid.json"), JsonSerializer.Serialize(new { x0, y0, w, h, rows, items }));
        e.Mobile.SendMessage($"Wrote walkgrid.json ({w}x{h}, {items.Count} items).");
    }

    private static string LayoutFolder =>
        Environment.GetEnvironmentVariable("COSMETIC_LAYOUTS")
        ?? @"C:\Users\brend\Documents\Britannia Renaissance\work\cosmetics\layouts";

    private static void Clear()
    {
        foreach (var item in Placed)
        {
            if (!item.Deleted)
            {
                item.Delete();
            }
        }

        Placed.Clear();
    }

    private static void OnDecorCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)serial) is not PlayerMobile player || e.Length < 2)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyDecor <player-serial> <layout-name|clear>");
            return;
        }

        Clear();
        var name = e.GetString(1);
        if (name.Equals("clear", StringComparison.OrdinalIgnoreCase))
        {
            e.Mobile.SendMessage("Cleared.");
            return;
        }

        var path = Path.Combine(LayoutFolder, name + ".json");
        if (!File.Exists(path))
        {
            e.Mobile.SendMessage($"No layout {path}");
            return;
        }

        using var doc = JsonDocument.Parse(File.ReadAllText(path));
        var map = player.Map;
        // "absolute": true in the layout makes x/y/z world coordinates instead of offsets from the player (used for mock-ups at a real site)
        var absolute = doc.RootElement.TryGetProperty("absolute", out var abs) && abs.GetBoolean();
        var origin = absolute ? new Point3D(0, 0, 0) : player.Location;
        var count = 0;
        foreach (var node in doc.RootElement.GetProperty("items").EnumerateArray())
        {
            var item = new Static(node.GetProperty("id").GetInt32())
            {
                Hue = node.TryGetProperty("hue", out var hue) ? hue.GetInt32() : 0
            };
            var x = origin.X + node.GetProperty("x").GetInt32();
            var y = origin.Y + node.GetProperty("y").GetInt32();
            var z = origin.Z + (node.TryGetProperty("z", out var zz) ? zz.GetInt32() : 0);
            item.MoveToWorld(new Point3D(x, y, z), map);
            Placed.Add(item);
            count++;
        }

        e.Mobile.SendMessage($"Placed {count} items from {name}.");
    }
}
