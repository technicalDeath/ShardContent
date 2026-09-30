# ModernUO UOR Safe-World — Phased Implementation Roadmap

**Source design:** `ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md`  
**Status:** Planning baseline  
**Release sequence:** Alpha 1 → Alpha 2 → Alpha 2b → Alpha 3 → Beta 1 → Beta 2a → Beta 2b → Beta 2c → Beta 2d → Beta 3 → Beta 4

## Purpose

This roadmap turns the Safe-World / PvP Hot-Zones alternative plan into eleven coherent releases. It intentionally starts with the rules that every character, combat interaction and later system depends on, establishes a reproducible UOR/Felucca world population, then adds region rules and housing, then world-concentration systems, and only after that adds the larger retention and content feature sets.

The shard's guiding theme is **Felucca, without the griefing.** Felucca remains the only world, and crime remains part of ordinary play. Thieves may pick pockets and snoop across most of the map. Reds, criminals, full loot, loss and emergent encounters remain real. Protections should stop repeated, targeted behavior from ruining another player's play without removing the first theft, the risk, or the thief profession.

The continent has been overtaken, and **Greater Britain is the only city left standing**. It is the shard's surviving social, residential and commercial center. Rotating events should lead players out from Greater Britain along the old roads to explore the fallen continent, then draw survivors, resources and stories back into the city. Other classic locations may remain as wilderness destinations, ruins, outposts or contested ground, but they must not be presented as peer cities that dilute Greater Britain's role.

The sequence is a dependency order, not a promise to enable every feature immediately on a production shard. Each release must be tested on a clean test world, survive save/restart, and have a documented rollback or feature-flag disable path before the next release begins.

## Shared delivery rules

- Pin and record the ModernUO commit before Alpha 1. Keep upstream changes isolated from shard-specific code and configuration.
- Put shard policy in a typed shard configuration layer (target: `Distribution/Configuration/shard-rules.json`), not scattered constants or imagined stock JSON keys.
- Prefer narrow adapters at proven ModernUO extension points. Do not rewrite upstream combat, loot-rights, housing, fishing, or region systems without source evidence and regression coverage.
- Keep production-facing features behind flags until their region, persistence, economy and exploit tests pass.
- After every milestone: compile, run focused automated tests, launch the shard, inspect logs, exercise the affected rules with real clients, and verify a save/restart cycle.
- Preserve the fixed power ceiling: UOR platform, Felucca-only world, pre-AoS itemization, 700 skill / 225 stat caps, no insurance, no mandatory vertical-progression treadmill, and no hidden post-UOR systems.
- Test every safety rule against both halves of the theme. It must limit sustained harassment or disproportionate denial of play while preserving ordinary Felucca crime and unscripted interaction. Safe-World must never become a second facet or a general prohibition on stealing and snooping.
- Preserve pre-AoS UO's loose skill-build identity. Do not design or describe PvE around formal party composition, tanks, healers, damage roles or required group roles. Players may cooperate informally, but the rules should not assume a modern party structure.

## Alpha 1 — Era-correct playable core

### Goal

Make the shard launch as a stable, recognizably pre-AoS UOR-era world with the intended hybrid combat contract, character progression and classic economy foundations. At the end of this alpha, a player can create a character, progress, fight monsters, travel, die, recover, craft and trade under the correct baseline rules and controlled test fixtures—but no custom Safe-World, production-scale world population or rotation system is active yet.

### Scope

1. Establish the engineering baseline.
   - Record the pinned ModernUO version/commit and build configuration.
   - Produce a clean build/startup baseline and inventory current warnings, feature flags, maps and extension points.
   - Create the shard configuration model, typed bindings, validation and staff-readable diagnostics.
2. Apply the era and world gates.
   - Set UOR as the global expansion baseline and make Felucca, including the Lost Lands, the only accessible map.
   - Audit and disable post-UOR mechanics, content paths and later-era itemization rather than relying on assumptions about configuration names.
   - Audit insurance, veteran skill-cap rewards, bonding and other cross-era branches against the pinned source.
3. Lock the combat baseline.
   - Enable and prove T2A-style instant-hit behavior and classic precasting using the real ModernUO control points.
   - Remove confirmed original weapon automatic procs and UOR Wrestling Stun/Disarm at both request and resolution points.
   - Preserve ordinary pre-AoS weapon, poison, mace, shield and archery identities. Keep optional numerical buffs disabled until comparative testing justifies them.
4. Establish character, death and economic foundations.
   - Enforce 700 total skill, 100 individual skill and 225 stat caps.
   - Implement and test the accelerated-but-capped skill-gain curve.
   - Replace the existing 95.0+ fixed-UTC Mastery implementation with one durable 18-hour cycle per
     character. Give each 95+ skill a configurable Easy/Standard/Hard/VeryHard allowance
     (launch values 1.0/0.5/0.3/0.2), grant deterministic +0.1 on every otherwise gain-eligible use
     while allowance remains, and bank no more than three cycles of that skill's allowance.
   - Migrate or deliberately clear the pre-release fixed-period/pending-increment state; this
     workspace has no live shard population, so do not preserve obsolete Alpha 1 timing semantics.
   - Validate pre-AoS death, corpse, loot, blessed runebook, stealable-key/property and travel behavior.
   - Validate ordinary crafting, BODs, player trade, vendors, boats, and the no-pets-in-dungeons policy, whose only exception is an animal while it is being ridden, plus the restricted pet-PvP policy.
   - Implement the starter package and one-time account/character issuance controls without economic extraction loopholes.

### Exit criteria

- Clean build and repeatable startup from a clean test save.
- Automated and manual tests prove expansion/map gating, caps, insta-hit, precast timing, special-attack removal, swing behavior, 95+ Mastery cycle anchoring, difficulty allowances, deterministic eligible-use gains, three-cycle banking, death/loot, key recovery, starter issuance and save/restart persistence.
- A client can complete the basic loop—create, train, fight, loot, die, bank, travel, craft and trade—without accessing disabled era content.
- The configuration layer exposes only verified shard controls and produces understandable startup validation errors.

### Explicitly deferred

Safe-World hostility, murder replacement, theft wards, production-scale world population, Hot/Cool zones, housing geography, Expedition systems, Pilgrimage, road speed, and all custom retention content.

---

## Alpha 2 — Safe-world law, crime and consent

### Goal

Make the shard's defining social contract correct: Felucca, without the griefing. Ordinary blue players are protected from unsolicited direct attacks outside Hot Zones, but theft and snooping remain legal game systems across most of the world. Thieves can pick pockets; narrow protections prevent one thief from repeatedly denying another player the ability to play. Criminals, greys, reds, lawful retaliation, full loot and voluntary PvP remain intact. This is the first phase in which the custom world identity is enabled.

**Current local status (2026-09-24): Alpha 2 enablement is complete.** This workspace has no live
shard and no legacy character population requiring migration. All four Alpha 2 gates are enabled in
the local baseline; Hot-Zone activation remains deferred to Alpha 3.

### Scope

1. Implement a central player-hostility decision service.
   - Route direct player hostility through a single auditable authority that considers region, blue/grey/red state, `[Intent]`, guild-war exceptions and inherited lawful encounter rights.
   - Block ordinary-blue versus ordinary-blue initiation outside Hot Zones.
   - Preserve attacks on criminals and murderers everywhere, direct-target retaliation rights, approved guild conflict and independent pet restrictions.
   - Current implementation status: `PvpIntentService` is the single stock-boundary decision point and resolves controlled-creature hostility to the player master before applying the same consent/retaliation policy. Its notoriety and harmful-action delegates are rebound after stock startup, and a staged two-account matrix proves ordinary-blue refusal plus opted-in attack acceptance. The local profile enables SafeWorld, automatic murder adjudication, TheftProtection, and Knocked Out after the geography and disposable live-test gates.
2. Implement **Criminal Intent** as a stored, blue-only voluntary PvP preference. The current compatibility command is `[Intent]` and the implementation remains `PvpIntentService`.
   - Make Criminal Intent opt-in, visible, persistent and independently reversible for new opponents. Enabling it makes the blue player appear grey and attackable outside Hot Zones; killing that player does not create a murder count.
   - Preserve existing encounter rights when it is turned off; prohibit turning it off while genuinely criminal or red.
   - Ensure intent-only grey status remains attackable without being confused with genuine criminality.
