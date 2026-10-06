using System.Text.Json;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace ActionRepeatTools;

// Test-only, disposable-host-only. Results are JSON beside the host's Server.dll so a driver reads
// authoritative server state. Each setup first removes what the previous setup gave that player.
//   [TestOnlyActionSetup <player-serial hex> tame [offset]        a horse that cannot walk, one tile east; Animal Taming set to
//                                                                 the horse's minimum plus offset (default 8, about one try in six)
//   [TestOnlyActionSetup <serial> lock <level> <max> <required> <picks>   a locked wooden chest at the player's feet, Lockpicking 50
//   [TestOnlyActionSetup <serial> spin <n>                        a spinning wheel one tile east and n wool
//   [TestOnlyActionSetup <serial> loom <n>                        a loom one tile east and n spools of thread
//   [TestOnlyActionSetup <serial> cook <n>                        a fire pit one tile east, n raw fish steaks, Cooking 50
//   [TestOnlyActionReport <serial>                                pack counts and the state of that player's props
//   [TestOnlyActionFlag on|off                                    featureFlags.actionAutoRepeat in memory only
public static class ActionProbe
{
    private sealed class Props
    {
        public BaseCreature? Creature;
        public LockableContainer? Chest;
        public BaseAddon? Addon;
        public Item? Fire;
    }

    private static readonly Dictionary<Serial, Props> ByPlayer = [];

    public static void Configure()
    {
        CommandSystem.Register("TestOnlyActionSetup", AccessLevel.Administrator, OnSetup);
        CommandSystem.Register("TestOnlyActionReport", AccessLevel.Administrator, OnReport);
        CommandSystem.Register("TestOnlyActionFlag", AccessLevel.Administrator, OnFlag);
    }

    private static bool TryPlayer(CommandEventArgs e, out PlayerMobile player)
    {
        player = null!;

        if (e.Length < 1 || !int.TryParse(e.GetString(0), System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)(uint)serial) is not PlayerMobile found)
        {
            e.Mobile.SendMessage("Usage: <hex player serial> ...");
            return false;
        }

