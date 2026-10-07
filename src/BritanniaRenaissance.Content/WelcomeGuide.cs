using System.Globalization;
using System.Text.RegularExpressions;
using Server;
using Server.Gumps;
using Server.Items;
using Server.Mobiles;
using Server.Network;

namespace BritanniaRenaissance.Content;

/// <summary>
/// The [Welcome guide: one window with a topic list on the left and the text on the right, instead of a burst of
/// overhead messages that scroll away before they can be read. It opens by itself for a new character and any time with
/// [Welcome. Topics and sentences appear only for what is switched on, and every claim was checked against the code
/// behind it (PvpIntentService, KnockedOutService, BackpackWardState and its design document, TheftProtectionService,
/// MasteryEngine, SkillBankLedger, CampTravelService) and the owner's rulings; docs/Beta-2b-Camp-Travel-Plan.md records
/// the audit. Numbers come from the configuration, never from memory.
/// </summary>
public static class WelcomeGuide
{
    public sealed record Topic(string Key, string Title, IReadOnlyList<string> Paragraphs);

    /// <summary>What is switched on, so the guide never describes a rule the shard does not have.</summary>
    public readonly record struct Context(
        bool Theft,
        bool SkillBank,
        bool SkillClasses,
        bool CampTravel,
        bool TravelWarning,
        bool SafeWorld = true,
        bool KnockedOut = true,
        bool HotZones = true,
        bool CampingKit = false,
        bool CampingFires = false,
        bool FaintMemories = false
    );

    public static Context Current =>
        new(
            TheftProtectionService.Enabled,
            SkillBankService.Enabled,
            SkillGainCurveService.Enabled,
            CampTravelService.Enabled,
            TravelWarningService.Enabled,
            PvpIntentService.SafeWorldEnabled,
            KnockedOutService.Enabled,
            OutdoorHotZonePolicy.Enabled,
            CampingService.KitEnabled,
            CampingService.FiresEnabled,
            FaintMemoriesService.Enabled
        );

    /// <summary>The numbers the pages quote. The defaults are the shipped values.</summary>
    public sealed record Numbers(
        int SkillCapPoints = 700,
        int BankPoints = 300,
        int EasyTenths = 20,
        int StandardTenths = 10,
        int HardTenths = 6,
        int CycleHours = 24,
        int StoredCycles = 3,
        int WardPrice = 2000,
        int WardBuyBack = 110,
        int WardIngots = 20,
        int WardCraftSkill = 45,
        int RestoreStepTenths = 2,
        int FaintPointsTenths = 50,
        int FaintHours = 24,
        int FaintFloorTenths = 100,
        int FaintCeilingTenths = 900
    )
    {
        public static Numbers Current
        {
            get
            {
                var settings = ShardRulesConfiguration.Settings;

                if (settings is null)
                {
                    return new Numbers();
                }

                int Allowance(string name, int fallback) =>
                    settings.Mastery.AllowanceTenths.TryGetValue(name, out var tenths) && tenths > 0 ? tenths : fallback;

                return new Numbers(
                    settings.Character.TotalSkillCap,
                    settings.SkillBank.CapacityTenths / 10,
                    Allowance("easy", 20),
                    Allowance("standard", 10),
                    Allowance("hard", 6),
                    settings.Mastery.CycleHours,
                    settings.Mastery.BankCycles,
                    settings.WardVendor.StockPerVendor > 0 ? settings.WardVendor.Price : 0,
                    settings.WardVendor.BuyBackPrice,
                    settings.WardCraft.Enabled ? settings.WardCraft.Ingots : 0,
                    (int)settings.WardCraft.MinSkill,
                    settings.SkillBank.RestoreStepTenths,
                    FaintMemoriesPolicy.PointsTenths(settings.FaintMemories),
                    (int)Math.Round(settings.FaintMemories.UnlockHours),
                    FaintMemoriesPolicy.FloorTenths(settings.FaintMemories),
                    FaintMemoriesPolicy.CeilingTenths(settings.FaintMemories)
                );
            }
        }
    }

    private const string CommandColor = "#8FD3FF";
    public const string HeadingMark = "# ";