3. Replace murder adjudication with the approved automatic model.
   - Create a separate kill/murder adjudicator and historical ledger.
   - Award at most one automatic count for each qualifying ordinary-blue death and add 24 hours to a cumulative UTC red timer.
   - Ensure Hot-Zone location, lawful self-defense and guild-war status do not waive the ordinary-blue murder consequence unless the death was actually intent-classified.
   - Disable conflicting stock reporting, threshold and decay behavior before enabling any reward system.
   - Current implementation status: `MurderAdjudicationService` contains the tested policy, account-tag ledger, persisted encounter snapshots, and feature-gated `PlayerDeathEvent` hook behind `featureFlags.automaticMurderAdjudication`; duplicate death callbacks are deduplicated by a UTC marker owned by the victim account (with a one-time legacy-killer-account fallback), so attribution changes cannot create a second count. The ModernUO fork exposes the narrow legacy-reporting disable, legacy-red suppression, and additional-red-status hooks. The read-only migration audit found no legacy or custom records, and this workspace has no live shard or legacy character population requiring migration. The local Alpha 2 flag is enabled; future imported-world migration remains a separate optional audit.
4. Preserve crime while adding narrowly targeted anti-harassment protections.
   - Keep ordinary stealing and snooping intact by default across most towns, roads, wilderness and dungeons. A thief must still be able to pick a pocket. Protections should limit repetition and sustained disruption, not eliminate the profession or make theft opt-in.
   - Add explicit bank theft-protection polygons and Cool-Dungeon-compatible theft checks that do not create combat-safe bank bubbles.
   - Add consumable Backpack Wards, mechanics defined in [BACKPACK-WARD-DESIGN.md](BACKPACK-WARD-DESIGN.md) (the sole source of truth for this feature, not redefined here).
   - Add the invisible Loot Protection Ward: permit the first unlawful non-Hot monster-corpse transfer, then block only repeated unlawful looting by that offender account against the protected victim’s still-rights-protected monster corpses for ten minutes.
   - Current implementation status: the feature-gated `BackpackWard` and stock Stealing/Corpse pre/post hooks implement deterministic physical-Ward selection, per-thief-account 25%/50%/100% escalation, first-transfer/ten-minute-repeat protection for unlawful non-Hot monster corpses, a permanent invisible Loot Protection entitlement with idempotent bounded world-load migration plus login/creation fallback, character-creation starter issuance with durable account binding, and data-driven bank/Cool polygon checks at the theft boundary. The pinned engine now observes ordinary drag/lift corpse transfers as well as context-menu use and exposes the monster-corpse rights snapshot; markers are keyed by rights-holder character and offender account so separate corpses from the same victim cannot bypass the ward. The 87/87 content suite covers the corpse-repeat policy matrix. The runtime geometry contains 18 compact bank envelopes with a 5–6 tile apron and the ten UOR-era dungeon rectangles. Movement transitions explain the active theft rules to players; snooping and combat remain untouched. The review export tools remain the reproducible source evidence for future map revisions.
   - Implementation note: the deployed `BackpackWard` code still uses the superseded post-resolution-consumption/120-second-victim-immunity model. It has not yet been updated to the Primed/Activated state machine in [BACKPACK-WARD-DESIGN.md](BACKPACK-WARD-DESIGN.md), which is the current approved design.
   - Phase boundary correction: the configured Cool Dungeon polygons are dormant while `coolZones` is false. Bank protection, Backpack Wards and monster-corpse Loot Protection remain Alpha 2 behavior; Cool Dungeon theft immunity and its entry/exit messages begin in Beta 3.
5. Implement the Knocked Out state and safe-world resolution path.
   - Make qualifying zero-health outcomes for genuinely blue players enter a durable, untargetable, damage-immune 90-second Knocked Out state rather than death; clear effects and active aggression while retaining an immutable completed-encounter record.
   - Permit no-skill Knocked-Out looting only to the criminal/red who held recorded target-specific engagement rights at the moment of Knock Out; retain all item-binding and Ward rules.
   - Make safe-world Execution an explicit, encounter-authorized action that applies the same automatic ordinary-blue murder count and cumulative red time as a normal player kill.
    - Current implementation status: the feature-gated `KnockedOutService`, narrow ModernUO lethal-damage/damageability/targetability/recovery hooks, and stock Stealing no-skill boundary persist a 90-second ordinary-blue state only for attributable player damage with an active target-specific encounter, clear combat/status effects and targets, reject further damage/heal/cure/target actions, wake at half health after expiry or offline login reconciliation, retain a completed-encounter record, resolve controlled-creature damage to its player master, permit only the recorded criminal/red engagement holder to loot backpack items, and expose encounter-authorized `[Execute` with automatic murder adjudication. Its recovery guard is rebound at `ServerStarted` after stock Notoriety initialization so beneficial checks cannot silently bypass Knocked Out restrictions. The explicit Execute target cursor is the narrow exception to the otherwise global Knocked Out untargetable guard. For ordinary players, the engine action gate denies gameplay mutations including movement, combat, item use/lifting/dropping, world-item interaction, spellcasting, special moves, skill use, travel, normal speech and speech-triggered pet/guard commands, trade, crafting, and loot; emotes, party chat, party membership management, and explicitly marked read-only gump responses remain allowed. Gameplay-mutating command packets, gump responses, target callbacks, and party loot-permission changes remain blocked. Staff characters are fully exempt from Knocked Out restrictions and are excluded from entering or retaining the state. Logout and reconnect remain allowed, with the absolute expiry persisted and reconciled on login; staff retain `[KnockedOutRecover` for immediate revival of ordinary players. Real-client staging rehearsals prove hostile-swing denial, self-heal and self-cure target rejection while Knocked Out, staff and natural recovery, reagent-equipped post-recovery cure, and save/restart/reconnect persistence of an active KO. The engine `Corpse.OnItemLifted` observer, monster-rights snapshot, read-only gump gate, and 97/97 ShardContent suite cover the corpse-repeat policy predicates and staff-bypass policy; the live first-transfer/repeat-transfer and separate-corpse matrix is complete. The local Alpha 2 flag is enabled and the isolated release bundle has been deployed and booted successfully; Hot-Zone resolution remains deferred to Alpha 3. Optional high-contention concurrency and formal dispute-recovery rehearsal remain hardening follow-ups, not Alpha 2 enablement blockers.
6. Add the observability needed to support the rules.
   - Log hostility decisions, encounter classification, murder adjudication, theft/Ward activity and corpse-transfer enforcement with stable character/account identifiers.
   - Provide staff inspection and recovery tools before public enablement.
    - Current implementation status: `ShardAuditLog` records stable subject/other serial and account identifiers for Intent toggles, encounter classification, denied hostility, murder adjudication, Backpack Ward/corpse enforcement, and Knocked Out transitions; `[IntentStatus`, `[MurderStatus`, `[MurderMigrationAudit`, `[TheftStatus`, `[KnockedOutStatus`, `[KnockedOutRecover`, and `[ShardRulesStatus` provide staff/player inspection and recovery. Intent lifecycle, two-account hostility, the core two-account Knocked Out → `[Execute` → automatic-murder-count rehearsal, ordinary-blue no-consent refusal, no-record execution denial, and outsider execution-rights denial are complete on disposable staging. Fresh real-client rehearsals also prove Knocked Out hostile-swing denial, self-heal/self-cure rejection, staff/natural recovery, reagent-equipped cure after recovery, and save/restart/reconnect persistence. The startup lifecycle audit covers the stock `AllowBeneficialHandler` overwrite: the `ServerStarted` callback rebinds the Knocked Out recovery guard after stock initialization while retaining the stock delegate for ordinary checks. Theft geography, live boundary messaging, completed entitlement migration, Backpack Ward denial, the engine lift observer, and the automated corpse-repeat policy matrix have been exercised or proven with fresh Navrey/isolated tests; the Ward constructor is marked `[Constructible]` for controlled staging and staff repair workflows. A fresh live staging run now also proves first unlawful corpse transfer, repeat denial, and a separate-corpse transfer for the same rights holder. Alpha 2 local enablement is complete and the isolated release bundle boots with all four gates enabled; optional high-contention concurrency and formal dispute-recovery rehearsals remain hardening follow-ups, while Hot-Zone activation is deferred to Alpha 3.

