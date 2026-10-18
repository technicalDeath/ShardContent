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
        ("start", "Start here", ["welcome", "firsthour", "screen", "seen", "locks"]),
        ("rules", "Rules", ["fighting", "hotzones", "ward", "loot", "pets", "dying"]),
        ("skills", "Skills", ["training", "trainers", "mastery", "skillbank"]),
        ("work", "Work", ["gather", "crafting", "shops"]),
        ("travel", "Travel", ["gates", "camping", "camp"]),
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

        p.Add(HeadingMark + "Where to go");
        p.Add(
            c.StartInBritainOnly
                ? "You begin in Britain, the only town with shops, a bank, healers and trainers. The big map (the Map button, clicked twice) marks them with coloured dots: hover over a dot, or zoom in, to read its name. The Moongates page tells you how the gates reach the other towns, which have none of them."
                : "Britain is the only town with shops, a bank, healers and trainers. If you began in another town, the Moongates page tells you how to get there."
        );

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

        p.Add(
            $"Once a skill reaches {MasteryEngine.ThresholdText}, use it a little every day: Mastery guarantees it gains, and it is the sure way to Grandmaster (see the Mastery page)."
        );

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

        p.Add(
            (c.TownGuardsKillMonsters
                ? "Monsters stay dangerous everywhere. If a monster follows you into a guarded town, shout guards and the guards will kill it, even if you struck it first, so run to town when one chases you. " +
                  "Britain's woods and fields west of the castle, and south of the south-west houses, are not guarded. "
                : "Monsters stay dangerous everywhere. If a monster follows you into town and attacks you, shout guards and the guards will kill it; if you struck it first, they will not help, so don't fight back in town. ") +
            "A healer can bring you back if you die (see Dying)."
        );
        p.Add("Use the tabs above to read how things work, and type [Welcome any time to open this guide again.");

        return new Topic("firsthour", "Your first hour", p);
    }

    // ---- Your screen

    /// <summary>
    /// What the bars and buttons on the screen do, each only when the shard has that feature switched on (the client draws them from the same flags). Written 2026-10-13 from the
    /// client's own behavior, checked in the real client (docs/New-Player-Pass-2026-10-13.md).
    /// </summary>
    private static Topic ScreenTopic(Context c)
    {
        var p = new List<string>();

        if (c.MenuBar)
        {
            p.Add(HeadingMark + "The top bar");

            var buttons = "Character opens your paperdoll, Backpack your pack, Skills your skills window, Journal your messages and Map the small map (click it again for the big map). " +
                          "Names shows everyone's name, and every corpse's, and turns green while on; click it again to hide them (Alt+N, or holding Ctrl+Shift, does the same)";

            if (c.CampTravel)
            {
                buttons += ". Camp is camp travel";
            }

            if (c.GuildChat)
            {
                buttons += ". Guild chat lets you type to everyone in your guild who is online";
            }

            buttons += ". About opens this guide, and Options opens the settings.";
            p.Add(buttons);
        }

        p.Add(HeadingMark + "Fighting");
        p.Add(
            "Your paperdoll's Peace button, and the sword at the left of the bar under the game window, switch war mode. In war mode you attack what you target: double-click a monster to start. " +
            "The sword shows peace or WAR. Click it again to stop fighting. A box asks before you help a grey, criminal or red player, since that can make you a criminal too."
        );

        if (c.PotionBar)
        {
            p.Add(HeadingMark + "The potion bar");
            p.Add(
                "The first bar under the game window shows every potion you can use and how many you carry; a bigger bottle is a stronger potion. Click one to drink it. If both your hands are " +
                "full, your weapon is put away first and taken up again afterwards. The small diamonds show only the potions you have, fold the bar into one small icon, or show them all again."
            );
        }

        var bar = new List<string>
        {
            "The second bar under the game window holds what you reach for in a fight. Bandages: click to bandage yourself, or hold Shift and click to choose who. The count turns red when you are running low. " +
            "Arrows and bolts follow, dimmed when the weapon in your hand does not use them. If you have trained Magery, Alchemy or Inscription it also shows your reagents.",
            "Then come three slots for your weapon, shield and tool. They remember the last one you held: click one marked equip to put it on (whatever is in the way comes off first) or one marked held to put it away. " +
            "Hold the button down for a moment to open a strip of the others in your pack and click one to choose it. Escape or a click elsewhere closes the strip."
        };

        if (c.CombatBar)
        {
            bar.Add("The thin bar beside a weapon or shield shows how worn it is: all green when new, with red filling from the top as it wears.");
        }

        if (c.WearNotice)
        {
            bar.Add("You are also told once when a weapon, shield or armor piece you wear drops to about a quarter of its durability.");
        }

        bar.Add("The number at the end of the bar is how many stones you carry against how many you can. It turns red when you are overloaded. Your own small health bar, opened beside the potion bar when you first log in, shows your hits, mana and stamina.");

        p.Add(HeadingMark + "The combat bar");
        p.AddRange(bar);

        if (c.AutoUse)
        {
            p.Add(HeadingMark + "Auto options");
            p.Add(
                "The potion bar and the combat bar each have a small gear button at the end. It opens a panel with options that do for you what you could do with the bar: the combat bar can bandage you when your health " +
                "falls below 75%, and the potion bar can drink a Heal potion at 25% health, a Refresh potion at 25% stamina, and the Cure potion that fits the poison you have. Potions are drunk strongest first, " +
                "one at a time, and only when you could drink them yourself. A new character starts with them on; change them in that panel or on the Item shortcuts page of Options."
            );
        }

        if (c.AutoPickup)
        {
            p.Add(HeadingMark + "Picking up arrows and reagents");
            p.Add(
                "As you walk, the shard picks up arrows and bolts lying within one step of you if your Archery is 30 or more, and reagents if your Magery, Alchemy or Inscription is 30 or more. " +
                "The combat bar's gear button and the Auto pickup page of Options have a switch each for arrows, bolts and reagents."
            );
        }

        p.Add(HeadingMark + "The spell bar");
        p.Add(
            "Once you have trained Magery, a bar shows one circle of spells at a time as icons, with the mana each one costs under it, starting with the highest circle your Magery can cast. The small arrows beside the circle's name change circle. " +
            "Click an icon to cast that spell; an icon is dim while your mana, or your Magery, is short for it. Hover over one for the spell's words, reagents and the Magery it needs. The spell must be in your spellbook. " +
            "The small diamonds work as on the other bars, and the Item shortcuts page of Options switches any of these bars off or on."
        );

        p.Add(HeadingMark + "If you die");
        p.Add(
            "A small strip beside the game window tells you what to do as a ghost and shows the direction and distance to your body, updated as you walk, until you open it. " +
            "Right-click the strip to hide it. See the Dying page for how to come back."
        );

        p.Add(HeadingMark + "Keys");
        p.Add(
            "A new profile starts with a few hotkeys: Alt+S opens your skills, Alt+C your status, Alt+P your paperdoll, Alt+I your backpack and Alt+J your journal, Alt+R the small map and Alt+O the settings. " +
            "Alt+B bandages yourself and Alt+Shift+B bandages the person you targeted last. Alt+H drinks your strongest Heal potion, Alt+F your strongest Refresh potion and Alt+U the Cure potion that fits your poison (with the potion bar open). Alt+N shows or hides names. Tab switches war mode on and off. The Macros page of Options changes any of them. " +
            "Type [HelpInfo to see every command you can type."
        );

        p.Add(HeadingMark + "Windows");
        p.Add(
            "If your screen is wide enough, the journal, skills window and small map open in the dark column to the right of the game window, one under the other, so they do not cover your paperdoll or each other. " +
            "Your backpack and other containers go there too while there is room. " +
            "The window Alt+C opens shows your strength, dexterity, intelligence, hits, mana, stamina, gold, armor rating and weight. " +
            "In a shop window, hover over an item for sale to read it. If a player bothers you, Options has an Ignore List and this guide has a Page staff button."
        );

        p.Add(HeadingMark + "Item shortcuts");
        p.Add(
            "The box beside the game window is empty to start with. Drop any item into it to make a shortcut: it counts how many of that item you carry and double-clicking it uses one. " +
            "Hold Alt and right-click a shortcut to remove it."
        );

        return new Topic("screen", "Your screen", p);
    }

    // ---- Bars and numbers

    /// <summary>
    /// What the game draws over and around characters and items, apart from the shard's own bars: health bars (a missing one means full health), damage and heal numbers, buff icons and item tooltips.
    /// Split from the Your screen page, which was at the line limit.
    /// </summary>
    private static Topic SeenTopic(Context c)
    {
        var p = new List<string>();

        p.Add(HeadingMark + "Health bars");
        p.Add(
            "The small bar under a character shows how hurt it is. Yours, your friends', the townspeople's and the animals' bars show only while they are hurt, and go about five seconds after they are full again: " +
            "no bar means full health. Anything that could attack you (a grey or red character, or a monster that is after you) keeps a wider bar with an amber fill. " +
            "The Mobiles part of the Options window turns this off."
        );


        if (c.DamageNumbers || c.HealNumbers || c.StaminaNumbers)
        {
            var numbers = c.DamageNumbers
                ? "When you hurt something, or something hurts you, the damage floats up over the one hit: yellow over you, red over anything else. Nobody else's fights show numbers. "
                : "";

            if (c.HealNumbers)
            {
                numbers += "A heal floats up as a green plus sign and a number over the one healed, when you heal or are healed, by bandage, potion or spell. ";
            }

            if (c.StaminaNumbers)
            {
                numbers += "The stamina a hit takes from you floats up over you in blue, such as -3 stam (a mace or a staff takes 3 to 5 more), and so does the stamina a refresh potion gives back, such as +8 stam; each has its own switch. ";
            }

            p.Add(HeadingMark + "Numbers over heads");
            p.Add(numbers + "The Combat-Spells page of Options turns the numbers off.");
        }

        if (c.BuffBar)
        {
            var states = new List<string>();

            if (c.SafeWorld)
            {
                states.Add("Criminal Intent");
            }

            if (c.Theft)
            {
                states.Add("a Backpack Ward");
            }

            if (c.FaintMemories)
            {
                states.Add("Faint Memories");
            }

            if (c.HotZones)
            {
                states.Add("a Hot Zone");
            }

            if (c.CampingFires)
            {
                states.Add("a secure camp");
            }

            var shard = states.Count == 0 ? "" : $" and this shard's own states: {string.Join(", ", states.Take(states.Count - 1))}{(states.Count > 1 ? " and " : "")}{states[^1]}";

            p.Add(HeadingMark + "The buff icons");
            p.Add(
                "Small icons at the top left of the game window show what is affecting you: a spell on you, poison, being hidden" + shard + ". " +
                "Hover over one to read what it means and, if it runs out, how long is left."
            );
        }

        if (c.ItemTooltips)
        {
            p.Add(HeadingMark + "Item tooltips");
            p.Add(
                "Hover the pointer over an item, in your pack, on your paperdoll, on the ground or in a shop, to read its name and its weight. A weapon also shows its damage, speed, Strength needed and skill, " +
                "and armor its armor rating and Strength needed. A tooltip tells what is magical about an item only after Item Identification has been used on it. Click an item once for its name over its head, as before."
            );
        }

        return new Topic("seen", "Bars and numbers", p);
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

        needUp.Add("Mastery's daily allowance is spent only by a skill set to Up");

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
            $"From {MasteryEngine.ThresholdText} a skill also gains through Mastery: a daily allowance of guaranteed gains on top of ordinary gain (see the Mastery page).",
            HeadingMark + "Trainers",
            "Town NPCs will teach you a skill they know well, for gold. An NPC teaches a skill only if it has at least " +
            $"{Points(StockTraining.MinimumTrainerSkillTenths)} in it, and raises yours to a third of its own, never past your own skill cap: about 20.0 to 33.0 for most trainers. " +
            "You pay 1 gold for each 0.1 point you gain.",
            "To start, click the NPC once and pick the skill from its menu; skills it can teach you no more of are greyed out. The NPC tells you the price. " +
            "Then drop exactly that much gold on the NPC, and only after it has named the price: gold dropped on an NPC you have not asked is kept as a gift. " +
            "Paying less teaches you less; paying more is lost.",
            "You can also stand within three tiles and say the NPC's name followed by train: a town NPC lists the skills it can teach you, but only the menu gives a price.",
            $"The skill must be set to Up, and you need room under the {n.SkillCapPoints}-point cap. At the cap a lesson takes its points from skills you have set to Down, and those points are lost.",
            HeadingMark + "Finding a trainer",
            "The Who teaches what page lists the trainers in Britain, shopkeepers and guildmasters both, and the skills each one teaches."
        };

        if (c.FaintMemories)
        {
            p.Add(HeadingMark + FaintMemoriesPolicy.Name);
            p.Add($"{FaintMemoriesPolicy.Name} points come back through ordinary skill use, not through a trainer's lesson (see the Skill Bank page).");
        }

        return new Topic("training", "Training", p);
    }

    // ---- Trainers

    /// <summary>
    /// Who teaches what in Britain, read from the NPCs' constructors (docs/Britain-Guildmasters-Evidence.md): a town NPC's menu offers a skill it has at 60.0 or more, and only a Healer
    /// limits itself (to four skills). Only NPCs the world spawns are listed: there is no plain Ranger or Veterinarian in Britain.
    /// </summary>
    private static Topic TrainersTopic()
    {
        var p = new List<string>
        {
            HeadingMark + "How to learn from one",
            "A trainer teaches a skill whenever you know less than a third of what it knows. The Training page has the rules and the price: click the NPC, pick the skill, pay what it names.",
            HeadingMark + "Shops and workshops",
            "Alchemist: Alchemy, Taste Identification. Animal Trainer: Animal Lore, Animal Taming, Veterinary. Armorer and Weaponsmith: Arms Lore, Blacksmithy. " +
            "Baker: Cooking. Bard: Discordance, Musicianship, Peacemaking, Provocation. Blacksmith: Blacksmithy, Fencing, Mace Fighting, Swordsmanship, Tactics, Parrying.",
            "Bowyer: Bowcraft/Fletching, Archery. Carpenter: Carpentry, Lumberjacking. Cobbler, Tailor and Weaver: Tailoring. Cook: Cooking, Taste Identification. " +
            "Fisherman: Fishing. Furtrader: Alchemy, Animal Lore. Healer: Healing, Forensic Evaluation, Spirit Speak, Swordsmanship. Herbalist: Alchemy, Cooking, Taste Identification.",
            "Jeweler: Item Identification. Mage: Magery, Evaluating Intelligence, Inscription, Meditation, Resisting Spells. Mapmaker: Cartography. Miner: Mining. " +
            "Scribe: Inscription, Evaluating Intelligence. Shipwright: Carpentry. " +
            "Tinker: Tinkering, Lockpicking, and Remove Trap (which needs 50.0 in Lockpicking and in Detecting Hidden).",
            HeadingMark + "Guildmasters",
            "The guildmasters know more. Blacksmiths': Arms Lore, Blacksmithy. Fishermen's: Fishing. Healers': Anatomy, Forensic Evaluation, Healing, Resisting Spells, Spirit Speak. " +
            "Mages': the Mage's list and Wrestling. Merchants': Arms Lore, Item Identification. Miners': Item Identification, Mining. Tailors': Tailoring. " +
            "Tinkers': Tinkering, Lockpicking, Remove Trap.",
            "Rangers': Animal Lore, Archery, Camping, Hiding, Resisting Spells, Stealth, Tactics, Tracking. " +
            "Thieves': Detecting Hidden, Fencing, Hiding, Lockpicking, Poisoning, Remove Trap, Snooping, Stealing, Stealth. " +
            "Warriors': Arms Lore, Fencing, Mace Fighting, Parrying, Resisting Spells, Swordsmanship, Tactics. Bards': Archery, Swordsmanship and the Bard's list.",
            "Stealth is taught only to someone with 80.0 in Hiding. A few trainers also know some other skill only part of the time, and teach it only while it is at 60.0 or more: " +
            "the trainer's menu shows what it teaches today."
        };

        return new Topic("trainers", "Who teaches what", p);
    }

    // ---- Moongates

    /// <summary>
    /// How to get to Britain from the town a character began in. World generation keeps the shopkeepers, bankers, healers, trainers and guildmasters in Britain only (the manifest's
    /// <c>britainOnlySpawnerFiles</c>), yet the stock character-creation list offers nine starting towns, so a new character can begin in one with none of them. The gate list is the
    /// stock Felucca list (<c>PMList.Felucca</c>: no Vesper); the Britain gate stands outside the town (docs/Moongates-Evidence.md).
    /// </summary>
    private static Topic GatesTopic(Context c)
    {
        var p = new List<string>
        {
            HeadingMark + "Britain is the town",
            "Britain is the only town with shopkeepers, bankers, healers, trainers and guildmasters: the other towns have none of them. " +
            (c.StartInBritainOnly ? "Every new character starts in Britain, inside the town. " : "If your character began in another town, take its moongate to Britain. ") +
            "The Britain gate stands in open country south of the town, outside the walls: walk north from it to reach the town.",
            HeadingMark + "Using a moongate",
            "Stand next to a moongate, a blue shimmering gate, and double-click it. Choose a town from the list and press Okay. There are gates at Moonglow, Britain, Jhelom, Yew, Minoc, " +
            "Trinsic, Skara Brae, New Magincia and Buccaneer's Den. Vesper has none; Minoc's is the nearest.",
            "A gate will not work while you are a criminal, in a fight or casting a spell. It puts you at peace and hides you, and your pets that are following you and within three steps of you come with you."
        };

        if (c.HotZones && c.TravelWarning)
        {
            p.Add("Buccaneer's Den is a Hot Zone. If you go there from outside one, a window warns you and asks you to confirm first (see the Hot Zones page).");
        }
        else if (c.HotZones)
        {
            p.Add("Buccaneer's Den is a Hot Zone (see the Hot Zones page).");
        }

        p.Add(HeadingMark + "Other ways");
        p.Add(
            (c.MenuBar ? "The Map button on the top bar opens a map that shows where you are; click it again for the big map. " : "") +
            (c.CampTravel ? "A camp you have made can carry you across the land too: see the Camp travel page." : "On foot, follow the roads between the towns.")
        );

        return new Topic("gates", "Moongates", p);
    }

    // ---- Money and shops

    private static Topic ShopsTopic(Context c, Numbers n)
    {
        var p = new List<string>
        {
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
        };

        if (c.Furnishers)
        {
            p.Add(HeadingMark + "The Furnisher");
            p.Add(
                "The Furnisher stands in a showroom hall in the Counselor's Guild in Britain, where every piece is on show, and sells decorations for a house" +
                (n.FurnisherHighGold > 0 ? $", from {n.FurnisherLowGold:N0} to {n.FurnisherHighGold:N0} gold a piece" : "") + ". The Furnisher buys nothing back."
            );
        }

        return new Topic("shops", "Money and shops", p);
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
            "Smelt and Repair are in the Blacksmith menu. Blacksmithing needs an anvil and a forge within two tiles.",
            HeadingMark + "Choosing what to make to train",
            "Click the small ? beside an item in the menu: it shows the skill the item needs and your chance of making it. Making things trains the skill, and it trains most on items you are not sure to make, " +
            "so an item you almost always make (a shirt, once your Tailoring is well past its need) teaches you very little. Move up to something harder as your chance rises."
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
                "A full pack, a worn-out tool, or carrying as much as you can without being overloaded ends it too. Target something new while it runs and it moves on to that once the current attempt finishes."
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

        p.Add(HeadingMark + "Selling what you gather");
        p.Add("No one buys raw ore: smelt it into ingots at a forge first (Smelt is in the Blacksmith menu), then sell the ingots to a blacksmith.");

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

        p.Add(HeadingMark + "Setting a pet free");
        p.Add("Say its name and then release (or all release for every pet). A window asks you to confirm: nothing happens until you press Continue.");

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
        var dr = DeathRecovery.Rules;
        var p = new List<string>
        {
            HeadingMark + "When you die",
            "You become a ghost and your body stays where you died. A ghost cannot take anything: come back first (below), then return to your body, open it and take your things. " +
            (c.LongerPlayerCorpses
                ? $"Your body turns to bones after about {dr.PlayerCorpseMinutes} minutes, and the bones, with whatever is still in them, are gone about 7 minutes after that."
                : "Your body turns to bones after about seven minutes, and the bones, with whatever is still in them, are gone about seven minutes after that.")
        };

        if (c.CorpseCompass)
        {
            p.Add("An arrow on your screen points to your body, as a ghost and after you come back, until you reach it, open it, or it is gone.");
        }

        if (c.StarterPackage)
        {
            p.Add("Your newbied starting items are not left on the corpse: they stay with you, even inside bags (a murderer loses them). The Bag itself is an ordinary bag and stays on your body.");
            p.Add("They come back into your pack, not onto your body: after you are resurrected, put your weapon and armor on again before you fight.");
        }

        p.Add(HeadingMark + "Coming back");
        p.Add(
            "Walk up to a healer in a town (within four tiles, in sight) or to an ankh shrine, and a window offers to bring you back. A healer can see a ghost only in war mode (Tab), " +
            "and offers only as you step within reach, so if you are already beside one, switch to war mode, step back and walk up again. Healers will not help a criminal or a murderer. " +
            "Coming back costs no skill and no stats on this shard."
        );

        if (c.Materializing)
        {
            p.Add(HeadingMark + "Between Worlds");
            p.Add(
                $"When you come back you are Between Worlds: monsters cannot see you, and other players see you as a pale shape. It lasts up to {dr.MaterializingMinutes} minutes, " +
                $"or until {Span(dr.MaterializingAfterOpenSeconds)} after you open your body. Walking, opening doors, looking in your pack, your bank and your body, taking things " +
                "from your body, sorting your pack and putting on your gear keep you there. Anything else (using an item or a skill, casting, attacking, taking things from your bank " +
                "or anywhere but your body and your pack, buying or selling) brings you fully back, " +
                "but a window asks you first: OKAY brings you back and goes ahead, CANCEL keeps you Between Worlds."
            );
        }

        if (c.KillerGoesHome)
        {
            p.Add($"A monster that killed you, if it was fighting nobody else, goes back to where it lives and leaves you alone for {Span(dr.KillerSpareSeconds)} after it next sees you.");
        }

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

        if (c.BlueSelfLoot)
        {
            p.Add(
                "While you are not a murderer or a criminal, double-clicking your own body takes everything back into your pack where it was and puts the gear you " +
                "were wearing on again. Anything that does not fit stays on the body."
            );
        }

        return new Topic("dying", "Dying", p);
    }

    private static string Span(int seconds) =>
        seconds % 60 != 0 ? $"{seconds} seconds" : seconds == 60 ? "a minute" : $"{seconds / 60} minutes";
}
