using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The [Welcome guide makes claims about rules. These tests pin each claim to the code or the configuration it describes,
/// so a rule that changes shows up here instead of in a player's confusion. The wording was audited against
/// PvpIntentService, KnockedOutService, BackpackWardState, TheftProtectionService, MasteryEngine and SkillBankLedger.
/// </summary>
public class WelcomeGuideTests
{
    private static readonly CampTravelRules Rules = new();

    private static WelcomeGuide.Context Context(
        bool theft = true, bool skillBank = true, bool skillClasses = true, bool camp = false, bool warning = false,
        bool safeWorld = true, bool knockedOut = true, bool hotZones = true, bool campingKit = false, bool campingFires = false,
        bool faintMemories = false, bool harvestRepeat = false, bool actionRepeat = false, bool petRestrictions = false,
        bool starterPackage = false, bool starterGold = false
    ) => new(
        theft, skillBank, skillClasses, camp, warning, safeWorld, knockedOut, hotZones, campingKit, campingFires, faintMemories,
        harvestRepeat, actionRepeat, petRestrictions, starterPackage, starterGold
    );

    private static string[] Keys(WelcomeGuide.Context c) => WelcomeGuide.Topics(c, Rules).Select(t => t.Key).ToArray();

    private static string Text(string key, WelcomeGuide.Context? c = null, WelcomeGuide.Numbers? numbers = null) =>
        string.Join(" ", WelcomeGuide.Topics(c ?? Context(camp: true, warning: true), Rules, numbers).Single(t => t.Key == key).Paragraphs);

    // ---- which topics there are

    [Fact]
    public void TheDeployedShardGetsTheCoreTopicsInReadingOrder() =>
        Assert.Equal(
            ["welcome", "firsthour", "locks", "fighting", "hotzones", "ward", "loot", "pets", "dying", "training", "mastery", "skillbank", "crafting", "shops", "commands"],
            Keys(Context())
        );

    [Fact]
    public void CampTravelAddsItsOwnTopicBeforeTheCommands() =>
        Assert.Equal(
            ["welcome", "firsthour", "locks", "fighting", "hotzones", "ward", "loot", "pets", "dying", "training", "mastery", "skillbank", "crafting", "shops", "camp", "commands"],
            Keys(Context(camp: true))
        );

    [Fact]
    public void WithoutTheWardsTheWardTopicsAreLeftOut() =>
        Assert.Equal(
            ["welcome", "firsthour", "locks", "fighting", "hotzones", "pets", "dying", "training", "mastery", "skillbank", "crafting", "shops", "commands"],
            Keys(Context(theft: false))
        );

    [Fact]
    public void WithoutTheSkillBankItsTabAndItsMentionsAreLeftOut()
    {
        var c = Context(skillBank: false);

        Assert.DoesNotContain("skillbank", Keys(c));
        Assert.DoesNotContain("Skill Bank", Text("mastery", c));
    }

    [Fact]
    public void MasteryAlwaysHasItsTabBecauseItHasNoFlag() =>
        Assert.Contains("mastery", Keys(Context(theft: false, skillBank: false, skillClasses: false, safeWorld: false, knockedOut: false, hotZones: false)));

    [Fact]
    public void WithoutPlayerCombatRulesTheFightingTabIsLeftOut()
    {
        Assert.DoesNotContain("fighting", Keys(Context(safeWorld: false, knockedOut: false)));
        Assert.DoesNotContain("hotzones", Keys(Context(hotZones: false)));
    }

    [Fact]
    public void NoChapterHasMoreTopicsThanTheListUnderTheTabsCanHold()
    {
        var everything = Context(
            theft: true, skillBank: true, skillClasses: true, camp: true, warning: true, campingKit: true, campingFires: true,
            faintMemories: true, harvestRepeat: true, actionRepeat: true, petRestrictions: true, starterPackage: true, starterGold: true
        );
        var topics = WelcomeGuide.Topics(everything, Rules);

        Assert.All(WelcomeGuide.Chapters(topics), c => Assert.InRange(c.TopicKeys.Count, 1, WelcomeGuide.MaximumTopicsPerChapter));
    }

    // ---- every page is readable and cannot be mistaken for markup

    [Fact]
    public void EveryTopicHasATitleAndReadableParagraphs()
    {
        foreach (var topic in WelcomeGuide.Topics(Context(camp: true, warning: true), Rules))
        {
            Assert.False(string.IsNullOrWhiteSpace(topic.Title), topic.Key);
            Assert.NotEmpty(topic.Paragraphs);
            Assert.All(topic.Paragraphs, p => Assert.InRange(p.Length, 5, 620));
        }
    }

    [Fact]
    public void NoParagraphCanBeMistakenForMarkup()
    {
        foreach (var topic in WelcomeGuide.Topics(Context(camp: true, warning: true), Rules))
        {
            Assert.All(topic.Paragraphs, p => Assert.DoesNotContain('<', p));
            Assert.All(topic.Paragraphs, p => Assert.DoesNotContain('>', p));
        }
    }

    [Fact]
    public void NoTopicSendsPlayersToAStaffCommandOrUsesTheOldName()
    {
        var all = string.Join(" ", WelcomeGuide.Topics(Context(camp: true, warning: true), Rules).SelectMany(t => t.Paragraphs));

        Assert.DoesNotContain("[TheftStatus", all);
        Assert.DoesNotContain("Britannia Renaissance", all);
        Assert.Contains("UO Rekindled", all);
    }

    // ---- Fighting other players

    [Fact]
    public void TheFightingPageSaysWhoCanAttackWhom()
    {
        var text = Text("fighting");

        Assert.Contains("Outside the Hot Zones, a player can attack you only if you have Criminal Intent on, you are a criminal or a murderer, or you are already fighting them.", text);
        Assert.Contains("You can attack another player only by the same rules.", text);
        Assert.Contains("Guild wars also allow fighting between the guilds involved.", text);
    }

    [Fact]
    public void TheIntentTextDescribesTheToggleItsHueAndItsLimits()
    {
        var text = Text("fighting");

        Assert.Contains("[Intent turns Criminal Intent on or off, and it stays as you leave it.", text);
        Assert.Contains("you appear grey and other players may attack you", text);
        Assert.Contains("Killing a player who has Intent on is not murder.", text);
        Assert.Contains(PvpIntentService.NotACriminalNote, text);
        Assert.Contains("You cannot change it while you are a criminal or a murderer.", text);
        Assert.Contains("[IntentStatus shows whether it is on.", text);
    }

    [Fact]
    public void TheFightingPageTellsAboutTheIntentTagTheGuardCallTheCountdownsAndTheFiveSecondExecute()
    {
        var text = Text("fighting");

        Assert.Contains("An [Intent] tag also shows after your name when someone clicks you.", text);
        Assert.Contains("Calling guards on such a player does nothing: the caller is told that the player has not yet performed a criminal act.", text);
        Assert.Contains("A countdown over you shows everyone nearby when that will be.", text);
        Assert.Contains("or choose Execute from the menu you get by clicking them. It takes 5 seconds with a countdown over the victim, and the executor must stay next to them: walking away cancels it.", text);
        Assert.Contains("[Execute - Execute a Knocked Out player you are allowed to, next to them, in five seconds.", Text("commands"));
    }

    [Fact]
    public void TheKnockedOutTextSaysWhoIsKnockedOutForHowLongAndWhatItDoes()
    {
        var text = Text("fighting");
        var seconds = (int)KnockedOutService.Duration.TotalSeconds;

        Assert.Equal(30, seconds);
        Assert.Contains($"is brought down by another player is Knocked Out for {seconds} seconds instead of dying", text);
        Assert.Contains("A player who is not a criminal or a murderer", text);
        Assert.Contains("you cannot act, be hurt or be healed, and when it ends you wake with half your health", text);
        Assert.Contains("Monsters and other causes still kill normally.", text);
    }

    [Fact]
    public void TheExecuteTextSaysWhoMayExecuteAndWhenTheVictimCanReport()
    {
        var text = Text("fighting");

        Assert.Contains("a criminal or murderer who knocked them out, or who has damaged them recently, may [Execute them", text);
        Assert.Contains("Nobody else can, including a player who is only grey because of Criminal Intent.", text);
        Assert.Contains("An Execute is murder, and the victim can report it, unless the victim had Criminal Intent on or the two were at guild war.", text);
        Assert.DoesNotContain("unless the executed player attacked first", text);
        Assert.DoesNotContain("blue players cannot", text);
    }

    [Fact]
    public void ExecutingABlueWhoAttackedFirstIsStillMurder()
    {
        // Owner ruling 2026-10-06 (K-5 amended): a blue may attack a criminal, a murderer or a player with Intent on, who may
        // fight back and Knock the blue out, but an Execute is murder (ExecutionMurderRule).
        var text = Text("fighting", Context());

        Assert.Contains("That is true even if the victim attacked first: a blue may attack a criminal, a murderer or a player with Criminal Intent on, who may fight back and Knock the blue out, but executing the blue still counts.", text);
        Assert.Contains("Reporting gives the killer a murder count.", text);
        Assert.Contains("Fighting back never costs you the report, and a Hot Zone does not make a killing lawful.", text);
        Assert.DoesNotContain("you attacked them first", text);
    }

    [Fact]
    public void TheMurderTextSaysWhatMakesAPlayerRed()
    {
        var text = Text("fighting");

        Assert.Contains("Five counts make a player a murderer (red)", text);
        Assert.Contains("a guard pays any bounty posted on a murderer for their head", text);
        Assert.Contains("Guards do not take a report from a Thieves' Guild member.", text);
    }

    [Fact]
    public void TheExecuteRuleLeavesOutIntentAndHotZonesWhenTheyAreOff()
    {
        var text = Text("fighting", Context(safeWorld: false, hotZones: false));

        Assert.Contains("An Execute is murder, and the victim can report it, unless the two were at guild war.", text);
        Assert.Contains("a blue may attack a criminal or a murderer, who may fight back", text);
        Assert.DoesNotContain("Criminal Intent on", text);
        Assert.DoesNotContain("Hot Zone", text);
    }

    [Fact]
    public void WithoutKnockedOutTheStockRightToAttackRuleIsTold()
    {
        var text = Text("fighting", Context(knockedOut: false));

        Assert.Contains("If another player kills you and had no right to attack you, you can report them as a murderer, which gives them a murder count.", text);
        Assert.Contains("A player has the right to attack you if you have Criminal Intent on, you are a criminal or a murderer, you attacked them first, or you are at guild war with them.", text);
        Assert.Contains("Fighting back does not cost you the report, and a Hot Zone does not give the right.", text);
        Assert.DoesNotContain("An Execute is murder", text);
    }

    [Fact]
    public void KnockedOutIsExplainedAsTheWayAFightEndsWithoutAMurderCount()
    {
        var text = Text("fighting", Context());

        Assert.Contains("Knocked Out is how a fight ends without a killing.", text);
        Assert.Contains("The winner, even a criminal or a murderer, can simply walk away and takes no murder count, because nobody died.", text);
        Assert.Contains("Killing is a choice.", text);
        Assert.DoesNotContain("Knocked Out is how a fight ends", Text("fighting", Context(knockedOut: false)));
    }

    [Fact]
    public void TheFightingPageLeavesOutRulesThatAreSwitchedOff()
    {
        var noKnockedOut = Text("fighting", Context(knockedOut: false));
        var noSafeWorld = Text("fighting", Context(safeWorld: false));

        Assert.DoesNotContain("Knocked Out", noKnockedOut);
        Assert.DoesNotContain("[Execute", noKnockedOut);
        Assert.Contains("[Intent", noKnockedOut);
        Assert.DoesNotContain("[Intent", noSafeWorld);
        Assert.Contains("Knocked Out", noSafeWorld);
    }

    // ---- Hot Zones

    [Fact]
    public void TheHotZoneTopicSaysWhereTheZonesAreAndWhoCanFightInThem()
    {
        var text = Text("hotzones", Context());

        Assert.Contains("Fire Island", text);
        Assert.Contains("Buccaneer's Den", text);
        Assert.Contains("Hythloth", text);
        Assert.Contains("Players in the same Hot Zone can attack each other freely, with or without Criminal Intent", text);
        Assert.Contains("Wards and Loot Protection do not apply", text);
        Assert.Contains("no extra rewards", text);
        Assert.Contains("Fighting in a Hot Zone is free, but it does not make a killing lawful: if someone executes you there, you can still report them as a murderer unless you had Criminal Intent on or were at guild war with them.", text);
        Assert.Contains("if someone kills you there and had no other right to attack you, you can still report them as a murderer", Text("hotzones", Context(knockedOut: false)));
    }

    [Fact]
    public void TheHotZoneLootTextMatchesWhoMayLootAKnockedOutPlayer()
    {
        var text = Text("hotzones", Context());

        Assert.Contains("anyone may open their pack and take items from it, like looting a corpse", text);
        Assert.Contains("A player who is not already a criminal becomes criminal for doing so", text);
        Assert.Contains("newbied, blessed or bound cannot be taken", text);
        Assert.Contains("what the player is wearing stays on them", text);
        Assert.Contains("Outside Hot Zones only a criminal or murderer who knocked the player out may loot them", text);
        Assert.DoesNotContain("Knocked Out", Text("hotzones", Context(knockedOut: false)));
    }

    [Fact]
    public void TheHotZoneTopicMentionsTheTravelWarningOnlyWhenItIsOn()
    {
        Assert.DoesNotContain("[TravelWarning", Text("hotzones", Context()));
        Assert.Contains("[TravelWarning off", Text("hotzones", Context(warning: true)));
        Assert.Contains("[TravelWarning on", Text("hotzones", Context(camp: true)));
    }

    // ---- Backpack Ward and Loot Protection

    [Fact]
    public void TheWardPageDescribesTheItemWhereItWorksAndWhereItComesFrom()
    {
        var text = Text("ward");

        Assert.Contains("one-use item that watches for thieves", text);
        Assert.Contains("Carry it in your backpack or a bag inside it", text);
        Assert.Contains("does nothing in a bank, a house, on the ground or in a pet's pack", text);
        Assert.Contains("You start with one free Ward, bound to you.", text);
        Assert.Contains("Tinker vendors sell them for 2000 gold each", text);
        Assert.Contains("Tinkers can craft them from 20 iron ingots (Tinkering 45 or more, in the Miscellaneous list)", text);
        Assert.Contains("A Ward you buy or make can be traded until it starts watching a thief.", text);
        Assert.Contains("Tinkers buy an unused one back for 110 gold.", text);
        Assert.DoesNotContain("cannot be lost or traded", text);
    }

    [Fact]
    public void TheWardPageOnlyOffersWhatTheShardActuallySells()
    {
        var offSale = Text("ward", numbers: new WelcomeGuide.Numbers(WardPrice: 0, WardIngots: 0));

        Assert.DoesNotContain("Tinker", offSale);
        Assert.DoesNotContain("More Wards", offSale);
        Assert.Contains("You start with one free Ward", offSale);

        var craftOnly = Text("ward", numbers: new WelcomeGuide.Numbers(WardPrice: 0, WardIngots: 15, WardCraftSkill: 50));

        Assert.Contains("Tinkers can craft them from 15 iron ingots (Tinkering 50 or more", craftOnly);
        Assert.DoesNotContain("vendors sell", craftOnly);
        Assert.DoesNotContain("buy an unused one back", craftOnly);
    }

    [Fact]
    public void TheWardPageSaysWhatACaughtThiefCannotDoAndWhatTheWardDoesNotDo()
    {
        var text = Text("ward");

        Assert.Contains("A Ward does not change a thief's chance to steal from you, and it never undoes a theft: the thief keeps what they took.", text);
        Assert.Contains("A thief is caught when a theft from you succeeds and either you detect it in the usual way or the Ward detects it for you.", text);
        Assert.Contains("A caught thief turns criminal and cannot steal from you again, on any of their characters, until the Ward is used up.", text);
        Assert.Contains("It does not stop thieves it has not caught, and it does nothing inside a Hot Zone.", text);
        Assert.Contains("Double-click a Ward to see what it is, where it stands (Unprimed, Primed or Activated) and how many quiet minutes are left.", text);
    }

    [Fact]
    public void TheWardNumbersAreTheOnesTheCodeUses()
    {
        var text = Text("ward");
        var window = (int)WardState.InactivityWindow.TotalMinutes;
        var first = TheftProtectionService.AdditionalDetectionChance(1) * 100;
        var second = TheftProtectionService.AdditionalDetectionChance(2) * 100;

        Assert.Equal(30, window);
        Assert.Equal(25.0, first, 6);
        Assert.Equal(50.0, second, 6);
        Assert.True(TheftProtectionService.AdditionalDetectionChance(3) >= 1.0);
        Assert.Contains($"{first:0}% for that thief's first such theft, {second:0}% for the second and certain for the third", text);
        Assert.Contains($"until {window} minutes pass with no theft attempt against you", text);
        Assert.Contains($"{window} quiet minutes pass the Ward is used up", text);
    }

    [Fact]
    public void TheWardPageSaysWhenItResetsAndWhenItIsUsedUp()
    {
        var text = Text("ward");

        Assert.Contains("Until a theft attempt has been detected, by you or by the Ward, it only watches, and then it resets and you keep it.", text);
        Assert.Contains("Once one has been detected the Ward is activated: caught thieves stay blocked", text);
        Assert.Contains("A blocked thief's attempts do not restart the timer.", text);
    }

    [Fact]
    public void TheLootProtectionPageMatchesTheTenMinuteRule()
    {
        var text = Text("loot");
        var minutes = (int)TheftProtectionService.LootProtectionDuration.TotalMinutes;

        Assert.Equal(10, minutes);
        Assert.Contains($"For the next {minutes} minutes they cannot take anything from any monster corpse you have loot rights to.", text);
        Assert.Contains("they keep that first item and become criminal as usual", text);
        Assert.Contains("outside the Hot Zones", text);
        Assert.Contains("It does not protect your backpack, player corpses, pets' packs, items on the ground or monster corpses once their loot rights have run out", text);
    }

    // ---- Mastery

    [Fact]
    public void TheMasteryPageSaysWhyItExistsBeforeHowItWorks()
    {
        var topic = WelcomeGuide.Topics(Context(), Rules).Single(t => t.Key == "mastery");

        Assert.Equal("# Why Mastery exists", topic.Paragraphs[0]);
        Assert.Contains("grind", topic.Paragraphs[1]);
        Assert.Contains("rewards you for playing", topic.Paragraphs[1]);
        Assert.DoesNotContain("macro", string.Join(" ", topic.Paragraphs));
        Assert.Contains("# How it works", topic.Paragraphs);
    }

    [Fact]
    public void TheMasteryPageQuotesTheShippedNumbers()
    {
        var text = Text("mastery", Context());

        Assert.Contains("A day's allowance takes about 20 successful uses for an easy skill, 10 for a standard one and 6 for a hard one.", text);
        Assert.Contains("Below 90.0 a skill gains by chance, as in Ultima Online. From 90.0 it no longer does.", text);
        Assert.Contains("24-hour cycle", text);
        Assert.Contains("2.0 for easy skills, 1.0 for standard ones and 0.6 for hard ones", text);
        Assert.Contains("at least 5 days for an easy skill, 10 for a standard one and 17 for a hard one", text);
        Assert.Contains("up to 3 cycles' worth", text);
        Assert.Contains("[Mastery opens a window", text);
        Assert.DoesNotContain("MasteryStatus", text);
        Assert.Contains("[SkillClasses", text);
        Assert.Contains("Points held in your Skill Bank come back before Mastery applies.", text);
        Assert.Contains("the use gives nothing and spends nothing", text);
    }

    [Fact]
    public void TheMasteryPageFollowsTheConfiguredNumbers()
    {
        var numbers = new WelcomeGuide.Numbers(EasyTenths: 40, StandardTenths: 20, HardTenths: 12, CycleHours: 12, StoredCycles: 2);
        var text = Text("mastery", Context(), numbers);

        Assert.Contains("12-hour cycle", text);
        Assert.Contains("4.0 for easy skills, 2.0 for standard ones and 1.2 for hard ones", text);
        Assert.Contains("at least 3 cycles for an easy skill, 5 for a standard one and 9 for a hard one", text);
        Assert.Contains("up to 2 cycles' worth", text);
        Assert.Contains("about 40 successful uses for an easy skill, 20 for a standard one and 12 for a hard one", text);
    }

    [Theory]
    [InlineData(20, 5)]
    [InlineData(10, 10)]
    [InlineData(6, 17)]
    [InlineData(4, 25)]
    public void TheFewestDaysFromNinetyToAHundredFollowTheAllowance(int tenths, int days) =>
        Assert.Equal(days, WelcomeGuide.MinimumCycles(tenths));

    // ---- Skill Bank

    [Fact]
    public void TheSkillBankPageExplainsFillingRestoringFullBankAndCommands()
    {
        var topic = WelcomeGuide.Topics(Context(), Rules).Single(t => t.Key == "skillbank");
        var text = string.Join(" ", topic.Paragraphs);

        Assert.Contains("# How the bank fills", topic.Paragraphs);
        Assert.Contains("# Getting points back", topic.Paragraphs);
        Assert.Contains("# When the bank is full", topic.Paragraphs);
        Assert.Contains("# Commands", topic.Paragraphs);
        Assert.Contains("up to 700 points", text);
        Assert.Contains("more often the closer your total is to the cap, and every time at it", text);
        Assert.Contains("whether or not you are at the cap", text);
        Assert.Contains("holds up to 300 points", text);
        Assert.Contains("Only points a Down skill loses to skill gain are banked.", text);
        Assert.Contains("brings back 0.2 from the bank instead of a normal gain", text);
        Assert.Contains("(0.1 if that is all that is left)", text);
        Assert.DoesNotContain("each time it would gain", text);
        Assert.Contains("These two settings belong to the bank entry, not to the skill's arrow.", text);
        Assert.Contains("the points a skill loses are not banked, and you are told so", text);
        Assert.Contains("[SkillBank opens a window", text);
        Assert.Contains("Press the box beside Locked or Down to change a skill's setting, or Discard to delete its banked points.", text);
        Assert.DoesNotContain("[SkillBank lock", text);
    }

    [Fact]
    public void TheSkillBankPageTellsPlayersTheyCanDiscardAndWhatToTypeToConfirm()
    {
        var text = Text("skillbank", Context());

        Assert.Contains("# Discarding banked points", WelcomeGuide.Topics(Context(), Rules).Single(t => t.Key == "skillbank").Paragraphs);
        Assert.Contains("press Discard beside it to delete its banked points and free the room", text);
        Assert.Contains("type the word discard to be sure", text);
        Assert.Contains("The points do not go back to the skill, and the skill stays as it is.", text);
        Assert.Contains("or Discard to delete its banked points", text);
    }

    [Fact]
    public void FaintMemoriesGetsItsOwnParagraphsOnlyWhileItIsSwitchedOn()
    {
        var off = Text("skillbank", Context());
        var on = Text("skillbank", Context(faintMemories: true));
        var paragraphs = WelcomeGuide.Topics(Context(faintMemories: true), Rules).Single(t => t.Key == "skillbank").Paragraphs;

        Assert.DoesNotContain("Faint Memories", off);
        Assert.Contains("# Faint Memories", paragraphs);
        Assert.Contains("Faint memories of a past in Britannia linger, and skills of the past come back to you.", on);
        Assert.Contains("Every new character starts with 5.0 points of Faint Memories, free, and they unlock 24 hours after the character was created.", on);
        Assert.Contains("each use brings back 0.2 into it", on);
        Assert.Contains("They never take a skill past 90.0, where Mastery begins, and a skill below 10.0 is left to ordinary gain.", on);
        Assert.Contains("They do not use any room in the bank, and cannot be discarded.", on);
        Assert.Contains("when they are gone the display goes with them", on);
    }

    [Fact]
    public void TheFaintMemoriesParagraphsFollowTheConfiguredNumbers()
    {
        var text = Text(
            "skillbank", Context(faintMemories: true),
            new WelcomeGuide.Numbers(RestoreStepTenths: 3, FaintPointsTenths: 80, FaintHours: 12, FaintFloorTenths: 200, FaintCeilingTenths: 800)
        );

        Assert.Contains("starts with 8.0 points", text);
        Assert.Contains("unlock 12 hours after", text);
        Assert.Contains("each use brings back 0.3 into it", text);
        Assert.Contains("past 80.0", text);
        Assert.Contains("below 20.0", text);
    }

    [Fact]
    public void TheCommandsListMentionsDiscardingAndFaintMemoriesOnlyWhenTheyExist()
    {
        var lines = WelcomeGuide.Topics(Context(), Rules).Single(t => t.Key == "commands").Paragraphs;
        var withFaint = WelcomeGuide.Topics(Context(faintMemories: true), Rules).Single(t => t.Key == "commands").Paragraphs;

        Assert.Contains("[SkillBank - Your banked skill points: whether each is Locked or Down, or discard them.", lines);
        Assert.Contains("[SkillBank - Your banked skill points: whether each is Locked or Down, or discard them, and your Faint Memories.", withFaint);
    }

    [Fact]
    public void TheSkillBankPageFollowsTheConfiguredNumbers()
    {
        var text = Text("skillbank", Context(), new WelcomeGuide.Numbers(SkillCapPoints: 600, BankPoints: 150));

        Assert.Contains("up to 600 points", text);
        Assert.Contains("holds up to 150 points", text);
    }

    [Fact]
    public void TheFirstPageDoesNotRepeatTheTaglineTheHeaderShows()
    {
        var text = Text("welcome");

        Assert.Contains("Welcome to UO Rekindled.", text);
        Assert.DoesNotContain(ShardBranding.Tagline, text);
        Assert.DoesNotContain("without the griefing", text);
    }

    [Fact]
    public void TheWardPageSaysDetectedNeverNoticed()
    {
        var text = Text("ward");

        Assert.DoesNotContain("notice", text, StringComparison.OrdinalIgnoreCase);
        Assert.Contains("the Ward gets an extra chance to detect it", text);
        Assert.Contains("succeeds undetected", text);
    }

    [Fact]
    public void AMissedMasteryCycleIsNotPresentedAsLostProgress()
    {
        var text = Text("mastery");

        Assert.Contains("Nothing you have gained is ever taken away.", text);
        Assert.Contains("A cycle in which a skill is not used simply gives that skill no allowance, and it is not made up later.", text);
        Assert.DoesNotContain("is lost", text);
    }

    // ---- camping

    [Fact]
    public void CampingGetsAPageWhenEitherCampingSwitchIsOnBeforeCampTravel()
    {
        Assert.DoesNotContain("camping", Keys(Context()));
        Assert.Contains("camping", Keys(Context(campingFires: true)));
        Assert.Contains("camping", Keys(Context(campingKit: true)));
        Assert.DoesNotContain("camp", Keys(Context(campingKit: true)));

        var both = Keys(Context(campingKit: true, campingFires: true, camp: true));
        Assert.True(Array.IndexOf(both, "camping") < Array.IndexOf(both, "camp"));
        Assert.True(Array.IndexOf(both, "camp") < Array.IndexOf(both, "commands"));
    }

    [Fact]
    public void TheCampingPageQuotesTheShippedNumbersFromTheCode()
    {
        var text = Text("camping", Context(campingKit: true, campingFires: true));
        var rules = new CampingRules();
        var low = CampingService.TimingFor(rules, 0.0);
        var high = CampingService.TimingFor(rules, 100.0);

        Assert.Contains("Every new character starts with a Bedroll and 5 Kindling.", text);
        Assert.Equal(5, rules.StarterKindling);
        Assert.Contains("the chance is 50% for a Camping skill of 50 or less and rises with skill to 100%", text);
        Assert.Contains("A failed try costs nothing, a fire that lights uses one Kindling, and trying trains Camping.", text);
        Assert.Contains("You cannot light a fire inside a dungeon.", text);
        Assert.Contains($"A fire burns for 100 seconds plus 2 for each point of the lighter's Camping skill: {low.Out.TotalSeconds:0} seconds at skill 0 and {high.Out.TotalSeconds:0} at skill 100.", text);
        Assert.Equal(100, (int)low.Out.TotalSeconds);
        Assert.Equal(300, (int)high.Out.TotalSeconds);
        Assert.Contains("The last third burns low.", text);
        Assert.Contains($"another 60 seconds plus 1.2 per point ({(low.Expire - low.Out).TotalSeconds:0} to {(high.Expire - high.Out).TotalSeconds:0})", text);
        Assert.Contains("A stock fire lasts 90 seconds and smoulders for 10.", text);
        Assert.Contains("Use Kindling within one tile of a fire to feed it.", text);
        Assert.Contains("(a fire never gets shorter)", text);
        Assert.Contains("a fire can be fed again 5 seconds after it was lit or fed", text);
        Assert.Contains("To light a second fire, stand two tiles away.", text);
        Assert.Contains("Stay within 7 tiles of a burning fire for 30 seconds and you are in a secure camp. Embers do not count.", text);
        Assert.Contains("double-click your Bedroll to unroll it and double-click it again to roll it up, then choose Continue", text);
        Assert.Contains("you log out at once and safely", text);
        Assert.Contains("Fires are not saved when the server restarts.", text);
    }

    [Fact]
    public void TheCampingPageFollowsTheConfiguredNumbers()
    {
        var rules = new CampingRules { SkillFloor = 40, LitBaseSeconds = 50, LitPerSkillSeconds = 1.5, StarterKindling = 3, FeedCooldownSeconds = 8 };
        var text = string.Join(" ", WelcomeGuide.Topics(Context(campingKit: true, campingFires: true), Rules, null, rules).Single(t => t.Key == "camping").Paragraphs);

        Assert.Contains("a Bedroll and 3 Kindling", text);
        Assert.Contains("the chance is 40% for a Camping skill of 40 or less", text);
        Assert.Contains("A fire burns for 50 seconds plus 1.5 for each point", text);
        Assert.Contains("50 seconds at skill 0 and 200 at skill 100", text);
        Assert.Contains("fed again 8 seconds after", text);
    }

    [Fact]
    public void TheCampingPageLeavesOutWhatIsSwitchedOff()
    {
        var noKit = Text("camping", Context(campingFires: true));
        var noFires = Text("camping", Context(campingKit: true));

        Assert.DoesNotContain("starts with a Bedroll", noKit);
        Assert.Contains("A fire burns for", noKit);

        Assert.Contains("starts with a Bedroll", noFires);
        Assert.DoesNotContain("A fire burns for", noFires);
        Assert.DoesNotContain("Feeding it", noFires);
        Assert.Contains("using your Camping skill", noFires);
        Assert.Contains("secure camp", noFires);
    }

    [Fact]
    public void TheCampingPageSendsPartiesToCampTravelOnlyWhenItIsOn()
    {
        Assert.DoesNotContain("[CampTravel", Text("camping", Context(campingFires: true)));
        Assert.Contains("[CampTravel", Text("camping", Context(campingFires: true, camp: true)));
    }

    [Fact]
    public void TheGuideCanOpenOnAnyTopicAndNavigateTheRestInOrder()
    {
        // The window opens on page 1, so the topic asked for takes it and the others follow in a ring.
        Assert.Equal(1, GuideWindow.PageOf(3, 3, 8));
        Assert.Equal(2, GuideWindow.PageOf(4, 3, 8));
        Assert.Equal(8, GuideWindow.PageOf(2, 3, 8));
        Assert.Equal(1, GuideWindow.PageOf(0, 0, 8));
        Assert.Equal(8, GuideWindow.PageOf(7, 0, 8));
    }

    // ---- the command list

    [Fact]
    public void TheCommandListHasOnlyCommandsThatAreOn()
    {
        var core = string.Join("\n", WelcomeGuide.Commands(Context(skillBank: false, skillClasses: false)));

        Assert.Contains("[Welcome", core);
        Assert.Contains("[Intent", core);
        Assert.Contains("[Execute", core);
        Assert.DoesNotContain("[SkillBank", core);
        Assert.DoesNotContain("[SkillClasses", core);
        Assert.DoesNotContain("[CampTravel", core);
        Assert.DoesNotContain("[TravelWarning", core);

        var all = string.Join("\n", WelcomeGuide.Commands(Context(camp: true)));

        Assert.Contains("[SkillBank", all);
        Assert.Contains("[SkillClasses", all);
        Assert.Contains("[Mastery - ", all);
        Assert.DoesNotContain("MasteryStatus", all);
        Assert.Contains("[CampTravel", all);
        Assert.Contains("[TravelWarning", all);

        var noCombat = string.Join("\n", WelcomeGuide.Commands(Context(safeWorld: false, knockedOut: false)));

        Assert.DoesNotContain("[Intent", noCombat);
        Assert.DoesNotContain("[Execute", noCombat);
    }

    // ---- rendering

    [Fact]
    public void ACommandIsPickedOutInColorAndItsMeaningFollows()
    {
        var line = WelcomeGuide.Highlight("[Intent - Turn Criminal Intent on or off.", true);

        Assert.StartsWith("<BASEFONT COLOR=#8FD3FF>[Intent</BASEFONT> - ", line);
        Assert.Contains("Turn Criminal Intent on or off.", line);
    }

    [Fact]
    public void CommandsInsideAParagraphAreColoredToo()
    {
        var text = WelcomeGuide.Highlight("[Intent turns on Criminal Intent. [IntentStatus shows your state.", false);

        Assert.Contains("<BASEFONT COLOR=#8FD3FF>[Intent</BASEFONT> turns on", text);
        Assert.Contains("<BASEFONT COLOR=#8FD3FF>[IntentStatus</BASEFONT> shows", text);
    }

    [Fact]
    public void ParagraphsAreSeparatedByABlankLine()
    {
        var body = WelcomeGuide.Body(new WelcomeGuide.Topic("x", "X", ["First paragraph here.", "Second paragraph here."]));

        Assert.Contains("here.<BR><BR>Second", body);
    }

    [Fact]
    public void ACommandListIsOneLinePerCommandAndTopicsAreSpacedOut()
    {
        var commands = WelcomeGuide.Body(new WelcomeGuide.Topic("commands", "Commands", ["[A - one.", "[B - two."]));
        var topic = WelcomeGuide.Body(new WelcomeGuide.Topic("ward", "Ward", ["First paragraph here.", "Second paragraph here."]));

        Assert.DoesNotContain("<BR><BR>", commands);
        Assert.Contains("<BR>", commands);
        Assert.Contains("<BR><BR>", topic);
    }

    [Fact]
    public void AHeadingIsGoldAndSitsCloseToWhatItIntroduces()
    {
        var body = WelcomeGuide.Body(new WelcomeGuide.Topic("x", "X", ["# Why", "First paragraph here.", "Second paragraph here."]));

        Assert.StartsWith("<BASEFONT COLOR=#FFD060>Why</BASEFONT><BR>First", body);
        Assert.Contains("here.<BR><BR>Second", body);
    }

    [Fact]
    public void AHeadingCostsOneLineAndNoBlankLineAfterIt()
    {
        var topic = new WelcomeGuide.Topic("x", "X", ["# Why", new string('a', 58), "# Next", new string('a', 58)]);

        // heading (1) + paragraph (1) + blank (1) + heading (1) + paragraph (1)
        Assert.Equal(5, WelcomeGuide.EstimateLines(topic));
    }

    [Fact]
    public void ShortPagesHaveNoScrollbarAndLongOnesDo()
    {
        var topics = WelcomeGuide.Topics(Context(camp: true, warning: true), Rules).ToDictionary(t => t.Key);

        Assert.False(WelcomeGuide.NeedsScroll(topics["welcome"]));
        Assert.False(WelcomeGuide.NeedsScroll(topics["commands"]));
        Assert.True(WelcomeGuide.NeedsScroll(topics["fighting"]));
        Assert.True(WelcomeGuide.NeedsScroll(topics["ward"]));
        Assert.True(WelcomeGuide.NeedsScroll(topics["mastery"]));
        Assert.True(WelcomeGuide.NeedsScroll(topics["skillbank"]));
        Assert.True(WelcomeGuide.NeedsScroll(new WelcomeGuide.Topic("x", "X", [new string('a', 2000)])));
    }

    [Fact]
    public void TheLineEstimateCountsWrappedLinesAndTheBlankLinesBetweenParagraphs()
    {
        var two = new WelcomeGuide.Topic("x", "X", [new string('a', 58), new string('a', 59)]);

        Assert.Equal(1 + 2 + 1, WelcomeGuide.EstimateLines(two));
        Assert.Equal(1 + 2, WelcomeGuide.EstimateLines(new WelcomeGuide.Topic("commands", "C", [new string('a', 58), new string('a', 59)])));
    }

    [Fact]
    public void TheCreationPromptPointsBackToTheGuide() =>
        Assert.Contains("[Welcome", StarterOnboarding.CreationPrompt);
}
