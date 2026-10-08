using Server;
using Server.Mobiles;
using Server.Regions;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Guards come for a player with the Criminal flag, never for one who only has Criminal Intent on, so calling guards on a grey with
/// Intent does nothing and says nothing. When someone calls guards in a guarded town, each Intent player they can see within the call's
/// range is marked for the caller alone, so nobody is left wondering why the guards ignore them (owner ruling 2026-10-07).
/// </summary>
public static class GuardCallNotice
{
    /// <summary>The range of a guard call: the same as the region's own.</summary>
    public const int CallRange = 14;

    public const string Text = "This player has not yet performed a criminal act.";

    private const int Hue = 0x3B2;
    private static bool _configured;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;
        EventSink.Speech += OnSpeech;
    }

    /// <summary>The rule, free of the game: a live caller, in a town whose guards work, and a player whose Intent counts and who is not staff.</summary>
    public static bool ShouldMark(bool callerAlive, bool guardsWork, bool targetIsPlayer, bool targetAlive, bool targetIsStaff, bool intentCounts) =>
        callerAlive && guardsWork && targetIsPlayer && targetAlive && !targetIsStaff && intentCounts;

    private static void OnSpeech(SpeechEventArgs e)
    {
        // Keyword 7 is "guards", the one the guarded region listens for.
        if (e.Mobile is not PlayerMobile caller || caller.Map is null || !e.HasKeyword(0x0007))
        {
            return;
        }

        var region = caller.Region.GetRegion<GuardedRegion>();

        if (region is null)
        {
            return;
        }

        var guardsWork = !region.IsDisabled();

        foreach (var mobile in caller.Map.GetMobilesInRange(caller.Location, CallRange))
        {
            if (mobile != caller && caller.CanSee(mobile) &&
                ShouldMark(
                    caller.Alive,
                    guardsWork,
                    mobile is PlayerMobile,
                    mobile.Alive,
                    mobile.AccessLevel > AccessLevel.Player,
                    mobile is PlayerMobile player && PvpIntentService.ShowsIntent(player)
                ))
            {
                mobile.PrivateOverheadMessage(MessageType.Label, Hue, false, Text, caller.NetState);
            }
        }
    }
}
