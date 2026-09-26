# ModernUO UOR Safe-World — Phased Implementation Roadmap

**Source design:** `ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md`  
**Status:** Planning baseline  
**Release sequence:** Alpha 1 → Alpha 2 → Alpha 2b → Alpha 3 → Beta 1 → Beta 2 → Beta 3

## Purpose

This roadmap turns the Safe-World / PvP Hot-Zones alternative plan into seven coherent releases. It intentionally starts with the rules that every character, combat interaction and later system depends on, establishes a reproducible UOR/Felucca world population, then adds region rules and housing, then world-concentration systems, and only after that adds the larger retention and content feature sets.

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
   - Add consumable Backpack Wards: one-active physical backpack presence, account-aware post-success detection escalation, 120-second victim protection, durable persistence and starter-issued binding rules.
   - Add the invisible Loot Protection Ward: permit the first unlawful non-Hot monster-corpse transfer, then block only repeated unlawful looting by that offender account against the protected victim’s still-rights-protected monster corpses for ten minutes.
   - Current implementation status: the feature-gated `BackpackWard` and stock Stealing/Corpse pre/post hooks implement deterministic physical-Ward selection, per-thief-account 25%/50%/100% escalation, post-resolution consumption, persistent 120-second victim protection, first-transfer/ten-minute-repeat protection for unlawful non-Hot monster corpses, a permanent invisible Loot Protection entitlement with idempotent bounded world-load migration plus login/creation fallback, character-creation starter issuance with durable account binding, and data-driven bank/Cool polygon checks at the theft boundary. The pinned engine now observes ordinary drag/lift corpse transfers as well as context-menu use and exposes the monster-corpse rights snapshot; markers are keyed by rights-holder character and offender account so separate corpses from the same victim cannot bypass the ward. The 87/87 content suite covers the corpse-repeat policy matrix. The runtime geometry contains 18 compact bank envelopes with a 5–6 tile apron and the ten UOR-era dungeon rectangles. Movement transitions explain the active theft rules to players; snooping and combat remain untouched. The review export tools remain the reproducible source evidence for future map revisions.
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

Production world population, permanent zone activation, weekly Hot/Cool dungeon rotations, reward premiums, housing placement policy, weekly activity systems, and feature content. The code may understand a Hot-region context, but no live bonus/reward program ships until Alpha 3 is stable.

---

## Alpha 2b — Era-safe initial world population

### Goal

Turn the Felucca map into a reproducible, playable UOR world without importing inactive facets, post-UOR content, duplicate infrastructure or a stock layout that contradicts Greater Britain’s role as the only surviving city. World generation is a controlled content deployment: its inputs, exclusions, order, counts, save provenance and rollback point must be reviewable and repeatable.

ModernUO’s Admin → World Building → **Do everything** action is not approved for this shard. The stock actions are convenience generators, not a UOR/Felucca migration plan: several write to every facet, the spawner action imports the entire Felucca tree including later-era locations, and some actions replace or overlap existing world objects.

**Current local implementation and execution status (2026-09-26):** complete. The former runtime state was stopped, verified to have no second writer, and moved intact to `ModernUO/Distribution/WorldStateArchive/alpha2b-reset-2026-09-26-14-13-19`. Only the existing owner-account index was carried into the fresh save so the generation command could be authenticated; no prior items, mobiles, guilds or other world objects were restored. `data/world-generation/alpha2b/world-generation.json` is the reviewed source manifest, `tools/Prepare-Alpha2bWorldData.ps1` reads stock inputs from the pinned Git commit and combines them with shard-owned sign exclusions, Britain vendor overrides and bounty-board data under `data/world-generation/alpha2b`. It builds alternate runtime inputs under `Distribution/Data/BritanniaRenaissance/Alpha2b`, so unrelated or uncommitted stock-file edits cannot silently change the generated baseline. Deployment prepares those inputs automatically without editing stock data. The owner-only `[Alpha2bWorldGen preview|apply CONFIRM-UOR-FELUCCA [rerun]|audit` command enforces the UOR/Felucca pin, refuses an unexpected non-empty world, canonicalizes overlapping stock records with last-definition-wins semantics, audits inactive facets and required infrastructure, and saves only after the audit passes.

