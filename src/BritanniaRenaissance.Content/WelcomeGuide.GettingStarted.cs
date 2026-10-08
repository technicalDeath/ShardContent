namespace BritanniaRenaissance.Content;

/// <summary>
/// The getting-started pages of the [Welcome guide (owner sign-off 2026-10-07): Your first hour, Skill locks 101, Training, Money and
/// shops, Crafting, Gathering and repeats, Pets and Dying, and the chapters the guide's tabs group every page into. Each claim was read
/// against the code or the owner's ruling behind it; docs/Guide-Getting-Started-Pages.md records the audit, and WelcomeGuideTests pins
/// the wording so a rule that changes shows up there.
/// </summary>
public static partial class WelcomeGuide
{
    /// <summary>A tab of the guide and the topics under it, in reading order.</summary>
    public sealed record Chapter(string Key, string Title, IReadOnlyList<string> TopicKeys);

    private static readonly (string Key, string Title, string[] Topics)[] ChapterTable =
    [
        ("start", "Start here", ["welcome", "firsthour", "locks"]),
        ("rules", "Rules", ["fighting", "hotzones", "ward", "loot", "pets", "dying"]),
        ("skills", "Skills", ["training", "mastery", "skillbank"]),
        ("work", "Work", ["gather", "crafting", "shops"]),
        ("travel", "Travel", ["camping", "camp"]),
        ("commands", "Commands", ["commands"])
    ];

    /// <summary>The most topics one chapter may hold (the topic list under the tabs has room for six).</summary>
    public const int MaximumTopicsPerChapter = 6;

    /// <summary>The chapters that have at least one topic in <paramref name="topics"/>, with only the topics that exist.</summary>
    public static IReadOnlyList<Chapter> Chapters(IReadOnlyList<Topic> topics)
    {
        var present = topics.Select(t => t.Key).ToHashSet();

        return ChapterTable
            .Select(c => new Chapter(c.Key, c.Title, c.Topics.Where(present.Contains).ToArray()))
            .Where(c => c.TopicKeys.Count > 0)
            .ToArray();
    }

    /// <summary>Every topic key the guide can show, in the order the chapters give them.</summary>
    public static IReadOnlyList<string> AllTopicKeys => ChapterTable.SelectMany(c => c.Topics).ToArray();

    private static List<Topic> InChapterOrder(List<Topic> topics)
    {
        var order = AllTopicKeys.Select((key, index) => (key, index)).ToDictionary(p => p.key, p => p.index);

        return topics.OrderBy(t => order.TryGetValue(t.Key, out var i) ? i : int.MaxValue).ToList();
    }

    /// <summary>What a town NPC can teach, from <c>BaseCreature.CheckTeachSkills</c>: a skill it has at 60.0 or more, up to a third of it, never past 42.0.</summary>
    public static class StockTraining
    {
        public const int MinimumTrainerSkillTenths = 600;
        public const int MaximumLessonTenths = 420;
    }

    // ---- Your first hour

    private static Topic FirstHourTopic(Context c, Numbers n)
    {
        var p = new List<string> { HeadingMark + "What you start with" };

        if (c.StarterPackage)
        {
            p.Add(
                "You begin with a Bag, a pair of scissors and the tools, weapon, armor and supplies your skills call for. Newbied items stay with you when you die, " +
                "even inside bags (a murderer loses them), and shopkeepers will not buy them. The Bag itself is an ordinary bag."
            );
        }

        if (c.StarterGold)
        {
            p.Add("Your first character on an account starts with 500 gold; later characters start with none. See Money and shops for the bank and the shops.");
        }

        if (c.Theft)
        {
            p.Add("A Backpack Ward watches for thieves: one it catches turns criminal and cannot steal from you again until the Ward runs out. Double-click it for details.");
        }

        if (c.CampingKit)
        {
            p.Add("A Bedroll and Kindling let you make a camp. See the Camping page.");
        }

        p.Add(HeadingMark + "Your skills");
        p.Add(
            "Your skills are in your skills window (the Skills button on your paperdoll). You start with the three skills of your template (an Advanced character picks its own), " +
            "and any skill can be raised by using it. Each skill has a setting that decides whether it can gain: see Skill locks 101."
        );

        if (c.FaintMemories)
        {
            p.Add(
                $"{FaintMemoriesPolicy.Name}: {Points(n.FaintPointsTenths)} free points unlock {n.FaintHours} hours after you create your character, and come back as you train a skill set to Up, " +
                $"between {Points(n.FaintFloorTenths)} and {Points(n.FaintCeilingTenths)}. [SkillBank shows the countdown."
            );
        }

        if (c.SkillClasses)
        {
            p.Add("[SkillClasses shows how fast each skill trains.");
        }

        p.Add(HeadingMark + "Training");
        p.Add(
            "Town trainers teach the basics of many skills for gold (see Training). Otherwise use the skill. A use that cannot fail, or is far too hard, does not train it."
        );

        p.Add(HeadingMark + "Staying safe");

        if (c.SafeWorld)
        {
            p.Add(
                (c.HotZones ? "Outside the Hot Zones, other" : "Other") +
                " players cannot attack you unless you opt in with [Intent, break the law or are already fighting them."
            );
        }

        p.Add("Monsters stay dangerous everywhere. Guards protect the towns, and a healer can bring you back if you die (see Dying).");
        p.Add("Use the tabs above to read how things work, and type [Welcome any time to open this guide again.");

        return new Topic("firsthour", "Your first hour", p);
    }

