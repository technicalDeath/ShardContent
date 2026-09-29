# Alpha 3 Phase K: Permanent outdoor Hot Zones readiness

**Decision:** Ready for Alpha 3 enablement, with `hotZones` still disabled. This closes feature readiness only; the combined Phase L activation decision remains outstanding.

## Reused accepted evidence

- Two island polygons (Fire Island, Buccaneer's Den) cover their connected land, exclude dungeons, and passed focused membership and hostility checks; a disposable client saw entry and exit notices. See [Hot Zone survey](Alpha-3-Outdoor-Hot-Zone-Survey.md).
- K1 boundary pass: map and tiledata hashes match, the Buccaneer's Den east-dock leak was closed, and 18 live boundary cases pass, including the 3-second login delay for the entry message. See [K1](Alpha-3-Outdoor-Hot-Zone-Survey.md).
- K2 combat and consequence pass: same-region and cross-boundary combat with its 2-minute carryover (H1-H6), Knocked Out (KO1-KO4), Knocked Out loot (L2, L2a, L3), Execute outside Hot (X2, X3), theft and Ward effects (T1-T4), corpse and exit observations (C1, B10). See [K2](Alpha-3-Outdoor-Hot-Zone-Survey.md#k2-combat-and-consequence-pass-2026-09-29).
- Owner rulings K-4 (Execute needs a grey or red actor with damage-record rights; in Hot anyone may loot a Knocked Out player's pack, and a blue who does becomes criminal), K-5 (match stock: no murder count when the victim attacked first), K-7 (Buccaneer's Den bank polygon not theft protected) and K-9 (no Fire Island reward premium; removed from the design) are recorded in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md).

## Current-source review

- `OutdoorHotZonePolicy` decides membership at decision time; `PvpIntentService.AllowHarmful`, `KnockedOutService`, `TheftProtectionService` and `PlayerMobile.PositionChanged` are the only consumers. Nothing in ModernUO spawn, creature loot or gold code references a Hot Zone, so ordinary outdoor spawn cadence and rewards are unchanged.
- Only the `FireIsland` and `BuccaneersDenIsland` regions exist. The validator rejects `coolZones` and requires both surveyed regions when `hotZones` is on. Dungeons (including Hythloth) are outside the polygons, and no dungeon Hot or Cool rule is in Alpha 3.
- Since the K2 commit (`3c737f1`) the only ShardContent changes are the K3 test driver, the `[TestOnlyCorpseAggressors` probe command (test scenarios, not shipped code) and documentation. ModernUO is clean, so no K2 or K1 evidence is reopened.

## New verification

Disposable host `phase-k3`, `hotZones` and `alpha3EnablementAcknowledged` on in the host copy only, `TestOnlyProbe` loaded, driver `tests/scenarios/hot-zones/hot_k3_live.py` (phase 1 seeds, one save, one restart, phase 2 asserts). Full table in the [K3 section of the survey](Alpha-3-Outdoor-Hot-Zone-Survey.md#k3-login-save-restart-and-release-scope-pass-2026-09-29).

- **Reruns of K2 cases changed by rulings:** X1 (blue bystander refused), L1 (blue looter authorized and flagged criminal), XR (red with rights executes in Hot, murder +1), XR2, X4 (executor in the corpse's aggressor list), X5a (victim aggressed first: no murder count), X5b (never-aggressor: murder +1). All pass.
- **Dungeon exclusion:** D1-D3 in Hythloth (blue-vs-blue refused, `[HotZoneStatus` reports no region, no boundary message). All pass.
- **Login, save, restart:** P1-P5 seeded; R1 (Knocked Out 15 s before the restart stays Knocked Out), R2 (entry message after the restart), R3 (expired Knocked Out cleared and the player woken on login). All pass.
- **Cleanup:** all client sessions stopped by recorded PID, server stopped with `-NoSave`, host removed. The dev world and `ModernUO/Distribution` were not touched.

## Gate and validator

- `featureFlags.hotZones` is `false` in source and in the deployed copy; `alpha3EnablementAcknowledged` is `false` in both. The validator requires the acknowledgment before `hotZones` can load.
- The deployed `Distribution` still lags K2: its `shard-rules.json` lacks the K-7 change (one extra Buccaneer's Den bank envelope remains) and its DLL predates the K2 commit. The next `Deploy-Alpha1Baseline.ps1` run, with the server stopped, brings it in line; flags stay false.

## Readiness limits

- Login-time messages are not visible to Navrey, so the Knocked Out state at login was asserted through hits and damage immunity, not the message text.
- Spawn cadence, rewards and the absence of any dungeon Hot or Cool activation or surface premium are established by source inspection and the validator, not a live spawn run.
- XR's murder +1 was proven in two full runs; the final full rerun reused a victim who had attacked first and correctly gave murder +0 under K-5, so it is not a defect.
- Stock Snooping is refused once the victim is Knocked Out, so a looter must open the pack before the Knock Out. Stock Stealing refuses Newbied, container and immovable items, so loot cases use plain items.
- H7 (pets) is unit-tested only and H8 (delayed damage) and boat and Recall crossings (B7, B8) are source-only. House multis are Beta 2.
- Restart coverage is one restart with a 15 s-old Knocked Out; the 90 s deadline is an account tag, and the in-memory expiry timer is not persisted, so login does the reconciliation.
