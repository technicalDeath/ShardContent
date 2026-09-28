# Alpha 3 Greater Britain housing survey

This is a terrain, static-object and stock-region pass for the Alpha 3 residential districts. It does
not establish launch district polygons or practical house capacity. The `housingGeography` flag
remains off.

## Source and method

The Felucca terrain came from local `UOData/map0LegacyMUL.uop` and the `Wet` land flag in
`UOData/tiledata.mul`. Britain town rectangles came from the pinned ModernUO
`Distribution/Data/regions.json` at commit `9fb5448445c0a53ebb77a4ad9d72e9ec06ce8f3d`.
The Alpha 2b Greater Britain rectangle is `x=1280..1749, y=1400..1899`, as validated by
`Alpha2bWorldGenerationConfiguration`. Every tile in that rectangle was counted once. A separate
overview plot surveyed `x=950..1999, y=1200..2199` in local scratch space.

| Source | SHA-256 |
| --- | --- |
| `map0LegacyMUL.uop` | `EA42CB16A224FACD3FA177C6001AE80B50C30C5EDB35877A4841CE865ECE3944` |
| `tiledata.mul` | `F44860782F4818CBFF36A9372A3F16E5747886E0064C72A4AEC922DFE1994E37` |
| `regions.json` | `CBFE5DF4097D16185CE3FD9B902B42F71029227C366247214CA16A401340687D` |
| `statics0.mul` | `AAC798AE8786D97EB893D5338E27113F3ACE606221C4A7F80C24E57BD4A19976` |
| `staidx0.mul` | `209319AEFF26E01C7EA7EC86B8F01E3D598E4D82411431C43CB6E9B6CCC69DE7` |

## Measured constraint

| Alpha 2b rectangle classification | Tiles | Share |
| --- | ---: | ---: |
| All tiles | 235,000 | 100% |
| Inside Britain's guarded town rectangles | 163,208 | 69.5% |
| Wet terrain | 47,666 | 20.3% |
| Outside town rectangles and non-wet | 50,735 | 21.6% |

The guarded and wet counts overlap; their shares must not be added. The last row is only an upper
bound on potentially usable terrain, not a placement capacity estimate. It includes roads,
uneven ground, static structures, spawns, landmarks, transition routes and other sites that must
remain open.

The pinned `TownRegion` derives from `GuardedRegion`, whose `AllowHousing` returns false. The
stock house-placement check calls that rule for occupied foundation tiles. Thus the Alpha 2b
rectangle is an operational world-population boundary, **not** a ready-made residential district.
The first normal-cost districts need a surveyed envelope around Britain that extends beyond the
guarded town footprint and is shaped around practical lots and travel corridors.

## Static and height filter

The second pass read the local Felucca static index/data and land elevations in the overview
rectangle `x=1000..1999, y=1200..2199`. It applied the stock road land-ID ranges from
`HousePlacement` and parsed item flags from `tiledata.mul`. A static was marked as a near-ground
obstruction when it had `Impassable` or non-background `Surface` flags and its Z/height overlapped
the approximate ground-to-20-Z band. This deliberately errs toward excluding uncertain sites.

| Filter inside Alpha 2b rectangle | Count |
| --- | ---: |
| Dry tiles outside guarded town | 50,735 |
| Of those, road-ID land tiles | 1,192 |
| Of those, near-ground blocking static tiles | 7,229 |
| Dry, outside town, non-road, without marked static obstruction | 42,341 |
| Overlapping flat, clear 8×8 windows fully inside the rectangle | 3,259 |

The road and static counts can overlap. The 8×8 windows are **positions**, many of which overlap
each other; they are not distinct lots and cannot be used as a house-capacity figure. The strongest
candidate concentrations in the wider overview are immediately east/northeast of the town
footprint (`x=1700..1899, y=1300..1599`) and south/southwest of it (`x=1200..1599,
y=1800..1999`). These are survey targets, not approved district boundaries.

