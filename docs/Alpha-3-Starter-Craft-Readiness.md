# Alpha 3 Phase H: Starter craft materials and tools readiness

**Decision:** Ready for Alpha 3 enablement, with `alpha3StarterCraftMaterials` still disabled (the validator hard-rejects it outright regardless; see Gate and validator). This closes feature readiness only; the combined Phase L activation decision remains outstanding.

## Reused accepted evidence

- The existing `ST-ECON-CRAFT-*` rows in the [starter audit](Alpha-3-Starter-Package-Audit.md#economy-route-checkpoint--september-28-2026) (Blacksmith Dagger, Tinkering Gears/Scissors, Carpentry chair, Tailoring shirt/leather cap, Bowyer shaft/arrow, Scribe runebook, Alchemy potion, Cooking fish) proved stock crafting systems accept the bound subclasses as valid resource inputs, via `CraftItem.ConsumeRes`/`Container.GetAmount`'s subclass-inclusive type matching (`Type.IsAssignableFrom`, confirmed by source trace). A plain stock type is a strictly simpler case (no subclass matching involved at all), so this evidence is reused as direction-confirming for the redesigned plain-type grants, not re-run from scratch.
- The vendor/trade/salvage/BOD guard mechanism, and the Newbied-blocks-vendor-sale guard specifically, are unchanged from Feature G: `GenericSell.cs`'s `NontransferableItemPolicy.ContainsVendorRestricted` is generic (checks `Nontransferable` or `LootType.Newbied`), not combat-specific, so it already covers every one of H's newbied item types with no new guard code. Reused directly from G's `StarterBoundVendorTests` (UOContent.Tests).

## Current-source review

Stock `CharacterCreation.cs`'s per-skill `AddSkillItems` grants for the 8 craft categories were traced exactly (file:line cited in the contract review and readiness record). Two real gaps against the design doc's targets: stock Tinkering never grants ingots in any era (only three random tinker parts), and stock Tailoring's own grant is a `BoltOfCloth`, which Tailoring's crafting recipes cannot consume as a `Cloth` resource. Both are resolved as additions, not top-ups. Stock's own `BaseTool`/`Pickaxe` constructors give a random 25-75 (BaseTool) or a hardcoded 50 (Pickaxe, coincidentally matching the shard's chosen convention) uses; none of the granted item constructors set `LootType` themselves, so all are eligible for (and receive) the same UOR-era auto-newbie stamp G relied on.

`StarterCraftMaterialIssuance.Issue()` is now a uniform `ClaimOnce`/`TopUp`/`SetToolUses` pattern per craft category, gated on `Alpha3StarterCraftMaterials` and the pre-existing per-account entitlement tag (versioned to `v2` since the grant shape changed from bound-replacement to top-up/addition). It never deletes anything stock already granted - this is also what fixes H-2 structurally, the same way G-1's redesign fixed G-5. All ~25 bound material/reagent/tool types (`StarterIronIngot`, `StarterBoard`, `StarterFeather`, `StarterCloth`, `StarterLeather`, `StarterBlankScroll`, `StarterBottle`, `StarterRawFishSteak`, `StarterKindling`, the 8 reagent types, and the 8 tool types) are deleted; only `StarterScissors` (D) and `BackpackWard` (F) remain bound anywhere in the codebase.

The ModernUO pin (`pinnedModernUoCommit`) was bumped from `16f6189ae...` to `df67e74b4...` (the vendor-guard commit) across `shard-rules.json`, `world-generation.json` and `Alpha2bWorldGenerationConfigurationTests.cs`; `Deploy-Alpha1Baseline.ps1` refused to run against the stale pin, since it postdated that commit.

## New verification

Full Shard suite: 230/230 (verification run `20260928T200647938Z-a35d89`, after the pin bump). No new UOContent tests were needed - G's `StarterBoundVendorTests` already cover the generic Newbied-vendor-guard behavior H relies on.

Live: seven fresh ordinary accounts on disposable host `phase-h`, created in one continuous server run via `New-TestCharacter.ps1 -NoRestart` (so the in-memory `TestOnlyFlagOverride` stayed live across all seven `createcharacter` calls) - Blacksmith profession (Blacksmith+Tinkering+Mining together) and six Advanced characters (Tailoring, Carpentry, Fletching, Inscribe, Alchemy, Cooking, each paired with Camping as a neutral filler skill). Server-side `TestOnlyInventoryInspect` confirmed every category's exact target quantity, correct Newbied stamping, and no Nontransferable flag, across all 8 craft categories in one pass. A save/restart cycle on the most complex character (the combined Blacksmith+Tinker grant) reproduced identical serials and amounts, closing persistence. Full details, including two harmless unexplained stock quirks and named gaps in the live pass (no live H-2 second-character repro, no independent tool-charge confirmation), are in the [starter audit's Phase H section](Alpha-3-Starter-Package-Audit.md#owner-rulings-and-phase-h-closure--september-28-2026).

## Gate and validator

Source and deployed `alpha3StarterCraftMaterials` are both `false`. `ShardRulesConfiguration.Validate` still hard-rejects this flag outright (H-6, unchanged) - it cannot be set `true` in `shard-rules.json` even on a disposable host; `Load()` throws before the server starts. Live gated testing used the shared, feature-agnostic `TestOnlyFlagOverride`/`TestOnlyInventoryInspect` probe (`ShardContent/tests/scenarios/alpha3-tools/TestOnlyProbe.cs`, generalized from Feature G's own one-off version) rather than any validator change.

## Readiness limits

- Two stock quirks observed live but not chased further, since neither is touched by shard code: a Blacksmith-profession character (no Tailoring selected) also receives a stock `BoltOfCloth`/`SewingKit`, likely from Mining's own stock skill-item grant (Mining wasn't in scope for the traced 8 craft categories).
- Blacksmith's and Tinker's IronIngot grants don't merge into one stack (`Container.DropItem` doesn't auto-merge same-type items the way player drag-drop does) - functionally identical for crafting resource-counting, just a cosmetic difference from the old bound design.
- Tool charge (fixed 50 uses, the owner's deliberate deviation from stock's own random 25-75) wasn't independently confirmed live - `TestOnlyInventoryInspect` doesn't report `UsesRemaining`. The mechanism is simple and build-verified (same `IUsesRemaining` interface `Pickaxe` itself already uses for its own stock-hardcoded 50).
- H-2's fix (a second same-profession character on one account keeps its own ordinary stock grant rather than losing it) was verified by source inspection only, not a live second-character-same-account repro - the current test tooling creates a fresh account per character name.
- No fresh live crafting-consumption pass for the redesigned plain stock types specifically; the existing bound-subclass evidence is reused as direction-confirming (see Reused accepted evidence) rather than re-run.

**Phase L review (2026-09-30):** `StarterCraftMaterialIssuance.cs` and the shared vendor-sale guard are unchanged since this evidence through current HEAD. H issues no weapons, so today's `BaseWeapon.PoisonCorrosionEnabled` toggle has no overlap. CLEAN, no reopening.
