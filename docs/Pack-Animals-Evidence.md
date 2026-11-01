# Pets keep up (`petsKeepUp`) and the bots' pack horses: evidence

**Owner, 2026-11-01:** asked why pack animals don't work and whether the problem was general. After the report (`work/botfarm-watch/pack-animals-report-2026-11-01.md`) he chose "A and B together":
- **A:** a shard rule so following pets keep up.
- **B:** the bots' own pack-horse handling.

## The engine facts

| Fact | Source |
| --- | --- |
| Every animal a UOR tamer can own (pack horse and llama, horse, llama, wolves, bears, cougar, panther, hind, great hart, dog, cat) steps every 0.45 s when active ("Medium") | `Distribution/Data/npc-speeds.json` |
| A player on foot steps every 0.4 s walking and 0.2 s running | `movement.delay.walkFoot` / `runFoot` (`Server/Mobiles/Movement.cs`) |
| Before AOS a following pet has no catch-up pace; AOS caps it at 0.1 s | `BaseCreature.FollowMoveSpeed => Core.AOS ? 0.1 : 0` |
| A following pet more than `RangePerception` (16) tiles from its master stands still ("Master is missing. Staying put.") until the master comes back in range | `BaseAI/PetOrders.cs FollowTarget` |
| The AOS-only pace came from RunUO, with no publish cited; upstream's pet-order rewrite cites publishes for every other rule | ModernUO `f606225f4` (2026-09-10) |

## A: the shard rule

- **Engine hook:** `BaseCreature.FollowMoveSpeedFilter`, a `Func<BaseCreature, double, double>`, null by default. It is applied where `CurrentMoveSpeed` reads `FollowMoveSpeed`, only while a pet is closing on its master (`IsPacingToMaster`).
- **Shard code:** `PetsKeepUp.cs`, behind the flag `featureFlags.petsKeepUp`.
  - With the flag on, a pet with no follow cap gets the run-on-foot pace (`movement.delay.runFoot`, 200 ms, so 0.2 s a step).
  - An AOS cap, or a creature already faster, is left alone.
- **Tests:** `PetsKeepUpTests` (5).
- **Flag state:** off in the source config. On only on the bot farm's host, for the bots' test.

## B: the bots (`packy.py`)

- **Every leg is led.** `LEAD_MIN` went from 12 to 3. A long walk goes in legs of 9-36 tiles, and every leg under 12 used to run.
- **The horse is called in first.** A horse in view but more than 3 tiles off gets "all come" before a led walk sets off. If it doesn't come, the bot walks to it.
- **The bot runs when the shard keeps pets up.** It runs (runmode auto) under the farm feature `pets_keep_up`, which mirrors the server flag. Otherwise it walks.
- **A horse left behind is walked back for at once**, once per walk, instead of the walk carrying on.
- **Tests:** `work/botfarm/patches/test_gatherer_homes.py` (lead, call-in, walk-back).

## Live check: one pack horse following the farm's admin character

Driver: `work/pets-keepup/pet_pace_live.py`. Before is the farm host's 2026-10-19 build. The admin makes a pack horse its pet, says "all follow me", then runs in a straight line.

| Case | Run | Horse | Result |
| --- | --- | --- | --- |
| Before, 40 tiles | 40 tiles in about 10 s | 15-18 behind, out of view for 2 s | caught up 8 s after the stop (just inside the 16-tile limit) |
| Before, 89 tiles | 89 tiles in 19 s | 16 behind at 4 s, then out of view | **not back 10 s after the stop: it stood still** |
| After (petsKeepUp on) | (pending) | | |
