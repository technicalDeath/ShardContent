# Bot farm: what new players run into (night of 2026-10-14)

Fifty headless bots played the shard unattended on the disposable farm host (`work/hosts/farm`, a copy of the dev distribution), for about four hours on the main roster and up to an hour on the newest. They covered 16 professions and the Advanced template: archer, bard, ranger, mage, warlock, sorcerer, mace fighter, fencer, swordsman, blacksmith, carpenter, tailor, tinker, tamer, fisherman and prospector. "Veteran" bots know the monster, craft and taming tables, while "newbie" bots go only by what a new player can see and learn from what happens to them. They share what they learn per profession. A second session watched their logs all night, reported what went wrong, and reviewed this report against the logs (its corrections are folded in).

This report keeps only what a player would meet. Each entry says how many bots and professions hit it, how it was confirmed, and the levers I can see. Nothing here has been changed on the dev world. The economy details (prices, stock, material supply) are in `Bot-Farm-Tuning-Notes.md`.

## In short

**Observation period:** 2026-10-14 19:00 to 2026-10-15 01:38. The roster grew from 12 to 50 bots by 23:21 and held there (the supervisor stopped up to three at a time when memory ran low). Bot faults were fixed as they turned up until 00:41; from 00:41 to 01:38 the farm ran untouched, as a clean hour.

**The findings most worth acting on**, each confirmed in game and in the code, or in the real client:
1. **Guards ignore monsters inside Britain** (finding 1). Monsters chased bots into town, bots called the guards five times inside the town region, no guard came, and gazers killed bots on the healer's doorstep.
2. **Training dummies cannot train a new character** (finding 6). Their limit is 25, and every template starts at 50.
3. **Nothing tells a new crafter which items still teach** (finding 8). Over two hours of a fair test, the veteran tailor gained 3.5 times the newbie's Tailoring. The newbie spent its 500 starting gold on items that taught nothing within the first hour, and then could not craft at all.
4. **The Bowyer lists fletcher's tools as "Arrow Fletching"** (finding 22, real-client screenshot). They sit beside "Arrow" at the same price.
5. **Raw ore has no buyer** (finding 10). A miner has to smelt first, and nothing says so.
6. **A ghost in peace mode is invisible to the healer** (finding 2, already on the to-do list).

**Your decisions**, none of them taken: which of these to change (or to answer in the guide instead), whether the crafted-goods pricing goes to the dev world (`Crafted-Goods-Pricing.md`), and whether the farm should keep running.

How sure each finding is:
- **Confirmed:** seen in game by several bots *and* found in the server code.
- **Seen:** seen in game by the bots. Check it in the real client before acting on it.
- **Candidate:** seen once or twice, or only inferred. Worth a check, not yet a finding.
- Bot-only artifacts (the headless client lacks the tooltips and bars, or the brain made a mistake) are listed at the end, so nobody acts on them.

Counts are distinct bots that logged the matching line. Brains restarted many times tonight as they were fixed, so anything counted per brain run (tool lifetimes, gold per hour) is rough.

## 1. Danger and death

