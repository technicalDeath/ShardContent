# Unified Design: The Rekindling

**Status:** design proposal (2026-10-02), not approved and not scheduled. Written at the owner's request: apply the seven design constraints to the whole shard plan, with every linked design included, and tie it all together. It keeps what is built through Beta 2a and reuses the plan's approved systems wherever they survive the constraints. Where a system changes, the change is listed with the ruling it needs. This document does not replace the roadmap or the contract; it is the proposal for how they should be re-planned.

**Vision:** *A classic Ultima Online experience that keeps Felucca's thieves, criminals and murderers, and the emergent encounters they create, but not the griefing: a single world where deliberate systems concentrate the population, build community and draw players into contact with one another, and where the classic UO:R power ceiling holds, because the experience lies in the adventures and interactions that unfold in the world, not in the grind of character progression. Custom content extends that world outward with new activities and reasons to travel, while the core of play stays recognizable and true to the classic experience.*

**The seven constraints** (owner, 2026-10-02): classic and recognisable with no power creep; thieves, criminals and murderers kept, griefing not; population concentrated and players drawn into contact; every playstyle tied in; everything doable alone or in a small group; every role has its own on-ramp at the site, never gated behind another role; roles present together make each other's work better.

---

## 1. Diagnosis of the current plan

The plan already contains almost every part a great design needs. What it lacks is a single place and a single reason that puts those parts on the same ground. Measured against the constraints:

| Plan system | Where it fails the constraints |
| --- | --- |
| Rotating Hot Dungeon and Cool Dungeon as *different* dungeons | Sorts PvP and PvE players into different places on purpose ("the systems serve different populations"). Thieves are banned from the Cool Dungeon. Gatherers, crafters and tamers have no on-ramp in either. |
| Expedition region and trade route | Good for gatherers and haulers, but cargo is unstealable by design, so thieves and PvP are excluded; crafters have nothing to do at the destination; fighters are incidental. The parts don't touch. |
| Pilgrimage | A solo race for a skill-gain buff: the one reward the vision says not to use. Everyone walks the same road, then disperses. |
| Wanted, Nemesis, Shipwreck, Artisan Signatures, Destination Vendor | Each is a fine horizontal loop for one playstyle, standing alone. None gives another role a reason to be present. |
| Roleplay POIs | Permanent and in Yew, so they pull a slice of the population away from wherever everyone else is, except in a Yew week. |
| Rekindled camping | A utility skill with a list of flavour options and no place in the world's rhythm. |
| The weekly board | Advertises five simultaneous rotations in five places, which is the dispersion the board is meant to prevent. |

None of these needs to be cut. They need to happen in the same place, on the same week, for the same reason.

---

## 2. The idea: each week, Britain rekindles one fallen town

The continent has been overtaken and Greater Britain is the only living city. Every week, the city sends an expedition to **rekindle one fallen town**: Minoc, Vesper, Cove, Yew, Trinsic or Skara Brae. For seven days that town's square has a lit **Hearth**, a camp around it, a relit forge, a returning merchant, a bounty board, a healer, a stable; its dungeon is the week's dungeon; its shrine is the week's shrine; its coast is the week's coast; its road from Britain is the week's road. On Sunday the fire goes out, the camp packs up, and the town is a ruin again until its turn comes round.

This gives the shard exactly four places at any moment, and all four are places where other players are:

| Place | What it is | Rules |
| --- | --- | --- |
| **Greater Britain** | Home. Bank, housing districts, vendors, the Activity Board, the curator, the departure square | Safe world |
| **The rekindled town** | The week's frontier: camp, forge, dungeon, shrine, coast, the road there and back | Safe world in town and on the road; the dungeon has Cool floors and Hot floors |
| **Fire Island and Hythloth** | Permanent PvP and the PvP residents' district | Hot |
| **Buccaneer's Den** | The outlaw capital: the fence, the Marque board, the black market | Hot |

Everything the plan rotates separately now rotates together, because it all belongs to one town. The name the owner chose for the shard, Rekindled, is the name of the weekly act.

