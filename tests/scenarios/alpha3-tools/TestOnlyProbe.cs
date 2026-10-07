using System.Globalization;
using System.Reflection;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Misc;
using Server.Mobiles;
using Server.Accounting;

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
        CommandSystem.Register("TestOnlyCorpseInventory", AccessLevel.Administrator, OnCorpseInventoryCommand);
        CommandSystem.Register("TestOnlyReportFlags", AccessLevel.Administrator, OnReportFlagsCommand);
        CommandSystem.Register("TestOnlySkillBankSeed", AccessLevel.Administrator, OnSkillBankSeedCommand);
        CommandSystem.Register("TestOnlyDoubleClick", AccessLevel.Administrator, OnDoubleClickCommand);
        CommandSystem.Register("TestOnlySkillUse", AccessLevel.Administrator, OnSkillUseCommand);
        CommandSystem.Register("TestOnlyFaintAge", AccessLevel.Administrator, OnFaintAgeCommand);
        CommandSystem.Register("TestOnlySkillCap", AccessLevel.Administrator, OnSkillCapCommand);
    }

    // [TestOnlySkillUse <player-serial> <Skill> <count>] makes that many skill checks that always succeed, each at a place the anti-macro
    // check has not seen, so every one reaches the gain hook (Skill Bank, Faint Memories, Mastery, then the stock roll) the way a real use
    // does. Count 0 only reports. Reports "SkillUse <Skill> before=<tenths> after=<tenths> lock=<Up|Down|Locked> total=<tenths>/<cap>".
    private static void OnSkillUseCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            e.Length < 3 || !Enum.TryParse<SkillName>(e.GetString(1), true, out var name) || !int.TryParse(e.GetString(2), out var count))
        {
            e.Mobile.SendMessage("Usage: [TestOnlySkillUse <player-serial> <Skill> <count>");
            return;
        }

        var skill = player.Skills[name];
        var before = skill.BaseFixedPoint;

        for (var i = 0; i < count; i++)
        {
            SkillCheck.CheckSkill(player, skill, new object(), 1.0);
        }

        e.Mobile.SendMessage($"SkillUse {name} before={before} after={skill.BaseFixedPoint} lock={skill.Lock} total={player.Skills.Total}/{player.Skills.Cap}");
    }

    // [TestOnlySkillCap <player-serial> <tenths>] sets the character's total skill cap, so the "at the cap" cases need no 700 points of skills.
    // Reports "SkillCap <tenths> total=<tenths>".
    private static void OnSkillCapCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            e.Length < 2 || !int.TryParse(e.GetString(1), out var cap) || cap <= 0)
        {
            e.Mobile.SendMessage("Usage: [TestOnlySkillCap <player-serial> <tenths>");
            return;
        }

        player.Skills.Cap = cap;
        e.Mobile.SendMessage($"SkillCap {player.Skills.Cap} total={player.Skills.Total}");
    }

    // [TestOnlyFaintAge <player-serial> <hours>] moves the character's Faint Memories grant that far into the past, so the wait can be
    // rehearsed without waiting. Reports "FaintAge remaining=<tenths> granted=<UTC>".
    private static void OnFaintAgeCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            player.Account is not Account account || e.Length < 2 ||
            !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var hours) ||
            !FaintMemoriesService.TryLoad(player, out var state))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyFaintAge <player-serial> <hours> (the character must have Faint Memories)");
            return;
        }

        state = state with { GrantedUtc = state.GrantedUtc.AddHours(-hours) };
        account.SetTag("BritanniaRenaissance.FaintMemories.v1." + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture), FaintMemoriesPolicy.Serialize(state));
        e.Mobile.SendMessage($"FaintAge remaining={state.RemainingTenths} granted={state.GrantedUtc:u}");
    }

    // [TestOnlyDoubleClick <player-serial> <ItemTypeName>] double-clicks the first item of that type in the player's backpack for them (a
    // player's client does the same when they double-click it), so what that opens can be checked without finding the item on screen.
    private static void OnDoubleClickCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (e.Length < 2 || !uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyDoubleClick <player-serial> <ItemTypeName>");
            return;
        }

        Item? item = null;

        if (player.Backpack is { } pack)
        {
            foreach (var held in pack.FindItemsByType<Item>(true))
            {
                if (held.GetType().Name == e.GetString(1))
                {
                    item = held;
                    break;
                }
            }
        }

        if (item is null)
        {
            e.Mobile.SendMessage($"DoubleClick {e.GetString(1)} none");
            return;
        }

        item.OnDoubleClick(player);
        e.Mobile.SendMessage($"DoubleClick {e.GetString(1)} done");
    }

    // [TestOnlySkillBankSeed <player-serial> [+] Anatomy=35 Hiding=12:down ...] replaces the player's Skill Bank with these entries (tenths of
    // a point, optionally set Down), or with "+" adds to what is there (a typed line is short, so a long bank is seeded in pieces), so the
    // [SkillBank window can be looked at with something in it. Reports "SkillBankSeed player=<name> total=<tenths> entries=<n>".
    private static void OnSkillBankSeedCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlySkillBankSeed <player-serial> Skill=tenths[:down] ...");
            return;
        }

        var capacity = ShardRulesConfiguration.Settings!.SkillBank.CapacityTenths;
        var add = e.Length > 1 && e.GetString(1) == "+";
        var ledger = new SkillBankLedger(capacity);

        if (add && !SkillBankLedger.TryDeserialize(player.SkillBankData, capacity, id => (player.Skills[id].Info.Name, player.Skills[id].CapFixedPoint), out ledger))
        {
            ledger = new SkillBankLedger(capacity);
        }

        var entries = 0;

        for (var i = add ? 2 : 1; i < e.Length; i++)
        {
            var parts = e.GetString(i).Split('=', 2);
            var amount = parts.Length == 2 ? parts[1].Split(':') : [];

            if (amount.Length == 0 || !Enum.TryParse<SkillName>(parts[0], true, out var name) || !int.TryParse(amount[0], out var tenths))
            {
                e.Mobile.SendMessage($"Skipped '{e.GetString(i)}'.");
                continue;
            }

            var skill = player.Skills[(int)name];
            ledger.Deposit((int)name, skill.Info.Name, tenths, skill.CapFixedPoint);

            if (amount.Length > 1 && amount[1].Equals("down", StringComparison.OrdinalIgnoreCase))
            {
                ledger.SetRetention((int)name, BankRetention.Down);
            }

            entries++;
        }

        player.SkillBankData = ledger.Serialize();
        e.Mobile.SendMessage($"SkillBankSeed player={player.Name} total={ledger.TotalTenths} entries={entries}");
    }

    // Reports a mobile's aggressor records, "ReportFlags target=<name> aggressors=<attacker>:can=<0|1>:crim=<0|1>:rep=<0|1>,...|none":
    // can = the murder report would be offered for that attacker if the mobile died now, crim = the attacker's last hit was criminal,
    // rep = already reported. For watching how a fight moves the stock report flag.
    private static void OnReportFlagsCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyReportFlags <mobile-serial>");
            return;
        }

        if (World.FindMobile((Serial)serial) is not { } target)
        {
            e.Mobile.SendMessage($"ReportFlags target={serial:X} aggressors=unknown");
            return;
        }

        var rows = target.Aggressors
            .Select(i => $"{i.Attacker.Name}:can={(i.CanReportMurder ? 1 : 0)}:crim={(i.CriminalAggression ? 1 : 0)}:rep={(i.Reported ? 1 : 0)}")
            .ToArray();
        e.Mobile.SendMessage($"ReportFlags target={target.Name} aggressors={(rows.Length == 0 ? "none" : string.Join(",", rows))}");
    }

    // Reports the contents of the newest corpse owned by the given player serial, the same way
    // OnInspectCommand reports a live backpack - for confirming kept-item-death-routing left the
    // corpse without Newbied/Blessed/Nontransferable items after a K4 Execute-triggered death.
    private static void OnCorpseInventoryCommand(CommandEventArgs e)
    {
        var raw = e.Length < 1 ? "" : e.GetString(0);
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCorpseInventory <owner-player-serial>");
            return;
        }

        Corpse? newest = null;
        foreach (var item in World.Items.Values)
        {
            if (item is Corpse { Owner: { } owner } corpse && owner.Serial.Value == serial &&
                (newest is null || corpse.Serial.Value > newest.Serial.Value))
            {
                newest = corpse;
            }
        }

        if (newest is null)
        {
            e.Mobile.SendMessage($"CorpseInventory owner={serial:X} corpse=none");
            return;
        }

        e.Mobile.SendMessage($"CorpseInventory owner={serial:X} corpse={newest.Serial.Value:X}; items follow.");
        foreach (var item in newest.Items)
        {
            Report(e.Mobile, "corpse", item);
        }
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
            $"lootType={item.LootType} nontransferable={item.Nontransferable}" +
            (item is IUsesRemaining uses ? $" usesRemaining={uses.UsesRemaining}" : "")
        );
}
