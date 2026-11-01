# Bot farm: the technology plan (2026-10-20)

Written on the owner's "plan further improvements in the underlying technology", after the step-change review (`Bot-Farm-Step-Change-Review-2026-10-19.md`),
the release pipeline and simulator (`Bot-Farm-Simulator-Evidence.md`), and the decision core through plan 2 (`Bot-Farm-Decision-Core-Evidence.md`).
Nothing here is built. Each item names the step change, why it is one, how it is measured, and its cost; the order is the order to do them. The owner's
rules hold throughout: merit over migration cost, bots general by lookup, no LLM in the per-tick loop, the farm runs only when there is a release to read.

## Where the technology stands

| Layer | Today | What it costs us |
| --- | --- | --- |
| Client | One headless Navrey (Lean9, about 240 MB) per bot; walking fire-and-forget with `.nav`; perception by state and world files | Fine at 50 bots (6.5 GB free). Not the bottleneck. |
| Brains | 24,000 lines, 19 mixins on `BotBase`, the rule list for every class, the decision core for the hunter only; casters on the old `mage_bot.Bot` borrowing members; six monitors beside the list | Two architectures to maintain; every class but the hunter still flips between rules (50 to 70 flips a bot-hour) and has no record of why it did what it did |
| Memory and data | Append-only `world.jsonl` (23 MB, 174,000 events) folded by every bot with decay; `farm.db` (rates, decisions); whole-file JSON tables; per-bot `facts.json`; `features.json`; `metrics.jsonl` (70 MB); `notes.jsonl` (12 MB) | Every brain folds the whole history at start (the seeded simulator ran four times slower than unseeded); 50 processes each hold a copy; no per-bot memory; the dashboard reads logs, not a store |
| Simulator | 50 bots x 10 h in 10 to 30 min; fighters within a third of the farm on work, kills, deaths; walks over an 8x8 route grid | Its route grid refuses places the client reaches (70 "unreachable" tours a run); crowding harsher than the farm's; no dungeons, teleporters or moongates; gains and vendor stock patched by hand |
| Release and measurement | `farm_release.py --check` (gates, 107 patch tests, smoke) and a release line; A/B windows; scorecards written by hand each morning | No branch or tag yet (the tree is a content hash); the five numbers are computed by a different script in every session; the lost-fight measure has meant three things |
| Operation | Three agent sessions (Operator, Watcher, a build session) reading logs and exchanging messages; the owner relays between them | Usage: 0.7 to 1.2 weekly points a farm-hour on a quiet night, more on a patching day; the farm cannot run a week |

## The plan, in order

### 1. One brain architecture: the decision core for every class, the rule list retired

**What.** Finish what the review's recommendation 3 started: a `Brain` whose only per-class part is its task table and its reflexes. Casters get
`CasterBot` on `BotBase` (the borrowing ends) and a task set (hunt with fields, meditate, buy reagents, practise, recall home); crafters a craft task
(make N, sell N, restock) with the planner's rates as expectations; gatherers (mine, fish, chop, sell) and tamers (find, tame, hunt with the pet) the
same. The six monitors (stall sense, loop guard back-offs, planner switching, progress check, recovery gate, ambition vetoes) fold into the one monitor;
the 263 patch scripts, the backup folders and the md5 bookkeeping are retired for the branch-and-tag flow below.
**Why a step change.** One code path, one record per decision for every class, and every class gets what the hunter got (no flips, fewer deaths, a
record that says why). It is also the precondition for 2, 3 and 5: a task is the unit the store, the simulator and the scoreboard are built on.
**Measure.** Per class: flips a bot-hour to near zero, deaths not up, the five numbers against the rule-list run in the simulator and then live; the
line count of `bot_common.py` down by the monitors.
**Cost.** About a day a class with the simulator (casters first: they are the class whose crash classes cost the most nights), four days in all.

### 2. The store: one SQLite database, per-bot memory as a view

**What.** Finish `farm.db`: the shared memory's events, the rates, the decisions, the facts, the features and the presence and claims all in the one
WAL database, written by the brains directly (no JSONL folding at start), with the derived knowledge (danger map, ground rates, spot clocks, vendor
prices) as queries rebuilt by filter after a world change. Per-bot memory as the owner asked: a bot's beliefs are the events it witnessed plus hearsay
from bots it stood near, partied with or guild-chatted with, weighted lower until confirmed, which is a `where` clause over the same table. The JSONL
files remain as exports for the dashboard until it reads the database.
**Why a step change.** Brain start from seconds of folding to a query; 50 copies of the memory to one; no lost updates; bots that know different things
spread out (the owner's observed problem with converging bots); a world change (a spawn redesign) is a filter, not a reset by hand.
**Measure.** Brain start time, brain RSS, the simulator's seeded run time (four times slower today), distinct spots worked an hour up and bots per spot
down live.
**Cost.** Two days; half the schema exists.

### 3. The simulator's fidelity, and a calibration gate

**What.** Close the gaps the runs keep hitting, in this order: the client's own planner (route the simulated walks over the walk grid with the client's
rules, so "unreachable" means the same thing in both worlds); creature behaviour from the shard's AI (animals that flee, packs that aggro together,
casters that cast); the crowding model from the farm's presence records; teleporters, dungeons and moongates from the gazetteer (the ladder needs them);
the gain table from the shard's curve and Mastery instead of the hand-set formula; death and resurrection as the shard does them. Then a **calibration
gate** in `farm_release.py --check`: `calibrate.py` against the last farm day, and a check fails when a fighter number drifts outside a band (sim
between 0.5 and 2 times the farm on the five numbers), so the simulator cannot silently stop being a predictor.
**Why a step change.** The simulator is the lever that makes every other item cheap, and today's reads disagree with the farm on exactly the numbers
that decide promotion (lost fights, travel, crowding). A simulator that is kept calibrated by the pipeline turns "run a live night and see" into "the
live night confirms".
**Measure.** The calibration table's ratios on the five numbers within the band for two farm days running; "unreachable" tours a run to under five.
**Cost.** Three days spread over the other items (each gap when its item needs it); the gate itself half a day.