The accepted clean run produced 13,970 decorations, 385 canonical generic teleporter placements, 1,546 canonical spawners, 410 Felucca signs, nine public moongates and 63 Khaldun dynamic items. The initial validation pass correctly caught four effective teleporter overlaps and 122 superseded spawner records before any generated state was saved. Two controlled convergence reruns then passed; the final rerun created zero additional decorations, rebuilt the replaceable travel/spawner/sign layers, found Khaldun already complete, passed the same audit and saved. A shutdown/restart loaded the generated world successfully, the real-client audit passed again with all inactive facets empty, and a final completed save was published at 2026-09-26 14:42 local time.

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
   - Current implementation: the source manifest, sign exclusion, Britain vendor overrides and Britain bounty-board supplement live under `data/world-generation/alpha2b`; the preparation tool reads stock files from the pinned commit, copies and filters them into the shard-specific runtime namespace and writes `generation-report.json` with candidate and canonical counts. The runtime command validates every generated sign, teleporter and spawner before mutation. Use `preview` first, the exact confirmation token for the clean apply, `audit` after load, and the additional `rerun` argument only for a controlled convergence rehearsal.
3. Populate the world in a deliberate, rehearsed order.
   - **Decorations:** apply only the reviewed Felucca result from the shared Britannia and Felucca decoration sets, plus Felucca bounty boards only while the configured bounty system remains approved. Do not call the stock `Decorate` command unchanged: it also targets Trammel, Ilshenar, Malas and Tokuno. Curate functioning shops, civic fixtures and settlement dressing so fallen towns read as ruins, outposts or contested ground rather than peer cities to Greater Britain.
   - **Teleporters:** import only reviewed Felucca definitions from `Data/teleporters.json`. The stock `TelGen` spans six facets and replaces generic teleporters near configured endpoints, so the runner must facet-filter the input and report each replacement. Verify Lost Lands, dungeon entrances/exits and other required links from both directions.
   - **Public moongates:** run `MoonGen` only after confirming the active-map selection is Felucca-only. It deletes existing `PublicMoongate` objects before rebuilding them; the current configuration should produce the nine Felucca gates, which must be counted and client-tested after generation.
   - **Spawners:** import an explicit, file-level and, where necessary, entry-level UOR allowlist from `Data/Spawns/shared/felucca`. Never use the stock Felucca-folder button as the allowlist. Review towns, vendors, wilderness and every dungeon against the Greater Britain narrative and the era audit; explicitly exclude `BlightedGrove`, `PaintedCaves`, `PalaceOfParoxysmus`, `PrismOfLight`, `Sanctuary` and `SolenHive` unless a later approved design deliberately repurposes them. Account for the importer’s deletion/recreation and immediate-respawn behavior.
   - **Signs:** use the tracked `Distribution/Data/signs.cfg` as reviewed source data, but generate only the Felucca placements. The current file has 508 source records: 395 shared-Britannia records and 15 Felucca-only records yield the accepted 410 Felucca signs. Haven’s tailor, butcher, healer and blacksmith entries are Trammel-only and are deliberately excluded from this UOR/Felucca world rather than copied across facets. Recompute these figures whenever the pinned ModernUO data changes, audit localized and ordinary labels, and remove or rewrite signs that incorrectly present fallen settlements as active peer cities.
   - **Khaldun:** run `GenKhaldun` only if Khaldun is approved as launch-accessible UOR content. Count its puzzle/controller objects, test the encounter flow, and prove a rerun does not duplicate them.
   - After each stage, capture its report and inspect representative locations before continuing. Decorations precede specialized travel, spawner and sign passes so those later operations can provide the reviewed authoritative result where inputs overlap.
4. Make exclusions explicit instead of silently relying on configuration.
   - Do not run `DoorGen` by default. Shared Britannia and Felucca decoration data already place doors, while the stock door scan also visits inactive facets; use a reviewed gap list only if client testing finds missing doors.
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