An isolated UOContent test bootstrap with the installed client data then called stock
`HousePlacement.Check` for the classic small old house (`multiID=0x0064`) at sampled centers in
those two areas. This is a stronger terrain, static, footprint, yard and region filter than the
8×8 approximation, but the test world has no accepted Alpha 2b decorations, doors, spawns or
current houses, and it does not load the live shard housing policy.

| Sample rectangle | Step | Centers | Stock-valid centers | Main rejection counts |
| --- | ---: | ---: | ---: | --- |
| East/northeast, `1700..1899 × 1300..1599` | 5 | 2,400 | 231 | BadStatic 1,580; NoSurface 402; BadLand 187 |
| South/southwest, `1200..1599 × 1800..1999` | 10 | 800 | 57 | BadStatic 449; NoSurface 167; BadLand 127 |

The isolated test's valid coordinates are in local scratch evidence under
`work/alpha3-stock-placement-survey.txt`; the dense eastern pocket is around
`x=1845..1895, y=1465..1555`. These numbers are sampled, overlapping centers for one small-house
type. They do not establish practical lot capacity, district boundaries or release readiness.

This first pass did not apply `stadif0` static patches, generated Alpha 2b world objects, current
house multis, every item-height interaction, the stock five-tile yard and border rules, or the
server's region hierarchy at each candidate. The server sampling below adds those checks against
a disposable copy of the accepted Alpha 2b world.

## Server placement sampling

The administrator-only `[HousingSurvey` command provides a bounded pass through ModernUO's
actual `HousePlacement.Check` on Felucca. Run it on a disposable copy of the accepted Alpha 2b
world. It creates and deletes an ordinary player probe inside each game-loop batch, so no
existing player account or character is required:

```text
[HousingSurvey run <xMin> <yMin> <xMax> <yMax> <classicEntryIndex> <step>
[HousingSurvey status
[HousingSurvey results [page]
[HousingSurvey spawns <x> <y> <classicEntryIndex>
[HousingSurvey cancel
[HousingStatus
```

The command accepts at most 4,096 candidate centers per run and a step of 1–16 tiles, checks in
small game-loop batches, and pauses during world saves. Its temporary probe is removed before
each batch ends, so it is never present for a save. It uses the selected stock classic house
footprint and reports the count of valid centers and each rejection reason. It does not create a
house or save the world. Use several small rectangles and house sizes around the candidate areas.
The results command pages through valid center coordinates, 20 per page, until the next run or
server restart; capture them with the survey metadata when evaluating potential lots.
The `spawns` subcommand scans the populated Felucca world for spawner bounds that overlap the
selected classic house foundation plus an eight-tile buffer. It reports the matching spawner
GUIDs, anchors and bounds without changing them. It is a conflict screen, not a clearance result:
region-wide spawns, active mobile movement and resource sites still need inspection. `HousingStatus`
reports the configured district order and open state, center occupancy against each soft capacity,
other geographic house counts, decay-eligible houses and missing owners. Its occupancy uses house
centers; it is not a count of available lots or an automatic expansion trigger.
Valid centers can overlap heavily and **are not a count of distinct lots**. Record the world
snapshot, active housing flags, selected house, rectangle and step with each result before using
the numbers to design districts.

### Populated-world rehearsal

On September 27, 2026, a disposable server loaded a copy of the accepted Alpha 2b automatic
backup `2026-09-27-15-55-00`, current content assemblies, and source shard rules. It used
the installed Felucca client data and listened on an isolated loopback port. The housing geography
flag was **off**; all configured residential and protected polygon lists were empty. The stock
check therefore measured existing terrain, statics, placed world objects, regions, footprint and
yard constraints, without asserting that the shard housing policy would permit the site.
Each row below is a separate run. The house names are stock classic placement-tool entries.

