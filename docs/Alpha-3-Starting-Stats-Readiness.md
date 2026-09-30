# Alpha 3 Phase B: Starting stats readiness

**Decision:** Ready for Alpha 3 enablement, with `alpha3StartingStats` still disabled. This closes feature readiness only; Phase L activation remains a separate owner decision.

## Current-source review

- The existing ordinary-client creation matrix remains applicable: Warrior 50/40/30, Mage 30/30/60, Blacksmith 60/30/30, and Advanced 42/42/36. Each totals 120, each stat is at least 30, and the configured character stat cap remains 225. The ordinary Advanced case used Healing 50 and Anatomy 50. Details and earlier result are in [the starter package audit](Alpha-3-Starter-Package-Audit.md#combined-ordinary-creation-packet-matrix-september-27).
- Current `CharacterCreation.OnCharacterCreated` resolves the selected profession, creates a player, initializes stock stats, and then applies the normal profession skills and items. The incoming creation packet invokes the stock creation event first and then invokes the shard `CharacterCreatedHandler` with the same populated event args and created mobile.
- `Alpha3StartingStats.Configure` uses additive registration (`+=`) behind an idempotence guard. `Apply` filters to ordinary player mobiles and checks `alpha3StartingStats` before changing stats. It reads the active profession definition for Warrior, Mage, and Blacksmith, and uses the Advanced packet's requested stats for Advanced choices.
- The allocation keeps the approved three named allocations. Advanced uses the player's preference weights while applying a 30 minimum and distributing its remaining 30 points deterministically. Existing unit cases cover template values, minimums, exact totals, and preference weighting.
- The only uncommitted edits in the inspected ModernUO character-creation source add a starting-gold callback and reject Mysticism in a later-era skill-validation case. They do not change profession stat resolution, stock `SetStats`, or the post-event shard callback. The profession definition source was unchanged. No accepted stat case needs to be reopened.

## Gate and verification

The validator requires `alpha3EnablementAcknowledged` when `alpha3StartingStats` is true. Current source configuration has `alpha3StartingStats:false` and `alpha3EnablementAcknowledged:false`; no configuration or runtime deployment change was made.

No checks were rerun because the accepted four-client creation matrix and focused implementation tests already cover this path, and this review found no relevant source change since that evidence. The existing audit records the combined creation rehearsal and 210 passing Shard tests after callback registration was corrected. The acknowledged Alpha 3 gate remains independent from this readiness decision.

## Readiness limits

This pass covers the specified four creation templates and the current Shard/ModernUO creation path. It does not authorize Alpha 3 activation or alter the configured 225 stat cap.

**Phase L review (2026-09-30):** `Alpha3StartingStats.cs` and ModernUO's `CharacterCreation.cs` are unchanged since this evidence through current HEAD (zero diff). CLEAN, no reopening.
