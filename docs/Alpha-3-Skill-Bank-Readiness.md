# Alpha 3 Phase A: Skill Bank readiness

**Decision:** Ready for Alpha 3 enablement, with the `skillBank` source flag still off. This is a feature-readiness decision only; it is not the Phase L activation acknowledgment.

## Current-source review

- The accepted gain, cap, retention, restoration, Mastery ordering, recovery, ordinary-client, and three-save/reload matrix remains applicable. Its test and rehearsal evidence is recorded in [the persistence rehearsal](Alpha-3-Skill-Bank-Persistence-Rehearsal.md).
- `SkillEvents.SkillDisplaced` is emitted for eligible organic displacement after anti-macro checks. Scripted changes and modifier-only losses do not publish bankable displacement; the focused UOContent cases cover the anti-macro denial boundary.
- `SkillBankService` is configured idempotently, subscribes once to the displacement event, and checks the runtime `skillBank` gate for deposits, restoration, and player-facing bank actions. The Mastery path asks the bank to restore before applying the Mastery threshold logic.
- The ledger validates and bounds balances; the PlayerMobile persistence record stores the ledger payload and recovery archive with the active skills. Staff recovery archives malformed data and does not change active skills. The recovery and persistence paths remain usable for diagnostics while the feature gate is off.
- Capacity remains configured as 3000 tenths (300.0 points), within the validator's 1–60000 tenths range. No source or deployed runtime policy was changed to turn the feature on.
- Phase A excludes time-driven Mastery award scheduling and broader skill contract review; those remain in Phase J.

## Validator and configuration decision

The former blanket validator rejection prevented a reviewed Skill Bank feature from ever passing validation, even after the separate Alpha 3 acknowledgment. The guard is now conditional: `skillBank:true` is rejected until `alpha3EnablementAcknowledged:true`; after acknowledgment it may validate, subject to all other rules. This change does not activate Skill Bank. Current source configuration has both values false. The checked-in deployed configuration is older and has no Alpha 3 acknowledgment or Skill Bank setting; no deployment was performed.

The validator tests cover rejection without acknowledgment, acceptance with acknowledgment, and the unchanged capacity bound. The feature gate remains an independent runtime switch, so final activation still requires the Phase L owner decision and the explicit flag change after release review.

## Verification

Focused isolated source verification passed on 2026-09-28:

- Command: `./ShardContent/tools/Invoke-AgentVerification.ps1 -Suite Shard -Filter 'FullyQualifiedName~SkillBankLedgerTests|FullyQualifiedName~ShardRulesConfigurationTests'`
- Result: 45 passed, 0 failed; report `work/agent-verification/runs/20260928T135430222Z-291f4c`.
- The runner built current ModernUO references, did not deploy to the shared host, and recorded source fingerprints. No shared server or save was changed.

## Readiness limits

This closes Phase A only. The existing rehearsal's explicit limitations remain, including no live-client capture for every recovery message branch and no time-driven Mastery award-period test here. Mastery period behavior and the wider UOR skill audit remain assigned to Phase J. Alpha 3 flags remain off pending Phase L.
