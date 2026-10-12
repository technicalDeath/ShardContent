# Resources and consumables (area R): notes for the audit

Topics: 31. Assigned classes: 376. Covered by my topics: 230. Covered by the existing Alchemy fallbacks: 45. Left to the general page: 101.

Claim format: topic | claim | file:line (UOC = ModernUO/Projects/UOContent, SC = ShardContent/src/BritanniaRenaissance.Content). Vendor lines are the stock SBInfo lists; a vendor type is mentioned only when it is spawned in `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns` (Vendors.json, TownsPeople.json).

## OPEN

- OPEN: Colored hides and leather (SpinedHides/HornedHides/BarbedHides and the leathers): DefTailoring lists them (Tailoring 65/80/99) and BaseArmor.ArmorRating gives +10/+13/+16 from UOR on, and spined/horned/barbed creatures are spawned (Lizardman, Ratman, Drake, Wyvern, Dragon, wyrms), but the T2A tailoring menu only accepts exactly Leather or Hides as a target (TailoringMenu.cs TrySelectResource: 'That is not a valid resource') and never selects a sub-resource, so colored leather cannot be used or sold (vendors buy exact types only). The Hides and Leather topics say the tailor's menu takes only plain hides and leather. Owner: is that intended?
- OPEN: Dragon scales (BaseScales family): carved from dragons, drakes' kin and sea serpents, but the only use is DefBlacksmithy dragon armor, which BlacksmithMenu (T2A) does not offer; no vendor buys scales. Left to the general page. The generated craft:Blacksmithing table (HelpGenerators, filtered by expansion only) will list Dragon armor recipes the menu cannot make.
- OPEN: Bone armor: DefTailoring has Bone armor and Orc helm, but TailoringMenu (T2A) offers only Shoes, Leather, Studded and Female armor, and no vendor buys bones. Bone/BonePile/RibCage left to the general page. The generated craft:Tailoring table will list bone armor.
- OPEN: Generated craft tables vs T2A menus: HelpGenerators.CraftTable lists every DefXxx recipe whose RequiredExpansion is not later than UOR, but players craft through the T2A menus (t2aCraftMenus is on: ExpansionConfiguration.cs, not overridden in Distribution/Configuration). Recipes the menus never offer (dragon armor, bone armor, colored leather armor, the Tinkering 'assembly' ClockParts/SextantParts recipes that SearchFor shadows, Cooking, and more) would appear on the skill pages. Skill writers and the coordinator should know.
- OPEN: Cooking: only 'raw food on a heat source' works (CookableFood.cs, Cooking-Era-Restore-Readiness.md). The unbaked pies/pizzas/mixes (UnbakedApplePie ..., CookieMix, CakeMix, Dough) are in the Raw food and Flour topics only as part of the family; I wrote that the baking recipes 'are not in the game yet'. That sentence is time-sensitive: drop it when Part B (flour, water, dough) ships.
- OPEN: Aquarium: SBFisherman (the Fisherman is spawned in Britain) sells AquariumFishNet (250), FishBowl, AquariumFood, VacationWafer and aquarium deeds with no era gate, and the net catches BaseFish creatures. The aquarium is post-UOR. I wrote nothing about it and left all BaseFish/aquarium classes to the general page. Owner: remove it from the vendor or keep it?
- OPEN: SBProvisioner (spawned in Britain) sells PlantBowl (Plant system, post-UOR) and OilFlask 9 gold (its only use, refilling a Lantern, does nothing because Lantern/BaseLight.Burnout is false). Not in my classes beyond OilFlask; not described.
- OPEN: ClockworkAssembly (15 percent drop of Golem, which spawns in the Wrong dungeon) lets a player with Tinkering 60 build a controlled Golem pet from a Power Crystal, 5 gears and 50 bronze and 50 iron ingots (ClockworkAssembly.cs, no era gate). That is a post-UOR feature; left to the general page.
- OPEN: Springs and Hinge have no use in any recipe the T2A tinker menu offers (they appear only in the assembly recipes for ClockParts and SextantParts, which CraftItemCollection.SearchFor shadows with the ingot recipes, and in faction traps). The Tinker parts topic gives no use for them.
- OPEN: Vendor types that are coded but not spawned in this world (Vendors.json holds only Britain): Tinker, Miner, Farmer, Rancher, Ranger, Vagabond, Beekeeper, Miller, Glassblower, StoneCrafter, LeatherWorker. So no one sells ore, tinker parts, hay, glass or the stone and sand books; my topics name only vendors that are spawned.
- OPEN: Granite and sand: Mining returns granite only when Mining base is 100, the Stone Mining book was read and the toggle is on (Mining.cs GetResourceType), and sand likewise with the Sand Mining book; both books are sold only by the StoneCrafter and Glassblower, who are not spawned. All nine granite classes and Sand are left to the general page.
- OPEN: Flax, lettuce and pumpkin plants (FarmableFlax, FarmableLettuce, FarmablePumpkin) are not in any Alpha2b spawn file; only wheat, cotton, cabbage, carrot, onion and turnip plants are. The Crops topic lists only those; flax is sold only by tailors (about 100 gold).
- OPEN: Eggs: nothing in Britain sells Eggs (only SBFarmer, not spawned; bakers buy them) and no spawned creature drops them (Yamandon is SE). Eggs are described only in the Raw food family text. Chickens give feathers and raw birds, not eggs.
- OPEN: Head bounty text: the guard takes a head only when PlayerMurderSystem.BountiesEnabled (murderSystem.bountiesEnabled defaults to !Core.LBR, not overridden here). The root README and WelcomeGuide.cs both already say guards pay bounties for a murderer's head, so I described it.
- OPEN: Magic fish chance: PrizedFish, WondrousFish, TrulyRareFish and PeculiarFish are picked by the Fishing MutateType table at (125 minus skill) divided by 2500 of the catches that already succeeded (5 percent at skill 0, 1 percent at 100). I wrote only 'a rare catch'; the number is in the claim lines if the coordinator wants it.
- OPEN: Carving a human corpse in Felucca: Corpse.Carve blocks carving only on maps with HarmfulRestrictions (not Felucca), so carving another player's innocent corpse is allowed and costs 70 karma plus a criminal flag. The Body parts topic states the karma. Intended for this safe-world shard?
- OPEN: Tailor vendors sell Cotton and Flax for 102 gold each but a bolt of cloth only 100, although one cotton spins to 6 spools (more than a bolt's 5). That is stock SBTailor; the topics quote it.

## Coordinator decisions

- Fallbacks: I used inherits for Food, BaseBeverage, CookableFood, BaseOre, BaseIngot, Log, Board, BaseHides, BaseLeather, BaseClothMaterial, Wool, BaseMagicFish and FarmableCrop. Because Food and CookableFood are fallbacks, the holiday candy, the Asian-cooking foods, the Halloween foods and the unbaked items (not in this world) show the generic Food or Raw food text. BaseFish, BaseGranite and BaseScales have no fallback by design (see OPEN); say if you want one.
- The Hides and Leather topics state that the tailor's menu takes only plain leather and hides, and the Flour topic states that baking recipes are not in the game yet. Both come straight from the code and the Cooking docs, but they read like complaints about the shard: keep, soften or drop.
- Gold: the Gold topic explains the banker words (bank, balance, withdraw, check). The root README or the Welcome guide may already cover the bank; delete the topic if you prefer one place.
- Topics with no skill link (Body parts, Gold) have no left-hand buttons; that is allowed (links optional).
- I did not use the 'requires' gate for anything but CampingFires, CampingStarterKit, CampingTravel and ActionAutoRepeat (all four are on in shard-rules.json). HarvestAutoRepeat is not mentioned in the item topics (gathering repeat belongs on the Mining, Lumberjacking and Fishing pages).
- Prices in the topics are the stock SBInfo base prices ('about N gold'); the vendor price scalar is 100 (no town tax) so they hold. They would drift if the owner re-prices vendors.

## Claims

### r-ore (Ore)

- r-ore | eight rare ores exist in the mining table (dull copper..valorite), ReqSkill 65/70/75/80/85/90/95/99 | UOC/Engines/Harvest/Mining.cs:121
- r-ore | ReqSkill 65 dull copper | UOC/Engines/Harvest/Mining.cs:117
- r-ore | ReqSkill 99 valorite | UOC/Engines/Harvest/Mining.cs:180
- r-ore | patch size 8x8 tiles | UOC/Engines/Harvest/Mining.cs:86
- r-ore | a patch holds 10 to 34 (MinTotal 10, MaxTotal 34) | UOC/Engines/Harvest/Mining.cs:89
- r-ore | respawn 10 to 20 minutes (MinRespawn 10, MaxRespawn 20) | UOC/Engines/Harvest/Mining.cs:90
- r-ore | respawn timer starts at the first harvest of a full bank | UOC/Engines/Harvest/Core/HarvestBank.cs:54
- r-ore | one piece per good dig: ConsumedPerHarvest 1 | UOC/Engines/Harvest/Mining.cs:97
- r-ore | Felucca double yield needs Core.AOS (off); racial bonus needs RaceBonus = Core.ML (off): single yield | UOC/Engines/Harvest/Core/HarvestSystem.cs:193
- r-ore | the patch's vein is fixed by position when RandomizeVeins (Core.ML) is off | UOC/Engines/Harvest/Core/HarvestDefinition.cs:142
- r-ore | rare veins fall back to iron half the time (ChanceToFallback 0.5) | UOC/Engines/Harvest/Mining.cs:193
- r-ore | below the metal's ReqSkill the fallback (iron) is chosen | UOC/Engines/Harvest/Core/HarvestSystem.cs:366
- r-ore | you need base Mining >= ReqSkill to dig the rare metal | UOC/Engines/Harvest/Core/HarvestSystem.cs:163
- r-ore | cannot mine while riding | UOC/Engines/Harvest/Mining.cs:302
- r-ore | pickaxe or shovel starts the mining (BaseHarvestTool double-click begins harvesting) | UOC/Items/Skill Items/Harvest Tools/BaseHarvestTool.cs:120
- r-ore | ore must be within 2 tiles to be used; target is a forge or another pile | UOC/Items/Resources/Blacksmithing/Ore.cs:107
- r-ore | forge = ForgeAttribute type or item id 4017 / 6522-6569 / 11736 (small and large forges) | UOC/Items/Resources/Blacksmithing/Ore.cs:144
- r-ore | smelting difficulty 50 iron, 65..99 rare; minSkill = difficulty-25, maxSkill = difficulty+25 | UOC/Items/Resources/Blacksmithing/Ore.cs:181
- r-ore | a rare ore refuses to smelt when Mining is below its difficulty | UOC/Items/Resources/Blacksmithing/Ore.cs:184
- r-ore | CheckTargetSkill: below minSkill always fails; at or above maxSkill always succeeds; else (value-min)/(max-min) | UOC/Skills/SkillCheck.cs:67
- r-ore | the whole stack is smelted at once on success (toConsume = Amount) | UOC/Items/Resources/Blacksmithing/Ore.cs:199
- r-ore | a miss halves the pile | UOC/Items/Resources/Blacksmithing/Ore.cs:251
- r-ore | big pile (0x19B9) makes 2 ingots each | UOC/Items/Resources/Blacksmithing/Ore.cs:226
- r-ore | small pile (0x19B7) makes 1 ingot per 2 piles | UOC/Items/Resources/Blacksmithing/Ore.cs:217
- r-ore | medium piles make 1 ingot each | UOC/Items/Resources/Blacksmithing/Ore.cs:230
- r-ore | size of a new piece: 12.5% small, 12.5% medium, 75% big (RandomSize) | UOC/Items/Resources/Blacksmithing/Ore.cs:55
- r-ore | pile weights 2 / 7 / 12 stones: Item.DefaultWeight reads the TileData weight; tiledata.mul parsed: 0x19B7=2, 0x19B8=7, 0x19BA=7, 0x19B9=12 (BaseOre has no weight override) | ModernUO/Projects/Server/Items/Item.cs:504
- r-ore | the server reads tiledata.mul from the UOData directory | ModernUO/Distribution/Configuration/modernuo.json:6
- r-ore | ingot weight 0.1 | UOC/Items/Resources/Blacksmithing/Ingots.cs:17

### r-ingots (Ingots)

- r-ingots | ingots stack and weigh 0.1 | UOC/Items/Resources/Blacksmithing/Ingots.cs:17
- r-ingots | ingot stackable | UOC/Items/Resources/Blacksmithing/Ingots.cs:10
- r-ingots | double-click a craft tool then target a resource: 'Target this tool to make last item, or any other target to begin crafting.' | UOC/Items/Skill Items/Tools/BaseTool.cs:165
- r-ingots | blacksmith: targeting an ingot of the sub-resource list selects it and opens the menu (TrySelectResource) | UOC/Engines/Craft/T2A/BlacksmithMenu.cs:574
- r-ingots | tinkering accepts a BaseIngot target (or wood) as the material | UOC/Engines/Craft/T2A/TinkeringMenu.cs:429
- r-ingots | Blacksmithing needs anvil and forge within 2 tiles (CheckAnvilAndForge(from, 2,...), message 1044267 'You must be near an anvil and a forge to smith items.') | UOC/Engines/Craft/DefBlacksmithy.cs:110
- r-ingots | the anvil/forge need is dropped only from Core.SE on; here it applies | UOC/Items/Skill Items/Tools/BaseTool.cs:158
- r-ingots | Blacksmith sub-resource skill numbers 65/70/75/80/85/90/95/99 | UOC/Engines/Craft/DefBlacksmithy.cs:688
- r-ingots | Blacksmith valorite 99 | UOC/Engines/Craft/DefBlacksmithy.cs:695
- r-ingots | Tinkering uses the same sub-resource numbers | UOC/Engines/Craft/DefTinkering.cs:590
- r-ingots | a craft is refused when the crafter's base main skill is below the sub-resource's RequiredSkill | UOC/Engines/Craft/Core/CraftItem.cs:630
- r-ingots | armor rating bonus +2 dull copper .. +16 valorite, applied from UOR on (Core.UOR) | UOC/Items/Armor/BaseArmor.cs:310
- r-ingots | armor rating bonus gated by Core.UOR | UOC/Items/Armor/BaseArmor.cs:305
- r-ingots | valorite +16 | UOC/Items/Armor/BaseArmor.cs:317
- r-ingots | the smith's menu starts with Repair and Smelt | UOC/Engines/Craft/T2A/BlacksmithMenu.cs:215
- r-ingots | Smelt runs Resmelt.Do | UOC/Engines/Craft/T2A/BlacksmithMenu.cs:434
- r-ingots | a player-made weapon or armor returns Amount/2 ingots; otherwise 1 ingot | UOC/Engines/Craft/Core/Resmelt.cs:102
- r-ingots | rare metals need Mining skill at least equal to the metal's number to resmelt (NoSkill) | UOC/Engines/Craft/Core/Resmelt.cs:90
- r-ingots | Blacksmith NPC sells iron ingots at 5, stock 16 | UOC/Mobiles/Vendors/SBInfo/SBBlacksmith.cs:16
- r-ingots | Blacksmith NPC buys iron ingots at 4 | UOC/Mobiles/Vendors/SBInfo/SBBlacksmith.cs:119
- r-ingots | Blacksmith NPCs are spawned in Britain (2 spawners) | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:49

### r-logs (Logs)

- r-logs | log weight 2.0, stackable | UOC/Items/Skill Items/Lumberjack/Log.cs:29
- r-logs | axe must be equipped: message 500487 | UOC/Engines/Harvest/Lumberjacking.cs:134
- r-logs | 10 logs per chop (ConsumedPerHarvest 10); Felucca double needs Core.AOS | UOC/Engines/Harvest/Lumberjacking.cs:53
- r-logs | grove holds 20 to 45 wood, bank 4x3 | UOC/Engines/Harvest/Lumberjacking.cs:46
- r-logs | respawn 20 to 30 minutes | UOC/Engines/Harvest/Lumberjacking.cs:47
- r-logs | chance = skill percent: log row ReqSkill 0, MinSkill 0, MaxSkill 100 (non-ML branch) | UOC/Engines/Harvest/Lumberjacking.cs:105
- r-logs | only plain Log below Core.ML (special woods are in the Core.ML branch) | UOC/Engines/Harvest/Lumberjacking.cs:67
- r-logs | knife/sword on a tree cuts Kindling (5 wood from the bank) | UOC/Targets/BladedItemTarget.cs:99
- r-logs | Carpenter NPC buys Log at 1 | UOC/Mobiles/Vendors/SBInfo/SBCarpenter.cs:81
- r-logs | a recipe asking for Log takes Board too (types table) | UOC/Engines/Craft/Core/CraftItem.cs:70
- r-logs | T2A carpentry: target Log or Board | UOC/Engines/Craft/T2A/T2ACraftSystem.cs:66
- r-logs | T2A fletching: target Log, Board, Feather or Shaft | UOC/Engines/Craft/T2A/T2ACraftSystem.cs:54
- r-logs | T2A tinkering: wood category accepts Log or Board target | UOC/Engines/Craft/T2A/TinkeringMenu.cs:416
- r-logs | axe on logs: Log.Axe makes boards 1 per log (ScissorHelper amount 1) for the whole stack | UOC/Items/Skill Items/Lumberjack/Log.cs:41
- r-logs | HarvestTarget: the logs must be in your pack (1062334) | UOC/Engines/Harvest/Core/HarvestTarget.cs:62
- r-logs | board weight 1 (tiledata 0x1BD7 raw weight 1; Board has no override) | UOC/Items/Skill Items/Carpenter Items/Board.cs:7

### r-boards (Boards)

- r-boards | board weight 1 vs log 2 | UOC/Items/Skill Items/Carpenter Items/Board.cs:7
- r-boards | Carpenter NPC sells Board at 3 | UOC/Mobiles/Vendors/SBInfo/SBCarpenter.cs:18
- r-boards | Carpenter NPC buys Board at 2 | UOC/Mobiles/Vendors/SBInfo/SBCarpenter.cs:71
- r-boards | Carpenter NPC spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:893

### r-kindling (Kindling)

- r-kindling | kindling weight 5.0, stackable | UOC/Items/Skill Items/Camping/Kindling.cs:38
- r-kindling | double-click lights a campfire; Camping skill roll CheckSkill(Camping,0,100) by default | UOC/Items/Skill Items/Camping/Kindling.cs:104
- r-kindling | no campfire in a DungeonRegion ('There is not a spot nearby to place your campfire.') | UOC/Items/Skill Items/Camping/Kindling.cs:118
- r-kindling | campfire graphics 0xDE3-0xDE9 are a cooking heat source | UOC/Items/Food/CookableFood.cs:133
- r-kindling | flag CampingFires: ignite chance = max(Camping, 50)/100 | SC/CampingService.cs:46
- r-kindling | config skillFloor 50, lit 100 s + 2 s/point | ShardContent/data/configuration/shard-rules.json:42
- r-kindling | embers 60 s + 1.2 s per point | ShardContent/data/configuration/shard-rules.json:46
- r-kindling | burn timing uses the real Camping skill (floor does not apply) | SC/CampingService.cs:58
- r-kindling | feeding: Kindling within one tile of a Campfire resets the burn and relights embers, only with CampingFires | SC/CampingService.cs:128
- r-kindling | feed lookup range is 1 tile | UOC/Items/Skill Items/Camping/Kindling.cs:91
- r-kindling | flag CampingStarterKit: Bedroll if none and Kindling up to starterKindling (5) | SC/CampingService.cs:71
- r-kindling | starterKindling 5 | ShardContent/data/configuration/shard-rules.json:48
- r-kindling | camp travel costs 2 Kindling (kindlingCost 2) | ShardContent/data/configuration/shard-rules.json:53
- r-kindling | camp travel refusal 'You need N Kindling in your backpack to travel.' | SC/CampTravelService.cs:294
- r-kindling | Provisioner sells Kindling at 2 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:81
- r-kindling | Provisioner buys Kindling at 1 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:140
- r-kindling | Fletching turns 1 log into Kindling at skill 0 | UOC/Engines/Craft/DefBowFletching.cs:94
- r-kindling | Fletching T2A menu lists Kindling | UOC/Engines/Craft/T2A/BowFletchingMenu.cs:12
- r-kindling | knife/sword on a tree gives Kindling | UOC/Targets/BladedItemTarget.cs:103
- r-kindling | Provisioner NPC spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:758

### r-barrel-parts (Barrel parts)

- r-barrel-parts | Carpentry makes BarrelStaves from logs | UOC/Engines/Craft/DefCarpentry.cs:99
- r-barrel-parts | Carpentry makes BarrelLid from logs | UOC/Engines/Craft/DefCarpentry.cs:100
- r-barrel-parts | Keg from BarrelStaves + BarrelHoops + BarrelLid | UOC/Engines/Craft/DefCarpentry.cs:253
- r-barrel-parts | T2A carpentry menu offers Keg, BarrelStaves, BarrelLid | UOC/Engines/Craft/T2A/CarpentryMenu.cs:49
- r-barrel-parts | Tinkering makes BarrelHoops and BarrelTap from iron ingots | UOC/Engines/Craft/DefTinkering.cs:272
- r-barrel-parts | T2A tinkering parts list has BarrelTap, BarrelHoops | UOC/Engines/Craft/T2A/TinkeringMenu.cs:47
- r-barrel-parts | PotionKeg = Keg + 10 Bottle + BarrelLid + BarrelTap | UOC/Engines/Craft/DefTinkering.cs:425
- r-barrel-parts | weights staves 1, lid 2, hoops 5, tap 1 | UOC/Items/Construction/Misc/BarrelParts.cs:36

### r-hides (Hides)

- r-hides | hide weight 5.0 | UOC/Items/Resources/Tailor/Hides.cs:16
- r-hides | knife (BaseKnife) double-click raises BladedItemTarget | UOC/Items/Weapons/Knives/BaseKnife.cs:24
- r-hides | sword (BaseSword) double-click raises BladedItemTarget | UOC/Items/Weapons/Swords/BaseSword.cs:21
- r-hides | BladedItemTarget carves an ICarvable (a Corpse) | UOC/Targets/BladedItemTarget.cs:36
- r-hides | an axe on an ICarvable carves it (Lumberjacking target) | UOC/Engines/Harvest/Core/HarvestTarget.cs:71
- r-hides | plain hides are dropped on the corpse (no SkinningKnife leather path before AOS): 'You skin it, and the hides are now in the corpse.' | UOC/Mobiles/BaseCreature.cs:2109
- r-hides | leather-in-pack path is Core.AOS + SkinningKnife only (off here) | UOC/Mobiles/BaseCreature.cs:2079
- r-hides | hides, feathers and wool x2 when the corpse is in Felucca (meat and scales only with Core.ML) | UOC/Mobiles/BaseCreature.cs:2034
- r-hides | Furtrader sells Hides at 3 (40 in stock) | UOC/Mobiles/Vendors/SBInfo/SBFurtrader.cs:16
- r-hides | Furtrader buys Hides at 2 | UOC/Mobiles/Vendors/SBInfo/SBFurtrader.cs:24
- r-hides | Furtrader spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:155
- r-hides | vendors buy only the exact listed type (colored hides are not bought) | UOC/Mobiles/Vendors/GenericSell.cs:163
- r-hides | spined hides: Lizardman 12, Ratman/RatmanArcher/RatmanMage 8, GiantSerpent/IceSerpent/LavaSerpent 15 (all spawned) | UOC/Mobiles/Monsters/Humanoid/Melee/Ratman.cs:47
- r-hides | spined: Lizardman | UOC/Mobiles/Monsters/Reptile/Melee/Lizardman.cs:47
- r-hides | spined: GiantSerpent | UOC/Mobiles/Animals/Reptiles/GiantSerpent.cs:59
- r-hides | horned: Drake | UOC/Mobiles/Monsters/Reptile/Melee/Drake.cs:54
- r-hides | horned: Wyvern | UOC/Mobiles/Monsters/Reptile/Melee/Wyvern.cs:56
- r-hides | barbed: Dragon | UOC/Mobiles/Monsters/Reptile/Magic/Dragon.cs:54
- r-hides | barbed: AncientWyrm / ShadowWyrm / WhiteWyrm (spawned: AncientWyrm, ShadowWyrm, WhiteWyrm in the Alpha2b spawn files) | UOC/Mobiles/Monsters/Reptile/Magic/ShadowWyrm.cs:56
- r-hides | Hides.Scissor makes 1 Leather per hide (ScissorHelper amount 1) | UOC/Items/Resources/Tailor/Hides.cs:103
- r-hides | scissors range 2, item must be movable | UOC/Items/Skill Items/Tailor Items/Misc/Scissors.cs:46
- r-hides | leather weight 1.0 | UOC/Items/Resources/Tailor/Leathers.cs:16
- r-hides | T2A tailoring: leather-or-hides target opens the leather menu (exact Leather or Hides classes only) | UOC/Engines/Craft/T2A/TailoringMenu.cs:337
- r-hides | T2A tailoring: other targets, such as spined hides, get 'That is not a valid resource.' | UOC/Engines/Craft/T2A/TailoringMenu.cs:371
- r-hides | a leather recipe takes Leather or Hides (types table) | UOC/Engines/Craft/Core/CraftItem.cs:77
- r-hides | sewing kit is the tailoring tool (starter scissors/sewing kit issuance) | SC/StarterCraftMaterialIssuance.cs:88

### r-leather (Leather)

- r-leather | leather weight 1.0 | UOC/Items/Resources/Tailor/Leathers.cs:16
- r-leather | leather menu: shoes, leather armor, studded armor, female armor | UOC/Engines/Craft/T2A/TailoringMenu.cs:187
- r-leather | footwear list sandals, shoes, boots, thigh boots | UOC/Engines/Craft/T2A/TailoringMenu.cs:45
- r-leather | T2A tailoring accepts only exact Leather/Hides targets | UOC/Engines/Craft/T2A/TailoringMenu.cs:337
- r-leather | Tanner sells Leather at 6 | UOC/Mobiles/Vendors/SBInfo/SBTanner.cs:42
- r-leather | Tanner buys Leather at 5 | UOC/Mobiles/Vendors/SBInfo/SBTanner.cs:58
- r-leather | Tanner spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:150
- r-leather | Hides.Scissor -> one Leather per hide | UOC/Items/Resources/Tailor/Hides.cs:103

### r-cloth (Cloth)

- r-cloth | cloth weight 0.1, stackable | UOC/Items/Resources/Tailor/Cloth.cs:17
- r-cloth | uncut cloth weight 0.1 | UOC/Items/Resources/Tailor/UncutCloth.cs:17
- r-cloth | T2A tailoring: Cloth or UncutCloth target opens the cloth menu with that hue | UOC/Engines/Craft/T2A/TailoringMenu.cs:324
- r-cloth | menus: hats, shirts, pants, misc (skirt, cloak, robe, dress...) | UOC/Engines/Craft/T2A/TailoringMenu.cs:178
- r-cloth | hats/shirts/pants/misc type lists | UOC/Engines/Craft/T2A/TailoringMenu.cs:39
- r-cloth | Cloth and UncutCloth are interchangeable in recipes (types table) | UOC/Engines/Craft/Core/CraftItem.cs:81
- r-cloth | crafted clothing takes the target cloth's hue (BaseClothing.OnCraft Hue = resHue; hue-aware tailoring craft) | UOC/Items/Clothing/BaseClothing.cs:192
- r-cloth | tailoring carries the targeted cloth hue into the craft | UOC/Engines/Craft/T2A/TailoringMenu.cs:276
- r-cloth | Cloth is IDyable (a dye tub colors it) | UOC/Items/Resources/Tailor/Cloth.cs:8
- r-cloth | dye tub works on any IDyable not worn | UOC/Items/Skill Items/Tailor Items/Dyetubs/DyeTub.cs:113
- r-cloth | Cloth.Scissor makes 1 Bandage per piece | UOC/Items/Resources/Tailor/Cloth.cs:40
- r-cloth | UncutCloth.Scissor makes 1 Bandage per piece | UOC/Items/Resources/Tailor/UncutCloth.cs:40
- r-cloth | Tailor sells Cloth at 2 and UncutCloth at 2 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:52
- r-cloth | Tailor sells UncutCloth at 2 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:53
- r-cloth | Weaver sells UncutCloth at 3 | UOC/Mobiles/Vendors/SBInfo/SBWeaver.cs:19
- r-cloth | Tailor and Weaver spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:469
- r-cloth | bolt scissors -> 50 cloth | UOC/Items/Resources/Tailor/BoltOfCloth.cs:41
- r-cloth | loom turns 5 pieces of thread or yarn into a bolt | UOC/Items/Resources/Tailor/YarnsAndThreads.cs:91

### r-bolt (Bolt of cloth)

- r-bolt | bolt weight 5.0 | UOC/Items/Resources/Tailor/BoltOfCloth.cs:17
- r-bolt | Scissor on a bolt makes 50 Cloth | UOC/Items/Resources/Tailor/BoltOfCloth.cs:41
- r-bolt | ScissorHelper carries the hue by default | ModernUO/Projects/Server/Items/Item.cs:4371
- r-bolt | BoltOfCloth is IDyable | UOC/Items/Resources/Tailor/BoltOfCloth.cs:8
- r-bolt | Tailor sells BoltOfCloth at 100 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:50
- r-bolt | Tailor buys BoltOfCloth at 50 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:71
- r-bolt | Weaver sells BoltOfCloth at 100 and buys at 50 | UOC/Mobiles/Vendors/SBInfo/SBWeaver.cs:24
- r-bolt | loom makes a BoltOfCloth after 5 pieces | UOC/Items/Resources/Tailor/YarnsAndThreads.cs:99

### r-cotton (Cotton and flax)

- r-cotton | Cotton weight 4.0, Flax weight 1 | UOC/Items/Resources/Tailor/Cotton.cs:16
- r-cotton | Flax weight 1 | UOC/Items/Resources/Tailor/Flax.cs:17
- r-cotton | cotton must be in the pack; target a spinning wheel within WheelRange 3 | UOC/Items/Resources/Tailor/Cotton.cs:54
- r-cotton | a spin makes 6 spools of thread (cotton) | UOC/Items/Resources/Tailor/Cotton.cs:45
- r-cotton | a spin makes 6 spools of thread (flax) | UOC/Items/Resources/Tailor/Flax.cs:45
- r-cotton | spinning takes 3 seconds | UOC/Items/Addons/SpinningWheelEastAddon.cs:85
- r-cotton | spinning wheels in Britain's tailor shops: SpinningWheel addons at (1473,1689), (1390,1604), (1545,1656) beside the Tailor/Weaver spawners at (1467,1686), (1388,1588), (1547,1659); looms at (1392,1601), (1545,1660) | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia__britain.cfg:1440
- r-cotton | loom addon in the same shops | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia__britain.cfg:1453
- r-cotton | flag ActionAutoRepeat: spinning repeats while material is left (SpinningContinues) | SC/ActionRepeatService.cs:77
- r-cotton | repeat cancels on any step, casting, another skill, war mode, fighting/hurt, cursor (shared cancel code) | ShardContent/docs/Action-AutoRepeat-Evidence.md:21
- r-cotton | farm plants: double-click within 2 tiles, produce is created at the plant's spot | UOC/Items/Farming/FarmableCrop.cs:43
- r-cotton | FarmableCotton gives Cotton | UOC/Items/Farming/FarmableCotton.cs:15
- r-cotton | cotton fields are spawned (FarmableCotton in FelCropsLS.json); FarmableFlax is not in any spawn file | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/FelCropsLS.json:149
- r-cotton | Tailor sells Cotton 102 and Flax 102, buys at 51 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:55
- r-cotton | Tailor sells Flax at 102 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:57
- r-cotton | Tailor buys Cotton at 51 and Flax at 51 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:110

### r-wool (Wool)

- r-wool | Wool weight 4.0, TaintedWool 4.0 | UOC/Items/Resources/Tailor/Wool.cs:16
- r-wool | spun wool gives 3 yarn | UOC/Items/Resources/Tailor/Wool.cs:45
- r-wool | spun tainted wool gives 1 yarn | UOC/Items/Resources/Tailor/Wool.cs:134
- r-wool | wheel range 3 | UOC/Items/Resources/Tailor/Wool.cs:54
- r-wool | shearing a living sheep with a blade: ICarvable, 2 wool in Felucca, next wool in 3 hours | UOC/Mobiles/Animals/Misc/Sheep.cs:82
- r-wool | sheep regrow after 3 hours | UOC/Mobiles/Animals/Misc/Sheep.cs:84
- r-wool | dead sheep: wool 3 doubled in Felucca (6) carved as TaintedWool on the corpse | UOC/Mobiles/BaseCreature.cs:2053
- r-wool | sheep are spawned (TownsLife, WildLife, Outdoors, FelCropsLS) | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/WildLife.json:50
- r-wool | Tailor sells Wool at 62, buys at 31 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:56
- r-wool | Tailor buys Wool at 31 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:111
- r-wool | flag ActionAutoRepeat spins a stack through (Wool SpinOn) | SC/ActionRepeatService.cs:207

### r-thread (Thread and yarn)

- r-thread | BaseClothMaterial weight 1.0, stackable, dyeable | UOC/Items/Resources/Tailor/YarnsAndThreads.cs:15
- r-thread | target a loom within 3 (PickLoomTarget range 3) | UOC/Items/Resources/Tailor/YarnsAndThreads.cs:49
- r-thread | each piece advances the loom; the fifth makes a bolt with the material's hue | UOC/Items/Resources/Tailor/YarnsAndThreads.cs:99
- r-thread | Tailor sells SpoolOfThread at 18, buys at 9 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:58
- r-thread | Tailor buys SpoolOfThread at 9 | UOC/Mobiles/Vendors/SBInfo/SBTailor.cs:107
- r-thread | Weaver sells DarkYarn/LightYarn/LightYarnUnraveled at 18 | UOC/Mobiles/Vendors/SBInfo/SBWeaver.cs:29
- r-thread | Weaver buys the yarns at 9 | UOC/Mobiles/Vendors/SBInfo/SBWeaver.cs:48
- r-thread | looms at (1392,1601) and (1545,1660) in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia__britain.cfg:1457
- r-thread | flag ActionAutoRepeat: FeedAmount feeds the whole stack in one use | SC/ActionRepeatService.cs:64

### r-feather (Feathers, shafts)

- r-feather | Feather weight 0.1; Shaft weight 0.1 | UOC/Items/Resources/Arrows/Feather.cs:15
- r-feather | Shaft weight 0.1 | UOC/Items/Resources/Arrows/Shaft.cs:15
- r-feather | Arrow = 1 shaft + 1 feather | UOC/Engines/Craft/DefBowFletching.cs:100
- r-feather | Bolt = 1 shaft + 1 feather | UOC/Engines/Craft/DefBowFletching.cs:104
- r-feather | Shaft is cut from a log (Fletching 0 to 40) | UOC/Engines/Craft/DefBowFletching.cs:96
- r-feather | T2A fletching menu: Kindling, Shafts, Arrows, Bolts, bows | UOC/Engines/Craft/T2A/BowFletchingMenu.cs:12
- r-feather | T2A fletching: target Log, Board, Feather or Shaft | UOC/Engines/Craft/T2A/T2ACraftSystem.cs:61
- r-feather | feathers doubled in Felucca; the corpse gets them | UOC/Mobiles/BaseCreature.cs:2032
- r-feather | Chicken 25 feathers | UOC/Mobiles/Animals/Birds/Chicken.cs:49
- r-feather | Bird 25 feathers | UOC/Mobiles/Animals/Town Critters/Bird.cs:58
- r-feather | Eagle 36 feathers | UOC/Mobiles/Animals/Birds/Eagle.cs:50
- r-feather | Harpy 50 feathers | UOC/Mobiles/Monsters/Reptile/Melee/Harpy.cs:46
- r-feather | Orc may carry shafts (spawned) | UOC/Mobiles/Monsters/Humanoid/Melee/Orc.cs:61
- r-feather | Bowyer sells Feather 2, Shaft 3 (SBRangedWeapon) | UOC/Mobiles/Vendors/SBInfo/Weapons/SBRangedWeapon.cs:27
- r-feather | Bowyer sells Shaft at 3 | UOC/Mobiles/Vendors/SBInfo/Weapons/SBRangedWeapon.cs:28
- r-feather | Bowyer buys Feather and Shaft at 1 | UOC/Mobiles/Vendors/SBInfo/Weapons/SBRangedWeapon.cs:39
- r-feather | Bowyer spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:498

### r-parts (Tinker parts)

- r-parts | Gears/Springs/Hinge/Axle/AxleGears weight 1.0 | UOC/Items/Skill Items/Tinkering/Gears.cs:16
- r-parts | Gears stackable | UOC/Items/Skill Items/Tinkering/Gears.cs:12
- r-parts | Gears from iron ingots (Tinkering 5 to 55) | UOC/Engines/Craft/DefTinkering.cs:270
- r-parts | Springs from iron ingots | UOC/Engines/Craft/DefTinkering.cs:273
- r-parts | Hinge from iron ingots | UOC/Engines/Craft/DefTinkering.cs:276
- r-parts | Axle from logs | UOC/Engines/Craft/DefTinkering.cs:236
- r-parts | AxleGears from an Axle and Gears | UOC/Engines/Craft/DefTinkering.cs:405
- r-parts | T2A tinker menu: Parts category lists Gears, Springs, Hinge, ClockParts, SextantParts, BarrelTap, BarrelHoops, AxleGears | UOC/Engines/Craft/T2A/TinkeringMenu.cs:45
- r-parts | T2A tinker menu: Wood category lists Axle and ClockFrame | UOC/Engines/Craft/T2A/TinkeringMenu.cs:30
- r-parts | Carpenter sells Axle at 2, buys at 1 | UOC/Mobiles/Vendors/SBInfo/SBCarpenter.cs:17
- r-parts | Carpenter buys Axle at 1 | UOC/Mobiles/Vendors/SBInfo/SBCarpenter.cs:72
- r-parts | Golem (non-summoned) carries Gears 25% (Golem spawned in Wrong.json) | UOC/Mobiles/Monsters/Misc/Melee/Golem.cs:80
- r-parts | Golem is spawned | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Wrong.json:224

### r-clock-parts (Clock parts)

- r-clock-parts | ClockParts weight 1, ClockFrame weight 2 | UOC/Items/Skill Items/Tinkering/ClockFrame.cs:16
- r-clock-parts | SextantParts weight 2 | UOC/Items/Skill Items/Tinkering/SextantParts.cs:16
- r-clock-parts | ClockParts weight 1 | UOC/Items/Skill Items/Tinkering/ClockParts.cs:16
- r-clock-parts | ClockParts from iron ingots (first matching recipe, which the menu uses) | UOC/Engines/Craft/DefTinkering.cs:271
- r-clock-parts | SextantParts from iron ingots | UOC/Engines/Craft/DefTinkering.cs:274
- r-clock-parts | ClockFrame from logs | UOC/Engines/Craft/DefTinkering.cs:235
- r-clock-parts | the menu looks a recipe up by SearchFor (first match), so the ingot recipes are the ones offered | UOC/Engines/Craft/Core/CraftCollectionExtensions.cs:42
- r-clock-parts | Clock (ClockRight/ClockLeft) from ClockFrame + ClockParts | UOC/Engines/Craft/DefTinkering.cs:414
- r-clock-parts | Sextant from SextantParts | UOC/Engines/Craft/DefTinkering.cs:420
- r-clock-parts | T2A tinker menu Miscellaneous list has Sextant, ClockRight, ClockLeft | UOC/Engines/Craft/T2A/TinkeringMenu.cs:69

### r-body-parts (Body parts)

- r-body-parts | carving a human corpse leaves Blood, Torso, both legs and arms, Head | UOC/Items/Misc/Corpses/Corpse.cs:441
- r-body-parts | karma -20 for a lawful carve, -70 and a criminal action when IsCriminalAction | UOC/Items/Misc/Corpses/Corpse.cs:466
- r-body-parts | karma -20 | UOC/Items/Misc/Corpses/Corpse.cs:470
- r-body-parts | criminal action = corpse notoriety Innocent and you are not the owner or a looting party member | UOC/Items/Misc/Corpses/Corpse.cs:787
- r-body-parts | head carries the dead player's name and bounty target (PlayerMurderSystem.BountiesEnabled = !Core.LBR) | UOC/Items/Misc/Corpses/Corpse.cs:450
- r-body-parts | bounties are on before LBR | UOC/Engines/Player Murder System/PlayerMurderSystem.cs:54
- r-body-parts | a guard pays the bounty for a head carved within 24 hours, credited to the bank; the head is deleted either way | UOC/Mobiles/Guards/BaseGuard.cs:152
- r-body-parts | bounty credited with Banker.Deposit | UOC/Mobiles/Guards/BaseGuard.cs:175
- r-body-parts | the report gump lets the victim place a bounty paid from the bank | UOC/Engines/Player Murder System/BountyReportMurdererGump.cs:62
- r-body-parts | shard text: a guard pays any bounty posted on a murderer for their head | SC/WelcomeGuide.cs:264
- r-body-parts | Torso weight 2 | UOC/Items/Body Parts/Torso.cs:13

### r-gems (Gems)

- r-gems | gem weight 0.1, stackable | UOC/Items/Gems/Amber.cs:15
- r-gems | the nine gems used in jewelry (GetGemType) | UOC/Items/Jewels/BaseJewel.cs:285
- r-gems | T2A tinkering jewelry: gem chosen by target ('Target the gemstone you wish to use.') | UOC/Engines/Craft/T2A/TinkeringMenu.cs:377
- r-gems | T2A jewelry recipes: gold/silver necklace, earrings, ring, wedding ring (Tinkering 40 to 90) | UOC/Engines/Craft/DefTinkering.cs:396
- r-gems | T2A jewelry branch is the one used when T2ACraftSystem.Enabled | UOC/Engines/Craft/DefTinkering.cs:380
- r-gems | T2ACraftSystem.Enabled defaults on unless UOTD (not set in config) | UOC/Configuration/ExpansionConfiguration.cs:15
- r-gems | gems drop from monsters (LootPack.Gems, e.g. Dragon) | UOC/Mobiles/Monsters/Reptile/Magic/Dragon.cs:67
- r-gems | Loot.GemTypes are exactly these nine | UOC/Misc/Loot.cs:146
- r-gems | Jeweler buys: Amber 25, Amethyst 50, Citrine 25, Diamond 100, Emerald 50, Ruby 37, Sapphire 50, StarSapphire 62, Tourmaline 47 | UOC/Mobiles/Vendors/SBInfo/SBJewel.cs:75
- r-gems | Jeweler buys Diamond 100 | UOC/Mobiles/Vendors/SBInfo/SBJewel.cs:78
- r-gems | Jeweler sells Amber 50 ... Diamond 200 | UOC/Mobiles/Vendors/SBInfo/SBJewel.cs:67
- r-gems | Provisioner buys the same gems at the same prices | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:156
- r-gems | Jeweler and Provisioner spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:78

### r-gold (Gold)

- r-gold | gold weight 0.02 (Core.ML off) | UOC/Items/Misc/Gold.cs:22
- r-gold | gold stackable | UOC/Items/Misc/Gold.cs:18
- r-gold | vendor buy: gold from the pack first; bank only for totals of 2000 or more | UOC/Mobiles/Vendors/BaseVendor.cs:288
- r-gold | AccountGold.Enabled defaults to Core.TOL (off): gold stays an item in the bank box | ModernUO/Projects/Server/IAccount.cs:33
- r-gold | Banker hears speech within 12 tiles | UOC/Mobiles/Townfolk/Banker.cs:454
- r-gold | keyword *bank* opens the bank box | UOC/Mobiles/Townfolk/Banker.cs:534
- r-gold | keyword *balance* | UOC/Mobiles/Townfolk/Banker.cs:509
- r-gold | keyword *withdraw* N, cap 5000 before Core.ML | UOC/Mobiles/Townfolk/Banker.cs:483
- r-gold | keyword *check* N | UOC/Mobiles/Townfolk/Banker.cs:548
- r-gold | criminal refused ('I will not do business with a criminal!' / 'Thou art a criminal and cannot access thy bank box.') | UOC/Mobiles/Townfolk/Banker.cs:540
- r-gold | Banker spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:671

### r-fish (Fish)

- r-fish | Fish weight 1.0, stackable | UOC/Items/Resources/Fishing/Fish.cs:15
- r-fish | carving a Fish makes 4 RawFishSteak per fish | UOC/Items/Resources/Fishing/Fish.cs:19
- r-fish | ScissorHelper consumes the whole stack (amount = Amount) | ModernUO/Projects/Server/Items/Item.cs:4374
- r-fish | knives and swords raise the carving cursor | UOC/Items/Weapons/Knives/BaseKnife.cs:24
- r-fish | BigFish weight random 3 to 200 | UOC/Items/Resources/Fishing/BigFish.cs:18
- r-fish | BigFish carves into max(16, weight)/4 steaks | UOC/Items/Resources/Fishing/BigFish.cs:26
- r-fish | BigFish only from deep water (mutate entry deepWater true), reqSkill 80, chance (skill-80)/4000, Expansion UOR | UOC/Engines/Harvest/Fishing.cs:16
- r-fish | mutation applies only if skill base >= ReqSkill and deep water | UOC/Engines/Harvest/Fishing.cs:182
- r-fish | fishing pole: harvest water; raw fish steak sold by Fisherman at 3, Fish at 6 (80 in stock) | UOC/Mobiles/Vendors/SBInfo/SBFisherman.cs:16
- r-fish | Fisherman sells Fish at 6 | UOC/Mobiles/Vendors/SBInfo/SBFisherman.cs:19
- r-fish | Fisherman buys Fish at 1 and RawFishSteak at 1 | UOC/Mobiles/Vendors/SBInfo/SBFisherman.cs:40
- r-fish | Fisherman spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:218
- r-fish | raw fish steaks cook at a heat source (fire, forge, oven) | UOC/Items/Food/CookableFood.cs:439

### r-magic-fish (Magic fish)

- r-magic-fish | BaseMagicFish weight 1.0 | UOC/Items/Resources/Fishing/MagicFish.cs:15
- r-magic-fish | double-click must be in pack; swallowed whole | UOC/Items/Resources/Fishing/MagicFish.cs:39
- r-magic-fish | stat offset lasts 1 minute | UOC/Items/Resources/Fishing/MagicFish.cs:19
- r-magic-fish | 'You are already under a similar effect.' | UOC/Items/Resources/Fishing/MagicFish.cs:23
- r-magic-fish | PrizedFish +5 Int | UOC/Items/Resources/Fishing/MagicFish.cs:54
- r-magic-fish | WondrousFish +5 Dex | UOC/Items/Resources/Fishing/MagicFish.cs:68
- r-magic-fish | TrulyRareFish +5 Str | UOC/Items/Resources/Fishing/MagicFish.cs:82
- r-magic-fish | PeculiarFish +10 Stam at once | UOC/Items/Resources/Fishing/MagicFish.cs:99
- r-magic-fish | catch chance (125 - skill)/2500 of a successful catch: 5% at 0 down to 1% at 100 (mutate row: ReqSkill 0, MinSkill 125, MaxSkill -2375, Expansion T2A) | UOC/Engines/Harvest/Fishing.cs:22
- r-magic-fish | mutation chance formula (skillValue - MinSkill) / (MaxSkill - MinSkill) | UOC/Engines/Harvest/Fishing.cs:189

### r-food (Food)

- r-food | eating: double-click within 1 tile calls Eat | UOC/Items/Food/Food.cs:46
- r-food | 'Eat' in the item's context menu | UOC/Items/Food/Food.cs:35
- r-food | food stacks (Food base sets Stackable) | UOC/Items/Food/Food.cs:24
- r-food | hunger >= 20: 'You are simply too full to eat any more!' and the food is not consumed | UOC/Items/Food/Food.cs:86
- r-food | hunger = hunger + fill, capped at 20 ('stuffed') | UOC/Items/Food/Food.cs:92
- r-food | stamina gain Random(6,3) + fill/5 when Stam < StamMax | UOC/Items/Food/Food.cs:96
- r-food | new characters start with Hunger 20 | UOC/Engines/Character Creation/CharacterCreation.cs:238
- r-food | hunger drops by 1 every 5 minutes for connected players (NetState.Instances) | UOC/Misc/FoodDecay.cs:35
- r-food | decay timer interval 5 minutes | UOC/Misc/FoodDecay.cs:8
- r-food | nothing else reads Hunger (grep of UOContent, Server and ShardContent: only Food.cs, FoodDecay.cs, CharacterCreation.cs and Mobile.cs storage) | ModernUO/Projects/Server/Mobiles/Mobile.cs:532
- r-food | poisoned food poisons the eater | UOC/Items/Food/Food.cs:72
- r-food | dropping food on a controlled pet feeds it (CheckFeed); only liked food; 'Your pet looks happier.' | UOC/Mobiles/BaseCreature.cs:4591
- r-food | 'The animal shies away.' for food the pet does not like | UOC/Mobiles/BaseCreature.cs:4600
- r-food | 'Your pet looks happier.' when loyalty rises | UOC/Mobiles/BaseCreature.cs:4635

### r-raw-food (Raw food)

- r-raw-food | raw food is an Item with a cook cursor, not Food: double-click then target a heat source | UOC/Items/Food/CookableFood.cs:42
- r-raw-food | heat sources: campfire 0xDE3-0xDE9, sandstone and stone ovens/fireplaces, fire pit, heating stands, fire field, large and small forge | UOC/Items/Food/CookableFood.cs:174
- r-raw-food | fire field graphics | UOC/Items/Food/CookableFood.cs:163
- r-raw-food | target range 1 tile (CookTarget base(1, ...)) | UOC/Items/Food/CookableFood.cs:96
- r-raw-food | food must be within 2 tiles ('I can't reach that.') | UOC/Items/Food/CookableFood.cs:53
- r-raw-food | 5 second cook delay | UOC/Items/Food/CookableFood.cs:10
- r-raw-food | walking more than 3 tiles from the heat source burns the food | UOC/Items/Food/CookableFood.cs:68
- r-raw-food | success chance is CheckSkill(Cooking, 0, 100), usable at skill 0; per-food CookingLevel unused (owner ruling in Cooking-Era-Restore-Readiness.md) | UOC/Items/Food/CookableFood.cs:77
- r-raw-food | second cook during the 5 s: 'You must wait to perform another action.' | UOC/Items/Food/CookableFood.cs:107
- r-raw-food | one item per cook even from a stack (food.Consume()) | UOC/Items/Food/CookableFood.cs:116
- r-raw-food | burn message 500686 | UOC/Items/Food/CookableFood.cs:70
- r-raw-food | no cooking tool: the double-click needs only the food | ShardContent/docs/Cooking-Era-Restore-Readiness.md:6
- r-raw-food | RawRibs cook to Ribs | UOC/Items/Food/CookableFood.cs:190
- r-raw-food | RawLambLeg to LambLeg | UOC/Items/Food/CookableFood.cs:203
- r-raw-food | RawChickenLeg to ChickenLeg | UOC/Items/Food/CookableFood.cs:217
- r-raw-food | RawBird to CookedBird | UOC/Items/Food/CookableFood.cs:232
- r-raw-food | RawFishSteak to FishSteak | UOC/Items/Food/CookableFood.cs:439
- r-raw-food | Eggs to FriedEggs | UOC/Items/Food/CookableFood.cs:368
- r-raw-food | flag ActionAutoRepeat: cooking repeats while food remains (CookingContinues) | SC/ActionRepeatService.cs:79
- r-raw-food | repeat stops on any step, casting, another skill, war mode, fighting/hurt, open cursor | ShardContent/docs/Action-AutoRepeat-Evidence.md:21
- r-raw-food | Butcher sells RawRibs 16, RawLambLeg 9, RawBird 9, RawChickenLeg 6 | UOC/Mobiles/Vendors/SBInfo/SBButcher.cs:22
- r-raw-food | Butcher sells RawLambLeg 9 | UOC/Mobiles/Vendors/SBInfo/SBButcher.cs:21
- r-raw-food | Butcher sells RawBird 9 | UOC/Mobiles/Vendors/SBInfo/SBButcher.cs:20
- r-raw-food | Butcher sells RawChickenLeg 6 | UOC/Mobiles/Vendors/SBInfo/SBButcher.cs:19
- r-raw-food | Fisherman sells RawFishSteak 3 | UOC/Mobiles/Vendors/SBInfo/SBFisherman.cs:16
- r-raw-food | Butcher spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:816
- r-raw-food | carving a corpse leaves raw meat (ribs, birds, lamb legs by MeatType) on the corpse | UOC/Mobiles/BaseCreature.cs:2061

### r-cooked-meat (Cooked meat)

- r-cooked-meat | fill values: Bacon 1 | UOC/Items/Food/Food.cs:146
- r-cooked-meat | Bacon FillFactor 1 (line after ctor) | UOC/Items/Food/Food.cs:148
- r-cooked-meat | SlabOfBacon fill 3 | UOC/Items/Food/Food.cs:158
- r-cooked-meat | FishSteak fill 3 weight 0.1 | UOC/Items/Food/Food.cs:170
- r-cooked-meat | ChickenLeg fill 4 | UOC/Items/Food/Food.cs:454
- r-cooked-meat | Sausage fill 4 | UOC/Items/Food/Food.cs:254
- r-cooked-meat | FriedEggs fill 4 | UOC/Items/Food/Food.cs:218
- r-cooked-meat | Ribs fill 5 | UOC/Items/Food/Food.cs:291
- r-cooked-meat | LambLeg fill 5 weight 2 | UOC/Items/Food/Food.cs:442
- r-cooked-meat | CookedBird fill 5 | UOC/Items/Food/Food.cs:230
- r-cooked-meat | Ham fill 5 | UOC/Items/Food/Food.cs:266
- r-cooked-meat | RoastPig fill 20 weight 45 | UOC/Items/Food/Food.cs:242
- r-cooked-meat | RoastPig weight 45 | UOC/Items/Food/Food.cs:247
- r-cooked-meat | stuffed at 20 | UOC/Items/Food/Food.cs:102
- r-cooked-meat | Provisioner sells LambLeg 8, ChickenLeg 5, CookedBird 17 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:54
- r-cooked-meat | Provisioner CookedBird 17 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:56
- r-cooked-meat | InnKeeper sells Ribs 7, CookedBird 17, LambLeg 8, ChickenLeg 5 | UOC/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:33
- r-cooked-meat | TavernKeeper sells Ribs 7 | UOC/Mobiles/Vendors/SBInfo/SBTavernKeeper.cs:33
- r-cooked-meat | Cook sells RoastPig 106 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:39
- r-cooked-meat | Butcher sells Bacon 7, Sausage 18, Ham 26 | UOC/Mobiles/Vendors/SBInfo/SBButcher.cs:16
- r-cooked-meat | Butcher Sausage 18 | UOC/Mobiles/Vendors/SBInfo/SBButcher.cs:18
- r-cooked-meat | Butcher Ham 26 | UOC/Mobiles/Vendors/SBInfo/SBButcher.cs:17
- r-cooked-meat | Provisioner, InnKeeper, TavernKeeper, Cook spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:324
- r-cooked-meat | Cook spawned | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:334
- r-cooked-meat | InnKeeper spawned | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:551

### r-baked (Bread and pies)

- r-baked | BreadLoaf fill 3 | UOC/Items/Food/Food.cs:134
- r-baked | FrenchBread fill 3 weight 2 | UOC/Items/Food/Food.cs:206
- r-baked | Muffins fill 4 | UOC/Items/Food/Food.cs:316
- r-baked | Cookies fill 4 | UOC/Items/Food/Food.cs:303
- r-baked | Cake fill 10 | UOC/Items/Food/Food.cs:278
- r-baked | CheesePizza fill 6 | UOC/Items/Food/Food.cs:330
- r-baked | ApplePie fill 5 | UOC/Items/Food/Food.cs:400
- r-baked | Baker sells BreadLoaf 6 and 5 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:16
- r-baked | Baker FrenchBread 5, Muffins 3, Cookies 3, ApplePie 7, CheesePizza 8, Cake 13 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:22
- r-baked | Baker Muffins 3 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:20
- r-baked | Baker Cookies 3 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:23
- r-baked | Baker ApplePie 7 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:18
- r-baked | Baker CheesePizza 8 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:24
- r-baked | Baker Cake 13 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:19
- r-baked | Baker buys BreadLoaf 3, Cake 5, Muffins 2, Cookies 3, Pizza 4, ApplePie 5 (a little over half) | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:40
- r-baked | Cook sells BreadLoaf 5, ApplePie 7, Cake 13, Muffins 3 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:18
- r-baked | Provisioner sells BreadLoaf 6; InnKeeper BreadLoaf 6, ApplePie 7 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:53
- r-baked | Baker spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:840

### r-cheese (Cheese)

- r-cheese | CheeseWheel fill 3 weight 0.1 | UOC/Items/Food/Food.cs:179
- r-cheese | CheeseWedge fill 3 | UOC/Items/Food/Food.cs:188
- r-cheese | CheeseSlice fill 1 | UOC/Items/Food/Food.cs:197
- r-cheese | wheel and wedge interchangeable in recipes | UOC/Engines/Craft/Core/CraftItem.cs:82
- r-cheese | Cook sells CheeseWheel 21, buys at 12 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:22
- r-cheese | Cook buys CheeseWheel 12 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:52
- r-cheese | InnKeeper and TavernKeeper sell CheeseWheel 21 | UOC/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:29

### r-fruit-veg (Fruit, vegetables)

- r-fruit-veg | fruit/veg fill 1: Banana | UOC/Items/Food/Fruits.cs:34
- r-fruit-veg | FruitBasket fill 5, leaves a Basket | UOC/Items/Food/Fruits.cs:24
- r-fruit-veg | Watermelon fill 5 weight 5 | UOC/Items/Food/Fruits.cs:203
- r-fruit-veg | SmallWatermelon fill 5 | UOC/Items/Food/Fruits.cs:215
- r-fruit-veg | Pumpkin fill 8 | UOC/Items/Food/Vegetables.cs:50
- r-fruit-veg | SmallPumpkin fill 8 | UOC/Items/Food/Vegetables.cs:59
- r-fruit-veg | Carrot fill 1 | UOC/Items/Food/Vegetables.cs:10
- r-fruit-veg | EarOfCorn fill 1 | UOC/Items/Food/Food.cs:506
- r-fruit-veg | Turnip fill 1 | UOC/Items/Food/Food.cs:518
- r-fruit-veg | InnKeeper sells Peach 3, Pear 3, Grapes 3, Apple 3, Banana 2 | UOC/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:53
- r-fruit-veg | InnKeeper Peach 3 | UOC/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:49
- r-fruit-veg | Provisioner sells Pear 3 and Apple 3 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:63
- r-fruit-veg | crop plants spawned: cabbage, carrot, onion, turnip (FelCropsLS) | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/FelCropsLS.json:127
- r-fruit-veg | FarmableCarrot gives Carrot | UOC/Items/Farming/FarmableCarrot.cs:16
- r-fruit-veg | FarmableCabbage gives Cabbage | UOC/Items/Farming/FarmableCabbage.cs:16
- r-fruit-veg | FarmableOnion gives Onion | UOC/Items/Farming/FarmableOnion.cs:16
- r-fruit-veg | FarmableTurnip gives Turnip | UOC/Items/Farming/FarmableTurnip.cs:16
- r-fruit-veg | InnKeeper spawned | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:551

### r-crops (Crops)

- r-crops | double-click a plant within 2 tiles and in line of sight | UOC/Items/Farming/FarmableCrop.cs:27
- r-crops | the produce is created where the plant stood | UOC/Items/Farming/FarmableCrop.cs:43
- r-crops | the plant is deleted 5 minutes after it is picked | UOC/Items/Farming/FarmableCrop.cs:49
- r-crops | crops are immovable | UOC/Items/Farming/FarmableCrop.cs:12
- r-crops | spawned crop types: wheat, cotton, cabbage, carrot, onion, turnip (spawn files); lettuce, pumpkin and flax plants are not spawned | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/FelCropsLS.json:61
- r-crops | FarmableWheat gives WheatSheaf | UOC/Items/Farming/FarmableWheat.cs:15
- r-crops | fields west of Britain: spawners at x 1120-1232, y 1576-1887 (FelCropsLS.json); other fields near (823,2260), (375,1191), (4567,1475) | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/FelCropsLS.json:29

### r-bowls (Bowls of food)

- r-bowls | Bowl of carrots fill 2, stackable false | UOC/Items/Food/Bowls.cs:34
- r-bowls | wooden bowl food leaves EmptyWoodenBowl | UOC/Items/Food/Bowls.cs:46
- r-bowls | pewter bowl food leaves EmptyPewterBowl | UOC/Items/Food/Bowls.cs:142
- r-bowls | stew and soup leave EmptyWoodenTub | UOC/Items/Food/Bowls.cs:286
- r-bowls | stew weight 2 | UOC/Items/Food/Bowls.cs:252
- r-bowls | Cook sells wooden bowls 3, pewter bowls 3, stew 3, soup 3, empty pewter bowl 2 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:31
- r-bowls | Cook sells WoodenBowlOfStew 3 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:36
- r-bowls | TavernKeeper and InnKeeper sell the same bowls | UOC/Mobiles/Vendors/SBInfo/SBTavernKeeper.cs:40
- r-bowls | buy-back price 1 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:76

### r-drinks (Drinks)

- r-drinks | holds: bottle 5, jug 10, glass mug 5, pitcher 5, mug/goblet 1 | UOC/Items/Food/Beverage.cs:82
- r-drinks | pitcher MaxQuantity 5 | UOC/Items/Food/Beverage.cs:48
- r-drinks | goblet and mugs MaxQuantity 1 | UOC/Items/Food/Beverage.cs:104
- r-drinks | double-click a drink: target yourself to drink (Pour_OnTarget from == targ), Thirst +1, one measure | UOC/Items/Food/Beverage.cs:624
- r-drinks | pouring into another empty container | UOC/Items/Food/Beverage.cs:606
- r-drinks | fill from a water source (water trough), a cow (milk), another drink | UOC/Items/Food/Beverage.cs:536
- r-drinks | water troughs are IWaterSource (decorative troughs stand in Britain) | UOC/Items/Addons/WaterTroughEastAddon.cs:6
- r-drinks | poisoned drink poisons the drinker | UOC/Items/Food/Beverage.cs:651
- r-drinks | drunkenness Ale 1, Wine 2, Cider 3, Liquor 4 (max 60) | UOC/Items/Food/Beverage.cs:638
- r-drinks | drunk: every 5 s lose 1 Stam and 1 Mana, 10% chance to lose 1 BAC, a hic and a stagger | UOC/Items/Food/Beverage.cs:850
- r-drinks | water and milk are not alcohol | UOC/Items/Food/Beverage.cs:322
- r-drinks | Provisioner sells bottles of ale/wine/liquor at 7 and a jug of cider at 13 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:58
- r-drinks | Provisioner Jug cider 13 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:61
- r-drinks | TavernKeeper sells Pitcher milk 7, other pitchers 11 | UOC/Mobiles/Vendors/SBInfo/SBTavernKeeper.cs:21
- r-drinks | TavernKeeper Pitcher ale 11 | UOC/Mobiles/Vendors/SBInfo/SBTavernKeeper.cs:22
- r-drinks | InnKeeper and Waiter sell the same list | UOC/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:26
- r-drinks | Tinkering makes Goblet and PewterMug from iron ingots | UOC/Engines/Craft/DefTinkering.cs:306
- r-drinks | T2A tinker utensil list has Goblet and PewterMug | UOC/Engines/Craft/T2A/TinkeringMenu.cs:56
- r-drinks | Waiter, TavernKeeper, InnKeeper, Provisioner spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:329

### r-flour (Flour and honey)

- r-flour | SackFlour weight 5, 20 uses | UOC/Items/Food/Cooking.cs:77
- r-flour | Baker sells SackFlour 3, JarHoney 3 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:21
- r-flour | Baker sells JarHoney 3 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:25
- r-flour | Baker buys SackFlour 1 and JarHoney 1 | UOC/Mobiles/Vendors/SBInfo/SBBaker.cs:46
- r-flour | Cook sells SackFlour 3 and JarHoney 3 | UOC/Mobiles/Vendors/SBInfo/SBCook.cs:40
- r-flour | wheat sheaves come from wheat plants | UOC/Items/Farming/FarmableWheat.cs:15
- r-flour | Dough and SweetDough are not stackable before ML | UOC/Items/Food/Cooking.cs:13
- r-flour | the only cooking route is raw food on a heat source; the Skillet / Rolling Pin / Flour Sifter menus open nothing and flour/dough preparation is Part B, not built (owner doc) | ShardContent/docs/Cooking-Era-Restore-Research.md:41
- r-flour | T2ACraftSystem.ShowMenu has no Cooking branch | UOC/Engines/Craft/T2A/T2ACraftSystem.cs:104
- r-flour | Baker and Cook spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:840

## Classes left to the general page

- Acid: a creature's acid pool (effect item), not something a player holds
- AgapiteGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- AlbinoCourtesanFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- AlbinoFrog: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- Beads: trade good only: jewelers sell for about 27 and buy for 13, providers buy for 13; no recipe uses it
- Beeswax: trade good only: provisioners and innkeepers sell and buy it for 1 gold; no recipe uses it
- BlackScales: dragon scales have no usable recipe on this shard (dragon armor is not in the T2A blacksmith menu) and no vendor buys them; see OPEN
- Blood: blood left on the ground when a corpse is carved; not carried
- BlueDiamond: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- BlueScales: dragon scales have no usable recipe on this shard (dragon armor is not in the T2A blacksmith menu) and no vendor buys them; see OPEN
- Bone: no reachable recipe (bone armor is not in the T2A tailor menu) and no vendor buys it; see OPEN
- BonePile: decoration bones, no recipe (see Bone)
- BrilliantAmber: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- BrineShrimp: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- BritainCrownFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- BronzeGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- ClockworkAssembly: builds a Golem pet (post-UOR); see OPEN
- Coal: holiday item, not in this world
- CocoaButter: Chocolatiering ingredient of a later cooking set; nothing in this world sells or drops it
- CocoaLiquor: Chocolatiering ingredient of a later cooking set; nothing in this world sells or drops it
- CocoaPulp: Chocolatiering ingredient of a later cooking set; nothing in this world sells or drops it
- CopperGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- CopperWire: decorative rare (wire, forged metal or dried goods) found only in filled crates; no recipe or vendor uses it
- Coral: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- DarkSapphire: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- DemonSkull: champion decoration; champion spawns are not in the Alpha2b world data
- DriedHerbs: decorative rare (wire, forged metal or dried goods) found only in filled crates; no recipe or vendor uses it
- DriedOnions: decorative rare (wire, forged metal or dried goods) found only in filled crates; no recipe or vendor uses it
- DullCopperGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- EcruCitrine: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- EggBomb: later-era Ninjitsu and cooking item, not in this world
- Eggshells: nothing in this world creates it
- EmptyOilFlask: left when an oil flask refuels a lantern; lanterns never burn out here
- EmptyVial: empty glass decoration; Glassblowing is not reachable
- FandancerFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- FertileDirt: Plant system ingredient (post-UOR)
- FireRuby: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- Firebomb: later-era item (oil cloth); not in this world
- ForgedMetal: decorative rare (wire, forged metal or dried goods) found only in filled crates; no recipe or vendor uses it
- FullMoonFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- Glass: empty glass decoration; Glassblowing is not reachable
- GlassBottle: empty glass decoration; Glassblowing is not reachable
- GoldGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- GoldWire: decorative rare (wire, forged metal or dried goods) found only in filled crates; no recipe or vendor uses it
- GoldenBroadtail: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- Granite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- GreenScales: dragon scales have no usable recipe on this shard (dragon armor is not in the T2A blacksmith menu) and no vendor buys them; see OPEN
- HydraScale: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- IronWire: decorative rare (wire, forged metal or dried goods) found only in filled crates; no recipe or vendor uses it
- Jellyfish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- KillerFrog: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- LongClawCrab: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- MakotoCourtesanFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- MeltedWax: immovable decoration (melted wax)
- MinocBlueFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- Muculent: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- NujelmHoneyFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- OilCloth: later-era item, not in this world
- OilFlask: sold by provisioners but its only use, refilling a lantern, does nothing here (lanterns never burn out); see OPEN
- OrangePetals: Plant system resource (post-UOR)
- PerfectEmerald: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- Plate: a tinker's table plate with no use beyond decoration
- PowderOfTemperament: a Bulk Order reward that the shard filters out of the UOR reward pool (Alpha-3-Blacksmith-BOD-Readiness.md, Rewards.cs)
- PowderOfTranslocation: Solen hive item; the Solen hive spawn file is not in the Alpha2b world data
- PurpleFrog: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- RedDartFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- RedLeaves: Plant system resource (post-UOR)
- RedScales: dragon scales have no usable recipe on this shard (dragon armor is not in the T2A blacksmith menu) and no vendor buys them; see OPEN
- RibCage: decoration bones; scissors cut it into bones, which have no use (see Bone)
- SackOfSugar: Chocolatiering ingredient of a later cooking set; nothing in this world sells or drops it
- Sand: needs the Sand Mining book from the Glassblower, who is not spawned
- Scales: a tinker's balance scale with no use beyond decoration
- SeaHorseFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- Seed: Plant system seed (post-UOR)
- ShadowIronGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- SheafOfHay: sold only by farmers and millers, who are not spawned; animal fodder
- Shell: aquarium decoration reward (post-UOR)
- Shrimp: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- Silver: currency of the faction system, used by faction traps; no vendor or recipe a new player meets uses it
- SilverWire: decorative rare (wire, forged metal or dried goods) found only in filled crates; no recipe or vendor uses it
- SmallMouthSuckerFin: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- SmokeBomb: later-era Ninjitsu item, not in this world
- SpeckledCrab: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- SpinedScratcherFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- SpottedBuccaneer: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- StrippedFlakeFish: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- StrippedSosarianSwill: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- TribalBerry: dropped by savages, who are excluded from the spawn data
- Turquoise: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- UnfinishedBarrel: rare decoration, not obtainable
- ValoriteGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- Vanilla: Chocolatiering ingredient of a later cooking set; nothing in this world sells or drops it
- VeriteGranite: not in this world: Mining yields granite only for Mining base 100 with the Stone Mining book read (sold only by the StoneCrafter, who is not spawned)
- VesperReefTiger: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- Vines: dropped by a whipping vine, which is excluded from the spawn data
- Web: champion decoration; champion spawns are not in the Alpha2b world data
- WhitePearl: later-era resource: its source is gated on Core.ML (bonus mining, lumberjacking or fishing drops) or a later monster; not in this world
- WhiteScales: dragon scales have no usable recipe on this shard (dragon armor is not in the T2A blacksmith menu) and no vendor buys them; see OPEN
- WoodDebris: immovable ruined-building debris
- YellowFinBluebelly: aquarium creature (post-UOR); only a Fisherman's aquarium net yields it; see OPEN
- YellowScales: dragon scales have no usable recipe on this shard (dragon armor is not in the T2A blacksmith menu) and no vendor buys them; see OPEN

## Classes covered by the existing Alchemy-chain fallbacks (not mine)

- AgilityPotion: named by the Alchemy chain
- BatWing: BaseReagent family: falls to the existing 'reagents' topic
- BlackPearl: named by the Alchemy chain
- Bloodmoss: named by the Alchemy chain
- Bottle: named by the Alchemy chain
- ConflagrationPotion: BasePotion family: falls to the existing 'potion' topic
- ConfusionBlastPotion: BasePotion family: falls to the existing 'potion' topic
- CurePotion: named by the Alchemy chain
- DaemonBlood: BaseReagent family: falls to the existing 'reagents' topic
- DaemonBone: BaseReagent family: falls to the existing 'reagents' topic
- DarkglowPotion: BasePotion family: falls to the existing 'potion' topic
- DeadWood: BaseReagent family: falls to the existing 'reagents' topic
- DeadlyPoisonPotion: named by the Alchemy chain
- DragonsBlood: BaseReagent family: falls to the existing 'reagents' topic
- ExplosionPotion: named by the Alchemy chain
- Garlic: named by the Alchemy chain
- Ginseng: named by the Alchemy chain
- GraveDust: BaseReagent family: falls to the existing 'reagents' topic
- GreaterAgilityPotion: named by the Alchemy chain
- GreaterConflagrationPotion: BasePotion family: falls to the existing 'potion' topic
- GreaterConfusionBlastPotion: BasePotion family: falls to the existing 'potion' topic
- GreaterCurePotion: named by the Alchemy chain
- GreaterExplosionPotion: named by the Alchemy chain
- GreaterHealPotion: named by the Alchemy chain
- GreaterPoisonPotion: named by the Alchemy chain
- GreaterStrengthPotion: named by the Alchemy chain
- HealPotion: named by the Alchemy chain
- InvisibilityPotion: BasePotion family: falls to the existing 'potion' topic
- LesserCurePotion: named by the Alchemy chain
- LesserExplosionPotion: named by the Alchemy chain
- LesserHealPotion: named by the Alchemy chain
- LesserPoisonPotion: named by the Alchemy chain
- MandrakeRoot: named by the Alchemy chain
- MelisandesFermentedWine: BasePotion family: falls to the existing 'potion' topic
- NightSightPotion: named by the Alchemy chain
- Nightshade: named by the Alchemy chain
- NoxCrystal: BaseReagent family: falls to the existing 'reagents' topic
- ParasiticPotion: BasePotion family: falls to the existing 'potion' topic
- PigIron: BaseReagent family: falls to the existing 'reagents' topic
- PoisonPotion: named by the Alchemy chain
- RefreshPotion: named by the Alchemy chain
- SpidersSilk: named by the Alchemy chain
- StrengthPotion: named by the Alchemy chain
- SulfurousAsh: named by the Alchemy chain
- TotalRefreshPotion: named by the Alchemy chain

## Classes covered by my topics (class -> topic)

- r-ore: AgapiteOre, BronzeOre, CopperOre, DullCopperOre, GoldOre, IronOre, ShadowIronOre, ValoriteOre, VeriteOre
- r-ingots: AgapiteIngot, BronzeIngot, CopperIngot, DullCopperIngot, GoldIngot, IronIngot, ShadowIronIngot, ValoriteIngot, VeriteIngot
- r-logs: AshLog, BloodwoodLog, FrostwoodLog, HeartwoodLog, Log, OakLog, YewLog
- r-boards: AshBoard, BloodwoodBoard, Board, FrostwoodBoard, HeartwoodBoard, OakBoard, YewBoard
- r-kindling: Kindling
- r-barrel-parts: BarrelHoops, BarrelLid, BarrelStaves, BarrelTap
- r-hides: BarbedHides, Hides, HornedHides, SpinedHides
- r-leather: BarbedLeather, HornedLeather, Leather, SpinedLeather
- r-cloth: Cloth, UncutCloth
- r-bolt: BoltOfCloth
- r-cotton: Cotton, Flax
- r-wool: TaintedWool, Wool
- r-thread: DarkYarn, LightYarn, LightYarnUnraveled, SpoolOfThread
- r-feather: Feather, Shaft
- r-parts: Axle, AxleGears, Gears, Hinge, Springs
- r-clock-parts: ClockFrame, ClockParts, SextantParts
- r-body-parts: Head, LeftArm, LeftLeg, RightArm, RightLeg, Torso
- r-gems: Amber, Amethyst, Citrine, Diamond, Emerald, PrismaticAmber, Ruby, Sapphire, StarSapphire, Tourmaline
- r-gold: Gold
- r-fish: BigFish, Fish
- r-magic-fish: PeculiarFish, PrizedFish, TrulyRareFish, WondrousFish
- r-food: AwaseMisoSoup, BentoBox, CandyCane, CreepyCake, DarkChocolate, GingerBreadCookie, GreenTea, JellyBeans, Lollipops, MilkChocolate, MiniatureMushroom, MisoSoup, MrPlainsCookies, NougatSwirl, RedMisoSoup, Spam, SushiPlatter, SushiRolls, Taffy, Wasabi, WasabiClumps, WhiteChocolate, WhiteMisoSoup, WrappedCandy
- r-raw-food: BrightlyColoredEggs, CakeMix, CookieMix, EasterEggs, Eggs, RawBird, RawChickenLeg, RawFishSteak, RawLambLeg, RawRibs, UnbakedApplePie, UnbakedFruitPie, UnbakedMeatPie, UnbakedPeachCobbler, UnbakedPumpkinPie, UnbakedQuiche, UncookedCheesePizza, UncookedSausagePizza
- r-cooked-meat: Bacon, ChickenLeg, CookedBird, FishSteak, FriedEggs, Ham, LambLeg, PeppercornFishsteak, PixieLeg, Ribs, RoastPig, Sausage, SlabOfBacon
- r-baked: ApplePie, BreadLoaf, Cake, CheesePizza, Cookies, FrenchBread, FruitPie, MeatPie, Muffins, PeachCobbler, PumpkinPie, PumpkinPizza, Quiche, SausagePizza
- r-cheese: CheeseSlice, CheeseWedge, CheeseWheel
- r-fruit-veg: Apple, Banana, Bananas, Cabbage, Cantaloupe, Carrot, Coconut, Dates, EarOfCorn, FruitBasket, Grapes, GreenGourd, HoneydewMelon, Lemon, Lemons, Lettuce, Lime, Limes, Onion, OpenCoconut, Peach, Pear, Pumpkin, SmallPumpkin, SmallWatermelon, SplitCoconut, Squash, Turnip, Watermelon, YellowGourd
- r-crops: FarmableCabbage, FarmableCarrot, FarmableCotton, FarmableFlax, FarmableLettuce, FarmableOnion, FarmablePumpkin, FarmableTurnip, FarmableWheat
- r-bowls: EmptyPewterBowl, EmptyPewterTub, EmptyWoodenBowl, EmptyWoodenTub, PewterBowlOfCarrots, PewterBowlOfCorn, PewterBowlOfLettuce, PewterBowlOfPeas, PewterBowlOfPotatos, WoodenBowl, WoodenBowlOfCarrots, WoodenBowlOfCorn, WoodenBowlOfLettuce, WoodenBowlOfPeas, WoodenBowlOfStew, WoodenBowlOfTomatoSoup
- r-drinks: AdmiralsHeartyRum, CeramicMug, EndlessDecanter, GlassMug, Goblet, HarvestWine, MurkyMilk, PewterMug, Pitcher
- r-flour: Dough, JarHoney, SackFlour, SweetDough, WheatSheaf
