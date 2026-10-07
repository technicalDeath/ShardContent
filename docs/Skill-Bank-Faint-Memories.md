# Skill Bank: Faint Memories, the 0.2 step, banking below the cap, and Discard

Status: **built and verified on a disposable host 2026-10-07; committed, pushed and deployed to the dev distribution the same day. `faintMemories` was enabled on the owner's explicit "activate" (2026-10-07).** The 0.2 step, the text fixes, the engine hook and Discard are not behind a new flag: they act through the existing `skillBank` flag. The ModernUO hook is `ee7ccd518`; the pin is bumped to it. Characters created before activation have no pool; staff `[GrantFaintMemories <serial>` gives one.

Owner requests (2026-10-07, off the roadmap like `harvestAutoRepeat`):

1. Every new character starts with a pool of free points called **Faint Memories**: "faint memories of a past in Britannia linger, and skills of the past come back to you".
2. The Skill Bank restores in increments of **0.2** (0.1 when only 0.1 is left), "to make retraining faster", **including** Faint Memories.
3. The player should not need to be at the 700 cap to bank points: **any skill that goes down** is banked.
4. A player can **discard** a skill's banked points (not Faint Memories) after typing a confirmation word.

## Sign-off record

| Date | Decision |
| --- | --- |
| 2026-10-07 | Pool of **5.0** points (the owner dropped it from 20). Unlocks **24 hours from character creation** (not account age). "Used just like the skill bank": it comes back through the same hook, on training, not through a picker. Free points **stop at 90.0** (Mastery's threshold) |
| 2026-10-07 | Restores come back **0.2 at a time**, or 0.1 when only 0.1 is left, for the bank and for Faint Memories |
| 2026-10-07 | The category is called **Faint Memories** |
| 2026-10-07 | Banking: owner chose option **C**, bank the points a Down skill loses even to a sub-10 gain the anti-macro check refused (a ModernUO hook) |
| 2026-10-07 | Discard removes a skill's **whole** balance. "Remove" became **Discard**, and the word the player types is **`discard`** |
| 2026-10-07 | Four choices proposed and signed off: the skill's own bank comes **first**; a **10.0 floor** (stock gains below it are already faster); at the **total cap the pool waits** (no Down-skill swap); a **staff grant command** |

## What it does

**Faint Memories.** At creation a player-level character gets 5.0 points (`FaintMemoriesService.Grant`, registered once on `CharacterCreatedHandler`). State is one account tag per character, `BritanniaRenaissance.FaintMemories.v1.<serial>` = `1|<granted UTC ticks>|<tenths left>`, like Mastery and Intent: no ModernUO save format change. A used-up pool keeps its tag (0 left), so it is never granted twice. Existing characters and staff get nothing.

From 24 hours after creation, `SkillBankService.TryRestore` falls through to Faint Memories for a skill with no banked points of its own. On a skill use the anti-macro check allows, in a skill set to **Up**, a step of 0.2 comes back instead of the gain roll. It does not apply: below 10.0 (stock already gains 0.1 to 0.4 on every use there, faster than 0.2), from 90.0 up (Mastery), when the character is at the total cap (free points cannot make room), or while it is still locked. At 0.0 the display disappears and the player gets one line.

**The 0.2 step.** `skillBank.restoreStepTenths` (default 2, valid 1 to 10). `SkillBankLedger.TryPlanRestoration` plans up to the step, never more than the balance or the room under the skill's cap. At the total cap, whatever does not fit comes out of **one** Down skill and the bank keeps it for that skill; if no Down skill can give that much, the next smaller step is tried, down to 0.1.

**Banking below the cap.** The bank already banked any Down skill's loss from a counted gain, with no cap check (`SkillCheck.Gain` displaces a Down skill with probability total ÷ cap even far below the cap). It had been proved only near the cap (689.9/700). The one gap: a sub-10 gain the anti-macro check refused still took points from a Down skill, but `SkillCheck` published the bank event only for counted attempts, so those points vanished. The hook is one line in `ModernUO/Projects/UOContent/Skills/SkillCheck.cs`: that branch now calls `Gain(..., organicAttempt: true)`. Its test was renamed `SubTenAntiMacroDenialStillBanksItsStockCapDisplacement`. This supersedes row SB-GAIN-ANTIMACRO of `Alpha-3-Skill-Bank-Persistence-Rehearsal.md`.

**Discard.** A **Discard** button on each bank row opens `SkillBankDiscardGump`: it says how many points will be deleted for good, that they do not go back to the skill and that the skill stays as it is, and asks the player to type `discard` in a box. Case and surrounding spaces are ignored. Any other text, a blank box, Keep them, or closing the window changes nothing. On confirm the server discards what that skill has banked at that moment and says how much. Each discard is written to the audit log.

## What changed

| Where | Change |
| --- | --- |
| ModernUO `Skills/SkillCheck.cs`, `UOContent.Tests/.../SkillEventsTests.cs` | The sub-10 hook above and its test |
| `FaintMemories.cs` (new) | `FaintMemoriesPolicy` (pure rules: tag, clock, plan, view, texts), `FaintMemoriesService` (grant, restore, login and unlock messages, staff lines) |
| `SkillBankLedger.cs` | Multi-tenth `TryConsume`, `Discard`, step-aware `TryPlanRestoration` |
| `SkillBankService.cs` | Step, Faint Memories fall-through, `Discard`, view carries the banner, staff status lines |
| `SkillBankGump.cs`, `SkillBankDiscardGump.cs` (new) | Faint Memories banner (4 rows a page while it shows), Discard column, corrected hint and empty-bank text, the confirmation window |
| `WelcomeGuide.cs` | Skill Bank page rewritten (step, below-cap, Discard, Faint Memories paragraphs only while the flag is on); commands line |
| `ShardRulesConfiguration.cs`, `shard-rules.json` | `skillBank.restoreStepTenths`, `faintMemories` section and flag (needs `skillBank`) |
| `ShardRulesCommands.cs`, `ShardBootstrap.cs` | `[GrantFaintMemories <serial>` (staff), service registration |
| Tests | `FaintMemoriesTests`, `SkillBankStepAndDiscardTests`, additions to `WelcomeGuideTests` and `ShardRulesConfigurationTests` |
| Live | `TestOnlySkillUse`, `TestOnlyFaintAge`, `TestOnlySkillCap` probe verbs; `tests/scenarios/faint-memories/faint_live.py`; `work/faint-memories/` scripts (scratch) |

## New player-facing text (for review)

- Window banner: "Faint Memories", "5.0 points" / "3.4 of 5.0 left", the theme line, "Unlocks in 8 hours 14 minutes" / "Train a skill set to Up: 0.2 per use".
- Messages: "Faint Memories: 5.0 points are ready. Train a skill you have set to Up and they come back to you, 0.2 at a time. [SkillBank shows what is left." and "Faint Memories: the last of them has come back to you, into <Skill>. There is nothing left to remember."
- Skill Bank hint: "Set a skill to Up and train it: every use brings back 0.2 from the bank. Discard throws a skill's banked points away for good."
- Empty bank: "Whenever a skill you have set to Down loses points because another skill gained, those points are saved here, and you earn them back by training that skill again. You do not need to be at the skill cap for that."
- Confirmation: "Discard the banked points of <Skill>?", "<N> banked points will be deleted for good. They do not go back to <Skill>, and <Skill> stays at <value>.", "Type discard in the box to confirm:", notices "Discarded <N> banked points of <Skill>.", "Nothing was discarded: discard was not typed.", "Nothing was discarded. <Skill> keeps its <N> banked points."
- Guide: the Skill Bank page ("Getting points back", "Discarding banked points", and "Faint Memories" while the flag is on) and the `[SkillBank` command line.
- The window and the guide used to say a restore happens "each time it would gain". The code restores on **every use the anti-macro check allows**, before the gain roll. The wording now says so.

## Verification (2026-10-07)

**Unit.** Shard suite 891 pass (96 new: `FaintMemoriesTests`, `SkillBankStepAndDiscardTests`, and additions to `WelcomeGuideTests` and `ShardRulesConfigurationTests`). UOContent suite 1362 pass, 2 skipped as before; the renamed engine test `SubTenAntiMacroDenialStillBanksItsStockCapDisplacement` passes.

**Live, disposable host `faint-memories`** (flag on, shipped numbers, probes `TestOnlySkillUse`, `TestOnlyFaintAge`, `TestOnlySkillCap`), driver `tests/scenarios/faint-memories/faint_live.py`. Skill uses are real `SkillCheck.CheckSkill` calls through the gain hook; the world was saved, the server restarted and the saved state read back.

| Case | What | Result |
| --- | --- | --- |
| F1, F2 | New characters start with 5.0, locked for 24 hours; a staff character is not granted it | pass |
| F3 to F3d | A character made while the flag was off has none; `[GrantFaintMemories` grants it once and refuses a second time | pass |
| F4 | A locked pool is not touched by 12 uses | pass |
| F5, F5b | `[TestOnlyFaintAge` +24.5 h unlocks it; one use is exactly 500 to 502, 4.8 left | pass |
| F6 to F6c | 24 more uses empty it (502 to 550, 0.0 left); the player is told the last of it came back; afterwards a use is the ordinary gain and the pool stays 0.0 | pass |
| W1 to W3 | The window shows the ready banner (4.5 of 5.0 left), the countdown while locked, and no Faint Memories once used up | pass |
| G1 to G3 | 89.8 to 90.0 in one step; at 90.0 the pool is left to Mastery; 89.9 returns 0.1 | pass |
| G4, G5 | 9.9 is left to the stock gain (pool untouched); 10.0 applies (100 to 102) | pass |
| G6 | A skill set to Down, and one set to Locked, get nothing | pass |
| G7 | At the total cap (cap set equal to the total) the pool waits | pass |
| G8 | A skill's own banked points come back first (+0.2 from the bank, pool unchanged) | pass |
| B1 to B4 | The bank returns 0.2 a use; an odd last tenth comes back alone; 0.1 of room under the skill's cap returns 0.1 | pass |
| B5 | At the cap 0.2 comes out of a Down skill and is banked for it, total unchanged (2000/2000) | pass |
| B6 | **Below the cap** (cap set to twice the total) a Down skill's lost points are banked: Hiding lost 5.3, bank 5.3, total 2532 of 5000 | pass |
| D1 to D5 | Each bank row has a Discard button; it asks first and says what goes; a wrong word and Keep them discard nothing; typing the word discards that skill's points only | pass |
| P1 to P3 | After a save and restart: the pools (4.5, 5.0, 0.0), Hal's bank after the Discard, and the unlock clock (23 h 44 m left, still counting from creation) all survived | pass |

The first runs showed four faults of the driver, not of the shard: the flag override left off by an aborted run, the Welcome guide window absorbing `gumpresponse` replies, a character-creation subprocess whose pipe stayed open on the Navrey session it started, and sessions restarted without their own account files (they logged in as the staff account and kicked the staff session). Each was fixed in the driver or the scratch scripts and the affected cases re-run.

**Real ClassicUO client** (character Nia, a new character logged in through the client; screenshots under `work/player-client/Nia/shots/`, scratch): the banner locked with its 25% bar and "Unlocks in 17 hours 43 minutes"; the confirmation window; the wrong word and its notice; the right word and its notice; the banner at "3.0 of 5.0 left" after ten uses (the journal behind shows each +0.2); the window after the pool was used up (banner gone, rows back); the guide's Skill Bank page with the Discard and Faint Memories paragraphs. Found and fixed on the way: the ready banner's label ran past its box ("per use" was cut off) and is shorter; the confirmation box's text was white on beige and is now black.

**Not run:** the anti-macro-refused sub-10 case live (the probe's uses are unique, so the anti-macro check always allows them; the engine unit test covers it); the older drivers `mastery_live.py` and `gain_live.py` in full (neither expects +0.1 restores, and their bank cases read the window as before).

## Named limits

- **Faint Memories at the total cap waits** rather than swapping points through a Down skill (signed off). It is not lost; it comes back once there is room.
- **Below 10.0 the pool is left alone** on purpose: the stock gain there is 0.1 to 0.4 on every use, which beats 0.2.
- **Every use counts, not every gain.** The pool and the bank return a step on each eligible use, successful or not, as the bank always did. Five points are 25 uses.
- **Option C and farming.** Points a Down skill loses to a sub-10 gain the anti-macro check refused are now banked, so a macro spamming a sub-10 skill can bank them. It is bounded: a skill cannot pass 10.0 this way and the total cap still holds.
- A window shows what it had when it opened; it does not update by itself (as with every shard window).
- The anti-macro-refused sub-10 case is proved by the engine unit test only; the live probe makes unique uses, which the anti-macro check always allows.