Faction activation, champion spawns and their reward progression, post-UOR locations and generators, optional door-gap repair, and any unreviewed stock world-building input. Alpha 3 geography and housing work begins only after the populated baseline and its rollback are accepted.

---

## Alpha 3 — Geographic risk and housing foundation

### Goal

Apply the legal and economic geography to the accepted Alpha 2b world: predictable permanent PvP regions and a housing system that makes Greater Britain the social and commercial capital without artificial global scarcity. Establish region boundaries that the weekly Hot/Cool dungeon rotations can use in Beta 1.

### Scope

1. Deliver the permanent high-risk geography.
   - Define Hythloth as the permanent Hot Dungeon and Fire Island plus Buccaneer’s Den island as permanent outdoor Hot regions.
   - Implement authoritative region boundaries, entry/exit messaging, combat carryover, login placement and extraction behavior.
   - Apply Fire Island’s special residential rules and Buccaneer’s Den’s house-placement prohibition.
   - Apply the shared Knocked Out state in Hot Zones while changing its resolution: any criminal/red may perform no-skill looting without engagement-right restrictions, any player may Execute, and physical Backpack Wards have no effect on Hot-Zone theft or Knocked-Out looting.
2. Implement concentrated housing policy.
   - Enforce one house per account with explicit household/IP exception tooling.
   - Survey Greater Britain, define launch residential polygons, classify land as residential/rural/protected, estimate capacity and protect roads, landmarks, dungeons and reserves.
   - Allow normal-cost placement only inside opened Greater Britain districts; implement a one-way, observable district expansion sequence.
   - Implement optional high-cost rural placement, non-refundable surcharge, protected-land override prevention, inactive-house qualification/decay and occupancy metrics.
3. Establish release-level operational tools.
   - Add permanent-region and housing inspection commands, audit reports and regression fixtures for boundary and placement cases.
4. Deliver the Skill Bank defined in `ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md`, Section 5.1.
   - Preserve only exact skill points organically displaced by ordinary skill-cap gains, in a per-character bank capped at 300.0 total points and the individual skill cap per entry.
   - Provide per-entry Locked/Down retention controls. At capacity, replace only Down bank entries, draining the largest balance first with alphabetical tie-breaking; if no Down balance is available, preserve existing bank contents and notify the player that the incoming loss was not banked.
   - Restore one banked 0.1 per valid gain-eligible skill use, subject to existing anti-macro and skill-use eligibility. Bank restoration precedes ordinary gains and Mastery, including restoration of previously earned value through 100.0.
   - Preserve the 700.0 active cap with atomic exchanges that bank the exact active Down-skill loss. Provide player-visible balances and retention states, durable character persistence, staff diagnostics, a feature flag and a safe disabled default.
5. Preserve T2A/UOR Arms Lore behavior. Keep its stock weapon, armor and swamp-dragon-barding inspection; do not add direct combat bonuses or the later exceptional-crafting weapon-damage and armor-resistance bonuses. Those crafting effects remain unavailable under the UOR expansion. The Skill Bank changes skill retention only and does not change Arms Lore mechanics.
6. Include one ordinary pair of scissors in the universal starting package for every newly created character. Apply the package's four-hour Starter Protection and permanent `StarterIssued` resale/salvage restrictions; never replace scissors after loss or destruction.
7. Allocate character-creation stats for every selectable template and the **Advanced** custom option. Each receives exactly **120 starting stat points** across Strength, Dexterity, and Intelligence, with every stat at least **30**. Tune the distribution to the selected template's playstyle; preserve the 225 total stat cap and do not grant ongoing stat bonuses. Audit every option and add regression checks for the 120-point total and per-stat minimum.
8. Complete a full UOR-era compliance audit of every player skill exposed by the shard.
   - Build a definitive skill matrix from the UOR skill table. For every skill, record whether it is enabled, its intended UOR behavior, the authoritative era reference, the ModernUO entry points and configuration gates that implement it, and its automated and live-client evidence. No skill may be marked compliant solely because it is rarely used or lacks an obvious command.
   - Trace active uses and passive hooks end to end: success formulas, difficulty and target rules, skill-delay and cooldown behavior, stat influence, gain eligibility, anti-macro behavior, skill-cap loss, required tools and resources, crafted or harvested outputs, combat modifiers, creature and item interactions, criminal/notoriety effects, messages, and persistence where applicable.
   - Identify every pre-UOR, T2A/UOR, and post-UOR branch reachable from each skill. Disable or remove later-era mechanics, bonuses, recipes, resources, mastery/special-move interactions and expansion-only targets unless a separately approved shard rule explicitly overrides the era; document every intentional deviation rather than allowing it to inherit silently from stock content.
   - Add focused regression tests for each skill's important era boundary and representative real-client rehearsals for actions that depend on targeting, timing, world objects, vendors, crafting menus, combat or network state. Include cross-skill and cross-system cases where one skill changes another skill's result.
   - Publish the completed audit matrix with no unreviewed skills, unresolved era classifications or unexplained stock defaults. Any uncertain historical behavior is a release blocker until an owner-approved ruling and testable shard policy replace the ambiguity.

