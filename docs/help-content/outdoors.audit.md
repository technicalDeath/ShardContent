# Audit: outdoors Skill Guide pages

File audited and fixed in place: `work/help-gumps/parts/outdoors.skills.json` (Mining, Lumberjacking, Fishing, Camping, Tracking, Herding, AnimalTaming, AnimalLore, Veterinary). Original saved only in the auditor's scratchpad; the diff is the table below. File parses (`json.load`), ASCII only, no `<`/`>` except `<BR>`, every `requires` is a real `DeferredFeatureFlags` name, every page still has `stats` + `gain`, 6 to 8 headings and 2,100 to 6,000 characters of own text (the 900 / 3 minimum holds on all nine).

Paths below are relative to the workspace root. "Vendors.json" means `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json` (the Britain-only generated spawn file the world actually loads; it equals the stock `Spawns/shared/felucca/Vendors.json` inside Britain bounds minus the excluded types, plus `britain-vendor-overrides.json`, which only adds mage-shop NPCs).

## Counts

| | |
| --- | --- |
| Sentence-level claims read against code, config or data | about 410 (every sentence and table line of the 9 pages, gated paragraphs included) |
| Wrong against the code, fixed | 8 |
| True but misleading or imprecise (missing condition, rounded the wrong way, wrong range), fixed | 12 |
| Removed: unsupported, inference or duplicate of a generated block | 6 sentences (plus the 9 identical Faint Memories paragraphs, removed per the coordinator) |
| Left alone (verified as written) | the rest, about 370 |

## Changes

