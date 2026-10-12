# Crafting skill pages: claim lines and open items

Pages written (9): Blacksmith, Fletching, Carpentry, Cartography, Cooking, Inscribe, Tailoring, Tinkering, Poisoning.
File: `work/help-gumps/parts/crafting.skills.json`. Own text per page (characters, before the generated blocks): Blacksmith about 5,600, Tailoring 4,200, Tinkering 4,100, Fletching 3,400, Inscribe 3,300, Carpentry 3,100, Cooking 2,900, Poisoning 2,400, Cartography 2,100.

Path shorthand used below:
- UOC = ModernUO/Projects/UOContent
- CRAFT = ModernUO/Projects/UOContent/Engines/Craft
- T2A = ModernUO/Projects/UOContent/Engines/Craft/T2A
- SB = ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo
- NPC = ModernUO/Projects/UOContent/Mobiles/Vendors/NPC
- SHARD = ShardContent/src/BritanniaRenaissance.Content
- DOCS = ShardContent/docs
- DATA = ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b

Format: `topic | claim | source file:line`.

## Era and flow facts shared by all eight craft pages

all | T2A packet menus are on for this shard (UOTD false, so t2aCraftMenus defaults on) | ModernUO/Projects/UOContent/Configuration/ExpansionConfiguration.cs:15; DOCS/Cooking-Era-Restore-Research.md:8
all | double-click a craft tool (it must be in the pack or worn) and the game says "Target this tool to make last item, or any other target to begin crafting." | UOC/Items/Skill Items/Tools/BaseTool.cs:149-176 (message at 165, pack check at 151)
all | targeting the tool itself repeats the last item; with nothing made yet it says "You have not yet crafted anything." and opens the menu | T2A/T2ACraftToolTarget.cs:17-62
all | any other target is passed to the menu code as the material to use | T2A/T2ACraftToolTarget.cs:64-69; T2A/T2ACraftSystem.cs:18-108
all | the menu does not reopen after a craft in T2A mode ("Don't reopen menu. Player double-clicks tool to restart.") | CRAFT/Core/CraftItem.cs:1977-1995 (1981 comment); 1549-1558, 1764-1779
all | menus list only items the player has the skill and materials for; empty menu says "You lack the skill and materials to craft anything." | T2A/T2ACraftSystem.cs:194-248 (CanCraftItem), 262-291 (FilterEntries), 113-120 (message); a recipe at exactly its first number has chance 0 and is also hidden (line 205)
all | one attempt takes about 1.25 s (craft delay 1.25 s, 1 + 1 ticks: first at once, second after 1.25 s) | CRAFT/Core/CraftItem.cs:1008-1012, 1850-1853; ctor `base(1, 1, 1.25)` in DefBlacksmithy.cs:16, DefBowFletching.cs:13, DefCarpentry.cs:13, DefCartography.cs:14, DefInscription.cs:33, DefTailoring.cs:21, DefTinkering.cs:30
all | success chance = minChance + (skill - min) / (max - min) x (1 - minChance); below min the recipe cannot be made | CRAFT/Core/CraftItem.cs:869-904
all | minChance is 0% for Blacksmith, Cartography, Inscription, Tinkering (potion keg 50%), 50% for Bowcraft, Carpentry, Tailoring | DefBlacksmithy.cs:28; DefCartography.cs:26; DefInscription.cs:45; DefTinkering.cs:40-48; DefBowFletching.cs:25; DefCarpentry.cs:23; DefTailoring.cs:33
all | the 50% note is printed by the generated table for Bowcraft, Carpentry, Tailoring | SHARD/HelpGenerators.cs:84-88
all | a failure takes the other half of the materials rounded up (amount minus amount/2) and one tool charge; a success takes all and one charge | CRAFT/Core/CraftItem.cs:681-688, 1585-1625 (tool use 1609-1611), 1411
all | failure message "You failed to create the item, and some of your materials are lost." | CRAFT/DefBlacksmithy.cs:139-144 (same in the other defs); text of 1044043 read from Cliloc.enu
all | crafted/bought tool has 25 to 75 charges; crafted exceptional tool has 100 in UOR; breaks at 0 | UOC/Items/Skill Items/Tools/BaseTool.cs:29, 71-76; CRAFT/Core/CraftItem.cs:1426-1434
all | skill gain per attempt uses CheckSkill(skill, min, max): no gain below min or at/above max | UOC/Skills/SkillCheck.cs:61-80, 118-171
all | the gain curve block says what happens under 10 and the class multipliers (not repeated in the text) | SHARD/HelpGenerators.cs:171-202
all | training needs the skill set to Up | SHARD/WelcomeGuide.GettingStarted.cs:141-142 (Skill locks 101)
all | exceptional chance: default ECA is success chance minus 0.60; Blacksmith and Tailoring use minus clamp(0.60 - (skill - 95) x 0.03, 0.45, 0.60); Bowcraft uses chance x 0.5 - 0.1 | CRAFT/Core/CraftItem.cs:812-839; Def files: DefBlacksmithy.cs:26, DefTailoring.cs:31, DefBowFletching.cs:23; others use the default (DefCarpentry/DefTinkering/DefCartography/DefInscription have no ECA override, DefCraftSystem ECA default at CRAFT/Core/CraftSystem.cs:55)
all | maker's mark offered only when the item is exceptional, markable and Base skill is 100.0; T2A always prompts | CRAFT/Core/CraftItem.cs:1936-1955; markable types 110-122
all | prompt text "Do you wish to place your maker's mark on this item?" with CONTINUE / CANCEL | CRAFT/Core/QueryMakersMarkGump.cs:38-44 (texts read from Cliloc.enu 1018317, 1011011, 1011012)
all | Exceptional weapon: +20% damage and +20 durability bonus; exceptional armor: +8 armor rating and +20 durability bonus in UOR | UOC/Items/Weapons/BaseWeapon.cs:2729-2732, 1007; UOC/Items/Armor/BaseArmor.cs:325, 897; quality setters scale durability: BaseWeapon.cs:407-415, BaseArmor.cs:191-199
all | shops pay x1.25 for exceptional armor and weapons | UOC/Mobiles/Vendors/GenericSell.cs:72-73, 89-90
all | Mastery/class numbers are generated, not typed | SHARD/HelpGenerators.cs
all | the town trainers named (Armorer, Weaponsmith, Blacksmith, Bowyer, Carpenter, Mapmaker, Cook, Herbalist, Mage, Scribe, Tailor) teach these skills; the Welcome guide states it | SHARD/WelcomeGuide.GettingStarted.cs:187-203
all | those NPC types are spawned in Britain (Armorer 4, Weaponsmith 4, Blacksmith 2, Bowyer 1, Carpenter 1, Mapmaker 1, Cook 4, Herbalist 2, Mage 5, Scribe 2, Tailor 3, Tanner 1, Butcher 1, Provisioner 2, Alchemist 5, Jeweler 2, Weaver 3) | DATA/Spawns/Vendors.json (tally of entry names, all in Britain: britainOnlySpawnerFiles), ShardContent/data/world-generation/alpha2b/world-generation.json
starter | each Alpha 3 starter craft package is a one-time per-account grant, newbied, tools set to 50 uses; amounts are ceilings | SHARD/StarterCraftMaterialIssuance.cs:24, 57-146, 197-203
starter | bulk supplies are trimmed to 85% of the carry limit | DOCS/Starter-Weight-Budget.md:21-24, shard-rules.json starterWeight
starter | newbied items stay when you die and shops will not buy them | SHARD/WelcomeGuide.GettingStarted.cs:64-68, 230; UOC/Mobiles/Vendors/GenericSell.cs:34-52
starter | feature flag Alpha3StarterCraftMaterials is true | ShardContent/data/configuration/shard-rules.json:203
flags | HarvestAutoRepeat true: mining, lumberjacking, fishing repeat; list of stops | DOCS/Harvest-AutoRepeat-Evidence.md:24-34; README.md:45
flags | ActionAutoRepeat true: cooking, spinning wheel, loom (plus taming, lockpicking) repeat | DOCS/Action-AutoRepeat-Evidence.md:24-30; README.md:46
flags | requires names used are real properties of DeferredFeatureFlags: Alpha3StarterCraftMaterials, Alpha3StarterScissors, HarvestAutoRepeat, ActionAutoRepeat, PoisonRelief, TheftProtection | SHARD/ShardRulesConfiguration.cs:758-870

