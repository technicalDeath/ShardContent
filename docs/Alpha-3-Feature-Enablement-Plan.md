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
| F | Welcome and Backpack Ward compatibility | Existing theft-protection path; no new Alpha 3 flag | Welcome, marked Ward issuance, legacy trade/vendor and NPC buyback; 2026-09-28 Ward is newbied and kept on death, loose in backpack only (live E-NOBAG/E-DEATH/E-MURDERER) | Deferred to Beta 1 (owner decision, 2026-09-28); the accepted Welcome/Ward evidence above stands, only the remaining old-world review moved out of Alpha 3 |
| G | Starter combat gear and consumables | `alpha3StarterCombatGear` | Owner ruling 2026-09-28: newbied only (not bound), five narrow stock top-ups/patches; G-5 bug fixed; ordinary-client, vendor-sale-guard and death cases verified | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Starter-Combat-Readiness.md) |
| H | Starter craft materials and tools | `alpha3StarterCraftMaterials` | Owner ruling 2026-09-28: newbied only (not bound), stock top-ups/patches for all 8 categories; H-2 bug fixed; ordinary-client and persistence cases verified | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Starter-Craft-Readiness.md) |
| I | Blacksmith Bulk Order Deeds | UOR stock-content paths; no separate shard flag | Owner-approved retention, UOR vendor acceptance and reward exclusions; owner rulings 2026-09-28 closed the remaining reward classification, gold cap and Weaponsmith-issuance items | Ready for Alpha 3 enablement; see [readiness record](Alpha-3-Blacksmith-BOD-Readiness.md) |
| J | UOR player skills and approved deviations | UOR era gates plus skill-specific paths | 58-ID inventory, initial deviation register and selected boundary fixes; skill-15 ruling and the 9 later-era skills' item-acquisition gaps closed 2026-09-28 | Ready for enablement (source-survey basis, 2026-09-28; see [pre-AoS record](Alpha-3-UOR-Pre-AoS-Skills-Readiness.md)); live-client evidence waived by the owner |
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
- Deferred to Beta 1 (owner decision, 2026-09-28): classifying the remaining pre-marker Ward population and locations in the accepted old world, and confirming no migration retroactively marks or deletes ordinary Wards, moves out of Alpha 3 scope. See [Phase boundaries](#phase-boundaries). Starter restriction labels remain a Beta 1 text task.

### G. Starter combat gear and consumables

- [x] Owner rulings 2026-09-28 (Contract-Review.md G-1 through G-9; design doc §16.1 updated to match): the custom package-selection/replacement system and all ~20 bound gear/consumable types are gone. Stock character-creation grants run as-is (already newbied under this shard's UOR era with zero shard code); two quantities are raised (arrows, reagents) and three stock gaps are patched narrowly (archer leather armor, Parry shield, bandage fallback). Combat gear/consumables are newbied only, not bound; a Newbied item is now also blocked from vendor sale (alongside Nontransferable) so the resale faucet stays closed without reintroducing binding. The mage Spellbook stays stock Blessed (owner ruling) and is a named, accepted vendor-sale exception.
- [x] G-5 bug fixed: the arrow top-up is unconditional on "was Archery selected," never gated on which combat package is primary, so a secondary Archery pick can't lose its arrows. See [starter audit](Alpha-3-Starter-Package-Audit.md#owner-rulings-and-phase-g-closure--september-28-2026) and [readiness record](Alpha-3-Starter-Combat-Readiness.md).
- [x] Ordinary-client archetype creation (Warrior, Mage, Archer, Melee+Parry, two-weapon hybrid), weapon/ammunition/reagent/bandage grants, vendor-sale/trade/salvage guard behavior, and ordinary-death survival are verified (full Shard suite 255/255, UOContent guard tests 11/11, seven live createcharacter cases, one live death case). Named limits (no live murderer case for G's own items — reused Phase E's identical-code-path evidence instead; no live vendor-sale click-through — used UOContent.Tests engine-level proof instead) are recorded, not silently dropped. See [readiness record](Alpha-3-Starter-Combat-Readiness.md).

### H. Starter craft materials and tools

- [x] The eight selected craft packages, bound tools, representative stock recipes and ordinary output controls have issuance, automated or live evidence in [the starter audit](Alpha-3-Starter-Package-Audit.md). Direct scissors, Salvage Bag, Blacksmith, Tinker and Tailor NPC routes have representative live cases.
- [x] Owner rulings 2026-09-28 (Contract-Review.md H-1 through H-6, plus the Cooking call; design doc §16.1 updated to match): all ~25 bound material/reagent/tool types are gone. Stock character-creation grants run as-is (already newbied under this shard's UOR era with zero shard code); quantities are raised per the design doc's targets, and two stock gaps are patched (Tinker ingots, Tailor cloth/leather — stock's own grants for these either don't exist or can't be consumed as the needed resource). Craft materials/tools are newbied only, not bound; already covered by G's generic Newbied vendor-sale guard with no new guard code.
- [x] H-2 bug fixed: the redesign never deletes anything stock granted, so a second same-profession character on one account keeps its own ordinary stock allotment instead of losing it to a pre-entitlement-check deletion. See [starter audit](Alpha-3-Starter-Package-Audit.md#owner-rulings-and-phase-h-closure--september-28-2026) and [readiness record](Alpha-3-Starter-Craft-Readiness.md).
- [x] Ordinary-client creation for all 8 craft categories verified live in one disposable-host pass (full Shard suite 230/230, seven characters, server-side inventory inspection, save/restart persistence). Named limits (no live H-2 second-character repro; crafting-consumption evidence reused from the prior bound-subclass design rather than re-run) are recorded, not silently dropped. See [readiness record](Alpha-3-Starter-Craft-Readiness.md).

### I. Blacksmith Bulk Order Deeds

- [x] The owner retained Smith BODs as a documented UOR deviation, excluded runic hammers, and current source also excludes four Publish 16 rewards. Focused vendor/reward cases and ordinary-client Smith issue/acceptance pass; Tailor/Weaver BODs remain AoS gated. See [player-skill audit](Alpha-3-Player-Skill-Audit.md).
- [x] Owner rulings 2026-09-28 (Contract-Review.md I-1 through I-6): the five remaining unclassified reward types are kept in the pool (no UOR-rule violation found); the 222,222-gold maximum payout is accepted as-is (stock math, unmodified); the gold-only top reward tiers are kept as built, with a named Beta 3 follow-up to add a real reward there. A previously-unruled shard deviation was also found and reverted to match stock: Weaponsmith Smith-BOD issuance under UOR (identical deed/reward content to Blacksmith's) now requires `Core.AOS` again, same as Tailor/Weaver. See [player-skill audit](Alpha-3-Player-Skill-Audit.md#discrepancy-and-ruling-log) (SK-003) and [readiness record](Alpha-3-Blacksmith-BOD-Readiness.md).
- [x] Focused UOContent BOD/vendor tests (18/18) and the full Shard suite (230/230) pass against the reverted Weaponsmith gate. See [readiness record](Alpha-3-Blacksmith-BOD-Readiness.md).

### J. UOR player skills and approved deviations

- [x] The [player-skill audit](Alpha-3-Player-Skill-Audit.md) inventories all 58 exposed IDs, seeds the deviation register, and records selected UOR entry-gate, Arms Lore, delay, item-bonus, Poisoning and later-skill fixes.
- [x] Complete cited historical contract and current entry-point trace for every exposed skill, in combat/magic, bard/animal, stealth/crime, craft/harvest, medical/utility and nine later-era skill families. Every row needs effective shard behavior, gate, gain/cap/anti-macro interaction and proportionate automated/client evidence. Preserve every approved custom system. **Closed 2026-09-28 on a source-survey basis; the owner waived live and automated evidence for this pass.** Later-era IDs 49–57: [readiness record](Alpha-3-UOR-Later-Era-Skills-Readiness.md). Pre-AoS IDs 0–48: [readiness record](Alpha-3-UOR-Pre-AoS-Skills-Readiness.md), with no high-confidence unapproved era leak. Named limits: no live-client evidence, and the surveys are not exhaustive.
- [x] Close named known gaps, including old poisoned-weapon load/save and normal-client behavior, reachable later-era item/spell/special paths, remaining stock defaults and cross-skill effects; publish a reviewed matrix and discrepancy log with no unexplained result. **Closed 2026-09-28 (source-survey basis):** later-era item/spell/special paths fixed (Contract-Review.md J-9); stock defaults ruled (Stock-Default-Audit rows 10–16: keep stock except Felucca harvest, now single yield before AoS); the discrepancy log SK-001 to SK-013 has a state for every entry. Named limits carried to Beta/live play: old-version poisoned-weapon load fixture and normal-client poison behavior (SK-005), cross-skill effects not exercised, and the bard-difficulty ruling is provisional.
- [x] Owner ruling 2026-09-28: skill ID 15 is Discordance, as an explicit shard deviation from the April 2000 Enticement baseline. No code change was needed — the active implementation was already Discordance unconditionally. See [player-skill audit](Alpha-3-Player-Skill-Audit.md), ID 15 and SK-001.

### K. Permanent outdoor Hot Zones

- [x] Source polygons for Fire Island and Buccaneer's Den cover their connected land components, exclude dungeons, and passed focused membership/hostility checks; a disposable client saw island entry/exit and Hythloth-interior exclusion notices. See [Hot Zone survey](Alpha-3-Outdoor-Hot-Zone-Survey.md).
- [x] K1 geography and boundary pass (2026-09-29): map and tiledata hashes match the survey; a walkability check found and closed a Buccaneer's Den east-dock leak (polygon vertices moved); 18 live boundary cases pass on a disposable host, and a login-message defect (message sent before the client entered the world) was fixed with a 3-second login delay. Named limits: Recall/Gate Travel and boats (B7, B8) are source-verified only, death placement (B10) moves to K2/K3, house multis are Beta 2. The corrected polygon and login-delay DLL are not yet deployed to `ModernUO/Distribution`. See [Hot Zone survey](Alpha-3-Outdoor-Hot-Zone-Survey.md).
- [x] K2 combat and consequences pass (2026-09-29): same-region and cross-boundary combat, carryover and its 2-minute lapse (H1-H6), Knocked Out (KO1-KO3), Knocked Out loot (L1-L3), Execute (X1-X3), theft and Ward effects (T1-T4), corpse and exit-message observations (C1, B10) all pass live on a disposable host. Named limits: delayed damage (H8) is source-only, pets (H7) unit-only, stock Stealing refuses Newbied items and stock Snooping cannot open a Knocked Out victim's pack, so L3 asserts the authorization decision only. Owner rulings K-4, K-5 and K-7 remain open. See [Hot Zone survey](Alpha-3-Outdoor-Hot-Zone-Survey.md#k2-combat-and-consequence-pass-2026-09-29).
- [ ] K3: login/save/restart cases. Confirm ordinary outdoor spawn cadence/rewards and no dungeon Hot/Cool activation or new surface premium.

### L. Integrated Alpha 3 release and activation

- [?] Owner rulings required on the custom F–K rules in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md) before each letter starts. The two bugs it lists (G-5 arrows, H-2 second-character materials) are fixed within G and H regardless of rulings.
- [?] Owner rulings required on the post-UOR stock defaults in [Alpha-3-Stock-Default-Audit.md](Alpha-3-Stock-Default-Audit.md): passive Detect Hidden, virtues (Honor damage, Sacrifice self-resurrection), one house per account, mount stamina, insta-hit confirmation, and the insurance flag check gap.
- [x] Owner ruling 2026-09-28: ModernUO's Young player system is disabled shard-wide. It lived outside `shard-rules.json`, in ModernUO's own native feature-flag store (`ModernUO/Distribution/Configuration/FeatureFlags/flags.json`, key `young_player_system`, git-ignored runtime state rather than tracked config); set `Enabled: false` there. `PlayerMobile.Young`/`Account.Young` both gate on `ContentFeatureFlags.YoungPlayerSystem`, so this takes effect for every account immediately on next load, with no per-character migration needed and no account-age immunity remaining — matching design doc §16's rejection of account-age immunity. Live death tests no longer need `[set Young false` per test character.
- [!] Keep house zoning and all Hot/Cool dungeon rules, including Hythloth, in Beta 2; keep Beta 1 starter restriction labels and living-world systems in Beta 1. Maintain the accepted Alpha 2b world and disabled source Alpha 3 gates during feature preparation.
- [g] Review the readiness record for every A–K feature and rerun only evidence affected by intervening source/configuration changes. Complete the grouped current-source, ordinary-client, persistence and regression release pass.
- [g] Verify pinned and deployed assemblies/configuration, disabled dungeon/housing behavior, accepted-world save lineage, single-writer safety, recovery/rollback and no accidental shared-world mutation.
- [g] Present the exact proposed flag set and effective behavior for owner acknowledgment. Change `alpha3EnablementAcknowledged` and feature flags only after that explicit decision and after their own validation guards and route checks permit activation; reconcile every roadmap exit criterion before declaring Alpha 3 complete.

## Phase boundaries

House zoning, residential districts and all dungeon Hot/Cool systems are Beta 2. Expeditions, cargo, Pilgrimage, road speed and starter restriction labels are Beta 1. Existing preparatory housing hooks, survey results and three approved east-Britain spawner relocations are preserved as background work; `housingGeography` and `coolZones` remain false. No new outdoor PvE multiplier is part of Alpha 3.

Feature F's remaining old-world Backpack Ward population/location classification is deferred to Beta 1 (owner decision, 2026-09-28); the Welcome/Ward evidence already accepted for Alpha 3 (Phase E) is unaffected.