| Area and sample rectangle | Step | House | Centers checked | Valid overlapping centers | Rejections |
| --- | ---: | --- | ---: | ---: | --- |
| Eastern pocket, `1845..1895 × 1465..1555` | 5 | SmallOldHouse | 209 | 141 | BadLand 14; BadStatic 41; NoSurface 13 |
| Eastern pocket, same rectangle | 5 | SmallTower | 209 | 135 | BadLand 19; BadStatic 39; NoSurface 16 |
| Eastern pocket, same rectangle | 5 | TwoStoryVilla | 209 | 96 | BadLand 22; BadStatic 70; NoSurface 21 |
| Eastern pocket, same rectangle | 5 | GuildHouse | 209 | 76 | BadLand 14; BadStatic 93; NoSurface 26 |
| South/southwest, `1200..1599 × 1800..1999` | 10 | SmallOldHouse | 800 | 37 | BadRegion 254; BadLand 50; BadStatic 293; NoSurface 166 |
| South/southwest, same rectangle | 10 | TwoStoryVilla | 800 | 13 | BadRegion 284; BadLand 44; BadStatic 281; NoSurface 178 |
| Broad Fire Island vicinity, `4400..4790 × 3400..3880` | 16 | SmallOldHouse | 775 | 18 | BadLand 94; BadStatic 289; NoSurface 374 |
| Northwest Fire Island vicinity, `4410..4580 × 3400..3550` | 5 | SmallOldHouse | 1,085 | 75 | BadLand 55; BadStatic 597; NoSurface 358 |
| Northeast Fire Island vicinity, `4600..4770 × 3400..3560` | 5 | SmallOldHouse | 1,155 | 62 | BadLand 179; BadStatic 524; NoSurface 383; BadRegionHidden 7 |
| West/northwest, `1000..1290 × 1300..1550` | 10 | SmallOldHouse | 780 | 20 | BadRegion 35; BadLand 133; BadStatic 353; NoSurface 239 |
| Far southwest, `1050..1350 × 1800..2150` | 10 | SmallOldHouse | 1,116 | 32 | BadRegion 289; BadLand 118; BadStatic 476; NoSurface 198; BadRegionHidden 3 |
| Far east, `1900..2200 × 1300..1600` | 10 | SmallOldHouse | 961 | 39 | BadLand 38; BadStatic 190; NoSurface 694 |

The accepted backup's server load reported 55,733 items and 12,469 mobiles. These results are
from its disposable copy, not the shared running world. The broad Fire Island rectangles extend
beyond the island; their valid coordinates still require intersection with the outdoor island
polygon and explicit clearance for travel, dungeon approaches, spawns, resources and landmarks.
The eastern pocket has many valid centers for several house sizes, but most overlap. The southern
sample is more fragmented and includes numerous stock region denials. After all runs, a staff
`global count` still found zero ordinary `PlayerMobile` objects, confirming that the temporary
survey probe did not remain in the world.

### Spawn conflict found during lot selection

A later client session on the same disposable accepted world paged all 141 SmallOldHouse centers
in the eastern `1845..1895 × 1465..1555` pocket and teleported a staff character to a valid center
at `(1870,1490)`. Active Mongbat and Orc mobiles were nearby. The generated Alpha 2b spawn inputs
explain why: two `Outdoors.json` spawners at `(1877,1515)` each have a 30-tile home range and include
Mongbat/Orc and stronger wilderness creatures; another pair at `(1862,1434)` borders the north end.
`WildLife.json` also has a 50-tile wildlife spawner at `(1798,1471)`. The stock house placement
check did not classify these anchors or home ranges as a site reservation. Consequently **141
valid overlapping centers are not 141 approved housing sites**, and the eastern pocket cannot be
opened as drawn without a spawn-safe lot plan or a deliberate, audited relocation of the overlapping
spawners. Keep its district polygons empty for now.

The southern sampled candidates have their own generated spawn clusters: `Outdoors.json` anchors
near `(1383,1949)`, `(1435,1917)`, `(1475,1958)` and `(1541,1895)`, among others, plus wide-range
wildlife and reagent spawns. Screen those areas against home ranges before selecting any lots.
Preserve the accepted Alpha 2b population baseline unless a separate relocation pass proves the
new sites and resulting world audit. No spawn manifest or active world object was changed in this
survey.

