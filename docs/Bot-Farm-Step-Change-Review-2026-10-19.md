# Bot farm: step-change review (2026-10-19)

Written for the owner at his request: how the farm runs, how its bot logic is authored, how it stores data and how it operates, with the aim of step changes in the bots' ability to play and reason toward their goals, and in how effectively the agents iterate on them. Read: the operating guide and README, the three earlier reviews (`work/botfarm-watch/framework-review-2026-10-14.md`, `research-2026-10-18-botfarm-tech.md`, `plan-2026-10-19-bot-smarts.md`), the player-likeness goals, the resume notes, the operator log, the brain base, the hunter, the planner, stall, progress and loop-guard layers, the memory module and the store, the supervisor and evaluator, Navrey's protocol, and the farm's own data (`metrics.jsonl`, `memory/world.jsonl`, `supervisor.log`, the run logs). Measurements are from run 2b (2026-10-15 to today, 16:35). Weekly usage was 53% at the start and the owner's ceiling is 65%, so this review used no subagents and no live tests.

## 1. How the farm works today

- **Client.** One headless Navrey (ClassicUO fork, Lean9 build, about 240 MB) per bot, driven through a command file and two state files. Walking is fire-and-forget with the outcome in `.nav`; perception is the mobiles and movable items in view plus a handful of query commands (`items`, `los`, `shop`, `gumps`).
- **Brains.** One Python process per bot. `BotBase` (2,500 lines) carries 19 mixins; `HunterBot` adds six more and 22 rules; crafters, tamers, fishers and miners subclass it; casters subclass the older `mage_bot.Bot` instead and "borrow" base methods by assignment. About 24,000 lines in roughly 90 modules.
- **Decision loop.** Every tick: read the journal, observe, then walk the brain's `RULES` list top to bottom; the first rule that acts ends the tick. Rules block inside the tick (a `goto(...).wait(timeout=2..5)`, a 1.4 s attack pause, menu reads). Six monitors sit beside the list and veto or back off rules: the stall sense (15 min without progress), the loop guard (the same event many times a minute), the recovery gate, the planner (activity rates, crafters only choose), the ambition layer (personas and milestones) and the progress check (realized worth per hour; turned off once today for false verdicts, now v2).
- **Knowledge.** Generated from the shard: creature stats, craft tables, spawner lists, a walk grid, a gazetteer, hunt and tame spots, loot values, vendor roles. A "newbie" mode hides the server tables.
- **Memory and data.** Append-only shared event logs (`memory/world.jsonl`, 23.7 MB and 174,000 events; one `prof-*.jsonl` per profession) folded by every bot with half-life decay; a SQLite store `farm.db` (rates, decision records) added on 10-18; whole-file JSON rate tables still in use; per-bot `facts.json`, `knowledge.json`, `totals.json`, `bank.json`; `features.json` for A/B cohorts (48 switches); `notes.jsonl` (12 MB of findings), `metrics.jsonl` (70 MB, one row per bot per minute), `decisions.jsonl` per bot, `shops.json`, `status.json`, `dashboard.json`, and a DuckDB dashboard over the lot.
- **Operation.** A supervisor restarts dead clients and brains, kills a silent brain after 4 minutes, sheds bots on low memory and rebuilds the report every 5 minutes. `farmctl.py` is the operator's tool.
- **Authoring.** A watcher session reads the logs and writes `patch_<name>.py` scripts that string-replace code in the live brain tree (assert the fragment occurs once, write the file). An operator session dry-runs the patch on a copy, runs three gates (`test_no_shadow`, `test_borrow`, `test_main_last`) and the patch's own fake-client test, records md5s in `operator.log`, and restarts the affected brains; the supervisor relaunches them on the new code. Helpers build features the same way. Backups are timestamped folder copies. The brain tree is uncommitted work in `ShardContent/tests/scenarios/bot-farm`.
- **Measurement.** `evaluate.py` grades rule episodes (fix-first list), the watcher's scorecard and milestone scripts, the dashboard, and hand-written reads in the resume notes.

## 2. What the data says

**Skill gain of each bot's top skill, per bot-hour, by day (mean over bots with an hour or more that day)**

| Day | Fighters | Casters | Crafters | Gatherers | Tamers |
| --- | --- | --- | --- | --- | --- |
| 10-15 | 2.97 | 4.76 | 3.09 | 4.35 | 0.09 |
| 10-17 | 1.35 | 1.16 | 1.33 | 2.14 | 1.16 |
| 10-18 | 1.50 | 2.64 | 0.98 | 1.03 | 0.65 |
| 10-19 | 0.46 | 0.83 | 0.29 | 0.44 | 0.12 |

Median top skill now: fighters 84, casters 82, crafters 82, gatherers 96, tamers 58. The fall is mostly by design: above 80 the shard's gain curve and Mastery give about two points a day. Skill per hour has stopped being a useful measure of the bots' competence for every group but tamers.

