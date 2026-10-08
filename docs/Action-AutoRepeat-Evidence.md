# Action auto-repeat: taming, lockpicking, spinning wheel, loom, cooking

Owner request 2026-10-05, after the gathering repeat (`Harvest-AutoRepeat-Evidence.md`): four more loops with the same
rule. The owner chose these four from a researched list and declined bandages, loot-all and snooping; crafting
("make this many") is a separate item. Not a roadmap phase item.

Flag: `featureFlags.actionAutoRepeat`, **enabled 2026-10-07 on the owner's explicit "activate"** (it shipped false). The README "Repeated actions" line below is now in the root `README.md`.

## Sign-off (2026-10-05)

- One flag for all four loops.
- A taming retry starts from the stock 2-tile targeting range; beyond it the stock "That is too far away" ends the loop.
- Cancel rules, silence on cancel and no attempt cap carry over from gathering.
- Plan approved.

## Design

Every attempt is the stock one, restarted the way a macro would restart it: the skill or item is used again and the
same target is answered through the stock cursor code (`UseSkill`/`Use` then `Target.Invoke`), so every stock range,
sight and refusal check runs with its own message. Lockpicking and spinning restart through a public form of the stock
target body because their cursor prompt would otherwise repeat every attempt. Cancel (silent): any step, casting,
another skill, war mode, fighting or being hurt, death, disconnect, any open cursor. One loop per player.

| Loop | Stock | Repeat rule | Natural stop (stock message) |
| --- | --- | --- | --- |
| Animal Taming | 2-tile target, 9–12 s attempt, re-target every try | After "You fail to tame the creature", try the same creature again | Accepted; too far, no path, angered, dead, someone's pet, too many owners, must be subdued |
| Lockpicking | 1-tile target, 3 s, 25% pick break on a miss | After "You are unable to pick the lock", try again while a pick remains and it is still locked | Yields; last pick broke; cannot be picked; not enough skill; stepped away (stock silent) |
| Spinning wheel | One wool/cotton/flax per click, 3 s | After the yarn or thread lands, spin the next of the same stack | Stack gone; wheel taken by someone else |
| Loom | One thread per click, no timer; five make a bolt | One use feeds the whole stack (instant, like logs to boards) | n/a |
| Cooking | One item per attempt, 5 s, burn on a miss or when away | After each attempt, cook the next of the same stack at the same heat source | Stack gone |

The "another skill" cancel does not apply to taming: stock locks the skill timer during an attempt and resets it as the
attempt ends, so it is excluded from taming's comparison (unit-tested).

## Code

- ModernUO hooks, notifications only: `AnimalTaming.AttemptStarted/AttemptEnded` (+ `TameResult`),
  `Lockpick.AttemptStarted/AttemptEnded` (+ `LockpickResult`) and `Lockpick.BeginPick`, `SpinningWheelEvents`
  (`SpinStarted`, `Spun`) raised by `Wool`, `Cotton`, `Flax` with a public `SpinOn`, `BaseClothMaterial.FeedAmount`
  (loom; default 1), `CookableFood.CookStarted/CookFinished` (+ `CookResult`). Stock behavior is unchanged with no
  subscriber and `FeedAmount` unset.
- `ShardContent/src/BritanniaRenaissance.Content/ActionRepeatService.cs`: the loops, the decision tables, the cancel
  check (shares `HarvestRepeatService.CheckCancel`), `[ActionRepeatStatus` (Administrator).
- Flag in `ShardRulesConfiguration.cs` and `shard-rules.json`; service registered in `ShardBootstrap`.
- Tests: `tests/ActionRepeatTests.cs`. Live: `tests/scenarios/action-repeat/` (probe, driver).

## Acceptance matrix

| Case | Verified by | Result |
| --- | --- | --- |
| Taming repeats only after a plain miss | Unit test | Pass |
| Lockpicking repeats while picks and the lock remain | Unit test | Pass |
| Spinning repeats while material remains and the wheel is free | Unit test | Pass |
| Cooking repeats while food remains, burn or not | Unit test | Pass |
| Taming ignores the skill timer; the other cancels still apply | Unit test | Pass |
| Flag defaults off, listed when on, source config ships it off | Unit test | Pass |
| Taming: one targeting is tried until the horse accepts; no second cursor; loop gone | Live, disposable host | Pass (4 attempts, 43 s; no cursor left pending) |
| Lockpicking: one targeting until the chest yields | Live | Pass (4 misses, 2 picks broke, yielded at 18 s) |
| Lockpicking: impossible lock ends when the last pick breaks; chest stays locked | Live | Pass |
| Spinning: 5 wool to 15 yarn from one targeting, paced by the 3 s spin | Live | Pass (18 s) |
| Loom: 12 thread to 2 bolts on one use | Live | Pass |
| Cooking: 5 raw steaks in one targeting; cooked + burned = 5 | Live | Pass (3 cooked, 2 burned, 27 s) |
| A step ends the taming loop and the cooking loop after the attempt in flight | Live | Pass |
| Flag off: taming, spinning, loom and cooking are one attempt each | Live control | Pass |
| Casting, war mode, damage, death, disconnect | Unit test only (shared cancel code, live-verified for gathering) | |

## Player text and README

No new player strings. When activated, add to the root `README.md` rules section: "**Repeated actions.** Taming keeps
trying the same creature until it accepts you, lockpicking keeps working the same lock while you have picks, a
spinning wheel spins your whole stack, a loom takes your whole stack at once, and cooking cooks your whole stack at the
heat source you chose. The same things end these as end gathering."

## Run IDs and notes

- Unit and full Shard suite: 539 passed, 0 failed (run 20261006T004603348Z-cdb6d1; includes the 18 new tests and the
  camping tests from parallel work).
- Live: disposable host `actions` on the new UOContent and shard DLLs, driver `tests/scenarios/action-repeat/action_live.py`
  (tame, lock, lockout, spin, loom, cook, cancel, off), logs in `work/action-live/`. Host and accounts removed afterwards;
  no dev saves touched.
- Finding fixed during the run: restarting through the stock cursor (`UseSkill`/`Use` then `Target.Invoke`) sends the
  client a cursor that consuming it server-side does not take back, so the player would be left holding a dead cursor.
  The service now sends the stock cancel-target in the same flush; the driver asserts nothing is left asking.
- Driver faults, not feature faults: the first cooking count was taken the instant the last steak was consumed, five
  seconds before its result; the first chest yielded on the first try, so its odds were lowered to one in ten so a
  miss-and-retry is exercised. Process fault: stopping the host without a save after creating characters lost them.
- Sign-off decisions above stand. Flag stays false until the owner acknowledges activation.