The same session paged the 75 northwest and 62 northeast Fire Island SmallOldHouse candidate
centers. They are scattered, with a small northwest cluster around `(4425..4450,3520..3545)` and
an east-side cluster around `(4690..4755,3440..3500)`. The east-side cluster overlaps wildlife
at `(4692,3494)` and Orcs at `(4729,3485)`; the northwest cluster had reagent items near a
staff-visited valid center `(4430,3530)`. Nearby Fire Island wilderness also contains Dragon,
Drake and Daemon spawners. This makes the small northwest pocket a better **survey target**, not
an approved residential polygon. Its actual island membership, shoreline and approach, resource
preservation and count of distinct non-overlapping lots still need explicit checks.

An offline screen of the paged SmallOldHouse centers against the generated Felucca
`homeRange` squares, expanded by 12 tiles as a conservative foundation/yard allowance, found
the following. The screen includes wilderness, wildlife and resource spawners; its result is a
planning filter, not a live placement verdict or an approved lot count. Region spawners and
custom spawn bounds require the separate live check.

| Sample | Valid overlapping centers | Without `Outdoors.json` home-range overlap | Without any manifest home-range overlap |
| --- | ---: | ---: | ---: |
| East `1845..1895 × 1465..1555` | 141 | 0 | 0 |
| West/northwest `1000..1290 × 1300..1550` | 20 | 0 | 0 |
| North `1700..1840 × 1300..1450` | 35 | 15 | 0 |
| South `1200..1599 × 1800..1999` | 37 | 20 | 0 |
| Far southwest `1050..1350 × 1800..2150` | 32 | 16 | 0 |
| Far east `1900..2200 × 1300..1600` | 39 | 12 | 0 |
| Fire northwest `4410..4580 × 3400..3550` | 75 | 61 | 0 |
| Fire northeast `4600..4770 × 3400..3560` | 62 | 21 | 1 |

This screen strengthens the need for an explicit relocation decision in the east. The other
areas may still support lots if the owner accepts housing near wildlife or resource routes, but
those sites need visual review and measured non-overlap before district boundaries are chosen.
As a rough shortlist, a greedy 18-tile center separation among the non-`Outdoors.json` centers
leaves eight in the south, six in the far southwest, three in the north and five in the far east,
versus 18 northwest and 11 northeast on Fire Island. The southern samples overlap, so their
shortlists must not be added together. These are **not** parcel capacities: the separation ignores exact multi footprints,
roads, routes, shorelines, resource appearance, polygon edges and interaction between different
house sizes. It only shows why preserving all eastern monster spawners may make the Greater
Britain launch districts very small unless another area is found.

These are stock eligibility samples, not approved launch lots or district capacity. Next, select
non-overlapping lots from the valid-center pages, inspect them in the client, reserve protected
corridors and sites, then check placement and payment with housing geography enabled on another
disposable copy. Candidate coordinate pages remain in local scratch logs, not in this source
document because no location has yet been approved.

## Work required before drawing launch polygons

1. Use the populated-world stock-valid centers to select non-overlapping lots of several house
   sizes. Count practical lots, then choose district soft capacities against expected launch
   demand and the 125–150% initial-supply target.
2. Inspect selected lots and approaches with a real client on a disposable world, including
   representative purchase and placement attempts.
3. Mark no-housing buffers around roads, the graveyard, waterfronts, docks, bridges, dungeon
   routes, scenery, resource/spawn sites and event space. Check Fire Island separately.
4. Define connected Greater Britain A–D polygons and explicit protected polygons, then verify
   every boundary and representative placement with a real client. Normal-cost districts must
   stay within Greater Britain; no other town enters the expansion sequence.

Neither the terrain count nor the stock-region overlay proves that any specific tile can hold a
house. Keep the housing flag disabled until classification, surcharge, expansion, persistence,
metrics and client/restart tests meet the roadmap exit criteria.

## Owner-approved east-Britain spawner relocation

