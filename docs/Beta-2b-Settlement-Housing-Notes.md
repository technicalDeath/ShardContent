# Beta 2b: settlement housing and its alternatives (proposed amendment to house zoning)

Status: **proposals from the owner's ideas of 2026-10-09 (settlements) and 2026-10-10 (a roadside ribbon and a distance-scaled rural fee); discussed, not signed off, nothing built.** Sections 1 to 5 are the settlement idea and its population model; section 6 adds the 2026-10-10 alternatives and the land-clearing cost they share. It belongs to [Beta 2b](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md) (house zoning, the "district decisions" batch) and would amend sections 11.4 to 11.6 of the [design contract](ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md), which today say the opposite. Per the usual rhythm it gets a work plan and the owner's sign-off before any code.

## 1. The idea (owner, 2026-10-09)

- Every town except Greater Britain stays unpopulated, to concentrate players.
- The other towns become **housing for players**, opening only when demand for housing in Britain overruns supply.
- **Wandering healers are available in every town.**
- As a housing district reaches a given occupancy, **certain vendors populate it; each full district triggers more**, so an active guild with enough members can populate a district and cause critical infrastructure to spawn.
- Purpose, in the owner's words: "proving that the shard population is enough to warrant spreading population density." The unlock gates are the proof.
- The keystone question, again the owner's: **how much population does a city need to feel alive?**

## 2. What it changes in the contract

Contract sections 11.4 to 11.6 (and the rural-housing text around them) make Greater Britain the **only** place with normal-cost residential districts, forbid districts around Cove, Vesper, Yew, Trinsic, Minoc and the rest, and make rural housing (a surcharge, 2x by default) the permanent overflow valve. This proposal replaces "rural is the permanent valve" with "settlements are the ordered overflow, and rural stays an optional extra". The machinery the contract already specifies carries it: a fixed expansion order, an occupancy trigger of about 80% or fewer than 20% usable lots, never closing an opened district, a staff command to open the next one, and `housingGeography` off until the owner approves. The proposal appends towns after Britain's last district.

## 3. The keystone: population and "alive" (model, not measurement)

**Definition.** A city feels alive when a player at its bank or market at a typical hour sees other players. The engine's view range is 18 tiles (`Core.GlobalUpdateRange`), so the measure is players within 18 tiles of the Britain bank.

| Players in sight | Feels like |
| --- | --- |
| 0 to 1 | dead |
| 2 to 3 | sparse |
| 4 to 8 | alive (target 6 or more at peak, 3 or more at a median hour) |
| 10 or more | busy |

