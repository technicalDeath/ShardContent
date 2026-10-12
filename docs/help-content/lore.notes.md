# Lore skill pages: claim sources and open items

Pages: ItemID, ArmsLore, TasteID, Forensics, Musicianship, Peacemaking, Provocation, Discordance (8) in `lore.skills.json`.
Paths below are relative to the workspace root. Abbreviations: UOC = `ModernUO/Projects/UOContent`, SRV = `ModernUO/Projects/Server`, SC = `ShardContent`, CL = client text from `UOData/Cliloc.enu` (read with `ShardContent/tools/world-decorating/cliloc.py`; the number is given).
Era gates used throughout: Expansion UOR (`SC/data/configuration/expansion.json:8-11`, Core.AOS/LBR/UOTD false; `SRV/Main.cs:324-332`; enum order `SRV/ExpansionInfo.cs:24-38`).
Own-text sizes (characters): ItemID 2873, ArmsLore 3179, TasteID 2528, Forensics 2641, Musicianship 3143, Peacemaking 4753, Provocation 3934, Discordance 3709. Every page has `stats` and `gain` blocks and 5 to 7 headings. Only Peacemaking has a gated paragraph (`SafeWorld`).

## Common to all eight

- All | The skills window has a small use button to the left of a skill's name when the skill is clickable; clicking it uses the skill | `ClassicUO/src/ClassicUO.Client/Game/UI/Gumps/StandardSkillsGump.cs:794-803`, `SkillGumpAdvanced.cs:281-289`
- All | Skills with no use callback answer 'That skill cannot be used directly.' (CL 500014) | `SRV/Skills.cs:809`
- All | A skill used too soon answers 'You must wait a few moments to use another skill.' (CL 500118) | `SRV/Skills.cs:798-805`, `SRV/Mobiles/Mobile.cs:3763-3772`
- All | The skill's callback return value is the wait before the next skill use | `SRV/Skills.cs:798-800`
- All | Chance of a plain min/max check = (skill - min) / (max - min); at or above max it succeeds with no gain; below min it fails with no gain | `UOC/Skills/SkillCheck.cs:205-222`
- All | Below 10.0 skill every check gains (the gain block states it; text only says 'every try can teach you') | `UOC/Skills/SkillCheck.cs:130-141`
- All | Anti-macro is disabled (not mentioned in text) | `SC/data/configuration/antimacro.json:4`
- Trainers | A town NPC teaches a skill it has at 60.0 or more, up to a third of it (at most 42.0); 1 gold for each 0.1 point | `UOC/Mobiles/BaseCreature.cs:2849-2866, 4754-4762`, `UOC/Mobiles/AI/BaseAI/OnSpeech.cs:303-310`, `SC/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:186-193`
- Trainers | Vendors can teach (CanTeach); only healers restrict which skills | `UOC/Mobiles/Vendors/BaseVendor.cs:114`, `UOC/Mobiles/Healers/Healer.cs:28-35`, `BaseHealer.cs:11`
- Trainers | Lesson ranges in the text are one third of the NPC's skill range, rounded (see each skill below) | same sources plus the SetSkill lines below
- All | Vendors exist only in Britain (Vendors.json and TownsPeople.json are 'Britain only'); the generated world data holds exactly the spawners named below | `SC/data/world-generation/alpha2b/world-generation.json` (`britainOnlySpawnerFiles`), `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json`
- Links | 'Training', 'Dying', 'Fighting other players' are Welcome guide topics | `SC/src/BritanniaRenaissance.Content/WelcomeGuide.cs:268` (fighting), `WelcomeGuide.GettingStarted.cs:178-212` (training), `:329-367` (dying)

## ItemID (Item Identification)

