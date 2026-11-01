# Cove spawn areas, and monsters spread into groups of three

Signed off by the owner on 2026-10-19 ("Signed off. Build the Britain split and the Cove plan, test on the farm, and show me real-client shots before deploying"). The map page with both plans as tabs is the spawn-plan artifact, built by `tools/spawn-design/make_page.py tools/spawn-design/plans.json`.

## What the owner asked for

- "Take the center point ... and do the same concentric circle spawn plan from that point out like you did from Britain, where they collide, the britain plan should win", then "this should have been for Cove".
- "The orc fort can be even tougher as an outlier. put easy orcs in the front half of the fort, and harder orcs in the rear. if there are more varied types of orcs, include them."
- "pull them in (make the center ring smaller), the lands full of just animals are too big to the east."
- "Rather than spawns with '7 max' for example, have 3 spawns with 3 max and 1 with 1 max ... Do the same for britain", "this should only apply to step-up, dangerous and deadly", and "I don't want them 'within 10 tiles' i want them spread out over the area more."

## The design

- **Centre and rings.** Cove's town (2243, 1178). Cove's rings are smaller than Britain's: the Doorstep is beginner within about 180 tiles, the Near wilds step-up to 280, the Far wilds dangerous to 400, and the Frontier lies beyond (`ringEdges` and `rings` in `areas-cove.json`; Britain keeps 300 / 400 / 500).
- **Britain wins.** Every spawner and every new site inside Britain's plan rectangle (1000-2000 x 1250-2050) is left to Britain's plan (`britainWins`). The Cove file comes just before Britain's in `customSpawnerFiles`, so Britain's records win on any shared GUID or place. There are none.
- **The orc fort.** The north gate faces Cove. The front half (y < 1372) is the Orc Fort Gate: plain orcs, step-up. The rear half is the Orc Fort Keep: orcish lords and mages with a few orcs, dangerous, 16 at once on two spawners (one new). The keep is a ring exception and keeps its packs (`cluster`). Orc, orcish lord and orcish mage are all the orcs of the era: the orc captain, bomber and brute are later and stay in `excludedSpawnerTypes`.
- **The east.** The open plain east of Cove escalates in bands:
  - Cove East Plains: deer and small game, beginner.
  - Ratman Plains: ratmen, step-up, three new spawners.
  - Troll Plains: trolls, ettins and ogres, dangerous, three new.
  - East Coast Forest: deep-forest creatures, dangerous, two new.
- **Spread into groups of three** (`split_sites.py`, both plans):
  - Which spawners: every step-up, dangerous or deadly themed spawner holding more than 3 becomes groups of at most 3 (7 becomes 3, 3 and 1). Beginner areas, the wildlife and the orc keep keep their spawners whole.
  - Where the groups go: the first group keeps the spawner's GUID and spot. Each other group goes to the emptiest walkable spot left in the area (farthest-point choice). Such a spot is off roads, outside the guard zones, at least 16 tiles from any other spawner (8 in a cramped area) and never nearer the centre than its grade allows.
  - How far they roam: each group roams half way to its nearest neighbouring spawner, 10 to 30 tiles.
  - Totals are unchanged. Britain has 47 spawners in 110 groups, Cove 31 in 81.
- **Wildlife and flavor**, as in Britain:
  - Wildlife: 23 stock wildlife spawners take ring rosters, and 15 new forest sites are added. The 9 sites that fell inside Britain's plan were dropped.
  - Flavor: 503 single flavor pieces go into the map's statics (`data/map-patches/cove-flavor-statics.json`). They are placed from the pristine map, none blocks, and each is at least 10 tiles from any other piece and from Britain's. The graveyards and the orc fort get none.

## Files

| File | What |
| --- | --- |
| `data/world-generation/alpha2b/cove-spawn-areas.json` | 148 records, listed before `greater-britain-spawn-areas.json` |
| `data/world-generation/alpha2b/greater-britain-spawn-areas.json` | 102 → 167 records: every earlier GUID kept, 65 new split groups |
| `data/map-patches/cove-flavor-statics.json` | 503 flavor pieces |
| `tools/spawn-design/areas-cove.json`, `split_sites.py`, `plan.py` (`ringEdges`, area `homeRange`, `--splits`, `britainWins` for new sites), `build_data.py` (output name), `make_page.py`, `page-template.html`, `plans.json` | the pipeline |
| `tests/CoveSpawnAreasTests.cs`, `tests/GreaterBritainSpawnAreasTests.cs` | manifest order, unique GUIDs and places and none of Britain's, no post-era creature, nothing dangerous within 180 tiles of Cove, the fort halves, at most 3 per step-up+ spawner, flavor in era, not player items, not blocking, spread |

The pipeline for one plan:
1. `census.py`.
2. `plan.py` without splits.
3. `split_sites.py`.
4. `plan.py --splits`.
5. `build_data.py`.
6. `place_flavor.py --patch`, with `UO_ROOT=work/uodata-pristine-full`.
7. `make_page.py`.

The map files for clients: `apply_statics_patch.py work/uodata-pristine OUT greater-britain-flavor-statics.json cove-flavor-statics.json` (948 pieces).

