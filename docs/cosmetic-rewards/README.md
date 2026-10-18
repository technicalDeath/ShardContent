# Cosmetic rewards (house decoration)

A catalog of **1,161 cosmetic, house-placeable reward items** for UO Rekindled, built so that **other systems can pick rewards by id**: Nemesis trophies, the Wanted-monster curator, shipwreck salvage, Expedition town vendors, Pilgrimage, camping, artisan signatures, BOD rewards, Hot Zone drops, seasonal events.

A second, separate section (added 2026-10-08) holds **925 era-neutral rewards** (ids `CN-<CAT>-<NNN>`): objects whose art or concept came after April 2000 but that are generic enough to sit naturally in 2000 Britannia. See "The era-neutral section" below.

Nothing here is implemented in the game. It is a design catalog and a reference. Using any entry as a reward is a separate item that follows the normal plan, sign-off and activation rules. Every pool in `Reward-Pools.md` is a **proposal** for the owner, not a ruling.

Created 2026-10-07 (owner request). Art is read straight from the client data in `UOData`; every picture is the real client art, and every in-game shot is a real ClassicUO screenshot.

## Where things are

| File | What |
| --- | --- |
| [`Cosmetic-Reward-Catalog.md`](Cosmetic-Reward-Catalog.md) | The readable catalog: every reward with its picture, id, tier, placement, graphic ids, tags, era grade, implementation note and suggested pool, grouped into 29 categories (monster figurines, FIG, are the largest with 110). Generated. |
| [`cosmetic-rewards.json`](cosmetic-rewards.json) | The same data for code and agents: one object per reward, including exact client graphics, offsets, hues, rotated facings, the Felucca foliage note and the suggested pool. Generated. |
| [`Era-Neutral-Reward-Catalog.md`](Era-Neutral-Reward-Catalog.md), [`cosmetic-rewards-neutral.json`](cosmetic-rewards-neutral.json) | **The era-neutral section**: 925 rewards (`CN-` ids) outside the era grading but generic in theme (jack-o'-lanterns, weapon racks, ship's wheels, flags, mirrors, necromancy-flavoured skulls and bones, elven furnishings, ...). Generated from `catalog-neutral/`. |
| [`Reward-Pools.md`](Reward-Pools.md), [`reward-pools.json`](reward-pools.json) | **Suggested** allocations to the systems in the Hot-Zones plan: 52 Nemesis species trophies, ten dungeon collections for the Wanted curator, the 12-design shipwreck set, twelve Expedition town collections, shrine tokens, Hot Zone and Hythloth drops, camping, artisan signatures, BOD tiers, seasonal sets. No id is in two pools. |
| [`client-shots/`](client-shots/README.md) | **134 real-client screenshots** (ClassicUO 7.0.117.0; 75 for the main catalog, 47 for the era-neutral section, 12 for the gold-sink showroom): every reward standing on the ground in Felucca, numbered with the number part of its id (showroom pages with the showroom number). The README there is the legend. All figurines, including the 40 added and the 59 neutral ones, were photographed on 2026-10-08. |
| [`gold-sink/`](gold-sink/) | **The gold-sink set (Design Proposal 3):** 100 home furnishings nobody can get today, for sale from Furnisher vendors: `picks.json` (source of truth), `collections.json`, generated `selection.json`, `Gold-Sink-Items.csv` (pricing worksheet), `pricing-sandbox.html` (price-curve playground), and the picture sheets `overview.png`, `wing-<WING>.png`, `tier-<N>.png`. The design is [`../Design-Proposal-3-House-Decoration-Gold-Sink.md`](../Design-Proposal-3-House-Decoration-Gold-Sink.md). |
| `sheets/<CAT>.png` | A labelled contact sheet per category (renders of the client art, with ids and tiers). |
| `images/<CAT>/<id>.png` | One picture per reward (transparent, 2x). `<id>-fel.png` shows an entry as the Felucca client draws it when leaf tiles are hidden. |
| `catalog/<CAT>.json` | The source of truth, one array per category. Edit these, then rebuild. |
| `pools/<pool>.json` | The source of the suggested pools. |
| [`Era-Evidence.md`](Era-Evidence.md) | The era research: what existed by April 2000, with sources and reliability, and what is still unverified. |