### Exit criteria

- The complete safe, Intent, criminal, murderer, guild-war, retaliation, Knocked Out and Hot-context matrices pass in automated and real-client testing.
- Stealing and snooping remain functional where allowed; banks, Wards and corpse protections restrict only the specified actions and identities.
- Representative allowed-theft tests prove that stealing still succeeds outside the explicit bank and Cool-Dungeon polygons. Denial tests alone are not sufficient evidence for release.
- Multiple-account and concurrency tests prove one count per death, no duplicate Ward/corpse state, correct offline red-timer expiry and save/restart survival.
- Staff can explain a disputed PvP, theft or corpse decision from logs and diagnostic commands.

### Explicitly deferred

Production world population, permanent outdoor Hot-Zone activation, housing placement policy, weekly activity systems, and feature content remain deferred beyond Alpha 2. Hot/Cool dungeon designation, Cool Dungeon theft immunity, weekly rotations and their reward premiums remain dormant until Beta 2a (Hythloth), Beta 2b (rotating Hot Dungeon) and Beta 3 (Cool Dungeon). The code may recognize dormant region data, but it must not enforce a dungeon rule before that phase.

---

## Alpha 2b — Era-safe initial world population

### Goal

Turn the Felucca map into a reproducible, playable UOR world without importing inactive facets, post-UOR content, duplicate infrastructure or a stock layout that contradicts Greater Britain’s role as the only surviving city. World generation is a controlled content deployment: its inputs, exclusions, order, counts, save provenance and rollback point must be reviewable and repeatable.

ModernUO’s Admin → World Building → **Do everything** action is not approved for this shard. The stock actions are convenience generators, not a UOR/Felucca migration plan: several write to every facet, the spawner action imports the entire Felucca tree including later-era locations, and some actions replace or overlap existing world objects.

**Current local implementation and execution status (2026-09-26):** complete and accepted; see `Alpha-2b-Release-Evidence.md` and `Alpha-2b-World-Generation-Runbook.md`. The door-corrected rebuild archived the former accepted save intact at `ModernUO/Distribution/WorldStateArchive/alpha2b-door-rebuild-2026-09-26-20-55-00`. Only the existing owner-account index was carried into the fresh save so the generation command could be authenticated; no prior items, mobiles, guilds or other world objects were restored. `data/world-generation/alpha2b/world-generation.json` is the reviewed source manifest, `tools/Prepare-Alpha2bWorldData.ps1` reads stock inputs from the pinned Git commit and combines them with shard-owned sign exclusions, Britain vendor overrides, bounty-board data and the pinned door-generator source contract under `data/world-generation/alpha2b`. It builds alternate runtime inputs under `Distribution/Data/BritanniaRenaissance/Alpha2b`, so unrelated or uncommitted stock-file edits cannot silently change the generated baseline. Its schema-2 report hashes all 57 inputs and 55 outputs. Deployment prepares those inputs automatically without editing stock data. The owner-only `[Alpha2bWorldGen preview|apply CONFIRM-UOR-FELUCCA [rerun]|audit` command enforces the UOR/Felucca pin, refuses an unexpected non-empty world, canonicalizes overlapping stock records with last-definition-wins semantics, reports created/replaced/skipped/failed work by source and facet, audits inactive facets and required infrastructure, and saves only after the audit passes.

The accepted clean run produced 13,970 decorations, 1,345 exact town/shop door placements (1,215 created and 130 preserved decoration doors), 385 canonical generic teleporter placements, 1,546 canonical spawners, 410 Felucca signs, nine public moongates and 63 Khaldun dynamic items. All 327 double-door pairs are linked. The initial validation pass correctly caught four effective teleporter overlaps and 122 superseded spawner records before any generated state was saved. Instrumented restart testing also repaired seven non-serialized or graphic-normalizing `_orccave.cfg` decorations. Both the immediate second rerun and the first rerun after shutdown/restart created zero decorations and zero doors, removed zero duplicates, retained all 63 Khaldun objects, passed the exact audit and saved. The final audit additionally proves all 64 town/service spawners selected from `Vendors.json` and `TownsPeople.json` remain inside Greater Britain, with zero outside. Real-client checks crossed generated doors at Britain's Lord's Clothiers and Minoc bank in addition to the earlier dungeon-door, travel, spawn, sign, moongate and death/recovery coverage. The generated authoritative save survived repeated save, shutdown, restart and reconnect cycles.

### Scope

1. Establish a safe operating baseline before any world mutation.
   - Pin and record the exact ModernUO and ShardContent revisions, runtime configuration, source save, client-data version and hashes of every selected generator input.
   - Prove that exactly one authoritative server instance can touch the selected save. Check both the configured listener and running processes with `ModernUO.dll`, `Server.dll` or `Assemblies/UOContent.dll` loaded; a listenerless orphan can still autosave and overwrite a successful generation.
   - Inventory the selected save before changing it: item/mobile counts by type and facet, spawners, doors, teleporters, public moongates, signs and any existing generated-system controllers. Treat an inherited save as partially populated until the inventory proves otherwise.
   - Make a named, immutable pre-generation backup and first rehearse the complete plan against a disposable copy. Record the recovery procedure and never rely on an in-process save alone as rollback.
2. Build a shard-owned world-population manifest and runner.
   - Store the reviewed source manifest with ShardContent and deploy it as an explicit build/runtime input. It must name every selected data file, target facet, expected era, operation order and intentional exclusion; directory wildcards and implicit “all maps” behavior are prohibited.
   - Add preview/dry-run output where practical. Every operation must report created, replaced, skipped and failed objects by facet and source file, plus a final manifest version and input hashes.
   - Make reruns convergent. Exact-object replacement must be intentional, duplicate detection must cover overlaps between decoration and specialized generators, and a second run over the same save must not continually grow world-object counts.
   - Keep generated runtime saves and deployment copies out of the source-of-truth role. Changes to stock data such as `signs.cfg`, decoration files, teleporter data or spawner JSON must be reviewed and versioned in their owning repository before deployment.
   - Current implementation: the source manifest, sign exclusion, Britain vendor overrides, Britain bounty-board supplement and Felucca-only door scan contract live under `data/world-generation/alpha2b`; the preparation tool reads stock files from the pinned commit, copies and filters them into the shard-specific runtime namespace and writes `generation-report.json` with candidate and canonical counts. The runtime command validates every generated sign, door, teleporter and spawner before mutation. Use `preview` first, the exact confirmation token for the clean apply, `audit` after load, and the additional `rerun` argument only for a controlled convergence rehearsal. Follow `Alpha-2b-World-Generation-Runbook.md` for the full reset, generation, restart and acceptance sequence.
3. Populate the world in a deliberate, rehearsed order.
   - **Decorations:** apply only the reviewed Felucca result from the shared Britannia and Felucca decoration sets, plus Felucca bounty boards only while the configured bounty system remains approved. Do not call the stock `Decorate` command unchanged: it also targets Trammel, Ilshenar, Malas and Tokuno. Curate functioning shops, civic fixtures and settlement dressing so fallen towns read as ruins, outposts or contested ground rather than peer cities to Greater Britain.
   - **Doors:** run the shard-owned Felucca-only scan after decorations. It uses the pinned stock frame classifier and committed Britannia scan rectangles/exclusions, preserves intentional decoration door types within the stock Z tolerance, fills only genuine gaps, links double doors and requires exactly 1,345 placements with 327 linked pairs. Do not call stock `DoorGen`, which also writes inactive facets.
   - **Teleporters:** import only reviewed Felucca definitions from `Data/teleporters.json`. The stock `TelGen` spans six facets and replaces generic teleporters near configured endpoints, so the runner must facet-filter the input and report each replacement. Verify Lost Lands, dungeon entrances/exits and other required links from both directions.
   - **Public moongates:** run `MoonGen` only after confirming the active-map selection is Felucca-only. It deletes existing `PublicMoongate` objects before rebuilding them; the current configuration should produce the nine Felucca gates, which must be counted and client-tested after generation.
   - **Spawners:** import an explicit, file-level and, where necessary, entry-level UOR allowlist from `Data/Spawns/shared/felucca`. Never use the stock Felucca-folder button as the allowlist. Review towns, vendors, wilderness and every dungeon against the Greater Britain narrative and the era audit; explicitly exclude `BlightedGrove`, `PaintedCaves`, `PalaceOfParoxysmus`, `PrismOfLight`, `Sanctuary` and `SolenHive` unless a later approved design deliberately repurposes them. Account for the importer’s deletion/recreation and immediate-respawn behavior.
   - **Signs:** use the tracked `Distribution/Data/signs.cfg` as reviewed source data, but generate only the Felucca placements. The current file has 508 source records: 395 shared-Britannia records and 15 Felucca-only records yield the accepted 410 Felucca signs. Haven’s tailor, butcher, healer and blacksmith entries are Trammel-only and are deliberately excluded from this UOR/Felucca world rather than copied across facets. Recompute these figures whenever the pinned ModernUO data changes, audit localized and ordinary labels, and remove or rewrite signs that incorrectly present fallen settlements as active peer cities.
   - **Khaldun:** run `GenKhaldun` only if Khaldun is approved as launch-accessible UOR content. Count its puzzle/controller objects, test the encounter flow, and prove a rerun does not duplicate them.
   - After each stage, capture its report and inspect representative locations before continuing. Decorations precede specialized travel, spawner and sign passes so those later operations can provide the reviewed authoritative result where inputs overlap.