- ItemID | Callback prompts 'What do you wish to appraise and identify?' and returns a 1 second wait | `UOC/Skills/ItemIdentification.cs:16-25`
- ItemID | Target reaches 8 tiles, may be nonlocal; usable on goods in a player vendor's shop | `ItemIdentification.cs:27-30`; `UOC/Mobiles/Vendors/VendorBackpack.cs:73-76`
- ItemID | On a creature or person it only calls OnSingleClick (name), no check | `ItemIdentification.cs:34-38`
- ItemID | Only IIdentifiable items (BaseWeapon, BaseArmor) get CheckTargetSkill(ItemID, item, 0, 100), so chance = skill/100, certain at 100 | `ItemIdentification.cs:44-48`; `UOC/Items/Weapons/BaseWeapon.cs:32`; `UOC/Items/Armor/BaseArmor.cs:17`
- ItemID | Under UOR (not AOS) the item's single-click name is shown after the try | `ItemIdentification.cs:50-53`
- ItemID | Any target that ended unidentified, including a non-weapon item that never rolled, gets 'You are not certain...' (CL 500353) | `ItemIdentification.cs:57-60`
- ItemID | Identified is set true and is saved with the item | `ItemIdentification.cs:46`; `BaseWeapon.cs:176-181`; `BaseArmor.cs:85-89`
- ItemID | Identified is read only to build the label; an unidentified magic piece works the same | `BaseWeapon.cs:3237, 3311`; `BaseArmor.cs:1358, 1400`
- ItemID | Under UOR the label comes from the pre-UOTD path: 'an unidentified NAME' for an unidentified magic piece | `BaseWeapon.cs:3204-3210, 3304-3316`; `BaseArmor.cs:1326-1331, 1395-1405`
- ItemID | Label words: durable, substantial, massive, fortified, indestructible; accurate, surpassingly accurate, eminently accurate, exceedingly accurate, supremely accurate; of ruin, might, force, power, vanquishing; armor of defense, guarding, hardening, fortification, invulnerability; the slayer name | `BaseWeapon.cs:3318-3330, 3385-3430`; `BaseArmor.cs:1407-1425, 1460-1490`
- ItemID | Each list ascends weakest to strongest | `UOC/Items/Weapons/WeaponEnums.cs:22-50`; `UOC/Items/Armor/ArmorEnums.cs:10-28`
- ItemID | Monsters drop magical weapons and armor (accuracy 80%, damage 60%, durability 40% for weapons; protection 80%, durability 40% for armor; a rare slayer) | `UOC/Misc/LootPack.cs:31-38, 426-487, 689-790`
- ItemID | A jeweler (Item Identification 64.0 to 100.0) teaches it: a third is 21.3 to 33.3 | `UOC/Mobiles/Vendors/NPC/Jeweler.cs:14`
- ItemID | Two jewelers in Britain | `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json` (spawners at 1451,1679 and 1650,1642)

## ArmsLore (Arms Lore)

- ArmsLore | Callback prompts for an item and returns a 1 second wait | `UOC/Skills/ArmsLore.cs:15-22`
- ArmsLore | Target reaches 2 tiles, nonlocal, usable on a player vendor's goods | `ArmsLore.cs:24-27`
- ArmsLore | Weapon: CheckTargetSkill(ArmsLore, weapon, 0, 100), chance = skill/100 | `ArmsLore.cs:31-33`
- ArmsLore | Condition message index = int(HitPoints / MaxHitPoints * 10) clamped 0..9, from CL 1038285 'about to fall apart' to 1038294 'unused' | `ArmsLore.cs:35-40`; CL 1038285-1038294
- ArmsLore | Damage class = ceil(min(average of min and max damage, 30) / 5), average under 3 gives class 0; classes read 'scratch slightly', 'minimal damage', 'some damage', 'hurt a fair amount', 'quite a lot of damage and pain', 'a superior weapon', 'extraordinarily deadly' | `ArmsLore.cs:42-52`; CL 1038216, 1038225, 1038234, 1038243, 1038252, 1038261, 1038270
- ArmsLore | The same message names how the weapon strikes (hit, stabbed, slashed, bashed, shot at long range) and one hand or two | `ArmsLore.cs:43, 54-75`
- ArmsLore | Poisoned weapon with charges adds 'It appears to have poison smeared on it.' (CL 1038284) | `ArmsLore.cs:77-80`
- ArmsLore | Under UOR a weapon's damage range is OldMinDamage/OldMaxDamage: dagger 3-15, long sword 5-33, bow 9-41, halberd 5-49 | `UOC/Items/Weapons/BaseWeapon.cs:508-530`; `Weapons/Knives/Dagger.cs:26-27`, `Swords/Longsword.cs:26-27`, `Ranged/Bow.cs:32-33`, `Polearms/Halberd.cs:26-27`
- ArmsLore | Armor: class = ceil(min(ArmorRating, 35) / 5); messages 'no defense' ... 'superbly crafted to provide maximum protection' (CL 1038295-1038302) | `ArmsLore.cs:87-99`
- ArmsLore | ArmorRating = base + magic protection (UOR: +10 and +5 per level) + resource bonus + 8 per quality step (exceptional +8), then scaled 50% to 100% by durability | `UOC/Items/Armor/BaseArmor.cs:289-328, 986-996`
- ArmsLore | Base ratings: leather chest 13, studded chest 16, ringmail chest 22, chainmail chest 28, platemail chest 40 (pieces of one type share the rating) | `Armor/Leather/LeatherChest.cs:28`, `Studded/StuddedChest.cs:28`, `Ring/RingmailChest.cs:30`, `Chain/ChainChest.cs:30`, `Plate/PlateChest.cs:30`, `Plate/PlateLegs.cs:30`, `Plate/PlateArms.cs:30`
- ArmsLore | Anything else answers 'This is neither weapon nor armor.' (CL 500352) | `ArmsLore.cs:117-120`
- ArmsLore | It is an inspection skill, not a combat bonus | `SC/docs/UOR-ERA-AUDIT.md:52-54`
- ArmsLore | A Blacksmith menu Repair choice exists | `SC/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:247`
- ArmsLore | Armorer and weaponsmith (Arms Lore 64.0 to 100.0) teach it: 21.3 to 33.3 | `UOC/Mobiles/Vendors/NPC/Armorer.cs:15`, `Weaponsmith.cs:17`; Welcome guide trainer list `WelcomeGuide.GettingStarted.cs:197`
- ArmsLore | Four armorers and four weaponsmiths in Britain | Vendors.json spawners