## Blacksmith

Blacksmith | skill shown as Blacksmithy | ModernUO/Distribution/Data/skills.json (SkillID 7)
Blacksmith | tools: Tongs, Smith's Hammer, Sledge Hammer all use DefBlacksmithy | UOC/Items/Skill Items/Tools/Tongs.cs:22, SmithHammer.cs:18, SledgeHammer.cs:16
Blacksmith | must be within 2 tiles (line of sight) of an anvil and a forge; message 1044267 at the double-click | CRAFT/DefBlacksmithy.cs:30-91, 93-118 (CheckAnvilAndForge(from, 2) at 110); BaseTool.cs:155-161
Blacksmith | Britain's smithies have anvils and forges (anvils 1363,1574 / 1423,1556 / 1346-1355,1774-1786; forges 1361,1574 / 1424,1558 / 1344-1356,1776-1784), beside the Blacksmith spawns (1418,1547) (1349,1778) | DATA/Decoration/Britannia__britain.cfg:1412-1430, 1735-1743; DATA/Spawns/Vendors.json
Blacksmith | first target must be ingots; others re-prompt "Target the ingots you wish to use." / "That is not a valid ingot." | T2A/BlacksmithMenu.cs:474-532 (499, 529), 591-624 (621)
Blacksmith | main menu "What would you like to do?": Repair, Smelt, Build Armor, Build Shield, Build Weapons; Repair/Smelt always shown | T2A/BlacksmithMenu.cs:98, 212-219, 291-345 (302)
Blacksmith | armor: ring, chain, plate (helmets inside plate list); weapons: blades, axes, pole arms, bludgeoning | T2A/BlacksmithMenu.cs:27-70, 221-243
Blacksmith | each line "name (N ingots)" | T2A/BlacksmithMenu.cs:137-169 (160)
Blacksmith | a menu with no build lines means no skill/ingots or a metal the character cannot work (only Repair and Smelt remain) | T2A/BlacksmithMenu.cs:291-345; T2ACraftSystem.cs:194-248
Blacksmith | Dagger is the cheapest (3 ingots) and teaches from -0.4; Buckler -25..25 (10 ingots) | CRAFT/DefBlacksmithy.cs:302, 276
Blacksmith | shields teach to about 25-40 (Buckler 25, Bronze/Wooden kite 34.8, Metal shield 39.8) | DefBlacksmithy.cs:276-281
Blacksmith | ring/chain/mace/sword ranges (ring mail 12..72, chain coif 14.5..64.5, mace 14.5..64.5, longsword 28..78) | DefBlacksmithy.cs:187-197, 301-307, 602
Blacksmith | plate gorget 56.4 (10 ingots) and gloves 58.9 (12) are the cheapest plate; plate chest 75..125 | DefBlacksmithy.cs:198-203
Blacksmith | a Buckler sells for 25; iron ingot costs 5 | SB/SBBlacksmith.cs:121, 16
Blacksmith | Tongs 13, Smith's Hammer 21, iron ingot 5 with 16 on the shelf | SB/SBBlacksmith.cs:16-17, 100
Blacksmith | Tinkering makes Tongs and Smith's Hammer | CRAFT/DefTinkering.cs:258-259; T2A/TinkeringMenu.cs:33-38
Blacksmith | smelting: double-click ore, target a forge; Mining check 25..75 for iron, difficulty +-25 for colored; failure halves the pile; colored ore needs Mining at least its difficulty | UOC/Items/Resources/Blacksmithing/Ore.cs:96-100, 160-200 (difficulty 160-184, check 197, failure 251)
Blacksmith | special ingot skill thresholds 65/70/75/80/85/90/95/99 | CRAFT/DefBlacksmithy.cs:687-695
Blacksmith | selecting an ingot pile chooses the metal for the menu | T2A/BlacksmithMenu.cs:568-588, 603-619
Blacksmith | colored armor bonus +2 Dull Copper ... +16 Valorite in UOR | UOC/Items/Armor/BaseArmor.cs:305-323
Blacksmith | shield armor rating scales with Parry | UOC/Items/Shields/BaseShield.cs:15-29
Blacksmith | weapons made from colored ingots get no Resource/bonus in UOR (Resource set only under Core.AOS or with a runic tool) | UOC/Items/Weapons/BaseWeapon.cs:702-756 (Core.AOS at 718, 720)
Blacksmith | Repair: weaken chance 40 + (max - cur) - skill/10 percent; weaken 3 below skill 70, 2 from 70, 1 from 90 (Base skill); refusal at max durability <= weaken; poisoned weapons refused; no materials | CRAFT/Core/Repair.cs:41-45, 239-262, 273, 281-307, 163-167
Blacksmith | Repair needs forge and anvil | Repair.cs:165-168
Blacksmith | Smelt: half the ingots for player-made, 1 for shop items; colored metal needs Mining; needs anvil and forge | CRAFT/Core/Resmelt.cs:72-107, 124-145
Blacksmith | exceptional only above 60% success; mark at Base 100 | see shared lines
Blacksmith | bulk order: Blacksmith class supports it with Blacksmith Base > 0; Bulk Order Info menu entry (client text 3006152 "Bulk Order Info") | NPC/Blacksmith.cs:109; UOC/Mobiles/Vendors/BaseVendor.cs:1359-1363, 1396-1432
Blacksmith | waits 1 h (skill 50 or below), 2 h (50.1+), 6 h (70.1+); real time (DateTime) | NPC/Blacksmith.cs:76-94; UOC/Mobiles/PlayerMobile.cs:187, 293-307
Blacksmith | deed: 10/15/20 pieces; exceptional and special metal only from skill 70.1; material only for armor | UOC/Engines/Bulk Orders/SmallSmithBOD.cs:76-164
Blacksmith | deed gump "Combine this deed with the item requested." then target each piece; drop the full deed on a Blacksmith | UOC/Engines/Bulk Orders/SmallBODGump.cs:62-63; SmallBOD.cs:71-86, 117-180; BaseVendor.cs:1111-1175
Blacksmith | reward is gold (check over 1,000), fame and maybe an item chosen at random | BaseVendor.cs:1143-1175 (1148, 1164-1170); Engines/Bulk Orders/BaseBOD.cs:61-70
Blacksmith | Tailor and Weaponsmith bulk orders are gated off until AoS | DOCS/Alpha-3-Blacksmith-BOD-Readiness.md:19-23; DOCS/Alpha-3-Player-Skill-Audit.md:25, 52
Blacksmith | the table lists Dragon scale armor (RedScales etc.), which the Blacksmith menu has no category for | CRAFT/DefBlacksmithy.cs:655-668 vs T2A/BlacksmithMenu.cs:27-70
Blacksmith | starter: Tongs, 2 Pickaxes, ingots topped to 250 (merged with other ingot grants), Tongs and Pickaxe set to 50 uses | SHARD/StarterCraftMaterialIssuance.cs:57-65; UOC/Engines/Character Creation/CharacterCreation.cs:1028-1035
Blacksmith | trainers Armorer, Weaponsmith, Blacksmith | SHARD/WelcomeGuide.GettingStarted.cs:197-198

