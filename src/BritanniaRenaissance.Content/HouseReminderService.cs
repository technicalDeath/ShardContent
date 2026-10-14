using Server;
using Server.Accounting;
using Server.Commands;
using Server.Items;
using Server.Mobiles;
using Server.Multis;

namespace BritanniaRenaissance.Content;

/// <summary>
/// House lockdown reminder (docs/House-Lockdown-Reminder-Plan.md), behind <c>featureFlags.houseReminder</c>. When the owner or a co-owner puts an item down on the floor of their own
/// house and it is still loose ten seconds later (not locked down, not secured, not picked up), they are told once a day how to lock it down. The engine event is
/// <c>Item.DroppedToWorld</c>. A player switches it off with <c>[HouseReminder off</c>. The decisions are pure so they can be tested without game objects.
/// </summary>
public static class HouseReminderService
{
    public static readonly TimeSpan Wait = TimeSpan.FromSeconds(10.0);
    public static readonly TimeSpan Cooldown = TimeSpan.FromHours(24.0);

    public const string Text =
        "That item is not locked down, so it may decay or be taken. Say I wish to lock this down, then target it, to keep it. (Type [HouseReminder off to stop these reminders.)";

    private const string OffTagPrefix = "BritanniaRenaissance.HouseReminderOff.v1.";
    private const string LastTagPrefix = "BritanniaRenaissance.HouseReminderLast.v1.";

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.HouseReminder == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        Item.DroppedToWorld += OnDropped;
        CommandSystem.Register("HouseReminder", AccessLevel.Player, OnCommand);
    }

    // ---- the decisions

    /// <summary>Whether a drop starts the ten-second wait: the flag on, an ordinary player, and the owner or a co-owner of the house the item landed in.</summary>
    public static bool ShouldWatch(bool enabled, bool ordinaryPlayer, bool ownerOrCoOwner, bool switchedOff) => enabled && ordinaryPlayer && ownerOrCoOwner && !switchedOff;

    /// <summary>Whether the reminder is sent when the wait ends: the item is still loose in the same house, and the last reminder was long enough ago.</summary>
    public static bool ShouldRemind(bool stillLoose, bool sameHouse, DateTime? lastReminderUtc, DateTime nowUtc) =>
        stillLoose && sameHouse && (lastReminderUtc is null || nowUtc - lastReminderUtc.Value >= Cooldown);

    // ---- the watch

    private static void OnDropped(Mobile from, Item item)
    {
        if (from is not PlayerMobile { Account: Account account } player || item.Deleted || BaseHouse.FindHouseAt(item) is not { } house)
        {
            return;
        }

        var off = account.GetTag($"{OffTagPrefix}{player.Serial.Value}") is not null;

        if (!ShouldWatch(Enabled, player.AccessLevel == AccessLevel.Player, house.IsOwner(player) || house.IsCoOwner(player), off))
        {
            return;
        }

        Server.Timer.DelayCall(Wait, () => Remind(player, account, item, house));
    }

    private static void Remind(PlayerMobile player, Account account, Item item, BaseHouse house)
    {
        if (player.Deleted || player.NetState is null)
        {
            return;
        }

        var loose = !item.Deleted && item.Parent == null && item.Movable && !item.IsLockedDown && !item.IsSecure;
        var same = !item.Deleted && BaseHouse.FindHouseAt(item) == house;
        var tag = $"{LastTagPrefix}{player.Serial.Value}";
        DateTime? last = long.TryParse(account.GetTag(tag), out var ticks) ? new DateTime(ticks, DateTimeKind.Utc) : null;
        var now = DateTime.UtcNow;

        if (!ShouldRemind(loose, same, last, now))
        {
            return;
        }

        account.SetTag(tag, now.Ticks.ToString());
        player.SendMessage(0x35, Text);
    }

    [Usage("HouseReminder [on|off]")]
    [Description("Turns the reminder to lock down items in your house on or off for this character.")]
    private static void OnCommand(CommandEventArgs e)
    {
        if (!Enabled)
        {
            e.Mobile.SendMessage("There is no house reminder to switch.");
            return;
        }

        if (e.Mobile is not PlayerMobile { Account: Account account } player)
        {
            return;
        }

        var tag = $"{OffTagPrefix}{player.Serial.Value}";

        switch (e.Length > 0 ? e.GetString(0).Trim().ToLowerInvariant() : "")
        {
            case "off":
                account.SetTag(tag, "off");
                player.SendMessage("House reminders are off for this character. Type [HouseReminder on to turn them back on.");
                break;
            case "on":
                account.RemoveTag(tag);
                player.SendMessage("House reminders are on for this character: about once a day, when you leave an item loose in your house.");
                break;
            default:
                player.SendMessage($"House reminders are {(account.GetTag(tag) is null ? "on" : "off")} for this character. Type [HouseReminder off or [HouseReminder on.");
                break;
        }
    }
}
