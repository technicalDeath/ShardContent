# Showroom Hall: where it could go

**Status:** survey (2026-10-08), nothing placed or changed. **Owner's choice: Counselor's Guild (east), site 4** (see "The chosen site" and "The arranged showroom" below; the first rough mock-up with pieces on the forecourt was replaced by an arranged layout that fits everything inside). Answers the owner's request to find possible locations for the Showroom Hall in [Design Proposal 3](../../../Design-Proposal-3-House-Decoration-Gold-Sink.md). Every building below was measured from the shard's own map data and world data, then **photographed in the real ClassicUO client** on a disposable test server (so doors, signs and decoration items are exactly what a player would see).

## What the hall has to hold

Only the pieces that **arrive as deeds** need a place on the showroom floor. A single-graphic piece (a chair, a lamp, a clock, a shelf, a hearth that is one graphic) needs no deed, and the vendor-window icon is the whole piece, so it can be seen in the vendor list. Of the Britain Furnisher's 37 pieces, **14 are single-graphic** and **23 are multi-tile deeds** (beds, tables, settles, rugs, the two hearths that are two tiles, a tapestry and a portrait).

Those 23 take **207 tiles of floor** if nothing overlaps: **145 of rugs** (the Great Hall Carpet is 8 by 6) and **62 of furniture**, plus about 5 tiles of wall. With a walkway round each group that is **about 310 tiles**; with the beds and tables standing on the rugs, as in a real room, it is nearer **220**. (An earlier version of this survey sized the hall for all 37 pieces, 220 tiles and about 330 with walkways; counting only the deed pieces saves little because the rugs, which are all deeds, are 145 of the 207 tiles.) The hall also needs to be public, safe (inside Britain's guarded town), reachable on foot, and free of fixed furniture that cannot be removed.

## How it was searched

* Britain's map statics (walls, roofs, floors, fixed furniture) read straight from the client data, building by building, to find every roofed building and measure its interior.
* The shard's world data for each building: the decoration items placed inside (`Britannia/britain.cfg` through the world-generation manifest), the vendor and townsperson spawners, and the shop signs (named from the client's text table).
* Open ground inside the town walls, looking for a lot big enough to build on.
* The eight buildings that survived were visited in the real client, outside and inside.

![Britain with the eight sites numbered; green are the four worth considering, red are not suitable. B is the Bank, C the town centre.](overview.png)

## The short list

Interior tiles are measured from roof and floor data (give or take about 10%). "Bank" is the walking distance in tiles from the First Bank of Britain, the town's busiest spot.

| # | Building | Where (x, y) | Interior | What is inside today | To make it ready | Bank |
| --- | --- | --- | --- | --- | --- | --- |
| **1** | **Counselor's Guild (north)** | 1496-1512, 1512-1528 | about 260 | Empty. Two large red carpets (140 tiles) laid in the floor art; one stray crate | Nothing to remove; the Furnisher and the hall data only | 236 |
| **2** | **Bay Side warehouses** | 1560-1584, 1736-1752 | about 360, in three long halls | Stock: 81 crates, 41 barrels, 15 large vases, sacks (160 decoration items). No carpets, bare wooden floor | Remove the 160 items through a world-generation rule; then the hall data | 200 |
| 3 | King's Men Theater | 1440-1460, 1576-1600 | about 165 plus a stage | **38 benches that are part of the map itself**, so the audience seating cannot be cleared | Not possible without a client map change | 114 |
| 4 | Counselor's Guild (east) | 1624-1640, 1656-1672 | about 210, L-shaped | Empty but for a chimney, a bookcase and a lamp post. Red carpets (145 tiles) in the floor art | Remove 3 items | 220 |
| 5 | Lord British's Conservatory of Music | 1436-1475, 1548-1567 | about 400 | The Bardic guild: a bard and the guildmaster, 29 chairs, 28 bookcases, music stands, rugs, planters | Move a working guild | 150 |
| 6 | River Road house | 1538-1560, 1680-1696 | about 270 | A furnished home: beds, tables, bookshelves and rugs, some of it fixed in the map | Not possible | 121 |
| 7 | North-east house | 1592-1616, 1512-1528 | about 240 | A furnished home, same problem | Not possible | 336 |
| 8 | Cavalry Guild | 1576-1600, 1552-1568 | about 150 | Half an archery yard with training dummies and hay, half an office | Not possible | 280 |

The four in green on the map (1 to 4) are the only ones with an interior that is empty or clearable. Number 3 drops out because its benches are fixed; that leaves three real choices (the numbers are map labels, not a ranking).

### 1. Counselor's Guild (north): the clean one

![Plan of site 1](plan-1.png)

| Inside | Outside |
| --- | --- |
| ![inside](photos/site-1-inside.png) | ![outside](photos/site-1-outside.png) |

