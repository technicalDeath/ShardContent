# Thieves skill pages: claim lines, OPEN items, decisions

Output: `parts/thieves.skills.json` (8 pages: Hiding, Stealth, Stealing, Snooping, Lockpicking, RemoveTrap, DetectHidden, Begging).

Path shorthand: `UOC/` = `ModernUO/Projects/UOContent/`, `SRV/` = `ModernUO/Projects/Server/`, `BR/` = `ShardContent/src/BritanniaRenaissance.Content/`, `GEN/` = `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/`.

Era facts used throughout: `Core.Expansion` is UOR (`ShardContent/data/configuration/expansion.json`; `Core.UOR` true, `Core.AOS/SE/ML/LBR` false: `SRV/Main.cs:326-346`). Every `Core.AOS/SE/ML` branch below was read and the UOR branch taken. No shard code changes any of the eight skills (grep of `BR/` finds only the theft hooks, the Lockpick events and the Knocked Out snoop hook). Anti-macro is disabled and is not mentioned. The Young system is off (`Distribution/Configuration/FeatureFlags/flags.json` young_player_system Enabled false) and is not mentioned.

Skill buttons: the six skills with a button (Begging, Detecting Hidden, Hiding, Stealing, Stealth, Remove Trap) have the clickable flag in `UOData/skills.mul` (parsed); Lockpicking and Snooping do not. The skills window draws a use button for clickable skills: `ClassicUO/src/ClassicUO.Client/Game/UI/Gumps/StandardSkillsGump.cs:796-803`.

