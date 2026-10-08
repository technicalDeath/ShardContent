using Server;
using Server.Accounting;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;
using Server.Spells;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Hot Zone travel warning (Beta 2b, added to the camp-travel item at the owner's request). A blue (innocent) player about to
/// be taken into a Hot Zone from outside one by Recall, by a gate (Gate Travel and every other moongate) or by camp travel is
/// warned and must confirm; the confirmation has a "do not show me this warning again when traveling" checkbox, kept on the
/// account and undone with <c>[TravelWarning on</c>. Recall and gates are behind <c>hotZoneTravelWarning</c> (off until the
/// owner acknowledges it) through the stock-null <see cref="SpellHelper.TravelConfirmation"/> hook; camp travel asks the same
/// rule under <c>campingTravel</c>.
/// </summary>
public static class TravelWarningService
{
    private const string Tag = "HotZoneTravelWarning";
    private const string TagOff = "off";
    private const int WarningHue = 0x22;
    private static readonly TimeSpan PromptLife = TimeSpan.FromMinutes(2.0);

    public const string Headline = "You are about to travel into a Hot Zone.";

    public const string Risk = "Other players can attack you in a Hot Zone, and Wards and Loot Protection do not apply.";

    public const string CheckboxLabel = "Do not show me this warning again when traveling";

    private static bool _configured;

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.HotZoneTravelWarning == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        SpellHelper.TravelConfirmation = Ask;
        CommandSystem.Register("TravelWarning", AccessLevel.Player, OnCommand);
    }

    // ---- the rules, free of game objects so they can be tested directly

    /// <summary>
    /// Whether a trip is warned about: the feature is on, the destination is Hot, the traveler is not already in a Hot Zone
    /// (nothing new to warn of), the traveler is blue, and they have not switched the warning off.
    /// </summary>
    public static bool ShouldWarn(bool featureOn, bool destinationHot, bool originHot, bool innocent, bool suppressed) =>
        featureOn && destinationHot && !originHot && innocent && !suppressed;

    public static bool IsSuppressed(string? tag) => string.Equals(tag, TagOff, StringComparison.OrdinalIgnoreCase);

    public static string StatusText(bool suppressed) =>
        suppressed
            ? "The Hot Zone travel warning is off. Use [TravelWarning on to turn it back on."
            : "The Hot Zone travel warning is on. Use [TravelWarning off to turn it off.";

    // ---- in the game

    /// <summary>Blue: not a criminal and not a murderer. Staff are never warned.</summary>
    public static bool IsInnocent(Mobile mobile) =>
        mobile.AccessLevel == AccessLevel.Player && !mobile.Criminal && !mobile.Murderer;

    public static bool IsSuppressed(Mobile mobile) => IsSuppressed((mobile.Account as Account)?.GetTag(Tag));

    public static void SetSuppressed(Mobile mobile, bool suppressed)
    {
        if (mobile.Account is not Account account)
        {
            return;
        }

        if (suppressed)
        {
            account.SetTag(Tag, TagOff);
        }
        else
        {
            account.RemoveTag(Tag);
        }
    }

    /// <summary>Whether this traveler is warned about a trip to a place that is (or is not) Hot, for a feature that is on or off.</summary>
    public static bool Applies(Mobile traveler, bool featureOn, bool destinationHot) =>
        ShouldWarn(featureOn, destinationHot, OutdoorHotZonePolicy.IsHot(traveler), IsInnocent(traveler), IsSuppressed(traveler));

    /// <summary>Records the checkbox when a traveler confirms, and tells them how to undo it.</summary>
    public static void ApplyChoice(Mobile traveler, bool doNotShowAgain)
    {
        if (!doNotShowAgain)
        {
            return;
        }

        SetSuppressed(traveler, true);
        traveler.SendMessage("You will not be warned again before traveling into a Hot Zone. Use [TravelWarning on to turn the warning back on.");
    }

    /// <summary>The Recall and gate hook: shows the prompt and holds the trip until the traveler confirms.</summary>
    private static bool Ask(Mobile traveler, Map map, Point3D destination, Action proceed)
    {
        if (traveler is not PlayerMobile { NetState: not null } player ||
            !Applies(player, Enabled, OutdoorHotZonePolicy.IsHot(map, destination)))
        {
            return false;
        }

        player.SendGump(new HotZoneTravelGump(proceed, Core.Now + PromptLife));
        return true;
    }

    [Usage("TravelWarning [on|off]")]
    [Description("Opens a window for the warning before you travel into a Hot Zone; [TravelWarning on or off sets it.")]
    private static void OnCommand(CommandEventArgs e)
    {
        var mobile = e.Mobile;

        if (e.Length > 0)
        {
            switch (e.GetString(0).ToLowerInvariant())
            {
                case "on":
                    SetSuppressed(mobile, false);
                    break;
                case "off":
                    SetSuppressed(mobile, true);
                    break;
                default:
                    mobile.SendMessage("Use [TravelWarning on or [TravelWarning off.");
                    return;
            }
        }

        if (mobile is PlayerMobile { NetState: not null } player)
        {
            StatusWindows.OpenTravelWarning(player);
            return;
        }

        mobile.SendMessage(StatusText(IsSuppressed(mobile)));
    }

    private sealed class HotZoneTravelGump : DynamicGump
    {
        private const int Height = 270;
        private const int TextWidth = GumpStyle.DialogWidth - 2 * GumpStyle.Margin;

        private readonly Action _proceed;
        private readonly DateTime _expires;

        public override bool Singleton => true;

        public HotZoneTravelGump(Action proceed, DateTime expires) : base(GumpStyle.DialogX, GumpStyle.DialogY)
        {
            _proceed = proceed;
            _expires = expires;
        }

        protected override void BuildLayout(ref DynamicGumpBuilder builder)
        {
            builder.AddPage();
            GumpStyle.Frame(ref builder, "Hot Zone Warning", Headline, GumpStyle.DialogWidth, Height);
            GumpStyle.Banner(ref builder, BannerKind.Danger, Risk, width: TextWidth - 38, height: 54);
            GumpStyle.Tick(ref builder, GumpStyle.Margin, GumpStyle.ContentTop + 70, CheckboxLabel, 1, TextWidth - 32);
            GumpStyle.Rule(ref builder, GumpStyle.RuleInset, Height - GumpStyle.FooterRoom, GumpStyle.DialogWidth - 2 * GumpStyle.RuleInset);
            GumpStyle.OkayCancel(
                ref builder, GumpStyle.Margin, GumpStyle.DialogWidth - GumpStyle.Margin - GumpStyle.OvalWidths[0], GumpStyle.FooterButtonsY(Height), 1, 0
            );
        }

        public override void OnResponse(NetState sender, in RelayInfo info)
        {
            if (sender.Mobile is not { } traveler)
            {
                return;
            }

            if (info.ButtonID != 1)
            {
                // CANCEL or a right-click.
                traveler.SendMessage(WarningHue, "You decide not to travel.");
                return;
            }

            if (Core.Now > _expires)
            {
                traveler.SendMessage(WarningHue, "That took too long. Try again.");
                return;
            }

            ApplyChoice(traveler, info.IsSwitched(1));
            _proceed();
        }
    }
}
