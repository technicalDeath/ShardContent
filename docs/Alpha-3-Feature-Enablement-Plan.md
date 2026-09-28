# Alpha 3 feature enablement plan

**Status:** Proposed alphabetical work order for owner review, 2026-09-28. No Alpha 3 feature is authorized for activation by this plan.

The [phased roadmap](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md#alpha-3--geographic-risk-progression-and-skill-foundation) defines Alpha 3 scope, and the [alternative plan](ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md) defines the approved feature contracts. This is the sole active Alpha 3 execution plan. The [implementation log](Alpha-3-Implementation-Log.md) preserves earlier decisions and dated results as history; the linked feature audits hold detailed evidence. Use current source, configuration and evidence when a letter begins. Do not repeat an accepted check unless its relevant implementation, configuration or data changed.

## Working rule

Work on **one lettered feature at a time**. Close its named behavior, entry point, economy, failure and persistence cases; run the focused checks and ordinary-client cases that exercise distinct paths; then record a feature-readiness decision with evidence and remaining limits. Begin the next letter after the current feature is ready or the owner explicitly changes the order or suspends a blocked feature. A feature can be **ready for Alpha 3 enablement** while its source flag remains off. The final phase-level activation decision is separate.

All source Alpha 3 feature flags and `alpha3EnablementAcknowledged` are currently false. The validator requires `alpha3EnablementAcknowledged` for `skillBank`, `hotZones` and the other Alpha 3 flags, and independently rejects `alpha3StarterCraftMaterials` and `alpha3StarterCombatGear`; changing that guard belongs to the relevant readiness or release work and does not itself enable a feature. Do not change the shared host or saves for a planning step. Use isolated current-source verification and a disposable world for risky state, migration and death cases.

## Feature list and order

| Phase | Feature | Source gate | Evidence already on file | Readiness state |
| --- | --- | --- | --- | --- |
| A | Skill Bank | `skillBank` | Focused ledger, gain, recovery, ordinary-client and three-save/reload matrix | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Skill-Bank-Readiness.md) |
| B | Starting stats | `alpha3StartingStats` | Four normal creation templates, including Advanced, met 120 total and 30 minimum | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Starting-Stats-Readiness.md) |
| C | Starter gold | `alpha3StarterGold` | 500 once-per-account, repeated character and save/restart checks; ordinary first grant | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Starter-Gold-Readiness.md) |
| D | Starter scissors | `alpha3StarterScissors` | Issuance/no-regrant probe, ordinary Healing creation, paired transfer matrix, movement callback; 2026-09-28 newbied death rule re-verified live (E-NOBAG, E-MURDERER) | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Starter-Scissors-Readiness.md) (death section superseded by the 2026-09-28 ruling) |
| E | Starter Bag | `alpha3StarterBag` | Plain stock Bag issuance; live E-ISSUE, E-NOBAG, E-DEATH and E-MURDERER cases | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Starter-Bag-Readiness.md) |
| F | Welcome and Backpack Ward compatibility | Existing theft-protection path; no new Alpha 3 flag | Welcome, marked Ward issuance, legacy trade/vendor and NPC buyback; 2026-09-28 Ward is newbied and kept on death, loose in backpack only (live E-NOBAG/E-DEATH/E-MURDERER) | Old-world unmarked-Ward population/location review remains |
| G | Starter combat gear and consumables | `alpha3StarterCombatGear` | Package selection/issuance and 41-type direct transfer matrix; now newbied and permanently bound (2026-09-28) | Ordinary-client use, lifecycle and economy cases remain |
| H | Starter craft materials and tools | `alpha3StarterCraftMaterials` | Eight package grants, selected stock recipes, conversion and NPC-family cases | Distinct remaining conversion/failure, persistence and output routes remain |
| I | Blacksmith Bulk Order Deeds | UOR stock-content paths; no separate shard flag | Owner-approved retention, UOR vendor acceptance and reward exclusions | Remaining reward classification and gold-economy ruling remain |
| J | UOR player skills and approved deviations | UOR era gates plus skill-specific paths | 58-ID inventory, initial deviation register and selected boundary fixes | Full cited matrix, reachable-path audit, owner skill-15 ruling and client evidence remain |
| K | Permanent outdoor Hot Zones | `hotZones` | Two island polygons, dungeon exclusion, focused policy cases and entry/exit client notices | Shore/water, boundary, combat, crime and restart matrix remain |
| L | Integrated Alpha 3 release and activation | `alpha3EnablementAcknowledged` plus approved feature flags | Accepted Alpha 2b world and prior focused checks | Final source/deployed review, grouped regression, rollback and explicit owner acknowledgment remain |

Phases A–K are feature-readiness passes. Phase L is the combined release gate, not another gameplay feature. Earlier evidence may close a case without another run when the relevant source and configuration are unchanged. A newly discovered shared-path change reopens only affected evidence.

## Todo

Status key: `[x]` accepted evidence on file; `[ ]` open; `[?]` owner ruling; `[!]` invariant; `[g]` final release gate. Checklist entries are distinct finish conditions, not percentages. `tools/Get-Alpha3WorkQueue.ps1` reads this plan.

