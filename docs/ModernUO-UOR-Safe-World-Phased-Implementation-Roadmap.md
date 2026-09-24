# ModernUO UOR Safe-World — Phased Implementation Roadmap

**Source design:** `ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md`  
**Status:** Planning baseline  
**Release sequence:** Alpha 1 → Alpha 2 → Alpha 3 → Beta 1 → Beta 2 → Beta 3

## Purpose

This roadmap turns the Safe-World / PvP Hot-Zones alternative plan into six coherent releases. It intentionally starts with the rules that every character, combat interaction and later system depends on, then adds region rules and housing, then world-concentration systems, and only after that adds the larger retention and content feature sets.

The sequence is a dependency order, not a promise to enable every feature immediately on a production shard. Each release must be tested on a clean test world, survive save/restart, and have a documented rollback or feature-flag disable path before the next release begins.

## Shared delivery rules

- Pin and record the ModernUO commit before Alpha 1. Keep upstream changes isolated from shard-specific code and configuration.
- Put shard policy in a typed shard configuration layer (target: `Distribution/Configuration/shard-rules.json`), not scattered constants or imagined stock JSON keys.
- Prefer narrow adapters at proven ModernUO extension points. Do not rewrite upstream combat, loot-rights, housing, fishing, or region systems without source evidence and regression coverage.
- Keep production-facing features behind flags until their region, persistence, economy and exploit tests pass.
- After every milestone: compile, run focused automated tests, launch the shard, inspect logs, exercise the affected rules with real clients, and verify a save/restart cycle.
- Preserve the fixed power ceiling: UOR platform, Felucca-only world, pre-AoS itemization, 700 skill / 225 stat caps, no insurance, no mandatory vertical-progression treadmill, and no hidden post-UOR systems.

## Alpha 1 — Era-correct playable core

### Goal

Make the shard launch as a stable, recognizably pre-AoS UOR-era world with the intended hybrid combat contract, character progression and classic economy foundations. At the end of this alpha, a player can create a character, progress, fight monsters, travel, die, recover, craft and trade under the correct baseline rules—but no custom Safe-World or rotation system is active yet.

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
   - Implement 95.0+ Mastery with one server-wide UTC period schedule: four-hour boundaries,
     +0.1 pending increments, login-date qualification, offline reconciliation, a 0.6 pending cap,
     and valid-use consumption through 100.0.
   - Validate pre-AoS death, corpse, loot, blessed runebook, stealable-key/property and travel behavior.
   - Validate ordinary crafting, BODs, player trade, vendors, boats, and the no-combat-pets-in-dungeons / restricted pet-PvP policy.
   - Implement the starter package and one-time account/character issuance controls without economic extraction loopholes.

### Exit criteria

- Clean build and repeatable startup from a clean test save.
- Automated and manual tests prove expansion/map gating, caps, insta-hit, precast timing, special-attack removal, swing behavior, 95+ Mastery period banking/consumption, death/loot, key recovery, starter issuance and save/restart persistence.
- A client can complete the basic loop—create, train, fight, loot, die, bank, travel, craft and trade—without accessing disabled era content.
- The configuration layer exposes only verified shard controls and produces understandable startup validation errors.

### Explicitly deferred

Safe-World hostility, murder replacement, theft wards, Hot/Cool zones, housing geography, Expedition systems, Pilgrimage, road speed, and all custom retention content.

---

## Alpha 2 — Safe-world law, crime and consent

### Goal

Make the shard’s defining social contract correct: ordinary blue players are protected from unsolicited direct attacks outside Hot Zones while real crime, thieves, greys, reds, lawful retaliation, full loot and voluntary PvP remain meaningful. This is the first phase in which the custom world identity is enabled.

### Scope

1. Implement a central player-hostility decision service.
   - Route direct player hostility through a single auditable authority that considers region, blue/grey/red state, `[Intent]`, guild-war exceptions and inherited lawful encounter rights.
   - Block ordinary-blue versus ordinary-blue initiation outside Hot Zones.
   - Preserve attacks on criminals and murderers everywhere, direct-target retaliation rights, approved guild conflict and independent pet restrictions.
2. Implement `[Intent]` as a stored, blue-only voluntary PvP preference.
   - Make `[Intent]` opt-in, visible, persistent and independently reversible for new opponents.
   - Preserve existing encounter rights when it is turned off; prohibit turning it off while genuinely criminal or red.
   - Ensure intent-only grey status remains attackable without being confused with genuine criminality.
