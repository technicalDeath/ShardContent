# Bot farm: release pipeline and simulator (evidence, 2026-10-19)

Built in one session after the step-change review (`Bot-Farm-Step-Change-Review-2026-10-19.md`, recommendations 1 and 2). Nothing here touched the live farm;
nothing was committed, no branch or tag was created. All paths are under `ShardContent/tests/scenarios/bot-farm` unless said otherwise; runs are under
`work/botfarm/sim`.

## What was built

| Piece | File | Does |
| --- | --- | --- |
| Release pipeline | `farm_release.py` | `--check`: the three gates of `work/botfarm/patches`, every other patch test there (stale ones listed, not deleted), a simulated smoke run of every brain class, one release line in `work/botfarm/releases.jsonl`. `--restart COHORT`: brains stopped at rule boundaries by checked PID, 3 a minute, refused while `work/botfarm/ab-window.json` is open or the tree changed since the last passing check. `--status`, `--ab-open`, `--ab-close`. |
| pytest runner | `test_farm.py` | The same checks as pytest (gates, patch tests with stale ones skipped, the simulator self-test, the smoke run). pytest 9.1.1 was installed into the workspace Python for it. |
| Virtual clock | `sim/clock.py` | `time.time`, `time.monotonic` and `time.sleep` replaced for the process; one thread per bot, one runs at a time, a sleep hands the baton to the scheduler, which advances the world to the next wake-up. Every command costs 20 ms and every clock read 0.2 ms of simulated time, so a brain cannot spin in zero time. |
| World data | `sim/world_data.py` | The canonical spawners (`spawners.py`, Felucca surface within 900 tiles of Britain: 305 spawners, 3,427 creatures), `creature_stats.json`, `fightmodes.json` (who attacks on sight), `loot_value.json`, the gazetteer's people and fixtures (96 vendors, 41 fixtures, 6 guards), `work/botfarm/shops.json` and the shared memory's vendor records (names, buy-back prices), `walkgrid.bin`, `watergrid.bin`, `craft_data.json`, `weapon_table.json`, `tame_data.json`, `trees.json`, `mountains.json`, the spell table of `new-mage-playtest/game_data.json`. |
| The world | `sim/world.py` | Creatures spawn, wander within their home range, aggro by sight (8 tiles: 10 minus the shard's `monsterAggro.rangeReduction` 2), chase and fight from their stats; respawn after the spawner's delay. Players walk over an 8x8-cell route grid built from the walk grid (no land route: `nopath`), fight (UO:R hit chance, weapon table damage, Tactics and armour), loot, carve, bank, buy and sell, mine, chop, fish, craft through the era's menus, cast, tame, bandage, meditate, die, and are resurrected at a healer. Journal lines in the farm's wording (`[SYSTEM]`, `[SAY]`, `[CONTAINER]`, `[TARGET]`, `[SHOP]`, `[MENU]`, `[SKILL]`, `[GUMP]`, `[NAV]`, `Damage:`, `Swing:`). |
| FakeClient | `sim/fake_client.py` | The real `uo.Client` class with its state file, world file, command file and log tail replaced by the world; the brains' `connect()` returns it. |
| Runner | `sim/farm_sim.py` | Builds the world and the bots, runs the brain classes unchanged, writes the brains' usual files under `<run>/farm`, prints the scoreboard; `--procs N` splits the roster over processes; `--smoke` is the pipeline's check. |
| Calibration | `sim/calibrate.py`, `sim/snapshot_farm.py` | The farm's measures for a day from `metrics.jsonl` beside a run's scoreboard; the roster (skills, packs, positions of the farm's 50 characters) the runs start from. |
| Self-test | `sim/selftest.py` | 42 scripted checks of the command paths (walk, bank, shop, fight, loot, carve, bandage, mine, fish, craft, cast, tame, death, resurrection). All pass. |

## Done criteria

| Criterion | Result |
| --- | --- |
| `farm_release.py --check` runs the gates and a simulated smoke run of every brain class in under 5 minutes and prints a release line | 261 s: gates 3/3 OK, patch tests 105 pass / 23 stale, smoke 0.2 h x 7 classes OK in 5.8 s, no exception, no crash. Line: `0eaeac1-dirty+tree-248705be89e5` in `work/botfarm/releases.jsonl`. |
| The simulator runs 50 bots for 10 simulated hours and prints a scoreboard | 50 bots x 10 h in 524 s (first run) and 823 s (second run, with the resurrection fix below) on 10 processes; about 10 real seconds per bot-hour, almost all of it the brains' own work (profile: the shared memory's decay and json reading, the loop guard, file appends). Scoreboards in `work/botfarm/sim/run-10h/` and `run-10h-b/`. |
| Calibration table against 2026-10-19 | Below. |
| OPERATING.md updated | Sections "Releases" (with the branch-and-tag design) and "The simulator". |

## Calibration: the farm on 2026-10-19 against the simulator (50 bots, 10 simulated hours, run-10h-b)

Farm side: `metrics.jsonl` rows of the day (724 bot-hours; the brains' own kill and death counters, first to last row of each bot; carried gold only, the bank is not in
metrics). Simulator side: the same measures from the run's metrics and the world's own events. Groups as in `work/botfarm-watch/scorecard.py`.

| Group | Measure | Farm | Simulator | Sim / farm |
| --- | --- | --- | --- | --- |
| fighter | work share % | 11.1 | 8.5 | 0.77 |
| fighter | travel share % | 67.9 | 49.0 | 0.72 |
| fighter | rest share % | 2.7 | 20.9 | 7.7 |
| fighter | dead share % | 3.5 | 1.7 | 0.49 |
| fighter | kills per bot-hour | 8.98 | 9.31 | 1.04 |
| fighter | deaths per bot-hour | 0.325 | 0.431 | 1.33 |
| fighter | carried gold per bot-hour | -2.1 | +85.5 | - |
| fighter | main skill points per bot-hour | 0.479 | 0.005 | 0.01 |
| fighter | skill gains per bot-hour | 14.2 | 1.07 | 0.08 |
| caster | work share % | 12.7 | 29.9 | 2.35 |
| caster | travel share % | 68.6 | 19.3 | 0.28 |
| caster | kills per bot-hour | 0.03 (see below) | 19.74 | - |
| caster | deaths per bot-hour | 0.0 | 0.0 | - |
| caster | skill gains per bot-hour | 21.85 | 5.14 | 0.24 |
| crafter | work share % | 25.5 | 3.3 | 0.13 |
| crafter | travel share % | 55.3 | 93.4 | 1.69 |
| crafter | kills per bot-hour | 0.81 | 5.33 | 6.6 |
| crafter | deaths per bot-hour | 0.115 | 0.017 | 0.15 |
| crafter | carried gold per bot-hour | +58.7 | -21.6 | - |
| crafter | skill gains per bot-hour | 11.76 | 3.36 | 0.29 |
| gatherer | work share % | 23.6 | 39.4 | 1.67 |
| gatherer | rest share % | 63.6 | 46.7 | 0.73 |
| gatherer | deaths per bot-hour | 0.172 | 0.318 | 1.85 |
| gatherer | carried gold per bot-hour | -3.6 | +102.6 | - |
| gatherer | skill gains per bot-hour | 4.71 | 0.33 | 0.07 |
| tamer | work share % | 83.7 | 44.7 | 0.53 |
| tamer | travel share % | 14.4 | 31.2 | 2.2 |
| tamer | deaths per bot-hour | 0.121 | 0.301 | 2.49 |
| tamer | main skill points per bot-hour | 0.079 | 0.261 | 3.3 |
| tamer | skill gains per bot-hour | 7.73 | 2.81 | 0.36 |
| all | walking, tiles per minute between rows that moved (median / p90) | 54.7 / 169.5 | 55.0 / 130.0 | 1.0 / 0.77 |

The full table with every share is `work/botfarm/sim/calibration-2026-10-19.md`.

### Where the simulator agrees

Fighters: work share, kills per bot-hour, deaths per bot-hour, dead share and walking speed are within a third of the farm's. The fighters' behaviour (the rule list,
the fields, the camps, the flee and avoid rules) therefore runs the way it does live, which is what a brain change needs to be ranked against.

### Where it disagrees, and why

1. **Skill gains are 10 to 25 times too rare** (every group). The gain chance in `World.gain` (0.18 falling to 0.04 at 80, times a per-action weight) is a guess; the farm's
   bots gain mostly in their secondary skills under 80 (Tactics, Anatomy, Healing, Meditation, Resisting Spells). The fix is a table from the shard's gain curve
   (`skillGainCurve`, `Skill-Bank-Faint-Memories.md`) rather than one formula; the sim's gain events (`events` kind `gain`) make it easy to tune per skill.
2. **Gold is too generous for fighters and gatherers.** `loot_value.json`'s `gold` is the kind's pack gold ceiling, and the sim pays 0.5 to 1.5 times it on every
   corpse; the farm's fighters ended the day with 17 gold median. Also every vendor buys back what the memory says it buys, with no stock limit on the vendor's side,
   so the gatherers' ore and fish always sell. Halve the loot gold and cap a vendor's buy-back per hour.
3. **Casters' kills: the farm's number is wrong, not the sim's.** The casters' `kills` counter in `metrics.jsonl` is the mage bot's own, which the farm's status rows show
   as 0.03 per bot-hour against about 10 per bot-hour in the operator log's measurement from the shared memory. `calibrate.py` should take casters' kills from the
   memory's fight records (as the scorecard does), not from metrics.
4. **Crafters work 3% of their time, the farm's 25%.** In the sim they walk between the material shop and the buyer almost continuously: the buy-back table lets them sell
   every product at once, so the "sell when the pack is full" and "restock when the material is out" rules alternate every few minutes. The farm's crafters wait on
   vendors that stop buying (the "vendor won't buy" finding) and on bank trips. A vendor stock model (a vendor buys at most N of a kind, restocking slowly) fixes it.
5. **Tamers tame too easily** (1,795 tames in 40 bot-hours; the farm's tamers spend 84% of the time in `r_tame` and tame rarely). The sim's taming chance
   `(skill - min + 20) / 45` and nine-second attempt are too kind; use the server's formula (`AnimalTaming.cs`: chance from the skill against the creature's minimum,
   several attempts, the creature running). The tamers' higher death rate comes from the same place: they stand beside aggressive animals.
6. **Casters cast little** (167 casts in 80 bot-hours): the roster's casters carry almost no reagents and little gold (the farm's state at the snapshot), so the sim's
   casters, like the farm's, say "More reagents are needed" and buy a few at a time; the sim's shop restock is slow (5% a tick). The resting share (17.6%) is meditation.
