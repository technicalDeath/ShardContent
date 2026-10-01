# Beta 1: cosmetic Elf readiness

**Decision:** Ready and **activated** (owner sign-off 2026-09-30): `CharacterListFlags.ML` is true in source and deployed `expansion.json`. `SupportedFeatures.ML`, `SupportedFeatures.SA` and `Id` (UOR) are unchanged. This closes Beta 1 scope item 1 only; pet restrictions, the gain curve and the two client-creation items remain.

## Reused accepted evidence
- `CosmeticElfPolicy` (Alpha 3, ModernUO `16f6189ae`): equipment and Cu Sidhe routing through the Human gameplay race. Reconfirmed live and by unit test; unchanged.

## Current-source review
All hooks are as described in [the audit](Beta-1-Cosmetic-Elf-Audit.md). The only code change in ShardContent is `CosmeticElfCreationService` (testable split, registered last). ModernUO has no engine change. The ClassicUO gump change and the rebuilt `bin/dist/cuo.dll` are what players run; the same source change is in Navrey.

## New verification
Matrix, run IDs and live results are in [Beta-1-Cosmetic-Elf-Audit.md](Beta-1-Cosmetic-Elf-Audit.md): 24 ShardContent and 9 UOContent unit tests for this item, 267/267 full Shard suite, and a 12-character live run on a disposable host covering creation, parity, forged packets, death, resurrection, save/restart and equipment.

## Gate and validator
Source and deployed `expansion.json` match. The era-gate validator still requires `SupportedFeatures.ML` false and accepts the activated file; the dev host boots with it.

## Readiness limits
- The player build's creation screen was verified through Navrey's identical-source gump (headless), not by driving `bin/dist` visually. The owner may want to look once at the Elf button in the real client.
- Staff accounts are excluded by `AppliesTo` (unit-tested) but no staff Elf creation was run live.
- Left stock by decision: Disguise Kit hair/beards, Polymorph hue on human bodies, the NPC hairstylist for elves.
- ML-gated racial code is inert under UOR and guarded by parity tests, not re-routed. Raising `Core.Expansion` would need that revisited.
- Two UOContent tests fail on ModernUO HEAD independent of this item (listed in the audit).