    public static IReadOnlyList<Topic> Topics(Context c, CampTravelRules rules, Numbers? numbers = null, CampingRules? camping = null)
    {
        var n = numbers ?? new Numbers();
        var topics = new List<Topic> { WelcomeTopic(c) };

        if (c.SafeWorld || c.KnockedOut)
        {
            topics.Add(FightingTopic(c));
        }

        if (c.HotZones)
        {
            topics.Add(HotZoneTopic(c));
        }

        if (c.Theft)
        {
            topics.Add(WardTopic(n));
            topics.Add(LootProtectionTopic());
        }

        topics.Add(MasteryTopic(c, n));

        if (c.SkillBank)
        {
            topics.Add(SkillBankTopic(c, n));
        }

        if (c.CampingKit || c.CampingFires)
        {
            topics.Add(CampingTopic(c, camping ?? new CampingRules()));
        }

        if (c.CampTravel)
        {
            topics.Add(new Topic("camp", "Camp travel", CampTravelService.GuideParagraphs(rules)));
        }

        topics.Add(new Topic("commands", "Commands", Commands(c)));
        return topics;
    }

    private static Topic WelcomeTopic(Context c)
    {
        var paragraphs = new List<string>
        {
            $"Welcome to {ShardBranding.Name}. The rules are Ultima Online's Renaissance rules (April 2000) on Felucca, with the changes described in this guide."
        };

        if (c.SafeWorld)
        {
            paragraphs.Add(
                (c.HotZones ? "Outside the Hot Zones, other" : "Other") +
                " players cannot attack you unless you opt in to fighting with [Intent or break the law. The next page has the details."
            );
        }

        paragraphs.Add("Choose a topic on the left to read how it works, and type [Welcome any time to open this guide again.");
        return new Topic("welcome", "Welcome", paragraphs);
    }

    private static Topic FightingTopic(Context c)
    {
        var paragraphs = new List<string>();
        var knockedOutSeconds = (int)KnockedOutService.Duration.TotalSeconds;

        if (c.SafeWorld)
        {
            paragraphs.Add(
                (c.HotZones ? "Outside the Hot Zones, a" : "A") +
                " player can attack you only if you have Criminal Intent on, you are a criminal or a murderer, or you are already fighting them. " +
                "You can attack another player only by the same rules. Guild wars also allow fighting between the guilds involved."
            );
            paragraphs.Add(
                "[Intent turns Criminal Intent on or off, and it stays as you leave it. While it is on you appear grey and other players may attack you. " +
                "Killing a player who has Intent on is not murder. " + PvpIntentService.NotACriminalNote + " " +
                "You cannot change it while you are a criminal or a murderer. [IntentStatus shows whether it is on."
            );
        }

        if (c.KnockedOut)
        {
            // The purpose, in the owner's words (2026-10-06): a grey or red can walk away from a fight and not take a murder count.
            paragraphs.Add(
                "Knocked Out is how a fight ends without a killing. " +
                $"A player who is not a criminal or a murderer and is brought down by another player is Knocked Out for {knockedOutSeconds} seconds instead of dying. " +
                "While Knocked Out you cannot act, be hurt or be healed, and when it ends you wake with half your health. " +
                "The winner, even a criminal or a murderer, can simply walk away and takes no murder count, because nobody died. " +
                "Monsters and other causes still kill normally."
            );
            paragraphs.Add(
                "Killing is a choice. While a player is Knocked Out, a criminal or murderer who knocked them out, or who has damaged them recently, may [Execute them. " +
                "Nobody else can, including a player who is only grey because of Criminal Intent."
            );
            // Owner ruling 2026-10-06 (K-5 amended): attacking and killing differ. A blue may attack a criminal, a murderer or a player
            // with Intent on, who may fight back and Knock the blue out, but executing the blue is still murder.
            var intentOr = c.SafeWorld ? "the victim had Criminal Intent on or " : string.Empty;
            var targets = c.SafeWorld ? "a criminal, a murderer or a player with Criminal Intent on" : "a criminal or a murderer";
            paragraphs.Add(
                $"An Execute is murder, and the victim can report it, unless {intentOr}the two were at guild war. " +
                $"That is true even if the victim attacked first: a blue may attack {targets}, who may fight back and Knock the blue out, " +
                "but executing the blue still counts. Reporting gives the killer a murder count. " +
                "Fighting back never costs you the report" + (c.HotZones ? ", and a Hot Zone does not make a killing lawful." : ".")
            );
        }
        else
        {
            // Without Knocked Out a death is the stock one: the killer is reportable when they had no right to attack.
            var rights = (c.SafeWorld ? "you have Criminal Intent on, " : string.Empty) +
                         "you are a criminal or a murderer, you attacked them first, or you are at guild war with them";
            paragraphs.Add(
                "If another player kills you and had no right to attack you, you can report them as a murderer, which gives them a murder count. " +
                $"A player has the right to attack you if {rights}. Fighting back does not cost you the report" +
                (c.HotZones ? ", and a Hot Zone does not give the right." : ".")
            );
        }
        paragraphs.Add(
            "Five counts make a player a murderer (red), and a guard pays any bounty posted on a murderer for their head. " +
            "Guards do not take a report from a Thieves' Guild member."
        );

        return new Topic("fighting", "Fighting other players", paragraphs);
    }