### Why this satisfies the constraints at once
- **Concentration:** one town, one dungeon, one road, one departure square. The board has one line: *This week Britain rekindles Minoc.*
- **Every role, independently:** a town has ore and trees and fish, a dungeon, a forge, a shrine, a stable, a chest to pick, a road to rob. Section 4 gives each role its own on-ramp with nobody else present.
- **Roles amplify each other:** the Hearth (Section 5) is fed by every role's work and raises the site for every role at once.
- **Thieves, criminals and murderers kept, griefing not:** the town and the road are safe-world; the dungeon's deep floors are Hot; open cargo and Marques are consent flags; stealing stays legal everywhere outside banks, with Wards as built.
- **Small population:** one town, one road, one dungeon, all scaled by the Hearth; a single player can light it.
- **Classic and recognisable:** towns, camps, forges, dungeons, shrines, trade routes, bounties, pilgrimages and pack animals are all 1999 UO. Nothing new is added to combat, items or caps.

---

## 3. The week

**Friday reset (the plan's boundary).** The Activity Board names the town. The road is announced. The Hearth is lit at level 0 by the Crown's quartermaster.

**Departures every four hours (the plan's Pilgrimage windows, widened).** Cargo is issued at any hour, so a solo player is never locked out. But for fifteen minutes every four hours the Britain square is the place to leave from: the Pilgrimage for the town's shrine starts only in the window, the crier calls it, and haulers and escorts time their cargo to it. Pilgrims, haulers and escorts leave Britain together and arrive together. The Den posts its Marques each Friday, so the thieves know the timetable too. The road is busy six times a day by design, and everyone knows when.

**The town, all week.** Gathering, the dungeon, the forge, the shrine, the coast, the camp. The Hearth rises and falls with what is delivered.

**Nightly, at a fixed hour.** The raid (Section 5). The camp defends the fire or loses a level.

**Sunday: Homecoming in Britain.** The fire goes out and the town's **Hearthstone** keeps the week's names by role. That evening the Britain square holds the Homecoming: the crier reads the Hearthstone, the curator opens the week's trophies, the merchant sells the week's leftover stock in Britain for one evening only, and the feast, if the fire reached it, is laid in the capital. Everyone comes home at once, which is the one weekly gathering Britain itself gets. Next Friday, another town.

**A season is seven weeks**: the six towns and the Hot week on Fire Island. At the season's end the Britain square gets a monument naming the season's top contributors by role and the week with the highest fire. Cosmetic, permanent, and the only ladder that doesn't end.

---

## 4. Every role arrives alone and works alone

The table is the design. Each row is a complete solo activity using only stock mechanics; each "better with" is an extra that exists only because someone else is there.

| Role | Alone, with nobody else in the town | Better when others are there |
| --- | --- | --- |
| **Miner, lumberjack** | The town's veins and woods carry the Expedition **+50% yield** (plan 15.7) and the **Logistics** carry bonus (15.8). Haul to Britain or sell at the camp. | Fighters' corpses are extra nodes (hide, bone, scale). Guards keep the spawn off the vein. Tamers' pack animals haul. Crafters buy at the forge, so the trip home is optional. |
| **Fisher** | Coastal weeks: the week's water is +50% and the **Wreck Charts** (plan 12.1) surface here. | Shipwrights at the harbour; a boat party for the salvage site; buyers at the camp. |
| **Fighter, mage** | The town's dungeon: **Cool floors** (upper) and **Hot floors** (deep), the **Wanted** bounties (20.6A) for this dungeon's species, **Nemesis** spawns (6.1) with trophies. | Crafters repair and supply at the camp. Healers and bards. Gatherers' materials make the week's gear at the forge. Rival parties on the Hot floors. |
| **Smith, tailor, alchemist, cook, fletcher, carpenter** | The town's **relit forge**: bring your own materials, make the ordinary grades (crafting design §4) plus the **town's regional pattern** (cosmetic variants from the Destination Vendor's collections, 15.12A, now made rather than bought). | Site materials and Nemesis parts make the signature variants; fighters need repairs now; the camp is a market with buyers in it. |
| **Tamer** | The town's fauna, one regional creature or hue per town; the quartermaster buys **pack animals** for the Logistics haul. | Gatherers hire the animals; fighters clear the predators; a Fire Island resident wants a mount; the Den pays double for a stolen one. |
| **Healer, bard** | The quartermaster pays for healing the camp's workers and calming the town's spawn. | Players pay more. |
| **Cartographer, tracker** | Survey the road's ambush points (the plan's checkpoints); the quartermaster buys the map. | Escorts buy it first; trackers follow cargo thieves. |
| **Hauler (anyone, new players first)** | **Bonded cargo** (plan 15.5): character-bound, unstealable, modest pay, the ordinary route with checkpoints. The first-week on-ramp. | Travel with the departure; the road is safer with escorts. |
| **Escort / PvP** | **Open cargo**: unbound, stealable, lootable, pays three times bonded, and the carrier is **Intent-flagged while carrying** (consent, as the Intent system built in Alpha 3). Also the **Hot floors**. | Marque holders come for the cargo; rivals race the Hot floors; the fire pays Wardens for raider kills. |
| **Thief** | Stock snooping and stealing everywhere in the town (Wards as built), the dungeon's chests on the Cool floors, the quartermaster's locked chest. | A **Marque** from the Den: paid for open cargo stolen on the week's road and fenced in the Den; signing flags the thief to the week's escorts. A crowded camp is a crowded pocket. |
| **Pilgrim** | The **Pilgrimage** (15.13) to the town's shrine, departing Britain in the window, checkpoints on the week's road. The reward is the **Pilgrim's Mark** (cosmetic sash hue, title progress, a shrine token for the curator), not a skill-gain buff. | The race against the same window; the road shared with the cargo run. |
| **Roleplayer** | The town's camp is a stage; Yew weeks light the **RP POIs** (16A) and their guestbooks. | Everyone else is there. |
| **Camper** | **Rekindled camping**: the Hearth's keeper. Kindling feeds the fire; a camper tending it through the night slows its decay by Camping skill; the signal fire guides the party; the camp stall (camping §6.3) is the field market. | The whole camp depends on the fire, and a kept fire is a higher fire for everyone at dawn. |
| **Guild** | Stock guilds and guild wars as built. | The guild that fed the fire most flies its banner over the camp for the week, and the names go on the stone under it. A guild war between two camps' guilds is the week's story. |
| **Fire Island resident** | Hythloth and Fire Island are Hot all week, as built; a Hot-Zone Hearth week (Section 7) brings the expedition to them. | |

Nothing in the right column is required for the left column. That is constraint 6. Everything in the right column exists only because of constraint 7.

---

## 5. The Hearth: the one mechanism that makes a crowd pay

The Hearth is a fire in the town square with a visible level, 0 to 5. **Everything given to it feeds it, weighted by value**: ore and logs and fish, Nemesis parts, bounty heads, pack animals, crafted goods, completed cargo, a pilgrim's arrival, a map, a healed worker, kindling. It burns down every night. One player can keep it at level 1. Five mixed roles make it roar.

**The Hearth is a sink, not a buyer.** What goes into the fire is consumed. It pays in fire level and in a name on the stone, never in gold. Players still sell their surplus to each other at the camp and to NPCs at home; the fire takes what they choose to give. That makes it the resource sink the plan's economy section asks for and never finds, and it means the only way to buy standing is to give something up.

**The fire draws the raid.** The town's dungeon notices the light. Each night at the shard's configured peak hour the camp is raided by the dungeon's own inhabitants, and the raid's size follows the fire's level: a few at level 1, a war band at level 5. A raid that reaches the square knocks the fire down a level. Guards, healers and bards have a job every night that every other role wants done, and the fire's reward is paid for in risk by the people who earned it. Raiders are ordinary spawns with ordinary loot, so the raid is also the night's hunt.

| Fire | What the town gains, for everyone at once |
| --- | --- |
| 1 | The healer's tent; the vein and woods at +50% |
| 2 | The stable (pack animals bought and hired); the forge's regional pattern unlocked |
| 3 | The returning merchant opens (the Destination Vendor's **core** stock) |
| 4 | Cool floors pay the +10% premium; the merchant's **rare** offers open; a second Nemesis cap |
| 5 | The Hot floors pay the full rotating premium (20.6); the town's **feast** (cook's recipe) fills everyone present; every contributor's name goes on the Hearthstone |

The plan's reward premiums survive unchanged in value; they are now *earned by the town* rather than switched on by the calendar. That is the whole difference between a rotation and a community. A solo miner at level 1 is already better off than at home; by level 4 the smith wants her ore, the fighter wants the smith, the tamer wants the fighter, and the thief wants all of them.

**Outlaw counterplay.** A fenced open cargo in the Den takes a level off the fire. Thieves and reds have a reason to work the week's road that is the mirror image of everyone else's reason to defend it, and every move is one a signatory agreed to.

---

## 6. What changes from the plan, and the rulings needed

| System | Keep / merge / change | Ruling needed |
| --- | --- | --- |
| Expedition region, +50% yield, Logistics, checkpoints, bonded cargo | **Keep** as the spine | None |
| Rotating Hot Dungeon and Cool Dungeon | **Merge:** the town's dungeon, Cool upper floors, Hot deep floors, one boundary inside | The floor split; Cool stealing stays legal (the plan disables it; constraint 2 says keep thieves, Wards protect) |
| Hot and Cool premiums | **Keep the numbers; gate them by fire level** | Yes |
| Wanted | **Keep;** one list for the town's dungeon, Marks on Hot floors, Seals on Cool | None beyond the merge |
| Nemesis | **Keep;** Nemesis corpses also yield a part usable at the forge for the trophy variant | Minor |
| Shipwreck | **Keep;** charts for the week's coast surface in the week's water | Minor |
| Pilgrimage | **Keep the route, windows and race; replace the skill-gain buff** with a cosmetic mark and token | Yes (removes an approved reward) |
| Trade cargo | **Keep bonded; add open cargo** (unbound, Intent-flagged, 3× pay) and the Den's **Marque** | Yes (the plan deferred cargo theft) |
| Destination Vendor | **Keep the collections and the gold sink; move it into the camp** and gate its stock by fire level; the regional pattern is also craftable at the forge | Yes (changes #36's placement and access rule) |
| Road speed | **Keep** | None |
| Artisan Signatures, crafting overhaul | **Keep;** the forge is where they are made in public | None |
| Rekindled camping | **Keep the core package; the Hearth is its purpose**, the camp stall is the field market | The camping doc's open questions |
| RP POIs | **Keep;** lit in Yew weeks, guestbooks as designed | None |
| Hot-Zone veteran title | **Keep** as a cosmetic | None |
| Housing | **Keep** Greater Britain districts, Fire Island district, rural; rural houses on the week's road may register as waystations (a checkpoint and a name on the stone) | Optional |
| Diminishing returns | **Keep** as combat balance; unrelated to concentration | As designed |
| Weekly board | **Change:** one town, one line | None |
| Permanent Hot Zones, Mastery, Wards, Knocked Out, Intent, pets | **Unchanged** | None |

Nothing approved is cut. Three approved rules change (Cool stealing, Pilgrimage reward, vendor access), and two deferred things are added (open cargo, the Marque). Everything else is placement.

---

## 7. The town circuit

Each town brings its own assets, so each week has a different shape without different rules:

Dungeon and shrine pairings are by measured distance from each town's stock go-location to the stock dungeon entrance and the shrine decoration (`regions.json`, `Britannia__shrines.cfg`), each dungeon used once:

| Week | Road from Britain | Dungeon (tiles from town) | Shrine | Coast | Extras |
| --- | --- | --- | --- | --- | --- |
| Cove | the shortest road | Covetous (370) | Compassion, on the road itself | the Cove coast | the new player's week |
| Minoc | the mountain road | Wrong (530) | Sacrifice | the Minoc bay | the richest ore; the smith's week |
| Vesper | the long road | Deceit (across the eastern bridge; the far week) | Sacrifice, shared with Minoc | the Vesper canals | the fisher's week |
| Yew | the Yew road | Despise (760) | Justice | none | the RP trinity; the orc fort |
| Skara Brae | road and ferry | Shame (680) | Spirituality | the Skara coast | the sailor's week |
| Trinsic | the southern road | Destard (710) | Honor | the Trinsic coast | the tamer's week (dragons) |
| **Fire Island** | the ferry to the Hot week | Hythloth, Hot as built | Valor, the island's own | the island shore | the Wardens' week |

The seventh week of each season is the **Hot week**: the expedition goes to Fire Island itself, the Hearth is lit at the Hythloth entrance, the whole site is Hot as built, the shrine is Valor, and the fire pays the Wardens most. Fire Island residents host; everyone else decides whether the fire is worth it.

---

## 8. The first hour, four players, and forty

**A new player's first hour.** She finishes creation in Britain with the starter package. The board says: *This week Britain rekindles Minoc. Next departure in forty minutes.* The quartermaster gives her a bonded cargo, which cannot be stolen and pays on delivery, and tells her the road. At the window she finds six other people in the square: two pilgrims, a tamer with a pack horse, an escort with open cargo, and a man who is clearly a thief. They walk the mountain road together because the window put them there. In Minoc there is a fire, a healer, a forge with a smith at it, and a stable that opened an hour ago because somebody delivered ore. She hands in the cargo, is paid, and her name is on the stone. Nobody explained a system to her. She has met seven players and learned the one sentence that runs the shard.

**Four online, Minoc week.** A miner, a smith, a tamer and a thief. The departure window opens in Britain; the tamer takes bonded cargo, the thief takes nothing he'd admit to, and they walk the mountain road together because the window put them there. In Minoc the miner has been digging since noon and the fire is at level 1. The smith buys her ore at the forge and makes the Minoc pattern; the tamer's pack horse hauls the surplus; the fire hits 2 and the stable opens, so the tamer sells a second horse. The thief picks the quartermaster's chest, snoops the smith, lifts a pattern blade and runs for the road, and all three chase him. Four people, one square, one story, and nobody was griefed.

**Forty online, Trinsic week.** The fire is at 5 by Saturday. Three anvils working, a guard line at the Destard stairs, two parties racing the Hot floors for the Wanted dragon, pack trains on the southern road, open cargo escorts fighting a Marque crew at the bridge, pilgrims arriving at Honor in a pack, a Nemesis drake's hide on the forge, the merchant's rare offers open, the feast on, and forty names going on the Trinsic stone on Sunday.

---

## 9. Why it attracts and why it retains

It attracts because "every week Britain rekindles a fallen town" is one sentence that every playstyle can see itself in, and because the screenshot of a lit town square full of players beside a ruin is the shard's identity in one image.

It retains because the week is new every Friday, the road is busy six times a day, the fire rewards showing up more than showing off, the town circuit comes round every seven weeks with a monument at the end, and the four places are always the same four places, so a returning player always knows where everyone is.

---

## 10. Build order (replaces the content of Beta 2b to Beta 3)

1. **The spine:** the Expedition region, road, checkpoints and bonded cargo as planned, plus the camp, the quartermaster and a Hearth with levels 0 to 2 (healer, stable, forge). One town. Playable by one person.
2. **The dungeon:** the town's dungeon with Cool and Hot floors, Wanted and the premiums gated by fire.
3. **The roles' extras:** corpse nodes, Nemesis parts at the forge, pack-animal hire, the regional pattern, the Pilgrimage to the town's shrine with its cosmetic mark, the departure window issuing everything at once.
4. **The outlaw layer:** open cargo with the Intent flag, the Marque and the fence, the fire penalty.
5. **The circuit:** the other five towns, the Hot week, the Hearthstone, the season monument, Shipwreck on the coasts, RP in Yew.
6. **Housing** as planned, in parallel; it does not block any of the above.

Each step reuses stock items, spawners, regions and the consent rules already ruled on. Each is small enough to verify on a disposable host with the existing Navrey drivers.

### How this re-plans the roadmap
| Roadmap phase | Today | Under this design |
| --- | --- | --- |
| Beta 2b | House zoning, rotating Hot Dungeon, Rekindled camping | House zoning as planned; **the spine** (step 1) with the Hearth as camping's purpose; the week's dungeon with Cool and Hot floors (step 2) in place of a separate rotating dungeon |
| Beta 2c | Expedition, cargo, Pilgrimage, roads, Nemesis, Salvage, Wanted | The same systems, placed in the town (step 3) and given the outlaw layer (step 4); the Pilgrimage reward ruling; Shipwreck on the week's coast |
| Beta 2d | Crafting overhaul | As planned; the forge in the square is where it happens in public |
| Beta 3 | Cool Dungeon, rename, roleplay, BOD tiers | The Cool floors already exist; the rename to Rekindled names the weekly act; RP lights in Yew weeks; the circuit and the season monument (step 5) |
| Beta 4 | Hardening and launch | Unchanged |

---

## 10A. The constraint audit

Each role, checked against the seven constraints. "Alone" is constraint 5 and 6 together; "pulled" is constraint 3 and 7; "kept" is constraint 2; "classic" is constraint 1 and the vision's power ceiling.

| Role | Alone | Pulled to the town | Better with others | Kept (crime) | Classic |
| --- | --- | --- | --- | --- | --- |
| Gatherer | +50% nodes, Logistics, bonded sale | the yield and the fire | corpse nodes, guards, pack animals, buyers | can be robbed; Wards as built | stock nodes |
| Fisher | +50% water, Wreck Charts | the coast is the week's coast | boat parties, shipwright, buyers | pirates at sea | stock SOS |
| Fighter | Cool floors, Wanted, Nemesis, the raid | the dungeon is the week's dungeon; premiums by fire | repairs, healers, materials, rivals | Hot floors; reds on the road | stock dungeons |
| Crafter | the forge, own materials, the regional pattern | the pattern exists only here; the buyers are here | site and Nemesis materials; repairs wanted now | can be robbed at the forge | stock crafting, cosmetic variants |
| Tamer | regional fauna, pack animals for hire | the stable opens with the fire | hauls hired, predators cleared | stolen mounts fenced | stock taming |
| Healer, bard | paid by the quartermaster | the camp is the work | players pay more | | stock skills |
| Hauler, new player | bonded cargo, any hour | the window and the road | company on the road | nothing to steal, by choice | the plan's cargo |
| Escort, PvPer | open cargo, Hot floors, the Hot week | three times the pay; the premiums | Marque crews, rivals, Wardens' fire pay | consent by Intent flag and by floor | the Intent system as built |
| Thief | pockets, the chest, Cool-floor chests | everyone is here | the Marque, open cargo, the fence | the point of the role | stock stealing |
| Pilgrim | the race and the mark | the shrine is the week's shrine | the window's crowd | | the plan's Pilgrimage, cosmetic reward |
| Roleplayer | the camp as a stage; Yew's POIs | the week is where the people are | everyone | | the plan's POIs |
| Camper | the Hearth's keeper | the fire is the camp | a kept fire is everyone's dawn | | stock campfire and bedroll |
| Guild | wars as built | the banner | the stone | | stock guilds |

No cell is empty where a constraint applies. The two places where the plan's own rules resist the constraints are flagged for rulings in Section 6: stealing on the Cool floors, and the Pilgrimage's skill-gain reward.

---

## 11. Risks and the answers

- **The Hearth can be fed with junk.** Contributions are weighted by the quartermaster's buy price and capped per item type per hour; bulk junk raises nothing.
- **Alts and AFK feeding.** The fire counts delivered value, not time; an alt delivering is a player delivering. If it is abused, the per-account hourly cap is the lever.
- **Open cargo consent must be unmistakable.** A confirmation on pickup, the Intent appearance while carrying, a message on drop. The bonded tier is always there for anyone who wants no part of it.
- **Thieves at small population** have the chest, the pockets and the Marque; at tiny population the Marque's target is the NPC courier, so the role exists from day one.
- **A town without an asset** (Yew has no coast; Minoc and Vesper share a shrine) simply has fewer rows that week. The rules never change; the shape does.
- **Vesper's dungeon is far.** Deceit sits across the eastern bridge, so the Vesper week is the long one. That is a feature once a season, not a flaw: it is the week the road matters most, and the Logistics buff and pack animals earn their keep.
- **Rule load.** The player learns one sentence: *this week Britain rekindles Minoc; go there.* Everything else is discovered on arrival. That is fewer concepts than the plan's five parallel rotations.
- **Fire Island and Hythloth stay relevant** through the Hot week and the Hot floors; they are the permanent answer and the circuit visits them.
- **A fire three players can't light is worse than no fire.** The level thresholds scale with the week's average online count: a three-player shard can reach the feast in a good evening, a forty-player shard has to work for it, and the board states what the fire needs this week. The fire asks more of a bigger town.
- **The stairs between Cool and Hot floors are a Hot Zone boundary** and get the same unmistakable entry and exit messages Hythloth's entrance has, with the Knocked Out, loot and Execute rules switching at the step. A new player cannot walk into open PvP without being told.

---

## 12. Iteration log

**Pass 1** produced the merge (one town, one week) and the role table.

**Pass 2** found that the role table still gated two things: the Cool floors excluded thieves (the plan's stealing ban) and the Pilgrimage rewarded progression; both are listed for rulings. It also found that the fire had no outlaw counterplay, which made thieves spectators; the Marque and the fence penalty fix that.

**Pass 3** checked the four-player case and found the departure window did the pulling that no system had done before: it is the plan's Pilgrimage cadence, widened to issue cargo and Marques too, so solo travellers leave together without being asked to. It also checked rule load and replaced the five-line board with one line.

**Pass 4** asked what a town without a dungeon, shrine or coast does, and answered it with the circuit table: fewer rows, same rules. It added the Hot week so Fire Island and Hythloth are part of the circuit rather than outside it, and confirmed every system in Section 6 either keeps its approved form or lists the ruling it needs.

**Pass 5** found three economic and rhythmic faults. The quartermaster buying deliveries made the Hearth a gold faucet; it is now a sink that pays in fire and names. The week had nothing between Friday and Sunday but decay; the nightly raid, scaled by the fire, gives every night a fight that every role wants won, and prices the reward in risk. Britain had nothing of its own; the Sunday Homecoming is the capital's weekly gathering. It also wrote the new player's first hour, which turned out to be the design's best feature: she meets seven players before she has learned a single system.

**Pass 6** audited every role against every constraint (Section 10A) and fixed what the audit found: cargo is issued at any hour so solo players are never locked out of the window; Marques are posted in the Den, not handed out in Britain; the camper's Camping skill keeps the fire overnight, which gives the skill the purpose the Rekindled camping design was looking for; and guilds got a banner over the camp at no mechanical cost. It mapped the build order onto the roadmap's phases so the owner can see what this replaces and what it keeps.

**Pass 7** read the design as an opponent. It scaled the Hearth's thresholds to the week's population so a small shard can light the fire, and made the Cool-to-Hot staircase a proper Hot Zone boundary with the Hythloth messages. It then re-read the role table, Section 6 and the circuit for contradictions and found none left: every plan system is placed, every role has a solo row, every amplification is optional, and the three approved rules that change are named with their rulings.

**Pass 8** checked the circuit against the map instead of memory. Measured from each town's stock go-location, the first table had Deceit 1,600 tiles from Minoc and Covetous nowhere near Vesper; the table now pairs each town with its nearest unused dungeon entrance and nearest shrine decoration, with the distances, and gives the Hot week the Valor shrine on Fire Island. The season is seven weeks, not six, so the Hot week fits.
