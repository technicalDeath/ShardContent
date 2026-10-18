# Bot farm: what new players run into (night of 2026-10-14)

Fifty headless bots played the shard unattended on the disposable farm host (`work/hosts/farm`, a copy of the dev distribution), for about four hours on the main roster and up to an hour on the newest. They covered 16 professions and the Advanced template: archer, bard, ranger, mage, warlock, sorcerer, mace fighter, fencer, swordsman, blacksmith, carpenter, tailor, tinker, tamer, fisherman and prospector. "Veteran" bots know the monster, craft and taming tables, while "newbie" bots go only by what a new player can see and learn from what happens to them. They share what they learn per profession. A second session watched their logs all night, reported what went wrong, and reviewed this report against the logs (its corrections are folded in).

This report keeps only what a player would meet. Each entry says how many bots and professions hit it, how it was confirmed, and the levers I can see. Nothing here has been changed on the dev world. The economy details (prices, stock, material supply) are in `Bot-Farm-Tuning-Notes.md`.

## In short

**Observation period:** 2026-10-14 19:00 to 2026-10-15 01:38. The roster grew from 12 to 50 bots by 23:21 and held there (the supervisor stopped up to three at a time when memory ran low). Bot faults were fixed as they turned up until 00:41; from 00:41 to 01:38 the farm ran untouched, as a clean hour.

**The findings most worth acting on**, each confirmed in game and in the code, or in the real client:
1. **Guards ignore a monster the player struck first** (finding 1, corrected 2026-10-16). Monsters chased bots into town, bots called the guards five times inside the town region, no guard came, and gazers killed bots on the healer's doorstep. The bots had always struck first; stock guards do kill a monster that attacks a player unprovoked.
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