1. **Monsters chase new players into Britain and the guards do nothing.** Bots that fled into town shouted "guards" six times. Five of the calls were inside Britain's town region (from `Data/regions.json`): an ettin at 1377,1752, a named monster (Oogorim) twice, and a troll twice (once at 1428,1590, near the Carpenter). No guard came, and the monster stayed. Gazers killed two bots inside the town region, one on the healer's doorstep (1470,1619). During the untouched hour, gazers roamed central Britain: they were seen at 1642,1590, 1658,1574, 1456,1696 and 1446,1709. Two more "guards" calls against them (00:52 and 00:54) brought no guard, and a gazer killed a new tailor at 1462,1652, between the Tinker and the healer (00:55). *Confirmed:* `GuardedRegion.IsGuardCandidate` only accepts criminals and murderers, so an ordinary monster is never a guard target. Levers: guards (or a town-guard spawner) that act on hostile monsters inside the guarded region; or, at least, a line in the guide that the guards protect against people, not monsters.
2. **A ghost in peace mode is invisible to the healer, and standing beside the healer does nothing.** A living mobile sees a ghost only in war mode (`Mobile.CanSee`), and the healer offers resurrection only when a ghost walks *into* range. Three bots, in three professions, stood beside the healer and were never offered. *Confirmed in code;* the bots now switch war mode on before reaching the healer, so they no longer show it. Already on `To-Do-List.md` at the owner's request.
3. **After resurrection, the starting weapon and armour are in the backpack, not worn.** 16 bots, 10 professions. Nothing reminds the player, and a character that forgets fights barehanded. *Seen.* Lever: a one-time tip after the first resurrection (the shard's `newPlayerTips` system would fit).
4. **Undead and orc camps lie within a short walk of Britain.** Shades, wraiths, spectres and zombies by the graveyard north-west of town (about 1300-1400, 1410-1520), and orcs and ratmen to the north and north-east (about 1360,1414 and 1627,1411). They killed bots of every fighting profession, and every melee bot that fought a shade died. Named orcs and ratmen ("Tekchichak", "Oogorim") follow a new character a long way. *Seen,* 20 bots. Lever: beginner spawns (rabbits, deer, wolves, mongbats, slimes) in a ring round Britain, with the undead kept further out. See tuning note 9.
5. **New characters run out of stamina.** *On the owner's to-do list (2026-10-15: "running out of stamina is an issue").* Running costs a point every 16 steps, and an extra point per step below 10% (`StaminaSystem`). At 0 a character cannot run, and stamina returns at about a point every 7 seconds. A new character's maximum stamina is its Dexterity, often about 33. Bots that ran 150 to 300 tiles to hunting ground arrived at stamina 1, could not run from a monster, and had to stand and rest; one mage died out of breath. The bots made it worse by always running (their walking command did); the next client build walks them while their stamina is below half. *Confirmed in code and in game.* Levers are in `To-Do-List.md`: a first-time tip, cheaper running or faster regeneration for new characters, or guide lines.

## 2. Learning a skill

6. **Training dummies cannot train any new character's weapon skill.** 11 melee bots in 3 professions tried at 50 skill and got "Your skill in this weapon cannot improve any further by simply practicing with a dummy". *Confirmed:* `TrainingDummies.cs` MaxSkill is 25, and every template starts its main skills at 50 (Advanced characters at about 30-35). The map still marks five dummies as places to practise. The archery butte is unproven: every try failed on "You aren't properly lined up with the target", never on a skill cap. Lever: raise the dummies' limit (for example to 50 or 60), or change the markers' wording.
7. **Bandages barely help anyone without Healing.** 15 bots in 7 professions. At Healing near 0, a bandage takes about 14 seconds and heals about 1 hit point ("they barely help"), yet every template starts with 50. *Confirmed.* Lever: a guide line, or fewer bandages for non-healers.
8. **Nothing says which crafted items still teach.** The craft menu lists what a character can make, never how hard it is. The newbie tailor (BotTailorB) made over 80 shirts, caps and sashes at Tailoring 54.5 and gained nothing in 34 minutes: those items are too easy, and they kept coming out "exceptional". The veteran tailor picked a cloak from the skill table and gained. *Seen* (one clear case; the fair newbie tailor will add a second). Lever: one line in the Skill Guide's craft pages, "when your work keeps coming out exceptional, it has nothing left to teach you: make something harder".
9. **A new Sorcerer runs dry fast.** The Sorcerer template starts with Meditation near 0 (the Pure Mage and Warlock start with some), so its mana comes back slowly, and nothing tells it to train Meditation. Starting reagents do not last one hunt ("More reagents are needed for this spell"). *Seen,* caster bots. Lever: the Skill Guide's Magery page could name Meditation and the reagent shop.

## 3. Money, shops and material

10. **No NPC buys raw ore.** A full pack of ore sold for 0 gold all evening. A Blacksmith buys iron ingots (4 gold), so ore has to be smelted at a forge first. *Confirmed; this is the era's rule.* Once taught to smelt, the miner turned 19 ore into 27 ingots and sold them for 44 gold. Lever: one guide line, "smelt ore at a forge before you sell it".
11. **Shops do not say what they sell, and two vendors often share one.** Boards are sold at both the Tinker and the Carpenter; hatchets at the Weaponsmith, not the Tinker. The Tailor sells "Cloth" and bolts, and the Weaver beside it "Folded Cloth"; neither says "cut cloth", the name the craft uses. The Armorer and the Weaponsmith share a shop. *Seen;* the bots kept walking to the wrong vendor until they were taught. Lever: the map markers or the guide could say who sells each material and tool.
12. **Crafting material runs out.** A Blacksmith stocks 16 ingots, and the farm emptied every shelf in Britain of ingots, cloth and boards by about 22:30. Stock ModernUO doubles a sold-out shelf at the hourly restock, so it eases within hours. The farm's demand was inflated, though: one bot bought 368 ingots during a fault that stopped it crafting. *Confirmed rule, inflated demand.* Details and levers: tuning note 3.
13. **Crafting at starting skill loses money at stock prices.** *Addressed on the farm host only* by the crafted-goods pricing (`Crafted-Goods-Pricing.md`, not on dev yet). With it, crafters grossed roughly 140 gold an hour each, a rough and fault-affected figure (a chair sold for 38, a cutlass 50, a cloak 53). Tools stay at stock prices, so a Tinker training on tools still loses about half its material each time.
14. **Tools wear out with no warning.** Every crafting and mining bot saw "You have worn out your tool!" with nothing before it. A stock tool has 25 to 75 uses, set at random when it is made (`BaseTool`). The shard's wear notice covers weapons, shields and armour, not tools. *Confirmed.* Lever: the same quarter-left warning for tools.

## 4. Gathering and taming

15. **Mining repeats until the pack is overloaded.** The shard's harvest repeat keeps digging while the pack gets heavier, with nothing to stop it short of the weight limit. *Seen,* 7 bots. Lever: stop the repeat near the weight limit, with a line saying why.
16. **Fishing spots run out, and the message does not say how far to move.** "The fish don't seem to be biting here" after a few minutes on one patch. *Seen,* probably intended.
17. **Looting goes past the weight limit.** An archer picked up loot (boards, mostly) until it carried 200 of 180 stones. *Seen.* Overloaded, it could not drop one board, but at 199 of 180 stones it later dropped fletcher's tools without trouble. So dropping works while overloaded (the engine's `Mobile.Lift` has no weight check either), and the board was a one-off.

