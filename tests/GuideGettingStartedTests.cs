using Xunit;

namespace BritanniaRenaissance.Content.Tests;

/// <summary>
/// The guide's getting-started pages and its chapter tabs (owner sign-off 2026-10-07). Each page says what the code or the owner's ruling
/// behind it says; these tests pin the wording and the gating so a rule that changes shows up here. The audit that tied every sentence
/// to its source is docs/Guide-Getting-Started-Pages.md.
/// </summary>
public class GuideGettingStartedTests
{
    private static readonly CampTravelRules Rules = new();

    private static WelcomeGuide.Context Everything() => new(
        Theft: true, SkillBank: true, SkillClasses: true, CampTravel: true, TravelWarning: true, SafeWorld: true, KnockedOut: true,
        HotZones: true, CampingKit: true, CampingFires: true, FaintMemories: true, HarvestRepeat: true, ActionRepeat: true,
        PetRestrictions: true, StarterPackage: true, StarterGold: true
    );

    private static WelcomeGuide.Context Bare() => new(false, false, false, false, false, false, false, false);

    private static IReadOnlyList<WelcomeGuide.Topic> All(WelcomeGuide.Context? c = null) =>
        WelcomeGuide.Topics(c ?? Everything(), Rules, camping: new CampingRules());

    private static string Text(string key, WelcomeGuide.Context? c = null, WelcomeGuide.Numbers? n = null) =>
        string.Join(" ", WelcomeGuide.Topics(c ?? Everything(), Rules, n, new CampingRules()).Single(t => t.Key == key).Paragraphs);

    // ---- chapters

    [Fact]
    public void EveryTopicTheGuideCanShowBelongsToExactlyOneChapter()
    {
        var keys = All().Select(t => t.Key).ToArray();
        var chaptered = WelcomeGuide.Chapters(All()).SelectMany(c => c.TopicKeys).ToArray();

        Assert.Equal(keys.OrderBy(k => k), chaptered.OrderBy(k => k));
        Assert.Equal(chaptered.Length, chaptered.Distinct().Count());
    }

    [Fact]
    public void TheTopicsComeInChapterOrderSoNextTopicWalksTheTabsInOrder()
    {
        var keys = All().Select(t => t.Key).ToArray();

        Assert.Equal(WelcomeGuide.Chapters(All()).SelectMany(c => c.TopicKeys), keys);
    }

    [Fact]
    public void TheChaptersAreStartRulesSkillsWorkTravelCommandsAndALonelyChapterIsLeftOut()
    {
        Assert.Equal(["Start here", "Rules", "Skills", "Work", "Travel", "Commands"], WelcomeGuide.Chapters(All()).Select(c => c.Title));

        var noCamp = Everything() with { CampingKit = false, CampingFires = false, CampTravel = false };

        Assert.DoesNotContain("Travel", WelcomeGuide.Chapters(All(noCamp)).Select(c => c.Title));
    }

    [Fact]
    public void NoChapterIsLongerThanTheListUnderTheTabs() =>
        Assert.All(WelcomeGuide.Chapters(All()), c => Assert.InRange(c.TopicKeys.Count, 1, WelcomeGuide.MaximumTopicsPerChapter));

    [Fact]
    public void TheSixTabsFitAcrossTheWindow()
    {
        var width = 24 + GuideWindow.TabRowWidth(WelcomeGuide.Chapters(All()).Count);

        Assert.True(width <= GumpStyle.Width - 24, $"tabs need {width} pixels");
    }

    [Fact]
    public void EveryChapterTitleFitsItsStoneTab() =>
        Assert.All(WelcomeGuide.Chapters(All(Everything())), c => Assert.True(GuideWindow.TabTitleFits(c.Title), c.Title));

    [Fact]
    public void TheTextBoxUnderTheTabsIsShorterThanTheOneWithoutThem() =>
        Assert.True(GuideWindow.TabbedContentHeight < GumpStyle.Height - 178);

