# Bot farm: technology that unlocks more capable bots (2026-10-20)

**Signed off by the owner on 2026-10-20: the travel planner (4b) first; item 1's other classes (the casters' mind) wait until the fighters are more effective, so the fighters' pieces (4b, the fight plan, 4, 3, 5) come before any new class.** The owner's cut of `Bot-Farm-Technology-Plan-2026-10-20.md`: only the technology that makes the bots themselves more capable. The process items
(branch and tag, the release flow, the scoreboard command) are out; the simulator's fidelity stays only where an item needs it. Nothing here is built.
Rulings taken: no branch yet; per-bot memory is a bot's own events plus hearsay.

Five items, in the order to do them. "Capability" is measured the way the owner judges the bots: do they act like smart players (the right targets,
the right places, no loops), and do the five numbers move (kills and net worth a bot-hour, deaths, lost fights, travel).

### 1. One mind for every class: the decision core everywhere, with a real fight step

**Unlocks.** Every bot plans: a goal, a task with an expectation and a budget, one monitor, a record of why. Today only the hunter has it; casters,
crafters, gatherers and tamers still run the rule list (50 to 70 flips a bot-hour, deaths from standing in the wrong place, loops the monitors veto one
by one). The fight step grows into a **fight plan** from the shard's own numbers (`danger.py`'s exchange estimate): when to drink, when to bandage, when
to retreat, an archer kiting at range, a caster opening with the right spell for the kind and meditating between pulls, a tamer's pet as the front line.
**Build.** `CasterBot` on `BotBase` (the borrowing ends) with its task set (hunt with fields, meditate, reagents, practise, recall home); crafters
(make N, sell N, restock, gather its own material), gatherers (mine, fish, chop, sell by evidence), tamers (find, tame, hunt with the pet); the six
monitors folded into the one; the fight plan shared by all. The simulator's creature AI (packs that aggro together, animals that flee, casters that
cast) is the dependency for the fight plan's read.
**Measure.** Per class, against the rule list in the simulator and then live: flips to near zero, deaths not up, the five numbers; the owner's
"dumb behaviour ranked by cost" list shrinking.
**Cost.** A day a class with the simulator: casters, crafters, gatherers, tamers; the fight plan a day. Five days.

### 2. Each bot its own memory, on one store

**Unlocks.** Bots that know different things go to different places (the owner's converging-bots problem), and a bot can be told things: hearsay
from bots it stood near, partied with or guild-chatted with counts, weighted lower until it sees for itself. Fifty bots become fifty players with
their own maps instead of one hive.
**Build.** `farm.db` as the one store for events, rates, decisions, facts, presence and claims, written by the brains directly (no 23 MB fold at
start); a bot's beliefs as a view: its own events, plus hearsay with a source and a weight; the derived knowledge (danger map, spot clocks, prices,
ground rates) as queries over that view. Guild chat and party talk become the channel hearsay travels on ("the graveyard is full of shades" said once,
heard by whoever stands near). The JSONL files stay as exports.
**Measure.** Distinct spots worked an hour up, bots per spot down, brain start time and memory down; a bot acting on something it was told.
**Cost.** Two days.

### 3. The bots learn their own expectations

**Unlocks.** Today every expectation (kills a visit, gold a kill, the chance a kind kills you, what a shop pays) starts from a hand-set prior and an
exponential average. The decision records now hold, for every task, what was expected, what was weighed and what came of it, by spot, kind, skill
band and errand. A bot that fits its expectations to its own outcomes stops repeating a bad choice after two tries and finds a good ground faster
than a player would.
**Build.** One estimator over the `task` and `rates` tables (a bandit per spot and kind in the bot's band, shrinking to the class's and then the
shard's prior, with the Thompson draw already in the choice), and a nightly job that reads the records back into the priors (`task_core`'s
`SPAWNER_KILLS_H`, `LOOT_SHARE`, `SKILL_PER_KILL`, the danger prior) so the next night starts where the last ended. The same estimator rates errands
(which shop pays, which buyer runs dry).
**Measure.** Expected against actual in `task_end` within 30% by the second hour of a night; tasks ended "yield" halved.
**Cost.** Two days.

### 4. Perception and reaction: see what a player sees, act within a second