**Formula.** In sight at the hub = peak concurrent players x share of them in Britain (0.40, range 0.30 to 0.55) x share of those near the bank (0.60). Peak concurrent is about 5% to 10% of monthly active accounts. Weak calibration: the MMO rule of thumb of [10 to 20 times monthly actives to peak concurrent](https://voxbooster.com/blog/mmorpg-statistics-2026/); [UO Evolution](https://uoevolution.com/) reports about 550 online on average and over 1,000 at peak on 10,000+ accounts; a [UO forum thread](https://forum.uo.com/discussion/1021/population) calls "the same old group of 10 people" an indecent population. Households wanting a normal-cost district are taken as about 28% of monthly actives (house owners around 40%, about 70% of them choosing a district over rural or Fire Island; range 15% to 40%). The model is `work/towns-model/model.py` (scratch).

| Monthly actives | Peak concurrent | In sight at the bank at peak (low / mid / high) | Normal-cost households (mid) | Britain's ~32 lots |
| ---: | ---: | --- | ---: | --- |
| 90 | 7 | 0.8 / 1.6 / 3.0 | 25 | 80% full |
| 150 | 11 | 1.3 / 2.7 / 5.0 | 42 | 1.3x full |
| 250 | 19 | 2.2 / 4.5 / 8.2 | 70 | 2.2x full |
| 400 | 30 | 3.6 / 7.2 / 13.2 | 112 | 3.5x full |
| 650 | 49 | 5.8 / 11.7 / 21.4 | 182 | 5.7x full |
| 1,000 | 75 | 9.0 / 18.0 / 33.0 | 280 | 8.8x full |

**Reading it.** Britain feels alive (6 in sight at peak) from about **15 to 25 players online at peak, roughly 200 to 330 monthly actives** (range about 180 to 670), and busy (12) from about **40 to 50 online**. The shard's concentration systems (bank, vendors and activities only in Britain) raise the two shares and would roughly halve the population needed.

**The finding that matters.** The Britain survey ([Alpha-3-Greater-Britain-Housing-Survey.md](Alpha-3-Greater-Britain-Housing-Survey.md)) found only about 30 to 35 practical small-house lots (a proven lower bound of 12 in the east pocket; north, south and far-east shortlists add a few more), because eastern spawners and the built-up city leave little land. On the model Britain's houses reach 80% at about **90 monthly actives, around 7 online, well before the city feels alive**. Housing pressure alone is therefore far too weak a proof: opening a town on it would spread a shard that is still too small to feel alive in one place.

## 4. Proposed rules

1. **Opening a settlement needs two proofs, not one.** (a) Britain's open districts are about 80% full of **active** houses (the contract's existing rule; abandoned houses must decay first, the inactive-house policy is already Beta 2b scope). (b) The hub is busy: the **median daily peak of players within sight of the Britain bank over 14 days is about 10 or more**, so that moving residents out still leaves Britain alive. Until both hold, overflow houses go rural or to Fire Island, as the contract already says. The 10 is a starting number to calibrate in beta, not a measured one.
2. **One town at a time, nearest to Britain first, in a fixed order.** Never all at once; never closed after opening.
3. **District size: about 30 households**, clustered tightly around the town square, a mix of small and medium lots. Density is what a player sees, so a compact 30 beats a sprawling 100 with the same people. A 30-household cluster shows about 3 residents in sight at peak (owners online about 25% at peak, about 40% of those at home at a given moment), so guild nights and vendors, not residents alone, are what make a settlement feel alive.
4. **Vendor tiers by household count, latched** (a tier, once earned, stays): at **6, 12, 20 and 30 households** (about 20%, 40%, 65%, 100%). A guild of about 12 reaches the second tier alone. The vendor list per tier is an owner decision; the principle is "what a household needs daily first (provisioner, innkeeper, banker), then trade vendors", few and thin, so **Britain stays the commercial hub and keeps what is unique to it** (Activity Board, curator, departure square, moongates, the deepest market). A full district makes the next district eligible.
5. **Wandering healers in every town from the start**, so a ghost always has somewhere to go.
6. **Counting is hard to fake.** A household counts when it is a distinct account (one house per account already holds), the house is of a minimum age and its owner has logged in recently; the figure must hold over several days. House cost is already a strong Sybil cost.
7. **Rural housing stays**, at its surcharge, so settlements are cheaper than scattering.
8. **Scale.** At about 1,000 monthly actives demand is about 250 households beyond Britain: **6 to 8 settlements**, opened one by one over a long growth curve, each surveyed only when the previous one nears full.
9. **State is shard-owned and persistent** (the district latches and tiers stored shard-side, vendors spawned as ordinary persisted NPCs, idempotent across restarts); no ModernUO save-format change; a staff command opens or seeds a district without a deployment.

## 5. Build the thermometer first

Before any of this ships, log (a) the number of players within sight of the Britain bank every minute, (b) distinct active accounts over 7 and 30 days and (c) players per segment of the Britain to Yew and Britain to Minoc roads (needed to choose a roadside, section 6.1), and show all three in a staff status command. Every number above is calibrated from that data during beta. This is small, safe and useful whatever is decided.

## 6. Alternatives raised on 2026-10-10 (owner)

### 6.1 Roadside housing ribbon

**Idea.** The roads connecting Britain with Yew, with Minoc, or with both get housing plots cleared along the roadside, so that running the road has a point: you see your neighbors' houses and discover player vendors. The owner offered it as an alternative to the other housing district options (the settlements of section 4).

**Assessment.**
- Exposure is the strength: every traveler passes every house, far more than in a cluster. Player vendors get foot traffic; no new NPC systems are needed; wandering healers can simply walk the road; segments open outward from Britain in a natural order.
- Length is the weakness. Britain to Yew is about 1,150 tiles in a straight line and Britain to Minoc about 1,550 (from the bank locations; roads wind, so more). At 15 to 25 players online at peak only a couple are on any one road, so a fully built road would feel empty.
- **Proposed shape:** a short ribbon first, about 150 to 250 tiles from Britain's gate, where nearly everyone leaving that way passes, grown outward in segments through the same two-part proof as settlements (section 4, rule 1). A rough capacity of 10 to 20 lots per 100 tiles of road (both sides, small and medium houses) makes a segment a district of about a dozen households; to be confirmed by survey.
- **Which road first:** survey both and choose by natural open land and measured traffic. Minoc is a guess (miners and smiths pass along it, so player vendors would sell to them); Yew has lumber and the abbey.

