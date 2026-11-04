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

## Map statics rollout plan (2026-11-01, owner: "Plan it first")

**What changes.** Four map files: `statics0.mul`, `staidx0.mul`, `statics0x.mul` and `staidx0x.mul`.
- They are built from the pristine originals (`work/uodata-pristine`) with three patches:
  - Greater Britain flavor: 445 pieces, live since 2026-10-19.
  - Cove flavor: 503 pieces.
  - The Britain Outskirts roadside clearing: 270 statics removed.
- `apply_statics_patch.py`: 948 of 948 added, 270 of 270 removed, in both the plain and the x pair.
- Built copies: `work/map-statics-20261101/statics`. A full client data folder that hard-links every other file: `work/map-statics-20261101/uodata`.

**Who reads them.** The dev server, the farm server (both `dataDirectories` = the workspace `UOData`), the player client (`ClassicUO/bin/dist/settings*.json` `ultimaonlinedirectory` = `UOData`) and every Navrey bot client.

**Real-client check** (character RoadEye, client on the built folder, 2026-11-01): shots in `work/player-client/RoadEye/shots/20261101-*`.
- East of Cove's wall: rocks, pebbles and a mushroom, drawn as map art.
- The Outskirts strip at 1356, 1875: the trees and their leaves are gone. Grass, rocks, logs and brambles stay, as on 2026-10-20. The faint grey shapes are the map's own rocks that the trees hid; they are in the 2026-10-19 "before" shot too.

**Rollout, in one window:**
1. Stop the farm (supervisor, every bot client, the farm server) and the dev server. Nothing may hold `UOData`.
2. Snapshot the dev and farm saves, and copy the four current `UOData` files to `work/uodata-before-20261101`.
3. Copy the four built files into `UOData`, and check the hashes.
4. Start dev, then `[Alpha2bWorldGen audit`, then save and stop. Start the farm and restart its bots.
5. Players' files: put the four files in `work/client-release/map-patch` with a README of checksums, as on 2026-10-19. Shipping them with the client download is the owner's step.
6. Add a README rules line: houses can now fit along the cleared Outskirts road.

**Roll back:** stop as in step 1, then copy the four files back from `work/uodata-before-20261101`.

**Not checked:** walking through the cleared strip with the patched server. The server reads the same files after the swap, and stock house placement over the strip was surveyed on 2026-10-20 (441 valid centres against 116).

## Fewer ettins by Covetous, 2026-11-03

**The owner's ruling:** "There is a large group of ettins nearby the entrance in the grove. Bots will need to quickly run past them. In fact, there are too many there. Modify the spawn so there are less ettins (half of what there are today)." The same message chose Covetous as the bot ladder's dungeon ("I ran to Covetous with no problem yesterday").

**What was there.** On the farm world, 25 ettins stood between x 2200-2750 and y 600-1100. They came from the 30 hill-giant camps of the `troll-hills` theme:
- 24 in Minoc South Hills, north of Covetous;
- 6 in Troll Plains, south-east of the main entrance, the nearest at 2548,946.

Each camp is Troll 1, Ettin 1, Ogre 1, with a count of 2 or 3, so it holds at most one ettin. No other spawner near Covetous holds ettins. The stock Spawner (213) at 2349,722 holds 1 creature.

**The change.** In `data/world-generation/alpha2b/cove-spawn-areas.json`:
- Every other camp in map order (y, then x) lost its Ettin entry. That's 15 of 30: 12 in Minoc South Hills, 3 in Troll Plains.
- Each changed camp's count was capped at the kinds it has left, which took 12 counts from 3 to 2. The trolls and ogres stay as they were.
- The rule is noted on both areas in `tools/spawn-design/areas-cove.json` (`ettinsHalved`), so a rebuild from the plan can apply it again.
- Script: the scratchpad's `halve_ettins.py`, whose rule is the one stated here.

**Checks.** A Python check of the test rules this change could touch: all 148 spawners can fill their counts, and GUIDs and places are unchanged. The C# test run was blocked by another session's uncommitted build break (`ActionProgressBars.cs` needs engine hooks that aren't built).

**Farm world, 10:05:**
1. Saves snapshot: `work/save-snapshots/farm-saves-20261103-100457-before-ettins-halved`.
2. The new file copied into `work/hosts/farm` (backup `.bak-20261103-before-ettins`).
3. `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` added the 15 changed camps and replaced their 15 stale ones.
4. The audit passed: 1,744 spawners.
5. Ettins in the box after: 15. Trolls: 29. Ogres: 26.

**Dev world:**
- The file is in the dev distribution's data (backup `.bak-20261103-before-ettins`).
- The dev world itself still has the old camps. When the dev server next runs, it needs `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` after a Saves snapshot.
- Dev can't run while the farm holds port 2593.

## Fewer trolls at Despise's door, 2026-11-04

**The owner's ruling:** "Halve the trolls", for the troll camp at Despise's door. The same morning he made Despise the bots' beginner dungeon again ("Despise is probably the better beginner dungeon to send bots to").

**What was there.** One stock spawner, `Outdoors.json` Spawner (213) at 1325,1071: 10 trolls, home range 30, 29 tiles from the door at 1296,1081. It is the only spawner within 45 tiles of the door. Two bots met it there:
- BotHealAdvR's first Despise trip (2026-11-02) was boxed in by seven trolls.
- BotWarAdvR, on foot (2026-11-04 10:44-10:56), took three escapes on the way in and was boxed in by four trolls on the way out. Its lowest was 35/90.

**The change.** `data/world-generation/alpha2b/despise-door-trolls.json` holds one spawner:
- It has the stock spawner's guid (`409e129c-f95e-4a05-aff8-e2d577aede77`) and place, so the generator's rule (one spawner per guid and per place, later files win) replaces the stock one.
- Its count and the Troll entry's maxCount are both 5. Everything else is unchanged.
- It is listed in `customSpawnerFiles` before `cove-spawn-areas.json`.
- `tests/DespiseDoorTrollsTests.cs` pins it: the guid, the place, the count, and that no other custom file takes them. With the Cove, Greater Britain, beginner and world-generation tests, 37 pass.

**Farm world, 15:11:**
1. Saves snapshot: `work/save-snapshots/farm-saves-20261104-151006-before-despise-trolls`.
2. The file copied into `work/hosts/farm`, and its manifest line added (backup `.bak-20261104-before-despise-trolls`).
3. `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` added the camp and replaced the stale one. The old camp's trolls went with it (`BaseSpawner.OnDelete` removes its spawns).
4. The audit passed: 1,744 spawners.

**Dev world:**
- The file and the manifest line are in the dev distribution's data (backup `.bak-20261104-before-despise-trolls`).
- The dev world itself still has the 10-troll camp. When the dev server next runs, it needs `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` after a Saves snapshot.
