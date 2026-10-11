# Design Proposal 3: The Furnishers (house furnishings as a gold sink)

**Status (2026-10-09):** the Britain Furnisher (37 pieces, one vendor, one showroom hall) was approved and built, flag `furnishers` OFF, not yet committed, deployed or activated: `Furnisher-Evidence.md`. The rest of this proposal (the other 63 pieces, specialist towns, the weekly window) is still a proposal. Original status (2026-10-08): proposal, not approved, not scheduled, nothing built. Written at the owner's request: *a set of house decorations that are not available to players through any means, a major gold sink, grouped into categories with escalating rarities by how "cool" each one is, priced later on a curve, sold by one or more vendors in the world; roughly 100 items.* **Revised the same day** after the owner's curation pass (no seasonal or holiday pieces; standard home furnishings only) and after his rulings on the shop design: no weekly window, a Furnisher NPC, a showroom hall, a **toned-down price curve that tops out at 80,000 gp**, and **for now one vendor in Britain selling a selection of every rarity** (listed under "Decisions for the owner"). This is **off the roadmap** (like the gathering repeat), so its place in the Beta order is the owner's call; see "Where it fits". Companion to [Design Proposal 2: Hearths](Design-Proposal-2-Hearths.md); built on the [cosmetic reward catalog](cosmetic-rewards/README.md).

**Vision it serves:** *A classic Ultima Online experience that keeps Felucca's thieves, criminals and murderers, and the emergent encounters they create, but not the griefing: a single world where deliberate systems concentrate the population, build community and draw players into contact with one another, and where the classic UO:R power ceiling holds, because the experience lies in the adventures and interactions that unfold in the world, not in the grind of character progression. Custom content extends that world outward with new activities and reasons to travel, while the core of play stays recognizable and true to the classic experience.*

![All 100 furnishings, ordered by rarity](cosmetic-rewards/gold-sink/overview.png)

## The short version

