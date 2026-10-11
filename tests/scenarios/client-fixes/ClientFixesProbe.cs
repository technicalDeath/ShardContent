using System.Globalization;
using Server;
using Server.Commands;
using Server.Engines.BuffIcons;
using Server.Items;
using Server.Mobiles;

namespace ClientFixesTools;

// Test-only, disposable-host-only.
//   [TestOnlyBuff <player> <seconds>]   adds a stock Strength buff icon with that countdown, so the client shows an icon whose tooltip carries the time left
//   [TestOnlyCampfire <player>]         lights a stock campfire at the player's feet (Add refuses it: the type is not marked constructible)
public static class ClientFixesProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyBuff", AccessLevel.Administrator, OnBuff);
        CommandSystem.Register("TestOnlyCampfire", AccessLevel.Administrator, OnCampfire);
    }

    private static void OnCampfire(CommandEventArgs e)
    {
        var hex = e.Length > 0 ? e.GetString(0) : "";
        hex = hex.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? hex[2..] : hex;

        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyCampfire <player>");
            return;
        }

        new Campfire(player).MoveToWorld(player.Location, player.Map);
        e.Mobile.SendMessage($"TestOnlyCampfire lit at {player.Location}");
    }

    private static void OnBuff(CommandEventArgs e)
    {
        var hex = e.Length > 0 ? e.GetString(0) : "";
        hex = hex.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? hex[2..] : hex;

        if (!uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) || World.FindMobile((Serial)serial) is not PlayerMobile player ||
            e.Length < 2 || !int.TryParse(e.GetString(1), out var seconds))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyBuff <player> <seconds>");
            return;
        }

        player.AddBuff(new BuffInfo(BuffIcon.Strength, 1075845, TimeSpan.FromSeconds(seconds), "10"));
        e.Mobile.SendMessage($"TestOnlyBuff added a {seconds} s Strength icon");
    }
}
