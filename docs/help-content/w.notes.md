# Weapons item topics (key prefix w-): notes

Writer: weapons item-topic agent, 2026-10-11. Output: `parts/w.items.json` (17 topics). Era = UOR (`DIST/Configuration/expansion.json:7-14`: T2A true, UOR true, UOTD/AOS/SE/ML false), so every `Old*` weapon property is the live one (`BaseWeapon.cs` getters pick `Aos*` only when `Core.AOS`).

Path shorthand: UOC = `ModernUO/Projects/UOContent`, SRV = `ModernUO/Projects/Server`, DIST = `ModernUO/Distribution`, SC = `ShardContent/src/BritanniaRenaissance.Content`, CFG = `ShardContent/data/configuration`. `BaseWeapon.cs` = `UOC/Items/Weapons/BaseWeapon.cs`. Item-class files are under `UOC/Items/` (listed with that prefix removed in the generated lines).

Hand-ness (one- or two-handed) of a weapon that does not set `Layer` itself is the `Quality` byte of its graphic in `UOData/tiledata.mul` (`BaseWeapon.cs:250` `Layer = (Layer)ItemData.Quality`; reader `SRV/TileData.cs:355-364`; Layer 1 = OneHanded, 2 = TwoHanded). I decoded the file with my own script (HS layout, 41-byte item records, records start after 512 x (4 + 32 x 30) bytes of land data); the item names it prints match the graphics, so the offsets are right. The shield graphics read 2 (TwoHanded), which is why a two-handed weapon and a shield cannot be worn together.

## Topics

| key | title | types / inherits | links |
| --- | --- | --- | --- |
| w-weapon | A weapon |  ; inherits: BaseWeapon | Tactics, Anatomy, ArmsLore, Blacksmith |
| w-sword | Swords | types: Broadsword, Cutlass, Katana, Longsword, Scimitar, ThinLongsword, VikingSword | Swords, Parry, Blacksmith, w-weapon |
| w-fencing | Dagger and kryss | types: Dagger, Kryss | Fencing, Parry, Blacksmith, w-weapon |
| w-knife | Knives | types: ButcherKnife, Cleaver, SkinningKnife | Swords, Tinkering, w-sword, w-fencing |
| w-spear | Spears and forks | types: Spear, ShortSpear, Pitchfork, WarFork | Fencing, Blacksmith, w-fencing, w-weapon |
| w-axe | Axes | types: Axe, BattleAxe, DoubleAxe, ExecutionersAxe, LargeBattleAxe, TwoHandedAxe, WarAxe | Swords, Lumberjacking, Blacksmith, w-hatchet |
| w-hatchet | Hatchet | types: Hatchet | Lumberjacking, Tinkering, w-axe |
| w-pickaxe | Pickaxes | types: Pickaxe, GargoylesPickaxe | Mining, Tinkering, w-axe |
| w-mace | Maces and clubs | types: Club, Mace, Maul, WarMace, WarHammer, HammerPick | Macing, Parry, Blacksmith, w-staff |
| w-staff | Staves | types: BlackStaff, GnarledStaff, QuarterStaff | Macing, Carpentry, w-mace, w-crook |
| w-crook | Shepherd's crook | types: ShepherdsCrook | Herding, AnimalTaming, w-staff |
| w-polearm | Pole arms | types: Bardiche, Halberd | Swords, Blacksmith, Lumberjacking, w-hatchet |
| w-bow | Bow | types: Bow | Archery, Fletching, w-ammo, w-crossbow |
| w-crossbow | Crossbows | types: Crossbow, HeavyCrossbow | Archery, Fletching, w-ammo, w-bow |
| w-ammo | Arrows and bolts | types: Arrow, Bolt | Archery, Fletching, w-bow, w-crossbow |
| w-wand | Wands |  ; inherits: BaseWand | ItemID, w-weapon |
| w-quiver | Quiver |  ; inherits: BaseQuiver | Archery, w-ammo, w-bow |

Flagged paragraphs: `HarvestAutoRepeat` (w-hatchet, w-pickaxe), `Alpha3StarterCombatGear` (w-ammo). Both are real `DeferredFeatureFlags` names (`SC/ShardRulesConfiguration.cs:797`, `:815`) and are `true` in `CFG/shard-rules.json:204,210`.

## Claims (topic | claim | source)

