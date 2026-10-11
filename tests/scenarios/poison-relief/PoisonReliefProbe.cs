using System.Globalization;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace PoisonReliefTools;

// Test-only, disposable-host-only. Reports come back to the staff caller as system messages.
//   [TestOnlyPoisonFlag on|off|status]                               the flag, switched in memory
//   [TestOnlyPoisonApply <player> <level> <none|orc|player>]         ApplyPoison with that source (a throwaway Orc, or the caller as a player source)
//   [TestOnlyPoisonCure <player>]                                    CurePoison on the player (the end the watcher must see)
//   [TestOnlyPoisonSkills <player> <healing> <anatomy>]              sets the two skills the hint reads
//   [TestOnlyPoisonPack <player>]                                    the Lesser Cure potions in the pack: count, newbied count, weight and the weight limit
public static class PoisonReliefProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyPoisonFlag", AccessLevel.Administrator, OnFlag);
        CommandSystem.Register("TestOnlyPoisonApply", AccessLevel.Administrator, OnApply);
        CommandSystem.Register("TestOnlyPoisonCure", AccessLevel.Administrator, OnCure);
        CommandSystem.Register("TestOnlyPoisonSkills", AccessLevel.Administrator, OnSkills);
        CommandSystem.Register("TestOnlyPoisonPack", AccessLevel.Administrator, OnPack);
    }

    private static DeferredFeatureFlags Flags => ShardRulesConfiguration.Settings!.FeatureFlags;

    private static PlayerMobile? Player(CommandEventArgs e)
    {
        var hex = e.Length > 0 ? e.GetString(0) : "";
        hex = hex.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? hex[2..] : hex;

        return uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) ? World.FindMobile((Serial)serial) as PlayerMobile : null;
    }

    private static void OnFlag(CommandEventArgs e)
    {
        var mode = e.Length > 0 ? e.GetString(0).ToLowerInvariant() : "status";

        if (mode is "on" or "off")
        {
            Flags.PoisonRelief = mode == "on";
        }

        e.Mobile.SendMessage($"PoisonFlag on={Flags.PoisonRelief}");
    }

    private static void OnApply(CommandEventArgs e)
    {
        if (Player(e) is not { } player || e.Length < 3 || !int.TryParse(e.GetString(1), out var level))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPoisonApply <player> <level> <none|orc|player>");
            return;
        }

        var kind = e.GetString(2).ToLowerInvariant();
        Orc? orc = null;

        try
        {
            Mobile? from = null;

            if (kind == "orc")
            {
                orc = new Orc();
                orc.MoveToWorld(player.Location, player.Map);
                from = orc;
            }
            else if (kind == "player")
            {
                from = e.Mobile;
            }

            var result = player.ApplyPoison(from, Poison.GetPoison(level));
            e.Mobile.SendMessage($"PoisonApply result={result} poisoned={player.Poisoned} level={player.Poison?.Level ?? -1} source={kind}");
        }
        finally
        {
            orc?.Delete();
        }
    }

    private static void OnCure(CommandEventArgs e)
    {
        if (Player(e) is not { } player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPoisonCure <player>");
            return;
        }

        var cured = player.CurePoison(player);
        e.Mobile.SendMessage($"PoisonCure cured={cured} poisoned={player.Poisoned}");
    }

    private static void OnSkills(CommandEventArgs e)
    {
        if (Player(e) is not { } player || e.Length < 3 ||
            !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var healing) ||
            !double.TryParse(e.GetString(2), NumberStyles.Float, CultureInfo.InvariantCulture, out var anatomy))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPoisonSkills <player> <healing> <anatomy>");
            return;
        }

        player.Skills[SkillName.Healing].Base = healing;
        player.Skills[SkillName.Anatomy].Base = anatomy;
        e.Mobile.SendMessage(
            string.Create(CultureInfo.InvariantCulture, $"PoisonSkills healing={player.Skills[SkillName.Healing].Value:0.#} anatomy={player.Skills[SkillName.Anatomy].Value:0.#}")
        );
    }

    private static void OnPack(CommandEventArgs e)
    {
        if (Player(e) is not { Backpack: { } pack } player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyPoisonPack <player>");
            return;
        }

        var potions = 0;
        var newbied = 0;

        foreach (var potion in pack.FindItemsByType<LesserCurePotion>())
        {
            potions++;
            newbied += potion.LootType == LootType.Newbied ? 1 : 0;
        }

        e.Mobile.SendMessage($"PoisonPack potions={potions} newbied={newbied} weight={player.TotalWeight} max={player.MaxWeight} alive={player.Alive}");
    }
}
