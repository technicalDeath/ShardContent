# Help text notes: Miscellaneous area (key prefix m-)

Output: `parts\m.items.json` (17 topics). Checked: JSON parses; ASCII only; no angle brackets except `<BR>`; every title is 18 characters or fewer; every `types`/`inherits` name is a class or base class in `assign\M.tsv`; no class name is claimed twice; links per topic are at most 4; every `requires` is a property of `DeferredFeatureFlags`.

Path legend for the claim lines (all relative to the workspace root):
- `U/` = `ModernUO/Projects/UOContent/`
- `S/` = `ShardContent/src/BritanniaRenaissance.Content/`
- `D/` = `ModernUO/Distribution/`
- `V` = `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json` (the generated Greater Britain vendor spawners)
- `SC/` = `ShardContent/`
- `UOData/speech.mul` = the client speech file: keyword id to spoken phrase (the English entries were read from it; the server code only names the keyword number).

Era gates relied on everywhere: `Core.AOS` false and `Core.SE`/`Core.ML` false under `Expansion.UOR` (`D/Configuration/expansion.json`: AOS, SE, ML all false). Housing flag `housingGeography` is false in `SC/data/configuration/shard-rules.json:198` and is not mentioned in any text.

World presence of the vendors named in the texts: `D/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json` (Greater Britain only, `britainOnlySpawnerFiles`): Jeweler :78 and :1092, TavernKeeper :324 :382 :961 :995, InnKeeper :551 :1169 :1352, Banker :671 :1323, Provisioner :758 :1477, Carpenter :893, Architect :898, RealEstateBroker :903, Shipwright :1246. No plain "Tinker" entry exists in that file or in `TownsPeople.json` (see OPEN 1).

## Topics and what each reaches

| key | title | reaches |
| --- | --- | --- |
| m-house-deed | House deeds | `inherits HouseDeed` (20 classes) |
| m-house-sizes | House sizes | no class: reached only by a link from m-house-deed (the validator allows a topic reached only by links, `HelpCatalog.cs:300`) |
| m-addon-deed | Add-on deeds | `inherits BaseAddonDeed, BaseAddonContainerDeed` (156 classes; most are later-era deeds that do not exist here, the text is generic and true for all) |
| m-forge-anvil-deed | Forge and anvil | 5 exact deed types |
| m-training-dummy | Training dummies | 2 deed types |
| m-pickpocket-dip | Pickpocket dips | 2 deed types |
| m-decorator | Decorator tool | `InteriorDecorator` |
| m-furniture | Furniture | 13 carpenter furniture types |
| m-decoration | Statues and busts | 9 statue and bust types |
| m-boat-deed | Ship deeds | `inherits BaseBoatDeed` (6 classes) |
| m-guild-deed | Guild deed | `GuildDeed` |
| m-vendor-contract | Vendor contract | `ContractOfEmployment`, `BarkeepContract` |
| m-commodity-deed | Commodity deed | `CommodityDeed` |
| m-ward | Backpack ward | `BackpackWard` |
| m-shrunken-pet | Shrunken pet | `ShrunkenPet` |
| m-fire-horn | Fire horn | `FireHorn` |
| m-crystals | Message crystals | `BroadcastCrystal`, `ReceiverCrystal` |

## Claim lines (topic | claim | source)

### m-house-deed
- m-house-deed | The deed is a deed item (art 0x14F0 = 5360) | U/Multis/HouseDeed.cs:18
- m-house-deed | Double-click needs the deed in the pack | U/Multis/HouseDeed.cs:34-37
- m-house-deed | Only one house per account, all characters counted (GMs exempt) | U/Multis/HouseDeed.cs:38-41, :91; U/Multis/Houses/BaseHouse.cs:3541-3554; SC/docs/Alpha-3-Stock-Default-Audit.md:22 (owner kept the cap, 2026-09-30)
- m-house-deed | Click the ground to place; the house is built, the deed is used up | U/Multis/HouseDeed.cs:49 (target), :154-155 (MoveToWorld and Delete)
- m-house-deed | A refused spot tells you and keeps the deed (messages only, no Delete on those branches) | U/Multis/HouseDeed.cs:173-205
- m-house-deed | Two keys, one in the pack and one in the bank box (non-AOS rules) | U/Multis/Houses/BaseHouse.cs:1988-2014; every house constructor calls `CreateKeys(owner)` (U/Multis/Houses/Houses.cs:14, 49, 79 ...)
- m-house-deed | Not in towns | U/Regions/GuardedRegion.cs:151 (`AllowHousing` false); U/Regions/TownRegion.cs:5 (TownRegion : GuardedRegion); U/Multis/Houses/HousePlacement.cs:156
- m-house-deed | Not in dungeons | U/Regions/DungeonRegion.cs:25
- m-house-deed | Not on roads | U/Multis/Houses/HousePlacement.cs:54-65, :296-301, :371-376
- m-house-deed | Not in the Lost Lands (x 5120 and over, y 2304 and over) | U/Multis/Houses/HousePlacement.cs:91; U/Spells/Base/SpellHelper.cs:690-695
- m-house-deed | Not over water, rocks, trees or uneven ground | U/Multis/Houses/HousePlacement.cs:129-135 (rules), :237 (BadLand), :254 (BadStatic), :282 (NoSurface, foundation must rest flat), :368 (impassable land at the border)
- m-house-deed | No other house within one tile | U/Multis/Houses/HousePlacement.cs:438-442
- m-house-deed | The 5 tiles south of a house stay clear of other houses (deeds are south facing) | U/Multis/Houses/HousePlacement.cs:51, :444-448, :456-460; U/Multis/HouseDeed.cs:26
- m-house-deed | Double-click the sign opens the house window | U/Multis/Houses/HouseSign.cs:155-175
- m-house-deed | Window pages INFO, FRIENDS, OPTIONS | U/Gumps/Houses/HouseGump.cs:285-291
- m-house-deed | INFO shows the owner and the locked-down counts | U/Gumps/Houses/HouseGump.cs:303-315
- m-house-deed | FRIENDS: co-owners, friends, bans | U/Gumps/Houses/HouseGump.cs:331-361
- m-house-deed | OPTIONS: transfer, demolish and get deed back, change locks, public or private | U/Gumps/Houses/HouseGump.cs:370-396
- m-house-deed | Demolishing puts the deed in the bank box (non-AOS branch) | U/Gumps/Houses/ConfirmDemolishHouseGump.cs:118-130
- m-house-deed | What was inside is left on the ground, free to take | U/Multis/Houses/BaseHouse.cs:3371-3416 (`OnAfterDelete`: lock-downs released and made movable)
- m-house-deed | Say "I wish to lock this down" then click an item; "I wish to release this" undoes it; co-owner or owner only, inside the house | U/Regions/HouseRegion.cs:226-236, :293-313; `UOData/speech.mul` ids 0x23 "i wish to lock this down" and 0x24 "i wish to release this"
- m-house-deed | A house falls after 5 days without a refresh | U/Multis/Houses/BaseHouse.cs:108 (DecayPeriod 5 days), :144-146 (non-AOS is ManualRefresh), :567-577 (collapsed at 100%), :551-557 and :1303-1306 (decay tick every minute), :627-636 and :659-670 (collapsed house is deleted); D/Configuration/modernuo.json:48 (`houseDecay.enable` True)
- m-house-deed | A fallen house gives no deed back | U/Multis/Houses/BaseHouse.cs:659-670 (Decay_Sandbox: KillVendors, Delete; no GetDeed call)
- m-house-deed | Owner or friend refreshes by double-clicking the sign or opening a door | U/Multis/Houses/HouseSign.cs:109-121; U/Items/Construction/Doors/HouseDoors.cs:122-128
- m-house-deed | Click the sign to read how worn the house is | U/Multis/Houses/HouseSign.cs:88-106
- m-house-deed | The architect sells the deeds | U/Mobiles/Vendors/NPC/Architect.cs:20-26 (SBHouseDeed added when not AOS); U/Mobiles/Vendors/SBInfo/SBHouseDeed.cs:19-84; world: V:898 (Architect, Britain)
- m-house-deed | A real estate broker (Britain) pays 80 percent into the bank box when the deed is handed to him | U/Mobiles/Vendors/NPC/RealEstateBroker.cs:69-86 (OnDragDrop, Banker.Deposit), :125-152 (`AOS.Scale(price, 80)`); world: V:903
- m-house-deed | Shopkeepers will not buy it (Newbied deed, vendor guard) | U/Multis/HouseDeed.cs:20; U/Mobiles/Vendors/GenericSell.cs:37-40, :153
- m-house-deed | housingGeography is off, nothing said about premium or districts | S/HousingGeographyPolicy.cs:24-28 (returns 0 premium when flag false); SC/data/configuration/shard-rules.json:198

