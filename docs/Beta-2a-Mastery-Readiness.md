# Beta 2a item 2: Mastery redesign readiness

**Decision:** Built, verified live on a disposable host and deployed to the dev distribution (2026-10-02). Mastery has no feature flag, so the new rules are live as soon as the dev server next starts. No flag was changed. Closes Beta 2a scope item 2; permanent Hythloth remains.

## Reused accepted evidence
- Skill Bank restoration still acts first through `SkillEvents.SkillGainOverride` and neither claims nor spends allowance. The Alpha 3 Skill Bank matrix applies unchanged.
- The Beta 1 gain curve's class table is reused for the allowance. Its range now ends at 90.0, where Mastery begins; the class multipliers themselves are unchanged.

## Current-source review
Full design, rulings, the case for 90 and results are in [the audit](Beta-2a-Mastery-Audit.md). `MasteryEngine.cs` holds the rules without game types and the threshold constant, `MasteryProgression.cs` runs them, and `shard-rules.json` has a `mastery` section (cycle hours, cycles stored, allowance per class) with validation. No ModernUO change.

## New verification
`MasteryEngineTests` and updated `SkillGainCurveTests` (Shard suite 388/388); live on a disposable host at threshold 90, 15/15 plus 2/2 after a restart, including the total-cap displacement and the Skill Bank deposit.

## Rulings built (owner, 2026-10-02)
- B with the bank: a skill claims its cycle's allowance with its first valid successful use, an unclaimed cycle is lost, unspent allowance carries up to three cycles; no login-day rule; a gain at the total cap displaces a Down skill as stock does.
- Mastery starts at 90.0 with allowances Easy 2.0 / Standard 1.0 / Hard 0.6 / VeryHard 0.4 per cycle (minimum 5 / 10 / 17 / 25 days to 100).

## Readiness limits
- **Owner declined three hardening items** (see the audit): a minimum-uses claim threshold, a skill-reachability audit, and a downtime heartbeat. One valid use therefore claims a cycle, a skill whose every action is trivial near 100 cannot progress (as in stock), and a long server outage costs everyone cycles.
- **Decide threshold and allowance changes before release.** After launch they would strand players part-way through the band.
- Saved state is an account tag, version 2. Version 1 (the Alpha 1 mechanic) is discarded on load; characters already at 90+ in the dev world start a fresh cycle with a full first allowance.
- Not exercised live: a failed check at 90+, the move to 100.0, and Skill Bank restoration above 90 (all covered by code paths and earlier evidence).
- Player text, and a prediction of player reactions to check in beta, are in the audit for the owner's review with the release.
- Two UOContent tests fail on ModernUO HEAD independent of this item (see the Elf audit).