| Page | Before | After | Source |
| --- | --- | --- | --- |
| all 9 | `FaintMemories` paragraph | deleted | coordinator rule 2 (Welcome guide covers it once) |
| Mining | "uses one of the tool's 50 uses" | "uses one use of the tool (a new Pickaxe or Shovel has 50)" | `Items/Weapons/Axes/Pickaxe.cs:15,41-52` (exceptional +50 under UOR), `Items/Skill Items/Harvest Tools/Shovel.cs:10`, `BaseHarvestTool.cs:75-85` (exceptional doubles) |
| Mining | "about 1 dig in 4 gives the better metal and most of the rest give iron" | "...gives the better metal, and the rest give iron or nothing" | `Engines/Harvest/Core/HarvestSystem.cs:163,352-371`, `Mining.cs:193-200`: at the listed skill 25% metal, iron is 0.5 x Mining% (32.5% at 65), so "most of the rest" was false below the top metals |
| Mining | "teaches Mining up to about 30" | "about 30 to 33" | `Mobiles/Vendors/NPC/Guildmasters/MinerGuildmaster.cs:12` (Mining 90-100), `BaseCreature.cs:2859-2866,4754` (a third, max 42). Spawned: Vendors.json spawner at 1417,1578,30. `BaseVendor.cs:114` CanTeach true, no override |
| Mining | "A tinker can also make a Pickaxe or a Shovel..." (no Shovel source) | Pickaxe from a blacksmith plus "a character created with Mining skill starts with one"; "The town shops do not sell a Shovel"; "make ... yourself with Tinker's Tools" | Shovel is sold only by `SBMiner`/`SBTinker`, used by Miner, Tinker, Vagabond, GolemCrafter (`Mobiles/Vendors/NPC/*.cs`), none in Vendors.json; starter Pickaxe `Engines/Character Creation/CharacterCreation.cs:486-509,1219-1223`; craft `Engines/Craft/DefTinkering.cs:256,262` |
| Mining | "A Pickaxe or Shovel is also the tool for digging up the chest on a treasure map." | "you need a Shovel in your pack. A Pickaxe does not count" | `Items/Maps/TreasureMap.cs:277-293,571` (`HasDiggingTool` looks for `BaseHarvestTool`); `Pickaxe.cs:10` is a `BaseAxe`, `Shovel.cs:7` is a `BaseHarvestTool` |
| Lumberjacking | "...a bardiche and a halberd." | adds "(those two are used up after 150 good chops)" | `Items/Weapons/PoleArms/BasePoleArm.cs:10-23` (IUsesRemaining, 150), `HarvestSystem.cs:245-259` |
| Lumberjacking | "carpenter ... up to about 20" | "about 20 to 27" | `Mobiles/Vendors/NPC/Carpenter.cs:16` (Lumberjacking 60-83); Carpenter spawned, Vendors.json 1430,1597,20 |
| Lumberjacking | "A tinker can also make one..." | "You can also make one yourself with Tinker's Tools" (no tinker vendor exists) | `DefTinkering.cs:250` |
| Fishing | "..., so fishing is mostly a slow, quiet way to train the skill." | clause removed (inference) | none |
| Fishing | "holds 5 to 15 fish at a time" | "5 to 15 catches" | `Fishing.cs:75-76`; any successful pull (boots, rare fish, net) consumes one, `HarvestSystem.cs:214` |
| Fishing | "far from every shore ... deep for about 25 tiles in every direction, so you need a boat" | "deep open water: the game checks the water around the spot you fish in, out to about 25 tiles along each diagonal"; boat claim removed | `Items/Skill Items/Fishing/Misc/SpecialFishingNet.cs:323-354` (target plus 5,10..25 tiles on the four diagonals; nothing about boats or shores) |
| Fishing | "a sodden treasure map" | "a sodden piece of parchment (a treasure map)"; "Each is rarer lower down" added | `Fishing.cs:414-418` (the name the player sees), `Fishing.cs:15-18` (chance (skill-80)/4000 grows with skill) |
| Camping | "Your pets do not go with you." | "Only a bonded pet beside you would come with you, and there is no bonding on this shard, so your pets stay behind." | `CampTravelService.cs:1088` calls `TeleportPets(..., onlyBonded: true)`; `BaseCreature.cs:4138-4166`, `:1389`, `:4323`; `Configuration/modernuo-era-gates.json:8` (`taming.enableBonding` False) |
| Camping | "an ordinary orange fire" | "an ordinary fire" | colour unverified; `CampTravelService.BlueFire.cs:180` only sets hue 0 |
| Camping | "campfire lit by a member of your party" | "by another member" | `CampTravelService.cs:172,275` (refusal OwnFire) |
| Tracking | "finds living things" | "finds creatures and people" | `Skills/Tracking/Tracking.cs:246` skips the dead only under `Core.AOS`; under UOR dead players (ghosts) are listed |
| Tracking | "There are no footprints to follow here: the arrow does the work." | removed (absence claim) | none |
| Tracking | "You can use Tracking again 10 seconds after you last used it." | "You must wait 10 seconds after using Tracking before you can use it, or any other skill from your skills window, again." | `Server/Skills.cs:796-800` (the delay is the global `NextSkillTime`) |
| Tracking | "every use below 10.0 gains. Tracking is an easy skill, but ..." | removed; "the first check is the one that trains you" kept | duplicates the generated `gain` block |
| Herding | "Herding has few uses beyond moving animals, so many players raise it only as far as they need." | removed (opinion, unsupported) | none |
| AnimalTaming | "It is a hard skill to raise, because ..." | "The animals worth having ask for a lot of skill." | class label is printed by the generated block |
| AnimalTaming | difficulty list with 11, 17, ... 84, 94, 95, 96 and "the animals in the world" | exact values 11.1 ... 84.3, 93.9, 95.1, 96.3; header "most of the tameable animals"; "desert and forest ostards" (the Frenzied Ostard is 77.1); giant rats added at 29.1 | each class's `MinTameSkill` (`Mobiles/Animals/**`, `Mobiles/Monsters/**`); `Skills/AnimalTaming.cs:206` compares the exact value, players see one decimal; spawn counts from the generated Spawns/*.json |
| AnimalTaming | "listed at 29 or lower always obeys" | "29.1 or lower" | `BaseCreature.cs:1779` (`MinTameSkill <= 29.1`) |
| AnimalLore | "Animal Lore 110 at wild creatures that cannot be tamed" | adds "and a skill stops at 100 here" | `Skills/AnimalLore.cs:54`; `shard-rules.json` `individualSkillCap` 100; `Server/Skills.cs:250-330` (Value = Base at 100) |
| AnimalLore | "Use it on wild creatures once you reach Animal Lore 100 ..." | "use it on a wild animal that can be tamed" | `AnimalLore.cs:49-58` |
| Veterinary | "A poisoned pet trains you only at 60 and above." | "only when both Veterinary and Animal Lore are 60 or more" | `Items/Skill Items/Misc/Bandage.cs:322,442-446` |

