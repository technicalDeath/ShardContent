
# Item topics: armor and clothing (area A, prefix a-)

Written by the area-A item writer. Output: `parts/a.items.json` (18 topics). All paths below are relative to the workspace root.
Era facts used throughout: `Core.Expansion` is UOR (`ShardContent/data/configuration/expansion.json`), so `Core.UOR` is true and `Core.AOS`/`SE`/`ML`/`SA`/`UOTD` are false;
the craft menus are the T2A packet menus (`ExpansionConfiguration.cs:15`, `t2aCraftMenus` defaults to `!Core.UOTD`; confirmed in `ShardContent/docs/Cooking-Era-Restore-Research.md:8`).
Vendors, TownsPeople and Vendors spawners are generated for Britain only (`ShardContent/data/world-generation/alpha2b/world-generation.json`, `britainOnlySpawnerFiles`), so "sold by X" means an X spawns in Britain
(count in `ModernUO/Distribution/Data/Spawns/shared/felucca/Vendors.json` inside the Britain bounds x 1280-1750, y 1400-1900: Armorer 4, Blacksmith 2, Tanner 1, Tailor 3, Weaver 3, Cobbler 2, Provisioner 2, Jeweler 2, Mage 3 (+2 in `britain-vendor-overrides.json`)).
Vendor prices are the listed `GenericBuyInfo` prices unscaled: `BaseVendor.GetPriceScalar` = 100 + town tax and the faction town state defaults to Tax 0 (`BaseVendor.cs:1384`, `Engines/Factions/Core/TownState.cs:116`).

How the fallback resolves (`ShardContent/src/BritanniaRenaissance.Content/HelpCatalog.cs:410-433`): `TopicFor` walks the item's own class and then each base class, checking `types` then `inherits` at each level.
So a class derived from a class in a `types` list (artifacts such as ArcaneShield, DeathRobe, HelmOfInsight) shows the family topic, and everything else under BaseArmor/BaseShield/BaseClothing/BaseJewel shows the fallback.


Path key for the short names used below (all under the workspace root):
- UOContent = `ModernUO/Projects/UOContent/`; Server = `ModernUO/Projects/Server/`; Shard = `ShardContent/src/BritanniaRenaissance.Content/`.
- `BaseArmor.cs`, `ArmorEnums.cs` = UOContent/Items/Armor/; armor classes = UOContent/Items/Armor/<Plate|Chain|Ring|Studded|Leather|Bone|Helmets>/<Class>.cs; shields and `BaseShield.cs` = UOContent/Items/Shields/.
- `BaseWeapon.cs` = UOContent/Items/Weapons/; `Bow.cs` = UOContent/Items/Weapons/Ranged/; `BaseClothing.cs`, `Hats.cs`, `Shirts.cs`, `MiddleTorso.cs`, `OuterTorso.cs`, `OuterLegs.cs`, `Pants.cs`, `Shoes.cs`, `Waist.cs`, `Cloaks.cs` = UOContent/Items/Clothing/; `BaseJewel.cs`, `Ring.cs`, ... = UOContent/Items/Jewels/.
- `PlayerMobile.cs` = UOContent/Mobiles/; `Mobile.cs` = Server/Mobiles/; `Item.cs` = Server/Items/.
- `RegenRates.cs`, `Loot.cs`, `LootPack.cs` = UOContent/Misc/; `Stealth.cs`, `ArmsLore.cs`, `ItemIdentification.cs`, `SkillCheck.cs` = UOContent/Skills/; `Spell.cs` = UOContent/Spells/Base/.
- `Repair.cs`, `CraftItem.cs`, `CraftCollectionExtensions.cs` = UOContent/Engines/Craft/Core/; `DefBlacksmithy.cs`, `DefTailoring.cs`, `DefCarpentry.cs`, `DefTinkering.cs` = UOContent/Engines/Craft/; `T2A/*.cs` = UOContent/Engines/Craft/T2A/.
- `SBInfo/*.cs`, `GenericSell.cs`, `BaseVendor.cs`, `NPC/*.cs` = UOContent/Mobiles/Vendors/ (`SBInfo/Armors/` for the armor lists); `Skeleton.cs` = UOContent/Mobiles/Monsters/Humanoid/Melee/.
- `CharacterCreation.cs` = UOContent/Engines/Character Creation/; `Dyes.cs` = UOContent/Items/Skill Items/Tailor Items/Misc/; `DyeTub.cs` = UOContent/Items/Skill Items/Tailor Items/Dyetubs/; `SmithHammer.cs`, `Tongs.cs` = UOContent/Items/Skill Items/Tools/.
- `ExpansionConfiguration.cs` = UOContent/Configuration/; `TownState.cs` = UOContent/Engines/Factions/Core/.
- `HelpCatalog.cs`, `StarterCombatIssuance.cs`, `StarterPackageSelection.cs` = Shard.
- `tiledata.mul` = `UOData/tiledata.mul` (item entry = 41 bytes after the 512 x 964-byte land block; byte 9 of the entry is the layer/quality). Layers read: PlateHelm 0x1412, CloseHelm 0x1408, Helmet 0x140A, Bascinet 0x140C, NorseHelm 0x140E, ChainCoif 0x13BB, LeatherCap 0x1DB9, OrcHelm 0x1F0B, BoneHelm 0x1451, hats 0x1713/0x1718/0x1544/0x1540 = 6 (Helm); PlateGorget 0x1413, LeatherGorget 0x13C7, Necklace 0x1085 = 10 (Neck); PlateLegs 0x1411, ChainLegs 0x13BE, LeatherLegs 0x13CB, BoneLegs 0x1452, LeatherShorts 0x1C00, LeatherSkirt 0x1C08, short/long pants 0x152E/0x1539 = 4 (Pants); kilt 0x1537, skirt 0x1516 = 23 (OuterLegs); shields 0x1B73/0x1B76/0x1B7A = 2 (TwoHanded); Doublet/Tunic/Surcoat/JesterSuit/BodySash/FullApron = 17 (MiddleTorso); PlainDress/FancyDress/Robe = 22 (OuterTorso); Shirt/FancyShirt = 5; Cloak = 20; HalfApron = 12 (Waist).

## Claims (one per line: topic | claim | source)

