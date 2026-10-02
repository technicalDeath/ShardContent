# Beta 2a item 2: Mastery redesign audit

Roadmap: [Beta 2a](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 2 (deferred from Alpha 3 J-2/J-3). Design contract: Hot Zones plan, "Character Mastery cycles, skill allowances and limited banking" (DD 837-928), as ruled below.

## Sign-off (owner, 2026-10-02)
Plan approved with these answers. Do not reopen.
- **Activity rule: B with the bank.** A skill's allowance for a cycle is claimed by the first valid, successful use of that skill in the cycle. An unclaimed cycle for that skill is lost (not banked). Unspent allowance carries up to three cycles of that skill's allowance. There is no login-day rule: consistency means using the skill each cycle.
- **Total-cap blockage uses stock displacement.** A Mastery gain at the 700-point cap lowers a Down-locked skill exactly as stock does, so Skill Bank deposits still happen. With no Down skill the use grants and spends nothing.
- **Owner declined:** a minimum-uses claim threshold, a skill-reachability audit at 95+, and a downtime heartbeat. None is built. (Known consequence: one valid use claims a cycle; a skill with no non-trivial action above 95 cannot progress, as in stock.)
- Settled from the first plan, not changed: failed checks grant and spend nothing; the existing gain classes set the allowance (Easy 1.0 / Standard 0.5 / Hard 0.3 / VeryHard 0.2 per cycle); a skill reaching 95 mid-cycle claims that cycle's allowance once; Mastery replaces the as-built mechanic in place with no new feature flag.

## As-built (Alpha 1), being replaced
`MasteryProgression.cs`: shared 4-hour UTC periods, +0.1 pending per period on UTC days the character logged in (cap 0.6), each use spends 0.1 whether it succeeded or not, state in an account tag keyed by character serial, no feature flag. At the total cap it gained nothing and spent nothing.

## Design as built
| Rule | Behavior |
| --- | --- |
| Threshold | 95.0 (unchanged). Below it the gain curve and stock gain apply |
| Cycle | 24 hours per character, anchored at the server time the character first holds a 95+ skill (first valid use or login). Server clock only |
| Valid use | The stock hook fired (non-trivial check, region and anti-macro eligible), the check succeeded, the skill is Up-locked and below its cap, and a gain is possible (see cap rule) |
| Claim | The first valid use of a 95+ skill in a cycle adds that skill's allowance to its bank (capped), once per skill per cycle. Dropping below 95 and returning cannot claim a cycle twice; cycles missed meanwhile are lost |
| Allowance | Easy 10, Standard 5, Hard 3, VeryHard 2 tenths per cycle, by the skill's `skillGain` class; unlisted skills count as Standard |
| Gain | +0.1 per valid use while the bank is not empty, through stock `SkillCheck.Gain` (so displacement and the Skill Bank event are stock); never more than +0.1 |
| Bank | At most 3 cycles of that skill's allowance |
| Total cap | A gain displaces a Down-locked skill as stock does; with none, nothing is granted or spent |
| 100.0 | Mastery ends for the skill and its bank is cleared |
| Skill Bank | Restoration still acts first and neither claims nor spends allowance |
| Gain bonuses | None can change it: the decision is made before the stock gain roll and its multipliers |
| Entry | First valid use at 95+ (or login) tells the player Mastery has begun |
| Reminder | At login, a line when any Mastery skill has not claimed this cycle |
| `[MasteryStatus` | Per skill: value, class, allowance per cycle, bank, claimed this cycle, gains left; the next refresh. Staff may pass a player serial |

Minimum calendar cost at 24 hours: 5 / 10 / 17 / 25 cycles (Easy / Standard / Hard / VeryHard), each needing a valid use that cycle.

## Persistence and migration
Account tag `BritanniaRenaissance.Mastery.<serial>`, JSON version 2: `{version, anchor, skills:{id:{claimed, allowance}}}`. Version 1 (periods, login days, pending) is discarded on load: the workspace has no live population, per the roadmap.

## Decisions made while building (within the signed-off plan)
- **No ModernUO change was needed.** Stock `SkillCheck.Gain` is public, so Mastery calls it for the +0.1. That gives the stock cap displacement and the Skill Bank event for free. The result is clamped to +0.1 and the allowance is returned if stock declines.
- **A valid use also requires a possible gain.** A use at the total cap with no Down skill, a locked skill or a skill at its own cap claims and spends nothing (the contract's "blockage grants nothing").
- **Under the cap**, stock displacement is probabilistic, so a Mastery gain may occasionally lower a Down skill by 0.1, exactly as an ordinary gain does.
- **No refresh sweep.** Claiming is lazy, on use, so the 60-second sweep in the first plan was dropped. A login line tells the player when Mastery skills can still claim this cycle (sent three seconds after login; the client is not ready earlier).
- **Anchor** is set on the first valid use at 95+ or at login if the character already holds a 95+ skill.
- Staff support in production code: `[MasteryStatus <serial>` (administrators), `MasteryProgression.ShiftAnchorEarlier` and `ForgetCachedState` for the test probe.

## Acceptance matrix and results
Unit: `MasteryEngineTests` (cycles, one claim per cycle, lost cycles, three-cycle bank cap, backwards clock, spending, 5/10/17/25 cycles to 100, persistence, discard of version-1 state, config validation, the committed config values). Shard suite 387/387 (run `20261002T190230233Z-c24da4`). The two known UOContent failures are unrelated and no ModernUO file changed.

Live: disposable host `mastery-b`, real Navrey clients, real Anatomy checks (an Easy skill that still has a 5% failure chance at 95), a probe that moves the cycle anchor back (`tests/scenarios/mastery/mastery_live.py`, `MasteryProbe.cs`). 15/15 on the final build in the main run, plus 6/6 after a server restart.
| Case | Result |
| --- | --- |
| M1 first valid use at 95: entry message, claim of 1.0, +0.1 | pass |
| M2 ten gains empty the bank; Anatomy 96.0, 0.0 available, claimed | pass |
| M3 further valid uses with no allowance grant nothing | pass |
| M4 `[MasteryStatus` text (24 hours, next cycle, class, allowance) | pass |
| M5 after 24 hours the skill claims again and gains | pass |
| M6 four further cycles: the bank stops at three cycles (2.9 of 3.0 shown after spending) | pass |
| M7 below 95 Mastery does not act | pass |
| M8 back to 95 in the same cycle: no second claim, no second entry message, gain from the bank | pass |
| M9 saved state from the earlier mechanic is discarded | pass |
| M10 and Mastery starts fresh at the next use | pass |
| M11 Alchemy shows Hard 0.3, Magery Standard 0.5 | pass |
| C0 character at exactly 700 total | pass |
| C1 at the cap with no Down skill: no gain, no spend | pass (final run observed 0 gains, 0.0 available, not claimed; the first assertion mishandled a missing status line before Mastery began and was fixed, then rerun after the restart) |
| C2 with a Down skill: +0.1, total unchanged, claimed | pass |
| C3 the displaced point is in the Skill Bank (Fishing banked) | pass |
| R1 state survives a restart (claimed cycle and allowance) | pass |
| R2 login line when skills can still claim | pass |
Not exercised live: a failed check at 95+ (the 5% case; covered by the `!success` branch and unit rules), the Skill Bank restoration path above 95 (unchanged, covered by Alpha 3 evidence), and a skill reaching 100.0 (covered by the clear-on-100 branch only).

## Player text (for owner review with the release)
- Entry: "<Skill> has reached 95.0: ordinary gain has ended and Mastery begins. Use [MasteryStatus to see your allowance."
- Claim: "Mastery: <Skill> claims this cycle's allowance of 1.0."
- Gain: "Mastery advanced <Skill> to 95.1. Allowance left: 0.9."
- Grandmaster: "<Skill> has reached Grandmaster (100.0)."
- Login: "Mastery: N of your Mastery skills can claim this cycle's allowance with a valid use. Use [MasteryStatus for details."
- `[MasteryStatus`: the rule summary, a line saying what counts as valid ("A use is valid only if it had a real chance of failing. Trivially easy actions and failed attempts count for nothing."), the cycle length, "Your next cycle begins in 5h 12m." (countdown only, no UTC time), and one line per skill ("Anatomy 96.0 (easy): 1.0 per cycle, 0.0 stored (holds up to 3.0), claimed this cycle, 4.0 points to reach 100.0."). "Stored" avoids confusion with the Skill Bank. The wording was revised on the owner's review the same day.
- README Skill section: a new Mastery paragraph.