3. Replace murder adjudication with the approved automatic model.
   - Create a separate kill/murder adjudicator and historical ledger.
   - Award at most one automatic count for each qualifying ordinary-blue death and add 24 hours to a cumulative UTC red timer.
   - Ensure Hot-Zone location, lawful self-defense and guild-war status do not waive the ordinary-blue murder consequence unless the death was actually intent-classified.
   - Disable conflicting stock reporting, threshold and decay behavior before enabling any reward system.
   - Current implementation status: `MurderAdjudicationService` contains the tested policy, account-tag ledger, persisted encounter snapshots, and feature-gated `PlayerDeathEvent` hook behind `featureFlags.automaticMurderAdjudication`; the ModernUO fork exposes the narrow legacy-reporting disable, legacy-red suppression, and additional-red-status hooks. Live migration rehearsal, old-context audit, and public enablement remain gated work.
4. Preserve crime while adding narrowly targeted anti-harassment protections.
   - Keep ordinary stealing and snooping intact by default.
   - Add explicit bank theft-protection polygons and Cool-Dungeon-compatible theft checks that do not create combat-safe bank bubbles.
   - Add consumable Backpack Wards: one-active physical backpack presence, account-aware post-success detection escalation, 120-second victim protection, durable persistence and starter-issued binding rules.
   - Add the invisible Loot Protection Ward: permit the first unlawful non-Hot monster-corpse transfer, then block only repeated unlawful looting by that offender account against the protected victim’s still-rights-protected monster corpses for ten minutes.
   - Current implementation status: the feature-gated `BackpackWard` and stock Stealing/Corpse pre/post hooks implement deterministic physical-Ward selection, per-thief-account 25%/50%/100% escalation, post-resolution consumption, persistent 120-second victim protection, and first-transfer/ten-minute-repeat protection for unlawful non-Hot monster corpses. Bank/Cool polygons, starter issuance/binding, and live enablement remain gated work.
5. Implement the Knocked Out state and safe-world resolution path.
   - Make qualifying zero-health outcomes for genuinely blue players enter a durable, untargetable, damage-immune 90-second Knocked Out state rather than death; clear effects and active aggression while retaining an immutable completed-encounter record.
   - Permit no-skill Knocked-Out looting only to the criminal/red who held recorded target-specific engagement rights at the moment of Knock Out; retain all item-binding and Ward rules.
   - Make safe-world Execution an explicit, encounter-authorized action that applies the same automatic ordinary-blue murder count and cumulative red time as a normal player kill.
6. Add the observability needed to support the rules.
   - Log hostility decisions, encounter classification, murder adjudication, theft/Ward activity and corpse-transfer enforcement with stable character/account identifiers.
   - Provide staff inspection and recovery tools before public enablement.

### Exit criteria

- The complete safe, Intent, criminal, murderer, guild-war, retaliation, Knocked Out and Hot-context matrices pass in automated and real-client testing.
- Stealing and snooping remain functional where allowed; banks, Wards and corpse protections restrict only the specified actions and identities.
- Multiple-account and concurrency tests prove one count per death, no duplicate Ward/corpse state, correct offline red-timer expiry and save/restart survival.
- Staff can explain a disputed PvP, theft or corpse decision from logs and diagnostic commands.

### Explicitly deferred

Permanent and rotating zone activation, reward premiums, housing placement policy, weekly activity systems, and feature content. The code may understand a Hot-region context, but no live bonus/reward program ships until Alpha 3 is stable.

---

## Alpha 3 — Geographic risk and housing foundation

### Goal

Put the legal and economic rules into the world: predictable permanent and rotating PvP geography, a concentrated safe PvE destination, and a housing system that makes Greater Britain the social and commercial capital without artificial global scarcity.

### Scope

1. Deliver the permanent high-risk geography.
   - Define Hythloth as the permanent Hot Dungeon and Fire Island plus Buccaneer’s Den island as permanent outdoor Hot regions.
   - Implement authoritative region boundaries, entry/exit messaging, combat carryover, login placement and extraction behavior.
   - Apply Fire Island’s special residential rules and Buccaneer’s Den’s house-placement prohibition.
   - Apply the shared Knocked Out state in Hot Zones while changing its resolution: any criminal/red may perform no-skill looting without engagement-right restrictions, any player may Execute, and physical Backpack Wards have no effect on Hot-Zone theft or Knocked-Out looting.
