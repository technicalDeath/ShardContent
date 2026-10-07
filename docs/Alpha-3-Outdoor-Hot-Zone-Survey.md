# Alpha 3 outdoor Hot-zone map survey

The candidate `FireIsland` and `BuccaneersDenIsland` polygons are in
`data/configuration/shard-rules.json` under `hotZones.permanentOutdoorRegions`. The feature flag
remains off. Hythloth and every other `DungeonRegion` interior are excluded by
`OutdoorHotZonePolicy`, regardless of polygon coordinates.

## Source and method

The survey read the local Felucca `UOData/map0LegacyMUL.uop` through ModernUO's UOP block layout
and classified land tiles using the `Wet` flag in `UOData/tiledata.mul`. The map was configured as
7168 × 4096 tiles. The source file SHA-256 values were:

| Local source | SHA-256 |
| --- | --- |
| `map0LegacyMUL.uop` | `EA42CB16A224FACD3FA177C6001AE80B50C30C5EDB35877A4841CE865ECE3944` |
| `tiledata.mul` | `F44860782F4818CBFF36A9372A3F16E5747886E0064C72A4AEC922DFE1994E37` |

A four-neighbor flood fill from each landmark selected its connected non-wet land component.
Tracing the component shoreline, adding a three-tile margin and simplifying the resulting contour
to a three-tile tolerance produced the configured polygons. Two Fire Island vertices were moved
outward to account for the server's integer point-in-polygon arithmetic. The margin prevents safe
land strips at a simplified coast; it does include nearshore water and inlets.

| Region | Land seed | Survey rectangle | Connected land tiles | Land bounds | Polygon vertices |
| --- | --- | --- | ---: | --- | ---: |
| Fire Island | Hythloth entrance `(4722,3814)` | `(3700,2850)`–`(5000,4050)` | 311,444 | `(4098,3074)`–`(4860,3989)` | 185 |
| Buccaneer's Den island | Town arrival `(2706,2163)` | `(2490,1880)`–`(2930,2420)` | 85,142 | `(2570,1928)`–`(2888,2368)` | 86 |

Neither land component touched its survey rectangle. Exhaustive raster checks using the same
integer ray-casting rule as `TheftRegionPolicy.Contains` found **zero missed component land tiles**
and **zero tiles from another non-wet land component** inside either polygon. Fire Island's polygon
contains 13,197 wet tiles; Buccaneer's Den island's contains 4,565 wet tiles. All vertices are
unique, and neither polygon has a proper edge intersection. Automated source fixtures cover the
town and Hythloth arrival points, outer Buccaneer's Den land, nearby open ocean, Felucca-only
membership and dungeon exclusion.

## K1 geography and boundary pass (2026-09-29)

**Runtime data.** The workspace `UOData` directory is the one directory both the server and Navrey read. `map0LegacyMUL.uop` and `tiledata.mul` still match the hashes above. Other inputs, recorded for later comparison: no `mapdif0` files exist; `stadif0/stadifi0/stadifl0.mul` patch 1,783 static blocks. An independent parse (UOP entries ordered by their filename hash, HS-format tiledata) reproduced the survey's counts exactly: 85,142 dry and 4,565 wet tiles inside the original Buccaneer's Den polygon, 13,197 wet tiles in Fire Island's.

**Static walkability check.** From every walkable spot inside a polygon (land that is not Wet or Impassable, plus passable Surface statics, including stadif patches), a flood fill (step up 8, down 14, eight neighbours) looked for reachable spots outside the polygon.

| Region | Reachable spots outside | Result |
| --- | ---: | --- |
| Fire Island | 0 | No leak |
| Buccaneer's Den island (before) | 177 | An east dock of wooden plank statics (x 2749-2762, y 2154-2179, z -2) crossed the polygon edge `(2750,2152)`-`(2749,2178)`, leaving up to 13 tiles of dock outside |
| Buccaneer's Den island (after) | 0 | Fixed |

**Fix.** In the BuccaneersDenIsland polygon, vertices `(2750,2152)` and `(2749,2178)` became `(2766,2151)` and `(2767,2182)`, which put the dock plus a three-tile margin inside. Rechecked against map data: 86 vertices, no proper edge intersections, all 85,142 island land tiles inside, zero tiles from any other land component, wet tiles inside 5,068 (was 4,565). The source-fixture test now asserts the dock corners, the moongate, and the teleporter arrival tiles are Hot, and that the neighbouring bay and the outside teleporter source are not.

