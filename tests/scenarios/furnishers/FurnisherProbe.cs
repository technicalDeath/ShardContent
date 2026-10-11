using System.Globalization;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;
using Server.Multis;

namespace FurnisherTools;

// Test-only, disposable-host-only (never ships). Lets a live scenario set up and read back what the Furnisher does:
//   [TestOnlyFurnisherHouse <player-serial> <x> <y> <z>]   builds a small stone-and-plaster house owned by the player and writes
//                                                          furnisher-house-<serial>.json (house serial, its wall and floor tiles)
//   [TestOnlyFurnisherGold <player-serial> <amount>]       deposits gold in the player's bank box
//   [TestOnlyFurnisherFit <player-serial> <pieceId> <x> <y> <z>]   asks the stock addon fit rule whether the piece fits there for the player,
//                                                          for every facing, and writes furnisher-fit-<serial>.json
//   [TestOnlyFurnisherReport <player-serial>]              writes furnisher-report-<serial>.json: the Furnisher and hall as they stand, and
//                                                          every furnishing the player holds or has placed in a house
// Hex serials as printed by Navrey (no 0x). Results are JSON files in the server's base directory.
public static class FurnisherProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyFurnisherHouse", AccessLevel.Administrator, OnHouse);
        CommandSystem.Register("TestOnlyFurnisherGold", AccessLevel.Administrator, OnGold);
        CommandSystem.Register("TestOnlyFurnisherFit", AccessLevel.Administrator, OnFit);
        CommandSystem.Register("TestOnlyFurnisherReport", AccessLevel.Administrator, OnReport);
    }

    private static PlayerMobile? Player(CommandEventArgs e, int arg)
    {
        var hex = e.Length > arg ? e.GetString(arg) : "";

        if (uint.TryParse(hex.Replace("0x", ""), NumberStyles.HexNumber, null, out var serial) &&
            World.FindMobile((Serial)serial) is PlayerMobile player)
        {
            return player;
        }

        e.Mobile.SendMessage("Give the player's serial in hex.");
        return null;
    }

    private static void Write(string name, PlayerMobile player, object data) =>
        File.WriteAllText(Path.Combine(Core.BaseDirectory, $"furnisher-{name}-{player.Serial.Value:X}.json"), JsonSerializer.Serialize(data));

    private static void OnHouse(CommandEventArgs e)
    {
        if (Player(e, 0) is not { } player || e.Length < 4)
        {
            return;
        }

        var spot = new Point3D(e.GetInt32(1), e.GetInt32(2), e.GetInt32(3));
        var house = new SmallOldHouse(player, 0x64);
        house.MoveToWorld(spot, Map.Felucca);

        var walls = new List<object>();
        var surfaces = new List<object>();

        foreach (var tile in house.Components.List)
        {
            var at = new { x = house.X + tile.OffsetX, y = house.Y + tile.OffsetY, z = house.Z + tile.OffsetZ, id = (int)tile.ItemId };

            if ((tile.Flags & TileFlag.Wall) != 0)
            {
                walls.Add(at);
            }

            if ((tile.Flags & TileFlag.Surface) != 0 || (tile.Flags & TileFlag.Impassable) == 0 && tile.OffsetZ == 7)
            {
                surfaces.Add(at);
            }
        }

        Write("house", player, new { house = $"{house.Serial.Value:X}", x = house.X, y = house.Y, z = house.Z, walls, surfaces, maxLockDowns = house.MaxLockDowns });
        e.Mobile.SendMessage($"House {house.Serial.Value:X} built at {spot}.");
    }

    private static void OnGold(CommandEventArgs e)
    {
        if (Player(e, 0) is not { } player || e.Length < 2)
        {
            return;
        }

        var ok = Banker.Deposit(player, e.GetInt32(1));
        e.Mobile.SendMessage(ok ? "Deposited." : "The bank box would not take it.");
    }

    private static void OnFit(CommandEventArgs e)
    {
        if (Player(e, 0) is not { } player || e.Length < 5)
        {
            return;
        }

        var pieceId = e.GetString(1);
        var piece = FurnishersConfiguration.Find(pieceId);

        if (piece is null)
        {
            e.Mobile.SendMessage("No such piece.");
            return;
        }

        var spot = new Point3D(e.GetInt32(2), e.GetInt32(3), e.GetInt32(4));
        var results = new List<object>();

        // Every facing, by building the addon at that facing the way a turn does and asking the stock rule.
        for (var i = 0; i < piece.Facings.Count; i++)
        {
            var addon = new FurnishingAddon(pieceId);
            addon.MoveToWorld(spot, Map.Felucca);
            var facing = piece.Facings[i];

            foreach (var c in addon.Components.ToArray())
            {
                c.Addon = null;
                c.Delete();
            }

            addon.ClearComponents();
            addon.Direction = FurnishersConfiguration.ToDirection(facing.Facing);

            foreach (var part in facing.Parts)
            {
                addon.AddComponent(new FurnishingComponent(part.Id) { Hue = part.Hue }, part.Dx, part.Dy, part.Dz);
            }

            BaseHouse? house = null;
            addon.Map = Map.Internal;
            var fit = addon.CouldFit(spot, Map.Felucca, player, ref house);
            addon.Map = Map.Felucca;

            results.Add(new { facing = facing.Facing, fit = fit.ToString(), parts = facing.Parts.Count });
            addon.Delete();
        }

        Write("fit", player, new { piece = pieceId, x = spot.X, y = spot.Y, z = spot.Z, results });
        e.Mobile.SendMessage($"Fit checked for {pieceId}.");
    }

    private static void OnReport(CommandEventArgs e)
    {
        if (Player(e, 0) is not { } player)
        {
            return;
        }

        var rules = FurnishersConfiguration.Settings;
        var bounds = rules is null
            ? default
            : new Rectangle2D(rules.Hall.Bounds[0], rules.Hall.Bounds[1], rules.Hall.Bounds[2] - rules.Hall.Bounds[0] + 1, rules.Hall.Bounds[3] - rules.Hall.Bounds[1] + 1);

        var vendors = new List<object>();
        var displays = 0;

        if (rules is not null)
        {
            foreach (var mobile in Map.Felucca.GetMobilesInBounds(bounds))
            {
                if (mobile is Furnisher v)
                {
                    var buyInfo = v.GetBuyInfo();
                    vendors.Add(new
                    {
                        serial = $"{v.Serial.Value:X}",
                        name = v.Name,
                        title = v.Title,
                        x = v.X, y = v.Y, z = v.Z,
                        direction = v.Direction.ToString(),
                        cantWalk = v.CantWalk,
                        invulnerable = v.IsInvulnerable,
                        activeSeller = v.IsActiveSeller,
                        activeBuyer = v.IsActiveBuyer,
                        sellTypes = v.GetSellInfo().Sum(s => s.Types.Length),
                        entries = buyInfo.Length,
                        minAmount = buyInfo.Min(b => b.Amount),
                        prices = buyInfo.Select(b => new { name = b.Name, price = b.Price, amount = b.Amount }).ToList()
                    });
                }
            }

            foreach (var item in Map.Felucca.GetItemsInBounds<FurnisherDisplayItem>(bounds))
            {
                _ = item;
                displays++;
            }
        }

        object Describe(Item item) => item switch
        {
            FurnishingItem f => new { kind = "item", serial = $"{f.Serial.Value:X}", piece = f.PieceId, graphic = f.ItemID, hue = f.Hue, name = f.Name, loot = f.LootType.ToString(), movable = f.Movable, x = f.X, y = f.Y, z = f.Z },
            FurnishingDeed d => new { kind = "deed", serial = $"{d.Serial.Value:X}", piece = d.PieceId, graphic = d.ItemID, hue = d.Hue, name = d.Name, loot = d.LootType.ToString(), movable = d.Movable, x = d.X, y = d.Y, z = d.Z },
            _ => new { kind = item.GetType().Name, serial = $"{item.Serial.Value:X}", piece = "", graphic = item.ItemID, hue = item.Hue, name = item.Name ?? "", loot = item.LootType.ToString(), movable = item.Movable, x = item.X, y = item.Y, z = item.Z }
        };

        var carried = new List<object>();

        if (player.Backpack is { } pack)
        {
            foreach (var item in pack.FindItemsByType<Item>())
            {
                if (item is FurnishingItem or FurnishingDeed)
                {
                    carried.Add(Describe(item));
                }
            }
        }

        var houses = new List<object>();

        foreach (var house in BaseHouse.GetHouses(player))
        {
            var addons = new List<object>();

            foreach (var a in house.Addons)
            {
                if (a is FurnishingAddon fa)
                {
                    addons.Add(new
                    {
                        serial = $"{fa.Serial.Value:X}",
                        piece = fa.PieceId,
                        direction = fa.Direction.ToString(),
                        x = fa.X, y = fa.Y, z = fa.Z,
                        components = fa.Components.Select(c => new { serial = $"{c.Serial.Value:X}", id = c.ItemID, hue = c.Hue, x = c.X, y = c.Y, z = c.Z, name = c.Name, needsWall = c.NeedsWall }).ToList()
                    });
                }
            }

            var locked = house.LockDowns.OfType<FurnishingItem>().Select(Describe).ToList();
            houses.Add(new { serial = $"{house.Serial.Value:X}", addons, lockedDown = locked });
        }

        Write("report", player, new { flag = FurnishersService.Enabled, displayItems = displays, vendors, carried, houses });
        e.Mobile.SendMessage("Furnisher report written.");
    }
}