### m-house-sizes
- m-house-sizes | The 19 deeds the architect sells and their prices (small house six looks 43,800; brick 144,500; two-story wood-and-plaster 192,400; tower 433,200; small stone keep 665,200; castle 1,022,800; large patio 152,800; marble patio 192,000; small tower 88,500; log cabin 97,800; sandstone patio 90,900; villa 136,500; stone workshop 60,600; marble workshop 63,000) | U/Mobiles/Vendors/SBInfo/SBHouseDeed.cs:19-84
- m-house-sizes | Footprints (small 7 x 7; workshops 7 x 7; small tower 8 x 7; sandstone 12 x 8; log cabin 8 x 13; villa 11 x 11; brick 14 x 14; large patio and marble 15 x 14; two-story about 14 x 14; tower 16 x 14 with a 4 x 7 wing each side; keep about 24 x 24 (bounding box of its rectangles); castle 31 x 31) | the `AreaArray` rectangles in U/Multis/Houses/Houses.cs:10, 45, 75-76, 109-111, 142-145, 167, 193, 224, 249, 273, 300, 325, 353-354
- m-house-sizes | Lock-downs and secures per house (425/3, 580/4, 850/6, 1,100/8, 1,370/10, 2,119/15, 2,625/18, 4,076/28) | U/Multis/Houses/Houses.cs:12, 47, 77, 113, 147, 169, 195, 226, 251, 275, 302, 327, 356; limits applied at U/Multis/Houses/BaseHouse.cs:2195 (lock-downs), :2463 (secures)
- m-house-sizes | An item inside a container counts toward the lock-down limit | U/Multis/Houses/BaseHouse.cs:2168 (`amt = 1 + item.TotalItems`)
- m-house-sizes | Broker takes a deed back for about 80 percent | U/Mobiles/Vendors/NPC/RealEstateBroker.cs:152
- m-house-sizes | The stone-and-plaster two-story deed (`TwoStoryStonePlasterHouseDeed`) is not sold, so it is not listed | absent from U/Mobiles/Vendors/SBInfo/SBHouseDeed.cs

### m-addon-deed
- m-addon-deed | Deed item, double-click from the pack, then click a spot | U/Items/Addons/BaseAddonDeed.cs:14, :42-52; U/Items/Addons/BaseAddonContainerDeed.cs:60-70
- m-addon-deed | Only the house owner can place; messages for not in a house you own, does not fit, near a door, needs a wall | U/Items/Addons/BaseAddon.cs:198-203 (`house.IsOwner(from)`), :186 (door within 1 tile), :167 (NoWall); U/Items/Addons/BaseAddonDeed.cs:93-110 (messages)
- m-addon-deed | The deed is used up | U/Items/Addons/BaseAddonDeed.cs:112; U/Items/Addons/BaseAddonContainerDeed.cs:145
- m-addon-deed | Getting the deed back: use an axe on the fixture, within 3 tiles, owner only | U/Engines/Harvest/Core/HarvestTarget.cs:52-54 (Lumberjacking tool on IChoppable); U/Items/Addons/AddonComponent.cs:133-143 (range 3); U/Items/Addons/BaseAddon.cs:84-125 (owner check, deed added to the pack)
- m-addon-deed | Carpenters make them in the Add-Ons part of the menu (legacy item-list menu is on under UOR) | U/Engines/Craft/T2A/CarpentryMenu.cs:53-76 (AddonTypes), :193; U/Configuration/ExpansionConfiguration.cs:15 (`t2aCraftMenus` defaults to `!Core.UOTD`); no override in D/Configuration/modernuo.json
- m-addon-deed | A carpenter-made deed is newbied, so shopkeepers will not buy it, but it can be traded | U/Items/Addons/BaseAddonDeed.cs:16-19 (Newbied when not AOS); U/Mobiles/Vendors/GenericSell.cs:37-40, :153; trade is open (comment at GenericSell.cs:34-36)
- m-addon-deed | (gated Furnishers) The Furnisher sells furnishings from 1,850 to 80,000 gold, in the Counselor's Guild hall in Britain; big pieces are deeds; tradeable and lootable | SC/data/configuration/furnishers.json (minimum price 1850 at :1892, ceiling 80000 at "priceCeiling"); SC/docs/Furnisher-Evidence.md:11 and the README line at :66; flag `furnishers` true at SC/data/configuration/shard-rules.json

### m-forge-anvil-deed
- m-forge-anvil-deed | A smith must be within 2 tiles of an anvil and a forge | U/Engines/Craft/DefBlacksmithy.cs:110-117 (`CheckAnvilAndForge(from, 2, ...)`, message 1044267 "You must be near an anvil and a forge to smith items.")
- m-forge-anvil-deed | The placed pieces are anvil and forge components | U/Items/Addons/AnvilEastAddon.cs:11 (graphic 0xFAF = 4015, counted as an anvil at U/Engines/Craft/DefBlacksmithy.cs:46); U/Items/Addons/SmallForgeAddon.cs:11 (ForgeComponent)
- m-forge-anvil-deed | Small forge 5 wood + 75 ingots, Carpentry 73.6, Blacksmith 75 | U/Engines/Craft/DefCarpentry.cs:512-514
- m-forge-anvil-deed | Large forge (east/south) 5 wood + 100 ingots, Carpentry 78.9, Blacksmith 80 | U/Engines/Craft/DefCarpentry.cs:515-520
- m-forge-anvil-deed | Anvil (east/south) 5 wood + 150 ingots, Carpentry 73.6, Blacksmith 75 | U/Engines/Craft/DefCarpentry.cs:521-526
- m-forge-anvil-deed | East/South are facings | the class names and the label comment `anvil (east)` at U/Items/Addons/AnvilEastAddon.cs:26
- m-forge-anvil-deed | Chop to get the deed back; deed not sold to shopkeepers | see m-addon-deed

### m-training-dummy
- m-training-dummy | Double-click the placed dummy with a melee weapon; trains the weapon's skill | U/Items/Addons/TrainingDummies.cs:62-68 (`CheckSkill(weapon.Skill, MinSkill, MaxSkill)`), :70-99
- m-training-dummy | Only while the skill is below 25 (MinSkill -25, MaxSkill +25; refuses at Base >= MaxSkill) | U/Items/Addons/TrainingDummies.cs:23-24, :86
- m-training-dummy | Bare hands train Wrestling (the default weapon is Fists) | `Mobile.DefaultWeapon = new Fists()` at U/Items/Weapons/Fists.cs:42; ModernUO/Projects/Server/Mobiles/Mobile.cs:1622-1640 (Weapon falls back to the default)
- m-training-dummy | Within reach of the weapon; not ranged; not mounted; wait for the swing | U/Items/Addons/TrainingDummies.cs:74-95; timer 0.25 s then 2.75 s at :114
- m-training-dummy | Carpentry 68.4, 55 wood, 60 cloth, Tailoring 50 (east and south) | U/Engines/Craft/DefCarpentry.cs:529-534