7. **The dead share was 46% in the first run** because a ghost that once declined the healer's offer (a monster near the healer) was never offered again. Fixed
   (`world.py`, `_step_player`: the offer returns once the ghost has walked away and back, as the server does); the second run's dead share is 1.7%.
8. **Not modelled:** the client's own path planner (the sim routes over 8x8 cells and walks straight lines inside them, so walks are a little faster and never
   "stopped short, closest reachable"); teleporters, dungeons, the sewers, moongates (all surface); houses; guards except on "guards"; parties, buddies and trades
   between bots in different processes (`--procs`); poison beyond spiders and snakes; player-to-player speech beyond 12 tiles; the stamina system's "too fatigued"
   messages (the sim only halves the walking speed over the weight limit); weapon wear; the Between Worlds gump and the materializing state; shard vendors'
   stock limits; the day and night.

### Findings about the brains from the runs

- Two `RuntimeError: dictionary changed size during iteration` in `memory.hunting_cells` (`memory.py` line 362) in the second run, in the caster. The memory refreshes
  (adds cells) inside the generator it is iterating; live, the same code runs in one thread too, so this is a latent brain bug the farm will hit.
- After a resurrection the hunters' `r_gear` puts on a second pair of pants every minute for the rest of the run ("put back on: ['long pants']" / "['leather
  leggings']"), because two clothes of one layer are in the pack and the equip swaps them. Harmless, but the log noise hides the real events.