### Boundary case list

Every way a player can change Hot status. Land walking cannot cross a boundary on either island (both are islands with a water margin), so all transitions are teleports, sailing, login or death placement. All go through `PlayerMobile.PositionChanged` and the settled-position check in `OutdoorHotZoneBoundaryService`.

| # | Direction | Case | Coordinates | Verification |
| --- | --- | --- | --- | --- |
| B1 | safe to Hot | Public moongate from any other city to Buccaneer's Den (stock Felucca list) | destination `(2711,2234)` | Source fixture; live |
| B2 | Hot to safe | Buccaneer's Den moongate out to any city | source `(2711,2234)` | Live |
| B3 | safe to Hot | Generated teleporter from `(2618,977)` to Buccaneer's Den docks | arrival `(2727,2133)` | Fixture; live |
| B4 | Hot to safe | Same teleporter, reverse | source `(2727,2133)` | Live |
| B5 | Hot to dungeon | Hythloth entrance teleporters on Fire Island | `(4721..4723,3813)` to `(5904..5906,16)` | Fixture; earlier live evidence (`hot.log`); recheck live |
| B6 | dungeon to Hot | Hythloth exit back to Fire Island | reverse of B5 | Live |
| B7 | either | Recall and Gate Travel to a rune inside or outside the polygon | any | Live: one in, one out |
| B8 | either | Sailing a boat across the three-tile margin (Buccaneer's Den docks, Fire Island coast) | margin | Live if a boat can be placed; otherwise source only |
| B9 | either | Login placement, logout inside or outside | any | Source; live |
| B10 | either | Death and resurrection at a healer or shrine | any | Belongs to K2/K3 |
| B11 | Hot to Hot | Cellar teleporters on the island, same polygon | `(2603,2120)`, `(2669,2071)`, `(2676,2241)`, `(2685,2063)`, `(2758,2092)` | Fixture; no messages expected |
| B12 | Hot | Dock at x 2749-2762 | as fixed above | Fixture; live |
| B13 | safe | Bay east of the dock, water beyond the margin | `(2775,2166)` | Fixture |

### K1 live results (2026-09-29)

Disposable host (`hotZones` on with acknowledgment, scratch only; the source flags stay off), one ordinary fresh player and one staff session. Driver: `tests/scenarios/hot-zones/hot_boundary_live.py <player> <staff>`; it asserts the entry and exit messages per case and exits non-zero on a mismatch. Placement uses `[set Location`; teleporters and moongates are used by walking onto them and answering the real gate gump.

| Case | Result |
| --- | --- |
| Safe to Fire Island shore `(4600,3500)`, and back to Britain | Entry then exit message |
| Open ocean `(4000,3500)`, west of the polygon | No message |
| B12 dock corners `(2749,2154)`, `(2762,2154)`, `(2762,2179)` | Entry at the first, no message between corners |
| B13 bay `(2775,2166)`, then the dock again `(2755,2166)` | Exit, then entry |
| Town and ocean south `(2711,2400)` | Exit |
| B5 walk north onto Hythloth entrance `(4722,3813)` from `(4722,3816)` | Entry on Fire Island, then exit on arrival at `(5905,16,64)` |
| B6 step onto the return teleporter from `(5905,17,64)` | Entry on Fire Island, arrival `(4722,3813)` |
| Hythloth interior `(5905,22,44)` by placement | Exit |
| B3 walk onto `(2618,977)` | Entry, arrival `(2727,2133,5)` |
| B4 step back onto `(2727,2133)` | Exit, arrival `(2618,977,5)` |
| B1 Britain moongate to Buccaneer's Den (real gate gump) | Entry, arrival `(2711,2234)` |
| B2 Buccaneer's Den moongate to Britain | Exit, arrival `(1336,1997)` |
| B11 cellar teleporter `(2603,2120,-20)` to `(2605,2130,8)` | No message |
| B9 login while standing on the Buccaneer's Den dock | See the finding below |

**Finding (B9, fixed).** A player who logged in inside a Hot Zone received no entry message. `OutdoorHotZoneBoundaryService` scheduled its observation for the next tick after `EventSink.Connected`, which is before the client has entered the world, and the client discards system messages until then. Login observation now waits `LoginObservationDelay` (3 seconds); the fixed build delivered the entry message about 2.5 seconds after "Entered the world". Movement-driven observation is unchanged (next tick). A unit test pins the delay to at least one second.

**Source-only cases.** B7 (Recall and Gate Travel) and B8 (a ship crossing the margin) were not driven live. Recall, Gate Travel and boats all end in `Mobile.SetLocation` or the `Location` setter, which reach `OnLocationChange` and therefore `PlayerMobile.PositionChanged`, the same path the placement and teleporter cases used. B10 (death and resurrection placement) belongs to K2 and K3.

Not covered by these checks: house multis (Beta 2b zoning), ship decks (dynamic, see B8), and any client asset changes after the hashes above.

## K2 combat and consequence pass (2026-09-29)

Scope: behavior at and across the Hot boundary. Login, save and restart, spawn and rewards, and the readiness record are K3. Membership is evaluated where the victim, thief or corpse is at decision time (`OutdoorHotZonePolicy.IsHot`). Pure decisions already have unit tests (`OutdoorHotZonePolicyTests`, `KnockedOutTests`, `TheftProtectionTests`, `MurderAdjudicationTests`); this pass adds the live cases that prove the hooks are wired to them.

Live driver: `tests/scenarios/hot-zones/hot_consequences_live.py`. Disposable host with `hotZones` on and `alpha3EnablementAcknowledged`; `safeWorld`, `knockedOut`, `theftProtection` and `automaticMurderAdjudication` are already on in the deployed config. Six fresh ordinary players (attacker A, victims V1-V3, bystander E, thief T) plus one staff session.

| ID | Behavior | Entry point | Expected | Verification | Result |
| --- | --- | --- | --- | --- | --- |
| H1 | Blue attacks blue, both in the same Hot region | `PvpIntentService.AllowHarmful` | Allowed; victim loses hits | Live | Pass. Hits 72 to 71, attacker Criminal |
| H2 | Same pair, both in a safe town | same | Refused; no damage | Live (control) | Pass. No damage, `hostility denied` +1 |
| H3 | Attacker in Hot, victim one tile outside | same (`attackerRegion` != `defenderRegion`) | Refused | Live | Pass. Denied +1, no damage |
| H4 | Attacker outside, victim one tile inside | same | Refused | Live | Pass. Denied +1, no damage |
| H5 | Fight begun in Hot, both then step outside | `HasExistingRelationship` | Attacker may keep attacking; a bystander outside may not join | Live | Pass. Attacker continued after the crossing (victim hits 72 to 71), bystander denied +1 with no damage. The crossing is by staff placement, not walking, and the attacker was already Criminal from the Hot initiation |
| H6 | Same fight after the 2-minute aggression window lapses | `Aggressors` expiry | Attacker refused again | Live | Pass on rerun. Idle 207 s, attacker Innocent again, denied +1, no damage. The first two attempts were harness faults (the victim's client kept swinging, then the attacker was a ghost) |
| H7 | Pet or summon as the source | `directPlayerSource` | No Hot initiation | Unit test (`NewHotZoneHostility...`) | Unit only (named limit) |
| H8 | Delayed damage (poison tick, field, explosion) landing after a crossing | `Mobile.Damage` then `TryInterceptLethalDamage` | Hostility is not re-checked; Knocked Out decided at the victim's position when the damage lands | Source only (named limit) | Source only (named limit) |
| KO1 | Lethal blow to a blue in Hot | `TryInterceptLethalDamage` | Knocked Out, no death | Live | Pass. Knocked Out, hits 1, unarmed attacker |
| KO2 | Lethal blow outside Hot after an H5 carryover | same, active encounter | Knocked Out | Live | Pass. Knocked Out audit, attacker recorded |
| KO3 | Attacking a Knocked Out player | `AllowHarmful` first line | Refused, hits stay at 1 | Live | Pass. No second Knocked Out (client hits read 1 to 2 through regeneration, not damage) |
| KO4 | Criminal or murderer victim at lethal damage | `IsQualifyingVictim` | Dies, not Knocked Out | Live (found while running L2) | Observed. A Criminal victim in Hot died outright. Matches the source predicate `Alive && !Criminal && !Murderer` |
| L1 | Blue opens a Knocked Out blue's pack and lifts an item in Hot | `Snooping.KnockedOutOpen`, `PlayerMobile.CheckNonlocalLift`, then `KnockedOutService.OnKnockedOutLootResolved` | Allowed corpse-style with no Snooping or Stealing skill (owner ruling 2026-09-29); the blue becomes criminal | Unit (`hot-zone-blue-looting`); live in K3 | Pass on the corpse-style path with the looter at 0 Snooping and 0 Stealing: `authorized` +1, item moved into the looter's pack, `blue-flagged-criminal` recorded, looter Criminal. Supersedes the earlier Stealing-bypass runs |
| L2 | Criminal looter, no recorded rights, in Hot | same | Allowed | Live (earlier Stealing-bypass path) | Passed on the old path. Corpse-style rerun covered by L1 (same eligibility predicate) |
| L2a | Snooping a Knocked Out victim's pack | stock `Snooping` (`CanBeHarmful`) | Observation only | Live observation | Superseded. An eligible looter now opens the pack through `Snooping.KnockedOutOpen` before any skill check; ineligible players still get the stock refusal |
| L3 | Knocked Out victim moved outside Hot: blue bystander, then criminal non-attacker, then criminal recorded attacker | same | Bystander and non-attacker denied; recorded criminal attacker allowed | Live | Pass. Denied, denied, authorized. Asserts the authorization decision only (see limits) |
| X1 | Blue bystander executes a Knocked Out blue in Hot | `[Execute` then `KnockedOutService.Execute` | Refused: K-4 ruling (2026-09-29) limits Execute to a grey or red actor with damage-record rights. Victim stays alive, no murder count | Unit (`ExecutionRequiresRedActorWithDamageRecordRights`); live rerun in K3 | Originally passed live under the old "anyone may Execute" rule. Superseded. K3 rerun (X1) passes: refused, victim alive, murder +0 |
| X4 | Red executor with damage-record rights kills a Knocked Out blue; executor loots the corpse | `KnockedOutService.Execute` → `RecordExecutorAsAggressor` | Corpse aggressor list contains the executor (Knocked Out cleared the victim's lists), so lifting an item raises no "criminal act" warning | Live in K3: corpse aggressor membership read through `[TestOnlyCorpseAggressors` | Pass in K3 (X4): the corpse's aggressors held the executor's serial |
| X5 | K-5: red executes a Knocked Out blue who attacked the red first; and red executes a blue the red attacked first | `KnockedOutService.Execute` → `ExecutionCountsAsMurder` | Blue attacked first: no murder count, audit says "victim aggressed first". Red attacked first: murder count plus 24h red | Unit (`ExecutionCountsAsMurderOnlyForReportableAttackers`); live in K3 (both orders, since it depends on engine aggressor bookkeeping) | Pass in K3 (X5a, X5b): see the K3 section |
| X2 | Blue bystander executes outside Hot | same | Refused | Live | Pass. "not eligible for encounter-authorized execution" |
| X3 | Criminal recorded attacker executes outside Hot | same | Allowed | Live | Pass. Executed, automatic murder count |
| T1 | Thieves-guild thief attempts a steal from a blue in Hot | `CanAttemptTheft` (Hot bypass) | Reaches the stock skill roll | Live | Pass. Roll message ("You fail to steal the item.") |
| T2 | Same attempt outside Hot on a blue | `Stealing` harmful check | No steal | Live (control) | Pass. No roll and no message, `hostility denied` +1, no Ward consumed |
| T3 | Ward protection seeded on a criminal victim outside Hot, then victim enters Hot | `IsProtectionActive` after the Hot bypass | Denied outside while protected; allowed in Hot; denied again outside within 120 s | Live | Pass (T3a seed, T3b denied, T3c Hot allowed, T3d denied again 48 s after the seed). Needs a victim who still carries a Backpack Ward |
| T4 | Caught theft in Hot | `ResolveTheft` skips Hot | Ward not consumed, no protection started | Live | Pass. `ward-consumed` +0 |
| C1 | Player corpse created in Hot | stock corpse rules; `CanLiftCorpseItem` skips Hot | Recorded only (stock behavior, no shard rule) | Live observation | Observed. Corpses appear at the death position in Hot |
| B10 | Ghost leaves Hot | `PlayerMobile.PositionChanged` | Exit message | Live | Pass. Exit and re-entry messages both sent |

**Run.** Driver `tests/scenarios/hot-zones/hot_consequences_live.py` on the disposable host `phase-k2`, nine fresh players and one staff session, run in stages (the theft, loot and H6 stages were rerun after harness fixes). Every pass above is from the final assertions of the stage that closed it.

**Named limits and findings.**
- **H7** is unit-tested only and **H8** is source-only: delayed damage does not re-check hostility, and Knocked Out is decided where the victim stands when the damage lands.
- **Corpse-style looting lifts nothing Newbied, Blessed or Nontransferable, and refuses any bag holding one** (as a corpse never holds them). Starter items, including the starter gold, are Newbied, so no starter pack item can be looted. Loot cases use plain items added by staff.
- **Stock Snooping and Stealing are not used for Knocked Out looting.** `Snooping.KnockedOutOpen` opens the pack and `PlayerMobile.CheckNonlocalLift` allows the lift for an eligible looter, with no skill roll, thieves guild or karma loss. Ineligible players get the stock behavior. Thieving against ordinary players (T1, T2) is unchanged.
- **Looting stacks:** a looted stackable item merges into a matching stack in the looter's pack and its serial disappears, so live checks loot a non-stacking item (Torch, Lantern).
- **Crossing by placement.** H5 moves players with staff placement rather than walking; both call the same `PositionChanged` path.
- **A Backpack Ward is single-use.** A caught theft outside Hot consumes and deletes the victim's physical Ward (`ActivateProtection`), so a victim reused across theft runs has none left and T3a cannot seed protection. The theft stage uses a victim that still carries a Ward. This was first mistaken for a death-handling loss; the server log shows the `theft ward-consumed` audit for that character, and Newbied starter items (Ward included) are kept through non-murderer death.
- **K-4 ruled 2026-09-29:** Execute needs a grey or red actor with rights on the victim's damage record (the KO's recorded attacker, or a live `DamageEntries` entry, pets credited to their master), in Hot and outside it. Blue bystanders can no longer Execute. Looting a Knocked Out player's pack in a Hot Zone is open to anyone, and a blue who takes an item becomes criminal (audit `knocked-out-loot blue-flagged-criminal`); outside Hot it still needs a grey or red with recorded rights. X3 (criminal recorded attacker outside Hot) still applies. K3 confirmed live that a red damage-record holder executes in Hot (XR).
- **K-5 and K-7 ruled 2026-09-29:** K-5 matched stock (an Execute on a victim who attacked first was no murder count; X5 covered both orders), **amended 2026-10-06: an Execute counts even then**, and the Buccaneer's Den bank polygon is removed from theft protection (17 bank envelopes remain).

## K3 login, save, restart and release-scope pass (2026-09-29)

Scope: the live reruns of the cases K-4 and K-5 changed, login and restart behavior of Knocked Out and the Hot notices, dungeon exclusion, and spawn and reward scope. Live driver `tests/scenarios/hot-zones/hot_k3_live.py` on the disposable host `phase-k3` (`hotZones` and `alpha3EnablementAcknowledged` on in the host copy only; `TestOnlyProbe` loaded for `[TestOnlyCorpseAggressors`). Fresh ordinary players plus one staff session. Phase 1 seeds state and saves once, then restarts the host; phase 2 asserts after the restart.

| ID | Behavior | Verification | Result |
| --- | --- | --- | --- |
| KO | Lethal blow to a blue in Hot | Live | Pass. Knocked Out audited, hits 1 |
| X1 | Blue bystander Executes a Knocked Out blue in Hot | Live | Pass. Refused, murder +0, victim alive |
| L1 | Blue looter takes a plain item from a Knocked Out blue's pack in Hot (pack opened before the Knock Out) | Live | Pass. `authorized` +1, looter Criminal, `blue-flagged-criminal` +1 |
| XR | Red with damage-record rights Executes in Hot | Live | Pass. Executed, murder +1 (runs a and b). The final full rerun reused a victim who had attacked first, so K-5 correctly gave murder +0 there |
| XR2 | Executor afterwards | Live | Pass. Murderer |
| X4 | Executor is in the corpse's aggressor list | Live probe | Pass. Corpse aggressors contain the executor |
| X5a | Blue attacks the red first, red Executes | Live | **Superseded 2026-10-06 (K-5 amended): the Execute now counts, murder +1; see `Murder-Report-Right-To-Attack.md`.** Originally: Pass. Damage lands, attacker stays Innocent; audit "victim aggressed first, no murder count", murder +0 |
| X5b | Grey attacks a blue first, grey Executes the never-aggressor | Live | Pass. Murder +1, Murderer |
| D1 | Blue attacks blue inside Hythloth | Live | Pass. Refused, denial audited, no damage |
| D2 | `[HotZoneStatus` inside Hythloth | Live | Pass. "outdoor Hot region: none" |
| D3 | Hot boundary message inside the dungeon | Live | Pass. None sent |
| P1 | Fire Island entry message | Live | Pass |
| P2 | Relog inside Fire Island | Live | Pass. Entry message again after login |
| P3, P5 | Players Knocked Out in Hot before the save | Live | Pass. Knocked Out audited |
| P4 | Relog inside the 90 s window | Live (functional) | Pass. Still damage-immune with hits at 1. The login-time message itself is not visible to Navrey |
| R1 | Knocked Out player, 15 s old at the restart | Live after restart | Pass. Still Knocked Out (hits 2 of 72) |
| R2 | Fire Island entry message after the restart | Live after restart | Pass |
| R3 | Player whose Knocked Out expired during the restart | Live after restart | Pass. Cleared on login, hits 37 of 72 |
| SP | Ordinary outdoor spawn cadence and rewards unchanged; no Hot hook in spawn or loot code | Source inspection | Pass. No `OutdoorHotZone` references in ModernUO spawn, creature loot or Bank/gold code |
| DZ | No dungeon Hot or Cool activation, no surface premium | Source inspection | Pass. Only `FireIsland` and `BuccaneersDenIsland` regions exist; the validator rejects `coolZones`; the K-9 Fire Island reward premium was removed from the design |

**Findings.**
- **Looting needs no setup order.** The looter opens the Knocked Out victim's pack by double-click after the Knock Out and lifts items directly (K3 cases L1, L5, L6). L5: a Newbied starter item stays. L6: a criminal without recorded rights outside Hot cannot lift.
- **Tooling.** The driver's Navrey client processes inherit stdout, so a `| tee` pipeline never returns. The driver now ends with `os._exit` and its output is redirected to a file.
- **Restart behavior.** The Knocked Out deadline is an account tag, so it survives the save. A player still inside the 90 s window at the restart stays Knocked Out on login; one whose deadline passed during the restart is cleared and woken (hits about half of max) on login. The in-memory expiry timers are not persisted, so login does this reconciliation.

## Release checks still required

The September 28 source-data check reproduced both hashes above in the workspace `UOData` directory. No separate `ModernUO/Distribution/UOData` copy was present, so this confirms the contour inputs have not changed in the workspace; it does not establish which map/tiledata files a running distribution loaded.

A disposable accepted-world Navrey session enabled only the outdoor Hot flag
with explicit Alpha 3 acknowledgment in scratch configuration. A connected
player entered Fire Island at `(4600,3500)` and received its entry warning,
returned to Britain and received its exit warning, entered Buccaneer's Den
island at `(2706,2163)` and received that entry warning, then teleported to
Hythloth's interior at `(5905,22,44)` and received only the Buccaneer's Den
exit warning. The probe restored the player's original location and staff
access; the scratch rules and probe registration were restored after shutdown.
Client evidence is `work/alpha3-housing-client/hot.log`. Source flags remain off.

The configuration validator now permits an isolated outdoor Hot rehearsal
only when `alpha3EnablementAcknowledged` is true and both named regions are
present. This does not activate Hot rules in the source configuration.

The land masks do not model static docks, ship decks, house multis, map diff patches or changed
client assets. Walk and sail the shorelines, docks, town edges and Fire Island inlets with a real
client; confirm the nearshore water margin does not expose a broad travel route. Test Hythloth's
entrance and interior separately, as well as houses, teleports, login placement, logout/restart,
combat carryover, theft, Knocked Out and Execute. Compare the deployed map
and tiledata hashes before accepting these source coordinates. Keep the feature flag disabled
until those checks and the remaining Alpha 3 release gates pass.