## TasteID (Taste Identification)

- TasteID | Callback prompts 'What would you like to taste?' (CL 502807), 1 second wait | `UOC/Skills/TasteID.cs:15-22`
- TasteID | Target reaches 2 tiles; out of range says 'You are too far away to taste that.' (CL 502815); usable on a player vendor's goods | `TasteID.cs:24-27, 78-81`
- TasteID | Food: CheckTargetSkill(TasteID, food, 0, 100), chance = skill/100 | `TasteID.cs:35-37`
- TasteID | Success: poisoned food says CL 1038284, clean food says CL 1010600 ('You detect nothing unusual about this substance.'), so a safe result is never wrong | `TasteID.cs:39-46`
- TasteID | Failure says CL 502823 ('You cannot discern anything about this substance.') | `TasteID.cs:48-52`
- TasteID | The food is not consumed | `TasteID.cs` (no Delete or consume call)
- TasteID | Potion: 'You already know what kind of potion that is.' plus its name, no skill check; keg likewise | `TasteID.cs:54-70`
- TasteID | A mobile: 'You feel that such an action would be inappropriate.' (CL 502816) | `TasteID.cs:31-34`
- TasteID | Anything else: 'That's not something you can taste.' (CL 502820); drinks (BaseBeverage : Item) are not Food | `TasteID.cs:71-75`; `UOC/Items/Food/Beverage.cs:274`; `Food/Food.cs:8`
- TasteID | Eating poisoned food poisons the eater | `UOC/Items/Food/Food.cs:70-72`
- TasteID | Poisoned food comes from the Poisoning skill (potion applied to food) | `SC/data/help/items.json` topic potion-poison ('poisoned food poisons whoever eats it')
- TasteID | Bread loaf about 6 gold at provisioner, innkeeper, tavern keeper; apple 3 gold at the provisioner; muffins 3 gold at baker and cook | `UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:53, 64`; `SBInnKeeper.cs:28`; `SBTavernKeeper.cs:28`; `SBBaker.cs:20`; `SBCook.cs:20`
- TasteID | Provisioner x2, baker x1, cook x4, innkeeper x3, tavern keeper x4, alchemist x5, herbalist x2 in Britain | Vendors.json, britain-vendor-overrides.json
- TasteID | Trainers: alchemist 65.0-88.0, cook 75.0-98.0, herbalist 80.0-100.0, so lessons reach 21.7 to 33.3; the Welcome guide lists the same trades | `UOC/Mobiles/Vendors/NPC/Alchemist.cs:16`, `Cook.cs:16`, `Herbalist.cs:16`; `WelcomeGuide.GettingStarted.cs:197, 199-200`
- TasteID | Cure potion and Cure spell cure poison | `SC/data/help/items.json` topic potion-cure