4. Make exclusions explicit instead of silently relying on configuration.
   - Do not run stock `DoorGen`. The required door-frame population is now an audited stage of the shard-owned Alpha 2b runner and is restricted to Felucca.
   - Do not generate Faction stones or monoliths. The stock action enables factions in configuration, while factions are deliberately disabled for initial launch.
   - Do not run `GenChamps`. It deletes all champion-spawn controllers before creating the stock Felucca set, and champion-style systems, artifacts and power-scroll progression require a separate owner decision.
   - Exclude Magincia regeneration, stealable artifacts, Samurai Empire teleporters, secret-location generation, Doom/Gauntlet content and other post-UOR generators.
   - Do not treat `GenBounds` as a world-population step. Item bounds are internal client-data preparation and are generated automatically only when the required bounds file is absent.
5. Validate the published world and its recovery path.
   - Complete a controlled save, wait for the save to finish publishing to disk, stop the sole server cleanly, restart from that save and repeat the inventory. No inactive-facet leakage, unexplained count drift or missing serialized objects is acceptable.
   - Test representative Greater Britain services, approved wilderness and dungeon spawns, vendors, doors, signs, public moongates, dungeon/region teleporters, Lost Lands travel, boats and player death/recovery with real clients.
   - Verify that excluded later-era creatures, items, regions, spawners and travel destinations are absent and that other classic towns do not function as equivalent social/commercial capitals.
   - Rehearse both an idempotent second run and restoration of the named pre-generation backup. Preserve reports, count deltas, known intentional replacements and owner approvals as release evidence.

### Exit criteria

- A versioned manifest can rebuild the approved Felucca/UOR population from the selected baseline without using **Do everything**, unrestricted facet loops or directory-wide spawner imports.
- The authoritative save has one documented lineage, one writer and a tested rollback; its post-generation state survives save, shutdown, restart and client reconnection.
- Decorations, teleporters, moongates, approved spawners, signs and any approved Khaldun content pass count, facet, era, duplication and representative client-play checks.
- A second identical run is convergent, produces no unexplained object growth and reports every intentional replacement or skip.
- Inactive facets and explicitly excluded post-UOR, Faction and champion content contain no newly generated objects, while Greater Britain remains the world’s only functioning peer-level city.

### Explicitly deferred

Faction activation, champion spawns and their reward progression, post-UOR locations and generators, and any unreviewed stock world-building input. Alpha 3 geography and housing work begins only after the populated baseline and its rollback are accepted.

---

## Alpha 3 — Geographic risk, progression and skill foundation

The [Alpha 3 feature enablement plan](Alpha-3-Feature-Enablement-Plan.md) is the active, lettered work order for preparing one feature at a time. This roadmap remains the phase scope and exit-criteria authority; its dated implementation-status notes are milestones rather than the current task queue. The former [implementation log](Alpha-3-Implementation-Log.md) is historical evidence.

### Goal

Apply permanent outdoor PvP geography and the remaining Alpha 3 systems to the accepted Alpha 2b world. House zoning—including residential districts, land classification, capacity and district expansion—is deferred to Beta 2b by owner decision. Dungeon Hot/Cool rules begin later: permanent Hythloth in Beta 2a, the rotating Hot Dungeon in Beta 2b and the Cool Dungeon in Beta 3.

For Alpha 3, UOR is the default historical baseline, not a mandate to roll back intentional Britannia Renaissance behavior. A documented, owner-approved shard rule or already-delivered custom system takes precedence over stock UOR behavior; otherwise, the UOR-era result is authoritative. The phase must preserve those approved deviations while rejecting accidental or inherited later-era behavior.

### Scope

1. Deliver the permanent high-risk outdoor geography.
   - Define Fire Island and Buccaneer’s Den island as permanent outdoor Hot regions. Keep dungeon interiors under ordinary rules until Beta 2a.
   - Implement authoritative region boundaries, entry/exit messaging, combat carryover, login placement and extraction behavior.
   - Apply the shared Knocked Out state in Hot Zones while changing its resolution: anyone may perform no-skill looting of a Knocked Out player's pack (a blue who does becomes criminal), only a criminal/red with damage-record rights on the victim may Execute (owner ruling K-4, 2026-09-29), and physical Backpack Wards have no effect on Hot-Zone theft or Knocked-Out looting.
   - Current implementation status: named source polygons now cover the two connected island landmasses with zero missed land tiles in the local map survey documented in `Alpha-3-Outdoor-Hot-Zone-Survey.md`. The policy excludes dungeon interiors. Hostility requires both players inside the same active outdoor Hot region and retains the stock targetability boundary; controlled pets do not gain Hot-only attack permission. Knocked Out classification, open criminal/red looting, any-player Execution and Ward/corpse-loot exceptions now use physical Hot membership instead of the global feature flag. `[HotZoneStatus` reports the configured regions and current membership. Settled-position notifications now provide entry/exit and Hot-zone login warnings for ordinary players, including the continued murder consequence. The Hot-Zone flag remains disabled while nearshore water, docks, map-data updates, boundary/extraction, login/restart and real-client combat/theft matrices remain unverified. Housing zoning is a separate Beta 2b deliverable.
   - The harmful-action policy now preserves stock safe-zone and duel denials before considering shard consent. Focused tests cover direct-player same-region initiation, cross-boundary refusal, controlled-pet refusal, stock denial and existing-aggression carryover; delayed spells, poison, fields, projectiles and live boundary movement still need end-to-end checks.
   - A disposable real-client session confirmed Fire Island and Buccaneer's Den entry warnings, exits to ordinary land and Hythloth's interior, and no Hot entry warning inside Hythloth. The validator permits this isolated test only with explicit Alpha 3 acknowledgment and both named polygons. Source activation remains off.
2. Keep house placement safe while district zoning remains dormant.
   - Existing stock one-house-per-account checks, foundation-wide geography hooks, placement quote/recheck paths and staff survey/status commands remain in the codebase behind the disabled housing gate. Do not open districts or continue residential/protected-land surveying in Alpha 3.
   - Owner decision: defer house zoning to Beta 2b. Greater Britain and Fire Island residential polygons, land classification, capacity estimates, protected/landmark/road/reserve polygons, district expansion order, household/IP exceptions, inactivity policy and zoning release checks move to Beta 2b.
   - Existing evidence is retained in `Alpha-3-Greater-Britain-Housing-Survey.md`: accepted-world placement/spawner rehearsals, approved east-Britain spawner relocations, resource exclusion fix, rural-premium quote/recheck implementation, and read-only diagnostics. The survey is background evidence only; its candidate lots and small-house lower bounds do not authorize zoning or placement.
3. Establish release-level operational tools.
   - Add permanent-region and housing inspection commands, audit reports and regression fixtures for boundary and placement cases.