**Unlocks.** A bot that notices a monster turning on it, a corpse appearing, a spell being cast, a pack forming, and acts in the same second. Today a
brain ticks every one to three seconds, reads three files, and asks line of sight, items and skills in separate commands; the fight step waits a
second between attacks.
**Build.** In Navrey: a `threats` query (hostiles with distance, line of sight, health, direction and who they attack, in one call), `.nav` with the
reason a walk ended, a journal event stream with kinds (hit, miss, spell cast, speech) instead of text matching; in the brains: the tick cost taken
down (the memory through the store, event counts instead of log matching, `prey()` cached a second) so a tick costs a tenth of today and the brain can
react at the client's pace.
**Measure.** Real seconds a simulated bot-hour (ten today) under two; the brain's reaction to a new attacker under a second; lost fights down.
**Cost.** Two days (one in the client, one in the brains).

### 4b. A travel planner (added on the owner's "anything more impactful?")

**Unlocks.** Walking is 40 to 60% of a fighter's time in every read, live and simulated, and no item above attacks it directly. A bot that picks the
fastest safe way for each journey (walk, a moongate, a camp-travel fire, Recall with a marked rune) and routes around the danger map spends that time
hunting: travel from 43% toward 25% is worth more kills than any fight tuning.
**Build.** One leg planner over the pieces that exist (`walkroute.py`, `tele.py`'s teleporters and moongates, camp travel, `runes.py`'s Mark and
Recall), costed in minutes and risk, used by every task's travel step; runes marked at the grounds a bot works; the simulator given moongates and
camp travel so the planner can be read.
**Measure.** Travel share by group; minutes from Britain's bank to a tier-3 ground; kills a bot-hour.
**Cost.** Two days.

### 6. Using the shard's own features (added)

**Unlocks.** The farm exists to test the shard, and the bots barely touch what it added: the potion bar's auto-use, the combat bar's durability notice,
the Ward, Faint Memories and the skill bank, the Hot Zone warning, guild chat, the help gumps, the Furnisher, houses. A layer of "what this shard lets a
player do", one capability per feature with its trigger, its act and a record, makes every bot a tester of the feature as well as a player, and the
records (`feature_used {name, outcome}`) the shard's own QoL evidence.
**Build.** A `shard_features` table in the brains (name, trigger, act, the flag it needs), each act built on the real client's protocol (the potion bar's
0xA7 / 0xAA answers, the menu mask, the Ward's double-click, the camp-travel fire); the owner's QoL findings list as the backlog.
**Measure.** Each feature used by a bot and recorded, with the outcome; the findings the bots raise about it.
**Cost.** Half a day a feature, done one at a time as the owner names them.

Item 5 also gets **the shared tour**: a party of two on one task (one pulls, one heals, the loot split), on the buddy and party code that exists, because
the dungeon rungs on a UO:R shard are a party's game and the hearsay memory gives the two something to say to each other.

### 5. The world beyond Britain: the ladder, dungeons, travel

**Owner's ruling, 2026-10-20 evening: the other towns are dropped for now. Britain is the hub; every journey starts from and returns to it (the dungeon rungs and the Hot Zone are reached from Britain; the errands, the bank, the runes and a ghost's healer are Britain's). The plan's "a healer in another town" measure is dropped.**

**Unlocks.** Fighters at 80 earning in dungeon level 1 instead of 17 gold on tier-3 farmland; casters recalling home; bots that use moongates, camp
travel, the Hot Zone warning and corpse recovery under real risk, which is what the farm exists to test. The spot model already carries tiers; the
rungs are the tiers above 3.
**Build.** Dungeon and Hot Zone spots from the spawn files and the gazetteer with the price of entry (potions, bandages, a retreat line) as a task
precondition; moongates, camp travel and Recall as legs the travel step can take (`tele.py`, `runes.py` exist); the other towns' ground and services by
gazetteer lookup; in the simulator, teleporters, dungeon maps and the Hot Zone so the rungs can be read before a live night.
**Measure.** Fighter net worth a bot-hour toward the review's +100 to +300; deaths under 0.25 a bot-hour for veterans; the first fighter potion, gear
and house purchases; a bot seen using a moongate, a camp fire and a healer in another town.
**Cost.** Three days (one of them the simulator's).

### Order and budget

1 (casters first) and 4's client half can start together; 4b beside them (its own files); 2 after 1's first class; 3 after 2; 6 one feature at a
time as the owner names them; 5 last, on 1, 4b and the simulator's dungeons. About eighteen session-days, three weekly windows at 2 to 3 usage
points a day with the farm stopped; the window resets on 2026-10-24. The dungeon rungs' price of entry (the owner, 2026-10-20): potions, bandages
and the weapon skill at 80; no party required.

### Open questions for the owner

1. The price of entry to the dungeon rungs: potions and bandages only, or also a skill floor (80) and a party of two.
2. Hearsay's weight: half a sighting until confirmed, or a quarter.