### 4. One scoreboard per release, computed by the pipeline

**What.** The five numbers (kills a bot-hour, net worth a bot-hour, deaths a bot-hour, lost-fight share, travel share) by group and cohort, defined once
in `farm_release.py --scoreboard` (the same code reads a simulator run folder and the farm's metrics and memory), with lost fights defined as engaged
fights the target left (the plan 2 definition) and the window taken from the A/B file. `--ab-open` records the before, `--ab-close` writes the after
and the deltas into the release line; the Watcher reads the deltas, not the logs; the dashboard shows the release lines.
**Why a step change.** Every session this week computed the numbers its own way and the owner had to reconcile them; a promotion rule needs one source.
**Measure.** One command gives the owner the A/B table; no hand-written scorecards.
**Cost.** Half a day.

### 5. The release flow finished: branch, tag, pinned releases, the nightly read

**What.** The designed branch-and-tag flow (`OPERATING.md`, "Releases"): the brain tree on `farm/brains`, a release a tag, the supervisor starting brains
from a worktree of the pinned tag so an edit never reaches a running brain, `status.json` naming the tag each bot runs, rollback a tag. Then the
**nightly read as one command**: check, start the farm on the tag, open the window, stop at the window's end, write the scoreboard and the morning note,
with the Operator and Watcher sessions reduced to reading that note. A usage budget per night written into the note.
**Why a step change.** The agents' tokens go to bookkeeping and relaying; the review measured one restart per bot every 26 minutes. This is what lets the
farm run a week of nights inside the owner's ceiling.
**Measure.** Weekly usage points a farm-hour (0.7 to 1.2 today) to under 0.3 on a read night; restarts a bot-day to one.
**Cost.** One day, after the owner says the tree gets its branch.

### 6. The brains' tick cost

**What.** Profile a brain tick (the simulator measures it: about ten real seconds a bot-hour, almost all in the shared memory's decay and JSON reading,
the loop guard's text matching and file appends) and take the three largest: the memory through the store (item 2), the loop guard's log matching
replaced by event counts, and `prey()`'s per-mobile assessment cached per serial for a second. Then the client: a `prey` query that returns the
hostiles with distance, line of sight and health in one call instead of three, and `.nav` with the reason a walk ended.
**Why a step change.** The simulator's speed is the agents' iteration speed (a 50-bot 5-hour read in five minutes instead of twenty), and live the
brains' 3.4 GB and CPU fall with it.
**Measure.** Real seconds a simulated bot-hour; brain CPU on the farm host.
**Cost.** One day.

### 7. The ladder and the world beyond Britain (needs 1 and 3)

**What.** Recommendation 4 of the review: the dungeon rungs and the Hot Zone as tiers above 3 in the spot model (the spot model already carries tiers),
with potions, bandages and a retreat threshold as the price of entry, moongates and camp travel as legs the travel step can take, and the other towns'
ground through the gazetteer. The farm then exercises what it exists to test: moongates, camp travel, the Hot Zone warning, corpse recovery under risk,
the crafted-goods economy.
**Measure.** Fighter net worth a bot-hour (the review's +100 to +300 at dungeon level 1), deaths a bot-hour under 0.25 for veterans, the first fighter
potion, gear and house purchases.
**Cost.** Two days once 1 and 3 exist.

### Not in this plan

A new client (RAM is not the ceiling), an LLM per tick, more monitors on the rule list, more bots.

## Order and budget

1 (casters first), 4 and 5 can start together and do not touch each other's files; 2 follows 1's first class; 3 runs beside all of them, gap by gap;
6 after 2; 7 last. About twelve session-days in all, 2 to 3 weekly usage points a day with the farm stopped, so two weekly windows. The weekly window
resets on 2026-10-24.

## Open questions for the owner

1. **The branch.** Item 5 needs the brain tree on its own branch with its first commit. Say when.
2. **Casters first?** Item 1's order is casters, crafters, gatherers, tamers (by the nights their crashes have cost). Say if another class matters more.
3. **The calibration band.** Sim between 0.5 and 2 times the farm on each of the five numbers, or tighter.
4. **Per-bot memory.** Hearsay from bots stood near, partied with and guild-chatted with, weighted lower until confirmed, or only what a bot saw itself.