1. **Monsters chase new players into Britain and the guards do nothing.** Bots that fled into town shouted "guards" six times. Five of the calls were inside Britain's town region (from `Data/regions.json`): an ettin at 1377,1752, a named monster (Oogorim) twice, and a troll twice (once at 1428,1590, near the Carpenter). No guard came, and the monster stayed. Gazers killed two bots inside the town region, one on the healer's doorstep (1470,1619). During the untouched hour, gazers roamed central Britain: they were seen at 1642,1590, 1658,1574, 1456,1696 and 1446,1709. Two more "guards" calls against them (00:52 and 00:54) brought no guard, and a gazer killed a new tailor at 1462,1652, between the Tinker and the healer (00:55). *Corrected 2026-10-16:* `GuardedRegion.IsGuardCandidate` accepts only criminals and murderers, but a monster that hurts a player who had not struck it becomes a criminal (`Mobile.IsHarmfulCriminal`), so a "guards" call kills it (the owner's own test; about 8 s in the bot farm helper's test). The guards ignored these monsters because the bots struck first, which makes the monster's hits self-defence. The earlier reading here, that monsters are never guard targets, was wrong. Levers: guards (or a town-guard spawner) that act on hostile monsters inside the guarded region; or, at least, a line in the guide that the guards protect against people, not monsters.
2. **A ghost in peace mode is invisible to the healer, and standing beside the healer does nothing.** A living mobile sees a ghost only in war mode (`Mobile.CanSee`), and the healer offers resurrection only when a ghost walks *into* range. Three bots, in three professions, stood beside the healer and were never offered. *Confirmed in code;* the bots now switch war mode on before reaching the healer, so they no longer show it. Already on `To-Do-List.md` at the owner's request.
3. **After resurrection, the starting weapon and armour are in the backpack, not worn.** 16 bots, 10 professions. Nothing reminds the player, and a character that forgets fights barehanded. *Seen.* Lever: a one-time tip after the first resurrection (the shard's `newPlayerTips` system would fit).
4. **Undead and orc camps lie within a short walk of Britain.** Shades, wraiths, spectres and zombies by the graveyard north-west of town (about 1300-1400, 1410-1520), and orcs and ratmen to the north and north-east (about 1360,1414 and 1627,1411). They killed bots of every fighting profession, and every melee bot that fought a shade died. Named orcs and ratmen ("Tekchichak", "Oogorim") follow a new character a long way. *Seen,* 20 bots. Lever: beginner spawns (rabbits, deer, wolves, mongbats, slimes) in a ring round Britain, with the undead kept further out. See tuning note 9.
5. **New characters run out of stamina.** *On the owner's to-do list (2026-10-15: "running out of stamina is an issue").* Running costs a point every 16 steps, and an extra point per step below 10% (`StaminaSystem`). At 0 a character cannot run, and stamina returns at about a point every 7 seconds. A new character's maximum stamina is its Dexterity, often about 33. Bots that ran 150 to 300 tiles to hunting ground arrived at stamina 1, could not run from a monster, and had to stand and rest; one mage died out of breath. The bots made it worse by always running (their walking command did); the next client build walks them while their stamina is below half. *Confirmed in code and in game.* In numbers (2026-10-15, To-Do-List): above 10%, running at full speed is a net loss of about 10 points a minute (a bot lost 1 to 2 over 130 tiles); below 10%, each running step costs an extra point (17 times the rate), so the last 10% is gone in under a second. The larger drain is being hit while hurt: a 12-point hit costs 1 stamina at 60 hit points and 19 at 15 (`FatigueOnDamage`). Levers are in `To-Do-List.md`: a first-time tip, cheaper running or faster regeneration for new characters, or guide lines.

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
24. **Coloured ingots are called "iron ingot".** (2026-10-15, 07:10) A smith that mined and smelted dull copper ore carried 8 dull copper ingots (hue 0x973) beside 52 plain iron ones, and both stacks read "iron ingot". Targeting the dull copper stack with the tongs selects it as the metal, dull copper needs Blacksmithy 65, and the T2A smithing menu then offers only "Repair" and "Smelt", with no word on why (`T2A/BlacksmithMenu.cs` filters every build by the selected metal). Two smith bots looped on that menu for hours. *Confirmed in game.* A new smith who digs its own ore would meet the same silent menu. Lever: a tooltip or single-click name that says the metal ("dull copper ingot"), or a line when the menu has nothing to build ("You lack the skill to work this metal.").
25. **"All release" releases nothing until a confirmation window is answered.** Saying "all release" (or "<name> release") opens "Are you sure you want to release your pet?" for each pet (`ConfirmReleaseGump`); nothing happens until CONTINUE is pressed. Stock behaviour, and sensible, but every bot release tonight silently failed because the window went unanswered. *Confirmed in code.* Worth a line in the Welcome guide's pet page, not a change.
26. **The banker says the balance aloud.** "Thy current bank balance is N gold" is spoken by the banker over its own head, so everyone at the bank sees everyone's balance: bots logged each other's balances all night. Stock UO behaviour. *Confirmed in game.* A privacy question for the owner: players of the era accepted it, but a crowded single bank (the shard concentrates players in Britain) makes it more visible.
27. **A character can be wedged on the lake shore south of Britain.** BotFisherA stood at 1447,1768 for twelve minutes; every step in all eight directions was refused. A player can leave with Help > "I'm stuck" (the shard allows it for ordinary players), which the bots cannot press yet. *Seen once.* Worth checking that tile in the real client.
28. **A crafted crate with its key inside cannot be sold, and nothing says why.** A carpenter with a little Tinkering (15 is enough) makes boxes and crates lockable, with a copper key inside ("Your tinker skill was sufficient to make the item lockable", `LockableContainer.OnCraft`), and a vendor never lists a container that holds anything (`BaseVendor.VendorSell`). The Carpenter does buy crates and boxes, but BotCarpB's 27 never appeared on its sell list. *Confirmed in code and in game* (found by the watcher, 07:55). A new carpenter would think the Carpenter does not buy them. Lever: a line when a container is left off the list for being full, or a tooltip "contains 1 item".
29. **No vendor buys a surcoat or a body sash.** Tailors can make both, and no stock vendor's buy list has them (the watcher's list of what vendors will not buy, `work/botfarm-watch/vendor-wont-buy.md`). *Confirmed in code.* A tailor who makes them can only wear them, give them away or drop them. Lever: add them to the Tailor's buy list (crafted-goods pricing would price them).

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