The owner selected relocation of the two overlapping monster spawners. The source manifest now
overrides GUID `362c3cc5-8548-43be-8fab-4d981cab5ed1` from `(1877,1515)` to
`(1750,1250)` and GUID `41dd143d-0df5-41eb-a23e-bc65a7255c49` from `(1862,1434)`
to `(2000,1210)`, both on Felucca at Z0. This preserves their creature lists, counts, timing,
home ranges, and the total of 1,546 canonical spawner definitions. Their chosen dry, flat
destination tiles are north of the surveyed housing windows. The relocation does not approve
either destination as a safe spawn site; client visual review and creature movement checks remain.

On a disposable copy of the accepted world, the controlled `Alpha2bWorldGen ... rerun` moved
both live GUIDs, removed them from their old anchors, and passed the exact 410-sign,
385-teleporter, 1,546-spawner, 1,345-door audit. An immediate second rerun and the first
rerun after save/restart each created zero decorations and zero doors and passed the same audit.
The owner subsequently approved moving the broad reagent spawner north. Distinct house
lots, the replacement resource route, active mobile movement, and district boundaries still
need review before housing can open.

Re-screening the recorded stock-valid centers against the **canonical** post-relocation
manifest (last definition wins by both position and GUID) leaves all 141 eastern centers
without an outdoor monster home-range overlap. A simple 18-tile greedy separation yields
12 eastern shortlist centers. This is a useful increase over the pre-relocation zero. The
resource spawner has since moved north, but wildlife touches some. The 12 centers remain
a planning shortlist rather than a residential capacity or approved placement sites.

### Simultaneous small-house rehearsal

An administrator probe on the disposable accepted world placed a stock `SmallOldHouse`
sequentially at all twelve shortlisted centers, each owned by a separate temporary ordinary
player. `HousePlacement.Check` returned `Valid` before every placement, and all twelve
houses coexisted simultaneously. The probe deleted the houses and owners in the same game
loop command; `[HousingStatus` then reported zero houses. The source housing flag was off.
This establishes a **twelve-lot lower bound for this exact small-house arrangement** on
that world snapshot, subject to live housing geography and resource-site policy. It does
not establish capacity for towers, villas, arbitrary player placement, roads, access or
district pricing. Raw results are in `work/alpha3-housing-client/lotprobe2.log`; a local
terrain overlay is `work/alpha3-east-housing-shortlist.png`.

A staff teleport to `(1875,1505)` found Blood Moss near `(1876,1503)` and other reagents
nearby. `[HousingSurvey spawns 1875 1505 0` reported one conflict: reagent spawner
`046e36ec-faf1-4f5f-8f8f-4cf50e2ba3ef` at `(1938,1408)`, count 160,
`homeRange=200`, with bounds `(1738,1208)–(2139,1609)`. Its source mix contains all
eight classic reagents. The owner approved moving this source north into nearby forest.
Its effect on placed-house interiors was tested before the move as described below.

A disposable live placement probe exposed a stock resource-spawn gap: with a
`SmallOldHouse` at `(1895,1545)`, six of 20,000 sampled positions from this
spawner landed inside the house. `Map.CanSpawnItem` accepted the house center
at Z7, while the private-house region check correctly identified it as
blocked. UOContent now applies that existing house-region check to items as
well as mobiles in both random and cached spawn-position paths. Repeating the
same 20,000-position probe with the new assembly produced **zero** positions
inside the house. Both probes deleted the temporary house and owner. Evidence
is in `work/alpha3-housing-client/resource2.log` and `resource3.log`.
The replacement resource route and wider housing-site survey remain open.

### Owner-approved reagent spawner relocation

The source manifest now overrides reagent spawner GUID
`046e36ec-faf1-4f5f-8f8f-4cf50e2ba3ef` from `(1938,1408)` to
`(1938,1220)` on Felucca at Z0. Its count 160, eight-reagent mix, 200-tile
home range, walking range, and 11–23 minute delay are unchanged. The local
terrain sample around the new anchor was dry forest/grass. Its northern route
and reagent accessibility still need a client survey.