* **100 furnishings** that players cannot get today: not crafted, not sold by any stock NPC, not in any loot table, and not in any of the 33 reward pools that other systems (Nemesis, Wanted, Shipwreck, Expedition, Pilgrimage) will hand out. Every piece is cosmetic art that already exists in the shard's client files, and every one was photographed standing in Felucca in the real ClassicUO client ([showroom shots](cosmetic-rewards/client-shots/README.md), part 3).
* **Eight wings** (categories): Bedchamber, Parlour & Music Room, Dining & Kitchen, Rugs & Carpets, Hearth & Light, Study & Observatory, Walls & Hangings, Hall Curios. Eleven to sixteen pieces each, so a wing is a ladder you climb.
* **Six rarities**, set by how cool a piece is (size, number of tiles, height, colour, facings): **Common 20, Uncommon 26, Scarce 20, Rare 20, Extremely Rare 10, Wonder 4.** The four Wonders are the Great Hall Table, the Great Hall Carpet (48 tiles), the Fieldstone Home Hearth and the Grand Gallery.
* **Sixteen collections** (a Master Bedchamber, a Dining Hall, a Music Room, an Observatory...) that span wings and rarities, so there is always a next room to furnish. Collections are descriptive only; no set bonus.
* **A toned-down price curve on a 2,000 gp base, topping out at 80,000 gp** (the owner's rulings). Rarity multipliers 1 : 2 : 4 : 8 : 16 : 35, so a Common is about 2,000 and a Wonder about 70,000; each piece sits within 15% of its rarity's price by how cool it is, and nothing sells above 80,000. A [pricing sandbox](cosmetic-rewards/gold-sink/pricing-sandbox.html) shows every price and lets you move the numbers.
* **One Furnisher in Britain for now**, in the Showroom Hall, selling **a selection of every rarity: 8 Common, 8 Uncommon, 8 Scarce, 6 Rare, 4 Extremely Rare, 3 Wonder** (37 pieces; 549,350 gp for one of each). The other 63 pieces stay designed, priced and photographed but are not on sale until another vendor exists. Ordinary gold only; the vendor never buys.
* **Rarity is the price and what the vendor carries, not a rotation.** The weekly window and per-account allowance of the first draft are out (owner's ruling); they can be added later without redesign.
* Everything is **cosmetic, tradable and lootable**, built from stock mechanics (vendor window, addon deeds, house lockdowns, the stock way of turning and moving pieces). The only custom pieces are the Furnisher NPC, a data-driven item and addon class, and the showroom hall's placement file.

## What changed in the curation pass

The first draft of this set (earlier the same day) was 100 pieces across ten wings, including a Festive wing, a Cellar & Crypt wing, monster figurines, necromancer's curios, statuary, garden ponds, camp gear and siege engines. The owner asked for a big curation: **no seasonal or holiday themes** (pumpkins, jack-o'-lanterns, snowmen, Halloween spiderwebs) and **standard home furnishings only**. This version applies that as a written rule, so the shop and every later addition to it are judged the same way.

**The furnishing rule.** A piece qualifies only if all of these hold:

1. **It is something you furnish a room with**: seating, tables, beds and bedding, chests of drawers and dressers, rugs and runners, hearths and lighting, kitchen and dining pieces (a stove, a pie safe, a stew pot, a wine cabinet, a bar), shelving and desks, books and maps, clocks, vases and urns, tapestries, portraits and drapes, musical instruments, and the study instruments (telescope, orrery, armillary sphere). A handful of single pieces from other categories qualify on the same test (a canary cage, a potted orchid, a hanging fern, a cast-iron stove).
2. **It has no seasonal or holiday theme**: no pumpkins, jack-o'-lanterns, ghosts, snowmen, wreaths, holiday trees, no spiderwebs, no roast-turkey feast. The tooling blocks the tags `festive`, `season:*` and words such as "pumpkin", "snowman", "holly", "web" and "turkey".
3. **It is not macabre, crypt, dungeon or necromantic** (skulls, bones, coffins, gravestones, torture furniture), **not camp or military gear** (tents, bedrolls, siege engines, training dummies, barding stands), **not nautical or treasure dressing** (ship's wheels, guns, hoards), and **not a monster figurine or trophy**.
4. **Outdoor garden pieces and statuary are out of this shop** (ponds, trees, fountains, statues). They are not standard furnishings; they stay in the catalog and could become a separate shop later if the owner wants one.

| First-draft wing | Pieces | Kept | Why |
| --- | --- | --- | --- |
| Hearth & Home | 10 | 9 | furnishings; the good ones stay |
| Walls & Banners | 10 | 5 | heraldic banners and a pirate flag out; tapestries and portraits stay |
| Garden & Grounds | 11 | 1 | outdoor garden pieces (trees, ponds, a portico, a rock pond) out |
| Statuary & Shrines | 9 | 0 | statues, virtue plaques and shrines are not furnishings |
| Study, Arcana & Curios | 11 | 2 | necromancer's curios (skulls, a ritual dagger, a skeleton) out; telescope and orrery stay |
| Arms, Trades & Games | 10 | 0 | shop signs, barding stands, a sparring dummy and a siege catapult out; the harpsichords were swapped for others in the Parlour |
| Sea, Camp & Hoard | 10 | 0 | camp gear, ship fittings, a ship in a bottle and treasure heaps out |
| Menagerie & Trophy Room | 10 | 0 | monster figurines, a mounted fish and a bearskin out |
| Cellar & Crypt | 10 | 0 | headstones, coffins, skeletons, torture furniture and the Halloween spiderweb out |
| Festive Stock | 9 | 0 | seasonal and holiday pieces out (pumpkins, jack-o'-lanterns, snowman, wreath, holiday trees) |

**17 of the first draft's 100 pieces survived**; the other 83 were replaced with pieces that pass the rule, which is why the wings are new (Bedchamber, Parlour & Music Room, Dining & Kitchen, Rugs & Carpets, Hearth & Light, Study & Observatory, Walls & Hangings, Hall Curios). The rarity shape (20 / 26 / 20 / 20 / 10 / 4) is unchanged, so the price framework did not move.

Things that are not in the set because the art does not exist or the game already gives them out: **no kettle** (the pewter stew pot is the cookware that exists), no chandelier, and no plain armoire, bookcase or writing table (carpenters already craft those).

## Design constraints

The owner's seven rules (2026-10-02) were written for activities. This is a shop, so the honest reading is below; nothing here breaks one.

| # | Rule | How this proposal stands |
| --- | --- | --- |
| 1 | Classic UO:R, recognisable, no power creep | Cosmetic only. No stats, no skill, no storage, no function. Pieces that look like beds, stoves, chests or lamps are stripped of the function. 42 of the 100 are era-graded art; the other 58 are era-neutral art (see "Era notes"; a strict-era shop is possible but thinner). |
| 2 | Keeps thieves, criminals, murderers; no griefing | Items are ordinary tradable, lootable goods: one in a backpack can be stolen as in stock, one locked down in a house cannot. Stock vendor rules for criminals and murderers in guarded towns apply unchanged. No ownership of ground, no blocking, no griefing surface. |
| 3 | Concentrates population, draws players into contact | The Showroom Hall in Britain is a place to walk through and be seen in; later vendors would be a reason to visit other towns. |
| 4 | Ties in every playstyle | Gold from any playstyle buys it (hunters, crafters, gatherers, thieves selling loot, tamers). It is a spending sink, not an activity, and says so. Wings tie in by theme: Dining to cooks and innkeepers, Study to mages and scribes, Hearth to smiths and tinkers, Bedchamber and Parlour to carpenters and tailors. |
| 5 | Doable alone or in a small group | A lone player buys everything alone. |
| 6 | Every role has its own on-ramp | There is nothing to be gated behind: ordinary gold from any source is the only price. |
| 7 | Roles together make each other better | Not applicable to a shop. Collections are the social hook: house tours and "finish my Dining Hall" among friends. |
| Vision | Power ceiling holds; no grind | Nothing here advances a character. Prices are the owner's, so the sink can be sized to a pastime, not a grind. |

Other owner rulings applied: **stock first** (stock vendor window, stock addon deeds, stock housing; custom only where stated); **era**: cut-off Publish 5, era-neutral pieces allowed (a harpsichord, a longcase clock, an orrery, elven pieces), nothing from a later expansion's content or a skill the era lacks; **no first-come race, no shared finite stock, ordinary gold only, the vendor never buys, zero NPC resale** (the approved Rare Expedition Destination Vendor pattern, 15.12A, reused here).

## "Not available through any means": how that was checked

A piece qualifies only if all of these hold (`ShardContent/tools/cosmetic-catalog/sinkplan.py`, `availability.py`):

1. **No graphic of it is reachable in the stock game.** `availability.py` reads every stock craft menu (including the legacy T2A menus), every NPC vendor stock list and every loot table in the pinned ModernUO source (and the addon deeds they place) and lists each graphic id they can produce. It is built to over-report, not to miss: it ignores expansion gates, so it counts things a UOR player could not actually reach. The corrected audit finds 1,185 reachable graphics; 277 of the 1,161 era catalog entries and 36 of the 925 era-neutral entries touch one.
2. **A second, raw check on the final 100.** A source scan cannot prove a negative, and the first run of this audit did miss pieces (it overlooked graphics declared in an attribute above a class, and the T2A menus), which let a craftable bookcase, a craftable writing table and a vendor-sold backgammon board into the first furnishing draft. The corrected audit caught those three; the raw scan below caught the open art of a craftable armoire and the art of a vendor-sold sextant. All five were swapped out. `availability.py rawscan` lists every mention of every pick's graphics anywhere in the server's content source, and the result was reviewed by hand (summary below the list).
3. **It is in none of the 33 suggested reward pools.** The pool validator (`pools.py validate`) now also fails if a pool lists a gold-sink piece, so the two supplies cannot overlap by accident.
4. It is era grade A or B (main catalog) or era-neutral; it is not retired; the 17 borderline neutral entries awaiting an owner ruling are held back; it is **visible in Felucca** (Felucca runs the Desolation map season, which hides every leaf tile); and it passes the furnishing rule above.

**25 of the 100** share a graphic with some class in the server source that players cannot obtain in UOR; **75 appear nowhere in it**. The shared ones, by kind:

| Kind of stock class | Pieces |
| --- | --- |
| Heritage-token rugs (a later promotion that nobody is handed here) | 9 |
| Gift items (anniversary and veteran gifts, never distributed here) | 2 |
| World decoration classes (portraits, tapestries, sconces, lanterns, a gray brick fireplace) that no craft menu, vendor or loot table gives out | 8 |
| Doom and Champion artifacts (post-era rewards) | 3 |
| Bottles and jugs, which appear only as small props on two tables | 2 |
| Gump art ids and unreferenced furniture classes (a chest of drawers class that no menu lists) | 1 |

None is on a craft menu, a vendor's list or a loot table, so none is obtainable. The one practical consequence: **if the owner ever turns on a stock promotion that hands those classes out (the Heritage tokens, the gifts), the matching pieces would overlap with it**.

Result: **381 furnishing candidates** (160 era-graded, 221 era-neutral). The 100 were hand-picked from them, so about 281 more pieces are in reserve for later additions to the shop.

What the check does not cover: staff `[Add` can create anything; the catalog's own reward pools are separate on purpose; and any future system that sells or grants decorations must draw from outside this set (the same validator rule covers new pools).

## Rarity: how "cool" decides it

Every candidate gets a **coolness score** (0 to 100): a base from its catalog rarity (12, 28, 46, 64 or 82), plus 4, 8 or 12 for two, six or fifteen tiles or more, plus 4 or 8 for a piece 120 or 200 pixels tall, plus 3 for any colour hue, 2 for a second facing, 2 for a dragon or demonic theme and 1 for a noble, macabre, arcane or treasure theme, minus 5 where leaf tiles would be hidden. The score **orders pieces inside a rarity and chose the finalists**; the **tier boundaries were set by hand** so every wing has a legible ladder instead of a score cut-off. Ladders that came out of it:

* **Beds:** Plank Bed (Common) > Carved Rosewood Bed (Uncommon) > Linen Four-Poster Bed (Scarce) > Feather-Down Four-Poster, Crimson Canopied Bed and Azure Carved Bed (Rare) > Midnight Carved Bed (Extremely Rare).
* **Seating:** Pale Pine Chair (Common) > Paneled Oak Armchair (Uncommon) > High-Backed Oak Settle (Scarce) > Four-Seat Settle and Black Leather Sofa (Rare) > Gnarled Root Throne (Extremely Rare).
* **Fire:** Wrought Taper Stand (Common) > Twin Blue-Glass Lamp (Uncommon) > Slate-Roofed Hearth (Scarce) > Gray Brick Fireplace (Rare) > Gilded Marble Hearth (Extremely Rare) > Fieldstone Home Hearth (Wonder).
* **Tables:** Rustic Plank Table (Common) > Cider and Ale Table (Uncommon) > Plank-Top Dining Table (Scarce) > Long Banquet Table (Rare) > Marble Banquet Table (Extremely Rare) > Great Hall Table (Wonder).
* **Rugs:** Plain Olive Rug (Common) > Crimson Runner (Uncommon) > Golden Arabesque Carpet (Scarce) > Blue Floral Carpet (Rare) > Slate Dragon Rug (Extremely Rare) > Great Hall Carpet (Wonder).
* **Clocks:** Oak Longcase Clock (Uncommon) > Walnut Longcase Clock (Scarce) > Ivory Longcase Clock (Rare).

### The six rarities

| Rarity | Name | Pieces | Price units | Centre price at the base | Range inside the rarity | Britain Furnisher sells |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Common** | 20 | x1 | 2,000 gp | 1,700 to 2,300 gp | 8 of 20 |
| 2 | **Uncommon** | 26 | x2 | 4,000 gp | 3,400 to 4,600 gp | 8 of 26 |
| 3 | **Scarce** | 20 | x4 | 8,000 gp | 6,800 to 9,200 gp | 8 of 20 |
| 4 | **Rare** | 20 | x8 | 16,000 gp | 13,600 to 18,400 gp | 6 of 20 |
| 5 | **Extremely Rare** | 10 | x16 | 32,000 gp | 27,200 to 36,800 gp | 4 of 10 |
| 6 | **Wonder** | 4 | x35 | 70,000 gp | 59,500 to 80,000 gp | 3 of 4 |

With the ceiling and rounding applied, the whole set of 100 costs **1,223,500 gp** (one of each) and the 37-piece Britain selection **549,350 gp**.

Pictures per rarity: [1 Common](cosmetic-rewards/gold-sink/tier-1.png), [2 Uncommon](cosmetic-rewards/gold-sink/tier-2.png), [3 Scarce](cosmetic-rewards/gold-sink/tier-3.png), [4 Rare](cosmetic-rewards/gold-sink/tier-4.png), [5 Extremely Rare](cosmetic-rewards/gold-sink/tier-5.png), [6 Wonder](cosmetic-rewards/gold-sink/tier-6.png).

### Wings by rarity

| Wing | 1 Common | 2 Uncommon | 3 Scarce | 4 Rare | 5 Extremely Rare | 6 Wonder | Total | Cost units |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bedchamber | 2 | 3 | 2 | 3 | 1 | - | 11 | 56 |
| Parlour & Music Room | 3 | 4 | 3 | 3 | 2 | - | 15 | 79 |
| Dining & Kitchen | 3 | 4 | 3 | 3 | 2 | 1 | 16 | 114 |
| Rugs & Carpets | 2 | 3 | 3 | 3 | 1 | 1 | 13 | 95 |
| Hearth & Light | 2 | 3 | 2 | 2 | 1 | 1 | 11 | 83 |
| Study & Observatory | 3 | 3 | 2 | 2 | 1 | - | 11 | 49 |
| Walls & Hangings | 2 | 3 | 2 | 3 | 1 | 1 | 12 | 91 |
| Hall Curios | 3 | 3 | 3 | 1 | 1 | - | 11 | 45 |
| **All wings** | **20** | **26** | **20** | **20** | **10** | **4** | **100** | **612** |

## The eight wings

Each wing has a picture sheet (rendered from the client art) and real-client shot pages; the tables list every piece. Numbers (`No.`) are the showroom numbers printed under each item in the shots. Every piece stands on bare grass in the shots; the grey diamond that earlier gallery shots show under the tiniest items was a test tile laid by the photographing tool, not part of any piece, and no piece in this set is small enough to need one. `CR-` pieces are era-graded, `CN-` pieces are era-neutral.

### Bedchamber (11 pieces)

Beds from a plank bed to the midnight-blue carved bed, a chest of drawers, a wash basin and a mirrored vanity.

![Bedchamber](cosmetic-rewards/gold-sink/wing-BEDCHAMBER.png)

Real-client shots: [GS-BEDCHAMBER-01](cosmetic-rewards/client-shots/GS-BEDCHAMBER-01.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Linen Small Bed** (`CR-FRN-038`) | 1 Common | 2,100 | later | floor 2x1 | A narrow bed made up in clean white linen. |
| 2 | **Plank Bed** (`CR-FRN-037`) | 1 Common | 2,050 | Britain | floor 1x2 | A plain single bed with a straw-coloured tick and a low wooden headboard. |
| 21 | **Carved Rosewood Bed** (`CN-FRN-016`) | 2 Uncommon | 4,450 | Britain | floor 1x3 | A bed with a carved headboard crowned by turned posts and a footboard to match, dressed in pale linen. |
| 22 | **Elven Wash Basin** (`CN-TBL-018`) | 2 Uncommon | 3,550 | later | floor | A washstand with a round white basin set in a pale carved top. |
| 23 | **Mahogany Chest of Drawers** (`CR-TBL-037`) | 2 Uncommon | 4,000 | later | floor | A tall chest of drawers in dark mahogany, each drawer fitted with a brass pull. |
| 47 | **Linen Four-Poster Bed** (`CR-FRN-028`) | 3 Scarce | 8,700 | Britain | floor 2x2 | A grand four-poster in carved brown wood, draped in crisp white linen with a fringed valance. |
| 48 | **Mirrored Vanity** (`CN-TBL-011`) | 3 Scarce | 6,800 | later | floor | A small wooden dressing table with drawers and a round swivel mirror, loved by every lady in Britain. |
| 67 | **Azure Carved Bed** (`CN-FRN-018`) | 4 Rare | 17,650 | later | floor 1x3 | The carved four-poster made up in a deep azure quilt, as if the sea had laid itself across the bed. |
| 68 | **Crimson Canopied Bed** (`CN-FRN-015`) | 4 Rare | 15,350 | later | floor 1x3 | The same tall canopy bed in a deep crimson quilt, with enough pillows for a baron and his dreams. |
| 69 | **Feather-Down Four-Poster** (`CR-FRN-029`) | 4 Rare | 16,100 | Britain | floor 2x2 | A four-poster dressed with a thick white eiderdown and plump pillows, as a duchess might insist. |
| 87 | **Midnight Carved Bed** (`CN-FRN-019`) | 5 Extremely Rare | 31,450 | Britain | floor 1x3 | A carved oak bed under a quilt dyed the deep blue of the small hours. |

### Parlour & Music Room (15 pieces)

Chairs, benches, settles and sofas up to a throne of gnarled root, with a cello, a harp and three harpsichords for the music room.

![Parlour & Music Room](cosmetic-rewards/gold-sink/wing-PARLOUR.png)

Real-client shots: [GS-PARLOUR-01](cosmetic-rewards/client-shots/GS-PARLOUR-01.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | **Pale Pine Chair** (`CR-FRN-011`) | 1 Common | 1,900 | Britain | floor | A slender chair of unstained pine, left bare as a carpenter's shop would display it. |
| 4 | **Pale Plank Bench** (`CR-FRN-024`) | 1 Common | 2,100 | later | floor 3x1 | A smooth plank seat on stout wooden legs, three feet of honest carpentry. |
| 5 | **Tall-Backed Linen Chair** (`CN-FRN-008`) | 1 Common | 2,000 | later | floor | A slender chair with a high linen back and a white cushioned seat, plain enough for any hall. |
| 24 | **Cello on a Stand** (`CN-MUS-005`) | 2 Uncommon | 3,900 | later | floor | A honey-gold cello resting on an iron stand, its bow laid across the strings. |
| 25 | **Crimson Studded Armchair** (`CN-FRN-001`) | 2 Uncommon | 3,950 | later | floor | A deep armchair in crimson leather, its tall back buttoned in rows of brass studs. The sort of seat a guildmaster keeps for guests. |
| 26 | **Paneled Oak Armchair** (`CR-FRN-010`) | 2 Uncommon | 4,000 | Britain | floor | A high-backed armchair of dark panelled oak, its tall back carved with recessed panels. |
| 27 | **Ribboned Linen Chair** (`CN-FRN-007`) | 2 Uncommon | 3,800 | later | floor | A light wooden chair dressed in white linen and tied with a bow at the back, as for a feast or a wedding. |
| 49 | **Blue and Gold Harp** (`CN-MUS-003`) | 3 Scarce | 7,300 | later | floor | A graceful harp strung in silver, its blue frame banded with gold. |
| 50 | **High-Backed Oak Settle** (`CR-FRN-026`) | 3 Scarce | 8,200 | Britain | floor 2x1 | A two-seat settle of dark panelled oak with a tall back, built to keep draughts off the fireside. |
| 51 | **Long Velvet Sofa** (`CN-FRN-005`) | 3 Scarce | 8,050 | later | floor 3x1 | A three-seat sofa in dark velvet, curved at one end like a swan's neck. Fit for a manor's long hall. |
| 70 | **Black Leather Sofa** (`CN-FRN-003`) | 4 Rare | 14,850 | later | floor 1x3 | A long sofa of black leather edged in polished copper, the kind of seat a master scholar sinks into with a heavy book. |
| 71 | **Crimson Lacquer Harpsichord** (`CN-MUS-014`) | 4 Rare | 15,600 | later | floor 2x3 | A harpsichord in glossy crimson lacquer with a gilt-edged keyboard and a stool to match. |
| 72 | **Four-Seat Settle** (`CR-FRN-027`) | 4 Rare | 16,400 | Britain | floor 4x1 | A long, high-backed settle for four, the sort of pew a guildmaster keeps beside the great hearth. |
| 88 | **Ebonwood Harpsichord and Bench** (`CN-MUS-002`) | 5 Extremely Rare | 32,550 | later | floor 3x2 | An ebonwood harpsichord with a long padded bench drawn up to the keys, set for a duet. |
| 89 | **Gnarled Root Throne** (`CN-FRN-011`) | 5 Extremely Rare | 29,350 | later | floor | A throne of twisted black roots that glow amber in the grain, with a seat of dark leather. A hermit-mage's whim. |

### Dining & Kitchen (16 pieces)

Plank tables, a pie safe, a cast-iron stove, a stew pot, a wine cabinet, a kitchen counter and a bar, up to the marble banquet table and the ten-tile Great Hall Table.

![Dining & Kitchen](cosmetic-rewards/gold-sink/wing-DINING.png)

Real-client shots: [GS-DINING-01](cosmetic-rewards/client-shots/GS-DINING-01.png), [GS-DINING-02](cosmetic-rewards/client-shots/GS-DINING-02.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 6 | **Pewter Stew Pot** (`CN-ALC-006`) | 1 Common | 1,750 | later | floor | A big two-handled pewter pot, as good for a brew as for a stew and a great deal easier to carry than a cauldron. |
| 7 | **Round Linen-Draped Table** (`CN-TBL-005`) | 1 Common | 1,800 | later | floor | A round table hidden under a gathered white cloth tied with ribbon, set for a feast or a wedding breakfast. |
| 8 | **Rustic Plank Table** (`CR-TBL-011`) | 1 Common | 2,150 | Britain | floor 4x1 | A long table of rough weathered planks on crossed legs, as served in a roadside inn. |
| 28 | **Cast-Iron Stove** (`CN-CMP-007`) | 2 Uncommon | 3,500 | later | floor | A squat black stove with a stove-pipe chimney, the kind a trapper hauls up to his winter cabin. |
| 29 | **Cider and Ale Table** (`CR-FOO-039`) | 2 Uncommon | 4,400 | Britain | floor 3x1 | A plank table with a blue-glazed pitcher, jugs of cider and bottles of ale, the makings of a country evening. |
| 30 | **Linen-Topped Table** (`CR-TBL-028`) | 2 Uncommon | 4,200 | later | floor 2x1 | A sturdy table topped with clean white linen, the kind a healer or tailor uses. |
| 31 | **Pie Safe** (`CN-FOO-022`) | 2 Uncommon | 3,750 | later | floor | A slate-topped cupboard with pierced tin doors that keep the pies safe from mice and flies. |
| 52 | **Cellarmaster's Table** (`CR-FOO-031`) | 3 Scarce | 8,450 | later | floor 3x1 | A plank table lined with wine, ale and spirit bottles, the stock-in-trade of a good cellarmaster. |
| 53 | **Plank-Top Dining Table** (`CR-TBL-013`) | 3 Scarce | 8,800 | Britain | floor 3x2 | A three-by-two dining table with a smooth plank top, plain and strong. |
| 54 | **Silver-Framed Wine Cabinet** (`CN-FOO-021`) | 3 Scarce | 7,450 | later | floor | A tall cabinet of silvered iron whose diamond racks hold green-glass bottles laid down to age. |
| 73 | **Candlelit Dinner Table** (`CN-FOO-016`) | 4 Rare | 15,100 | later | floor 2x1 | A long table laid for two, with a white runner, pewter cups, crimson napkins and a candle at each end. |
| 74 | **Kitchen Pump Counter** (`CN-FOO-018`) | 4 Rare | 15,900 | later | floor 3x1 | A run of oak cupboards under a dark stone top, with a hand pump and deep basin set into the middle. |
| 75 | **Long Banquet Table** (`CR-TBL-007`) | 4 Rare | 17,150 | Britain | floor 5x1 | A five-tile banquet table in polished oak, long enough to seat the whole guild at Midwinter. |
| 90 | **Marble Banquet Table** (`CR-TBL-022`) | 5 Extremely Rare | 34,650 | Britain | floor 2x4 | A grand double marble table, cool and gleaming, for banquets that end in treaties. |
| 91 | **Marble Bar with Sink** (`CN-FOO-020`) | 5 Extremely Rare | 33,600 | later | floor 3x1 | A marble-topped bar with a rinsing basin built into one end, so a barkeep need never leave the counter. |
| 97 | **Great Hall Table** (`CR-TBL-010`) | 6 Wonder | 66,500 | Britain | floor 2x5 | A vast two-by-five table of dark oak, the heart of any hall where lords are made to wait. |

### Rugs & Carpets (13 pieces)

Welcome mats, runners and plain rugs up to the Great Hall Carpet, which covers 48 tiles, with a dragon rug and a lunar-phases rug on the way.

![Rugs & Carpets](cosmetic-rewards/gold-sink/wing-FLOORS.png)

Real-client shots: [GS-FLOORS-01](cosmetic-rewards/client-shots/GS-FLOORS-01.png), [GS-FLOORS-02](cosmetic-rewards/client-shots/GS-FLOORS-02.png), [GS-FLOORS-03](cosmetic-rewards/client-shots/GS-FLOORS-03.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | **Plain Olive Rug** (`CR-RUG-002`) | 1 Common | 2,200 | Britain | floor covering 4x4 | A thick olive-green rug with a dark binding, the kind that hides a lot of muddy boots. |
| 10 | **Welcome Mat** (`CN-RUG-011`) | 1 Common | 2,000 | later | floor covering | A white doormat with a plain WELCOME stitched in grey, laid just inside the threshold. |
| 32 | **Blue Bordered Rug** (`CR-RUG-005`) | 2 Uncommon | 4,550 | later | floor covering 4x4 | A deep blue rug edged with a pale blue pattern and fringed all round. |
| 33 | **Crimson Runner** (`CR-RUG-010`) | 2 Uncommon | 4,600 | Britain | floor covering 5x3 | A plain crimson runner with a gold stripe and a tasselled fringe at each end. |
| 34 | **Golden Hall Runner** (`CR-RUG-009`) | 2 Uncommon | 4,500 | later | floor covering 5x2 | A golden-brown runner with a dark border, long enough for a manor hallway. |
| 55 | **Crimson Hall Runner** (`CR-RUG-016`) | 3 Scarce | 8,950 | later | floor covering 3x6 | A long red runner with a thin gold border and a fringe at each end, for a lord's hall. |
| 56 | **Golden Arabesque Carpet** (`CR-RUG-012`) | 3 Scarce | 9,050 | Britain | floor covering 4x4 | A bright golden carpet worked with brown arabesque scrolls and a banded edge. |
| 57 | **Orange Hearth Rug** (`CR-RUG-014`) | 3 Scarce | 9,200 | later | floor covering 4x4 | A warm orange and brown carpet with a tasselled border, made for firelight. |
| 76 | **Blue Floral Carpet** (`CR-RUG-020`) | 4 Rare | 17,900 | Britain | floor covering 5x5 | A large blue carpet scattered with coral blossoms and edged with a deep teal fringe. |
| 77 | **Lunar Phases Rug** (`CN-RUG-001`) | 4 Rare | 18,150 | later | floor covering 5x5 | A great round rug of black wool ringed in gold, the moon passing through all its phases around a bronze compass-star. |
| 78 | **Navy Medallion Carpet** (`CR-RUG-019`) | 4 Rare | 18,400 | later | floor covering 4x4 | A navy carpet with a great coral medallion at its heart and a double fringed border. |
| 92 | **Slate Dragon Rug** (`CN-RUG-004`) | 5 Extremely Rare | 36,800 | Britain | floor covering 5x5 | A square slate-grey rug with a fretted border, across which a flame-red dragon unfurls its wings. |
| 98 | **Great Hall Carpet** (`CR-RUG-023`) | 6 Wonder | 80,000 | Britain | floor covering 8x6 | A huge russet carpet of tightly woven coral and orange patterns, for a hall where banquets run for days. |

### Hearth & Light (11 pieces)

A taper stand and floor lamps at the bottom, then four lit hearths and fireplaces, ending in the Fieldstone Home Hearth.

![Hearth & Light](cosmetic-rewards/gold-sink/wing-HEARTH.png)

Real-client shots: [GS-HEARTH-01](cosmetic-rewards/client-shots/GS-HEARTH-01.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 11 | **Amber Globe Lamp** (`CN-LGT-017`) | 1 Common | 1,700 | later | tabletop | A round globe of amber glass on a slim white stem, a simple lamp for a bedside or a writing desk. |
| 12 | **Wrought Taper Stand** (`CN-LGT-020`) | 1 Common | 1,850 | Britain | floor | A twisted black-iron stem topped with one long taper, its wax running in golden streaks. |
| 35 | **Silk-Shaded Floor Lamp** (`CN-LGT-015`) | 2 Uncommon | 4,100 | Britain | floor | A tall brass lamp on a round, ringed foot, glowing softly through a shade of pleated cream silk. |
| 36 | **Songbird Globe Lamp** (`CN-LGT-013`) | 2 Uncommon | 3,850 | later | floor | A sea-green glass globe held aloft on a curling stem, a little songbird perched on the leaves below. |
| 37 | **Twin Blue-Glass Lamp** (`CN-LGT-016`) | 2 Uncommon | 4,150 | later | floor | A pair of swan-necked arms bearing two bulbs of cool blue glass, rising from a fluted iron foot. |
| 58 | **Dragon-Wrapped Oil Lamp** (`CN-LGT-011`) | 3 Scarce | 7,950 | later | tabletop | A burnished-bronze dragon coiled around a glass bulb of lamp oil, its flame glowing amber inside. |
| 59 | **Slate-Roofed Hearth** (`CN-LGT-003`) | 3 Scarce | 7,550 | Britain | floor | An open iron-posted hearth capped with a slab of grey slate, a steady fire glowing in its cage. |
| 79 | **Gray Brick Fireplace** (`CR-LGT-037`) | 4 Rare | 16,650 | Britain | floor 1x2 | A tall chimney-breast of grey brick with a heavy oak mantel above a warm, blazing grate. |
| 80 | **Stained-Glass Lamp** (`CN-LGT-014`) | 4 Rare | 13,850 | later | tabletop | A table lamp with a leaded stained-glass shade in amber, violet and rose, glowing on a bronze foot. |
| 93 | **Gilded Marble Hearth** (`CN-LGT-002`) | 5 Extremely Rare | 27,200 | Britain | floor | A small hearth of sand-gold marble, a flame dancing behind carved scrollwork and a gleaming trim. |
| 99 | **Fieldstone Home Hearth** (`CN-LGT-001`) | 6 Wonder | 59,500 | Britain | floor 1x2 | A tall fieldstone chimney-breast with a log fire laid in the grate and a timber mantel above, the heart of a warm, lived-in house. |

### Study & Observatory (11 pieces)

Shelves, tomes, stacks of books and a town map, bookcases and a drafting table, a brass telescope and a brass orrery.

![Study & Observatory](cosmetic-rewards/gold-sink/wing-STUDY.png)

Real-client shots: [GS-STUDY-01](cosmetic-rewards/client-shots/GS-STUDY-01.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 13 | **Brace of Old Books** (`CR-LIB-008`) | 1 Common | 1,750 | later | tabletop | Two old books, one russet and one gilt-edged, casually laid together. |
| 14 | **Open Illuminated Tome** (`CN-LIB-015`) | 1 Common | 1,900 | later | tabletop | A great book lying open, its pages edged in gold and one corner of vellum curling up. |
| 15 | **Pale Pine Shelves** (`CR-TBL-042`) | 1 Common | 1,950 | Britain | floor | A tall set of shelves in unstained pine, still smelling of fresh sawdust. |
| 38 | **Heaped Stack of Books** (`CN-LIB-016`) | 2 Uncommon | 3,650 | later | tabletop | A teetering heap of books in blue, rose and green, topped with a ribbon-bound folio. |
| 39 | **Map of Moonglow** (`CN-LIB-005`) | 2 Uncommon | 3,400 | later | tabletop | A map of Moonglow and its sea-wrapped island, with the scholars' tower marked in red. |
| 40 | **Tall Stack of Books** (`CR-LIB-011`) | 2 Uncommon | 3,450 | Britain | floor | A leaning tower of books in faded reds and blues, one good sneeze from collapse. |
| 60 | **Apothecary Bookcase** (`CN-TBL-014`) | 3 Scarce | 7,050 | later | floor | A tall bookcase of red-brown wood crowded with tomes, with coloured flasks on the top shelf. |
| 61 | **Scholar's Bookshelf and Mortar** (`CN-TBL-016`) | 3 Scarce | 7,200 | Britain | floor | A small bookshelf stacked with tomes, a pestle and mortar on top and a heap of red volumes at its foot. |
| 81 | **Brass Telescope on Tripod** (`CN-LIB-001`) | 4 Rare | 14,100 | Britain | floor | A long brass telescope on a three-legged stand of dark wood, aimed at the night sky or at a ship on the horizon. |
| 82 | **Cartographer's Drafting Table** (`CN-LIB-013`) | 4 Rare | 13,600 | later | floor | A tilting drafting table with a half-drawn chart pinned to the board and a pair of brass dividers laid across it. |
| 94 | **Brass Orrery** (`CN-LIB-002`) | 5 Extremely Rare | 28,250 | later | floor | A tiered brass orrery on a round marble-and-brass base, with golden worlds hung on arms about a bright centre. |

### Walls & Hangings (12 pieces)

Drapes, tapestries and a painted ship, then curtained portraits and galleries, up to the eight-tapestry Hall of the Eight Virtues and the Grand Gallery.

![Walls & Hangings](cosmetic-rewards/gold-sink/wing-WALLS.png)

Real-client shots: [GS-WALLS-01](cosmetic-rewards/client-shots/GS-WALLS-01.png), [GS-WALLS-02](cosmetic-rewards/client-shots/GS-WALLS-02.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 16 | **Blue Velvet Drape** (`CR-WLH-017`) | 1 Common | 2,250 | Britain | wall | The same heavy drape, dyed a rich ocean blue. |
| 17 | **Green Velvet Drape** (`CR-WLH-018`) | 1 Common | 2,300 | later | wall | The same heavy drape, dyed a deep forest green. |
| 41 | **Gold-and-Green Floral Tapestry** (`CR-WLH-013`) | 2 Uncommon | 4,300 | Britain | wall 2x1 | Gold blossoms on a deep green ground, woven so closely the cloth seems to glow. |
| 42 | **Midnight Blossom Tapestry** (`CR-WLH-014`) | 2 Uncommon | 4,350 | later | wall 2x1 | Pale blossoms drift across a ground as dark as a moonless night. |
| 43 | **Round Painting of a Ship** (`CN-WLH-008`) | 2 Uncommon | 4,050 | later | wall | An oval painting of a tall ship in full sail under a stormy sky, framed in dark wood and brass. |
| 62 | **Curtained Portrait** (`CR-WLH-031`) | 3 Scarce | 8,550 | Britain | wall 3x1 | A gentleman's portrait framed between two long red drapes, like a window onto the past. |
| 63 | **Portrait Between Sconces** (`CR-WLH-030`) | 3 Scarce | 8,300 | later | wall 3x1 | A lady in crimson, lit from either side by a candle in an iron wall sconce. |
| 83 | **Hall of Ancestors** (`CR-WLH-037`) | 4 Rare | 16,900 | later | wall 5x1 | Five generations of a proud family, frame to frame along a single wall. |
| 84 | **Tapestry of Sosaria** (`CN-WLH-018`) | 4 Rare | 14,600 | later | wall | A gold-bordered tapestry woven with a map of old Sosaria, the land that came before Britannia. |
| 85 | **Velvet Gallery** (`CR-WLH-038`) | 4 Rare | 17,400 | later | wall 5x1 | Three ladies in green, gold and crimson, framed at either end by tall velvet drapes. |
| 95 | **Hall of the Eight Virtues** (`CN-WLH-017`) | 5 Extremely Rare | 35,750 | later | wall 8x1 | All eight virtue tapestries hung side by side in the order of the old teaching, a pilgrim's shrine wall. |
| 100 | **Grand Gallery** (`CR-WLH-039`) | 6 Wonder | 73,500 | later | wall 8x1 | A gentleman, a gold-and-green tapestry and a lady in crimson, lit by sconces and framed by velvet drapes. |

### Hall Curios (11 pieces)

Vases and urns, three longcase clocks, a canary cage, a hanging fern, a white orchid, an hourglass stand and a gilded armillary sphere.

![Hall Curios](cosmetic-rewards/gold-sink/wing-CURIOS.png)

Real-client shots: [GS-CURIOS-01](cosmetic-rewards/client-shots/GS-CURIOS-01.png).

| No. | Piece (id) | Rarity | Price | Sold | Placement | What it is |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | **Grey Patterned Vase** (`CN-CUR-013`) | 1 Common | 1,850 | Britain | floor | A big stoneware vase glazed grey and etched all round with a band of tiny patterns. |
| 19 | **Large Clay Urn** (`CR-CUR-008`) | 1 Common | 2,150 | later | floor | A wide-bellied clay urn banded with shadows, big enough to hold a season's grain. |
| 20 | **Marble Hourglass Stand** (`CN-CUR-001`) | 1 Common | 2,250 | later | floor | A tall hourglass of red sand in a gilded frame, set on a marble stand where all may watch their time run out. |
| 44 | **Canary Cage** (`CN-ANM-002`) | 2 Uncommon | 4,250 | later | tabletop | A black iron cage holding a bright yellow canary that sings the morning in. |
| 45 | **Hanging Staghorn Fern** (`CN-FLO-006`) | 2 Uncommon | 3,600 | later | wall | A staghorn fern mounted on a board, its roots trailing and its fronds spread like antlers. |
| 46 | **Oak Longcase Clock** (`CN-CUR-003`) | 2 Uncommon | 3,700 | Britain | floor | A plain oak longcase clock with a brass pendulum, the sort of timepiece that outlives three generations of owners. |
| 64 | **Cobalt Spiral Urn** (`CN-CUR-017`) | 3 Scarce | 7,800 | later | floor | The great spiral urn in a deep cobalt glaze, with the white spiral standing out like a thumbprint in a pool. |
| 65 | **Walnut Longcase Clock** (`CN-CUR-002`) | 3 Scarce | 7,700 | Britain | floor | A tall walnut clock, carved at the foot and the hood, ticking out the hours in a voice like a heartbeat. |
| 66 | **White Orchid on a Stand** (`CN-FLO-009`) | 3 Scarce | 6,950 | later | floor | A spray of white orchids nodding over a wrought plant stand, a gift for a lady's solar. |
| 86 | **Ivory Longcase Clock** (`CN-CUR-004`) | 4 Rare | 14,350 | later | floor | A white-lacquered longcase clock with a gilded face and a pendulum that glints in the lamplight. |
| 96 | **Gilded Armillary Sphere** (`CN-CUR-007`) | 5 Extremely Rare | 30,400 | later | floor | A sphere of gleaming gold rings, the kind of instrument that a royal astronomer would be forgiven for guarding with his life. |

## Collections

Every piece belongs to exactly one collection: a themed room to build over time. They are names and shop windows only; owning a collection grants nothing. "Cost" is in price units (1 unit = the Common anchor price).

| Collection | Pieces | Rarities | Wings | Cost units | Contents |
| --- | --- | --- | --- | --- | --- |
| **The Gallery** | 7 (1 on sale) | 3-6 | Walls | 83 | Curtained Portrait, Portrait Between Sconces, Hall of Ancestors, Tapestry of Sosaria, Velvet Gallery, Hall of the Eight Virtues, Grand Gallery |
| **The Great Carpets** | 6 (4 on sale) | 3-6 | Rugs | 79 | Golden Arabesque Carpet, Blue Floral Carpet, Lunar Phases Rug, Navy Medallion Carpet, Slate Dragon Rug, Great Hall Carpet |
| **The Dining Hall** | 9 (6 on sale) | 1-6 | Dining | 77 | Round Linen-Draped Table, Rustic Plank Table, Cider and Ale Table, Linen-Topped Table, Plank-Top Dining Table, Candlelit Dinner Table, Long Banquet Table, Marble Banquet Table, Great Hall Table |
| **The Hearthside** | 4 (4 on sale) | 3-6 | Hearth | 63 | Slate-Roofed Hearth, Gray Brick Fireplace, Gilded Marble Hearth, Fieldstone Home Hearth |
| **The Parlour** | 11 (4 on sale) | 1-5 | Parlour | 49 | Pale Pine Chair, Pale Plank Bench, Tall-Backed Linen Chair, Crimson Studded Armchair, Paneled Oak Armchair, Ribboned Linen Chair, High-Backed Oak Settle, Long Velvet Sofa, Black Leather Sofa, Four-Seat Settle, Gnarled Root Throne |
| **The Master Bedchamber** | 5 (3 on sale) | 3-5 | Bedchamber | 44 | Linen Four-Poster Bed, Azure Carved Bed, Crimson Canopied Bed, Feather-Down Four-Poster, Midnight Carved Bed |
| **The Observatory** | 4 (1 on sale) | 2-5 | Curios, Study | 42 | Map of Moonglow, Brass Telescope on Tripod, Brass Orrery, Gilded Armillary Sphere |
| **The Kitchen and Cellar** | 7 (0 on sale) | 1-5 | Dining | 37 | Pewter Stew Pot, Cast-Iron Stove, Pie Safe, Cellarmaster's Table, Silver-Framed Wine Cabinet, Kitchen Pump Counter, Marble Bar with Sink |
| **The Music Room** | 4 (0 on sale) | 2-5 | Parlour | 30 | Cello on a Stand, Blue and Gold Harp, Crimson Lacquer Harpsichord, Ebonwood Harpsichord and Bench |
| **The Library** | 8 (3 on sale) | 1-4 | Study | 23 | Brace of Old Books, Open Illuminated Tome, Pale Pine Shelves, Heaped Stack of Books, Tall Stack of Books, Apothecary Bookcase, Scholar's Bookshelf and Mortar, Cartographer's Drafting Table |
| **The Entrance Hall** | 7 (3 on sale) | 1-4 | Curios | 21 | Grey Patterned Vase, Large Clay Urn, Marble Hourglass Stand, Oak Longcase Clock, Cobalt Spiral Urn, Walnut Longcase Clock, Ivory Longcase Clock |
| **The Lamplit Room** | 7 (2 on sale) | 1-4 | Hearth | 20 | Amber Globe Lamp, Wrought Taper Stand, Silk-Shaded Floor Lamp, Songbird Globe Lamp, Twin Blue-Glass Lamp, Dragon-Wrapped Oil Lamp, Stained-Glass Lamp |
| **Runners and Hearth Rugs** | 7 (2 on sale) | 1-3 | Rugs | 16 | Plain Olive Rug, Welcome Mat, Blue Bordered Rug, Crimson Runner, Golden Hall Runner, Crimson Hall Runner, Orange Hearth Rug |
| **The Guest Room and Dressing Room** | 6 (2 on sale) | 1-3 | Bedchamber | 12 | Linen Small Bed, Plank Bed, Carved Rosewood Bed, Elven Wash Basin, Mahogany Chest of Drawers, Mirrored Vanity |
| **Drapes and Tapestries** | 5 (2 on sale) | 1-2 | Walls | 8 | Blue Velvet Drape, Green Velvet Drape, Gold-and-Green Floral Tapestry, Midnight Blossom Tapestry, Round Painting of a Ship |
| **The Conservatory** | 3 (0 on sale) | 2-3 | Curios | 8 | Canary Cage, Hanging Staghorn Fern, White Orchid on a Stand |

## Where the pieces are sold

### The Furnisher

One new NPC type, the **Furnisher** ("the Crown's furnisher", owner's ruling: a new NPC, not an existing trade), using the stock vendor window: item graphic, name, price, ordinary gold. It **never buys** from players (empty sell list), so there is no resale path. Its stock comes from a data file (`furnishers.json`: shop, piece, price), so adding a piece or changing a price is a data change, not code. Ordinary vendors' stock lists are untouched. For now there is **one Furnisher, in Britain**, inside the Showroom Hall, in a surveyed, publicly reachable spot outside any Hot Zone, like the approved destination vendor. Everything it carries is always on sale.

### The Britain selection

The owner asked for **a selection of each rarity**. The rule used: **one piece from every wing at each of Common, Uncommon and Scarce (eight each), then six Rare, four Extremely Rare and three Wonders** spread across the wings, so a buyer can furnish a bedchamber, a parlour, a dining room, a hearth, a study, a wall and a hall carpet entirely from this one shop, at every price point. The three Wonders are the Great Hall Table, the Fieldstone Home Hearth and the Great Hall Carpet; the fourth, the Grand Gallery, waits for a later vendor. The list is a data file (`gold-sink/vendors.json`); swapping any piece is a one-line change.

| Rarity | Wing | Piece (id) | Price |
| --- | --- | --- | --- |
| 1 Common | Bedchamber | **Plank Bed** (`CR-FRN-037`) | 2,050 gp |
| 1 Common | Parlour | **Pale Pine Chair** (`CR-FRN-011`) | 1,900 gp |
| 1 Common | Dining | **Rustic Plank Table** (`CR-TBL-011`) | 2,150 gp |
| 1 Common | Rugs | **Plain Olive Rug** (`CR-RUG-002`) | 2,200 gp |
| 1 Common | Hearth | **Wrought Taper Stand** (`CN-LGT-020`) | 1,850 gp |
| 1 Common | Study | **Pale Pine Shelves** (`CR-TBL-042`) | 1,950 gp |
| 1 Common | Walls | **Blue Velvet Drape** (`CR-WLH-017`) | 2,250 gp |
| 1 Common | Curios | **Grey Patterned Vase** (`CN-CUR-013`) | 1,850 gp |
| 2 Uncommon | Bedchamber | **Carved Rosewood Bed** (`CN-FRN-016`) | 4,450 gp |
| 2 Uncommon | Parlour | **Paneled Oak Armchair** (`CR-FRN-010`) | 4,000 gp |
| 2 Uncommon | Dining | **Cider and Ale Table** (`CR-FOO-039`) | 4,400 gp |
| 2 Uncommon | Rugs | **Crimson Runner** (`CR-RUG-010`) | 4,600 gp |
| 2 Uncommon | Hearth | **Silk-Shaded Floor Lamp** (`CN-LGT-015`) | 4,100 gp |
| 2 Uncommon | Study | **Tall Stack of Books** (`CR-LIB-011`) | 3,450 gp |
| 2 Uncommon | Walls | **Gold-and-Green Floral Tapestry** (`CR-WLH-013`) | 4,300 gp |
| 2 Uncommon | Curios | **Oak Longcase Clock** (`CN-CUR-003`) | 3,700 gp |
| 3 Scarce | Bedchamber | **Linen Four-Poster Bed** (`CR-FRN-028`) | 8,700 gp |
| 3 Scarce | Parlour | **High-Backed Oak Settle** (`CR-FRN-026`) | 8,200 gp |
| 3 Scarce | Dining | **Plank-Top Dining Table** (`CR-TBL-013`) | 8,800 gp |
| 3 Scarce | Rugs | **Golden Arabesque Carpet** (`CR-RUG-012`) | 9,050 gp |
| 3 Scarce | Hearth | **Slate-Roofed Hearth** (`CN-LGT-003`) | 7,550 gp |
| 3 Scarce | Study | **Scholar's Bookshelf and Mortar** (`CN-TBL-016`) | 7,200 gp |
| 3 Scarce | Walls | **Curtained Portrait** (`CR-WLH-031`) | 8,550 gp |
| 3 Scarce | Curios | **Walnut Longcase Clock** (`CN-CUR-002`) | 7,700 gp |
| 4 Rare | Bedchamber | **Feather-Down Four-Poster** (`CR-FRN-029`) | 16,100 gp |
| 4 Rare | Parlour | **Four-Seat Settle** (`CR-FRN-027`) | 16,400 gp |
| 4 Rare | Dining | **Long Banquet Table** (`CR-TBL-007`) | 17,150 gp |
| 4 Rare | Rugs | **Blue Floral Carpet** (`CR-RUG-020`) | 17,900 gp |
| 4 Rare | Hearth | **Gray Brick Fireplace** (`CR-LGT-037`) | 16,650 gp |
| 4 Rare | Study | **Brass Telescope on Tripod** (`CN-LIB-001`) | 14,100 gp |
| 5 Extremely Rare | Bedchamber | **Midnight Carved Bed** (`CN-FRN-019`) | 31,450 gp |
| 5 Extremely Rare | Dining | **Marble Banquet Table** (`CR-TBL-022`) | 34,650 gp |
| 5 Extremely Rare | Rugs | **Slate Dragon Rug** (`CN-RUG-004`) | 36,800 gp |
| 5 Extremely Rare | Hearth | **Gilded Marble Hearth** (`CN-LGT-002`) | 27,200 gp |
| 6 Wonder | Dining | **Great Hall Table** (`CR-TBL-010`) | 66,500 gp |
| 6 Wonder | Rugs | **Great Hall Carpet** (`CR-RUG-023`) | 80,000 gp |
| 6 Wonder | Hearth | **Fieldstone Home Hearth** (`CN-LGT-001`) | 59,500 gp |

The other 63 pieces are not on sale yet. The first draft's idea was a specialist in each of eight towns, one per wing, selling that wing's whole ladder; that stays on file as the likely shape, but **other vendors are not being designed now** (owner's ruling), so this document stops at Britain.

### The Showroom Hall (owner's ruling: the preview is a hall, not a window)

The stock vendor window shows one graphic per item. For a **single-graphic piece** (a chair, a lamp, a clock, a shelf) that icon is the whole piece, so it needs no deed and **no place on the showroom floor**. A **multi-tile piece** that arrives as a deed (a bed, a table, a rug, a hearth) would show as a single tile or a deed icon, so those are the ones to **show the real thing**:

* A hall in Britain with **the 23 deed pieces of the Britain selection on display** (the 14 single-graphic pieces are seen by their vendor icon, and can stand in the hall as dressing only if there is room), arranged as furnished rooms (a bedchamber, a dining room, a hearth room, a carpet hall), so a buyer sees how pieces go together and what a room costs. The Furnisher stands in the middle with the buy window. When other vendors open, their deed pieces join the hall.
* Display copies are the same classes as the sale items but **immovable, not lockable, not deedable and not stealable**, so they cannot be taken or moved by anyone. Each shows its name and its rarity when hovered or single-clicked.
* The hall is **generated from the same data** as the real-client photo pages (parts, offsets, facings), by a placement file loaded at startup that creates or repairs the display copies idempotently. Adding a piece to the selection adds it to the hall; nothing is hand-placed.
* **Size:** the 23 deed pieces cover about 62 floor tiles of furniture and 145 tiles of rugs (the Great Hall Carpet alone is an 8 by 6 patch), and about 5 tiles of wall frontage for the tapestry and the portrait: 207 tiles of floor with nothing overlapping, about 310 tiles with a walkway round each group.
* **Site (owner's choice): the Counselor's Guild (east).** The [site survey](cosmetic-rewards/gold-sink/showroom-sites/Showroom-Site-Survey.md) measured eight Britain buildings and photographed them in the real client. The east guild hall is an L-shaped plaster-and-timber hall of about 211 floor tiles in three rooms with one double door. After an arrangement pass the **whole Britain selection fits inside, one of each piece with nothing repeated**: all 23 deed pieces and all 14 single pieces, arranged as rooms: the **Great Hall** (carpet, table, long banquet table) by the door, a **hearth wall** with all four hearths side by side against the west wall and a lounge in front, a **dining room and study**, and a **bedchamber** with the five beds in a row. Only the **Crimson Runner** lies outside, across the cobblestones in front of the door. The layout is held as data and checked by a planner (floor, walls, doorways, reachability) and photographed in the real client. The hall data lives with the shard's own world data, never the stock generators; nothing needs to be cleared from the building (it holds only a chimney, a bookcase and a lamp post).
* The hall's display copies cost nothing to run and add no gameplay; they are the shop window.

### Buying and what the player gets

* **Single-graphic pieces** (52 of the 100; 14 of the Britain 37) are one ordinary item: the vendor-window icon is the whole piece, the buyer carries it into their house and locks it down, and it needs no deed.
* **Multi-tile pieces** (48 of the 100; 23 of the Britain 37: beds, tables, settles, rugs, hearths, hangings) are sold as **addon deeds**: the stock deed-to-addon mechanic (place on a target, house owner can re-deed). One data-driven addon class builds any of them from the catalog's part list (graphic, offset, hue), so there are not 100 C# classes. 70 pieces have a second facing; the stock 'turn' mechanic is used.
* The buy is **atomic**: check funds, take the gold, create the item, all in one server step. A refusal charges nothing. Persisted through save and restart.
* **Provenance:** each item carries its catalog id (`CR-...` or `CN-...`) as a hidden persistent tag for staff diagnostics and for the duplicate guard. The **rarity name and collection** appear on the item's property list (proposed; it is what the hall's display copies show).
* **Tradable and lootable** (owner's ruling): bought pieces are ordinary tradable goods, no account binding, no salvage and no NPC resale. A piece in a backpack can be stolen; a piece locked down in a house cannot.

### Placing, moving and turning pieces

This is how the stock server already works, which is the UOR way, plus one later tool.

* **A single-graphic piece** (a chair, a lamp, a vase, a clock): carry it into your house, drop it on the floor, on a table, or on a wall tile where it belongs, then say **"I wish to lock this down"** and target it. A locked-down piece costs **one lockdown** of the house's allowance, which runs from 425 for a small house to 4,076 for a castle (stock values for this ruleset), so a whole collection fits.
* **To move one**: say **"I wish to release this"**, target it, pick it up, drop it somewhere else, and lock it down again.
* **A multi-tile piece** (a bed, a table, a hearth, a rug, a gallery) arrives as a **deed**. Double-click the deed, target a spot in your house, and the whole piece appears, already fixed in place. **Addons cost no lockdowns** in this ruleset (they sit in the house's addon list), so a 48-tile carpet is free to hold. To move one, the house owner **chops it with an axe or hatchet** and it turns back into the deed in their pack; place it again where you like. Nothing is lost.
* **Turning** (east to south): there was no turning tool in 2000. The period way was to choose the facing when you bought or made the piece: the stock T2A carpentry menu lists a South deed and an East deed for beds, forges and anvils. That would double the vendor list for the **70 of the 100 that have a second facing**, so the proposal uses the later-era answer instead. is the **Interior Decorator** (Age of Shadows, 2003), which the stock server already has: use it on a locked-down piece to **Turn** it, and to nudge it **Up or Down** a step (handy for stacking a lamp on a table). It is sold by the **Architect** for 10,001 gp, and **it stays on sale** (owner's ruling); the shard's vendor spawns already include an Architect in Britain (a spawner at 1430, 1597 that lists a Carpenter, an Architect and a Real Estate Broker). Our data-driven classes would carry the stock flip hooks so the tool works on every piece that has a second facing.
* **What there is not:** no free x/y nudge. Some other shards redesigned the decorator so it also moves pieces sideways; that is a custom feature, not stock, and it is **not proposed**. A small convenience that is in reach: the shard already has a hook for custom right-click menu entries (it carries the Execute entry), so **right-click "Lock Down" and "Release"** on pieces in your own house (an AoS-era convenience) would be a small shard-owned item if the owner wants it. Not part of this proposal unless asked.

## The price curve

All prices are the owner's. This is the framework and a worked example at his **2,000 gp base with a 80,000 gp ceiling**, not a proposal of final numbers. **The curve was toned down on 2026-10-08:** the first ladder (1 : 3 : 8 : 22 : 60 : 150) made a Wonder cost 150,000 and the whole set nearly four million; the new one roughly doubles at each rarity and the dearest piece in the shop is 80,000.

**Rule:** `price = base × rarity multiplier × (0.85 + 0.30 × position)`, rounded to 50 and never above 80,000, where `position` runs from 0 (plainest in its rarity) to 1 (coolest in its rarity) by coolness score. So a piece is within 15% of its rarity's price, and a cool Common costs a little more than a dull Common but never as much as an Uncommon. Only the coolest Wonder (the Great Hall Carpet) reaches the ceiling.

Curves compared (multiplier per rarity, the Wonder's centre price, and what one of every piece would cost at the 2,000 gp base under the ceiling):

| Curve | 1 Common | 2 Uncommon | 3 Scarce | 4 Rare | 5 Extremely Rare | 6 Wonder | Wonder centre | Whole set |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Flatter | x1 | x1.5 | x2.5 | x5 | x10 | x25 | 50,000 gp | 818,000 gp |
| **Suggested** | x1 | x2 | x4 | x8 | x16 | x35 | 70,000 gp | 1,223,500 gp |
| Steeper | x1 | x3 | x6 | x12 | x24 | x40 | 80,000 gp | 1,700,000 gp |

All three use the 2,000 gp base and the within-rarity spread, and none sells anything above the 80,000 gp ceiling (the Steeper curve's two coolest Wonders are held down to it).

For scale: starter gold is 500, and the stock houses (this ruleset) run from 43,800 for a small house through 192,400 (two-story) and 433,200 (tower) to 1,022,800 for a castle. On the suggested ladder: a **Common is about 2,000 gp** (four starter purses), a **Rare about 16,000** (a third of a small house), an **Extremely Rare about 32,000** (three quarters of one) and a **Wonder 60,000 to 80,000** (about one and a half small houses). The whole set of 100 is **1,223,500 gp**, a little more than one castle; the Britain selection is **549,350 gp**. [Gold-Sink-Items.csv](cosmetic-rewards/gold-sink/Gold-Sink-Items.csv) is the pricing worksheet (it carries these illustrative prices and where each piece is sold; the `price` column is blank for the owner's final numbers), and the [pricing sandbox](cosmetic-rewards/gold-sink/pricing-sandbox.html) previews any curve and exports prices.

Pricing is data (`furnishers.json`). A change takes a config deploy, not a code change, and the validator refuses to enable the shop while any listed piece has no price.

**Sizing the sink** is the owner's lever and can be watched live: staff `[FurnisherStatus` will show gold removed per rarity. Raise or lower the base price, the multipliers or the ceiling as the numbers come in. Resale between players is allowed, so the vendor price is the floor for the top rarities and only the first sale of each piece removes gold. With no rotation or allowance, nothing limits how fast a rich player buys the top of the shop; the price is the only pacing.

## Gold-sink integrity

* The vendor **never buys**; no NPC resale, buyback, salvage, deed-for-gold or crafting-resource value (zero or negligible, as in 15.12A). Re-deeding returns the same deed, never gold.
* **Atomic purchase**: gold, item and persistence in one step; a failure charges nothing and never mints twice; restarts and saves cannot duplicate a piece.
* **No remote buying**; normal interaction range, living and valid-interaction checks.
* **No power**: nothing sold has any function. Bed-looking, stove-looking and chest-looking pieces are stripped of sleep, regen, cooking and storage.
* **Display copies are inert**: immovable, not lockable, not deedable, not stealable, not sellable.
* **Staff-created pieces** are logged.
* **Market risks accepted:** hoarding is harmless (stock is unlimited, so nobody can corner a piece); resale premium on the top rarities is expected and good for the sink.

## Era notes

* **58 of the 100 are era-neutral** (`CN-`): art that came after Publish 5 but is generic (harpsichords, longcase clocks, an orrery, an armillary sphere, a telescope, a cast-iron stove, a pie safe), all within the owner's rulings of 2026-10-08, including 1 elven piece (Elven Wash Basin). **42 are era-graded** (4 grade A, 38 grade B). Grade B means the art sits in an era block and shows up on the Britannia map; see [Era-Evidence](cosmetic-rewards/Era-Evidence.md).
* **A strict-era shop is a re-curation, not a swap.** The era-graded furnishing supply is 160 candidates (49 common, 57 uncommon, 35 scarce, 15 rare, 4 extremely rare: Great Hall Carpet, Grand Gallery, Great Hall Table, Marble Banquet Table). Taking the era-graded pieces only would give a shorter, plainer ladder with few pieces at the top, and no clocks, no harpsichords, no telescope or orrery, no stove and no lit hearth except the gray brick fireplace. The table below lists, for each neutral piece, the nearest era-graded candidate in the same catalog category (a mechanical suggestion from `selection.json`; many are not like-for-like), so the owner can see what the swap would cost.
* **Felucca map season** is Desolation, which hides leaf tiles; no picked piece depends on leaves (the hanging fern and the white orchid were checked in the real client and show).
* **Animated or lit art** (the four hearths and fireplaces, the oil lamp, the stained-glass lamp, the stove) is shown still-frame in the showroom shots; confirm the animation in the buy phase.

<details>
<summary>Nearest era-graded candidate for each of the 58 era-neutral pieces (mechanical suggestion)</summary>

| Neutral piece | Rarity | Nearest era-graded candidate |
| --- | --- | --- |
| Tall-Backed Linen Chair (`CN-FRN-008`) | 1 Common | Folded Wool Blanket (`CR-FRN-044`) |
| Pewter Stew Pot (`CN-ALC-006`) | 1 Common | none found |
| Round Linen-Draped Table (`CN-TBL-005`) | 1 Common | Dark Oak Dining Table (`CR-TBL-008`) |
| Welcome Mat (`CN-RUG-011`) | 1 Common | Woven Reed Mat (`CR-RUG-024`) |
| Amber Globe Lamp (`CN-LGT-017`) | 1 Common | Tall Pillar Candle (`CR-LGT-001`) |
| Wrought Taper Stand (`CN-LGT-020`) | 1 Common | Guttered Candle Stub (`CR-LGT-002`) |
| Open Illuminated Tome (`CN-LIB-015`) | 1 Common | Scrolls with Blue Ribbon (`CR-LIB-024`) |
| Grey Patterned Vase (`CN-CUR-013`) | 1 Common | Dirty Iron Pot (`CR-CUR-002`) |
| Marble Hourglass Stand (`CN-CUR-001`) | 1 Common | Jade Pylon (`CR-CUR-026`) |
| Carved Rosewood Bed (`CN-FRN-016`) | 2 Uncommon | Marble Garden Bench (`CR-FRN-021`) |
| Elven Wash Basin (`CN-TBL-018`) | 2 Uncommon | Pedestal Side Table (`CR-TBL-005`) |
| Cello on a Stand (`CN-MUS-005`) | 2 Uncommon | Loose Sheet Music (`CR-MUS-015`) |
| Crimson Studded Armchair (`CN-FRN-001`) | 2 Uncommon | Marble Bench (`CR-FRN-018`) |
| Ribboned Linen Chair (`CN-FRN-007`) | 2 Uncommon | Bamboo Cot (`CR-FRN-043`) |
| Cast-Iron Stove (`CN-CMP-007`) | 2 Uncommon | none found |
| Pie Safe (`CN-FOO-022`) | 2 Uncommon | Poached Salmon (`CR-FOO-008`) |
| Silk-Shaded Floor Lamp (`CN-LGT-015`) | 2 Uncommon | Candle Wall Sconce (`CR-LGT-024`) |
| Songbird Globe Lamp (`CN-LGT-013`) | 2 Uncommon | Iron Tripod Brazier (`CR-LGT-026`) |
| Twin Blue-Glass Lamp (`CN-LGT-016`) | 2 Uncommon | Violet Hanging Lantern (`CR-LGT-018`) |
| Heaped Stack of Books (`CN-LIB-016`) | 2 Uncommon | Illuminated Open Book (`CR-LIB-006`) |
| Map of Moonglow (`CN-LIB-005`) | 2 Uncommon | Blue-Ribbon Ledger (`CR-LIB-010`) |
| Round Painting of a Ship (`CN-WLH-008`) | 2 Uncommon | Portrait of a Lady in Green (`CR-WLH-004`) |
| Canary Cage (`CN-ANM-002`) | 2 Uncommon | none found |
| Hanging Staghorn Fern (`CN-FLO-006`) | 2 Uncommon | none found |
| Oak Longcase Clock (`CN-CUR-003`) | 2 Uncommon | Scrub Brush (`CR-CUR-004`) |
| Mirrored Vanity (`CN-TBL-011`) | 3 Scarce | Open Mahogany Armoire (`CR-TBL-034`) |
| Blue and Gold Harp (`CN-MUS-003`) | 3 Scarce | none found |
| Long Velvet Sofa (`CN-FRN-005`) | 3 Scarce | Long Courtyard Bench (`CR-FRN-020`) |
| Silver-Framed Wine Cabinet (`CN-FOO-021`) | 3 Scarce | Chicken on a Spit (`CR-FOO-002`) |
| Dragon-Wrapped Oil Lamp (`CN-LGT-011`) | 3 Scarce | Emerald-Flame Brazier (`CR-LGT-027`) |
| Slate-Roofed Hearth (`CN-LGT-003`) | 3 Scarce | Moonfire Brazier (`CR-LGT-028`) |
| Apothecary Bookcase (`CN-TBL-014`) | 3 Scarce | Marble Pedestal (`CR-TBL-043`) |
| Scholar's Bookshelf and Mortar (`CN-TBL-016`) | 3 Scarce | Marble Table (`CR-TBL-021`) |
| Cobalt Spiral Urn (`CN-CUR-017`) | 3 Scarce | Sandstone Pylon (`CR-CUR-022`) |
| Walnut Longcase Clock (`CN-CUR-002`) | 3 Scarce | none found |
| White Orchid on a Stand (`CN-FLO-009`) | 3 Scarce | none found |
| Azure Carved Bed (`CN-FRN-018`) | 4 Rare | Rumpled Four-Poster (`CR-FRN-032`) |
| Crimson Canopied Bed (`CN-FRN-015`) | 4 Rare | Grey Stone Bench (`CR-FRN-019`) |
| Black Leather Sofa (`CN-FRN-003`) | 4 Rare | Sandstone Garden Bench (`CR-FRN-022`) |
| Crimson Lacquer Harpsichord (`CN-MUS-014`) | 4 Rare | none found |
| Candlelit Dinner Table (`CN-FOO-016`) | 4 Rare | Bottles of Wine (`CR-FOO-020`) |
| Kitchen Pump Counter (`CN-FOO-018`) | 4 Rare | Bottles of Liquor (`CR-FOO-021`) |
| Lunar Phases Rug (`CN-RUG-001`) | 4 Rare | Grand Crimson Carpet (`CR-RUG-021`) |
| Stained-Glass Lamp (`CN-LGT-014`) | 4 Rare | Roasting Spit (`CR-LGT-034`) |
| Brass Telescope on Tripod (`CN-LIB-001`) | 4 Rare | Brass Sextant (`CR-LIB-030`) |
| Cartographer's Drafting Table (`CN-LIB-013`) | 4 Rare | Crimson Folio (`CR-LIB-007`) |
| Tapestry of Sosaria (`CN-WLH-018`) | 4 Rare | Lit Hall of Emblems (`CR-WLH-036`) |
| Ivory Longcase Clock (`CN-CUR-004`) | 4 Rare | none found |
| Midnight Carved Bed (`CN-FRN-019`) | 5 Extremely Rare | Rough-Hewn Log Bench (`CR-FRN-023`) |
| Ebonwood Harpsichord and Bench (`CN-MUS-002`) | 5 Extremely Rare | none found |
| Gnarled Root Throne (`CN-FRN-011`) | 5 Extremely Rare | Azure Bolster Pillow (`CR-FRN-050`) |
| Marble Bar with Sink (`CN-FOO-020`) | 5 Extremely Rare | Jugs of Cider (`CR-FOO-018`) |
| Slate Dragon Rug (`CN-RUG-004`) | 5 Extremely Rare | Orange Hall Runner (`CR-RUG-018`) |
| Gilded Marble Hearth (`CN-LGT-002`) | 5 Extremely Rare | Flanking Braziers (`CR-LGT-044`) |
| Brass Orrery (`CN-LIB-002`) | 5 Extremely Rare | Rolled Map (`CR-LIB-028`) |
| Hall of the Eight Virtues (`CN-WLH-017`) | 5 Extremely Rare | Great Hall Tapestries (`CR-WLH-034`) |
| Gilded Armillary Sphere (`CN-CUR-007`) | 5 Extremely Rare | none found |
| Fieldstone Home Hearth (`CN-LGT-001`) | 6 Wonder | Sapphire-Flame Coal Brazier (`CR-LGT-046`) |

</details>

## Where it fits

Not on the roadmap. The roadmap's Beta order stands (house zoning, rotating Hot Dungeon and camping in 2b; Expeditions, cargo, Pilgrimage in 2c; ...) and nothing here is pulled forward unasked. It is independent of every other system: it needs only housing, gold and the stock vendor window. A natural slot is **after Beta 2b's house zoning** (so the furnishings land with the housing rules settled) or alongside Beta 2c's Expedition work (it shares the vendor pattern and the "gold sink" purpose). It ships behind its own flag, **off**, like every feature: a new flag `furnishers` in `shard-rules.json`, enabled only on the owner's explicit say-so, and not before prices are filled in.

## Work plan (after sign-off)

**Design:** this document.

**Changes (when approved).** One phase now that the weekly window, the allowance and the catalogue window are out:

* `src/BritanniaRenaissance.Content/Furnishers.cs`: the Furnisher NPC (one, in Britain), its stock list (data-driven from the Britain selection), the hall's display copies, `[FurnisherStatus`.
* `src/BritanniaRenaissance.Content/FurnisherDecor.cs`: the data-driven furnishing item, addon and deed classes (parts, hues, facings, stripped functions, the stock flip hooks so the Interior Decorator can turn them), plus the inert display variant.
* `data/configuration/furnishers.json` (the Britain selection, rarities, prices, ceiling) with a validator class like the other configuration validators; generated `data/furnisher-catalog.json` and the hall's placement file from the catalog tooling; a `furnishers` flag in `shard-rules.json` and its validator.
* Showroom Hall placement data in the shard's world data, after the building is surveyed; README lines for players when it deploys; deploy through `Deploy-Alpha1Baseline.ps1`.
* ModernUO: none expected; checked at the code review.

**Verification:**

* Tests: every id in the catalog, tiers and counts as designed, prices present and rising by rarity, the vendor never buys, deed round trip, display copies inert, the placement file idempotent, flip hooks present on every piece with a second facing.
* Disposable host: buy one piece of every rarity, place it in a real house (single, addon, wall, surface, floor covering), lock down, release, turn with the Interior Decorator, re-deed with an axe, restart the server and check the saved pieces and the hall.
* **Real client:** the vendor window, the Showroom Hall (each collection vignette) and a furnished house, screenshotted and sent to the owner.
* Navrey scenario for the buy path. A repeat of the raw availability scan against the live server's craft, vendor and loot tables.

**Activation:** flag off until the owner has set prices and acknowledged it. No existing player behavior changes while it is off.

**Deferrals:** every other vendor (the eight-town specialist idea, and the 63 pieces they would carry); a weekly window of Extremely Rare pieces and a Wonder of the Week with a per-account allowance (a clean add-on later: it needs a weekly boundary, a saved ledger and a board); a catalogue window; right-click Lock Down / Release entries; an x/y nudge tool; crafting recipes for any piece; a garden and statuary shop; more pieces from the reserve; any reward-pool use of these ids.

## Decisions for the owner

**Rulings so far (2026-10-08):**

1. Version 1 has no weekly window and no per-account allowance; rarity is the price.
2. A new **Furnisher** NPC.
3. The preview is a **showroom hall** in Britain.
4. The **base price is 2,000 gp**, and the **curve is toned down to top out at 80,000 gp** (all final prices remain the owner's).
5. Pieces are **tradable and lootable**.
6. **One vendor, in Britain, selling a selection of every rarity**; other vendors are not being designed now.
7. The **Interior Decorator stays on sale** at the Architect.
8. The showroom is the **Counselor's Guild (east)**, arranged as rooms with everything inside.

**Still open:**

* **The showroom layout** at the Counselor's Guild (east): the arranged layout in the survey is ready for your eye; where the Furnisher stands (proposed just inside the door); and whether the spare 63 pieces later need a second hall (Bay Side warehouses); see the [site survey](cosmetic-rewards/gold-sink/showroom-sites/Showroom-Site-Survey.md).
* **The Britain selection**: the 37 pieces above are a starting list; swap any, or ask for more or fewer per rarity.
* **Right-click Lock Down / Release** entries for pieces in your own house: build later, or never.
* **Rarity and collection on each item's property list** (proposed yes).
* **Borderline "furnishing" calls to confirm:** the **canary cage, hanging staghorn fern and white orchid** (pets and plants as furnishings), the **cello, harp and three harpsichords** (instruments), the **Gnarled Root Throne**, the **cast-iron stove and pewter stew pot** (kitchen), the **hourglass stand, longcase clocks and gilded armillary sphere** (curios), and the **telescope and orrery** (study instruments, as the owner named the telescope). Anything that fails the owner's eye is a one-line swap.
* **Era-neutral shelf.** Keep the 58 neutral pieces (recommended), or go strict-era, which is a re-curation with a thinner top end.
* **Slot.** After 2b house zoning, with 2c, or later.
* **Later vendors** (the eight specialist towns, or something else) when you want them.

## Files

* Pictures: [overview](cosmetic-rewards/gold-sink/overview.png), per wing `cosmetic-rewards/gold-sink/wing-<WING>.png`, per rarity `cosmetic-rewards/gold-sink/tier-<N>.png`, real-client showroom shots `cosmetic-rewards/client-shots/GS-<WING>-NN.png` ([index](cosmetic-rewards/client-shots/README.md), part 3).
* Data: [selection.json](cosmetic-rewards/gold-sink/selection.json) (the 100 with tier, wing, collection, score, nearest era-graded candidate), [picks.json](cosmetic-rewards/gold-sink/picks.json) (the source of truth), [collections.json](cosmetic-rewards/gold-sink/collections.json), [Gold-Sink-Items.csv](cosmetic-rewards/gold-sink/Gold-Sink-Items.csv) (pricing worksheet), [vendors.json](cosmetic-rewards/gold-sink/vendors.json) (the Britain selection), [pricing-sandbox.html](cosmetic-rewards/gold-sink/pricing-sandbox.html).
* Tools: `tools/cosmetic-catalog/sinkplan.py` (`supply`, `candidates`, `build`, `showroom`; the furnishing rule is `FURNISHING_CATS`, `FURNISHING_EXTRA`, `BLOCK_TAGS`, `BLOCK_WORDS`; the price curve is `BASE_PRICE`, `TIER_UNITS` and `PRICE_CAP`; the Britain selection is `vendors.json`), `availability.py` (`rawscan`), `galleries.py`. Edit `picks.json`, run `sinkplan.py build`, and the sheets and files regenerate; the tables in this document were generated from `selection.json` on 2026-10-08 and must be refreshed by hand if the picks change.