### Exit criteria

- All permanent Hot-Zone boundaries produce the correct hostility, theft, loot and log-in behavior under client and restart tests.
- Housing placement obeys one-per-account, polygon, rural-cost, protected-land and special-island rules; capacity/expansion data is visible to staff.
- Permanent Hot-Zone reward multipliers, if enabled, pass economy and anti-exploit validation while ordinary spawn cadence and cap remain unchanged.
- Skill Bank deposits, replacement, restoration, Mastery interaction, both skill caps, anti-macro eligibility and save/restart persistence pass focused automated and real-client tests. Full-bank behavior never removes Locked entries, silently changes balances, or exceeds the 300.0 bank cap.
- The complete player-skill matrix is reviewed and approved: every UOR skill has a cited era classification, traced implementation/configuration path, automated boundary coverage and proportionate live-client evidence; no reachable post-UOR behavior or unresolved stock default remains.

### Explicitly deferred

Weekly Hot/Cool dungeon rotations and their reward premiums, Expeditions, trade cargo, Pilgrimage and road speed; these depend on trustworthy regions, travel and housing topology. Nemesis, Wanted, Salvage and roleplay systems remain disabled.

---

## Beta 1 — The weekly living world

### Goal

Create repeatable, synchronized reasons for players to leave Britain, gather in changing Hot and Cool dungeons, travel roads and wilderness together, and return to the economy—without raising the permanent character-power ceiling or relying on respawn acceleration.

### Scope

1. Deliver the weekly Hot/Cool dungeon rotations before economic bonuses.
   - Implement exactly one rotating Hot Dungeon and exactly one distinct Cool Dungeon, with schedule, eligibility pool, conflict prevention, announcements, offline transition handling, staff override and player-visible status.
   - In the Cool Dungeon, retain Safe-World hostility and disable direct player stealing while retaining snooping.
   - First ship rotations with reward multipliers disabled; activate the modest +10% ordinary reward/gold and relative magic-chance premium only after region and exploit tests pass. Do not change spawn rate, spawn cap or difficulty as a shortcut.
   - Add force/advance/disable controls, rotation audit reports and regression fixtures for boundary and transition cases.
2. Implement the weekly Expedition Region and physical Britain trade route.
   - Activate exactly one outdoor Expedition Region and one Britain-origin route to a configured destination town.
   - Use broad ordered checkpoints/waystations; add player boards/status and staff controls.
   - Apply +50% eligible ordinary harvest yield only within the active Expedition while keeping respawn cadence and rare-resource chances unchanged.
   - Add Expedition Logistics: 3× resource-only carrying capacity in Britain, the active corridor and destination town, with server-authoritative eligibility, provenance and cleanup.
   - Implement character-bound cargo, fast-travel blocking only while it is carried, death/logout/restart handling, rotation grace/abandonment, atomic turn-in and anti-duplication safeguards.
