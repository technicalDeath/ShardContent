# Alpha 2b release evidence

**Accepted local baseline:** 2026-09-26  
**ModernUO pin:** `9fb5448445c0a53ebb77a4ad9d72e9ec06ce8f3d`  
**ShardContent implementation:** `f9e54f3`, `283356e`, and `d38fa51`

This record covers the clean UOR/Felucca population run required by Alpha 2b. Runtime saves,
generated deployment copies, logs, accounts, and client credentials remain local and are not source
artifacts.

## Lineage and rollback

- The former authoritative world was stopped after both the listener and loaded-module checks
  proved there was no second ModernUO writer. It was preserved intact at
  `ModernUO/Distribution/WorldStateArchive/alpha2b-reset-2026-09-26-14-13-19`.
- The generation save began empty except for the existing owner account index needed to authorize
  the owner-only generation command. No prior items, mobiles, guilds, or world systems were copied
  into the new save.
- The generated world completed a controlled save, clean shutdown, restart, client reconnect,
  strict audit, convergence rerun, second save, and another restart.
- The stopped accepted `Distribution/Saves` contains 18 files / 8,358,965 bytes with latest write
  `2026-09-26T20:20:43.7585753-04:00`. SHA-256 over the sorted UTF-8 lines
  `<relative-path> <per-file-sha256>` is
  `e50a337c794b50fea4bf50283b2809b0e2ccf0e7ad00d0cf0df9a1048a7b3ea8`.
- Rollback was tested from a disposable distribution copy. The archived `Saves` loaded 175,622
  items and 34,854 mobiles, opened the game and ping listeners, and shut down normally. The
  authoritative `Distribution/Saves` was not replaced or written during this test; the disposable
  tree was removed afterward.

## Reproducible inputs

`data/world-generation/alpha2b/world-generation.json` is the source manifest.
`tools/Prepare-Alpha2bWorldData.ps1` reads stock data from the pinned Git commit rather than the
working-tree copies and writes only to the shard-specific runtime namespace. Its schema-2
`generation-report.json` records SHA-256 for all 56 selected inputs and 55 generated outputs.
Two consecutive preparations produced identical output hashes.

The accepted prepared set contains 28 decoration files, 410 Felucca signs, 353 teleporter
definitions reduced from 390 candidates to 385 canonical placements, and 1,546 canonical spawner
records reduced from 1,669 candidates. The runtime command refuses an unexpected non-empty initial
world, validates the UOR/Felucca and ModernUO pins, and writes a per-operation JSON report before it
saves.

## Exact runtime audit

The final strict post-restart audit passed with:

| Contract | Accepted result |
| --- | ---: |
| Felucca signs with exact graphic, height, and ordinary/localized label | 410 |
| Canonical generic teleporters with exact destination and multiplicity | 385 |
| Canonical spawners with unique GUID and exact location | 1,546 |
| Felucca public moongates | 9 |
| Khaldun dynamic puzzle objects | 63 |
| Britain-only service/town spawners | 64 inside Greater Britain; 0 outside |
| Champion spawns | 0 |
| Faction infrastructure | 0; Faction system disabled |
| Root objects on inactive facets | 0 |

The audit also validates every selected spawner against the explicit post-UOR exclusion list and
rejects any teleporter outside the UOR Felucca map boundary.

## Convergence defect and remediation

Instrumentation found that the first rerun after each restart recreated three stock `Campfire`
objects and four extended-graphic `SpikeTrap` objects from `_orccave.cfg`. `Campfire` deliberately
skips serialization and expires; `SpikeTrap` normalizes the extended `0x1121` graphic to stable
`0x111B` during deserialization. Earlier reruns had therefore accumulated four trap duplicates at
each of four coordinates.

The source manifest now applies two explicit, counted rewrites while preparing the alternate
decoration copy: persistent `Static 0x0DE3 (Light=Circle300)` ambient fires and stable
`SpikeTrap 0x111B` traps. A narrowly allowlisted cleanup removed the 16 accumulated duplicates.
The remediation run created the three missing persistent fires and saved; its immediate second run
created zero decorations and removed zero duplicates. After shutdown and restart, the first rerun
again created zero decorations and removed zero duplicates. Both runs retained all 63 Khaldun
objects, rebuilt only the intentionally replaceable travel/spawner/sign layers, passed the exact
audit, and saved successfully.

## Real-client release rehearsal

- Greater Britain: the mage shop exposed its buy list, a localized Reagent Shop sign rendered,
  and the public moongate displayed a Felucca-only destination list and transported the client to
  Moonglow.
- Peer-city exclusion: the client visited Minoc bank; no banker, vendor, healer, stablemaster, or
  other service NPC was present. The runtime contract independently proves that all 64 town/service
  spawners sourced from `Vendors.json` and `TownsPeople.json` are inside Greater Britain.
- Travel: a generic teleporter pair worked in both directions. A real `SmallBoat` beside the
  mainland serpent pillar responded to `doracron` and moved the client and boat from
  `(424,3283,-5)` to `(5284,2801,-5)` in the Lost Lands destination rectangle. A second real boat
  beside the reciprocal pillar responded to `sueacron` and returned to `(397,3257,-5)` in the
  mainland destination rectangle.
- Population and fixtures: an approved wilderness location produced era-reviewed ogre, ettin,
  orc, ratman, and wildlife spawns. Covetous produced slimes, spiders, a water elemental, shades,
  spectres, zombies, and skeletons. A generated Covetous metal door opened and the client crossed
  its tile.
- Death/recovery: on disposable staging, the test character was made mortal, died, entered true
  ghost state at 0/100 hits, approached the generated Britain healer, received the Resurrection
  gump, explicitly accepted it, and returned alive at 10/100 hits.

All boat creation, death, and corpse state occurred only in the disposable current-save copy. That
server was stopped and its staging tree was removed after the rehearsal.

## Automated verification

The ShardContent suite passes **108/108** after staging `Server.dll` and `UOContent.dll` beside the
test host. Coverage includes pin/era/facet validation, the exact Khaldun contract, constrained
decoration rewrites and cleanup, the fixed Greater Britain rectangle, and the Britain-only source
allowlist. `git diff --check` passes for all Alpha 2b implementation and evidence files.

## Exit decision

All five Alpha 2b exit criteria are accepted: rebuild inputs are versioned and hashed; save
lineage, sole-writer discipline, restart and rollback are proven; all generated layers pass exact
and representative client checks; immediate and post-restart reruns converge; and inactive facets,
Faction/champion content, excluded later-era spawns, and peer-city services remain absent.
