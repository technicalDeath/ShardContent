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
- **Memory:** keep available memory above about 500 MB. The supervisor sheds bots by itself under 450 MB; when adding bots, check first.
- The owner wants a short progress line at least every five minutes during long runs, and quality-of-life findings worth acting on go into `ShardContent/docs/To-Do-List.md` only when the owner asks.

## Starting from nothing

```powershell
. .\.claude\scripts\Use-Toolchain.ps1
& .\.claude\scripts\Start-DevServer.ps1 -DistributionPath work\hosts\farm      # the farm host's server (one server per port)
& $py ShardContent\tests\scenarios\bot-farm\farm_launch.py --plan work\botfarm\plan-all.json --parallel 2 --reserve-mb 1100
& $py ShardContent\tests\scenarios\bot-farm\farmctl.py supervisor start --hours 8
```

To stop everything: `farmctl.py supervisor stop`, then stop each client by the PID in its `session.json`, then `Stop-DevServer.ps1`.