    // ---- Skill locks 101

    private static Topic SkillLocksTopic(Context c, Numbers n)
    {
        var p = new List<string>
        {
            HeadingMark + "The three settings",
            "Every skill has a setting in your skills window (the Skills button on your paperdoll). Click the arrow beside a skill to change it: it cycles Up, Down and Locked, and Locked shows a padlock.",
            "Up: the skill can gain. Down: the skill can give points up. When another skill gains, a skill set to Down may lose the same amount. " +
            "Locked: the skill neither gains nor loses.",
            HeadingMark + $"The {n.SkillCapPoints}-point cap",
            $"Your skills together can hold {n.SkillCapPoints} points. Below that, any skill set to Up can gain, and a gain sometimes takes points from a skill set to Down (more often the closer you are to the cap). " +
            "At the cap a skill can gain only when a skill set to Down has points to give up, so keep some skill you no longer train set to Down.",
            HeadingMark + "Why a skill is not gaining",
            "It is set to Down or Locked: set it to Up.",
            $"You are at the {n.SkillCapPoints}-point cap and no skill set to Down has points left.",
            "Uses that cannot fail, or are far too hard, do not train a skill.",
            $"It has reached {MasteryEngine.ThresholdText}: from there Mastery takes over (see the Mastery page).",
            "It has reached its cap."
        };

        var needUp = new List<string>();

        if (c.SkillBank)
        {
            needUp.Add("Skill Bank points come back into a skill set to Up");
        }

        if (c.FaintMemories)
        {
            needUp.Add($"{FaintMemoriesPolicy.Name} go into a skill set to Up");
        }

        needUp.Add("Mastery allowance is spent only by a skill set to Up");

        p.Add(HeadingMark + "Other systems that need Up");
        p.Add(string.Join(". ", needUp) + ".");

        if (c.SkillBank)
        {
            p.Add(
                $"Points a skill set to Down gives up to a skill gain are saved in your Skill Bank, up to its {n.BankPoints}-point limit (see the Skill Bank page and [SkillBank). " +
                "Points taken for a trainer's lesson are not saved."
            );
        }

        return new Topic("locks", "Skill locks 101", p);
    }

    // ---- Training