### m-pickpocket-dip
- m-pickpocket-dip | Double-click within 1 tile; a search uses the Stealing check; refuses when Stealing is 25 or more | U/Items/Addons/PickpocketDips.cs:61, :77, :85
- m-pickpocket-dip | A bump swings it about 3 seconds and you wait; no use mounted | U/Items/Addons/PickpocketDips.cs:68-72, :90-93, :110
- m-pickpocket-dip | Carpentry 73.6, 65 wood, 60 cloth, Tailoring 50 | U/Engines/Craft/DefCarpentry.cs:535-540

### m-decorator
- m-decorator | Art 0xFC1 = 4033, blessed | U/Items/Misc/InteriorDecorator.cs:23-25
- m-decorator | You must be in a house where you are an owner or co-owner | U/Items/Misc/InteriorDecorator.cs:71-79
- m-decorator | A window offers Turn, Up, Down; the target stays up for the next click; Esc closes the window | U/Items/Misc/InteriorDecorator.cs:102-118 (window), :253 (target re-armed), :258-261 (cancel closes window)
- m-decorator | Turn spins pieces with another facing (chairs, tables are `[Flippable]`) | U/Items/Misc/InteriorDecorator.cs:264-306 (Turn uses the FlippableAttribute); U/Items/Construction/Chairs/Chairs.cs:5-6, :18-19, :31-32; U/Items/Construction/Tables/Tables.cs:30, :43, :56
- m-decorator | Up and Down move one step, up to 15 above the floor | U/Items/Misc/InteriorDecorator.cs:307-334
- m-decorator | A loose item must be locked down or secured first | U/Items/Misc/InteriorDecorator.cs:219 (message 1042271 "That is not locked down.")
- m-decorator | Inside the house, at most 100 stones | U/Items/Misc/InteriorDecorator.cs:213-228
- m-decorator | Sold by the architect for 10,001 and bought for 5,000 | U/Mobiles/Vendors/SBInfo/SBArchitect.cs:16, :28; world: V:898
- m-decorator | "Blessed, so you keep it if you die" | U/Items/Misc/InteriorDecorator.cs:25; blessed items are kept (ModernUO/Projects/Server/Items/Item.cs:81-100 LootType doc: Blessed is unstealable and unlootable)

### m-furniture
- m-furniture | The 13 pieces are in the carpentry Furniture list | U/Engines/Craft/T2A/CarpentryMenu.cs:21-27
- m-furniture | Wood needed and Carpentry minimums (footstool 11, stool 11, bamboo and wooden chair 21, cushioned chairs 42.1, bench 52.6, wooden throne 52.6, throne 73.6, nightstand 42.1, writing table 63.1, yew-wood table 63.1, large table 84.2) | U/Engines/Craft/DefCarpentry.cs:174-186
- m-furniture | Weights: chairs 20, wooden throne 15, stool 10, footstool 6, bench 6, throne 1, tables 1, nightstand 1, writing table 1 | U/Items/Construction/Chairs/Chairs.cs:15, 28, 41, 54; Stools.cs:14, :26; Benchs.cs:15; Thrones.cs:15, :28; Tables/Tables.cs:14 (and the other tables, same file); Tables/WritingTable.cs:15
- m-furniture | Turning works on every piece except the two stools (no `[Flippable]` on Stool, FootStool) | U/Items/Construction/Chairs/Stools.cs:5-8, :17-20
- m-furniture | A carpenter buys most pieces for 6 to 24 gold (Throne 24, WoodenThrone 6, Stool 6, FootStool 6, cushioned 12 and 10, chair 8, bamboo 6, bench 6, large table 10, yew table 10, nightstand 7; no entry for the writing table) | U/Mobiles/Vendors/SBInfo/SBCarpenter.cs:44-57
- m-furniture | Lock-down wording | see m-house-deed
- m-furniture | (gated Furnishers) Furnisher sells furnishings 1,850 to 80,000; a one-piece furnishing is locked down like any furniture | SC/docs/Furnisher-Evidence.md:66 (README rules line)

### m-decoration
- m-decoration | Statues and busts weigh 10 stones; graphics 0x139A etc. (art 0x139A = 5018) | U/Items/Construction/Misc/Statues.cs:6-117
- m-decoration | They are decoration only | no OnDoubleClick in U/Items/Construction/Misc/Statues.cs
- m-decoration | A ratman mage carries one 2 times in 100 | U/Mobiles/Monsters/Humanoid/Magic/RatmanMage.cs:45-48; U/Misc/Loot.cs:185-190 (statue types); U/Mobiles/BaseCreature.cs:5700-5703; world: D/Data/BritanniaRenaissance/Alpha2b/Spawns/Ice.json:514, :716
- m-decoration | Shopkeepers do not buy them | no SBInfo lists any of the nine types (reference scan of U/Mobiles/Vendors/SBInfo)

### m-boat-deed
- m-boat-deed | Deed art 0x14F2 = 5362; deed is newbied | U/Multis/Boats/BaseBoatDeed.cs:20, :22-25
- m-boat-deed | Double-click needs the deed in the pack, then click water | U/Multis/Boats/BaseBoatDeed.cs:35-60
- m-boat-deed | Cannot launch from a house or from another ship; not in a dungeon; not in a house region | U/Multis/Boats/BaseBoatDeed.cs:92-98, :153-162
- m-boat-deed | Needs open water with room | U/Multis/Boats/BaseBoat.cs:1416-1470 (`CanFit`, water test)
- m-boat-deed | Deed used up, ship appears anchored, two keys (pack and bank box) that lock and unlock the planks | U/Multis/Boats/BaseBoatDeed.cs:105-125; U/Multis/Boats/BaseBoat.cs:331-365 ("a ship key", pack and bank box); key value set on both planks BaseBoatDeed.cs:116-124
- m-boat-deed | Anyone aboard can give orders | U/Multis/Boats/BaseBoat.cs:404 (`CanCommand` returns true), :1008 (`Contains(from)`)
- m-boat-deed | Words: forward, back, left, right, stop, turn left, turn right, turn around, raise anchor, drop anchor, one forward | keyword numbers at U/Multis/Boats/BaseBoat.cs:1033 (0x45), :1073 (0x4F), :1128 (0x5A), :1159 (0x65), :1164-1165 (0x4A, 0x66), :1170 (0x67), :1185 (0x6A), :1190 (0x6B); phrases from `UOData/speech.mul` ids 0x45 "forward", 0x46 "back", 0x47 "left", 0x48 "right", 0x4F "stop", 0x5A "one forward", 0x65 "turn right", 0x66 "turn left", 0x67 "turn around", 0x6A "drop anchor"/"lower anchor", 0x6B "raise anchor"
- m-boat-deed | Anchor must be up or the tiller man refuses | U/Multis/Boats/BaseBoat.cs:497-503 region (`StartMove` refuses when Anchored), message 501419 at :939
- m-boat-deed | Back, left, right are drift moves (slide without turning) | U/Multis/Boats/BaseBoat.cs:71-78 (Left = West etc.), :504 (drift is anything not forward)
- m-boat-deed | Plank opens by double-click, closes after about 5 seconds, locked planks need the key | U/Multis/Boats/Plank.cs:125, :330 (CloseTimer 5 s), :296-319 (locked messages); U/Items/Misc/Key.cs:186 and :242 (key toggles the lock of an ILockable target; ship key range 10 at BaseBoat.cs:338)
- m-boat-deed | The hold opens only from on board while still | U/Multis/Boats/Hold.cs:54-71
- m-boat-deed | Docking: anchor down, key in pack, hold empty, nothing on deck, stand off the ship, double-click the tiller man; the ship becomes an item | U/Multis/Boats/BaseBoat.cs:590-640 (CheckDryDock), :673-725 (EndDryDock gives `DockedBoat` to the pack); U/Multis/Boats/TillerMan.cs:74-83
- m-boat-deed | Sinks after about 9 days without a plank opened or closed | U/Multis/Boats/BaseBoat.cs:57 (9 days), :415-419 (Refresh), :422 (ShouldDecay), :2177-2203 (DecayTimer deletes the boat); Refresh callers: U/Multis/Boats/Plank.cs:125, :255
- m-boat-deed | Shipwright (Britain) sells all six: small 10,177, medium 11,552, large 12,927, plain and dragon | U/Mobiles/Vendors/SBInfo/SBShipwright.cs:16-21; world: V:1246
- m-boat-deed | Provisioner sells the small plain deed | U/Mobiles/Vendors/SBInfo/SBProvisioner.cs:83; world: V:758, :1477
- m-boat-deed | Shopkeepers will not buy the deed (newbied) | U/Multis/Boats/BaseBoatDeed.cs:22-25; GenericSell.cs:37-40; and the Shipwright has no sell list (SBShipwright.cs:25-27)
- m-boat-deed | Boat placement feature flag is on | D/Configuration/FeatureFlags/flags.json (`boat_placement` true)