    // ---- which pages appear

    [Fact]
    public void TheCorePagesAreAlwaysThereAndTheOptionalOnesFollowTheirSwitches()
    {
        var bare = All(Bare()).Select(t => t.Key).ToArray();

        foreach (var key in new[] { "welcome", "firsthour", "locks", "pets", "dying", "training", "mastery", "crafting", "shops", "commands" })
        {
            Assert.Contains(key, bare);
        }

        Assert.DoesNotContain("gather", bare);
        Assert.DoesNotContain("camping", bare);
        Assert.Contains("gather", All(Bare() with { HarvestRepeat = true }).Select(t => t.Key));
        Assert.Contains("gather", All(Bare() with { ActionRepeat = true }).Select(t => t.Key));
    }

    // ---- Your first hour

    [Fact]
    public void YourFirstHourOnlyDescribesWhatTheShardGives()
    {
        var all = Text("firsthour");
        var bare = Text("firsthour", Bare());

        Assert.Contains("You begin with a Bag, a pair of scissors and the tools, weapon, armor and supplies your skills call for.", all);
        Assert.Contains("Newbied items stay with you when you die, even inside bags (a murderer loses them), and shopkeepers will not buy them. The Bag itself is an ordinary bag.", all);
        Assert.Contains("Your first character on an account starts with 500 gold; later characters start with none.", all);
        Assert.Contains("A Backpack Ward watches for thieves: one it catches turns criminal and cannot steal from you again until the Ward runs out.", all);
        Assert.Contains("A Bedroll and Kindling let you make a camp", all);
        Assert.Contains("Faint Memories: 5.0 free points unlock 24 hours after you create your character", all);
        Assert.Contains("between 10.0 and 80.0", all);
        Assert.Contains("Once a skill reaches 80.0, use it a little every day: Mastery guarantees it gains, and it is the sure way to Grandmaster (see the Mastery page).", all);
        Assert.Contains("Once a skill reaches 80.0", bare);
        Assert.Contains("You start with the three skills of your template (an Advanced character picks its own)", all);
        Assert.DoesNotContain("protects you from thieves", all);
        Assert.Contains("[SkillClasses shows how fast each skill trains.", all);

        Assert.DoesNotContain("You begin with", bare);
        Assert.DoesNotContain("500 gold", bare);
        Assert.DoesNotContain("Ward", bare);
        Assert.DoesNotContain("Bedroll", bare);
        Assert.DoesNotContain("Faint Memories", bare);
        Assert.DoesNotContain("[SkillClasses", bare);
    }

    [Fact]
    public void YourFirstHourSaysWhoCanAttackYouAndPointsToTheTabs()
    {
        var text = Text("firsthour");

        Assert.Contains("Outside the Hot Zones, other players cannot attack you unless you opt in with [Intent, break the law or are already fighting them.", text);
        Assert.Contains("Monsters stay dangerous everywhere.", text);
        Assert.Contains("Use the tabs above to read how things work, and type [Welcome any time to open this guide again.", text);
    }

    [Fact]
    public void TheWelcomePagePointsANewcomerOnToTheirFirstHourAndTheTabs()
    {
        var text = Text("welcome");

        Assert.Equal(["welcome", "firsthour"], All().Take(2).Select(t => t.Key));
        Assert.Contains("New here? Start with Your first hour.", text);
        Assert.Contains("or another tab above", text);
        Assert.Contains("The Rules tab has the details.", text);
        Assert.DoesNotContain("The next page has the details", text);
    }

    // ---- Skill locks 101