### w-weapon (A weapon, inherits BaseWeapon)
w-weapon | Equip it to fight with it; the swing uses the equipped weapon | SRV/Mobiles/Mobile.cs:801-835 (`CheckCombatTime`: `var weapon = Weapon`, in range `weapon.MaxRange` line 821, `InLOS` line 826, `weapon.OnSwing`)
w-weapon | Each kind uses one combat skill: Swordsmanship (swords, knives other than the Dagger, axes except the War axe, pole arms), Mace Fighting (BaseBashing, BaseStaff, War axe), Fencing (BaseSpear, Dagger, Kryss), Archery (BaseRanged) | UOC/Items/Weapons/Swords/BaseSword.cs:13; Knives/BaseKnife.cs:16; Axes/BaseAxe.cs:32; PoleArms/BasePoleArm.cs:27; Maces/BaseBashing.cs:15; Staves/BaseStaff.cs:15; Axes/WarAxe.cs:37; SpearsAndForks/BaseSpear.cs:15; Swords/Kryss.cs:36; Knives/Dagger.cs:33; Ranged/BaseRanged.cs:34; `Skill` returns `OldSkill`->`DefSkill` when not AOS: BaseWeapon.cs:632-635
w-weapon | With empty hands you fight with Wrestling | UOC/Items/Weapons/Fists.cs:36 (`DefSkill => Wrestling`), :42 (`Mobile.DefaultWeapon = new Fists()`)
w-weapon | You need at least the weapon's Strength requirement to equip it; otherwise You are not strong enough to equip that | BaseWeapon.cs:1069-1074 (players only), :1092-1096 (message cliloc 500213, comment line 1094), :454-457 (`StrRequirement` = `OldStrengthReq` when not AOS), :1010-1013 (`GetLowerStatReq` = 0 when not AOS)
w-weapon | A two-handed weapon cannot be used with a shield; a one-handed weapon can | BaseWeapon.cs:1042-1062 (`CheckConflictingLayer`) with SRV/Mobiles/Mobile.cs:7806-7807 (both directions); shields take `Layer = ItemData.Quality` = 2 = TwoHanded (UOC/Items/Armor/BaseArmor.cs:155, :504; tiledata items 0x1B73 and 0x1B7A quality 2)
w-weapon | Each hit rolls between the weapon's lowest and highest damage | BaseWeapon.cs:2530-2534 (`GetBaseDamage` = `Utility.RandomMinMax(min, max)`)
w-weapon | Tactics, Strength and Anatomy then change the damage | BaseWeapon.cs:2693 (Tactics: `damage += damage * ((tactics - 50) / 100)`), :2698 (Strength / 5 / 100), :2705 (Anatomy / 5 / 100); called by `ComputeDamage` :2765 (not AOS)
w-weapon | A worn weapon does less, down to half with no durability left | BaseWeapon.cs:2743, :2746-2756 (`scale = 50 + 50 * hitPoints / maxHitPoints`)
w-weapon | The target's armor and shield take some damage away | BaseWeapon.cs:1722-1771 (non-AOS `AbsorbDamage`: shield `OnHit`, armor piece, virtual armor), called :1952; UOC/Items/Shields/BaseShield.cs:50-76
w-weapon | A hit on another player does half damage | BaseWeapon.cs:2767-2771 (`defender is PlayerMobile || attacker is not PlayerMobile` -> `damage /= 2`)
w-weapon | A swing takes 15000 / ((stamina + 100) x speed) seconds; 75 / speed at 100 stamina; higher speed swings faster | BaseWeapon.cs:1555-1565 (non-AOS branch of `GetDelay`: `v = (stamina + 100) * speed`, `15000.0 / v`); `Speed` = `OldSpeed` when not AOS/ML :578-597; 15000 / (200 x speed) = 75 / speed. Confirmed independently by ShardContent/docs/Novice-Combat-Assist-Evidence.md (Bow speed 20: 3.75 s at stamina 100)
w-weapon | Your stamina can never be higher than your Dexterity | SRV/Mobiles/Mobile.cs:2166 (`StamMax => Dex`); UOC/Mobiles/PlayerMobile.cs:582 adds only the AOS BonusStam attribute (0 here)
w-weapon | The Skill Guide ([SkillGuide) explains the weapon skill, Tactics and Anatomy | ShardContent/docs/Help-Content-Spec.md line 68 (`[SkillGuide` exists); the fighting skill pages in parts/fighting.skills.json carry the same facts
w-weapon | About one hit in 25 costs a weapon a point of durability | BaseWeapon.cs:2088 (`if (damageGiven > 0)`), :2148 (`Utility.Random(25) == 0`), :2161 (`--HitPoints`); non-AOS `AOS.Damage` returns the damage dealt: UOC/Misc/AOS.cs:63-67
w-weapon | Slimes and acid elementals cost a melee weapon a point on every hit | BaseWeapon.cs:2143-2146 (`isAcidMonster = _maxHitPoints > 0 && MaxRange <= 1 && ... defender is Slime or AcidElemental`), :2148, message *Acid blood scars your weapon!* :2152; Slime and AcidElemental are in the world: DIST/Data/BritanniaRenaissance/Alpha2b/Spawns/Covetous.json, Fire.json, Outdoors.json (Slime); Despise.json, Outdoors.json, Shame.json (AcidElemental)
w-weapon | With no durability left it starts to lose its maximum; when that is used up it breaks and is gone | BaseWeapon.cs:2159-2176 (`hitPoints > 0` -> `--HitPoints`; `else if maxHitPoints > 1` -> `--MaxHitPoints` with message 1061121; else `Delete()`)
w-weapon | Arms Lore tells you a weapon's condition and how hard it hits | UOC/Skills/ArmsLore.cs:29-90 (condition from hit points 1038285+, damage class from the average of min and max, hand and weapon type)
w-weapon | A Blacksmith can repair the weapons a Blacksmith can forge | UOC/Engines/Craft/Core/Repair.cs:263-268 (`CraftItems.SearchForSubclass(weapon.GetType()) == null && !IsSpecialWeapon` refuses); `IsSpecialWeapon` (Repair.cs:100-116) for the Blacksmith system lists only Pitchfork and ML items (line 116)
w-weapon | Choose Repair in the Blacksmith menu | UOC/Engines/Craft/T2A/BlacksmithMenu.cs:214 (`ItemListEntry("Repair"...)`), :431 (`Repair.Do`); T2A menus are the live ones (`t2aCraftMenus` defaults to `!Core.UOTD`: UOC/Configuration/ExpansionConfiguration.cs:15); ShardContent WelcomeGuide.GettingStarted.cs:244-247 says the same
w-weapon | Near a forge and anvil | Repair.cs:165-167 (`CanCraft == 1044267` -> 1044282 You must be near a forge and an anvil to repair items); WelcomeGuide.GettingStarted.cs:247
w-weapon | With the weapon in your backpack | Repair.cs:269-271 (`!weapon.IsChildOf(from.Backpack) && (!Core.ML || weapon.Parent != from)` -> 1044275)
w-weapon | And no poison on it | Repair.cs:273-275 (`!Core.AOS && weapon.PoisonCharges != 0` -> 1005012)
w-weapon | A repair can lower its maximum a little | Repair.cs:41-46 (weaken chance 40 + (max - current) - skill/10 percent), :287-290 (`MaxHitPoints -= toWeaken`), toWeaken 3/2/1 by skill below 70/70/90: :249-260
w-weapon | Some weapons from monsters or treasure chests are magical | UOC/Misc/LootPack.cs:753-766 (non-AOS: accuracy 80%, damage 60%, durability 40%), LootPackItem(BaseWeapon) :35, :181; UOC/Items/TreasureChests/TreasureChestLevel3.cs:78-90 (treasure chest weapons get damage/accuracy/durability levels); chests are spawned in the dungeons: DIST/Data/BritanniaRenaissance/Alpha2b/Spawns/Covetous.json etc. (TreasureChestLevel1..4)
w-weapon | A magical weapon reads as unidentified until Item Identification is used on it | BaseWeapon.cs:3304-3315 (`OnSingleClickPreUOTD`, Core.UOTD is false so this path runs: BaseWeapon.cs:3207-3211), UOC/Skills/ItemIdentification.cs:44-47 (`identifiable.Identified = true`); ObjectPropertyList is off (`opl.enable` defaults to `Core.AOS`: UOC/Configuration/ExpansionConfiguration.cs:10; not set in DIST/Configuration/modernuo.json), so there are no tooltips and the single-click name is how a player sees it
w-weapon | Accuracy steps add 5, 10, 15, 20, 25 to Tactics (Archery for a bow or crossbow) | BaseWeapon.cs:276 (`UseSkillMod => !Core.AOS`), :349-382 and :1149 (`new DefaultSkillMod(AccuracySkill, "WeaponAccuracy", true, (int)_accuracyLevel * 5)`), :339 (`AccuracySkill => Tactics`), UOC/Items/Weapons/Ranged/BaseRanged.cs:38 (`AccuracySkill => Archery`); step names WeaponEnums.cs:32-40
w-weapon | Ruin, might, force, power, vanquishing add 1, 3, 5, 7, 9 to each damage roll | BaseWeapon.cs:2549-2561 (`Core.T2A`: `damage += 2 * (int)_damageLevel - 1`; Core.T2A is true: DIST/Configuration/expansion.json:7); enum order WeaponEnums.cs:22-29
w-weapon | Durable, substantial, massive, fortified, indestructible add 20%, 50%, 70%, 100%, 120% to durability | BaseWeapon.cs:984-1008 (`Core.UOR` branch lines 991-999), scaling :829-845
w-weapon | An exceptional weapon does 20% more damage and has 20% more durability | BaseWeapon.cs:2729-2732 (`modifiers += ((int)_quality - 1) * 0.2`; WeaponEnums.cs:3-8 Low 0, Regular 1, Exceptional 2), :1007 (`_quality == Exceptional ? bonus + 20`)
w-weapon | Shopkeepers pay about half of what they charge, plus 100 gold per step of ruin or durability | UOC/Mobiles/Vendors/BaseVendor.cs:561 (player is paid `GetSellPriceFor`), UOC/Mobiles/Vendors/GenericSell.cs:94-95 (`price += 100 * DurabilityLevel`, `price += 100 * DamageLevel`); typical pairs: Longsword buy 55 / pays 27, Katana 33 / 16, Bow 35 / 17 (SBBlacksmith.cs:68,218; :65,216; :57,184)
w-weapon | Shopkeepers will not buy newbied gear such as the starting weapon, which you keep when you die | GenericSell.cs:35-39 (`ContainsVendorRestricted`: Nontransferable or Newbied), :153,155; starting gear is made Newbied when not AOS: UOC/Engines/Character Creation/CharacterCreation.cs:734-737; the keep-on-death part is stated in SC/WelcomeGuide.GettingStarted.cs:64

### Generated per-weapon lines (stats, hands, shop prices, crafting)

Each weapon's numbers in the lists of w-sword, w-fencing, w-knife, w-spear, w-axe, w-hatchet, w-pickaxe, w-mace, w-staff, w-crook, w-polearm, w-bow and w-crossbow. Line numbers inside the class file are the `DefaultWeight`, `OldStrengthReq`, `OldMinDamage`, `OldMaxDamage`, `OldSpeed`, `InitMinHits`, `InitMaxHits` (and `DefMaxRange` for ranged) lines. Shop lines name the shop and the line in `UOC/Mobiles/Vendors/SBInfo/SBBlacksmith.cs` (Blacksmith), `SBWeaponSmith.cs` (Weaponsmith), `Weapons/SBRangedWeapon.cs` (Bowyer), `Weapons/SBStavesWeapon.cs` (Carpenter). "Blacksmith pays N" is the sell table in the same file. Craft lines are `Engines/Craft/Def*.cs`.

w-sword | Broadsword: Str 25, damage 5 to 29, speed 45, weight 6.0 stones, durability 31 to 100 | Items/Weapons/Swords/Broadsword.cs:14,25-28,33-34
w-sword | Broadsword hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF5E quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-sword | Broadsword price: Blacksmith sells at 35 (line 67); Weaponsmith sells at 35 (line 63); Blacksmith pays 17 (line 214) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-sword | Broadsword craft: AddCraft(typeof(Broadsword), 1011081, 1023934, 35.4, 85.4, typeof(IronIngot), 1044036, 10, 1044037); | DefBlacksmithy.cs:294
w-sword | Cutlass: Str 10, damage 6 to 28, speed 45, weight 8.0 stones, durability 31 to 70 | Items/Weapons/Swords/Cutlass.cs:14,25-28,33-34
w-sword | Cutlass hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x1441 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-sword | Cutlass price: Blacksmith sells at 24 (line 61); Weaponsmith sells at 24 (line 55); Blacksmith pays 12 (line 215) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-sword | Cutlass craft: AddCraft(typeof(Cutlass), 1011081, 1025185, 24.3, 74.3, typeof(IronIngot), 1044036, 8, 1044037); | DefBlacksmithy.cs:301
w-sword | Katana: Str 10, damage 5 to 26, speed 58, weight 6.0 stones, durability 31 to 90 | Items/Weapons/Swords/Katana.cs:14,25-28,33-34
w-sword | Katana hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13FF quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-sword | Katana price: Blacksmith sells at 33 (line 65); Weaponsmith sells at 33 (line 61); Blacksmith pays 16 (line 216) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-sword | Katana craft: AddCraft(typeof(Katana), 1011081, 1025119, 44.1, 94.1, typeof(IronIngot), 1044036, 8, 1044037); | DefBlacksmithy.cs:303
w-sword | Longsword: Str 25, damage 5 to 33, speed 35, weight 7.0 stones, durability 31 to 110 | Items/Weapons/Swords/Longsword.cs:14,25-28,33-34
w-sword | Longsword hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF61 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-sword | Longsword price: Blacksmith sells at 55 (line 68); Weaponsmith sells at 55 (line 64); Blacksmith pays 27 (line 218) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-sword | Longsword craft: AddCraft(typeof(Longsword), 1011081, 1023937, 28.0, 78.0, typeof(IronIngot), 1044036, 12, 1044037); | DefBlacksmithy.cs:305
w-sword | Scimitar: Str 10, damage 4 to 30, speed 43, weight 5.0 stones, durability 31 to 90 | Items/Weapons/Swords/Scimitar.cs:14,25-28,33-34
w-sword | Scimitar hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13B6 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-sword | Scimitar price: Blacksmith sells at 36 (line 76); Weaponsmith sells at 36 (line 75); Blacksmith pays 18 (line 219) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-sword | Scimitar craft: AddCraft(typeof(Scimitar), 1011081, 1025046, 31.7, 81.7, typeof(IronIngot), 1044036, 10, 1044037); | DefBlacksmithy.cs:306
w-sword | ThinLongsword: Str 25, damage 5 to 33, speed 35, weight 1.0 stones, durability 31 to 110 | Items/Weapons/Swords/ThinLongsword.cs:14,22-25,30-31
w-sword | ThinLongsword hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13B8 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-sword | ThinLongsword price: Blacksmith sells at 27 (line 69); Weaponsmith sells at 27 (line 65); Blacksmith pays 13 (line 220) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-sword | VikingSword: Str 40, damage 6 to 34, speed 30, weight 6.0 stones, durability 31 to 100 | Items/Weapons/Swords/VikingSword.cs:14,25-28,33-34
w-sword | VikingSword hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13B9 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-sword | VikingSword price: Blacksmith sells at 55 (line 70); Weaponsmith sells at 55 (line 66); Blacksmith pays 27 (line 221) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-sword | VikingSword craft: AddCraft(typeof(VikingSword), 1011081, 1025049, 24.3, 74.3, typeof(IronIngot), 1044036, 14, 1044037); | DefBlacksmithy.cs:307
w-fencing | Dagger: Str 1, damage 3 to 15, speed 55, weight 1.0 stones, durability 31 to 40 | Items/Weapons/Knives/Dagger.cs:14,25-28,30-31
w-fencing | Dagger hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF52 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-fencing | Dagger price: Blacksmith sells at 21 (line 62); Weaponsmith sells at 21 (line 56); Blacksmith pays 10 (line 173) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-fencing | Dagger craft: AddCraft(typeof(Dagger), 1011081, 1023921, -0.4, 49.6, typeof(IronIngot), 1044036, 3, 1044037); | DefBlacksmithy.cs:302
w-fencing | Kryss: Str 10, damage 3 to 28, speed 53, weight 2.0 stones, durability 31 to 90 | Items/Weapons/Swords/Kryss.cs:14,25-28,33-34
w-fencing | Kryss hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x1401 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-fencing | Kryss price: Blacksmith sells at 32 (line 66); Weaponsmith sells at 32 (line 62); Blacksmith pays 16 (line 217) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-fencing | Kryss craft: AddCraft(typeof(Kryss), 1011081, 1025121, 36.7, 86.7, typeof(IronIngot), 1044036, 8, 1044037); | DefBlacksmithy.cs:304
w-knife | ButcherKnife: Str 5, damage 2 to 14, speed 40, weight 1.0 stones, durability 31 to 40 | Items/Weapons/Knives/ButcherKnife.cs:14,25-28,30-31
w-knife | ButcherKnife hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13F6 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-knife | ButcherKnife price: Blacksmith sells at 14 (line 58); Weaponsmith sells at 14 (line 50); Blacksmith pays 7 (line 171) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-knife | ButcherKnife craft: AddCraft(typeof(ButcherKnife), 1044048, 1025110, 25.0, 75.0, typeof(IronIngot), 1044036, 2, 1044037); | DefTinkering.cs:297
w-knife | Cleaver: Str 10, damage 2 to 13, speed 40, weight 2.0 stones, durability 31 to 50 | Items/Weapons/Knives/Cleaver.cs:14,25-28,30-31
w-knife | Cleaver hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xEC3 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-knife | Cleaver price: Blacksmith sells at 15 (line 71); Weaponsmith sells at 15 (line 68); Blacksmith pays 7 (line 172) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-knife | Cleaver craft: AddCraft(typeof(Cleaver), 1044048, 1023778, 20.0, 70.0, typeof(IronIngot), 1044036, 3, 1044037); | DefTinkering.cs:303
w-knife | SkinningKnife: Str 5, damage 1 to 10, speed 40, weight 1.0 stones, durability 31 to 40 | Items/Weapons/Knives/SkinningKnife.cs:14,25-28,30-31
w-knife | SkinningKnife hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xEC4 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-knife | SkinningKnife price: Blacksmith sells at 14 (line 77); Weaponsmith sells at 14 (line 77); Blacksmith pays 7 (line 174) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-knife | SkinningKnife craft: AddCraft(typeof(SkinningKnife), 1044048, 1023781, 25.0, 75.0, typeof(IronIngot), 1044036, 2, 1044037); | DefTinkering.cs:308
w-spear | Spear: Str 30, damage 2 to 36, speed 46, weight 7.0 stones, durability 31 to 80 | Items/Weapons/SpearsAndForks/Spear.cs:14,25-28,30-31
w-spear | Spear hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF62 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-spear | Spear price: Blacksmith sells at 31 (line 102); Weaponsmith sells at 31 (line 25); Blacksmith pays 15 (line 203) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-spear | Spear craft: AddCraft(typeof(Spear), 1011083, 1023938, 49.0, 99.0, typeof(IronIngot), 1044036, 12, 1044037); | DefBlacksmithy.cs:595
w-spear | ShortSpear: Str 15, damage 4 to 32, speed 50, weight 4.0 stones, durability 31 to 70 | Items/Weapons/SpearsAndForks/ShortSpear.cs:14,25-28,30-31
w-spear | ShortSpear hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x1403 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-spear | ShortSpear price: Blacksmith sells at 23 (line 101); Weaponsmith sells at 23 (line 24); Blacksmith pays 11 (line 205) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-spear | ShortSpear craft: AddCraft(typeof(ShortSpear), 1011083, 1025123, 45.3, 95.3, typeof(IronIngot), 1044036, 6, 1044037); | DefBlacksmithy.cs:588
w-spear | Pitchfork: Str 15, damage 4 to 16, speed 45, weight 11.0 stones, durability 31 to 60 | Items/Weapons/SpearsAndForks/Pitchfork.cs:14,25-28,30-31
w-spear | Pitchfork hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xE87 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-spear | Pitchfork price: Blacksmith sells at 19 (line 75); Weaponsmith sells at 19 (line 73); Blacksmith pays 9 (line 204) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-spear | WarFork: Str 35, damage 4 to 32, speed 45, weight 9.0 stones, durability 31 to 110 | Items/Weapons/SpearsAndForks/WarFork.cs:14,25-28,33-34
w-spear | WarFork hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x1405 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-spear | WarFork price: Weaponsmith sells at 32 (line 37) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-spear | WarFork craft: AddCraft(typeof(WarFork), 1011083, 1025125, 42.9, 92.9, typeof(IronIngot), 1044036, 12, 1044037); | DefBlacksmithy.cs:596
w-axe | Axe: Str 35, damage 6 to 33, speed 37, weight 4.0 stones, durability 31 to 110 | Items/Weapons/Axes/Axe.cs:14,25-28,30-31
w-axe | Axe hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF49 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-axe | Axe price: Blacksmith sells at 40 (line 72); Weaponsmith sells at 40 (line 69); Blacksmith pays 20 (line 166) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-axe | Axe craft: AddCraft(typeof(Axe), 1011082, 1023913, 34.2, 84.2, typeof(IronIngot), 1044036, 14, 1044037); | DefBlacksmithy.cs:530
w-axe | BattleAxe: Str 40, damage 6 to 38, speed 30, weight 4.0 stones, durability 31 to 70 | Items/Weapons/Axes/BattleAxe.cs:12,22-25,27-28
w-axe | BattleAxe hand-ness: TwoHanded set in the constructor (Weapons/Axes/BattleAxe.cs:10) | BaseWeapon.cs:250 (+ the file above)
w-axe | BattleAxe price: Blacksmith sells at 26 (line 55); Weaponsmith sells at 26 (line 45); Blacksmith pays 13 (line 159) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-axe | BattleAxe craft: AddCraft(typeof(BattleAxe), 1011082, 1023911, 30.5, 80.5, typeof(IronIngot), 1044036, 14, 1044037); | DefBlacksmithy.cs:531
w-axe | DoubleAxe: Str 45, damage 5 to 35, speed 37, weight 8.0 stones, durability 31 to 110 | Items/Weapons/Axes/DoubleAxe.cs:14,25-28,30-31
w-axe | DoubleAxe hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF4B quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-axe | DoubleAxe price: Blacksmith sells at 52 (line 73); Weaponsmith sells at 52 (line 70); Blacksmith pays 26 (line 160) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-axe | DoubleAxe craft: AddCraft(typeof(DoubleAxe), 1011082, 1023915, 29.3, 79.3, typeof(IronIngot), 1044036, 12, 1044037); | DefBlacksmithy.cs:532
w-axe | ExecutionersAxe: Str 35, damage 6 to 33, speed 37, weight 8.0 stones, durability 31 to 70 | Items/Weapons/Axes/ExecutionersAxe.cs:14,25-28,30-31
w-axe | ExecutionersAxe hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF45 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-axe | ExecutionersAxe price: Blacksmith sells at 30 (line 53); Weaponsmith sells at 30 (line 43); Blacksmith pays 15 (line 161) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-axe | ExecutionersAxe craft: AddCraft(typeof(ExecutionersAxe), 1011082, 1023909, 34.2, 84.2, typeof(IronIngot), 1044036, 14, 1044037); | DefBlacksmithy.cs:533
w-axe | LargeBattleAxe: Str 40, damage 6 to 38, speed 30, weight 6.0 stones, durability 31 to 70 | Items/Weapons/Axes/LargeBattleAxe.cs:14,25-28,30-31
w-axe | LargeBattleAxe hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13FB quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-axe | LargeBattleAxe price: Blacksmith sells at 33 (line 78); Weaponsmith sells at 33 (line 79); Blacksmith pays 16 (line 162) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-axe | LargeBattleAxe craft: AddCraft(typeof(LargeBattleAxe), 1011082, 1025115, 28.0, 78.0, typeof(IronIngot), 1044036, 12, 1044037); | DefBlacksmithy.cs:534
w-axe | TwoHandedAxe: Str 35, damage 5 to 39, speed 30, weight 8.0 stones, durability 31 to 90 | Items/Weapons/Axes/TwoHandedAxe.cs:14,25-28,30-31
w-axe | TwoHandedAxe hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x1443 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-axe | TwoHandedAxe price: Blacksmith sells at 32 (line 56); Weaponsmith sells at 32 (line 46); Blacksmith pays 16 (line 164) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-axe | TwoHandedAxe craft: AddCraft(typeof(TwoHandedAxe), 1011082, 1025187, 33.0, 83.0, typeof(IronIngot), 1044036, 16, 1044037); | DefBlacksmithy.cs:535
w-axe | WarAxe: Str 35, damage 9 to 27, speed 40, weight 8.0 stones, durability 31 to 80 | Items/Weapons/Axes/WarAxe.cs:15,26-29,34-35
w-axe | WarAxe hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13B0 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-axe | WarAxe price: Blacksmith sells at 29 (line 79); Weaponsmith sells at 29 (line 80); Blacksmith pays 14 (line 165) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-axe | WarAxe craft: AddCraft(typeof(WarAxe), 1011082, 1025040, 39.1, 89.1, typeof(IronIngot), 1044036, 16, 1044037); | DefBlacksmithy.cs:536
w-hatchet | Hatchet: Str 15, damage 2 to 17, speed 40, weight 4.0 stones, durability 31 to 80 | Items/Weapons/Axes/Hatchet.cs:14,25-28,30-31
w-hatchet | Hatchet hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF43 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-hatchet | Hatchet price: Weaponsmith sells at 25, 27 (line 35, 36) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-hatchet | Hatchet craft: AddCraft(typeof(Hatchet), 1044046, 1023907, 30.0, 80.0, typeof(IronIngot), 1044036, 4, 1044037); | DefTinkering.cs:250
w-pickaxe | Pickaxe: Str 25, damage 1 to 15, speed 35, weight 11.0 stones, durability 31 to 60 | Items/Weapons/Axes/Pickaxe.cs:19,31-34,36-37
w-pickaxe | Pickaxe hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xE86 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-pickaxe | Pickaxe price: Blacksmith sells at 22 (line 74); Weaponsmith sells at 22 (line 71); Blacksmith pays 11 (line 163) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-pickaxe | Pickaxe craft: AddCraft(typeof(Pickaxe), 1044046, 1023718, 40.0, 90.0, typeof(IronIngot), 1044036, 4, 1044037); | DefTinkering.cs:262
w-pickaxe | GargoylesPickaxe: Str 25, damage 1 to 15, speed 35, weight 11.0 stones, durability 31 to 60 | Items/Skill Items/Harvest Tools/GargoylesPickaxe.cs:21,35-38,40-41
w-pickaxe | GargoylesPickaxe hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xE85 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-pickaxe | GargoylesPickaxe price: not sold by the shops read | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-mace | Club: Str 10, damage 8 to 24, speed 40, weight 9.0 stones, durability 31 to 40 | Items/Weapons/Maces/Club.cs:14,25-28,30-31
w-mace | Club hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13B4 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-mace | Club price: Blacksmith sells at 16 (line 94); Weaponsmith sells at 16 (line 17); Blacksmith pays 8 (line 176) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-mace | Mace: Str 20, damage 8 to 32, speed 30, weight 14.0 stones, durability 31 to 70 | Items/Weapons/Maces/Mace.cs:14,25-28,30-31
w-mace | Mace hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF5C quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-mace | Mace price: Blacksmith sells at 28 (line 96); Weaponsmith sells at 28 (line 19); Blacksmith pays 14 (line 178) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-mace | Mace craft: AddCraft(typeof(Mace), 1011084, 1023932, 14.5, 64.5, typeof(IronIngot), 1044036, 6, 1044037); | DefBlacksmithy.cs:602
w-mace | Maul: Str 20, damage 10 to 30, speed 30, weight 10.0 stones, durability 31 to 70 | Items/Weapons/Maces/Maul.cs:14,25-28,30-31
w-mace | Maul hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x143B quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-mace | Maul price: Blacksmith sells at 21 (line 97); Weaponsmith sells at 21 (line 20); Blacksmith pays 10 (line 179) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-mace | Maul craft: AddCraft(typeof(Maul), 1011084, 1025179, 19.4, 69.4, typeof(IronIngot), 1044036, 10, 1044037); | DefBlacksmithy.cs:603
w-mace | WarMace: Str 30, damage 10 to 30, speed 32, weight 17.0 stones, durability 31 to 110 | Items/Weapons/Maces/WarMace.cs:14,25-28,30-31
w-mace | WarMace hand-ness: OneHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x1407 quality byte = 1 | BaseWeapon.cs:250 (+ the file above)
w-mace | WarMace price: Blacksmith sells at 31 (line 104); Weaponsmith sells at 31 (line 27); Blacksmith pays 15 (line 181) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-mace | WarMace craft: AddCraft(typeof(WarMace), 1011084, 1025127, 28.0, 78.0, typeof(IronIngot), 1044036, 14, 1044037); | DefBlacksmithy.cs:610
w-mace | WarHammer: Str 40, damage 8 to 36, speed 31, weight 10.0 stones, durability 31 to 110 | Items/Weapons/Maces/WarHammer.cs:12,22-25,27-28
w-mace | WarHammer hand-ness: TwoHanded set in the constructor (Weapons/Maces/WarHammer.cs:10) | BaseWeapon.cs:250 (+ the file above)
w-mace | WarHammer price: Blacksmith sells at 25 (line 103); Weaponsmith sells at 25 (line 26); Blacksmith pays 12 (line 180) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-mace | WarHammer craft: AddCraft(typeof(WarHammer), 1011084, 1025177, 34.2, 84.2, typeof(IronIngot), 1044036, 16, 1044037); | DefBlacksmithy.cs:611
w-mace | HammerPick: Str 35, damage 6 to 33, speed 30, weight 9.0 stones, durability 31 to 70 | Items/Weapons/Maces/HammerPick.cs:12,22-25,27-28
w-mace | HammerPick hand-ness: OneHanded set in the constructor (Weapons/Maces/HammerPick.cs:10) | BaseWeapon.cs:250 (+ the file above)
w-mace | HammerPick price: Blacksmith sells at 26 (line 64); Weaponsmith sells at 26 (line 59); Blacksmith pays 13 (line 177) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-mace | HammerPick craft: AddCraft(typeof(HammerPick), 1011084, 1025181, 34.2, 84.2, typeof(IronIngot), 1044036, 16, 1044037); | DefBlacksmithy.cs:601
w-staff | QuarterStaff: Str 30, damage 8 to 28, speed 48, weight 4.0 stones, durability 31 to 60 | Items/Weapons/Staves/QuarterStaff.cs:12,22-25,27-28
w-staff | QuarterStaff hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xE89 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-staff | QuarterStaff price: Blacksmith sells at 19 (line 98); Weaponsmith sells at 19 (line 21); Carpenter/staves sells at 19 (line 18); Blacksmith pays 9 (line 209) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-staff | QuarterStaff craft: AddCraft(typeof(QuarterStaff), Core.ML ? 1044566 : 1044295, 1023721, 73.6, 98.6, typeof(Log), 1044041, 6, 1044351); | DefCarpentry.cs:306
w-staff | GnarledStaff: Str 20, damage 10 to 30, speed 33, weight 3.0 stones, durability 31 to 50 | Items/Weapons/Staves/GnarledStaff.cs:12,22-25,27-28
w-staff | GnarledStaff hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x13F8 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-staff | GnarledStaff price: Blacksmith sells at 16 (line 95); Weaponsmith sells at 16 (line 18); Carpenter/staves sells at 16 (line 17); Blacksmith pays 8 (line 208) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-staff | GnarledStaff craft: AddCraft(typeof(GnarledStaff), Core.ML ? 1044566 : 1044295, 1025112, 78.9, 103.9, typeof(Log), 1044041, 7, 1044351); | DefCarpentry.cs:307
w-staff | BlackStaff: Str 35, damage 8 to 33, speed 35, weight 6.0 stones, durability 31 to 70 | Items/Weapons/Staves/BlackStaff.cs:14,25-28,30-31
w-staff | BlackStaff hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xDF0 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-staff | BlackStaff price: Blacksmith sells at 22 (line 93); Weaponsmith sells at 22 (line 16); Carpenter/staves sells at 22 (line 16); Blacksmith pays 11 (line 207) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-crook | ShepherdsCrook: Str 10, damage 3 to 12, speed 30, weight 4.0 stones, durability 31 to 50 | Items/Weapons/Staves/ShepherdsCrook.cs:16,26-29,31-32
w-crook | ShepherdsCrook hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xE81 quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-crook | ShepherdsCrook price: Blacksmith sells at 20 (line 99); Weaponsmith sells at 20 (line 22); Carpenter/staves sells at 20 (line 19); Blacksmith pays 10 (line 210) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-crook | ShepherdsCrook craft: AddCraft(typeof(ShepherdsCrook), Core.ML ? 1044566 : 1044295, 1023713, 78.9, 103.9, typeof(Log), 1044041, 7, 1044351); | DefCarpentry.cs:305
w-polearm | Bardiche: Str 40, damage 5 to 43, speed 26, weight 7.0 stones, durability 31 to 100 | Items/Weapons/PoleArms/Bardiche.cs:14,25-28,30-31
w-polearm | Bardiche hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0xF4D quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-polearm | Bardiche price: Blacksmith sells at 60 (line 54); Weaponsmith sells at 60 (line 44); Blacksmith pays 30 (line 168) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-polearm | Bardiche craft: AddCraft(typeof(Bardiche), 1011083, 1023917, 31.7, 81.7, typeof(IronIngot), 1044036, 18, 1044037); | DefBlacksmithy.cs:564
w-polearm | Halberd: Str 45, damage 5 to 49, speed 25, weight 16.0 stones, durability 31 to 80 | Items/Weapons/PoleArms/Halberd.cs:14,25-28,30-31
w-polearm | Halberd hand-ness: TwoHanded: no Layer set, so Layer = ItemData.Quality (BaseWeapon.cs:250); tiledata.mul item 0x143E quality byte = 2 | BaseWeapon.cs:250 (+ the file above)
w-polearm | Halberd price: Blacksmith sells at 42 (line 63); Weaponsmith sells at 42 (line 57); Blacksmith pays 21 (line 169) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-polearm | Halberd craft: AddCraft(typeof(Halberd), 1011083, 1025183, 39.1, 89.1, typeof(IronIngot), 1044036, 20, 1044037); | DefBlacksmithy.cs:576
w-bow | Bow: Str 20, damage 9 to 41, speed 20, weight 6.0 stones, durability 31 to 60, range 10 | Items/Weapons/Ranged/Bow.cs:17,31-34,36,38-39
w-bow | Bow hand-ness: TwoHanded set in the constructor (Weapons/Ranged/Bow.cs:13) | BaseWeapon.cs:250 (+ the file above)
w-bow | Bow price: Blacksmith sells at 35 (line 57); Weaponsmith sells at 35 (line 48); Bowyer sells at 40 (line 25); Blacksmith pays 17 (line 184) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-bow | Bow craft: AddCraft(typeof(Bow), 1044566, 1025042, 30.0, 70.0, typeof(Log), 1044041, 7, 1044351); | DefBowFletching.cs:116
w-crossbow | Crossbow: Str 30, damage 8 to 43, speed 18, weight 7.0 stones, durability 31 to 80, range 8 | Items/Weapons/Ranged/Crossbow.cs:17,31-34,36,38-39
w-crossbow | Crossbow hand-ness: TwoHanded set in the constructor (Weapons/Ranged/Crossbow.cs:13) | BaseWeapon.cs:250 (+ the file above)
w-crossbow | Crossbow price: Blacksmith sells at 46 (line 59); Weaponsmith sells at 46 (line 52); Bowyer sells at 55 (line 16); Blacksmith pays 23 (line 185) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-crossbow | Crossbow craft: AddCraft(typeof(Crossbow), 1044566, 1023919, 60.0, 100.0, typeof(Log), 1044041, 7, 1044351); | DefBowFletching.cs:117
w-crossbow | HeavyCrossbow: Str 40, damage 11 to 56, speed 10, weight 9.0 stones, durability 31 to 100, range 8 | Items/Weapons/Ranged/HeavyCrossbow.cs:17,31-34,36,38-39
w-crossbow | HeavyCrossbow hand-ness: TwoHanded set in the constructor (Weapons/Ranged/HeavyCrossbow.cs:13) | BaseWeapon.cs:250 (+ the file above)
w-crossbow | HeavyCrossbow price: Blacksmith sells at 55 (line 60); Weaponsmith sells at 55 (line 53); Bowyer sells at 55 (line 17); Blacksmith pays 27 (line 183) | SBBlacksmith.cs / SBWeaponSmith.cs / SBRangedWeapon.cs / SBStavesWeapon.cs lines as given
w-crossbow | HeavyCrossbow craft: AddCraft(typeof(HeavyCrossbow), 1044566, 1025117, 80.0, 120.0, typeof(Log), 1044041, 10, 1044351); | DefBowFletching.cs:118

### Remaining claims by topic
w-sword | Swords are one-handed blades that use Swordsmanship | generated hand-ness lines above (all q=1 in tiledata); UOC/Items/Weapons/Swords/BaseSword.cs:13
w-sword | Because they are one-handed you can carry a shield | see w-weapon (shield rule)
w-sword | The Kryss is a Fencing weapon and has its own page | UOC/Items/Weapons/Swords/Kryss.cs:36; Kryss is a type of w-fencing
w-sword | At 100 stamina a Katana swings every 1.3 s and a Longsword every 2.1 s | 75 / 58 = 1.29, 75 / 35 = 2.14 (formula: BaseWeapon.cs:1555-1565)
w-sword | Slimes and acid elementals scar a sword on every hit | BaseWeapon.cs:2143-2152
w-sword | Double-click a sword and click a corpse to carve it, or a tree to cut Kindling | UOC/Items/Weapons/Swords/BaseSword.cs:17-22 (target 1010018 What do you want to use this item on?); UOC/Targets/BladedItemTarget.cs:34-37 (`ICarvable`), :74-101 (Lumberjacking tree -> `new Kindling()`, needs 5 wood in the bank :91); UOC/Items/Misc/Corpses/Corpse.cs:415-481; creature results UOC/Mobiles/BaseCreature.cs:2003-2100 (feathers, wool, meat, hides)
w-sword | With the Poisoning skill you can coat a sword with a poison potion; each hit uses one of 12 to 18 charges and poisons about half the time | UOC/Skills/Poisoning.cs:68-76 (non-AOS: one-handed Slashing or Piercing weapons), :133 (`PoisonCharges = 18 - Poison.Level * 2`); potions Lesser/Regular/Greater/Deadly = levels 0..3 (UOC/Misc/PoisonKinds.cs:88-91; potion files LesserPoisonPotion.cs:13, PoisonPotion.cs:13, GreaterPoisonPotion.cs:13, DeadlyPoisonPotion.cs:13) -> 18/16/14/12; UOC/Items/Weapons/Swords/BaseSword.cs:28-35 (`--PoisonCharges`, `Utility.RandomBool()` 50%); corrosion is switched off by the shard: SC/PostUorSystemGates.cs:18
w-sword | A new Swordsmanship or Tactics character starts with a Katana; it is newbied | UOC/Engines/Character Creation/CharacterCreation.cs:911-917 (`SwordsWeapon` -> Katana for Humans), :1290-1296 (`case Tactics: case Swords: EquipItem(SwordsWeapon)`), :727-737 (`EquipItem` makes it Newbied when not AOS); Elf characters are created with the Human package first: SC/CosmeticElfCreationService.cs:48
w-sword | Shops pay no gold for it (newbied) | GenericSell.cs:35-39
w-sword | Blacksmiths sell Cutlass 24, Thin longsword 27, Katana 33, Broadsword 35, Scimitar 36, Longsword 55, Viking sword 55 | generated price lines (SBBlacksmith.cs:61,69,65,67,76,68,70). Blacksmith NPCs and Weaponsmith NPCs are in the world: DIST/Data/Spawns/shared/felucca/Vendors.json (Weaponsmith 20, Blacksmith 12, Bowyer 7, Provisioner 18, Carpenter 9 spawner entries) and DIST/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json (Weaponsmith 4, Blacksmith 2, Bowyer 1, Provisioner 2, Carpenter 1)
w-sword | A weaponsmith may not stock every kind | UOC/Mobiles/Vendors/SBInfo/SBWeaponSmith.cs:39-41 (`switch (Utility.Random(3))` has only `case 0`, so about one weaponsmith in three gets the long list, lines 43-92; the short fixed list is lines 16-37); the Blacksmith NPC sells the full list (UOC/Mobiles/Vendors/NPC/Blacksmith.cs:53, SBBlacksmith.cs:53-104). The fighting skill pages say the same ("a Weaponsmith may stock only some"). See OPEN 2
w-sword | A Blacksmith forges all but the Thin longsword from iron ingots | UOC/Engines/Craft/T2A/BlacksmithMenu.cs:50-54 (`BladeTypes`: Broadsword, Cutlass, Dagger, Katana, Kryss, Longsword, Scimitar, VikingSword), UOC/Engines/Craft/DefBlacksmithy.cs:294-307; no AddCraft for ThinLongsword anywhere in Engines/Craft
w-sword | Monsters also drop swords | UOC/Misc/Loot.cs:67-80 (`WeaponTypes` includes Broadsword, Cutlass, Katana, Kryss, Longsword, Scimitar, VikingSword; not ThinLongsword), used by the loot packs (LootPack.cs:35)
w-fencing | The Dagger and the Kryss are one-handed piercing blades using Fencing | UOC/Items/Weapons/Knives/Dagger.cs:33-34 (`DefSkill Fencing`, `DefType Piercing`), Swords/Kryss.cs:36-37; one-handed per generated lines
w-fencing | Both swing about every 1.4 s at 100 stamina | 75 / 55 = 1.36, 75 / 53 = 1.42
w-fencing | A new Fencing character starts with a Kryss (newbied) | CharacterCreation.cs:929-935 (`FencingWeapon` -> Kryss), :1114-1117 (`case Fencing`), :736 (Newbied)
w-fencing | Carve / Kindling / poison | BaseKnife.cs:20-25 and BaseSword.cs:17-22 (BladedItemTarget), Poisoning.cs:68-76 (Dagger and Kryss are one-handed Piercing), BaseKnife.cs:28-35 / BaseSword.cs:28-35
w-fencing | Blacksmiths sell the Dagger for about 21 and the Kryss for 32 | SBBlacksmith.cs:62,66
w-fencing | A Blacksmith forges both; the Dagger takes 3 ingots, is the first weapon you can try to forge even at Blacksmithy 0, though it rarely works until the skill has grown | DefBlacksmithy.cs:302 (`Dagger -0.4 to 49.6, 3 ingots`), :304 (Kryss), :28 (`GetChanceAtMin => 0.0`): at skill 0 the chance is (0 - (-0.4)) / 50 = 0.8% (Core/CraftItem.cs success formula, `GetSuccessChance`); every other forged weapon starts at 14.5 or more (DefBlacksmithy.cs:530-611 and 294-307)
w-knife | Small one-handed knives that use Swordsmanship | BaseKnife.cs:16 (`DefSkill Swords`); generated hand-ness lines (q=1)
w-knife | Carve a corpse (meat, hides, feathers or wool, when the creature has any) or cut Kindling from a tree | BaseKnife.cs:20-25; BladedItemTarget.cs:34-37,74-101; BaseCreature.cs:2003-2100
w-knife | A tinker makes all three from 2 or 3 iron ingots; a Blacksmith does not forge them | DefTinkering.cs:297 (ButcherKnife 25-75, 2), :303 (Cleaver 20-70, 3), :308 (SkinningKnife 25-75, 2); T2A TinkeringMenu.cs:50-55 (`UtensilTypes`); BlacksmithMenu.cs:50-70 and DefBlacksmithy.cs list no knife
w-knife | Blacksmiths sell Butcher knife 14, Cleaver 15, Skinning knife 14 | SBBlacksmith.cs:58,71,77
w-spear | Spears and forks are piercing weapons using Fencing | BaseSpear.cs:15-16
w-spear | The Spear, Short spear and Pitchfork are two-handed; the War fork is one-handed | generated hand-ness lines (Spear 0xF62 q2, ShortSpear 0x1403 q2, Pitchfork 0xE87 q2, WarFork 0x1405 q1)
w-spear | The Short spear swings about every 1.5 s at 100 stamina | 75 / 50
w-spear | Only the one-handed War fork can be coated with poison | Poisoning.cs:70-72 (`Layer == OneHanded` and Slashing or Piercing); BaseSpear.cs:23-30
w-spear | The Pitchfork is a farm tool and does the least damage | Pitchfork.cs damage 4 to 16 against 2-36, 4-32, 4-32 (generated lines); 'farm tool' is a description of the item (SBBlacksmith sells it with the plain tools list, line 75)
w-spear | Blacksmiths sell the Short spear 23, Spear 31, Pitchfork 19; weaponsmiths sell the War fork for 32 | SBBlacksmith.cs:101,102,75; SBWeaponSmith.cs:37 (fixed list, the War fork is not in the Blacksmith list)
w-spear | A Blacksmith forges the Short spear, Spear and War fork under Build Pole Arms; the Pitchfork cannot be forged | BlacksmithMenu.cs:62-65 (`PolearmTypes`: Bardiche, Halberd, WarFork, ShortSpear, Spear), :225 (`Build Pole Arms`); DefBlacksmithy.cs:588,595,596 and the comment at :598-599 (Pitchfork not craftable)
w-axe | Six axes are two-handed, use Swordsmanship; the War axe is one-handed, trains Mace Fighting, cannot chop | BaseAxe.cs:32 (Swords); WarAxe.cs:37-41 (`DefSkill Macing`, `DefType Bashing`, `HarvestSystem => null`); BattleAxe.cs:10 (explicit TwoHanded); others tiledata q=2 (generated lines); WarAxe tiledata q=1
w-axe | Axes hit hard and swing slowly | speeds 30 to 40 = 1.9 to 2.5 s at 100 stamina (generated lines), against the swords' 35 to 58
w-axe | Each 5 points of Lumberjacking add 1% to damage (every axe but the War axe) | BaseWeapon.cs:2716-2720 (`Core.UOR && Type == WeaponType.Axe`); BaseAxe.cs:33 (`DefType Axe`), WarAxe.cs:38 (Bashing)
w-axe | Fighting with one slowly trains Lumberjacking | BaseWeapon.cs:2681-2685 (`CheckSkill(Lumberjacking, 0, 100)` on an Axe-type hit)
w-axe | Chop a tree: equip the axe (it will not chop from the pack), double-click, click the tree | BaseAxe.cs:75-98 (`OnDoubleClick` -> `HarvestSystem.BeginHarvesting`), UOC/Engines/Harvest/Lumberjacking.cs:125-139 and :141-155 (`tool.Parent != from` -> 500487 The axe must be equipped for any serious wood chopping)
w-axe | Chopping does not wear an axe out; fighting does | BaseAxe is not an `IUsesRemaining` (only Pickaxe, GargoylesPickaxe and BasePoleArm are: Pickaxe.cs:10, BasePoleArm.cs:10, grep over Items/Weapons); UOC/Engines/Harvest/Core/HarvestSystem.cs:245-258 only touches `IUsesRemaining` tools
w-axe | Blacksmiths sell Battle axe 26, War axe 29, Executioner's axe 30, Two handed axe 32, Large battle axe 33, Axe 40, Double axe 52 | SBBlacksmith.cs:55,79,53,56,78,72,73
w-axe | A Blacksmith forges all seven under Build Axes | BlacksmithMenu.cs:56-60 (`AxeTypes`), :224
w-axe | Monsters also drop axes | Loot.cs:67-80 (Axe, BattleAxe, DoubleAxe, ExecutionersAxe, Hatchet, LargeBattleAxe, TwoHandedAxe, WarAxe)
w-hatchet | The lumberjack's tool; light two-handed axe; Swordsmanship in a fight | Hatchet.cs (generated lines; tiledata 0xF43 quality 2); BaseAxe.cs:32; HarvestSystem Lumberjacking via BaseAxe.cs:36 (`HarvestSystem => Lumberjacking.System`)
w-hatchet | Equip it, double-click it, click a tree; will not chop from the pack; chopping does not wear it out | Lumberjacking.cs:125-155, BaseAxe.cs:75-98, HarvestSystem.cs:245-258 (Hatchet is not IUsesRemaining)
w-hatchet | (HarvestAutoRepeat) keep chopping until the wood runs out or you walk, fight, cast or use another skill | ShardContent/docs/Harvest-AutoRepeat-Evidence.md design table; SC/HarvestRepeatService.cs (`CheckCancel`, `StageAllowsRepeat`); flag CFG/shard-rules.json:210
w-hatchet | Weaponsmiths sell hatchets for about 25 to 27 | SBWeaponSmith.cs:35-36 (25 and 27, fixed list); no other shop sells it (grep Mobiles/Vendors)
w-hatchet | A tinker can make one from 4 iron ingots (Tinkering 30 and up) | DefTinkering.cs:250 (`Hatchet 30.0-80.0, 4 ingots`); T2A TinkeringMenu.cs:40
w-hatchet | A new Lumberjacking character starts with one | CharacterCreation.cs:1178-1181 (`EquipItem(elfOrHuman ? new Hatchet() : new DualShortAxes())`)
w-hatchet | Any other axe except the War axe chops too | BaseAxe.cs:36 and :75-98; WarAxe.cs:41
w-pickaxe | Miner's tool; weak one-handed axe: Str 25, damage 1 to 15, speed 35, 11 stones, Swordsmanship | Pickaxe.cs:19,31-34 (generated lines), tiledata 0xE86 quality 1, BaseAxe.cs:32
w-pickaxe | Double-click and click a mountainside or cave floor to dig ore; cannot dig while riding | Pickaxe.cs:20 (`HarvestSystem => Mining.System`), UOC/Engines/Harvest/Mining.cs:60-97 (`LandTiles = _mountainCaveTiles`, `StaticTiles = _mountainCaveStaticTiles`), :302-305 and :343-346 (501864 You can't mine while riding)
w-pickaxe | A new pickaxe has 50 uses (100 if made exceptional); each successful dig uses one; worn out and destroyed at none | Pickaxe.cs:15-16 (`UsesRemaining = 50`), :48-53 (`Core.UOR` and Exceptional: `UsesRemaining += 50`), HarvestSystem.cs:245-258 (`--UsesRemaining` after a successful give, `tool.Delete()` at < 1, 1044038 You have worn out your tool!)
w-pickaxe | (HarvestAutoRepeat) keep digging | same evidence as the hatchet (Harvest-AutoRepeat-Evidence.md: mining included)
w-pickaxe | Blacksmiths sell pickaxes for about 22 | SBBlacksmith.cs:74 (also SBMiner.cs:21 and SBTinker.cs:63 at 25)
w-pickaxe | A tinker can make one from 4 iron ingots (Tinkering 40 and up) | DefTinkering.cs:262
w-pickaxe | Some gargoyles carry a gargoyle's pickaxe with 101 to 125 uses | UOC/Mobiles/Monsters/Humanoid/Magic/Gargoyle.cs:42-45 (`RandomDouble() < 0.025` -> `PackItem(new GargoylesPickaxe())`), UOC/Items/Skill Items/Harvest Tools/GargoylesPickaxe.cs:10-12 (`RandomMinMax(101, 125)`), :15-18; Gargoyle spawns: DIST/Data/BritanniaRenaissance/Alpha2b/Spawns/Outdoors.json, Hythloth.json
w-mace | Club, mace, hammers use Mace Fighting | BaseBashing.cs:15
w-mace | Every hit takes 3 to 5 points of stamina from the target, which slows its swings | BaseBashing.cs:23 (`defender.Stam -= Utility.Random(3, 3)`; `Random(from, count)` = from + [0, count): SRV/Utilities/Utility.cs:890, SRV/Random/BuiltInRng.cs:34), and swing time depends on stamina (BaseWeapon.cs:1557)
w-mace | All are one-handed except the War hammer | HammerPick.cs:10 (explicit OneHanded), WarHammer.cs:10 (explicit TwoHanded); Club 0x13B4, Mace 0xF5C, Maul 0x143B, WarMace 0x1407 tiledata quality 1
w-mace | A War mace weighs 17 stones | WarMace.cs:14 (`DefaultWeight => 17.0`)
w-mace | A new Mace Fighting character starts with a Club (newbied) | CharacterCreation.cs:920-926 (`MacingWeapon` -> Club), :1183-1186
w-mace | Blacksmiths sell Club 16, Maul 21, War hammer 25, Hammer pick 26, Mace 28, War mace 31 | SBBlacksmith.cs:94,97,103,64,96,104
w-mace | A Blacksmith forges all but the Club under Build Bludgeoning Weapons | BlacksmithMenu.cs:67-70 (`MaceTypes`: HammerPick, Mace, Maul, WarMace, WarHammer), :226; DefBlacksmithy.cs:601-611; no Club craft in Engines/Craft
w-mace | Monsters also drop them | Loot.cs:67-80 (Club, Mace, Maul, WarHammer, WarMace, HammerPick)
w-staff | Two-handed, Mace Fighting, 3 to 5 stamina per hit | BaseStaff.cs:15,23; tiledata 0xE89, 0xDF0, 0x13F8 quality 2 (generated lines)
w-staff | The Quarter staff swings about every 1.6 s at 100 stamina | 75 / 48 = 1.56
w-staff | Weaponsmiths, blacksmiths and carpenters sell Gnarled staff 16, Quarter staff 19, Black staff 22 | SBWeaponSmith.cs:16-22, SBBlacksmith.cs:93-99, SBStavesWeapon.cs:16-19; Carpenter NPC: UOC/Mobiles/Vendors/NPC/Carpenter.cs:25
w-staff | A carpenter can make the Quarter staff and Gnarled staff (Carpentry about 74 and 79); the Black staff cannot be made | DefCarpentry.cs:306 (QuarterStaff 73.6-98.6, 6 logs), :307 (GnarledStaff 78.9-103.9, 7 logs); T2A CarpentryMenu.cs:36-39; no craft for BlackStaff in Engines/Craft
w-crook | Light two-handed staff, Mace Fighting, 3 to 5 stamina per hit | ShepherdsCrook.cs (generated lines), BaseStaff.cs:15,23
w-crook | Double-click, click an untamed animal that could be tamed, then click where it should go; depends on Herding; a pet looks tame already | ShepherdsCrook.cs:34-38 (OnDoubleClick 502464), :55-83 (`HerdingTarget.OnTarget`: not a BaseCreature 502472 line 59; not herdable 502468 line 65; `Controlled` 502467 That animal looks tame already line 74; else 502475 Click where you wish the animal to go line 80), :85-92 (`IsHerdable`: paragon refused, `Tamable` accepted), :126-153 (`InternalTarget.OnTarget`: min/max from `MinTameSkill` at :133-134, `CheckTargetSkill(Herding...)` at :146)
w-crook | Weaponsmiths, blacksmiths and carpenters sell it for about 20 | SBWeaponSmith.cs:22, SBBlacksmith.cs:99, SBStavesWeapon.cs:19
w-crook | A carpenter can make one (Carpentry about 79) | DefCarpentry.cs:305 (78.9-103.9, 7 logs)
w-crook | A new character who starts with Herding, Animal Lore or Animal Taming carries one | CharacterCreation.cs:1141-1145 (Herding), :972-985 (AnimalLore, non-elf), :987-994 (AnimalTaming, Human)
w-polearm | Two-handed pole arms using Swordsmanship; biggest damage ranges of the melee weapons, slow | BasePoleArm.cs:27; Bardiche and Halberd tiledata quality 2; ranges 5-43 and 5-49 against the widest of the others (Spear 2-36, Two handed axe 5-39), generated lines
w-polearm | At 100 stamina a Halberd swings every 3 s and a Bardiche every 2.9 s | 75 / 25 = 3.0, 75 / 26 = 2.88
w-polearm | Equipped, a pole arm chops trees like an axe; each successful chop uses one of its 150 uses and the last destroys it | BasePoleArm.cs:10 (`IUsesRemaining`), :22 (`_usesRemaining = 150`), :33-46 (`OnDoubleClick` -> `HarvestSystem.BeginHarvesting`), :31 (`HarvestSystem => Lumberjacking.System`; only Scythe turns it off, Scythe.cs:34); Lumberjacking.cs:125-155 (must be equipped); HarvestSystem.cs:245-258 (`--UsesRemaining`, `tool.Delete()`), message 500499 You broke your axe (Lumberjacking.cs:64)
w-polearm | Blacksmiths sell the Halberd for about 42 and the Bardiche for 60 | SBBlacksmith.cs:63,54
w-polearm | A Blacksmith forges both under Build Pole Arms | BlacksmithMenu.cs:62-65, :225
w-polearm | Monsters also drop them | Loot.cs:67-80 (Bardiche, Halberd)
w-bow | Two-handed ranged weapon for arrows using Archery; Str 20, damage 9 to 41, speed 20, range 10, 6 stones, durability 31 to 60 | Bow.cs:13 (explicit TwoHanded), :19 (`AmmoType => Arrow`), generated lines (Bow.cs:17,31-34,36,38-39), BaseRanged.cs:34; `MaxRange` = `OldMaxRange` = `DefMaxRange` when not AOS: BaseWeapon.cs:326,616
w-bow | Each shot uses one arrow from the backpack, hit or miss; with none the bow just stops shooting | BaseRanged.cs:97 (`OnFired`), :187-216 (consume `AmmoType` from the quiver first, else `pack?.ConsumeTotal`; `return false` when none), :97-125 (no message when `OnFired` is false; a delay is still returned)
w-bow | A clear line to the target within 10 tiles | SRV/Mobiles/Mobile.cs:821 (`InRange(combatant, weapon.MaxRange)`), :826 (`InLOS`)
w-bow | You must stand still: 1 second at 25 Dexterity or less, shorter as Dexterity rises, 0.5 second at 100 | BaseRanged.cs:46-58 (`GetStationaryDelay`: UOR branch 1000 - (dex - 25) x 500/75 ms, rounded to 50 ms, Dex clamped 25..100), :65 (`Core.TickCount - attacker.LastMoveTime >= delay`), :123-125 (otherwise try again in 0.25 s); `LastMoveTime` set on each move: SRV/Mobiles/Mobile.cs:4381
w-bow | At 100 stamina a bow shoots every 3.75 s; a Crossbow every 4.2 s; a Heavy crossbow every 7.5 s | 75 / 20, 75 / 18 = 4.17, 75 / 10 (BaseWeapon.cs:1555-1565); the 3.75 figure also appears in Novice-Combat-Assist-Evidence.md
w-bow | Blacksmiths sell bows for about 35 and bowyers for 40 | SBBlacksmith.cs:57; UOC/Mobiles/Vendors/SBInfo/Weapons/SBRangedWeapon.cs:25; Bowyer NPC uses SBRangedWeapon: UOC/Mobiles/Vendors/NPC/Bowyer.cs:37
w-bow | Bowcraft/Fletching can make one from 7 logs (skill 30 and up) | DefBowFletching.cs:116 (`Bow 30.0-70.0, 7 logs`); T2A BowFletchingMenu.cs:10-13
w-bow | A new Archery character starts with a Bow, newbied | CharacterCreation.cs:938-944 (`RangedWeapon` -> Bow), :996-1002 (`case Archery`), :736
w-crossbow | Two-handed, bolts, Archery; both reach 8 tiles | Crossbow.cs:13,19,36 and HeavyCrossbow.cs:13,19,36 (generated lines)
w-crossbow | Shooting: bolt per shot, stand still, clear line within 8 tiles | as w-bow (BaseRanged.cs, Mobile.cs)
w-crossbow | Blacksmiths sell the Crossbow for about 46 and the Heavy crossbow for 55; bowyers sell both for 55 | SBBlacksmith.cs:59,60; SBRangedWeapon.cs:16,17
w-crossbow | Bowcraft/Fletching: Crossbow 7 logs from skill 60; Heavy crossbow 10 logs from skill 80 | DefBowFletching.cs:117,118
w-ammo | Arrows for bows, bolts for crossbows and heavy crossbows; one used per shot | Bow.cs:19, Crossbow.cs:19, HeavyCrossbow.cs:19 (`AmmoType`); BaseRanged.cs:187-216
w-ammo | Each weighs a tenth of a stone | UOC/Items/Resources/Arrows/Arrow.cs:15, Bolt.cs:15 (`DefaultWeight => 0.1`)
w-ammo | About 4 misses in 10 leave the arrow or bolt on the ground near the target | BaseRanged.cs:159-185 (`attacker.Player && RandomDouble() < 0.4`, non-SE branch `Ammo?.MoveToWorld` within 1 tile of the defender, lines 171-181); `Ammo` is `new Arrow()` / `new Bolt()` (Bow.cs:20, Crossbow.cs:20)
w-ammo | About 4 hits in 10 on an animal or a monster leave it in the creature's pack; not on players or human enemies | BaseRanged.cs:128-134 (`attacker.Player && !defender.Player && (defender.Body.IsAnimal || defender.Body.IsMonster) && RandomDouble() < 0.4 && ... defender.AddToBackpack(ammo)`)
w-ammo | (Alpha3StarterCombatGear) a new character who starts with Archery is given 100 arrows | SC/StarterCombatIssuance.cs:19 (`ArrowTarget = 100`), :64-67 (`TopUpOrGrant(pack, ArrowTarget, ...)` when Archery is selected); the stock grant is 25: CharacterCreation.cs:998; the fighting page (parts/fighting.skills.json) says the same
w-ammo | Provisioners sell arrows for about 2 and bolts for 5 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:27,28; Provisioner NPC: Vendors/NPC/Provisioner.cs:22
w-ammo | Bowyers sell arrows for 2 and bolts for 3 | SBRangedWeapon.cs:24,26
w-ammo | A provisioner starts with 20 of each; a bowyer with 30 to 89 | SBProvisioner.cs:27-28 (amount 20); SBRangedWeapon.cs:24,26 (`Utility.Random(30, 60)` = 30 + [0, 60), SRV/Random/BuiltInRng.cs:34); stock refills hourly (BaseVendor.cs:154-165)
w-ammo | You can make your own with Bowcraft/Fletching from shafts and feathers (skill 0 and up) | DefBowFletching.cs:100-107 (`Arrow` and `Bolt` 0.0-40.0 from a Shaft and a Feather), :96 (Shaft from a Log)
w-wand | Kinds: clumsiness, feeblemindedness, weakness, mana draining, magic arrow, harming, fireball, lightning, healing, greater healing, identification | UOC/Misc/Loot.cs:266-281 and :346-361 (UOR uses `_oldWandTypes`: IDWand + WandTypes + NewWandTypes), Items/Wands/*.cs (`base(WandEffect...)`)
w-wand | A wand with charges reads as unidentified until Item Identification is used | UOC/Items/Wands/BaseWand.cs:241-257 (`OnSingleClickPreUOTD`: `isMagicItem = _charges > 0`, `!Identified` -> an unidentified ...); ItemIdentification.cs:44-47
w-wand | Equip the wand, double-click it and choose a target | BaseWand.cs:98-125 (`OnDoubleClick`: must be equipped 502641, `OnWandUse`), WandTarget.cs
w-wand | No mana, no reagents, never fizzles, no casting delay, spends one charge | UOC/Spells/Base/MagerySpell.cs:45 (`GetMana` = 0 for a wand), Spell.cs:260-261 (`ConsumeReagents` true when `Scroll != null`), :621-623 (`CheckFizzle` true for a wand), MagerySpell.cs:103-106 (`!Core.ML && Scroll is BaseWand` -> zero cast delay), Spell.cs:781-784 (`wand.ConsumeCharge`)
w-wand | Wait about 4 seconds between uses (an identification wand has no wait) | BaseWand.cs:68 (`GetUseDelay` 4 s), :85-95 (`ApplyDelayTo`), :100-103 (1070860), IDWand.cs:14 (`GetUseDelay => Zero`)
w-wand | When the charges are gone the game tells you; the wand is a weak one-handed club (Mace Fighting, damage 2 to 6) | BaseWand.cs:76 and :114 (1019073 This item is out of charges), :61-66 (`OldMinDamage 2`, `OldMaxDamage 6`, speed 35, Str 0), BaseWand : BaseBashing (:27), tiledata 0xDF2-0xDF5 quality 1
w-wand | Shops do not sell wands; they turn up in the better locked treasure chests in dungeons | no `Wand` in UOC/Mobiles/Vendors (grep); Loot.RandomWand() is called only by TreasureChestLevel3.cs:75 and TreasureChestLevel4.cs:76; those chests are in the world's dungeon spawn files (DIST/Data/BritanniaRenaissance/Alpha2b/Spawns: Covetous, Deceit, Despise, Destard, Fire, Hythloth, Ice, Shame, ...)
w-quiver | Worn in the cloak slot; cannot wear a cloak at the same time | UOC/Items/Quivers/BaseQuiver.cs:75 (`Layer = Layer.Cloak`); same-layer conflict: SRV/Items/Item.cs:2208
w-quiver | Holds up to 500 of one kind of ammunition, arrows or bolts, nothing else | BaseQuiver.cs:74 (`Capacity = 500`), :83 (`DefaultMaxItems => 1`), :10 and :133-155 (`CheckType`: Arrow or Bolt, the same type once it holds one), :159-185 (`CheckHold`, message 1074836)
w-quiver | Ammunition comes from the quiver first, then the backpack | BaseRanged.cs:191-203
w-quiver | Some special quivers make the ammunition weigh less or last longer | UOC/Items/Quivers/ElvenQuiver.cs:10 (`WeightReduction = 30`), UOC/Items/Special/8th Anniversary Items/QuiverOfInfinity.cs:13-14 (`WeightReduction = 30`, `LowerAmmoCost = 20`), BaseRanged.cs:194
w-quiver | Not obtainable in this world | see OPEN 1: no vendor, craft (DefTailoring.cs:215-250 is `Core.ML`), loot or decoration source; the plain quiver's tooltip says Requirement: Mondain's Legacy (BaseQuiver.cs:291 `list.Add(1075085)`)

## OPEN:

OPEN 1 (decide): Quivers (BaseQuiver and the six subclasses) are not obtainable in this world: no vendor sells one, no loot table or decoration file has one, and the only craft routes are `Core.ML` (`DefTailoring.cs:215-250`); the plain quiver's own tooltip says Requirement: Mondain's Legacy. You asked for a quiver topic, so `w-quiver` is written, mechanics only, with no "where to get it". Delete it (drop the object from w.items.json) if you would rather leave quivers to the general page; nothing else points at it (w-ammo and w-bow do not link to it).
OPEN 2 (owner design question, stock quirk): `SBWeaponSmith.cs:39-41` builds the long weapon list (swords, axes, bows, crossbows, knives, pole arms...) in only one of three random cases (`switch (Utility.Random(3))` with a single `case 0`), so about two weaponsmiths in three sell only staves, clubs, maces, spears, the War fork and hatchets. The Blacksmith NPC sells the full list. The text says only that a weaponsmith may not stock every kind. The vendor tables are rebuilt each time the vendor loads (BaseVendor.cs:610-640), so which weaponsmith has what can change after a restart.
OPEN 3 (verification note): one- or two-handedness of every weapon without an explicit `Layer` comes from `tiledata.mul` (Layer = ItemData.Quality) which I decoded with my own script, not from C# source. Surprising but consistent results: Hatchet, Axe, Double axe, Executioner's axe, Large battle axe, Two handed axe, Short spear, Spear, Pitchfork, the staves and the crook are two-handed; the War axe, War fork, Pickaxe and Club/Mace/Maul/War mace are one-handed. If the auditor can read the same file with the ModernUO reader (SRV/TileData.cs) they will see the same numbers.
OPEN 4: accuracy levels are described as adding 5 points per step to Tactics (Archery for ranged weapons), which is what `BaseWeapon.cs:369` does (a relative skill mod on `AccuracySkill`). I did not test it in play. If you prefer, delete the sentence; it is the only claim in the general page I verified from code alone.
OPEN 5: the Pickaxe topic also covers GargoylesPickaxe (2.5% drop from `Gargoyle`, `Gargoyle.cs:42-45`; 101 to 125 uses). Gargoyle spawns exist in Outdoors.json and Hythloth.json of the Alpha2b data, but I did not check that the spawner entries are active; the text says only "some gargoyles carry".
OPEN 6: numbers copied from config: w-weapon no longer quotes the NoviceCombat numbers (the fighting skill pages do, behind `requires NoviceCombat`). The only flagged paragraphs in this file are the two HarvestAutoRepeat ones and the Alpha3StarterCombatGear one (100 arrows); the 100 comes from a code constant (`StarterCombatIssuance.cs:19`), not from shard-rules.json.
OPEN 7: ammunition shop stock amounts (20 at a provisioner, 30 to 89 at a bowyer) are the initial `GenericBuyInfo` amounts; the actual restock rhythm (hourly, BaseVendor.cs:154) was not tested in play.
OPEN 8: no tooltips exist in this era (`opl.enable` defaults to Core.AOS and is not set), so weapon stats are never shown on hover; the pages therefore give the numbers. If the owner turns tooltips on later, the damage/speed lines in the lists remain correct but become redundant.

## Assigned classes: covered and left to the general page

Assigned classes: 254. Named in a topic (`types`, or BaseQuiver via `inherits`): 44. Reaching a specific topic through a named parent or base (`TopicFor` walks the base chain): 59. Left to the general weapon page (`w-weapon`, inherits BaseWeapon) or the general item page: 151. So 103 classes have a specific topic and 151 fall to the general pages.

### Named in a topic

- w-sword: Broadsword, Cutlass, Katana, Longsword, Scimitar, ThinLongsword, VikingSword
- w-fencing: Dagger, Kryss
- w-knife: ButcherKnife, Cleaver, SkinningKnife
- w-spear: Pitchfork, ShortSpear, Spear, WarFork
- w-axe: Axe, BattleAxe, DoubleAxe, ExecutionersAxe, LargeBattleAxe, TwoHandedAxe, WarAxe
- w-hatchet: Hatchet
- w-pickaxe: GargoylesPickaxe, Pickaxe
- w-mace: Club, HammerPick, Mace, Maul, WarHammer, WarMace
- w-staff: BlackStaff, GnarledStaff, QuarterStaff
- w-crook: ShepherdsCrook
- w-polearm: Bardiche, Halberd
- w-bow: Bow
- w-crossbow: Crossbow, HeavyCrossbow
- w-ammo: Arrow, Bolt
- w-quiver: BaseQuiver

### Reach a specific topic through a named parent or base (their own numbers may differ from the page; none of them is obtainable in this world except as noted)

- w-sword: BladeOfInsanity (via Katana), BladeOfTheRighteous (via Longsword), BraveKnightOfTheBritannia (via Katana), CaptainQuacklebushsCutlass (via Cutlass), HolySword (via Longsword), JocklesQuicksword (via Longsword)
- w-fencing: FangOfRactus (via Kryss), NightsKiss (via Dagger), OblivionsNeedle (via Dagger), SerpentsFang (via Kryss), SilverSerpentBlade (via Kryss)
- w-knife: ColdBlood (via Cleaver), RoyalGuardSurvivalKnife (via SkinningKnife)
- w-spear: EnchantedTitanLegBone (via ShortSpear), RecarosRiposte (via WarFork), TheTaskmaster (via WarFork)
- w-axe: AxeOfTheHeavens (via DoubleAxe), ZyronicClaw (via ExecutionersAxe)
- w-hatchet: MelisandesCorrodedHatchet (via Hatchet)
- w-pickaxe: JacobsPickaxe (via Pickaxe)
- w-mace: ArcticDeathDealer (via WarMace), BoneCrusher (via WarMace), CavortingClub (via Club), ChurchillsWarMace (via WarMace), TheBeserkersMaul (via Maul), TitansHammer (via WarHammer)
- w-staff: EmberStaff (via QuarterStaff), GlacialStaff (via BlackStaff), StaffOfPower (via BlackStaff), StaffOfTheMagi (via BlackStaff), WrathOfTheDryad (via GnarledStaff)
- w-polearm: BlazeOfDeath (via Halberd), Calm (via Halberd), LegacyOfTheDreadLord (via Bardiche), Quell (via Bardiche)
- w-bow: BowOfTheJukaKing (via Bow), Frostbringer (via Bow), JukaBow (via Bow), TheDryadBow (via Bow)
- w-crossbow: NoxRangersHeavyCrossbow (via HeavyCrossbow)
- w-wand: ClumsyWand (via BaseWand), FeebleWand (via BaseWand), FireballWand (via BaseWand), GreaterHealWand (via BaseWand), HarmWand (via BaseWand), HealWand (via BaseWand), IDWand (via BaseWand), LightningWand (via BaseWand), MagicArrowWand (via BaseWand), ManaDrainWand (via BaseWand), WeaknessWand (via BaseWand)
- w-quiver: ElvenQuiver (via BaseQuiver), QuiverOfBlight (via BaseQuiver), QuiverOfElements (via BaseQuiver), QuiverOfFire (via BaseQuiver), QuiverOfIce (via BaseQuiver), QuiverOfInfinity (via BaseQuiver), QuiverOfLightning (via BaseQuiver), QuiverOfRage (via BaseQuiver)

### Left to the general pages, with the reason

- **Age of Shadows** (10): Age of Shadows era weapons: sold, forged and looted only under `Core.AOS` (SBBlacksmith.cs:81-91,107-110; DefBlacksmithy.cs:283-298,566-590; DefBowFletching.cs:120-124; Loot.cs:60-65,88-91). Not in this world.
  BladedStaff, BoneHarvester, CompositeBow, CrescentBlade, DoubleBladedStaff, Lance, Pike, RepeatingCrossbow, Scepter, Scythe
- **Mondain's Legacy or later** (85): Mondain's Legacy (or later) weapons: elven and runic weapons, wild staves, gem maces, ML bows and axes, ML artifacts and recipe weapons, tribal spear, the plain MagicWand and FireworksWand (only ML quest NPC equipment: Engines/ML Quests/Definitions/Heartwood.cs, Sanctuary.cs). Crafted only under `Core.ML` (DefBlacksmithy.cs:538-..., DefBowFletching.cs:132-..., DefCarpentry.cs `Core.ML` block) or by quest. Not in this world.
  AdventurersMachete, AncientWildStaff, ArcanistsWildStaff, AssassinSpike, AssassinsShortbow, BarbedLongbow, BladeDance, BlightGrippedLongbow, BoneMachete, Bonesmasher, Boomstick, ButchersWarCleaver, ChargedAssassinSpike, ColdForgedBlade, CorruptedRuneBlade, DarkglowScimitar, DiamondMace, DiseasedMachete, ElvenCompositeLongbow, ElvenMachete, ElvenSpellblade, EmeraldMace, FaerieFire, FierySpellblade, FireworksWand, FleshRipper, FrozenLongbow, GuardianAxe, HardenedWildStaff, HeavyOrnateAxe, IcyScimitar, IcySpellblade, KnightsWarCleaver, Leafblade, LeafbladeOfEase, LightweightShortbow, LongbowOfMight, Luckblade, LuminousRuneBlade, MacheteOfDefense, MagekillerAssassinSpike, MagekillerLeafblade, MagesRuneBlade, MagicWand, MagicalShortbow, MischiefMaker, MysticalShortbow, OrcishMachete, OrnateAxe, OverseerSunderedBlade, PhantomStaff, RadiantScimitar, RaedsGlory, RangersShortbow, RighteousAnger, RubyMace, RuneBlade, RuneBladeOfKnowledge, RuneCarvingKnife, Runesabre, SapphireMace, SerratedWarCleaver, ShardThrasher, SilvanisFeywoodBow, SilverEtchedMace, SingingAxe, SlayerLongbow, SoulSeeker, SpellbladeOfDefense, TalonBite, TheNightReaper, ThornedWildStaff, ThunderingAxe, TribalSpear, TrueAssassinSpike, TrueLeafblade, TrueRadiantScimitar, TrueSpellblade, TrueWarCleaver, TwinklingScimitar, WarCleaver, WildStaff, WildfireBow, Windsong, WoundingAssassinSpike
- **Samurai Empire** (24): Samurai Empire weapons and Treasures of Tokuno rewards (craft `Core.SE`: DefBlacksmithy.cs:309-..., DefBowFletching.cs:108,126; Tokuno map disabled). Not in this world.
  Bokuto, Daisho, DarkenedSky, DemonForks, DragonNunchaku, Exiler, HanzosBow, Kama, Lajatang, NoDachi, Nunchaku, PeasantsBokuto, PilferedDancerFans, Sai, SwordOfTheStampede, SwordsOfProsperity, Tekagi, Tessen, Tetsubo, TheDestroyer, TheHorselord, Wakizashi, WindsEdge, Yumi
- **Stygian Abyss era and thrown weapons** (19): Stygian Abyss-era gargoyle weapons and the thrown weapons (BaseThrown, Throwing skill, which is not one of the UOR skills in parts/skills categories). Not in this world.
  AbyssReaver, BansheesCall, BloodBlade, Boomerang, Cyclone, DiscMace, DreadSword, DualPointedSpear, DualShortAxes, GargishTalwar, GlassStaff, GlassSword, RaptorClaw, SerpentstoneStaff, SoulGlaive, StoneSlithClaw, StormCaller, ValkyriesGlaive, WindOfCorruption
- **artifacts, quest rewards, gifts** (11): Artifacts, champion and quest rewards, Bulk Order rewards (AOS-only `Core.AOS` in Weaponsmith.SupportsBulkOrders), and a staff gift (ShaminoCrossbow). Not in this world.
  BreathOfTheDead, Heartseeker, LunaLance, Pacify, PixieSwatter, ProspectorsTool, ShaminoCrossbow, SturdyPickaxe, Subdue, TheDragonSlayer, TheDragonsTail
- **other** (2): Fists is the unarmed 'weapon' every mobile has (never held, `Visible = false`, Fists.cs:12). CrossbowBolts is a non-stackable decoration rare (UOC/Items/Special/Rares/Tinker/CrossbowBolts.cs), not ammunition (the crossbows use `Bolt`); it falls to the general item page (not a BaseWeapon).
  CrossbowBolts, Fists

Bola and BolaBall are not in the assignment file and have no topic (owner ruling pending).

## Method

Read in full: Help-Content-Spec.md, items.json, skills.json, HelpCatalog.cs (validator and `TopicFor`), W.tsv. Code read: BaseWeapon.cs (whole), BaseMeleeWeapon.cs, BaseRanged.cs, WeaponEvents.cs, the family base classes and every in-world weapon class, BaseQuiver.cs, BaseWand and the wand classes, CharacterCreation.cs (starter weapons), SBInfo files and the vendor NPC classes, the craft definitions and T2A menus, Repair.cs, Poisoning.cs, ArmsLore.cs, ItemIdentification.cs, LootPack.cs and Loot.cs, the harvest engine, shard sources (StarterCombatIssuance, NoviceCombatService, PostUorSystemGates, CosmeticElfCreationService, HarvestRepeatService) and the config files. Scratch scripts (tiledata decoder, class table, coverage simulation of `TopicFor`) are in the session scratchpad, not in the repository.