        player = found;
        return true;
    }

    private static void Write(PlayerMobile player, string what, object data) =>
        File.WriteAllText(Path.Combine(Core.BaseDirectory, $"action-{what}-{player.Serial.Value:X}.json"), JsonSerializer.Serialize(data));

    private static Props Reset(PlayerMobile player)
    {
        if (ByPlayer.TryGetValue(player.Serial, out var old))
        {
            old.Creature?.Delete();
            old.Chest?.Delete();
            old.Addon?.Delete();
            old.Fire?.Delete();
        }

        if (player.Backpack is { } pack)
        {
            var junk = new List<Item>();

            foreach (var held in pack.FindItemsByType<Item>(true))
            {
                if (held is Wool or BaseClothMaterial or BoltOfCloth or RawFishSteak or FishSteak or Lockpick)
                {
                    junk.Add(held);
                }
            }

            foreach (var item in junk)
            {
                item.Delete();
            }
        }

        var props = new Props();
        ByPlayer[player.Serial] = props;
        return props;
    }

    // The test characters stand on one tile, so each kind of prop gets its own side of it.
    private static Point3D East(Mobile m) => new(m.X + 1, m.Y, m.Z);
    private static Point3D North(Mobile m) => new(m.X, m.Y - 1, m.Z);
    private static Point3D South(Mobile m) => new(m.X, m.Y + 1, m.Z);

    private static void OnSetup(CommandEventArgs e)
    {
        if (!TryPlayer(e, out var player) || e.Length < 2)
        {
            return;
        }

        var props = Reset(player);
        var map = player.Map;
        var kind = e.GetString(1).ToLowerInvariant();
        object result;

        switch (kind)
        {
            case "tame":
                {
                    var offset = e.Length >= 3 ? e.GetDouble(2) : 8.0;
                    var horse = new Horse { CantWalk = true };
                    horse.MoveToWorld(East(player), map);
                    props.Creature = horse;
                    player.Skills.AnimalTaming.Base = horse.MinTameSkill + offset;
                    result = new { ok = true, creature = $"{horse.Serial.Value:X}", minTame = horse.MinTameSkill, taming = player.Skills.AnimalTaming.Base };
                    break;
                }
            case "lock":
                {
                    if (e.Length < 6)
                    {
                        e.Mobile.SendMessage("lock <level> <max> <required> <picks>");
                        return;
                    }

                    var chest = new WoodenChest { Movable = false };
                    chest.MoveToWorld(player.Location, map);
                    chest.LockLevel = e.GetInt32(2);
                    chest.MaxLockLevel = e.GetInt32(3);
                    chest.RequiredSkill = e.GetInt32(4);
                    chest.Locked = true;
                    props.Chest = chest;
                    player.Skills.Lockpicking.Base = 50.0;
                    var picks = new Lockpick(e.GetInt32(5));
                    player.AddToBackpack(picks);
                    result = new { ok = true, chest = $"{chest.Serial.Value:X}", picks = $"{picks.Serial.Value:X}", lockpicking = player.Skills.Lockpicking.Base };
                    break;
                }
            case "spin":
            case "loom":
                {
                    var n = e.Length >= 3 ? e.GetInt32(2) : 5;
                    BaseAddon addon = kind == "spin" ? new SpinningWheelEastAddon() : new LoomEastAddon();
                    addon.MoveToWorld(North(player), map);
                    props.Addon = addon;
                    Item material = kind == "spin" ? new Wool(n) : new SpoolOfThread(n);
                    player.AddToBackpack(material);
                    result = new
                    {
                        ok = true,
                        component = $"{addon.Components[0].Serial.Value:X}",
                        material = $"{material.Serial.Value:X}",
                        amount = n
                    };
                    break;
                }
            case "cook":
                {
                    var n = e.Length >= 3 ? e.GetInt32(2) : 5;
                    var fire = new Item(0xFAC) { Movable = false, Name = "fire pit" };
                    fire.MoveToWorld(South(player), map);
                    props.Fire = fire;
                    player.Skills.Cooking.Base = 50.0;
                    var raw = new RawFishSteak(n);
                    player.AddToBackpack(raw);
                    result = new { ok = true, fire = $"{fire.Serial.Value:X}", food = $"{raw.Serial.Value:X}", amount = n, cooking = player.Skills.Cooking.Base };
                    break;
                }
            default:
                e.Mobile.SendMessage("Usage: <serial> tame|lock|spin|loom|cook ...");
                return;
        }

        Write(player, "setup", result);
    }

    private static int Count<T>(PlayerMobile player) where T : Item
    {
        var total = 0;

        if (player.Backpack is { } pack)
        {
            foreach (var item in pack.FindItemsByType<T>(true))
            {
                total += item.Amount;
            }
        }

        return total;
    }

    private static void OnReport(CommandEventArgs e)
    {
        if (!TryPlayer(e, out var player))
        {
            return;
        }

        ByPlayer.TryGetValue(player.Serial, out var props);

        Write(player, "report", new
        {
            wool = Count<Wool>(player),
            yarn = Count<DarkYarn>(player),
            thread = Count<SpoolOfThread>(player),
            bolts = Count<BoltOfCloth>(player),
            raw = Count<RawFishSteak>(player),
            cooked = Count<FishSteak>(player),
            picks = Count<Lockpick>(player),
            controlled = props?.Creature?.Controlled ?? false,
            creatureAlive = props?.Creature is { Deleted: false, Alive: true },
            owners = props?.Creature?.Owners.Count ?? 0,
            locked = props?.Chest?.Locked ?? false,
            loops = ActionRepeatService.ActiveLoops,
            enabled = ActionRepeatService.Enabled
        });
    }

    private static void OnFlag(CommandEventArgs e)
    {
        if (e.Length < 1 || e.GetString(0) is not ("on" or "off"))
        {
            e.Mobile.SendMessage("Usage: <on|off>");
            return;
        }

        ShardRulesConfiguration.Settings.FeatureFlags.ActionAutoRepeat = e.GetString(0) == "on";
        e.Mobile.SendMessage($"actionAutoRepeat in memory: {e.GetString(0)}");
    }
}