4. Deliver the Skill Bank defined in `ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md`, Section 5.1.
   - Preserve only exact base-skill points organically displaced by ordinary skill-cap gains, in a per-character bank capped at 300.0 total points and the individual skill cap per entry. Temporary gameplay penalties and expiring bonuses never create bank credit.
   - Provide per-entry Locked/Down retention controls. At capacity, replace only Down bank entries, draining the largest balance first with alphabetical tie-breaking; if no Down balance is available, preserve existing bank contents and notify the player that the incoming loss was not banked.
   - Restore one banked 0.1 per valid gain-eligible skill use, subject to existing anti-macro and skill-use eligibility. Bank restoration precedes ordinary gains and Mastery, including restoration of previously earned value through 100.0.
   - Preserve the 700.0 active cap with atomic exchanges that bank the exact active Down-skill loss. Provide player-visible balances and retention states, durable character persistence, staff diagnostics, a feature flag and a safe disabled default.
   - Current implementation status: the typed capacity setting, disabled `skillBank` flag, and per-character ledger policy cover bounded deposits, Locked/Down retention, deterministic Down-entry replacement, and consumption in tenths. The ModernUO content gain path emits the exact displaced base skill and tenths after an organic, anti-macro-eligible gain, without treating direct scripted gains as organic. Stock under-10 gains still occur after anti-macro denial, but their displaced points are not reported for banking. Tests confirm that temporary skill penalties and expiring bonuses change effective skill values without reporting a bankable base-skill loss; a separate test confirms that a genuine cap displacement during a penalty reports only the exact base-skill tenth lost. ShardContent connects that observer to validated per-character deposits and a `[SkillBank` status/retention command; the payload saves in the same `PlayerMobile` record as active skills. An eligible bank restoration takes precedence over ordinary gain and Mastery, including below 10.0 and above 95.0, and a full active cap uses a planned one-tenth Down-skill exchange that aborts without consuming bank credit if it cannot preserve the loss. Administrators can inspect a player's saved bank and active total with the read-only `[SkillBankStatus [serial]` command even while the feature is disabled. Focused policy and integration-boundary tests pass; edge-case and persistence rehearsals, client UI review and full live validation remain outstanding. The flag cannot yet be enabled.
   - Player status now warns when bank capacity reaches its final 10% and explains full-bank loss or Down-entry replacement. A deterministic mixed-operation test checks bank totals, individual caps and full-cap restoration plans. `Alpha-3-Skill-Bank-Persistence-Rehearsal.md` records a service-level exchange and an ordinary-client full-cap Anatomy restoration followed by an organic deposit; the client's retention command and 0.2-point balance survived save/restart. The client run exposed duplicate gain-handler registration from automatic and bootstrap configuration, now guarded. A second ordinary-client matrix confirmed anti-macro denial consumes no bank credit, all-Locked full-bank overflow preserves balances with a warning, and explicit Down retention replaces the exact incoming displaced amount while leaving Locked balances intact. Other skills, gain stages, malformed-data recovery and longer persistence sequences remain release work.
5. Preserve T2A/UOR Arms Lore behavior. Keep its stock weapon, armor and swamp-dragon-barding inspection; do not add direct combat bonuses or the later exceptional-crafting weapon-damage and armor-resistance bonuses. Those crafting effects remain unavailable under the UOR expansion. The Skill Bank changes skill retention only and does not change Arms Lore mechanics.
6. Include one ordinary pair of scissors in the universal starting package for every newly created character. Like all starter-issued items it is newbied and permanently bound (owner ruling 2026-09-28, replacing the earlier four-hour Starter Protection): loose in the owner's backpack only, kept through every death, never sold, traded, salvaged or replaced. The starter organization bag is an ordinary stock `Bag`, and ordinary newbied items stay protected inside bags unless the owner is a murderer.
   - Current implementation status: starter systems are implemented behind disabled Alpha 3 flags. Per-feature readiness, open cases and evidence live in `Alpha-3-Feature-Enablement-Plan.md` and `Alpha-3-Starter-Package-Audit.md`; this roadmap does not track them.
   - Starter craft materials now have a disabled, validation-blocked gate and Blacksmith, Tinker, Tailor, Carpenter, Bowyer, Scribe, Alchemist and Cook resource packages with separate account entitlements and bound material types. Bound starting tools now replace the relevant stock tools or fill missing Bowyer and Scribe tools; one combined disposable creation probe confirmed tool issuance and stock removal. It is not ready for activation: craft-menu use, crafting consumption and runtime persistence/economy checks remain open.
7. Allocate character-creation stats for every selectable template and the **Advanced** custom option. Each receives exactly **120 starting stat points** across Strength, Dexterity, and Intelligence, with every stat at least **30**. Tune the distribution to the selected template's playstyle; preserve the 225 total stat cap and do not grant ongoing stat bonuses. Audit every option and add regression checks for the 120-point total and per-stat minimum.
   - Current implementation status: the shard post-creation hook allocates Warrior 50/40/30, Mage 30/30/60, Blacksmith 60/30/30, and Advanced from the player's relative stat preferences with a 30-point floor. These are the three templates in the active UOR `Data/Professions/None/prof.txt` plus Advanced. A disposable real-client packet matrix confirmed Warrior 50/40/30, Mage 30/30/60, Blacksmith 60/30/30 and Advanced Healing/Anatomy 42/42/36, each totaling 120 with a 30-point floor. The test also exposed and corrected a creation-hook registration overwrite that had suppressed stats, scissors and bag issuance. The source flag `alpha3StartingStats` remains off pending the rest of the Alpha 3 phase gate.
8. Complete a full UOR-baseline and shard-contract compliance audit of every player skill exposed by the shard.
   - Apply this decision order consistently: an explicit, owner-approved Britannia Renaissance rule or already-delivered custom contract; otherwise the cited UOR-era behavior; never an uncatalogued stock default. Later-era implementation code may remain only when it is necessary to support an approved player-visible result and cannot expose unapproved behavior.
   - Build a definitive skill matrix from the UOR skill table. For every skill, record whether it is enabled, its cited UOR baseline, its effective Britannia Renaissance behavior, any approved-deviation identifier, the ModernUO entry points and configuration gates that implement it, and its automated and live-client evidence. No skill may be marked compliant solely because it is rarely used or lacks an obvious command.
   - Maintain an approved-deviation register for every intentional non-UOR or custom result. Seed it before discrepancy triage from the roadmap's delivered-status notes, committed shard code and tests, active shard configuration, persistence/migration contracts, and recorded owner decisions; absence from a UOR source is not evidence that delivered custom behavior is a defect. Each entry must identify its authority and rationale, implementation or configuration source, feature gate, player-visible contract, persistence or migration concerns, affected skills and systems, and required tests.
   - Treat delivered shard systems as protected compatibility surfaces, including at minimum the hybrid combat contract (T2A-style instant hit and precasting, removed original-weapon procs, and removed Wrestling Stun/Disarm); the accelerated-but-capped gain curve and 95+ Mastery cycle; the no-pets-in-dungeons exception and restricted pet-PvP policy; SafeWorld and Criminal Intent; automatic murder adjudication and the custom murder/red ledger; bank theft rules, Backpack Wards, corpse protections, and Loot Protection; Knocked Out and Execute; and shard-specific starter issuance, binding, and protection rules. Treat the accepted Alpha 2b population manifest, bank polygons, Greater Britain world identity, and other approved shard geography as the world baseline consumed by Alpha 3. Audit these systems' interactions with skills rather than classifying their mere deviation from stock UOR as a defect.
   - Trace active uses and passive hooks end to end: success formulas, difficulty and target rules, skill-delay and cooldown behavior, stat influence, gain eligibility, anti-macro behavior, skill-cap loss, required tools and resources, crafted or harvested outputs, combat modifiers, creature and item interactions, criminal/notoriety effects, messages, and persistence where applicable.
   - Identify every pre-UOR, T2A/UOR, post-UOR, and shard-custom branch reachable from each skill. Disable or remove unapproved later-era mechanics, bonuses, recipes, resources, mastery/special-move interactions and expansion-only targets, but do not remove or silently normalize an approved custom outcome merely because it is not stock UOR.
   - Add focused regression tests for each skill's important era boundary and every approved deviation, plus representative real-client rehearsals for actions that depend on targeting, timing, world objects, vendors, crafting menus, combat or network state. Include cross-skill and cross-system cases where one skill changes another skill's result, and run non-regression coverage against the delivered custom systems before and after remediation.
   - Publish the completed audit matrix, approved-deviation register, and discrepancy log with no unreviewed skills, unresolved classifications or unexplained stock defaults. Any uncertain historical or shard-contract behavior is a release blocker until an owner-approved ruling and testable shard policy replace the ambiguity.
   - Current audit evidence and open classifications are tracked in `Alpha-3-Player-Skill-Audit.md`. The 58-entry runtime inventory and initial deviation register are recorded; UOR character creation, NPC training, and generic skill checks/gains now reject all nine later-era skill IDs. Power scrolls cannot raise a UOR skill beyond 100.0 or act on a later-era skill, and throwing weapons cannot be equipped before SA. Exceptional armor resistance distribution now requires AoS, preserving the UOR Arms Lore crafting boundary. The UOR Detect Hidden delay now follows the documented one-second March 2000 behavior. Item skill bonuses now exclude unavailable skills under UOR. The owner approved retaining Blacksmith BODs as a shard deviation and instructed Alpha 3 to exclude runic hammers before AoS. The vendor path now issues and accepts Smith BODs under UOR while Tailor/Weaver BOD issue and turn-in stay gated to AoS; an ordinary client verified Smith issuance/acceptance and no Tailor BOD option. The reward lookup filters the runic hammer and four items added in Publish 16; four focused reward tests pass in isolated output. Earlier isolated ModernUO runs passed 60 UOR-focused cases, 20 SkillEvents cases and one starter-bound BOD case; the full ShardContent suite passed 211 cases against staged current-source ModernUO assemblies. Other Smith BOD reward types and economy remain open; the current table can pay up to 222,222 gold on a high-value deed and has not been assessed against the accepted shard economy. Item-specific routes, the full skill-by-skill baseline, remediation and client matrix also remain open.

