# Bot farm: the decision core, phase 1 (evidence, 2026-10-19)

Phase 1 of `Bot-Farm-Decision-Core-Plan.md` (recommendation 3 of `Bot-Farm-Step-Change-Review-2026-10-19.md`): the hunter's goal, task, choice, monitor and
decision records, and the hunt task as a behaviour tree, built and measured in the simulator (`Bot-Farm-Simulator-Evidence.md`) with the live farm stopped.
Nothing here touched the farm's processes; nothing was committed, no branch or tag was made. Paths are under `ShardContent/tests/scenarios/bot-farm`
unless said otherwise; the runs are under `work/botfarm/sim`.

## What was built

| Piece | File | Does |
| --- | --- | --- |
| The core | `task_core.py` | `on(bot)`: the feature `task_core` on a brain class with `TASK_CORE` (HunterBot, BardBot; CrafterBot sets it False). The **goal** (`facts["core_goal"]`) from the persona and `goals.py`: A3 a skill milestone (measure skill points of the main skill), A1 / A2 / A5 the gear piece goals.py offers or the next banked milestone (measure gold carried and banked), A4 the next rung of 25 kills (measure kills); re-picked when done, gone or two hours old. The **task** (`facts["task"]`): area, spots, expected kills / gold / skill points an hour of work, budget 20 min, the counters at its start, the tree's state. The **choice**: every open area (tiers from the fields' and the patrol tiers, never above 3; a spawner with a deadly kind, a risky cell or three bots puts the area out; a banned area is out) scored as expected goal progress a minute over walk + budget + expected deaths x 20 min; the walk from `walkroute.plan` at the bot's measured tiles a minute; the expected yield a **Thompson draw** over the farm.db rate tables `task_kills` / `task_gold` / `task_skill` keyed `hunt\|group\|band\|area` (the prior from the area's spawner contents: `creature_stats` through `knowledge.py` for the time to kill, `loot_value.json` through `profit.py` for the gold, the memory's `prey_worth` where five fights are known, `danger.risk` for the death chance), spread `0.7 x mean / sqrt(n + 1)`, so unmeasured ground draws wide and is tried. **Commitment**: the running task's score is the better of its actual rate and its expectation, raised by half; a candidate replaces it only past five minutes of work and by half again (event `task_switch`). The **judge measure**: a hunt task is judged and scored on the goal's measure unless its expected yield in one budget is under one unit (a fighter above 80 gains its skill by Mastery's daily allowance, not by any one task): then on kills, the thing hunting yields (`judge_measure`; the first run failed 73 skill-goal tasks "yield" for want of a point in 20 minutes). The **monitor** every 60 s: two deaths fail; after 7 minutes of work the actual yield against the expected one pro rata: on track (half or more), under (one extension of 10 min), failed (under 15%, or under again); on track at the budget's end: the extension; a failed task bans the task and area an hour (`facts["core_bans"]`; the tree's own failures rest it 30 min for empty, 10 for stale, 15 for crowded, an hour for unreachable, and an unreachable area's spot goes to the shared memory as blocked for six hours so no other bot walks there). Events `task_start`, `task_arrived`, `task_extend`, `task_switch`, `task_end {why, expected, actual, mins, deaths}`; the rate tables updated at every task end. **Decision records**: farm.db `decisions`, kind `task`, the context (`decision_context` plus the goal), the candidates with score / draw / mean / walk / die / n, the chosen; closed with why / expected / actual by the new `farmdb.decision_close` at the task's end. The acted rule is `task:<task>:<step>`. |
| The hunt tree | `hunt_tree.py` | py_trees, the `trade_tree.py` pattern: `hunt [guard, steps [travel, work (loop) [pick, pursue, fight, loot]]]`. Travel: legs of at most 40 tiles from `walkroute`, one goto per leg, `.nav` read each tick, a walk that is not ours (a reflex's flee or avoid) not counted, a leg the client cannot path skipped for the next (the destination itself three times: "unreachable"; the walk estimate + 3 min: "unreachable"); **prey met on the road** (within 9 tiles, the danger model's say) is fought with the same pursue / fight / loot steps and the walk goes on (the first run walked past everything and killed a third less than the rule list). Pick: a waiting kill of ours is looted first; hurt with nothing on top of it: rest (bandage) before a new target; prey by `HunterBot.prey` (the danger model, the worth, other bots' fights, the town guards); two other bots on the pack: "crowded"; nothing ever seen here 75 s after arriving: "empty" (the plan's rule, the owner's "move on at once"); an area that paid and went quiet (no kill in 6 min, nothing in sight 75 s): "stale" (fields.py's STALE, a 10 min rest); meanwhile the nearest spawner not just visited, and 30 s standing at it for the respawn (`task:hunt:camp`, the old r_camp's class). Pursue: up to 25 tiles and 20 s from where the chase began, the goto re-issued when the target moves or the line of sight is lost; past the limits the target is dropped (ignored 90 s), never the task. Fight: attack every 2.5 s, the no-hurt clock (40 s) paused while a reflex holds the tick, a target that moves off chased within the pursuit limits, an archer keeps its distance and walks round for a line of sight; a fight is booked (`begin_fight`, the kill / lost record) from 9 tiles as `r_fight` did, so a chase given up further out is no "lost fight". Loot: the kill's own corpse only (one that appeared where the target fell), through the new `BotBase.loot_corpse` (r_loot's second half: open, carve with a blade, take); a pending corpse waits while a hostile is near. Nothing blocks on a walk. |
| The wiring | `bot_common.py`, `hunter.py`, `crafter.py` | `BotBase.REFLEXES`, `core_active()` / `core_tick()` (False / None on the base); the run loop runs only the reflexes and then `core_tick()` while `core_active()`; `facts` `task`, `core_goal`, `core_bans` persisted; `HunterBot.TASK_CORE = True` with `core_active` / `core_tick` through `task_core`; `CrafterBot.TASK_CORE = False`. The reflex rules are untouched. |
| Off for core bots | `stall.py`, `progress.py`, `loopguard.py` | `stall_tick` and `progress_tick` return at once when `core_active()`; `guard_trip` only reports (never backs off) a `task:` rule; `guard_client` (the server's refusals) unchanged. |
| Records | `farmdb.py` | `decision_close(id, extra)` merges the outcome and closes the row. |
| Simulator | `sim/farm_sim.py` | `--with-feature NAME` / `--without-feature NAME` (every bot of the run in or out of a feature, in the run's own `features.json`); the `task:` steps classed work / travel / camp / rest; the scoreboard adds the lost-fight share (`lost / (kill + lost)` from the memory's fight records), the rule changes and A-B-A flips a bot-hour from the run logs, and which rule-list rules below the reflexes acted (none for a core bot: the pass criterion "the rule list is bypassed"). |
| Tests | `tests/test_task_core.py` | The goal (A3, savers with and without a gear piece, A4, done / gone / renewed), the choice (tiers, the deadly veto, bans and their expiry, no tier 4, the Thompson draw on measured and unmeasured ground, a measured dead area passed over), the task and its records (the row, the options, the outcome closed), the monitor (grace, under + extension + yield, two deaths, on track to the budget + extension + done, the dwell and the switch), the tree (legs and `.nav`, a reflex's walk, nopath x3, the estimate, pick / pursue re-plan / drop past 20 s / fight / attacks / the kill's own corpse and not the rabbit's / empty / crowded / rest / a restart / an archer's line of sight), the whole tick and the wait fallback, the wiring. Run by `farm_release.py --check` and `test_farm.py` beside the patch tests (a failure fails the check). |
| Pipeline | `farm_release.py`, `test_farm.py` | The tree's own tests folder `tests/` runs with the patch tests. |
| Cohort | `work/botfarm/features.json` | `task_core` added EMPTY; `_planned.task_core` = the ten `fields` bots (the plan's default answer 3). The farm is stopped; nothing runs it. |
| Handover | `OPERATING.md` | Section "The decision core". |

Two bugs the build found in the existing tree, fixed because both arms of the comparison hit them:

1. **An archer out of arrows and gold switched to its fists and `r_gear` put the bow straight back on** (`hunter.fists_check`): a bow with no arrows swings
   nothing, so every fight of such an archer was "lost" and the farm's roster has several. The bow is now marked `gear_failed` while in fist mode (the mark
   `r_upgrade` uses), lifted when arrows are back.
2. **r_loot's second half** was inseparable from its corpse search, so the tree could not loot its own kill without also taking others' (`loot_corpse`).

## The runs: 20 hunters x 4 simulated hours, the core on against the rule list

`sim/farm_sim.py --classes hunter,bard --bots 20 --hours 4` (the roster's 17 hunters and 3 bards, one process so the bots see each other; `--with-feature
task_core` for every one of the 20, against `--without-feature task_core` as the control; the same seed and world). Groups and classes as in the farm's
scorecard: work = fight / hunt / loot (the core's pick, pursue, fight, loot), travel = explore / wander (the core's travel and roam), camp = r_camp (the core's
standing at a spawner for the respawn), rest = rest / heal. Lost fights = the memory's fight records `lost / (kill + lost)`; rule flips = A-B-A changes between
rule-list rules in the run logs, a bot-hour.

| Run | Work | Travel | Camp | Rest | Dead | Kills / bot-h | Deaths / bot-h | Gold / bot-h | Gains / bot-h | Lost fights | Rule flips / bot-h | Rule-list rules acted | Exceptions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Control: the rule list (`core-off-4h`) | 11.8% | 44.8% | 3.3% | 29.3% | 1.0% | 13.71 | 0.351 | +27.2 | 14.3 | 16.5% of 611 | 60.1 | 19 (r_explore, r_fight, r_hunt, r_loot, r_camp, r_bank, ...) | 0 |
| Core, first tree (`core-on-4h`) | 6.6% | 50.5% | 26.5% | 11.3% | 0.3% | 8.84 | 0.075 | +15.8 | 10.0 | 15.1% of 436 | 2.4 | none | 0 |
| Core, empty / stale split, nopath legs skipped (`core-on-4h-b`) | 6.8% | 41.7% | 41.3% | 9.2% | 0.4% | 10.33 | 0.163 | +12.2 | 12.1 | 9.2% of 402 | 2.9 | none | 0 |
| Core, fights on the road, the kills judge, shared blocked spots (`core-on-4h-c`) | 8.2% | 29.3% | 37.3% | 20.9% | 0.3% | 12.89 | 0.138 | +23.7 | 14.0 | 13.9% of 597 | 2.0 | none | 0 |
| Core, rested areas before a wait (`core-on-4h-d`) | 7.9% | 32.2% | 35.2% | 19.9% | 0.3% | 10.73 | 0.126 | +14.6 | 14.7 | 21.2% of 509 | 2.0 | none | 0 |
| **Core, final tree** (rests under 20 min only, `core-on-4h-e`, release `tree-ad9ff4a6f475`) | 8.0% | 32.7% | 32.7% | 21.4% | 0.7% | 11.28 | 0.251 | +20.2 | 15.7 | 15.1% of 516 | 3.1 | none | 0 |

The core's rule flips are between the reflexes (`r_heal` and `r_avoid` trading the tick over a hurt bot), never a rule-list rule. The core bots do not
sell, bank or buy beyond arrows (phase 2), so their gold is loot only; the control's includes 28 sales.

**The final run's task records** (`task_start` / `task_end` in `decisions.jsonl`, the `task` rows in farm.db: 646 opened, 626 closed with why / expected /
actual): 646 tasks; 236 chosen from the open areas, 386 from areas whose rest was ending (the fallback), 24 switches; 73 extensions (43 on track at the
budget's end, 30 under). Endings: 368 "done" (the two-minute waits when nothing at all was open, and the budgets run out), 77 "yield" (9.6 min of
work, 1.4 kills), 76 "stale" (12.5 min, 3.8 kills), 36 "empty" (1.4 min: nothing there on arrival), 31 "unreachable" (8.9 min walking: the simulator's own
route grid refuses some of walkroute's destinations; shared as blocked spots so the others skip them), 24 "switch", 8 "crowded", 6 "deaths". 352 fights
on the road. 27% of the choices went to an area with no record in the rate tables (the plan's open question 1 asked for about one in five; the draw's
spread is `SPREAD` 0.7 in `task_core.py`). Judge: 424 tasks on kills (every skill-goal task of a fighter above 80), 222 on gold. The three rate tables
hold 44 keys each (group x band x area) at 5.8 records a key after the run.

**Where the time goes under the core**: 33% standing at spawners for the respawn, 33% walking (18% between areas, 15% between an area's spawners), 21%
resting, 15% waiting with nothing open, 8% fighting and looting. The simulator's fights are short (a kill in 10-20 s) and its ground thin for 20 bots on
the twelve areas their tiers allow, so neither arm comes near the plan's 40% work share here; the calibration table in `Bot-Farm-Simulator-Evidence.md`
put the rule list's farm work share at 11.1% against 7.9% simulated for the same code.

## Phase 1 pass

| Criterion (the plan, phase 1) | Control | Core, final | Pass |
| --- | --- | --- | --- |
| Work share 40% or more | 11.8% | 8.0% | **No.** Neither arm reaches it in the simulator (its fights are three times shorter than the farm's and its ground thinner); the core's share is 8.0% against the rule list's 11.8% at a kill rate of 11.3 against 13.7 a bot-hour, with the lower kill rate mostly the 15% of time with no open area (every area banned, resting, vetoed by the danger map or crowded for that bot) and the 9 min walks to areas the simulator cannot route. The plan's number was set in farm units; it is read live in phase 3. |
| Lost fights 20% or less | 16.5% | 15.1% | **Yes** (13.9% to 21.2% over the three tuned runs). |
| No exception in any tick | 0 | 0 | **Yes** (every run and the release smoke run; 1,600 bot-hours simulated in all). |
| No rule flips (the rule list is bypassed) | 60.1 flips a bot-hour, 19 rule-list rules acted | 3.1 a bot-hour between the reflexes, 0 rule-list rules acted | **Yes** for the rule list; the reflexes still trade the tick over a hurt bot (r_heal / r_avoid), which is their design. |
| Deaths (the plan's phase 2 ceiling, 0.33 a bot-hour) | 0.351 | 0.251 | For the record: the core dies 0.13 to 0.25 a bot-hour against 0.35. |

So phase 1 passes three of its four simulator criteria and fails the work share, as the control does. What the core does deliver on the control, in the
same world: a quarter to a third fewer deaths, a third less travel, the same or a slightly lower kill rate, no rule flips, one task record per decision
with the expectation and the outcome beside it, and a bot that can say what it is doing and why (`core: task hunt Castle Woods for Swordsmanship to 90
(score 0.264, 8.1 min walk, expected {...}; others: ...)`). The kill-rate gap and the waits are the first thing for phase 2 to take up (below).

## Release check

`farm_release.py --check` on the final tree: **RELEASE OK `0eaeac1-dirty+tree-ad9ff4a6f475`** in 180 s: gates 3/3 (`test_no_shadow`: 9 brain classes, no
method hidden; `test_borrow`; `test_main_last`), patch tests 106 pass and `tests/test_task_core.py` pass, 24 stale (the 22 of the 2026-10-19 19:35 check
plus `test_gather_risk.py`, a time-decay boundary at 0.5000004 in area_danger that is not this work, and `test_ingot_market.py` / `test_tamer_hunt.py`, the
Operator's queued patches that are not applied), smoke run of every brain class clean (kills 25, exceptions none, crashes none). The line is in
`work/botfarm/releases.jsonl`; the two earlier lines of this session (`tree-d16a9858f67a`, a check that ran while the tree was still changing, and
`tree-b6c2f2fc2deb`) are superseded. `work/botfarm/operator.log` has the session's lines (files changed, the release id). Run the check again before
any farm start; the restart refuses a tree that differs from the last passing check.

## The live A/B, 2026-10-19 23:28 to 2026-10-20 07:31 (closed by the owner's word)

The owner had the farm started overnight on the checked tree (`tree-ad9ff4a6f475`; the review session and the Operator, 23:28; `--ab-open 10`): the ten
`fields` bots on the core, the other ten fighters on the rule list, no restarts or patches inside the window. Measured from `metrics.jsonl` (one row a
bot-minute), the memory's fight records and the core bots' `decisions.jsonl`; 74.8 bot-hours each side.

| Measure | Core (10 fields bots) | Rule list (other 10 fighters) |
| --- | --- | --- |
| Time: work / travel / camp / rest / wait / other / dead | 7.1 / 19.2 / 45.3 / 4.5 / 12.3 / 10.6 / 0.9% | 8.4 / 60.1 / 6.4 / 4.1 / 0 / 20.4 / 0.7% |
| Kills a bot-hour | 8.94 | 8.78 |
| Deaths a bot-hour | 0.214 | 0.134 |
| Net worth a bot-hour (gold carried + banked) | +18.9 | -0.1 |
| Lost fights (lost / (kill + lost)) | 36.4% of 393 (flee 89, deaths 11) | 29.7% of 657 (flee 56, deaths 3) |
| Rule flips a bot-hour (A-B-A on the minute rows) | 0.03 | 3.25 |
| Rule-list rules acted | none | 15 (r_explore, r_fight, r_hunt, r_loot, r_camp, r_resupply, ...) |
| Core tasks | 641 started (249 chosen, 364 from a rest ending, 28 switches); endings: done 350, yield 126, stale 50, empty 40, unreachable 30, switch 28, crowded 17 | |
| Exceptions in the window | 0 from the core; 17 `BotBase.wants()` lines in one core bot from `ambition.py` line 81 (`self.wants` for `ambition_wants`, a pre-existing name clash, the last at 22:32 before the window) | 0 |

**Reading.** On the farm the core matches the rule list on kills (8.9 against 8.8 a bot-hour), keeps the gold it loots (+19 a bot-hour against the rule
list's break-even, which spends on resupply and sells little), walks a third as much (19% against 60%), and never flips between rules; the
simulator's prediction of the kill rate and the travel held. It did not deliver the two numbers the plan wanted most: the work share is 7% (the rule
list's 8%), and the lost-fight share is 36% against 30% with 11 deaths against 3. Where the core's time went: 45% standing at a spawner for the respawn
and 12% in the wait task with no open area, the same two sinks the simulator showed (above); the deaths and the lost fights come from the fights it does
take, which the simulator's shorter fights understated. Compared with the review's farm baseline (fighters 11-20% work, 62-70% travel, 46% lost, 0.33
deaths a bot-hour), both arms lost less and died less overnight, so the baseline itself moved with the 2026-10-18/19 spawn and danger changes.

**Verdict.** Phase 1 is a working core with a measured gap: not a promotion. Do not widen `task_core` beyond the ten; keep it on them only if the
owner wants the data to keep coming (the cost is the 11 deaths a night). The next steps, in order:

1. **The waits and the camps (the kill rate)**: give the choice the rule list's wider ground (the memory's hunting cells and the patrol ring as areas of
   their own, not only the 21 `britain_areas.json` areas), let two bots share a large area, judge a quiet spawner by the area's respawn delay rather than a
   fixed 30 s, and shorten a "yield" ban on ground that paid before. Expected: the 57% of standing and waiting halves, kills up by a third.
2. **The deaths and the lost fights**: read the 11 deaths' `task_end` and `learned: avoid` lines (ettins, gargoyles, trolls and reapers at the tier-3
   areas the patrol tiers open to 84-skill fighters); the choice's risk term uses `danger.risk` with a pack of one, which understates tier-3 packs, and
   the fight step has no "this is going badly" exit of its own below the reflexes' flee line. A retreat threshold in the fight step and the pack size in
   the risk term are phase 2's first two changes.
3. **Phase 2 as planned** (the other eight tasks, the bards' play, `evaluate.py` on `task_end`), then the ladder (recommendation 4), then phase 3 again
   with the five-number scoreboard.
4. **Two pre-existing crashes seen overnight, not the core's**: `ambition.py` line 81 calls `self.wants("A4")` (the method is `ambition_wants`), and every
   caster logged thousands of `'CasterBot' object has no attribute 'decision_record'` lines (a `BotBase` member the caster does not borrow; `test_borrow`
   misses it because `dlog` is borrowed and calls it). Both are one-line fixes for the next release check.

## Steps 1 and 2 after the live A/B (2026-10-20 morning, the owner's "Steps 1 and 2 now")

Built on the tree the Operator updated for the Spawn Designer's spawns (regenerated areas, hunt spots, gazetteer; bot memory reset), so the control
was run again too. Release check on the final tree: **`0eaeac1-dirty+tree-5cda46f60140`** (gates 3/3, 107 pass, 24 stale, smoke clean).

**Step 1, the ground and the camping** (`task_core.py`): the memory's best hunting cells within 320 tiles of home become areas of their own
(`ground <cell>`, the kinds sighted there, away from the Britain areas' spawners: the rule list's r_explore ground); a large area holds one bot per two
spawners instead of the fields' three; a "yield" task that still made two kills rests the area 20 minutes, not an hour; and the camp at a spawner is
the spawner's own respawn clock (`spawn_delays` from the canonical spawn files, `spawn_delay_at`, `camp_seconds`): a 20 s look-around when nothing was
killed there lately, a wait only once the respawn is due (the last kill there plus the minimum delay, `spot_kills` in the task state), never more than
three minutes. The first cut stood up to three minutes at every spawner and killed a third less (`step12-on-b`: 9.7 kills a bot-hour); the due-respawn
rule is what stands.
**Step 2, the deaths** (`task_core.kind_risk`, `hunt_tree.Fight`): the risk term scores a pack kind on tier-2+ ground as a pack of two or more
companions (the danger model's "2+" band; one companion on tier 1, none otherwise), a death costs 30 minutes in the score, and the fight step has its own
retreat: under 60% health with the target's share of its health 15 points above ours, the bot leaves it (ignored five minutes, a step away, the fight
booked as a flee) before the reflexes' flee line; two retreats from one kind in a task put the kind on the task's avoid list (event `retreat`).

| Run (20 hunters x 4 h, the new spawn data) | Work | Travel | Camp | Rest | Other | Kills / bot-h | Deaths / bot-h | Gold / bot-h | Lost fights | Flips / bot-h | Rule-list rules |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Control: the rule list (`step12-off`) | 12.3% | 49.9% | 3.3%* | 25.5% | 10.7%* | 14.59 | 0.301 | +41.2 | 18.2% of 622 | 58.2 | 19 |
| Core, steps 1 and 2 first cut, 3 min camps (`step12-on-b`) | 7.0% | 26.7% | 36.0% | 12.5% | 17.1% | 9.74 | 0.226 | +15.1 | 18.4% of 407 | 2.9 | none |
| **Core, due-respawn camping (`step12-on-c`, release `tree-5cda46f60140`)** | 7.4% | 28.2% | 28.9% | 28.9%** | 5.9% | 10.74 | 0.238 | +18.6 | 15.9% of 498 | 2.6 | none |

(* the control's camp is inside "other" in its scoreboard row: 3.3% r_camp, 10.7% other; ** the core's rest column holds the reflexes' r_heal and
its own rest step.) 60 retreats in the first cut, no exception in either core run after the keyword fix (the first run of the day raised 190
`BotBase.ev() got multiple values for 'kind'` lines from the retreat event; fixed, and the test fake now has the base's `ev` signature so a clash fails
in the unit test).

**Reading.** On the new spawn data the rule list itself got better (14.6 kills a bot-hour, 0.30 deaths), and the core, at 10.7 kills, 0.24 deaths and
15.9% lost, is safer and loses fewer fights but still kills a quarter less. The gap is no longer the waits (38 rested starts, no wait step in the top
steps) but the camps and the reflex time: 29% standing at spawners between respawns and 6% in r_avoid, against the rule list that walks between any
sightings it remembers and fights what it meets. The memory grounds were chosen 9 times in 4 hours: the memory of a fresh run has few sightings; live,
with the farm's memory, they will weigh more. Not a promotion; the ten `fields` bots can keep the core for data, as before.

**What is left for the kill rate, for phase 2:** (1) walk between spawners *inside* an area the way the rule list walks between sightings, with the
camp only when a respawn is due (done) and the empty / stale rules counted per spawner, not per area; (2) take the fight to what is in sight on the way
between spawners (the road fight is only on the travel leg today); (3) read the live memory's grounds (the simulator starts empty); (4) the eight
other tasks, which also stop the core bot from standing with a full pack.

## Phase 2 (2026-10-20, the owner's "Start now")

**Built** (`errands.py`, `task_core.py`, `hunt_tree.py`, `evaluate.py`, `tests/test_task_core.py`; release check on the final tree
**`0eaeac1-dirty+tree-ef7c2680c7b2`**, gates 3/3, 107 pass, 24 stale, smoke clean):

- **The eight errand tasks** as short trees with the hunt tree's shape: a non-blocking travel to the place (the counter, within 3 tiles, no scatter, no
  fights on the road), then one act that reuses the rule list's own code standing where its walk is a step or two: sell (`r_sellgear` / `r_sellmeat` /
  `r_sellloot` with their cooldowns cleared), resupply (`r_resupply`), bank (`r_bank` / `visit_bank`), rest (bandages, a Refresh potion when tired,
  standing until 75% health, no walk), train (the dummy or the butte while the weapon skill is under 30), upgrade (`r_upgrade`), camp (the hunt tree
  bound to the last kill's spawner for two respawns) and loot (the hunt tree's loot step for a corpse of ours left pending). An errand ends "done"
  when its act met the need, "unmet" when it could not (that task rests 30 min).
- **The needs** (`errands.needs`): the bot's state raises errands with an urgency (bandages under 8: 2, none: 3; an archer's ammunition the same;
  gold over the purse limit: 1 to 2, overloaded: 2; loot to sell: 1.2, 1.8 when heavy; under 50% health with nothing about: 1.5; a gear piece
  affordable: 1.6; the dummy: 0.9; a fresh camp: 0.9). The choice (`task_core.tick`) takes an errand of urgency 1 or more over the best hunt and
  records every errand beside the hunt candidates; a pressing need (urgency 2, `PRESSING`) interrupts a running hunt through the monitor
  (`task_switch`).
- **The bards' play step** in the hunt cycle after the loot: `BardBot.r_music` with its own cooldown (Peacemaking, Discordance, Provocation on two),
  counted as work (`task:hunt:play`).
- **`evaluate.py`** gains a section "The decision core's tasks": endings by bot and why, the hunt tasks' expected against actual kills.
- Fixes on the way: the errand's walk was scattered like a hunting spot (never "arrived"); the rest errand first held a bot to 85% health from 65% at
  the simulator's slow regeneration (now from 50% to 75%; the hunt tree rests itself between 50 and 65); the crowd cap doubles in the rested pass.

**The full board, 50 bots x 10 simulated hours, 5 processes** (the plan's phase 2 pass: fighters work 50% or more, travel 30% or less, deaths at or
under 0.33 a bot-hour, net worth above the rule-list hunters in the same run):

| Fighters (20, about 200 bot-hours) | Work | Travel | Rest | Camp + wait + errands | Kills / bot-h | Deaths / bot-h | Gold / bot-h | Lost fights | Flips / bot-h |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Control: the rule list (`phase2-off`) | 9.4% | 40.8% | 25.6% | 21.9% | 11.97 | 0.346 | +20.9 | 20.1% of 1179 | 49.9 |
| Core, phase 2 first run (`phase2-on`) | 4.5% | 24.2% | 34.4% | 35.6% | 7.64 | 0.306 | +12.1 | 15.5% of 753 | 2.1 |
| **Core, phase 2 final (`phase2-on-b`, `tree-ef7c2680c7b2`)** | 4.4% | 25.9% | 23.2% | 45.5% | 7.46 | 0.276 | +14.5 | 14.9% of 753 | 2.1 |

The other groups are the rule list in both runs (the core is the hunters' only). No exception in any tick. The final run's core tasks: 685 hunts,
847 waits, 156 rests, 131 sells (33 done, 98 unmet), 33 resupplies (26 done), 20 banks (all done), 2 camps; the hunts ended stale 179, yield 172,
empty 117, done 70, switch 66, unreachable 53. The core's fighter time: 34% standing at a spawner, 16% walking to areas, 16% waiting with nothing
open, 14% walking between spawners, 6% resting, 5.5% fighting.

| Phase 2 criterion | Control | Core | Pass |
| --- | --- | --- | --- |
| Work share 50% or more | 9.4% | 4.4% | **No** |
| Travel 30% or less | 40.8% | 25.9% | **Yes** |
| Deaths at or under 0.33 a bot-hour | 0.346 | 0.276 | **Yes** |
| Net worth a bot-hour above the rule-list hunters | +20.9 | +14.5 | **No** |

**Reading.** The errands do their job (the bots bank, buy, sell and rest, with no exceptions and far fewer deaths), and the core keeps every
property it had: no rule flips, a record per decision, a third less walking. But the hunter underneath it still kills 40% less than the rule list on a
full board, and that gap is not in the errands: it is the **ground model**. The core hunts 21 fixed areas with a crowd cap per area, so on a board
where 20 fighters, 8 casters and 12 crafters all work the same farmland around Britain, a bot keeps finding every area banned, resting or crowded
(847 waits) and stands at spawners between respawns (34%); the rule list roams any memory cell with a sighting, counts crowding per spot, and fights
what it meets. The sell errand also fails two times in three (`sell:unmet`): the rule list's own sell code refuses with a hostile within ten tiles or
no buyer found, and the errand has no answer of its own yet.

**The conclusion to put to the owner.** The task, monitor and errand machinery is sound and worth keeping. The hunt task's ground model is not: it
should be rebuilt on the rule list's own ground (every spawner and every remembered sighting cell as a spot of its own, crowding by spot, the empty and
stale rules per spot, the walk between spots as the work), which is a design change, not a tuning. Until then the core should stay on the ten
`fields` bots for data and not be promoted. The live A/B numbers (kills at parity with the rule list on the farm, the simulator's 40% gap) say the
simulator's crowding is harsher than the farm's; a second live night on the phase 2 tree would show whether the errands change the farm's reading.

## Plan 2: beat the rule list (2026-10-20 afternoon, the owner's sign-off on `Bot-Farm-Decision-Core-Plan-2.md`)

**Built** (release check on the final tree **`0eaeac1-dirty+tree-89621fcd44b9`**, gates 3/3, 107 pass, 24 stale, smoke clean):

- **Piece 1, per-spot ground** (`spots.py`): every canonical creature spawner on the surface within 320 tiles of home (place, kinds, count, respawn delays from
  the spawn files) and every memory cell with sightings no spawner covers is a spot; a spot carries its respawn clock (the shared memory's last kill at its
  cell: a new `spotkill` event folded in `memory.py`, so one bot's kill tells every bot when the respawn is due), the bots on it now (crowding by spot:
  skipped unless it holds three creatures), its tier (the Britain area it lies in) and its rate record (farm.db `task_spot`: kills a visit). The hunt task
  is a **tour**: a cluster of up to six spots within 90 tiles of a seed, ordered nearest-next, scored as expected kills a minute over the walk to the seed,
  the legs, and the fights, a Thompson draw per spot; the tree works the tour in order, judges empty per spot (a spot found empty twice is passed), camps
  only at a due respawn, and a failed tour rests its spots, not an area. The rested fallback and the wait task survive only for a bot with no spot at all.
- **Piece 2, fight what is met**: the pick and the road fight take prey within the view range (18 tiles), the "safe ground" filter only beyond 8; a kill
  updates the nearest spot's clock for every bot. A **worth floor** (the Watcher's read of the live A/B: rabbits, birds and rats were the core's most-fought
  kinds): beyond two tiles a target must be worth the walk (its measured worth at the floor, else a kind the loot table rates above it); a bot in fist mode
  takes what fists can kill; a spot of unmeasured low-loot kinds is no ground.
- **Piece 3, errands that finish**: the sell errand has its own act (a buyer by role from the memory's vendor records, the role's shop next, a second
  shop when the first takes nothing, gear no shop buys dropped), the resupply errand tops bandages up to 60 for the next tour, and, on the owner's ruling
  of 2026-10-20 ("low skill hunters can get resources from corpses ... hides that can be cut into leather at 5gp ... feathers, meat"), a core bot loots
  hides, the sell errand cuts them into leather with scissors (bought at the Tailor when none is carried) and sells leather at the Tanner and feathers at
  the Bowyer, and the worth model counts the loot table's carve value (regular hides as leather at 5, meat at the Butcher) at 0.8 for a bot with a blade.
  The simulator's scissors cut cloth and fish only; they now cut hides into leather as the shard does.
- **Piece 4, learning per spot**: the rate tables keyed by spot cell and folded at every tour's end (kills a visit per spot visited); the simulator runs
  seed the farm's memory (`--memory-from work/botfarm/memory`) so the grounds exist from the first minute, as they do live.
- The fight is booked (`begin_fight`, the kill / lost / flee record) when the target is engaged, in reach, so an abandoned chase is no "lost fight"; the
  first plan 2 run booked from nine tiles and read 17% lost against the rule list's 9%.

**The runs** (the full board, 50 bots, 5 processes, the farm's memory seeded, the control in a run of its own on the same board; fighters only; lost
fights from each run's own window, since the seeded memory carries the farm's history):

| Run | Work | Travel | Rest | Kills / bot-h | Deaths / bot-h | Net worth / bot-h | Lost fights | Flips / bot-h | Exceptions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule list, 10 h (`plan2-off`) | 11.0% | 43.7% | 23.7% | 15.86 | 0.411 | +13.4 | 9.2% | 53.9 | 0 |
| Core, 10 h, fights booked from 9 tiles, no leather yet (`plan2-on-c`, `tree-32eb672aed64`) | 10.2% | 42.2% | 19.0% | 17.92 | 0.396 | +14.8 | 17.4% | 2.5 | 0 |
| Rule list, 5 h (`plan2-5h-off`) | 10.0% | 29.2% | 24.0% | 14.69 | 0.793 | +18.3 | 9.5% | 71.0 | 0 |
| **Core, 5 h, final tree (`plan2-5h-on`, `tree-89621fcd44b9`)** | 11.9% | 43.3% | 22.1% | 16.42 | 0.492 | +21.4 | 12.6% | 3.3 | 0 |

The final run's core tasks: 36 hunts done, 130 switches, 120 yield, 72 unreachable (the simulator's route grid), 20 stale, 19 empty, 36 waits; 62 sell
errands done and 87 unmet (the simulator's vendors buy at most 20 of a kind an hour, so twenty bots selling meat run the Butcher dry), 39 banks, 38
resupplies, 31 upgrades; sales 1,364 gold of meat, 1,023 of leather (1,273 hides cut), 155 of gear. The owner's five-hour rule for simulator reads
(2026-10-20) applies from here.

**Against the owner's pass rule** (kills 1.1x and net worth above decide; deaths, lost fights and travel must not be worse):

| Number | 10-hour read | 5-hour read |
| --- | --- | --- |
| Kills 1.1x the rule list | 1.13x: met | 1.12x: met |
| Net worth above | +14.8 against +13.4: met | +21.4 against +18.3: met |
| Deaths not worse | 0.40 against 0.41: met | 0.49 against 0.79: met |
| Lost fights not worse | 17.4% against 9.2%: not met (booked from 9 tiles) | 12.6% against 9.5%: not met by 3 points |
| Travel not worse | 42% against 44%: met | 43% against 29%: not met |

The two deciding numbers pass in both reads, deaths pass in both, and the two that miss sit inside the run-to-run noise of this board (the rule list's own
travel read 44% then 29%, its deaths 0.41 then 0.79, with the same code). Deaths and lost fights live have been the core's weak side (the first live
night: 0.21 against 0.13, 36% against 30%), and the live reading is the one the plan says decides. So: **the simulator says the core now out-earns the
rule list; the live night on the final tree is the promotion test**, the ten `fields` bots against the other ten, eight hours, no restarts, judged on
the same five numbers.

## The travel planner (capability plan item 4b, signed off 2026-10-20 afternoon)

**Built** (release check on the final tree **`0eaeac1-dirty+tree-3b73d2fd8ecb`**, gates 3/3, 107 pass, 24 stale, smoke clean): `travel.py`, a journey
planner every task's travel step asks: the cheapest safe sequence of legs among four kinds, each costed in minutes plus a danger charge (2 min a waypoint
in a cell the memory calls dangerous): **walk** (the routed waypoints, the last one the destination itself so an errand stands at the counter),
**gate** (the nearest public moongate, the gate's list answered with the town nearest the destination through Navrey's `gumpresponse 1 <radio>`
syntax, the jump checked, the walk on from that gate; only when it saves 150 tiles), **recall** (a rune this bot marked near the destination, the rune
code's own criteria and cast; when its Magery can), **camp fire** (a party member's blue travel fire near the destination; chosen only when a fire is
on the list, which the shared tour brings). A leg that fails blocks its kind ten minutes and the journey is planned again from where the bot stands;
the journey lives in the task's state. The hunt tree's travel step runs journeys leg by leg (walk legs one goto at a time by `.nav`, the other legs
one tick at a time); a mark step after the loot and a rune-buying errand give core bots runes; the simulator gained the public moongates (the
gazetteer's gates, a gump on the gate, the response moves the bot) and Mark and Recall on a rune. Events `journey {dest, how, minutes, walk_minutes,
legs, options}`, `leg_failed`, `gate_used`, `rune_recall`.

**A simulator defect found on the way.** A `--procs` run's five parts each re-edited the run's `features.json` at start and raced: a part that read a
half-written file wrote back only its own ten names, so the first travel-planner pair ran twenty bots without the core and lost every other cohort,
and the plan 2 five-hour control ran with no features at all (its file is corrupt JSON), which is why that control read 14.7 kills against a clean
ten-hour control's 15.9. Only the parent process edits the cohorts now. The plan 2 ten-hour pair was clean on both sides and stands.

**The read** (the owner's new rule: one simulated hour per iteration, 50 bots, 5 processes, the farm's memory seeded, clean cohort files):

| Fighters, 1 h (20 bot-hours each) | Work | Travel | Rest | Kills / bot-h | Deaths / bot-h | Net worth / bot-h | Lost fights | Flips / bot-h | Rule-list rules | Exceptions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule list (`travel-1h-off`) | 20.0% | 47.8% | 15.5% | 32.5 | 0.20 | +63.8 | 8.4% | 53 | yes | 0 |
| Core with the travel planner (`travel-1h-on`) | 22.4% | 42.9% | 13.6% | 32.2 | 0.15 | +39.0 | 8.0% | 2.9 | none | 0 |

The first hour of a run is loot-rich for both arms (fresh spawns, full packs), so these rates are not the 5-hour ones. Kills at parity, deaths and lost
fights better, travel five points better, net worth lower (the rule list's first-hour loot sales). All 118 core journeys were walks: within the 320-tile
hunting radius no journey saves 150 tiles through a gate, and no fighter can cast Mark, so the gate and recall legs got no exercise here; they matter
for far errands, corpse runs and the ladder's dungeons, which is where the next item reads them. The planner's target (travel toward 25%) is not met in
the simulator; the travel that remains is the walk between an area's spots and to the shops, which is the ground model's, not the journey's.

**Where this leaves the capability plan.** 4b is built and safe; its read waits for item 5 (the world beyond Britain) where the legs apply. The one-hour
rule makes the next iterations cheap: about three minutes real for the control and eight for the core.

## Item 5: the world beyond Britain (capability plan item 5, built 2026-10-20 evening)

**The owner's rulings.** The price of entry to a dungeon rung is potions, bandages and the weapon skill at 80, no party required (2026-10-20). During the
build: "drop 'towns beyond britain' for now. britain is the hub, they all should be journeying to/from there", so the plan's third piece (the other towns'
ground and services, the reach widened to the moongate network, errands in whatever town the bot stands in) is **out**: every journey starts from and returns
to Britain, the errands sell, resupply, bank and buy runes in Britain, a ghost walks to a Britain healer, and the measure "a healer in another town" is dropped.
(The piece was built and taken out again the same evening; the gazetteer lookups by role from the bot's position stay as they were.)

**Built** (release check on the final tree **`0eaeac1-dirty+tree-7d381c9fc911`**, gates 3/3, 107 pass, 24 stale, smoke clean):

- **The rungs as tiers** (`spots.py`): the canonical creature spawners of the seven rung dungeons (Despise, Shame, Deceit, Covetous, Wrong, Destard, Hythloth;
  213 spawners) are spots with tiers above 3: level 1 of a dungeon is tier 4 (rung 1), its deeper levels tier 5 (rung 2), the Hot Zone (`shard-rules.json`
  `hotZones.dungeonRegions`: Hythloth) tier 6 (rung 3). A "level" is a walkable component of the new dungeon-side grid `walkgrid-dungeons.bin`
  (`make_walkgrid.py --x0 5120 --width 2048`, doors counted open, 244 KB): level 1 is what the entrance landing reaches on foot, through one inner teleporter
  when the landing is a small antechamber (Despise lands in 18 cells behind a stair teleporter). Despise 17 / 15, Shame 7 / 40, Deceit 11 / 23, Covetous 31 / 4,
  Wrong 6 / 3, Destard 13 / 7 spots on level 1 / deeper; Hythloth 36 at tier 6. A tour stays on one side and in one walkable component (a dungeon's stairs are
  teleporters), and each dungeon's best spot gets a seed in the tour choice, so the fourteen nearest spots no longer take every seat. Surface ground stays within
  320 tiles of home (the hub ruling); a dungeon door up to 900 tiles from Britain or from a public moongate is a journey a player makes (Despise is 540 from the
  bank; Hythloth's island door is beyond every gate and waits on Recall or camp travel, so rung 3 is in the model and out of reach on foot).
- **The price of entry as a precondition** (`task_core.py`): `kit()` is 3 Heal and 2 Refresh potions (the era's "Yellow Potion" / "Red Potion"), 20 bandages and
  the main weapon skill at 80; `rung_update()` opens the next rung only when the kit is carried AND the rung below has paid `RUNG_PAY` (10) kills recorded on its
  tier (`facts["rung_kills"]`, folded at every hunt's end from the task's tier: for rung 1 the surface's tiers 2 and 3, since a fighter at 80 hunts both; then the
  rung's own tier). `facts["rung"]` persists across restarts (`BotBase.PERSIST`); event `rung {from, to, why}`. `tiers()` offers the rungs' tiers only while the
  kit is carried: a bot that spends its potions is back on the surface until it restocks (the resupply errand buys both). The danger model's say stays in
  `spot_prior` (`fightable`, `kind_risk` with the tier's pack size), the fight step's retreat line stays. Plan 1's open question 2 is answered: the rungs open.
- **Travel across sides** (`travel.py`): a destination on another side of the map gets a journey of `tele` legs (`plan_cross`: `tele.py`'s `tele_route` over the
  gazetteer's pairs and the pairs bots have seen, each hop a leg between same-side journeys that may themselves take the gate or a rune), and inside a dungeon a
  destination no walk reaches gets the stair teleporters between components (`plan_inner`, `spots.inner_hops`); the hop step is `tele_hop` once, judged by the
  side and the landing. A task on another side allows it (`tele_allow`) at its start and every tick, so the goto wrappers may cross; `route_length` no longer
  calls another side unreachable. `walkroute.py` knows the dungeon grid (`WalkMap.side_map`, `dungeon()`): a plan across sides is None, a plan on the dungeon side
  uses the dungeon grid. Events `tele_used {to_side, land}`, `leg_failed {leg: tele}`. One regression the release check caught and this fixed: `far.py`'s
  far walk read "the land grid has no tile there" as a dungeon end and left it to the goto wrapper's teleporter crossing; with the dungeon grid answering, a
  corpse run from Britain into a dungeon was planned as a land walk and failed (`test_tele.py`, `test_tele_v5.py` stale). A far walk across sides now always
  takes the crossing. The one-hour reads above ran before this fix and before a rung's opening cleared the ten-minute spot cache; neither touches a surface walk.
- **The shared tour** (`task_core.tour2_candidates`, `hunt_tree.Buddy`): with a party member, else a buddy candidate (`buddy.py`), within 40 tiles, every tour of
  tier 4 or more comes again as a task "tour2" at 1.25 the score and 0.6 the death risk; the partner's own published tour2 (`buddy.json` now carries the core task,
  "core") is joined as the follower. In the tree a Buddy step heads the cycle: bandage the partner under 50% (`r_buddy_heal`), walk back when farther than 15
  tiles with nothing in hand, the follower takes the prey nearest the leader (one pulls, one heals), the loot by turns (the odd kills the leader's, the even ones
  the partner's, event `loot_turn`); a partner out of sight three minutes leaves the tour running alone (`tour2_alone`). `task_core.party_tick` gives `r_party` a
  turn every 5 s under the core (the rule list is bypassed), so invitations and acceptances still happen. `HunterBot.camp_fires()` reads partners' published fires
  (`buddy.json` "fire", from `facts["camp_fire"]`) for the planner's camp leg and `camp_travel_to()` works the `[CampTravel` list by the lighter's name; **no bot
  lights a travel fire yet**, so the camp leg stays unexercised (the lighter's side is the next piece).
- **The simulator** (`sim/`): the dungeon spawners of the seven rung dungeons on their own grid, teleporters (the gazetteer's 389 transitions: standing on an entry
  moves the bot to its exit, the entry tile always standable), a walk across sides answered "nopath" as the client does, routes over the dungeon grid, parties
  enough for two bots in one process to share a tour (`partyinvite` + `target`, `partyaccept`, `partyinfo` in Navrey's line format, `partyleave`, `partyloot`), a
  bandage on a party member, the healers' potions under the era's names (so the brains' purchases work), and **Between Worlds** after a resurrection (monsters
  cannot see the character until an attack, a cast or a skill, or ten minutes; the first one-hour core run had one bot killed three times in 25 s at 10 hit
  points beside the healer, which the live shard's flag prevents). Camp travel is not modelled. `sim/selftest.py` has 13 new checks (55 in all);
  `sim/item5_read.py <run>` reads a run (the fighters' row, the lost-fight share from the run's own window, the events by kind).
- **Tests** (`tests/test_task_core.py`, +130 lines in its style): the kit and the rung's opening (the kit alone opens nothing; the kills below open it; spent
  bandages or a skill under 80 take the rungs' tiers away while the rung stays), the dungeon spots' tiers (every rung dungeon has a level 1; Despise has deeper
  levels; Hythloth is tier 6; the entrance lands on level 1), rung 1 offers level 1 only and a bot without the rung gets no dungeon spot whatever its skill, the
  choice's dungeon tour with its side and `tele_allow` at the start, kills on tier 4 opening rung 2, the teleporter leg (walk / tele / walk, no walk across
  sides, a hop that does not jump fails the leg, no chain no journey), the hub ruling (surface ground within reach of home only; Despise's door is a journey from
  Britain, Hythloth's is not), the shared tour's choice (tier 4 or more only, the bonus, no partner no tour2, the joiner's follower candidate) and tree (follow,
  the leader's first loot, the partner's second).

**The one-hour reads** (the owner's rule: one simulated hour per iteration; 50 bots, 5 processes, the farm's memory seeded, clean cohort files; both arms with the
`party` and `buddy` features on so the shared tour could show; fighters only, 20 bot-hours each; lost fights from the run's own window):

| Fighters, 1 h | Work | Travel | Rest | Kills / bot-h | Deaths / bot-h | Net worth / bot-h | Lost fights | Flips / bot-h | Exceptions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rule list (`item5-1h-off`, first pair) | 16.4% | 33.7% | 14.9% | 21.5 | 0.25 | +44.7 | 10.5% of 228 | 120 | 0 |
| Core (`item5-1h-on`, first pair: tier-3-only rung rule, no Between Worlds) | 21.5% | 39.7% | 14.7% | 28.2 | 0.46 | +39.2 | 10.3% of 358 | 2.9 | 0 |
| Rule list (`item5-1h-off`, final pair) | 14.7% | 34.8% | 15.3% | 22.9 | 0.36 | +39.7 | 9.8% of 265 | 128 | 0 |
| Core (`item5-1h-on`, final pair) | 16.9% | 42.1% | 16.1% | 22.3 | 0.46 | +48.7 | 13.7% of 248 | 3.5 | 0 |

What the first pair taught: no rung opened in an hour because the 80+ fighters hunt tier 1 and 2 ground (20 to 52 kills an hour there, none on tier 3), so
"the rung below" for rung 1 became the surface's tiers 2 and 3; and the core's extra deaths were one bot resurrected at 10 hit points beside the healer and
killed three times in 25 seconds by a cat and a bird (the simulator lacked Between Worlds). In the final pair one rung opened (BotFairSwordVR, 25 kills on tier
2, kit 3 heal, 3 refresh, 30 bandages, skill 88) 44 minutes in; the bot then went to sell and the hour ended before its next hunt choice, so no dungeon task
started in an hour: 116 journeys, all walks, kills recorded on tier 1 (100) and tier 2 (243), one party formed. The core's deaths (0.46 against 0.36: 9 against
7 fighter deaths) are again mostly one bot (BotMaceCR, 3; giant rats and a snake); the one-hour reads are noise at this size, as the earlier reads showed.

**The final read is the one-hour pair above.** The owner's word during this build (2026-10-20 evening): simulator runs for testing are one hour only, so the
five-hour pair the brief planned was stopped and is not part of this record.

**Against the owner's pass rule and the plan's measures** (the final one-hour pair; the owner's rule: kills 1.1x and net worth above decide, deaths, lost
fights and travel not worse):

| Number | Read | Verdict |
| --- | --- | --- |
| Kills 1.1x the rule list | 22.3 against 22.9 (0.97x) | not met: parity, as every one-hour read of the core has been |
| Net worth above | +48.7 against +39.7 | met |
| Deaths not worse | 0.46 against 0.36 (9 against 7 deaths, one bot 3 of them) | not met by two deaths |
| Lost fights not worse | 13.7% of 248 against 9.8% of 265 | not met by 4 points |
| Travel not worse | 42.1% against 34.8% | not met (the core walks to spots and shops it chose; the one-hour travel reads have run 33% to 48% on both arms) |
| Fighter net worth a bot-hour toward +100 | +48.7 | half way |
| Deaths under 0.25 a bot-hour for veterans | 0.46 (0.36 for the rule list) | not met in an hour |
| A bot seen using a moongate | no journey took the gate: within the hub's 320 tiles none saves 150 tiles | not seen |
| A bot seen using a teleporter | no dungeon tour started in the hour (one rung opened at minute 44) | not seen |
| A bot seen using a camp fire | no bot lights a travel fire | not seen |
| A healer in another town | dropped (the hub ruling) | out |
| `farm_release.py --check` on the final tree | `0eaeac1-dirty+tree-7d381c9fc911`: gates 3/3, 107 pass, 24 stale (the counts before item 5), smoke clean | met |

The two deciding numbers split (net worth up, kills at parity) and the one-hour pair is one sample of twenty bot-hours an arm: the brief's five-hour read would
have shown the rungs (a rung opens at about three quarters of an hour of hunting and the dungeon tour is a quarter of an hour's walk), the five-hour rule-list
control of plan 2 read 0.79 deaths a bot-hour against the core's 0.49 with the same code, and the ten-hour read is where the core beat the rule list on both
deciding numbers. On the owner's "one hour only" word this record carries the one-hour numbers as they are; the item is built, tested on fakes and in the
simulator's own checks, and its live read (the rungs, the teleporters, the gate) waits for a night on the farm.

**What is left.** A rung's ground is chosen on the same score as every tour (expected progress a minute over the walk and the fights): a kills-judged goal rarely
sends a bot 540 tiles to Despise for the same twelve kills it finds nearer home, a gold-judged one does when the loot table says the dungeon pays; whether the
live fighters reach a dungeon in a night is the live read. The camp-fire leg waits on a bot that lights a travel fire (the lighter publishes
`facts["camp_fire"]`). Hythloth (tier 6) is in the model and out of reach on foot: Recall or camp travel. The other towns are out by the owner's ruling. The
rung's price of entry is checked each time the tiers are asked, never cached.

## Fixes from the live hour and the simulator corrected against it (2026-10-21)

**What the live hour (2026-10-20 20:59-21:59) taught, and what was built** (release check on the final tree **`0eaeac1-dirty+tree-0758c2a19078`**, gates 3/3, 106 pass, 25 stale; `test_gather_risk.py` is flaky on its own, a time-decay bound, in code this work does not touch):

1. **Predictions calibrated** (`task_core.calib`, `record_calib`): every expected kills, gold and skill figure is multiplied by a measured/expected ratio per task kind, group and measure, seeded from the hour (0.056 kills, 0.005 gold), learnt at each hunt's end (farm.db `task_calib`).
2. **Poison:** a snake is no prey (`NO_PREY`); the Cure potion is the first item the restock buys.
3. **Hurt with nothing to heal with** (`hurt_bare`): under a third of health, no bandage and no Heal potion: the hunt ends ("hurt") and a pressing rest errand takes the bot to a refuge and rests it to 95%.
4. **Escapes counted** (`kill_share`): a kind's worth is multiplied by its kill share (rabbits escaped 48 of 64 fights); peaceful animals within two tiles are judged by worth too (the first corrected-simulator read had the core lose 29 of 44 rabbit fights).
5. **Judged before the first blow** (`judge_target`): the danger model's say on the target with the hostiles around it.
6. **Undead ground** (`death_ground`): two of a bot's own deaths within 60 tiles, or one to a wraith, spectre, shade or lich, closes that ground to it for six hours; ranged bots under 45 stamina leave a losing fight 15 points earlier.
7. **One town visit:** in town after an errand, every errand due at urgency 0.5 or more is done before the next hunt.
- **Why the shop step bought nothing:** the one Britain healer lists 32 to 40 bandages and restocks hourly; twenty bots each asking for 60 emptied it by 21:00. The restock now asks for 40 bandages, 5 Heal, 3 Refresh and 3 Cure potions (Cure first), takes 300 out of the bank when carried gold is short, ends "done" only when the pack holds more than before, and, the owner's addition, cuts bandages from cloth when the healer is out (folded cloth at 3 gold each; a bolt of cloth only for a pack with none left and 400 gold).
- **Hunting time:** the camp wait is counted from arrival, the look-around is 4 seconds, a wait for a due respawn is capped at 60 s, the next roam spot is chosen by the shared respawn clock (due and near first, spots already in view last), and a sell category no shop took is not raised again for 30 minutes.

**The simulator corrected** (the Watcher's eight gaps, all in before any run): creatures that do not attack on sight flee under half their hit points; the engine's Lesser poison (4 to 16 a tick, 2.25 s, ten ticks); casters hit from range (11 tiles); shops restock hourly and their lists are the live ones (self-check); a hit takes at most 3 stamina and running costs none unless overloaded; speech keywords act inside a sentence; the first quarter hour can be dropped (`--warmup`); Between Worlds after a resurrection. `sim/calibrate.py --run <run>` compares a run with the live hour measure by measure (`sim/live_reference.json`), and `farm_release.py --check` reports it without gating. Net worth now also counts what a bot holds (`holdings`, `wealth_per_h`): consumables at the shop's selling price, the rest at the shops' real buy-back records, a stack beyond 40 at a quarter.

**The reads** (40 simulated minutes, the first 10 dropped, 50 bots, 5 processes, three seeds; fighters; the owner asked for 40-minute runs and for averages after the same tree swung deaths from 0.21 to 0.75 between runs):

| Fighters, 40 min, 3 seeds | Kills / bot-h | Deaths / bot-h | Gold + bank / bot-h | Lost fights | Travel | Camp |
| --- | --- | --- | --- | --- | --- | --- |
| Rule list | 15.0 | 0.46 | +34.8 | 31.0% | 32.9% | 2.4% |
| Core, before the camp and roam fixes | 9.8 | 0.75 | +7.0 | 32.6%* | 39.6% | 16.4% |
| Core, final tree | 11.8 | 0.74 | +13.0 | 31.4% | 48.1% | 11.9% |

*Lost fights are read from both `memory/` and `memory-newbie/` (15 of the 50 simulated bots are newbie-mode and write to the second; the first readings, and this row, used `memory/` only). The core's row before the fixes was not re-read.

The core is still behind the rule list in the simulator: kills 0.79x, deaths 0.74 against 0.46 (spectres and wraiths killed 13 of the core's 27 deaths and 9 of the rule list's 18), travel 48% against 33%; lost fights are level (31.4% against 31.0%), as they are live (the Watcher's corrected live reads: 43% of 1,224 core and 42% of 1,200 rule list overnight, 47% of 341 in the live hour). The holdings-inclusive net worth gap (+34 against +259 on the earlier prices) came largely from a few rule-list bots hoarding 100 or more raw ribs priced at 8 gold when the butcher pays 4; the valuation was corrected afterwards and the arms are not re-run on it yet. The first calibration against the live hour: kills 12.7 against 8.9, deaths 0.64 against 0.47, unmet errands 2% against 7%, lost fights about 25 to 31% against 47% (rabbits 31 to 41% against 75%, rats 19% against 100%): the simulator still under-states how many fights are lost, the creature kinds that escape being the gap.

**Left:** the gap in kills is search time (the core roams and camps 45% of the hour, the rule list 35%), and its travel share rose when the camp was cut; the graveyard undead kill both arms; the live hour decides all of it. The owner's word: run the farm for one hour once the progress is substantial, compare it with the simulator and refine the simulator on the deviation.

## What phase 2 needed (written before phase 2; kept for the record)

- **The other eight tasks** of the plan's table (sell, resupply, bank, rest, train, upgrade, camp, loot-and-carve) as short trees with the same shape, the
  existing `shop_at`, `sell_items`, `visit_bank`, `bandage_self`, `next_upgrade` code made non-blocking where it waits on a walk. Until then a core bot
  buys arrows through the old `r_resupply` code from inside the hunt tree and never sells, banks or upgrades: the plan's phase 2 measures (net worth a
  bot-hour) cannot be read on phase 1, and a long live run would leave core hunters with full packs and no bandages.
- **The bards' play step** between fights (Peacemaking, Provocation on two hostiles) in place of `r_music`; in phase 1 a bard under the core hunts
  without music.
- **`evaluate.py` reads `task_end` reasons** and the `task` decision rows (why, expected against actual, by area and band), which is also what the
  watcher's scorecard should show instead of rule episodes for core bots.
- **The priors want the farm's numbers.** The spawner-content prior (2 kills an hour a spawner, 120 s a kill beyond the time to kill, a third of
  `loot_value`'s gold ceiling, 0.15 / 0.05 / 0.01 skill points a kill by band) was set from the farm's 9 kills a bot-hour; the rate tables replace it as
  tasks end. The first live hours should be read for the gap between expected and actual in the `task_end` events, and the constants moved.
- **Walk speed and routes**: `facts["walk_rate"]` is only measured by the far walks; a core bot that never takes one keeps the 55 tiles a minute default.
- **The reflexes' hand-offs**: a flee or an avoid cancels the tree's walk and the tree re-issues it (counted correctly in travel); a long reflex hold
  (a corpse run) leaves the task's budget running, so a task can end "done" with little work after a death. Phase 2's rest task and the death-recovery
  layer should pause the budget.
- **The waits and the kill-rate gap.** 15% of a core bot's time went to the two-minute wait task because every area it knew was banned, resting,
  vetoed (a deadly kind, the danger map, a shared blocked spot) or crowded (`fields.CROWD`); the rule list falls back to any memory cell with a sighting.
  Phase 2 should give the choice the rule list's wider ground (the memory's hunting cells and the patrol ring as "areas" of their own), let two bots share
  a large area, and shorten the hour ban of a "yield" task on an area that paid before. The 31 "unreachable" tasks a run are the simulator's route grid
  refusing destinations walkroute accepts; live, the client's planner decides, and the shared blocked-spot record keeps the loss to one bot.
- **The dungeon rungs** stay off (`MAX_TIER` 3); the ladder (recommendation 4) opens them in phase 3 with the owner's word.
- **The live A/B** (phase 3): `farm_release.py --check`, the `task_core` cohort set to the ten `fields` bots, `--ab-open 2`, the five-number scoreboard
  before and after.

## The live hour, 2026-10-20 20:59-21:59 (the watcher's read)

All 20 HunterBot-family fighters ran on the decision core: release 7d381c9fc911 from 20:59 to 21:44, then e9898f6d4016 (the watcher-coordinated fixes: resupply, gear goal, no_ground fallback) to 21:59. The two control columns are live runs, read the same way (ep durations, kills and died from decisions.jsonl; lost = fight records in memory/*.jsonl and memory-newbie/*.jsonl not "kill" (corrected 2026-10-21: the first read counted memory/ only, giving 36% / 50% / 45%); net worth = carried + bank from farm.db decision contexts, first to last record). Work = the fight, hunt, loot and camp steps, or the rule list's r_fight, r_hunt, r_loot and r_camp.

| Live run | Bot-hours | Work | Lost fights | Kills / bot-h | Net worth / bot-h | Deaths / bot-h |
| --- | --- | --- | --- | --- | --- | --- |
| Rule list, 10 fighters, overnight 10-19/20 | 79.2 | 16% | 42% of 1,200 | 8.1 | +16 | 0.13 |
| Core, 10 fighters, overnight 10-19/20 | 78.3 | 51% | 43% of 1,224 | 7.7 | +17 | 0.23 |
| Core, 20 fighters, tonight's hour | 19.2 | 30% | 47% of 341 | 8.9 | +72 | 0.47 (9 deaths) |
| ... the first 45 min (7d381c9fc911) | 14.3 | 29% | 46% | 9.2 | +128 | 0.49 |
| ... the last 15 min (e9898f6d4016) | 4.9 | 32% | 44% | 8.2 | -80 (restocking) | 0.41 |

task_end reasons over the hour: done 143, switch 64, yield 29, unmet 19, unreachable 7, stale 5, crowded 1. no_ground 8 (7 after the fix), ground_relaxed 4, rung 1.
Exceptions: none (0 EXCEPTION lines in all 20 run.logs since each brain's last start).

Bugs found:
1. **Major, fixed in part: resupply bought nothing.** Before the fix, 8 of 20 bots ended resupply errands "done" with 0 gold spent; BotFenceAdvR held 2,680 banked and BotMaceBR idled 20 minutes ("no hunt area is open" plus a gear goal met every 3 s). After e9898f6d4016 the errand ends "unmet" honestly, but it STILL buys nothing: BotMaceAdvR (495 carried, 1,548 banked) "arrived" at the shops at 1471,1611 (twice) and 1469,1668 and logged "nothing bought (bandages 1 ...)". Five other bots logged "still short of bandage". The shop step itself fails silently: no vendor found at the spot, or no bandage on its list. Next: log the vendor and the list seen at shop_at, and check the shared memory's vendor_selling('bandage') spots against the Britain healers and provisioners.
2. **Missed: think_aloud never ran.** The code is in e9898f6d4016, but features.json has no think_aloud cohort, so 0 think events. The owner asked for it to watch in the client.
3. Deaths: 0.47 per bot-hour, against 0.23 for the core overnight and 0.13 for the rule list. Most of the hour ran without bandages (bug 1).
4. Minor: a hunt task carried over from overnight ended "after 799.9 min" (BotMaceBR): a stale persisted task. Kills per bot-hour are up (8.9 against 7.7 and 8.1); lost fights are still high (45%).

### Learnings from the hour (the watcher, 2026-10-21; the owner: send all seven)

1. **Predictions are uncalibrated.** 105 hunt tasks expected 2,455 kills and 95,975 gold; they got 137 kills and 491 gold (kills 18x, gold about 195x too high). Every choice (where to hunt, when to leave, whether an errand pays) is made on these numbers. Calibrate each expected value against the measured result for that kind of task, area and spot, and shrink unmeasured ones toward the measured mean.
2. **Poison kills: running does not cure it.** Snakes killed 3 of the 9 (BotBardAR, BotRangerBR, BotArcherCR). Each death shows 4-point poison ticks for 20-26 s after the bite, with the bot in r_flee. Cure first (a Cure potion, or a bandage where Healing and Anatomy allow it), then move. A snake is no prey: it drops nothing.
3. **Hurt with nothing to heal with.** A boar, an eagle and a swallow killed bots at 1-2 hit points (BotBardBR, BotBardAdvR, BotArcherCR; each had hp_min10 1-2). Below a third of health with no bandage or Heal potion, end the hunt and go home; never start a fight hurt.
4. **Rabbits.** 64 fights, 48 lost (escaped), about 43 s each: some 45 minutes of the hour. Rats 4 of 4 escaped. The worth floor does not stop them (carve value, or fights against whatever is near). Count escapes into a kind's worth: worth x kill rate less time.
5. **Engaged, then fled.** Orcs 7 of 7 and giant rats 6 of 6 ended in flee within about 10-20 s. Judge the target before the first blow, with the danger estimate the bot already makes.
6. **Undead north of Britain** (about 1320-1480 x 1360-1440): wraiths and spectres killed BotRangerBR, BotArcherCR (twice) and BotMaceCR. MaceCR died to a wraith 11 tiles off (30 + 16 damage, probably spells). Rangers and archers have 37-39 stamina. Mark the area deadly for these bots, and give ranged bots an earlier leave threshold.
7. **More time walking to shops than fighting.** Fighting and pursuit 12% of the hour, camp 17%, travel to hunts 13%, errand walks 18% (resupply 9, upgrade 5, sell 4). 64 hunts ended "switch", often after 2 minutes. One town visit should do every errand due (sell, bank, restock, upgrade), followed by a long hunt; a need ends a hunt only when it is pressing.

The gear-goal spam (BotMaceAdvR 1,664 core_goal events, BotFairSwordNR 1,547, BotMaceBR 964) stopped with e9898f6d4016: none after 21:44.

### What the simulator misses, against the live runs (the watcher, 2026-10-21)

The simulator's core runs against the live core runs:

| Measure | Simulator, core, 1 h (`travel-1h-on`) | Simulator, core, 4 h (`core-on-4h-e`) | Live, core, overnight (10 bots) | Live, core, the hour (20 bots) |
| --- | --- | --- | --- | --- |
| Kills / bot-h | 32.2 | 11.3 | 7.7 | 8.9 |
| Lost fights | 8% | 15% | 43% | 47% |
| Deaths / bot-h | 0.15 | 0.25 | 0.23 | 0.47 |

It gets the direction about right (core near the rule list on kills) but the levels badly wrong: lost fights 3-6 times too low, kills 1.2-4 times too high, the hour's deaths about 3 times too low. Its verdicts on fights and safety can't be trusted until these close. Gaps, by cost:

1. **Creatures never run** (world.py: a creature attacks, steps toward its target or wanders). Live, prey runs: rabbits escaped 48 of 64 fights, rats 4 of 4, hinds and eagles often. That one gap is most of the lost-fight difference. It's also why the simulator could never show the core wasting 45 minutes an hour on rabbits. Model a flee AI per kind (animals flee below some health, or at once for the timid kinds), at their real speed.
2. **Poison is too weak.** Simulator: 2 damage, with a 1-in-5 chance each second (about 0.4 a second), a 25% chance per snake or spider hit. Live: 4-point ticks for 20-26 s finished three bots. Use the engine's Lesser/Regular poison (damage and interval from the server's Poison table, with its duration), so a cure-or-die choice exists in the simulator.
3. **No ranged spells.** A caster creature adds 5-12 damage to 25% of its melee swings. Live, a wraith did 30 + 16 from 11 tiles (BotMaceCR), and spectres and wraiths killed 4 bots north of Britain. Give casting kinds spell range (about 10 tiles), cast time and spell damage from SPELL_DAMAGE.
4. **Shops always sell.** world.buy succeeds whenever the vendor is within 6 tiles and holds the item. Live, resupply bought nothing at 1471,1611 and 1469,1668 with gold in the pack. The simulator ran 26 of 33 resupplies done, so it hid the defect. Once the live cause is known, model it (the vendors' real lists from shops.json and the shared memory, real stock and restock, the bot standing out of the vendor's reach). Add a selftest that the simulator's vendor list for each Britain shop equals the live one.
5. **The first hour is loot-rich** (the evidence's own note: fresh spawns, full packs). The simulator's one-hour runs read 32 kills a bot-hour against 8.9 live. Seed one-hour runs from a snapshot of a world that has run for a while (spawns thinned, packs as the farm's), or discard a warm-up.
6. **Stamina and speed.** Rangers and archers have 37-39 stamina live and can't outrun undead. Check that the simulator's stamina drain on running and in fights, and creature speeds, match (calibrate.py measures walking speed only).
7. **Speech keywords.** Live, a bot's speech can open a bank box or a shop list (think_aloud had to rephrase them), and guards answer "guards". The simulator's say() does none of it. Model the keyword triggers, so a speech change is tested.
8. **Calibrate on more than time shares.** calibrate.py compares time shares, kills, deaths, gold and walking speed for a day. Add the lost-fight share by kind, deaths by cause (killer kind, poison or not, health before), errand outcomes (done / unmet) and predicted against actual task value. Make a calibration against the latest live window part of farm_release.py --check, with tolerances.

## The sim-comparison hour, 2026-10-21 10:35-11:36 (the watcher's read, release 0758c2a19078)

20 core fighters, 19.5 bot-hours, no restarts, no exceptions, think_aloud on (195 lines). The data pack is in work/botfarm-watch/hour-20261021-1035.json (both memory folders).

| Live, core | Work | Lost fights | Kills / bot-h | Net worth / bot-h | Deaths / bot-h |
| --- | --- | --- | --- | --- | --- |
| Overnight 10-19/20 (10 bots) | 51% | 43% of 1,224 | 7.7 | +17 | 0.23 |
| The hour 10-20 20:59 (20 bots) | 30% | 47% of 341 | 8.9 | +72 | 0.47 |
| **This hour (the seven learnings)** | 24% | 52% of 381 | 8.8 | -16 | 0.51 (10) |

- **Prey worth did not take.** Rabbits: 95 fights, 82 lost (escaped). Rats: 54 fights, 44 lost. Both are worse than the previous hour (64/48 and 4/4). The escape rate in worth, and judging before the first blow, are not stopping these fights.
- **Bandages.** The healer's list had no bandages at any of 39 reads all hour; resupply ended unmet 12 times against 16 done. BotMaceBR said "Next: restock at the healer, I have 0 bandages" again and again. The provisioner and cloth routes did not cover the shortfall.
- **Death loop.** BotMaceBR died 5 times (10:44 to 11:26), hunting the south with 0 bandages: at 1270-1516 x 1943-2376, among lizardmen, a giant spider, a bone mage, dire and timber wolves, an ettin and a troll. Health before death was 1-11. Its "No ground open, too risky, waiting" fallback, then its relaxing, led it there. The other deaths: a giant rat, a dog, a great hart, a headless one, a wraith.
- **Calibration.** Better, but still far off: 89 hunts expected 725 kills and 25,295 gold, and got 161 kills and 353 gold (4.5x and about 72x, against 18x and 195x before).
- Time: roam 19%, fight 13%, travel 10%, camp 8% (+4% camp task), errand walks about 6%. task_end: hunt yield 38, switch 21, resupply done 16 / unmet 12, rest done 14.