    private static Topic HotZoneTopic(Context c)
    {
        var paragraphs = new List<string>
        {
            "Fire Island, Buccaneer's Den island and the Hythloth dungeon (entered from Fire Island) are permanent player-versus-player zones. " +
            "Players in the same Hot Zone can attack each other freely, with or without Criminal Intent, and Wards and Loot Protection do not apply. " +
            "Other dungeons are not Hot Zones, and Hot Zones carry no extra rewards.",
            c.KnockedOut
                ? "Fighting in a Hot Zone is free, but it does not make a killing lawful: if someone executes you there, you can still report them as a murderer " +
                  (c.SafeWorld ? "unless you had Criminal Intent on or were at guild war with them." : "unless you were at guild war with them.")
                : "Fighting in a Hot Zone is free, but it does not make a killing lawful: if someone kills you there and had no other right to attack you, " +
                  "you can still report them as a murderer."
        };

        if (c.KnockedOut)
        {
            paragraphs.Add(
                "While a player is Knocked Out in a Hot Zone, anyone may open their pack and take items from it, like looting a corpse. " +
                "A player who is not already a criminal becomes criminal for doing so. Items that are newbied, blessed or bound cannot be taken, " +
                "and what the player is wearing stays on them. Outside Hot Zones only a criminal or murderer who knocked the player out may loot them."
            );
        }

        if (c.CampTravel || c.TravelWarning)
        {
            paragraphs.Add(CampTravelService.HotZoneWarningHelp);
        }

        return new Topic("hotzones", "Hot Zones", paragraphs);
    }

    private static string Chance(int count) =>
        TheftProtectionService.AdditionalDetectionChance(count) >= 1.0
            ? "certain"
            : $"{TheftProtectionService.AdditionalDetectionChance(count) * 100:0}%";