    private static Topic TrainingTopic(Context c, Numbers n)
    {
        var p = new List<string>
        {
            HeadingMark + "How skills grow",
            "You train a skill by using it, within the limits on the Skill locks 101 page. " +
            (c.SkillClasses ? "How fast depends on the skill's class: [SkillClasses lists them. " : string.Empty) +
            $"From {MasteryEngine.ThresholdText} a skill grows through Mastery instead.",
            HeadingMark + "Trainers",
            "Town NPCs will teach you a skill they know well, for gold. An NPC teaches a skill only if it has at least " +
            $"{Points(StockTraining.MinimumTrainerSkillTenths)} in it, and raises yours to a third of its own, never past your own skill cap: about 20.0 to 33.0 for most trainers. " +
            "You pay 1 gold for each 0.1 point you gain.",
            "To start, click the NPC once and pick the skill from its menu; skills it can teach you no more of are greyed out. The NPC tells you the price. " +
            "Then drop exactly that much gold on the NPC, and only after it has named the price: gold dropped on an NPC you have not asked is kept as a gift. " +
            "Paying less teaches you less; paying more is lost.",
            "You can also stand within three tiles and say the NPC's name followed by train: a town NPC lists the skills it can teach you, but only the menu gives a price.",
            $"The skill must be set to Up, and you need room under the {n.SkillCapPoints}-point cap. At the cap a lesson takes its points from skills you have set to Down, and those points are lost.",
            HeadingMark + "Who teaches what",
            "A trainer teaches the skills listed here whenever you know less than a third of what it knows:",
            "Alchemist: Alchemy, Taste Identification. Animal Trainer: Animal Lore, Animal Taming, Veterinary. Armorer and Weaponsmith: Arms Lore, Blacksmithy. " +
            "Bard: Discordance, Musicianship, Peacemaking, Provocation. Blacksmith: Blacksmithy, Fencing, Mace Fighting, Swordsmanship, Tactics, Parrying.",
            "Bowyer: Bowcraft/Fletching, Archery. Carpenter: Carpentry, Lumberjacking. Cook: Cooking, Taste Identification. Fisherman: Fishing. " +
            "Healer: Healing, Forensic Evaluation, Spirit Speak, Swordsmanship. Herbalist: Alchemy, Cooking, Taste Identification.",
            "Mage: Magery, Evaluating Intelligence, Inscription, Meditation, Resisting Spells. Mapmaker: Cartography. Miner: Mining. " +
            "Ranger: Detecting Hidden, Archery, Tracking, Veterinary. Scribe: Inscription, Evaluating Intelligence. Tailor: Tailoring. " +
            "Tinker: Tinkering, Lockpicking, and Remove Trap (which needs 50.0 in Lockpicking and in Detecting Hidden). Veterinarian: Animal Lore, Veterinary."
        };

        if (c.FaintMemories)
        {
            p.Add(HeadingMark + FaintMemoriesPolicy.Name);
            p.Add($"{FaintMemoriesPolicy.Name} points come back through ordinary skill use, not through a trainer's lesson (see the Skill Bank page).");
        }

        return new Topic("training", "Training", p);
    }

    // ---- Money and shops

    private static Topic ShopsTopic()
    {
        return new Topic(
            "shops",
            "Money and shops",
            [
                HeadingMark + "Banks",
                "Say bank near a banker to open your bank box. Other things to say to a banker: balance (how much gold you have in the bank), " +
                "withdraw 500 (take gold out, at most 5,000 at a time) and check 10000 (turns 5,000 to 1,000,000 gold from your bank box into a check that stays in the box).",
                "There is no deposit command: drag gold into your bank box. A banker will not do business with a criminal.",
                HeadingMark + "Shops",
                "Stand within four tiles of a shopkeeper and say vendor buy or vendor sell, or click the shopkeeper once for a menu with Buy and Sell.",
                "A purchase is paid from your pack. If your pack is short and the purchase costs 2,000 gold or more, it is paid from your bank instead.",
                "Shopkeepers do not buy newbied items. In a guarded town a murderer is refused service.",
                HeadingMark + "Your pets",
                "Say stable to an animal trainer, then click the pet to leave there, and say claim to get your pets back. Stabling costs 30 gold for each pet; claiming is free. Unload a pack animal first."
            ]
        );
    }

    // ---- Crafting

    private static Topic CraftingTopic(Context c, Numbers n)
    {
        var p = new List<string>
        {
            HeadingMark + "Making things",
            "Double-click a crafting tool, then target the material you want to work (ingots for a Blacksmith, for example). A menu opens: a Blacksmith sees Repair, Smelt and lists of things to build, a Tinker sees categories. " +
            "A menu lists only what your skill and your materials allow, so a longer list means more skill or more materials.",
            "To make the same thing again, double-click the tool and target the tool itself instead of the material: the game reminds you with Target this tool to make last item.",
            "Smelt and Repair are in the Blacksmith menu. Blacksmithing needs an anvil and a forge within two tiles."
        };

        if (c.Theft && n.WardIngots > 0)
        {
            p.Add($"A Tinker can make a Backpack Ward from {n.WardIngots} iron ingots once Tinkering is a little above {n.WardCraftSkill} (it is in the Miscellaneous list).");
        }

        if (c.ActionRepeat)
        {
            p.Add("Cooking, spinning and weaving carry on through a whole stack: see the Gathering and repeats page.");
        }

        return new Topic("crafting", "Crafting", p);
    }

    // ---- Gathering and repeats

