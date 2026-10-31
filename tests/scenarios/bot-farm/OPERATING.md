# Operating the bot farm (for agents)

This is the handover for an agent that has to watch the bot farm, read what the bots produce, or steer it. Read it before touching anything.
The design and the brains are in `README.md` in this folder; this file covers running, reading and steering. Workspace rules in the root `CLAUDE.md` still apply.

## What is running

| Piece | What it is | Where |
| --- | --- | --- |
| Server | ModernUO on the **disposable host `farm`**, a copy of the dev world (not the real dev saves), port 2593 | `work/hosts/farm`, logs in `work/dev-server/logs/server-*.log` |
| Clients | One headless Navrey client (`dotnet.exe ... Navrey\bin\Debug\net10.0\cuo.dll`) per bot, about 400 MB each | sessions in `work/navrey-sessions/<Bot>/` (`session.json` has the client PID) |
| Brains | One Python process per bot (`hunter.py`, `caster.py`, `crafter.py`, `fisher.py`, `miner.py`, `tamer.py`) that plays the character through the client | `work/botfarm/<Bot>/` (`brain.pid`) |
| Supervisor | `supervisor.py`: every ~15 s restarts a dead client or brain, kills a brain that has written no status for 4 minutes, stops the lowest-priority bots when available memory falls under 450 MB (and brings them back over 1,700 MB), and every 5 minutes rebuilds the report and the evaluation | `work/botfarm/supervisor.log` |
| Shared memory | What the bots learn about the world, shared by all of them | `work/botfarm/memory/` |

The roster is the plan files `work/botfarm/plan-all.json`, `plan-more.json` and `plan-adv.json` (one `{"name", "profession"}` per bot; Advanced characters also have `"create": "createui {name} Advanced <4 skill ids>"`).
The supervisor reads them only when it starts.

## The one tool: `farmctl.py`