    private static Topic WardTopic(Numbers n)
    {
        var window = (int)WardState.InactivityWindow.TotalMinutes;
        var sources = new List<string>();

        if (n.WardPrice > 0)
        {
            sources.Add($"Tinker vendors sell them for {n.WardPrice} gold each");
        }

        if (n.WardIngots > 0)
        {
            sources.Add($"Tinkers can craft them from {n.WardIngots} iron ingots (Tinkering {n.WardCraftSkill} or more, in the Miscellaneous list)");
        }

        var more = sources.Count == 0
            ? string.Empty
            : $"More Wards: {string.Join(", and ", sources)}. A Ward you buy or make can be traded until it starts watching a thief." +
              (n.WardBuyBack > 0 && n.WardPrice > 0 ? $" Tinkers buy an unused one back for {n.WardBuyBack} gold." : string.Empty);

        var paragraphs = new List<string>
        {
            HeadingMark + "What it is",
            "A Backpack Ward is a one-use item that watches for thieves. Carry it in your backpack or a bag inside it: it does nothing in a bank, a house, " +
            "on the ground or in a pet's pack. It needs no skill and no switching on. You start with one free Ward, bound to you."
        };

        if (more.Length > 0)
        {
            paragraphs.Add(more);
        }

        paragraphs.Add(HeadingMark + "How it catches thieves");
        paragraphs.Add(
            "A Ward does not change a thief's chance to steal from you, and it never undoes a theft: the thief keeps what they took. " +
            "A thief is caught when a theft from you succeeds and either you detect it in the usual way or the Ward detects it for you. " +
            "A caught thief turns criminal and cannot steal from you again, on any of their characters, until the Ward is used up."
        );
        paragraphs.Add(
            "When a theft from you succeeds undetected, the Ward gets an extra chance to detect it: " +
            $"{Chance(1)} for that thief's first such theft, {Chance(2)} for the second and {Chance(3)} for the third. Each thief is counted separately."
        );
        paragraphs.Add(HeadingMark + "How long it lasts");
        paragraphs.Add(
            $"The Ward watches until {window} minutes pass with no theft attempt against you. Until a theft attempt has been detected, by you or by the Ward, " +
            "it only watches, and then it resets and you keep it. Once one has been detected the Ward is activated: caught thieves stay blocked, and when " +
            $"{window} quiet minutes pass the Ward is used up. A blocked thief's attempts do not restart the timer."
        );
        paragraphs.Add(HeadingMark + "Limits");
        paragraphs.Add(
            "It does not stop thieves it has not caught, and it does nothing inside a Hot Zone. Double-click a Ward to see what it is, where it stands " +
            "(Unprimed, Primed or Activated) and how many quiet minutes are left."
        );

        return new Topic("ward", "Your Backpack Ward", paragraphs);
    }

    private static Topic LootProtectionTopic()
    {
        var minutes = (int)TheftProtectionService.LootProtectionDuration.TotalMinutes;

        return new Topic(
            "loot",
            "Loot Protection",
            [
                "Loot Protection stops repeat looting of your monster kills outside the Hot Zones. When someone takes an item from a monster corpse you have the right to loot " +
                $"and they have no right to, they keep that first item and become criminal as usual. For the next {minutes} minutes they cannot take anything from any monster corpse you have loot rights to.",
                "It is automatic: there is nothing to carry or switch on. It does not protect your backpack, player corpses, pets' packs, items on the ground or " +
                "monster corpses once their loot rights have run out, and it does not apply in Hot Zones."
            ]
        );
    }

    private static string Points(int tenths) => (tenths / 10.0).ToString("0.0", CultureInfo.InvariantCulture);

    /// <summary>The fewest cycles to climb from 90.0 to 100.0 at an allowance of this many tenths per cycle.</summary>
    public static int MinimumCycles(int allowanceTenths) =>
        (MasteryEngine.GrandmasterFixedPoint - MasteryEngine.ThresholdFixedPoint + allowanceTenths - 1) / allowanceTenths;

