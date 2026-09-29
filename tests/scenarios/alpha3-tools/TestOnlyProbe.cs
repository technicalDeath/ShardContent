using System.Globalization;
using System.Reflection;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace Alpha3TestOnlyTools;

// Test-only, disposable-host-only. Reusable across Alpha 3 letters: several feature flags are
// validator-rejected outright in ShardRulesConfiguration.Validate (currently
// alpha3StarterCraftMaterials, alpha3StarterCombatGear, housingGeography, expeditions, pilgrimage,
// roadSpeed, retentionContent, coolZones), so they can never be true in shard-rules.json, not even
// on a disposable host - Load() throws before the server starts. TestOnlyFlagOverride flips an
// already-loaded flag's in-memory value directly, after Load()'s validation already passed with it
// false, so an ordinary gameplay packet can exercise the gated code path. Never touches disk;
// discarded on restart. Pair with New-TestCharacter.ps1's -NoRestart switch so the override
// survives across every character you create with it. TestOnlyInventoryInspect reports a player's
// items authoritatively from the server side (type, amount, LootType, Nontransferable), instead of
// relying on client tooltip text.
public static class TestOnlyProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyFlagOverride", AccessLevel.Administrator, OnFlagCommand);
        CommandSystem.Register("TestOnlyInventoryInspect", AccessLevel.Administrator, OnInspectCommand);
        CommandSystem.Register("TestOnlyCorpseAggressors", AccessLevel.Administrator, OnCorpseAggressorsCommand);
    }

    // Reports the private Corpse._aggressors list (built at death from the owner's aggressor lists) for the newest
    // corpse owned by the given player serial, as "CorpseAggressors owner=<serial> corpse=<serial> aggressors=<serial,...|none>".
    private static void OnCorpseAggressorsCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCorpseAggressors <owner-player-serial>");
            return;
        }

        var field = typeof(Corpse).GetField("_aggressors", BindingFlags.NonPublic | BindingFlags.Instance);
        Corpse? newest = null;
        foreach (var item in World.Items.Values)
        {
            if (item is Corpse { Owner: { } owner } corpse && owner.Serial.Value == serial &&
                (newest is null || corpse.Serial.Value > newest.Serial.Value))
            {
                newest = corpse;
            }
        }

        if (newest is null || field?.GetValue(newest) is not List<Mobile> list)
        {
            e.Mobile.SendMessage($"CorpseAggressors owner={serial:X} corpse=none");
            return;
        }

        var names = list.Count == 0 ? "none" : string.Join(",", list.Select(m => m.Serial.Value.ToString(CultureInfo.InvariantCulture)));
        e.Mobile.SendMessage($"CorpseAggressors owner={serial:X} corpse={newest.Serial.Value:X} aggressors={names}");
    }

    private static void OnFlagCommand(CommandEventArgs e)
    {
        if (e.Length < 1)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyFlagOverride <FeatureFlags property name, e.g. Alpha3StarterCraftMaterials> [true|false]");
            return;
        }

        var settings = ShardRulesConfiguration.Settings;
        if (settings is null)
        {
            e.Mobile.SendMessage("Shard rules configuration is not loaded.");
            return;
        }

        var name = e.GetString(0);
        var value = e.Length < 2 || !string.Equals(e.GetString(1), "false", StringComparison.OrdinalIgnoreCase);
        var property = settings.FeatureFlags.GetType().GetProperty(name, BindingFlags.Public | BindingFlags.Instance);
        if (property is null || property.PropertyType != typeof(bool) || !property.CanWrite)
        {
            e.Mobile.SendMessage($"No writable bool feature flag named '{name}' (use the C# property name, e.g. Alpha3StarterCraftMaterials).");
            return;
        }

        property.SetValue(settings.FeatureFlags, value);
        e.Mobile.SendMessage($"Flag override: {name} in-memory = {value}. Disk config unchanged; discarded on restart.");
    }

    private static void OnInspectCommand(CommandEventArgs e)
    {
        if (e.Length < 1)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyInventoryInspect <player-serial>");
            return;
        }

        var raw = e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)serial) is not PlayerMobile { Backpack: { } pack } player)
        {
            e.Mobile.SendMessage("TestOnlyInventoryInspect requires a live player serial with a backpack.");
            return;
        }

        e.Mobile.SendMessage($"Inspect {player.Name} ({player.Serial}): equipped+backpack items follow.");
        foreach (var item in player.Items)
        {
            if (item != pack)
            {
                Report(e.Mobile, "equipped", item);
            }
        }

        foreach (var item in pack.Items)
        {
            Report(e.Mobile, "backpack", item);
        }
    }

    private static void Report(Mobile to, string where, Item item) =>
        to.SendMessage(
            $"{where}: {item.GetType().Name} serial={item.Serial} amount={item.Amount} " +
            $"lootType={item.LootType} nontransferable={item.Nontransferable}"
        );
}
