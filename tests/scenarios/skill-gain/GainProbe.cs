using System.Text.Json;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Misc;
using Server.Mobiles;

namespace SkillGainTools;

// Test-only, disposable-host-only. Results are JSON beside the host's Server.dll so a driver reads
// authoritative server state.
//   [TestOnlyGainRun <player-serial> <SkillName> <base> <n> <chance> <curve|stock|asis> [reset]
//       Runs n stock skill checks (SkillCheck.CheckSkill, the same call a skill use ends in) on the player's
//       skill and counts the tenths gained. reset 1 (default) puts the skill back to <base> before every check, so
//       each check is an independent sample at that value; reset 0 lets the skill climb. "stock" switches the
//       skillGainCurve flag off in memory for the run (and back), which is the control for the same server; "asis" leaves the flag as it is.
//   [TestOnlyGainBank <player-serial> <SkillName> <tenths>
//       Seeds the player's Skill Bank with a balance for that skill (the same ledger Skill Bank writes).
//   [TestOnlyGainReport <player-serial> <SkillName>
//       Current skill value, bank balance and the curve multiplier at the current value.
public static class GainProbe
{
    private const string Prefix = "gain-";

    public static void Configure()
    {
        CommandSystem.Register("TestOnlyGainRun", AccessLevel.Administrator, OnRun);
        CommandSystem.Register("TestOnlyGainBank", AccessLevel.Administrator, OnBank);
        CommandSystem.Register("TestOnlyGainReport", AccessLevel.Administrator, OnReport);
        CommandSystem.Register("TestOnlyGainSet", AccessLevel.Administrator, OnSet);
        CommandSystem.Register("TestOnlyGainFlag", AccessLevel.Administrator, OnFlag);
    }

    private static bool TryPlayer(CommandEventArgs e, out PlayerMobile player, out Skill skill)
    {
        player = null!;
        skill = null!;

        if (e.Length < 2 || !int.TryParse(e.GetString(0), System.Globalization.NumberStyles.HexNumber, null, out var serial) ||
            World.FindMobile((Serial)(uint)serial) is not PlayerMobile found ||
            !Enum.TryParse<SkillName>(e.GetString(1), true, out var name))
        {
            e.Mobile.SendMessage("Usage: <hex player serial> <SkillName> ...");
            return false;
        }

        player = found;
        skill = player.Skills[name];
        return true;
    }

    private static void Write(PlayerMobile player, string what, object data)
    {
        var path = Path.Combine(Core.BaseDirectory, $"{Prefix}{what}-{player.Serial.Value:X}.json");
        File.WriteAllText(path, JsonSerializer.Serialize(data));
    }

    private static void OnRun(CommandEventArgs e)
    {
        if (!TryPlayer(e, out var player, out var skill) || e.Length < 6)
        {
            return;
        }

        var start = double.Parse(e.GetString(2), System.Globalization.CultureInfo.InvariantCulture);
        var n = int.Parse(e.GetString(3));
        var chance = double.Parse(e.GetString(4), System.Globalization.CultureInfo.InvariantCulture);
        var modeName = e.GetString(5).ToLowerInvariant();
        var stock = modeName == "stock";
        var reset = e.Length < 7 || e.GetString(6) != "0";
        var startFixed = (int)Math.Round(start * 10);

        var flags = ShardRulesConfiguration.Settings.FeatureFlags;
        var original = flags.SkillGainCurve;
        if (modeName != "asis")
        {
            flags.SkillGainCurve = !stock;
        }
        var gainedTenths = 0;
        var gainEvents = 0;
        var multiplier = 1.0;

        try
        {
            skill.BaseFixedPoint = startFixed;
            multiplier = SkillGainCurveService.GetMultiplier(player, skill);
            for (var i = 0; i < n; i++)
            {
                if (reset)
                {
                    skill.BaseFixedPoint = startFixed;
                }

                var before = skill.BaseFixedPoint;
                SkillCheck.CheckSkill(player, skill, new object(), chance);
                var delta = skill.BaseFixedPoint - before;
                if (delta > 0)
                {
                    gainEvents++;
                    gainedTenths += delta;
                }
            }
        }
        finally
        {
            flags.SkillGainCurve = original;
        }

        var end = skill.BaseFixedPoint;
        skill.BaseFixedPoint = startFixed;
        Write(player, "run", new
        {
            skill = skill.SkillName.ToString(),
            start,
            n,
            chance,
            mode = modeName,
            multiplierAtStart = multiplier,
            gainEvents,
            gainedTenths,
            rate = (double)gainEvents / n,
            endFixed = end
        });
    }

    private static void OnBank(CommandEventArgs e)
    {
        if (!TryPlayer(e, out var player, out var skill) || e.Length < 3)
        {
            return;
        }

        var tenths = int.Parse(e.GetString(2));
        var ledger = new SkillBankLedger(ShardRulesConfiguration.Settings.SkillBank.CapacityTenths);
        var result = ledger.Deposit(skill.SkillID, skill.Info.Name, tenths, skill.CapFixedPoint);
        player.SkillBankData = ledger.Serialize();
        Write(player, "bank", new { skill = skill.SkillName.ToString(), tenths, result.BankedTenths });
    }

    private static void OnReport(CommandEventArgs e)
    {
        if (!TryPlayer(e, out var player, out var skill))
        {
            return;
        }

        var balance = 0;
        if (SkillBankLedger.TryDeserialize(
                player.SkillBankData,
                ShardRulesConfiguration.Settings.SkillBank.CapacityTenths,
                id => (player.Skills[id].Info.Name, player.Skills[id].CapFixedPoint),
                out var ledger
            ))
        {
            balance = ledger.GetBalance(skill.SkillID);
        }

        Write(player, "report", new
        {
            skill = skill.SkillName.ToString(),
            baseTenths = skill.BaseFixedPoint,
            bankTenths = balance,
            multiplier = SkillGainCurveService.GetMultiplier(player, skill),
            enabled = SkillGainCurveService.Enabled,
            total = player.Skills.Total
        });
    }

    // [TestOnlyGainSet <player-serial> <SkillName> <base>   sets the skill's base value
    private static void OnSet(CommandEventArgs e)
    {
        if (!TryPlayer(e, out var player, out var skill) || e.Length < 3)
        {
            return;
        }

        skill.BaseFixedPoint = (int)Math.Round(
            double.Parse(e.GetString(2), System.Globalization.CultureInfo.InvariantCulture) * 10
        );
        Write(player, "set", new { skill = skill.SkillName.ToString(), baseTenths = skill.BaseFixedPoint });
    }

    // [TestOnlyGainFlag on|off   flips featureFlags.skillGainCurve in memory (the disposable host's copy)
    private static void OnFlag(CommandEventArgs e)
    {
        ShardRulesConfiguration.Settings.FeatureFlags.SkillGainCurve = e.Length > 0 && e.GetString(0) == "on";
        e.Mobile.SendMessage($"skillGainCurve is now {SkillGainCurveService.Enabled}");
    }
}
