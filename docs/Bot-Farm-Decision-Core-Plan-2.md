# Bot farm: the decision core, plan 2: beat the rule list (2026-10-20)

Written on the owner's word after phase 2 ("make a plan to improve and beat the rule list"). Nothing here is built. The evidence it rests on is
`Bot-Farm-Decision-Core-Evidence.md` (phase 1, the live A/B, steps 1 and 2, phase 2); the machinery it keeps is `task_core.py`, `hunt_tree.py`,
`errands.py` as released at `0eaeac1-dirty+tree-ef7c2680c7b2`.

## The target

The core's hunters beat the rule-list hunters on the five-number scoreboard, in the same world, on a full board:

| Number | Beat means |
| --- | --- |
| Kills a bot-hour | at least 1.1 times the rule list's |
| Net worth a bot-hour (gold carried + banked, sales included) | above the rule list's |
| Deaths a bot-hour | not above the rule list's |
| Lost-fight share | not above the rule list's |
| Travel share | 30% or less (the rule list: 41 to 60%) |

Read first in the simulator (50 bots x 10 h, the control in the same run, the farm's memory seeded), then live (ten `fields` bots against the
other ten fighters, 8 hours, no restarts in the window). The live reading decides; the simulator's crowding is harsher than the farm's (the one
live night was kill parity where the simulator said -20%).

## Where the five rounds left it

| Round | Kills, core / rule list | Deaths | Lost | Travel | What the records blamed |
| --- | --- | --- | --- | --- | --- |
| Phase 1, 20 hunters, sim | 11.3 / 13.7 | 0.25 / 0.35 | 15% / 17% | 33% / 45% | 15% waits (every area banned or vetoed), unroutable areas |
| Live A/B, 10 v 10, 8 h | 8.9 / 8.8 | 0.21 / 0.13 | 36% / 30% | 19% / 60% | 45% camping, 12% waits, tier-3 pack deaths |
| Steps 1 and 2, sim | 10.7 / 14.6 | 0.24 / 0.30 | 16% / 18% | 28% / 50% | 29% camping, reflex time |
| Phase 2, full board, sim | 7.5 / 12.0 | 0.28 / 0.35 | 15% / 20% | 26% / 41% | 847 waits, 34% camping, sell errands unmet |

Every round took out the sink the records named and the time moved to the next sink, never into fighting. Deaths, lost fights, travel and rule flips
were won in round one and held; kills never were. The cause is the **ground model**: 21 fixed areas with a crowd cap per area, bans and rests per
area, camping per area. On a board where 40 bots share the farmland around Britain, a bot keeps finding every area closed and stands at a spawner
between respawns, while the rule list roams any remembered sighting, counts crowding per spot and fights what it meets. The rule list is sloppy
but dense; the core is tidy and hunts emptier ground.

## The plan

Four pieces, in order. Each names the change, the expected gain on the numbers, how it is measured, and its cost. The machinery around the hunt
(goal, task record, monitor, commitment, errands, reflexes) is kept as it is.

### 1. Per-spot ground: the hunt as a circuit of spots (the step change)

**Change.** The unit of ground becomes the **spot**, not the area: every canonical spawner within the bot's reach of home (the spawn files give its
place, its kinds, its count and its respawn delays; `spawn_delays` already reads them) and every memory cell with a sighting (the rule list's
ground). A spot carries: its kinds, the respawn clock (the shared memory's last kill at that cell, so one bot's kill tells every bot when the
respawn is due), the bots near it now (presence within 20 tiles: crowding **by spot**), the bot's own last visit, and its rate record. The hunt task
becomes a **circuit**: the choice picks a cluster of spots and orders them nearest-next (a greedy tour from the best cluster), scored as expected
kills a minute over the whole tour including the walks between spots; the budget is the tour's; empty and stale are judged **per spot** (a spot with
nothing now and no respawn due within two minutes is passed, not camped); a spot with another bot on it is skipped unless it holds three or more
creatures; the tour returns to a spot whose respawn is due. Camping only at a due respawn, as now. The Britain areas stay as tier and danger labels
for the spots inside them; the rested-area fallback and the wait task go.
**Expected gain.** Waits to nil (there is always a spot), camping under 10%, the walk between spots counted as the hunt's work the way the rule
list's r_hunt is; kills at or above the rule list's, because the core then hunts the same ground with a plan instead of a random walk.
**Measure.** `task_end` by spot, the tour's expected against actual kills, kills a bot-hour against the control in the same run.
**Cost.** About four hours of one session. The largest piece.

