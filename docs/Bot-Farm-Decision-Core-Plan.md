# Bot farm: the decision core (design and work plan, 2026-10-19)

Recommendation 3 of `Bot-Farm-Step-Change-Review-2026-10-19.md`, written on the owner's "do it" with the weekly usage ceiling (65%) one point away, so that the build can start the moment the window resets. Nothing here is built. The build runs in the simulator first (`Bot-Farm-Simulator-Evidence.md`) and goes live through `farm_release.py` as an A/B cohort.

## What it replaces, and what it keeps

Today a hunter walks a 22-rule priority list every tick; the first rule that acts wins. Six monitors beside the list (stall sense, loop guard, planner, ambitions, progress check, recovery) each measure progress their own way and can only veto rules. Measured result on 2026-10-19: fighters work 11 to 20% of their time, travel 62 to 70%, lose 46% of their fights, and flip between `r_avoid` and `r_fight` up to 86 times in half an hour.

**Kept, unchanged:** the reflexes at the top of the list (`r_dead`, `r_corpse`, `r_gear`, `r_cure`, `r_flee`, `r_avoid`, `r_sewer_out`, `r_heal`), the loop guard's reading of server refusals, the shared memory and `farm.db`, the danger model and danger map, the area file, the gazetteer, the fields' area knowledge, the ambition personas and `goals.py`'s goal candidates, the pacing layer, buddy and party, the owner's rules (no sewers, generality by lookup, danger by evidence and pack size).

**Replaced for bots with the feature `task_core`:** every rule below the reflexes (`r_loot`, `r_fight`, `r_lighten`, `r_fletch`, `r_wood`, `r_resupply`, `r_upgrade`, `r_bank`, `r_facility`, `r_hunt`, `r_rest`, `r_camp`, `r_sewer_in`, `r_explore`, and `r_music` for bards) and the rule back-offs of the stall sense, the loop guard and the progress check. Bots without the feature run exactly as today. `CrafterBot` inherits `HunterBot` and is excluded by class until its own task set exists.

## The model

**Goal.** One active goal per bot, from the persona (`ambition.py`) and the candidates `goals.py` already produces: a skill target (A3), a banked sum (A1, A2), a gear piece (A5), a ladder rung (A4). Re-picked when done, when its candidate disappears, or every two hours. The goal defines the **progress measure**: skill points, realized gold, or rung reached.

**Task.** A concrete activity with an expected yield and a budget:

| Task | Parameters | Expected yield (per the budget) | Budget |
| --- | --- | --- | --- |
| hunt | area (from `britain_areas.json` / fields), kinds allowed | kills, gold, main-skill gains | 20 min, extended once if on track |
| camp | a spawner | kills per respawn, gold | 2 respawn intervals |
| loot and carve | the corpse in view | gold, hides, meat | 2 min |
| sell trip | shops that buy what is carried (memory) | gold | walk time plus 5 min |
| resupply | a list (bandages, ammo, potions) and a budget | stock reached | walk time plus 3 min |
| bank | deposit above the purse, withdraw for a goal | gold safe | walk time plus 2 min |
| rest | until hp and stamina thresholds | none | 5 min |
| train | the dummy in town while Tactics or Anatomy is under its cap | gains | 10 min |
| upgrade | the goal's gear piece | the piece worn | walk time plus 3 min |

