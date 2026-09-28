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