Tools are in `ShardContent/tools/cosmetic-catalog/` (`uoart.py` reads the client art and tile data, `catalog.py` validates and builds, `pools.py` validates and builds the pools, `galleries.py` plans and finishes the in-game pages, `Run-GalleryShots.ps1` drives the real client, `flatspots.py` and `staticsusage.py` are survey helpers, `availability.py` finds the graphics the stock game already hands out, `sinkplan.py` plans and builds the gold-sink set). The test-only probe that places the gallery items on a disposable host is `ShardContent/tests/scenarios/cosmetic-catalog/DecorProbe.cs`.

## At a glance

| | |
| --- | --- |
| Rewards | 1,161 in 29 categories (FIG 110, FLO 70, FRN 51, DNG 50, ALC 48, LGT 47, CRF 45, LIB 45, TBL 45, ARM 41, GRV 41, ARC 42, NAU 42, WLH 42, STA 40, FOO 40, HER 38, TWN 38, TRO 35, SEA 33, CMP 31, TRS 31, CUR 27, REL 26, RUG 26, ANM 22, GAM 21, MUS 21, WTR 13) |
| Tiers | 326 common, 365 uncommon, 280 scarce, 142 rare, 48 extremely rare |
| Era grades | 109 **A** (documented in-game by April 2000), 992 **B** (original-world art, plausible), 60 **C** (needs an audit before use) |
| Shapes | 513 multi-tile pieces, 429 with rotated facings, 171 hued |
| Suggested pools | 33 pools holding 426 rewards; 735 stay in general stock |

## Ids

Every reward has a permanent id **`CR-<CAT>-<NNN>`**, for example `CR-FIG-014`. The category code is three letters, the number is assigned once and never reused.

* Refer to rewards by id only. Names, blurbs, tiers, tags and graphics may be edited; the id never changes.
* A withdrawn reward stays in its category file with `"retired": true` so saved items and references keep resolving; it disappears from the generated pages.
* New rewards take the next number in their category.

## How a system should choose

1. **By tier** to match effort: `common`, `uncommon`, `scarce`, `rare`, `extremely-rare`. The shipwreck plan's weights (uncommon 60 / scarce 25 / rare 12 / extremely rare 3) line up with these tiers.
2. **By tag** for theme: `monster:<species>`, `dungeon:<name>`, `town:<name>`, `shipwreck`, `camp`, `season:<...>`, `craft:<skill>`, `virtue:<name>`, `signature`, plus mood tags (`nautical`, `undead`, `noble`, ...). Tags are listed with counts at the end of the catalog page.
3. **By category** for the kind of object, **by placement** (`floor`, `surface`, `wall`, `ceiling`, `ground-cover`, ...) when a system must avoid items a house cannot display.
4. **By era grade**: `A` documented, `B` plausible original art, `C` needs an audit. A system that wants zero era risk uses `A` and `B` only.
5. **By suggested pool** when the system is one the plan names; otherwise take from the 735 unallocated rewards.