## Fletching

Fletching | skill shown as Bowcraft/Fletching | ModernUO/Distribution/Data/skills.json (SkillID 8)
Fletching | first target Log, Board, Feather or Shaft, else it re-prompts "Target the wood or feathers you wish to use." | T2A/T2ACraftSystem.cs:52-63, 122-158
Fletching | menu: Kindling, Shafts, Arrows, Bolts, Bow, Crossbow, Heavy Crossbow | T2A/BowFletchingMenu.cs:10-23
Fletching | menu "What would you like to make?" | T2A/BowFletchingMenu.cs:28
Fletching | shafts/arrows/bolts 0..40, Bow 30..70 (7 logs), Crossbow 60..100 (7), Heavy Crossbow 80..120 (10), Kindling 1 log | CRAFT/DefBowFletching.cs:94-118
Fletching | Shaft, Arrow and Bolt use UseAllRes: maxAmount is the lowest GetAmount/needed across resources, whole pack including bags; failure takes half | CRAFT/DefBowFletching.cs:97, 102, 106; CRAFT/Core/CraftItem.cs:649-679, 691-697, 749-753, 1585-1588; Server/Items/Container.cs:873-900 (recurse default true)
Fletching | Log and Board count as the same material | CRAFT/Core/CraftItem.cs:66-85; T2A/T2ACraftSystem.cs:315-333
Fletching | exceptional chance = chance x 0.5 - 0.1 (max 0.4) | CRAFT/DefBowFletching.cs:23; CRAFT/Core/CraftItem.cs:829
Fletching | Bow/Crossbow sell 17/25, Heavy Crossbow 27; Bowyer buys arrows, bolts, shafts, feathers 1 | SB/Weapons/SBRangedWeapon.cs:36-43 (Bowyer NPC has SBRangedWeapon: NPC/Bowyer.cs:37)
Fletching | boards 3 at a Carpenter; Fletcher's Tools 2 at a Bowyer; feathers 2, arrows 2, bolts 3 at a Bowyer; Provisioner arrows 2, bolts 5, Kindling 2 | SB/SBCarpenter.cs:18; SB/SBBowyer.cs:16; SB/Weapons/SBRangedWeapon.cs:24-28; SB/SBProvisioner.cs:27-28, 81
Fletching | log 2 stones; board 1 stone | UOC/Items/Skill Items/Lumberjack/Log.cs:29; DOCS/Starter-Weight-Budget.md:11-17 ("A Board and a Bottle weigh 1 stone each")
Fletching | an axe in hand on a log pile cuts boards | UOC/Engines/Harvest/Core/HarvestTarget.cs:56; UOC/Items/Skill Items/Lumberjack/Log.cs:42, 70-85; UOC/Engines/Harvest/Lumberjacking.cs:132-135 (axe must be equipped)
Fletching | carving a bird leaves feathers on the corpse | UOC/Mobiles/BaseCreature.cs:2005, 2040-2046
Fletching | Kindling lights a campfire | UOC/Items/Skill Items/Camping/Kindling.cs:40-70
Fletching | shafts/arrows/bolts carry no quality (plain items, not ICraftable) | UOC/Items/Resources/Arrows/Arrow.cs, Shaft.cs, Bolt.cs
Fletching | Bows hit 20% harder and last 20% longer when exceptional | see shared lines
Fletching | starter: boards topped to 200, feathers to 100, Fletcher's Tools 50 uses | SHARD/StarterCraftMaterialIssuance.cs:101-110
Fletching | trainer: Bowyer | SHARD/WelcomeGuide.GettingStarted.cs:199

