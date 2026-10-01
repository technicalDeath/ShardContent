using System.Globalization;
using System.Text.Json;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace CosmeticElfTools;

// Test-only, disposable-host-only. [TestOnlyElfReport <player-serial> writes the character's
// authoritative server-side state (race, body, appearance, derived stats, skills, equipment and
// backpack) to elf-report-<serial>.json beside the host's Server.dll, so a driver can compare a
// Human and an Elf character, or the same character before and after death, resurrection and a
// save/restart, without relying on client tooltips.
public static class ElfProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyElfReport", AccessLevel.Administrator, OnReport);
        CommandSystem.Register("TestOnlyElfEquip", AccessLevel.Administrator, OnEquip);
    }

    // [TestOnlyElfEquip <player-serial> <ItemTypeName> creates the item, tries Mobile.EquipItem on the
    // player (the same CanEquip path a client equip or drag takes) and writes
    // elf-equip-<serial>-<type>.json with whether it ended up equipped. A refused item is deleted.
    private static void OnEquip(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (e.Length < 2 || !uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyElfEquip <player-serial> <ItemTypeName>");
            return;
        }

        var typeName = e.GetString(1);
        var type = AssemblyHandler.FindTypeByName(typeName);
        if (type is null || Activator.CreateInstance(
                type,
                System.Reflection.BindingFlags.CreateInstance | System.Reflection.BindingFlags.Public |
                System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.OptionalParamBinding,
                null,
                Array.Empty<object>(),
                null
            ) is not Item item)
        {
            e.Mobile.SendMessage($"No item type '{typeName}'.");
            return;
        }

        var equipped = player.EquipItem(item);
        var layer = item.Layer.ToString();
        if (!equipped)
        {
            item.Delete();
        }

        var path = Path.Combine(Core.BaseDirectory, $"elf-equip-{serial:X}-{typeName}.json");
        File.WriteAllText(path, JsonSerializer.Serialize(new { type = typeName, equipped, layer, race = player.Race.Name }));
        e.Mobile.SendMessage($"ElfEquip {typeName} equipped={equipped}");
    }

    private static void OnReport(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyElfReport <player-serial>");
            return;
        }

        var skills = new SortedDictionary<string, double>();
        foreach (var skill in player.Skills)
        {
            if (skill.Base > 0)
            {
                skills[skill.SkillName.ToString()] = skill.Base;
            }
        }

        var resistances = new SortedDictionary<string, int>();
        foreach (var type in Enum.GetValues<ResistanceType>())
        {
            resistances[type.ToString()] = player.GetResistance(type);
        }

        var equipped = player.Items
            .Where(i => i.Layer != Layer.Backpack && i.Layer != Layer.Hair && i.Layer != Layer.FacialHair)
            .OrderBy(i => (int)i.Layer)
            .Select(i => new { layer = i.Layer.ToString(), type = i.GetType().Name, hue = i.Hue, loot = i.LootType.ToString() })
            .ToList();

        var pack = player.Backpack?.Items
            .OrderBy(i => i.GetType().Name)
            .Select(i => new { type = i.GetType().Name, amount = i.Amount, hue = i.Hue, loot = i.LootType.ToString() })
            .ToList();

        var report = new SortedDictionary<string, object?>
        {
            ["serial"] = serial.ToString("X"),
            ["race"] = player.Race.Name,
            ["female"] = player.Female,
            ["alive"] = player.Alive,
            ["accessLevel"] = player.AccessLevel.ToString(),
            ["body"] = player.Body.BodyID,
            ["bodyMod"] = player.BodyMod.BodyID,
            ["hue"] = player.Hue,
            ["hueMod"] = player.HueMod,
            ["hairItemID"] = player.HairItemID,
            ["hairHue"] = player.HairHue,
            ["facialHairItemID"] = player.FacialHairItemID,
            ["facialHairHue"] = player.FacialHairHue,
            ["rawStr"] = player.RawStr,
            ["rawDex"] = player.RawDex,
            ["rawInt"] = player.RawInt,
            ["hitsMax"] = player.HitsMax,
            ["stamMax"] = player.StamMax,
            ["manaMax"] = player.ManaMax,
            ["maxWeight"] = player.MaxWeight,
            ["racialSkillBonus"] = player.RacialSkillBonus,
            ["skillsTotal"] = player.Skills.Total,
            ["skills"] = skills,
            ["resistances"] = resistances,
            ["gold"] = player.Backpack?.GetAmount(typeof(Gold)) ?? 0,
            ["equipped"] = equipped,
            ["pack"] = pack,
        };

        var path = Path.Combine(Core.BaseDirectory, $"elf-report-{serial:X}.json");
        File.WriteAllText(path, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
        e.Mobile.SendMessage($"ElfReport {serial:X} written race={player.Race.Name} body={player.Body.BodyID}");
    }
}