## Forensics (Forensic Evaluation)

- Forensics | Callback reveals the user, prompts (CL 501000 'Select what you want to examine.'), 1 second wait | `UOC/Skills/ForensicEval.cs:16-24`
- Forensics | Target reaches 10 tiles | `ForensicEval.cs:28`
- Forensics | Mobile: CheckTargetSkill(Forensics, target, 40, 100); success says 'You notice nothing unusual.' (a Thieves' Guild member would say 'This individual is a thief!', left out, see OPEN); failure CL 501001 | `ForensicEval.cs:34-50`
- Forensics | Below 40.0 a mobile target returns false with no gain | `SkillCheck.cs:209-212`
- Forensics | Corpse: CheckTargetSkill(Forensics, corpse, 0, 100), chance = skill/100 | `ForensicEval.cs:52-54`
- Forensics | First successful reader is stored; later readers get CL 1042750 ('The forensicist NAME has already discovered that:') and still get the answers | `ForensicEval.cs:56-64`; `UOC/Items/Misc/Corpses/Corpse.cs:339`
- Forensics | Human body: CL 1042751 with the killer's name or 'no one' | `ForensicEval.cs:66-70`
- Forensics | Killer is the most recent aggressor or defender by last combat time | `Corpse.cs:270-300`
- Forensics | Looters (everyone who used or lifted an item from the body): CL 1042752 else CL 501002 ('This corpse has not been desecrated.') | `ForensicEval.cs:72-100`; `Corpse.cs:134, 266, 811, 832`
- Forensics | Monster corpses give only the looter answer (the killer line is for human bodies only) | `ForensicEval.cs:66`
- Forensics | Failure says 'You cannot determine anything useful.' | `ForensicEval.cs:102-105`
- Forensics | Locked container (ILockpickable): 'This lock was opened by NAME' or 'You notice nothing unusual.', no skill check | `ForensicEval.cs:107-117`
- Forensics | The picker is cleared when the box is locked and is a plain property | `UOC/Items/Containers/LockableContainer.cs:49, 86, 97`
- Forensics | No murder count or notoriety is shown by the code | `ForensicEval.cs` (whole file)
- Forensics | Using it reveals a hidden user | `ForensicEval.cs:19`
- Forensics | Anyone can loot a player's corpse here | `WelcomeGuide.GettingStarted.cs:359-364`; owner ruling SK-010 keep stock `SC/docs/Alpha-3-Player-Skill-Audit.md:208`
- Forensics | Healer (Forensic Evaluation 80.0-100.0) teaches it; lessons reach 26.7 to 33.3; one healer in Britain | `UOC/Mobiles/Healers/Healer.cs:18, 28-35`; `WelcomeGuide.GettingStarted.cs:200`; Vendors.json spawner at 1471,1611
- Forensics | The 'living target teaches nothing below 40' and 'corpses from 0' claims | `ForensicEval.cs:36, 54`; `SC/docs/Beta-1-Skill-Gain-Curve-Audit.md:45`

## Musicianship

- Musicianship | No use callback: 'That skill cannot be used directly.' | `SRV/Skills.cs:809`; no `SkillInfo.Table[(int)SkillName.Musicianship].Callback` assignment exists in `ModernUO/Projects` or `SC/src`
- Musicianship | Double-clicking an instrument plays it; needs to be within 1 tile of the instrument (pack counts) | `UOC/Items/Skill Items/Musical Instruments/BaseInstrument.cs:498-503`
- Musicianship | 6 second wait between plays; busy answer CL 500119 | `BaseInstrument.cs:504-509, 520-523`
- Musicianship | The played instrument is remembered for the bard skills while it stays in the pack | `BaseInstrument.cs:201-210, 353-356, 506`
- Musicianship | Playing by double-click does not consume a use | `BaseInstrument.cs:498-524` (no ConsumeUse)
- Musicianship | CheckMusicianship: rolls CheckSkill(Musicianship, 0, 120) then succeeds with chance skill/100 | `BaseInstrument.cs:526-531`
- Musicianship | Musicianship 0 never plays well, 100 always does | `BaseInstrument.cs:530` (value/100 > RandomDouble)
- Musicianship | Each bard skill rolls Musicianship first and consumes a use on every outcome | `Peacemaking.cs:77-82`; `Provocation.cs:142-147`; `Discordance.cs:162-167`
- Musicianship | New instrument uses 350 to 450 under UOR | `BaseInstrument.cs:52, 55-56`
- Musicianship | Last use message 'The instrument played its last tune.' (CL 502079) and the instrument is deleted | `BaseInstrument.cs:185-199`
- Musicianship | Exceptional instrument: difficulty -5, more uses (quality setter scales uses) | `BaseInstrument.cs:86-99, 118-144, 183, 311-314`
- Musicianship | Bard sells drums, tambourine, lap harp, lute at 21 gold (10 in stock); carpenter sells the same four at 21 (20 in stock); no harp sold | `UOC/Mobiles/Vendors/SBInfo/SBBard.cs:16-19`; `SBCarpenter.cs:29-32`; `NPC/Bard.cs:28`; `NPC/Carpenter.cs:26`
- Musicianship | Vendor prices are the base prices (no town tax scaling in this world; matches the Alchemy page's 8 gold mortar) | `UOC/Mobiles/Vendors/GenericBuy.cs:51-84`, `BaseVendor.cs:1384`
- Musicianship | Weights: tambourine 1, drums 4, lute 5, lap harp 10, harp 35 | `Drums.cs:13`, `Harp.cs:13`, `LapHarp.cs:13`, `Lute.cs:13`, `Tambourine.cs:13` (all under `Items/Skill Items/Musical Instruments`)
- Musicianship | One bard in Lord British's Conservatory of Music (sign at 1454,1561; spawner 1455,1557) and one carpenter at The Saw Horse (sign 1433,1600; spawner 1430,1597) | `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json`, `signs.cfg` (names via CL)
- Musicianship | Starting characters get an instrument for each of Musicianship, Peacemaking, Provocation, Discordance, picked from drums, harp, lap harp, lute, tambourine (two tambourine graphics); newbied | `UOC/Engines/Character Creation/CharacterCreation.cs:495-506, 756-761, 833-846, 1109-1112, 1224-1228, 1262-1266, 1274-1278`
- Musicianship | The Bard template starts Musicianship 50, Provocation 50, Archery 20 | `SC/data/professions/Prof.txt:98-111`
- Musicianship | Newbied items stay with you on death | `WelcomeGuide.GettingStarted.cs:64-66`
- Musicianship | Instrument crafting: Carpentry 57.8 (drums, tambourine) / 63.1 (lap harp) / 68.4 (lute) / 78.9 (harp) plus Musicianship 45.0, logs and cloth; the T2A menu lists only what all required skills allow | `UOC/Engines/Craft/DefCarpentry.cs:403-420`; `T2A/CarpentryMenu.cs:41-44`; `T2ACraftSystem.cs:194-208`; `Core/CraftItem.cs:861-899`
- Musicianship | Bard (Musicianship 64.0-100.0) teaches 21.3 to 33.3; bard guildmaster (80.0-100.0) 26.7 to 33.3 | `UOC/Mobiles/Vendors/NPC/Bard.cs:14-17`; `Guildmasters/BardGuildmaster.cs:12-15`
- Musicianship | Bard and guildmaster appear in Britain together | Vendors.json spawner at 1455,1557

## Peacemaking

- Peacemaking | Use reveals, picks the instrument (asks 'What instrument shall you play?' with a 1 tile cursor if the remembered one is not in the pack), prompts 'Whom do you wish to calm?', 1 second return, 30 second cursor wait | `UOC/Skills/Peacemaking.cs:16-31`; `BaseInstrument.cs:214-239`
- Peacemaking | Range = 8 + int(skill/15) | `BaseInstrument.cs:212`; `Peacemaking.cs:37-41`
- Peacemaking | Instrument must be in the pack when targeting | `Peacemaking.cs:64-68`
- Peacemaking | Non-mobile target: 'You cannot calm that!' | `Peacemaking.cs:52-55`
- Peacemaking | Self-target: Musicianship check, then CheckSkill(Peacemaking, 0, 120); both failures print CL 500612 / 500613 and consume a use | `Peacemaking.cs:73-88`
- Peacemaking | Self-target chance = Musicianship/100 x Peacemaking/120 | `BaseInstrument.cs:526-531`; `Peacemaking.cs:83`
- Peacemaking | Area effect: everyone in range except you, Uncalmable, AreaPeaceImmune or not CanBeHarmful loses combatant and warmode; pacified for 1 second only if not already pacified | `Peacemaking.cs:95-123`
- Peacemaking | CL 500615 on success, CL 1049648 if nothing calmed | `Peacemaking.cs:125-133`
- Peacemaking | Waits: base 10 s, success 5 s (area and single) | `Peacemaking.cs:71, 91, 182`
- Peacemaking | Single target refusals: CanBeHarmful false 'You cannot calm that!', Uncalmable CL 1049526, already pacified CL 1049527 | `Peacemaking.cs:142-152`
- Peacemaking | Poor-play in single mode waits 10 s under UOR | `Peacemaking.cs:154-160`
- Peacemaking | Difficulty window: diff = difficulty(target, instrument) - 10; CheckTargetSkill(Peacemaking, target, diff - 25, diff + 25) | `Peacemaking.cs:163-171`
- Peacemaking | Success: combatant cleared, calm lasts 100 - diff/1.5 seconds clamped 10..120 | `Peacemaking.cs:182-201`
- Peacemaking | Pacified creatures stop fighting each tick until BardEndTime | `UOC/Mobiles/AI/BaseAI/BaseAI.cs:712-727`; `AITimer.cs:210-225`
- Peacemaking | Damage can end the calm with chance (HitsMax - Hits) x 0.001 | `UOC/Mobiles/BaseCreature.cs:1941-1946`
- Peacemaking | Uncalmable = BardImmune (vendors, familiars, many monsters under non-AOS) | `BaseCreature.cs:974-977`; `Vendors/BaseVendor.cs:116`; `Familiars/BaseFamiliar.cs:21`; e.g. `Monsters/Humanoid/Melee/Juggernaut.cs:58`
- Peacemaking | Difficulty formula: (0.625 x HitsMax + StamMax + ManaMax + total skill points) with +100 each for Magery above 5 on an AI_Mage, a fire breather, poison immunity, +20 per poison level step, then divided by 10 | `BaseInstrument.cs:249-305` (Core.LBR is false, so 0.625; SkillsTotal is in tenths and divided by 10, `Server/Mobiles/Mobile.cs:504`, `Skills.cs:185`)
- Peacemaking | BaseCreature HitsMax/StamMax/ManaMax follow seeds or Str/Dex/Int | `BaseCreature.cs:1040-1052`
- Peacemaking | Example difficulties (computed from midpoints of each creature's SetStr/SetDex/SetInt/SetHits/SetMana/SetSkill ranges): rabbit 5.0, mongbat 6.0, giant rat 17.7, ogre 32.6, orc 37.2, harpy 42.0, cyclops 49.9, gargoyle 69.2, evil mage 70.6 | `Animals/Rodents/Rabbit.cs`, `Monsters/Humanoid/Melee/Mongbat.cs`, `Animals/Rodents/GiantRat.cs`, `Ogre.cs`, `Orc.cs`, `Harpy.cs`, `Cyclops.cs`, `Humanoid/Magic/Gargoyle.cs`, `EvilMage.cs` (all under `UOC/Mobiles`)
- Peacemaking | Animals and monsters are never 'innocent'; only human-bodied non-pets can be | `UOC/Misc/Notoriety.cs:485-491`
- Peacemaking | Tiers in the text (rabbits and mongbats to about 20 ... evil mages to 85) = difficulty + 15 | derived from the window above
- Peacemaking | Players: single or area calm needs CanBeHarmful; under SafeWorld ordinary blue players are not harmable unless Intent, retaliation, criminal or guild war; knocked-out players are never harmable | `SC/src/BritanniaRenaissance.Content/PvpIntentService.cs:230-240, 355-441`
- Peacemaking | Bard (Peacemaking 65.0-88.0) teaches 21.7 to 29.3; guildmaster (80.0-100.0) 26.7 to 33.3 | `Bard.cs:16`; `BardGuildmaster.cs:14`
- Peacemaking | Using it reveals a hidden user; the 'cursor waits' remark is the 30 second NextSkillTime | `Peacemaking.cs:18, 27, 30`

## Provocation

- Provocation | Use reveals, picks an instrument, prompts 'Whom do you wish to incite?' | `UOC/Skills/Provocation.cs:16-30`
- Provocation | First target must be a BaseCreature the user can harm; pack check | `Provocation.cs:47-53`
- Provocation | Innocent notoriety: creature says CL 501591, user loses 75 karma | `Provocation.cs:55-61`
- Provocation | Controlled creature: CL 501590 | `Provocation.cs:62-65`
- Provocation | Success on first target plays well and prompts CL 1008085 | `Provocation.cs:70-78`
- Provocation | Second target must be a BaseCreature, neither Unprovokable, within bard range of the first, and not the same one (CL 501593) | `Provocation.cs:106-127, 171-174`
- Provocation | Bard range applies to both clicks and to the pair | `Provocation.cs:36-41, 92-96, 121-122`
- Provocation | Waits: 10 s after a success, 5 s after a poor note or a failed roll | `Provocation.cs:129, 144, 156`
- Provocation | diff = (D1 + D2) / 2 - 5; CheckTargetSkill(Provocation, second, diff - 25, diff + 25) | `Provocation.cs:131-133, 154`
- Provocation | Musicianship check first; every outcome consumes a use | `Provocation.cs:142-168`
- Provocation | Messages CL 501602 (success), CL 501599 (fail), CL 1049446 (immune) | `Provocation.cs:115-119, 157, 163`
- Provocation | Provoke(): both creatures target each other for at least 30 seconds | `UOC/Mobiles/BaseCreature.cs:4019-4062`
- Provocation | After 30 s they continue until one dies or the provoker or the opponent is out of the creature's perception range or gone | `UOC/Mobiles/AI/BaseAI/BaseAI.cs:729-765`; default RangePerception 16 `BaseCreature.cs:171`
- Provocation | The ranges 'two rabbits ... about 25', '... about 90' = average difficulty + 20 | derived from the window above
- Provocation | Bard (Provocation 60.0-83.0) teaches 20.0 to 27.7; guildmaster (80.0-100.0) 26.7 to 33.3 | `Bard.cs:17`; `BardGuildmaster.cs:15`
- Provocation | Bard template starts Provocation 50 and Musicianship 50 | `Prof.txt:98-111`

## Discordance

- Discordance | Use reveals, picks an instrument, prompts CL 1049541, 6 second cursor wait | `UOC/Skills/Discordance.cs:18-33`
- Discordance | Range 8 + int(skill/15) | `Discordance.cs:119-127`; `BaseInstrument.cs:212`
- Discordance | Refused on yourself, on BardImmune creatures and on creatures that cannot be harmed (unless you control them) | `Discordance.cs:142-147`
- Discordance | Already discorded: refused (CL 1049537 text) | `Discordance.cs:148-151`
- Discordance | Players: no effect (the instrument plays badly) | `Discordance.cs:152, 262-265`
- Discordance | Non-player target: diff = difficulty - 10 (- (Musicianship - 100)/2 above 100, unreachable); Musicianship check first | `Discordance.cs:154-167`
- Discordance | CheckTargetSkill(Discordance, target, diff - 25, diff + 25); success CL 1049539, failure CL 1049540, both consume a use | `Discordance.cs:168-173, 253-258`
- Discordance | UOR branch (not AOS): effect = int(skill / -5); Str, Int, Dex StatMods of int(raw stat x effect/100) with no expiry, plus a skill mod of effect% on every skill above 0 | `Discordance.cs:203-241`
- Discordance | The AOS resistance branch is dead under UOR (no resistances are changed) | `Discordance.cs:177-202`
- Discordance | Stat mods lower max hits, stamina, mana of creatures | `UOC/Mobiles/BaseCreature.cs:1040-1052`
- Discordance | The effect persists while the bard is alive, visible and within range; otherwise it ends 15 seconds later (resets if conditions recover); checked every 1.25 s | `Discordance.cs:46-91, 244-249`
- Discordance | Wait after a try on a creature: 12 s | `Discordance.cs:260`
- Discordance | Bard (Discordance 64.0-100.0) teaches 21.3 to 33.3 | `Bard.cs:14`
- Discordance | Owner ruling: the shard targets Discordance (the weaken song), not Enticement | `SC/docs/Alpha-3-Player-Skill-Audit.md:33, 123`
- Discordance | Stat gain data: Dex/Int 0.25, primary Int, secondary Dex; tiny stat scale | `ModernUO/Distribution/Data/skills.json:243-257`

## OPEN:

- OPEN: Discordance versus Enticement. `Alpha-3-Player-Skill-Audit.md:33,123` records an owner ruling of 2026-09-28 for Discordance (the Publish 16 weaken song, which is what the code does, nothing else exists). Your brief says the owner may still be reviewing it. The page describes exactly the coded behavior and never says Enticement. Please confirm. Also unverified: which name the player's client skills window shows for skill 15 (the client table, not the server, decides; ClassicUO's own hotkey list calls it Enticement, `ClassicUO/.../HotkeysManager.cs:533`).
- OPEN: the generated `stats` sentence says the higher the stats, 'the better the skill works for you than its number says'. That is false for ItemID, ArmsLore, TasteID, Forensics, Musicianship and Peacemaking, whose stat scales are all 0 (`ModernUO/Distribution/Data/skills.json`), and almost false for Provocation and Discordance (a bonus of at most about 5 points at skill 0 and nothing at 100). The generator (`HelpGenerators.StatsText`) needs a different sentence for skills without a stat scale.
- OPEN: Forensic Evaluation on a person says 'This individual is a thief!' for a Thieves' Guild member. There is no thief guildmaster in the spawn data, so I left the Thieves' Guild out of the text.
- OPEN: wands. `BaseWand` derives from `BaseBashing`, so Item Identification and Arms Lore treat a wand as a weapon. Wands drop only from treasure chests (`Loot.RandomWand`), whose reachability I did not check, so the pages do not mention wands.
- OPEN: example creature difficulties are computed from the midpoints of each creature's stat and skill ranges (rabbit 5, mongbat 6, giant rat 18, ogre 33, orc 37, harpy 42, cyclops 50, gargoyle 69, evil mage 71). Each spawn rolls its own, so they are approximate and said to be. The Magery above 5 test was assumed true for gargoyle and evil mage (their Magery is 70 or more).
- OPEN: the bard difficulty add-ons (SK-011) are 'provisionally keep stock' (`Alpha-3-Player-Skill-Audit.md:209`). If the owner changes them, the difficulty paragraph on three pages changes.
- OPEN: Carpentry instrument crafting (Musicianship 45.0 gate, skill ranges) is read from `DefCarpentry` and the T2A menu filter but was not exercised live.
- OPEN: no Tinker NPC is spawned (SBTinker also lists instruments), the harp is sold nowhere, and the tassel tambourine is craft-and-starter only; none of these is advertised.
- OPEN: the Welcome guide's trainer list (`WelcomeGuide.GettingStarted.cs:196-203`) omits jewelers (Item Identification) although the code lets them teach it; the Item Identification page says jewelers teach it. The guildmasters (merchant, miner for Item Identification; bard, healer, warrior) also teach; only the bard guildmaster is mentioned.
- OPEN: Peacemaking on yourself also pauses fights of other creatures and of players you may lawfully attack; I did not check how it interacts with Hot Zone rules, tamed pets, or Knocked Out players beyond the Safe World harm check.
- OPEN: Provocation: whether damage the provoked pair deal each other is credited to the bard (loot rights or karma) was not traced, so the page says nothing.
- OPEN: `Alpha-3-Player-Skill-Audit.md:197` lists an 'Item Identification relabel' live check as still open; I could not tell what it refers to and did not examine it.
- OPEN: shop and place names ('Lord British's Conservatory of Music', 'The Saw Horse') come from the nearest sign in `signs.cfg` to each vendor spawner (3 to 4 tiles away); a vendor wanders up to 5 tiles from its spawner.
- OPEN: client claim 'a small button beside the skill name' is from `StandardSkillsGump.cs` / `SkillGumpAdvanced.cs`; whether a given skill is clickable comes from the player's client skill data, which I did not read. The text avoids saying which skills have a button, except Musicianship, which the server answers with 'cannot be used directly'.

## For the coordinator to decide

- The stats generator sentence (above).
- Whether to keep the numeric creature examples in the three bard pages, or replace them by plain named tiers.
- Whether `requires: SafeWorld` on the Peacemaking player paragraph is how you want Safe World handled; no other flagged text was needed on these eight pages.
- Item topics for musical instruments (other writers) should name skills Musicianship, Peacemaking, Provocation, Discordance so the pages list them; I left `items` empty.
- Housekeeping: the shared scratchpad holds my `build_lore.py`, `extract_cliloc.py`, `extract2.py`, `signs_near.py` and `cliloc_extract.txt`; I may have overwritten another agent's `extract2.py` there (generic name).
