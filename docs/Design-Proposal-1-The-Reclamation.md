# Design Proposal 1: The Reclamation

**Status:** proposal (2026-10-02), not approved and not scheduled. Written at the owner's request from the vision statement alone, ignoring the roadmap beyond Beta 1 and the existing design contracts. It takes the shard as built through Beta 2a (safe world, Intent, Knocked Out, Wards, Hot Zones, Mastery) as its base.

**Vision it serves:** *A classic Ultima Online experience that keeps Felucca's thieves, criminals and murderers, and the emergent encounters they create, but not the griefing: a single world where deliberate systems concentrate the population, build community and draw players into contact with one another, and where the classic UO:R power ceiling holds, because the experience lies in the adventures and interactions that unfold in the world, not in the grind of character progression. Custom content extends that world outward with new activities and reasons to travel, while the core of play stays recognizable and true to the classic experience.*

## The idea

**The world state is the game.** Everything outside Britain's walls is divided into about a dozen *wards* along the old roads (the Britain crossroads, the Minoc mines, the Vesper canals, the Yew abbey, Trinsic, Cove, the Skara ferry, and so on). Each ward has one visible number, **Hold**, from 0 to 100, moved by what players do and by what they fail to do. The map is the scoreboard, shared by everyone on the shard.

| Hold | State | What is there |
| --- | --- | --- |
| 0-24 | **Lost** | Ruins. Heavy spawn, a raider camp with real loot, no patrols |
| 25-59 | **Contested** | Raider bands roam the roads, the best drops, the most fighting |
| 60-89 | **Held** | NPC patrols that fight monsters (never players), a healer's tent, a supply courier |
| 90-100 | **Secured** | The town's own vendors return, stables open, house placement is allowed |

A ward can only climb past Contested if the ward between it and Britain is Held, so the frontier radiates outward from the capital along the roads. At any moment two or three wards are where the fighting is, and everyone knows which, because the Steward's board in Britain says so. That solves population density structurally rather than by scheduling.

Hold decays every day. If players stop, the frontier recedes and towns fall. Nothing is ever finished: the experience is the holding, not the having.

## The five layers

### 1. Supply: crafting with a destination
The Steward posts what each frontier ward needs (ingots, bandages, arrows, potions, cloth, food, kindling). Prices rise with scarcity, so the board is a market signal every crafter reads. Goods are packed into a **Supply Crate** (a plain stock crate) and carried to the ward's waystone. Delivery raises Hold, pays gold, and writes the carrier's name on the stone.

The crate is the hinge of the design:
- It cannot be recalled or gated with, like a faction sigil in classic UO. Crates travel by road, boat or pack animal, which puts people on the roads.
- **Carrying a crate turns `[Intent` on.** The carrier is a lawful target while holding it. Pick it up and you have consented; set it down and you have not. No blue is ever attacked without cause, and every road fight is one both sides chose. This reuses the Intent system as built and has a classic precedent: sigil carriers were attackable.
- It can be snooped, stolen, dropped on death and looted from a Knocked Out carrier under the existing rules.

### 2. Crime: an economy for outlaws, not a nuisance
A stolen crate has two buyers. The **fence** in Buccaneer's Den pays gold. A **raider camp** in a Lost ward accepts it as sabotage and knocks Hold down hard. Either way the thief's name goes on the Den's own board, the **Black Ledger**, which runs the Den's titles and black-market vendors the way the Hall of Deeds runs Britain's.

Two capitals, two careers. Reclaimers hold the land; outlaws profit when it falls, because a ward that drops to Lost spawns a raider camp full of loot that only they know is coming. Every outlaw move is already legal under the ruled consent and Hot Zone rules. Bounties on outlaws are posted by players with real gold on the Britain board, and the head goes to whoever collects.

### 3. Roads and the sea: travel with stakes
Held roads have patrols; Lost roads have ambushes. Boats carry crates along the coast to Vesper, Skara and Trinsic without walking the road, which makes piracy a real occupation and keeps the shipwright in business. Pack horses and llamas carry more crates, giving tamers a role and raiders something to kill that is not a player.