**Time use (share of bot-minutes)**

| Group | Window | Work | Travel | Rest | Dead | Other |
| --- | --- | --- | --- | --- | --- | --- |
| Fighters | whole run (530 bot-h) | 20.6% | 62.1% | 3.7% | 4.5% | 9.0% |
| Fighters | last 6 h | 11.2% | 70.3% | 4.8% | 5.1% | 8.6% |
| Casters | whole run | 11.5% | 70.9% | 8.4% | 1.1% | 8.0% |
| Crafters | whole run | 26.6% | 55.8% | 2.3% | 1.3% | 14.1% |
| Gatherers | whole run | 29.2% | 1.4% | 61.9% ("every mining spot is taken or blocked") | 1.7% | 5.8% |
| Tamers | whole run | 66.7% | 26.7% | 1.5% | 4.0% | 1.1% |

Fighter work share by day: 25.9% (10-15), 16.6% (10-17), 33.4% (10-18), 15.4% (10-19). The watcher's target since 10-15 is 50%.

**Fights, deaths and loot (shared memory), all bots**

| Day | Bot-hours | Kills | Kills per bot-h | Fights lost (target gone) | Deaths | Deaths per bot-h | Loot gold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10-15 | 288 | 594 | 2.1 | 146 | 4 | 0.01 | 52 |
| 10-18 | 209 | 981 | 4.7 | 273 | 14 | 0.07 | 2,605 |
| 10-19 | 712 | 3,094 | 4.3 | 2,637 | 94 | 0.13 | 20,992 |

Today 46% of engagements ended with the target lost, not killed.

**Wealth now:** median gold carried, fighters 17, casters 106, crafters 100, tamers 120, gatherers 120. Two crafters hold 4,000 to 5,300; one bot has placed a house. Every ambition that costs money (potions, gear, scrolls, the house) is blocked for almost every bot.

**The development loop**

| Measure | Value |
| --- | --- |
| Patch scripts in `work/botfarm/patches` | 263 (plus 129 tests, 40 dry-run trees, 50 backup folders) |
| Distinct patches applied on 10-19 | 34 |
| Brain starts in `supervisor.log` over about 1,300 bot-hours | 3,019 (one restart per bot every 26 minutes on average); farm-wide restarts of 40 to 50 brains more than once an hour today |
| `EXCEPTION` lines in the run logs | 37,838, of which 36,737 are one missing attribute on `CasterBot` (8 casters idle for about 1.5 h) and 1,055 a second one; the rest are mixin signature clashes |
| Weekly Claude usage consumed per farm-hour | about 0.7 points on a quiet night run, 1.2 points on a patching day (operator log marks: 38% at 23:20, 45% at 08:51, 53% at 16:30) |
| Free RAM with 50 clients | 6.5 GB (clients about 12 GB, brains about 3.4 GB) |

## 3. Diagnosis

**D1. The decision architecture cannot express a plan, so every fix is a new veto.** A rule list answers "what do I do this tick"; nothing answers "what am I trying to achieve for the next twenty minutes, what do I expect it to yield, and when do I give up". The six monitors each measure "progress" differently (any pack change; the same event repeated; realized gold; activity rates; milestones), each with its own timers and back-offs, and they only veto rules. The symptoms in today's evaluation: 86 flips between `r_avoid` and `r_fight` in 30 minutes, 62 between `r_avoid` and `r_explore`, bots "watching the ground" for most of an hour, a tamer in `r_tame` for 30 minutes with nothing tamed, 46% of fights lost because pursuit is a 2 s walk then a re-evaluation. The 10-14 review recommended utility selection with commitment (R2) and non-blocking execution (R1); five days and 263 patches later the hunter still runs the rule list, and the fighter work share is lower than on 10-15.

**D2. Every hypothesis is tested on the live farm, confounded, at a cost of agent tokens.** There is no offline simulation. A change is written from log reading, applied, and read 30 to 60 minutes later, during which other patches, restarts, world changes and the owner's own changes land (the watcher's own change log notes read after read voided by a restart or a coincident change). The 36,737-exception incident, the `sys.exit(main())` placement bug that kept three rules out of every brain for hours, and the two mixin signature crashes were all found live. One restart per bot every 26 minutes resets fights, targets, walks, spot choices and the planner's windows, so the A/B cohorts rarely get a clean window.

**D3. The code and release process are the fragile part.** A 24,000-line codebase with 19-mixin inheritance, a caster class that borrows methods from a base it does not inherit, string-replacement patches on an uncommitted live tree, hand-recorded md5s, timestamped backup folders and three bespoke gates that each exist because of a crash class the previous gate missed. This is where the agents' tokens go: the operator log is mostly mechanical application and bookkeeping.

