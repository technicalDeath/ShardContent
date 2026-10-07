# Alpha 3 Phase K: Permanent outdoor Hot Zones readiness

**Decision:** Ready for Alpha 3 enablement, with `hotZones` still disabled. This closes feature readiness only; the combined Phase L activation decision remains outstanding.

## Reused accepted evidence

- Two island polygons (Fire Island, Buccaneer's Den) cover their connected land, exclude dungeons, and passed focused membership and hostility checks; a disposable client saw entry and exit notices. See [Hot Zone survey](Alpha-3-Outdoor-Hot-Zone-Survey.md).
- K1 boundary pass: map and tiledata hashes match, the Buccaneer's Den east-dock leak was closed, and 18 live boundary cases pass, including the 3-second login delay for the entry message. See [K1](Alpha-3-Outdoor-Hot-Zone-Survey.md).
- K2 combat and consequence pass: same-region and cross-boundary combat with its 2-minute carryover (H1-H6), Knocked Out (KO1-KO4), Knocked Out loot (L2, L2a, L3), Execute outside Hot (X2, X3), theft and Ward effects (T1-T4), corpse and exit observations (C1, B10). See [K2](Alpha-3-Outdoor-Hot-Zone-Survey.md#k2-combat-and-consequence-pass-2026-09-29).
- Owner rulings K-4 (Execute needs a grey or red actor with damage-record rights; in Hot anyone may loot a Knocked Out player's pack, and a blue who does becomes criminal), K-5 (matched stock: no murder count when the victim attacked first; **amended 2026-10-06: an Execute counts unless the victim had Criminal Intent on or it was a duel or guild war, see `Murder-Report-Right-To-Attack.md`**), K-7 (Buccaneer's Den bank polygon not theft protected) and K-9 (no Fire Island reward premium; removed from the design) are recorded in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md).

## Current-source review

- `OutdoorHotZonePolicy` decides membership at decision time; `PvpIntentService.AllowHarmful`, `KnockedOutService`, `TheftProtectionService` and `PlayerMobile.PositionChanged` are the only consumers. Nothing in ModernUO spawn, creature loot or gold code references a Hot Zone, so ordinary outdoor spawn cadence and rewards are unchanged.
- Only the `FireIsland` and `BuccaneersDenIsland` regions exist. The validator rejects `coolZones` and requires both surveyed regions when `hotZones` is on. Dungeons (including Hythloth) are outside the polygons, and no dungeon Hot or Cool rule is in Alpha 3.
- Since the K2 commit (`3c737f1`) the only ShardContent changes are the K3 test driver, the `[TestOnlyCorpseAggressors` probe command (test scenarios, not shipped code) and documentation. ModernUO is clean, so no K2 or K1 evidence is reopened.

## New verification

Disposable host `phase-k3`, `hotZones` and `alpha3EnablementAcknowledged` on in the host copy only, `TestOnlyProbe` loaded, driver `tests/scenarios/hot-zones/hot_k3_live.py` (phase 1 seeds, one save, one restart, phase 2 asserts). Full table in the [K3 section of the survey](Alpha-3-Outdoor-Hot-Zone-Survey.md#k3-login-save-restart-and-release-scope-pass-2026-09-29).

- **Reruns of K2 cases changed by rulings:** X1 (blue bystander refused), L1 (blue looter authorized and flagged criminal), XR (red with rights executes in Hot, murder +1), XR2, X4 (executor in the corpse's aggressor list), X5a (victim aggressed first: no murder count), X5b (never-aggressor: murder +1). All pass.
- **Dungeon exclusion:** D1-D3 in Hythloth (blue-vs-blue refused, `[HotZoneStatus` reports no region, no boundary message). All pass. **Superseded 2026-10-02 (Beta 2a):** Hythloth now follows the Hot Zone rules behind `hythlothHotZone`; other dungeons stay excluded. See `Beta-2a-Hythloth-Hot-Zone-Audit.md`.
- **Login, save, restart:** P1-P5 seeded; R1 (Knocked Out 15 s before the restart stays Knocked Out), R2 (entry message after the restart), R3 (expired Knocked Out cleared and the player woken on login). All pass.
- **Cleanup:** all client sessions stopped by recorded PID, server stopped with `-NoSave`, host removed. The dev world and `ModernUO/Distribution` were not touched.

## Gate and validator

- `featureFlags.hotZones` is `false` in source and in the deployed copy; `alpha3EnablementAcknowledged` is `false` in both. The validator requires the acknowledgment before `hotZones` can load.
- The deployed `Distribution` still lags K2: its `shard-rules.json` lacks the K-7 change (one extra Buccaneer's Den bank envelope remains) and its DLL predates the K2 commit. The next `Deploy-Alpha1Baseline.ps1` run, with the server stopped, brings it in line; flags stay false.

## Readiness limits

- Login-time messages are not visible to Navrey, so the Knocked Out state at login was asserted through hits and damage immunity, not the message text.
- Spawn cadence, rewards and the absence of any dungeon Hot or Cool activation or surface premium are established by source inspection and the validator, not a live spawn run.
- XR's murder +1 was proven in two full runs; the final full rerun reused a victim who had attacked first and correctly gave murder +0 under K-5, so it is not a defect.
- Knocked Out looting is corpse-style (owner ruling 2026-09-29): an eligible looter opens the pack and lifts items with no Snooping or Stealing skill. It needs three narrow ModernUO hooks (uncommitted at the time of this record): `Snooping.KnockedOutOpen`, `PlayerMobile.NonlocalLiftHandler` and `PlayerMobile.ItemLiftedHandler`; the `Stealing.KnockedOutLoot` bypass was removed. Newbied, Blessed and Nontransferable items, and bags holding one, cannot be lifted. Live cases L1, L5 and L6 passed on disposable host `phase-k4` with the looter at 0 Snooping and 0 Stealing. The XR rerun on that host showed murder +0 and exposed a defect: `RecordExecutorAsAggressor` left a non-criminal `Aggressed` entry on the executor that made the victim read as an enemy (stock `Notoriety.CheckAggressed`), so a second kill of the same victim was not a reportable murder, and the entry was not swept because the stock expiry timer does not start for directly added records. Fixed in `KnockedOutService.TryExecute` by removing the executor and victim aggressor entries after the kill; re-run live in Phase L (2026-09-30, disposable host `phase-l`): the first fix removed only one of the executor's two `Aggressed` entries (stock `RemoveAggressed`/`RemoveAggressor` drop one match, and combat had already left a criminal entry ahead of the one Execute adds), so a repeat kill inside the 2-minute expiry window still counted 0. `ClearExecutionAggression` now removes every match. Live after the fix: first Execute murder +1, then the same victim Executed again within seconds also +1 (count=2). Regression test `KnockedOutTests.ExecutionLeavesNoLawfulFightRecordSoARepeatKillStillCountsAsMurder` pins the stock notoriety behavior and the cleanup (focused suite, 108 tests, run `20260930T000042737Z-1ab969`; full Shard suite 238 tests, run `20260930T000136484Z-8869fb`). A murderer who kills the same non-aggressor victim twice should get two counts.
- H7 (pets) is unit-tested only and H8 (delayed damage) and boat and Recall crossings (B7, B8) are source-only. House multis are Beta 2b.
- Restart coverage is one restart with a 15 s-old Knocked Out; the 90 s deadline is an account tag, and the in-memory expiry timer is not persisted, so login does the reconciliation.

**Phase L live pass (2026-09-30, `phase-l`, driver `tests/scenarios/hot-zones/hot_l_protected_live.py`, 10/10):** Blessed (stock Spellbook), Nontransferable (starter scissors and Ward) and Newbied items each refuse a lift from a Knocked Out pack in Hot while a plain item lifts and the looter turns criminal (extends L5, which covered Newbied only); after Execute the corpse holds none of the 26 protected serials and the dead player keeps all 26; a repeat Execute of the same non-aggressor victim counts a second murder. Blessed items came from a stock Spellbook because a staff `[set LootType Blessed` on an item in another player's pack silently did nothing.