    [Fact]
    public void SkillLocksExplainsTheThreeSettingsTheCapAndWhatToCheck()
    {
        var text = Text("locks");

        Assert.Contains("Up: the skill can gain. Down: the skill can give points up.", text);
        Assert.Contains("Locked: the skill neither gains nor loses.", text);
        Assert.Contains("Your skills together can hold 700 points.", text);
        Assert.Contains("At the cap a skill can gain only when a skill set to Down has points to give up", text);
        Assert.Contains("no skill set to Down has points left", text);
        Assert.Contains("It is set to Down or Locked: set it to Up.", text);
        Assert.Contains("Uses that cannot fail, or are far too hard, do not train a skill.", text);
        Assert.Contains("it cycles Up, Down and Locked, and Locked shows a padlock", text);
        Assert.DoesNotContain("It has reached 80.0", text);
        Assert.DoesNotContain("Mastery takes over", text);
        Assert.Contains("It has reached its cap.", text);
    }

    [Fact]
    public void SkillLocksMentionsTheBankAndFaintMemoriesOnlyWhenTheyExist()
    {
        var all = Text("locks");
        var bare = Text("locks", Bare());

        Assert.Contains("Skill Bank points come back into a skill set to Up", all);
        Assert.Contains("Faint Memories go into a skill set to Up", all);
        Assert.Contains("are saved in your Skill Bank, up to its 300-point limit", all);
        Assert.Contains("Points taken for a trainer's lesson are not saved.", all);
        Assert.DoesNotContain("Skill Bank", bare);
        Assert.DoesNotContain("Faint Memories", bare);
        Assert.Contains("Mastery's daily allowance is spent only by a skill set to Up", bare);
    }

    [Fact]
    public void SkillLocksFollowsTheConfiguredCap() =>
        Assert.Contains("600-point cap", Text("locks", null, new WelcomeGuide.Numbers(SkillCapPoints: 600)));

    // ---- Training

    [Fact]
    public void TrainingStatesTheStockRuleExactly()
    {
        var text = Text("training");

        Assert.Contains("An NPC teaches a skill only if it has at least 60.0 in it", text);
        Assert.Contains("raises yours to a third of its own, never past your own skill cap: about 20.0 to 33.0 for most trainers", text);
        Assert.Contains("You pay 1 gold for each 0.1 point you gain.", text);
        Assert.Contains("click the NPC once and pick the skill from its menu", text);
        Assert.Contains("drop exactly that much gold on the NPC, and only after it has named the price", text);
        Assert.Contains("gold dropped on an NPC you have not asked is kept as a gift", text);
        Assert.Contains("Paying less teaches you less; paying more is lost.", text);
        Assert.Contains("a town NPC lists the skills it can teach you, but only the menu gives a price", text);
        Assert.Contains("The skill must be set to Up", text);
        Assert.Contains("At the cap a lesson takes its points from skills you have set to Down, and those points are lost.", text);
        Assert.DoesNotContain("right-click", text);
        Assert.DoesNotContain("Fenwick", text);
        Assert.Equal(600, WelcomeGuide.StockTraining.MinimumTrainerSkillTenths);
        Assert.Equal(420, WelcomeGuide.StockTraining.MaximumLessonTenths);
    }

    [Fact]
    public void TrainingNamesTheSkillsByTheirGameNamesAndTheTrainersThatAlwaysTeachThem()
    {
        var text = Text("training");

        // Names as the skills window shows them (Distribution/Data/skills.json), not code identifiers.
        foreach (var name in new[]
                 {
                     "Blacksmithy", "Mace Fighting", "Swordsmanship", "Parrying", "Bowcraft/Fletching", "Detecting Hidden", "Forensic Evaluation",
                     "Evaluating Intelligence", "Resisting Spells", "Taste Identification", "Remove Trap", "Spirit Speak", "Inscription"
                 })
        {
            Assert.Contains(name, text);
        }

        Assert.Contains("Blacksmith: Blacksmithy, Fencing, Mace Fighting, Swordsmanship, Tactics, Parrying.", text);
        Assert.Contains("Healer: Healing, Forensic Evaluation, Spirit Speak, Swordsmanship.", text);
        Assert.Contains("Tinker: Tinkering, Lockpicking, and Remove Trap (which needs 50.0 in Lockpicking and in Detecting Hidden).", text);
        Assert.DoesNotContain("Detect Hidden", text);
        Assert.DoesNotContain("Mace Fighting,Macing", text);
    }

