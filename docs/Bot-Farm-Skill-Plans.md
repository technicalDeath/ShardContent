# Bot skill plans: a full 700-point set per bot type (2026-11-01)

**Owner, 2026-11-01:** "Do a pass at giving each bot type a full set of skills to fill out their 700 points that will help them in their goals, and give them the behavior and logic to use them." His example: "A tamer could use their pets to hunt, and hunt themselves with a weapon, so them plus pets hunt to get gold."

## Where the bots stand

Measured from each bot's skill list.
- **Base totals** are 280-490 of 700. The display values look higher because they include stat bonuses.
- **Room:** every bot has 200-400 points free.
- **Locks:** no bot has ever changed a lock (all are "up").
- **Drift:** points went into whatever the bot happened to use: Camping and Cooking on fighters, Wrestling on archers, Meditation almost everywhere.
- **The real gap is behaviour.** The bots use two or three skills.

## Era rules the plans follow

Research report, with sources: the official publish notes (Publish 1, 4 and 5), Stratics, UOSA and Lost Lands.
- **Skill locks** (up / down / locked) arrived in Publish 1 (1999), with the 700 cap.
  - A skill set down loses points only while another one gains past the cap.
- **Publish 5 (UOR, April 2000):** damage done by tamed or provoked creatures counts toward the tamer's or bard's loot rights.
- **Veterinary** heals a pet with bandages (there is no bonding or pet resurrection in UOR).
- **Healing** cures poison at 60 Healing / 60 Anatomy.
- **This engine, from code:**
  - Lumberjacking adds up to +20% damage with axes (`BaseWeapon`, `Core.UOR`).
  - Arms Lore gives crafted gear nothing before ML, so no plan uses it.
- **Not used (AOS or later):** Chivalry, Necromancy, Bushido, Focus, power scrolls, Discordance.

## The plans (7 skills at 100 = 700)

Mechanics: `skillplan.py`, feature `skill_plan`. Every 30 minutes the bot reads its skills and sets each lock: up below the target, locked at it, down for everything else. A skill set down only falls while another rises past the cap.

