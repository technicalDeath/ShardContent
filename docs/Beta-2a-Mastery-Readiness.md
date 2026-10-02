# Beta 2a item 2: Mastery redesign readiness

**Decision:** Built, verified live on a disposable host and deployed to the dev distribution (2026-10-02). Mastery has no feature flag, so the new rules are live as soon as the dev server next starts. No flag was changed. Closes Beta 2a scope item 2; permanent Hythloth remains.

## Reused accepted evidence
- Skill Bank restoration still acts first through `SkillEvents.SkillGainOverride` and neither claims nor spends allowance. The Alpha 3 Skill Bank matrix applies unchanged.
- The Beta 1 gain curve still ends at 95.0 and its class table is reused for the allowance.

## Current-source review
Full design, rulings and results are in [the audit](Beta-2a-Mastery-Audit.md). `MasteryEngine.cs` holds the rules without game types, `MasteryProgression.cs` runs them, and `shard-rules.json` gains a `mastery` section (cycle hours, bank cycles, allowance per class) with validation. No ModernUO change.

## New verification
New `MasteryEngineTests` (Shard suite 360 to 387, all passing); live on a disposable host, 15/15 plus 6/6 after a restart, including the total-cap displacement and the Skill Bank deposit.

## Rulings built (owner, 2026-10-02)
B with the bank: a skill claims its cycle's allowance with its first valid successful use, an unclaimed cycle is lost, unspent allowance carries up to three cycles; no login-day rule; a gain at the total cap displaces a Down skill as stock does.

## Readiness limits
- **Owner declined three hardening items** (see the audit): a minimum-uses claim threshold, an audit of whether every skill has a non-trivial action above 95, and a downtime heartbeat. One valid use therefore claims a cycle, a skill whose every action is trivial at 95+ cannot progress (as in stock), and a long server outage costs everyone cycles.
- Saved state is an account tag, now version 2. Version 1 (the Alpha 1 mechanic) is discarded on load; characters already at 95+ in the dev world start a fresh cycle with a full first allowance.
- Not exercised live: a failed check at 95+, the move to 100.0, and Skill Bank restoration above 95 (all covered by code paths and earlier evidence).
- Player text is collected in the audit for the owner's review with the release.
- Two UOContent tests fail on ModernUO HEAD independent of this item (see the Elf audit).
- Nothing is committed or pushed.