### A. Skill Bank

- [x] Focused policy, organic/sub-10/non-organic gain, anti-macro, cap, Mastery ordering, staff recovery and ordinary-client save/reload cases are reconciled in [the Skill Bank rehearsal](Alpha-3-Skill-Bank-Persistence-Rehearsal.md).
- [x] Compare the accepted matrix with current Skill Bank/gain/configuration source, close any affected delta, and record whether its existing validation guard can be made conditional on the final Alpha 3 acknowledgment without activating the flag. Finish with a feature-readiness record; time-driven Mastery awards stay in J. See [Skill Bank readiness](Alpha-3-Skill-Bank-Readiness.md).

### B. Starting stats

- [x] The ordinary creation packet matrix covers Warrior, Mage, Blacksmith and Advanced, each with 120 total starting points and at least 30 in each stat; the 225 cap remains in force. See [starter audit](Alpha-3-Starter-Package-Audit.md).
- [x] Map those accepted cases to current profession and creation-hook source, confirm no changed path reopens them, and record feature readiness with the source gate still off. See [starting stats readiness](Alpha-3-Starting-Stats-Readiness.md).

### C. Starter gold

- [x] Existing disposable evidence covers the 500-gold account grant, same-account second character, deletion/recreation after saved account state, removal of stock repeatable gold, and an ordinary-client first grant. See [starter audit](Alpha-3-Starter-Package-Audit.md).
- [x] Review current entitlement, stock-grant and save code against those cases; close any changed path and record feature readiness with the source gate still off. See [starter gold readiness](Alpha-3-Starter-Gold-Readiness.md).

### D. Starter scissors

- [x] The disposable issuance/loss probe and bound-item policy matrix cover one marked pair, removal of stock pairs, persistence of the no-regrant tag and permanent sale/transfer restrictions. See [starter audit](Alpha-3-Starter-Package-Audit.md).
- [x] Use an ordinary Healing-selected creation to check duplicate stock scissors removal; verify owner movement and paired trade/vendor refusal at the actual item callbacks and no regrant after destruction. See [starter scissors readiness](Alpha-3-Starter-Scissors-Readiness.md). The four-hour death boundary was superseded by the 2026-09-28 newbied ruling; the pair's bag refusal and murderer-death retention were re-verified live under Phase E.

### E. Starter Bag

- [x] Creation, issuance guard and save/restart were checked in disposable probes and one normal client creation. See [starter audit](Alpha-3-Starter-Package-Audit.md).
- [x] Owner ruling 2026-09-28: the bag is a plain stock `Bag` (the bound `StarterBag` and its trade/vendor/corpse cases no longer exist). Starter-issued items are newbied, bound, loose in the backpack only and kept through every death. Ordinary newbied items stay protected inside bags except for murderers. Live disposable cases E-ISSUE, E-NOBAG, E-DEATH and E-MURDERER passed. See [Starter Bag readiness](Alpha-3-Starter-Bag-Readiness.md).

### F. Welcome and Backpack Ward compatibility

- [x] Ordinary-client Welcome and marked-Ward issuance and marker persistence pass. The earlier unused-Ward death deletion was replaced on 2026-09-28: the marked Ward is newbied and kept through death, loose in the backpack only (live under Phase E); existing marked Wards become newbied on load. Unmarked legacy Wards passed paired trade/player-vendor intake, NPC sale/same-serial repurchase and a disposable save/restart no-op. See [starter audit](Alpha-3-Starter-Package-Audit.md).
- [ ] Classify the remaining pre-marker Ward population and locations in the accepted old world, confirm no migration retroactively marks or deletes ordinary Wards, and record the compatibility result. Starter restriction labels remain a Beta 1 text task.

### G. Starter combat gear and consumables

- [x] Package planner and synthetic issuance cover melee, archer and mage stock overlap; the 41-type direct bound-transfer matrix covers the emitted item set. See [starter audit](Alpha-3-Starter-Package-Audit.md).
- [ ] Complete ordinary-client archetype creation and weapon, ammunition, spell/reagent and bandage use; check duplicate/loss handling, output and BOD/conversion paths that differ from the shared transfer policy, save/restart, and the 2026-09-28 death rule (newbied, bound, kept through every death) for gear and consumables.
- [ ] Reconcile each distinct NPC/player-vendor, salvage and crafting entry point with existing 41-type policy evidence and representative live transactions; list any genuinely untested hook before adding another item example. Record readiness without lifting the validation guard prematurely.

### H. Starter craft materials and tools

- [x] The eight selected craft packages, bound tools, representative stock recipes and ordinary output controls have issuance, automated or live evidence in [the starter audit](Alpha-3-Starter-Package-Audit.md). Direct scissors, Salvage Bag, Blacksmith, Tinker and Tailor NPC routes have representative live cases.
- [ ] Inventory distinct conversion and consumption entry points for the eight material/tool families, map accepted cases to shared code, then close only uncovered routes: Tinkering/tool transformations, category-specific failure/partial-consumption paths, remaining output economy hooks and bound material/tool save-restart states. Include same-account character recreation and no repeat material entitlement.
- [ ] Confirm ordinary crafted outputs stay unrestricted while bound inputs and equipment cannot be laundered through sale, resale, BOD combine, salvage, commodity or nested-container paths. Record a finite case map and feature readiness before changing the validation guard.

