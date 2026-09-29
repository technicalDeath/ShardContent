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

Not covered by these checks: house multis (Beta 2 zoning), ship decks (dynamic, see B8), and any client asset changes after the hashes above.

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
