using System.Text.RegularExpressions;
using Server;
using Server.Gumps;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The three small windows built on <see cref="StatusWindow"/>: Criminal Intent ([IntentStatus), the Hot Zone travel warning
/// ([TravelWarning) and a Backpack Ward (double-click). What each says is worked out by pure methods so it can be tested; the Open
/// methods only send it.
/// </summary>
public static class StatusWindows
{
    private const int ButtonChange = 1;

    private static readonly Regex IntentPrefix = new(@"^Criminal Intent is (on|off): ", RegexOptions.Compiled);

    /// <summary>What a status window says: the headline and its color, the sentences, and the label of the button that changes it (none if it cannot be changed).</summary>
    public sealed record View(string Headline, string HeadlineColor, IReadOnlyList<string> Paragraphs, string? ButtonLabel);

    // ---- Criminal Intent

    public static View DescribeIntent(bool safeWorld, bool hotZones, bool intentOn, bool criminalOrMurderer)
    {
        if (!safeWorld)
        {
            return new View("Not used here", GumpStyle.Muted, ["Criminal Intent is not used on this shard."], null);
        }

        var lines = PvpIntentService.DescribeForPlayer(true, hotZones, intentOn, criminalOrMurderer).ToArray();

        // The headline already says whether it is on, so the sentence starts at what that means.
        var meaning = IntentPrefix.Replace(lines[0], string.Empty);
        var paragraphs = new List<string> { char.ToUpperInvariant(meaning[0]) + meaning[1..] };

        // The second line is what a player may not do (a criminal) or what Intent is not (everyone else); the third is the typed
        // command, which the button replaces.
        paragraphs.Add(lines[1]);

        return new View(
            intentOn ? "Criminal Intent is ON" : "Criminal Intent is OFF",
            intentOn ? GumpStyle.Danger : GumpStyle.Good,
            paragraphs,
            criminalOrMurderer ? null : intentOn ? "Turn Criminal Intent off" : "Turn Criminal Intent on"
        );
    }

    public static void OpenIntent(PlayerMobile player)
    {
        if (player.NetState is null)
        {
            return;
        }

        var view = DescribeIntent(
            PvpIntentService.SafeWorldEnabled,
            OutdoorHotZonePolicy.Enabled,
            PvpIntentService.IsIntentEnabled(player),
            player.Criminal || player.Murderer
        );

        Send(
            player, "Criminal Intent", "Whether other players may fight you", view, "Type [Intent to switch it without this window.",
            static (p, id) =>
            {
                if (id == ButtonChange)
                {
                    PvpIntentService.ToggleIntent(p);
                    OpenIntent(p);
                }
            }
        );
    }

    // ---- the Hot Zone travel warning

    public static View DescribeTravelWarning(bool inUse, bool warningOff)
    {
        if (!inUse)
        {
            return new View("Not in use", GumpStyle.Muted, ["The Hot Zone travel warning is not in use on this shard right now."], null);
        }

        return new View(
            warningOff ? "The warning is OFF" : "The warning is ON",
            warningOff ? GumpStyle.Danger : GumpStyle.Good,
            [
                "When Recall, a gate or camp travel is about to take you into a Hot Zone from outside one, you are asked to confirm first. " +
                "Only blue players are asked.",
                warningOff
                    ? "You will not be asked. Turn it back on to be warned again."
                    : "You can also tick \"Do not show me this warning again when traveling\" on the warning itself."
            ],
            warningOff ? "Turn the warning on" : "Turn the warning off"
        );
    }

    public static void OpenTravelWarning(PlayerMobile player)
    {
        if (player.NetState is null)
        {
            return;
        }

        var view = DescribeTravelWarning(
            TravelWarningService.Enabled || CampTravelService.Enabled,
            TravelWarningService.IsSuppressed(player)
        );

        Send(
            player, "Hot Zone Travel Warning", "Asked before you travel into a Hot Zone", view, "Type [TravelWarning on or off.",
            static (p, id) =>
            {
                if (id == ButtonChange)
                {
                    TravelWarningService.SetSuppressed(p, !TravelWarningService.IsSuppressed(p));
                    OpenTravelWarning(p);
                }
            }
        );
    }

    // ---- a Backpack Ward

    private static readonly Regex StatusPrefix = new(@"^Status: [A-Za-z]+\.\s*", RegexOptions.Compiled);

    /// <summary>The Ward's own sentences, with "Status: Primed." taken off the front of the line that carries it (the headline says it).</summary>
    public static View DescribeWard(bool enabled, WardPhase phase, IEnumerable<string> lines)
    {
        var paragraphs = lines.Select(line => StatusPrefix.Replace(line, string.Empty)).Where(line => line.Length > 0).ToArray();

        if (!enabled)
        {
            return new View("Switched off", GumpStyle.Muted, paragraphs, null);
        }

        return new View(
            phase.ToString(),
            phase switch { WardPhase.Activated => GumpStyle.Good, WardPhase.Primed => GumpStyle.Command, _ => GumpStyle.Muted },
            paragraphs,
            null
        );
    }

    public static void OpenWard(PlayerMobile player, bool enabled, WardPhase phase, IEnumerable<string> lines)
    {
        if (player.NetState is null)
        {
            return;
        }

        Send(player, "Backpack Ward", "Watches your backpack for thieves", DescribeWard(enabled, phase, lines), "Double-click a Ward to see this again.", null);
    }

    private static void Send(PlayerMobile player, string title, string subtitle, View view, string footerHint, Action<PlayerMobile, int>? onButton) =>
        player.SendGump(
            new StatusWindow(
                title,
                subtitle,
                view.Headline,
                view.HeadlineColor,
                view.Paragraphs,
                view.ButtonLabel is null ? [] : [new StatusWindow.WindowButton(view.ButtonLabel, ButtonChange)],
                footerHint,
                onButton
            )
        );
}