### 2. Fight what is met, everywhere

**Change.** The pick radius becomes the view range (18 tiles) on the walk between spots and on the travel leg alike, the "safe ground" filter is
dropped for prey within 8 tiles (the danger model still judges the kind and the pack), and a kill on the way updates the spot clock of the nearest
spot. The retreat exit stays.
**Expected gain.** The rule list's density of fights without its flips; a few kills a bot-hour.
**Cost.** An hour.

### 3. Errands that finish

**Change.** The sell errand gets its own act (a buyer by role from the memory's vendor records, a second shop when the first refuses, what no shop
buys dropped) instead of the rule list's sell rules with their "a hostile within ten tiles" refusal (two of three sell errands were "unmet"). The
resupply errand buys bandages and ammunition for the next tour's expected fights, not a fixed 40. The bank errand's purse limit follows the goal
(goals.py's purse) as it does for the rule list.
**Expected gain.** Net worth a bot-hour above the rule list's (the core already keeps more of its loot; it only has to sell it).
**Cost.** An hour.

### 4. Learning per spot, and the records read back

**Change.** The rate tables are keyed by spot cell (group, band, cell) and seeded from the shared memory's kills per cell, so a spot other bots
have worked is not "unmeasured"; the Thompson draw stays. `evaluate.py`'s task section ranks spots by expected against actual, which is the watcher's
read. The simulator runs seed the farm's memory (`--memory-from work/botfarm/memory`), so the grounds exist from the first minute as they do live.
**Expected gain.** The choice converges on the paying spots within an hour instead of re-learning each run.
**Cost.** An hour.

## Verification and pass

1. Unit tests in `tests/test_task_core.py` for the spot model (spots from spawners and sightings, the respawn clock from a shared kill, crowding by
   spot, the tour's order and score, per-spot empty and stale) and the new sell act; `farm_release.py --check` passes.
2. Simulator, the full board (50 bots x 10 h, 5 processes, the farm's memory seeded), core on against core off: the five numbers for fighters, and
   the core's `task_end` reasons. Pass: the target table above, in the simulator.
3. Live: the Operator starts the farm on the checked tree, the ten `fields` bots on the core, `--ab-open 8`, no restarts or patches in the window;
   the five numbers from `metrics.jsonl` and the memory's fight records in the morning. Pass: the target table, live. Then promote to all 20
   fighters for a second night, and only then to the other classes (phase 4 of the first plan).
4. If the simulator passes and the live night does not, the live records (`task_end` by spot) say which piece missed; one more round on that piece,
   not a new design.

## Cost and usage

About a day of one session for pieces 1 to 4 and the simulator runs (pieces 1 and 2 in one go, then 3 and 4), plus a live night read by the Operator
and the Watcher. Today's five rounds cost about 12 weekly usage points; this plan should cost 15 to 20. The weekly window resets on 2026-10-24.

## What this plan does not do

- No LLM in the loop, no new client, no more monitors (the review's "not recommended now").
- The dungeon rungs stay off until the ladder item; a core bot still hunts surface ground up to tier 3.
- The other classes keep the rule list until the hunter beats it live.

## Open questions for the owner

1. **Promotion rule.** Beat on all five numbers, or kills and net worth alone with the other three not worse? (The plan says all five.)
2. **Start.** After the weekly reset on 2026-10-24, or now past the line?
3. **The live night.** The ten `fields` bots again as the treatment, or a fresh random ten?