## Carpentry

Carpentry | tools: Saw, Dovetail Saw, Hammer, Draw Knife, Froe, Inshave, Scorp, Nails, Jointing/Moulding/Smoothing Plane use DefCarpentry | UOC/Items/Skill Items/Tools/*.cs (CraftSystem property, listed by grep)
Carpentry | first target Log or Board else re-prompt "Target the wood you wish to use." | T2A/T2ACraftSystem.cs:64-75
Carpentry | menu: Furniture, Containers, Weapons, Instruments, Miscellaneous, Add-Ons; lines show wood | T2A/CarpentryMenu.cs:186-195, 100-130
Carpentry | recipes (Barrel Staves 0..25 5 logs; Small Crate 10..35 8; Stool, Footstool 11..36 9; Wooden Box 21..46 10; Wooden Shield 52.6..77.6 9; Quarter Staff 73.6..98.6 6; Shepherd's Crook, Gnarled Staff 78.9..103.9 7; Keg 57.8..82.8 from 3 barrel staves) | CRAFT/DefCarpentry.cs:99, 219, 174-175, 218, 356, 306, 305, 307, 253
Carpentry | recipes teach over 25-point stretches | CRAFT/DefCarpentry.cs:99-592 (all 25.0 wide)
Carpentry | Carpentry Board craft only for AoS/SE, not UOR | CRAFT/DefCarpentry.cs:93
Carpentry | prices: Saw 15, Board 3 buy; wooden shield 15, crook 10, quarterstaff 9, stool 6 sell; Tinkering makes the tools | SB/SBCarpenter.cs:18, 24; SB/Armors/SBWoodenShields.cs; SB/Weapons/SBStavesWeapon.cs; SB/SBCarpenter.cs (sell list: Stool 6); NPC/Carpenter.cs:25-27; CRAFT/DefTinkering.cs:232-237, 253-260
Carpentry | wooden box, small/medium/large crate and chest are LockableContainer; OnCraft rolls Tinkering -5..15 for a lock and key | UOC/Items/Containers/Container.cs:399-483; UOC/Items/Containers/LockableContainer.cs:17-45
Carpentry | Add-On deeds place in a house you own ("You can only place this in a house that you own!") | UOC/Items/Addons/BaseAddonDeed.cs:42-100; BaseAddon.cs:140-200
Carpentry | exceptional shield/staff/instrument; staff +20% damage | UOC/Items/Weapons/BaseWeapon.cs:2729-2732; UOC/Items/Skill Items/Musical Instruments/BaseInstrument.cs:118-143
Carpentry | no ECA override: default minus 0.60 | CRAFT/DefCarpentry.cs (none) ; CRAFT/Core/CraftSystem.cs:55
Carpentry | starter: Boards topped to 250 and a Saw with 50 uses | SHARD/StarterCraftMaterialIssuance.cs:92-99
Carpentry | trainer: Carpenter | SHARD/WelcomeGuide.GettingStarted.cs:199

## Cartography

Cartography | no tool in T2A mode, the skill callback opens the menu | CRAFT/DefCartography.cs:24; UOC/Skills/Cartography.cs:14-24
Cartography | menu "What kind of map?" with four lines | T2A/CartographyMenu.cs:12-60
Cartography | the list shows only maps the character can make and has a blank map for | T2A/CartographyMenu.cs:64-92
Cartography | Local 10..70, City 25..85, Sea chart 35..95, World map 39.5..99.5, each from one blank map | CRAFT/DefCartography.cs:91-94
Cartography | blank scrolls do not substitute for blank maps in T2A mode | CRAFT/Core/CraftItem.cs:87-91
Cartography | map areas: Local 64 + 2 x skill, City max(64 + 4 x skill, 200), Sea chart max(64 + 10 x skill, 200) around the maker; World map fixed centre widening with skill | UOC/Items/Maps/LocalMap.cs, CityMap.cs, SeaChart.cs, WorldMap.cs (CraftInit)
Cartography | the maps are ICraftable returning quality 1; MapItem not in the markable table | UOC/Items/Maps/MapItem.cs:53-58; CRAFT/Core/CraftItem.cs:110-122
Cartography | blank map 5, Mapmaker buys Local, City, World maps for 3, not Sea chart | SB/SBMapmaker.cs:16, 33-36
Cartography | one Mapmaker spawns in Britain at 1416,1754 | DATA/Spawns/Vendors.json
Cartography | stock start items: 4 blank maps and a sextant | UOC/Engines/Character Creation/CharacterCreation.cs:1076-1083
Cartography | treasure map decode thresholds: level 1 -3, 2 41, 3 51, 4 61, 5 and 6 70; CheckSkill min..min+60; failure message 503018 "You fail to make anything of the map."; double-click calls Decode | UOC/Items/Maps/TreasureMap.cs:371-421 (decode), 341
Cartography | treasure maps come from fishing at 90 and rarely from monsters | UOC/Engines/Harvest/Fishing.cs:17, 221-234; UOC/Mobiles/BaseCreature.cs:3251; DOCS/Alpha-3-Player-Skill-Audit.md:206-211 (SK-008, SK-013)
Cartography | trainer: Mapmaker | SHARD/WelcomeGuide.GettingStarted.cs:201

## Cooking

Cooking | skill shown as Cooking; no craft table | ModernUO/Distribution/Data/skills.json (SkillID 13)
Cooking | no tool: the T2A menu has no Cooking branch so Skillet, Rolling Pin and Flour Sifter open nothing; flour/dough/baking (Part B) not built | DOCS/Cooking-Era-Restore-Research.md:8-10, 41; T2A/T2ACraftSystem.cs:18-108 (no DefCooking branch); DOCS/Cooking-Era-Restore-Readiness.md:6
Cooking | double-click raw food, target a heat source; range 1; food within 2 tiles or in pack, not in another's hands | UOC/Items/Food/CookableFood.cs:35-60 (CanCook 46-58), 96 (range 1), 100-120
Cooking | 5 second delay; walking over 3 tiles away or changing map burns the food | CookableFood.cs:10, 62-72, 118
Cooking | chance = Cooking skill: CheckSkill(Cooking, 0, 100); failure: "You burn the food to a crisp! It's ruined." | CookableFood.cs:77-81; Cliloc 500686
Cooking | one piece per attempt; a second attempt says "You must wait to perform another action." | CookableFood.cs:105-109, 116
Cooking | heat sources: campfire, sandstone and stone ovens/fireplaces, fire pit, heating stand, Fire Field, small and large forge | CookableFood.cs:131-174
Cooking | raw foods that cook: ribs, lamb leg, chicken leg, bird, fish steak (eggs, pies, mixes also exist but are not obtainable) | CookableFood.cs:179-228, 428-440; DOCS/Cooking-Era-Restore-Readiness.md:43
Cooking | ovens at 1424,1712 and 1448,1615 (cook and baker shops); forges in smithies | DATA/Decoration/Britannia__britain.cfg:115-118, 1423-1430
Cooking | Kindling 2 gold at a Provisioner; double-click lights a campfire with a Camping roll | SB/SBProvisioner.cs:81; UOC/Items/Skill Items/Camping/Kindling.cs:40-70
Cooking | Butcher prices: chicken leg 6, bird 9, lamb leg 9, ribs 16; Cook pays chicken 3, lamb 4, cooked bird 8 | SB/SBButcher.cs:19-22; SB/SBCook.cs:53, 59-60
Cooking | carving gives ribs, lamb legs, birds; scissors on a fish give 4 raw fish steaks | UOC/Mobiles/BaseCreature.cs:2052-2072; UOC/Items/Resources/Fishing/Fish.cs:19
Cooking | eating fills hunger (max 20), a little stamina, "too full" message | UOC/Items/Food/Food.cs:57-100 (96 stamina, 88 full)
Cooking | poisoned food poisons the eater | UOC/Items/Food/Food.cs:57-80 (Poison, ApplyPoison)
Cooking | starter: lamb, chicken, fish topped to 20, Kindling, flour sack, pitcher | SHARD/StarterCraftMaterialIssuance.cs:135-146; UOC/Engines/Character Creation/CharacterCreation.cs:1085-1093
Cooking | cooking repeat through a stack at the chosen heat source, burned or not, until the stack is gone | DOCS/Action-AutoRepeat-Evidence.md:30; README.md:46
Cooking | trainers: Cook, Herbalist | SHARD/WelcomeGuide.GettingStarted.cs:199-200
Cooking | skill class easy | ShardContent/data/configuration/shard-rules.json:82

## Inscribe

Inscribe | skill shown as Inscription; no tool in T2A mode; skill callback | CRAFT/DefInscription.cs:43; UOC/Skills/Inscribe.cs:19-27
Inscribe | the prompt "Target the book you wish to copy or scroll you want to use." with a 60 s timeout | UOC/Skills/Inscribe.cs:23-27
Inscribe | blank scroll target must be in the pack; recall rune target crafts a Runebook; book target copies | UOC/Skills/Inscribe.cs:94-153
Inscribe | menu "Which circle of spells?" with Runebook, then circles; "Which spell would you like to scribe?" | T2A/InscriptionMenu.cs:39-40, 74-85, 150-196
Inscribe | a spell is listed only if the spell is in a spellbook the character carries, skill, a blank scroll and reagents are there | T2A/InscriptionMenu.cs:105-147 (HasSpellInBook), 149-166 (CanScribeScroll); CRAFT/DefInscription.cs:49-72
Inscribe | mana per circle 4, 6, 9, 11, 14, 20, 40, 50 (so the seventh and eighth circles need a pool of 40 and 50); the page no longer talks about stats, the generated stats block does | CRAFT/DefInscription.cs:255-340 (327-328 mana 40, 339-340 mana 50)
Inscribe | mana is spent only on success; a failure ruins the scroll and reagents ("You fail to inscribe the scroll, and the scroll is ruined.") | CRAFT/Core/CraftItem.cs:1388 (ConsumeAttributes true only in success branch); 1585-1625; CRAFT/DefInscription.cs:116-122
Inscribe | mana message "You lack the mana required to inscribe that spell." | CRAFT/DefInscription.cs:204 (1042403); Cliloc
Inscribe | circle ranges: 1st -25..25, 2nd -10.8..39.2, 3rd 3.5..53.5, 4th 17.8..67.8, 5th 32.1..82.1, 6th 46.4..96.4, 7th 60.7..110.7, 8th 75..125 | CRAFT/DefInscription.cs:131-182
Inscribe | single-reagent spells: Magic Arrow (sulfurous ash), Fireball (black pearl), Poison (nightshade) | CRAFT/DefInscription.cs:263, 283, 285
Inscribe | blank scroll 5 (Scribe, Mage), 12 (Mapmaker); Mage sells reagents 3 (5 for black pearl, bloodmoss), spellbook 18, recall rune 15, scrolls of the first three circles | SB/SBScribe.cs:17; SB/SBMage.cs; SB/SBMapmaker.cs:18; SB/SBAlchemist.cs (reagents)
Inscribe | Mage pays (circle + 2) x 2 = 4 to 18 per scroll | SB/SBMage.cs (sell loop `(i / 8 + 2) * 2`); UOC/Misc/Loot.cs:192-204 (scroll order)
Inscribe | dropping a scroll on a spellbook adds the spell | UOC/Items/Skill Items/Magical/Spellbook.cs:499-529
Inscribe | Runebook 45..95: 8 blank scrolls, Recall scroll, Gate Travel scroll, an unmarked recall rune | CRAFT/DefInscription.cs:433-437; CRAFT/Core/CraftItem.cs:704-723
Inscribe | book copy is CheckTargetSkill(Inscribe, 0, 50), no materials | UOC/Skills/Inscribe.cs:237
Inscribe | starter: blank scrolls topped to 75, bag of reagents, Scribe's Pen (50 uses) | SHARD/StarterCraftMaterialIssuance.cs:112-123
Inscribe | trainers: Mage, Scribe | SHARD/WelcomeGuide.GettingStarted.cs:201-202

## Tailoring

Tailoring | tool Sewing Kit | UOC/Items/Skill Items/Tools/SewingKit.cs:21
Tailoring | first target: cloth or uncut cloth opens clothes (hue-matched), leather or hides opens leather; otherwise "Select the resource you wish to use (cloth, leather, or hides)." / "That is not a valid resource..." | T2A/TailoringMenu.cs:316-374 (318, 324, 337, 371)
Tailoring | cloth menu: Build Hats, Shirts, Pants, Misc; leather menu: Build Shoes, Leather Armor, Studded Armor, Female Armor | T2A/TailoringMenu.cs:176-190
Tailoring | hue-aware crafting: only resources of the targeted hue are used and spent, the garment takes that hue | T2A/TailoringMenu.cs:273-283; CRAFT/Core/CraftItem.cs:1019-1098, 1104-1143, 1150-1243
Tailoring | hides count as leather, uncut cloth counts as cloth | CRAFT/Core/CraftItem.cs:66-85; T2A/T2ACraftSystem.cs:315-333
Tailoring | recipes: Skull Cap, Bandana 0..25 (2 cloth); Leather Cap 6.2..31.2 (2 leather); Sandals 12.4..37.4 (4); Shoes 16.5..41.5 (6); Boots 33.1..58.1 (8); Leather Gloves 51.8..76.8 (3); Gorget 53.9..78.9 (4); Arms 53.9..78.9 (4); Legs 66.3..91.3 (10); Chest 70.5..95.5 (12); Studded Gorget 78.8..103.8 (6) | CRAFT/DefTailoring.cs:116-117, 430, 367-369, 431, 429, 432-434, 563
Tailoring | cloth items teach to about 80 (Robe 53.9..78.9) | CRAFT/DefTailoring.cs:143-152
Tailoring | Tanner buys leather gloves 30, gorget 37, arms 40; leather 6 buy, 5 sell | SB/SBTanner.cs:42, 58-64 (sell list)
Tailoring | Sewing Kit 3, Cloth 2 at a Tailor; Tinkering makes the kit | SB/SBTailor.cs:16, 52; CRAFT/DefTinkering.cs:252
Tailoring | the table lists Bolt of Cloth (non-AoS), Oil Cloth, bone armor and Orc Helm; none is in the Tailoring menu | CRAFT/DefTailoring.cs:262, 639-655, 668-672; T2A/TailoringMenu.cs:21-63
Tailoring | the menu accepts only Leather or Hides, not Spined/Horned/Barbed (see OPEN) | T2A/TailoringMenu.cs:337
Tailoring | scissors on hides turn the whole pile to leather 1:1; hides 5 stones, leather 1 | UOC/Items/Resources/Tailor/Hides.cs:16, 103; Leathers.cs:16; Server/Items/Item.cs:4371-4400
Tailoring | scissors on a bolt of cloth give 50 cloth | UOC/Items/Resources/Tailor/BoltOfCloth.cs:41
Tailoring | scissors on clothing/leather armor give back half (made by you) or 1 (shop) | UOC/Items/Clothing/BaseClothing.cs:238-278 (273); UOC/Items/Armor/BaseArmor.cs:632-662 (651)
Tailoring | wool to 3 yarn, cotton and flax to 6 thread each at a wheel; loom takes 5 into a bolt | UOC/Items/Resources/Tailor/Wool.cs:43-48; Cotton.cs:43-50; Flax.cs:43-48; YarnsAndThreads.cs:80-103 (91, 98)
Tailoring | Britain spinning wheels and looms in weaver/tailor shops | DATA/Decoration/Britannia__britain.cfg:1440-1460
Tailoring | spinning/loom repeat | DOCS/Action-AutoRepeat-Evidence.md:28-29
Tailoring | carving leaves hides on the corpse (plain Hides for a Regular hide type, not cut) | UOC/Mobiles/BaseCreature.cs:2092-2123
Tailoring | exceptional leather armor +8 AR, +20% durability; clothing exceptional only labelled | see shared lines; UOC/Items/Clothing/BaseClothing.cs:722-725 (label), 399-406 (durability from attributes only)
Tailoring | Tailor and Weaver bulk orders gated until AoS | DOCS/Alpha-3-Blacksmith-BOD-Readiness.md:19-23
Tailoring | starter: 300 cloth, 50 leather, Sewing Kit 50 uses | SHARD/StarterCraftMaterialIssuance.cs:79-90
Tailoring | starter scissors, one pair per character, newbied and nontransferable | SHARD/StarterScissors.cs:14-100; README.md:56
Tailoring | trainer: Tailor | SHARD/WelcomeGuide.GettingStarted.cs:202

## Tinkering

Tinkering | tools: TinkerTools and TinkersTools both use DefTinkering | UOC/Items/Skill Items/Tools/TinkerTools.cs:22, 40
Tinkering | first target: Log/Board (wooden items), BaseIngot (menu), Keg (potion keg); else re-prompt "Select the resource you wish to use (wood or ingots)." | T2A/TinkeringMenu.cs:410-450
Tinkering | menu "What would you like to make?" : Wooden Items, Tools, Parts, Utensils, Traps, Miscellaneous, Jewelry | T2A/TinkeringMenu.cs:205-215
Tinkering | tool list in the menu (no Skillet, Flour Sifter, Fletcher's Tools, pens); Bola and Bola Balls absent | T2A/TinkeringMenu.cs:28-75
Tinkering | utensils 0..50 1 ingot; Hammer 30..80 1; Tongs 35..85 1; Lockpick 45..95 1; Gears, Springs, Hinge, Scissors 5..55 2; Tinker Tools 10..60 2; Sewing Kit 10..70 2; Candelabra, Globe 55..105 4; Scales, Spyglass, Heating Stand 60..110 4; Potion Keg 75..100 | CRAFT/DefTinkering.cs:298-309, 257-263, 246-252, 270-276, 310-317, 425-428
Tinkering | the potion keg starts at 50% | CRAFT/DefTinkering.cs:40-48
Tinkering | prices: Hammer sells to Carpenter 14; Tongs to Blacksmith 7; Smith's Hammer 10; saw to Carpenter 9; scissors to Tailor 6; ingot 5 | SB/SBCarpenter.cs:66, 61; SB/SBBlacksmith.cs:118, 212, 16; SB/SBTailor.cs:66
Tinkering | tool charges 25-75, exceptional 100 | see shared lines
Tinkering | traps: dart (ingot + bolt), poison (ingot + poison potion), explosion (ingot + explosion potion); target an unlocked lockable chest within 2 tiles, not locked down, no trap yet; "Trap is disabled until you lock the chest."; strength = Tinkering/10 x 9 | CRAFT/DefTinkering.cs:431-451, 605-700 (Verify 616-649, power 678-683)
Tinkering | jewelry: gold/silver necklaces, earrings, rings and wedding ring, 2 ingots 40..90; "Target the gemstone you wish to use."; the whole targeted gem stack is consumed and names the piece | CRAFT/DefTinkering.cs:393-403; T2A/TinkeringMenu.cs:70-75, 368-381, 486-540; UOC/Items/Jewels/BaseJewel.cs:186-209
Tinkering | Jewelers sell gems | SB/SBJewel.cs:59-67
Tinkering | there is no Repair or Smelt entry in the Tinkering menu | T2A/TinkeringMenu.cs:205-215
Tinkering | the table lists Skillet, Flour Sifter, Fletcher's Tools, two pens, Bola Ball, Bola, faction traps and kit that the menu does not show | CRAFT/DefTinkering.cs:264-268, 277, 422-424, 453-524
Tinkering | Ward recipe (Miscellaneous, no quality) under TheftProtection and wardCraft | SHARD/BackpackWardCraft.cs:56-85; README.md:35; shard-rules.json:61-66
Tinkering | starter: 200 iron ingots and Tinker's Tools 50 uses | SHARD/StarterCraftMaterialIssuance.cs:67-77
Tinkering | no Tinker NPC is spawned (OPEN 1); the text does not say who sells or teaches | DATA/Spawns/Vendors.json (only TinkerGuildmaster at 1422,1654)

## Poisoning

Poisoning | skill callback: "Select the poison you wish to use." then "To what do you wish to apply the poison?"; 10 s delay | UOC/Skills/Poisoning.cs:20-22, 35
Poisoning | weapon must be Layer.OneHanded and Slashing or Piercing; food allowed; refusal message 502145 | UOC/Skills/Poisoning.cs:57-72, 93-101
Poisoning | after 2 seconds CheckTargetSkill(Poisoning, target, min, max) | UOC/Skills/Poisoning.cs:113, 124
Poisoning | the potion is consumed and a Bottle returned when the application starts | UOC/Skills/Poisoning.cs:76-86
Poisoning | success: weapon poison, charges 18 - 2 x level; food poison; 20 karma lost | UOC/Skills/Poisoning.cs:126-154 (133 charges, 154 karma)
Poisoning | failure: below Base 80, 1 in 20 chance of poisoning yourself | UOC/Skills/Poisoning.cs:157-165 (159)
Poisoning | potion skill ranges Lesser 0..60, Regular 30..70, Greater 60..100, Deadly 95..100 | UOC/Items/Skill Items/Magical/Potions/Poison Potions/LesserPoisonPotion.cs:15-16, PoisonPotion.cs:15-16, GreaterPoisonPotion.cs:15-16, DeadlyPoisonPotion.cs:15-16
Poisoning | poisoned swords, knives and spears use a charge per hit and poison on a coin flip; axes and other types have no such code | UOC/Items/Weapons/Swords/BaseSword.cs:23-38; Knives/BaseKnife.cs:26-41; SpearsAndForks/BaseSpear.cs:18-33
Poisoning | corrosion is off in this shard | SHARD/PostUorSystemGates.cs:18; UOC/Items/Weapons/BaseWeapon.cs:112-139
Poisoning | oil cloth at UOR only cleans corrosion, so it does not clean poison here; message 1005422 | UOC/Items/Misc/OilCloth.cs:69-83; BaseWeapon.cs:151-163
Poisoning | a poisoned weapon cannot be repaired | CRAFT/Core/Repair.cs:273
Poisoning | poison charges tooltip "lesser poison charges: ~1_val~" | UOC/Items/Weapons/BaseWeapon.cs:3030-3032 (1062412 + level)
Poisoning | the whole stack of food is poisoned (Poison is set on the stack item) | UOC/Skills/Poisoning.cs:143-146
Poisoning | Alchemy: Lesser poison -5..45 from 1 nightshade + bottle | CRAFT/DefAlchemy.cs:172-186
Poisoning | nightshade 3 gold, Lesser Poison 15 at Alchemist and Mage | SB/SBAlchemist.cs:21 and buy list; SB/SBMage.cs:36
Poisoning | starter: 2 Lesser poison potions | UOC/Engines/Character Creation/CharacterCreation.cs:1268-1273
Poisoning | PoisonRelief: 5 starter Lesser Cure potions for every new character | DOCS/Poison-Relief-Plan.md:15-17; shard-rules.json:136-140 (cure potions 5)
Poisoning | Lesser Cure cures Lesser poison 75 in 100 | DOCS/Poison-Relief-Plan.md:19 ; data in items.json potion-cure
Poisoning | skill class hard | ShardContent/data/configuration/shard-rules.json:123

## OPEN:

OPEN: No `Tinker` NPC is spawned in the generated world. DATA/Spawns/Vendors.json holds only a TinkerGuildmaster at 1422,1654 (BaseGuildmaster.IsActiveVendor is false), and Vendors.json is a Britain-only file, so SBTinker (the only list that sells Tinker's Tools, as the TinkersTools class) is not reachable. README.md:35, BackpackWardVendor.Sells (typeof(Tinker)) and the Welcome guide's trainer list ("Tinker: Tinkering") name Tinkers. The Tinkering text therefore says nothing about buying Tinker's Tools or about who trains Tinkering; it only says to keep a spare set and that Tinkering makes the tools.
OPEN: The generated craft tables list recipes that the T2A menus never offer: Blacksmith dragon scale armor (5 pieces); Tailoring Bolt of Cloth, Oil Cloth, bone armor (5) and Orc Helm; Tinkering Skillet, Flour Sifter, Fletcher's Tools, Scribe's Pen, Mapmaker's Pen, Bola Ball, Bola, four faction traps and the trap removal kit. Each page carries one sentence naming them (Blacksmith, Tailoring, Tinkering). If the generator is changed to hide recipes the menu lacks, delete those three sentences.
OPEN: The Tailoring menu accepts only Leather or Hides as a leather material (TailoringMenu.cs:337) and never sets LastResourceIndex, so Spined, Horned and Barbed leather cannot be used and their +10/+13/+16 armor rating is unreachable by crafting, although Hides of those kinds can still be carved (BaseCreature.cs:2092-2123) and Smith BODs can ask for them (SmallSmithBOD.cs:106-108). The page says the menu works with ordinary cloth, leather and hides only. Owner question: intended?
OPEN: Oil cloth cannot remove poison from a weapon here (corrosion disabled, OilCloth.cs:69-83); Alpha-3-Player-Skill-Audit.md SK-005 describes oil-cloth cleanup as a Publish 5 feature. The Poisoning page says the poison only goes as the charges are used. Confirm.
OPEN: Corpse carving doubles feathers, wool and hides in Felucca at every expansion (BaseCreature.cs:2027-2034), while SK-012 made mining and lumber single yield before AoS. The text does not mention the doubling. Owner question: intended?
OPEN: Tinkering jewelry consumes the whole stack of gems you target (BaseJewel.cs:186-209, code comment says "The entire targeted gem stack is consumed"). The page warns the player to split off one gem. Confirm this is intended.
OPEN: Cooking: the Cook NPCs sell Skillets, Rolling Pins and Flour Sifters that open nothing, and a starter cook's flour sack and pitcher have no use (Part B of the cooking restore is unbuilt). The page says so plainly. Eggs, pies and mixes exist as CookableFood but nothing in the world produces them, so the page does not list them.
OPEN: The Ward craft sentence on the Tinkering page is gated on TheftProtection only; the recipe also needs `wardCraft.enabled` (a config value, not a flag), so the sentence would be wrong if that switch were turned off.
OPEN: Bulk order reward text: cliloc 1045132 says "Select a reward for your effort" but the code picks one reward at random and puts it in the pack (BaseVendor.cs:1143-1160). The page says "sometimes a reward item" and does not mention choosing.
OPEN: Cartography at base skill 0: the first map needs 10 skill, and a brand-new character has only the stat bonus (up to about 14 for Dex and Int near 100). Whether a Cartography beginner with low stats can make any map at all depends on stats and on a Mapmaker lesson; the page says a local map teaches "from about 10" and refers to the Welcome guide trainers.
OPEN: Bought and crafted tools get a random 25 to 75 charges (BaseTool.cs:29) while starter tools get a fixed 50; the pages say "between 25 and 75" for bought or made tools. Confirm that vendor tools are meant to be random.

## Coordinator decisions

1. Tinker NPC missing from the world (OPEN 1): spawn one, or change README.md:35 and the Welcome guide's trainer list.
2. Whether the generated craft tables should hide recipes the T2A menus do not offer (OPEN 2).
3. Tailoring special leather unreachable (OPEN 3) and oil cloth versus poison (OPEN 4): owner rulings.
4. The "[Welcome" tag: pages say "see Training in [Welcome" and "see Skill locks 101 in [Welcome", the same as the fighting pages.
5. Item-topic keys: every page has "items": [] because the item writers' keys were not known; the item topics that name these skills are listed automatically.
