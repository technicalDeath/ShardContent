# Beta 2a item 2: Mastery redesign audit

> **Superseded 2026-10-09 by [`Mastery-Layered-Plan.md`](Mastery-Layered-Plan.md)** (owner sign-off): Mastery now begins at 80.0, its daily allowance is layered on ordinary gain instead of replacing it (allowances 2.0 / 1.4 / 1.0 / 0.8, so 10 / 15 / 20 / 25 days from 80), and Faint Memories stops at 80.0. The cycle, claim, bank and Up-lock rules below still stand. Evidence for the change: `Mastery-Layered-Evidence.md`.

Roadmap: [Beta 2a](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 2 (deferred from Alpha 3 J-2/J-3). Design contract: Hot Zones plan, "Character Mastery cycles, skill allowances and limited banking" (DD 837-928), as ruled below.

## Sign-off (owner, 2026-10-02)
Plan approved with these answers. Do not reopen.
- **Activity rule: B with the bank.** A skill's allowance for a cycle is claimed by the first valid, successful use of that skill in the cycle. An unclaimed cycle for that skill is lost (not banked). Unspent allowance carries up to three cycles of that skill's allowance. There is no login-day rule: consistency means using the skill each cycle.
- **Total-cap blockage uses stock displacement.** A Mastery gain at the 700-point cap lowers a Down-locked skill exactly as stock does, so Skill Bank deposits still happen. With no Down skill the use grants and spends nothing.
- **Owner declined:** a minimum-uses claim threshold, a skill-reachability audit, and a downtime heartbeat. None is built. (Known consequence: one valid use claims a cycle; a skill with no non-trivial action near 100 cannot progress, as in stock; a long outage costs everyone cycles.)
- Settled from the first plan, not changed: failed checks grant and spend nothing; the existing gain classes set the allowance; a skill reaching the threshold mid-cycle claims that cycle's allowance once; Mastery replaces the as-built mechanic in place with no new feature flag.
- **Revision, same day (owner): Mastery starts at 90.0, not 95.0, with the allowances doubled** to Easy 2.0 / Standard 1.0 / Hard 0.6 / VeryHard 0.4 per cycle, so the minimum days to 100 stay 5 / 10 / 17 / 25. The gain curve now ends at 90. Reasons recorded in "Why 90" below.

## Why 90 (analysis behind the revision)
- **Grind.** In the Beta 1 gain model (`work/gain-model/band_share.py`), 90 to 95 is only 8-12% of the checks to reach 95, but the costliest stretch per point: 1.6x (Easy), 2.0x (Standard) and 2.5x (Hard) the average below 90 for a 50%-chance skill, and about 5x for crafting resources (Blacksmithy ~2,500 of 11,300 ingots, Alchemy ~1,200 of 3,600 nightshade). Starting at 90 removes the most expensive stretch, not most of the journey.
- **Identity.** UO titles 90.0 "Master" and 100.0 "Grandmaster"; the contract already calls 90 "fully usable/competitive". Mastery now starts at Master.
- **What moves into the time-earned band** (stock UOR values): agapite ore and smithing 90, dragons 93.9, verite 95, nightmares 95.1, white wyrms 96.3, valorite 99, maker's mark 100; pre-ML Magery 7th circle 75% at 90 / 100% at 100 and 8th circle 50% / 75%. Melee changes little (pre-AoS hit chance 46.7% for 90 against 100, 50% even).
- **Accepted costs:** the new-versus-established gap is 10 points instead of 5, felt mostly by Hot Zone mages; top-tier goods (verite, valorite, maker's mark) reach the market later at launch.

## As-built (Alpha 1), replaced
`MasteryProgression.cs`: 95.0 threshold, shared 4-hour UTC periods, +0.1 pending per period on UTC days the character logged in (cap 0.6), each use spent 0.1 whether it succeeded or not, state in an account tag keyed by character serial, no feature flag. At the total cap it gained nothing and spent nothing.

## Design as built
| Rule | Behavior |
| --- | --- |
| Threshold | 90.0 (`MasteryEngine.ThresholdFixedPoint`, the single source; the gain curve reads it). Below it the gain curve and stock gain apply |
| Cycle | 24 hours per character, anchored at the server time the character first holds a skill at 90+ (first valid use or login). Server clock only |
| Valid use | The stock hook fired (non-trivial check, region and anti-macro eligible), the check succeeded, the skill is Up-locked and below its cap, and a gain is possible (see cap rule) |
| Claim | The first valid use of a 90+ skill in a cycle adds that skill's allowance to its store (capped), once per skill per cycle. Dropping below 90 and returning cannot claim a cycle twice; cycles missed meanwhile are lost |
| Allowance | Easy 20, Standard 10, Hard 6, VeryHard 4 tenths per cycle, by the skill's `skillGain` class; unlisted skills count as Standard |
| Gain | +0.1 per valid use while the store is not empty, through stock `SkillCheck.Gain` (so displacement and the Skill Bank event are stock); never more than +0.1 |
| Store | At most 3 cycles of that skill's allowance (6.0 / 3.0 / 1.8 / 1.2) |
| Total cap | A gain displaces a Down-locked skill as stock does; with none, nothing is granted or spent |
| 100.0 | Mastery ends for the skill and its store is cleared |
| Skill Bank | Restoration still acts first and neither claims nor spends allowance |
| Gain bonuses | None can change it: the decision is made before the stock gain roll and its multipliers |
| Entry | First valid use at 90+ tells the player Mastery has begun |
| Reminder | Three seconds after login, a line when any Mastery skill has not claimed this cycle |
| `[MasteryStatus` | Per skill: value, class, allowance per cycle, stored and its limit, claimed this cycle, points to 100; the countdown to the next cycle. Administrators may pass a player serial |

From 90 to 100 is 100 valid uses. Minimum calendar cost at 24 hours: 5 / 10 / 17 / 25 cycles (Easy / Standard / Hard / VeryHard), each needing a valid use that cycle; spending a full day's allowance takes 20 / 10 / 6 / 4 valid uses.

## Persistence and migration
Account tag `BritanniaRenaissance.Mastery.<serial>`, JSON version 2: `{version, anchor, skills:{id:{claimed, allowance}}}`. Version 1 (periods, login days, pending) is discarded on load: the workspace has no live population, per the roadmap. Changing the threshold or allowances after launch would strand players part-way through the band; do it before release only.

## Decisions made while building (within the signed-off plan)
- **No ModernUO change was needed.** Stock `SkillCheck.Gain` is public, so Mastery calls it for the +0.1. That gives the stock cap displacement and the Skill Bank event for free. The result is clamped to +0.1 and the allowance is returned if stock declines.
- **A valid use also requires a possible gain.** A use at the total cap with no Down skill, a locked skill or a skill at its own cap claims and spends nothing (the contract's "blockage grants nothing").
- **Under the cap**, stock displacement is probabilistic, so a Mastery gain may occasionally lower a Down skill by 0.1, exactly as an ordinary gain does.
- **No refresh sweep.** Claiming is lazy, on use. A login line tells the player when Mastery skills can still claim this cycle (sent three seconds after login; the client drops messages sent during the connection event).
- **The threshold is a code constant, not a config value.** The gain curve's bands and validation depend on it, and changing it after launch is a data decision, not a setting.
- Staff support in production code: `[MasteryStatus <serial>` (administrators), `MasteryProgression.ShiftAnchorEarlier` and `ForgetCachedState` for the test probe.
- Tooling fixed on the way: `New-TestCharacter.ps1` regenerated a password on a retry for an account that already existed (the server keeps the old one, so the login failed), and its request-file cleanup could fail while the server still held the file. It now reuses an existing `work/accounts/<Name>.env`, records accounts in the host manifest before logging in, and retries the cleanup. `Test-Tooling.ps1` passed.

## Acceptance matrix and results (threshold 90)
Unit: `MasteryEngineTests` (cycles, one claim per cycle, lost cycles, three-cycle cap, backwards clock, spending, 100 uses from 90 in 5/10/17/25 cycles, persistence, discard of version-1 state, config validation, the committed allowances) and `SkillGainCurveTests` (bands end at 89.9, stock from 90.0). Shard suite 388/388. The two known UOContent failures are unrelated and no ModernUO file changed.

Live: disposable host `mastery-e`, real Navrey clients, real Anatomy checks on the other test character (an Easy skill with a 10% failure chance at 90), a probe that moves the cycle anchor back (`tests/scenarios/mastery/mastery_live.py`, `MasteryProbe.cs`). 15/15, then 2/2 after a server restart.
| Case | Result |
| --- | --- |
| M1 first valid use at 90: entry message, claim of 2.0, +0.1 | pass |
| M2 twenty gains empty the store; Anatomy 92.0, 0.0 stored (holds up to 6.0), claimed | pass |
| M3 further valid uses with nothing stored grant nothing (stock gain also suppressed) | pass |
| M4 `[MasteryStatus` text (90.0, valid-use line, 24 hours, countdown with no UTC time, class, 2.0 per cycle) | pass |
| M5 after 24 hours the skill claims 2.0 again and gains | pass |
| M6 three further cycles: the store stops at three cycles (5.9 of 6.0 after spending) | pass |
| M7 below 90 Mastery does not act | pass |
| M8 back to 90 in the same cycle: no second claim, no second entry message, a gain from the store | pass |
| M9 saved state from the earlier mechanic is discarded | pass |
| M10 and Mastery starts fresh at the next use | pass |
| M11 Alchemy shows Hard 0.6 (holds 1.8), Magery Standard 1.0 | pass |
| C0 character at exactly 700 total | pass |
| C1 at the cap with no Down skill: no gain, no spend, not claimed | pass |
| C2 with a Down skill: +0.1, total unchanged, claimed | pass |
| C3 the displaced point is in the Skill Bank (Fishing banked) | pass |
| R1 state survives a restart (claimed cycle and store) | pass |
| R2 login line when skills can still claim | pass |
Not exercised live: a failed check at 90+ (covered by the `!success` branch), Skill Bank restoration above 90 (unchanged path, Alpha 3 evidence), and a skill reaching 100.0 (covered by the clear-on-100 branch only). Earlier runs at 95 (hosts `mastery-a` to `mastery-c`) passed the same matrix before the revision.

## Player text (for owner review with the release)
- Entry: "<Skill> has reached 90.0: ordinary gain has ended and Mastery begins. Use [MasteryStatus to see your allowance."
- Claim: "Mastery: <Skill> claims this cycle's allowance of 2.0."
- Gain: "Mastery advanced <Skill> to 90.1. Allowance left: 1.9."
- Grandmaster: "<Skill> has reached Grandmaster (100.0)."
- Login: "Mastery: N of your Mastery skills can claim this cycle's allowance with a valid use. Use [MasteryStatus for details."
- `[MasteryStatus`: "Mastery: a skill at 90.0 or above gains +0.1 for each valid, successful use while it has allowance." / "A use is valid only if it had a real chance of failing. Trivially easy actions and failed attempts count for nothing." / the cycle and carry-over rule / "Your next cycle begins in 5h 12m." / one line per skill: "Anatomy 92.0 (easy): 2.0 per cycle, 0.0 stored (holds up to 6.0), claimed this cycle, 8.0 points to reach 100.0." Wording revised on the owner's review the same day ("stored" avoids confusion with the Skill Bank; countdown only).
- `[SkillClasses`: "Skill gain speed, compared with stock, from skill 10 up to 90:" and class lines ending "to 90".
- README: Skill gain and Mastery paragraphs.

## Expected player reactions (prediction, 2026-10-02, for checking against beta)
- Likely net positive with returning adult players and crafters (no end-game macro or resource grind, predictable time to GM, fair to everyone); mixed with UOR purists ("GM without the grind isn't UO") and Hot Zone mages (a 90 mage casts Flamestrike at 75% against a veteran's 100% for about ten days); tamers mildly negative (dragons about day 7, with the pet restrictions on top).
- Expected complaints, most frequent first: a missed day is lost; "that use didn't count" (trivial actions); a cycle that resets mid-session; 17 or 25 days for Hard and VeryHard skills; an outage costing everyone a cycle; Skill Bank restoration looking like a bypass (it restores already-earned points).
- Watch in beta: the rate of missed cycles, where players stop, and the number of "didn't count" questions. The levers if feedback demands them are the ones the owner declined (one free missed day a week, a minimum-uses claim, a downtime credit).