**D4. Progression no longer matches the shard's design, and the measures have drifted.** Fighters at 84 skill hunt tier 1 and 2 ground around Britain for 17 gold, because the danger model, the death-spot avoidance and the ring-graded spawn areas keep them there, and the dungeon rungs are off. On a UO:R shard a fighter at that skill earns in dungeon level 1. Until income exists, no ambition past A3 can complete, and A3 is now at the designed ceiling. Meanwhile the north-star measure has changed four times (kills per hour, work share, gains per hour, net worth per hour, milestones).

**D5. The binding constraint is the owner's weekly usage, not RAM or bots.** At 0.7 to 1.2 usage points per farm-hour, a week of continuous operation is impossible, and most of that spend is agents reading logs and applying patches by hand. The client memory question (UOTerm) and bot count are not the bottleneck at 50 bots with 6.5 GB free.

What is already right and should stay: everything goes through player commands; knowledge is generated from the shard's data; the shared memory is event-sourced with decay; decisions are recorded as episodes and graded; A/B cohorts; the newbie mode; the store in WAL mode; the DuckDB dashboard; the owner's rules on generality and critique.

## 4. Recommendations

Six, in the order to do them. Each names the step change, why it is one, the expected outcome and the cost. The first two are about the agents' effectiveness and make the other four cheap to do and possible to measure.

### 1. A farm simulator and a regression harness (agents' effectiveness)

**What.** A Python simulation of the shard good enough to rank brain changes, built from data the farm already generates: the canonical spawners (kinds, counts, respawn delays) from `spawners.py`, creature stats, the walk grid, the gazetteer and vendor roles, the shard's buy and sell prices, loot values and craft tables, the Navrey state and world files as the interface. Creatures spawn, wander and aggro by sight range; fights resolve from creature stats and the shard's combat numbers; walking follows the walk grid at the measured tiles per minute; vendors buy and sell by the shard's tables. The brains run unchanged against a `FakeClient` that serves the same files and commands. Fifty bots for ten simulated hours should run in minutes.

**Why a step change.** It turns every brain change into a measured experiment before it touches the farm, kills the crash classes at zero live cost (any AttributeError, signature clash or rule never reached shows up in the first simulated tick), and lets an agent try ten variants of a rule for the price of reading one farm hour today. It also makes the Voyager-style loop real: propose a change, simulate, keep it only when the scoreboard improves.

**Expected outcome.** Live exceptions from brain code to zero; A/B reads with no restarts in the window; the agent cost per accepted change down by roughly five to ten times; the farm's live hours spent on validation and QoL finding, not debugging. The simulator will be wrong in places; the live farm stays the final check, and its disagreements with the simulator are themselves findings about the shard.

**Cost.** About two days of one session. The fakes in the 129 patch tests are the seed.

### 2. A release pipeline instead of live patching (agents' effectiveness)

**What.** Put the brain tree on a git branch. A change is a commit; a release is a tag the supervisor pins (`farm_launch` reads the tag). One script (`farm_release.py`) runs the gates and the simulator's smoke run, tags, and restarts a named cohort at rule boundaries, at most a few bots a minute, never inside an open A/B window; it writes the release line itself. Rollback is a tag. Retire the string-replacement patches, the backup folders and the md5 bookkeeping. Fold the three gates into one `pytest` run, and fix or delete the stale tests.

**Why a step change.** The operator session's mechanical work disappears, the restart storm ends, and every live number can be tied to a release.

**Expected outcome.** Farm-wide restarts from more than one an hour to one or two a day; the operator session reduced to a script; a third or more of the per-farm-hour usage saved; no more "which code is this bot running".

**Cost.** Half a day. Do it first, because recommendation 1's harness should run in the same pipeline.

### 3. One decision core: goal, task, steps, with commitment and one progress monitor (bots' reasoning)

**What.** Replace "first rule wins" with a task object per bot. The persona's ambition picks a **goal** (train to 90, bank 1,000, buy the ringmail, reach Despise level 1). A planner turns it into a **task** with an expected yield and a budget (hunt the West Foothills for 20 minutes expecting 8 kills and 60 gold; craft 10 chairs; fish the shore until 40 fish). The task runs as a small behaviour tree of **steps** (the py_trees pilot already proved the shape on the trade), non-blocking, re-checked each tick, with explicit failure branches. Survival reflexes (dead, flee, cure, heal) stay as a short override list above it. The task has a **commitment** (it is not re-chosen for a minimum dwell) and one **progress monitor** (expected against actual yield, deaths, time), which is the single replacement for the stall sense, the loop guard's rule back-offs, the planner's switching and the progress check. Every task start and end is a decision record in `farm.db` with the options weighed, which is the data a bandit or any later learning needs. Migrate the hunter first and compare against the rule-list hunters on the scoreboard; then casters (and make `CasterBot` inherit `BotBase` properly), crafters, gatherers, tamers.