    [Fact]
    public void TrainingMentionsFaintMemoriesAndTheSkillClassesWindowOnlyWhenOn()
    {
        Assert.Contains("[SkillClasses lists them", Text("training"));
        Assert.DoesNotContain("[SkillClasses", Text("training", Bare()));
        Assert.Contains("Faint Memories points come back through ordinary skill use, not through a trainer's lesson", Text("training"));
        Assert.DoesNotContain("Faint Memories", Text("training", Bare()));
    }

    // ---- Money and shops

    [Fact]
    public void MoneyAndShopsStatesTheBankerAndVendorRules()
    {
        var text = Text("shops");

        Assert.Contains("Say bank near a banker to open your bank box.", text);
        Assert.Contains("withdraw 500 (take gold out, at most 5,000 at a time)", text);
        Assert.Contains("check 10000 (turns 5,000 to 1,000,000 gold from your bank box into a check that stays in the box)", text);
        Assert.Contains("There is no deposit command: drag gold into your bank box.", text);
        Assert.Contains("A banker will not do business with a criminal.", text);
        Assert.Contains("Stand within four tiles of a shopkeeper and say vendor buy or vendor sell, or click the shopkeeper once for a menu with Buy and Sell.", text);
        Assert.DoesNotContain("right-click", text);
        Assert.Contains("If your pack is short and the purchase costs 2,000 gold or more, it is paid from your bank instead.", text);
        Assert.Contains("Shopkeepers do not buy newbied items.", text);
        Assert.Contains("Stabling costs 30 gold for each pet; claiming is free. Unload a pack animal first.", text);
    }

    // ---- Crafting

    [Fact]
    public void CraftingExplainsTheTargetThenMenuFlowAndMakeLast()
    {
        var text = Text("crafting");

        Assert.Contains("Double-click a crafting tool, then target the material you want to work", text);
        Assert.Contains("a Blacksmith sees Repair, Smelt and lists of things to build, a Tinker sees categories", text);
        Assert.Contains("A menu lists only what your skill and your materials allow", text);
        Assert.Contains("double-click the tool and target the tool itself instead of the material", text);
        Assert.Contains("Target this tool to make last item", text);
        Assert.Contains("Smelt and Repair are in the Blacksmith menu. Blacksmithing needs an anvil and a forge within two tiles.", text);
    }

    [Fact]
    public void CraftingMentionsTheWardRecipeAndRepeatsOnlyWhenTheyExist()
    {
        Assert.Contains("A Tinker can make a Backpack Ward from 20 iron ingots once Tinkering is a little above 45", Text("crafting"));
        Assert.DoesNotContain("Backpack Ward", Text("crafting", Bare()));
        Assert.DoesNotContain("Backpack Ward", Text("crafting", Everything(), new WelcomeGuide.Numbers(WardIngots: 0)));
        Assert.Contains("Gathering and repeats page", Text("crafting"));
        Assert.DoesNotContain("Gathering and repeats", Text("crafting", Bare()));
    }

    // ---- Gathering and repeats

    [Fact]
    public void GatheringAndRepeatsMatchTheReadmeLinesForEachSwitch()
    {
        var both = Text("gather");
        var harvestOnly = Text("gather", Bare() with { HarvestRepeat = true });
        var actionOnly = Text("gather", Bare() with { ActionRepeat = true });

        Assert.Contains("Mining, lumberjacking and fishing repeat on the tile you chose until its resource runs out, at the usual pace.", both);
        Assert.Contains("Walking, casting, using another skill, entering war mode, fighting or being hurt, or opening another gathering target ends it.", both);
        Assert.Contains("Taming tries the same creature again after each plain failure until it accepts you or something stops it", both);
        Assert.Contains("and so does opening any target cursor", both);
        Assert.Contains("a loom takes your whole stack at once", both);
        Assert.Contains("Each attempt is the ordinary one", both);

        Assert.DoesNotContain("Taming tries", harvestOnly);
        Assert.DoesNotContain("Mining, lumberjacking", actionOnly);
    }

