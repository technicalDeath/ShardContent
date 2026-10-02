using System.Globalization;
using BritanniaRenaissance.Content;
using Server;
using Server.Commands;
using Server.Items;
using Server.Mobiles;

namespace WardTools;

// Test-only, disposable-host-only. Reports go back to the staff caller as system messages.
//   [TestOnlyWardAdd <player-serial>             puts a regular (non-starter) BackpackWard in the player's pack
//   [TestOnlyWardPrime <ward-serial> <player>    Primes that Ward for the player (as a theft event would)
//   [TestOnlyWardMove <ward-serial> <player>     drops the Ward into another player's backpack (a transfer)
//   [TestOnlyWardAge <ward-serial> <minutes>     moves the Ward's last-activity time that far into the past
//   [TestOnlyWardReport <ward-serial>            phase, protected serial, loot type, blessing, holder, last activity, counts
//   [TestOnlyWardFind <player-serial>            the serials of every Ward in the player's pack
public static class WardProbe
{
    public static void Configure()
    {
        CommandSystem.Register("TestOnlyWardAdd", AccessLevel.Administrator, OnAdd);
        CommandSystem.Register("TestOnlyWardPrime", AccessLevel.Administrator, OnPrime);
        CommandSystem.Register("TestOnlyWardMove", AccessLevel.Administrator, OnMove);
        CommandSystem.Register("TestOnlyWardAge", AccessLevel.Administrator, OnAge);
        CommandSystem.Register("TestOnlyWardReport", AccessLevel.Administrator, OnReport);
        CommandSystem.Register("TestOnlyWardFind", AccessLevel.Administrator, OnFind);
    }

    private static void OnAdd(CommandEventArgs e)
    {
        if (!TryPlayer(e, 0, out var player) || player.Backpack is null)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyWardAdd <player-serial>");
            return;
        }

        var ward = new BackpackWard();
        player.Backpack.DropItem(ward);
        e.Mobile.SendMessage($"WardAdd {ward.Serial.Value:X8}");
    }

    private static void OnPrime(CommandEventArgs e)
    {
        if (!TryWard(e, 0, out var ward) || !TryPlayer(e, 1, out var player))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyWardPrime <ward-serial> <player-serial>");
            return;
        }

        ward.Prime(player);

        // A real theft event registers the Ward with the service's sweep; do the same here.
        var tracking = (HashSet<BackpackWard>)typeof(BackpackWardService)
            .GetField("Tracking", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static)!
            .GetValue(null)!;
        tracking.Add(ward);

        e.Mobile.SendMessage($"WardPrime {ward.Serial.Value:X8} {ward.State.Phase}");
    }

    private static void OnMove(CommandEventArgs e)
    {
        if (!TryWard(e, 0, out var ward) || !TryPlayer(e, 1, out var player) || player.Backpack is null)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyWardMove <ward-serial> <player-serial>");
            return;
        }

        player.Backpack.DropItem(ward);
        e.Mobile.SendMessage($"WardMove {ward.Serial.Value:X8} -> {player.Name}");
    }

    private static void OnAge(CommandEventArgs e)
    {
        if (!TryWard(e, 0, out var ward) || e.Length < 2 ||
            !double.TryParse(e.GetString(1), NumberStyles.Float, CultureInfo.InvariantCulture, out var minutes))
        {
            e.Mobile.SendMessage("Usage: [TestOnlyWardAge <ward-serial> <minutes>");
            return;
        }

        var s = ward.State;
        s.Restore(s.Phase, s.ProtectedSerial, s.LastActivityUtc - TimeSpan.FromMinutes(minutes), s.Successes, s.Caught);
        e.Mobile.SendMessage($"WardAge {ward.Serial.Value:X8} last activity now {s.LastActivityUtc:u}");
    }

    private static void OnReport(CommandEventArgs e)
    {
        if (!TryWard(e, 0, out var ward))
        {
            e.Mobile.SendMessage("WardReport missing (deleted or no such Ward)");
            return;
        }

        var s = ward.State;
        var holder = ward.RootParent is Mobile m ? $"{m.Name}/{m.Serial.Value:X8}" : "none";
        e.Mobile.SendMessage(
            $"WardReport {ward.Serial.Value:X8} phase={s.Phase} protected={s.ProtectedSerial:X8} loot={ward.LootType} " +
            $"blessedFor={ward.BlessedFor?.Serial.Value.ToString("X8") ?? "none"} holder={holder} last={s.LastActivityUtc:O} " +
            $"successes={string.Join(',', s.Successes.Select(p => $"{p.Key}:{p.Value}"))} caught={string.Join(',', s.Caught)}"
        );
    }

    private static void OnFind(CommandEventArgs e)
    {
        if (!TryPlayer(e, 0, out var player) || player.Backpack is null)
        {
            e.Mobile.SendMessage("Usage: [TestOnlyWardFind <player-serial>");
            return;
        }

        var ids = new List<string>();

        foreach (var item in player.Backpack.FindItemsByType<BackpackWard>(true))
        {
            ids.Add(item.Serial.Value.ToString("X8"));
        }

        e.Mobile.SendMessage($"WardFind {string.Join(' ', ids)}");
    }

    private static bool TryWard(CommandEventArgs e, int index, out BackpackWard ward)
    {
        ward = null!;
        var raw = e.Length > index ? e.GetString(index) : "";
        var hex = raw.StartsWith("0x", StringComparison.OrdinalIgnoreCase) ? raw[2..] : raw;
        if (uint.TryParse(hex, NumberStyles.HexNumber, null, out var serial) && World.FindItem((Serial)serial) is BackpackWard w && !w.Deleted)
        {
            ward = w;
            return true;
        }

        return false;
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
