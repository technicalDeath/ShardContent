> **About this file.** Research pack compiled 2026-10-07 for the cosmetic reward catalog (see `README.md`). It records what existed in UO by the April 2000 Renaissance window, with sources and reliability marks, and an explicit list of what could not be verified (section 8). The catalog's era grades and the validator's art-id fences come from sections 4, 5b and 6. Treat anything marked UNVERIFIED as unknown. The fetches went through a summariser, so bullets are faithful in substance but not verbatim.
>
> Two corrections from later work: (1) the trophy tiles 0x1E60-0x1E6D are placed by the original Britannia map in Papua, Delucia and Deceit statics, which hints at pre-2001 art even though taxidermy itself dates from 2001-03-14; the catalog still grades mounted heads C until that is confirmed. (2) Felucca runs the client's Desolation season, which hides foliage tiles (see README).

# Era Evidence Pack: UO Renaissance (April 2000) house-decor catalog

Compiled 2026-10-07. Research only; no code or shard files were changed.

Reliability tags used throughout:
- **[P]** primary: official publish/patch notes (the uo.com wiki mirror of the original notes).
- **[S]** secondary: fan wiki, Wikipedia, emulator source code, local client data.
- **[W]** weak: search-result snippet, forum memory, or a page I could not open (stated where so).
- **UNVERIFIED** = I could not establish it. Nothing here is guessed.

URL shorthand: `PP/` = `https://uo.com/wiki/ultima-online-wiki/technical/previous-publishes/`

Two of my own tools are cited as "evidence" and need a caveat:
- **Local tiledata** = `UOData/tiledata.mul` in this workspace. It is a modern High Seas-format file (3,188,736 bytes, 0x10000 item records), so its tile NAMES reflect the modern client, not the April-2000 client. Use it for "what is at this id", never for "did this id exist in 2000".
- **ModernUO source** (`ModernUO/Projects/UOContent`) is a reimplementation of OSI behaviour, so it is [S].

---

## 0. Executive findings (read this first)