### 4. Legacy: your name in the world
Characters stop growing at Grandmaster, so the world grows instead:
- Every waystone lists its contributors. When a ward is Secured, the top names are inscribed on that town's monument for the season.
- Housing exists only in Secured wards. A house stands because the community held the land; if the ward falls, its services go dark around it. A reason to defend a neighbourhood.
- **Seasons** are twelve-week arcs with a named threat (the orc warlord of Yew, the undead of Vesper). At season's end one Secured ward becomes *permanently* restored, vendors and all. Over a year the continent is visibly reclaimed by the people who played; the next arc threatens it again.

### 5. Density: two hubs and a frontier
Britain is the lawful hub (Steward, bank, stalls, Hall of Deeds). Buccaneer's Den is the outlaw hub (fence, Black Ledger, black market). Fire Island and Hythloth stay the permanent PvP answer. Between the hubs lies a frontier that moves. At peak, players are in one of four places, all of them places where other players are.

## How it touches the classic game
No new skills, items, caps or tiers. Each existing skill gets a reason:

| Skill | Role |
| --- | --- |
| Blacksmithy, Tailoring, Alchemy, Cooking, Fletching | Make supply; read the board; get paid and named |
| Mining, Lumberjacking | Contested wards have the richest nodes, so gathering is where the fighting is |
| Cartography | Surveys reveal raider camps and the week's safest roads; maps are sellable |
| Tracking, Forensics, Detect Hidden | Follow crate thieves, name them, post the bounty |
| Stealing, Snooping, Hiding, Stealth | The outlaw trade, now with buyers |
| Animal Taming | Pack animals and mounts for carriers; stock rules unchanged |
| Camping | A frontier camp is a safe logout point and a tiny supply delivery |
| Peacemaking, Provocation | Turn raider bands on each other |
| Healing, Veterinary | The healer's tent is NPC, but the field medic is a player |
| Magery | Gates do not carry crates, but they carry reinforcements |

Mastery, the Ward, Knocked Out and Hot Zones keep working exactly as built. Skill use at the frontier is real use, so it feeds Mastery without a special rule.

## A Tuesday night
A smith sees Minoc iron at triple price on the board, crafts for an hour, packs a crate and hires a tamer with a pack horse. Both go grey the moment they lift it. A thief at the bank snoops the crate and follows. On the Minoc road two reds, who read the same board, ambush them. The thief steals the crate in the confusion and vanishes. The tamer's horse dies, the smith is Knocked Out, the reds get nothing and pick a fight with the thief. The smith's guild answers her call; a tracker follows the thief toward the Den. Half the crate is fenced, Minoc slips to Contested overnight, a raider camp appears outside the mines, and on Wednesday a PvE party goes to clear it for the loot and the Hold. Every outcome feeds the next encounter, and nobody was griefed.

## Why it attracts and why it retains
It attracts because no classic shard offers a world that changes because of what players did last week, inside mechanics people already know. "Reclaim Britannia" is a pitch, and the frontier map is a screenshot.

It retains because the board changes daily, the frontier weekly, the season quarterly, and the thing a player works toward is a name on a monument and a town that stays restored, not a number on a skill. It gives thieves and reds a career with standing, which keeps the players who make a Felucca feel like Felucca.

## Build order
1. **The spine:** wards, waystones, Hold, decay, raider camps and the Steward's board, in three wards along the Britain-Minoc road. Testable in a month.
2. **Crates and the Intent flag**, then the fence and the Black Ledger.
3. **Services that return**, and housing in Secured wards.
4. **Monuments, seasons and permanence.**
5. **The skill flourishes** (surveys, tracking, camps, boats).

Each step is small, reuses stock items and spawners, and sits on the consent rules already ruled on.

## Risks
- Tuning decay against population; beta settles it.
- The crate's consent flag must be impossible to miss (a message on pickup, the Intent appearance, a warning before the first lift).
- The frontier must stay optional for pure PvE players, who can still hunt elsewhere; Hold rewards are access and names, never power.