* **What it is:** a plain wooden hall, about 15 by 15 inside, one level, a single door in the south wall (the "Counselor's Guild" sign hangs beside it at 1505, 1528). Nobody lives or works in it and no spawner is inside.
* **Fit:** 260 tiles is comfortable for the 23 deed pieces if the beds and tables stand on the rugs (about 220), and a little tight if nothing overlaps (about 310). The two permanent red carpets cover over half the floor, so the displayed rugs will sit on top of them, which is busy but workable; furniture can stand on the fixed carpets and the displayed rugs can use the bare floorboards.
* **Position:** at the north end of town beside the river, about a minute's run from the Bank. Quiet; players would have to come to it.
* **Work:** the least of any site. No decoration to clear; the Furnisher spawner and the hall's placement file are all that is added.

### 2. Bay Side warehouses: the big one

![Plan of site 2](plan-2.png)

| Inside | Outside |
| --- | --- |
| ![inside](photos/site-2-inside.png) | ![outside](photos/site-2-outside.png) |

* **What it is:** three long wooden halls side by side (each roughly 8 by 16) with a door each on the west side, in the south-east of the old town, on Bay Side Road near the shore. About 360 interior tiles, no carpets, plain wooden floor, no fixed furniture.
* **Fit:** comfortable for the 23 deed pieces with aisles, with room for the deed pieces of the other 63 when more vendors open. The three halls suggest their own arrangement: one hall for the dining and hearth pieces, one for the bedchamber and parlour, one for the carpets, walls and study.
* **Position:** the south-east corner of the old town, about 20 tiles from the Unicorn's Horn tavern (with its tavern keeper, waiter and cook), near the bay shore. About 200 tiles from the Bank; the Customs house is some 80 tiles west along the shore.
* **Work:** the warehouses are stocked with goods that the shard's decoration data places as items (81 crates, 41 barrels, 15 large vases, sacks and urns, 160 in all). They are server items, not map art, so they can be removed, but only by adding a rule to the world-generation manifest (it already has `decorationRewrites` and `decorationDuplicateCleanup`; a "clear this rectangle" rule is a small addition). A showroom in a warehouse also fits the story: furnishings arriving by ship.

### 4. Counselor's Guild (east): the small one

![Plan of site 4](plan-4.png)

| Inside | Outside |
| --- | --- |
| ![inside](photos/site-4-inside.png) | ![outside](photos/site-4-outside.png) |

* About 210 tiles in an L-shaped plaster-and-timber hall with 145 tiles of fixed red carpet, east side of town (220 tiles from the Bank). Nearly empty (a chimney, a bookcase and a lamp post to remove). Borderline: it holds the 23 deed pieces only if the beds and tables stand on the rugs (about 220 tiles); a fallback.

## The chosen site: Counselor's Guild (east)

![Detailed plan of the hall and the ground in front of it (red = fixed carpet, black = walls, grey = cobblestone road, green = grass; the white dot is the Counselor's Guild sign at 1634, 1673, beside the hall's one door)](plan-4-front.png)

**The building.** An L-shaped plaster-and-timber hall, about 211 floor tiles in three rooms, one double door in its south wall (door tiles 1631 and 1632 at y 1671, sign at 1634, 1673). The long **south hall** is 15 by 7 tiles; a **north-west room** (6 by 7) and a **north-east room** (8 by 8) sit above it, joined to each other by an interior door at 1630, 1659. Fixed red carpet (145 tiles of floor art) lies under most of the south hall and the north-east room. The room edges below were read from the server's own walkable-floor grid (`layout/walkgrid.json`), not estimated.

**The forecourt** south of the door is open flat cobblestone, about 20 by 8 tiles, at the junction of two roads. It stays clear except for the runner at the door.

## The arranged showroom

**One of each, nothing repeated.** Every one of the Britain selection's 37 pieces stands in the hall exactly once (23 deed pieces and 14 single pieces; the Crimson Runner lies outside the door as a red carpet to the entrance). The hall is arranged by function, the way a furniture showroom is, with bare floor left between the groups for walking: 75 floor tiles of furniture on 145 tiles of rugs, in a hall of 211.

![Plan of the layout. Numbers: 1-5 hearth wall, 6 Slate Dragon Rug, 7-14 lounge, 15-17 Great Hall, 18-29 dining room and study, 30-36 bedchamber, 37 the runner at the door. Tan = furniture, red = rugs, blue dots = wall hangings.](layout/plan.png)

* **Hearth lounge (west end of the south hall).** All four hearths and fireplaces stand **side by side against the west wall** (Gray Brick Fireplace, Fieldstone Home Hearth, Slate-Roofed Hearth, Gilded Marble Hearth), with the Oak Longcase Clock at the end of the row. The **Slate Dragon Rug** lies in front of the fires, carrying the **Cider and Ale Table** and the **Paneled Oak Armchair**. The **Four-Seat Settle** and the **High-Backed Oak Settle** line the north wall under the **Gold-and-Green Tapestry**; the **Rustic Plank Table** runs along the south wall. A **silk-shaded floor lamp** and the **Wrought Taper Stand** flank the passage into the next room.
* **The Great Hall (east end, by the door).** The **Great Hall Carpet** (8 by 6) with the **Great Hall Table** on it, and the **Long Banquet Table** running down the east wall. It is the first thing a visitor sees from the door.
* **Dining room (north-east).** Two dining sets side by side under the **Curtained Portrait** and a **Blue Velvet Drape**: the **Plain Olive Rug** with the **Plank-Top Dining Table** and its **Pale Pine Chair**, and the **Golden Arabesque Carpet** with the **Marble Banquet Table**.
* **Study corner (south end of the north-east room).** **Brass Telescope**, **Scholar's Bookshelf and Mortar**, **Pale Pine Shelves**, a **Tall Stack of Books** and a **vase**.
* **Bedchamber (north-west).** The **Blue Floral Carpet** with the five **beds** in a row along the north wall (Linen and Feather-Down four-posters, Carved Rosewood, Midnight Carved, Plank Bed) and the **Walnut Longcase Clock** in the corner.