**Risks and gaps.** A ghost road if built too long; wilderness spawns along the road and reagent or resource sites that houses must not pave over (the survey already had to move a reagent spawner near Britain); how theft rules treat player vendors outside a town (not checked); house decay leaving gaps in the strip; vendor discovery should be a real tool (a nearby-vendors list or sign convention), not luck.

### 6.2 Distance-scaled rural placement fee

**Idea.** Rural placement fees scale with distance from a town center or an approved road, so housing concentrates. Land would be cleared around the appropriate areas.

**Assessment and fit with the code.** The existing quote (`HousingPlacementQuote`) computes the rural premium as `ceil(normalValue x (multiplier - 1))` from one constant, `housing.ruralCostMultiplier`, validated between 2.0 and 5.0; `HousingGeographyPolicy` already classifies each tile as residential, rural or protected. A distance function replaces the constant:
- a normal price inside a cleared roadside or settlement district;
- **2x at the district's edge, rising with distance to the nearest live anchor to a cap of 5x** (the validator range stands);
- the bands live in configuration, so tuning needs no deployment; future placements only (existing rural homes are never recharged, as the contract says); Fire Island unchanged; it is a small code change.

**Anchors are live only after proof.** An anchor is Greater Britain, an opened settlement or an opened roadside segment. Town centers of unopened towns are not anchors, so the price gradient never pulls people toward places the population has not yet earned (section 4, rule 1). This keeps the proof gates and the price gradient as one mechanism.

### 6.3 One principle, three pieces

Housing is cheapest where people pass and where services are, and "where" grows as the population proves it. The pieces are independent: (a) settlement districts, clusters around town squares (section 4); (b) the roadside ribbon (6.1); (c) the distance-scaled fee (6.2). (a) and (b) are alternative shapes for overflow housing (the owner called the ribbon an alternative); (c) works with either and is the cheapest to build and the easiest to reverse.

### 6.4 Land clearing is the shared cost

Both (a) and (b) need cleared land, and neither works without it. The Britain survey shows the existing towns have almost no free lots and that blocking statics (trees, rocks) are the largest rejection reason for placement. Statics are client data as well as server data, so clearing means:
1. editing the statics (and land where needed) with CentrEDSharp, already in the workspace;
2. putting the patched files into the server's data and into every player's client, through the shard's client package (the dist already carries the shard's own gump and text files, so a pipeline exists, but not for map data);
3. relocating the spawners over the cleared strip and ruling on resource and reagent sites;
4. a clearing budget that follows the proof gates: clear only what has earned it.

This is new work, so the first step is to prove the whole pipeline on one short stretch before committing to more.

### 6.5 Checks not yet made

- Survey the first 250 tiles of both roads for natural open land with the existing survey commands (`[HousingSurvey`), which also tells how much clearing a ribbon needs.
- Measure traffic per road segment (section 5, item c).
- Check the theft rules for player vendors outside towns, and how decay would gap a strip.
- Confirm the real road lengths and the capacity per 100 tiles.

## 7. Open questions

- **Healers.** Check the era behavior of wandering healers online before specifying (who they resurrect, fees, murderers), and whether other towns still have working guards and sane spawns (not yet checked).
- **Vendor ladder.** Which vendors at which tier, and how thin their stock and buy lists should be.
- **Order of towns** and the exact district polygon for each (a survey per town, only when needed).
- **Britain's own capacity.** If more Britain lots are wanted (moving more eastern spawners, using more of the surroundings), the settlement gate moves later; the survey's honest figure today is about 30 to 35.
- **Services in settlements** beyond the vendors (a bank is the big one: it removes the reason to visit Britain).
- **Whether settlements join the weekly "rekindled town"** idea in the Rekindling design, or stay separate.

## 8. Out of scope here

Pricing of settlement lots, resident-only perks, guild-owned districts, and any change to Fire Island housing.

## 9. Next step

The owner chooses among the shapes in sections 4 and 6 (settlements, a roadside ribbon, the fee gradient, or a combination; the fee gradient stands alone). Then sections 4 to 7 become the Beta 2b district-decisions work plan for sign-off; the first small steps either way are the staff-visible thermometer (section 5) and the road survey (6.5). Nothing is built, no flag changes, and the contract sections above are marked as under review, not rewritten.