### Exit criteria

- All permanent outdoor Hot-Zone boundaries produce the correct hostility, theft, loot and log-in behavior under client and restart tests.
- House zoning remains closed: `housingGeography` stays disabled and no residential district is opened in Alpha 3. Existing account and payment safeguards retain their focused regression coverage.
- Alpha 3 outdoor Hot Zones retain ordinary spawn cadence, caps and reward tables; the code adds no PvE multiplier. Any later surface reward premium requires a separate owner-approved economy review. Hot dungeon reward premiums remain Beta 2b and Cool Dungeon work Beta 3.
- Skill Bank deposits, replacement, restoration, Mastery interaction, both skill caps, anti-macro eligibility and save/restart persistence pass focused automated and real-client tests. Full-bank behavior never removes Locked entries, silently changes balances, or exceeds the 300.0 bank cap.
- The complete player-skill matrix is reviewed and approved: every exposed skill has a cited UOR baseline and effective shard-contract classification, traced implementation/configuration path, automated boundary coverage and proportionate live-client evidence; every intentional deviation is registered and covered; delivered custom behavior passes non-regression checks; and no unapproved reachable post-UOR behavior or unresolved stock default remains.

**Status (2026-09-30):** all five exit criteria are met and Alpha 3 is enabled; see the closure section of [Alpha-3-Feature-Enablement-Plan.md](Alpha-3-Feature-Enablement-Plan.md).

### Explicitly deferred

Dungeon Hot/Cool rules begin in Beta 2a (permanent Hythloth), Beta 2b (rotating Hot Dungeon and its reward premiums) and Beta 3 (Cool Dungeon); house zoning begins in Beta 2b. Expeditions, trade cargo, Pilgrimage and road speed remain deferred to Beta 2c. Nemesis, Wanted, Salvage and roleplay systems remain disabled.

---

## Beta phase order and owner input

Beta was reorganized on 2026-09-30 by how much input each item needs from the owner. The order is fixed: each phase builds on the ones before it.

| Phase | Theme | Owner input |
| --- | --- | --- |
| Beta 1 | Cosmetic Elf, pet combat restrictions, sub-95 gain curve, live 120-stat creation test, era-correct character templates | Approve the pet policy, the gain-curve numbers and the template list |
| Beta 2a | Ward rulings, 24-hour Mastery redesign, permanent Hythloth | Rulings, Mastery parameters, Hythloth boundary rules |
| Beta 2b | House zoning, rotating Hot Dungeon, Rekindled camping | District decisions, rotation pool and numbers, five camping decisions |
| Beta 2c | Expeditions, cargo, Pilgrimage, road speed, Nemesis, Salvage, Wanted, small leftovers | Contract review, whitelist approval |
| Beta 2d | Crafting and itemization overhaul, Artisan Signature collections | Up to 19 tuning decisions, in slices |
| Beta 3 | Cool Dungeon, shard rename, roleplay layer, BOD reward tiers | Design input for each |
| Beta 4 | Hardening, operations, text review, launch | Final go/no-go only |

Settled by the owner and not part of any phase: dungeon Recall and Gate keep stock behavior with no new restriction (2026-09-30). The game is not a live shard, so nothing in any phase reviews or migrates an old world; migration code that only serves old saves is dropped when a system is touched.

Each phase's new player text is reviewed by the owner with its release. Beta 4 does the final consistency pass.

---
## Beta 1 — Character creation, pet combat restrictions and skill-gain curve

### Goal

Finish the character-facing foundations that later systems depend on: a cosmetic Elf option, character creation that is proven in the real client and shows only era-appropriate templates, a clear pet policy, and the sub-95 skill-gain curve.

### Scope
1. Enable cosmetic Elf character creation in the distributed Britannia Renaissance ClassicUO fork. No owner input.
   - Set `CharacterListFlags.ML` in the shard-owned `expansion.json` to true at activation while keeping `SupportedFeatures.ML` false and the UOR/Felucca ruleset intact; retain the SA-off Gargoyle restriction.
   - Preserve native Elf body, skin and hair while applying Human-equivalent starting rules and gameplay permissions. Keep Elf-only equipment, creature access and ML racial bonuses unavailable.
   - Verify character creation, starter entitlements, Human/Elf parity and appearance after death, resurrection and save/restart on a disposable server before activation.
2. Pet combat restrictions (deferred from Alpha 3 J-5). The owner approves the exact pet policy before anything is built.
   - Already built in Alpha 3: controlled pets do not gain the Hot-only attack permission.
   - Build the dungeon restriction: no controlled pets in dungeon regions unless ridden, and no Recall, Gate, teleport, login, resurrection or restart path that places a combat pet in a dungeon (DD 1209-1250). Confirm pets cannot attack blues inside Hot Zones.
   - Large impact on tamers, so test live with tamer cases and build in isolation.
3. Accelerated skill-gain curve below 95 skill (deferred from Alpha 3 J-4). The owner approves the classes and factors.
   - Survey current gain behavior per skill, propose per-skill difficulty classes and factors (DD 770-835), then build. Alpha 3 keeps stock gain factors (1.0).
   - Check the result against Skill Bank restoration and Mastery, which share the gain path.
4. Live-client test of the 120-point starting stats (Alpha 3 Phase B). No owner input.
   - Alpha 3 verified the 120 total / 30 minimum allocation through Navrey's `createcharacter` command, which sends the creation packet directly. Repeat it in the actual ClassicUO client, driven through its character-creation screens.
   - Cover Advanced creation and every offered template: confirm the stat sliders allow the intended allocations, the client cannot submit anything the server rejects, and each new character ends with exactly 120 points, at least 30 in each stat, and the 225 cap untouched.
   - Record each template and any allocation the client blocks or the server silently adjusts.
5. Show only era-appropriate character templates in ClassicUO. The owner approves the template list.
   - The client lists every profession in its `prof.txt` for the client version, including later-era ones (for example Paladin, Necromancer, Samurai, Ninja); the server only defines Warrior, Mage and Blacksmith for UOR. Remove templates that do not make sense for the UOR era from the creation screen in the distributed ClassicUO fork, so players cannot pick one the shard cannot honor.
   - Keep Advanced creation and the approved templates working, including the cosmetic Elf path from item 1.
   - Verify in the real client that the removed templates are gone, the remaining ones create correctly, and a forged creation packet for a removed template is rejected or falls back safely on the server.

