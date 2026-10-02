# Beta 2a item 3: Hythloth joins the permanent Hot Zones (audit)

Roadmap: [Beta 2a](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 3 ("Permanent Hythloth Hot Dungeon", renamed by the ruling below). Design contract: Hot Zones plan §20.1, §20.11-20.13, as ruled below. Outdoor Hot Zone rulings: [Contract Review K-1 to K-10](Alpha-3-Contract-Review.md).

## Sign-off (owner, 2026-10-02)
Do not reopen.
- **Hythloth is not a "Hot Dungeon".** It simply follows the permanent Hot Zone rules, like Fire Island and Buccaneer's Den island, and gets none of the Hot Dungeon benefits. Its reward premium in the contract (+35% gold, +25% magic items, +50% cosmetic drops) is **removed**, matching K-9 for Fire Island. The Beta 2b rotating Hot Dungeon remains a separate system.
- **Rules inside Hythloth are K-1 to K-6 unchanged:** same-region player initiation (no pets), Knocked Out with open pack loot (a blue who takes an item becomes criminal), Execute only by a grey or red with damage rights, the K-5 murder-count rule, Wards and Loot Protection inactive.
- **Communication is K-10:** entry and exit messages plus `[HotZoneStatus`; no login summary, Britain board or Recall/Gate warning.
- **Travel is stock:** Recall and Gate do not work into or out of Felucca dungeons, so the way out is the entrance onto Fire Island. Nothing is added.
- **Defaults accepted:** Hythloth is its own named Hot region (not merged with Fire Island); the server refuses to start if a configured dungeon region does not exist.
- **Activation acknowledged:** `featureFlags.hythlothHotZone` is turned on once verification passes ("turn it on when verified").

## Review findings
- Every Hot rule asks one membership check, `OutdoorHotZonePolicy.GetRegionName` / `IsHot` (initiation K-2, Knocked Out loot and Execute K-4, murder counts K-5, Ward, theft and corpse-loot exemptions K-6). It excluded every dungeon interior by design.
- Hythloth is one stock `DungeonRegion` on Felucca, x 5898-6136, y 2-246, entrance 4722,3814. Its only boundary crossing is the stock two-way teleporter at 4721-4723,3813 (Fire Island, already Hot) to 5904-5906,16; 42 teleporters are internal. Shame (x to 5895), Ice (x to 5888) and Sanctuary (x from 6144) are separate regions 3-10 tiles away. No other dungeon has its entrance inside an outdoor Hot polygon.
- Inside: 81 spawners (gargoyles, daemons, hell hounds, gazers, imps, two balrons) and 49 treasure chests; no vendor, bank or healer.
- Stock travel: `SpellHelper` forbids Recall and Gate from and to Felucca dungeons.

## Design as built
| Piece | Behavior |
| --- | --- |
| Membership | `OutdoorHotZonePolicy` (the one check every Hot rule uses) returns a dungeon's name when the mobile or item is inside a stock `DungeonRegion` listed in `hotZones.dungeonRegions` on the same map, and only while `featureFlags.hythlothHotZone` and `hotZones` are on. Every other dungeon interior, named or not, stays ordinary. Outdoors the polygons decide, unchanged. |
| Config | `shard-rules.json`: `hotZones.dungeonRegions: [{ name: "Hythloth", map: "Felucca" }]`; `featureFlags.hythlothHotZone: true` (activated 2026-10-02 after verification, owner acknowledged). Validation: names unique across all Hot regions, an enabled map, and the flag needs `hotZones` and a Hythloth entry. |
| Boot check | After startup, with the flag on, every listed region must be a stock dungeon region on its map, or the server stops (`Validated Hot Zone dungeon regions: Hythloth (Felucca).`). |
| Rules | The unchanged K-1 to K-6 code paths: same-region player initiation, Knocked Out with open pack loot (a blue looter is flagged criminal), Execute by a grey or red with damage rights, the K-5 murder rule, Wards and Loot Protection inactive. |
| Messages | Entry: "You have entered Hythloth, a PvP Hot Zone. Players may initiate combat freely here. Murdering an ordinary blue still adds a murder count and 24 hours of red time." Leaving one Hot Zone straight into another (Hythloth's entrance onto Fire Island) says only "You have left Hythloth." before the Fire Island entry line; leaving for ordinary ground keeps the existing "Hot Zone initiation no longer applies here" line. |
| Status | `[HotZoneStatus` (staff) lists the dungeon Hot Zones and the flag, and now shows the stock region name of the caller's tile. |
| Player text | `[Welcome` and `[TheftStatus`: Wards do nothing "inside a Hot Zone (Fire Island, Buccaneer's Den island or Hythloth)". README Hot Zones bullet. |
| Not built | No reward premium, no login summary or Britain board, no change to travel, spawns or pets. |

## Acceptance matrix and results
Unit: `HythlothHotZoneTests`:
- only the listed dungeon is Hot, and all of it; Shame, Ice, Sanctuary, Fire and a nameless dungeon are not;
- Felucca only; with the flag off nothing is Hot; outdoor polygons unchanged;
- same-region initiation; the three message cases;
- shipped config, validation, the boot check, and the shipped name matching the stock `regions.json`.

Shard suite 408/408. No ModernUO change.

Live: disposable host `hyth-b` with the flag on, then restarted with it off; real Navrey clients; driver `tests/scenarios/hot-zones/hythloth_live.py`. The controls stand inside Shame (its go-location) and Ice (5763,189; Ice's stock go-location lies outside its own rectangles), each confirmed by the stock region name in `[HotZoneStatus`.

| Case | Result |
| --- | --- |
| Y1 walking into Hythloth on the real entrance teleporter: "You have left Fire Island." then "entered Hythloth, a PvP Hot Zone" | pass |
| Y2 `[HotZoneStatus` inside: stock region Hythloth, Hot region Hythloth | pass |
| Y3 walking out onto Fire Island: "You have left Hythloth." (no "no longer applies"), then the Fire Island entry line | pass |
| Y4 blue attacks blue inside Hythloth: damage lands, attacker turns criminal, no denial | pass |
| Y5 / Y5b Shame: the same attack refused and the denial audited; stock region Shame, not Hot | pass |
| Y6 / Y6b Ice: the same attack refused and the denial audited; stock region Ice, not Hot | pass |
| Y7 lethal blow inside Hythloth: Knocked Out, attacker recorded | pass |
| Y8 a blue opens the Knocked Out pack without Snooping and takes an item: loot authorized, looter flagged criminal | pass |
| Y9 a blue bystander's Execute is refused | pass |
| Y10 the criminal recorded attacker executes (11 s into the 90 s window) | pass |
| Y11 automatic murder count (observation) | 0, as expected: `automaticMurderAdjudication` is off, so the stock report-murder path applies, as outdoors |
| Y12 snooping a blue inside Hythloth opens the pack | pass |
| Y13 stealing from a blue inside Hythloth reaches the roll; no Ward audit | pass |
| Y14 Shame: the same theft gets no roll, hostility denied | pass |
| R1 logging in inside Hythloth after a restart: the entry warning about 3 s after login | pass |
| R2 membership after the restart | pass |
| R3 blue-on-blue inside Hythloth after the restart | pass |
| F1 flag off: Hythloth is ordinary, the attack is refused, `[HotZoneStatus` shows "Hot region: none" | pass |
| Pets (source inspection) | `PetRestrictionService` does not consult Hot membership, so the dungeon pet rules are untouched |

Harness faults fixed during the run (not product defects):
- `[HotZoneStatus` is staff-only, so readings come from the staff session standing on the player's tile.
- The row south of Hythloth's go-location is the slope from the entrance, out of line of sight.
- Knocked Out looting is opening the pack and dragging items (K-4 corpse-style), not Stealing, which stock refuses on a Knocked Out target.
- Shame's elementals killed a test character twice at a spot left occupied too long.
- A restarted Navrey session starts a new client log.
