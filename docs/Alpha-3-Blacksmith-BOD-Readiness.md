# Alpha 3 Phase I: Blacksmith Bulk Order Deeds readiness

**Decision:** Ready for Alpha 3 enablement. Smith BODs have no separate shard flag (they ride the pre-existing `ContentFeatureFlags.BulkOrders` stock flag, already `true`); `alpha3EnablementAcknowledged` stays false. This closes feature readiness only; the combined Phase L activation decision remains outstanding.

## Reused accepted evidence

- The Blacksmith BOD deviation itself (Smith BODs enabled under UOR, ahead of the April 2000 baseline; Publish 14, November 2001) was already owner-approved and is unchanged by this pass. Focused vendor tests and an ordinary-client Smith-deed issue/acceptance check, with no Tailor BOD option visible, were previously accepted — see [Alpha-3-Player-Skill-Audit.md](Alpha-3-Player-Skill-Audit.md#inventory), skill ID 7 and SK-003.
- The Publish 16 reward exclusion (Runic Hammer, Blacksmith Scrolls of Power, Gargoyle's Pickaxe, Prospector's Tool, Powder of Temperament) and the resulting gold-only top tiers were already built and tested; unchanged by this pass.
- The Tailor/Weaver `Core.AOS` gate pattern (unchanged stock code) is the reused reference behavior for reverting Weaponsmith to the same gate.

## Current-source review

Traced the full Smith BOD path in `ModernUO/Projects/UOContent/Engines/Bulk Orders/Rewards.cs` and `Mobiles/Vendors/NPC/{Blacksmith,Weaponsmith,Tailor,Weaver}.cs`, plus the vendor context-menu entry point in `BaseVendor.cs:1371-1397`. Findings and rulings (Contract-Review.md I-1 through I-6, 2026-09-28):

- **I-1, I-3** (Smith BODs under UOR; Publish 16 exclusions): kept, unchanged.
- **I-2** (gold-only top tiers): the runic-hammer/power-scroll exclusion leaves point tiers 500, 550, 600, 650, 700, 800, 900, 950, 1050, 1150 and 1200 with zero items after filtering, since every reward in those specific groups was excluded. Kept as-is (gold + fame only) — zero new engineering. The owner asked for a Beta 3 note to add a real reward to these tiers; recorded as a named limitation below, not a blocker.
- **I-4** (five unclassified reward types: `SturdyShovel`, `SturdyPickaxe`, the three `GlovesOfMining` variants, `ColoredAnvil`, `AncientSmithyHammer`): kept in the pool, conditioned on no UOR-era-rule violation. Traced each: all are plain `BaseHarvestTool`/`BaseAxe`/`BaseArmor`/`BaseTool`/`Item` types using only the stock dual Old/AOS stat fields already used everywhere in armor and weapons. `AncientSmithyHammer` and `GlovesOfMining` apply a flat, era-independent `SkillMod` (+Blacksmith / +Mining) directly in their own class code — not through `AosSkillBonuses` or gated by `SkillCheck.IsSkillAvailable`, and neither would block it anyway since Blacksmith and Mining are always-available skills. No violation found.
- **I-5** (222,222-gold maximum payout): confirmed as pure stock math — `Rewards.cs`'s Platemail-exceptional gold table caps at a 200,000 cell, and `ComputeGold` applies a `gold * 10 / 9` random upper bound (`200000 * 10 / 9 = 222222`), for a GM six-piece exceptional high-material Large BOD. Not shard-modified. Accepted as-is.
- **I-6** (Weaponsmith BOD issuance under UOR): found to be an existing, unruled shard deviation. Stock ModernUO gates `Weaponsmith.SupportsBulkOrders` behind `Core.AOS` (identical pattern to `Tailor.SupportsBulkOrders`); `Blacksmith.SupportsBulkOrders` has never had that gate in stock. An earlier shard commit (`16f6189ae`) had dropped `Core.AOS &&` from `Weaponsmith.SupportsBulkOrders` only. Traced the deed/reward content itself: both vendor types draw from the identical `SmallSmithBOD`/`LargeSmithBOD` pool, the same 50/50 random draw between `SmallBulkEntry.BlacksmithWeapons` (axes, maces, polearms, swords — all Blacksmithing-craftable, no Fletching/bow items) and `SmallBulkEntry.BlacksmithArmor`, and the same `SmithRewardCalculator` tables and UOR filtering — there is no distinct "Weaponsmith BOD," only a second issuing NPC. The owner ruled to match stock: reverted `Weaponsmith.SupportsBulkOrders` to require `Core.AOS` again (`ModernUO/Projects/UOContent/Mobiles/Vendors/NPC/Weaponsmith.cs:81-82`). `BaseVendor.cs`'s own `Core.AOS` removal (needed for Blacksmith's already-approved UOR support, since `BaseVendor.OnClick` gates on `vendor.SupportsBulkOrders(from)` before reaching that code) was left untouched — it doesn't bypass the per-vendor gate, so nothing else needed to change.