    private static Topic MasteryTopic(Context c, Numbers n)
    {
        var threshold = MasteryEngine.ThresholdText;
        var classes = c.SkillClasses ? " [SkillClasses lists every skill's class." : string.Empty;
        var bank = c.SkillBank ? " Points held in your Skill Bank come back before Mastery applies." : string.Empty;
        var days = n.CycleHours == 24 ? "days" : "cycles";

        return new Topic(
            "mastery",
            "Mastery",
            [
                HeadingMark + "Why Mastery exists",
                "In stock Ultima Online the last points of a skill are a grind: each one takes the most checks, and for crafters the most ingots or reagents. " +
                "Mastery replaces that grind with a steady daily pace that rewards you for playing. Use a skill each day and it grows, with no marathon sessions and no piles of resources.",
                "Playing more in one day does not make it faster; playing on more days does. A day's allowance takes about " +
                $"{n.EasyTenths} successful uses for an easy skill, {n.StandardTenths} for a standard one and {n.HardTenths} for a hard one.",
                HeadingMark + "How it works",
                $"Below {threshold} a skill gains by chance, as in Ultima Online. From {threshold} it no longer does. Your character has a {n.CycleHours}-hour cycle, " +
                $"which starts the first time you hold a skill at {threshold} or higher, and in each cycle a skill has an allowance: " +
                $"{Points(n.EasyTenths)} for easy skills, {Points(n.StandardTenths)} for standard ones and {Points(n.HardTenths)} for hard ones.{classes}",
                "A skill claims its allowance with its first valid, successful use in the cycle. A valid use is a success that had a real chance of failing: " +
                "trivially easy actions and failed attempts count for nothing. While the allowance lasts, each valid, successful use gives +0.1, up to Grandmaster (100.0).",
                $"So going from {threshold} to 100.0 takes at least {MinimumCycles(n.EasyTenths)} {days} for an easy skill, {MinimumCycles(n.StandardTenths)} for a standard one " +
                $"and {MinimumCycles(n.HardTenths)} for a hard one.",
                "Nothing you have gained is ever taken away. A cycle in which a skill is not used simply gives that skill no allowance, and it is not made up later. " +
                $"Allowance you claimed but did not spend carries over, up to {n.StoredCycles} cycles' worth.",
                HeadingMark + "Good to know",
                "The skill must be set to Up. If your skills are at the total cap, a skill set to Down gives up the 0.1 to make room; if none can, the use gives nothing and spends nothing." + bank,
                "[Mastery opens a window showing when your cycle ends and, for each Mastery skill, where it stands, its allowance, what is stored and how far it is from 100. When you log in you are told if a skill has not claimed this cycle."
            ]
        );
    }

    private static Topic SkillBankTopic(Context c, Numbers n)
    {
        var step = Points(n.RestoreStepTenths);
        var paragraphs = new List<string>
        {
            HeadingMark + "How the bank fills",
            $"Your skills can add up to {n.SkillCapPoints} points. Each time a skill gains, a skill you have set to Down (the arrows in your skills window) may give up points to pay for it: " +
            "more often the closer your total is to the cap, and every time at it. Without the bank those points are simply lost.",
            $"With the bank, they are saved instead, whether or not you are at the cap. Each point a Down skill gives up goes into your bank under that skill's name. The bank holds up to {n.BankPoints} points in all, " +
            "and never more for one skill than that skill could hold. Only points a Down skill loses to skill gain are banked.",
            HeadingMark + "Getting points back",
            $"Set the skill to Up and keep training it. Every use of it that counts toward skill gain brings back {step} from the bank instead of a normal gain, until its banked points are used up " +
            "(0.1 if that is all that is left). If you are at the cap again, a skill set to Down gives up the same amount to make room, and that goes into the bank in turn.",
            "Example: Anatomy is Up and Hiding is Down. Anatomy gains 0.1, so Hiding loses 0.1 and the bank keeps it, wherever your total stands. " +
            $"Later you set Hiding to Up: each time you use Hiding, {step} returns to it from the bank.",
            HeadingMark + "When the bank is full",
            "A full bank cannot take new points unless it can push out old ones. Each banked skill is either Locked (the default: its points are safe) or Down " +
            "(its points may be replaced when the bank is full, the largest Down entry first, one point at a time). These two settings belong to the bank entry, not to the skill's arrow. " +
            "With a full bank and nothing set to Down, the points a skill loses are not banked, and you are told so.",
            HeadingMark + "Discarding banked points",
            "If you will never train a skill again, press Discard beside it to delete its banked points and free the room. " +
            $"You are asked to type the word {SkillBankDiscardGump.ConfirmWord} to be sure. The points do not go back to the skill, and the skill stays as it is."
        };

        if (c.FaintMemories)
        {
            paragraphs.Add(HeadingMark + FaintMemoriesPolicy.Name);
            paragraphs.Add(
                FaintMemoriesPolicy.Theme + " " +
                $"Every new character starts with {Points(n.FaintPointsTenths)} points of {FaintMemoriesPolicy.Name}, free, and they unlock {n.FaintHours} hours after the character was created."
            );
            paragraphs.Add(
                $"Once unlocked they come back the way bank points do: train a skill you have set to Up and each use brings back {step} into it, until they are gone. " +
                $"They never take a skill past {Points(n.FaintCeilingTenths)}, where Mastery begins, and a skill below {Points(n.FaintFloorTenths)} is left to ordinary gain. " +
                "They do not use any room in the bank, and cannot be discarded. [SkillBank shows the countdown, then what is left; when they are gone the display goes with them."
            );
        }

        paragraphs.Add(HeadingMark + "Commands");
        paragraphs.Add(
            "[SkillBank opens a window showing how full your bank is and, for each banked skill, its current value, how much is banked and whether it is Locked or Down. " +
            "Press the box beside Locked or Down to change a skill's setting, or Discard to delete its banked points. The window tells you when the bank is nearly full."
        );

        return new Topic("skillbank", "Skill Bank", paragraphs);
    }