3. Implement the weekly Virtue Pilgrimage.
   - Use Britain-only start, 15-minute windows every four hours, one mainland shrine route, blessed character-bound scrolls and ordered checkpoints.
   - Block fast travel while active, allow mounted travel, preserve state through death/restart, enforce one weekly success and award the documented first-five/later finisher logged-in-time skill bonuses.
4. Implement road travel incentives.
   - Audit road tiles/regions and add modest on-foot/mounted speed only on approved roads.
   - Disable the bonus during active PvP aggression and within Hot Zones; validate client synchronization and speedhack detection.
5. Validate the combined economy and population effect.
   - Test dungeon premiums, harvest yield, carrying capacity, cargo rewards, Pilgrimage gain bonuses and road travel together so stacking does not create a hidden progression or inflation system.
6. Review all user-facing text.
   - Audit messages, gumps, menus, prompts, journals, status displays, help text, system notifications and staff-facing player text introduced or modified through Beta 1.
   - Bring the wording, tone, terminology, capitalization and localization style into consistency with the base game's prose, and require human review before release.

### Exit criteria

- Hot/Cool rotation selection never overlaps prohibited regions and safely handles online/offline players, boundary transitions, restart and schedule changes; Cool-Dungeon theft and hostility rules pass client tests.
- Dungeon rotations, Expedition, cargo, Pilgrimage and road state are fully server-authoritative, feature-flagged, visible to players and recoverable by staff.
- Tests cover bypass attempts: teleporting with cargo, route skips, duplicate turn-ins, rotation changes, death, logout, restart, mixed inventories, mounted travel, PvP suppression and client speed synchronization.
- Reward multipliers, if enabled, pass economy and anti-exploit validation; no system accelerates resource respawn, changes ordinary spawn caps or raises the character cap.
- All Beta 1 user-facing text has passed a human editorial review for consistency with the base game's prose style, terminology and localization conventions.

### Explicitly deferred

New monster/loot/content systems and roleplay collections. Beta 1 should demonstrate that the world-concentration loop works before adding more reward surfaces.

---

## Beta 2 — Horizontal endgame and world-content extensions

### Goal

Add optional repeatable goals—harder natural spawns, themed collections, sea activity and weekly bounties—using existing ModernUO systems and the stable risk/reward foundations from earlier releases. These features broaden choice rather than create vertical power.

### Scope

1. Add Nemesis Monsters as a controlled variation of existing natural spawns.
   - Use a data-driven species/spawner/region whitelist, per-area caps and opt-outs.
   - Keep the approved horizontal rewards: a mutually exclusive trophy path or consolation gold path, no extra spawn/respawn acceleration, and compatibility-gated presentation fallback.
2. Add Shipwreck Salvage through existing SOS, fishing and boat systems.
   - Use valid Felucca water/chart locations, finite timed salvage rights and at least one weighted decoration outcome.
   - Preserve ordinary MiB/SOS treasure generation; do not add early fishing chart drops or bypass normal treasure paths.
3. Add Wanted Monsters after the existing looting-rights scorer is audited.
   - Restrict contracts to approved Hot/Cool rotations and eligible existing creatures/dungeons.
   - Rank contributors through the proven ModernUO scoring API, select the first living recipient deterministically, and use one atomic physical backpack payout with durable same-character overflow reservation.
   - Keep ordinary corpse rights untouched and avoid an independent rolling-damage tracker.
4. Add the approved horizontal crafting and collection work.
   - Enable Artisan Signature Collections and destination-specific cosmetics only after BOD, vendor, currency, weight, supply and demand audits.
   - Keep rewards cosmetic, collectible, convenience-oriented or otherwise non-escalating; do not introduce artifacts, power scrolls, mastery ladders or mandatory grind.
5. Build content/economy operations.
   - Add reward-table validation, catalog checks, per-spawner opt-outs, analytics and crash/restart recovery tests.

### Exit criteria