**Photographed in the real client** (a disposable test server, nothing in the live world was touched):

| From the door | West end | From the street |
| --- | --- | --- |
| ![from the door](layout/sh-door.png) | ![west end](layout/sh-west.png) | ![from the front](layout/front.png) |

| Bedchamber | North-east room | Great Hall and the east end |
| --- | --- | --- |
| ![north-west room](layout/nw-mid.png) | ![north-east room](layout/ne-mid.png) | ![south hall east end](layout/sh-east.png) |

| Dining nooks | Bedchamber and hearths |
| --- | --- |
| ![north-east room from the south](layout/ne-sw.png) | ![north-west room from the south](layout/nw-se.png) |

**How the layout was made and checked.** (An earlier draft repeated the chair designs round the tables; the owner asked for one of each, as in a real showroom, and they were removed.) A planner (`ShardContent/tools/world-decorating/planner.py`; layout `layouts/counselor-guild-east.json`, site config `sites/counselor-guild-east.json`; method in the skill `world-decorating`) holds the layout as a list of (piece, facing, tile). Before each photo run it checks that every piece stands on server-walkable floor and does not overlap another of its kind, that wall hangings sit against a wall facing the right way, that **nothing blocks the double door or the interior door**, and that **every room can be walked to from the entrance**. It also fixed a real bug the first attempt showed: the Slate Dragon Rug is a taller rug than the others and drew over the table on it, so furniture now rests on each rug's own height. The tool then writes the placement file and the real-client photos use it unchanged.

**Pieces for a later hall.** The other 63 pieces (the 37 here are 37 of 100) are not in the layout. When more vendors open, their deed pieces would need more room, and the Bay Side warehouses (site 2) remain the roomy fallback.

**Things still open:**

* **Fixed carpets show under the displayed rugs.** The map's red carpet cannot be changed from the server, so the displayed rugs sit on top of it and its red border shows round their edges (in the photos the dragon, olive and arabesque rugs all read clearly).
* **Where the Furnisher stands (proposed, not yet photographed).** Just inside the door at about 1631, 1668, one tile off the entry lane. The layout keeps 1631 to 1632 by 1669 to 1670 clear so a Furnisher (which blocks its tile like any NPC) never narrows the doorway.
* **Walls:** the layout uses the two real north-wall pieces (tapestry, portrait) and one drape; the planner rejects a hanging that is not against a wall facing the right way.
* **Placement file:** `layout/site4-showroom.client-layout.json` is the placement list used for the photos (229 graphics at absolute world coordinates, with each piece's height). It is test scaffolding for the photos; the shard's own hall data would be generated from the same layout list.

## Why the other five are out

* **King's Men Theater (the most central, 114 tiles from the Bank):** its 38 benches are map statics, part of the client's own art, so the seating cannot be cleared from the server. A shame, since it is a public hall in a good spot.

![King's Men Theater inside](photos/site-3-inside.png)

* **Conservatory of Music, the two furnished houses and the Cavalry Guild:** each holds working NPCs or fixed furnishings and would mean displacing them (see the table). Their photos are in `photos/site-5` to `site-8`.

## Open ground

No lot inside the walls is big enough to build on. The largest clear rectangle in the whole town is 22 by 20 tiles and is a paved ceremonial walkway with lamp posts and planters; the next ones are roads and junctions (photos `open-1` to `open-3`). A purpose-built hall would have to go outside the walls, which is where the housing districts are planned, so it is not recommended.

## Decision

The owner chose **Counselor's Guild (east)** (site 4). A first rough mock-up put pieces on the forecourt; after the owner asked for a real showroom arrangement, everything was fitted inside (see "The arranged showroom"), so the forecourt only carries the runner at the door. The rest of this survey (sites 1 to 3 and 5 to 8) is kept as the record of what else was considered.

## Notes and limits

* Interior tile counts come from roof and floor map data and are good to about 10%; a floor plan with real furniture footprints is the next step once a site is chosen.
* Photos are from a disposable test server using the shard's own generated world data (doors and decoration included). Nothing in the live dev world was touched.
* Britain's walls, floors and some furniture are map statics; its crates, barrels, chairs and bookcases are server items placed from `Britannia/britain.cfg`. Only the second kind can be moved from the server side.
* Tools: the scan scripts were scratch work; the numbers can be reproduced from `UOData`, `Distribution/Data/BritanniaRenaissance/Alpha2b/` (decoration, spawns, signs) and the pinned `regions.json`.
