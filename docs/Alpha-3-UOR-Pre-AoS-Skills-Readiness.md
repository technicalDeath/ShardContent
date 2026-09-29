# Alpha 3 Phase J (slice 2): pre-AoS skill families readiness

**Decision:** Ready for Alpha 3 enablement on a **source-survey basis only**, with every flag still disabled and `alpha3EnablementAcknowledged` false. The owner directed on 2026-09-28 that this pass needs no live or automated evidence. This closes Feature J readiness only; the combined Phase L decision remains outstanding.

## Reused accepted evidence

- Slice 1 (later-era IDs 49–57 and the skill-15 ruling): [Alpha-3-UOR-Later-Era-Skills-Readiness.md](Alpha-3-UOR-Later-Era-Skills-Readiness.md).
- Earlier J fixes and their tests (UOR entry gates, Arms Lore, delays, item bonuses, Poisoning corrosion, Peacemaking timing): [Alpha-3-Player-Skill-Audit.md](Alpha-3-Player-Skill-Audit.md), SK-002 to SK-007.

## Current-source review

Five read-only, agent-assisted source surveys covered IDs 0–48 by family (combat/magic, bard/animal, stealth/crime, craft/harvest, medical/utility). Key claims were spot-checked against source. No high-confidence unapproved era leak was found. Under UOR the AoS/SE/ML/SA branches are inert, and player crafting is limited to T2A whitelist menus. Full findings are in the audit's "Pre-AoS family source survey" section. Owner rulings are in [Alpha-3-Stock-Default-Audit.md](Alpha-3-Stock-Default-Audit.md) rows 10–16 and audit entries SK-008 to SK-013:

| Item | Ruling (2026-09-28) |
| --- | --- |
| Fishing catch table | Keep stock |
| Pet stock rules | Keep stock |
| Small items (Forensic looter reveal, potion kegs, Runebook craft, town field/summon block, bandage-target packet) | Keep stock |
| Bard difficulty add-ons; Animal Lore 110 limit | Provisionally keep stock; revisit after live play |
| Felucca doubled harvest | **Changed to single yield** before AoS |
| Treasure-map monster drops; level-0 maps | Keep drops stock; level 0 unreachable, no action |

## New verification

- Code change: `ModernUO/Projects/UOContent/Engines/Harvest/Core/HarvestSystem.cs` applies the Felucca yield bonus only when `Core.AOS`.
- Isolated ModernUO build succeeded and the focused UOContent test `UorLaterEraItemGate` passed 7/7 (run `20260929T030851323Z-d5dd57`). No harvest-yield test was written.

## Gate and validator

No feature-flag or `ShardRulesConfiguration` change. The harvest change is an era gate on stock ModernUO code. The ModernUO commit will move once this is committed, so `pinnedModernUoCommit` needs a bump before the next `Deploy-Alpha1Baseline.ps1`.

## Readiness limits

- **No live-client evidence** for any of the 48 pre-AoS skills. Their inventory rows in the audit stay `Pending`.
- The surveys are not exhaustive, and their April 2000 dating rests on recollection rather than dated sources.
- The single-yield harvest change is compile-checked only.
- Old-version poisoned-weapon load fixture and normal-client poison behavior (SK-005) are not tested.
- Open live checks for later: Cooking menu reachability, Meditation and Resisting Spells numbers, Magery cast timing, Item Identification relabel, Tracking arrow, stone/sand mining, bandage formula.
- Passive Detect Hidden and Young rulings (Stock-Default-Audit #1, #2; SK-007) and rows 3–9 remain owner decisions outside this pass.
