# Bot farm: what new players run into (night of 2026-10-14)

Fifty headless bots played the shard unattended on the disposable farm host (`work/hosts/farm`, a copy of the dev distribution), for about four hours on the main roster and up to an hour on the newest. They covered 16 professions and the Advanced template: archer, bard, ranger, mage, warlock, sorcerer, mace fighter, fencer, swordsman, blacksmith, carpenter, tailor, tinker, tamer, fisherman and prospector. "Veteran" bots know the monster, craft and taming tables, while "newbie" bots go only by what a new player can see and learn from what happens to them. They share what they learn per profession. A second session watched their logs all night and reported what went wrong.

This report keeps only what a player would meet. Each entry says how many bots and professions hit it, how it was confirmed, and the levers I can see. Nothing here has been changed on the dev world. The economy details (prices, stock, material supply) are in `Bot-Farm-Tuning-Notes.md`.

How sure each finding is:
- **Confirmed:** seen in game by several bots *and* found in the server code.
- **Seen:** seen in game by the bots. Check it in the real client before acting on it.
- Bot-only artifacts (the headless client lacks the tooltips and bars, or the brain made a mistake) are listed at the end, so nobody acts on them.

## 1. Danger and death

1. **Monsters chase new players into Britain and the guards do nothing.** Bots that fled into town shouted "guards" six times. Five of the calls were inside Britain's town region: an ettin at 1377,1752, a named monster (Oogorim) twice, and a troll twice (once at 1428,1590, near the Carpenter). No guard came, and the monster stayed. Gazers killed two bots inside Britain, one on the healer's doorstep (1470,1619). *Confirmed:* `GuardedRegion.IsGuardCandidate` only accepts criminals and murderers, so an ordinary monster is never a guard target. Levers: guards (or a town-guard spawner) that act on hostile monsters inside the guarded region; or, at least, a line in the guide that the guards protect against people, not monsters.
2. **A ghost in peace mode is invisible to the healer.** 18 bots, 12 professions. The healer only offers resurrection to a ghost it can see, and a living mobile sees a ghost only in war mode (`Mobile.CanSee`). The healer also offers only when a ghost walks *into* range, so standing beside it does nothing. *Confirmed; already on `To-Do-List.md` at the owner's request.*
3. **After resurrection, the starting weapon and armour are in the backpack, not worn.** 16 bots, 10 professions. Nothing reminds the player, and a character that forgets fights barehanded. *Seen.* Lever: a one-time tip after the first resurrection (the shard's `newPlayerTips` system would fit).
4. **Undead and orc camps lie within a short walk of Britain.** Shades, wraiths, spectres and zombies by the graveyard north-west of town (about 1300-1400, 1410-1520), and orcs and ratmen to the north and north-east (about 1360,1414 and 1627,1411). They killed bots of every fighting profession; every melee bot that fought a shade died. Named orcs and ratmen ("Tekchichak", "Oogorim") follow a new character and cannot be outrun. *Seen,* 20 bots. Lever: beginner spawns (rabbits, deer, wolves, mongbats, slimes) in a ring round Britain, with the undead kept further out. See tuning note 9.
5. **Running drains stamina, and nothing says so.** 22 bots, 6 professions. Running to hunting ground 150 to 300 tiles out left bots at stamina 1 of 33, unable to fight or flee. Two mages died that way. Stamina returns at about a point every 7 seconds. *Confirmed* (`StaminaSystem`: running costs a point every few steps, more below a third, and you cannot run at 0). Lever: a guide line, "walk the last stretch, or rest before a fight".

## 2. Learning a skill

6. **Training dummies and the archery butte cannot train any new character's main skill.** 12 melee bots and 9 archery bots. Every try at 50 skill says "Your skill in this weapon cannot improve any further by simply practicing with a dummy". *Confirmed:* `TrainingDummies.cs` MaxSkill is 25, and every template starts its main skills at 50 (Advanced characters at about 30-35). The map still marks five dummies and a butte as places to practise. Lever: raise the limit (for example to 50 or 60), or change the markers' wording.
7. **Bandages barely help anyone without Healing.** 7 bots in 5 professions. At Healing near 0, a bandage takes about 14 seconds and heals about 1 hit point ("they barely help"), yet every template starts with 50. *Confirmed.* Lever: a guide line, or fewer bandages for non-healers.
8. **Nothing says which crafted items still teach.** The craft menu lists what a character can make, never how hard it is. The newbie tailor made over 80 shirts, caps and sashes at Tailoring 54.5 and gained nothing in 34 minutes: those items are too easy, and they kept coming out "exceptional". A veteran tailor picked a cloak from the skill table and gained. *Seen,* 13 crafting bots. Lever: one line in the Skill Guide's craft pages, "when your work keeps coming out exceptional, it has nothing left to teach you: make something harder".
9. **A new mage runs dry fast.** Mana is gone after about nine spells, and Meditation is the only quick way back, which a new mage is not told about. Starting reagents do not last one hunt ("More reagents are needed for this spell"). *Seen,* 9 caster bots. Lever: the Skill Guide's Magery page could name Meditation and the reagent shop.

## 3. Money, shops and material

10. **No NPC buys raw ore.** A full pack of ore sold for 0 gold all evening. A Blacksmith buys iron ingots (4 gold), so ore has to be smelted at a forge first. *Confirmed; this is the era's rule.* Once taught to smelt, the miner turned 19 ore into 27 ingots and sold them for 44 gold. Lever: one guide line, "smelt ore at a forge before you sell it".
11. **Nobody in Britain buys hides.** Cows drop them, and every fighter that kills a cow fills its pack with them. No Tanner or Leatherworker appears among Britain's map markers, and only a Leatherworker buys hides (2 gold) or a Tanner leather (5). *Seen.* Lever: a Tanner in Britain, or the guide says where hides sell and that scissors turn them into leather.
12. **Shops do not sell what their names suggest, and two vendors often share one.** The Tinker sells no hatchets (the Weaponsmith does) and no boards (the Carpenter does, and they were sold out all night). The Tailor sells "Cloth" and bolts, the Weaver next to it sells "Folded Cloth"; neither says "cut cloth", the name the craft uses. The Armorer and the Weaponsmith share a shop. *Seen.* Lever: the map markers or the guide could say who sells each material and tool.
13. **Crafting material runs out.** A Blacksmith stocks 16 ingots, and three crafters empty every shelf in Britain. Stock ModernUO doubles a sold-out shelf at the hourly restock, so it eases within hours, but a new crafter just finds nothing to buy. *Confirmed.* Details and levers: tuning note 3.
14. **Crafting at starting skill loses money at stock prices.** *Addressed on the farm host only* by the crafted-goods pricing (`Crafted-Goods-Pricing.md`, not on dev yet). With it, crafters earned about 140 gold an hour each (a chair 38, a cutlass 50, a cloak 53). Tools stay at stock prices, so a Tinker training on tools still loses about half its material each time.
15. **Tools wear out with no warning.** Tongs lasted about 24 crafts, a tool kit about a dozen, a pickaxe under ten minutes, each ending with "You have worn out your tool!" and nothing before. *Seen* in every crafting and mining bot. The shard's wear notice covers weapons, shields and armour, not tools. Lever: the same quarter-left warning for tools.

## 4. Gathering and taming

16. **Penned and wandering animals look tameable but cannot be reached.** Tamers chased cows and sheep inside fences, and wild animals that kept moving, for minutes without getting within the two tiles taming needs. Nothing says the animal is out of reach. *Seen.* The first real attempt of the night was "Target cannot be seen" (an animal on another floor).
17. **Fishing spots run out, and the message does not say how far to move.** "The fish don't seem to be biting here" after a few minutes on one patch. *Seen,* probably intended.
18. **Mining repeats until the pack is overloaded.** The shard's harvest repeat keeps digging while the pack gets heavier, with nothing to stop it short of the weight limit. *Seen,* 7 bots. Lever: stop the repeat near the weight limit, with a line saying why.
19. **Looting goes past the weight limit.** An archer picked up loot until it carried 200 of 180 stones. *Seen.* Overloaded, it then could not drop anything, but that part is **not** confirmed: the engine's `Mobile.Lift` has no weight check, so it may be only how the bot drops. Needs a real-client test (tuning note 17).

## 5. Messages

20. **A spell at a target behind a wall, or on another floor, is lost with no message.** No fizzle, no mana spent, no hint. *Seen,* 12 caster and archer bots. Lever: a "You cannot see that" message, as stock sends elsewhere.
21. **Selling crafted goods to one vendor (Aithne) sometimes paid nothing and said nothing.** *Seen,* cause not found (tuning note 2).

## Newbie against veteran

Newbie bots have no tables, so they learn by dying and by trying. The early gaps show what the game does not tell a player:
- **Deaths:** newbies died at camps veterans avoid. BotBardB was killed four times by the same named ratman (Tekchichak), three times on the same spot, before it learned.
- **Crafting:** a newbie tailor never found which items teach (finding 8).
- **Tamers:** a newbie tamer tried a rat, which can teach nothing at 54 Animal Taming.

A fair comparison is running now: three pairs of brand-new characters (Swordsman, Tailor, Archer), one veteran brain and one newbie brain each, started together at about 23:37. The watcher measures them at 00:38 and 01:38, and the results will be added here.

## Bot-only artifacts (not player problems)

- "The Heal potion can only be told by its colour" (29 bots). The headless client names items from tile data, so it sees "Yellow Potion". A player's client shows the server's name, and the shard's item tooltips and potion bar cover it.
- "Ran out of arrows with no warning". The shard's combat bar shows ammunition, but the headless bots do not draw it.
- "Saying '<name> buy' opened no list" and "Smelting gave nothing": bot timing and target mistakes, fixed tonight.

## Where the evidence is

- `work/botfarm/report.md`: every finding with the bots that hit it (`farmctl.py report`).
- `work/botfarm/evaluation.md`: how the bots' decisions paid off (`farmctl.py eval`).
- `docs/Bot-Farm-Tuning-Notes.md`: the shard-side economy and world notes this report draws on.
- The bot code and its operating guide: `tests/scenarios/bot-farm/` (`OPERATING.md`).