- Every custom reward flow has atomic issuance, duplication protection, recipient/rights correctness and save/restart coverage.
- Spawn caps and respawn cadence remain unchanged unless a separately approved rule says otherwise.
- Economy review confirms that rewards are horizontal and that Hot/Cool premiums, cargo rewards, collections and gold sources do not combine into runaway inflation.
- Content can be independently disabled without corrupting creatures, rewards, cargo, player inventories or existing world saves.

### Explicitly deferred

Broader roleplay POIs, guestbooks and scene systems. Beta 2 focuses on combat/PvE/crafting/maritime systems that consume the now-proven world infrastructure.

---

## Beta 3 — Social layer, hardening and launch candidate

### Goal

Complete the shard’s social identity and prove launch readiness: roleplay support without mandatory participation, complete observability and operations, a fresh-world rehearsal, and a release candidate that has passed the full regression, economy and persistence suite.

### Scope

1. Deliver the narrow approved roleplay layer.
   - Implement the four launch RP POIs, issued RP Gear Chests, IC status toggle, character-bound/non-economic gear tracking, cooldowns, death/repair behavior, scene prop bags and role guides.
   - Add the four fixed RP POI Guestbooks only after the ordinary POI/issued-gear rules work: open reading, costume/proximity-gated writing, immediate append-only publication, archive rollover and report-only staff queue without automatic hiding.
   - Add RP directory and telemetry without rewarding roleplay participation, forcing preapproval or creating new POIs beyond the approved four.
2. Complete administrative and player-facing operations.
   - Finish inspection, force/advance/recovery and audit commands for zones, housing, Expeditions, Pilgrimage, road travel, Wards, content rewards and RP systems.
   - Publish player rules, staff runbooks, configuration reference, release notes and support procedures.
3. Run launch-candidate validation.
   - Execute the full automated regression suite: era/core, combat, Safe/Hot/boundary, murder/Intent, theft/Wards, corpse rights, housing, rotations, Expeditions, Pilgrimage, roads, pets, rewards, content and roleplay.
   - Perform clean-world, client compatibility, multi-account/concurrency, restart, recovery, log-review, economy-simulation and manual PvP matrix rehearsals.
   - Freeze feature scope; resolve only launch blockers, correctness defects, security/exploit defects and documentation gaps.
4. Prepare a release gate.
   - Produce an owner-facing go/no-go checklist with known limitations, rollback paths, data migration plan, monitoring thresholds and staged feature-flag activation order.

### Exit criteria

- A fresh world can be built, configured, started, played, saved, restarted and restored with all enabled systems remaining consistent.
- The manual PvP and social matrices pass with intended client versions; logs make material decisions supportable.
- All custom serialized entities and migrations survive repeated save/reload and versioned configuration changes.
- Documentation, operations and feature flags support a staged launch, and the owner formally accepts the launch rules that require approval.

## Release gates and feature activation order

| Gate | Required before enabling | Examples |
| --- | --- | --- |
| Core gate | Alpha 1 complete | era/content audit, hybrid combat, caps, starter and classic economy | 
| Law gate | Alpha 2 complete | Safe-World, Intent, murder adjudication, theft and corpse protection | 
| World gate | Alpha 2b complete | versioned Felucca/UOR population manifest, reviewed generators, restart-stable save and tested rollback |
| Geography gate | Alpha 3 complete | permanent Hot regions, boundaries, housing policy, Skill Bank and verified permanent reward premiums |
| Living-world gate | Beta 1 complete | Hot/Cool dungeon rotations, verified rotation premiums, Expedition, cargo, Pilgrimage, roads and combined economy tests |
| Content gate | Beta 2 complete | Nemesis, Salvage, Wanted and collections | 
| Launch gate | Beta 3 complete | RP systems, full operations, fresh-world rehearsal and launch sign-off | 

## Definition of readiness for any phase

A phase is not complete because it compiles. It is complete only when its documented goal works from a clean test save, its automated and manual tests pass, persistence and recovery are proven, logs support diagnosis, configuration is validated, and its systems do not weaken the settled shard rules or create an unapproved vertical power path. For world-population phases, “clean test save” also requires a recorded source-save lineage, a single writer, a versioned input manifest, per-facet count evidence and a successfully rehearsed rollback.
