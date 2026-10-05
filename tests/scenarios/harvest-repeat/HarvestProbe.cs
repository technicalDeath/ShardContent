using System.Text.Json;
using Server;
using Server.Commands;
using Server.Engines.Harvest;
using Server.Items;
using Server.Mobiles;
using Server.Targeting;
using BritanniaRenaissance.Content;

namespace HarvestRepeatTools;

// Test-only, disposable-host-only. Results are JSON beside the host's Server.dll so a driver reads
// authoritative server state.
//   [TestOnlyHarvestSetup <player-serial hex> <mine|tree|water> [hintX hintY [radius]]
//       Finds the nearest tile the stock harvest definition accepts plus a spot to stand within range, moves the
//       player there, gives the matching tool (a pickaxe in the pack, a hatchet equipped, a pole in the pack) and sets
//       the skill. Writes harvest-setup-<serial>.json: stand, target (x, y, z, graphic; graphic 0 = land tile).
//   [TestOnlyHarvestBank <mine|tree|water> <x> <y> <leave>
//       Drains the resource bank under that tile down to <leave> (-1 only reports). Writes harvest-bank.json.
//   [TestOnlyHarvestHurt <player-serial hex> <amount>
//       Lowers the player's hit points, as damage from any source would.
public static class HarvestProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyHarvestSetup", AccessLevel.Administrator, OnSetup);
        CommandSystem.Register("TestOnlyHarvestBank", AccessLevel.Administrator, OnBank);
        CommandSystem.Register("TestOnlyHarvestHurt", AccessLevel.Administrator, OnHurt);
        CommandSystem.Register("TestOnlyHarvestFlag", AccessLevel.Administrator, OnFlag);
    }

    //   [TestOnlyHarvestFlag <on|off>   Sets featureFlags.harvestAutoRepeat in memory only (the stock-behavior control).
    private static void OnFlag(CommandEventArgs e)
    {
        if (e.Length < 1 || e.GetString(0) is not ("on" or "off"))
        {
            e.Mobile.SendMessage("Usage: <on|off>");
            return;
        }

        ShardRulesConfiguration.Settings.FeatureFlags.HarvestAutoRepeat = e.GetString(0) == "on";
        e.Mobile.SendMessage($"harvestAutoRepeat in memory: {e.GetString(0)}");
    }

    private sealed record Kind(
        HarvestSystem System, HarvestDefinition Definition, bool Land, SkillName Skill, double SkillValue,
        int HintX, int HintY, int Radius, int StandDistance);

    private static Kind? KindOf(string name) => name.ToLowerInvariant() switch
    {
        "mine" => new Kind(Mining.System, Mining.System.OreAndStone, true, SkillName.Mining, 100, 2570, 520, 160, 1),
        "tree" => new Kind(Lumberjacking.System, Lumberjacking.System.Definitions[0], false, SkillName.Lumberjacking, 100,
            1450, 1600, 160, 1),
        "water" => new Kind(Fishing.System, Fishing.System.Definitions[0], true, SkillName.Fishing, 70, 2900, 700, 160, 2),
        _ => null
    };

    private static void Write(string file, object data) =>
        File.WriteAllText(Path.Combine(Core.BaseDirectory, file), JsonSerializer.Serialize(data));

    private static void OnSetup(CommandEventArgs e)
    {
        if (e.Length < 2 || !int.TryParse(e.GetString(0), System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)(uint)serial) is not PlayerMobile player || KindOf(e.GetString(1)) is not { } kind)
        {
            e.Mobile.SendMessage("Usage: <hex player serial> <mine|tree|water> [hintX hintY [radius]]");
            return;
        }

        var hintX = e.Length >= 4 ? e.GetInt32(2) : kind.HintX;
        var hintY = e.Length >= 4 ? e.GetInt32(3) : kind.HintY;
        var radius = e.Length >= 5 ? e.GetInt32(4) : kind.Radius;
        var file = $"harvest-setup-{player.Serial.Value:X}.json";
        var map = Map.Felucca;

        // The server refuses a target the player cannot see, so a spot only counts once the player standing there can.
        bool Sees(Point3D standAt, Point3D targetAt)
        {
            player.MoveToWorld(standAt, map);
            return player.InLOS(kind.Land ? new LandTarget(targetAt, map) : new StaticTarget(targetAt, 0));
        }

        if (!TryFind(map, kind, hintX, hintY, radius, Sees, out var stand, out var target, out var graphic))
        {
            Write(file, new { ok = false, error = $"no {e.GetString(1)} spot within {radius} of {hintX},{hintY}" });
            return;
        }

        player.Hidden = false;
        player.Warmode = false;
        player.Skills[kind.Skill].BaseFixedPoint = (int)(kind.SkillValue * 10);

        // Earlier setups (and earlier cases) leave tools and haul behind; that overloads the pack and ends loops early.
        if (player.Backpack is { } pack)
        {
            var junk = new List<Item>();

            foreach (var held in pack.FindItemsByType<Item>(true))
            {
                if (held is Pickaxe or Hatchet or FishingPole or BaseOre or Log or Fish)
                {
                    junk.Add(held);
                }
            }

            foreach (var item in junk)
            {
                item.Delete();
            }
        }

        Item tool;
        switch (e.GetString(1).ToLowerInvariant())
        {
            case "mine":
                tool = new Pickaxe();
                player.AddToBackpack(tool);
                break;
            case "tree":
                foreach (var layer in new[] { Layer.OneHanded, Layer.TwoHanded })
                {
                    if (player.FindItemOnLayer(layer) is { } held)
                    {
                        player.AddToBackpack(held);
                    }
                }

                tool = new Hatchet();
                player.EquipItem(tool);
                break;
            default:
                tool = new FishingPole();
                player.AddToBackpack(tool);
                break;
        }

        var bank = kind.Definition.GetBank(map, target.X, target.Y);
        var alts = new List<object>();

        for (var dx = -kind.StandDistance - 1; dx <= kind.StandDistance + 1 && alts.Count < 5; dx++)
        {
            for (var dy = -kind.StandDistance - 1; dy <= kind.StandDistance + 1 && alts.Count < 5; dy++)
            {
                int x = target.X + dx, y = target.Y + dy;

                if ((x != target.X || y != target.Y) && TryTile(map, kind, x, y, out var az, out var ag) &&
                    Math.Max(Math.Abs(x - stand.X), Math.Abs(y - stand.Y)) <= kind.Definition.MaxRange)
                {
                    alts.Add(new { x, y, z = az, graphic = ag });
                }
            }
        }

        Write(file, new
        {
            ok = true,
            stand = new { x = stand.X, y = stand.Y, z = stand.Z },
            target = new { x = target.X, y = target.Y, z = target.Z, graphic },
            alts,
            tool = $"{tool.Serial.Value:X}",
            bank = bank?.Current ?? -1,
            consumed = kind.Definition.ConsumedPerHarvest
        });
    }

    private static bool TryFind(
        Map map, Kind kind, int cx, int cy, int radius, Func<Point3D, Point3D, bool> accept, out Point3D stand,
        out Point3D target, out int graphic)
    {
        stand = default;
        target = default;
        graphic = 0;

        for (var r = 0; r <= radius; r++)
        {
            for (var dx = -r; dx <= r; dx++)
            {
                for (var dy = -r; dy <= r; dy++)
                {
                    if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != r)
                    {
                        continue;
                    }

                    int x = cx + dx, y = cy + dy;

                    if (!TryTile(map, kind, x, y, out var tz, out var tg))
                    {
                        continue;
                    }

                    if (TryStand(map, x, y, kind.StandDistance, out stand) &&
                        accept(stand, new Point3D(x, y, tz)))
                    {
                        target = new Point3D(x, y, tz);
                        graphic = tg;
                        return true;
                    }
                }
            }
        }

        return false;
    }

    private static bool TryTile(Map map, Kind kind, int x, int y, out int z, out int graphic)
    {
        z = 0;
        graphic = 0;

        if (kind.Land)
        {
            var land = map.Tiles.GetLandTile(x, y);

            if (!kind.Definition.Validate(land.ID, true))
            {
                return false;
            }

            z = land.Z;
            return true;
        }

        foreach (var tile in map.Tiles.GetStaticTiles(x, y))
        {
            if (kind.Definition.Validate(tile.ID, false))
            {
                z = tile.Z;
                graphic = tile.ID;
                return true;
            }
        }

        return false;
    }

    private static bool TryStand(Map map, int x, int y, int distance, out Point3D stand)
    {
        for (var dx = -distance; dx <= distance; dx++)
        {
            for (var dy = -distance; dy <= distance; dy++)
            {
                if (Math.Max(Math.Abs(dx), Math.Abs(dy)) != distance)
                {
                    continue;
                }

                int sx = x + dx, sy = y + dy;
                var sz = map.GetAverageZ(sx, sy);

                if (map.CanSpawnMobile(sx, sy, sz))
                {
                    stand = new Point3D(sx, sy, sz);
                    return true;
                }
            }
        }

        stand = default;
        return false;
    }

    private static void OnBank(CommandEventArgs e)
    {
        if (e.Length < 4 || KindOf(e.GetString(0)) is not { } kind)
        {
            e.Mobile.SendMessage("Usage: <mine|tree|water> <x> <y> <leave>");
            return;
        }

        var bank = kind.Definition.GetBank(Map.Felucca, e.GetInt32(1), e.GetInt32(2));
        var leave = e.GetInt32(3);
        var before = bank?.Current ?? -1;

        if (bank is not null && leave >= 0 && before > leave)
        {
            bank.Consume(before - leave, e.Mobile);
        }

        Write("harvest-bank.json", new { before, after = bank?.Current ?? -1, consumed = kind.Definition.ConsumedPerHarvest });
    }

    private static void OnHurt(CommandEventArgs e)
    {
        if (e.Length < 2 || !int.TryParse(e.GetString(0), System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)(uint)serial) is not { } mobile)
        {
            e.Mobile.SendMessage("Usage: <hex player serial> <amount>");
            return;
        }

        mobile.Hits -= e.GetInt32(1);
    }
}