### Exit criteria

- Elf creation works in the distributed ClassicUO fork and passes Human-equivalence, era-gate, Gargoyle-restriction and appearance-persistence tests.
- The pet policy is approved and covered by unit tests and live tamer cases, including every transport path.
- The gain curve is approved, covered by automated tests and does not break Skill Bank or Mastery.
- Live ClassicUO creation gives every offered template and Advanced creation exactly 120 starting stat points with at least 30 in each stat.
- The ClassicUO creation screen lists only approved era-appropriate templates, and the server handles a removed template safely.

### Explicitly deferred

Everything in Beta 2 onward.

---
## Beta 2a — Ward rulings, Mastery redesign and permanent Hythloth

### Goal

Settle the remaining rule decisions that other systems build on, and open the first permanent dungeon Hot Zone.

### Scope
1. Ward and Welcome rulings.
   - Rule F-1 to F-7 in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md), mostly keep. There is no old-world review. Propose removing F-3 and F-7 and their migration code, which only serve an old world, and ask the owner to keep or simplify F-5.
2. Mastery redesign (deferred from Alpha 3 J-2/J-3).
   - Replace the as-built Alpha 1 Mastery mechanic (95.0+ gain suppression, 4-hour UTC pending accrual capped at 0.6, 0.1 spent per valid use) with the design doc's cycle/difficulty-allowance/bank version (DD 837-928), but with a **24-hour** cycle instead of the doc's 18-hour one. The owner approves the parameters. Delete the 18-hour description once this ships.
3. Permanent Hythloth Hot Dungeon. The owner approves the boundary and dungeon rules before building.
   - Define Hythloth as a permanent Hot Dungeon without making other dungeon interiors Hot merely because their entrances are on Fire Island.
   - Apply dungeon-specific hostility, theft, Knocked Out, loot and Execute rules at the authoritative boundary; cover entry/exit messages, login placement, extraction, combat carryover and restart.
   - No reward premium in this phase.

### Exit criteria

- Ward and Welcome rulings are recorded and their code matches.
- Mastery runs on the approved 24-hour design with persistence and save/restart coverage.
- Hythloth hostility, theft and loot rules pass client tests; no other dungeon becomes Hot.

### Explicitly deferred

The rotating Hot Dungeon, the Cool Dungeon and all reward premiums.

---
## Beta 2b — House zoning, rotating Hot Dungeon and Rekindled camping

### Goal

Open housing districts, add the weekly Hot Dungeon, and give camping its flavor identity.

### Scope
1. Deliver the deferred house-zoning foundation. The owner decides districts, capacities and expansion order in one batch after the survey.
   - Survey and configure Greater Britain and Fire Island residential districts; classify residential, rural and protected land, and protect roads, landmarks, dungeons and reserves. Preserve Buccaneer's Den housing prohibition.
   - Establish usable capacity by house size and access constraints; define the one-way district expansion order and occupancy metrics.
   - Complete household/IP exception tooling, inactive-house qualification and decay policy, and placement/payment/save/restart verification before opening a district.
   - Reconcile the Alpha 3 placement, premium, spawner and resource-exclusion work with the approved zoning policy. Keep `housingGeography` disabled until this phase's exit criteria pass and the owner approves.
2. Implement exactly one rotating Hot Dungeon outside Hythloth. The owner approves the pool, schedule and premium numbers.
   - Reuse the Hythloth boundary rules from Beta 2a. Add a schedule, eligibility pool, announcements, offline transition handling, staff override and player-visible status.
   - First ship with reward multipliers disabled; enable the modest +10% ordinary reward/gold and relative magic-chance premium only after region and exploit tests pass. Do not change spawn rate, spawn cap or difficulty as a shortcut.
   - Add force/advance/disable controls, rotation audit reports and regression fixtures for boundary and transition cases.
3. Rekindled camping. The owner decides the five open questions in [Rekindled-Camping-Design.md](Rekindled-Camping-Design.md) before any build.
   - Core package: starter Kindling and Bedroll, skill-scaled campfire burn time, rekindle, embers and a party-visible signal fire.
   - After zoning: the decorative fire pit and the gated camp-stall economy feature.
   - The long-burning torch piece waits for Pilgrimage in Beta 2c.

### Exit criteria

- Housing districts remain closed until land classification, protections, capacity, occupancy and placement/payment/recovery checks pass.
- Rotation selection never overlaps prohibited regions and safely handles online/offline players, boundary transitions, restart and schedule changes; state is server-authoritative, feature-flagged, visible to players and recoverable by staff.
- Camping changes are covered by tests and every part has an owner ruling.

### Explicitly deferred

The Cool Dungeon and the shard rename (Beta 3).

---
## Beta 2c — Weekly living world and world-content extensions

### Goal

Create repeatable, synchronized reasons for players to leave Britain, travel roads and wilderness together, and add optional repeatable goals, without raising the permanent character-power ceiling or relying on respawn acceleration.

### Scope
1. Contract review of the Expedition, cargo, Pilgrimage and road-speed rules. The owner marks each custom rule keep, simplify or cut before any build, as was done for Alpha 3 F to K.
2. Implement the weekly Expedition Region and physical Britain trade route.
   - Activate one outdoor Expedition Region and one Britain-origin route to a configured destination town.
   - Use broad ordered checkpoints/waystations; add player boards/status and staff controls.
   - Apply +50% eligible ordinary harvest yield only within the active Expedition while keeping respawn cadence and rare-resource chances unchanged.
   - Add Expedition Logistics: 3× resource-only carrying capacity in Britain, the active corridor and destination town, with server-authoritative eligibility, provenance and cleanup.
   - Implement character-bound cargo, fast-travel blocking only while it is carried, death/logout/restart handling, rotation grace/abandonment, atomic turn-in and anti-duplication safeguards.
3. Implement the weekly Virtue Pilgrimage.
   - Use Britain-only start, 15-minute windows every four hours, one mainland shrine route, blessed character-bound scrolls and ordered checkpoints.
   - Block fast travel while active, allow mounted travel, preserve state through death/restart, enforce one weekly success and award the documented first-five/later finisher logged-in-time skill bonuses. Coordinate Rekindled's long-burning torch with it.
4. Implement road travel incentives.
   - Audit road tiles/regions and add modest on-foot/mounted speed only on approved roads.
   - Disable the bonus during active PvP aggression and within Hot Zones; validate client synchronization and speedhack detection.
5. Validate the combined economy and population effect.
   - Test harvest yield, carrying capacity, cargo rewards, Pilgrimage gain bonuses and road travel together so stacking does not create a hidden progression or inflation system.
6. Add Nemesis Monsters as a controlled variation of existing natural spawns. The owner approves the prepared whitelist.
   - Use a data-driven species/spawner/region whitelist, per-area caps and opt-outs.
   - Keep the approved horizontal rewards: a mutually exclusive trophy path or consolation gold path, no extra spawn/respawn acceleration, and compatibility-gated presentation fallback.
7. Add Shipwreck Salvage through existing SOS, fishing and boat systems.
   - Use valid Felucca water/chart locations, finite timed salvage rights and at least one weighted decoration outcome.
   - Preserve ordinary MiB/SOS treasure generation; do not add early fishing chart drops or bypass normal treasure paths.
8. Add Wanted Monsters after the existing looting-rights scorer is audited.
   - Restrict contracts to approved Hot rotations and eligible existing creatures/dungeons (the Cool Dungeon joins in Beta 3).
   - Rank contributors through the proven ModernUO scoring API, select the first living recipient deterministically, and use one atomic physical backpack payout with durable same-character overflow reservation.
   - Keep ordinary corpse rights untouched and avoid an independent rolling-damage tracker.
9. Small leftovers: the poison-weapon corrosion formula (corrosion is gated off; the owner picks a formula or drops it), a discard path for bound items, and the "Forged in Danger" Hot-Zone skill veteran title (DD 1003-1041; build or cut).

### Exit criteria