Use it from the workspace root with the workspace Python (`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`; plain `python` is not on PATH):

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py ShardContent\tests\scenarios\bot-farm\farmctl.py status
```

| Command | Does | Changes anything? |
| --- | --- | --- |
| `status` | Server and supervisor PIDs, available memory, the dashboard (one line per bot: hit points, kills, deaths, gold, rule, activity, top skills) | no |
| `health [--minutes 10]` | What each bot has been doing over the window, flags bots that are not moving | no |
| `eval [--minutes 30]` | Grades the bots' decisions and prints the **fix-first** list (writes `work/botfarm/evaluation.md`) | writes the evaluation file |
| `report` | Rebuilds `work/botfarm/report.md` (findings by category, skill gains, shared memory) and prints its headings | writes the report |
| `bot NAME` | One bot: status, last log lines, last decisions, last notes | no |
| `tail NAME [-n 40]` | The end of a bot's `run.log` | no |
| `notes [--bot B] [--category C] [-n 30]` | The newest findings | no |
| `memory` / `memory --kind K [-n 20]` | Shared-memory summary, or the newest events of one kind (`fight`, `sight`, `death`, `loot`, `vendor`, `craft`, `res`, `claim`, `blocked`, `gain`, `presence`) | no |
| `pause NAME` / `resume NAME` | The brain idles (the character stands still) / plays again | yes, that bot |
| `cmd [--keep-paused] [--timeout S] NAME COMMAND...` | Runs one Navrey command as that bot (for example `cmd BotMaceA skills`, `cmd BotFisherA pos`), pausing its brain around it. Options go before the name | yes, that bot |
| `restart NAME... \| all` | Stops brains by recorded PID **after checking the PID is that brain**; the supervisor starts them again with the current code (`all` goes in batches) | yes |
| `shed NAME` / `unshed NAME` | Stops a bot's client and brain through `work/botfarm/shed.txt`, or brings it back | yes |
| `supervisor start\|stop\|status` | Starts the supervisor with all plan files, stops it (the bots keep running, nothing restarts them), or shows its last log lines | yes |

Read-only commands are always safe. For anything in the "yes" rows, see the rules below.

## Files to read directly

All under `work/botfarm/`:

| File | Contents |
| --- | --- |
| `dashboard.txt`, `dashboard.json` | One line per bot, rewritten every ~15 s |
| `metrics.jsonl` | One line per bot per minute: hp, gold, kills, deaths, gain count, skills, rule, position |
| `notes.jsonl` | **The findings.** One line each: `t`, `bot`, `profession`, `category` (death, danger, combat, healing, potions, bank, shop, sell, money, loot, craft, cook, fish, mine, tame, chop, training, weight, music, stuck, bot, message), `text`, `key` (a bot records each key once) |
| `report.md` | Notes grouped and counted across bots (what many professions trip over comes first), skill gains, the shared memory |
| `evaluation.md` | The decision grading: fix-first list, time and yield per profession and rule, shared-memory health |
| `supervisor.log` | Restarts, sheds, watchdog kills |
| `<Bot>/status.json` | That bot's heartbeat (every 10 s): rule, activity, hp, position, gold, kills, deaths, skill gains, top skills |
| `<Bot>/run.log` | What the brain did, in plain text (rule changes, fights, purchases, crafts, exceptions) |
| `<Bot>/decisions.jsonl` | `ep` lines: each stretch of one rule with its yield (`dur`, `gold`, `kills`, `gains`, `hp`, `died`, `moved`); `mem` lines: a decision the shared memory overturned |
| `<Bot>/hang.txt` | A Python stack if a tick took more than 150 s (empty when fine) |
| `<Bot>/knowledge.json`, `menu_map.json`, `totals.json` | Places that killed the bot and kinds it avoids; a crafter's learned menu; lifetime counters |
| `shops.json` | The last stock list seen at each shop |
| `memory/world.jsonl`, `memory/prof-<Profession>.jsonl` | The shared memory's event logs (see below) |

The client side of each bot is in `work/navrey-sessions/<Bot>/`: `cuolog` (the client's own log), `cuostate.json` (live state), `cuoworld.json` (what it sees).

## The shared memory

Append-only JSON lines; every bot reads them incrementally and folds them into dicts (`memory.py`, class `SharedMemory`). `world.jsonl` holds facts for everyone: monster sightings and kills by 40x40 map cell, deaths, gold looted, shop stock and buy prices, gathering spots that work or are blocked, claims (a bot working a spot), presence (where bots are, for crowding). `prof-<Profession>.jsonl` holds what only that profession uses: fight results by monster kind (time to kill, share of hit points lost, deaths, flees), craft attempts and skill gains per item, which action raised which skill. Kills, gold and fight records fade with a half-life (30 minutes for a cell's kills, 2 hours for deaths and fight records).

To read it from code:

```python
import sys; sys.path.insert(0, r"ShardContent\tests\scenarios\bot-farm")
import memory
m = memory.SharedMemory("Archer", "my-agent")      # a profession whose file you want, and a name for yourself
print(m.summary())                                  # fights, best cells
print(m.fight_stats("troll"))                       # how archers have fared against trolls
print(m.vendor_selling("ingot"), m.hunting_cells())
```

An agent may add knowledge by appending events with `m.record(kind, scope="world", ...)` in the formats listed at the top of `memory.py`; the bots pick them up within 20 seconds. Do not edit or truncate the files while bots run (they read by byte offset).

## Talking to a bot's client yourself

`farmctl.py cmd` is the safe way. For a longer script, pause the bot first, then:

```python
import sys
sys.path[:0] = [r"Navrey\cli", r".claude\scripts"]
from navrey_session import connect
c = connect("BotMaceA")              # the session in work/navrey-sessions/BotMaceA
print(c.x, c.y, c.hp, [i.name for i in c.backpack])
print(c.call("help"))                # every Navrey command
```

Two drivers on one client interleave commands and confuse each other, so never script a bot whose brain is not paused. Resume it afterwards.

## Changing the bots

1. Edit the brain in `ShardContent/tests/scenarios/bot-farm/` (shared behavior in `bot_common.py`).
2. Check the syntax: `& $py -c "import ast; ast.parse(open('FILE', encoding='utf-8').read())"`.
3. `farmctl.py restart NAME...` for the bots that use it (or `restart all`). Watch `supervisor.log` and the bots' `run.log` for `EXCEPTION` lines.
4. Run `farmctl.py eval` after 10 to 30 minutes and compare with the previous `evaluation.md`.

Adding a bot: append it to a plan file, start its client with `farm_launch.py --plan <a plan with just that bot> --reserve-mb 1100`, then `supervisor stop` and `supervisor start` so the supervisor knows it. Each client costs about 400 to 450 MB; check `status` first.

## Rules (do not break these)

- **Never stop processes by name.** The server and every client are `dotnet.exe`, every brain is `python.exe`. Stop only by recorded PID after checking the command line (`farmctl.py restart` does this). A recorded PID can be reused by an unrelated process after the original dies.
- **One operator at a time.** Before restarting, shedding, editing brains or stopping the supervisor, check `supervisor.log` for another agent's recent actions. Write a line to `work/botfarm/operator.log` saying who you are and what you are changing. Reading needs no coordination.
- **The farm host is disposable,** but it holds the port: the dev server (`ModernUO/Distribution`) cannot run at the same time. Do not start a second server.
- **Secrets:** `work/accounts/*.env` and each session's `.env` hold the bots' passwords. Never print or commit them.
- **`work/` is never committed.** Code changes go to the ShardContent repository and are committed only when the owner allows it.
- **No bot goes into the Britain sewers** (owner, 2026-10-18: "terrible hunting grounds and 1 lane corridors make it awful to navigate"). `HunterBot.SEWERS_BANNED` refuses it in code, whatever a `features.json` cohort or an ambition says. Don't re-add a `sewers` cohort. A bot that finds itself below climbs out (`r_sewer_out`, why `off`). `work/botfarm/patches/test_sewer_ban.py` checks this.
- **Runes, Mark and Recall** (owner, 2026-10-18; feature `runes`, `runes.py`): a bot with enough Magery buys blank runes, marks home and far grounds, and recalls on far walks. Runes are known by serial only, because the Backpack Ward looks the same to the client. Events are `rune_buy`, `rune_mark`, `rune_recall` and `rune_fail`. Tests: `test_runes.py`; the live run is in `work/runes-live/`.
- **Memory:** keep available memory above about 500 MB. The supervisor sheds bots by itself under 450 MB; when adding bots, check first.
- The owner wants a short progress line at least every five minutes during long runs, and quality-of-life findings worth acting on go into `ShardContent/docs/To-Do-List.md` only when the owner asks.

## Starting from nothing

```powershell
. .\.claude\scripts\Use-Toolchain.ps1
& .\.claude\scripts\Start-DevServer.ps1 -DistributionPath work\hosts\farm      # the farm host's server (one server per port)
& $py ShardContent\tests\scenarios\bot-farm\farm_launch.py --plan work\botfarm\plan-run2b.json --parallel 2 --reserve-mb 1100   # the 50-bot roster (plan-all.json is the old 12 "A" bots)
& $py ShardContent\tests\scenarios\bot-farm\farmctl.py supervisor start --hours 8
```

To stop everything: `farmctl.py supervisor stop`, then stop each client by the PID in its `session.json`, then `Stop-DevServer.ps1 -DistributionPath work\hostsarm` (the farm's own server only).

## Releases: the pipeline instead of live patching (2026-10-19)

The review of 2026-10-19 (`docs/Bot-Farm-Step-Change-Review-2026-10-19.md`) found that string-replacement patches on the live tree, hand-recorded md5s and
restart storms were where the agents' time went. A brain change now goes through one script, and every live number can be tied to a release id.

```powershell
& $py ShardContent\tests\scenarios\bot-farm\farm_release.py --check                 # gates + patch tests + a simulated smoke run of every brain class; a release line
& $py ShardContent\tests\scenarios\bot-farm\farm_release.py --restart casters        # the cohort onto the checked tree, 3 brains a minute, at rule boundaries
& $py ShardContent\tests\scenarios\bot-farm\farm_release.py --release --cohort all   # both
& $py ShardContent\tests\scenarios\bot-farm\farm_release.py --status                 # the last release lines, the A/B window, whether the tree changed since the check
& $py -m pytest ShardContent\tests\scenarios\bot-farm\test_farm.py -q                # the same checks as pytest (stale patch tests show as skipped)
```

- **The check** runs the three gates in `work/botfarm/patches` (`test_no_shadow`, `test_borrow`, `test_main_last`), then every other `test_*.py` there (a test that fails
  under both folder conventions is *stale* and only listed; it is not deleted), then `sim/farm_sim.py --smoke`: one bot of every brain class (hunter, bard, caster,
  crafter, tamer, fisher, miner) constructed and run for 0.2 simulated hours against the simulator's FakeClient. Any exception in a tick, or a brain that cannot be
  constructed, fails the check: the crash classes of run 2b (a hidden method, a borrowed member, code after the main block, a missing attribute) show up here, at no
  farm cost. The whole check takes about three minutes. It appends one line to `work/botfarm/releases.jsonl` (release id, gate results, patch-test tallies, the smoke
  scoreboard, the cohort) and writes the detail to `work/botfarm/sim/release-check-latest.json`.
- **The release id** is `git describe --tags --dirty` of the ShardContent checkout plus `tree-<hash>`, a content hash of every brain file (`bot-farm/*.py`, `sim/*.py`,
  `new-mage-playtest/mage_bot.py` and `knowledge.py`). The hash is what the restart checks: a restart is refused when the tree changed since the last passing check.
- **The restart** stops brains at rule boundaries: it touches the bot's `pause` file (the brain honours it at the top of its next tick, so nothing is killed mid-walk,
  mid-fight or mid-trade), waits for `status.json` to say `paused` (90 s at most), stops the brain by a PID checked against the process table (`farm_launch.is_brain`), and
  removes the pause file; the supervisor starts the brain again on the current tree. At most `--per-minute` bots a minute (default 3), so a farm-wide release takes about
  17 minutes and never resets fifty fights at once. A cohort is `all`, a feature name of `features.json` (its treatment list), a plan file, or a comma list of names.
  Every restart writes `operator.log` and a `restart` line in `releases.jsonl`.
- **The A/B window** is `work/botfarm/ab-window.json` (`--ab-open HOURS --ab-note TEXT`, `--ab-close`). While it is open (its `until` in the future, or no `until`), every
  restart is refused unless `--force`: a measurement window has no restarts in it, which is what the scoreboard-per-release idea (review, recommendation 6) needs.

**Branch and tag (designed, not yet created: the owner decides when the brain tree gets its branch).** The brain tree is tracked in the ShardContent repository with
large uncommitted changes. The flow once the owner says so:

1. `git -C ShardContent checkout -b farm/brains` and the first commit of the tree as it is (everything under `tests/scenarios/bot-farm` and `new-mage-playtest`; `work/` stays
   out of git as always).
2. A change is a commit on that branch; `farm_release.py --check` is run on the working tree, and when it passes the commit is tagged `farm-YYYYMMDD-N` (`git tag farm-20261020-1`).
   `git describe --tags --match farm-*` then gives the release id without the `-dirty` suffix, and `releases.jsonl` carries the tag.
3. The supervisor and `farm_launch.py` pin a tag: a file `work/botfarm/release.txt` holds the tag the farm runs; `supervisor.start_brain` starts brains from a checkout of
   that tag (`git worktree add work/botfarm/tree-<tag> <tag>`, one worktree per tag, removed when no brain runs on it), not from the live tree, so an edit to the tree
   never reaches a running brain by accident, and "which code is this bot running" is the tag in `status.json`. `farm_release.py --restart` moves `release.txt` to the new
   tag before the restarts; a rollback is `--restart all --tag farm-20261019-3`.
4. The patch scripts, the backup folders and the md5 bookkeeping in `work/botfarm/patches` are retired: the tests there move into `tests/scenarios/bot-farm/tests/` as pytest
   files (the gates first), and `test_farm.py` runs them.

Until step 1, the release id is the content hash and the restart refuses a tree that differs from the last passing check, which gives most of the safety already.

## The simulator (2026-10-19)

`sim/farm_sim.py` plays the unchanged brain classes against a simulated shard built from the farm's own data (the canonical spawners, creature stats, the walk and
water grids, the gazetteer's vendors and fixtures, the shops seen, the shared memory's buy-back prices, the craft tables). Fifty bots for ten simulated hours take
about ten minutes on ten processes; one bot-hour costs about ten real seconds, almost all of it the brains' own work. The scoreboard prints the farm's measures (rule
time shares by group as in `work/botfarm-watch/scorecard.py`, kills and deaths per bot-hour, gold and skill gains per bot-hour, exceptions by brain class), and
`sim/calibrate.py --day YYYY-MM-DD --sim <run>/scoreboard.json` puts them beside the farm's day. What is modelled, what is not, and where it disagrees with the farm:
`docs/Bot-Farm-Simulator-Evidence.md`.

```powershell
& $py ShardContent\tests\scenarios\bot-farm\sim\snapshot_farm.py                    # the roster: the farm's 50 characters (skills, packs, positions) -> work/botfarm/sim/roster.json
& $py ShardContent\tests\scenarios\bot-farm\sim\farm_sim.py --bots 50 --hours 10 --procs 10   # a run; scoreboard in work/botfarm/sim/run-<stamp>/
& $py ShardContent\tests\scenarios\bot-farm\sim\farm_sim.py --smoke --hours 0.5               # one bot per class, exit 1 on any exception
& $py ShardContent\tests\scenarios\bot-farm\sim\selftest.py                                    # the simulator's own 42 checks (walk, bank, shop, fight, loot, mine, fish, craft, cast, tame, death)
& $py ShardContent\tests\scenarios\bot-farm\sim\calibrate.py --day 2026-10-19 --sim work\botfarm\sim\run-<stamp>\scoreboard.json
```

A run's files are under its own folder (`<run>/farm/`: `metrics.jsonl`, `<Bot>/run.log`, `notes.jsonl`, `memory/`, `work/navrey-sessions/<Bot>/cuolog`), never under
`work/botfarm` itself; `BOTFARM_DIR=<run>/farm` makes the watcher's scorecard read a run. To try a brain change: edit, `farm_sim.py --classes hunter --bots 20 --hours 4`,
compare the scoreboard with the previous run's, then `farm_release.py --check` and `--restart`.

## The decision core (2026-10-19, phase 1: the hunter)

`docs/Bot-Farm-Decision-Core-Plan.md` built for `HunterBot` (and `BardBot`; `CrafterBot` is excluded by class, `TASK_CORE = False`) behind the feature **`task_core`**
(`features.json`; the cohort is EMPTY until the owner opens the A/B in phase 3: the planned treatment is the ten `fields` bots, under `_planned`). A bot with
the feature runs the reflexes at the top of its rule list unchanged (`BotBase.REFLEXES`: `r_dead`, `r_corpse`, `r_gear`, `r_cure`, `r_flee`, `r_avoid`,
`r_sewer_out`, `r_heal`) and then `task_core.tick()` instead of every rule below them; the stall sense, the progress check and the loop guard's rule back-offs
are off for it (`core_active()`), the loop guard's server-refusal reading stays. Without the feature nothing changes.

- `task_core.py`: the goal (`facts["core_goal"]`, from the persona and `goals.py`), the task (`facts["task"]`: area, expected kills / gold / skill an hour, budget,
  the tree's state; a restarted brain resumes it), the choice (expected goal progress a minute net of the walk and the risk; a Thompson draw over the farm.db rate
  tables `task_kills` / `task_gold` / `task_skill` keyed `hunt|group|band|area`, so unmeasured areas are tried; commitment and a five-minute dwell), the monitor
  (every 60 s: on track / under with one extension / failed; two deaths fail; a failed task and area are banned an hour, `facts["core_bans"]`), the decision
  records (farm.db `decisions`, kind `task`, closed with why / expected / actual by `farmdb.decision_close`).
- `hunt_tree.py`: the hunt task as a py_trees tree (travel in legs with `.nav` read each tick, pick, pursue, fight, loot the bot's own kill), the failures
  `unreachable`, `empty` (75 s nothing in sight, the area rests 30 min), `crowded` (two other bots on the pack).
- The acted rule of a core bot is `task:<task>:<step>` (`task:hunt:fight`, `task:hunt:travel`, `task:hunt:camp`, ...): `status.json`, `metrics.jsonl` and the
  episodes in `decisions.jsonl` show it; `sim/farm_sim.py` and the scorecard class the steps as work / travel / camp / rest. Events: `core_goal`,
  `core_goal_end`, `task_start`, `task_arrived`, `task_extend`, `task_switch`, `task_end {why, expected, actual}`.
- Tests: `tests/test_task_core.py` (run by `farm_release.py --check` and `test_farm.py` with the patch tests; a failure fails the check). Simulator runs:
  `sim/farm_sim.py --classes hunter,bard --bots 20 --hours 4 --with-feature task_core` against `--without-feature task_core`; the scoreboard now carries the
  lost-fight share, the rule flips a bot-hour and which rule-list rules acted (none for core bots). Evidence: `docs/Bot-Farm-Decision-Core-Evidence.md`.
- Phase 2 (not built): the other eight tasks (sell, resupply, bank, rest, train, upgrade, camp, loot-and-carve as a task), the bards' play step; until then a
  core bot buys arrows through the old `r_resupply` code from inside the hunt tree and never sells, banks or upgrades.
- **The world beyond Britain (capability plan item 5, 2026-10-20).** The dungeon rungs are the spot tiers above 3 (`spots.py`: level 1 of Despise, Shame, Deceit,
  Covetous, Wrong and Destard is tier 4, their deeper levels tier 5, the Hot Zone Hythloth tier 6; a level is a walkable component of `walkgrid-dungeons.bin`,
  made by `make_walkgrid.py --x0 5120 --width 2048` with doors open). A rung opens (`task_core.rung_update`, `facts["rung"]`, event `rung {from, to, why}`) when the
  tier below paid `RUNG_PAY` kills (`facts["rung_kills"]`) and the bot carries the price of entry (`task_core.KIT`: 3 Heal, 2 Refresh, 20 bandages, the weapon skill
  at 80; the owner's ruling, no party required); the rungs' tiers are offered only while the kit is carried. A tour on another side is reached by the journey
  planner's `tele` leg (`travel.plan_cross`: `tele_route`'s chain, each hop a `tele_hop`; inside a dungeon `plan_inner` takes the stair teleporters between
  components); the task allows its side (`tele_allow`). Britain is the hub (the owner, 2026-10-20: "drop 'towns beyond britain' for now"): surface ground stays within 320 tiles
  of home, every journey starts from and returns to Britain, the errands and the ghost's healer are Britain's; a dungeon door up to 900 tiles from Britain or a
  public moongate is reached with the gate as a leg. The shared tour (`tour2`, `task_core.tour2_candidates`, `hunt_tree.Buddy`): with a party member or buddy within 40 tiles every tour of
  tier 4 or more comes again at 1.25 the score and 0.6 the risk; one pulls, one heals, the loot by turns; the partner's published task (`buddy.json` "core") is joined
  as the follower; `task_core.party_tick` runs the party rule under the core. `HunterBot.camp_fires()` reads partners' published fires for the camp leg (no bot lights
  one yet). The simulator: dungeon spawners of the seven rung dungeons, the dungeon grid, teleporters (standing on an entry moves the bot), a walk across sides is
  nopath, parties (partyinvite / target / partyaccept / partyinfo / partyleave / partyloot), a
  bandage on a party member. `sim/item5_read.py <run>` reads a run: the fighters' row, the lost-fight share from the run's own window, the events by kind.
  Evidence: `docs/Bot-Farm-Decision-Core-Evidence.md`, "Item 5".