**Why a step change.** It is the difference between a bot that reacts and a bot that intends. Flip-flops, locking, false stall verdicts and lost fights are all the same missing thing: a commitment with an expectation. The owner's requests (loop breakers, explore wider, leave empty areas at once, path around monsters) become properties of tasks and routes rather than five separate patches.

**Expected outcome.** Fighters' work share from 11 to 20% to 50% or more and travel under 30% (33% was reached on 10-18 with camping logic alone); lost fights from 46% to under 15% with pursuit as a committed step; rule flips to near zero; one place to read why a bot did what it did.

**Cost.** Three to four days for the hunter with the simulator, then a day per group.

### 4. A progression ladder that matches the shard, and income first (bots' goals)

**What.** Make the ambition layer follow the path the shard designs for players: skill band to ground tier to dungeon rung to Hot Zone, with the gold each rung is expected to pay. Fighters at 75+ go to tier 3 and Despise level 1 (the ladder's rungs, currently off), with potions, bandages and a retreat threshold as the price of entry; casters hunt with fields and recall home; crafters and gatherers supply fighters through the market. Treat income as the first milestone of every persona, because every other milestone is bought with it. Keep the owner's rules: no sewers, danger by evidence and pack size, generality by gazetteer lookup.

**Why a step change.** Today 84-skill fighters earn 17 gold and the ambitions beyond mastery cannot start. Opening the ladder is also how the farm starts to exercise moongates, camp travel, the Hot Zone warning, corpse recovery under real risk and the crafted-goods economy, which is what the farm exists to test.

**Expected outcome.** Fighter net worth from about zero to +100 to +300 gold per bot-hour (UO:R dungeon level 1 rates with the shard's loot and prices); the first fighter potion, gear and house purchases; deaths per bot-hour will rise at first (budget 0.25 for veterans) and the simulator can tune the retreat thresholds before the farm pays for them.

**Cost.** Two days once recommendation 3 exists for the hunter.

### 5. Finish the store, and give each bot its own memory as a view over it (data)

**What.** Move the remaining whole-file JSON tables (`ground_rates.json`, `activity_rates.json`), the per-bot facts and `features.json` into `farm.db`; keep the JSONL logs as exports for the dashboard. The owner's "own memory per bot" becomes a filter: a bot's beliefs are the events it witnessed, plus **hearsay** from bots it stood near, partnered with or guild-chatted with, weighted lower until confirmed. Derived knowledge (danger map, ground rates, prices) is a query over events, rebuilt by filter after a world change instead of reset by hand.

**Why a step change.** One store, one schema, no lost updates, and per-bot memory for the cost of a `where` clause. Bots spread out because they know different things, which is the owner's observed problem with converging bots.

**Expected outcome.** Distinct areas worked per hour up and bots per area down; no more memory resets after a spawn redesign; the watcher's questions become SQL.

**Cost.** One to two days; the schema is half done.

### 6. One scoreboard per release, frozen windows, automated verdicts (measurement)

**What.** Fix five numbers and stop changing them: net worth per bot-hour by group; work share by group; deaths per bot-hour; milestones completed per bot-day (gear, potions, rungs, trades, house); lost-fight share. Each release gets a two-hour window with no restarts and no other change; a script writes the before and after table into the release record. The watcher reads deltas, not logs. Skill per hour stays as a tamer measure only.

**Why a step change.** The farm has produced four north-star measures in five days and almost no clean reads. A fixed scoreboard tied to releases is what lets the owner say whether a week of work improved the bots.

**Expected outcome.** A verdict on every change within two hours of its release; the watcher's token spend down because it stops re-deriving measures.

**Cost.** Half a day, mostly from `scorecard.py` and `evaluate.py`.

### Not recommended now

- **A new client (UOTerm) or more bots.** RAM is not the ceiling at 50 bots on Lean9 and 50 is enough to find QoL problems. Revisit when the brains are the smaller problem.
- **An LLM in the per-tick loop.** Too costly under the usage ceiling and not where the gap is. An LLM reading a gump or an unexpected journal line once, cached by text, is the only use that pays today.
- **More monitors on the rule list.** Each one so far has added a timer and a veto, not a plan.

## 5. Order and budget

1. Release pipeline (2), then the simulator and harness (1). These make everything after them cheaper, and they can be built with the farm stopped, which costs no usage for watching.
2. The decision core for the hunter (3), tuned in the simulator, released as an A/B cohort of ten, read on the scoreboard (6).
3. The ladder and income (4), then the store and per-bot memory (5), then the other brain classes.

Under the 65% weekly ceiling, the farm should run only when there is a release to read, and the watcher should read scoreboards, not logs. Building 1 and 2 with the farm stopped is the cheapest usage the farm has ever cost.