## 5. Candidates (worth a check, not yet findings)

18. **Healing yourself while poisoned only says "You cannot heal yourself in your current state."** It never says that the character is poisoned and needs a cure. Seen once (BotWarlockA, 22:04). It bears on the poison relief hints. The bots only started recording overhead messages to themselves late tonight, so more such lines will show up in the next run.
19. **A criminal ghost is refused by the healer** ("Thou art a criminal. I shall not resurrect thee.") with no word on how long to wait. Three bots, around 20:53. Their criminal flag came from a bot looting fault, so it says nothing yet about how often a real player meets it.
20. **Tamers could not reach penned or wandering animals.** They chased animals for minutes without getting within the two tiles taming needs. The game does say so when a player tries from too far ("That is too far away", seen at 01:50), so only the penned case is still open: whether an animal behind a fence can be reached at all is untested. Once the bots stopped chasing the unreachable ones, they tamed a black bear (02:13) and a cow (02:30), and Animal Lore gained on the bear.
21. **No Tanner or Leatherworker appears among Britain's map markers.** Hides come only from carving a corpse, which the bots never do, so no bot met this. A player who carves would find no one in Britain to sell hides to.
22. **The Bowyer's list calls fletcher's tools "Arrow Fletching".** *Seen in the real client* (`images/bot-farm/bowyer-arrow-fletching.png`, 2026-10-15 00:15): the shop list shows "Arrow Fletching at 2gp" first, with an icon of feathered arrows, and "Arrow at 2gp" last. The shard's tooltip says only "Arrow Fletching, Weight: 2 Stones", and nothing says it is a tool for making arrows. The archer bots bought dozens in place of arrows (a bot fault, fixed), and at 2 stones each the tools overloaded them. A new archer could make the same mistake. Lever: an item-tooltip line for fletcher's tools ("a tool: makes shafts and arrows from logs and feathers"), from the shard's own tooltip list.
23. **A gargoyle hunts at Britain's north-east edge.** It killed four bots in 15 minutes (23:45-23:54) around 1527-1667, 1410-1528, one of them inside the town region (1527,1528). It casts spells, a bot reckoned a fight with it would cost about 116 hit points against a new character's 74, and the guards ignore it (finding 1). If its spawn sits that close to town, it is deadly to new players.

## Newbie against veteran

Newbie bots have no tables, so they learn by dying and by trying. Tonight's early gaps:
- **Crafting:** a newbie tailor never found which items teach (finding 8).
- **Tamers:** a newbie tamer tried a rat, which can teach nothing at 54 Animal Taming.
- **Deaths:** BotBardB was killed four times by the same named ratman (Tekchichak). Most of that came from bot faults (it walked back for its corpse into the camp, and kept war mode on after resurrection), fixed tonight, so it overstates what a new player would suffer.

**The fair comparison.** Three pairs of brand-new characters (Swordsman, Tailor, Archer) started together at about 23:37, each pair with one veteran brain and one newbie brain on the same template, starting gold and start time. The watching session measured them over two hours. The first hour was disturbed (every brain restarted several times as bots were fixed, both sides alike). The second hour, 00:41-01:35, ran untouched. Two deaths caused by bot faults are left out.