On the disposable accepted world, preparation retained 1,546 canonical
spawners. The controlled first rerun moved the live GUID and passed the exact
410-sign, 385-teleporter, 1,546-spawner, 1,345-door audit. The immediate
second rerun and first rerun after save/restart each generated zero decorations
and zero doors and passed the exact audit. The live spawner screen found the
GUID at `(1938,1220)` with bounds `(1738,1020)–(2139,1421)` and zero spawner
overlaps at east-Britain center `(1875,1505)`. Raw client evidence is in
`work/alpha3-housing-client/reagentmove.log` and `reagentrestart.log`.

### Fire Island small-house rehearsal

The same disposable accepted world placed eighteen stock `SmallOldHouse` lots
simultaneously in the northwest Fire Island shortlist. After that group was
deleted, a separate northeast group placed eleven simultaneously. Every center
passed the source Fire Island polygon check and stock `HousePlacement.Check`.
The probe deleted each group and its temporary owners; `[HousingStatus` reported
zero houses afterward. These are lower bounds for the two exact small-house
arrangements, **not** a combined 29-house capacity or approval for larger
houses. The evidence is in `work/alpha3-housing-client/firelotprobe.log`.

The live spawner screen at northwest center `(4440,3520)` found two broad
reagent spawners: `cdd876a8-1378-4ccd-8f12-9cdac9c3487a` at `(4570,3340)`
and `9f1da2ac-4a31-415d-99c6-76921de812b0` at `(4282,3700)`, each with a
200-tile home range. The northeast center `(4690,3560)` had no spawner-bound
overlap with its foundation and eight-tile buffer. Resource routes and other
house sizes still require review before Fire Island residential polygons open.

## Placement and rural-price integration audit

`HousePlacement.Check` is called by both purchase routes, and its shard tile hook covers the
center and every occupied foundation tile. It can reject protected land, but it cannot quote a
premium or confirm payment. The charge must be calculated from the final, freshly checked
footprint after the ordinary placement verdict succeeds.

| Route | Current final placement path | Normal value for a 100% rural premium |
| --- | --- | --- |
| Placement tool | `HousePlacementEntry.PlacementWarning_Callback` checks again after the preview, constructs a house, sets `house.Price = Cost`, then calls `Banker.Withdraw(from, Cost)` | That entry's `Cost`, which is the amount charged at placement |
| Classic deed | `HouseDeed.OnPlacement` checks, constructs and places a house, then deletes the already purchased deed | The matching deed's normal purchase value, not the placement-tool `Cost`; for example, a stone-and-plaster deed sells for 43,800 while the classic tool entry is 37,000 |

The stone workshop is a stock pricing exception: its deed vendor value is 60,600 while the
constructed house's `DefaultPrice` is 63,000. The premium basis follows the deed value.

The rural confirmation must name the premium and total economic cost. The deed route must charge
only the additional premium because the deed was purchased earlier. Both callbacks must recheck
placement, ownership, land class, charge and available funds after confirmation; a changed quote
requires a new confirmation. A failed or cancelled debit must leave the deed and land untouched.
The premium is never added to `house.Price` or a replacement deed's value, so demolition,
re-deeding and transfer cannot return it. Tests must cover both routes, stale confirmations,
insufficient funds and a footprint crossing a residential/rural or rural/protected boundary.

The UOContent purchase callbacks now invoke a shard quote hook after the stock verdict, show a
separate rural confirmation, and recalculate the quote before withdrawal. Tool placement debits
normal cost plus premium; deed placement debits only the premium. The shard classifier reads
explicit `housing.residentialDistricts`, `housing.fireIslandResidentialRegions`, and
`housing.protectedRegions` from the source rules. All three lists are empty until surveyed.
Buccaneer's Den and unsurveyed Fire Island tiles are protected; other Felucca land is
provisionally rural. Locked Greater Britain districts remain unavailable, and only an initial
ordered prefix may be open. The rural multiplier is configurable and defaults to 2.0. This is
**not** the launch classification: Greater Britain and Fire Island residential regions and
additional protected polygons still need the populated-world survey.
The housing feature flag remains disabled and its validation rejects activation.