- Expedition, cargo, Pilgrimage and road state are server-authoritative, feature-flagged, visible to players and recoverable by staff.
- Tests cover bypass attempts: teleporting with cargo, route skips, duplicate turn-ins, rotation changes, death, logout, restart, mixed inventories, mounted travel, PvP suppression and client speed synchronization.
- Expedition and Pilgrimage rewards pass economy and anti-exploit validation; no system accelerates resource respawn, changes ordinary spawn caps or raises the character cap.
- Every custom reward flow has atomic issuance, duplication protection, recipient/rights correctness and save/restart coverage.
- Spawn caps and respawn cadence remain unchanged unless a separately approved rule says otherwise.
- Content can be independently disabled without corrupting creatures, rewards, cargo, player inventories or existing world saves.

### Explicitly deferred

Crafting and itemization (Beta 2d), and roleplay systems (Beta 3).

---
## Beta 2d — Crafting and itemization

### Goal

Make crafters valuable through quality, specialization and economy while preserving high-end magic loot and the classic UO power ceiling.

### Scope
1. Deliver the crafting/itemization overhaul (craftsmanship grades, raw-power ceilings relative to magic loot, tinker tools, scroll/spellbook reliability), designed in [ModernUO-Crafting-and-Itemization-Design.md](ModernUO-Crafting-and-Itemization-Design.md). That document is still under iteration. Run the engineering audit first, then resolve its 19 open decisions with the owner in slices; do not redefine its mechanics here.
2. Enable Artisan Signature Collections and destination-specific cosmetics only after BOD, vendor, currency, weight, supply and demand audits.
   - Keep rewards cosmetic, collectible, convenience-oriented or otherwise non-escalating; do not introduce artifacts, power scrolls, mastery ladders or mandatory grind.

### Exit criteria

- The design's definition of done is met, including the hard raw-power ceiling and BOD, repair, death, loot and vendor-economy compatibility.
- Economy review confirms rewards are horizontal and that craft-quality premiums, collections and gold sources do not combine into runaway inflation.
- Content can be independently disabled without corrupting items, rewards or existing saves.

### Explicitly deferred

Gold-only Blacksmith BOD reward tiers (Beta 3), which should be reviewed together with the exceptional and BOD compatibility work here.

---
## Beta 3 — Cool Dungeon, rename, roleplay and BOD rewards

### Goal

Complete the shard's identity and remaining design-heavy content.

### Scope
1. Cool Dungeon. The owner picks the dungeon and its rules.
   - One Cool Dungeon distinct from the rotating Hot Dungeon, retaining Safe-World hostility and disabling direct player stealing while retaining snooping, with theft immunity, entry/exit messages and rotation pairing. `coolZones` stays off until the owner approves.
2. The shard rename to Rekindled, including names and assets. The owner decides.
3. Deliver the narrow approved roleplay layer.
   - Implement the four launch RP POIs, issued RP Gear Chests, IC status toggle, character-bound/non-economic gear tracking, cooldowns, death/repair behavior, scene prop bags and role guides.
   - Add the four fixed RP POI Guestbooks only after the ordinary POI/issued-gear rules work: open reading, costume/proximity-gated writing, immediate append-only publication, archive rollover and report-only staff queue without automatic hiding.
   - Add RP directory and telemetry without rewarding roleplay participation, forcing preapproval or creating new POIs beyond the approved four.
4. Gold-only Blacksmith BOD reward tiers (Alpha 3 I-2). The top point tiers (500 to 1200) are gold and fame only after the runic-hammer exclusion; the owner wants a real non-power reward added.

### Exit criteria

- No custom system ships without an owner ruling or an approved design.
- The Cool Dungeon passes hostility and theft client tests and can be disabled without corrupting saves.

### Explicitly deferred

Launch validation (Beta 4).

---
## Beta 4 — Hardening and launch candidate

### Goal

Prove launch readiness: complete observability and operations, closed test debt, consistent text, a fresh-world rehearsal, and a release candidate that has passed the full regression, economy and persistence suite. The owner's only input is the final go/no-go.

### Scope
1. Close Alpha 3 test debt.
   - Live Hot Zone cases for pets, delayed damage, boats and Recall crossings; time-driven Mastery periods (against the redesigned Mastery); the same-account second-character case; a crafting-consumption pass; the open live skill checks (Cooking menu reachability, Meditation and Resisting Spells numbers, Magery cast timing, Item Identification relabel, Tracking arrow, stone/sand mining, bandage formula); an integration test for `StarterCombatIssuance.Issue()`.
2. Clearly label starter gear and other starter items when they have special restrictions or properties, such as being non-sellable or nontransferable, so players can distinguish them from ordinary items.
3. Complete administrative and player-facing operations.
   - Finish inspection, force/advance/recovery and audit commands for zones, housing, Expeditions, Pilgrimage, road travel, Wards, content rewards and RP systems.
   - Add reward-table validation, catalog checks, per-spawner opt-outs, analytics and crash/restart recovery tests; add a scripted fresh-world build.
   - Publish player rules, staff runbooks, configuration reference, release notes and support procedures.
4. Review all user-facing text.
   - Audit messages, gumps, menus, prompts, journals, status displays, help text, system notifications and staff-facing player text introduced or modified through Beta 3.
   - Bring the wording, tone, terminology, capitalization and localization style into consistency with the base game's prose, and require human review before release. Refresh the README and website.
5. Run launch-candidate validation.
   - Execute the full automated regression suite: era/core, combat, Safe/Hot/boundary, murder/Intent, theft/Wards, corpse rights, housing, rotations, Expeditions, Pilgrimage, roads, pets, rewards, content, crafting and roleplay.
   - Perform clean-world, client compatibility, multi-account/concurrency, restart, recovery, log-review, economy-simulation and manual PvP matrix rehearsals.
   - Freeze feature scope; resolve only launch blockers, correctness defects, security/exploit defects and documentation gaps.
6. Prepare a release gate.
   - Produce an owner-facing go/no-go checklist with known limitations, rollback paths, data migration plan, monitoring thresholds and staged feature-flag activation order.

### Exit criteria

- A fresh world can be built, configured, started, played, saved, restarted and restored with all enabled systems remaining consistent.
- The manual PvP and social matrices pass with intended client versions; logs make material decisions supportable.
- All custom serialized entities and migrations survive repeated save/reload and versioned configuration changes.
- All Beta user-facing text has passed a human editorial review for consistency with the base game's prose style, terminology and localization conventions.
- Documentation, operations and feature flags support a staged launch, and the owner formally accepts the launch rules that require approval.


## Release gates and feature activation order

| Gate | Required before enabling | Examples |
| --- | --- | --- |
| Core gate | Alpha 1 complete | era/content audit, hybrid combat, caps, starter and classic economy | 
| Law gate | Alpha 2 complete | Safe-World, Intent, murder adjudication, theft and corpse protection | 
| World gate | Alpha 2b complete | versioned Felucca/UOR population manifest, reviewed generators, restart-stable save and tested rollback |
| Geography gate | Alpha 3 complete | permanent outdoor Hot regions and boundaries, starter systems, Skill Bank and UOR player-skill audit; ordinary outdoor spawn/reward tables remain unchanged |
| Character gate | Beta 1 complete | cosmetic Elf creation, pet combat restrictions, sub-95 gain curve |
| Rules gate | Beta 2a complete | Ward and Welcome rulings, redesigned 24-hour Mastery, permanent Hythloth Hot Dungeon |
| Home and camp gate | Beta 2b complete | housing districts, rotating Hot Dungeon and premiums, Rekindled camping |
| Living-world gate | Beta 2c complete | Expedition, cargo, Pilgrimage, roads, Nemesis, Salvage, Wanted and combined economy tests |
| Crafting gate | Beta 2d complete | craftsmanship and itemization overhaul, Artisan Signature collections |
| Identity gate | Beta 3 complete | Cool Dungeon, shard rename, RP systems, BOD reward tiers |
| Launch gate | Beta 4 complete | full operations, closed test debt, text review, fresh-world rehearsal and launch sign-off |


## Definition of readiness for any phase

A phase is not complete because it compiles. It is complete only when its documented goal works from a clean test save, its automated and manual tests pass, persistence and recovery are proven, logs support diagnosis, configuration is validated, and its systems do not weaken the settled shard rules or create an unapproved vertical power path. For world-population phases, “clean test save” also requires a recorded source-save lineage, a single writer, a versioned input manifest, per-facet count evidence and a successfully rehearsed rollback.