Expected yields come from `farm.db` rates per (profession, skill band, area or shop), with a prior from the area's spawner contents and `loot_value.json` when there is no record (the simulator's calibration table says how good those priors are). Cost is walk time (route length from `walkroute.py` at the bot's measured tiles per minute) plus risk (`danger.risk` for the area's kinds at the bot's skill and the pack size) times a death cost.

**Choice.** Each candidate is scored as expected goal progress per minute net of walk and risk. The running task keeps a commitment bonus and a minimum dwell of five minutes, so it is not re-chosen each tick. Unknown areas are tried in proportion to how little is known (a Thompson draw over the rate's uncertainty, `n` in `farm.db`), which replaces `EXPLORE_EVERY` and the random spot scatter. Every choice writes a decision record: the context, the candidates with their scores, the chosen task; the outcome is joined when the task ends.

**Steps.** Each task runs as a small behaviour tree (the `trade_tree.py` pattern, one tick per brain tick, every step re-checked, restart-safe through `facts["task"]`). The hunt tree:

```
[-] hunt                       guard: the task is still the chosen one and under budget
    --> travel to the area      non-blocking: issue goto once, read .nav each tick; nopath or 3 min over the estimate fails the task ("unreachable")
    {-} work the area           loop until the budget ends
        --> pick a target       prey by danger_ok and worth; crowded (2+ other bots on the pack) fails "crowded"
        --> pursue              up to 25 tiles and 20 s, re-plan on lost line of sight, chase re-issued goto; beyond that, drop the target (not the task)
        --> fight               attack until dead; hp under the reflex threshold yields to r_heal / r_flee, the task resumes after
        --> loot and carve      the kill's corpse only (never another bot's), carve when a blade is carried
        --> empty check         75 s with nothing in sight fails the task ("empty") and rests the area 30 min
```

Sell, resupply, bank, rest, train and upgrade are short sequences with the same shape; the existing `shop_at`, `sell_items`, `visit_bank`, `bandage_self` and `next_upgrade` code is reused inside the steps, made non-blocking where it waits on a walk.

**One progress monitor.** Every 60 s the task's actual yield is compared with the expected one: on track, under (extend the budget once), or failed (end the task, ban that task and area for an hour, record why). Two deaths inside one task fail it whatever the yield. This is the single replacement for the stall sense's rule back-offs, the loop guard's rule back-offs, the planner's switch and the progress check's rethink for `task_core` bots. Events: `task_start`, `task_end {why, expected, actual}`, `task_switch`.

**Bards.** The hunt tree's "work the area" loop gets a "play" step between fights (Peacemaking at the feet, Provocation on two hostiles) in place of `r_music`, so a bard's music is part of hunting, as a player's is.

## Generality and player-likeness

No coordinate appears in the core: areas come from the area file and the gazetteer, services by role from memory, home from the region. The scatter stays inside an area (a bot works the area, not a point). Walking in towns stays with the pacing layer. Sessions (log in, play, log out) are not in this item.

## Work plan

| Phase | Build | Pass in the simulator | Cost |
| --- | --- | --- | --- |
| 1 | `task_core.py`: goal, task, choice, monitor, decision records; the hunt tree; `HunterBot` reads it under the feature; the reflexes unchanged | 20 hunters x 4 h: work share 40% or more, lost fights 20% or less, no exception, no rule flips (the rule list is bypassed) | 1 day |
| 2 | The other eight tasks; bards' play step; stall, loop guard and progress check disabled for `task_core` bots; `evaluate.py` reads `task_end` reasons | 50 bots x 10 h full board: fighters work 50% or more, travel 30% or less, deaths at or under the farm's 0.33 per bot-hour, net worth per bot-hour above the rule-list hunters in the same run | 1 day |
| 3 | `farm_release.py --check`; A/B: `task_core` on 10 hunters (the `fields` split), control 10; `--ab-open 2`; the five-number scoreboard before and after | Live, 2 h: work share, lost-fight share, kills and net worth per bot-hour up on the cohort, deaths not up; then promote to all 20 | Half a day plus 2 farm-hours |
| 4 | Casters (and `CasterBot` inheriting `BotBase` properly), then crafters, gatherers, tamers, each with its own task table | The same measures per group | 1 day per group |

Usage: phases 1 to 3 are roughly two to three days of one session. The evening of 2026-10-19 cost about 11 weekly-usage points for about four hours of session work with the farm stopped, so budget 20 to 30 points for phases 1 to 3, and a fresh weekly window.

## Open questions for the owner

1. **How bold on unknown ground?** The Thompson draw will send a hunter to an unmeasured area about one task in five at first. Lower if deaths matter more than coverage.
2. **The dungeon rungs** (recommendation 4) stay off in this item; with them off, 84-skill fighters still hunt tier 3 surface ground at most. Say if the ladder should open in phase 3.
3. **The A/B split:** the ten `fields` bots as the treatment, or a fresh random ten.
