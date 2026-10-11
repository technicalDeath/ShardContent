# The Furnisher (evidence and readiness)

Status: **built and verified on disposable hosts 2026-10-09; deployed and ACTIVATED on the dev host 2026-10-11 on the owner's "Activate both this and furnisher" (flag `furnishers` true; the first start placed the vendor and 229 display items, a restart found them in place; a real-client check of the hall and the buy window was shown to the owner); the Furnisher was committed and pushed the same day (ShardContent `400ea01`).** The design is `Design-Proposal-3-House-Decoration-Gold-Sink.md`; the owner approved the build on 2026-10-09 ("Everything is approved. Check in with me for commit and deploy authorization."). The `furnishers` flag is `true` in `shard-rules.json` since 2026-10-11; the README line below was added the same day.

## 1. What was built

| Where | Change |
| --- | --- |
| `data/configuration/furnishers.json` (new, generated) | The whole shop as data: 37 pieces (id, name, rarity, price, item or deed, placement, every facing's graphics), the vendor's spot, and the 229 display items of the showroom hall. Made by `tools/world-decorating/build_furnishers_config.py` from the approved selection and the approved showroom layout, which the generator checks with `planner.py` first. Edit the sources and regenerate; never this file by hand |
| `FurnishersConfiguration.cs` (new) | The models, the loader and the validator (schema, unique ids, rarity 1 to 6, price within the 80,000 gp ceiling, a ladder where every rarity's cheapest piece costs more than the one below's dearest, item pieces have one graphic, wall pieces are north or west, vendor inside the hall, every hall item names a piece, every piece is in the hall). It is read and validated at every start, flag on or off, so bad data stops the server at once |
| `Furnishings.cs` (new) | `FurnishingItem` (one graphic, locked down like furniture), `FurnishingDeed` (stock `BaseAddonDeed`, made tradeable and lootable), `FurnishingAddon` + `FurnishingComponent` (the placed multi-graphic piece), `FurnisherDisplayItem` (the inert hall copy), and the two attributes that let the Interior Decorator and staff `[Flip` turn them through the facings in the file. Objects store only the piece id, so a price or name change needs no migration |
| `Furnisher.cs` (new) | The vendor (`Furnisher`, title "the furnisher") and its shop (`SBFurnisher`): stock from the file, never buys, does not wander, cannot be harmed, no town tax |
| `FurnishersService.cs` (new) | Keeps the shelf at 999 of everything after every purchase, writes an audit line per purchase, and makes the world match the file on every start and on `[FurnisherRefresh` (see section 2). Staff: `[FurnisherStatus`, `[FurnisherRefresh` (Administrator) |
| `ShardRulesConfiguration.cs`, `shard-rules.json` | Flag `furnishers` (off, no other requirement) |
| `ShardBootstrap.cs` | `FurnishersService.Configure()` once, behind a guard |
| `tools/Deploy-Alpha1Baseline.ps1` | Copies `furnishers.json` to `Distribution/Configuration` |
| Test tooling | `tests/scenarios/furnishers/FurnisherProbe.cs` (disposable host only: builds a house, deposits gold, reports the world as JSON, asks the stock fit rule), `furnisher_live.py` (the live cases below), `Start-DecorRig.ps1 -PrepareHost` (swap in a build under test before the rig starts) |

## 2. How the world gets it, and gets it back

The first plan was the world-generation manifest's `customSpawnerFiles` and `customDecorationFiles`. That does not fit: `[Alpha2bWorldGen apply` refuses a world that is not empty, and its rerun replaces spawners, so a hall placed by it would be fragile. Instead `FurnishersService.Ensure()` runs on every start (`ServerStarted`) and on `[FurnisherRefresh`:

- Flag **off**: removes the Furnisher and every display item inside the hall's bounds. Nothing the players own is touched.
- Flag **on** and Felucca **empty** (no root items, no non-player mobiles: the same test world generation uses): does nothing, so generation can still run. **The hall appears on the first start after world generation.**
- Flag **on** and the world has content: creates the vendor and any missing display item, removes extras and repeats, moves a drifted piece or vendor back, keeps one Furnisher. Only objects inside the hall's bounds (1622,1654 to 1641,1680) are managed.

Respawn the world and the vendor and hall come back by themselves. The runbook (`Alpha-2b-World-Generation-Runbook.md`) says so.

## 3. Verification

**Unit tests:** the full Shard suite passes, 1,114 tests (run `20261010T004350047Z-177bd8`), 29 of them new (`FurnishersTests`): the shipped file validates; 37 pieces with 8/8/8/6/4/3 by rarity; every price on the approved curve (base 2,000 gp x 1, 2, 4, 8, 16, 35 x 0.85 to 1.15, rounded to 50 gp, ceiling 80,000 gp); items have one graphic and deeds several; turning items differ in every facing; every piece is in the hall and the vendor is in the hall; ten kinds of bad data are rejected; the flag is false in the shipped file and validates when true; the ensure decision table; the hall-matching plan (right hall needs nothing, empty world gets all 229, missing/extra/repeated/drifted items); the shelf lists every piece at its price in full depth and buys nothing.

**Live, disposable host (`furnisher`, the dev world plus the new build, flag on), Navrey, real client:**

| # | Case | Result |
| --- | --- | --- |
| 1 | On the first start the world has one Furnisher at (1631,1668,15), titled "the furnisher", stationary, invulnerable, and 229 display items | pass (log: `vendor created; display items: 229 created`) |
| 2 | It buys nothing back (`IsActiveBuyer` false, no sell types), and no sell list opens | pass |
| 3 | The buy list has 37 pieces, 999 of each, at the exact configured prices up to 80,000 gp | pass (the server's shelf and the real client's window; at the time Navrey's `shop` wrapped prices over 65,535 gp, since fixed, see section 6) |
| 5 | One cart of one piece per rarity (8 pieces, 206,750 gp) in a single purchase: the vendor names the total, the ledger counts exactly the cart | pass |
| 6 | The backpack holds exactly those pieces, named as in the catalog, items as items and multi-graphic pieces as deeds, none newbied | pass |
| 7 | The shelf is 999 again after the purchase | pass |
| 8 | The gold ledger splits by rarity (4,100 / 4,300 / 7,550 / 16,650 / 34,650 / 139,500) | pass |
| 10 | A bought single piece is dropped in a house and locked down like furniture | pass (chair, hearth) |
| 11 | A bought deed places a 16-tile rug through the stock addon rules; the deed is used up; every tile is named for the piece | pass |
| 12 | A wall hanging is refused in the middle of the room (no wall), the deed stays; accepted against the north wall | pass |
| 13 | Turning a two-graphic piece into a tile that holds a locked-down chair is refused ("You cannot build that there"), and the piece is put back exactly as it was | pass |
| 14 | Chopping a placed two-graphic piece with an equipped hatchet returns its deed; placed again, the Interior Decorator turns it East to South (different graphics) and back, nothing duplicated | pass |
| 15 | The Interior Decorator turns a one-graphic piece (chair, 0x1E6F to 0x1E78); the 59,500 gp rarity 6 Fieldstone Home Hearth places | pass |
| 16 | The 48-tile, 80,000 gp Great Hall Carpet builds all its tiles (it does not fit a 5x5 room, which is a house-size limit, not a defect) | pass |
| 17 | After a save and restart: still one Furnisher (the same one) and 229 display items, none duplicated; the backpack, the placed addons and the locked-down furniture are identical to the snapshot | pass (`vendor in place; display items: 0 created, 0 removed, 229 already in place`) |
| 18 | Flag **off** at start: the Furnisher and all 229 display items are removed, and the player's two carried deeds, four placed pieces and two locked-down items remain | pass |
| 19 | Flag **on** again: the vendor and the hall come back | pass (`vendor created; display items: 229 created`) |
| 20 | `[FurnisherRefresh` brings back a vendor a staff member removed, and removes a second one added by hand | pass |
| 21 | **Respawn:** a host with an empty world and the flag on starts and leaves the world empty (`left alone: Felucca is empty`); `[Alpha2bWorldGen preview` shows 0 roots; `apply` completes; the hall is absent until the next start; after one restart the vendor and 229 display items appear; `[Alpha2bWorldGen audit` passes with the hall present (410 signs, 385 teleporters, 1,546 spawners, 1,345 doors, 9 moongates, 63 Khaldun items); the convergence `rerun` generates 0 decorations and 0 doors (1,345 existing), passes the audit, and leaves the hall alone | pass |

**Real client** (ClassicUO, screenshots under `work/furnisher/shots` and `work/player-client/DecorCam/shots`, scratch): the hall from the door and from the north-east corner (`door.png`, `ne-sw.png`, `west.png`, `east.png`, `nw-se.png`, `front.png`), a display piece's name label on a click (`click-rug`), the vendor's buy window at the top of the list ("Plank Bed (deed) at 2050gp", 999, the bed's icon) and at its end ("Fieldstone Home Hearth (deed) at 59500gp"), and the bought pieces in a house (`house-inside.png`: tapestry on the wall, three hearths, chair, rug).

## 4. Player-visible text

- Vendor window: each piece is listed by its catalog name with its own graphic as the icon; a multi-graphic piece reads "<name> (deed)". Prices are the curve's.
- Display pieces show their name when clicked; their tooltip shows the name, rarity, collection and price (gp).
- A bought piece's tooltip shows its rarity and collection.
- Refusals while placing or turning are the stock ones (500269 "You cannot build that there.", 500268 "This object needs to be mounted on something.", 500274, 500271).

**README rules line, to apply at activation:** "**The Furnisher.** A vendor in the Counselor's Guild hall in Britain sells house furnishings for gold, from 1,850 gp up to 80,000 gp, and never buys them back. The hall shows every piece, one of each. A one-piece furnishing is locked down like any furniture; a bigger one comes as a deed you place in your own house, turn with the Interior Decorator, and chop to get the deed back. Furnishings can be traded and looted."

## 5. Shipping (nothing below has been done)

1. **Commit** (selective: the repo holds other work in progress): the new `FurnishersConfiguration.cs`, `Furnishings.cs`, `Furnisher.cs`, `FurnishersService.cs`; the edits to `ShardRulesConfiguration.cs`, `ShardBootstrap.cs`, `shard-rules.json`, `Deploy-Alpha1Baseline.ps1`; `data/configuration/furnishers.json`; `tests/FurnishersTests.cs`; `tests/scenarios/furnishers/`; `tools/world-decorating/` (generator, README, rig param, layout, sites); this document and the runbook note. No ModernUO change.
2. **Deploy** with `Deploy-Alpha1Baseline.ps1` (server stopped; no engine rebuild needed). With the flag off, nothing changes for players: the server loads the types and removes any hall that is not there.
3. **Activate** only on the owner's explicit say-so: set `furnishers` true in `shard-rules.json`, redeploy, start. The first start places the vendor and the hall; check `[FurnisherStatus` (1 vendor, 229 display items). Then the README line above.
4. **Rollback:** with the flag off the content is removed at start. Once players hold furnishings the saves contain `FurnishingItem`, `FurnishingDeed`, `FurnishingAddon`, `FurnishingComponent`, `FurnisherDisplayItem` and `Furnisher`, so the content DLL cannot be rolled back to a build without them; snapshot `Saves` before the deploy as for any save-format change.

## 6. Named limits and notes

- The Furnisher's name and look are random each time it is created (stock vendor behaviour); a respawned world gets a new one.
- A gold cost of 80,000 gp is the ceiling; the dearest piece (Great Hall Carpet, 48 tiles) needs a house of about 7x7 interior tiles or more.
- Gold comes from the pack first and the bank when the pack lacks it (stock vendors); the buy window's "Gold Avail" shows the pack only.
- Only the 37 Britain pieces are sold. The other 63 pieces, the specialist towns and the weekly rotating window are deferred, as agreed.
- **Test tool (fixed 2026-10-10):** Navrey's `shop` command kept a buy-list price in 16 bits (it showed 66,500 gp as 964 gp); the server and the real client were always correct. Navrey now shows the exact price (verified on a disposable host: 66,500, 80,000 and 59,500 gp lines), and the live script's price check is exact. The sell list stays 16-bit because the protocol's is.
- **Dev world audit:** `[Alpha2bWorldGen audit` on a copy of the dev world reports spawners 1543/1546. A freshly generated world passes (case 21), so this is a difference in the dev world, not the Furnisher; it is not investigated here.