### m-guild-deed
- m-guild-deed | Old guild system is in force (`NewGuildSystem` = `Core.SE`, false) | U/Misc/Guild.cs:575; SC/docs/Guild-Chat-Plan.md:3, :14 (owner kept the old system)
- m-guild-deed | Needs the deed in the pack, no current guild, inside a house you own, one guildstone per house | U/Items/Guilds/GuildDeed.cs:20-52
- m-guild-deed | Name prompt, 40 letters at most | U/Items/Guilds/GuildDeed.cs:53, :98-102
- m-guild-deed | Deed used up, Guildmaster, guildstone placed where you stand | U/Items/Guilds/GuildDeed.cs:105-120
- m-guild-deed | Cannot demolish a house with a guildstone | U/Gumps/Houses/ConfirmDemolishHouseGump.cs:72-76; U/Gumps/Houses/HouseGump.cs:650-656
- m-guild-deed | Double-click the guildstone for the guild window (members, within 2 tiles) | U/Items/Guilds/Guildstone.cs:152-200
- m-guild-deed | "Recruit someone into the guild", the roster, the charter, resign | U/Gumps/Guilds/GuildGump.cs:80-100
- m-guild-deed | Guildmaster's recruit joins by using the guildstone; a member's recruit waits as a candidate | U/Gumps/Guilds/RecruitTarget.cs:81-89; U/Items/Guilds/Guildstone.cs:174-190
- m-guild-deed | (gated GuildChat) `[g` and the backslash key, every online guildmate, logged | S/GuildChatService.cs:20 (logged notice), :67 (command), :190 (sends to the guild); S/WelcomeGuide.cs:592; flag true at SC/data/configuration/shard-rules.json:217
- m-guild-deed | Provisioner sells the deed for 12,450 gold | U/Mobiles/Vendors/SBInfo/SBProvisioner.cs:103-106; world: V:758, :1477

### m-vendor-contract
- m-vendor-contract | Player vendors are enabled | D/Configuration/FeatureFlags/flags.json:66 (`player_vendors` true); U/Multis/Houses/BaseHouse.cs:95 (`NewVendorSystem` = `Core.AOS`, false: the old system applies)
- m-vendor-contract | Must be in a house; friend of the household (old system); house must be public | U/Items/Misc/PlayerVendorDeed.cs:44-61
- m-vendor-contract | An owner or co-owner counts as a friend | U/Multis/Houses/BaseHouse.cs:3612
- m-vendor-contract | The merchant appears where you stand | U/Items/Misc/PlayerVendorDeed.cs:79-86
- m-vendor-contract | Starts with 1,000 gold for wages | U/Mobiles/Vendors/PlayerVendor.cs:79
- m-vendor-contract | Drop items one at a time, owner only, asks price and description | U/Mobiles/Vendors/PlayerVendor.cs:519-546, :545 ("only the shop owner"), :636-640 (prompt)
- m-vendor-contract | Refuses newbied or bound items | U/Mobiles/Vendors/PlayerVendor.cs:549-553; U/Mobiles/Vendors/GenericSell.cs:32-48
- m-vendor-contract | "vendor buy", "vendor browse", "vendor collect", "vendor status", "vendor dismiss" | U/Mobiles/Vendors/PlayerVendor.cs:943, :957, :983, :992, :1005; `UOData/speech.mul` ids 0x3C "*vendor buy*", 0x3D "vendor browse", 0x3E "vendor collect", 0x3F "vendor status", 0x40 "vendor dismiss"
- m-vendor-contract | Sale gold is kept for the owner and collected into the bank box | U/Gumps/PlayerVendorGumps.cs:121 (HoldGold += price); U/Mobiles/Vendors/PlayerVendor.cs:788-835 (CollectGold, GiveGold, Banker.DepositUpTo at :806)
- m-vendor-contract | Dismissal needs an empty pack and pays the gold out | U/Mobiles/Vendors/PlayerVendor.cs:843-865
- m-vendor-contract | Pay each game day: 20 + 1 per 500 of listed prices above 500; the game day is 2 hours of real time | U/Mobiles/Vendors/PlayerVendor.cs:125-134 (ChargePerDay), :1051-1058 (interval); U/Items/Skill Items/Tinkering/Clocks.cs:22-23 (5 s per game minute, 24 x 5 = 120 minutes)
- m-vendor-contract | Pay comes from the wage fund first, then sales gold; dropping gold tops up the fund | U/Mobiles/Vendors/PlayerVendor.cs:1067-1100; :573-583
- m-vendor-contract | If he cannot be paid he quits, leaving a pack on the floor | U/Mobiles/Vendors/PlayerVendor.cs:1080 (Destroy), :381-387 (pack with goods and gold moved to the world)
- m-vendor-contract | Barkeep: owner only, 2 per house | U/Items/Deeds/BarkeepContract.cs:43; U/Multis/Houses/BaseHouse.cs:27, :791
- m-vendor-contract | Barkeep sells drinks, tells news, answers set keywords, gives the set tip for 50 gold or less | U/Mobiles/Vendors/SBInfo/SBPlayerBarkeeper.cs:16-25; U/Mobiles/Vendors/Barkeeper/PlayerBarkeeper.cs:239, :276, :297
- m-vendor-contract | Prices: contract 1,252 at bankers, innkeepers, tavern keepers; barkeep contract 1,252 at innkeepers and tavern keepers | U/Mobiles/Vendors/SBInfo/SBBanker.cs:17; SBInnKeeper.cs:63-64; SBTavernKeeper.cs:53-54; world: V:671, 1323, 551, 1169, 1352, 324, 382, 961, 995

### m-commodity-deed
- m-commodity-deed | Deed art 0x14F0; shows unfilled or the commodity and amount | U/Items/Deeds/CommodityDeed.cs:20, :70-90
- m-commodity-deed | Both deed and resource in the bank box; double-click the blank deed and target the stack | U/Items/Deeds/CommodityDeed.cs:107-112, :130-147, :204-212
- m-commodity-deed | Cashing: filled deed in the bank box, double-click, the commodity is dropped in the box, deed deleted | U/Items/Deeds/CommodityDeed.cs:116-126
- m-commodity-deed | What it holds: logs, boards, ingots, hides, leather, scales, cloth, bolts of cloth, bones, arrows, bolts, feathers, shafts, reagents, sand | `ICommodity.IsDeedable => true` in U/Items/Skill Items/Lumberjack/Log.cs:47, Carpenter Items/Board.cs:53, Resources/Blacksmithing/Ingots.cs:43 and Scales.cs:32, Resources/Tailor/Hides.cs:42, Leathers.cs:42, Cloth.cs:19, BoltOfCloth.cs:20, Bone.cs:18, Resources/Arrows/Arrow.cs:17, Bolt.cs:17, Feather.cs:17, Shaft.cs:17, Resources/Reagents/BaseReagent.cs:17, Skill Items/Specialized/Sand.cs:16
- m-commodity-deed | Potions, scrolls and bottles do not go in | `IsDeedable => Core.ML` (false) in U/Items/Skill Items/Magical/Potions/BasePotion.cs:65, Scrolls/SpellScroll.cs:27, Misc/Bottle.cs:18
- m-commodity-deed | One stack of one kind | U/Items/Deeds/CommodityDeed.cs:37-44 (single `Commodity` item)
- m-commodity-deed | A banker sells a blank deed for 5 gold | U/Mobiles/Vendors/SBInfo/SBBanker.cs:24; world: V:671, :1323