## Verified and left as written (principal items)

- Harvest numbers: Mining 8x8 patches, 10-34 ore, 10-20 min refill, 2-tile range, 0.9 s dig, 50-use tools, vein weights 496/112/98/84/70/56/42/28/14 (about half iron), metal requirements 65..99, smelt difficulty 50 (nil at 25, certain at 75) and colored ore difficulty +-25, ore 2/7/12 stones and 12.5/12.5/75 split (tiledata read from `UOData/tiledata.mul`), ingot 0.1 stone, large/medium/small ingot yield. Felucca double yield is off under UOR (`HarvestSystem.cs:193`). Lumberjacking 4x3 patches, 20-45 wood, 10 logs, 20-30 min, 1/2/2/2/3 swings (0.9, 2.5, 4.1 s), log 2 / board 1 stone, 20% axe damage at 100, passive gain. Fishing 8x8, 5-15, 4-tile range, 8 s, the catch table (computed shares 38/54/74 fish, 38/33/25 nothing, 19/10/1 footwear, 5/3/1 rare), magic fish effects, big fish 3-200 stones, serpent holding net/map/bottle (25% deep sea), net spawns monsters.
- Prices from the SBInfo lists with the vendor types that really spawn in Britain (Vendors.json): Pickaxe 22 (Blacksmith x2, `SBBlacksmith.cs:74`; the Weaponsmith stocks it only in one of three shop rolls, so the page rightly names the blacksmith), Hatchet 25 (Weaponsmith x4, outside the random switch, `SBWeaponSmith.cs:35`), Crook 20 (Blacksmith and Weaponsmith, both unconditional), Fishing Pole 15 and fish 1 (Fisherman x2), Kindling 2 and Bedroll 5 (Provisioner x2), logs 1 / boards 2 (Carpenter x1), iron ingot 4 (Blacksmith), Bandage 5 (Healer x1, `SBHealer.cs:16`), horse 550 / pack horse 631 (AnimalTrainer x3). The shop price scalar resolves to the base price (`BaseVendor.cs:1384`, `GenericBuy.cs:70-90`).
- Trainers (code only, not tried live): Miner guildmaster (Mining 90-100), Carpenter (Lumberjacking 60-83), Fisherman (Fishing 75-98), AnimalTrainer (Taming 90-100, Lore 64-100, Veterinary 65-88); a third of each, 1 gold per 0.1 (`BaseCreature.cs:2849-2866,4736-4800`; Welcome "Training" page agrees). No Camping, Tracking or Herding trainer is named (the only candidates, Provisioner and Furtrader, roll Camping/Tracking around the 60 threshold).
- Welcome page references: topics titled "Training", "Skill locks 101" and "Fighting other players" exist (`WelcomeGuide.GettingStarted.cs:173,212`, `WelcomeGuide.cs:268`).
- Camping: Kindling lights on a beside-tile (`Kindling.cs:116-165`), no dungeon fires, secure camp 7 tiles / 30 s / not embers (`Campfire.cs:44,190-208,252`), Bedroll flow and the 10 s window (`Bedroll.cs`), 5-minute default logout (`Region.cs:200,876`; Young system is off in `Configuration/FeatureFlags/flags.json`), nothing else reads the secure entry, fire timings 100/160, 200/320, 300/480 s from `shard-rules.json` `camping` and `CampingService.cs:56-67`, feeding rules, starter kit 5 Kindling + Bedroll (30 stones, not touched by `StarterWeightBudget`), camp travel numbers (`campTravel`: 2 Kindling, 5 s, 30 min, first place at 50, 6 max, 30 s secure) and refusals (`CampTravelService.cs:158-262`), blue fire rules (`CampTravelService.BlueFire.cs`), campfire as a cooking heat source 0xDE3-0xDE9, range 1 (`CookableFood.cs:100-130`).
- Tracking: window, 12 nearest, range 10 + 10 per 10, twice-range loss, right-click stop (ClassicUO `QuestArrowGump.cs:180`), first check 0..21.1, passive 21.1..100, hidden staff excluded (`Tracking.cs`).
- Herding: targets within 10, 1-15 tile rule (`BaseAI.cs:672`), check M-30 .. M+30..39, the 8 training windows recomputed from `MinTameSkill`.
- Taming: 2-tile target, 6-tile stay, 9 or 12 s, roll window M-0.1 .. M+49.9 (so 5 / 25 / 50 above = 20% / 50% / 100%), 6 per owner, 5 owners, anger 95% for Dragon/WhiteWyrm/Nightmare, control chance formula, loyalty -10 per hour even offline (auto-stable is Core.SE only), food coin flips, stable 30 gold and limits, speech orders, release, fight modes (Aggressor vs default Closest) for every animal named.
- Veterinary: range 1, 3/4/5 s, slip 2% / 4 hp, chance (V+10)%, heal formula and the 23-45 / 43-80 examples, cure formula and levels, no dead pets without bonding.
- ClassicUO: single click opens the context menu (`DelayedObjectClickManager.cs:36-46`), skills window use button exists for clickable skills (`StandardSkillsGump.cs:794`); `UOData/skills.mul` marks Tracking, Animal Lore and Animal Taming clickable and Mining, Lumberjacking, Fishing, Camping, Herding, Veterinary not, matching the pages.

