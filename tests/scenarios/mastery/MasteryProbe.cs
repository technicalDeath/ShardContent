using System.Globalization;
using BritanniaRenaissance.Content;
using Server;
using Server.Accounting;
using Server.Commands;
using Server.Mobiles;

namespace MasteryTools;

// Test-only, disposable-host-only. Reports go back to the staff caller as system messages.
//   [TestOnlyMasteryAge <player-serial> <hours>      moves the character's Mastery anchor that far into the past
//   [TestOnlyMasteryTotals <player-serial>           the character's total skill and cap, in tenths
//   [TestOnlyMasteryLock <player-serial> <skill> <up|down|locked>   sets a skill's lock
//   [TestOnlyMasteryPoison <player-serial>           overwrites the saved state with the earlier (version 1) form
public static class MasteryProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyMasteryAge", AccessLevel.Administrator, OnAge);
        CommandSystem.Register("TestOnlyMasteryTotals", AccessLevel.Administrator, OnTotals);
        CommandSystem.Register("TestOnlyMasteryLock", AccessLevel.Administrator, OnLock);
        CommandSystem.Register("TestOnlyMasteryPoison", AccessLevel.Administrator, OnPoison);
        CommandSystem.Register("TestOnlyMasterySeed", AccessLevel.Administrator, OnSeed);
    }

    // [TestOnlyMasterySeed <player-serial> <hours-into-cycle> [+] Anatomy=stored:claimed ...] ("+" keeps the skills already seeded; a typed line is
    // short, so many skills are seeded in pieces) starts the character's Mastery cycles that many
    // hours ago and gives each named skill that stored allowance (tenths) and claimed (1) or unclaimed (0) state for the current cycle, so the
    // [Mastery window can be looked at. The skills themselves are set separately with [SetSkill. Reports "MasterySeed player=<name> skills=<n>".
    private static void OnSeed(CommandEventArgs e)
    {
        if (!TryPlayer(e, 0, out var player) || e.Length < 2 ||
            !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var hours))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyMasterySeed <player-serial> <hours-into-cycle> Skill=stored:claimed ...");
            return;
        }

        var type = typeof(MasteryProgression);
        var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static;
        var getState = type.GetMethod("GetState", flags)!;
        var saveState = type.GetMethod("SaveState", flags)!;
        var state = (MasteryCharacterState)getState.Invoke(null, [player])!;

        var add = e.Length > 2 && e.GetString(2) == "+";
        state.AnchorUtc = Core.Now.AddHours(-hours);

        if (!add)
        {
            state.Skills.Clear();
        }

        var seeded = 0;

        for (var i = add ? 3 : 2; i < e.Length; i++)
        {
            var parts = e.GetString(i).Split('=', 2);
            var values = parts.Length == 2 ? parts[1].Split(':') : [];

            if (values.Length != 2 || !Enum.TryParse<SkillName>(parts[0], true, out var name) || !int.TryParse(values[0], out var stored))
            {
                e.Mobile.SendMessage($"Skipped '{e.GetString(i)}'.");
                continue;
            }

            state.Skills[(int)name] = new MasterySkillState { AllowanceTenths = stored, LastClaimedCycle = values[1] == "1" ? 0 : -1 };
            seeded++;
        }

        saveState.Invoke(null, [player, state]);
        e.Mobile.SendMessage($"MasterySeed player={player.Name} skills={seeded}");
    }

    private static void OnAge(CommandEventArgs e)
    {
        if (!TryPlayer(e, 0, out var player) || e.Length < 2 ||
            !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var hours))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyMasteryAge <player-serial> <hours>");
            return;
        }

        MasteryProgression.ShiftAnchorEarlier(player, TimeSpan.FromHours(hours));
        e.Mobile.SendMessage($"MasteryAge {player.Name} -{hours}h");
    }

    private static void OnTotals(CommandEventArgs e)
    {
        if (!TryPlayer(e, 0, out var player))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyMasteryTotals <player-serial>");
            return;
        }

        var notUp = new List<string>();
        for (var i = 0; i < player.Skills.Length; i++)
        {
            if (player.Skills[i] is { Lock: not SkillLock.Up } skill)
            {
                notUp.Add($"{skill.SkillName}:{skill.Lock}:{skill.BaseFixedPoint}");
            }
        }

        e.Mobile.SendMessage($"MasteryTotals {player.Skills.Total} {player.Skills.Cap} notUp=[{string.Join(',', notUp)}]");
    }

    private static void OnLock(CommandEventArgs e)
    {
        if (!TryPlayer(e, 0, out var player) || e.Length < 3 ||
            !Enum.TryParse<SkillName>(e.GetString(1), true, out var name) ||
            !Enum.TryParse<SkillLock>(e.GetString(2), true, out var skillLock))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyMasteryLock <player-serial> <skill> <up|down|locked>");
            return;
        }

        player.Skills[name].SetLockNoRelay(skillLock);
        e.Mobile.SendMessage($"MasteryLock {name} {player.Skills[name].Lock}");
    }

    private static void OnPoison(CommandEventArgs e)
    {
        if (!TryPlayer(e, 0, out var player) || player.Account is not Account account)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyMasteryPoison <player-serial>");
            return;
        }

        account.SetTag(
            "BritanniaRenaissance.Mastery." + player.Serial.Value.ToString("X8", CultureInfo.InvariantCulture),
            "{\"version\":1,\"qualifiedDays\":[100],\"skills\":{\"1\":{\"lastProcessedPeriodId\":5,\"pendingTenths\":4}}}"
        );
        MasteryProgression.ForgetCachedState(player);
        e.Mobile.SendMessage("MasteryPoison done");
    }

    private static bool TryPlayer(CommandEventArgs e, int index, out PlayerMobile player)
    {
        player = null!;
        var raw = e.Length > index ? e.GetString(index) : "";
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) && World.FindMobile((Serial)serial) is PlayerMobile p)
        {
            player = p;
            return true;
        }

        return false;
    }
}
