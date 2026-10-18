using Server;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The "your item is wearing out" notice (docs/To-Do-List.md, owner 2026-10-12), behind <c>featureFlags.wearNotice</c>. A watch over online players looks at what each one is wearing
/// that has durability (a weapon, a shield, an armor piece) and says one line the moment an item drops to a quarter of its durability or less. It never says anything for an item it
/// first sees already low (a login, a newly equipped worn item, a server restart), so an item is warned about once as it crosses the line, and again only after something brought it back
/// above the line and it fell below it again.
/// </summary>
public static class WearNoticeService
{
    public const int WarnPercent = 25;

    /// <summary>A tool has no stated maximum (a stock tool gets 25 to 75 uses when it is made), so the warning comes when this few uses are left.</summary>
    public const int ToolWarnUses = 3;
    public const int PollSeconds = 2;

    private static readonly Dictionary<uint, bool> WasLow = new();
    private static readonly Dictionary<uint, bool> ToolWasLow = new();
    private static readonly List<NetState> Online = [];
    private static bool _configured;
    private static int _ticks;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.WearNotice == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        Server.Timer.StartTimer(TimeSpan.FromSeconds(PollSeconds), TimeSpan.FromSeconds(PollSeconds), Poll);
    }

    /// <summary>At or below a quarter of the maximum. An item with no maximum has no durability to speak of.</summary>
    public static bool IsLow(int hits, int max) => max > 0 && hits * 100 <= max * WarnPercent;

    /// <summary>A tool with one to three uses left; at 0 it is already gone.</summary>
    public static bool ToolIsLow(int usesRemaining) => usesRemaining > 0 && usesRemaining <= ToolWarnUses;

    public static string ToolMessage(string toolName) =>
        $"Your {(string.IsNullOrWhiteSpace(toolName) ? "tool" : toolName.Trim().ToLowerInvariant())} is nearly worn out: only a few more uses are left. Buy or make another one.";

    /// <summary>The line the player sees; the item's own name, in lower case.</summary>
    public static string Message(string itemName) =>
        $"Your {(string.IsNullOrWhiteSpace(itemName) ? "equipment" : itemName.Trim().ToLowerInvariant())} is badly worn: about a quarter of its durability is left.";

    private static void Poll()
    {
        if (!Enabled)
        {
            return;
        }

        Online.Clear();
        Online.AddRange(NetState.Instances);

        foreach (var state in Online)
        {
            if (state.Mobile is PlayerMobile { Deleted: false } player)
            {
                Watch(player);
            }
        }

        if (++_ticks % 90 == 0)
        {
            Forget();
        }
    }

    private static void Watch(PlayerMobile player)
    {
        if (player.Backpack is { } pack)
        {
            foreach (var item in pack.FindItems(true))
            {
                if (item is BaseTool tool)
                {
                    WatchTool(player, tool);
                }
            }
        }

        foreach (var item in player.Items)
        {
            if (item is BaseTool worn)
            {
                WatchTool(player, worn);
                continue;
            }

            var (hits, max) = CombatBarService.DurabilityOf(item);

            if (max <= 0)
            {
                continue;
            }

            var low = IsLow(hits, max);
            var serial = item.Serial.Value;

            if (WasLow.TryGetValue(serial, out var before) && !before && low)
            {
                player.SendMessage(0x22, Message(string.IsNullOrWhiteSpace(item.Name) ? item.ItemData.Name : item.Name));
            }

            WasLow[serial] = low;
        }
    }

    private static void WatchTool(PlayerMobile player, BaseTool tool)
    {
        var low = ToolIsLow(tool.UsesRemaining);
        var serial = tool.Serial.Value;

        if (ToolWasLow.TryGetValue(serial, out var before) && !before && low)
        {
            player.SendMessage(0x22, ToolMessage(string.IsNullOrWhiteSpace(tool.Name) ? tool.ItemData.Name : tool.Name));
        }

        ToolWasLow[serial] = low;
    }

    /// <summary>Drops the memory of items that no longer exist.</summary>
    private static void Forget()
    {
        List<uint>? gone = null;

        foreach (var serial in WasLow.Keys)
        {
            if (World.FindItem((Serial)serial) is not { Deleted: false })
            {
                (gone ??= []).Add(serial);
            }
        }

        if (gone is not null)
        {
            foreach (var serial in gone)
            {
                WasLow.Remove(serial);
            }

            gone.Clear();
        }

        foreach (var serial in ToolWasLow.Keys)
        {
            if (World.FindItem((Serial)serial) is not { Deleted: false })
            {
                (gone ??= []).Add(serial);
            }
        }

        if (gone is not null)
        {
            foreach (var serial in gone)
            {
                ToolWasLow.Remove(serial);
            }
        }
    }
}