| Type | Skills | Era source | New behaviour needed |
| --- | --- | --- | --- |
| Animal Tamer | Animal Taming, Animal Lore, Veterinary, Archery, Tactics, Anatomy, Healing | Stratics tamer-archer, without its 8th skill (Magery) | **shoot the pet's target with a bow**; Veterinary on a hurt pet; self-Healing exists |
| Ranger | Archery, Tactics, Anatomy, Healing, Animal Taming, Tracking, Hiding | composite ranger (Archery core, Taming, Tracking, Hiding) | Hiding to escape |
| Archer | Archery, Tactics, Anatomy, Healing, Resisting Spells, Bowcraft/Fletching, Lumberjacking | light warrior, with fletching in place of Magery | fletch its own arrows from its own logs (the Bowyer's arrows sold out for hours) |
| Swordsman, Mace Fighter, Fencer | weapon, Tactics, Anatomy, Healing, Parrying, Resisting Spells, Hiding | UOSA dexxer core (Tactics, Anatomy, Healing, Resist) with Parry and Hiding | Hiding to escape |
| Bard | Musicianship, Provocation, Peacemaking, Archery, Tactics, Anatomy, Healing | composite bard-archer | provoke for loot rights (Publish 5) |
| Pure Mage | Magery, Evaluating Intelligence, Meditation, Resisting Spells, Wrestling, Tactics, Anatomy | tank-mage core | none: the casters already use these |
| Sorcerer | Magery, Evaluating Intelligence, Meditation, Inscription, Resisting Spells, Wrestling, Anatomy | Stratics pure mage with Inscription | none (`scribe.py`) |
| Warlock | Magery, Evaluating Intelligence, Meditation, Resisting Spells, Fencing, Tactics, Anatomy | UOSA tank mage | none |
| Prospector | Mining, Blacksmithy, Tinkering, Hiding, Healing, Anatomy, Wrestling | Stratics miner (Tinkering for its own shovels) + Hiding | **make its own tools** (Tinkering); Hiding; self-Healing |
| Blacksmith | Blacksmithy, Mining, Tinkering, Hiding, Healing, Anatomy, Wrestling | Lost Lands smith-miner core | make its own tongs and hammers; Hiding; Healing |
| Tinker | Tinkering, Mining, Lumberjacking, Carpentry, Hiding, Healing, Anatomy | Lost Lands tinker-smith core | Hiding; Healing |
| Carpenter | Carpentry, Lumberjacking, Swordsmanship, Tactics, Anatomy, Healing, Hiding | lumberjack-warrior (axe +20% from Lumberjacking) | fight with its axe; Healing |
| Tailor | Tailoring, Swordsmanship, Tactics, Anatomy, Healing, Tracking, Hiding | hunter-tailor (its own hides) | find animals by Tracking; Healing |
| Fisherman | Fishing, Cooking, Wrestling, Tactics, Anatomy, Healing, Hiding | fisher, who must fight sea serpents (Publish 4) | Healing; Hiding |

Magery for Recall is left out of the non-casters. Every bot would need reagents, runes and a spellbook; that is a later step if the walking times show it pays.

## Build order: biggest gold first, one A/B at a time

1. **The plan and locks for every type** (`skill_plan`). This costs nothing at play time and stops future drift.
2. **Tamer: fight beside the pet.** Buy a bow and arrows, shoot what the pet fights, bandage the pet (Veterinary) and itself (Healing). It was at about 200 gold with no armour.
3. **Shared self-Healing for gatherers and crafters.** Bandage after a fight, as the fighters already do.
4. **Shared Hiding.** Hide when a threat closes and running is not possible; practise it when idle.
5. **Tools from Tinkering** for the miners and smiths.
6. **Fletching** for the archers.

Each step is gated (`farm_release.py --check`), run on a canary for 30 minutes, and measured in gold an hour and skill points.

## Status, 2026-11-01 13:25

| Step | State |
| --- | --- |
| 1. Plans and locks | **Live on all bots** since 13:11 (`skill_plan`; tree 2bcc717fe8af). Dead weight is locked down: Meditation and Wrestling on fighters, Discordance on bards, Fletching and Tinkering on a carpenter. Hiding is set up where the plan holds it. |
| 2. Tamer fights beside its pet | **Live on BotTamerAR** (`tamer_weapon`): buys a bow and arrows once it carries the gold (no shop walk without it), shoots the pet's target, and bandages the pet from Veterinary 0. Its pet hunt also works tier-2 areas the pet can hold, and when poor it looks for a stronger pet (a grizzly beats orcs, a brown bear does not). |
| 3. Self-Healing | **Live** for miners, fishers and crafters (`basics.r_heal`); bandages are bought from Healing 0 when the plan holds Healing. |
| 4. Hiding | **Live** for miners, fishers and crafters (`basics.r_hide`, practised when idle). Engine rules (`Hiding.cs`): it fails while a monster within (100 − skill)/2 + 8 tiles has the bot as its target, the chance is the skill, and the next try is 10 s later. |
| 5. Tools from Tinkering | Not built. It needs the crafters' Tinkering menu inside the gatherer brain, and the saving is a few gold a pickaxe. |
| 6. Fletching | **Already built** (`r_fletch`, `r_wood`), now on for all five archers. |
| Fighters' Hiding, the carpenter's axe, bard provocation for loot | Next. |

## Second pass, 2026-11-01 evening (owner: "faster and more meaningful progress ... using more skills")

Measured first: the plan skills that rose less than 0.3 in four hours while still under 80, by profession. The causes, and what changed:

| Stuck skill | Cause | Change |
| --- | --- | --- |
| Parrying (all nine melee fighters) | no shield: Parrying blocks and rises only with one | `shields.py` `r_shield`: a one-handed fighter buys the best shield it can afford with 300 gold to spare (heater 231 gold, armour 23; metal kite 123/16; wooden kite 70/12; buckler 50/7; SBBlacksmith, ArmorBase) and wears it. Two swordsmen bought heaters within ten minutes. |
| Provocation, Peacemaking (bards); Bowcraft/Fletching, Lumberjacking (archers) | the decision core (`task_core`) runs only the reflex rules, so `r_music`, `r_fletch` and `r_wood` never ran: no event in four hours | `BotBase.CORE_SKILL_RULES`: the core lets these (and `r_shield`) run; each has its own limits |
| Tailoring at 75-79 (all four tailors) | above 78.9 only leather items teach (`craft_data.json`), and the tailors worked only cloth; at 79.1 they made floppy hats at 100% | leather mode in `crafter.py`: hides from the Furtrader (3 gold) or Leatherworker (4), cut with scissors, leather and studded armour in the window, sold to the Tanner |
| Archery, Veterinary (tamer) | no bow: its bank walk was refused, and then it bought "Arrow Fletching" for arrows | a withdrawal for a purchase passes the long-walk rule; arrows are bought by exact name |
| Hiding, Healing (gatherers and crafters) | live since 13:23 and starting from 0 | practising; measured over the next runs |
| Resisting Spells | rises only when spells hit you | left alone |

## Third pass, 2026-11-01 18:30-19:00: what the owner saw, and the causes

| Seen | Cause (from the code, the logs and the engine) | Change |
| --- | --- | --- |
| Archers' wood chopping yields nothing (0 or 10 logs a visit) | the fighters chop in war mode, and the shard's gather repeat stops in war mode (`HarvestRepeatService.CheckCancel`, `StopReason.WarMode`): one swing a visit | `BotBase.harvest_peace` before every chop, dig and cast of a line |
| The tamer buys no arrows | every Bowyer near Britain is out of arrows (the archers buy them; the shared memory has qty 0 at all three), while the same shelf holds 38 bolts at 3 gold; and "arrow" found a mage's shop by its Magic Arrow scroll | a crossbow (55) and bolts when arrows are sold out at every shop known (Archery covers both); exact names in the shared memory (`memory.name_match`, "=arrow"); the purchase gaps survive a brain restart |
| BotTamerAR's brain killed every 15 minutes (16 times) | `stock.r_stock`: when the money covers a restock but the goal fund (`goals.idle_ok`) does not, the "part of it" cut set the same target and looped forever | a part only when it is smaller |
| BotMinerAR stood still at the mountain for 4 minutes | overloaded ("too fatigued to move"): the message is read only with the journal, and a far walk's three legs of step-outs read none | a step that moves nothing reads the journal and sheds weight where it stands |
| BotMinerAR never smiths | `smith_plan` passed `ev=` to `bot.ev`, which is `dlog`'s own key: TypeError on every plan | renamed `gain` |
| BotFenceAdvR does not carve | it fights with a pitchfork (a spear: no carving) and the carve finder took only a dagger, knife or cleaver from the pack; a sword or knife carves from the pack (`BaseSword` / `BaseKnife` OnDoubleClick, no equip check), and it carries a katana | any sword or knife in the pack carves |
| Archers and fighters circle the same few spots near town | every tour whose expected kills reach `EXPECT_CAP` (18 an hour) scores 18 × minutes/60 ÷ minutes = 0.3, so all capped tours tie and the safest or nearest wins; the per-spot records (0.01-1.6 kills a visit around Britain) never decide. The estimates (9-24 kills an hour before the cap) run 2-3 times the actual (about 6), and the calibration compares the actual over work hours with an estimate made over the whole tour, walk included | in the canary (`tour_rank`): tours ranked by the calibrated estimate before the cap; the calibration over the same hours |
| Fighters at 86-91 skill and 13,000-20,000 gold banked never go down to the dungeons | the dungeon kit (10 Heal, 2 Refresh, 15 Cure, 50 bandages) is bought only by the `ladder` cohort (four bots), so `rung_ready` is never true for the others | owner, 19:00: "all bots who are equipped and skilled enough should do dungeons": `ladder` is now all 20 decision-core bots (the kit rules unchanged); a sold-out shelf doubles its stock at the next hourly restock (`GenericBuyInfo.OnRestock`) |
| Both rangers threw a TypeError every 2 s from 18:29 | `rangerpet.py` (and `tamerarms.py`) passed `kind=` to `ev(kind, ...)`; two more calls (`measured_params`, `box_entered`) passed `rule=`, which `ev` sets itself, and were silently never written | renamed; new gate `test_ev_keywords` checks every `ev()` / `dlog()` call in the tree for such clashes |
| BotTailorBR died twice in 8 minutes, "killed by a great hart" | the killer was a wraith beside it (the damage line, a sure source), but the death code took the nearest threat in view (the hart, 8 tiles off), so it learned nothing; its house site at 1346,1432 lay 40-49 tiles from four undead spawners | a sure `deathsrc` source names the killer; no house site within an attack-on-sight spawner's home range + 32 (the engine's perception range 16, chased as far again; the spawner at 1304,1413, home 24, reached the site 18 past its edge); an idle crafter more than 40 tiles from a bank waits in town |
| BotFairTailorVR stepped away from a dog and back every 1.6 s (72 flips an hour) | `r_avoid` counted any non-prey creature, and a dog fights only its attacker ("Aggressor" in the engine's fight modes) | an animal that fights only its attacker is no danger unless it is fighting the bot (war mode, beside it); `r_avoid` now writes an `avoid` event naming what it avoids |
| Tour ranking (canary, then all fighters) | capped tours tied at 0.3 | two 30-minute canary reads: 21.6 and 20.5 kills an hour against 15.2 and 13.6 for the control; on for all 20 core fighters from 20:35 (fleet 17.8-18.1 kills an hour, gross gold 1,102 an hour against 658 at 19:33; no control left, so not separable from the other changes) |
| Fighters left hunts to buy arrows every few minutes (8 of 10 ammo errands bought nothing) | every Britain Bowyer out of arrows; when all were marked empty `ammo_shop` fell back to an empty one; and the shop lookup matched "arrow" inside "Magic Arrow", so four mage shops counted as arrow shops | no ammo errand while every shop is known empty and arrows are carried; a fletcher buys shafts and feathers at an empty shelf; exact ammunition names; the empty marks survive restarts |
| Hunts cut off after 7-9 minutes to bank or sell with packs 53-64% full | bank urgency reaches PRESSING at twice the 160-gold purse limit | a bank or sell need waits for 10 minutes of work (half the hunt budget) unless the pack is 90% full |
| Kit-seekers looped sell, bank and resupply | Britain's four Cure shelves held 10 each when 20 fighters wanted 15 | the kit aim waits an hour (`BaseVendor.RestockDelay`) when the shelves cannot fill it |
| Hunters stranded in town after an errand; a crafter's house trek on foot through troll country; a crash on a journey's gate leg | an arrived hunt never re-travelled; `housegoal` walked with a raw `goto_near`; `far_run` read `["to"]` from gate legs | an arrived hunt more than 120 tiles from its spots ends "displaced"; far sites by `far_goto` (moongates); the leg's `to`/`at`/`land`; house sites centred on Britain (the owner's hub) |
| A smith struck off 39 good items in 2.5 minutes | it crafted away from its anvil, and each "nomenu" struck the item | a far smithy by `far_goto`, no craft until there; a menu that never opened strikes nothing and rests a minute |
| A carpenter stood at the bank with no wood | its nearby trees were spent, and the first idle rule walked it to town | idle-in-town only from monster ground; a carpenter walks on to the next wood within 300 tiles |
| BotTailorBR's house deed refused at six surveyed sites ("not on valid terrain") | a deed places its centre at the target minus its Offset (`HouseDeed.OnPlacement`; every small house deed has Offset 0,4,0), and the bot targeted the surveyed centre itself at its own height: each house went 4 tiles north of its surveyed spot (the 21:11 placement landed at 1554,1252 by luck after 21 tries) | stand on the surveyed centre for its ground height and target centre + offset |
| Five gatherers boxed each other in at one dig spot north of Britain (one for 8.5 minutes) | a dig tile was claimed only at the first swing, so every bot walking there chose it | the spot is claimed when chosen (600 s, for the walk), and a spot within 3 tiles of another bot's claim is passed over |
| A crafter banked "heavy" four times in 12 minutes against a full bank box | each visit took products out to sell, and the refused craft marked the pack unsold, so it was heavy again | with the box known full, a heavy pack goes to the shops |
| Bards' Provocation (32.5 and 52.1) gained nothing in two hours | `r_music` provoked only with two prey within 8 tiles, which a bard hunting one animal at a time almost never has; with one prey it played Discordance, which the era plan locks down | provoke the prey onto any other creature in bard range (`BaseInstrument.GetBardRange`: 8 + Provocation/15), never Discordance; one creature and nothing to set it on: the bow |
| The carpenters' wood walk looped (several a second) | it walked to the tree's own tile, which is not walkable | walk beside the tree; a tree it cannot get nearer to is marked off; one wood walk a minute |
| Open risk: dungeon trips | no fighter has the full kit yet (21:50: 0 of 20; Cure 9-12 of 15, Refresh 0 for several); Britain's Cure shelves restock 10 an hour and double after each sell-out, so supply should overtake demand in 2-3 hours. The only dungeon trips so far (7, on 10-21, to Covetous and Wrong) mostly ended "unreachable" (5) or in a death (2): the walk to Covetous' approach (2422,882) stalled at 2453,896. Today's planner routes Britain to the Covetous entrance (1,151 steps); the live walk is unproven | watch the first trips |
| Crafters stopped crafting beside a cow or a warbler (40 skips an hour) | `threats()` counts a harmless animal in war mode within 2 tiles, and cows fighting another bot tripped it | the craft rule ignores harmless animals |

