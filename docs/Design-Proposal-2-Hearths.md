# Design Proposal 2: Hearths

**Status:** proposal (2026-10-02), not approved and not scheduled. Written at the owner's request from the vision statement alone, ignoring the roadmap beyond Beta 1 and the existing design contracts. It takes the shard as built through Beta 2a (safe world, Intent, Knocked Out, Wards, Hot Zones, Mastery) as its base. Companion to [Design Proposal 1: The Reclamation](Design-Proposal-1-The-Reclamation.md).

**Vision it serves:** *A classic Ultima Online experience that keeps Felucca's thieves, criminals and murderers, and the emergent encounters they create, but not the griefing: a single world where deliberate systems concentrate the population, build community and draw players into contact with one another, and where the classic UO:R power ceiling holds, because the experience lies in the adventures and interactions that unfold in the world, not in the grind of character progression. Custom content extends that world outward with new activities and reasons to travel, while the core of play stays recognizable and true to the classic experience.*

## Design constraints (owner, 2026-10-02)
Every activity in this proposal, and in any later one, must satisfy all of these at once:
1. Classic UO:R, recognisable, no power creep.
2. Keeps thieves, criminals, murderers and emergent encounters; no griefing.
3. Concentrates population and draws players into contact.
4. Ties in every playstyle: PvE, PvP, gathering, crafting, taming, thieving, support.
5. Every activity is doable alone or in a small group, so a small starting population has a full game.
6. Every role has its own on-ramp at the site, never gated behind another role (a lone gatherer must be able to gather).
7. Roles present together make each other's work better, so solo players want company.

The owner's illustration of the pattern: monsters spawn, their corpses are *also* gathering nodes, and a special forge at the centre of the event crafts special items, so several roles are pulled to one spot without any of them being required.

## The idea

A **Hearth** is a camp the Crown lights at one place for one week: a fire, a quartermaster, a field forge, loom and still, beside ordinary resources and an ordinary spawn. At small population there is one Hearth and it is a short walk from Britain. Later, two or three burn at once. Everything below happens on one screen of ground.

### Every role arrives alone and works alone
| Role | Alone, with nobody else there | Better when others are there |
| --- | --- | --- |
| **Miner, lumberjack, fisher** | Ordinary veins, trees and water at the site, richer than elsewhere and with a chance of the week's special material | Monster corpses are extra nodes (hide, bone, scale); guards keep the spawn off; a tamer's pack animal hauls the ore to town |
| **Fighter, mage** | The site's spawn, its loot and gold, and a named beast that walks in twice a day | Crafters repair and supply on the spot; gatherers' output makes the week's gear; bards turn the spawn on itself |
| **Smith, tailor, alchemist, cook** | Bring your own materials and craft at the field forge; the site's recipes exist nowhere else | Site-gathered materials make the special variant; fighters' hides and shells supply it; buyers are standing right there |
| **Tamer** | The site's fauna, including one creature or hue found only there; the quartermaster pays for pack animals | Fighters clear the predators; gatherers hire the pack animals; the Den pays double for a stolen mount |
| **Healer, bard** | The quartermaster pays for healing the camp's NPC workers and for calming the spawn | Players pay more |
| **Cartographer, tracker** | Survey the raiders' approach; the quartermaster buys the map | Players buy it first |
| **Thief** | The quartermaster's locked chest and the raiders' camp cache, stock Lockpicking and Stealing | Everyone at the site is carrying something |
| **PvP** | Sign on as a **Warden**: the fire pays for raider kills; bounties on reds who come through | **Wreckers** show up |

No link in that table is required for any other. Each is an extra.

### The Fire: why a solo player wants company
Everything delivered to the fire feeds it: ore, pelts, a tamed horse, a crafted item, a raider captain's head, a map, a healed worker. The fire has a visible level, and its level raises the site for everyone at once: richer nodes, rarer drops, a second named beast, more recipes at the forge, a healer's tent, a bank courier, and at the top a one-week cosmetic reward for every contributor. The fire burns down every night. One miner can keep it lit. Five mixed roles make it roar. Nobody has to group; the fire makes a crowd pay.

### Embers: the goods and the road home
The forge makes **ember goods**: the week's items, cosmetic or convenience only (a hue, a repair-free season, a feast that fills everyone at the fire), never stats. They, and the week's raw material, are worth most in Britain, and they cannot be recalled with, so they go home by road, boat or pack animal. That is the reason to travel both ways, and it is where thieves and reds find them.

### Wreckers: the outlaw side, by consent
Buccaneer's Den wants the Hearth to fail and pays for it. A player who takes the Den's coin is a **Wrecker**: paid for stolen ember goods, for sabotaging the fire (a stolen fuel cache knocks a level off it), for a Warden's head. Signing as a Wrecker makes the player a lawful target to Wardens and them to the Wrecker, at the site and on its roads, for the week. Nobody who did not sign is touched. Ordinary stealing stays stock and legal everywhere, so a thief who signs nothing still has the quartermaster's chest and everybody's pockets. When the Hearth is lit inside a Hot Zone, the whole site is open PvP and the Wardens' fire pay goes up.

### Hearthstones: legacy and rhythm
When the fire goes out on Sunday, the site's stone keeps the names of those who fed it, by role, with the week's top name in each. Seasons rotate which Hearths burn and what they make, and a season's final Hearth is lit in Britain itself, at the walls, where the spawn is a siege and the forge makes the gate's repairs.

### Three players, and thirty
**Three online:** a miner, a smith and a thief. The miner digs the site vein, the smith forges from it at the field anvil, the fire rises a level and the vein gets richer. The thief picks the quartermaster's chest, snoops the smith's pack and lifts an ember blade, and the two chase him toward the Den. Each came alone; all three had a reason to be on the same tile.

**Thirty online:** three anvils working, a guard line on the spawn, pack trains to Britain, two Wrecker crews working the road, a named beast on the hour and the fire at its top level, with every contributor's name going on the stone.

## How it touches the classic game
Nodes are stock ore, wood and fish; the forge, loom and still are stock crafting stations with extra, cosmetic-only recipes; the camp is stock tents and an NPC quartermaster; the spawn and raiders are stock monsters; stealing, lockpicking, taming and bounties are stock. Mastery, the Ward, Knocked Out, Intent and Hot Zones work exactly as built; the Warden/Wrecker flag is the only new consent rule and it mirrors guild war. Rewards are gold, access, cosmetics and names, never power.

## Build order
1. One Hearth near Britain: the camp, the fire and its levels, richer nodes, the spawn and the named beast, the field forge with three recipes. Playable by one person.
2. The quartermaster's pay (pack animals, healing, maps), corpse nodes, the Hearthstone.
3. Ember goods, the no-recall rule and hauling.
4. Wardens, Wreckers, the Den's pay and the consent flag.
5. Rotation, seasons, Hot Zone Hearths and the Britain siege Hearth.

## Risks
- The fire's level curve must reward one player and still leave headroom for thirty; tune in beta.
- Site recipes must stay cosmetic or convenience; the first "ember sword that hits harder" breaks the power ceiling.
- The Warden/Wrecker flag must be unmistakable (a visible mark, a confirmation on signing, a clear end).
- A Hearth is only a pull if the board in Britain, the crier and the website all say where it is this week.