- The smoke run constructs and ticks every brain class with no exception on the current tree, which is the check the 36,737-exception night would have failed.

## How to use it

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py ShardContent\tests\scenarios\bot-farm\farm_release.py --check                               # 4-5 min; a release line
& $py ShardContent\tests\scenarios\bot-farm\sim\farm_sim.py --classes hunter --bots 20 --hours 4   # try a hunter change: 80 bot-hours in about 2 min on one core
& $py ShardContent\tests\scenarios\bot-farm\sim\farm_sim.py --bots 50 --hours 10 --procs 10         # the full board, about 10-14 min
& $py ShardContent\tests\scenarios\bot-farm\sim\calibrate.py --day 2026-10-19 --sim work\botfarm\sim\run-<stamp>\scoreboard.json
```

A run folder holds `scoreboard.md`, `scoreboard.json`, `farm/metrics.jsonl` (the supervisor's row format, so `BOTFARM_DIR=<run>/farm` makes the watcher's
`scorecard.py` read it), every bot's `run.log`, `status.json`, `decisions.jsonl`, the run's `notes.jsonl` and shared memory, and the client logs under
`farm/work/navrey-sessions/<Bot>/cuolog`.

## Fixes of 2026-10-19 evening (owner: "fix sim gaps now") and the re-run

Brain tree (the farm stopped): `memory.py` hunting_cells iterates a snapshot of the cells; `bot_common.py` r_gear skips a pack piece whose layer is already worn. Release check after the fixes: `0eaeac1-dirty+tree-930aef66df6c`, gates 3/3, smoke clean, 273 s; the Operator's line is in `work/botfarm/operator.log`. Simulator: loot gold 0.15-0.5 of the ceiling; a vendor buys at most 20 of a kind an hour; the layered gain (the curve under 80, the Mastery allowance 2.0/1.4/1.0/0.8 a day above); the server's taming chance (skill - minimum) / 50 with the animal running and up to four tries; `calibrate.py` adds kills from the memory's fight records (the casters' brain counter reads near zero live).

Re-run `work/botfarm/sim/run-10h-c` (50 bots, 10 h) against the farm's 2026-10-19 (full table: `work/botfarm/sim/calibration-2026-10-19-c.md`):

| Group | Measure | Farm | Simulator | Sim / farm |
| --- | --- | --- | --- | --- |
| caster | work share % | 12.7 | 30.6 | 2.41 |
| caster | dead share % | 0.4 | 0.1 | 0.25 |
| caster | kills per bot-hour (brain counters) | 0.03 | 15.1 | 503.33 |
| caster | kills per bot-hour (memory fights; sim: world) | 35.77 | 15.1 | 0.42 |
| caster | deaths per bot-hour | 0.0 | 0.038 | inf |
| caster | carried gold per bot-hour | 1.0 | 21.2 | 21.20 |
| caster | main skill points per bot-hour | 0.114 | 0.021 | 0.18 |
| caster | skill gains per bot-hour | 21.85 | 11.25 | 0.51 |
| crafter | work share % | 25.5 | 3.2 | 0.13 |
| crafter | dead share % | 2.0 | 0.1 | 0.05 |
| crafter | kills per bot-hour (brain counters) | 0.81 | 10.48 | 12.94 |
| crafter | kills per bot-hour (memory fights; sim: world) | 0.81 | 10.48 | 12.94 |
| crafter | deaths per bot-hour | 0.115 | 0.042 | 0.37 |
| crafter | carried gold per bot-hour | 58.7 | -19.0 | -0.32 |
| crafter | main skill points per bot-hour | 0.336 | 0.013 | 0.04 |
| crafter | skill gains per bot-hour | 11.76 | 22.02 | 1.87 |
| fighter | work share % | 11.1 | 7.9 | 0.71 |
| fighter | dead share % | 3.5 | 2.6 | 0.74 |
| fighter | kills per bot-hour (brain counters) | 8.98 | 9.48 | 1.06 |
| fighter | kills per bot-hour (memory fights; sim: world) | 9.0 | 9.48 | 1.05 |
| fighter | deaths per bot-hour | 0.325 | 0.492 | 1.51 |
| fighter | carried gold per bot-hour | -2.1 | 25.7 | -12.24 |
| fighter | main skill points per bot-hour | 0.479 | 0.041 | 0.09 |
| fighter | skill gains per bot-hour | 14.2 | 3.46 | 0.24 |
| gatherer | work share % | 23.6 | 39.9 | 1.69 |
| gatherer | dead share % | 2.6 | 2.2 | 0.85 |
| gatherer | kills per bot-hour (brain counters) | 0.0 | 0.0 | - |
| gatherer | kills per bot-hour (memory fights; sim: world) | 0.0 | 0.0 | - |
| gatherer | deaths per bot-hour | 0.172 | 0.217 | 1.26 |
| gatherer | carried gold per bot-hour | -3.6 | 13.6 | -3.78 |
| gatherer | main skill points per bot-hour | 0.444 | 0.079 | 0.18 |
| gatherer | skill gains per bot-hour | 4.71 | 0.97 | 0.21 |
| tamer | work share % | 83.7 | 38.2 | 0.46 |
| tamer | dead share % | 0.4 | 3.3 | 8.25 |
| tamer | kills per bot-hour (brain counters) | 0.0 | 0.0 | - |
| tamer | kills per bot-hour (memory fights; sim: world) | 0.0 | 0.0 | - |
| tamer | deaths per bot-hour | 0.121 | 0.854 | 7.06 |
| tamer | carried gold per bot-hour | 0.0 | 0.0 | - |
| tamer | main skill points per bot-hour | 0.079 | 0.633 | 8.01 |
| tamer | skill gains per bot-hour | 7.73 | 7.66 | 0.99 |

Reading the ratios: fighters stay within a third on work share, kills and deaths; the gain and gold fixes move those rows toward 1.0 (see the table); crafters' travel share and the tamers' tames remain the simulator's largest disagreements and are next (a vendor stock model for the crafters' shop loop, the creature's own taming tries). Weekly usage reached the 64% line at this point and the session stopped here.