### I. Blacksmith Bulk Order Deeds

- [x] The owner retained Smith BODs as a documented UOR deviation, excluded runic hammers, and current source also excludes four Publish 16 rewards. Focused vendor/reward cases and ordinary-client Smith issue/acceptance pass; Tailor/Weaver BODs remain AoS gated. See [player-skill audit](Alpha-3-Player-Skill-Audit.md).
- [ ] Classify each remaining Smith reward and craft consequence against the April 2000 baseline or an explicit approved deviation. Reconcile the maximum 222,222-gold deed payment with the accepted shard economy; obtain an owner ruling for any historically uncertain reward or material economy change before marking this feature ready.

### J. UOR player skills and approved deviations

- [x] The [player-skill audit](Alpha-3-Player-Skill-Audit.md) inventories all 58 exposed IDs, seeds the deviation register, and records selected UOR entry-gate, Arms Lore, delay, item-bonus, Poisoning and later-skill fixes.
- [ ] Complete cited historical contract and current entry-point trace for every exposed skill, in combat/magic, bard/animal, stealth/crime, craft/harvest, medical/utility and nine later-era skill families. Every row needs effective shard behavior, gate, gain/cap/anti-macro interaction and proportionate automated/client evidence. Preserve every approved custom system.
- [ ] Close named known gaps, including old poisoned-weapon load/save and normal-client behavior, reachable later-era item/spell/special paths, remaining stock defaults and cross-skill effects; publish a reviewed matrix and discrepancy log with no unexplained result.
- [?] Owner ruling required for skill ID 15: the April 2000 baseline is Enticement; Discordance replaced it in Publish 16. The recommendation on file is Discordance as an explicit shard deviation. Do not infer this choice from the runtime skill name.

### K. Permanent outdoor Hot Zones

- [x] Source polygons for Fire Island and Buccaneer's Den cover their connected land components, exclude dungeons, and passed focused membership/hostility checks; a disposable client saw island entry/exit and Hythloth-interior exclusion notices. See [Hot Zone survey](Alpha-3-Outdoor-Hot-Zone-Survey.md).
- [ ] Compare runtime-loaded map/tile data with surveyed hashes, then check both islands' shorelines, docks, nearshore water and extraction/teleport edges with ordinary clients. Name and close the exact safe-to-Hot and Hot-to-safe transition cases.
- [ ] Complete same-region/cross-boundary direct and delayed combat, movement/carryover, login/save/restart, theft and Ward effects, corpse loot, Knocked Out and Execute cases. Confirm ordinary outdoor spawn cadence/rewards and no dungeon Hot/Cool activation or new surface premium.

### L. Integrated Alpha 3 release and activation

- [?] Owner rulings required on the custom F–K rules in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md) before each letter starts. The two bugs it lists (G-5 arrows, H-2 second-character materials) are fixed within G and H regardless of rulings.
- [?] Owner rulings required on the post-UOR stock defaults in [Alpha-3-Stock-Default-Audit.md](Alpha-3-Stock-Default-Audit.md): passive Detect Hidden, virtues (Honor damage, Sacrifice self-resurrection), one house per account, mount stamina, insta-hit confirmation, and the insurance flag check gap.
- [?] Owner ruling required: ModernUO's Young player system (`ContentFeatureFlags.YoungPlayerSystem`, on by default) is active on the dev world. For each new account's first 40 logged-in hours it keeps every item through death and teleports the ghost to a healer. Design doc §16 rejects account-age immunity, and Young likely postdates the April 2000 UOR baseline. Decide whether to disable it before activation.
- [!] Keep house zoning and all Hot/Cool dungeon rules, including Hythloth, in Beta 2; keep Beta 1 starter restriction labels and living-world systems in Beta 1. Maintain the accepted Alpha 2b world and disabled source Alpha 3 gates during feature preparation.
- [g] Review the readiness record for every A–K feature and rerun only evidence affected by intervening source/configuration changes. Complete the grouped current-source, ordinary-client, persistence and regression release pass.
- [g] Verify pinned and deployed assemblies/configuration, disabled dungeon/housing behavior, accepted-world save lineage, single-writer safety, recovery/rollback and no accidental shared-world mutation.
- [g] Present the exact proposed flag set and effective behavior for owner acknowledgment. Change `alpha3EnablementAcknowledged` and feature flags only after that explicit decision and after their own validation guards and route checks permit activation; reconcile every roadmap exit criterion before declaring Alpha 3 complete.

## Phase boundaries

House zoning, residential districts and all dungeon Hot/Cool systems are Beta 2. Expeditions, cargo, Pilgrimage, road speed and starter restriction labels are Beta 1. Existing preparatory housing hooks, survey results and three approved east-Britain spawner relocations are preserved as background work; `housingGeography` and `coolZones` remain false. No new outdoor PvE multiplier is part of Alpha 3.
