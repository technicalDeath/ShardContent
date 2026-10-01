# Beta 1: skill-gain curve readiness

**Decision:** Ready and **activated** (owner sign-off 2026-10-01, "turn on when verified"): `featureFlags.skillGainCurve` is true in source and deployed `shard-rules.json`. This closes Beta 1 scope item 3; the live-client 120-stat test and era-correct ClassicUO templates remain.

## Reused accepted evidence
- Skill Bank restoration and Mastery both act through `SkillEvents.SkillGainOverride`, before the stock roll. That ordering is unchanged, and the new hook sits after it.

## Current-source review
Full design, survey and numbers are in [the audit](Beta-1-Skill-Gain-Curve-Audit.md). ModernUO gained one null-by-default delegate (`SkillEvents.GainChanceMultiplier`) applied in `SkillCheck.CheckSkill` after `GainFactor`; the class table, bands and service live in ShardContent (`SkillGainCurveService`, `skillGain` in `shard-rules.json`). The owner replaced the contract's hour targets with a stock-relative multiplier rule and approved the class assignment (Easy 19, Standard 26, Hard 4, VeryHard defined but empty).

## New verification
3 ModernUO hook tests (24/24 in `SkillEventsTests`), 25 ShardContent test cases (62/62 in the focused run with the config tests), full Shard suite 315/315, ModernUO Skill/Pet/Elf subset 201/201. Live, on a disposable host with the flag on: 34/34 (measured gain-rate ratios per class and band within 4% of the multipliers, sub-10 unchanged, no stock-roll gain at 95.0, staff stock, Skill Bank restore exact with the curve on and off, flag-off equals stock, `[SkillClasses` output, 120 real client skill uses gained 8.3 points). The dev host also booted clean with the flag on after deploy.

## Gate and validator
Source and deployed `shard-rules.json` match with `skillGainCurve` true. The validator requires every UOR skill assigned to a defined class, ascending bands from 0, and multipliers above 0 and at most 5.

## Readiness limits
- **ModernUO change is uncommitted.** `Skills/SkillCheck.cs`, `Skills/SkillEvents.cs` and `SkillEventsTests.cs` are in the working tree; the pinned ModernUO commit in `shard-rules.json` still names the previous HEAD. When ModernUO is committed, bump `pinnedModernUoCommit` in the three places (see the `shard-server` skill) before the next deploy.
- **Players only.** Staff, creatures and pets get stock gain. A pet's own gain keeps the stock doubling.
- **The curve changes probability only.** It does not change range limits (training dummy and butte stop at 25, Magic Resist stops above the spell's circle cap, recipe ranges), anti-macro (off) or stat gain.
- **Saturation.** A 1.5x multiplier caps at certainty. The measured early bands never reached it; very low totals with low skill could, which only makes those few checks always gain.
- **Dev-world effect.** The curve is on for existing characters the next time the dev server starts.
- **VeryHard is defined as a copy of Hard and has no skills.** Mastery (Beta 2a) reuses the four class names; changing a skill's class or a class's bands is a config edit.
- **Hour targets in the Hot Zones contract are superseded** by the stock-relative rule. The contract text still describes them.
- Player text (`[SkillClasses`) is for the owner's review with the release.
- Two UOContent tests fail on ModernUO HEAD independent of this item (see the Elf audit).