Rules every reward follows (from the plan and the owner's constraints): cosmetic only, no stats, skills, storage or function; tradable and lootable like any item; zero NPC resale, salvage, BOD or vendor-advance value; made only from existing client art.

## What the era research found (read before relying on a grade)

* **The cut-off is Publish 5, 2000-04-27** ("the Renaissance publish"). Release dates for Renaissance in sources range from 2000-04-03 to 2000-05-04.
* **Shrunken monsters did not exist as items in April 2000.** The 0x20C8-0x2137 "Frame" tiles were Tracking-menu icons and the pet-transfer trade item (Publish 3). The first obtainable creature statues were the 2001-07-24 veteran-reward mini-monster statues. The figurine concept (category FIG) is therefore **custom content on era-safe art**, graded B with that stated. **Owner ruling 2026-10-08: figurines are fine as long as the creature they show is present in our game.** The creatures the shard actually spawns are listed in [`Species-In-Game.md`](Species-In-Game.md) (149 types, read from the shard's own Felucca spawners); every figurine's `monster:` tag is validated against that list (a crocodile became an Alligator, the mountain goat a Goat, because those are what the world spawns). 110 figurines in the main catalog, 59 more in the era-neutral section (later icon art and statuettes).
* **Documented craftable or placeable decor by April 2000** (grade A material): house add-on deeds (forges, anvil, training dummy, pickpocket dip, oven, mill, spinning wheel, loom, pentagram, abbatoir; 1998-12-21), easels, music stands, dress forms, beds, instruments, dartboards, water troughs, globes, candelabras, goblets, potion kegs, Christmas trees (1998, 1999), potted plants (Dec 1999), shop game boards, dry-docked miniature boats.
* **No documented craft or deed before 2001** for rugs, tapestries, paintings, banners (2001 veteran reward), statues, fountains, gravestones, mounted heads (taxidermy, 2001), armor stands, weapon racks. These are original-world static art; the catalog uses them as rewards and says so in each entry's era note.
* **Halloween:** no Halloween items are documented before 2006; those entries are grade C.
* **Hard fences:** art ids from 0x4000, the 2003 winter-gift block (0x2328-0x2378), Tokuno (0x2440-0x24FF), the second creature-icon set (0x2554-0x2635), Samurai Empire (0x2700-0x28FF) and the Mondain's Legacy block (0x2D00-0x31FF) are rejected by the validator. Mixed-era blocks need a world-usage count of 50 or more for grade B.
* **Khaldun is post-era** (2000-09-03) and is not used. The dungeons Deceit, Destard, Shame, Wrong, Covetous and Fire are presumed launch-era but not documented in any publish note found.

## The era-neutral section (`CN-` ids)

Added on the owner's request, 2026-10-08. **Rule (owner's definition):** a reward is *era neutral* when it is a generic object whose look or lore ties it to no later expansion, creature, race, skill or event, so it would not seem out of place in 2000 Britannia, even though its art (or the object itself) came after April 2000. Examples that are in: a jack-o'-lantern, a weapon rack, a ship's wheel, a mirror, flags, a snowman. **Out:** samurai, ninja and other Tokuno/oriental pieces, gargoyle (Stygian Abyss, Ter Mur) styling, Eodon, figurines or trophies of creatures that did not exist, and items themed for skills the era lacks (Ninjitsu, Bushido, Spellweaving, Mysticism, Imbuing, Throwing). **Plausible-theming exception:** art that still reads naturally in the era is in even if a later skill inspired it, for example necromancy-flavoured skulls, bone ornaments, a preserved heart or a pickled brain. **Elven pieces are in** (owner ruling the same day: the shard has cosmetic Elves); they carry the tag `elven`.

* **Ids and use.** `CN-<CAT>-<NNN>`; the `CN-` prefix keeps them apart from the era catalog, so a system that must stay strictly in April 2000 simply ignores them. The era-neutral entries are not part of any suggested pool.
* **Era block.** Each entry has `era: {grade: "N", note, artEra}`: the note says why it is neutral, `artEra` is the curator's best knowledge of when the art first appeared (many say `unknown`), and the JSON adds `artEraEstimate`, a coarse guess from the id block (SA-or-later for ids from 0x4000, ML block 0x2D00-0x31FF, ...).
* **Numbers.** 925 rewards in 30 categories (the era catalog's 29, including 59 **monster figurines** of creatures present in our game, plus **NEC - Necromantic Curiosities**, 59): 238 common, 289 uncommon, 229 scarce, 127 rare, 42 extremely rare; 137 multi-tile, 537 with rotated facings, 34 hued, 61 tagged `elven`. Biggest categories: NEC 59, FIG 59, ARC 57, SEA 55 (about a dozen jack-o'-lantern faces, the winter set), HER 43, ARM 42 (weapon racks, armor stands), NAU 40 (ship's wheel, flags, cannons, lighthouse), DNG 40.
* **Validation.** `catalog.py --neutral validate` refuses tile names that belong to later content (samurai, ninja, katana, shoji, tatami, gargoyle, gargish, spellweaving, mysticism, imbuing, ter mur, eodon, minotaur, juka, meer, champion, doom, faction, bulletin, ethereal, heritage...) unless the entry explains itself in `era.themeOverride`; no override was used. It also rejects any graphic set already in the era catalog.
* **Pictures.** `sheets/neutral-<CAT>.png`, `images/<CAT>/CN-....png`, and 47 real-client pages `client-shots/CN-<CAT>-NN.png` (legend in `client-shots/README.md`, part 2).
* **Borderline entries for the owner to rule on:** the haunted mirrors and portraits (`CN-WLH-001`, `-002`, `-003` to `-005`, `-029`; Halloween art whose tiles are unnamed), the two copper fountain pieces from a 2005 anniversary token (`CN-WTR-003`, `-005`), the silver three-globe lamp and slender silver candelabra from a wedding set (`CN-LGT-018`, `-019`), the music box named for a later event (`CN-MUS-008`), the Skull-Marked Grimoire, which is the Necromancer spellbook graphic (`CN-NEC-042`), the daemon heads and masks (`CN-NEC-038` to `-041`), the Triangle-and-Spiral Circle (the ML arcane circle layout; may carry a Spellweaving association, `CN-ALC-025`), and the 16 Virtue/Vice emblem shields in ARM. Each is a plain object in the art; none was removed.
* **Not found.** Despite the brief there is no art for a jar of eyeballs, canopic jars, an iron-bar cage, slime pools, a generic altar, a chandelier or a lectern; Nautical has no figurehead or compass; no elven banners, signs, mirrors or armor stands exist in the Mondain's Legacy art.
* **Monster figurines (FIG).** Settled by the owner on 2026-10-08: a figurine is fine when its creature is present in our game (`Species-In-Game.md`). The main catalog keeps the early-icon figurines (110); the neutral FIG category (59) holds the later creature icons and statuettes: ghoul, mummy, skeletal knight and mage, lich lord, imp, ice fiend, hell hound and cat, efreet, stone gargoyle and harpy, golem, six more elementals, ogre lord, juka, ophidian and terathan variants, dread and frost spider, kraken, wyvern, drakes and a black dragon. The validator rejects any figurine whose creature the game does not spawn, and no theme-blocklist applies to them (Juka and the others are in our game).

Rebuild: `catalog.py --neutral validate`, `catalog.py --neutral build`, `galleries.py --neutral plan`, then the gallery run and `galleries.py index`. The in-game creature list is refreshed with `speciesingame.py`.

## The gold-sink set (2026-10-08)

On the owner's request: a set of about 100 decorations that players cannot get any other way, graded into six rarities by how cool each is, to be priced on a curve (owner's base: 2,000 gp for a Common) and sold by Furnisher vendors, with a showroom hall in Britain, as a major gold sink; owner rulings the same day: no weekly window or allowance in v1, tradable and lootable. The proposal is [`../Design-Proposal-3-House-Decoration-Gold-Sink.md`](../Design-Proposal-3-House-Decoration-Gold-Sink.md); nothing is built or approved. **Curation pass, same day (owner):** no seasonal or holiday pieces (pumpkins, jack-o'-lanterns, snowmen, Halloween spiderwebs) and standard home furnishings only (rugs, tables, chairs, hearths, pots, beds, dining, a telescope and the like). The first draft's Festive, Crypt, Menagerie, Statuary, Sea, Arms and Garden wings are gone.

* **The furnishing rule** (in `sinkplan.py`: `FURNISHING_CATS`, `FURNISHING_EXTRA`, `BLOCK_TAGS`, `BLOCK_WORDS`; written up in the proposal): seating, tables, beds, rugs, hearths and lighting, kitchen and dining, shelving and desks, books and maps, clocks, vases, wall hangings, instruments, study instruments; nothing seasonal, macabre, crypt, camp, military, nautical, treasure or monster-themed; no outdoor garden or statuary.
* **Candidates (381):** catalog or neutral entries that pass the furnishing rule, are in no suggested pool, whose graphics `availability.py` cannot find in any craft menu (including the T2A menus), NPC vendor list or loot table, that are era grade A or B or era-neutral, not retired, not held back as borderline, and visible in Felucca. `availability.py rawscan` re-checks the final 100 against every mention of their graphics in the server source. **The 100 are hand-picked** from them: 8 wings (Bedchamber, Parlour & Music Room, Dining & Kitchen, Rugs & Carpets, Hearth & Light, Study & Observatory, Walls & Hangings, Hall Curios), rarities 20 / 26 / 20 / 20 / 10 / 4 (Common, Uncommon, Scarce, Rare, Extremely Rare, Wonder), 16 collections; 58 are era-neutral (`CN-`), 42 era-graded. No piece is small enough to need the gallery's grey test tile (it is laid under any single piece 32 px or smaller; it is not part of any piece).
* **Prices and vendor (owner rulings, same day):** base 2,000 gp for a Common, rarity multipliers 1 : 2 : 4 : 8 : 16 : 35 (`TIER_UNITS` in `sinkplan.py`), nothing above 80,000 gp (`PRICE_CAP`); the whole set is about 1.22M. For now one Furnisher in Britain sells a selection of every rarity (37 pieces, listed in `gold-sink/vendors.json`: eight each of Common, Uncommon and Scarce, six Rare, four Extremely Rare, three Wonders); the other 63 are designed but not on sale. `Gold-Sink-Items.csv` and the sandbox carry the illustrative prices and where each piece is sold.
* **They are for sale only.** `pools.py validate` now fails if any suggested pool contains a gold-sink piece, so no reward system can hand one out. Any new reward system must pick from outside `gold-sink/picks.json`.
* **Change the set:** edit `gold-sink/picks.json` (and `collections.json`), run `sinkplan.py build` (sheets, `selection.json`, the CSV and the sandbox regenerate; `--no-sheets` skips the Edge renders; it prints a CURATION CHECK line for any pick that breaks the rule), then `sinkplan.py showroom` and the gallery run (`Run-GalleryShots.ps1 -Category GS`) for new real-client pages and `galleries.py index`. The tables inside the proposal are a copy and need refreshing by hand.

## Felucca hides leaves

Felucca's map is set to the client's *Desolation* season. The client hides every tile flagged *Foliage*, so leafy trees show as bare trunks (confirmed in the real client). 24 rewards contain such tiles; the catalog marks them and shows an "as seen in Felucca" picture. If full leaves are wanted, the map season is a server setting (`map-definitions.json`), an owner decision.

## Gaps the art could not fill

No ship's wheel, figurehead, compass, pirate flag, flagpole, market stall, mirror, lectern, bird cage, chandelier, oil lamp, weapon rack or armor stand exists in the era's client art; those were requested but are not in the catalog. Bowcraft has only humble art, and Spirit has no shrine token. These are noted in the relevant pools too.

## Rebuilding

```powershell
. .\.claude\scripts\Use-Toolchain.ps1
& $BRPython ShardContent\tools\cosmetic-catalog\catalog.py validate      # schema, art exists, era fences, duplicates
& $BRPython ShardContent\tools\cosmetic-catalog\catalog.py build         # ids, images, sheets, Cosmetic-Reward-Catalog.md, cosmetic-rewards.json
& $BRPython ShardContent\tools\cosmetic-catalog\pools.py validate        # pool rules (one id, one pool; per-system counts)
& $BRPython ShardContent\tools\cosmetic-catalog\pools.py build           # Reward-Pools.md, reward-pools.json
```

`build` needs Microsoft Edge (headless) for the labelled sheets. In-game gallery shots: see `client-shots/README.md` and `ShardContent/tests/scenarios/cosmetic-catalog/README.md`.

## Provenance and limits

* Pictures in `images/` and `sheets/` are renders of the client art (not game screenshots). Pictures in `client-shots/` are real ClassicUO screenshots on a disposable test server; wall pieces stand on the ground in them, and tiny items sit on a grey carpet pad so they can be seen.
* Era grading is an honest best effort. `C` entries are explicitly unverified; the evidence and its gaps are in `Era-Evidence.md`.
* Entry names, blurbs and tier suggestions are design proposals written for this catalog; none is an existing shard text.