## Fourth pass, 2026-11-07 (owner: "bots should action against their full 700 skill bank and not focus on a singular profession/skill")

**Measured** from each bot's `skill_plan` events over 24 hours:
- **Totals:** base totals are 407-620 of 700, and most bots gained under 10 points in the day.
- **Where it stops:** the main skills are at 100, and the rest of the plan is what stands still.

| Stuck plan skill (gained under 0.5 in 24 h) | Bots | Cause | Change |
| --- | --- | --- | --- |
| Healing | 22 of 33 | practice bandaging (`heal_practice`) was a two-bot cohort capped at 60; the cohort gained 2.0-3.7 a day, the rest 0-1.3 | every bot whose plan holds Healing practises to the plan's target; gatherers bandage a scratch of 3+ hit points (`basics.r_heal`) |
| Hiding | 16 of 27 (every fighter at 0) | only gatherers and crafters practised it idle; the decision core ran no practice rule | `basics.r_train`: Hiding practice with no prey in view, under the core (`CORE_SKILL_RULES`), ahead of `r_hunt` |
| Bowcraft/Fletching | 4 of 4 archers (30-35) | they made only shafts and arrows, which teach 0-40 (`DefBowFletching.cs`) | `hunter.fletch_bow`: with 100 arrows and 7 logs, a Bow from 30 (teaches to 70) and a Crossbow from 60 (to 100), sold with the looted gear; `r_wood` chops for them |
| Tracking (tailors) | 4 of 4 (0-50) | only the rangers had the `tracking` feature | the tailors' hide hunt tracks animals, and follows only kinds with 6+ hides; `tracking` given to the four tailors |
| Swordsmanship (tailors) | 4 of 4 | they hunt with the starter dagger, a Fencing weapon (`Dagger.cs`), and the plan locks Fencing down | a crafter's weapon skill is its plan's (`crafter.main_skill`); before a hide hunt it wields or buys a sword (`hunt_armed`, `weaponup.arms_buy`). Gate 111 |
| Tinkering | 8 of 8 gatherers and smiths (about 30) | no bot outside the Tinker brain can open the tinkering menu | smiths (gate 111, `tinkerside.py`): every 15 minutes with ingots to spare, a session of up to 5 items through Tools > item (the paths BotTinkAR learned): their own tongs (35-85) and a shovel (40-90) when short, else scissors (5-55) and lockpicks (45-95), sold to a Tinker. The three miners (another brain class) stay open |
| Swordsmanship, Tactics, Anatomy (carpenters) | 3 of 3 (about 30) | carpenters never fight | open: hunt with the hatchet (an axe is a Swordsmanship weapon) |
| Resisting Spells | 9 of 13 | rises only when spells hit the bot | left alone |
| Healing, Hiding, Tracking practice | - | ships in gate 110 | read after the 19:03 rollover |
| Provocation | 2 of 2 bards (36-50) | provoking needs two creatures in bard range | open |

**Not broke with money in the bank** (owner, the same day):
- **The problem:** a bare hide shelf sent two tailors (293,406 and 178,287 gold banked) to hunt rats "broke" for 6-7 hours a day.
- **The fix:** coin hunting now needs `short_of_money` (gold plus bank under 250). A bare shelf sends a hide hunter after hides and any other tailor back to waiting for the restock. `hide_hunt` now covers all four tailors; its A/B gave 9,000-12,300 gold a bot-hour against 3,200-3,500.
