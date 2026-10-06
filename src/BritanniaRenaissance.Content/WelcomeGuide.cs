using System.Text.RegularExpressions;
using Server;
using Server.Gumps;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The [Welcome guide: one window with a topic list on the left and the text on the right, instead of a burst of
/// overhead messages that scroll away before they can be read. It opens by itself for a new character and any time with
/// [Welcome. Topics appear only for what is switched on (the Wards, camp travel, the Hot Zone travel warning, the skill
/// commands), and every sentence comes from the rules as deployed (README, the services' own text).
/// </summary>
public static class WelcomeGuide
{
    public sealed record Topic(string Key, string Title, IReadOnlyList<string> Paragraphs);

    /// <summary>What is switched on, so the guide never describes a rule the shard does not have.</summary>
    public readonly record struct Context(bool Theft, bool SkillBank, bool SkillClasses, bool CampTravel, bool TravelWarning);

    public static Context Current =>
        new(
            TheftProtectionService.Enabled,
            SkillBankService.Enabled,
            SkillGainCurveService.Enabled,
            CampTravelService.Enabled,
            TravelWarningService.Enabled
        );

    private const string CommandColor = "#8FD3FF";

    public static IReadOnlyList<Topic> Topics(Context c, CampTravelRules rules)
    {
        var topics = new List<Topic>
        {
            new(
                "welcome",
                "Welcome",
                [
                    "Welcome to Britannia Renaissance: Felucca, without the griefing.",
                    "The rules are Ultima Online's Renaissance rules (April 2000) on Felucca, with a few changes that keep the world fair for everyone.",
                    "Outside the Hot Zones, other players cannot attack you unless you choose to fight. Choose a topic on the left to see how it works, and type [Welcome any time to open this guide again."
                ]
            ),
            new(
                "fighting",
                "Fighting other players",
                [
                    "Ordinary blue players can't be attacked by other players outside the Hot Zones. Criminals and murderers can be attacked anywhere, and you may always defend yourself against someone who attacked you.",
                    "[Intent turns on Criminal Intent: you appear grey and can fight, and be fought by, other players, and killing you doesn't give a murder count. [IntentStatus shows your state.",
                    "A blue player downed by another player is Knocked Out for 90 seconds instead of dying. Only a criminal or murderer who damaged them may [Execute them; if you execute an ordinary blue who never attacked you, they can report you for murder.",
                    "When you die to another player you may report them as a murderer. Five murder counts make them red, and guards pay bounties for a murderer's head."
                ]
            )
        };

        var hot = new List<string>
        {
            "Fire Island, Buccaneer's Den island and the Hythloth dungeon (entered from Fire Island) are permanent player-versus-player zones. Blue players can attack each other there, and Wards and Loot Protection don't apply. Other dungeons are not Hot Zones, and Hot Zones carry no extra rewards.",
            "In a Hot Zone anyone may open a Knocked Out player's pack and take items, like looting a corpse; a blue who does becomes criminal. Newbied, blessed and bound items can't be taken."
        };

        if (c.CampTravel || c.TravelWarning)
        {
            hot.Add(CampTravelService.HotZoneWarningHelp);
        }

        topics.Add(new Topic("hotzones", "Hot Zones", hot));

        if (c.Theft)
        {
            topics.Add(new Topic("ward", "Your Backpack Ward", [StarterOnboarding.WardWhat, StarterOnboarding.WardAlert, StarterOnboarding.WardTip]));
            topics.Add(new Topic("loot", "Loot Protection", [StarterOnboarding.LootProtection]));
        }

        if (c.CampTravel)
        {
            topics.Add(new Topic("camp", "Camp travel", CampTravelService.GuideParagraphs(rules)));
        }

        topics.Add(new Topic("commands", "Commands", Commands(c)));
        return topics;
    }

    /// <summary>One line per command a player can use, only for the features that are on.</summary>
    public static IReadOnlyList<string> Commands(Context c)
    {
        var lines = new List<string>
        {
            "[Welcome - Open this guide.",
            "[Intent - Turn Criminal Intent on or off.",
            "[IntentStatus - See whether it is on.",
            "[Execute - Execute a Knocked Out player you are allowed to.",
            "[MasteryStatus - Your Mastery cycle and what each Mastery skill can still gain."
        };

        if (c.SkillBank)
        {
            lines.Add("[SkillBank - Skills banked when the skill cap pushed a skill down, and whether each is kept.");
        }

        if (c.SkillClasses)
        {
            lines.Add("[SkillClasses - How fast each skill trains.");
        }

        if (c.CampTravel)
        {
            lines.Add("[CampTravel - Travel to a campfire lit by a member of your party.");
        }

        if (c.CampTravel || c.TravelWarning)
        {
            lines.Add("[TravelWarning - Turn the Hot Zone travel warning on or off.");
        }

        return lines;
    }

    private const int CharactersPerLine = 58;
    private const int LineHeight = 18;
    private const int Width = 640;
    private const int Height = 500;
    private const int NavWidth = 190;
    private const int ContentTop = 108;
    private const int ContentHeight = Height - 178;

    /// <summary>The page body: paragraphs separated by a blank line (a command list by a line break), commands picked out in color.</summary>
    public static string Body(Topic topic) =>
        string.Join(
            topic.Key == "commands" ? "<BR>" : "<BR><BR>",
            topic.Paragraphs.Select(p => Highlight(p, topic.Key == "commands"))
        );

    /// <summary>How many lines of the page's text box a topic needs, a little on the generous side.</summary>
    public static int EstimateLines(Topic topic)
    {
        var lines = 0;

        foreach (var paragraph in topic.Paragraphs)
        {
            lines += (paragraph.Length + CharactersPerLine - 1) / CharactersPerLine;
        }

        return topic.Key == "commands" ? lines : lines + Math.Max(0, topic.Paragraphs.Count - 1);
    }

    /// <summary>A scrollbar only when the text will not fit, so short pages are not dressed up with one.</summary>
    public static bool NeedsScroll(Topic topic) => EstimateLines(topic) > ContentHeight / LineHeight;

    private static readonly Regex CommandPattern = new(@"\[[A-Z][A-Za-z]*", RegexOptions.Compiled);

    /// <summary>Colors each [Command. In the command list the command stands alone, so the line is split at its first " - ".</summary>
    public static string Highlight(string text, bool listLine)
    {
        if (listLine)
        {
            var gap = text.IndexOf(" - ", StringComparison.Ordinal);

            if (gap > 0)
            {
                return $"<BASEFONT COLOR={CommandColor}>{text[..gap]}</BASEFONT>{text[gap..]}";
            }
        }

        return CommandPattern.Replace(text, m => $"<BASEFONT COLOR={CommandColor}>{m.Value}</BASEFONT>");
    }

    public static void Open(PlayerMobile player)
    {
        if (player.NetState is null)
        {
            return;
        }

        player.SendGump(new WelcomeGump(Topics(Current, ShardRulesConfiguration.Settings?.CampTravel ?? new CampTravelRules())));
    }

    private sealed class WelcomeGump : DynamicGump
    {
        private readonly IReadOnlyList<Topic> _topics;

        public override bool Singleton => true;

        public WelcomeGump(IReadOnlyList<Topic> topics) : base(40, 30) => _topics = topics;

        protected override void BuildLayout(ref DynamicGumpBuilder builder)
        {
            builder.AddPage();
            builder.AddBackground(0, 0, Width, Height, 9200);
            builder.AddImageTiled(10, 10, Width - 20, Height - 20, 2624);
            builder.AddHtml(20, 18, Width - 40, 24, "Britannia Renaissance", "#FFD060", size: 5, align: TextAlignment.Center);
            builder.AddHtml(20, 44, Width - 40, 20, "Felucca, without the griefing", "#BBBBBB", align: TextAlignment.Center);
            builder.AddImageTiled(NavWidth + 14, 72, 2, Height - 130, 2701);

            builder.AddButton(Width - 120, Height - 44, 4005, 4007, 0);
            builder.AddHtml(Width - 80, Height - 42, 60, 20, "Close", "#FFFFFF");
            builder.AddHtml(24, Height - 42, 300, 20, "Type [Welcome to open this guide again.", "#999999");

            for (var page = 0; page < _topics.Count; page++)
            {
                builder.AddPage(page + 1);

                for (var i = 0; i < _topics.Count; i++)
                {
                    var y = 80 + i * 44;
                    var selected = i == page;
                    var art = selected ? 4007 : 4005;

                    builder.AddButton(22, y, art, 4007, 0, GumpButtonType.Page, i + 1);
                    builder.AddHtml(62, y + 2, NavWidth - 52, 24, _topics[i].Title, selected ? "#FFD060" : "#FFFFFF", fontStyle: (byte)(selected ? 1 : 0));
                }

                var topic = _topics[page];

                builder.AddHtml(NavWidth + 30, 76, Width - NavWidth - 50, 26, topic.Title, "#FFD060", size: 4);
                builder.AddHtml(NavWidth + 30, ContentTop, Width - NavWidth - 50, ContentHeight, Body(topic), "#FFFFFF", scrollbar: NeedsScroll(topic));

                if (page + 1 < _topics.Count)
                {
                    builder.AddButton(Width - 290, Height - 44, 4005, 4007, 0, GumpButtonType.Page, page + 2);
                    builder.AddHtml(Width - 250, Height - 42, 110, 20, "Next topic", "#FFFFFF");
                }
            }
        }

        public override void OnResponse(NetState sender, in RelayInfo info)
        {
        }
    }
}