### m-ward
- m-ward | Art 0x1F14 = 7956 | S/BackpackWard.cs:15
- m-ward | One-line description | S/BackpackWardState.cs:196
- m-ward | Found in the backpack or a bag in it, not in a bank, house, ground or pet's pack | S/BackpackWardService.cs:90-150 (equipped backpack, nested containers); S/WelcomeGuide.cs:330-331
- m-ward | No skill, no switching on | S/WelcomeGuide.cs:330-331
- m-ward | Caught thief: success plus notice by victim or by the ward; turns criminal; blocked on every character (by account) until the ward is used up | S/BackpackWardService.cs:168-210 (OnTheftResolved), :217-231 (CriminalAction), :151-161 (IsBlocked by account name); S/BackpackWardState.cs:104-114; S/WelcomeGuide.cs:341-343
- m-ward | The thief keeps what was taken | S/WelcomeGuide.cs:341
- m-ward | Extra detection 25, 50, then always, counted per thief | S/TheftProtectionService.cs:197-204; S/BackpackWardService.cs:199-207
- m-ward | 30 minutes with no theft attempt: a Primed ward resets, an Activated ward is consumed | S/BackpackWardState.cs:32, :116-124; S/BackpackWardService.cs:66-92
- m-ward | Double-click shows where it stands and the quiet minutes left | S/BackpackWard.cs:58; S/BackpackWardState.cs:200-236; S/BackpackWardService.cs:236-269
- m-ward | (gated HotZones) Does nothing in a Hot Zone | S/TheftProtectionService.cs:253-256; S/BackpackWardState.cs:234
- m-ward | Every new character gets a starter ward bound to the character: cannot be traded, sold or stolen, kept on death | S/TheftProtectionService.cs:45-73; S/BackpackWard.cs:36 (Nontransferable), :53 (Newbied); S/BackpackWardState.cs:195; S/TheftProtectionService.cs:246-251 (a ward cannot be stolen)
- m-ward | A tinker can make one from 20 iron ingots, Tinkering 45 or more, in the Miscellaneous list | SC/data/configuration/shard-rules.json:61-66; S/BackpackWardCraft.cs:11-12 (header), :58-70; S/WelcomeGuide.cs:316-320
- m-ward | A ward you make can be traded until it starts watching a thief | S/WelcomeGuide.cs:324; S/BackpackWard.cs:99-110 (blessed to the character only while tracking)
- m-ward | The flags are true | SC/data/configuration/shard-rules.json:194 (theftProtection), :196 (hotZones)
- m-ward | NOT said: that Tinker vendors sell it (OPEN 1)

### m-shrunken-pet
- m-shrunken-pet | Item art 0x1870 = 6256 and the name "a shrunken <pet>" | U/Misc/ShrinkTable.cs:11; S/ShrunkenPet.cs:44
- m-shrunken-pet | (gated PetRestrictions) A pet in a dungeon is shrunk into the pack, with a notice | S/PetRestrictionService.cs:262-286
- m-shrunken-pet | One mount may be ridden in and left standing, fights monsters, never players | S/PetRestrictionService.cs:149-150; S/WelcomeGuide.GettingStarted.cs:307-316
- m-shrunken-pet | Double-click outside a dungeon with a free follower slot to bring it back | S/ShrunkenPet.cs:81-140, :108 (MayRelease), :120 (follower message)
- m-shrunken-pet | In a dungeon only a mount, not riding, no other mount standing | S/PetRestrictionService.cs:149-167
- m-shrunken-pet | Cannot be traded, sold or stolen; only the owner lifts it from the floor | S/ShrunkenPet.cs:38, :42; S/TheftProtectionService.cs:246-251 (Nontransferable cannot be stolen)
- m-shrunken-pet | Destroying the figure deletes the pet | S/ShrunkenPet.cs:143-151
- m-shrunken-pet | The floor case happens when the pack is full | S/PetRestrictionService.cs:291-296

### m-fire-horn
- m-fire-horn | Art 0xFC7 = 4039 | U/Items/Skill Items/Misc/FireHorn.cs:13
- m-fire-horn | 15 sulfurous ash per blast (non-AOS) | U/Items/Skill Items/Misc/FireHorn.cs:38, :85
- m-fire-horn | Target within 2 tiles; blast area 2 tiles | U/Items/Skill Items/Misc/FireHorn.cs:200 (target range), :101 (area)
- m-fire-horn | Musicianship chance 500 + (skill tenths - 775) x 2, over 1000: 50 percent at 77.5, 95 at 100 | U/Items/Skill Items/Misc/FireHorn.cs:72-76
- m-fire-horn | A failed try squeaks, no ash used; the wait starts first | U/Items/Skill Items/Misc/FireHorn.cs:63-83 (wait begins at :63, failure returns before the ash is consumed at :85)
- m-fire-horn | 12 seconds between tries (non-AOS) | U/Items/Skill Items/Misc/FireHorn.cs:64
- m-fire-horn | Targets are those you may attack | U/Items/Skill Items/Misc/FireHorn.cs:101-110
- m-fire-horn | Damage total = Provocation + Discordance/5 + Peacemaking/5 in tenths; a third against players; max = total x 2 / 30, min = 70 percent of max; shared between targets; at 100/100/100: 65 to 93 vs monsters, 21 to 31 vs players | U/Items/Skill Items/Misc/FireHorn.cs:147-166
- m-fire-horn | A target that resists takes half | U/Items/Skill Items/Misc/FireHorn.cs:177-181
- m-fire-horn | 16 in 100 chance of burning up (non-AOS) | U/Items/Skill Items/Misc/FireHorn.cs:188-193
- m-fire-horn | Not sold; found as a 1 percent replacement of weapons in loot-pack loot | U/Misc/LootPack.cs:696-700; no SBInfo or craft entry references `FireHorn` (reference scan)

### m-crystals
- m-crystals | Art 0x1ED0 = 7888 | U/Items/Misc/CommunicationCrystals.cs:62
- m-crystals | Both start off (graphic 0x1ED0 is the inactive one) | U/Items/Misc/CommunicationCrystals.cs:62 and :74 (broadcast crystal starts as graphic 0x1ED0, active only as 0x1ECD), :289 and :300 (receiver starts as 0x1ED0, active only as 0x1ED1)
- m-crystals | Link: double-click broadcast crystal within 2 tiles, click a receiver; up to 10 receivers; a receiver has one sender | U/Items/Misc/CommunicationCrystals.cs:163-175, :211-232
- m-crystals | Click the crystal itself to switch it on or off (broadcast needs charges) | U/Items/Misc/CommunicationCrystals.cs:189-205 (broadcast), :375-387 (receiver)
- m-crystals | Click yourself to unlink | U/Items/Misc/CommunicationCrystals.cs:237-245 (all receivers), :393-405 (one receiver)
- m-crystals | The broadcast crystal listens only when on, linked, and on the ground or carried by someone | U/Items/Misc/CommunicationCrystals.cs:118-126
- m-crystals | One charge per receiver per line; it switches off when dry | U/Items/Misc/CommunicationCrystals.cs:128-146
- m-crystals | Recharge amounts: citrine 500, amber 500, tourmaline 750, emerald/sapphire/amethyst 1,000, star sapphire 1,250, diamond 2,000; gem consumed; maximum 2,000 | U/Items/Misc/CommunicationCrystals.cs:12-21, :49, :249-278
- m-crystals | Receiver repeats "<name> says <text>" | U/Items/Misc/CommunicationCrystals.cs:330-352
- m-crystals | Jewelers sell 500/1000/2000 charges for 68/131/256 and a receiver for 6 | U/Mobiles/Vendors/SBInfo/SBJewel.cs:21-57; world: V:78, :1092

