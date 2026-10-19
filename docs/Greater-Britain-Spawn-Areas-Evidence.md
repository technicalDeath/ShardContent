# Greater Britain spawn areas, wildlife and flavor objects (2026-10-18)

Owner, 2026-10-18, as Rekindled Spawn Designer's brief: plan and carry out what spawns where. Signed off the same day ("Build the spawns, wildlife and decoration, test on a disposable host, and show me real-client shots before deploying"). **Spawns, wildlife and single flavor objects built and tested on a disposable host; deployed to dev on 2026-10-18 (not the farm), not committed. The composed scenery was dropped after the shots and replaced by single flavor objects (below).**

The plan was worked out on a map artifact (https://claude.ai/artifact/CoKFguHjeXRUAEgAizSPAm, version 9) with the owner's comments on it.

## The owner's rules

1. A spawner is graded by its most dangerous spawn, passive or not.
2. Danger is least near Britain and rises in rings going out (from the bank, 1470,1620): Doorstep (inside about 300 tiles, tier 1), Near wilds (to about 400, tier 2), Far wilds (tier 3), Frontier (500 and beyond, tier 4).
3. Spawns are thematically coherent. He met an ettin, an orc, mongbats and a reaper together: the stock Outdoors mix at 1640,1431 (Corpser, DireWolf, Ettin, Ogre, Reaper, Skeleton, Zombie) beside a Mongbat/Orc spawner.
4. Areas of several spawners, not single spawners, hold a theme, and the themes escalate going out.
5. Random wildlife stays among the forests.
6. (Dropped, see Scenery.) Each area gets a light decoration theme that goes with its spawns. Nothing that is also a player item (feathers were his example). Multi-piece art goes down whole. Scenery keeps off places that are already decorated (the Britain Graveyard gets none). Farm scenery blends in beside the farms' own buildings and fields.

Map comments, all applied: the strip of woods by the bay is beginner ("Bay Woods"); the land just north of the graveyard extends its undead with two step-up undead ("Barrow Fields", a ring exception on his ruling); west of the mountains is tier 3 ("West Mountain Woods"), and the east part joins the South-west Farmlands.

## Tiers

0 harmless, 1 beginner (up to about 60 hit points and 10 a hit), 2 step-up (60-75 hit points, or poison), 3 dangerous (75-130 hit points, or casts), 4 deadly. Calls from the bot farm's fights (`work/botfarm-watch/creature-danger.md`):
- Orc, ratman, lizardman, harpy, greater mongbat are step-up.
- Ettin, corpser, reaper, dire wolf, grizzly bear, skeletal and bone knights are dangerous, not deadly.
- The weak undead casters (shade, spectre, wraith, bone mage, skeletal mage) are step-up. Shades won 28% of 80 fights and killed bots in 23%, about the same as orcs (20% / 28%) and ratmen (22% / 26%).

`tools/spawn-design/census.py` has the table.

## The areas

21 areas (`tools/spawn-design/areas.json`). Tier 1: Britain Graveyard (lesser dead), North Fields (wolf meadow), Castle Woods and Bay Woods (deer and small game), South-west Farmlands (farm vermin and livestock), North-east Pasture (horses and game for tamers). Tier 2: Barrow Fields (spectres, wraiths and lesser dead; owner's exception at about 255 tiles), West Foothills and South Road (ratman warrens), North Hills (orc band), Bay Marsh (lizardmen), North-east Woods (woodland predators). Tier 3: Troll Hills and East Shore (hill giants), Gargoyle Heights, Harpy Crags, Far North-east Forest, South Woods and West Mountain Woods (deep forest), Haunted Wood (armoured and greater undead). Tier 4: Wisp Glade. The sea and the farms' cats, dogs and chickens are left as they were.

**Wildlife.** The 19 stock WildLife spawners stay wildlife, each with its ring's roster and never graded above the area it stands in. Doorstep: rabbits, hinds, harts, birds, eagles, boars, goats. Near wilds: those plus wolves, black and brown bears, cougars and panthers. Far wilds: grizzlies too. 24 new forest sites (`place_wildlife.py`) fill woods with no wildlife spawner within 70 tiles: walkable, at least 25 trees within 12 tiles, outside the guard zones.

## Scenery: dropped

Light scenery was planned and built beside each themed spawner: 58 small scenes, 439 plain statics. The owner saw the real-client shots and dropped it the same day:

> "I actually think most of the scenes look pretty bad. object placement doesn't seem logical, there's debri on top of a log, random fence piece looks bad."

What went wrong:
- The pieces were placed by a rule-based script (anchor, then supports and accents on the nearest free offsets). Nobody reasoned about each scene the way `world-decorating` requires.
- Its "free ground" test only excluded man-made statics. The map's own fallen logs, rocks and plants counted as free, so debris landed on a log.
- A lone fence section with nothing to fence is an orphan.

What stays useful from it, kept in `tools/spawn-design`:
- `check_deco.py` and `deco.json`'s `allowed` list: art that is also a player item.
- `assemblies.py`: multi-piece objects learned from the map.
- `builtmask.py`: places already decorated.

Any future scenery should be composed by hand per scene in the decorating rig and judged by eye before it is proposed.

## Flavor objects (replaces the scenery)

The owner, the same day:

> "instead of 'scenery' we can just do individual object placement. small items like mushrooms, a nest, spilled hay, things that on their own help give flavor to the different areas, don't require other items to be around, and not trying to compose a scene."

`place_flavor.py` scatters single pieces from each theme's standalone list (`deco.json` `flavor`), writing `greater-britain-flavor.cfg`.
- **What goes where:** mushrooms and nests in the woods, spilled hay and splintered wood on the farms, bones, grave mounds and a gravestone at the barrows and the Haunted Wood, cattails in the marsh, rocks on the heights.
- **How many:** about one per 900 tiles of area, at least 14 tiles apart. 316 pieces in 20 areas; the graveyard opts out.
- **Clean ground:** walkable, flat, off roads, outside the guard zones, 6 tiles from anything built or decorated. No map art on the tile or beside it, and nothing tall within 3 tiles.
- **Two rounds of shots.** The first (416 pieces) showed pieces hidden behind tree trunks, plus mud, barrel staves and jaw bones too small to read. Those three were cut and the clear-sightline rule added.
- `check_deco.py`: 80 pieces, none a player item, none multi-piece.

On a fresh host: `adddecorations` placed 316, then 0 on a second run; the audit passed, 1,583 spawners. Real-client shots in `work/spawn-design/flavor-shots/` (scratch): every piece in the open and readable; at play size they read as light, natural touches.

## Files

| File | What |
| --- | --- |
| `data/world-generation/alpha2b/greater-britain-spawn-areas.json` | 102 spawner records: 76 re-themed by GUID at their own places, 26 new (fixed name-based GUIDs). Last in `customSpawnerFiles`, so it wins |
| `data/world-generation/alpha2b/greater-britain-flavor.cfg` | 316 single flavor objects, in `customDecorationFiles` |
| `src/.../Alpha2bWorldGenerationCommands.cs` | A spawner is exact only if its count and creature list also match (`IsExact`, `SpawnsAsDefined`), so `addspawners` replaces re-themed ones; `adddecorations CONFIRM-UOR-FELUCCA` places the shard's own decoration files in a world in use (idempotent) |
| `tests/GreaterBritainSpawnAreasTests.cs` | Manifest order, unique GUIDs and places, no post-era creature, nothing dangerous inside 300 tiles, counts can fill, flavor pieces in era, never a player item, at least 14 tiles apart |
| `tools/spawn-design/` | census, plan, wildlife and scene placement, checks, the map page generator |

Canonical spawners: 1,557 → 1,583. Preparation report: 61 inputs, 59 outputs.

## Tests

- Full shard suite (isolated runner): 1,705 passed, 0 failed (`work/agent-verification/runs/20261018T132138096Z-f0ec28`).

## Disposable host `spawn-areas` (copy of the dev world, new build)

| # | Step | Result |
| --- | --- | --- |
| 1 | `[Alpha2bWorldGen audit` before | Failed as expected: spawners exact 1,481/1,583 (the dev world's 1,557 less the 76 re-themed; the 26 new missing). No other drift |
| 2 | `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` | Added 102, replaced 76 stale; audit passed: 410 signs, 385 teleporters, 1,583 spawners, 1,345 doors, 9 moongates, 63 Khaldun items |
| 3 | (scenery, since dropped) `[Alpha2bWorldGen adddecorations CONFIRM-UOR-FELUCCA` twice | First run: scenery placed 439 (Felucca root items 28,086 → 28,525), bounty board 0 placed, 2 already there. Second run: 0 placed |
| 4 | Audit after | Passed, 1,583 spawners |
| 5 | Creatures at sites (`[global get Name where BaseCreature Home...`) | 1640,1431 (was the ettin/reaper/orc mix): horse, goat, boar, great hart, hind, cow, rabbit. Graveyard: zombies, skeletons, headless ones. Barrow Fields 1361,1392: spectres, a wraith, a zombie, a skeleton. West Mountain Woods 1038,1728: grizzlies, giant spiders, a reaper, a corpser. Wildlife 1428,1470 and 1229,1655: deer, rabbits, boars, goats, eagles, birds |
| 6 | Real-client shots | 15 scenery shots; the owner judged them bad and dropped the scenery. They also show the new spawns in place (a skeleton by the Haunted Wood spawner, a gargoyle in Gargoyle Heights, a lizardman and black bear by the Bay Marsh, a cougar and black bear in the North-east Woods). Kept in `work/spawn-design/shots/` (scratch) |

## To deploy (owner's word needed)

1. Snapshot the dev `Saves`.
2. `Deploy-Alpha1Baseline.ps1`. The world-gen command change is shard code; no engine change.
3. Start the server, then run `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` and `[Alpha2bWorldGen adddecorations CONFIRM-UOR-FELUCCA`.
4. The farm host the same way, if wanted.

`BritainBeginnerHuntingSpawnTests` still describes the 2026-10-15 beginner file. The areas file now re-themes those six sites: the step-up creatures moved to neighbouring areas, by the owner's rule 1.

## Dev deploy (2026-10-18, owner: "Deploy all of it to dev")

Snapshot `work/save-snapshots/saves-20261018-103618-before-spawn-areas-season` (18 files, 8.3 MB). `Deploy-Alpha1Baseline.ps1` (it also carried another session's sell-price tooltips with `sellPriceTooltips` on; the owner chose to include it). On the started dev server: audit before 1,481/1,583 exact; `addspawners` added 102 and replaced 76; `adddecorations` placed 316 flavor objects (bounty board already in place); audit passed (410 signs, 385 teleporters, 1,583 spawners, 1,345 doors, 9 moongates, 63 Khaldun items); `[SeasonStatus` summer; both saves logged `Writing world save snapshot done`. README rules updated. The farm host still has the old spawns.

## Colour pieces (2026-10-18, owner: "add some additional items with more color ... the pallets are very monotone")

Each theme gained a `color` list in `deco.json`:
- pink campion and foxglove, orange orfluer, red and white poppies, white snowdrops and white flowers, scattered petals and bulrushes;
- red-capped mushrooms, chosen per area (pasture flowers in the pasture, snowdrops at the barrows and the Haunted Wood, bulrushes in the marsh, red-caps in the deep forest and the wisp glade).

`check_deco.py` passes all 102 pieces. The wildflower art the later-era plant system shares is allowed, and the bladed-tool mushrooms (0x0D15, 0x0D16) and the mushroom trap (0x1125, 0x1126) were left out.

`place_flavor.py` keeps the 316 deployed pieces byte for byte and adds 129 colour pieces on new sites, at least 10 tiles from every piece: 445 in all. Generating them showed that `builtmask.py` counted the deployed flavor file as "already decorated", so it now leaves that file out.

On the host, `adddecorations` placed 129 and left the 316 already there. Real-client shots in `work/spawn-design/color-shots/`. The map's dots take each piece's colour (`make_page.py` `main_colour`).

**Deployed to dev** the same day on the owner's word. Snapshot `work/save-snapshots/saves-20261018-115235-before-colour-flavor`, then `Deploy-Alpha1Baseline.ps1`. `adddecorations` placed 129 and left the 316 already there. The audit passed (1,583 spawners), `[SeasonStatus` reads summer, and the save completed.

## Farm host (2026-10-18, by the BotFarm Operator session)

The BotFarm Operator copied the new DLL, config, spawn file and flavor file to `work/hosts/farm` after a Saves snapshot. It then ran `addspawners` (102 added, 76 replaced) and `adddecorations` (all 445 flavor pieces). The audit passed with 1,583 spawners, and the save was logged done at 11:58:32. It regenerated the bots' hunt, tame and hard spots, added `britain_areas.json`, and cleared the bots' learned place memory inside the areas. The dev server was restarted afterwards on the owner's choice.