1. **Window**: "April 2000 UOR" = Publish 5 ("the Renaissance Publish", notes dated 2000-04-27 on uo.com) plus everything before it. Publishes 6-9 (Aug-Dec 2000) and everything in 2001 are AFTER. The Renaissance launch date itself is disputed in sources (Apr 3 / Apr 27 / May 4, 2000; see section 1) but all of them fall in or next to your window.
2. **"Shrunken monsters" did not exist as a player item in April 2000.** The 0x20C8-0x2137 "X Frame" art is creature-icon art. In the early game it was only UI/transient art (Tracking menu, pet-transfer trade item from Publish 3). The first obtainable creature statues were the **Veteran Reward "Mini-Monster Statues", Publish 12, 2001-07-24** (14 types: Dragon, Skeleton, Troll, Orc, Daemon, Ettin, Earth Elemental, Gargoyle, Gorilla, Crocodile, Lich, Lizard Man, Ogre, Ratman; plus Zombie, Cow, Llama for 3+ year accounts). They use exactly these Frame tiles. A pet "shrink" mechanic does not appear until the 2010s (EM shrinking potion 2018; pet statuettes 2014).
3. **Decor that WAS craftable/placeable by April 2000** (all [P]): carpentry furniture, small/large beds (1999-03-28), instruments (1999-03-28), dartboards/ballot boxes/water troughs (1999-03-28), easels/music stands/dress forms (1999-01-19), forges/anvils/looms/spinning wheels/ovens/flour mills/training dummies/pentagram/abbatoir as deeds (1998-12-21), tinkered globes and candelabras (1999-03-28), trash barrels (1999-02-24), potion kegs (1999-11-23), holiday trees (Dec 1998 and Dec 1999), potted plants (Dec 1999). Holiday bells and snow globes are first documented Dec 2000 (AFTER).
4. **Decor that is AFTER the window**: house decoration tool (2001-03-14), taxidermy trophies (2001-03-14), banners/flaming skull/furniture dye tub/mini-monster statues/ethereal mounts (all 2001-07-24 veteran rewards), holiday statuettes (2001-11), Halloween items (nothing documented before 2006 by the official wiki).
5. **Art ids**: a hard fence exists only at the extremes. Any id **>= 0x4000 is post-ML (2009+ client)**; the pre-7.0 clients top out at **0x3FFF**. Inside 0x0000-0x3FFF there is **no clean per-expansion cutoff**, because later expansions reused empty slots (e.g. AoS player bulletin boards sit at 0x1E5E in the classic block). Safest rule: trust ids that appear in a dated publish note or that sit in the dense classic blocks, and treat ids in 0x2328-0x2378 (holiday art), 0x2580-0x25E3, 0x2700-0x28FF (Samurai Empire), 0x2D00-0x31FF (Mondain's Legacy elf art) as post-UOR.

---

## 1. Timeline

### 1a. Expansion and era dates

| Event | Date(s) | Source / tag |
|---|---|---|
| UO launch | 1997-09-24 | Sphere client list `24.09.1997` [W], Wikipedia snippet [S]; uo.com's first patch notes are dated 1997-09-25 [P] |
| The Second Age (T2A): publish | **1998-10-24** ("Publish 15, The Second Age": Lost Lands, Papua, Delucia, Terathan Keep) | PP/1998-2/1998-15-24th-october/ [P] |
| T2A retail release | 1998-10-29 NA, 1999-06-25 EU (Sphere says 01.10.1998) | https://en.wikipedia.org/wiki/Ultima_Online_expansions [S]; https://forum.spherecommunity.net/Thread-Client-Versions-UO-Expansions-LIST [W] |
| **Renaissance (UOR)** | **CONFLICT**: 2000-04-03 (UltimaCodex "Ultima Online: Renaissance" and "Trammel (facet)"; Sphere list `03.04.2000`; UORenn wiki) / **2000-04-27** (uo.com Publish 5, "The Renaissance Publish", notes dated 27 April 2000) / 2000-05-04 NA and 2000-05-30 EU (Wikipedia "Ultima Online expansions"; UO Second Age wiki) | codex https://wiki.ultimacodex.com/wiki/Ultima_Online:_Renaissance [S]; PP/2000-2/2000-publish-05-27th-april/ [P]; wikipedia [S]; https://wiki.uosecondage.com/UO:_Renaissance [S] |
| Renaissance client versions | 2.0.0 through 2.0.9a | Sphere list [W] |
| Third Dawn | 2001-03-27 NA / 2001-03-30 EU (Wikipedia); 2001-03-07 (Sphere, probably client date); 2001-03-29 (UltimaCodex search snippet). Client 3.0.0-3.0.7a | wikipedia [S]; Sphere [W] |
| Lord Blackthorn's Revenge | 2002-02-12 NA / 2002-05-03 EU (Wikipedia); 2002-02-13 (codex snippet); 2002-02-24 (Sphere) | same [S/W] |
| Age of Shadows | 2003-02-11 NA / 2003-04-07 EU | wikipedia [S] |
| Samurai Empire | 2004-11-02 | wikipedia [S] |
| Mondain's Legacy | 2005-08-30 | wikipedia [S] |
| Kingdom Reborn (client) | 2007-06-27 | Sphere [W] |
| Stygian Abyss | 2009-09-08 | wikipedia [S] |
| High Seas | 2010-10-12 | wikipedia [S] |

Why the Renaissance conflict matters little here: Publish 5 had follow-up updates on **Apr 28, May 7, May 10, May 11 (x2), Jun 22, Jul 8, Jul 14, 2000** [P, PP/2000-2/2000-publish-05-27th-april/]. Pick "Publish 5 as of 2000-04-28" as the strict ceiling; every item in this pack is flagged against that line.

### 1b. Publishes 1997-2000 (uo.com numbering)

Marker: **[IN]** = inside the April-2000 window (Publish 5 or earlier). **[AFTER]** = later.
Note on numbering: uo.com numbers the early patches 01-22 per year. The official "Publish N" numbering starts with **Publish 1 = 1999-11-23**. There is no separate uo.com page for any "Publish 1" of 2000; 2000 starts at Publish 2.

**1997** (all [IN]; URLs `PP/1997-2/...`)
| # | Date | Decor/housing/crafting-relevant content |
|---|---|---|
| 01 | 09-25 | house sign no longer pickable; cooking burns food on failure; dice for board games restored |
| 02 | 10-10 | new shop deeds (counters, lockable storage rooms); **game sets (chess, checkers, backgammon, dice) in shop inventories**; scissors via weavers; stable service; pet "transfer" command |
| 03 | 10-16 | items in player chests stop vanishing; cloth shows yardage |
| 04 | 10-29 | house key to backpack; bank safety deposit boxes; items in houses no longer decay; new blacksmith helmet category; **multiple lamps added to the map**; "A portion of Despise will now have dragons. A portion of Hythloth will now have daemons." |
| 05 | 11-05 | ships/houses put spare key in bank |
| 06 | 11-12 | house longevity 9 days; harbormaster drydock (100 gp); "Wisps have been weakened"; reapers drop logs |
| 07 | 12-09 | **sitting in chairs/benches/logs/rocks in four directions**; pack horses/llamas; wooden shields removed from smithing |
| 08 | 12-16 | **player vendors**; wooden shields to carpentry; player-made tinker traps; no houses in Wind or dungeons; orc mage/orc lord |
| 09 | 12-18 | **Christmas 1997 surprise "check in your backpack"**; large smithies available; training dummies in houses work; town criers |

**1998** (all [IN]; URLs `PP/1998-2/...`)
| # | Date | Content |
|---|---|---|
| 01-06 | 01-12, 01-20, 01-29, 02-06, 02-12, 02-27 | house placement/decay fixes; 01-29 dungeon populations "revamped" (hellhounds, skeletal mages/warriors, new elementals, elder dragons), "Lanterns should now be sold"; 02-12 guilds, 2 vendors/house; 02-27 stackable cloth/torches/candles/oil flasks |
| 07-10 | 03-18, 04-13, 06-11, 06-19 | decay doubled; slimes split; spellbooks equippable; guild war colours |
| 11-14 | 09-07, 09-16, 10-01, 10-13 | vendor limits; 10-13 first-anniversary "Big Window" gift |
| **15** | **10-24** | **THE SECOND AGE** (Lost Lands, Papua, Delucia, Terathan Keep, ~11 entrances, large new monster list) |
| 16-19 | 10-28, 11-10, 11-19, 11-23 | 11-10 tailoring surcoats/tunics/jester suits, maker's marks; 11-23 lockdown by key, secure containers, tent reimbursement, torches auto-equip, spyglass moon phases, cake craftable |
| 20 | 12-02 | housing phase 2 (claims), house sign menu |
| **21** | **12-21** | **Housing Phase 3 + craftable house add-ons (see section 2)** |
| **22** | **12-23** | **Holiday gifts: Christmas tree deed, black dye tub, hairstyle deed, ranger armor, spyglass, fireworks wand** |

**1999** (all [IN]; URLs `PP/1999-2/...`)
| # | Date | Content |
|---|---|---|
| 01 | 01-19 | carpentry: easels, music stands, tall music stands, dress forms, fishing poles, shepherd's crooks, staves; lockdown asks "secure?" |
| 02 | 02-02 | holiday trees deleted, deeds disabled until next season; **voice-command lockdown ("I wish to lock this down")**; coloured ingots, 8 new ores; "large smithy" renamed "large house with patio" |
| 03 | 02-24 | **trash barrel** ("I wish to place a trash barrel"); stealth, remove trap |
| 04 | 03-28 | **beds, ballot boxes, dartboards, water troughs, harps/lute/drum/tambourines (carpentry); globes, candelabras, mugs, goblets, keyrings, jewelry (tinkering)**; Sea Serpents / Deep-Sea Serpents; Ice dungeon exit fix |
| 05 | 04-14 | house deeds become newbie items; real estate brokers sell inkwells |
| 06 | 05-25 | interior lockable doors; tinkered scales as shop decor; boats dry-dock into miniature models |
| 07 | 08-25 | new character templates; macro functionality |
| 08 | 09-22 | smelting/unravelling; items in armoire no longer vanish; 09-23 anniversary gifts |
| 09 = **Publish 1** | **11-23** | co-owners, strongbox, **potion kegs**, runebooks, maker's marks; **Dec holiday gifts incl. holiday tree deed, potted plant, wristwatch, snowballs**; Classic vs Modern house design |

**2000**
| Publish | Date | Tag | Content |
|---|---|---|---|
| 2 | 01-24 | [IN] | placement validation, **Land Surveying Tool**, **item decay in houses** (not applied to locked down/secured/add-ons/IGM-placed); pack animals 1,600 stones |
| 3 | 02-23 | [IN] | **house trading by trade window**; pet transfer deeds in trade window; guildstone decay; moonstones appear on monsters; monster treasure revamp |
| 4 | 03-08 | [IN] | bank checks 5,000-1,000,000; sea serpents from deep-sea fishing (80+); macro limits |
| **5** | **04-27 (+Apr 28 update)** | **[IN] = RENAISSANCE** | Trammel/Felucca, moonstones, Haven (Ocllo), party system, **7 new house types**, one house per account per shard, **NPC shop decorations replaced/added and not removable**, loot-right system, combat revisions |
| 5 updates | May 7 - Jul 14 | [AFTER] | not fetched |
| 6 | 08-21 | [AFTER] | lockdown restrictions (resources unusable; stacking; valueless items); blacksmith Make Last/Smelt/Repair/Maker's Mark prompt; no corpse cutting in Trammel |
| 7 | 09-03 (+9 updates to 11-03) | [AFTER] | secure container access levels; **candelabras, lanterns, instruments, mugs, dye tubs, books usable when locked down**; black dye tub not re-dyeable; communication crystals; **Khaldun dungeon**; player-vendor customisation |
| 8 | 12-05 | [AFTER] | Factions; faction-craftable items; floor traps; stable limits by skill |
| 9 | 12-15 | [AFTER] | holiday tree deed (classic/modern), **holiday bells, snow globes, snowballs**; "passable" items lockable near stairs; T2A travel restrictions lifted |

**2001 (AFTER; for reference)**: 10 (02-01), 11 (03-14), 12 (07-24), 13 (08-19), 13.5 (10-11), 13.6 (10-25), 14 (11-14 per index; page text says 11-30). Index: PP/2001-2/.

Sources for the whole table: the per-publish pages under `PP/` (all [P]); index pages PP/1997-2/, PP/1998-2/, PP/1999-2/, PP/2000-2/, PP/2001-2/.

---

## 2. Housing and decor by publish

### 2a. Chronological register (everything decor-relevant found)

| Date | Publish | What was added/changed | URL tail | In window? |
|---|---|---|---|---|
| 1997-09-25 | 01 | sign unpickable | 1997-2/1997-1-25th-september/ | IN |
| 1997-10-10 | 02 | shop deeds with counters; game sets in shops | 1997-2/1997-2-10th-october/ | IN |
| 1997-12-09 | 07 | sitting on chairs/benches/logs/rocks | 1997-2/1997-7-9th-december/ | IN |
| 1997-12-16 | 08 | wooden shields (carpentry); player vendors | 1997-2/1997-8-16th-december/ | IN |
| 1997-12-18 | 09 | training dummies placeable in houses; large smithies | 1997-2/1997-8-18th-december/ | IN |
| 1998-01-29 | 03 | "Lanterns should now be sold" | 1998-2/1998-3-29th-january/ | IN |
| 1998-02-27 | 06 | torches/candles/oil flasks stack | 1998-2/1998-6-27th-february/ | IN |
| 1998-11-23 | 19 | lockdown via key; torches auto-equip when lit; spyglass shows moon phases | 1998-2/1998-19-23rd-november/ | IN |
| **1998-12-21** | 21 | **Carpentry house add-on deeds**: Small Forge, Big Forge (E/S), Anvil (E/S), Training Dummy (E/S), Pickpocket Dummy (E/S), Stone Oven (E/S), Flour Mill (E/S), Spinning Wheel (E/S), Loom (E/S), **Pentagram, Abbatoir**. Placed by double-click with a ghost image; house-only; owner can axe-chop to destroy. House sign gets brass plaque + INFO/FRIENDS/OPTIONS tabs | 1998-2/1998-21-21st-december/ | IN |
| 1998-12-23 | 22 | Christmas tree deeds (blinking lights); only in/near own house, restricted to inside houses on Dec 31 | 1998-2/1998-22-23rd-december/ | IN |
| 1999-01-19 | 01 | **easels, music stands, tall music stands, dress forms**, staves, fishing poles, shepherd's crooks | 1999-2/1999-01-19th-january/ | IN |
| 1999-02-02 | 02 | holiday trees removed; voice-command lockdown | 1999-2/1999-02-2nd-february/ | IN |
| 1999-02-24 | 03 | **trash barrel** (one per house; items deleted 3 min after dropping); stack freely in houses | 1999-2/1999-03-24th-february/ | IN |
| **1999-03-28** | 04 | **small and large beds** (also need tailoring), **ballot boxes, dartboards, water troughs**, **lap harp, standing harp, drum, lute, tambourine, tassel tambourine**; tinkering **globes, pewter mugs, candelabras, goblets, forks, spoons, keyrings, iron keys, mortar and pestles**, jewelry | 1999-2/1999-04-28th-march/ | IN |
| 1999-05-25 | 06 | tinkered **scales** "as decorative shop items"; interior lockable doors; boats dry-dock to miniature models | 1999-2/1999-07-25th-may/ | IN |
| 1999-09-22 | 08 | armoire contents no longer vanish | 1999-2/1999-08-22nd-september/ | IN |
| 1999-11-23 | Publish 1 | co-owners, strongbox; secures (small house 3 secures / 425 lockdowns; castle 28 / 4,076); **potion keg** (carpentry+tinkering); runebook; Dec gifts **holiday tree deed, potted plant deed, wristwatch, snowballs, fireworks wand, clothing bless deed**; dry-docked boats show boat type/name | 1999-2/1999-publish-01-23rd-november/ | IN |
| 2000-01-24 | 2 | placement validation + preview; **Land Surveying Tool**; item decay in houses; list of plants that don't block placement (mushrooms, small flowers, poppies, red poppies, orfluer flowers, white flowers, foxglove, campion, snowdrops) | 2000-2/2000-publish-02-24th-january/ | IN |
| 2000-02-23 | 3 | trade a house by trade window | 2000-2/2000-publish-03-23rd-february/ | IN |
| **2000-04-27** | **5** | 7 new house designs: Small Stone Shop, Small Marble Shop, Small Tower, Sandstone Patio House, Two Story Log Cabin, Two Story Villa, Large Marble Patio House (60,600-192,000 gp; 425-1,370 lockdowns; 3-10 secures); one house/account/shard; **"Rares contained by another container or found in player houses will no longer be permanently locked down"**; **NPC shop decorations replaced on Felucca, added in Trammel, not removable**; keyring lockdown | 2000-2/2000-publish-05-27th-april/ | IN |
| 2000-08-21 | 6 | resources (ingots, boards, logs, shafts) unusable when locked; valueless items can't be locked; stacks | 2000-2/2000-publish-06-21st-august/ | AFTER |
| 2000-09-03 | 7 | usable when locked down: runes, maps, runebooks, books, **candelabras, lanterns, musical instruments**, dye tubs, mugs/glasses/cups | 2000-2/2000-publish-07-3rd-september/ | AFTER |
| 2000-12-15 | 9 | holiday tree classic/modern; **bells, snow globes, snowballs**; passable items lockable near stairs | 2000-2/2000-publish-09-15th-december/ | AFTER |
| 2001-03-14 | 11 | **House Decoration Tool** (architect NPC: turn/up/down on locked-down clocks, easels, paintings, crates); **Taxidermy Kit** (see 2c); hair stylists | 2001-2/2001-publish-11-14th-march/ | AFTER |
| 2001-07-24 | 12 | Veteran rewards: **banners, flaming skull, furniture dye tub, mini-monster statues, ethereal mounts** | 2001-2/2001-publish-12-24th-july/ | AFTER |
| 2001-08-19 | 13 | barkeep contract (customisable NPC barkeeps in public houses) | 2001-2/2001-publish-13-19th-august/ | AFTER |
| 2001-11 | 14 | holiday decorative statuettes (character-name, hued); universal crafting interface | 2001-2/2001-publish-14-14th-november/ | AFTER |

All rows [P].

### 2b. The pre-AoS carpentry menu, as encoded by ModernUO [S]

`ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs` gates AoS/SE/ML items behind `Core.AOS/SE/ML`, so the un-gated entries are the "classic" menu. This matches the publish notes above (every un-gated decor item has a dated publish in 1998-1999). Classic entries (name; skill range; logs):
- **Other**: barrel staves, barrel lid, short music stand (78.9), tall music stand (81.5), easel (86.8), fishing pole.
- **Furniture**: footstool, stool, bamboo chair, wooden chair, fancy wooden chair with cushion, wooden chair with cushion, wooden bench, wooden throne, throne, nightstand, writing table, yew-wood table, large table.
- **Containers**: wooden box, small/medium/large crate, wooden chest, empty bookcase, fancy armoire, armoire, keg (from barrel staves).
- **Weapons/armor**: shepherd's crook, quarter staff, gnarled staff, wooden shield.
- **Instruments**: lap harp, harp, drums, lute, tambourine, tassel tambourine.
- **Misc deeds**: small bed (S/E), large bed (S/E), dartboard (S/E), ballot box, pentagram, abbatoir.
- **Blacksmith add-ons**: small forge, large forge (E/S), anvil (E/S). **Training**: training dummy (E/S), pickpocket dip (E/S). **Tailoring**: dress form, spinning wheel (E/S), loom (E/S). **Cooking**: stone oven (E/S), flour mill (E/S). Water trough (E/S).
- NOT classic (gated): player bulletin board (AoS), hanging lanterns/shoji screens/bamboo chests/cabinets/colored armoires (SE), statues/elven everything/arcane bookshelf/alchemist table (ML).
- Whether each furniture row (e.g. throne, nightstand, writing table) existed from 1997 launch: the uo.com notes only document carpentry costs being "fixed" on 1997-10-29, not a launch menu. **UNVERIFIED per item; launch-era existence is strongly implied** (no publish adds them and the armoire bug is fixed in 1999).

Tinkering classic entries in the same file include candelabra, globe, lantern, spyglass, scales, key, keyring, goblet, pewter mug, plates/forks/knives/spoons, clock parts and **clocks (Clock Right/Left)**, sextant, potion keg, and jewelry. **Clock** first-documented date: UNVERIFIED (the only dated clock-adjacent item is the Dec 1997 Christmas wristwatch / 1999 holiday timepiece).

### 2c. Items the owner listed: status checklist

| Item | Status by April 2000 | Evidence |
|---|---|---|
| Beds | Craftable since 1999-03-28 | [P] 1999-04-28th-march |
| Rugs / carpets | **No craftable or deed rug found in any publish through 2000.** Rug art (tiles 0x1DD3-0x1DFC "rug", 0x1E36-0x1E5B "bearskin rug") is world/static art placed by developers/IGMs or taken as "rares". Placeable rug UNVERIFIED | local tiledata [S] |
| Banners / flags | Wall banner **deed = Veteran Reward 2001-07-24** (AFTER). Banner static art is wall dressing | [P] 2001-publish-12 |
| Tapestries | No deed found; tapestry tiles (0x0EAA-0x0EAF, 0x0FD5-0x0FE4, ...) are static art. UNVERIFIED | local tiledata [S] |
| Paintings | No craftable painting. Easel + canvas craftable 1999-01-19; paintings became turnable with the decoration tool 2001-03-14. Painting tiles 0x240D-0x2418 exist in modern data, era UNVERIFIED | [P]; local tiledata |
| Trophies / mounted heads | **Taxidermy Kit + 10 boards -> wall trophy deed, 2001-03-14 (AFTER).** Kit sold by tanners; only 90.1+ carpenters; corpses: orc, gorilla, troll, brown bear, polar bear, great hart, big fish. Trophy tiles 0x1E60-0x1E6D | [P] 2001-publish-11; tiles [S] |
| Statues | No craftable statue in classic menu (ML-gated statues). Creature statues = 2001 veteran reward (section 4). Static statue tiles 0x1224-0x1228, 0x129F-0x12B0, 0x12D5-0x12D9, 0x139A-0x13A3, 0x1F18 exist | [S] |
| Fountains | No placeable fountain found; world statics (0x090D-0x0910, 0x1731-0x175A, 0x19C3-0x19EC). UNVERIFIED as deco | [S] |
| Gravestones | Static world art (0x0ED4-0x0EDE, 0x1165-0x1184). Not placeable. UNVERIFIED | [S] |
| Plants / trees | **Potted plant deed: Christmas 1999** (tiles 0x11C8-0x11CC; veteran potted cactus 0x1E0F-0x1E14 is later). Holiday tree deed: Dec 1998, again Dec 1999 (trunk 0xCD6/0xCD7, ornaments 0xF0F-0xF30). Natural plants don't block placement (P2) | [P]; ids from ModernUO |
| Lanterns / torches / candles | Lanterns sold Jan 1998; candles/torches stackable Feb 1998; candelabra craftable 1999-03-28; lanterns/candelabras usable while locked down from 2000-09-03 | [P] |
| Instruments | Craftable 1999-03-28 (carpentry); shop-sold earlier (UNVERIFIED when) | [P] |
| Game boards | Chess/checkers/backgammon/dice sets sold in shops 1997-10-10 (tiles 0x0E12-0x0E14 chessmen, 0x0E1A checkers, 0x0E1C backgammon) | [P] |
| Globe | Tinkering 1999-03-28 (tiles 0x1047-0x1048) | [P] |
| Telescope / spyglass | Spyglass is a tinkering/holiday item (Dec 1998 gift; moon-phase feature Nov 1998). Placeable telescope (tiles 0x1459-0x149A are modern "telescope") UNVERIFIED | [P] |
| Suit of armor / armor stands | **None found** (only the carpentry-crafted "dress form" add-on, 1999-01-19, which is a mannequin: tiles 0x0EC6-0x0EC7 "dress form"). "Armor stand" UNVERIFIED | [P]; local tiledata |
| Weapon racks | **None found** | - |
| Barrels / kegs / crates | Barrel staves/lid, kegs, small/medium/large crates are classic carpentry; potion keg 1999-11-23 | [P] + [S] |
| Mannequins | Dress form (tailoring add-on, carpentry-crafted) 1999-01-19 | [P] |
| Signs | House signs exist from launch (1997-09-25 note); "shop signs" via architect deeds. Custom craftable signposts not documented through 2000. UNVERIFIED | [P] |
| Trash barrel | 1999-02-24 | [P] |
| Training dummy / pickpocket dip | 1997-12-18 (dummies) / 1998-12-21 (deeds) | [P] |

---

## 3. Rares and event items 1997-2000

### 3a. What "rare" meant in 1997-2000
- Event gifts and Seer-given unique items were handed out freely in 1997-98; by 1999-2000 collecting took off. (UOGuide "Rare" via search snippet [W]: https://www.uoguide.com/Rare, page returned HTTP 403 to me.)
- **Publish 5 (2000-04-27)** says rares were still ordinary tradable/placeable items: "Rares contained by another container or found in player houses will no longer be permanently locked down", and "On Felucca, the NPC shop decorations (which have, over the years, been taken by players) will be replaced ... Players will not be able to take these items" [P, PP/2000-2/2000-publish-05-27th-april/]. **So in 1997-2000 many "rares" were NPC shop dressing that players could carry off** (this is the origin of classic decor rares such as skull candles, vases, spittoons).
- Per-shard Stratics wiki rare lists exist ("Seer Items 1997-2000", "Event Moderator Items") but the wiki returned HTTP 403, so I only have search-snippet names [W]:
  - 1997 (Pacific): Backpack, Oil Flask, Reagent Box, Reagent Flask, "Bororm The Mighty".
  - 1998: Necklace of Ostard Talons, Crystalline Blackrock items, Daemonic Sword, Jade Necklace, Ancient Robe, Ancient Staff, Ancient Mage's Hat, Candle, HammerFist, Orc War Drum (of Wind).
  - 1999: Ring of Bone, Ring of Shadows, Liche Skull Candle, Bow of the Undead, undead-themed weapons.
  - 2000: "Blood".
  - Source pages (unopened): https://wiki.stratics.com/index.php?title=UO:Pacific_Rares , .../UO%3AAtlantic_Rares , .../UO:Lake_Superior_Rares . These were Seer/GM unique items on individual shards, not a systematic catalog.
  - "Bloody Table" = listed by Stratics under **2017** rares (NOT era). "Throne crafted from the bones of past victims" appears on Napa Valley Rares (year not captured). "Gold Candle" / "bear rug rare": not found. **UNVERIFIED.**
- A classic-style **"spawning rare"** list from an era-recreation shard (UORenn) names the shop-dressing type items: candelabra, skull candle, spittoon, large vase, cauldron, beaker, flask, candle with stand, fruit basket, brush, dirty pot, knitting, cannon balls, horse dung, bloody bandage, dried flowers/herbs/onions. https://uorenn.com/compendium/list/Spawning/P.html [S, but a custom recreation, so treat as hint not proof].

### 3b. Event / holiday items documented by year

From the official wiki holiday-gift pages (uo.com `/wiki/ultima-online-wiki/items/holiday-gifts/{christmas,easter,valentine,anniversary,other-holidays,halloween}-gifts/`) [S, official wiki but compiled later] cross-checked against the publish notes [P]:

| Year | Event | Items | First-seen note |
|---|---|---|---|
| 1997-12 | Christmas | **Santa Gloves** (black leather gloves "stolen from Santa Claus"); good-karma bags: Seasons Greetings card, bunch of dates, champagne glass, fireworks wand, bottle of champagne, bottle of eggnog, wrist watch; bad-karma bags: coal, spam, switches, "maybe next year" card | patch 1997-12-18 says "check in your backpack" [P] |
| 1998-10-13 | 1st anniversary | "Big Window" client feature (no item) | [P] |
| 1998-11-01 | Halloween | "the Abyss was launched for Halloween" (UOGuide Timeline snippet) - no item list | [W] |
| 1998-12-23 | Christmas | **Black Dye Tub, Hairstyle Deed, random Ranger Armor piece, Spyglass, Fireworks Wand, Holiday Tree Deed** | [P] PP/1998-2/1998-22-23rd-december/ |
| 1999 (spring) | St Patrick's Day | leprechaun suit, green cloak, long pants, feathered hat, white fancy shirt, dark blue boots from dead Leprechauns, green glass | [S] other-holidays page |
| 1999 | Easter | easter eggs, ten colours | [S] |
| 1999 | Valentine's Day | bag, card, champagne flute, conversation candies, pink champagne | [S] |
| 1999-09-23 | 2nd anniversary | **Commemorative Plate** (kiosks in Britain, Vesper); gift bags: crystal ball, commemorative coin, Jaana's hangover remedy, fireworks wand (the page labels it "300th Anniversary") | [S]; publish 1999-09-22 notes "anniversary gifts distributed" [P] |
| 1999-12 | Christmas | **Clothing Bless Deed, Holiday Tree Deed, Potted Plant Deed, Fireworks Wand, Holiday Timepiece (wristwatch), pile of snow/snowballs** | [P] PP/1999-2/1999-publish-01-23rd-november/ |
| 2000 (Feb) | Valentine's Day | Whispering Rose, pink champagne | [S] |
| 2000-12 | Christmas (AFTER) | **Holiday Bells, Holiday Tree Deed, snowballs, Snow Globe ("a snowy scene of {town}")** | [P] Publish 9 |
| Halloween 1997 / 1998 / 1999 | - | **UNVERIFIED.** The official Halloween-gifts page starts in 2006 ("Twilight Lantern, Halloween Ghoul Statuette, Grim Reaper's Scythe", candy, pumpkins from fields). No pumpkin / jack-o'-lantern / skeleton / candy / spider-web gift is documented before 2006 anywhere I could open. | https://uo.com/wiki/ultima-online-wiki/items/holiday-gifts/halloween-gifts/ |

### 3c. Art ids for the holiday items (so curators can pick era-safe tiles) [S: ModernUO source]
- Era-safe (classic blocks): holiday tree trunk 0x0CD6/0x0CD7 and ornaments 0x0F0F-0x0F30; potted plant 0x11C8-0x11CC; snow globe 0x0E2F; wristwatch/timepiece 0x1086; holiday bell 0x1C12; snow piles 0x08E0-0x08E6; fireworks wand (mace-class art).
- NOT era-safe (later holiday art): snowman 0x2328-0x2329, gift box 0x232A-0x232B, wreath 0x232C-0x232D, snowflake 0x232E-0x232F, poinsettia 0x2330-0x2331, "Christmas wisps" 0x2332-0x2339, holiday candle 0x236E-0x2373, mistletoe 0x2374-0x2375, festive cactus 0x2376, snowy tree 0x2377, topiary 0x2378, stockings 0x2BD9-0x2BDC. ModernUO ties snowman/gift box/wreath to the 2003 winter gift package (`WinterGiftPackage2003.cs`). Treat the 0x2328-0x2378 block as 2003+.

---

## 4. Monster figurines / shrunken pets / statuettes

### 4a. What the 0x20C8-0x2137 "Frame" tiles are [S: local tiledata names; ModernUO code]
Names in the local tiledata (item id: name):
- 0x20C8-0x20CC: ettin / gorilla / lizardman / ogre / troll "frame"; 0x20CD male; 0x20CE female.
- 0x20CF-0x20EC: Bear, Rat, Chicken, Corpser, Demon, Deer, Dog, Dragon, Earth Elemental, Ettin, Gargoyle, Crocodile, Grizzly Bear, Harpy, Horse, Lizard Man, Ogre, Orc, Polar Bear, Rabbit, Rat Man, Scorpion, Serpent, Sheep, Skeleton, Slime, Troll, Wolf, Wooly Sheep, Zombie **"Frame"**.
- 0x20ED-0x210B (lowercase): air elemental, bird, bull, dolphin, eagle, fire elemental, gazer, gorilla, llama, cougar, liche, mongbat, reaper, sea serpent, snake, spider, walrus, wisp, pig, panther, cow, daemon, human male/female, mountain goat, ghoul, headless, water elemental.
- 0x210C-0x210D: Elf Male/Female (**Mondain's Legacy 2005 or later; not UOR**).
- 0x2118-0x2127: black bear, big cat, bird, cat, dog, eagle, grizzly, horses, wolf, rat, rabbit, packhorse, packllama.
- 0x212A-0x2137: terathan warrior/drone/matriarch, cyclops, titan, giant toad, bullfrog, lizard, ophidian mage/warrior/queen, desert/frenzied/forest ostard. **These are exactly the Second Age (Oct 1998) creatures** [P, PP/1998-2/1998-15-24th-october/], so the icon block was already being extended in T2A, i.e. the "Frame/icon" art for launch creatures and T2A creatures predates April 2000. Empty slots in 0x210E-0x2117, 0x2128-0x2129, 0x2138-0x213E.
- **A second, later icon set sits at 0x2554-0x2635 and is NOT UOR**: 0x2554-0x257F are monster-weapon icons (daemon sword, ettin hammer, ... also naginata 0x2577 and no-dachi 0x2578, which are Samurai Empire weapons); 0x2580-0x25DD are creature icons (billy goat ... water elemental, incl. kirin, kraken, Efreet 0x2590, seahorse 0x25BA, nameless one/harrower 0x25BB, Dread Spider 0x25C4, Terathan Avenger/Queen); 0x25F8-0x25FC are NPCs (Adranath, Lord Blackthorn, Captain Dasha, Dawn, Warlord Kabur); 0x2602-0x2635 are LBR/AoS-era creatures (Solen, Exodus Minion/Overseer, Juka, Meer, then AoS: crystal elemental, treefellow, skittering hopper, devourer of souls, flesh golem, gore fiend, impaler, gibberling, patchwork skeleton, wailing banshee, shadow knight, abyssmal horror, darknight creeper, ravager, flesh renderer, wanderer of the void, vampire bat). Because it contains SE weapons and AoS monsters it was authored in 2004 or later (probably the Kingdom Reborn-era bestiary/tracking art). Local tiledata names [S]. Dates of authoring UNVERIFIED; "not UOR" is safe.
- Meaning of "Frame": UNVERIFIED (probably "one frame of the creature's animation").

### 4b. How the game used them
1. **Tracking skill menu icons.** ModernUO's `Tracking.cs` (`TrackWhoGump`) draws every tracked creature with `ShrinkTable.Lookup(m)`, which returns these tile ids. Tracking exists from launch. [S] (OSI behaviour reimplemented; no primary source.)
2. **Pet-transfer trade item.** ModernUO `TransferItem.cs` (the object put in the trade window, deleted on completion) is created with `ShrinkTable.Lookup(creature)`: "This item represents a pet currently in consideration for trade". The matching official change is **Publish 3, 2000-02-23**: "Pet transfer deeds display pet type and name in trade window" [P, PP/2000-2/2000-publish-03-23rd-february/]. It is transient and not obtainable decor. (That the 2000 icon was this same art is [S] inference.)
3. **Veteran-reward Mini-Monster Statues, Publish 12, 2001-07-24.** [P, PP/2001-2/2001-publish-12-24th-july/]
   - Year 1 (12-23 month accounts), choose from 14: **Dragon, Skeleton, Troll, Orc, Daemon, Ettin, Earth Elemental, Gargoyle, Gorilla, Crocodile, Lich, Lizard Man, Ogre, Ratman**.
   - Year 3+ adds 3: **Zombie, Cow, Llama**.
   - ModernUO `Items/Special/MonsterStatuette.cs` maps these 17 to the Frame tiles: Crocodile 0x20DA, Daemon 0x20D3, Dragon 0x20D6, Earth Elemental 0x20D7, Ettin 0x20D8, Gargoyle 0x20D9, Gorilla 0x20F5, Lich 0x20F8, Lizardman 0x20DE, Ogre 0x20DF, Orc 0x20E0, Ratman 0x20E3, Skeleton 0x20E7, Troll 0x20E9, Cow 0x2103, Zombie 0x20EC, Llama 0x20F6 [S]. The first 17 enum entries match Publish 12's list one-for-one, which confirms the identification.
   - ModernUO later adds Ophidian (0x2133), Reaper (0x20FA), Mongbat (0x20F9), Gazer (0x20F4), Fire Elemental (0x20F3), Wolf (0x2122), Slime (0x20E8), then 0x25xx/0x2Dxx/0x46xx/0x4Axx statues (Seahorse, Harrower, Efreet, Plague Beast, Red Death, Spider, Ophidian variants, Dread Horn, Minotaur, Black Cat, Halloween Ghoul, Santa). **Dates for the Ophidian/Reaper/Mongbat/Gazer/Fire Elemental/Wolf batch: UNVERIFIED (2001-2003 veteran-reward additions; not checked).**

### 4c. Plain answer for the owner
- **April 2000 (UOR): no obtainable monster figurine, shrunken pet, or creature statue existed.** No publish through 2000 mentions one.
- **First obtainable: 2001-07-24 (Publish 12), veteran reward only**, not craftable or purchasable. That is roughly 15 months after the window.
- Other creature-statue milestones, all AFTER: holiday "decorative statuettes" (2001-11, Publish 14 [P]); Halloween Ghoul Statuette (2006, official Halloween page [S]); War Ostard/War Horse **pet statuettes**, "Using the pet statuette will create a bonded pet" (Publish 86, 2014-09-25 [P] https://uo.com/wiki/ultima-online-wiki/publish-notes/publish-86/); a "Shrinking Potion" appears in the Stratics wiki as an **EM item (2018)** [W, page returned 403: https://wiki.stratics.com/index.php?title=UO%3AShrinking_Potion ]. There was never a general official pet-shrink item in the UOR/Third Dawn era.
- Contrast: the genuine "miniature model" decor that DID exist in 1997-2000 was **dry-docked boats** (miniature boat models, 1997-11-12 harbormaster dry-dock; 1999-05-25 and 1999-11-23 improvements) [P].
- **Design implication:** using Frame-tile creature figurines as house decor is a custom/late feature (2001 veteran reward). Art-wise the tiles are safe; "when obtainable" is not UOR. If the shard wants them it should be framed as a reward invented outside strict UOR, or tied to the 2001 veteran-reward concept.

---

## 5. Art-ID cutoffs

### 5a. Client/tile-file facts [S]
- UOFiddler's `Art.GetMaxItemId()`: **"ML and older" returns 0x3FFF; Stygian Abyss 0x7FFF; High Seas 0xFFDC** (decided by artidx.mul length). https://raw.githubusercontent.com/polserver/UOFiddler/master/Ultima/Art.cs
- ModernUO `Projects/Server/TileData.cs`: tiledata size >= 3,188,736 bytes = client 7.0.9.0 (0x10000 items); >= 1,644,544 bytes = "7.0.0.0" format (0x8000 items); smaller (older) files = **0x4000 items**. So the April-2000 (2.0.x) client's tile table has at most 0x4000 item records, i.e. ids 0x0000-0x3FFF. (My local ModernUO copy; the size-to-version mapping is the engine author's comment, treat the exact version labels as [S].)
- PolServer forum, via search snippets [W]: art.mul was extended to 0xFFDB with High Seas (7.0.9.0); in 7.x clients empty slots up to 0x3FFF were filled with an "unused" picture; 6.0.13.0 already had an artidx of 0x10000 entries. URLs: https://forums.polserver.com/viewtopic.php?p=16227 , https://www.forums.polserver.com/viewtopic.php?p=16998
- ServUO thread "item id #s by expansion?": **no definitive list exists**; one reply notes Broadsword "went back and used previously empty slots and filled them" after taking over. https://www.servuo.dev/threads/item-id-s-by-expansion.10714/ [W]
- Client versions per expansion (Sphere list) [W]: original UO 1.0.0-1.25.35; T2A 1.25.35b-1.26.4j; **Renaissance 2.0.0-2.0.9a**; Third Dawn 3.0.0-3.0.7a; LBR 3.0.7b-3.0.8r; AoS 3.0.8z-4.0.4b2; SE 4.0.5a-4.0.11c; ML 4.0.11d-5.0.9.1; KR 6.0.0.0-6.0.14.3; SA 6.0.14.4-7.0.8.2; HS 7.0.9.0+. https://forum.spherecommunity.net/Thread-Client-Versions-UO-Expansions-LIST
- Third Dawn "improved some 2D artwork, especially walls and trees" (replaced images, not new ids) [S] https://www.wiki.ultimacodex.com/wiki/Ultima_Online:_Third_Dawn

### 5b. Rule of thumb I can defend

| Id range | Verdict | Basis | Confidence |
|---|---|---|---|
| >= 0x4000 | **Not UOR. Post-ML (SA 2009+, mostly HS 2010+)** | UOFiddler max id 0x3FFF for ML and older; local tiledata shows gargish items begin at 0x4000 | High |
| 0x2328-0x2378 | **Not UOR** (2003+ holiday art: snowman, gift box, wreath, poinsettia, mistletoe, topiary, holiday candle) | ModernUO ties them to the 2003 winter package; the 1998-2000 holiday items use classic ids (section 3c) | Medium-high |
| 0x2700-0x28FF (esp. 0x2793-0x27F8) | **Not UOR** (Samurai Empire 2004: Bokuto 0x27A8, Tetsubo 0x27A6, Yumi 0x27A5, ninja jackets 0x2793) | ModernUO class ids; SE-gated carpentry | High |
| 0x2D00-0x31FF (partly) | **Not UOR** (Mondain's Legacy elf: arcanist/squirrel/warrior statues 0x2D0E-0x2D13, elven anvil/forge 0x2DD5-0x2DD8, elven bed/table 0x3xxx) | local tiledata names + ML-gated carpentry | High for the "elven/arcane" tiles; the remainder of the block is mixed |
| 0x2554-0x2635 | **Not UOR** (second creature/weapon icon set that includes SE weapons naginata/no-dachi, LBR Juka/Meer/Exodus, and AoS monsters) | local tiledata names (section 4a) + ModernUO statue table | High |
| 0x2440-0x24FF | **Not UOR** (Tokuno garden set: cherry blossoms, bamboo, paper lanterns/screens, zen rock garden, tea set, wasabi) | local tiledata names; SE theme | High |
| 0x2300-0x2319 | Probably not UOR (mini houses, flower garland, fur boots/cape, gilded dress, formal shirt, bulletin board); same cluster as the 2003 holiday art that follows | local tiledata names | Medium-low |
| 0x210C-0x210D | Not UOR (Elf male/female icons) | name + ML | High |
| 0x20C8-0x2137 | Creature-icon block, T2A-era at the latest for all except 0x210C-0x210D | T2A creatures live inside it | Medium-high (art presence), but see caution below |
| 0x0000-0x1FFF | **Presumed classic (1997-1999) and the safest region for UOR decor**, with isolated later fills | dense in modern data (about 240 of 256 slots named in nearly every 0x100 block); holiday tree/potted plant/snow globe/bell all live here | Medium |
| 0x2000-0x2327, 0x237A-0x2400 | Mixed; each tile needs a dated reason | - | Low |
| 0x3A00-0x3FFF | Sparse in modern data; 0x3B00-0x3CFF empty, 0x3D00 only 28 names, 0x3E00-0x3FFF populated (boats/multis). Likely partly classic (ships/houses), partly later fills. **UNVERIFIED which.** | local tiledata | Low |

**Caution (important):** later expansions put new art into previously empty low ids, so an id below 0x2000 is not guaranteed pre-2000. Concrete example: `bulletin board` at 0x1E5E-0x1E5F and `ankh of Sacrifice` 0x1E5C-0x1E5D sit between the classic bearskin-rug block (0x1E36-0x1E5B) and trophy block (0x1E60-0x1E6D), yet the player bulletin board is AoS-gated in ModernUO's carpentry (PlayerBB). The practical corollary is that **existence in the April-2000 client cannot be proven from an id alone**; the only strong evidence per tile is a dated publish note, a rare of that era, or an item that existed in the pre-AoS ModernUO behaviour set.

**Highest populated item id in the April-2000 client**: UNVERIFIED. All I can say is "at most 0x3FFF" (index-file ceiling) and that the 7.x client back-filled empty slots up to 0x3FFF with an "unused" image, so the original table had holes.

### 5c. Useful decor tile ranges (local tiledata names, modern; era of each UNVERIFIED unless noted)
rug 0x1DD3-0x1DFC; bearskin rug 0x1E36-0x1E5B; trophy 0x1E60-0x1E6D (taxidermy 2001); beds 0x0A55-0x0A91, 0x0DB0-0x0DB5, 0x11CE-0x11D5; bookcase 0x0A97-0x0A9C; armoire 0x0A4C-0x0A53; candelabra 0x0B1D-0x0B1F, 0x0B26-0x0B28; lantern 0x0A15-0x0A25; candle 0x0A0F-0x0A11, 0x142C-0x1437; sconce 0x09FB-0x0A04; training dummy 0x1070-0x1077; easel 0x0F65-0x0F6A; dartboard 0x1E2E-0x1E33; pentagram 0x0FE6-0x0FEE; anvil 0x0FAF-0x0FB0; forge 0x197E-0x19A9; loom 0x1049-0x104A, 0x105F-0x1066; spinning wheel 0x1015-0x101E; water trough 0x0B41-0x0B44; fountains 0x090D-0x0910, 0x1731-0x175A, 0x19C3-0x19EC; gravestones 0x0ED4-0x0EDE, 0x1165-0x1184; globe 0x1047-0x1048; clock 0x104B-0x1050; sextant 0x1057-0x105A; spyglass 0x14F5-0x14F6; chess/checkers/backgammon 0x0E12-0x0E1C, 0x0FA4-0x0FAD; harps/lute 0x0EB1-0x0EB4; keg 0x0E7F; barrel 0x0E77, 0x0FAE. (Some of these, e.g. "abbatoir", have no named tile in the local table.)

---

## 6. Dungeon and world-dressing facts

### 6a. Dungeons/locations: what the primary notes establish [P]

| Place | Earliest primary evidence | In window? |
|---|---|---|
| **Despise** (dragons) | 1997-10-29: "A portion of Despise will now have dragons." | IN |
| **Hythloth** (daemons) | 1997-10-29: "A portion of Hythloth will now have daemons." | IN |
| **Wind** (town/dungeon) | 1997-12-16 no houses in Wind, more monsters in Wind; 1998-01-29 no teleporting into Wind | IN |
| **Orc fort** | 1997-12-16 "the orc fort is becoming more populated" | IN |
| **Ice dungeon** | 1999-03-28 "exit from the ice dungeon will be corrected" | IN |
| **Terathan Keep** (Lost Lands) | 1998-10-24 Second Age | IN |
| Lost Lands entrances | 1998-11-23 some entrances made untouchable; housing banned beside them | IN |
| Haven (Ocllo, tutorial) | 2000-04-27 Publish 5 | IN |
| **Khaldun** (Lost Lands, Felucca, "two entrances far east of Delucia", "for veteran players ... very difficult") | 2000-09-03 Publish 7 | **AFTER** |
| Deceit, Destard, Shame, Wrong, Covetous, Fire | **UNVERIFIED in primary notes** (never named in the pages I searched). Secondary: UOGuide-type snippet says Despise "first seen September 1997" [W]; UltimaCodex lists Fire and Ice dungeons for Britannia in UO without dates [S]; these names are carried from Ultima IV/V (UltimaCodex dungeon pages [S]). Strongly presumed launch-era. | presumed IN |
| Ilshenar | Third Dawn 2001 | AFTER |
| Malas, Tokuno, Ter Mur, Eodon | AoS 2003, SE 2004, SA 2009, ToL 2015 | AFTER |

Context: In April 2000 the Lost Lands were reachable only by the 11 on-foot/boat/teleport entrances of the T2A publish; **recalls, gates and mounted creatures between Lost Lands and Britannia were restricted until Publish 9 (2000-12-15)** [P, Publish 9 page: "T2A Transport: travel restrictions lifted"]. Renaissance copied the Lost Lands to Trammel, and Ocllo is missing in Trammel; "Both Trammel and Felucca will have the T2A lands and dungeons" [P/S].

World dressing in the notes [P]: "multiple lamps added to the map" and "over 100 map bugs fixed" (1997-10-29); roaming herds of deer/sheep/cows/timber wolves, undead packs, gypsy and brigand camps, evil-mage towers with prisoners (1997-10-29); town criers (1997-12-18); banks added to Serpent's Hold, Minoc, Magincia, Moonglow, Ocllo (1997-12-16) and Jhelom, Skara Brae, Minoc (1998-02-12); Serpent Pillar animations (disabled Dec 1998); **NPC shop decorations** (replaced/added with Publish 5).

### 6b. Creatures: earliest primary documentation [P]

| Creature(s) | Earliest evidence | In window? |
|---|---|---|
| Orcs, trolls, ettins, lizardmen, ratmen, orc captains, harpies, liches, headless, daemons | 1997-10-10 "monster types now loot items" | IN |
| Dragons | 1997-10-29 (Despise) | IN |
| Wisps | 1997-11-12 "Wisps have been weakened" (already existed) | IN |
| Reapers | 1997-11-12 | IN |
| Drakes | 1997-12-09 ("dragons and drakes") | IN |
| Orc mage, orc lord | 1997-12-16 added | IN |
| Hellhounds, skeletal mages, skeletal warriors, "new kinds of elementals", elder dragons | 1998-01-29 | IN |
| Slimes (split), corpsers, giant silver serpents, kraken, swamp tentacles, ancient wyrms, energy vortices, blade spirits | 1998-03-18 (slimes); 1998-11-23 (aggressive list) | IN |
| **T2A list (1998-10-24)**: Cyclopian Warrior, Frost Troll, Ice Elemental, Ice Fiend, Imp, Mummy, Ophidian variants, Snow Elemental, Stone Gargoyle, Stone Harpy, Swamp Tentacle, Terathan variants, Titan, **Wyvern**; non-hostile: Bullfrog, Frost Spider, Giant Ice Serpent, Giant Toad, Ice Snake, Lava Lizard, Nightmare, Forest/Desert/Frenzied Ostard | IN |
| Sea Serpent, Deep-Sea Serpent | 1999-03-28; 80+ fishing pull-up 2000-03-08 | IN |
| Faction guard roster: Ogre Lords, Wisps, Silver Serpents, Daemons (Felucca spawns) | 2000-12-05 (the species themselves are older; the faction use is new) | AFTER (use) |
| Khaldun monsters (names not given in the note) | 2000-09-03 | AFTER |

Species the owner asked about with NO primary date found (**UNVERIFIED**): Lich Lord / Ancient Lich, Balron (balrog), Dread Spider, Elder Gazer, Succubus, Shadow Wyrm, White Wyrm, Gargoyle (generic; Stone Gargoyle is T2A), Giant Spider. Search snippets say "Sorcerers' dungeon content from the 1997-1999 era mentions balron / lich lord / dread spider / elder gazer" but I could not open a dated source. "Dread Spider tameable" is Publish 97 (2017), irrelevant to existence.

Post-April-2000 species (secondary list by expansion, UOG: Demise monster index https://uodemiseguide.spokland.com/mobile/monster [S], which lists by expansion):
- **LBR 2002**: Chaos Dragoon (+Elite), Exodus Minion/Overseer, Juka Lord/Mage/Warrior, Meer Captain/Eternal/Mage/Warrior.
- **AoS 2003**: Abyssmal Horror, Bone Demon, Crystal Elemental, Dark Father, Darknight Creeper, Devourer of Souls, Flesh Golem, Flesh Renderer, Gibberling, Gore Fiend, Impaler, Mound of Maggots, Patchwork Skeleton, Ravager, Shadow Knight, Skittering Hopper, Treefellow, Vampire Bat, Wailing Banshee, Wanderer of the Void.
- **SE 2004**: oni, kappa, yamandon, ronin, ninja, kitsune, rai-ju, tsuki wolf, deathwatch beetle, etc.
- **ML 2005**: minotaur, satyr, hydra, reptalon, centaur lines, dryad, Cu Sidhe, crystal creatures, etc.
- **Third Dawn / Ilshenar 2001**: "more than 30 new creatures" [W snippet]; individual names UNVERIFIED. Note the Demise index lumps TD creatures into its base categories, so it cannot separate them. **Treat any creature not in the table above or the T2A list as "unknown/not safe" for a UOR trophy catalog.**
- Elves, gargoyles-as-race (SA 2009), Ter Mur creatures: AFTER.
- Faction/Champion/Paragon (2002-2003+ ) creatures: AFTER.

Trophy-safe species (documented by April 2000): orc, orc captain, orc lord/mage, troll, frost troll, ettin, ogre/ogre lord (ogre lord UNVERIFIED date; "Ogre Lords" appear only as faction monsters in P8), lizardman, ratman, harpy/stone harpy, gazer (existing; date UNVERIFIED), liche, daemon, dragon, drake, wyvern, ancient wyrm, kraken, sea serpent, corpser, headless, reaper, wisp, slime, mummy, imp, titan, cyclops, terathan/ophidian lines, stone gargoyle, brown/grizzly/polar bear (taxidermy list names bears, orc, gorilla, troll, great hart, big fish; but taxidermy is 2001).

---

## 7. Sources list

**Primary [P]: uo.com wiki mirror of original publish notes (all opened successfully)**
- Index pages: PP/ (previous-publishes root), PP/1997-2/, PP/1998-2/, PP/1999-2/, PP/2000-2/, PP/2001-2/, PP/2002-2/ : lists with dates.
- 1997 notes 01-09 (`PP/1997-2/1997-1-25th-september/`, `.../1997-2-10th-october/`, `.../1997-2-16th-october/`, `.../1997-2-october-29th/`, `.../1997-5-5th-november/`, `.../1997-6-12th-november/`, `.../1997-7-9th-december/`, `.../1997-8-16th-december/`, `.../1997-8-18th-december/`): high value for 1997 dungeon/creature/housing facts.
- 1998 notes 01-22 (`PP/1998-2/1998-1-12th-january/` ... `.../1998-22-23rd-december/`): especially 1998-3-29th-january, 1998-15-24th-october (Second Age), 1998-19-23rd-november, 1998-21-21st-december (add-on deeds), 1998-22-23rd-december (holiday gifts).
- 1999 notes (`PP/1999-2/1999-01-19th-january/`, `1999-02-2nd-february/`, `1999-03-24th-february/`, `1999-04-28th-march/`, `1999-06-14th-april/`, `1999-07-25th-may/`, `1999-07-25th-august/`, `1999-08-22nd-september/`, `1999-publish-01-23rd-november/`): 03-28 and Publish 1 are the richest decor sources.
- 2000 notes (`PP/2000-2/2000-publish-02-24th-january/` ... `2000-publish-09-15th-december/`): Publish 5 is the window line.
- 2001 notes (`PP/2001-2/2001-publish-11-14th-march/`, `2001-publish-12-24th-july/`, `2001-publish-13-19th-august/`, `2001-publish-14-14th-november/`, also 10): taxidermy, decoration tool, veteran rewards.
- https://uo.com/wiki/ultima-online-wiki/publish-notes/publish-86/ : pet statuettes 2014.
- Caveat: the fetches went through a summariser, so the bullets are faithful in substance but not verbatim; items could have been dropped from long pages. Anything absent here is "not seen", not "not in the notes".

**Official wiki, secondary [S]**
- https://uo.com/wiki/ultima-online-wiki/items/holiday-gifts/ (+ `christmas-gifts/`, `easter-gifts/`, `valentine-gifts/`, `anniversary-gifts/`, `other-holidays/`, `halloween-gifts/`): holiday gift tables by year; Halloween starts 2006.
- https://uo.com/wiki/ultima-online-wiki/skills/carpentry/ and `.../carpentry-craftables/` : modern craft list (not era-gated). Low value for era.
- https://uo.com/wiki/ultima-online-wiki/world/dungeons/ (+ `despise-felucca/`, `destard/`): modern; no intro dates. Low value.

**Fan wikis, emulators, code [S]**
- https://wiki.ultimacodex.com/wiki/Ultima_Online:_Renaissance , .../Trammel_(facet) , .../Ultima_Online:_Third_Dawn , .../Ultima_Online:_The_Second_Age , .../Britannia_in_Ultima_Online , .../Ice_Dungeon , .../Carpentry : dates and general facts.
- https://en.wikipedia.org/wiki/Ultima_Online_expansions : expansion release dates (NA/EU).
- https://wiki.uosecondage.com/UO:_Renaissance (release May 4, 2000); https://wiki.uosecondage.com/Ancient_Wyrm; https://wikiwiki.jp/uosecondage/Carpentry (training path only).
- https://uorenn.com/compendium/ and `list/Spawning/P.html`, `list/House/M.html`, `list/Item/M.html`, `info/Carpentry.html`, `info/Tinkering.html` : UOR-recreation shard; its housing numbers disagree with the official Publish 1/5 numbers, so use only as hints.
- https://uodemiseguide.spokland.com/mobile/monster : monsters by expansion (UOG: Demise).
- https://raw.githubusercontent.com/polserver/UOFiddler/master/Ultima/Art.cs and `TileData.cs` : max item id by client generation.
- https://modernuo.com/docs/development/era-and-expansions/ : expansion enum only; no id ranges.
- Local files: `ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs`, `DefTinkering.cs`, `Items/Special/MonsterStatuette.cs`, `Items/Special/Holiday/*`, `Skills/Tracking/Tracking.cs`, `Mobiles/AI/BaseAI/TransferItem.cs`, `Misc/ShrinkTable.cs`, `Projects/Server/TileData.cs`, `Distribution/Data/shrink.json`; `UOData/tiledata.mul` (modern format).

**Weak [W]**
- https://forum.spherecommunity.net/Thread-Client-Versions-UO-Expansions-LIST : client versions by expansion with dates.
- https://www.servuo.dev/threads/item-id-s-by-expansion.10714/ : confirms no authoritative id-by-expansion list.
- https://www.servuo.dev/threads/xantos-shrink-system.4026/ : shrink-system config, no OSI history.
- https://forums.polserver.com/viewtopic.php?p=16227 and ?p=16998 (via snippets): art.mul ceilings by client generation.
- Search snippets for Stratics wiki rare lists (Pacific/Atlantic/Lake Superior/Napa Valley/Catskills Rares); for UOGuide "Rare", "Timeline", "Event/Rares" (Halloween 1998 Abyss).
- https://www.uoforum.com/threads/event-rares-alltime-list.32044/ : opened; nothing before 2013.

**Blocked or failed (could not read; claims attributed to them are snippet-only)**
- HTTP 403: uoguide.com (Trammel, Rare, Timeline, Event/Rares, Despise, Halloween_Pumpkins), wiki.stratics.com (Rares pages, Shrinking Potion), uo.stratics.com items catalogue. web.archive.org is blocked by the fetch tool. HTTP 404: uorenn.com/wiki sub-pages. ultima.fandom.com: HTTP 402. DNS failures: uo.guide, new.tcrf.net.

---

## 8. Still UNVERIFIED (do not claim these without more work)
1. Exact Renaissance go-live date (Apr 3 vs Apr 27 vs May 4, 2000); Third Dawn / LBR exact dates (spread of days across sources).
2. Any Halloween 1997-1999 item list (pumpkins, jack-o'-lanterns, skeletons, candy, webs). Nothing found before 2006.
3. Any named rare with a confirmed year in 1997-2000 beyond the Seer-item names above; "Gold Candle", "bear rug rare", "bone throne" dates; "Bloody Table" is 2017.
4. Per-item launch existence of carpentry furniture (chairs, tables, armoire, bookcase, chests) and of tinkered clocks, signs, spyglass, telescope.
5. Existence in the April-2000 client of specific tiles; highest populated static id; a clean per-expansion id map (none published).
6. Whether deed-placeable rugs, tapestries, paintings, statues, fountains, armor stands, weapon racks existed in any form before 2001 (none found).
7. Dungeon-by-dungeon launch dates for Deceit, Destard, Shame, Wrong, Covetous, Fire; creature intro dates for Lich Lord, Balron, Dread Spider, Elder Gazer, Succubus, Shadow/White Wyrm, Ogre Lord, Giant Spider, Gazer.
8. Dates of the second batch of veteran-reward mini-monster statues (Ophidian, Reaper, Mongbat, Gazer, Fire Elemental, Wolf, ...).
9. The original (1997) purpose of the creature "Frame" tiles beyond Tracking-menu/pet-transfer evidence, which is from emulator code, not an OSI document.
