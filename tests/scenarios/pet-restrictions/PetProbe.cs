using System.Globalization;
using System.Reflection;
using System.Text.Json;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace PetRestrictionTools;

// Test-only, disposable-host-only. Everything writes JSON beside the host's Server.dll so a driver
// reads authoritative server state instead of client text.
//   [TestOnlyPetTame <player-serial> <TypeName>   creates a tamed pet (SetControlMaster) at the player
//   [TestOnlyPetReport <serial>                    pet-report-<serial>.json for a pet; for a player: followers
//                                                  and any ShrunkenPet items in the pack
//   [TestOnlyPetGo <player-serial> x y z [pets]    MoveToWorld, then TeleportPets like a teleporter does
//   [TestOnlyPetDismount <player-serial>           BaseMount.Dismount, the same call a client dismount makes
public static class PetProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyPetTame", AccessLevel.Administrator, OnTame);
        CommandSystem.Register("TestOnlyPetReport", AccessLevel.Administrator, OnReport);
        CommandSystem.Register("TestOnlyPetGo", AccessLevel.Administrator, OnGo);
        CommandSystem.Register("TestOnlyPetDismount", AccessLevel.Administrator, OnDismount);
        CommandSystem.Register("TestOnlyPetClear", AccessLevel.Administrator, OnClear);
        CommandSystem.Register("TestOnlyPetSpawn", AccessLevel.Administrator, OnSpawn);
    }

    // [TestOnlyPetSpawn <player-serial> <TypeName> creates a wild creature beside the player and writes
    // pet-spawn-<player-serial>.json with its serial (for PvE targets where staff [add does not work).
    private static void OnSpawn(CommandEventArgs e)
    {
        if (e.Length < 2 || !TryMobile(e, 0, out var m) || m is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPetSpawn <player-serial> <TypeName>");
            return;
        }

        var type = AssemblyHandler.FindTypeByName(e.GetString(1));
        if (type is null || Activator.CreateInstance(
                type,
                BindingFlags.CreateInstance | BindingFlags.Public | BindingFlags.Instance | BindingFlags.OptionalParamBinding,
                null,
                Array.Empty<object>(),
                null
            ) is not BaseCreature creature)
        {
            e.Mobile.SendMessage($"No creature type '{e.GetString(1)}'.");
            return;
        }

        creature.MoveToWorld(new Point3D(player.X + 1, player.Y, player.Z), player.Map);
        Write($"pet-spawn-{player.Serial.Value:X}.json", new { serial = creature.Serial.Value.ToString("X") });
        e.Mobile.SendMessage($"PetSpawn {creature.Serial.Value:X}");
    }

    // [TestOnlyPetClear <player-serial> dismounts the player and deletes every follower and shrunken pet
    // item, so a test starts from an empty follower list.
    private static void OnClear(CommandEventArgs e)
    {
        if (!TryMobile(e, 0, out var m) || m is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPetClear <player-serial>");
            return;
        }

        BaseMount.Dismount(player);
        foreach (var item in (player.Backpack?.Items.OfType<ShrunkenPet>() ?? Enumerable.Empty<ShrunkenPet>()).ToList())
        {
            item.Delete();
        }

        foreach (var follower in (player.AllFollowers?.OfType<BaseCreature>() ?? Enumerable.Empty<BaseCreature>()).ToList())
        {
            follower.Delete();
        }

        e.Mobile.SendMessage($"PetClear {player.Serial.Value:X} followers={player.Followers}");
    }

    private static bool TryMobile(CommandEventArgs e, int index, out Mobile? mobile)
    {
        var raw = e.Length > index ? e.GetString(index) : "";
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        mobile = uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ? World.FindMobile((Serial)serial) : null;
        return mobile is not null;
    }

    private static void Write(string name, object value) =>
        File.WriteAllText(
            Path.Combine(Core.BaseDirectory, name),
            JsonSerializer.Serialize(value, new JsonSerializerOptions { WriteIndented = true })
        );

    private static void OnTame(CommandEventArgs e)
    {
        if (e.Length < 2 || !TryMobile(e, 0, out var m) || m is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPetTame <player-serial> <TypeName>");
            return;
        }

        var type = AssemblyHandler.FindTypeByName(e.GetString(1));
        if (type is null || Activator.CreateInstance(
                type,
                BindingFlags.CreateInstance | BindingFlags.Public | BindingFlags.Instance | BindingFlags.OptionalParamBinding,
                null,
                Array.Empty<object>(),
                null
            ) is not BaseCreature pet)
        {
            e.Mobile.SendMessage($"No creature type '{e.GetString(1)}'.");
            return;
        }

        pet.MoveToWorld(player.Location, player.Map);
        var ok = pet.SetControlMaster(player);
        pet.ControlTarget = player;
        pet.ControlOrder = OrderType.Follow;
        Write($"pet-tame-{player.Serial.Value:X}.json", new { pet = pet.Serial.Value.ToString("X"), ok, type = type.Name });
        e.Mobile.SendMessage($"PetTame {pet.Serial.Value:X} ok={ok}");
    }

    private static object Describe(BaseCreature pet) => new
    {
        serial = pet.Serial.Value.ToString("X"),
        type = pet.GetType().Name,
        name = pet.Name,
        deleted = pet.Deleted,
        alive = pet.Alive,
        map = pet.Map?.Name,
        x = pet.X,
        y = pet.Y,
        z = pet.Z,
        region = pet.Region?.Name,
        inDungeon = pet.Region?.IsPartOf<Server.Regions.DungeonRegion>() == true,
        controlled = pet.Controlled,
        summoned = pet.Summoned,
        master = pet.ControlMaster?.Serial.Value.ToString("X"),
        stabled = pet.IsStabled,
        combatant = pet.Combatant?.Serial.Value.ToString("X"),
        warmode = pet.Warmode,
        hits = pet.Hits,
    };

    private static void OnReport(CommandEventArgs e)
    {
        if (!TryMobile(e, 0, out var m))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPetReport <serial>");
            return;
        }

        object report;
        if (m is BaseCreature pet)
        {
            report = Describe(pet);
        }
        else if (m is PlayerMobile player)
        {
            var followers = player.AllFollowers?.OfType<BaseCreature>().Select(Describe).ToList() ?? [];
            var shrunken = player.Backpack?.Items.OfType<ShrunkenPet>()
                .Select(i => new
                {
                    serial = i.Serial.Value.ToString("X"),
                    name = i.Name ?? i.DefaultName,
                    loot = i.LootType.ToString(),
                    nontransferable = i.Nontransferable,
                    pet = i.Pet is { } p ? Describe(p) : null,
                })
                .ToList();
            report = new
            {
                serial = player.Serial.Value.ToString("X"),
                followers,
                followerCount = player.Followers,
                shrunken = shrunken ?? [],
                x = player.X,
                y = player.Y,
                z = player.Z,
                inDungeon = player.Region?.IsPartOf<Server.Regions.DungeonRegion>() == true,
            };
        }
        else
        {
            e.Mobile.SendMessage("Not a pet or player.");
            return;
        }

        Write($"pet-report-{m.Serial.Value:X}.json", report);
        e.Mobile.SendMessage($"PetReport {m.Serial.Value:X} written");
    }

    private static void OnGo(CommandEventArgs e)
    {
        if (e.Length < 4 || !TryMobile(e, 0, out var m) || m is not PlayerMobile player ||
            !int.TryParse(e.GetString(1), out var x) || !int.TryParse(e.GetString(2), out var y) ||
            !int.TryParse(e.GetString(3), out var z))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPetGo <player-serial> x y z [pets]");
            return;
        }

        var map = player.Map ?? Map.Felucca;
        var location = new Point3D(x, y, z);
        player.MoveToWorld(location, map);
        if (e.Length > 4 && string.Equals(e.GetString(4), "pets", StringComparison.OrdinalIgnoreCase))
        {
            BaseCreature.TeleportPets(player, location, map);
        }

        e.Mobile.SendMessage($"PetGo {player.Serial.Value:X} -> {x},{y},{z}");
    }

    private static void OnDismount(CommandEventArgs e)
    {
        if (!TryMobile(e, 0, out var m) || m is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPetDismount <player-serial>");
            return;
        }

        BaseMount.Dismount(player);
        e.Mobile.SendMessage($"PetDismount {player.Serial.Value:X} mounted={player.Mounted}");
    }
}
