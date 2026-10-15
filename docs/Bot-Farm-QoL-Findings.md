# Bot farm: what new players run into (night of 2026-10-14)

Fifty headless bots played the shard unattended on the disposable farm host (`work/hosts/farm`, a copy of the dev distribution), for about four hours on the main roster and up to an hour on the newest. They covered 16 professions and the Advanced template: archer, bard, ranger, mage, warlock, sorcerer, mace fighter, fencer, swordsman, blacksmith, carpenter, tailor, tinker, tamer, fisherman and prospector. "Veteran" bots know the monster, craft and taming tables, while "newbie" bots go only by what a new player can see and learn from what happens to them. They share what they learn per profession. A second session watched their logs all night, reported what went wrong, and reviewed this report against the logs (its corrections are folded in).

This report keeps only what a player would meet. Each entry says how many bots and professions hit it, how it was confirmed, and the levers I can see. Nothing here has been changed on the dev world. The economy details (prices, stock, material supply) are in `Bot-Farm-Tuning-Notes.md`.

How sure each finding is:
- **Confirmed:** seen in game by several bots *and* found in the server code.
- **Seen:** seen in game by the bots. Check it in the real client before acting on it.
- **Candidate:** seen once or twice, or only inferred. Worth a check, not yet a finding.
- Bot-only artifacts (the headless client lacks the tooltips and bars, or the brain made a mistake) are listed at the end, so nobody acts on them.

Counts are distinct bots that logged the matching line. Brains restarted many times tonight as they were fixed, so anything counted per brain run (tool lifetimes, gold per hour) is rough.

## 1. Danger and death

1. **Monsters chase new players into Britain and the guards do nothing.** Bots that fled into town shouted "guards" six times. Five of the calls were inside Britain's town region (from `Data/regions.json`): an ettin at 1377,1752, a named monster (Oogorim) twice, and a troll twice (once at 1428,1590, near the Carpenter). No guard came, and the monster stayed. Gazers killed two bots inside the town region, one on the healer's doorstep (1470,1619). *Confirmed:* `GuardedRegion.IsGuardCandidate` only accepts criminals and murderers, so an ordinary monster is never a guard target. Levers: guards (or a town-guard spawner) that act on hostile monsters inside the guarded region; or, at least, a line in the guide that the guards protect against people, not monsters.
2. **A ghost in peace mode is invisible to the healer, and standing beside the healer does nothing.** A living mobile sees a ghost only in war mode (`Mobile.CanSee`), and the healer offers resurrection only when a ghost walks *into* range. Three bots, in three professions, stood beside the healer and were never offered. *Confirmed in code;* the bots now switch war mode on before reaching the healer, so they no longer show it. Already on `To-Do-List.md` at the owner's request.
3. **After resurrection, the starting weapon and armour are in the backpack, not worn.** 16 bots, 10 professions. Nothing reminds the player, and a character that forgets fights barehanded. *Seen.* Lever: a one-time tip after the first resurrection (the shard's `newPlayerTips` system would fit).
4. **Undead and orc camps lie within a short walk of Britain.** Shades, wraiths, spectres and zombies by the graveyard north-west of town (about 1300-1400, 1410-1520), and orcs and ratmen to the north and north-east (about 1360,1414 and 1627,1411). They killed bots of every fighting profession, and every melee bot that fought a shade died. Named orcs and ratmen ("Tekchichak", "Oogorim") follow a new character a long way. *Seen,* 20 bots. Lever: beginner spawns (rabbits, deer, wolves, mongbats, slimes) in a ring round Britain, with the undead kept further out. See tuning note 9.
5. **Long runs leave a character out of breath.** Running costs stamina (`StaminaSystem`: a point every few steps, more below a third, and no running at 0), and stamina returns at about a point every 7 seconds. Bots that ran 150 to 300 tiles to hunting ground arrived at stamina 1 of 33. *Seen,* but inflated by the bots: their walking command always runs, which a player would not do for 300 tiles, and the status bar does show stamina. One mage death fits it (a brown bear, BotMageAdv). Lever: a guide line at most ("walk the last stretch, or rest before a fight").

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
17. **Looting goes past the weight limit.** An archer picked up loot (boards, mostly) until it carried 200 of 180 stones. *Seen.* Overloaded, it then could not drop anything, but that part is **not** confirmed: the engine's `Mobile.Lift` has no weight check, so it may be only how the bot drops. Needs a real-client test (tuning note 17).

## 5. Candidates (worth a check, not yet findings)

18. **Healing yourself while poisoned only says "You cannot heal yourself in your current state."** It never says that the character is poisoned and needs a cure. Seen once (BotWarlockA, 22:04). It bears on the poison relief hints. The bots only started recording overhead messages to themselves late tonight, so more such lines will show up in the next run.
19. **A criminal ghost is refused by the healer** ("Thou art a criminal. I shall not resurrect thee.") with no word on how long to wait. Three bots, around 20:53. Their criminal flag came from a bot looting fault, so it says nothing yet about how often a real player meets it.
20. **Tamers could not reach penned or wandering animals.** They chased animals for minutes without getting within the two tiles taming needs. The bots never tried the skill from range, so whether the game says "That is too far away" is untested.
21. **No Tanner or Leatherworker appears among Britain's map markers.** Hides come only from carving a corpse, which the bots never do, so no bot met this. A player who carves would find no one in Britain to sell hides to.

## Newbie against veteran

Newbie bots have no tables, so they learn by dying and by trying. Tonight's early gaps:
- **Crafting:** a newbie tailor never found which items teach (finding 8).
- **Tamers:** a newbie tamer tried a rat, which can teach nothing at 54 Animal Taming.
- **Deaths:** BotBardB was killed four times by the same named ratman (Tekchichak). Most of that came from bot faults (it walked back for its corpse into the camp, and kept war mode on after resurrection), fixed tonight, so it overstates what a new player would suffer.

A fair comparison is running: three pairs of brand-new characters (Swordsman, Tailor, Archer), one veteran brain and one newbie brain each, started together at about 23:37. The watcher measures them at 00:38 and 01:38, and the results will be added here.

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