Over the two hours (about 117 minutes):

| Pair (newbie / veteran) | Skill points an hour | Main skill gained | Kills | Crafted (ok / failed) | Deaths |
| --- | --- | --- | --- | --- | --- |
| Tailor | 3.5 / 9.5 | Tailoring +1.3 / +4.6 | 1 / 2 | 75 / 12 against 61 / 7 | 1 / 0 |
| Swordsman | 17.8 / 10.6 | Swordsmanship +11.0 / +3.3 | 15 / 14 | - | 1 / 1 |
| Archer | 6.2 / 7.1 | Archery +3.1 / +4.0 | 4 / 10 | - | 1 / 2 |

The untouched second hour on its own:

| Pair (newbie / veteran) | Main skill | Kills | Crafted | Deaths |
| --- | --- | --- | --- | --- |
| Tailor | 55.8 -> 55.8 / 57.7 -> 59.1 | 1 / 2 | 0 / 26 | 1 (a gazer in town) / 0 |
| Swordsman | 54.9 -> 63.4 / 53.8 -> 55.7 | 13 / 7 | - | 1 / 1 |
| Archer | 55.0 -> 55.0 / 53.5 -> 55.9 | 0 / 8 | - | 1 / 1 |

What it shows:
1. **For a crafter, not knowing what teaches becomes a poverty trap within an hour.** In the first hour the newbie tailor spent all 500 gold on 75 items that taught little. In the second it was broke, made nothing and gained no Tailoring, while the veteran kept crafting: 3.5 times the newbie's Tailoring over the two hours. This is finding 8, measured fairly, and the strongest case in this report for a guide line about which items still teach.
2. **The newbie archer stalled the same way.** It spent its gold in the first hour and could not keep itself in arrows: 0 kills and no Archery in the second hour. The veteran kept shooting (8 kills, Archery +2.4). Part of the first-hour spending may be the bots' fletcher's-tools buying fault, fixed at 00:01 for both archers, so read this one with care.
3. **In melee, knowledge does not hold a newbie back.** The newbie swordsman fought more and learned faster (Swordsmanship +11.0 against +3.3 over two hours). The veteran's table made it pick fewer fights. A new melee character does fine by fighting whatever it meets near town.
4. **Deaths: no gap.** Every fighter died about once an hour whichever brain it had. The places kill whatever goes there: the graveyard and ratman camp north-west of town, a camp to the south (about 1364-1489, 1928-1986), and gazers inside Britain. Across the whole farm in the untouched hour: 25 deaths in 40.7 bot-hours, 0.61 per bot-hour.

## Shard features the bots saw working

- **Wear notice:** "Your equipment is severely damaged." reached a swordsman when a worn piece first dropped to a quarter of its durability (01:21). (The bot did not react to it and died soon after; that part is the bot's.)
- **Starting supplies:** the packs of new characters held the 5 Cure (orange), 3 Heal (yellow) and 3 Refresh (red) potions and the camping kit (bedroll, 5 kindling). One fighter drank a Cure potion and stayed poisoned; whether that was a stronger poison than a Lesser Cure handles is not known.
- **Harvest and action repeat:** mining, fishing and cooking repeated on their own as designed (finding 15 is about where mining stops).

## Bot-only artifacts (not player problems)

- "The Heal potion can only be told by its colour" (29 bots). The headless client names items from tile data, so it sees "Yellow Potion". A player's client shows the server's name, and the shard's item tooltips and potion bar cover it.
- "A spell at a target behind a wall is lost with no message" (12 bots). The server does answer "Target cannot be seen." (15 bots logged it). The bots' note came from their own line-of-sight check before casting.
- "Selling crafted goods to Aithne paid nothing" (5 bots). The bot was reading the previous vendor's sell list, fixed tonight.
- "Ran out of arrows with no warning". The shard's combat bar shows ammunition, but the headless bots do not draw it.
- "Saying '<name> buy' opened no list" and "Smelting gave nothing": bot timing and target mistakes, fixed tonight.

## Where the evidence is

- `work/botfarm/report.md`: every finding with the bots that hit it (`farmctl.py report`).
- `work/botfarm/evaluation.md`: how the bots' decisions paid off (`farmctl.py eval`).
- `docs/Bot-Farm-Tuning-Notes.md`: the shard-side economy and world notes this report draws on.
- The bot code and its operating guide: `tests/scenarios/bot-farm/` (`OPERATING.md`).