Wait of 10 seconds is shared by all skills: `SRV/Skills.cs:796-800` (`NextSkillTime` set from the callback's return value, checked for every skill).

## Hiding

Hiding | Hiding.OnUse: refuses while casting (returns 1 s) | UOC/Skills/Hiding.cs:19-23
Hiding | house bonus: standing in a house you own/co-own/are a friend of = bonus 100 (check range -100..0, always succeeds); else (non-AOS) beside or inside any house = bonus 50 | UOC/Skills/Hiding.cs:32-49; friend test `BaseHouse.IsFriend` UOC/Multis/Houses/BaseHouse.cs:3612
Hiding | adjacent-house test uses the column at z 127, i.e. any house footprint tile next to you | UOC/Skills/Hiding.cs:40-43, UOC/Multis/Houses/BaseHouse.cs:1513-1557
Hiding | range = min((100 - Hiding)/2 + 8, 18): 18 tiles to Hiding 80, 13 at 90, 8 at 100 | UOC/Skills/Hiding.cs:53
Hiding | cannot hide if your combatant is within range with line of sight, or anyone in range with line of sight has you as combatant: "You can't seem to hide right now."; returns 1 s | UOC/Skills/Hiding.cs:55-83
Hiding | roll is CheckSkill(Hiding, 0 - bonus, 100 - bonus), so chance = skill/100 with no bonus | UOC/Skills/Hiding.cs:73; chance formula UOC/Skills/SkillCheck.cs:61-80
Hiding | success: hidden, war mode off, "You have hidden yourself well."; failure "You can't seem to hide here."; returns 10 s | UOC/Skills/Hiding.cs:85-98
Hiding | with a bonus of 100 (friend house) the roll has no challenge and teaches nothing; with bonus 50 skill 50 or more has no challenge | UOC/Skills/SkillCheck.cs:70-73 (value >= maxSkill returns true without gain); 205-222
Hiding | a roll that has a challenge: chance below 1 gives gain chance (1 - chance) * 0.5/0.2 so lower chance teaches more often | UOC/Skills/SkillCheck.cs:146-166
Hiding | below 10.0 every use gains (1 to 4 tenths) whether or not it succeeds | UOC/Skills/SkillCheck.cs:130-141, 299-302
Hiding | other players and monsters cannot see a hidden player | SRV/Mobiles/Mobile.cs:7357-7369 (CanSee)
Hiding | speaking reveals | SRV/Mobiles/Mobile.cs:7075-7094 (OnSaid -> RevealingAction)
Hiding | swinging a weapon reveals; ranged attack reveals | SRV/Mobiles/Mobile.cs:829; UOC/Items/Weapons/Ranged/BaseRanged.cs:118,123
Hiding | casting reveals (spells; wands too) | UOC/Spells/Base/Spell.cs:535 (RevealOnCast default true, UOC/Spells/Base/Spell.cs:54), 784 (wand)
Hiding | drinking a potion reveals | UOC/Items/Skill Items/Magical/Potions/BasePotion.cs:192
Hiding | bandage use reveals | UOC/Items/Skill Items/Misc/Bandage.cs:43,74
Hiding | throwing an explosion potion reveals | UOC/Items/Skill Items/Magical/Potions/Explosion Potions/BaseExplosionPotion.cs:74
Hiding | giving a pet an order reveals | UOC/Mobiles/AI/BaseAI/PetOrders.cs:96
Hiding | taking an item from a corpse that is not yours reveals | UOC/Items/Misc/Corpses/Corpse.cs:817-824
Hiding | pushing past someone (full stamina) reveals | SRV/Mobiles/Mobile.cs:4552-4570
Hiding | Stealing target and Begging reveal | UOC/Skills/Stealing.cs:85,376; UOC/Skills/Begging.cs:17,20,70
Hiding | failed Snooping reveals with chance 1 - Hiding/200 | UOC/Skills/Snooping.cs:105-110
Hiding | poison reveals 40% of damage ticks | UOC/Misc/Poison.cs:150-154
Hiding | UOR gates that were checked: Lumberjacking/Mining/Fishing reveal only `Core.ML`; public moongate reveal only `Core.ML` (so not listed) | UOC/Engines/Harvest/Lumberjacking.cs:182-188, Mining.cs:452-458, Fishing.cs:470-492, UOC/Items/Skill Items/Magical/Misc/Moongate.cs:72-78
Hiding | taking a step: non-SE PlayerMobile.OnMove calls Mobile.OnMove, which reveals when AllowedStealthSteps is used up (0 by default), or when running, or mounted | UOC/Mobiles/PlayerMobile.cs:3503-3507; SRV/Mobiles/Mobile.cs:4179-4190; AllowedStealthSteps reset to 0 when Hidden changes SRV/Mobiles/Mobile.cs:7255-7258
Hiding | passive detection: either party moving within 4 tiles; both players; detector has Detect Hidden > 0; Felucca; detector.CanBeHarmful(stealther) so only a player who may attack you; not same party; not same or allied guild; roll (detect +-10) >= (Hiding +-10) | UOC/Mobiles/PlayerMobile.cs:3542-3558; UOC/Skills/DetectHidden.cs:61-128; flag default on, deployed on (Distribution/Configuration/FeatureFlags/flags.json passive_detect_hidden)
Hiding | active Detect Hidden rolls Detect +-10 against Hiding +-10 | UOC/Skills/DetectHidden.cs:197-203
Hiding | monsters with Detect Hidden > 0 look for hidden players in sight every 26 to 132 s (depends on Int); chance uses Hiding/2.9 and Stealth/1.8 | UOC/Mobiles/AI/BaseAI/BaseAI.cs:1126-1167; UOC/Mobiles/AI/BaseAI/AITimer.cs:226-248
Hiding | a failed Snooping try reveals only with that chance; Hiding needs no tool, reagent or gold | UOC/Skills/Snooping.cs:105-110 (no item use in Hiding.cs)

## Stealth

Stealth | requires Hiding Base >= 80 in UOR (30 ML, 50 SE) | UOC/Skills/Stealth.cs:11-12, 77-81
Stealth | must be hidden first: "You must hide first" | UOC/Skills/Stealth.cs:73-76
Stealth | not hidden well enough: message and RevealingAction | UOC/Skills/Stealth.cs:77-81
Stealth | armor rating (int)m.ArmorRating in non-AOS; 26 or more refuses with message and RevealingAction | UOC/Skills/Stealth.cs:38-42, 89-95
Stealth | roll CheckSkill(Stealth, -20 + AR*2, 80 + AR*2) (non-AOS) so chance (Stealth + 20 - 2 AR)/100 | UOC/Skills/Stealth.cs:96-100
Stealth | silent steps = max((int)(Stealth/10), 1) in non-AOS | UOC/Skills/Stealth.cs:102
Stealth | success message "You begin to move quietly."; failure "You fail in your attempt to move unnoticed." + RevealingAction; returns 10 s | UOC/Skills/Stealth.cs:109-120
Stealth | each step: `AllowedStealthSteps-- <= 0` reveals, so N silent steps then the next reveals; running or mounted always reveals | SRV/Mobiles/Mobile.cs:4181-4187; UOC/Mobiles/PlayerMobile.cs:3503-3507 (SE-only stealth logic not used in UOR)
Stealth | steps reset to the full count by a new Stealth success; reset to 0 when revealed (Hidden changes) | UOC/Skills/Stealth.cs:102; SRV/Mobiles/Mobile.cs:7255-7258
Stealth | no challenge (value >= max) teaches nothing; value < min fails with no gain | UOC/Skills/SkillCheck.cs:205-222
Stealth | range with armor rating A is -20+2A to 80+2A; A = 13 gives 6 to 106 | arithmetic on UOC/Skills/Stealth.cs:98-100
Stealth | full leather set armor rating 13: every piece ArmorBase 13; body-position scalars 0.07, 0.07, 0.14, 0.15, 0.22, 0.35 sum to 1.0; new item at full durability | UOC/Items/Armor/Leather/LeatherChest.cs:28, LeatherGorget.cs:27, LeatherArms.cs:28, LeatherGloves.cs:28, LeatherLegs.cs:28, Helmets/LeatherCap.cs:28; UOC/Items/Armor/BaseArmor.cs:289-328, 517; UOC/Mobiles/PlayerMobile.cs:241-257
Stealth | leather set prices at a tanner: arms 80, chest (tunic) 101, gloves 60, gorget 74, legs 80, cap 10 = 405 | UOC/Mobiles/Vendors/SBInfo/SBTanner.cs:16-21; a Tanner is spawned in Britain: GEN/Spawns/Vendors.json:150
Stealth | the 10-second wait is shared by all skills, so Hide then Stealth is about 20 s | SRV/Skills.cs:796-800
Stealth | Detect Hidden rolls against Hiding only (active and passive); monsters use min(Hiding/2.9, Stealth/1.8) | UOC/Skills/DetectHidden.cs:197-203; UOC/Mobiles/AI/BaseAI/BaseAI.cs:1158-1160
Stealth | trainers will not teach Stealth unless the student has Hiding Base >= 80 | UOC/Mobiles/BaseCreature.cs:4715-4718 (not in the text; no Stealth teacher is in the world)

## Stealing

Stealing | needs both hands empty (OneHanded and TwoHanded layers: weapon, shield) | UOC/Skills/Stealing.cs:66-67, 74-77, 127-130
Stealing | skill button, target range 1, "Which item do you want to steal?"; reveals you | UOC/Skills/Stealing.cs:72-91, 98
Stealing | target an Item = that item; target a Mobile = RandomElement of its backpack | UOC/Skills/Stealing.cs:384-400
Stealing | 10 s after the skill was used (30 s targeter minus elapsed, floor 10 s from start) | UOC/Skills/Stealing.cs:460-466
Stealing | weight limit: item weight + contents' weight at most `stealing.maxWeightToSteal` (default 10, not overridden in modernuo.json) | UOC/Skills/Stealing.cs:54, 289-295
Stealing | cannot steal: equipped ("You cannot steal items which are equipped"), own pack ("You catch yourself red-handed"), ground items and non-movable items (except stealable artifacts), corpse contents, locked container contents, newbied, blessed, player vendors | UOC/Skills/Stealing.cs:155-158, 250-253, 264-285
Stealing | pack must have room (CheckHold) | UOC/Skills/Stealing.cs:246-249
Stealing | must be within 1 tile of the item | UOC/Skills/Stealing.cs:255-258
Stealing | roll CheckTargetSkill(Stealing, item, iw - 22.5, iw + 27.5) where iw = ceil(weight + contents) * 10 | UOC/Skills/Stealing.cs:343-346
Stealing | table rows: weight 1: -12.5/37.5, 3: 7.5/57.5, 5: 27.5/77.5, 10: 77.5/127.5 (never certain at 100) | arithmetic on UOC/Skills/Stealing.cs:343-346
Stealing | stack: random amount 1..maxAmount, maxAmount = clamp((int)(skill/10/weight), 1, Amount); pile weight of that amount sets the range | UOC/Skills/Stealing.cs:300-340
Stealing | _rolled true only when the weight check passed (a roll is made); refused attempts are not rolls | UOC/Skills/Stealing.cs:296-298
Stealing | caught = Stealing < Random(150): 149/150 at 0, 99/150 at 50, 49/150 at 100 | UOC/Skills/Stealing.cs:367
Stealing | caught victim is a mobile: if victim not in Thieves' Guild and Innocent to the thief the thief gets CriminalAction; everyone in 8 tiles of the thief is told "You notice X trying to steal from Y" | UOC/Skills/Stealing.cs:422-445
Stealing | stolen from a container nobody carries: root is an Item, so neither branch of the caught block applies | UOC/Skills/Stealing.cs:384-388, 420-445
Stealing | -50 karma every attempt via Titles.AwardKarma(from, -50) (scaled by current karma) | UOC/Skills/Stealing.cs:406; UOC/Misc/Titles.cs:216-250
Stealing | Criminal flag lasts 2 minutes | SRV/Mobiles/Mobile.cs:1865
Stealing | guards respond to a criminal in a guarded region (TownRegion is a GuardedRegion; Britain is a TownRegion without GuardsDisabled; Buccaneer's Den has GuardsDisabled true) | UOC/Regions/GuardedRegion.cs:226-234, 337-345; UOC/Regions/TownRegion.cs:5,33; ModernUO/Distribution/Data/regions.json (Britain, Buccaneer's Den entries)
Stealing | bankers refuse criminals; healers refuse criminals and murderers | BR/WelcomeGuide.GettingStarted.cs:226, 345
Stealing | Recall and Gate Travel refuse a criminal | UOC/Spells/Fourth/Recall.cs:69-72, 174-177; UOC/Spells/Seventh/GateTravel.cs:59, 120
Stealing | stolen non-stack, non-container items are marked for 2 minutes: cannot be traded; returned to the victim if the thief dies carrying it | UOC/Skills/Stealing.cs:410-418, 471-551; UOC/Mobiles/PlayerMobile.cs:2270-2285
Stealing | victim already criminal or murderer to the thief: IsInnocentTo false, no CriminalAction | UOC/Skills/Stealing.cs:64, 430
Stealing | stealing from players needs the Thieves' Guild ("You must be in the thieves guild to steal from other players") | UOC/Skills/Stealing.cs:62, 139-142
Stealing | member with Kills > 0 is suspended (suspendOnMurder default !Core.AOS = true, not overridden) | UOC/Skills/Stealing.cs:52, 143-146
Stealing | guards take no report against a Thieves' Guild member (shard text, stock rule unchanged) | BR/WelcomeGuide.cs:265; ShardContent/docs/Murder-Report-Right-To-Attack.md:44
Stealing | SafeWorld: a victim must pass `_thief.CanBeHarmful` -> AllowHarmful: target criminal/murderer, or Intent on, or existing aggression, or guild war/duel, or both in the same Hot region | UOC/Skills/Stealing.cs:276-278; BR/PvpIntentService.cs:230-248, 355-440; live case T2 "no steal outside Hot on a blue": ShardContent/docs/Alpha-3-Outdoor-Hot-Zone-Survey.md (case table, T1/T2)
Stealing | Hot Zones: Fire Island, Buccaneer's Den island, Hythloth | ShardContent/data/configuration/shard-rules.json hotZones; BR/WelcomeGuide.cs:275-277
Stealing | Ward does nothing in a Hot Zone | BR/TheftProtectionService.cs:253-256, 273
Stealing | 17 bank polygons of 24 by 24 tiles; either party inside blocks stealing from players; message text | ShardContent/data/configuration/shard-rules.json theftRegions.bankProtectionPolygons (17, each 24 x 24 checked by script); BR/TheftRegionPolicy.cs:11-18; BR/TheftProtectionService.cs:232-237
Stealing | Backpack Ward and Nontransferable items cannot be stolen: "That protected item cannot be stolen." | BR/TheftProtectionService.cs:246-251
Stealing | Ward: 25/50/100% extra detection for the first/second/third undetected successful theft per thief; exposure makes the thief criminal, tells "You have been caught stealing!", blocks the thief account until the Ward ends; 30 quiet minutes | BR/TheftProtectionService.cs:197-204; BR/BackpackWardService.cs:168-218, 220-236; BR/BackpackWardState.cs:32, 91, 111, 114; BR/WelcomeGuide.cs:339-358
Stealing | Ward block is by account (any character) | BR/BackpackWardService.cs:152-160 (account.Username), 168-178; BR/WelcomeGuide.cs:343
Stealing | Knocked Out target refused by AllowHarmful | BR/PvpIntentService.cs:357-360
Stealing | Knocked Out pack looting rules in a Hot Zone / elsewhere (cited on the Snooping page) | BR/KnockedOutService.cs:223-268, 289-296; BR/WelcomeGuide.cs:287-291
Stealing | criminal is attackable by any player under Safe World | BR/WelcomeGuide.cs:211-213; BR/PvpIntentService.cs:416-440
Stealing | a criminal is not Knocked Out: Knocked Out only for a victim who is not a criminal or murderer | BR/KnockedOutService.cs:220-221; BR/WelcomeGuide.cs:231
Stealing | training weights: chance (skill - (10w - 22.5))/50; 25% at w = skill/10 + 1; 45% at skill 100 with w = 10 | arithmetic on UOC/Skills/Stealing.cs:343-346
Stealing | no guards in Buccaneer's Den | ModernUO/Distribution/Data/regions.json ("Buccaneer's Den" GuardsDisabled true)
Stealing | stealing never gives murder counts (no Kills change in the skill); murder counts come from kills | UOC/Skills/Stealing.cs (whole file); BR/WelcomeGuide.cs:264-265

## Snooping

Snooping | no skill button (Callback null; skills.mul clickable 0) | UOC/Skills/Snooping.cs:14-17; UOData/skills.mul (parsed)
Snooping | double-click a container whose root is another mobile -> OnSnoop -> Container_Snoop | SRV/Mobiles/Mobile.cs:5048-5051; SRV/Items/Container.cs:196-198
Snooping | must be within 1 tile: "That is too far away." | UOC/Skills/Snooping.cs:45-49
Snooping | locked container: "It appears to be locked." | UOC/Items/Containers/LockableContainer.cs:149-163, 205-212
Snooping | refused for staff targets and for players you cannot harm: "You cannot perform negative acts" | UOC/Skills/Snooping.cs:19-26, 64-68
Snooping | non-player targets: Felucca map rules None, so allowed | UOC/Skills/Snooping.cs:28-31; SRV/Maps/Map.cs:36-38; ModernUO/Distribution/Data/map-definitions.json:10
Snooping | roll CheckTargetSkill(Snooping, 0, 100): chance skill/100; success opens (DisplayTo); trapped TrappableContainer fires its trap instead | UOC/Skills/Snooping.cs:94-102
Snooping | failure message "You failed to peek into the container."; revealed with chance 1 - Hiding/200 | UOC/Skills/Snooping.cs:103-111
Snooping | notice: before the roll, if Snooping < 100 and Snooping < random*100, every client within 8 tiles of the snooper except the snooper gets "You notice X attempting to peek into Y's belongings" | UOC/Skills/Snooping.cs:70-90
Snooping | -4 karma each attempt (players) | UOC/Skills/Snooping.cs:91
Snooping | no criminal action in the skill | UOC/Skills/Snooping.cs (whole file)
Snooping | no skill wait: no NextSkillTime in the double-click path | SRV/Mobiles/Mobile.cs:4999-5051
Snooping | SafeWorld rule (CanBeHarmful -> AllowHarmful) | UOC/Skills/Snooping.cs:23-26; BR/PvpIntentService.cs:355-440
Snooping | Knocked Out: AllowHarmful refuses; KnockedOutOpen opens the pack with no roll, karma or notice for an eligible looter (Hot Zone: anyone; elsewhere criminal/murderer with recorded rights); a blue who then takes an item becomes criminal | UOC/Skills/Snooping.cs:58-62; BR/KnockedOutService.cs:223-268, 289-296, 301-312; BR/WelcomeGuide.cs:287-291
Snooping | after a peek, Stealing needs the Thieves' Guild for players | UOC/Skills/Stealing.cs:139-142
Snooping | training on NPCs: Snooping NPCs is allowed; shards' vendors can be snooped (no vendor override) | UOC/Skills/Snooping.cs:28-31

## Lockpicking

Lockpicking | no skill button (skills.mul clickable 0, no callback) | UOData/skills.mul (parsed); SRV/Skills.cs:796-808
Lockpicking | double-click a Lockpick, target an ILockpickable within 1 tile; "You can't unlock that!" otherwise; "This does not appear to be locked" | UOC/Items/Skill Items/Thief/LockPick.cs:49-52, 56-80, 82-104
Lockpicking | only LockableContainer family implements ILockpickable (no doors) | UOC/Items/Containers/LockableContainer.cs:10; grep ILockpickable (Key.cs, MarkContainer, PuzzleChest, TreasureMapChest, ForensicEval, MagicLock, Unlock)
Lockpicking | 3-second timer, then one roll; out of range loses the try | UOC/Items/Skill Items/Thief/LockPick.cs:106-112, 134-141
Lockpicking | CannotPick (0) and MagicLock (-255): "This lock cannot be picked by normal means" | UOC/Items/Skill Items/Thief/LockPick.cs:143-149; UOC/Spells/Third/MagicLock.cs:35,58
Lockpicking | skill below RequiredSkill: "You don't see how that lock can be manipulated." (no pick lost) | UOC/Items/Skill Items/Thief/LockPick.cs:151-157
Lockpicking | roll CheckTargetSkill(Lockpicking, lock, LockLevel, MaxLockLevel); success "The lock quickly yields to your skill." | UOC/Items/Skill Items/Thief/LockPick.cs:161-167
Lockpicking | failure "You are unable to pick the lock."; 1 in 4 breaks the pick | UOC/Items/Skill Items/Thief/LockPick.cs:119-131, 169-175
Lockpicking | lockpicks stack | UOC/Items/Skill Items/Thief/LockPick.cs:45
Lockpicking | auto-repeat (flag ActionAutoRepeat): repeats the same lock after a plain failure while a pick remains and the lock is locked; stopped by the usual interrupts | BR/ActionRepeatService.cs:55-56, 74-75, 175-190; BR/WelcomeGuide.GettingStarted.cs:283-286
Lockpicking | refilling chest locks: difficulty (level - 1) * 30; LockLevel difficulty - 10, MaxLockLevel difficulty + 30, RequiredSkill difficulty; levels 1 to 3 (FillableContent definitions) | UOC/Items/Containers/Fillable Containers/FillableContainer.cs:153-161; FillableContent.ContentTypes.cs (level argument of each definition, max 3)
Lockpicking | refill: 60 to 90 minutes, relock and retrap on Respawn; timer starts when an item is removed or a lock is picked | FillableContainer.cs:31-32, 97-106, 128-175
Lockpicking | treasure-map chests: RequiredSkill 36/76/84/92/100 for levels 1..5, LockLevel = Required - 10, MaxLockLevel = Required + 40, explosion trap power 25 x level | UOC/Items/Containers/TreasureMapChest.cs:175-207
Lockpicking | treasure maps are loot from some monsters in Felucca (1%) | UOC/Mobiles/BaseCreature.cs:3224-3251; UOC/Items/Maps/TreasureMap.cs:17
Lockpicking | craft-made boxes: Carpentry WoodenBox/SmallCrate/MediumCrate/LargeCrate are LockableContainers; OnCraft: Tinkering CheckSkill(-5, 15) gives a key and lock; level = (int)(Tinkering*0.8); Required min(level - 4, 95); Max min(level + 35, 95); LockLevel min(level - 14, 95) | UOC/Items/Containers/LockableContainer.cs:17-47; UOC/Engines/Craft/DefCarpentry.cs:218-221; UOC/Engines/Craft/T2A/CarpentryMenu.cs:31; ICraftable called from UOC/Engines/Craft/Core/CraftItem.cs:1457
Lockpicking | at Tinkering 50: level 40, required 36, range 26 to 75; at 100: level 80, required 76, range 66 to 95 | arithmetic on LockableContainer.cs:32-38
Lockpicking | key locks and unlocks (toggles) its container | UOC/Items/Misc/Key.cs:168-204
Lockpicking | lockpicks sold by Provisioners at 12 (stock 20), bought back at 6 | UOC/Mobiles/Vendors/SBInfo/SBProvisioner.cs:39, 123; Provisioner.cs:22; GEN/Spawns/Vendors.json:758,1477 (Provisioner spawned in Britain)
Lockpicking | Tinkering recipe for a Lockpick: 45.0 to 95.0, 1 iron ingot; in the T2A tool list | UOC/Engines/Craft/DefTinkering.cs:263; UOC/Engines/Craft/T2A/TinkeringMenu.cs:47
Lockpicking | Tinkers' Guildmaster teaches Lockpicking: skill 65 to 88, lesson to a third (21.6 to 29.3), price 1 gold per 0.1 point; one is spawned in Britain | UOC/Mobiles/Vendors/NPC/Guildmasters/TinkerGuildmaster.cs:14; UOC/Mobiles/BaseCreature.cs:4754-4766, 4912; BR/WelcomeGuide.GettingStarted.cs:188-193; GEN/Spawns/Vendors.json:102
Lockpicking | traps on a refilling chest fire on open (`TrapOnOpen`); a trap set by a tinker fires when the lock is picked (`TrapOnLockpick`) | UOC/Items/Containers/LockableContainer.cs:13, 94-104; UOC/Items/Containers/TrappableContainer.cs:34, 67-72; UOC/Engines/Craft/DefTinkering.cs:683
Lockpicking | explosion damage Random(10,30) x TrapLevel (levels 1 to 3 shop/hall chests, up to 5 treasure) | UOC/Items/Containers/TrappableContainer.ExecuteTrap.cs:59-75
Lockpicking | trap fraction on level-1 refilling chests 4 in 5; always trapped from level 2 | FillableContainer.cs:164
Lockpicking | Magic Lock cannot be picked; Unlock spell or the key opens it | UOC/Spells/Third/MagicLock.cs:58; UOC/Spells/Third/Unlock.cs:58-73; UOC/Items/Misc/Key.cs:199-205
Lockpicking | testing a lock costs time only: the required-skill refusal comes before the break roll | UOC/Items/Skill Items/Thief/LockPick.cs:151-175
Lockpicking | training ranges: roll refused below LockLevel with no gain (value < min), Required = LockLevel + 10 in every source, so the first allowed roll has chance >= 25% (fillable) | UOC/Skills/SkillCheck.cs:205-222; sources above
Lockpicking | Dexterity helps the skill (DexScale) | ModernUO/Distribution/Data/skills.json (Lockpicking DexScale 0.25); shown by the generated Stats block

## Remove Trap

Remove Trap | requires Lockpicking Value >= 50 and Detect Hidden Value >= 50, messages 502366/502367 | UOC/Skills/RemoveTrap.cs:17-24
Remove Trap | target range 2; Mobile target: inappropriate; TrapType None: "That doesn't appear to be trapped" | UOC/Skills/RemoveTrap.cs:36, 42-52
Remove Trap | roll CheckTargetSkill(RemoveTrap, trap, TrapPower, TrapPower + 30); success "You successfully render the trap harmless"; failure "You fail to disarm the trap... but you don't set it off" | UOC/Skills/RemoveTrap.cs:61-71
Remove Trap | returns 10 s; no cancel handler | UOC/Skills/RemoveTrap.cs:31
Remove Trap | value below the trap's strength fails with no gain; value at or above strength + 30 succeeds with no gain | UOC/Skills/SkillCheck.cs:205-222
Remove Trap | trap strengths: treasure chest TrapPower 25 x level; refilling chest level x Random(10..30) with level 1 to 3; tinker trap 9 x (int)(Tinkering/10); Magic Trap 1 (non-AOS) | UOC/Items/Containers/TreasureMapChest.cs:193-194; FillableContainer.cs:164-168; UOC/Engines/Craft/DefTinkering.cs:678-682; UOC/Spells/Second/MagicTrap.cs:36-38
Remove Trap | Magic Trap is second circle Magery | UOC/Spells/Second/MagicTrap.cs:21
Remove Trap | trap effects: explosion Random(10,30) x TrapLevel; dart Random(5,15) x TrapLevel; poison Poison.GetPoison(clamp(level - 1, 0, 4)); magic trap Damage(TrapPower); explosion/dart/poison hurt only within 3 tiles, magic within 1 | UOC/Items/Containers/TrappableContainer.ExecuteTrap.cs:56-135
Remove Trap | poison levels Lesser 0, Regular 1, Greater 2, Deadly 3, Lethal 4 | UOC/Misc/PoisonKinds.cs:44-56, 80-84
Remove Trap | tinker trap levels: level = (int)(Tinkering/10) up to 10; TrapOnLockpick true; message "Trap is disabled until you lock the chest." | UOC/Engines/Craft/DefTinkering.cs:675-686
Remove Trap | trap crafts: dart 30-80 (iron ingot + bolt), poison 30-80 (ingot + poison potion), explosion 55-105 (ingot + explosion potion) | UOC/Engines/Craft/DefTinkering.cs:431-448
Remove Trap | the "Traps" category is in the T2A Tinkering menu | UOC/Engines/Craft/T2A/TinkeringMenu.cs:59-62, 211
Remove Trap | trap craft target must be an unlocked, movable (not locked down), accessible, key-bearing LockableContainer within 2 tiles with no trap | UOC/Engines/Craft/DefTinkering.cs:614-648
Remove Trap | key re-enables ("You re-enable the trap") when locking, disables when unlocking a TrapOnLockpick trap | UOC/Items/Misc/Key.cs:188-203
Remove Trap | Detect Hidden on a trapped container within range shows "[trapped]" | UOC/Skills/DetectHidden.cs:147-163
Remove Trap | trainers: Tinkers' Guildmaster has Remove Trap 85 to 100 (lesson to 28.3 to 33.3); teaches only if the student has Lockpicking and Detect Hidden Base >= 50; price 1 gold per 0.1 point | UOC/Mobiles/Vendors/NPC/Guildmasters/TinkerGuildmaster.cs:16; UOC/Mobiles/BaseCreature.cs:4720-4724, 4754-4766, 4912
Remove Trap | a trainer lesson of at least 20.0 requires the NPC to have 60.0 or more | UOC/Mobiles/BaseCreature.cs:2859, 4754-4761
Remove Trap | prices: iron ingot 5 at a Blacksmith (stock 16), crossbow bolt 5 at a Provisioner (stock 20), Lesser Poison Potion 15 and Lesser Explosion Potion 21 at an Alchemist (stock 10 each); Britain spawns Blacksmith x2, Provisioner x2, Alchemist x3 | UOC/Mobiles/Vendors/SBInfo/SBBlacksmith.cs:16, SBProvisioner.cs:28, SBAlchemist.cs:21,23; GEN/Spawns/Vendors.json (Britain list)
Remove Trap | the trap crafts accept any BasePoisonPotion / BaseExplosionPotion (the Lesser potions derive from them) | UOC/Engines/Craft/DefTinkering.cs:436-448 (type check; Lesser potions derive from the bases: LesserPoisonPotion.cs, LesserExplosionPotion.cs)
Remove Trap | tinker Tinkering windows (27-57 ... 90-120) and "80 or more for 100" | arithmetic: power = 9 x floor(T/10), window power..power+30
Remove Trap | Magic Trap window 1 to 31 | arithmetic on MagicTrap.cs:38 and RemoveTrap.cs:61

## Detecting Hidden

Detecting Hidden | skill button; asks "Where will you search?"; UOR use delay 1 s | UOC/Skills/DetectHidden.cs:30-36
Detecting Hidden | target range 12, ground allowed | UOC/Skills/DetectHidden.cs:132
Detecting Hidden | range = (int)(skill/10); area scan only when pointing at the ground or at yourself; CheckSkill(0,100), failure halves the range; range 0 finds nothing | UOC/Skills/DetectHidden.cs:145, 165-189
Detecting Hidden | house you own/co-own/are a friend of at the target point: range 22; hidden people inside the house are revealed even if they win the roll | UOC/Skills/DetectHidden.cs:180-186, 200
Detecting Hidden | every hidden mobile in range of the target point is rolled (detect +-10 against Hiding +-10) and revealed with "You have been revealed!" | UOC/Skills/DetectHidden.cs:190-212
Detecting Hidden | no party or friend exclusion in the active skill | UOC/Skills/DetectHidden.cs:190-212
Detecting Hidden | nothing found: "You can see nothing hidden there." | UOC/Skills/DetectHidden.cs:257-260
Detecting Hidden | pointing at another mobile does nothing (not a container, not self, not ground) | UOC/Skills/DetectHidden.cs:147, 165
Detecting Hidden | container: within range and CheckSkill(0,100) shows "[trapped]" (message 500813) when TrapType != None | UOC/Skills/DetectHidden.cs:147-163
Detecting Hidden | cadence: after a target resolves, NextSkillTime is recomputed from the 30-second targeter origin, which gives 0 remaining in UOR | UOC/Skills/DetectHidden.cs:262-265 (see OPEN 3)
Detecting Hidden | CheckSkill is called on every area search, so it teaches whether or not anyone is hidden | UOC/Skills/DetectHidden.cs:175; UOC/Skills/SkillCheck.cs:118-181
Detecting Hidden | 20 or more above always finds, more than 20 below never (uniform +-10 on both sides) | arithmetic on DetectHidden.cs:197-203
Detecting Hidden | passive detection (see Hiding) | UOC/Mobiles/PlayerMobile.cs:3542-3558; UOC/Skills/DetectHidden.cs:61-128
Detecting Hidden | Remove Trap needs 50 | UOC/Skills/RemoveTrap.cs:21
Detecting Hidden | monsters with the skill look for hidden players (see Hiding) | UOC/Mobiles/AI/BaseAI/BaseAI.cs:1126-1167

## Begging

Begging | skill button; "To whom do you wish to grovel?"; reveals you | UOC/Skills/Begging.cs:15-25
Begging | target range 12 but beggar must be within 2 tiles ("You are too far away to beg from him/her") | UOC/Skills/Begging.cs:29, 52-62
Begging | player target: "Perhaps just asking would work better."; non-human body: "There is little chance of getting money from that!"; non-Mobile: same | UOC/Skills/Begging.cs:40-50
Begging | mounted (non-ML): "They seem unwilling to give you any money." | UOC/Skills/Begging.cs:63-67
Begging | bow, then a 2-second timer; cooldown 10 s from the skill use; invalid target resets NextSkillTime | UOC/Skills/Begging.cs:70-83, 90, 164-170
Begging | refusal before the roll when Karma < 0 with chance 0.5 - Karma/8570: "Thou dost not look trustworthy" | UOC/Skills/Begging.cs:100, 106-110
Begging | roll CheckTargetSkill(Begging, 0, 100) | UOC/Skills/Begging.cs:111
Begging | gift = (gold in their pack)/10, capped at clamp(10 + Fame/2500, 10, 14); under 10 gold: "I have not enough money to give thee any!" | UOC/Skills/Begging.cs:113-157
Begging | karma loss per gift = min(Karma + 3000, 40) while Karma > -3000, passed to AwardKarma (scaled by positive karma) | UOC/Skills/Begging.cs:135-144; UOC/Misc/Titles.cs:216-250
Begging | shopkeepers start with PackGold(100, 200) in BaseVendor.InitOutfit; no code refills it | UOC/Mobiles/Vendors/BaseVendor.cs:828-871
Begging | no per-person limit or cooldown in the skill | UOC/Skills/Begging.cs (whole file)
Begging | no criminal action in the skill | UOC/Skills/Begging.cs (whole file)
Begging | Fame rises from kills (Fame/100 per kill); karma from kills is -Karma/100 of the killed creature, so evil monsters raise it | UOC/Misc/Titles.cs:119-131
Begging | Snooping and Stealing cost karma | UOC/Skills/Snooping.cs:91; UOC/Skills/Stealing.cs:406

## Every page

All | `{"generate":"stats"}` and `{"generate":"gain"}` are on every page; no recipe table (none of these skills has a craft) | ShardContent/docs/Help-Content-Spec.md
All | every `requires` is a property of `DeferredFeatureFlags`: SafeWorld, HotZones, TheftProtection, KnockedOut, ActionAutoRepeat | BR/ShardRulesConfiguration.cs:758-852
All | flags off in shard-rules.json (CoolZones and the others) are not mentioned; the Cool Dungeon theft rule is not mentioned | ShardContent/data/configuration/shard-rules.json featureFlags
All | in the text: the Welcome guide is named as `[Welcome` and the pages "Training", "Backpack Ward" exist | BR/WelcomeGuide.cs:131-181, BR/WelcomeGuide.GettingStarted.cs:14-22, 178-213
All | counts of own text with every gated paragraph shown: Hiding 3125, Stealth 2756, Stealing 5308, Snooping 2782, Lockpicking 3660, Remove Trap 4030, Detecting Hidden 2223, Begging 2457 characters

## OPEN

1. **No Thieves' Guildmaster is in the world.** The only `ThiefGuildmaster` spawner in the stock data is at Buccaneer's Den (`ModernUO/Distribution/Data/Spawns/shared/felucca/Vendors.json:1515`). Alpha 2b generation keeps `Vendors.json` and `TownsPeople.json` only inside Britain (`ShardContent/data/world-generation/alpha2b/world-generation.json` `britainOnlySpawnerFiles`), and the generated `GEN/Spawns/Vendors.json` has no ThiefGuildmaster (nor Thief, Ranger, RangerGuildmaster, Tinker or GolemCrafter). So no player can join the Thieves' Guild by normal play, and stealing from another player (guild required, `Stealing.cs:139-142`) is impossible for an ordinary player. The Stealing page states the rule and says nothing about where to join. If a guildmaster is spawned later, the entry facts are: character at least 7 days old and 2 days of play, 500 gold, no murder counts, Stealing 60.0 or more, not a guild member elsewhere (`ThiefGuildmaster.cs:31-48`, `BaseGuildmaster.cs:21-24, 85-100`).
2. **Which Britain containers are really locked or trapped is unverified.** A refilling container only gets a content type (and so a lock and a trap) if a vendor stands within 20 tiles when it is placed (`FillableContent.Acquire`, `FillableContent.cs:70-113`); decoration is generated before the spawners, so many may be unlocked and empty. Only the containers with an explicit `ContentType` are certain (in `GEN/Decoration/Britannia__britain.cfg`: 4 Guard chests at 1408,1715-1718 and 1512-1515,1610, 4 ThiefGuild chests at 1659-1662,1632, 2 Farm chests). The pages therefore describe lock and trap numbers and never name a place.
3. **Detecting Hidden cadence.** `OnUse` returns 1 s in UOR but the target handler then sets `NextSkillTime = now + max(0, 10000 - elapsed - 29000)`, which is now, so searches can follow each other as fast as the player can target (audit item SK-007 in `Alpha-3-Player-Skill-Audit.md`). The page says "almost no wait". If the intended cadence is different, change that sentence.
4. **Shopkeepers are not invulnerable in this world** (`vendor.isInvulnerable` defaults to `Core.LBR`, false in UOR; not set in modernuo.json). So the stock refusal "You can't steal from shopkeepers" never fires, and a vendor's pack can be robbed and snooped. The pages say nothing about shopkeepers being safe or unsafe except the training advice "do not practise on shopkeepers or townspeople" and "snoop shopkeepers". Confirm that is intended.
5. **Stealing from a player who is not a Thieves' Guild member** adds the thief to the victim's `PermaFlags` (`Stealing.cs:451-456`; `ClassicMode` is on in UOR), making the thief show as attackable to that victim until the thief dies (`Notoriety.cs:479`, `PlayerMobile.cs:2577, 2816-2826`). Under Safe World `AllowHarmful` does not read `PermaFlags`, so the practical effect is unverified. Left out of the text.
6. **`BaseHouse.IsFriend` needs a non-null Friends list** (`BaseHouse.cs:3612`), so a house owner with no friends list might not count as a friend for the Hiding and Detecting Hidden house rules. The text says "own or are a friend of". Not tested live.
7. **Remove Trap cannot start from 0.** With the stock check, no trap can teach a character with Remove Trap below the weakest trap strength (1). The Faint Memories and Skill Bank restores are applied inside the skill-gain roll, which is never reached below the trap's strength, so they cannot help either. The only way in is a trainer lesson (Tinkers' Guildmaster, Britain). If that NPC is ever removed, the skill becomes untrainable. The text says to begin with the lesson.
8. **Remove Trap prerequisite uses `Skill.Value`** (includes the Dexterity bonus for Lockpicking), the trainer check uses `Skill.Base` (`RemoveTrap.cs:17-21` against `BaseCreature.cs:4720-4724`). The text says "50" for both without distinguishing.
9. **Stealth step logic of newer eras (`PlayerMobile.OnMove` for SE)** is not used in UOR; the text follows the Mobile.OnMove path. Not live-tested; Navrey could confirm "N silent steps then reveal" for Stealth 10 (1 step) and 100 (10 steps).
10. **Treasure-map chests (levels 1 to 5)** are described from `TreasureMapChest.Fill`; the Cartography page owner should confirm treasure maps are obtainable (1% monster loot is the only source found).
11. **Armor rating shown to the player** is `(int)(AR + 0.5)` in the status packet (`OutgoingMobilePackets.cs:533`) while Stealth truncates (`Stealth.cs:42`); the text gives only the leather figure (13) and the threshold 26 and does not say where to read the rating.
12. **Dart/poison/explosion trap crafting and the Carpentry-box key path were read, not run.** Both are in the T2A menus per source, not tested on a live host.
13. **Passive Detect Hidden is a stock default kept by the owner** (`Alpha-3-Contract-Review.md` J-7). The text describes it for players who may attack each other only, which is what `CanBeHarmful` leaves.

## For the coordinator to decide

- OPEN 1 is a design question: spawn a Thieves' Guildmaster (where?) or accept that player-to-player theft cannot happen. Until then the Stealing page's "Stealing from other players" section describes a rule no player can use. If you prefer, drop that section and the Ward/bank paragraphs from this page.
- Whether item topics for Lockpick (`Lockpick`) and `Key`/`KeyRing` should link to these pages (skills `Lockpicking`, `Tinkering`); the item writers own those. `Lockpick` is the only holdable item class these pages depend on.
- The Remove Trap page names Tinkering traps (Tinkering, Traps). The Tinkering page's craft table does not list the trap crafts under "Traps" with their targeting step, so the Remove Trap page explains how to set one.