## Gated paragraphs (all names are `DeferredFeatureFlags` properties)
- m-addon-deed, m-furniture: `Furnishers` (true)
- m-guild-deed: `GuildChat` (true)
- m-ward: `TheftProtection` (true) on all but the first two lines; `HotZones` (true) on the Hot Zone line
- m-shrunken-pet: `PetRestrictions` (true) on everything but the first lines

## OPEN (not in the text; for the coordinator or the owner)

1. **No Tinker vendor in the generated world.** `BackpackWardVendor.Sells` is exactly `typeof(Tinker)` (S/BackpackWardVendor.cs:66), but `D/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json` (and `TownsPeople.json`) contain no `Tinker`, only `TinkerGuildmaster` (V:102). Stock Britain has no Tinker spawn either (`D/Data/Spawns/shared/felucca/Vendors.json` has Tinkers only in other towns). So "Tinker vendors sell wards for 2,000 gold" and the 110 gold buy-back (the Welcome guide, `S/WelcomeGuide.cs:314-325`) may not be reachable in the world as generated. I left vendor sale out of m-ward and kept only the craft route (wardCraft: enabled, 45 skill, 20 ingots). Worth checking on the live dev world before the help goes on.
2. **Aquarium items are on sale in Britain.** `SBFisherman` sells `AquariumNorthDeed`/`AquariumEastDeed` (250,002 gold), `AquariumFishNet`, `AquariumFood`, `FishBowl`, `VacationWafer` unconditionally (U/Mobiles/Vendors/SBInfo/SBFisherman.cs:19-27) and no shard hook filters them (grep of `S/` finds no Aquarium rule). The aquarium is a much later feature than UOR. The deeds fall under m-addon-deed's generic text; the other aquarium items are left to the general page. Owner decision: gate the Fisherman's list?
3. **Communication crystals on sale at the Jewelers** (U/Mobiles/Vendors/SBInfo/SBJewel.cs:21-57). Written up as m-crystals because the world sells them; if the owner decides they are not UOR, drop the topic with the vendor lines.
4. **Dragon ships on sale at the Shipwright** (SBShipwright.cs:17, 19, 21; the Provisioner sells only the plain small one). Written as "plain or dragon-prow". The era of the dragon-prow ship graphics was not verified.
5. **Player vendors, the Interior Decorator and the Architect's stock** are stock behaviour with the UOR gates applied; the era of each was not checked against an outside source (only the code was read). They are in the world and worth a topic either way.
6. **Real estate broker price table differs from the Architect's for two deeds** (marble house with patio: broker table 192,800 vs sold at 192,000; small marble workshop: 60,300 vs 63,000; U/Mobiles/Vendors/NPC/RealEstateBroker.cs:142 and :148 vs SBHouseDeed.cs:64 and :79). The text says "about 80 percent", which holds for both.
7. **One house per account** is stock and the owner kept it on 2026-09-30 "for now" (SC/docs/Alpha-3-Stock-Default-Audit.md:22, to be revisited under Beta 2b house zoning). m-house-deed and m-house-sizes state it; they need a pass when that ruling changes.
8. **Orc loot `BolaBall` has no use.** Orcs and savages carry it (U/Mobiles/Monsters/Humanoid/Melee/Orc.cs:68 and others) but the legacy Tinkering menu has no Bola or BolaBall recipe (U/Engines/Craft/T2A/TinkeringMenu.cs lists no Bola), so it is a dead drop. Left to the general page.
9. **House decay needs a visit every 5 days** (`houseDecay.enable` True); the text says so. If the owner wants a more lenient rule that is a config change and the text must follow.
10. **The `\` key in the guild-chat paragraph**: the JSON holds a single backslash (written `\\`). The window draws HTML; a lone backslash is plain text there (the Welcome guide draws the same character, S/WelcomeGuide.cs:592).

## Decisions for the coordinator
- `m-house-sizes` has no `types` or `inherits` (a link-only topic). The validator allows it (`HelpCatalog.cs:300`); if the loader or the window code assumes at least one class, fold its list into m-house-deed.
- `m-addon-deed` claims two bases (`BaseAddonDeed`, `BaseAddonContainerDeed`); the shard's own `FurnishingDeed` derives from `BaseAddonDeed` and so reaches this topic (and its Furnisher paragraph) although it is not in my assignment file.
- `Item` itself is in `M.tsv` but is claimed by `other-item`; I did not touch it.

## Assigned classes left to the general page, and why

Totals: 950 assigned; 223 reach a topic of this file (156 of them only through the generic add-on deed topic, because the stock add-on deed family is large and mostly later-era); 727 reach the general page. `Item` is claimed by `other-item`. Every left class is listed once below, in the group that gives the reason.

**A. Fixed in the world or part of a building, never picked up (so no Help menu): boats and camps (multis), dungeon traps, moongates and gates, shrine ankhs, add-on components, pillars, puzzle switches** (42)

AnkhNorth, AnkhWest, ArcheryButte, BallotBox, BankerCamp, BrigandCamp, ConfirmationMoongate, DartBoard, DisappearingRaiseSwitch, FireColumnTrap, FlameSpurtTrap, GasTrap, GiantSpikeTrap, HealerCamp, KhaldunPitTeleporter, LargeBoat, LargeDragonBoat, LargeForgeEast, LargeForgeWest, LeverPuzzleController, LizardmenCamp, MageCamp, MediumBoat, MediumDragonBoat, Moongate, MushroomTrap, Obelisk, OrcCamp, PublicMoongate, RaiseSwitch, RatCamp, ResGate, SHTeleComponent, SawTrap, SerpentPillar, SmallBoat, SmallDragonBoat, SpikeTrap, StarRoomGate, StoneFaceTrap, StoneFaceTrapNoDamage, TrainingDummy

**B. Staff, system, spawner and test objects, and items no vendor, craft or loot table makes** (27)

AlchemyStone, Blocker, ChampionSpawn, DarkSource, DisguisePersistenceTimers, DungeonChampionSpawn, EffectController, GauntletSpawner, HouseRaffleDeed, HouseRaffleStone, IngotStone, LLChampionSpawn, LOSBlocker, LightSource, NameChangeDeed, NewPlayerTicket, RegStone, ScribeStone, ShardPoller, SmithStone, SwarmOfFlies, SwitchItem, TailorStone, TimeoutGoal, TreasureChestDirt, VirtualCheck, WayPoint

**C. Factions and Ethics (not part of this world: the faction state is empty and ethics.enable is False)** (22)

Blight, BloodRose, ClarityPotion, EthicsPersistence, FactionExplosionTrap, FactionExplosionTrapDeed, FactionGasTrap, FactionGasTrapDeed, FactionPersistence, FactionSawTrap, FactionSawTrapDeed, FactionSpikeTrap, FactionSpikeTrapDeed, FactionStone, FactionTrapRemovalKit, GemOfEmpowerment, JoinStone, StormsEye, StrongholdMonolith, TownMonolith, TownStone, UrnOfAscension

**D. Later-expansion content (not reachable under the UOR gates: Mondain's Legacy, Samurai Empire / Tokuno, Stygian Abyss and later quests, dungeons, artifacts, mounts, pigments, talismans, plants, glassblowing, aquarium)** (202)

ABauble, APersonalLetterAddressedToAhie, AbscessTail, AcidProofRope, AlchemistsBandage, AncientUrn, AquariumFishNet, AquariumFood, AquariumMessage, ArcaneFocus, ArcaneGem, ArtifactLargeVase, ArtifactVase, BagOfSending, BallOfSummoning, BarkFragment, BasinOfCrystalClearWater, BatteredBucket, BedlamTeleporter, Bleach, BlueSoulstone, BridesLetter, CandelabraOfSouls, CapturedEssence, ChargerOfTheFallen, ChiselsNorth, ChiselsWest, CoilsFang, CompletedTuitionReimbursementForm, Corruption, CrateForSledge, CrystallineFragments, DirtPatch, DiseasedBark, DragonBardingDeed, DragonFlameSectBadge, DreadHornMane, DreadSpiderSilk, EmptyBentoBox, EnchantedSextant, EnchantedSwitch, EternallyCorruptTree, EtherealBeetle, EtherealCuSidhe, EtherealHiryu, EtherealHorse, EtherealKirin, EtherealLlama, EtherealOstard, EtherealReptalon, EtherealRidgeback, EtherealSwampDragon, EtherealUnicorn, EvilIdolSkull, ExecutionersCap, EyeOfTheTravesty, FabledFishingNet, FancyWindChimes, FishBones, FragmentOfAMap, FragmentOfAMapDelivery, FriendOfTheLibraryToken, FriendsOfTheLibraryApplication, Futon, GamanHorns, GhostShipAnchor, GlassblowingBook, GlobOfMonstreousInterredGrizzle, GoldBricks, GreenTeaBasket, GreenThorns, GrizzledBones, GrizzledMareStatuette, GrizzledSkullCollection, GrobusFur, Guillotine, HollowPrism, HonorableSwords, HornOfTheDreadhorn, IcyHeart, IslandStatue, JeweledFiligree, KirinBrains, LardOfParoxysmus, LargeVase, LavaTile, LesserPigmentsOfTokuno, LuckyDagger, LuminescentFungi, MangledHeadOfDreadhorn, MasonryBook, MelisandesHairDye, MetalPigmentsOfTokuno, MinotaurArtifact, MinotaurHedge, MirrorOfPurification, MonsterStatuette, MonsterousInterredGrizzleMaggots, NotarizedApplication, OfficialSealingWax, OrdersFromMinax, OrigamiButterfly, OrigamiFish, OrigamiFrog, OrigamiPaper, OrigamiShape, OrigamiSongbird, OrigamiSwan, ParasiticPlant, ParoxysmusCorrodedStein, ParoxysmusDinner, PhillipsWoodenSteed, Pier, PigmentsOfTokuno, PlagueBeastBackupOrgan, PlagueBeastBlood, PlagueBeastGland, PlagueBeastHeart, PlagueBeastMaidenOrgan, PlagueBeastMainOrgan, PlagueBeastMutationCore, PlagueBeastOrgan, PlagueBeastRockOrgan, PlagueBeastRubbleOrgan, PlantBowl, PlantItem, PlayerBBEast, PlayerBBSouth, PortraitOfTheBride, PowerCrystal, PrimitiveFetish, PrismaticCrystal, PristineDreadHorn, ProtectorsEssence, Putrefication, RaceChangeDeed, RedSoulstone, ReginasLetter, RepairDeed, ResolvesBridle, RideablePolarBear, RunedPrism, RunedSwitch, SalivasFeather, SamplesOfCorruptedWater, SandMiningBook, SapOfSosaria, Scourge, SeahorseStatuette, SealedNotesForJamal, SealingWaxOrderAddressedToPetrus, SerpentFangSectBadge, SeveredElfEars, SeveredHumanEars, ShimmeringCrystals, ShipModelOfTheHMSCape, Shuriken, SignedTuitionReimbursementForm, SkullPole, SmallTowerSculpture, SmallUrn, SoulStone, SoulstoneFragment, SoulstoneFragmentToken, SpecialBeardDye, SpecialFishingNet, SpecialHairDye, SpecialTreatForDrithen, SpeckledPoisonSac, StainedOoze, StoneMiningBook, StoutWhip, StringOfPartsOfParoxysmusVictims, SwampTile, SweatOfParoxysmus, Taint, TaintedMushroom, TaintedSeeds, TaintedTreeSample, TallMusicStand, TatteredAncientMummyWrapping, ThorvaldsMedallion, ThrashersTail, TigerClawSectBadge, TombstoneOfTheDamned, TormentedChains, ToyBoat, TravestysCollectionOfShells, TravestysFineTeakwoodTray, TravestysSushiPreparations, TreasuresOfTokunoPersistence, TribalPaint, TuitionReimbursementForm, UnholyBone, UnicornRibs, VacationWafer, Vase, WallBlood, WaterTile, WindChimes, WindSpirit, ZoogiFungus

**E. Veteran-reward, heritage, gift, holiday and event items (vetRewards.enable is False; no holiday event runs)** (106)

AngelDecoration, AwesomeDisturbingPortraitComponent, BadCard, BannerDeed, BlueSnowflake, BoneThroneComponent, BrokenArmoireComponent, BrokenBookcaseComponent, BrokenChestOfDrawersComponent, BrokenCoveredChairComponent, BrokenFallenChairComponent, BronzeStatueMaker, ChairInAGhostCostume, ClothingBlessDeed, ColoredAnvil, ColoredSmallWebs, CreepyPortraitComponent, CupidStatue, CupidsArrow, DawnsMusicBox, DawnsMusicGear, DecorativeShield, DecorativeShieldDeed, DecorativeTopiary, DisturbingPortraitComponent, DragonEasterEgg, ExcellentIronMaiden, FestiveCactus, Fireflies, FirefliesDeed, FlamingHead, FlamingHeadDeed, GrimWarning, GuillotineComponent, HairRestylingDeed, HalloweenGuillotine, HalloweenPumpkin, HangingSkeleton, HangingSkeletonDeed, HaunterMirrorComponent, HeritageToken, HolidayBell, HolidayPottedPlant, HolidayTreeDeed, IcicleLargeEast, IcicleLargeSouth, IcicleMedEast, IcicleMedSouth, IcicleSmallEast, IcicleSmallSouth, IcyPatch, JadeStatueMaker, LargeFishingNetComponent, LightOfTheWinterSolstice, MarbleStatueMaker, MistletoeAddon, MistletoeDeed, MountedPixieBlueComponent, MountedPixieGreenComponent, MountedPixieLimeComponent, MountedPixieOrangeComponent, MountedPixieWhiteComponent, PileOfGlacialSnow, PottedCactusDeed, PottedPlantDeed, PumpkinScarecrow, RedPoinsettia, RewardBrazier, RewardBrazierDeed, RewardCake, RewardPottedCactus, RockingHorse, RoseInAVase, RoseOfTrinsic, RoseOfTrinsicPetal, RuinedTapestry, ScarecrowComponent, SkullsOnPike, SmallFishingNetComponent, SnowGlobe, SnowGlobeOne, SnowGlobeThree, SnowGlobeTwo, SnowPile, SnowPileDeco, SnowStatueDeed, SnowStatueGriffon, SnowStatueMermaid, SnowStatuePegasus, SnowStatueSeahorse, Snowman, SnowyTree, StValentinesPanda, StValentinesPolarBear, StandingBrokenChairComponent, SuitOfGoldArmorComponent, SuitOfSilverArmorComponent, TapestryOfSosaria, UnsettlingPortraitComponent, ValentinesCardEast, ValentinesCardSouth, WallTorchComponent, WhitePoinsettia, WhiteSnowflake, WreathAddon, WreathDeed

**F. Decoration pieces that no vendor, craft recipe, loot table or decoration file of this world produces (Deco rares, ruined furniture, artifacts, paintings, tapestries, floors, rugs, banners, potted plants, flasks, jars)** (313)

AcademicBooksArtifact, AniLargeVioletFlask, AniRedRibbedFlask, AniSmallBlueFlask, BambooScreen, BigElvenChair, BloodyWaterArtifact, BlueBeaker, BlueCurvedFlask, BlueSlateFloorCenter, BooksFaceDownArtifact, BooksNorthArtifact, BooksWestArtifact, BottleArtifact, BowlArtifact, BowlsHorizontalArtifact, BowlsVerticalArtifact, BrazierArtifact, BricksFloor1, BricksFloor2, BrokenChair, CaveFloorCenter, CaveFloorEast, CaveFloorNorth, CaveFloorSouth, CaveFloorWest, CobblestonesFloor, CocoonArtifact, CoveredChair, CupsArtifact, CurvedFlask, DamagedBooksArtifact, DarkSandstoneFloorN, DarkSandstoneFloorW, DecoArrowShafts, DecoBlackmoor, DecoBloodspawn, DecoBottlesOfLiquor, DecoBridle, DecoBridle2, DecoBrimstone, DecoCards5, DecoCrystalBall, DecoDeckOfTarot, DecoDeckOfTarot2, DecoDragonsBlood, DecoDragonsBlood2, DecoEyeOfNewt, DecoFlower, DecoFlower2, DecoFullJar, DecoFullJars3, DecoFullJars4, DecoGarlic, DecoGarlic2, DecoGarlicBulb, DecoGarlicBulb2, DecoGinseng, DecoGinseng2, DecoGinsengRoot, DecoGinsengRoot2, DecoGoldIngot, DecoGoldIngot2, DecoGoldIngots, DecoGoldIngots2, DecoGoldIngots3, DecoGoldIngots4, DecoHay, DecoHay2, DecoHorseDung, DecoIronIngot, DecoIronIngot2, DecoIronIngots, DecoIronIngots2, DecoIronIngots3, DecoIronIngots4, DecoIronIngots5, DecoIronIngots6, DecoMagicalCrystal, DecoMandrake, DecoMandrake2, DecoMandrake3, DecoMandrakeRoot, DecoMandrakeRoot2, DecoNightshade, DecoNightshade2, DecoNightshade3, DecoObsidian, DecoPumice, DecoRock, DecoRock2, DecoRocks, DecoRocks2, DecoRoseOfTrinsic, DecoRoseOfTrinsic2, DecoRoseOfTrinsic3, DecoSilverIngot, DecoSilverIngot2, DecoSilverIngots, DecoSilverIngots2, DecoSilverIngots3, DecoSilverIngots4, DecoSilverIngots5, DecoSpittoon, DecoTarot, DecoTarot2, DecoTarot3, DecoTarot4, DecoTarot5, DecoTarot6, DecoTarot7, DecoTray, DecoTray2, DecoWyrmsHeart, DecorativeAxeNorth, DecorativeAxeWest, DecorativeBowNorth, DecorativeBowWest, DecorativeDAxeNorth, DecorativeDAxeWest, DecorativeShield1, DecorativeShield10, DecorativeShield11, DecorativeShield2, DecorativeShield3, DecorativeShield4, DecorativeShield5, DecorativeShield6, DecorativeShield7, DecorativeShield8, DecorativeShield9, DecorativeShieldSword1North, DecorativeShieldSword1West, DecorativeShieldSword2North, DecorativeShieldSword2West, DecorativeSwordNorth, DecorativeSwordWest, DirtyFrypan, DirtyKettle, DirtyPan, DirtyPot, DirtyRoundPot, DirtySmallPot, DirtySmallRoundPot, DolphinLeftArtifact, DolphinRightArtifact, EggCaseArtifact, ElegantLowTable, ElvenPodium, ElvenReadingChair, EmptyCurvedFlaskE, EmptyCurvedFlaskW, EmptyJar, EmptyJars, EmptyJars2, EmptyJars3, EmptyJars4, EmptyRibbedFlask, EmptyToolKit, EmptyToolKit2, EmptyVialsWRack, FanNorthArtifact, FanWestArtifact, FlowersArtifact, FullVialsWRack, GiantReplicaAcorn, GreenBeaker, GreenBottle, GreenCurvedFlask, GreenDriedFlowers, GreenMarbleFloor, GreyFlagstones, GreyMarbleFloor, GreySlateFloor, GruesomeStandardArtifact, HalfEmptyJar, HalfEmptyJars, HourglassAni, Jars2, Jars3, Jars4, LadyPortrait1, LadyPortrait2, LampPostArtifact, LargeEmptyFlask, LargeEmptyPot, LargeFlask, LargePainting, LargeVioletFlask, LargeYellowFlask, LeatherTunicArtifact, LongFlask, LtBlueCurvedFlask, ManPortrait1, ManPortrait2, ManStatuetteEastArtifact, ManStatuetteSouthArtifact, MarbleFloor, MarblePavers, MediumFlask, MountedDreadHorn, OrnateElvenChair, Painting1NorthArtifact, Painting1WestArtifact, Painting2NorthArtifact, Painting2WestArtifact, Painting3Artifact, Painting4NorthArtifact, Painting4WestArtifact, Painting5NorthArtifact, Painting5WestArtifact, Painting6NorthArtifact, Painting6WestArtifact, PlainLowTable, PottedCactus, PottedCactus1, PottedCactus2, PottedCactus3, PottedCactus4, PottedCactus5, PottedPlant, PottedPlant1, PottedPlant2, PottedTree, PottedTree1, RedBeaker, RedBottle, RedCurvedFlask, RedRibbedFlask, RockArtifact, RuinedArmoire, RuinedBookcase, RuinedBooks, RuinedChair, RuinedClock, RuinedDrawers, RuinedFallenChairA, RuinedFallenChairB, RuinedPainting, RuinedPaintingArtifact, SaddleArtifact, SakeArtifact, SandFlagstones, SandstoneFloorN, SandstoneFloorW, Sculpture1Artifact, Sculpture2Artifact, ShojiScreen, ShortMusicStand, SkinnedDeerArtifact, SkinnedGoatArtifact, SkullCandleArtifact, SmallBlueBottle, SmallBlueFlask, SmallBrownBottle, SmallEmptyFlask, SmallEmptyPot, SmallFlask, SmallGreenBottle, SmallGreenBottle2, SmallRedFlask, SmallVioletBottle, SmallYellowFlask, SpinningHourglass, SpiritBottle, StatuePegasus, StatuePegasus2, StoneChair, StonePaversDark, StonePaversLight, StonePaversMedium, StretchedHideArtifact, StuddedLeggingsArtifact, StuddedTunicArtifact, SwordDisplay1NorthArtifact, SwordDisplay1WestArtifact, SwordDisplay2NorthArtifact, SwordDisplay2WestArtifact, SwordDisplay3EastArtifact, SwordDisplay3SouthArtifact, SwordDisplay4NorthArtifact, SwordDisplay4WestArtifact, SwordDisplay5NorthArtifact, SwordDisplay5WestArtifact, Tapestry1N, Tapestry2N, Tapestry2W, Tapestry3N, Tapestry3W, Tapestry4N, Tapestry4W, Tapestry5N, Tapestry5W, Tapestry6N, Tapestry6W, TarotCardsArtifact, TeapotNorthArtifact, TeapotWestArtifact, TinyRedBottle, TinyYellowBottle, TowerLanternArtifact, TripleFanNorthArtifact, TripleFanWestArtifact, Urn1Artifact, Urn2Artifact, VioletRibbedFlask, WhiteDriedFlowers, WomanPortrait1, WomanPortrait2, YellowBeaker, ZenRock1Artifact, ZenRock2Artifact, ZenRock3Artifact

**G. Props, filler and ingredients with nothing useful to say (the general item page is right)** (9)

Bola, BolaBall, BowlFlour, DeceitBrazier, FishOilFlask, HorseShoes, HoveringWisp, ThrowingDagger, Whip

**H. Systems that are off or are not sold under UOR rules (AOS tool, AOS rental contracts, the new guild system, Mahjong)** (5)

GuildTeleporter, GuildstoneDeed, HousePlacementTool, MahjongGame, VendorRentalContract

Single classes worth a remark: `Bola` and `BolaBall` (not in the legacy Tinkering menu, see OPEN 8); `BowlFlour` (a baker sells it for 7 gold; no recipe uses it in this world); `HorseShoes`, `Whip`, `ThrowingDagger` (props found in fillable containers or unused); `BackpackWard` and `ShrunkenPet` are covered above; `TrainingDummy`, `ArcheryButte`, `BallotBox`, `DartBoard` are fixed add-on components, not carried; the Deco and Rares items are not placed by any decoration file of this world (the 28 allowlisted files place only furniture, plants, traps and statics, and decoration items are made immovable by `Decorate.cs:1062`).