    private static Topic GatheringTopic(Context c)
    {
        var p = new List<string>();

        if (c.HarvestRepeat)
        {
            p.Add(HeadingMark + "Gathering");
            p.Add(
                "Mining, lumberjacking and fishing repeat on the tile you chose until its resource runs out, at the usual pace. " +
                "Walking, casting, using another skill, entering war mode, fighting or being hurt, or opening another gathering target ends it. " +
                "A full pack or a worn-out tool ends it too. Target something new while it runs and it moves on to that once the current attempt finishes."
            );
        }

        if (c.ActionRepeat)
        {
            p.Add(HeadingMark + "Other repeated actions");
            p.Add(
                "Taming tries the same creature again after each plain failure until it accepts you or something stops it, lockpicking keeps working the same lock while you have picks, " +
                "a spinning wheel spins your whole stack, a loom takes your whole stack at once, and cooking cooks your whole stack at the heat source you chose. " +
                "Walking, casting, using another skill, war mode, fighting or being hurt end these too, and so does opening any target cursor."
            );
        }

        p.Add(HeadingMark + "Nothing speeds up");
        p.Add("Each attempt is the ordinary one, with the usual delay, skill check and yield. Only the re-targeting is done for you.");

        return new Topic("gather", "Gathering and repeats", p);
    }

    // ---- Pets

    private static Topic PetsTopic(Context c)
    {
        var p = new List<string>();

        if (c.PetRestrictions)
        {
            p.Add(HeadingMark + "Players");
            p.Add("Tamed pets never attack players.");
            p.Add(HeadingMark + "Dungeons");
            p.Add(
                "A tamed pet cannot enter or stay in a dungeon: it will not follow you through a dungeon teleporter or gate, and if one is tamed or dismounted inside a dungeon it is shrunk into your pack. " +
                "Double-click a shrunken pet outside a dungeon, with a free follower slot, to bring it out."
            );
            p.Add("You may ride one mount in and dismount it inside: it stays and fights, but never attacks players. Any other pet, or a second mount, is shrunk.");
            p.Add(
                "You can tame inside a dungeon, but if the creature would have to be shrunk you need room in your pack first. A shrunken mount can be brought out inside a dungeon only when you are not riding and no mount is standing. " +
                "You cannot set a pet free inside a dungeon: take it outside first. If a pet abandons you because it lost loyalty in a dungeon, it is moved outside when there is a way out (otherwise it is shrunk), and you are told."
            );
            p.Add("Spell summons, familiars, hirelings, pack llamas and pack horses are not affected.");
        }

        p.Add(HeadingMark + "Stables");
        p.Add(
            "Say stable to an animal trainer, then click the pet to leave there, and say claim to get your pets back. Stabling costs 30 gold for each pet; claiming is free. " +
            "You can keep 2 pets stabled in all, and more as your Animal Taming, Animal Lore and Veterinary rise together: 3 at 160, 4 at 200, 5 at 240."
        );

        return new Topic("pets", "Pets", p);
    }

    // ---- Dying

    private static Topic DyingTopic(Context c)
    {
        var p = new List<string>
        {
            HeadingMark + "When you die",
            "You become a ghost and your body stays where you died. A ghost cannot take anything: come back first (below), then return to your body, open it and take your things. " +
            "Your body turns to bones after about seven minutes, and the bones, with whatever is still in them, are gone about seven minutes after that."
        };

        if (c.StarterPackage)
        {
            p.Add("Your newbied starting items are not left on the corpse: they stay with you, even inside bags (a murderer loses them). The Bag itself is an ordinary bag and stays on your body.");
        }

        p.Add(HeadingMark + "Coming back");
        p.Add(
            "Walk up to a healer in a town (within four tiles, in sight) or to an ankh shrine, and a window offers to bring you back. Healers will not help a criminal or a murderer. " +
            "Coming back costs no skill and no stats on this shard."
        );

        if (c.KnockedOut)
        {
            var seconds = (int)KnockedOutService.Duration.TotalSeconds;
            p.Add(HeadingMark + "Knocked Out");
            p.Add(
                $"A player who is not a criminal or a murderer and is brought down by another player is Knocked Out for {seconds} seconds instead of dying: they cannot act, be hurt or be healed, and they wake with half health. " +
                "A criminal or murderer who fought them may still choose to Execute them. See Fighting other players."
            );
        }

        p.Add(HeadingMark + "Your corpse");
        p.Add(
            (c.HotZones ? "Anyone can loot your corpse, in a Hot Zone or not" : "Anyone can loot your corpse") +
            ", and a looter who was not your enemy turns criminal." +
            (c.HotZones ? " In a Hot Zone anyone may also open the pack of a Knocked Out player." : string.Empty)
        );

        return new Topic("dying", "Dying", p);
    }
}
