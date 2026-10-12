# Tools, containers and paper: item-topic notes (area T, prefix t-)

Writer notes for `parts/t.items.json` (37 topics). Paths are relative to the workspace root `C:\Users\brend\Documents\Britannia Renaissance\`. Every claim line is `topic | claim | file:line`; the line was found by a script that searched the quoted code pattern, so an auditor can jump straight to it. Vendor claims also cite the Britain vendor spawn (`ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json`, the only vendor spawn in the world generation: `britainOnlySpawnerFiles` in `ShardContent/data/world-generation/alpha2b/world-generation.json`).

Facts that apply to many topics: (1) `T2ACraftSystem.Enabled` is true (`ExpansionConfiguration.cs:15`, `expansion.json` UOTD false), so crafting tools open the era item-list menus and `BaseTool.OnDoubleClick` first asks you to target the material or the tool (`BaseTool.cs`, `T2ACraftToolTarget.cs`); (2) `Core.AOS/SE/ML` are all false, so every craft entry, vendor entry or behaviour gated on them was ignored; (3) the Young player system is off shard-wide (Alpha-3-Stock-Default-Audit.md row 1), so no Young checks are described; (4) price figures are SBInfo list prices (`GetPriceScalar` adds only a town tax, none in Britain); (5) a shard flag is mentioned only in a paragraph with `requires`: HarvestAutoRepeat, ActionAutoRepeat, Alpha3StarterScissors, Alpha3StarterBag, CampingStarterKit, HotZoneTravelWarning, all true in shard-rules.json.

## Claims

t-shovel | weighs 5 stones | ModernUO/Projects/UOContent/Items/Skill Items/Harvest Tools/Shovel.cs:14
t-shovel | new shovel has 50 uses (constructor default) | ModernUO/Projects/UOContent/Items/Skill Items/Harvest Tools/Shovel.cs:10
t-shovel | double-click works from the pack or when held | ModernUO/Projects/UOContent/Items/Skill Items/Harvest Tools/BaseHarvestTool.cs:118
t-shovel | mining targets mountain and cave land tiles, range 2 | ModernUO/Projects/UOContent/Engines/Harvest/Mining.cs:96
t-shovel | a use is spent only when something is dug up (inside the success branch, after Give) | ModernUO/Projects/UOContent/Engines/Harvest/Core/HarvestSystem.cs:249
t-shovel | tool is deleted at 0 uses | ModernUO/Projects/UOContent/Engines/Harvest/Core/HarvestSystem.cs:256
t-shovel | iron ore needs skill 0; dull copper needs 65 | ModernUO/Projects/UOContent/Engines/Harvest/Mining.cs:115
t-shovel | dull copper required skill 65 | ModernUO/Projects/UOContent/Engines/Harvest/Mining.cs:117
t-shovel | cannot mine while riding | ModernUO/Projects/UOContent/Engines/Harvest/Mining.cs:302
t-shovel | harvest auto-repeat text (flag harvestAutoRepeat is true in shard-rules.json) | ShardContent/docs/Harvest-AutoRepeat-Evidence.md:14
t-shovel | cancel list (walking, casting, other skill, war mode, fighting or being hurt, new gathering target; full pack or worn tool ends it) as stated for players | ShardContent/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:274
t-shovel | Tinker craft: Shovel 40-90, 4 iron ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:256
t-shovel | the Tinkering menu lists Shovel in its Tools list | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:39
t-smith-tools | SmithHammer, Tongs and SledgeHammer all use the Blacksmithy craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/SmithHammer.cs:18
t-smith-tools | Tongs craft system Blacksmithy | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Tongs.cs:22
t-smith-tools | SledgeHammer craft system Blacksmithy | ModernUO/Projects/UOContent/Items/Skill Items/Tools/SledgeHammer.cs:16
t-smith-tools | smith hammer weighs 8 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/SmithHammer.cs:16
t-smith-tools | tongs weigh 2 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Tongs.cs:20
t-smith-tools | anvil and forge within 2 tiles | ModernUO/Projects/UOContent/Engines/Craft/DefBlacksmithy.cs:110
t-smith-tools | anvil and forge need stated for players | ShardContent/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:247
t-smith-tools | double-click the tool then target the material; menu with Repair and Smelt | ShardContent/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:247
t-smith-tools | if a tool is held it must be the one used | ModernUO/Projects/UOContent/Items/Skill Items/Tools/BaseTool.cs:128
t-smith-tools | tool-in-hand message | ModernUO/Projects/UOContent/Engines/Craft/DefBlacksmithy.cs:102
t-smith-tools | a craft attempt uses a tool use (success path) | ModernUO/Projects/UOContent/Engines/Craft/Core/CraftItem.cs:1411
t-smith-tools | a failed attempt also uses a tool use | ModernUO/Projects/UOContent/Engines/Craft/Core/CraftItem.cs:1611
t-smith-tools | new tool uses random 25..75 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/BaseTool.cs:29
t-smith-tools | exceptional tool made under UOR has 100 uses | ModernUO/Projects/UOContent/Items/Skill Items/Tools/BaseTool.cs:75
t-smith-tools | Blacksmith sells Tongs 13 and SmithHammer 21 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBBlacksmith.cs:100
t-smith-tools | Blacksmith sells Tongs 13 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBBlacksmith.cs:17
t-smith-tools | Weaponsmith sells SmithHammer 21 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBWeaponSmith.cs:23
t-smith-tools | Blacksmith and Weaponsmith are spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:869
t-smith-tools | Blacksmith is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:49
t-smith-tools | Tinker craft: Tongs 35-85, 1 ingot | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:258
t-smith-tools | Tinker craft: SmithHammer 40-90, 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:259
t-smith-tools | Tinker craft: SledgeHammer 40-90, 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:260
t-smith-tools | the Tinkering menu lists Tongs, SmithHammer, SledgeHammer | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:37
t-tinker-tools | TinkerTools weighs 1 and uses the Tinkering craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/TinkerTools.cs:22
t-tinker-tools | TinkersTools (second graphic) also Tinkering | ModernUO/Projects/UOContent/Items/Skill Items/Tools/TinkerTools.cs:26
t-tinker-tools | weight 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/TinkerTools.cs:20
t-tinker-tools | T2A menu main categories Wooden Items, Tools, Parts, Utensils, Traps, Miscellaneous, Jewelry | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:207
t-tinker-tools | menu offers only what you can make | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:265
t-tinker-tools | logs go to the Wooden Items list; ingots to the main list | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:416
t-tinker-tools | tools list: SewingKit, TinkerTools, Scissors, Tongs, saws, Hammer, SmithHammer, SledgeHammer, Shovel, Lockpick | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:35
t-tinker-tools | misc list: keys, key ring, spyglass, lantern, sextant, clocks | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:66
t-tinker-tools | make-last by targeting the tool | ShardContent/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:246
t-tinker-tools | Tinker craft: TinkerTools 10-60, 2 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:249
t-tinker-tools | tools have 25-75 uses and each attempt uses one | ModernUO/Projects/UOContent/Items/Skill Items/Tools/BaseTool.cs:29
t-carpenter-tools | Saw uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Saw.cs:22
t-carpenter-tools | DovetailSaw uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/DovetailSaw.cs:22
t-carpenter-tools | Hammer uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Hammer.cs:21
t-carpenter-tools | Nails uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Nails.cs:22
t-carpenter-tools | DrawKnife uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/DrawKnife.cs:21
t-carpenter-tools | Froe uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Froe.cs:21
t-carpenter-tools | Inshave uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Inshave.cs:21
t-carpenter-tools | Scorp uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/Scorp.cs:21
t-carpenter-tools | JointingPlane uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/JointingPlane.cs:22
t-carpenter-tools | MouldingPlane uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/MouldingPlane.cs:22
t-carpenter-tools | SmoothingPlane uses the Carpentry craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/SmoothingPlane.cs:22
t-carpenter-tools | T2A carpentry menu offers its categories (furniture, containers, weapons=staves and shield, instruments, misc, add-ons) | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:13
t-carpenter-tools | carpentry takes logs or boards as the pre-target | ModernUO/Projects/UOContent/Engines/Craft/T2A/T2ACraftSystem.cs:66
t-carpenter-tools | weapons list is ShepherdsCrook, QuarterStaff, GnarledStaff, WoodenShield | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:38
t-carpenter-tools | add-on list includes beds | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:55
t-carpenter-tools | Carpenter sells Saw 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBCarpenter.cs:24
t-carpenter-tools | Carpenter sells Hammer 17 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBCarpenter.cs:25
t-carpenter-tools | Carpenter sells DovetailSaw 12 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBCarpenter.cs:23
t-carpenter-tools | Carpenter sells Nails 3 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBCarpenter.cs:16
t-carpenter-tools | Carpenter sells DrawKnife, Froe, Scorp, Inshave at 10 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBCarpenter.cs:22
t-carpenter-tools | Carpenter sells planes 10-11 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBCarpenter.cs:26
t-carpenter-tools | a Carpenter is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:893
t-carpenter-tools | Tinker craft: Saw 30-80 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:253
t-carpenter-tools | Tinker craft: DovetailSaw 30-80 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:254
t-carpenter-tools | Tinker craft: Hammer 30-80 1 ingot | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:257
t-carpenter-tools | Tinker craft: DrawKnife, Froe, Inshave, Scorp 30-80 2 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:261
t-carpenter-tools | Tinker craft: Scorp 30-80 | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:248
t-carpenter-tools | Tinker craft: planes 0-50 from 4 logs | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:232
t-carpenter-tools | Tinkering menu: planes in the Wooden Items list; Hammer, saws, DrawKnife, Froe, Inshave, Scorp in Tools | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:36
t-carpenter-tools | wood list has the three planes | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:29
t-fletcher-tools | FletcherTools uses the Bowcraft craft system | ModernUO/Projects/UOContent/Items/Skill Items/Tools/FletcherTools.cs:22
t-fletcher-tools | weighs 2 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/FletcherTools.cs:20
t-fletcher-tools | pre-targets: logs, boards, feathers, shafts | ModernUO/Projects/UOContent/Engines/Craft/T2A/T2ACraftSystem.cs:54
t-fletcher-tools | menu items: kindling, shafts, arrows, bolts, bow, crossbow, heavy crossbow | ModernUO/Projects/UOContent/Engines/Craft/T2A/BowFletchingMenu.cs:18
t-fletcher-tools | Bowyer sells FletcherTools 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBBowyer.cs:16
t-fletcher-tools | a Bowyer is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:498
t-fletcher-tools | FletcherTools is not in the Tinkering menu tool list (so no Tinker can make it here) | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:33
t-sewing-kit | SewingKit uses the Tailoring craft system and weighs 2 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/SewingKit.cs:21
t-sewing-kit | weight 2 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/SewingKit.cs:19
t-sewing-kit | tailoring asks for cloth, leather or hides | ModernUO/Projects/UOContent/Engines/Craft/T2A/TailoringMenu.cs:318
t-sewing-kit | Tailor sells SewingKit 3 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBTailor.cs:16
t-sewing-kit | a Tailor is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:464
t-sewing-kit | Tinker craft: SewingKit 10-70, 2 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:252
t-scissors | weighs 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Misc/Scissors.cs:20
t-scissors | target range 2 | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Misc/Scissors.cs:46
t-scissors | cloth is cut into bandages, 1 per cloth | ModernUO/Projects/UOContent/Items/Resources/Tailor/Cloth.cs:40
t-scissors | ScissorHelper takes the whole stack | ModernUO/Projects/Server/Items/Item.cs:4374
t-scissors | bolt of cloth gives 50 cloth | ModernUO/Projects/UOContent/Items/Resources/Tailor/BoltOfCloth.cs:41
t-scissors | hides give leather | ModernUO/Projects/UOContent/Items/Resources/Tailor/Hides.cs:103
t-scissors | clothing must be in the pack and is cut back into cloth | ModernUO/Projects/UOContent/Items/Clothing/BaseClothing.cs:238
t-scissors | scissors give a refusal when nothing can be made | ModernUO/Projects/UOContent/Items/Clothing/BaseClothing.cs:248
t-scissors | Tailor sells Scissors 11 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBTailor.cs:17
t-scissors | Weaver sells Scissors 11 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBWeaver.cs:33
t-scissors | Weaver spawned | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:469
t-scissors | Tinker craft: Scissors 5-55, 2 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:246
t-scissors | starter scissors: newbied, nontransferable; kept through every death (superseded ruling) | ShardContent/docs/Alpha-3-Starter-Scissors-Readiness.md:3
t-scissors | starter scissors issued at creation, flag alpha3StarterScissors true | ShardContent/src/BritanniaRenaissance.Content/StarterScissors.cs:68
t-mapmakers-pen | pen uses Cartography craft system, weighs 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/MapmakersPen.cs:22
t-mapmakers-pen | weight 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/MapmakersPen.cs:20
t-mapmakers-pen | with the T2A menus on, Cartography does not require a tool | ModernUO/Projects/UOContent/Engines/Craft/DefCartography.cs:24
t-mapmakers-pen | the Cartography skill opens the map menu with no tool | ModernUO/Projects/UOContent/Skills/Cartography.cs:22
t-mapmakers-pen | T2A menus are on by default unless UOTD (expansion.json: UOTD false) | ModernUO/Projects/UOContent/Configuration/ExpansionConfiguration.cs:15
t-mapmakers-pen | expansion UOTD false | ShardContent/data/configuration/expansion.json:9
t-mapmakers-pen | pre-target a blank map; otherwise asked to target one | ModernUO/Projects/UOContent/Engines/Craft/T2A/T2ACraftSystem.cs:84
t-mapmakers-pen | Mapmaker sells pen 8 and blank map 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMapmaker.cs:17
t-mapmakers-pen | blank map 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMapmaker.cs:16
t-mapmakers-pen | a Mapmaker is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:1251
t-mapmakers-pen | MapmakersPen is not in the Tinkering menu tool list | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:33
t-scribes-pen | pen uses Inscription craft system, weighs 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/ScribesPen.cs:22
t-scribes-pen | weight 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tools/ScribesPen.cs:20
t-scribes-pen | Inscription does not require a tool with T2A menus | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:43
t-scribes-pen | the Inscribe skill with T2A menus asks to target a book or scroll | ModernUO/Projects/UOContent/Skills/Inscribe.cs:25
t-scribes-pen | a blank scroll in the pack opens the Inscription menu | ModernUO/Projects/UOContent/Skills/Inscribe.cs:110
t-scribes-pen | menu asks 'Which circle of spells?' with Runebook entry first | ModernUO/Projects/UOContent/Engines/Craft/T2A/InscriptionMenu.cs:75
t-scribes-pen | you must have the spell in your spellbook | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:66
t-scribes-pen | each scroll uses its reagents, a blank scroll and mana | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:204
t-scribes-pen | Scribe sells pen 8, blank scroll 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBScribe.cs:16
t-scribes-pen | Scribe blank scroll 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBScribe.cs:17
t-scribes-pen | Mage sells pen 8 and blank scroll 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMage.cs:23
t-scribes-pen | a Scribe is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:440
t-scribes-pen | ScribesPen is not in the Tinkering menu tool list | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:33
t-fishing-pole | weighs 8 | ModernUO/Projects/UOContent/Items/Skill Items/Fishing/FishingPole.cs:14
t-fishing-pole | FishingPole is a plain Item: it has no uses, so it cannot wear out | ModernUO/Projects/UOContent/Items/Skill Items/Fishing/FishingPole.cs:9
t-fishing-pole | fishing range 4 | ModernUO/Projects/UOContent/Engines/Harvest/Fishing.cs:83
t-fishing-pole | special finds table includes TreasureMap at skill 90 | ModernUO/Projects/UOContent/Engines/Harvest/Fishing.cs:17
t-fishing-pole | fishing repeats under harvestAutoRepeat (mining, lumberjacking and fishing) | ShardContent/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:273
t-fishing-pole | Fisherman sells FishingPole 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBFisherman.cs:23
t-fishing-pole | a Fisherman is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:218
t-fishing-pole | Carpentry: FishingPole 68.4-93.4, 5 logs; Tailoring 40-45 and 5 cloth (non-AoS entry) | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:311
t-fishing-pole | fishing pole needs Tailoring 40 and 5 cloth | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:312
t-fishing-pole | the Carpentry menu lists FishingPole in its Misc list | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:49
t-lockpick | stackable | ModernUO/Projects/UOContent/Items/Skill Items/Thief/LockPick.cs:45
t-lockpick | target range 1 (next to you) | ModernUO/Projects/UOContent/Items/Skill Items/Thief/LockPick.cs:86
t-lockpick | 3 second pick time | ModernUO/Projects/UOContent/Items/Skill Items/Thief/LockPick.cs:112
t-lockpick | 25 percent chance to break on a failed try | ModernUO/Projects/UOContent/Items/Skill Items/Thief/LockPick.cs:122
t-lockpick | not enough skill message 'You don't see how that lock can be manipulated' | ModernUO/Projects/UOContent/Items/Skill Items/Thief/LockPick.cs:156
t-lockpick | magic lock cannot be picked by normal means | ModernUO/Projects/UOContent/Items/Skill Items/Thief/LockPick.cs:144
t-lockpick | trap may go off on pick (TrapOnLockpick) | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:99
t-lockpick | trap goes off on open unless trap-on-lockpick | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:13
t-lockpick | lockpicking repeats for the same lock while picks remain (actionAutoRepeat true) | ShardContent/docs/Action-AutoRepeat-Evidence.md:27
t-lockpick | cancel rules of the repeat (any step, casting, another skill, war mode, fighting or being hurt) | ShardContent/docs/Action-AutoRepeat-Evidence.md:21
t-lockpick | Provisioner sells Lockpick 12 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:39
t-lockpick | a Provisioner is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:758
t-lockpick | Tinker craft: Lockpick 45-95, 1 ingot | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:263
t-lockpick | Tinkering menu lists Lockpick | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:40
t-sextant | sextant weighs 2 | ModernUO/Projects/UOContent/Items/Skill Items/Fishing/Misc/Sextant.cs:13
t-sextant | sextant shows latitude and longitude over the head | ModernUO/Projects/UOContent/Items/Skill Items/Fishing/Misc/Sextant.cs:24
t-sextant | spyglass weighs 3 | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Spyglass.cs:17
t-sextant | spyglass reports the moon phases ('You peer into the heavens, seeking the moons') | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Spyglass.cs:22
t-sextant | Tinker craft: Spyglass 60-110, 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:315
t-sextant | Tinker craft: Sextant from SextantParts | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:420
t-sextant | Tinker craft: SextantParts 30-80, 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:274
t-sextant | Tinkering menu lists Spyglass and Sextant (Miscellaneous), SextantParts (Parts) | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:68
t-clock | clock weighs 3 | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Clocks.cs:32
t-clock | 5 real seconds per Britannian minute (a day = 24 x 60 x 5 s = 2 hours) | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Clocks.cs:22
t-clock | double-click gives a general phrase then the exact time | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Clocks.cs:126
t-clock | time-of-day phrases (witching hour ... late at night) | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Clocks.cs:101
t-clock | Tinker craft: ClockRight from ClockFrame + ClockParts | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:414
t-clock | Tinker craft: ClockFrame 0-50, 6 logs | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:235
t-clock | Tinker craft: ClockParts from iron ingots 25-75 | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:271
t-bandage | weighs 0.1 and stacks | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:25
t-bandage | range is 1 tile before AoS (Range = AOS ? 2 : 1) | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:16
t-bandage | a bandage is consumed when a heal begins | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:100
t-bandage | starting a new heal stops the old one | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:535
t-bandage | must stay close or the heal fails | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:217
t-bandage | self delay 9.4 + 0.6*((120-dex)/10) seconds | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:502
t-bandage | others: 3 s at Dex 100+, 4 s at 40+, else 5 s | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:522
t-bandage | others: 5 s below Dex 40 | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:530
t-bandage | chance to bandage well is (healing + 10)/100 | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:377
t-bandage | heal amount (non-AoS): min = anatomy/5 + healing/5 + 3, max = anatomy/5 + healing/2 + 10 | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:392
t-bandage | max heal formula | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:393
t-bandage | a failed bandage heals nothing ('barely help' and no heal) | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:423
t-bandage | poisoned patient: cure only, needs Healing and Anatomy 60 | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:322
t-bandage | resurrection needs Healing and Anatomy 80 | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:240
t-bandage | on animals and monsters the primary skill is Veterinary and the secondary Animal Lore | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:179
t-bandage | secondary skill on animals is Animal Lore | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:189
t-bandage | Healer sells Bandage 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBHealer.cs:16
t-bandage | a Healer is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:1506
t-instrument | weights: harp 35 | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/Harp.cs:13
t-instrument | lap harp 10 | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/LapHarp.cs:13
t-instrument | lute 5 | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/Lute.cs:13
t-instrument | drums 4 | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/Drums.cs:13
t-instrument | tambourine 1 | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/Tambourine.cs:13
t-instrument | double-click plays (within 1 tile), sets the chosen instrument, 6 second delay | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:508
t-instrument | must be within 1 tile | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:500
t-instrument | good tune chance = Musicianship/100, and playing trains Musicianship | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:530
t-instrument | skill check on Musicianship when played | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:528
t-instrument | Peacemaking asks for an instrument | ModernUO/Projects/UOContent/Skills/Peacemaking.cs:20
t-instrument | Provocation asks for an instrument | ModernUO/Projects/UOContent/Skills/Provocation.cs:20
t-instrument | Discordance asks for an instrument | ModernUO/Projects/UOContent/Skills/Discordance.cs:22
t-instrument | remembered instrument must be in the backpack, otherwise the skill asks 'What instrument shall you play?' | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:223
t-instrument | Peacemaking consumes an instrument use | ModernUO/Projects/UOContent/Skills/Peacemaking.cs:81
t-instrument | 350-450 uses under UOR | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:55
t-instrument | 450 max | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:56
t-instrument | instrument is deleted on its last use | ModernUO/Projects/UOContent/Items/Skill Items/Musical Instruments/BaseInstrument.cs:195
t-instrument | Bard sells Drums/Tambourine/LapHarp/Lute 21 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBBard.cs:19
t-instrument | Carpenter sells Drums/Tambourine/LapHarp/Lute 21 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBCarpenter.cs:32
t-instrument | a Bard is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:295
t-instrument | Carpentry: LapHarp 63.1-88.1 20 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:404
t-instrument | Carpentry: Harp 78.9-103.9 35 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:407
t-instrument | Carpentry: Drums 57.8-82.8 20 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:410
t-instrument | Carpentry: Lute 68.4-93.4 25 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:413
t-instrument | Carpentry: Tambourine 57.8-82.8 15 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:416
t-instrument | Carpentry menu lists the instruments | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:43
t-torch | held lights use Layer.TwoHanded | ModernUO/Projects/UOContent/Items/Lights/BaseEquipableLight.cs:9
t-torch | shields use the same layer | ModernUO/Projects/UOContent/Items/Weapons/BaseWeapon.cs:1577
t-torch | torch light Circle300, candle Circle150, lantern Circle300 | ModernUO/Projects/UOContent/Items/Lights/Torch.cs:17
t-torch | candle light Circle150 | ModernUO/Projects/UOContent/Items/Lights/Candle.cs:16
t-torch | lantern light Circle300 | ModernUO/Projects/UOContent/Items/Lights/Lantern.cs:17
t-torch | torch weighs 1 and stacks | ModernUO/Projects/UOContent/Items/Lights/Torch.cs:20
t-torch | candle weighs 1 and stacks | ModernUO/Projects/UOContent/Items/Lights/Candle.cs:19
t-torch | lantern weighs 2 | ModernUO/Projects/UOContent/Items/Lights/Lantern.cs:20
t-torch | lit light is put in a hand on double-click ('You put the torch in your left hand') | ModernUO/Projects/UOContent/Items/Lights/BaseEquipableLight.cs:69
t-torch | double-click again puts it out | ModernUO/Projects/UOContent/Items/Lights/BaseLight.cs:187
t-torch | a burning light put in a container goes out | ModernUO/Projects/UOContent/Items/Lights/BaseEquipableLight.cs:102
t-torch | Burnout is false: lights never burn out | ModernUO/Projects/UOContent/Items/Lights/BaseLight.cs:9
t-torch | Provisioner sells Candle 6, Torch 8, Lantern 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:35
t-torch | Provisioner Lantern 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:36
t-torch | Provisioner Candle 6 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:34
t-torch | InnKeeper sells Torch 7 and Candle 6 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:54
t-torch | InnKeeper Candle 6 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:55
t-torch | an InnKeeper is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:551
t-torch | Tinker craft: Lantern 30-80, 2 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:316
t-lamps | double-click within 2 tiles toggles; burnt-out or protected lights do nothing | ModernUO/Projects/UOContent/Items/Lights/BaseLight.cs:178
t-lamps | only lights with an unlit graphic can be put out | ModernUO/Projects/UOContent/Items/Lights/BaseLight.cs:187
t-lamps | Tinker craft: Candelabra 55-105, 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:311
t-lamps | Tinker craft: HeatingStand 60-110, 4 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:317
t-lamps | Tinkering menu lists HeatingStand and Candelabra | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:67
t-lamps | the lights in the Britain decoration data are placed fixtures | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia__britain.cfg:143
t-backpack | every new character gets a backpack at creation | ModernUO/Projects/UOContent/Engines/Character Creation/CharacterCreation.cs:241
t-backpack | backpack weighs 3 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:250
t-backpack | default container limits 125 items and 400 stones | ModernUO/Projects/Server/Items/Container.cs:177
t-backpack | 400 stones | ModernUO/Projects/Server/Items/Container.cs:179
t-backpack | nothing in the shard overrides the limits (searched GlobalMaxItems/GlobalMaxWeight in ShardContent; none) | ModernUO/Projects/Server/Items/Container.cs:151
t-backpack | Backpack keeps the 400 default before ML | ModernUO/Projects/UOContent/Items/Containers/Container.cs:256
t-backpack | contents of nested items count towards the limits | ModernUO/Projects/Server/Items/Container.cs:247
t-backpack | carry limit 40 + 3.5 x Str (non-ML) | ModernUO/Projects/UOContent/Mobiles/PlayerMobile.cs:239
t-backpack | body weight 11 | ModernUO/Projects/Server/Mobiles/Mobile.cs:1735
t-backpack | leeway of 4 stones (stamina.stonesOverweightAllowance default 4) | ModernUO/Projects/UOContent/Misc/StaminaSystem.cs:48
t-backpack | overloaded = body + total weight above max + allowance | ModernUO/Projects/UOContent/Misc/StaminaSystem.cs:440
t-backpack | stamina loss per step, doubled when running | ModernUO/Projects/UOContent/Misc/StaminaSystem.cs:427
t-backpack | too fatigued to move when stamina reaches 0 while overweight | ModernUO/Projects/UOContent/Misc/StaminaSystem.cs:338
t-backpack | Recall refuses while overloaded | ModernUO/Projects/UOContent/Spells/Fourth/Recall.cs:77
t-backpack | Provisioner sells Backpack 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:30
t-backpack | Innkeeper sells Backpack 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBInnKeeper.cs:58
t-backpack | Tanner sells Backpack 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBTanner.cs:41
t-backpack | a Tanner is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:150
t-bags | bag weighs 2 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:337
t-bags | pouch weighs 1 and is a TrappableContainer | ModernUO/Projects/UOContent/Items/Containers/Container.cs:279
t-bags | basket weighs 1 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:389
t-bags | picnic basket weighs 2 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:378
t-bags | Bag is dyeable (IDyable) | ModernUO/Projects/UOContent/Items/Containers/Container.cs:330
t-bags | Pouch is not IDyable | ModernUO/Projects/UOContent/Items/Containers/Container.cs:279
t-bags | Magic Trap works on any trappable container | ModernUO/Projects/UOContent/Spells/Second/MagicTrap.cs:25
t-bags | bags are limited by the parent container (CheckHold walks up the parents) | ModernUO/Projects/Server/Items/Container.cs:274
t-bags | Provisioner sells Bag 6 and Pouch 6 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:32
t-bags | Provisioner sells Pouch 6 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:31
t-bags | Tanner sells Bag 6 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBTanner.cs:39
t-bags | Tanner sells Pouch 6 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBTanner.cs:40
t-bags | starter bag issued (flag alpha3StarterBag true) | ShardContent/src/BritanniaRenaissance.Content/StarterBag.cs:32
t-bags | starter bag is one ordinary stock Bag | ShardContent/src/BritanniaRenaissance.Content/StarterBag.cs:10
t-chest | wooden box weighs 4, small crate 2, medium crate 2, large crate 1, wooden chest 2 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:399
t-chest | WoodenBox weight 4 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:406
t-chest | SmallCrate weight 2 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:415
t-chest | LargeCrate weight 1 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:441
t-chest | WoodenChest weight 2 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:486
t-chest | lockable containers can be locked and trapped (LockableContainer : TrappableContainer) | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:9
t-chest | crafting checks Tinkering -5..15 to make it lockable and drops a Copper key inside | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:22
t-chest | key dropped inside the container | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:29
t-chest | a locked container cannot be opened | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:195
t-chest | a locked container cannot be filled ('It appears to be locked') | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:111
t-chest | key lock/unlock toggles with range 3 | ModernUO/Projects/UOContent/Items/Misc/Key.cs:50
t-chest | Magic Lock works on any LockableContainer that is not locked | ModernUO/Projects/UOContent/Spells/Third/MagicLock.cs:26
t-chest | Magic Lock sets the magic-lock level, which lockpicks cannot pick | ModernUO/Projects/UOContent/Spells/Third/MagicLock.cs:58
t-chest | Unlock spell opens it with enough Magery | ModernUO/Projects/UOContent/Spells/Third/Unlock.cs:66
t-chest | a key resets the magic lock level when used | ModernUO/Projects/UOContent/Items/Misc/Key.cs:201
t-chest | Magic Trap works on any TrappableContainer | ModernUO/Projects/UOContent/Spells/Second/MagicTrap.cs:25
t-chest | Tinker traps need a container with a key (KeyValue != 0) | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:618
t-chest | Tinker trap is disabled until the chest is locked | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:683
t-chest | Tinkering menu has a Traps list (dart, explosion, poison) | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:61
t-chest | Remove Trap needs Lockpicking 50 and Detect Hidden 50 | ModernUO/Projects/UOContent/Skills/RemoveTrap.cs:17
t-chest | Remove Trap needs Detect Hidden 50 | ModernUO/Projects/UOContent/Skills/RemoveTrap.cs:21
t-chest | Remove Trap works on any trappable container | ModernUO/Projects/UOContent/Skills/RemoveTrap.cs:46
t-chest | Carpentry: WoodenBox 21-46, 10 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:218
t-chest | Carpentry: SmallCrate 10-35, 8 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:219
t-chest | Carpentry: MediumCrate 31-56, 15 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:220
t-chest | Carpentry: LargeCrate 47.3-72.3, 18 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:221
t-chest | Carpentry: WoodenChest 73.6-98.6, 20 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:222
t-chest | Carpentry menu lists the containers | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:31
t-chest | Provisioner sells WoodenBox 14 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:77
t-chest | the Provisioner's box is created with the default constructor, so it has no key (KeyValue 0) | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:69
t-chest | metal boxes and chests are placed in the world decoration (dungeons, Yew) | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia___covetous.cfg:677
t-barrel | barrel weighs 25 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:360
t-barrel | keg weighs 15 | ModernUO/Projects/UOContent/Items/Containers/Container.cs:371
t-barrel | Keg and Barrel are plain containers with the default limits | ModernUO/Projects/UOContent/Items/Containers/Container.cs:364
t-barrel | Carpentry: Keg 57.8-82.8, 3 barrel staves + barrel hoops + barrel lid | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:253
t-barrel | keg also needs a barrel hoops | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:254
t-barrel | keg also needs a barrel lid | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:255
t-barrel | Carpentry menu lists Keg | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:33
t-barrel | Tinker turns a keg into a potion keg (75-100) | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:425
t-barrel | barrels placed in dungeon decoration data | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia___covetous.cfg:86
t-armoire | an immovable, not locked down container with no parent cannot be filled | ModernUO/Projects/Server/Items/Container.cs:154
t-armoire | 'That is not your container, you can't store things here' | ModernUO/Projects/Server/Items/Container.cs:297
t-armoire | armoire is a BaseContainer | ModernUO/Projects/UOContent/Items/Containers/FurnitureContainer.cs:168
t-armoire | furniture is placed in the Britain decoration data | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia__britain.cfg:251
t-armoire | Carpentry: EmptyBookcase 31.5-56.5, 25 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:223
t-armoire | Carpentry: FancyArmoire 84.2-109.2, 35 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:224
t-armoire | Carpentry: Armoire 84.2-109.2, 35 logs | ModernUO/Projects/UOContent/Engines/Craft/DefCarpentry.cs:225
t-armoire | Carpentry menu lists EmptyBookcase, FancyArmoire, Armoire | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:32
t-armoire | FullBookcase, Drawer and FancyDrawer are not in the Carpentry list | ModernUO/Projects/UOContent/Engines/Craft/T2A/CarpentryMenu.cs:29
t-key | key weighs 1 | ModernUO/Projects/UOContent/Items/Misc/Key.cs:55
t-key | a key needs to be in the pack; range 3 | ModernUO/Projects/UOContent/Items/Misc/Key.cs:126
t-key | double-click: blank key copies, numbered key unlocks | ModernUO/Projects/UOContent/Items/Misc/Key.cs:133
t-key | UseOn only works if the key values match | ModernUO/Projects/UOContent/Items/Misc/Key.cs:176
t-key | the same click locks or unlocks (toggle) | ModernUO/Projects/UOContent/Items/Misc/Key.cs:186
t-key | clicking the key renames it | ModernUO/Projects/UOContent/Items/Misc/Key.cs:264
t-key | blank key copy uses Tinkering 0-75 | ModernUO/Projects/UOContent/Items/Misc/Key.cs:313
t-key | 10 percent chance to destroy the blank on a failed copy | ModernUO/Projects/UOContent/Items/Misc/Key.cs:322
t-key | Provisioner sells Key 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:78
t-key | Tinker craft: Key 20-70, 3 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:313
t-key | Tinkering menu lists Key | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:66
t-key | crafted lockable boxes get a key inside | ModernUO/Projects/UOContent/Items/Containers/LockableContainer.cs:29
t-keyring | holds 20 keys | ModernUO/Projects/UOContent/Items/Misc/KeyRing.cs:10
t-keyring | weighs 1 | ModernUO/Projects/UOContent/Items/Misc/KeyRing.cs:21
t-keyring | only non-blank keys go on the ring | ModernUO/Projects/UOContent/Items/Misc/KeyRing.cs:33
t-keyring | ring must be in the pack when keys are dragged on | ModernUO/Projects/UOContent/Items/Misc/KeyRing.cs:27
t-keyring | double-click then target tries each key | ModernUO/Projects/UOContent/Items/Misc/KeyRing.cs:169
t-keyring | 'You do not have a key for that' | ModernUO/Projects/UOContent/Items/Misc/KeyRing.cs:177
t-keyring | click the ring to open it (keys come off) | ModernUO/Projects/UOContent/Items/Misc/KeyRing.cs:162
t-keyring | Tinker craft: KeyRing 10-60, 2 ingots | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:310
t-dyes | dye tub weighs 10 | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Dyetubs/DyeTub.cs:30
t-dyes | dyes weigh 3 | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Misc/Dyes.cs:18
t-dyes | dyes: select the dye tub to use them on; hue picker | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Misc/Dyes.cs:53
t-dyes | dyes target range 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Misc/Dyes.cs:28
t-dyes | tub: within 1 tile of the tub and of the item | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Dyetubs/DyeTub.cs:115
t-dyes | cannot dye clothing being worn | ModernUO/Projects/UOContent/Items/Skill Items/Tailor Items/Dyetubs/DyeTub.cs:121
t-dyes | clothing is dyeable | ModernUO/Projects/UOContent/Items/Clothing/BaseClothing.cs:27
t-dyes | backpack and bag are dyeable | ModernUO/Projects/UOContent/Items/Containers/Container.cs:245
t-dyes | bandage is dyeable | ModernUO/Projects/UOContent/Items/Skill Items/Misc/Bandage.cs:14
t-dyes | cloth is dyeable | ModernUO/Projects/UOContent/Items/Resources/Tailor/Cloth.cs:8
t-dyes | Tailor sells DyeTub 8 and Dyes 8 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBTailor.cs:18
t-dyes | Tailor sells Dyes 8 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBTailor.cs:19
t-dyes | Weaver sells DyeTub and Dyes 8 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBWeaver.cs:17
t-hair-dye | weighs 1 | ModernUO/Projects/UOContent/Items/Misc/HairDye.cs:16
t-hair-dye | opens a color chart; must be reachable | ModernUO/Projects/UOContent/Items/Misc/HairDye.cs:24
t-hair-dye | must be in the pack to use | ModernUO/Projects/UOContent/Items/Misc/HairDye.cs:108
t-hair-dye | sets hair and facial hair hue | ModernUO/Projects/UOContent/Items/Misc/HairDye.cs:139
t-hair-dye | the dye is used up | ModernUO/Projects/UOContent/Items/Misc/HairDye.cs:142
t-hair-dye | no hair, no use | ModernUO/Projects/UOContent/Items/Misc/HairDye.cs:120
t-hair-dye | Provisioner sells HairDye 60 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:85
t-dice | dice weigh 1 | ModernUO/Projects/UOContent/Items/Games/Dices.cs:13
t-dice | double-click within 2 tiles rolls two dice for all to see | ModernUO/Projects/UOContent/Items/Games/Dices.cs:39
t-dice | range 2 | ModernUO/Projects/UOContent/Items/Games/Dices.cs:25
t-dice | a board weighs 5 and its pieces are part of it | ModernUO/Projects/UOContent/Items/Games/BaseBoard.cs:26
t-dice | a board is a container whose pieces stay in it | ModernUO/Projects/UOContent/Items/Games/BaseBoard.cs:14
t-dice | Provisioner sells Chessboard 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:87
t-dice | CheckerBoard 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:88
t-dice | Backgammon 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:89
t-dice | Dices 2 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:95
t-bedroll | weighs 5 | ModernUO/Projects/UOContent/Items/Skill Items/Camping/Bedroll.cs:18
t-bedroll | only works when not in a container (Parent != null returns) | ModernUO/Projects/UOContent/Items/Skill Items/Camping/Bedroll.cs:22
t-bedroll | within 2 tiles | ModernUO/Projects/UOContent/Items/Skill Items/Camping/Bedroll.cs:27
t-bedroll | rolling it up in a safe camp opens the logout window | ModernUO/Projects/UOContent/Items/Skill Items/Camping/Bedroll.cs:54
t-bedroll | Continue logs you out | ModernUO/Projects/UOContent/Items/Skill Items/Camping/Bedroll.cs:115
t-bedroll | secure camp: within 7 tiles of a burning fire | ModernUO/Projects/UOContent/Items/Skill Items/Camping/Campfire.cs:44
t-bedroll | secure after 30 seconds near a fire | ModernUO/Projects/UOContent/Items/Skill Items/Camping/Campfire.cs:190
t-bedroll | 30 seconds, embers do not count: as stated to players | ShardContent/src/BritanniaRenaissance.Content/WelcomeGuide.cs:538
t-bedroll | starter kit: every new character gets a Bedroll and Kindling, newbied, loose in the pack (flag campingStarterKit true) | ShardContent/docs/Beta-2b-Camping-Evidence.md:10
t-bedroll | Provisioner sells Bedroll 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:80
t-utensils | each weighs 1 | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Utensils.cs:10
t-utensils | no double-click behaviour (the file has no OnDoubleClick) | ModernUO/Projects/UOContent/Items/Skill Items/Tinkering/Utensils.cs:97
t-utensils | Tinker craft: ForkLeft 0-50, 1 ingot | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:301
t-utensils | Tinker craft: SpoonLeft 0-50 | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:298
t-utensils | Tinker craft: KnifeLeft 0-50 | ModernUO/Projects/UOContent/Engines/Craft/DefTinkering.cs:304
t-utensils | Tinkering menu Utensils list | ModernUO/Projects/UOContent/Engines/Craft/T2A/TinkeringMenu.cs:54
t-books | open with double-click; an unwritten writable book gets title 'a book' and your name | ModernUO/Projects/UOContent/Items/Books/BaseBook.cs:238
t-books | single-click shows title, author and pages | ModernUO/Projects/UOContent/Items/Books/BaseBook.cs:231
t-books | red/brown/tan books: 20 pages by default, writable | ModernUO/Projects/UOContent/Items/Books/BaseBook.cs:57
t-books | blue book 40 pages | ModernUO/Projects/UOContent/Items/Books/BlueBook.cs:9
t-books | Inscribe copies a book: pick the source, then a writable destination | ModernUO/Projects/UOContent/Skills/Inscribe.cs:231
t-books | copy success check is Inscription 0..50 (certain at 50) | ModernUO/Projects/UOContent/Skills/Inscribe.cs:237
t-books | a destination must be writable | ModernUO/Projects/UOContent/Skills/Inscribe.cs:229
t-books | Scribe sells Brown, Tan, Blue books at 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBScribe.cs:19
t-books | Scribe sells Tan 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBScribe.cs:20
t-books | Scribe sells Blue 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBScribe.cs:21
t-books | Provisioner sells Red, Blue, Tan at 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBProvisioner.cs:73
t-books | lore books are placed in the Britain library decoration data | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia__britain.cfg:4346
t-books | lore books in dungeon (Hythloth) decoration data | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia___hythloth.cfg:1428
t-books | defined (lore) books are not writable (Intended for defined books only constructor) | ModernUO/Projects/UOContent/Items/Books/BaseBook.cs:85
t-spellbook | spellbook weighs 3, blessed, one-handed layer | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:128
t-spellbook | blessed | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:122
t-spellbook | held in the one-handed layer | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:121
t-spellbook | blessed items stay in the pack at death | ModernUO/Projects/Server/Items/Item.cs:2321
t-spellbook | 64 spells in a regular book | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:134
t-spellbook | opens only when in the backpack (not a container within) or worn | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:699
t-spellbook | a scroll dragged onto the book is consumed | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:528
t-spellbook | a spell already present is refused | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:515
t-spellbook | a spell needs a book in the pack or hand that has it ('You do not have that spell!') | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:279
t-spellbook | the book is searched in the hand and the pack only | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:450
t-spellbook | Mage sells Spellbook 18, new one empty (content 0) | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMage.cs:16
t-spellbook | default content 0 | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Spellbook.cs:116
t-spellbook | Mage sells circle 1-3 scrolls | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMage.cs:60
t-spellbook | a Mage is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:179
t-scroll | a scroll weighs 1 and stacks | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Scrolls/SpellScroll.cs:24
t-scroll | scrolls are stackable | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Scrolls/SpellScroll.cs:18
t-scroll | double-click needs the scroll in the pack | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Scrolls/SpellScroll.cs:46
t-scroll | a scroll needs no reagents | ModernUO/Projects/UOContent/Spells/Base/Spell.cs:261
t-scroll | mana table 4,6,9,11,14,20,40,50 applies to scrolls too | ModernUO/Projects/UOContent/Spells/Base/MagerySpell.cs:8
t-scroll | required Magery for non-ML: scroll uses the table two circles lower | ModernUO/Projects/UOContent/Spells/Base/MagerySpell.cs:17
t-scroll | scroll vs book index | ModernUO/Projects/UOContent/Spells/Base/MagerySpell.cs:41
t-scroll | scroll consumed only when the cast does not fizzle | ModernUO/Projects/UOContent/Spells/Base/Spell.cs:777
t-scroll | scroll Circle 1-3 sold by Mage: price 12 + circle*10 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMage.cs:75
t-scroll | scroll types are the 64 regular spells in circle order | ModernUO/Projects/UOContent/Misc/Loot.cs:192
t-scroll | scrolls drop in monster loot | ModernUO/Projects/UOContent/Misc/LootPack.cs:40
t-scroll | treasure chests hold scrolls | ModernUO/Projects/UOContent/Items/TreasureChests/TreasureChestLevel2.cs:48
t-scroll | Inscription needs the spell in the scribe's book | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:66
t-scroll | Inscription uses a blank scroll, reagents and mana per scroll | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:202
t-scroll | Hot Zone warning: Recall (scroll, spell, runebook, rune) and gates, cancel spends nothing (flag hotZoneTravelWarning true) | ShardContent/docs/Beta-2b-Camp-Travel-Plan.md:132
t-scroll | the warning is for blue (innocent) players going from outside into a Hot Zone | ShardContent/src/BritanniaRenaissance.Content/TravelWarningService.cs:54
t-blank-scroll | weighs 1 and stacks | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Misc/BlankScroll.cs:15
t-blank-scroll | stackable | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Misc/BlankScroll.cs:11
t-blank-scroll | each spell scroll uses 1 blank scroll | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:202
t-blank-scroll | Runebook: 8 blank scrolls, Recall scroll, Gate Travel scroll | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:434
t-blank-scroll | Runebook needs a Recall scroll | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:435
t-blank-scroll | Runebook needs a Gate Travel scroll | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:436
t-blank-scroll | Scribe sells BlankScroll 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBScribe.cs:17
t-blank-scroll | Mage sells BlankScroll 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMage.cs:25
t-blank-scroll | Mapmaker sells BlankScroll 12 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMapmaker.cs:18
t-recall-rune | rune weighs 1 | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Misc/RecallRune.cs:27
t-recall-rune | Mark is a sixth-circle spell and marks the rune with the caster's location | ModernUO/Projects/UOContent/Spells/Sixth/Mark.cs:22
t-recall-rune | Mark needs the rune in the backpack | ModernUO/Projects/UOContent/Spells/Sixth/Mark.cs:49
t-recall-rune | pre-AoS Mark stores the caster's location | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Misc/RecallRune.cs:132
t-recall-rune | double-click renames a marked rune | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Misc/RecallRune.cs:284
t-recall-rune | a blank rune answers 'That rune is not yet marked' | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Misc/RecallRune.cs:290
t-recall-rune | Recall is a fourth-circle spell | ModernUO/Projects/UOContent/Spells/Fourth/Recall.cs:41
t-recall-rune | Recall refuses criminals | ModernUO/Projects/UOContent/Spells/Fourth/Recall.cs:71
t-recall-rune | Recall refuses in combat | ModernUO/Projects/UOContent/Spells/Fourth/Recall.cs:75
t-recall-rune | Recall refuses when overloaded | ModernUO/Projects/UOContent/Spells/Fourth/Recall.cs:79
t-recall-rune | some places refuse marking and recall (region / travel rules) | ModernUO/Projects/UOContent/Spells/Base/SpellHelper.cs:646
t-recall-rune | Mage sells RecallRune 15 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMage.cs:29
t-recall-rune | Hot Zone warning sits in the Recall confirmation hook | ShardContent/src/BritanniaRenaissance.Content/TravelWarningService.cs:43
t-runebook | holds up to 16 runes | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:314
t-runebook | weighs 3 before SE | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:74
t-runebook | blessed | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:63
t-runebook | held in the one-handed layer before AoS | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:66
t-runebook | rune dragged on is added (must be marked) | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:332
t-runebook | recall scrolls add charges up to the limit | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:351
t-runebook | 7 second use delay | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:16
t-runebook | the gump buttons: use charge, drop rune, set default, Recall, Gate | ModernUO/Projects/UOContent/Gumps/RunebookGump.cs:269
t-runebook | use charge casts Recall with the book as the scroll (no reagents) | ModernUO/Projects/UOContent/Gumps/RunebookGump.cs:280
t-runebook | Recall targeted at a runebook goes to its default entry | ModernUO/Projects/UOContent/Spells/Targeting/RecallSpellTarget.cs:34
t-runebook | Recall button casts from your own spellbook | ModernUO/Projects/UOContent/Gumps/RunebookGump.cs:329
t-runebook | Gate button casts Gate Travel from your spellbook | ModernUO/Projects/UOContent/Gumps/RunebookGump.cs:343
t-runebook | using a charge removes a charge | ModernUO/Projects/UOContent/Spells/Fourth/Recall.cs:104
t-runebook | Inscription: Runebook 45-95, 8 blank scrolls, Recall scroll, Gate scroll | ModernUO/Projects/UOContent/Engines/Craft/DefInscription.cs:434
t-runebook | max charges at craft: min(5 + quality + Inscribe/30, 10) with quality 1 (normal) or 2 (exceptional) only, so 7 at Inscription 45 up to 10 | ModernUO/Projects/UOContent/Items/Skill Items/Magical/Runebook.cs:104
t-runebook | craft quality is 1, or 2 when exceptional (CheckSkills only ever raises it to 2) | ModernUO/Projects/UOContent/Engines/Craft/Core/CraftItem.cs:854
t-runebook | Inscription menu offers the runebook | ModernUO/Projects/UOContent/Engines/Craft/T2A/InscriptionMenu.cs:75
t-maps | maps weigh 1 | ModernUO/Projects/UOContent/Items/Maps/MapItem.cs:51
t-maps | double-click within 2 tiles opens the map | ModernUO/Projects/UOContent/Items/Maps/MapItem.cs:96
t-maps | a blank map says it is blank | ModernUO/Projects/UOContent/Items/Maps/BlankMap.cs:15
t-maps | local map area grows with Cartography and is centred on the crafter | ModernUO/Projects/UOContent/Items/Maps/LocalMap.cs:19
t-maps | city map area grows with Cartography | ModernUO/Projects/UOContent/Items/Maps/CityMap.cs:20
t-maps | sea chart area grows with Cartography | ModernUO/Projects/UOContent/Items/Maps/SeaChart.cs:20
t-maps | world map area grows with Cartography | ModernUO/Projects/UOContent/Items/Maps/WorldMap.cs:22
t-maps | Cartography: LocalMap 10-70 | ModernUO/Projects/UOContent/Engines/Craft/DefCartography.cs:91
t-maps | Cartography: CityMap 25-85 | ModernUO/Projects/UOContent/Engines/Craft/DefCartography.cs:92
t-maps | Cartography: SeaChart 35-95 | ModernUO/Projects/UOContent/Engines/Craft/DefCartography.cs:93
t-maps | Cartography: WorldMap 39.5-99.5 | ModernUO/Projects/UOContent/Engines/Craft/DefCartography.cs:94
t-maps | the Cartography skill opens the map menu | ModernUO/Projects/UOContent/Skills/Cartography.cs:22
t-maps | Mapmaker sells BlankMap 5 | ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBMapmaker.cs:16
t-bod | small deed amount 10, 15 or 20 | ModernUO/Projects/UOContent/Engines/Bulk Orders/SmallSmithBOD.cs:42
t-bod | small deeds can require exceptional quality or a material | ModernUO/Projects/UOContent/Engines/Bulk Orders/SmallBOD.cs:57
t-bod | double-click opens the deed window | ModernUO/Projects/UOContent/Engines/Bulk Orders/SmallBOD.cs:85
t-bod | deed window has a button to combine the deed with the item requested | ModernUO/Projects/UOContent/Engines/Bulk Orders/SmallBODGump.cs:63
t-bod | the item must be in your pack to be combined | ModernUO/Projects/UOContent/Engines/Bulk Orders/BODTarget.cs:20
t-bod | large deeds are combined with small deeds | ModernUO/Projects/UOContent/Engines/Bulk Orders/LargeBODGump.cs:82
t-bod | completed deed handed to the vendor gives gold, fame and maybe an item | ModernUO/Projects/UOContent/Mobiles/Vendors/BaseVendor.cs:1157
t-bod | the Blacksmith vendor issues Smith deeds to players with Blacksmithing above 0 | ModernUO/Projects/UOContent/Mobiles/Vendors/NPC/Blacksmith.cs:109
t-bod | Bulk Order Info menu entry shown to the client | ShardContent/docs/Alpha-3-Implementation-Log.md:146
t-bod | 20 percent chance of an offer after selling to the vendor | ModernUO/Projects/UOContent/Mobiles/Vendors/NPC/Blacksmith.cs:79
t-bod | an offer after selling is part of BaseVendor sell | ModernUO/Projects/UOContent/Mobiles/Vendors/BaseVendor.cs:582
t-bod | waits of 1 h, 2 h (>= 50.1) and 6 h (>= 70.1) | ModernUO/Projects/UOContent/Mobiles/Vendors/NPC/Blacksmith.cs:85
t-bod | 2 hours from Blacksmithing 50.1 | ModernUO/Projects/UOContent/Mobiles/Vendors/NPC/Blacksmith.cs:89
t-bod | 1 hour below 50.1 | ModernUO/Projects/UOContent/Mobiles/Vendors/NPC/Blacksmith.cs:93
t-bod | large deeds only from 70.1 | ModernUO/Projects/UOContent/Mobiles/Vendors/NPC/Blacksmith.cs:96
t-bod | Smith BODs ride the stock bulk-orders flag, enabled; Blacksmith BODs are an owner-approved deviation; Tailor BODs not offered | ShardContent/docs/Alpha-3-Blacksmith-BOD-Readiness.md:3
t-bod | a Blacksmith is spawned in Britain | ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json:49

## OPEN:

OPEN: No plain Tinker vendor is in the Britain spawn data (only a TinkerGuildmaster, which sells nothing: BaseGuildmaster.IsActiveVendor is false), so no shopkeeper in this world sells Tinker's tools, Shovels, Sextants, Clocks, Key rings or the other SBTinker stock. The topics for those items therefore say how to make them and quote no shop price. If a Tinker is meant to exist, the Beta 2a Ward vendor text also assumes plain Tinkers (data/world-generation/alpha2b has none).
OPEN: Spyglass prints 'Trammel : <phase>' and 'Felucca : <phase>' lines to the player (Items/Skill Items/Tinkering/Spyglass.cs, GetMoonPhase(Map.Trammel...)). The Sextant topic says only 'the phase of the moons' and does not name either facet; the visible in-game text still names the later facet. Decide whether the spyglass should be trimmed to Felucca.
OPEN: Backpack topic: types ["Backpack"] also reaches every class derived from Backpack through the base chain (the Mondain's Legacy satchels AndricSatchel, AsandosSatchel, GervisSatchel, HargroveSatchel, LowelSatchel, MuggSatchel, NibbetSatchel, SadrahSatchel, the craftsman satchels, StrongBackpack, VendorBackpack, CreatureBackpack). The text is written to stay true for a plain pack; none of them is in this world. Decide whether to leave it.
OPEN: Bags topic: types ["Bag"] also reaches the staff/supply bags derived from Bag (AlchemyBag, BagOfAllReagents, BagOfNecroReagents, BagOfNecromancerReagents, BagOfReagents, BagOfSmokeBombs, BagOfingots, SmithBag, TailorBag, ScribeBag, SalvageBag and the ML quest bags). The BagOfReagents is real in this world (a new Scribe or Alchemist is issued one by StarterCraftMaterialIssuance); the text stays true for it as a plain bag, but nothing explains its contents.
OPEN: Boxes and chests topic: types ["WoodenBox"] also reaches RewardStrongbox (a Mondain's Legacy quest class derived from WoodenBox). Not in this world.
OPEN: Dyes topic: inherits ["DyeTub"] reaches every special tub (BlackDyeTub, BlazeDyeTub, LeatherDyeTub, MetallicClothDyetub, RunebookDyeTub, FurnitureDyeTub, StatuetteDyeTub, SpecialDyeTub, WhiteClothDyeTub and the reward tubs). The text describes the plain tub; the special ones are not in this world.
OPEN: Spellbook topic: types ["Spellbook"] also reaches every book derived from Spellbook through the base chain (BookOfBushido, BookOfChivalry, BookOfNinjitsu, MysticSpellbook, NecromancerSpellbook and OssianGrimoire, SpellweavingBook, HallowedSpellbook, TomeOfEnlightenment, TomeOfLostKnowledge). None is in this world; they would show the Magery text. If that matters, they need a one-line topic of their own, which the brief said not to write.
OPEN: Runebook: the Inscription Runebook recipe is stock and un-gated (owner ruling SK-010, 2026-09-28: keep stock). The runebook did not exist in April 2000; the text describes it as it works here.
OPEN: Bulk Order Book (BulkOrderBook) is left to the general page: the Inscription recipe for it is gated on Core.AOS (DefInscription.cs 'if (Core.AOS)') and no vendor sells it, so a UOR player cannot get one. Tailor deeds (SmallTailorBOD, LargeTailorBOD) are left to the general page too: Tailors and Weavers do not issue them under UOR.
OPEN: Mortar and Pestle (already in items.json): its text says a menu asks what to make after the double-click, but with the era menus the double-click first shows a target cursor ('Target this tool to make last item, or any other target to begin crafting', BaseTool.cs OnDoubleClick). For the Alchemy menu any click works, so one clause about clicking a reagent or bottle would match the Welcome crafting page (WelcomeGuide.GettingStarted.cs:244). The new tool topics all say 'then click the material'.
OPEN: Mapmaker's pen and Scribe's pen: both topics say the pen is not needed, because DefCartography.RequiresTool and DefInscription.RequiresTool are !T2ACraftSystem.Enabled and the skills open the menu on their own (Cartography.cs:22, Inscribe.cs:25 and 110). The Cartography and Inscription skill pages should agree. The client side of 'using the skill' (the skills window button) was not verified, so the topics only say 'using the Cartography skill'.
OPEN: Fishing finds: MessageInABottle and SOS (and the shipwreck chest, special nets, big fish) are left to the general page. The Fishing pole topic mentions only treasure maps, as an example of 'something else' at high skill (Fishing.cs:17, required skill 90, deep water).
OPEN: Pickaxe and Hatchet are weapon classes owned by the W area, so the Shovel topic does not link to them and the Mining and Lumberjacking pages must cover them.
OPEN: The Lantern sells for 2 gold at the Provisioner (SBProvisioner.cs, a stock oddity), the Torch 8 and the Candle 6; the text quotes the list prices as 'about'.
OPEN: Instruments: the Harp (35 stones) is craftable (Carpentry 78.9 to 103.9) but sold by nobody; the topic lists only drums, tambourines, lap harps and lutes as sold.
OPEN: Bulk orders: the topic names the 'Bulk Order Info' menu entry; its label was seen by a real client in the Alpha 3 log (Alpha-3-Implementation-Log.md:146).
OPEN: Link limit: most topics use 3 or fewer links. t-bandage uses 4 (Healing, Veterinary, Anatomy, Scissors) and t-chest uses 4 (Carpentry, Lockpicking, Keys, Lockpicks); the instrument topic carries the four bard skills and no related topic, as the coordinator asked.

## Assigned classes left to the general page (and why)

- 24 classes, immovable world fixture (its constructor sets Movable = false): Help is only offered for a held item or a movable item on the ground (HelpService.CanOfferHelp), so a topic would never be shown. Locks, traps and lockpicking on such chests are covered by the Boxes and chests, Lockpicks and Keys topics.
  Anvil, BountyBoard, BulletinBoard, Campfire, FillableBarrel, FillableLargeCrate, FillableMetalBox, FillableMetalChest, FillableMetalGoldenChest, FillableSmallCrate, FillableWoodenBox, FillableWoodenChest, Forge, LibraryBookcase, MarkContainer, MetalGoldenPuzzleChest, MetalGoldenTreasureChest, MetalTreasureChest, StrongBoxPuzzle, TreasureChestLevel1, TreasureChestLevel2, TreasureChestLevel3, TreasureChestLevel4, WoodenTreasureChest
- 49 classes, scroll of a magic school or spell this shard does not have (Necromancy, Chivalry, Bushido, Ninjitsu, Spellweaving, Mysticism, or an AoS/SE/ML spell): not among the 64 UOR spells.
  AnimateDeadScroll, AnimatedWeaponScroll, ArcaneCircleScroll, ArcaneEmpowermentScroll, AttuneWeaponScroll, BloodOathScroll, BombardScroll, CleansingWindsScroll, CorpseSkinScroll, CurseWeaponScroll, DryadAllureScroll, EagleStrikeScroll, EnchantScroll, EssenceOfWindScroll, EtherealVoyageScroll, EvilOmenScroll, ExorcismScroll, GiftOfLifeScroll, GiftOfRenewalScroll, HailStormScroll, HealingStoneScroll, HorrificBeastScroll, ImmolatingWeaponScroll, LichFormScroll, MassSleepScroll, MindRotScroll, NatureFuryScroll, NetherBoltScroll, NetherCycloneScroll, PainSpikeScroll, PoisonStrikeScroll, PurgeMagicScroll, ReaperFormScroll, RisingColossusScroll, SleepScroll, SpellPlagueScroll, SpellTriggerScroll, StoneFormScroll, StrangleScroll, SummonFamiliarScroll, SummonFeyScroll, SummonFiendScroll, ThunderstormScroll, VampiricEmbraceScroll, VengefulSpiritScroll, WildfireScroll, WitherScroll, WordOfDeathScroll, WraithFormScroll
- 4 classes, power or stat scroll of a later expansion (champions and power scrolls are neutralised by world generation).
  PowerScroll, ScrollofAlacrity, ScrollofTranscendence, StatCapScroll
- 29 classes, container, addon or furniture of Samurai Empire, Mondain's Legacy or Treasures of Tokuno, or the AoS bag balls: the Carpentry recipes are gated on Core.SE/Core.ML and no UOR vendor or loot gives them.
  ArcaneBookshelfEastAddon, ArcaneBookshelfSouthAddon, BoilingCauldronAddon, CherryArmoire, ChestOfHeirlooms, DecorativeBox, ElegantArmoire, ElvenDresserEastAddon, ElvenDresserSouthAddon, ElvenWashBasinEastAddon, ElvenWashBasinSouthAddon, FancyElvenArmoire, FinishedWoodenChest, FountainOfLife, GildedWoodenChest, LargeBagBall, MapleArmoire, OrnateElvenChestEastAddon, OrnateElvenChestSouthAddon, OrnateWoodenChest, PlainWoodenChest, RarewoodChest, RedArmoire, SacrificialAltarAddon, ShortCabinet, SimpleElvenArmoire, SmallBagBall, TallCabinet, WoodenFootLocker
- 15 classes, holiday or promotional gift container, not sold or crafted here.
  AnimatedHeartShapedBox, EarringBoxSet, GiftBox, GiftBoxAngel, GiftBoxCube, GiftBoxCylinder, GiftBoxNeon, GiftBoxOctogon, GiftBoxRectangle, GiftForArielle, GreenStocking, HeartShapedBox, RedStocking, RedVelvetGiftBox, WinterGiftPackage2003
- 14 classes, decoration artifact, quest, system, staff or house-moving item: not something a UOR player buys, crafts or finds in normal play.
  BackpackArtifact, Basket1Artifact, Basket2Artifact, Basket3NorthArtifact, Basket3WestArtifact, Basket4Artifact, Basket5NorthArtifact, Basket5WestArtifact, Basket6Artifact, Cauldron, CommodityDeedBox, GamblingStone, PackingBox, PlagueBeastBackpack
- 28 classes, pure decoration or rare collectible with no use of its own (or a fixture such as a trash barrel): the general page is enough.
  Bucket, Cards, Cards2, Cards3, Cards4, Checkers, Checkers2, Chessmen, Chessmen2, Chessmen3, ClosedBarrel, Dressform, Easel, FishBowl, Globe, Hourglass, LockableBarrel, Lockpicks, PaintsAndBrush, PenAndInk, PlayingCards, PlayingCards2, Rope, ToolKit, TrashBarrel, TrashChest, Tub, WaterBarrel
- 3 classes, cooking tool: with the era craft menus the Cooking skill has no tool menu (T2ACraftSystem.ShowMenu has no cooking branch) and food is cooked on a heat source, so the tool does nothing here.
  FlourSifter, RollingPin, Skillet
- 8 classes, tool or kit of a later expansion (glassblowing, masonry, ninja blowgun, taxidermy, weapon engraving, the bulk-order reward shovel) or with no source in this world (the Disguise kit is sold only by Thieves, none spawned in Britain).
  Blowpipe, DisguiseKit, Fukiya, FukiyaDarts, MalletAndChisel, SturdyShovel, TaxidermyKit, WeaponEngravingTool
- 3 classes, Bulk Order Book is craftable only under Core.AOS and sold by nobody; Tailor deeds are not issued under UOR (Blacksmith deeds only).
  BulkOrderBook, LargeTailorBOD, SmallTailorBOD
- 2 classes, rare fishing find (Fishing 100): the flow (SOS, sea serpent, shipwreck chest) is long and belongs on the Fishing skill page; the stock fishing table is kept by owner ruling (Alpha-3-Stock-Default-Audit.md row 10).
  MessageInABottle, SOS
- 3 classes, MapItem is the plain base class; the Indecipherable and Weather maps are system or later-expansion maps. Treasure maps (class TreasureMap, not in the assignment file) also reach the general page.
  IndecipherableMap, MapItem, WeatherMap
- 2 classes, owned by the Alchemy chain topics already in items.json (excluded by the brief).
  MortarPestle, PotionKeg

Total left: 184 of 491 assigned (2 of them, MortarPestle and PotionKeg, belong to the Alchemy chain).

## Classes that reach a topic only through a base class

The lookup walks up each item's base chain and takes the first topic that names a type or a base, so `types` (and `inherits`) also catch every subclass. These classes are not named in any topic but fall into one. The topic text was written to stay true for the plain members. Entries tagged leak are not in this world; the coordinator should decide whether to leave them:

- t-backpack (15; leak: Mondain's Legacy satchels and special packs derived from Backpack): AndricSatchel, AsandosSatchel, BlacksmithSatchel, CarpentrySatchel, FletchingSatchel, GervisSatchel, HargroveSatchel, LowelSatchel, MuggSatchel, NibbetSatchel, SadrahSatchel, StrongBackpack, TailorSatchel, TinkerSatchel, VendorBackpack
- t-bags (15; leak: supply, staff and quest bags derived from Bag): AlchemyBag, BagOfAllReagents, BagOfNecroReagents, BagOfNecromancerReagents, BagOfReagents, BagOfSmokeBombs, BagOfTreasure, BagOfTrinkets, BagOfingots, LargeBagOfTreasure, SalvageBag, ScribeBag, SmallBagOfTrinkets, SmithBag, TailorBag
- t-bandage (1; leak: EnhancedBandage (AoS) derived from Bandage): EnhancedBandage
- t-books (67; intended): ArmsAndWeaponsPrimer, BirdsOfBritannia, BlackthornWelcomeBook, BlueBook, BoldStranger, BritannianFlora, BrownBook, BurningOfTrinsic, CallToAnarchy, ChildrenTalesVol2, DeceitDungeonOfHorror, DimensionalTravel, DiversityOfOurLand, DrakovsJournal, EthicalHedonism, FropozJournal, GrammarOfOrcish, GrimmochJournal1, GrimmochJournal11, GrimmochJournal14, GrimmochJournal17, GrimmochJournal2, GrimmochJournal23, GrimmochJournal3, GrimmochJournal6, GrimmochJournal7, GuideToGuilds, KaburJournal, LifeOfATravellingMinstrel, LysanderNotebook1, LysanderNotebook11, LysanderNotebook2, LysanderNotebook3, LysanderNotebook7, LysanderNotebook8, MajorTradeAssociation, MyStory, NewAquariumBook, QuestOfVirtues, RankingsOfTrades, RedBook, RedLeatherBook, RegardingLlamas, SongOfSamlethe, TaleOfThreeTribes, TalesOfVesperVol1, TalkingToWisps, TamingDragons, TanBook, TavarasJournal1, TavarasJournal11, TavarasJournal14, TavarasJournal16, TavarasJournal16b, TavarasJournal17, TavarasJournal19, TavarasJournal2, TavarasJournal3, TavarasJournal6, TavarasJournal7, TavarasJournal8, TavarasJournal9, TheFight, TranslatedGargoyleJournal, TreatiseOnAlchemy, VirtueBook, WildGirlOfTheForest
- t-chest (1; leak: quest strongbox derived from WoodenBox): RewardStrongbox
- t-clock (4; leak: clock variants (ClockLeft and ClockRight are the real ones; HolidayTimepiece and WristWatch are not obtainable here)): ClockLeft, ClockRight, HolidayTimepiece, WristWatch
- t-dyes (12; leak: special and reward dye tubs derived from DyeTub): BlackDyeTub, BlazeDyeTub, FurnitureDyeTub, LeatherDyeTub, MetallicClothDyetub, MetallicLeatherDyeTub, RewardBlackDyeTub, RunebookDyeTub, SpecialDyeTub, StatuetteDyeTub, WhiteClothDyeTub, WhiteLeatherDyeTub
- t-fishing-pole (1; leak: artifact pole derived from FishingPole): CaptainBlackheartsFishingPole
- t-instrument (10; leak: reached by inherits BaseInstrument (Drums, Harp, LapHarp, Lute, Tambourine, TambourineTassel are intended; BambooFlute and the three artifact instruments are not in this world)): BambooFlute, Drums, FluteOfRenewal, GwennosHarp, Harp, IolosLute, LapHarp, Lute, Tambourine, TambourineTassel
- t-lamps (20; intended): Brazier, BrazierTall, Candelabra, CandelabraStand, CandleLarge, CandleLong, CandleShort, CandleSkull, HangingLantern, HeatingStand, LampPost1, LampPost2, LampPost3, PaperLantern, RedHangingLantern, RoundPaperLantern, ShojiLantern, WallSconce, WallTorch, WhiteHangingLantern
- t-smith-tools (2; leak: artifact hammers derived from SmithHammer): AndrosGratitude, HammerOfHephaestus
- t-spellbook (10; leak: spellbooks of later schools derived from Spellbook): BookOfBushido, BookOfChivalry, BookOfNinjitsu, HallowedSpellbook, MysticSpellbook, NecromancerSpellbook, OssianGrimoire, SpellweavingBook, TomeOfEnlightenment, TomeOfLostKnowledge
- t-tinker-tools (1; leak: quest toolbox derived from TinkerTools): AmeliasToolbox
- t-torch (5; leak: reached by inherits BaseEquipableLight (Torch, Candle, Lantern are intended; LanternOfSouls and TwilightLantern are artifacts)): Candle, Lantern, LanternOfSouls, Torch, TwilightLantern

## Counts

- Assigned classes in T.tsv: 491. Topics written: 37.
- Named in a topic's types or inherits: 143. Reaching a topic only through a base class: 164 (87 intended: lore books and fixed lamps; 77 reach a topic written for the plain class).
- Left to the general page: 184 (including the 2 Alchemy-chain classes).
- Check: 143 + 164 + 184 = 491.