    // ---- Pets

    [Fact]
    public void PetsStatesTheShardRestrictionsOnlyWhenTheyAreOn()
    {
        var on = Text("pets");
        var off = Text("pets", Bare());

        Assert.Contains("Tamed pets never attack players.", on);
        Assert.DoesNotContain("They only fight monsters", on);
        Assert.Contains("A tamed pet cannot enter or stay in a dungeon", on);
        Assert.Contains("to bring it out", on);
        Assert.Contains("You may ride one mount in and dismount it inside", on);
        Assert.Contains("A shrunken mount can be brought out inside a dungeon only when you are not riding and no mount is standing.", on);
        Assert.Contains("You cannot set a pet free inside a dungeon: take it outside first.", on);
        Assert.Contains("it is moved outside when there is a way out (otherwise it is shrunk), and you are told", on);
        Assert.Contains("Spell summons, familiars, hirelings, pack llamas and pack horses are not affected.", on);

        Assert.DoesNotContain("dungeon", off);
        Assert.Contains("Say stable to an animal trainer, then click the pet to leave there", off);
        Assert.Contains("You can keep 2 pets stabled in all", on);
        Assert.Contains("3 at 160, 4 at 200, 5 at 240", on);
    }

    // ---- Dying

    [Fact]
    public void DyingTellsWhatHappensAndHowToComeBack()
    {
        var text = Text("dying");

        Assert.Contains("A ghost cannot take anything: come back first", text);
        Assert.Contains("Your body turns to bones after about seven minutes, and the bones, with whatever is still in them, are gone about seven minutes after that.", text);
        Assert.Contains("Your newbied starting items are not left on the corpse", text);
        Assert.Contains("The Bag itself is an ordinary bag and stays on your body.", text);
        Assert.Contains("Healers will not help a criminal or a murderer.", text);
        Assert.Contains("Coming back costs no skill and no stats on this shard.", text);
        Assert.Contains($"Knocked Out for {(int)KnockedOutService.Duration.TotalSeconds} seconds instead of dying", text);
        Assert.Contains("A criminal or murderer who fought them may still choose to Execute them.", text);
        Assert.Contains("Anyone can loot your corpse, in a Hot Zone or not, and a looter who was not your enemy turns criminal.", text);
        Assert.Contains("In a Hot Zone anyone may also open the pack of a Knocked Out player.", text);
        Assert.DoesNotContain("Wards and Loot Protection do not apply", text);
    }

    [Fact]
    public void DyingLeavesOutTheKnockedOutAndHotZoneParagraphsWhenTheyAreOff()
    {
        var text = Text("dying", Bare());

        Assert.DoesNotContain("Knocked Out", text);
        Assert.DoesNotContain("Hot Zone ", text);
        Assert.DoesNotContain("newbied", text);
        Assert.Contains("Anyone can loot your corpse", text);
    }

    // ---- all of them

    [Fact]
    public void NoNewPageNamesAStaffCommandOrTheOldShardNameOrIsTooLongToRead()
    {
        foreach (var topic in All())
        {
            var text = string.Join(" ", topic.Paragraphs);

            Assert.DoesNotContain("Status", text.Replace("[IntentStatus", string.Empty));
            Assert.DoesNotContain("Britannia Renaissance", text);
            var limit = new[] { "firsthour", "locks", "training", "shops", "crafting", "gather", "pets", "dying" }.Contains(topic.Key) ? 60 : 80;

            Assert.True(WelcomeGuide.EstimateLines(topic) <= limit, $"{topic.Key} needs {WelcomeGuide.EstimateLines(topic)} lines");
        }
    }
}