2. Deliver rotation infrastructure before economic bonuses.
   - Implement exactly one rotating Hot Dungeon and exactly one distinct Cool Dungeon, with schedule, eligibility pool, conflict prevention, announcements, offline transition handling, staff override and player-visible status.
   - In Cool Dungeon, retain Safe-World hostility and disable direct player stealing while retaining snooping.
   - First ship rotations with reward multipliers disabled; activate the modest +10% ordinary reward/gold and relative magic-chance premium only after region and exploit tests pass. Do not change spawn rate, spawn cap or difficulty as a shortcut.
3. Implement concentrated housing policy.
   - Enforce one house per account with explicit household/IP exception tooling.
   - Survey Greater Britain, define launch residential polygons, classify land as residential/rural/protected, estimate capacity and protect roads, landmarks, dungeons and reserves.
   - Allow normal-cost placement only inside opened Greater Britain districts; implement a one-way, observable district expansion sequence.
   - Implement optional high-cost rural placement, non-refundable surcharge, protected-land override prevention, inactive-house qualification/decay and occupancy metrics.
4. Establish release-level operational tools.
   - Add region/housing inspection commands, force/advance/disable controls, audit reports and regression fixtures for boundary, rotation and placement cases.

### Exit criteria

- All permanent, Hot, Cool and transition boundaries produce the correct hostility, theft, loot and log-in behavior under client and restart tests.
- Rotation selection never overlaps prohibited regions and safely handles online/offline players, restart and schedule changes.
- Housing placement obeys one-per-account, polygon, rural-cost, protected-land and special-island rules; capacity/expansion data is visible to staff.
- Reward multipliers, if enabled, pass economy and anti-exploit validation while ordinary spawn cadence and cap remain unchanged.

### Explicitly deferred

Expeditions, trade cargo, Pilgrimage and road speed; these depend on trustworthy regions, travel and housing topology. Nemesis, Wanted, Salvage and roleplay systems remain disabled.

---

## Beta 1 — The weekly living world

### Goal

Create repeatable, synchronized reasons for players to leave Britain, travel roads and wilderness together, and return to the economy—without raising the permanent character-power ceiling or relying on respawn acceleration.

### Scope

1. Implement the weekly Expedition Region and physical Britain trade route.
   - Activate exactly one outdoor Expedition Region and one Britain-origin route to a configured destination town.
   - Use broad ordered checkpoints/waystations; add player boards/status and staff controls.
   - Apply +50% eligible ordinary harvest yield only within the active Expedition while keeping respawn cadence and rare-resource chances unchanged.
   - Add Expedition Logistics: 3× resource-only carrying capacity in Britain, the active corridor and destination town, with server-authoritative eligibility, provenance and cleanup.
   - Implement character-bound cargo, fast-travel blocking only while it is carried, death/logout/restart handling, rotation grace/abandonment, atomic turn-in and anti-duplication safeguards.
2. Implement the weekly Virtue Pilgrimage.
   - Use Britain-only start, 15-minute windows every four hours, one mainland shrine route, blessed character-bound scrolls and ordered checkpoints.
   - Block fast travel while active, allow mounted travel, preserve state through death/restart, enforce one weekly success and award the documented first-five/later finisher logged-in-time skill bonuses.
3. Implement road travel incentives.
   - Audit road tiles/regions and add modest on-foot/mounted speed only on approved roads.
   - Disable the bonus during active PvP aggression and within Hot Zones; validate client synchronization and speedhack detection.
4. Validate the combined economy and population effect.
   - Test harvest yield, carrying capacity, cargo rewards, Pilgrimage gain bonuses and road travel together so stacking does not create a hidden progression or inflation system.

### Exit criteria

- Expedition, cargo, Pilgrimage and road state are fully server-authoritative, feature-flagged, visible to players and recoverable by staff.
- Tests cover bypass attempts: teleporting with cargo, route skips, duplicate turn-ins, rotation changes, death, logout, restart, mixed inventories, mounted travel, PvP suppression and client speed synchronization.
- Economy simulation and live-scale test data support the final reward values; no system accelerates resource respawn or raises the character cap.

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
| Geography gate | Alpha 3 complete | permanent/rotating regions, boundaries, housing policy, verified reward premiums | 
| Living-world gate | Beta 1 complete | Expedition, cargo, Pilgrimage, roads and combined economy tests | 
| Content gate | Beta 2 complete | Nemesis, Salvage, Wanted and collections | 
| Launch gate | Beta 3 complete | RP systems, full operations, fresh-world rehearsal and launch sign-off | 

## Definition of readiness for any phase

A phase is not complete because it compiles. It is complete only when its documented goal works from a clean test save, its automated and manual tests pass, persistence and recovery are proven, logs support diagnosis, configuration is validated, and its systems do not weaken the settled shard rules or create an unapproved vertical power path.
