# Harvest auto-repeat: mining, lumberjacking, fishing

Owner request 2026-10-05: once a player targets a vein, tree or water, keep gathering on it until the resource is
exhausted or the player does something that logically cancels it, instead of re-targeting every attempt. Not a
roadmap item (no phase); it is a quality-of-life change that departs from UOR, where every attempt needed a fresh
double-click and target and players used UOAssist or Razor macros for the same effect (checked 2026-10-05 against
UO Renaissance and forum threads; no built-in repeat in 2000).

Flag: `featureFlags.harvestAutoRepeat`, **enabled 2026-10-05 on the owner's explicit "Activate"** (it shipped false). The README "Gathering" line below is in the root `README.md`.

## Sign-off (2026-10-05)

- Cancel is silent (stock has no cancel message); natural stops keep their stock messages.
- Any step cancels the loop (not only moving out of range).
- No cap on attempts and no periodic "still there?" check.
- Plan approved, with one ModernUO hook and the default-off flag.

## Design

Every attempt is the stock one (same delay, skill check, yield, skill gain and messages), so nothing speeds up. The only
change is that, when an attempt ends normally, the same target is started again.

| Rule | Stock | Here |
| --- | --- | --- |
| Re-target after each attempt | Double-click tool, target, every attempt | Automatic until a stop below |
| Resource bank empty | Stock "no metal / wood / fish" message ends it | Same message, same moment; the loop re-enters the stock start path, so stock messages are untouched |
| Out of range, tool worn out, riding or polymorphed, axe unequipped | Stock message and stop | Same (the stock checks run on every restart) |
| Pack full | Item lost, stock message | Loop stops |
| Skill-check miss | Fail message | Loop continues, as a manual player would |
| Walking | Stock continues while within range | Any step ends the loop |
| Casting, using another skill, war mode, fighting or being hurt (incl. poison), dying, disconnecting | Stock ignores | Ends the loop |
| Opening a fresh harvest cursor | n/a | Ends the loop (the player is choosing again) |
| Picking a new target mid-attempt | Stock refuses (silent, or "You are already fishing") | The current attempt finishes, then the loop moves to the new target |
| Opening containers, using items, talking | n/a | Do not cancel |
| Starting another harvest skill | Interleaves | One loop per player; the older one ends |

Not covered (named limits): treasure-map digging and the grave and furniture special cases stay single-shot; sand
mining (100 skill) is included automatically because it shares the engine.

## Code

- ModernUO hook (`Projects/UOContent/Engines/Harvest/Core/HarvestSystem.cs`): `HarvestSystem.StageChanged` plus the
  `HarvestStage` enum (Started, Harvested, Failed, PackFull, Concurrent). It does nothing on its own.
- `ShardContent/src/BritanniaRenaissance.Content/HarvestRepeatService.cs`: the loop, the cancel rules
  (`CheckCancel`, `StageAllowsRepeat`), `[HarvestRepeatStatus` diagnostics (Administrator).
- Flag in `ShardRulesConfiguration.cs` and `shard-rules.json`; service registered in `ShardBootstrap`.
- Tests: `tests/HarvestRepeatTests.cs`. Live: `tests/scenarios/harvest-repeat/` (probe, driver). Navrey gained a
  `targettile <x> <y> <z> [graphic]` command so a test client can answer a ground-target cursor.

## Acceptance matrix

| Case | Verified by | Result |
| --- | --- | --- |
| Cancel decision table (move, step back, skill, cast, war mode, disturbed, hits, cursor, dead, disconnected) | Unit test | Pass |
| Which stages repeat (miss yes; pack full, tool broke no) | Unit test | Pass |
| Flag defaults off, listed when on, source config ships it off | Unit test | Pass |
| Mining: one targeting drains the bank, stock "no metal" message ends it, no second cursor | Live, disposable host | Pass (5 left to 0) |
| Lumberjacking: same, two chops | Live | Pass (25 left to 5; "not enough wood") |
| Fishing: same | Live | Pass (3 left to 0, 67 s; "fish don't seem to be biting") |
| Walking, another skill, war mode, damage, open cursor each end the loop | Live | Pass, each: harvesting stops and no loop remains |
| New target mid-loop moves the loop | Live | Pass (status shows the new tile; bank keeps falling) |
| Flag off is exactly one attempt (stock) | Live control | Pass (30 to 29) |
| Casting, death, disconnect | Unit test only (named limit) | |

## Player text and README

No new player strings (cancel is silent; stops use stock messages). When activated, add to the root `README.md`
rules section: "**Gathering.** Mining, lumberjacking and fishing repeat on the tile you chose until its resource runs
out. Walking, casting, using another skill, entering war mode, fighting or being hurt, or opening a new target cursor
ends it."

## Run IDs and notes

- Unit and full Shard suite: 443 passed, 0 failed (run 20261005T164219460Z-cb2285, which includes the 16 new tests).
- Live: disposable host `harvest` on the new UOContent and shard DLLs, driver `tests/scenarios/harvest-repeat/harvest_live.py`
  (mine, tree, water, cancel, skill, off), results in `work/harvest-live/`. Host and accounts removed afterwards; no dev
  saves touched.
- Incidental: a full pack stopped a loop in the first cancel run (stock loses the ore; the loop stops), which is the
  PackFull rule working. The first runs of the walk and skill cases failed because the probe chose tiles the server
  refused as unseen ("Target cannot be seen") and stacked tools until the pack was overloaded; the probe now checks
  line of sight the way the server does and clears the pack, and those cases then passed. These were probe faults,
  not feature faults.
- Sign-off decisions above stand. Flag stays false until the owner acknowledges activation.