## OWNER:

- OWNER: Hatchet and the other axes never wear out when chopping (`BaseAxe` does not implement `IUsesRemaining`) while Pickaxe, Shovel, bardiche and halberd do. The page now says only that the polearms wear out and is silent about axes. Fork inconsistency or intended?
- OWNER: The Welcome "Camp travel" page and the travel confirmation window (`CampTravelService.cs:129,1211`) say "Bonded pets next to you come with you", but `taming.enableBonding` is False so no pet is ever bonded and none moves. The Camping page says only what the code does. Correct the Welcome text or change the rule.
- OWNER: No Shovel is for sale anywhere (only the unspawned Miner, Tinker, Vagabond and Golem Crafter stock one), and a treasure-map chest needs a Shovel (a Pickaxe does not count), so only Tinkering 40+ can supply one. Intended? (The Welcome Ward page's "Tinker vendors sell them" has the same cause for the Ward: no Tinker NPC spawns in Britain.)
- OWNER: Animal Lore on wild creatures that cannot be tamed needs 110 but a skill caps at 100 here, so it is unreachable (SK-011 "provisionally keep stock"). The page states the rule and the cap.
- OWNER: Deep-sea prizes (big fish, Special Fishing Net, treasure map, message in a bottle) are coded and live because the catch table stays stock (SK-008); the Fishing page advertises them in "Deep water". Remove that section if you would rather not advertise them.
- OWNER: Pets lose 10 loyalty an hour while their owner is logged out (auto-stable on logout is Core.SE only); a pet left out 10 hours goes wild. The Taming page says so and points at the stable.
- OWNER: The stable's own message promises the pet is sold after one real week, but nothing enforces it; the page does not mention it.
- OWNER: Sand and stone mining are unreachable (their books are sold only by the unspawned Glassblower and StoneCrafter); left out of the Mining page.
- OWNER: The Welcome "Training" page lists trainer types that do not spawn in Britain (Miner, Ranger, Tinker, Veterinarian, ...), while guildmasters, who do spawn and do teach, are not named. The Skill Guide pages name only spawned NPCs.

## Could not check

- Live behaviour of anything (no server or client was run): trainers, vendor stock rolls and every message are read from code.
- Whether colored ore (Dull Copper to Valorite) was in UOR by April 2000: the code does not gate it, the spec and `Beta-2a-Mastery-Audit.md` treat it as UOR, and an owner note finds it in the game by August 2000. Left as written.
- Taming list is not complete (Frost Spider 74.7, Giant Toad 77.1, Frenzied Ostard 77.1, Lava Lizard 80.7, Imp 83.1, Hell Hound 85.5, Strong Mongbat 71.1 are tameable and spawn); the header now says "most of".
- Hot Zone wording and the harvest-repeat paragraphs were checked against the Welcome guide text and `HarvestRepeatService.cs`/`ActionRepeatService.cs`, not re-derived.
- Camp travel refusals for "a dungeon" also cover the other places Recall cannot be used from or to (Khaldun, Felucca T2A lands, wind, etc., `SpellHelper.cs:107-130`); the page keeps the shorter Welcome wording.