### a-armor (inherits BaseArmor)
a-armor | Armor works against weapon hits only: the only caller of `AbsorbDamage` and of the armor `OnHit` is the weapon damage code; spells never reach it | BaseWeapon.cs:1713,1746,1952 (grep: no other caller of `IWearableDurability.OnHit`/`AbsorbDamage(`)
a-armor | Total armor rating = sum over neck, hands, head, arms, legs, chest and shield of `ArmorRating * ArmorScalar`; shield is added at scalar 1.0 (position Shield is outside the 6-entry table) | PlayerMobile.cs:241-258,1773-1779; BaseArmor.cs:330,461-474,517
a-armor | Shares: gorget 0.07, gloves 0.07, helmet 0.14, arms 0.15, legs 0.22, chest 0.35 (enum order Gorget, Gloves, Helmet, Arms, Legs, Chest, Shield) | BaseArmor.cs:517; ArmorEnums.cs:30-38
a-armor | Hit location chances: <0.07 neck, <0.14 hands, <0.28 arms, <0.43 head, <0.65 legs, rest chest (= 7, 7, 14, 15, 22, 35 in 100). Note: the rating shares give helm 14 and arms 15, the hit chances give head 15 and arms 14; the text states each correctly | BaseWeapon.cs:1735-1744
a-armor | Shield gets the first chance (shield.OnHit before the body armor) | BaseWeapon.cs:1728-1731
a-armor | The struck piece absorbs between half and all of its own `ArmorRating` (halfar + halfar*random) | BaseArmor.cs:729-732
a-armor | Pre-AoS minimum damage is 1 | BaseWeapon.cs:1954-1957
a-armor | Plate chest rating 40 absorbs about 20 to 40 | BaseArmor.cs:729-732 with PlateChest.cs:30
a-armor | Slots: leg armor is on the Pants layer (tiledata quality 4 for 0x1411/0x13BE/0x13CB/0x1C00/0x1C08/0x1452); long and short pants are `Layer.Pants`; kilt and skirt `Layer.OuterLegs` | UOData/tiledata.mul item entries (layer byte); Clothing/Pants.cs:8; Clothing/OuterLegs.cs:8; BaseArmor.cs:500-515
a-armor | Slots: helmets, ChainCoif, LeatherCap, BoneHelm, OrcHelm are layer 6 (Helm) in tiledata and every hat is `Layer.Helm`; gorgets and necklaces are layer 10 (Neck); shields are layer 2 (TwoHanded) and Bow/Crossbow/HeavyCrossbow set `Layer.TwoHanded` | tiledata.mul; Clothing/Hats.cs:17; Jewels/Necklace.cs:8; Weapons/Ranged/Bow.cs:13; BaseWeapon.cs:1042-1060
a-armor | Strength needed: `StrRequirement` = `OldStrReq` when not AoS; `CanEquip` refuses below it | BaseArmor.cs:395,1100-1113
a-armor | Dexterity: `DexBonus` = `OldDexBonus` (negative) when not AoS, added as a stat mod on equip; stamina max = Dex | BaseArmor.cs:357,1140-1169; Mobile.cs:2166; PlayerMobile.cs:582
a-armor | Mana: pre-AoS regen rate = f((Int+Meditation)/2) + GetArmorOffset, halved while meditating, clamped 0.5-7.0 s; offset = sum of piece base rating x scalar (None: full, Half: half, All: 0) / 4, including the shield | RegenRates.cs:144,200-217,223-255
a-armor | Plate chest alone: 40 x 0.35 / 4 = 3.5 s; studded chest alone 16 x 0.35 / 2 / 4 = 0.7 s ("under a second") | RegenRates.cs:223-255 with the class files below
a-armor | Armor never blocks casting: no armor check in the Spells folder; casting calls `ClearHands` (moves shield and weapon to the pack) | grep of Spells/ (no BaseArmor/ArmorRating use); Spell.cs:55,565-568,795-802; Mobile.cs:3787-3806
a-armor | Stealth refused at total armor rating >= 26 (pre-AoS uses `(int)m.ArmorRating`) | Skills/Stealth.cs:38-43,91-95
a-armor | Female-only pieces: `AllowMaleWearer => false` refuses males | BaseArmor.cs:1072-1084; per-class lines below
a-armor | Wear: 25% chance per landed blow; wear = Random(2) or, for Bashing weapons, max(1, absorbed/2) | BaseArmor.cs:734-743
a-armor | Rating halves at 0 durability: scale = 50 + 50*hp/max | BaseArmor.cs:986-996
a-armor | At 0 hit points more wear lowers the maximum, and the piece is deleted when the maximum is used up | BaseArmor.cs:745-777
a-armor | Blacksmith repair: needs anvil and forge within 2 tiles, item in the backpack (not worn pre-ML), only items in the blacksmith craft list (or subclass), may lower the maximum (1 to 3) | Repair.cs:165,337-345,321-331; DefBlacksmithy.cs:110; CraftCollectionExtensions.cs:27-40
a-armor | Leather, studded, bone and WoodenShield cannot be repaired: none is in the blacksmith craft list; tailoring and carpentry `Repair = Core.AOS` (false); the T2A tailoring menu has no repair entry | DefBlacksmithy.cs:707; DefTailoring.cs:675; DefCarpentry.cs:595; T2A/TailoringMenu.cs (no Repair entry)
a-armor | Smith's hammer or tongs are both blacksmith tools | Skill Items/Tools/SmithHammer.cs:18; Tongs.cs (CraftSystem => DefBlacksmithy)
a-armor | Arms Lore on armor reports condition and a rating band | Skills/ArmsLore.cs:87-101
a-armor | Colored ingot rating bonus (UOR): dull copper 2, shadow iron 4, copper 6, bronze 8, gold 10, agapite 12, verite 14, valorite 16 | BaseArmor.cs:306-322
a-armor | Ingot skill minimums 65/70/75/80/85/90/95/99 | DefBlacksmithy.cs:688-695
a-armor | Exceptional quality: +8 rating, +20 durability percent (UOR branch) | BaseArmor.cs:325,897
a-armor | Magical loot armor: 80% a ProtectionLevel (1-5), 40% a Durability level (pre-AoS Mutate) | LootPack.cs:776-787
a-armor | Protection adds `10` (UOR) + `5 x level` = 15/20/25/30/35 | BaseArmor.cs:295-303
a-armor | Durability levels add 20/50/70/100/120 percent | BaseArmor.cs:881-889
a-armor | Unidentified until Item Identification succeeds; labels "defense...invulnerability" and "durable...indestructible" | BaseArmor.cs:1395-1441,1459-1487; Skills/ItemIdentification.cs:44-47
a-armor | [gated Alpha3StarterCombatGear] starter outfit is newbied: creation `EquipItem`/`PackItem` stamp Newbied when not AoS, shirt/pants/shoes go through `EquipItem`; kept on death unless murderer; vendors refuse Newbied | CharacterCreation.cs:727-761,794; Item.cs:2296,2326; GenericSell.cs:37; docs/Alpha-3-Starter-Combat-Readiness.md ("Current-source review")