## Answered by the new-player pass (2026-10-15, source only, not deployed)
Findings 3 (gear after resurrection), 10 (raw ore), 14 (tool wear warning) and 25 (releasing a pet) now have a guide line, tip or notice: see row 49 of `New-Player-Pass-2026-10-13.md`. Everything else in this report is still open (guards in Britain, dummies capped at 25, crafting item guidance, the Bowyer's list, stamina, the rest).

Finding 1 (guards ignore monsters in Britain), 2026-10-15: guard behavior left as stock. Two online searches for 1999-2000 evidence that classic guards attacked monsters inside town found nothing either way, so no rule change was made (the owner expects era facts checked online). The first-hour guide page was corrected instead: it said "Guards protect the towns"; it now says a monster that follows you into town is not stopped by the guards, who act only against criminals and murderers (shout guards to call them on one). Source only, not deployed; shard suite 1,527 pass; not re-checked in the real client (same page type as the pages checked in row 49). A guard that engages monsters in town stays an owner decision.

Finding 6 (training dummies), 2026-10-15: the 25-skill cap is stock and consistent with templates that start at 50 (era-style), so it is not changed. The Britain map markers now say what the dummies are good for: "Training dummies (fighting skills up to 25)" (was "practise fighting skills"); regenerated `data/client/UORekindled-Britain.csv` with `tools/map-markers/make_britain_markers.py` and copied it to `ClassicUO/bin/dist/Data/Client/` (a plain data file, read at client start, so running clients are unaffected until restarted). Label text only; the marker mechanism was checked in the real client earlier, this new wording was not re-viewed. The Skill Guide already says "From 0 to 25".

Finding 22 (Bowyer's "Arrow Fletching"), 2026-10-15: crafting tools now say what they are on hover ("A tool: double-click it to open its crafting menu."; the fletcher's tools: "A tool, not ammunition: double-click it to make arrows, bolts and bows."), (seen on a sewing kit in the pack; the shop list uses the same tooltip path but the Bowyer's list was not viewed) (`ItemTooltipService`, `ToolLine`, `case BaseTool`). The tool's uses left are wear and stay off the tooltip. The shop's list name itself is unchanged. Checked in the real client on a sewing kit in the pack; shard suite 1,528 pass; source only, not deployed.

Finding 8 (which crafted items still teach), 2026-10-15: the Crafting guide page has a new "Choosing what to make to train" paragraph: click the small ? beside an item to see the skill it needs and your chance of making it; crafting trains most on items you are not sure to make, so an item you almost always make teaches very little. Grounded in the code (the item window draws the success chance, `CraftGumpItem.DrawSkill`; the craft skill check feeds `CheckSkill` with the item's skill range, and stock skill gain favours the less certain). Text only, shard suite 1,533 pass, same page type as those checked in row 49 of `New-Player-Pass-2026-10-13.md` but this paragraph was not viewed in the real client; source only, not deployed. A list that marks "still teaches" items directly in the craft menu would need a change to the stock craft gump and stays the owner's call.

Finding 15 (mining repeats until overloaded), 2026-10-15: the gathering repeat (`HarvestRepeatService`, flag `harvestAutoRepeat`, already on) now stops when the character reaches the carrying limit and says "You are carrying as much as you can without being overloaded, so you stop gathering. Sell or put some away, then start again." The check runs when the loop would start its next attempt, for ordinary players only (`ShouldStopForWeight`: carried weight at or over `StaminaSystem.GetMaxWeight`). The Gathering guide page names the new stop. Unit-tested (shard suite 1,539 pass); not seen live (it needs a character mining up to its limit); source only, not deployed. Finding 17 (looting past the limit) is unchanged: the engine's lift has no weight check and dropping still works.

Finding 1, 2026-10-16 (correction and owner ruling): the 2026-10-15 guide line built on the wrong reading ("a monster that follows you in is not stopped by the guards") was replaced. The owner then ruled that guards kill monsters in town whoever struck first, on their own, and that guard zones shrink where no vendor stands so that no monster spawns inside one. Built behind `townGuardsKillMonsters` (off, not deployed, held for the owner's batch test): `Town-Guards-Monsters-Evidence.md`.


## Owner rulings and batch test, 2026-10-17 (QoL items 11-20 of the real-player recap)

All new flags are **off** in source and were on only in the disposable host `work/hosts/batch`. Nothing is committed or deployed. Drivers: `work/batch-test/s12*-s15*.py`. Images: `images/batch-test-2026-10-17/item*.png`. All are real-client shots.

| Recap item | Ruling | Built | Batch test |
| --- | --- | --- | --- |
| 11 Training dummies stop at 25 | Leave as is | none | n/a |
| 12-13 Healing, Meditation | Fast starts, Meditation tip, Meditate button | see `Fast-Healing-Evidence.md` | Passed (earlier the same day) |
| 14 Prey near town that teaches at 50 | Test it | none | A 50-Swordsmanship fighter rose to 56.3 in 4 minutes on giant rats and ratmen (temporary staff spawners). The batch host, like the dev world, lacks the beginner spawners until `[Alpha2bWorldGen addspawners` is run. |
| 15 Raw ore can't be sold | Make sure the ore page says so | `data/help/items.json`: "no shop buys ore: smelt it and sell the ingots to a blacksmith" | The About page shows it (`item15-ore-about.png`) |
| 16 Coloured ingots, silent smithing menu (finding 24) | Say why, name the skill | `metalSkillNotice`, engine event `BlacksmithMenu.MetalBeyondSkill`. Also a fix under the live `itemTooltips` flag: coloured ingots and ore add "Metal: <name>" to their tooltip, since stock's metal line was dropped | Blacksmithy 30 with dull copper: "You need Blacksmithy 65 to work dull copper. Target iron ingots to make things now." Hover before and after: "20 Ingots" became "20 Ingots / Metal: Dull Copper" |
| 17 A crafted crate holding its key won't sell (finding 28) | Sell it, key and all | `sellCratesWithKeys`, engine hook `BaseVendor.ContainerSellsAsEmpty` | A crate holding only its own key sells to the Carpenter for 20; one also holding a shirt does not |
| 18 No buyer at all (finding 29, the watcher's list) | Crafted goods, all; plus bone armour, feathers, big fish | `extraVendorBuyers`, the lists in `shard-rules.json` `extraVendorBuyers` | Surcoat 35 and body sash 10 (Tailor, Weaver); Heal 18, Greater Heal 33, Cure 18, Explosion 25 (Alchemist); writing table 43 (Carpenter); globe, spyglass and candelabra 25 (Tinker Guildmaster); bone armour (Armorer, Blacksmith; the Tailor too, since bone armour is a tailoring recipe); feathers and shafts 1 (Bowyer); big fish 10 (Fisherman) |
| 19 Shops don't say what they sell | Leave as is | none | n/a |
| 20 Fletcher's tools read "Arrow Fletching" | The tooltip is enough | Tooltip already in source (`itemTooltips`), not yet deployed | n/a |

**Found in testing:**
- **House-addon deeds** (beds, forges, looms and the like; 33 of the 40 carpentry items with no buyer) are **newbied** in the pre-AOS era (`BaseAddonDeed`). No vendor buys a newbied item, so they still won't sell even with a buyer listed. This needs an owner ruling.
- **The runebook** is blessed, so it can't be sold either (stock).
- **A load-order bug, fixed before the test:** vendors load with the world, before the craft systems exist, so `extraVendorBuyers` now builds a vendor's extra list the first time a player sells to it.

**House-addon deeds, ruled the same day.**
- **Ruling:** "Stop newbie-ing deeds". This is flag `ordinaryAddonDeeds` (off), using the engine hook `BaseAddonDeed.NewbiedBeforeAos`. A deed made while the flag is on is an ordinary item; deeds made before keep their newbied state.
- **Live check:** a new loom (east) deed sold to the Carpenter for 275 gold. Unit tests pass (run `20261017T233635663Z-e1802d`: shard 1,671, UOContent 1,404).
- **Item 21** (tools sell back at about half): left as is.

**Buy-to-resell check (2026-10-17, from the stock SBInfo lists).**
- **Stock lists:** 302 item types are both sold and bought by some vendor. Six pairs pay at least the charge.
  - Arrows, beeswax and cookies pay exactly what they cost, so there is no profit.
  - The wizard's hat (Provisioner 11 to Mage 15), the black staff and the wooden shield are crafted goods. Crafted-goods pricing raises their charge to 1.5 times its pay floor, so they don't pay either. The black staff and wooden shield pairs also need the Stone Crafter, who isn't in Britain.
- **The new buys:** two of them overlap a vendor's stock, the heating stand (Alchemist 2) and the key ring (Tinker 8). Both are tinkering recipes, so crafted-goods pricing raises those vendors' charges above what the new buyer pays.
- **Result:** no profitable loop among Britain's shops while `craftedGoodsPricing` is on.
- **Caveat:** these are static checks. An automated audit test would keep it so.

**Buy-to-resell audit (owner's choice, 2026-10-17).**
- **The test:** `tests/VendorResaleAuditTests.cs` reads every stock shop list with crafted-goods pricing applied, adds the extra buyers from the source config, and fails if any vendor pays more than another charges.
- **What its first run caught** (both fixed):
  - The Scribe would have paid 14-18 for first-circle spell scrolls, which the Holy Mage sells for 12. `extraVendorBuyers` now adds a buyer only for items **no** stock vendor buys anywhere, which was the original finding.
  - A stock quirk: the Stone Crafter pays 24 for the Blacksmith's 22-gold black staff. The Stone Crafter and the Holy Mage never spawn in this world, so the test names their shop lists as not in this world.
- **Result:** run `20261017T235406065Z-4df521`, shard 1,672 passed, no loops.
- **Not re-run live:** the earlier sell lists (surcoat, potions, writing table, tinker goods, loot) are all items no stock vendor buys, so they are unchanged by the narrower rule.
