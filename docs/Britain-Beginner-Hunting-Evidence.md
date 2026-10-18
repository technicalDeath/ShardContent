# Beginner hunting around Britain (2026-10-15)

Owner, 2026-10-15: "If there is not enough hunting around Britain, you have authority to add new spawns to the config for early game monsters appropriate to the Brit region. Make sure they are added as configs (so they are preserved across new shard deployments)."

## Why

The bot farm (`Bot-Farm-QoL-Findings.md`) showed new fighters, archers and mages walking 200-320 tiles from Britain before they met anything to fight, then dying to what they met there. A survey of the generated spawn data confirmed it: Felucca has **no wild spawner within 140 tiles of Britain**. Inside that ring there are only town animals (cats, dogs, birds, horses, cows). The nearest monsters (the graveyard's spectres, wraiths and zombies, the orc, troll and ettin camps east and north-east, gargoyles and gazers) are beyond a character with 77 hit points and starting gear. Stock `WildLife.json` and `Outdoors.json` have nothing in Britain's own woods and fields.

## What was added

`data/world-generation/alpha2b/britain-beginner-hunting.json`, a new shard spawn file listed in the manifest's `customSpawnerFiles` (stock spawn data is not touched). Every deploy (`Deploy-Alpha1Baseline.ps1` → `Prepare-Alpha2bWorldData.ps1`) carries it into `Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/`. A new world gets the spawners from `[Alpha2bWorldGen apply`; a world in use gets them from `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` (after a `Saves` snapshot). Each spawner has a fixed GUID (a name-based UUID, so the same ids come out every time), respawns every 5 to 10 minutes and sits on a tile that a walking client reached from town (`tests/scenarios/bot-farm/spawn_site_probe.py`; the z values are where the probe ended up).

| Spawner | Where (x, y, z) | Creatures (most at once) | Count | Range |
| --- | --- | --- | --- | --- |
| Castle woods (was North fields, 1519, 1531) | 1240, 1600, 0 | Rabbit 3, Hind 2, Mongbat 2, GiantRat 2, Ratman 1 | 9 | 20 |
| Farm vermin (was 1301, 1760) | 1265, 1770, 0 | GiantRat 3, Snake 2, Slime 2, Ratman 2 | 7 | 15 |
| West woods edge | 1250, 1701, 0 | Rabbit 3, Hind 2, GreatHart 2, Eagle 1, Orc 1 | 9 | 25 |
| West woods | 1191, 1780, 3 | GreyWolf 2, GreatHart 2, BlackBear 1, Hind 1, Orc 2, OrcishMage 1, GreaterMongbat 1 | 8 | 25 |
| South-west forest (was 1329, 1849) | 1340, 1868, 0 | HeadlessOne 2, Mongbat 2, Slime 1, Lizardman 2, Ratman 1, GreaterMongbat 1 | 8 | 20 |
| Old bones | 1301, 1869, 0 | Skeleton 2, Zombie 2, HeadlessOne 1 | 4 | 15 |

45 creatures at most, easy to harder: animals and vermin north and west of the city, wolves, harts, a bear and a few orcs in the west woods, lizardmen and ratmen in the south-west forest, and a few weak undead (no spectres or wraiths) beside it.

**What counts as beginner:** creatures with at most about 60 hit points that hit for at most about 10 (the classes' `SetHits` / `SetDamage`): Rabbit 4-6 hp, Mongbat 4-6, Snake 15-19, Slime 15-19, Hind 15-29, HeadlessOne 16-30, Eagle 20-27, GiantRat 26-39, GreatHart 27-41, Zombie 28-42, GreyWolf 34-48, Skeleton 34-48, BlackBear 46-60.

**Step-up creatures** (the owner, the same day: "you can also sprinkle in mongbats, ratmen and lizardmen, and the weaker orc variants"): Ratman 58-72 hp hitting for 4-5, Lizardman and Orc 58-72 hitting for 5-7, GreaterMongbat 34-48 hitting for 5-7, and one Orcish Mage (70-90, casts) in the west woods, the farthest site. They are a minority of what can spawn at every site. Left out as too strong for a beginner: the Ratman archer and mage (88-108 hp) and the Orcish Lord (95-123); the Orc Captain, Brute and Bomber are post-UOR and on the manifest's excluded list anyway.

All of these exist in UO:R, and none is on the manifest's excluded list.

**Where:** all inside Britain's TownRegion rectangles (`Data/regions.json`), which take in the woods and fields around the city, on Felucca, and at least 60 tiles from the town centre (1470, 1620), so nothing spawns among the bank, the healer and the shops. The sites are placed so a new player walks out to hunt, not so the hunt walks in.

## Tests

`tests/BritainBeginnerHuntingSpawnTests.cs` (7): only the beginner and step-up sets are spawned; step-up creatures are under half of what can spawn at every site, with at most one Orcish Mage; every spawner is in Britain's region on Felucca; every spawner is 60 or more tiles from the town centre; GUIDs (also against the vendor overrides) and places are unique; no type is on the era's excluded list; the file is listed in the manifest. With `BritainGuildmasterSpawnTests` and `Alpha2bWorldGenerationConfigurationTests`: 28 passed.

## Deploy and world

| # | Step | Result |
| --- | --- | --- |
| 1 | `Deploy-Alpha1Baseline.ps1` to dev (`ModernUO/Distribution`; dev server stopped) | Spawners: 1,557 canonical records (was 1,551); report 59 inputs, 57 outputs |
| 2 | Farm host (`work/hosts/farm`, the running bot-farm server): its manifest gained the file (its own pin, 4fbc58cfb, kept) and the spawn file was copied in; no DLL touched, no restart (`[Alpha2bWorldGen` reloads the manifest each call) | `[Alpha2bWorldGen audit` before: failed, spawners exact 1,551/1,557 (the six new ones missing, nothing else) |
| 3 | Snapshot of the farm `Saves` just after the 04:40:00 autosave: `work/save-snapshots/farm-saves-20261015-044005-before-beginner-hunting` | 8.6 MB |
| 4 | `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA` on the farm (04:40:13, from `tests/scenarios/bot-farm/farm_staff.py`, a lean admin client) | "adding ..." for each of the six sites; "added 6 spawners and replaced 0 stale ones"; "every canonical spawner is now in the world. Saved."; audit passed: 410 signs, 385 teleporters, 1,557 spawners, 1,345 doors, 9 moongates, 63 Khaldun items. The server logged `Writing world save snapshot done` at 04:40:20 |
| 5 | Each site visited by the admin (`farm_staff.py "[go x y z" --look 22`) at 04:42, and asked of the server (`[global get Name where BaseCreature Home.X = x Home.Y = y`) at 04:46 | North fields: hinds, rabbits, a mongbat. West woods edge: a great hart, rabbits, an eagle. West woods: 2 great harts, 2 grey wolves, a black bear, a hind. Farm, south-west forest and old bones: empty or one creature left |
| 6 | Why some sites were empty: the bots' own logs and the server's corpse-loot audit lines | The spawners fill at creation (`Respawn()`), and the farm's hunters were on them within a minute: from 04:40:57 fighters looted mongbat, headless and slime corpses at the new sites (BotFairSwordV, BotMaceC), and casters and bards looted new serials (0xB5CB-0xB604). About 30 hunters clear a site faster than one creature per 5-10 minutes refills it |

The dev world (`ModernUO/Distribution/Saves`) gets the spawners with `addspawners` on its next start, after a `Saves` snapshot (the farm holds port 2593 now).

**Open:** the respawn rate. Each spawner adds one creature per tick (5 to 10 minutes) until it is full, so the six give about 50 creatures an hour in all. That is plenty for a handful of new players and thin for the farm's 30 hunters; the bot-farm watcher's kill counts by kind decide whether the delays come down.

## Moved out of the guard zone (2026-10-16)

The owner ruled that monsters should not spawn inside a guard zone, which shrinks only where no vendor stands (`Town-Guards-Monsters-Evidence.md`). The north fields spawner stood among the north stables and the farm vermin spawner under a thatch roof beside the south-west animal trainer, so both moved into the new unguarded Britain Outskirts west of the castle; the south-west forest spawner moved from 1329,1849 to 1340,1868 so its range stays south of the south-west houses. Every spawner's home square now lies in Britain Outskirts (`TownGuardsTests`). The dev world has none of them yet; the farm host keeps the old spots until its spawners are replaced.