    /// <summary>Stock: a player who stays beside a burning fire this long is in a secure camp (Campfire.cs).</summary>
    public const int SecureCampSeconds = 30;

    private static string Seconds(double seconds) => ((int)Math.Round(seconds)).ToString(CultureInfo.InvariantCulture);

    /// <summary>
    /// How camping works on this shard: the kit, lighting, how long a fire burns, feeding it and the secure camp with its Bedroll logout.
    /// Every number comes from the camping rules and the stock fire, never from memory; the paragraphs for the fire rules are left out when
    /// those are off, because the fire is then the stock one.
    /// </summary>
    private static Topic CampingTopic(Context c, CampingRules rules)
    {
        var paragraphs = new List<string>();

        if (c.CampingKit)
        {
            paragraphs.Add(HeadingMark + "Your kit");
            paragraphs.Add($"Every new character starts with a Bedroll and {rules.StarterKindling} Kindling.");
        }

        paragraphs.Add(HeadingMark + "Lighting a fire");

        if (c.CampingFires)
        {
            var floor = Seconds(rules.SkillFloor);
            paragraphs.Add(
                "Double-click Kindling to light a campfire next to you. Anyone can: the chance is " + floor + "% for a Camping skill of " + floor +
                " or less and rises with skill to 100%. A failed try costs nothing, a fire that lights uses one Kindling, and trying trains Camping. " +
                "You cannot light a fire inside a dungeon."
            );

            var low = CampingService.TimingFor(rules, 0.0);
            var high = CampingService.TimingFor(rules, 100.0);
            var stock = CampfireTiming.Stock;

            paragraphs.Add(HeadingMark + "How long it burns");
            paragraphs.Add(
                $"A fire burns for {Seconds(rules.LitBaseSeconds)} seconds plus {rules.LitPerSkillSeconds:0.##} for each point of the lighter's Camping skill: " +
                $"{Seconds(low.Out.TotalSeconds)} seconds at skill 0 and {Seconds(high.Out.TotalSeconds)} at skill 100. The last third burns low. " +
                $"Then it smoulders as embers for another {Seconds(rules.EmberBaseSeconds)} seconds plus {rules.EmberPerSkillSeconds:0.##} per point " +
                $"({Seconds((low.Expire - low.Out).TotalSeconds)} to {Seconds((high.Expire - high.Out).TotalSeconds)}) and goes out. " +
                $"A stock fire lasts {Seconds(stock.Out.TotalSeconds)} seconds and smoulders for {Seconds((stock.Expire - stock.Out).TotalSeconds)}."
            );

            paragraphs.Add(HeadingMark + "Feeding it");
            paragraphs.Add(
                "Use Kindling within one tile of a fire to feed it. Its burn time starts again as if you had lit it (a fire never gets shorter), and embers come back to life. " +
                $"Each feed costs one Kindling, and a fire can be fed again {Seconds(rules.FeedCooldownSeconds)} seconds after it was lit or fed. " +
                "To light a second fire, stand two tiles away."
            );
        }
        else
        {
            paragraphs.Add("Double-click Kindling to light a campfire next to you, using your Camping skill. You cannot light a fire inside a dungeon.");
        }

        paragraphs.Add(HeadingMark + "A secure camp");
        paragraphs.Add(
            $"Stay within {Server.Items.Campfire.SecureRange} tiles of a burning fire for {SecureCampSeconds} seconds and you are in a secure camp. Embers do not count. " +
            "In a secure camp, double-click your Bedroll to unroll it and double-click it again to roll it up, then choose Continue: " +
            "you log out at once and safely. Fires are not saved when the server restarts."
        );

        if (c.CampTravel)
        {
            paragraphs.Add("A secure fire is also where party members can travel to you with [CampTravel; the Camp travel page has the details.");
        }

        return new Topic("camping", "Camping", paragraphs);
    }