### a-plate
a-plate | per-piece rating, Str, Dex, weight, durability | see class lines below (Items/Armor/Plate/*.cs)
a-plate | All six places covered with PlateHelm (rating 40); full suit weight 10+7+5+2+2+5 = 31, Dex 8+6+2+2+1+1 = 20 | class lines below
a-plate | Prices gorget 104, chest 243, legs 218, arms 188, gloves 155 | SBInfo/SBBlacksmith.cs:28-32 (same in SBInfo/Armors/SBPlateArmor.cs)
a-plate | Blacksmith NPC always carries SBBlacksmith; armorer carries SBPlateArmor in 2 of its 4 random sets | NPC/Blacksmith.cs:53; NPC/Armorer.cs:25-60
a-plate | Craftable by blacksmith from iron ingots, female plate chest included | T2A/BlacksmithMenu.cs:37-42; DefBlacksmithy.cs:198-203
a-plate | FemalePlateChest is not sold (absent from SBBlacksmith/SBPlateArmor buy lists) | SBInfo/SBBlacksmith.cs:28-34

### a-chain / a-ring
a-chain | Only ChainChest, ChainLegs, ChainCoif exist for sale and in the craft menu | T2A/BlacksmithMenu.cs:32-35; SBBlacksmith.cs:44-46
a-chain | prices coif 17, chest 143, legs 149 | SBBlacksmith.cs:44-46
a-chain | set weight 7+7+1 = 15 | class lines below
a-ring | Ringmail chest/legs/arms 15 stones each, gloves 2; Str 20; prices 121/90/85/93 | class lines below; SBBlacksmith.cs:48-51
a-ring | "weighs more than plate": ringmail chest 15 vs plate chest 10 | RingmailChest.cs:14; PlateChest.cs:14

### a-helms
a-helms | Five metal helmets plus OrcHelm; ratings 40/30/30/30/18/20; Str 40/40/40/40/10/10; weight 5 | class lines below
a-helms | Prices 18-31 (PlateHelm 21, CloseHelm 18, Helmet 31 or 18 by graphic, NorseHelm 18, Bascinet 18) | SBBlacksmith.cs:34-42; SBInfo/Armors/SBHelmetArmor.cs (all four armorer sets include it, NPC/Armorer.cs:25-60)
a-helms | OrcHelm has explicit `DefMedAllowance None`, is in `Loot.ArmorTypes`, and is in no vendor list | OrcHelm.cs:32; Misc/Loot.cs:112-128
a-helms | Craftable by blacksmith (Bascinet, CloseHelm, Helmet, NorseHelm, PlateHelm in the platemail menu) | T2A/BlacksmithMenu.cs:37-42

### a-studded / a-leather
a-studded | Armorer set 0 and 1 carry SBStuddedArmor/SBLeatherArmor | NPC/Armorer.cs:27-46
a-studded | Armorer prices arms 87, chest 128, gloves 79, gorget 73, legs 103, female chest 142, bustier 120 | SBInfo/Armors/SBStuddedArmor.cs:16-22
a-studded | Tanner sells StuddedGorget 50, StuddedArms 57, StuddedBustierArms 97 (less than the armorer) | SBInfo/SBTanner.cs:23-24,36
a-studded | Studded counts half for mana (explicit `Half`) | StuddedChest.cs:33 etc. (class lines)
a-studded | Tailor craft menu has studded chest, gorget, gloves, arms, legs and the female pieces | T2A/TailoringMenu.cs:47-62
a-studded | Scissors on armor: only if a tailoring recipe has one resource of 2+ (leather, studded); gives half the leather if `PlayerConstructed`, otherwise 1 | BaseArmor.cs:633-668
a-leather | Armorer prices arms 80, chest 101, gloves 60, gorget 74, legs 80, cap 10, female chest 116, bustier 97, shorts 86, skirt 87 | SBInfo/Armors/SBLeatherArmor.cs:16-25 (Tanner has the same: SBTanner.cs)
a-leather | Cap sold also by Tailor (10) and Provisioner (10) | SBTailor.cs (LeatherCap); SBProvisioner.cs (LeatherCap)
a-leather | LeatherCap is a head-slot piece (tiledata layer 6) | tiledata.mul 0x1DB9
a-leather | Leather/studded `DefMedAllowance All`/`Half`; no Dexterity penalty (no `OldDexBonus`) | class lines below
a-leather | [gated] archer package: LeatherChest + LeatherLegs, equipped or packed, newbied; selection.Combat is Archer when Archery is the highest valued of Swords/Macing/Fencing/Archery/Magery | StarterCombatIssuance.cs:93-100; StarterPackageSelection.cs:36-63

### a-bone
a-bone | Bone armor is in no vendor list (grep of SBInfo: no Bone class) | grep ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo
a-bone | Every Skeleton packs one of five bone pieces (Random(5)) | Mobiles/Monsters/Humanoid/Melee/Skeleton.cs:40-67
a-bone | Skeletons are spawned in Outdoors (75), Covetous (13), Deceit (15), Graveyards (7), Khaldun (4), LostLands (1) | ModernUO/Distribution/Data/Spawns/shared/felucca/*.json (counted); those files are in `spawnerFiles` of world-generation.json
a-bone | Bone armor cannot be made by a player: the tailoring craft list has it (DefTailoring.cs) but the T2A tailoring menu has no bone category, so the text does not say it can be crafted | DefTailoring.cs (group 1049149); T2A/TailoringMenu.cs:12-23 (categories)
a-bone | Savage, SavageRider, SavageShaman (bone arms/legs wearers) are in `excludedSpawnerTypes`, so not mentioned | world-generation.json excludedSpawnerTypes

### a-shields
a-shields | Shield rating = Parry x ArmorRating / 200 + 1 when worn | BaseShield.cs:15-29
a-shields | Block chance = (Parry - 2 x rating)/100, floor 0.01, then `CheckSkill(Parry, chance)` (success iff chance >= random) | BaseShield.cs:56-63; Skills/SkillCheck.cs:101-130
a-shields | Block removes min(damage, rating/2), or rating against Archery weapons; 25% durability loss on a block | BaseShield.cs:65-72
a-shields | Worked example: Parry 100, base 23 -> 100x23/200+1 = 12.5; chance (100-25)/100 = 75% | arithmetic from the above
a-shields | Shields have no Strength requirement pre-AoS (only `AosStrReq` is overridden) | Shields/HeaterShield.cs:21 etc.; BaseArmor.cs:184,395
a-shields | Mana: shields have default `DefMedAllowance None` and the offset counts the shield when not AoS: heater 23/4 = 5.75 s, buckler 7/4 = 1.75 s | RegenRates.cs:229-232; BaseArmor.cs:170
a-shields | A shield cannot be combined with a two-handed weapon: same `TwoHanded` layer | BaseWeapon.cs:1042-1060; tiledata.mul 0x1B73/0x1B76/0x1B7A layer 2
a-shields | Blacksmith menu lists Buckler, BronzeShield, HeaterShield, MetalShield, MetalKiteShield, WoodenKiteShield (iron ingots); WoodenShield only in the carpentry menu (logs) | T2A/BlacksmithMenu.cs:44-48; DefBlacksmithy.cs:276-281; T2A/CarpentryMenu.cs:38; DefCarpentry.cs:356
a-shields | Prices buckler 50, wooden shield 30, bronze 66, wooden kite 70, metal 121, metal kite 123, heater 231; wooden shield only from Blacksmith (SBWoodenShields is in no NPC) | SBBlacksmith.cs:19-26; SBInfo/Armors/SBMetalShields.cs; NPC/Armorer.cs
a-shields | [gated] a Parry-skill character gets a WoodenShield | CharacterCreation.cs:1252-1259; StarterCombatIssuance.cs:102-106

### clothing
a-clothes | BaseClothing `OldStrReq 0` (no Strength), no armor rating (not counted in `PlayerMobile.ArmorRating`) | BaseClothing.cs:166; PlayerMobile.cs:1773-1779
a-clothes | Dyeing: Dyes target a dye tub and open the hue picker (tub redyable by default); the tub works on `IDyable` clothing only when not worn and within 1 tile of tub and item | Dyes.cs:20-55; DyeTub.cs:28,86-125; BaseClothing.cs:205-219
a-clothes | Dyes and dye tub 8 gold at Tailor and Weaver | SBTailor.cs:18-19; SBWeaver.cs:16-17
a-clothes | Tailor-sewn clothing takes the cloth hue (T2A cloth selection passes the hue; `Hue = resHue` when `DefaultResource` is None) | T2A/TailoringMenu.cs:275,324; BaseClothing.cs:143,184-192; CraftItem.cs:1459-1463
a-clothes | Scissors on clothing: tailoring recipe with one resource >= 2 -> half the cloth if `PlayerConstructed`, else 1 | BaseClothing.cs:238-286
a-hats | 12 hats, weight 1 each, head slot | Hats.cs (class lines), Hats.cs:17
a-hats | Tailor sells all but Bonnet (6-12 gold: Bandana 6, SkullCap/Floppy/Straw 7, WideBrim/TallStraw/Tricorne 8, Cap/Feathered 10, WizardsHat 11, JesterHat 12); Provisioner sells all but Bonnet and JesterHat; hues `RandomDyedHue` except JesterHat | SBTailor.cs:37-48; SBProvisioner.cs:41-51
a-magic-hat | MagicWizardsHat: BaseStrBonus -5, BaseDexBonus -5, BaseIntBonus +5; applied on add (`AddStatBonuses` is not AoS-gated) | Hats.cs:505-507; BaseClothing.cs:486-516,596
a-magic-hat | Int is max mana; Str gives hits 50 + Str/2; max weight 40 + 3.5 x Str; Dex is max stamina | Mobile.cs:2121,2166,2221; PlayerMobile.cs:239 (MaxWeight)
a-magic-hat | Sold by Mage for 11 in a random dyed hue | SBMage.cs:27
a-shirts | Weights shirt 1, fancy shirt 2, doublet 2, plain dress 2, fancy dress 3, jester suit 4, tunic 5, surcoat 6 | class lines below
a-shirts | Doublet, Tunic, Surcoat, JesterSuit, BodySash, FullApron are `Layer.MiddleTorso`; PlainDress, FancyDress, Robe are `Layer.OuterTorso` | Clothing/MiddleTorso.cs:8; OuterTorso.cs:11; tiledata.mul
a-shirts | Prices shirt 12, fancy shirt 21, doublet 13, plain dress 13, tunic 18, fancy dress 26, jester suit 26; Surcoat not sold | SBTailor.cs:21-35
a-shirts | Tailor menu: Doublet, Shirt, FancyShirt, Tunic, Surcoat, PlainDress; Misc: FancyDress, JesterSuit | T2A/TailoringMenu.cs:32-43
a-robes | Robe OuterTorso 3 stones, Cloak (Cloak layer) 5 stones; robe 18 gold, cloak 8 gold at Tailor | OuterTorso.cs:326; Cloaks.cs:23; SBTailor.cs:30-31
a-pants | ShortPants 2, LongPants 2 (Pants layer), Kilt 2, Skirt 4 (OuterLegs); prices 7, 10, 11; Skirt not sold; all four craftable (Skirt via Misc menu) | Pants.cs; OuterLegs.cs; SBTailor.cs:22,24,27; T2A/TailoringMenu.cs:37-43
a-shoes | Sandals 1, Shoes 2, Boots 3, ThighBoots 4; Cobbler 5/8/10/15 with `RandomNeutralHue`; made from leather | Shoes.cs; SBCobbler.cs:16-19; DefTailoring.cs (Leather resource)
a-aprons | BodySash 1 and FullApron 4 (MiddleTorso), HalfApron 2 (Waist); only HalfApron sold (10); all three in the tailoring Misc menu | MiddleTorso.cs; Waist.cs; SBTailor.cs:29; T2A/TailoringMenu.cs:39-43

### a-jewelry
a-jewelry | Jewelry stat bonuses (skill bonuses, stat mods) are applied only `if Core.AOS`; sold and crafted pieces carry none | Jewels/BaseJewel.cs:328-355
a-jewelry | Rings Layer.Ring, Bracelet Layer.Bracelet, Necklace Layer.Neck, Earrings Layer.Earrings; weight 0.1 | Jewels/Ring.cs:8; Bracelet.cs:8; Necklace.cs:8; Earrings.cs:8
a-jewelry | Jeweler sells GoldRing 27, Necklace 26, GoldNecklace 27, GoldBeadNecklace 27, GoldBracelet 27, GoldEarrings 27 | SBInfo/SBJewel.cs:16-22
a-jewelry | Tinkers make GoldNecklace, SilverNecklace, GoldEarrings, SilverEarrings, GoldRing, SilverRing, WeddingRing (T2A menu; no bracelets or bead necklaces) | T2A/TinkeringMenu.cs:72-82; DefTinkering.cs:394-402
a-jewelry | The player targets a gem; the whole targeted stack is consumed on success and names the piece | T2A/TinkeringMenu.cs:377-378,486-540; Jewels/BaseJewel.cs:186-206

### Per-class numbers (rating, Strength, Dexterity, weight in stones, durability, mana allowance, female-only), read from each class file
Line numbers are the lines of the matching override in that file. Missing fields mean the class does not override them (base defaults: Strength 0 via `OldStrReq`, Dexterity 0, mana allowance None for BaseArmor).

a-plate | PlateChest: weight=10.0, rating=40, str=60, dex=-8, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Armor/Plate/PlateChest.cs:14,22,23,26,28,30
a-plate | PlateLegs: weight=7.0, rating=40, str=60, dex=-6, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Armor/Plate/PlateLegs.cs:14,22,23,27,28,30
a-plate | PlateArms: weight=5.0, rating=40, str=40, dex=-2, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Armor/Plate/PlateArms.cs:14,22,23,26,28,30
a-plate | PlateGloves: weight=2.0, rating=40, str=30, dex=-2, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Armor/Plate/PlateGloves.cs:14,22,23,26,28,30
a-plate | PlateGorget: weight=2.0, rating=40, str=30, dex=-1, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Armor/Plate/PlateGorget.cs:13,21,22,25,27,29
a-plate | FemalePlateChest: weight=4.0, rating=30, str=45, dex=-5, minh=50, maxh=65, female=false | ModernUO/Projects/UOContent/Items/Armor/Plate/FemalePlateChest.cs:14,22,23,26,28,30,32
a-chain | ChainChest: weight=7.0, rating=28, str=20, dex=-5, minh=45, maxh=60 | ModernUO/Projects/UOContent/Items/Armor/Chain/ChainChest.cs:14,22,23,26,28,30
a-chain | ChainLegs: weight=7.0, rating=28, str=20, dex=-3, minh=45, maxh=60 | ModernUO/Projects/UOContent/Items/Armor/Chain/ChainLegs.cs:14,22,23,26,28,30
a-chain | ChainCoif: weight=1.0, rating=28, str=20, minh=35, maxh=60 | ModernUO/Projects/UOContent/Items/Armor/Helmets/ChainCoif.cs:14,22,23,26,28
a-ring | RingmailChest: weight=15.0, rating=22, str=20, dex=-2, minh=40, maxh=50 | ModernUO/Projects/UOContent/Items/Armor/Ring/RingmailChest.cs:14,22,23,26,28,30
a-ring | RingmailLegs: weight=15.0, rating=22, str=20, dex=-1, minh=40, maxh=50 | ModernUO/Projects/UOContent/Items/Armor/Ring/RingmailLegs.cs:14,22,23,26,28,30
a-ring | RingmailArms: weight=15.0, rating=22, str=20, dex=-1, minh=40, maxh=50 | ModernUO/Projects/UOContent/Items/Armor/Ring/RingmailArms.cs:14,22,23,26,28,30
a-ring | RingmailGloves: weight=2.0, rating=22, str=20, dex=-1, minh=40, maxh=50 | ModernUO/Projects/UOContent/Items/Armor/Ring/RingmailGloves.cs:14,22,23,26,28,30
a-helms | Bascinet: weight=5.0, rating=18, str=10, minh=40, maxh=50 | ModernUO/Projects/UOContent/Items/Armor/Helmets/Bascinet.cs:13,21,22,25,27
a-helms | CloseHelm: weight=5.0, rating=30, str=40, minh=45, maxh=60 | ModernUO/Projects/UOContent/Items/Armor/Helmets/CloseHelm.cs:13,21,22,25,27
a-helms | Helmet: weight=5.0, rating=30, str=40, minh=45, maxh=60 | ModernUO/Projects/UOContent/Items/Armor/Helmets/Helmet.cs:13,21,22,25,27
a-helms | NorseHelm: weight=5.0, rating=30, str=40, minh=45, maxh=60 | ModernUO/Projects/UOContent/Items/Armor/Helmets/NorseHelm.cs:13,21,22,25,27
a-helms | PlateHelm: weight=5.0, rating=40, str=40, dex=-1, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Armor/Helmets/PlateHelm.cs:13,21,22,25,27,29
a-helms | OrcHelm: weight=5, rating=20, str=10, minh=30, maxh=50, med=None | ModernUO/Projects/UOContent/Items/Armor/Helmets/OrcHelm.cs:19,20,23,25,27,32
a-studded | StuddedChest: weight=8.0, rating=16, str=35, minh=35, maxh=45, med=Half | ModernUO/Projects/UOContent/Items/Armor/Studded/StuddedChest.cs:14,22,23,26,28,33
a-studded | StuddedLegs: weight=5.0, rating=16, str=35, minh=35, maxh=45, med=Half | ModernUO/Projects/UOContent/Items/Armor/Studded/StuddedLegs.cs:14,22,23,26,28,33
a-studded | StuddedArms: weight=4.0, rating=16, str=25, minh=35, maxh=45, med=Half | ModernUO/Projects/UOContent/Items/Armor/Studded/StuddedArms.cs:14,22,23,26,28,33
a-studded | StuddedGloves: weight=1.0, rating=16, str=25, minh=35, maxh=45, med=Half | ModernUO/Projects/UOContent/Items/Armor/Studded/StuddedGloves.cs:14,22,23,26,28,33
a-studded | StuddedGorget: weight=1.0, rating=16, str=25, minh=35, maxh=45, med=Half | ModernUO/Projects/UOContent/Items/Armor/Studded/StuddedGorget.cs:13,21,22,25,27,32
a-studded | FemaleStuddedChest: weight=6.0, rating=16, str=35, minh=35, maxh=45, med=Half, female=false | ModernUO/Projects/UOContent/Items/Armor/Studded/FemaleStuddedChest.cs:14,22,23,26,28,33,35
a-studded | StuddedBustierArms: weight=1.0, rating=16, str=35, minh=35, maxh=45, med=Half, female=false | ModernUO/Projects/UOContent/Items/Armor/Studded/StuddedBustierArms.cs:14,22,23,26,28,33,35
a-leather | LeatherChest: weight=6.0, rating=13, str=15, minh=30, maxh=40, med=All | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherChest.cs:14,22,23,26,28,33
a-leather | LeatherLegs: weight=4.0, rating=13, str=10, minh=30, maxh=40, med=All | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherLegs.cs:14,22,23,26,28,33
a-leather | LeatherArms: weight=2.0, rating=13, str=15, minh=30, maxh=40, med=All | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherArms.cs:14,22,23,26,28,33
a-leather | LeatherGloves: weight=1.0, rating=13, str=10, minh=30, maxh=40, med=All | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherGloves.cs:14,22,23,26,28,33
a-leather | LeatherGorget: weight=1.0, rating=13, str=10, minh=30, maxh=40, med=All | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherGorget.cs:13,21,22,25,27,32
a-leather | LeatherCap: weight=2.0, rating=13, str=15, minh=30, maxh=40, med=All | ModernUO/Projects/UOContent/Items/Armor/Helmets/LeatherCap.cs:14,22,23,26,28,33
a-leather | FemaleLeatherChest: weight=1.0, rating=13, str=15, minh=30, maxh=40, med=All, female=false | ModernUO/Projects/UOContent/Items/Armor/Leather/FemaleLeatherChest.cs:14,22,23,26,28,33,35
a-leather | LeatherBustierArms: weight=1.0, rating=13, str=15, minh=30, maxh=40, med=All, female=false | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherBustierArms.cs:14,22,23,26,28,33,35
a-leather | LeatherShorts: weight=3.0, rating=13, str=10, minh=30, maxh=40, med=All, female=false | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherShorts.cs:14,22,23,26,28,33,35
a-leather | LeatherSkirt: weight=1.0, rating=13, str=10, minh=30, maxh=40, med=All, female=false | ModernUO/Projects/UOContent/Items/Armor/Leather/LeatherSkirt.cs:14,22,23,26,28,33,35
a-bone | BoneChest: weight=6.0, rating=30, str=40, dex=-6, minh=25, maxh=30 | ModernUO/Projects/UOContent/Items/Armor/Bone/BoneChest.cs:14,22,23,26,28,30
a-bone | BoneLegs: weight=3.0, rating=30, str=40, dex=-4, minh=25, maxh=30 | ModernUO/Projects/UOContent/Items/Armor/Bone/BoneLegs.cs:14,22,23,26,28,30
a-bone | BoneArms: weight=2.0, rating=30, str=40, dex=-2, minh=25, maxh=30 | ModernUO/Projects/UOContent/Items/Armor/Bone/BoneArms.cs:14,22,23,26,28,30
a-bone | BoneGloves: weight=2.0, rating=30, str=40, dex=-1, minh=25, maxh=30 | ModernUO/Projects/UOContent/Items/Armor/Bone/BoneGloves.cs:14,22,23,26,28,30
a-bone | BoneHelm: weight=3.0, rating=30, str=40, minh=25, maxh=30 | ModernUO/Projects/UOContent/Items/Armor/Helmets/BoneHelm.cs:14,22,23,26,28
a-shields | WoodenShield: weight=5.0, rating=8, minh=20, maxh=25 | ModernUO/Projects/UOContent/Items/Shields/WoodenShield.cs:13,21,22,26
a-shields | Buckler: weight=5.0, rating=7, minh=40, maxh=50 | ModernUO/Projects/UOContent/Items/Shields/Buckler.cs:13,21,22,26
a-shields | BronzeShield: weight=6.0, rating=10, minh=25, maxh=30 | ModernUO/Projects/UOContent/Items/Shields/BronzeShield.cs:13,21,22,26
a-shields | WoodenKiteShield: weight=5.0, rating=12, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Shields/WoodenKiteShield.cs:13,21,22,26
a-shields | MetalShield: weight=6.0, rating=11, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Shields/MetalShield.cs:13,21,22,26
a-shields | MetalKiteShield: weight=7.0, rating=16, minh=45, maxh=60 | ModernUO/Projects/UOContent/Items/Shields/MetalKiteShield.cs:13,21,22,26
a-shields | HeaterShield: weight=8.0, rating=23, minh=50, maxh=65 | ModernUO/Projects/UOContent/Items/Shields/HeaterShield.cs:13,21,22,26
a-hats | SkullCap: weight=1.0 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:191
a-hats | Bandana: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:211,219,220
a-hats | FloppyHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:131,139,140
a-hats | Cap: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:171,179,180
a-hats | WideBrimHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:151,159,160
a-hats | StrawHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:355,363,364
a-hats | TallStrawHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:335,343,344
a-hats | WizardsHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:472,480,481
a-hats | Bonnet: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:518,526,527
a-hats | FeatheredHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:538,546,547
a-hats | TricorneHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:558,566,567
a-hats | JesterHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:578,586,587
a-magic-hat | MagicWizardsHat: weight=1.0, minh=20, maxh=30 | ModernUO/Projects/UOContent/Items/Clothing/Hats.cs:492,500,501
a-shirts | Shirt: weight=1.0 | ModernUO/Projects/UOContent/Items/Clothing/Shirts.cs:34
a-shirts | FancyShirt: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/Shirts.cs:22
a-shirts | Doublet: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/MiddleTorso.cs:46
a-shirts | Tunic: weight=5.0 | ModernUO/Projects/UOContent/Items/Clothing/MiddleTorso.cs:70
a-shirts | Surcoat: weight=6.0 | ModernUO/Projects/UOContent/Items/Clothing/MiddleTorso.cs:58
a-shirts | PlainDress: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/OuterTorso.cs:437
a-shirts | FancyDress: weight=3.0 | ModernUO/Projects/UOContent/Items/Clothing/OuterTorso.cs:37
a-shirts | JesterSuit: weight=4.0 | ModernUO/Projects/UOContent/Items/Clothing/MiddleTorso.cs:94
a-robes | Robe: weight=3.0 | ModernUO/Projects/UOContent/Items/Clothing/OuterTorso.cs:326
a-robes | Cloak: weight=5.0 | ModernUO/Projects/UOContent/Items/Clothing/Cloaks.cs:23
a-pants | ShortPants: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/Pants.cs:22
a-pants | LongPants: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/Pants.cs:34
a-pants | Kilt: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/OuterLegs.cs:46
a-pants | Skirt: weight=4.0 | ModernUO/Projects/UOContent/Items/Clothing/OuterLegs.cs:34
a-shoes | Sandals: weight=1.0 | ModernUO/Projects/UOContent/Items/Clothing/Shoes.cs:167
a-shoes | Shoes: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/Shoes.cs:153
a-shoes | Boots: weight=3.0 | ModernUO/Projects/UOContent/Items/Clothing/Shoes.cs:46
a-shoes | ThighBoots: weight=4.0 | ModernUO/Projects/UOContent/Items/Clothing/Shoes.cs:69
a-aprons | BodySash: weight=1.0 | ModernUO/Projects/UOContent/Items/Clothing/MiddleTorso.cs:22
a-aprons | HalfApron: weight=2.0 | ModernUO/Projects/UOContent/Items/Clothing/Waist.cs:22
a-aprons | FullApron: weight=4.0 | ModernUO/Projects/UOContent/Items/Clothing/MiddleTorso.cs:34
a-jewelry | GoldRing: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Ring.cs:23
a-jewelry | SilverRing: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Ring.cs:34
a-jewelry | WeddingRing: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Ring.cs:47
a-jewelry | GoldBracelet: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Bracelet.cs:23
a-jewelry | SilverBracelet: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Bracelet.cs:34
a-jewelry | Necklace: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Necklace.cs:23
a-jewelry | GoldNecklace: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Necklace.cs:34
a-jewelry | SilverNecklace: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Necklace.cs:56
a-jewelry | GoldBeadNecklace: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Necklace.cs:45
a-jewelry | SilverBeadNecklace: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Necklace.cs:67
a-jewelry | GoldEarrings: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Earrings.cs:23
a-jewelry | SilverEarrings: weight=0.1 | ModernUO/Projects/UOContent/Items/Jewels/Earrings.cs:34

## Classes of the assignment that are not given their own topic

Totals: 374 assigned classes. 94 have their own topic (exact `types`). 258 resolve to one of my topics through a base class: the four fallbacks BaseArmor -> a-armor, BaseShield -> a-shields, BaseClothing -> a-clothes, BaseJewel -> a-jewelry, or a derived artifact walking up to a `types` class (for example ArcaneShield -> a-shields, DeathRobe -> a-robes, HelmOfInsight -> a-helms, TunicOfFire -> a-chain). 22 fall to the general "An item" page (talismans, staff suits, holiday masks; last bullet).
No text advertises any of these. Reasons:

- Gargoyle armor (Stygian Abyss, `Core.SA`): GargishCloth/Leather/Stone/Studded Arms/Chest/Kilt/Legs Type1/Type2 (32), GargishLeatherWingArmor, GargishWoodenShield. The tailoring entries are `Core.SA`-gated (DefTailoring.cs:541); no vendor or UOR loot list has them.
- Samurai and ninja items (Samurai Empire, `Core.SE`): PlateDo, PlateMempo, PlateHiroSode, PlateSuneate, PlateHaidate, PlateHatsuburi, ChainHatsuburi, the Jingasa and Kabuto helms, LeatherDo/Mempo/HiroSode/Suneate/Haidate/Jingasa, StuddedDo/Mempo/HiroSode/Suneate/Haidate, LeatherNinja*, ClothNinja*, Kasa, Hakama, TattsukeHakama, HakamaShita, Kamishimo, the kimonos, JinBaori, Obi, the tabi, Waraji, SamuraiHelm and their artifacts. The craft entries are `Core.SE`-gated (DefBlacksmithy.cs:210-259, DefTailoring.cs:134,161,197,209,264,359,436).
- Elven and Mondain's Legacy items (`Core.ML`): the Elven* clothing, Leaf* and Hide* armor, Woodland* plate, Raven/Vulture/Winged helms, Circlet, RoyalCirclet, GemmedCirclet, WoodlandBelt, FemaleElvenPlateChest, all the *Glasses (ElvenGlasses family), SpiritualityHelm, ValorGauntlets and the ML craftables BrambleCoat, IronwoodCrown, SongWovenMantle, SpellWovenBritches, StitchersMittens, HelmOfSwiftness.
- Age of Shadows or later: ChaosShield and OrderShield (blacksmith entries are `Core.AOS`-gated, DefBlacksmithy.cs:283-286), FlowerGarland, FurBoots, FurCape, FurSarong, GildedDress, FormalShirt (tailoring entries `Core.AOS`), BearMask and DeerMask (only in `AosHatTypes`), PolarBearMask, SpiritOfTheTotem.
- Dragon and daemon armor (DragonArms/Chest/Gloves/Helm/Legs, DaemonArms/Chest/Gloves/Helm/Legs): coded and, for dragon, in the blacksmith craft list (DefBlacksmithy.cs:655-680, scales, not `Core`-gated) but absent from the T2A blacksmith menu (T2A/BlacksmithMenu.cs:27-48), from every vendor list and from the `Loot` lists. Left out.
- RangerArms/Chest/Gloves/Gorget/Legs: in no vendor, craft or loot list.
- Artifacts, quest and reward items (86; no vendor, craft or standard loot source): ANecromancerShroud, AcidProofRobe, Aegis, AegisOfGrace, AlchemistsBauble, AnOldNecklace, AnOldRing, ArcaneShield, ArmorOfFortune, ArmsOfArmstrong, BraceletOfBinding, BraceletOfHealth, BraceletOfResilience, BulwarkLeggings, BurglarsBandana, CaptainJohnsHat, ClaspOfConcentration, CraftysFishingHat, CrimsonCincture, CrownOfTalKeesh, DeathRobe, DetectiveBoots, DivineCountenance, DjinnisRing, DreadPirateHat, DupresShield, EarringsOfProtection, EmbroideredOakLeafCloak, EscutcheonDeAriadne, EssenceOfBattle, FeyLeggings, GauntletsOfNobility, GladiatorsCollar, GlovesOfSafeguarding, GlovesOfThePugilist, GuantletsOfAnger, GustarShroud, HatOfTheMagi, HealersTouch, HeartOfTheLion, HelmOfInsight, HolyKnightsBreastplate, HoodedShroudOfShadows, HornedTribalMask, HuntersHeaddress, InquisitorsResolution, JackalsCollar, JesterHatofChuckles, LeggingsOfBane, LeggingsOfEmbers, LieutenantOfTheBritannianRoyalGuard, LuckyNecklace, MidnightBracers, MonkRobe, OrcChieftainHelm, OrcishKinMask, OrcishVisage, OrnamentOfTheMagician, OrnateCrownOfTheHarrower, PadsOfTheCuSidhe, PendantOfTheMagi, PhilosophersHat, ReginasRing, ResilientBracer, RewardCloak, RewardDress, RewardRobe, RingOfTheElements, RingOfTheSavant, RingOfTheVile, RobeOfTheEclipse, RobeOfTheEquinox, SamaritanRobe, SavageMask, ShadowDancerLeggings, ShieldOfInvulnerability, ShroudOfDeciet, TheMostKnowledgePerson, TheRobeOfBritanniaAri, TransparentHeart, TribalMask, TunicOfFire, TunicOfGuarding, VioletCourage, VoiceOfTheFallenKing, WaterloggedBoots. OrcishKinMask, SavageMask, TribalMask and HornedTribalMask are tribal disguises (the savage spawns are in `excludedSpawnerTypes` of world-generation.json). MonkRobe is sold only by the Tokuno monk vendor. The Reward* items are veteran rewards, disabled by `vetRewards.enable False` in modernuo-era-gates.json. Derived ones show the family topic through the base-class walk; their special properties are AoS-style and inert in this era, so the family text is not wrong for them, only incomplete. I did not check treasure-map chests or every monster loot table for artifacts; "no source" means none found in the vendor lists, craft menus, `Loot.cs` lists and spawn data I read.
- Left to the general "An item" page (22): talismans (Mondain's Legacy) BaseFormTalisman, BaseTalisman, BloodwoodSpirit, CuSidheFormTalisman, FerretFormTalisman, RandomTalisman, ReptalonFormTalisman, SquirrelFormTalisman, TotemOfVoid; staff and event suits (BaseSuit) AdminRobe, CounselorRobe, DeathShroud, DupreSuit, GMRobe, LordBlackthorneSuit, LordBritishSuit, SeerRobe; holiday masks (BasePaintedMask) PaintedDaemonMask, PaintedEvilClownMask, PaintedEvilJesterMask, PaintedPlagueMask, PaintedPorcelainMask.

## OPEN:
- OPEN: BaseClothing.OnHit looks like an upstream bug that matters for combat: `damageTaken = Math.Min(absorbed, damageTaken)` (Items/Clothing/BaseClothing.cs:325-331; the line comes from the upstream commit "Code cleanup (#188)", found with `git log -S` in ModernUO). RunUO subtracted the absorbed amount. As written, a blow that lands on a worn hat (head, 15 in 100), shirt or pants (chest 35, legs 22; `ChestArmor` is InnerTorso ?? Shirt, `LegsArmor` is InnerLegs ?? Pants, Mobile.cs:2355-2357) is cut to at most 1 to 4 damage, so a character in plain clothes would take almost nothing on about 70 percent of hits. No text depends on it (the topics only say clothing gives no armor rating). Follow ModernUO/CLAUDE.md workflow rule 1 before touching it; the owner decides.
- OPEN: Colored leather (spined +10, horned +13, barbed +16 rating, BaseArmor.cs:317-319; tailor skill 65/80/99 in DefTailoring.cs `AddSubRes`) left out: the T2A tailoring leather branch (`TailoringMenu.TrySelectResource`, leather or hides -> `Category.LeatherMain`, TailoringMenu.cs:337-347) does not set a leather sub-resource, so I could not show that a player can choose it.
- OPEN: Bone armor and the OrcHelm are in the tailoring craft list (DefTailoring.cs, group 1049149) but the T2A tailoring menu has no bone category (TailoringMenu.cs:11-23), so a player cannot make them; the text says only that skeletons carry bone armor and that monsters drop the orc helm. If bone crafting is meant to work, the menu needs a category.
- OPEN: Dragon armor craft entries are not `Core`-gated in DefBlacksmithy.cs (they need scales) but are missing from the T2A blacksmith menu and have no vendor or loot source; left out. Same for Daemon and Ranger armor.
- OPEN: Tile names for graphics 0x140C and 0x140E look swapped relative to the classes (tiledata name of 0x140C is "norse helm", of 0x140E is "bascinet", while Bascinet uses 0x140C and NorseHelm 0x140E). The topic uses the class names (as the craft menu does); the client may label a Bascinet "norse helm". I could not read the compressed Cliloc.enu to settle which label the client shows.
- OPEN: CLAUDE.md says starter items are "newbied and permanently bound", but `StarterCombatIssuance.cs:10-12` and `docs/Alpha-3-Starter-Combat-Readiness.md` say newbied only, not bound (owner ruling 2026-09-28), plus a vendor-sale guard. The gated paragraph says only what the code does: kept on death unless the player is a murderer, and shopkeepers refuse them. Trade is not mentioned.
- OPEN: Leather, studded and bone armor and clothing cannot be repaired by anyone (tailoring `Repair = Core.AOS`; the blacksmith list excludes them). The armor text says so. Whether tailors should repair leather is a design question.
- OPEN: The rating shares (helm 14, arms 15) differ from the hit chances (head 15, arms 14) in the stock tables (BaseArmor.cs:517 vs BaseWeapon.cs:1738-1743). The text states both without comment.
- OPEN: T2A jeweler crafting consumes the entire targeted gem stack on success and requires a gem to start (TinkeringMenu.cs:377-378,486-540; BaseJewel.cs:186-206). The text warns the player; whether that is intended is the owner's call.
- OPEN: I did not describe the Young-player protection (PlayerMobile.cs:2509-2551 moves every item to the pack on death for a Young player) or the Knocked Out looting rules for worn armor; they belong to other pages.

## Coordinator decisions
- The topics rely on `TopicFor` walking base classes for `types` (HelpCatalog.cs:419-433), although the brief says `types` are exact classes. If you intend `types` to be exact only, the derived artifacts (ArcaneShield, DeathRobe, ...) fall to the four fallbacks instead; nothing in my topics breaks either way.
- a-armor is about 2,700 characters (the shared-rules page for every armor piece, above the 900 guideline) and a-shields about 1,700. The per-family pages are 330 to 930 characters.
- Cross-area wording: a-clothes mentions Dyes, dye tubs and scissors in prose only (they belong to the tools area); a-armor names the Item Identification, Arms Lore and Stealth skills and the smith's hammer or tongs in prose. Make sure the other writers do not contradict the dye steps (double-click Dyes, target the tub, pick a color; then double-click the tub and target the clothing: Dyes.cs:20-55, DyeTub.cs:86-125).
- Six paragraphs carry `"requires": "Alpha3StarterCombatGear"` (a heading plus a paragraph each in a-armor, a-leather and a-shields); with the flag off both vanish together.
- Links: skills Blacksmith/Tailoring/Carpentry/Tinkering/Parry/ArmsLore/Magery are used on the topics; the skill-page writers will see these topics listed on their pages automatically.
