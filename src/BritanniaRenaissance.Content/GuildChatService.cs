using Server;
using Server.Commands;
using Server.Guilds;
using Server.Mobiles;

namespace BritanniaRenaissance.Content;

/// <summary>
/// Guild chat (behind <c>guildChat</c>, off until the owner acknowledges it; docs/Guild-Chat-Plan.md). The shard keeps the old guild
/// system, which has no chat: the client's <c>\</c> key sends a Guild-type line and the engine, outside the new guild system, says it
/// aloud to everyone within 15 tiles through ordinary speech (where "guards" calls guards and a "[" line runs a command). With the flag on,
/// a Guild line goes to every online member of the speaker's guild and to nobody else, through <see cref="PlayerMobile.GuildSpeechHandler"/>,
/// and <c>[g</c> says the same from the keyboard. Alliance (<c>|</c>) is answered "not available". With the flag off nothing changes.
/// </summary>
public static class GuildChatService
{
    public const string Command = "[g";

    /// <summary>Said once, in the guide and by the command, so nobody is surprised that guild chat is kept for moderation.</summary>
    public const string LoggedNotice = "Guild chat is logged for moderation.";

    public const string NotInGuildText = "You are not in a guild.";
    public const string MutedText = "You can not say anything, you have been squelched.";
    public const string KnockedOutText = "You cannot speak while you are Knocked Out.";
    public const string AllianceText = "Alliance chat is not available here.";
    public const string UsageText = "Type [g followed by your message to talk to your guild, or start a line with the \\ key. " + LoggedNotice;

    private const int RefusalHue = 0x22;
    private const int DefaultHue = 0x3B2;
    private const int StaffRange = 8;
    private static bool _configured;

    public enum Outcome
    {
        /// <summary>Not ours: the flag is off, so the stock path runs.</summary>
        Stock,

        /// <summary>Send it to the guild.</summary>
        Send,

        /// <summary>Nothing to send: an empty line. Nobody is told anything.</summary>
        Empty,

        NotInGuild,
        Muted,
        KnockedOut,
        AllianceUnavailable
    }

    /// <summary>What the rule depends on. A ghost and a hidden player are not here: neither changes the answer.</summary>
    public readonly record struct Facts(bool Enabled, bool IsAlliance, bool HasGuild, bool Squelched, bool CanAct, string? Text);

    public static bool Enabled => ShardRulesConfiguration.Settings?.FeatureFlags.GuildChat == true;

    public static void Configure()
    {
        if (_configured)
        {
            return;
        }

        _configured = true;

        var previous = PlayerMobile.GuildSpeechHandler;

        PlayerMobile.GuildSpeechHandler = (speaker, text, type, hue) => OnGuildSpeech(speaker, text, type, hue) || previous?.Invoke(speaker, text, type, hue) == true;
        CommandSystem.Register("g", AccessLevel.Player, OnCommand);
    }

    // ---- the rule, free of game objects so it can be tested directly

    /// <summary>The first thing that decides what happens to a line, in the order the player should hear about it.</summary>
    public static Outcome Decide(Facts f)
    {
        if (!f.Enabled)
        {
            return Outcome.Stock;
        }

        if (f.IsAlliance)
        {
            return Outcome.AllianceUnavailable;
        }

        if (f.Squelched)
        {
            return Outcome.Muted;
        }

        if (!f.CanAct)
        {
            return Outcome.KnockedOut;
        }

        if (string.IsNullOrWhiteSpace(f.Text))
        {
            return Outcome.Empty;
        }

        return f.HasGuild ? Outcome.Send : Outcome.NotInGuild;
    }

    /// <summary>What the speaker is told for an outcome that sends nothing, or null.</summary>
    public static string? RefusalText(Outcome outcome) =>
        outcome switch
        {
            Outcome.NotInGuild          => NotInGuildText,
            Outcome.Muted               => MutedText,
            Outcome.KnockedOut          => KnockedOutText,
            Outcome.AllianceUnavailable => AllianceText,
            _                           => null
        };

    /// <summary>The colour a line goes out in: the one the client chose, or the journal's own when it chose none.</summary>
    public static int HueFor(int requested, int remembered) => requested != 0 ? requested : remembered != 0 ? remembered : DefaultHue;

    /// <summary>One line of a log entry cannot be split by the text it carries.</summary>
    public static string OneLine(string text) => text.Replace('\r', ' ').Replace('\n', ' ');

    /// <summary>What a staff member near the speaker reads (the engine's own monitoring text for guild chat).</summary>
    public static string StaffText(string text) => $"[Guild]: {text}";

    // ---- in the game

    private static bool OnGuildSpeech(PlayerMobile speaker, string text, MessageType type, int hue)
    {
        if (!Enabled)
        {
            return false;
        }

        Handle(speaker, text, type == MessageType.Alliance, hue);

        return true;
    }

    [Usage("g <message>")]
    [Description("Talk to your guild, wherever its members are. The \\ key does the same.")]
    private static void OnCommand(CommandEventArgs e)
    {
        if (e.Mobile is not PlayerMobile speaker)
        {
            return;
        }

        if (!Enabled)
        {
            speaker.SendMessage(RefusalHue, "Guild chat is not available.");
            return;
        }

        var text = e.ArgString.Trim();

        if (text.Length == 0)
        {
            speaker.SendMessage(UsageText);
            return;
        }

        Handle(speaker, text, false, 0);
    }

    private static void Handle(PlayerMobile speaker, string text, bool alliance, int hue)
    {
        var guild = speaker.Guild as Guild;
        var outcome = Decide(
            new Facts(true, alliance, guild is not null, speaker.Squelched, speaker.CanPerformAction(), text)
        );

        switch (outcome)
        {
            case Outcome.Send:
                Send(speaker, guild!, text, hue);
                break;
            default:
                if (RefusalText(outcome) is { } refusal)
                {
                    speaker.SendMessage(RefusalHue, refusal);
                }

                break;
        }
    }

    private static void Send(PlayerMobile speaker, Guild guild, string text, int hue)
    {
        var colour = HueFor(hue, speaker.GuildMessageHue);

        speaker.GuildMessageHue = colour;
        guild.GuildChat(speaker, colour, text);

        // Staff of higher rank within a few tiles read it as the engine's own chat shows them (the stock monitoring of guild chat).
        foreach (var state in speaker.GetClientsInRange(StaffRange))
        {
            if (state.Mobile is { } viewer && viewer.AccessLevel >= AccessLevel.GameMaster && viewer.AccessLevel > speaker.AccessLevel)
            {
                speaker.PrivateOverheadMessage(MessageType.Regular, speaker.SpeechHue, false, StaffText(text), state);
            }
        }

        ShardAuditLog.Record("guild-chat", "message", speaker, null, $"guild={guild.Name}; text={OneLine(text)}");
    }
}