No ShardContent code exists for this feature at all — every custom rule above lives in the ModernUO fork (`ModernUO/Projects/UOContent`), gated only by era (`Core.AOS`), not by a `ShardContent` feature flag.

## New verification

- `UorBulkOrderVendorTests.cs` updated: renamed `UorKeepsBlacksmithOrdersAndGatesTailoringOrders` to `UorKeepsBlacksmithOrdersAndGatesTailoringAndWeaponsmithOrders` (now asserts Weaponsmith is also gated under UOR, alongside Tailor/Weaver); replaced `AoSKeepsTailoringBulkOrdersAvailable` with `AoSRestoresWeaponsmithOrdersAndTailoringOrders` (asserts Weaponsmith, Tailor and Weaver all support and issue BODs once `Core.Expansion = Expansion.AOS`).
- Focused UOContent run (`FullyQualifiedName~BulkOrder|FullyQualifiedName~SmithBod|FullyQualifiedName~StarterBound`): 18/18 passed, run `work/agent-verification/runs/20260928T231102384Z-969cdc`.
- Full Shard suite (post-pin, current source): 230/230 passed, run `work/agent-verification/runs/20260928T231015147Z-28e4d8`.
- No new live-client pass: the negative case (Weaponsmith no longer shows an "Order" option under UOR) is a straightforward boolean gate, mechanically identical to the already-accepted Tailor/Weaver pattern, and is directly asserted by the updated unit test. The existing live Smith-deed issue/acceptance evidence (Blacksmith vendor, no Tailor BOD option visible) is reused unchanged, since Blacksmith's own behavior did not change.

## Gate and validator

Smith BODs have no dedicated `ShardRulesConfiguration` flag; they ride the stock `ContentFeatureFlags.BulkOrders` flag (`ModernUO/Distribution/Configuration/FeatureFlags/flags.json`), already enabled. `alpha3EnablementAcknowledged` remains `false` on both source and deployed configuration. No validator change was needed or made.

## Readiness limits

- The five reward types in I-4 are accepted without a confirmed April 2000/November 2001 first-availability date — official references only confirm them by 2003 (Publish 18) and the current live catalog. The owner chose to accept this given no functional UOR-rule violation, rather than block on further historical research.
- The gold-only reward tiers (I-2) are a known, named gap the owner wants revisited in **Beta 3** with a real reward addition — not tracked as an Alpha 3 blocker.
- The 222,222-gold maximum payout (I-5) has not been tested against the shard's live economy in practice (e.g., how quickly a GM Blacksmith could reach it); accepted as a rare, GM-tier ceiling consistent with BODs already being an approved deviation, not economy-simulated.
- No fresh live client pass for Weaponsmith's reverted (now-negative) UOR gate; covered by unit test only, per the reasoning in New verification above.

**Phase L review (2026-09-30):** `Rewards.cs`, `BaseVendor.cs` and the smith/tailor/weaver vendor files are unchanged since this evidence through current HEAD. No BOD reward item carries a poison property, so today's `BaseWeapon.PoisonCorrosionEnabled` toggle has no overlap. CLEAN, no reopening.