## Tests

- 2026-10-19: 1,718 passed. A scratch copy was used because another session's uncommitted `NewPlayerTipsService.cs` needs an engine hook that isn't built yet. The 40 failures there are tests that find ModernUO by a relative path the scratch copy lacks. All 33 spawn and world-generation tests pass.

## Added on 2026-10-20 (owner requests during the build)

- **Wandering healers** (`pick_extras.py`): one per Greater Britain area, 21 in all, each roaming 20 tiles, on walkable ground outside the guard zones, never within 60 tiles of another (nearest pair 124). The stock wildlife mix had them; the themed rosters had dropped them.
- **Wild horses**: in each of the eight directions from the bank, the wildlife spawner at the middle distance gets a horse. East, where the bay leaves no wildlife spawner, gets a new wildlife site at 1748, 1561. Greater Britain's file is now 189 records.
- **Roadside clearing (experiment, the owner's map comment)**: `tools/map-patch/clear_road_edges.py` takes out every natural map static that stock house placement refuses (impassable, or a surface that isn't background), with its leaves. It works within 10 tiles of the roads in the Britain Outskirts south strip (x 1288-1416, y 1841-1907): 270 statics, 138 trees.
  - Logs, rocks, brambles and grass don't block a house and stay. One post is the only man-made blocker, and it stays.
  - `apply_statics_patch.py` now takes a patch's `remove` list.
  - The patch is in `work/road-clearing/` and the test map folder is `work/uodata-roadtest`. Neither the workspace UOData nor any server reads them yet.
- **Map page**: a name search in the map options shows only the spawners holding a creature, or with a label, that matches (for example horse, troll, healer). Britain's map image is drawn from the proposed map, and the clearing is shown as a dashed strip with a cross per tree.
- Tests: 35 of 35 spawn and world-generation tests pass, including healers 60+ apart with range 20, and horses in all eight directions.

## Farm test

- The farm Saves snapshot (Operator): `work/save-snapshots/farm-saves-20261019-221302-before-cove-split`.
- `Prepare-Alpha2bWorldData -OutputDistributionPath work\hostsarm`: 1,744 canonical spawner records.
- 2026-10-19 22:41, after the owner had his dev server stopped. The 22:40 autosave was complete first.
  - `addspawners` added 289 spawners and replaced 128 stale ones. The audit passed with 1,744 spawners, and that state is saved.
- House-placement survey of the roadside strip (`[HousingSurvey run 1288 1841 1416 1907 0 2`, small house, 2,210 centres):
  - Today's map: 0 valid; refused for region 2,114, for land 13, for statics 83.
  - Cleared map (the farm's `dataDirectories` pointed at `work/uodata-roadtest` for the test, then restored to md5 631C7CA0): 0 valid; region 2,114, land 14, statics 82.
  - The strip lies inside Britain's town region (only the guards are off there), where stock rules allow no house. So the clearing changes the look but opens no lot there.
- Real client (character RoadEye on the farm):
  - The strip at 1356, 1875 before and after: the trees are gone, and grass, rocks and logs remain.
  - The orc fort gate holds plain orcs and the keep holds orcish lords.
  - Shots are in `work/player-client/RoadEye/shots/`.

## Dev deploy, 2026-10-19 23:16 (owner: "Deploy to dev")

- Snapshot: `work/save-snapshots/saves-20261019-231612-before-cove-split`, 18 of 18 files, taken after the dev save of 22:40.
- `Prepare-Alpha2bWorldData` wrote the world data into the dev distribution. This was data only: `Deploy-Alpha1Baseline` can't build right now, because another session's uncommitted `NewPlayerTipsService.cs` needs an engine hook that isn't built.
- `addspawners` and the audit passed with 1,744 spawners. The world saved, and the dev server is stopped.
- Not deployed yet: the Cove flavor pieces and the roadside clearing. Both are map statics and need a UOData swap plus the player map files.

## Houses in the Britain Outskirts (owner's ruling, 2026-10-20: "Let houses in the Outskirts")

- `townGuards.unguardedAreas` entries take `allowHousing`, which is true for the Britain Outskirts only.
  - Such an area is registered as a plain `BaseRegion` instead of a `NoHousingRegion`, so stock house placement's region rule passes there.
  - The Moonglow Zoo stays no-housing.
  - `[TownGuardStatus` says which areas allow houses.
  - Test: `TownGuardsTests.HousesAreAllowedInTheBritainOutskirtsOnly`.
- Disposable host survey of the strip (small house, 2,210 centres, step 2):

| Map | Valid centres | Region | Land | Statics |
| --- | --- | --- | --- | --- |
| Today's map | 116 | 130 | 260 | 1,704 |
| Roadside clearing | 441 | 130 | 337 | 1,302 |

  The 130 refused for region are centres whose footprint reaches into Britain's guarded town.
- Not deployed:
  - The shard DLL can't be built in the workspace until the new-player tips work gets its engine hook, so the test host ran a DLL built from a scratch copy.
  - This reverses the stock no-houses-in-town rule for this one area, so the README rules need a line when it goes live.
