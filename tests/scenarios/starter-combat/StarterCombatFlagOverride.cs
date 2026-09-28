using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Mobiles;

namespace Alpha3StarterCombatProbe;

// Test-only. ShardRulesConfiguration.Validate rejects alpha3StarterCombatGear outright, so it can
// never be true in shard-rules.json, even on a disposable host. This flips the already-loaded
// in-memory setting directly, after Load()'s validation has already passed with it false, so an
// ordinary createcharacter packet can exercise StarterCombatIssuance.Issue. Never touches disk;
// discarded on restart.
public static class StarterCombatFlagOverride
{
    public static void Configure()
    {
        CommandSystem.Register("StarterCombatFlagOverride", AccessLevel.Administrator, OnFlagCommand);
        CommandSystem.Register("StarterCombatInspect", AccessLevel.Administrator, OnInspectCommand);
    }

    private static void OnFlagCommand(CommandEventArgs e)
    {
        var settings = ShardRulesConfiguration.Settings;
        if (settings is null)
        {
            e.Mobile.SendMessage("Shard rules configuration is not loaded.");
            return;
        }

        settings.FeatureFlags.Alpha3StarterCombatGear = true;
        e.Mobile.SendMessage(
            $"Starter combat flag override: Alpha3StarterCombatGear in-memory = " +
            $"{settings.FeatureFlags.Alpha3StarterCombatGear}. Disk config unchanged; discarded on restart."
        );
    }

    // Reports every equipped/backpack item's type, LootType and Nontransferable status for one
    // player, so a live createcharacter result can be verified authoritatively from the server
    // side rather than by client tooltip text.
    private static void OnInspectCommand(CommandEventArgs e)
    {
        if (e.Length < 1)
        {
            e.Mobile.SendMessage("Usage: [StarterCombatInspect <player-serial>");
            return;
        }

        var raw = e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)serial) is not PlayerMobile { Backpack: { } pack } player)
        {
            e.Mobile.SendMessage("StarterCombatInspect requires a live player serial with a backpack.");
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