    /// <summary>One line per command a player can use, only for the features that are on.</summary>
    public static IReadOnlyList<string> Commands(Context c)
    {
        var lines = new List<string> { "[Welcome - Open this guide." };

        if (c.SafeWorld)
        {
            lines.Add("[Intent - Turn Criminal Intent on or off.");
            lines.Add("[IntentStatus - Open a window showing whether it is on, with a button to switch it.");
        }

        if (c.KnockedOut)
        {
            lines.Add("[Execute - Execute a Knocked Out player you are allowed to.");
        }

        lines.Add("[Mastery - Your Mastery cycle and what each Mastery skill can still gain.");

        if (c.SkillBank)
        {
            lines.Add("[SkillBank - Your banked skill points: whether each is Locked or Down, or discard them" + (c.FaintMemories ? ", and your Faint Memories." : "."));
        }

        if (c.SkillClasses)
        {
            lines.Add("[SkillClasses - How fast each skill trains, and which skills are in which class.");
        }

        if (c.CampTravel)
        {
            lines.Add("[CampTravel - Travel to a campfire lit by a member of your party.");
        }

        if (c.CampTravel || c.TravelWarning)
        {
            lines.Add("[TravelWarning - Open a window to turn the Hot Zone travel warning on or off.");
        }

        return lines;
    }

    private const int CharactersPerLine = 58;
    private const int LineHeight = 18;
    private const int ContentHeight = GumpStyle.Height - 178;

    private static bool IsHeading(string paragraph) => paragraph.StartsWith(HeadingMark, StringComparison.Ordinal);

    /// <summary>
    /// The page body: paragraphs separated by a blank line (a command list by a line break, a heading by a line break from
    /// what it introduces), commands picked out in color and headings in gold.
    /// </summary>
    public static string Body(Topic topic)
    {
        var commands = topic.Key == "commands";
        var body = new System.Text.StringBuilder();

        for (var i = 0; i < topic.Paragraphs.Count; i++)
        {
            var paragraph = topic.Paragraphs[i];

            if (i > 0)
            {
                body.Append(commands || IsHeading(topic.Paragraphs[i - 1]) ? "<BR>" : "<BR><BR>");
            }

            body.Append(
                IsHeading(paragraph)
                    ? $"<BASEFONT COLOR=#FFD060>{paragraph[HeadingMark.Length..]}</BASEFONT>"
                    : Highlight(paragraph, commands)
            );
        }

        return body.ToString();
    }

    /// <summary>How many lines of the page's text box a topic needs, a little on the generous side.</summary>
    public static int EstimateLines(Topic topic)
    {
        var commands = topic.Key == "commands";
        var lines = 0;

        for (var i = 0; i < topic.Paragraphs.Count; i++)
        {
            var paragraph = topic.Paragraphs[i];

            lines += IsHeading(paragraph) ? 1 : (paragraph.Length + CharactersPerLine - 1) / CharactersPerLine;

            if (i > 0 && !commands && !IsHeading(topic.Paragraphs[i - 1]))
            {
                lines++;
            }
        }

        return lines;
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

    /// <summary>Opens the guide, on the topic with this key when it is given and the shard has that topic.</summary>
    public static void Open(PlayerMobile player, string? topicKey = null)
    {
        if (player.NetState is null)
        {
            return;
        }

        var settings = ShardRulesConfiguration.Settings;
        var topics = Topics(Current, settings?.CampTravel ?? new CampTravelRules(), Numbers.Current, settings?.Camping);
        var first = topicKey is null ? -1 : topics.ToList().FindIndex(t => t.Key == topicKey);

        player.SendGump(
            new GuideWindow(
                ShardBranding.Name,
                ShardBranding.Tagline,
                "Type [Welcome to open this guide again.",
                topics,
                Math.Max(0, first)
            )
        );
    }
}
