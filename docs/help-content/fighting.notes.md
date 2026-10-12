# Fighting skill pages: claim notes (Wrestling, Swords, Macing, Fencing, Archery, Parry, Tactics, Anatomy, Healing)

Output: `parts/fighting.skills.json` (9 pages). Every page has the `stats` and `gain` blocks, 5 headings and between 2,500 and 5,400 characters of own text with every gated paragraph counted (about 1,000 of those characters are gated paragraphs, so the ungated text is 2,100 to 4,300).
Format of the claim lines: `skill | claim | source file:line`. Paths are relative to the workspace root; `UOC` = `ModernUO/Projects/UOContent`, `SRV` = `ModernUO/Projects/Server`, `SC` = `ShardContent/src/BritanniaRenaissance.Content`, `SPAWN` = `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns`.
Era: UOR (`ShardContent/data/configuration/expansion.json`, Id 2, UOR true, UOTD/LBR/AOS false; `SRV/ExpansionInfo.cs:24-38`, `SRV/Main.cs:330`). Every path below was read for the non-AOS branch.

## OPEN: (left out of the text, or worded softly, for the coordinator)

OPEN: Generated `stats` block is wrong for Tactics and Anatomy. `HelpGenerators.StatsText` (SC/HelpGenerators.cs, StatsText) says "It leans on X, then Y: the higher they are, the better the skill works for you than its number says" from `PrimaryStat`/`SecondaryStat` only. In `ModernUO/Distribution/Data/skills.json` Tactics and Anatomy have StrScale = DexScale = IntScale = 0, so `Skill.Value` (SRV/Skills.cs:253-290) gets no stat bonus at all. The two pages say "no stat adds to it; only training raises it" (the true statement), which will contradict the generated paragraph until the generator skips the "leans on" sentence when all three scales are 0.
OPEN: `Novice-Combat-Assist-Evidence.md` ("Named limits") says an Orc has 96 to 120 hit points. The code is `SetHits(58, 72)` (UOC/Mobiles/Monsters/Humanoid/Melee/Orc.cs:20; 96 to 120 is its Strength). The pages use the code. Documentation error only.
OPEN: Knocked Out duration. `SC/KnockedOutService.cs:18` is 30 seconds; `Guide-Getting-Started-Pages.md` says 90. The pages give no number.
OPEN: `SBWeaponSmith.cs:39` builds its sword, axe, dagger and bow stock inside `switch (Utility.Random(3)) { case 0: ... }` with only a `case 0`, so a Weaponsmith carries Katana, Kryss, Bow and the others only about one time in three (rolled again at every start, the vendor stock is not saved). The maces, staves and spears (lines 14-37) are always carried. The pages send players to the Blacksmith (SBBlacksmith lists everything with no random part) and say a Weaponsmith "carries swords and axes only some of the time". Possible design question: is the random stock intended?
OPEN: One-handed or two-handed for weapons without an explicit `Layer =` comes from `Item.Layer = ItemData.Quality` (UOC/Items/Weapons/BaseWeapon.cs:250), i.e. the client's `tiledata.mul`. I read `UOData/tiledata.mul` myself (item entries after 512 land groups; Quality 1 = OneHanded, 2 = TwoHanded): one-handed Katana, Kryss, Club, Mace, Dagger, Longsword, Broadsword, Cutlass, Scimitar, Viking Sword, Long Sword (thin), War Mace, Maul, War Fork, War Axe; two-handed Axe, Hatchet, Double Axe, Two Handed Axe, Large Battle Axe, Executioner's Axe, Bardiche, Halberd, Quarter Staff, Black Staff, Gnarled Staff, Shepherd's Crook, Short Spear, Spear, Pitchfork. Explicit in code: Bow, Crossbow, Heavy Crossbow, Battle Axe, War Hammer two-handed; Hammer Pick one-handed. Not confirmed in a running server or client.
OPEN: Training lessons from guildmasters and wandering healers. `BaseVendor.CanTeach` is true (UOC/Mobiles/Vendors/BaseVendor.cs:114) and the guildmasters and `WanderingHealer` have no `CheckTeach` restriction that excludes the skills named, so the pages name the Warrior, Mage, Healer and Bard Guildmasters and wandering healers as teachers. The Welcome guide's "Who teaches what" list (SC/WelcomeGuide.GettingStarted.cs:195-203) does not list guildmasters or wandering healers. Not tried in a running game; the coordinator may want to reconcile the two lists.
OPEN: The monster "sensible order" (which monster for which skill range) is advice, not a code claim. The Wrestling skill and hit points of each monster are from code (claims below); the skill ranges were chosen from the hit-chance formula. I did not name hunting grounds beyond "Britain's streets have rats": the spawner files do not say which spawner is near a safe path, and I did not want to promise one.
OPEN: Healing and bandage thresholds (60 cure, 80 resurrect) are compared with `Skill.Value` (base plus the stat bonus) in `Bandage.cs:319-322, 237-240`, so Healing can qualify a few points under the displayed base (Healing has a stat scale of 0.2 in total). Anatomy has no stat bonus. The Healing page says so in one parenthesis; the Poison Relief hint (PoisonReliefService.cs:28) and the potion pages say "60" plainly.
OPEN: "The Healer sells bandages 20 at a time" is the initial `GenericBuyInfo` amount (SBHealer.cs:16). I did not read the restock timer, so the page does not say how fast it refills. Only one `Healer` spawner exists (Vendors.json, location [1471, 1611, 20] with a Healer Guildmaster), so a long Healing session means several trips or cutting cloth.
OPEN: Poison Relief page text says "a character created while it is on starts with 5 Lesser Cure potions". Potions go only to characters created while the flag was on (SC/PoisonReliefService.cs:108-128, Poison-Relief-Evidence.md "Named limits"); the numbers 5 and 30 seconds are the shipped `shard-rules.json:136-140` and will drift if the owner changes them.
OPEN: Dummies and buttes are in the decoration data (`ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Decoration/Britannia__britain.cfg:1431-1436` buttes at (1468,1579) and (1473,1576), `:1465-1475` dummies at (1589..1597,1554), (1349..1353,1777..1779), (1340..1350,1737..1744) and two at (1524..1528,1431..1436)); I never saw them in the client.

## Shared claims (used by several pages)

All weapon pages | Hit chance = (attacker skill + 50) / (2 x (defender skill + 50)), UOR branch | UOC/Items/Weapons/BaseWeapon.cs:1396-1402 (Core.AOS false)
All weapon pages | The skill check that feeds gain is `attacker.CheckSkill(weaponSkill, chance)`, done for hits and misses | BaseWeapon.cs:1411; SRV/Mobiles/Mobile.cs:8219-8220
All weapon pages | A chance of 1.0 or more returns success with no gain: skill >= 2 x defender skill + 50 means no more gain | UOC/Skills/SkillCheck.cs:101-116 (lines 108-111)
All weapon pages | The defender's skill is the skill of the weapon it holds, Wrestling when empty-handed; Fists defend with Wrestling only (no Anatomy/EvalInt mix, that needs `Core.LBR`) | BaseWeapon.cs:1281-1287, 1223-1277; UOC/Items/Weapons/Fists.cs:45-59; SRV/Main.cs:330
All weapon pages | Monsters hold no weapon (Orc, Lizardman, Ratman, Ettin, Troll, Ogre, Zombie, Skeleton, Headless One, Rat: no `AddItem`/`EquipItem` of a weapon) so they defend with Wrestling | UOC/Mobiles/Monsters/Humanoid/Melee/*.cs, Animals/Town Critters/Rat.cs (grep for AddItem: only Headless One's corpse body part)
All weapon pages | Stats add a few points to a low weapon skill (StrScale/DexScale, capped by StatTotal x (100 - base)) | SRV/Skills.cs:253-290, 395-418; skills.json entries for IDs 31, 40-43
All weapon pages | Swing wait = 15000 / ((stamina + 100) x speed) seconds, which is 75 / speed at stamina 100 | BaseWeapon.cs:1555-1565; UOC weapon files `OldSpeed`
All weapon pages | Stamina can never be higher than Dexterity | SRV/Mobiles/Mobile.cs:2166 (`StamMax => Dex`); PlayerMobile.cs:582 adds only AOS BonusStam
All weapon pages | Damage = random(min,max) x (1 + (Tactics - 50)/100), then x (1 + Str/500 + Anatomy/500 [+ Lumberjacking/500 for axes] [+0.2 exceptional]) and durability scale; Core.UOTD (the extra 10% at 100) is false | BaseWeapon.cs:2671-2744 (lines 2693, 2698, 2705-2710, 2716-2726, 2728-2732, 2743)
All weapon pages | Damage is halved when the defender is a player or the attacker is not a player | BaseWeapon.cs:2758-2774 (2768-2770)
All weapon pages | Armor and virtual armor take points off, a hit never does less than 1 | BaseWeapon.cs:1722-1771 (AbsorbDamage), 1952-1957; UOC/Items/Armor/BaseArmor.cs:727-780
All weapon pages | About 1 hit in 25 (that did damage) wears the weapon down by 1; a worn weapon hits for 50% + 50% x hp/maxhp | BaseWeapon.cs:2088, 2148-2177 (`Utility.Random(25) == 0`), 2746-2756
All weapon pages | "Repair is in the Blacksmith menu" | SC/WelcomeGuide.GettingStarted.cs:247 (Crafting page: "Smelt and Repair are in the Blacksmith menu")
All weapon pages | You cannot equip a weapon if Strength is below its requirement ("You are not strong enough to equip that") | BaseWeapon.cs:1069-1105 (1092-1096); weapons' `OldStrengthReq` (lines in the per-weapon claims)
All weapon pages | A one-handed weapon and a shield can be worn together; a two-handed weapon and a shield conflict (same layer) | BaseWeapon.cs:1042-1066; Shields use Layer.TwoHanded (BaseArmor.cs:504)
All weapon pages | Training needs the skill set to Up | UOC/Skills/SkillCheck.cs:295 (`skill.Lock == SkillLock.Up`); SC/WelcomeGuide.GettingStarted.cs:130-173 (Skill locks 101)
All weapon pages | Specials: Concussion Blow (axes, polearms), Crushing Blow (two-handed maces), Paralyzing Blow (two-handed spears) are removed; no weapon proc; Wrestling Stun and Disarm only answer "disabled" | ShardContent/docs/UOR-ERA-AUDIT.md:7-29; shard-rules.json:13-17; SC/ShardRulesConfiguration.cs:84; UOC/Items/Weapons/Fists.cs:61-93; I read BaseAxe.cs, BasePoleArm.cs, BaseBashing.cs, BaseStaff.cs, BaseSpear.cs, BaseSword.cs, BaseKnife.cs: no proc in their OnHit
All weapon pages | Insta-hit is on: not stated on the pages (only the equip delay) | ModernUO/Distribution/Configuration/modernuo-era-gates.json:10 (not used in the text)
All weapon pages | Training dummy: weapon skill check -25..25; refuses ranged weapons, out-of-range (weapon.MaxRange), a swinging dummy, a mounted player and base skill >= 25; swings for 0.25 + 2.75 seconds | UOC/Items/Addons/TrainingDummies.cs:23-24, 60-98, 114
All weapon pages | Dummies exist in Britain (also 4 more at 1524..1528,1431..1436 and others); I say "in Britain" | Alpha2b/Decoration/Britannia__britain.cfg:1465-1475
All weapon pages | Rats wander Britain's streets (15 and 5 per spawner) | SPAWN/TownsLife.json: spawners at [1550,1658,26] and [1340,1790,15] list Rat; world-generation.json spawnerFiles includes TownsLife.json
All weapon pages | Monster stats: Rat Wrestling 4, 6 hp, damage 1-2 | UOC/Mobiles/Animals/Town Critters/Rat.cs:18,21,30
All weapon pages | Headless One Wrestling 25.1-40, 16-30 hp | Monsters/Humanoid/Melee/HeadlessOne.cs:20,31
All weapon pages | Zombie Wrestling 35.1-50, 28-42 hp | Monsters/Humanoid/Melee/Zombie.cs:19,31
All weapon pages | Skeleton Wrestling 45.1-55, 34-48 hp | Monsters/Humanoid/Melee/Skeleton.cs:19,33
All weapon pages | Orc 50.1-70, Lizardman 50.1-70, Ratman 50.1-75, all 58-72 hp | Orc.cs:20,34; Lizardman.cs:20,33; Ratman.cs:20,34
All weapon pages | Ettin Wrestling 50.1-60, 82-99 hp; Troll 50.1-70, 106-123; Ogre 70.1-80, 100-117 | Ettin.cs:18,32; Troll.cs:18,32; Ogre.cs:19,34
All weapon pages | "None of those stops teaching before 100": smallest threshold 2 x 25.1 + 50 = 100.2 (Headless One) | arithmetic from the hit-chance formula above
All weapon pages | Rat stops teaching at 2 x 4 + 50 = 58 | arithmetic
All weapon pages | Snakes, giant spiders and scorpions poison with their bite; Wraith and Spectre are mages (Poison spell, always Lesser per Poison-Relief-Plan.md) | UOC/Mobiles/Animals/Reptiles/Snake.cs:48; Monsters/Arachnid/Melee/GiantSpider.cs:52; Monsters/Reptile/Melee/Scorpion.cs:57; Monsters/Humanoid/Magic/Wraith.cs:9, Spectre.cs:9; ShardContent/docs/Poison-Relief-Plan.md "What the code said"
All weapon pages | A Britain graveyard with Spectre/Wraith/Skeleton/Zombie exists at [1369,1475,10]; the final text only names the monsters, not the graveyard | SPAWN/Graveyards.json
All weapon pages | Teachers: a trainer teaches a skill it has 60.0 or more in, up to a third of its own skill (not over 42.0, not under 20.0), 1 gold per 0.1 | UOC/Mobiles/BaseCreature.cs:2849-2870, 4736-4775; SC/WelcomeGuide.GettingStarted.cs:176-194
All weapon pages | Vendors and guildmasters are spawned in Greater Britain only | ShardContent/data/world-generation/alpha2b/world-generation.json:98-101 (`britainOnlySpawnerFiles`: Vendors.json); SPAWN/Vendors.json locations x 1296-1650, y 1525-1826
All weapon pages | Faint Memories: 5.0 points, unlocks 24 h after creation, comes back 0.2 per use in a skill set to Up between 10.0 and 80.0 | shard-rules.json:20-28, 206; ShardContent/docs/Skill-Bank-Faint-Memories.md "What it does"
All weapon pages | Novice combat assist (flag NoviceCombat): second roll after a miss, chance x (1 + 0.66 x (1 - skill/100)) capped at 1 (so x1.66 at skill 0, x1.33 at skill 50, x1 at 100); Tactics counts as at least 30 for damage; stamina counts as at least 60 for the swing delay; ordinary players only, any target; gain odds unchanged because the lift is a second roll after the stock skill check | SC/NoviceCombatService.cs:33-80; BaseWeapon.cs:1416-1419, 2693, 1557; shard-rules.json:131-134, 218; ShardContent/docs/Novice-Combat-Assist-Evidence.md "Decisions"
All weapon pages | Attacking players follows the Fighting other players page; Hot Zones are Fire Island, Buccaneer's Den island and Hythloth; Knocked Out text | SC/WelcomeGuide.cs:203-300 (Fighting and Hot Zones topics); shard-rules.json:192, 195, 196
All weapon pages | Starter gear is gated on Alpha3StarterCombatGear (on): bandages topped to 50 for melee and archer packages, arrows to 100 when Archery is selected, archers get a leather chest and leather leggings, a Parry template gets a wooden shield (only added by the shard when stock gave none; stock Parry already equips one) | SC/StarterCombatIssuance.cs:38, 64-67, 91-111; UOC/Engines/Character Creation/CharacterCreation.cs:965-970, 996-1002, 1252-1262, 1290-1296; shard-rules.json:204
All weapon pages | Human templates get Katana (Swords), Club (Macing), Kryss (Fencing), Bow (Archery); the cosmetic Elf is mechanically a Human | CharacterCreation.cs:911-944; SC/CosmeticElfCreationService.cs:10-14
All weapon pages | Ready-made templates: Swordsman, Fencer, Mace Fighter have weapon 50, Parrying 35, Anatomy 35; Archer and Ranger Archery 50; no template has Tactics or Wrestling; only Tailor has Healing (20) | ShardContent/data/professions/Prof.txt:89, 121, 169-171, 185-187, 201-203, 251 (grep: 0 matches for Tactics, Wrestling)
Weapon, shield, arrow and bandage prices | The prices are the list prices in the SBInfo files ("about" N gold). The only modifier is a faction town's tax, which starts at 0 (`Faction.cs:682,744`); with no tax `PriceScalar` is 100 and `Price` returns the list price | UOC/Mobiles/Vendors/BaseVendor.cs:1384-1392; GenericBuy.cs:51-82; UOC/Engines/Factions/Core/Faction.cs:682,744

## Wrestling

Wrestling | Fists: 1-8 damage, speed 30, strength 0, Wrestling skill, Layer none | UOC/Items/Weapons/Fists.cs:28-31, 36
Wrestling | Fists swing 2.5 s at stamina 100 | arithmetic 15000/(200 x 30)
Wrestling | Katana 5-26, speed 58, 1.3 s | UOC/Items/Weapons/Swords/Katana.cs:25-28
Wrestling | Unarmed attack uses the Wrestling skill (weapon.Skill = DefSkill Wrestling) | Fists.cs:36; BaseWeapon.cs:1284
Wrestling | Stun and Disarm: requests clear the state and send "Wrestling Stun/Disarm is disabled on this shard." | Fists.cs:81-93; UOR-ERA-AUDIT.md:41-48 (buttons may still show)
Wrestling | Mage Guildmaster teaches Wrestling (skill 60.0-83.0, so about 20.0-27.7) | UOC/Mobiles/Vendors/NPC/Guildmasters/MageGuildmaster.cs:16; SPAWN/Vendors.json: MageGuildmaster at [1485,1550,30] and [1590,1654,10]
Wrestling | Healer in Britain sells bandages for 5 gold | UOC/Mobiles/Vendors/UOC/Mobiles/Vendors/SBInfo/SBHealer.cs:16; UOC/Mobiles/Healers/Healer.cs:25-26, 40 (`IsActiveVendor`, `SBInfos.Add(new SBHealer())`); SPAWN/Vendors.json [1471,1611,20]
Wrestling | "Wrestling defends you only while your hands are empty" | BaseWeapon.cs:1281-1287 (defender's weapon skill)

## Swords (Swordsmanship)

Swords | Swords, cutting knives, axes and polearms use Swords; the Dagger is Fencing, spears and forks are Fencing, War Axe is Macing | UOC/Items/Weapons/Swords/BaseSword.cs:13; Knives/BaseKnife.cs:16; Axes/BaseAxe.cs:32; PoleArms/BasePoleArm.cs:27; Knives/Dagger.cs:33; SpearsAndForks/BaseSpear.cs:15; Axes/WarAxe.cs:37; Staves/BaseStaff.cs:15
Swords | Katana 5-26 speed 58 Str 10, 33 gold | Swords/Katana.cs:25-28; SBBlacksmith.cs:65
Swords | Cutlass 6-28/45/Str 10, 24 gold | Swords/Cutlass.cs:25-28; SBBlacksmith.cs:61
Swords | Scimitar 4-30/43/Str 10, 36 gold | Swords/Scimitar.cs:25-28; SBBlacksmith.cs:76
Swords | Broadsword 5-29/45/Str 25, 35 gold | Swords/Broadsword.cs:25-28; SBBlacksmith.cs:67
Swords | Longsword 5-33/35/Str 25, 55 gold | Swords/Longsword.cs:25-28; SBBlacksmith.cs:68
Swords | Viking Sword 6-34/30/Str 40, 55 gold | Swords/VikingSword.cs:25-28; SBBlacksmith.cs:70
Swords | Axe 6-33/37/Str 35, 40 gold | Axes/Axe.cs:25-28; SBBlacksmith.cs:72
Swords | Battle Axe 6-38/30/Str 40, 26 gold, two-handed in code | Axes/BattleAxe.cs:10, 22-25; SBBlacksmith.cs:55
Swords | Halberd 5-49/25/Str 45, 42 gold | PoleArms/Halberd.cs:25-28; SBBlacksmith.cs:63
Swords | Swing seconds at stamina 100: 1.29, 1.67, 1.74, 1.67, 2.14, 2.5, 2.03, 2.5, 3.0 | arithmetic 75/speed
Swords | Axes add 1% per 5 Lumberjacking (UOR), a weapon of exceptional quality +20% | BaseWeapon.cs:2716-2726, 2728-2732; WeaponEnums.cs:3-8
Swords | New swordsman example: Katana avg 15.5 x 0.5 (Tactics 0) x (1 + 0.10 + 0.07) = 9.07; Grandmaster 15.5 x 1.5 x 1.4 = 32.55 | arithmetic
Swords | Teachers: Blacksmith Swords 60-83 (20.0-27.7); Healer Swords 80-100 (26.7-33.3); Warrior Guildmaster Swords 90-100 (30.0-33.3) | UOC/Mobiles/Vendors/NPC/Blacksmith.cs:21; UOC/Mobiles/Healers/Healer.cs:20, 28-37 (CheckTeach allows Swords); Guildmasters/WarriorGuildmaster.cs:15; Vendors.json (Blacksmith [1418,1547,30], [1349,1778,15]; WarriorGuildmaster [1341,1733,20])
Swords | Blacksmiths stock every weapon on the list | SBBlacksmith.cs:55-104 (War Fork is the only one of the three fighting pages' weapons it lacks; it is in the Fencing page); Weaponsmith: swords/axes only inside `case 0` | SBWeaponSmith.cs:39-95
Swords | Axes and polearms are also harvesting tools | not stated on the page

## Macing (Mace Fighting)

Macing | Club 8-24/40/Str 10, 16 gold | Maces/Club.cs:25-28; SBBlacksmith.cs:94
Macing | Mace 8-32/30/Str 20, 28 gold | Maces/Mace.cs:25-28; SBBlacksmith.cs:96
Macing | War Mace 10-30/32/Str 30, 31 gold | Maces/WarMace.cs:25-28; SBBlacksmith.cs:104
Macing | Maul 10-30/30/Str 20, 21 gold | Maces/Maul.cs:25-28; SBBlacksmith.cs:97
Macing | Hammer Pick 6-33/30/Str 35, 26 gold, one-handed in code | Maces/HammerPick.cs:10, 22-25; SBBlacksmith.cs:64
Macing | War Axe 9-27/40/Str 35, 29 gold, uses Macing | Axes/WarAxe.cs:26-29, 37; SBBlacksmith.cs:79
Macing | War Hammer 8-36/31/Str 40, 25 gold, two-handed in code | Maces/WarHammer.cs:10, 22-25; SBBlacksmith.cs:103
Macing | Quarter Staff 8-28/48/Str 30, 19 gold | Staves/QuarterStaff.cs:22-25; SBBlacksmith.cs:98
Macing | Black Staff 8-33/35/Str 35, 22 gold | Staves/BlackStaff.cs:25-28; SBBlacksmith.cs:93
Macing | Gnarled Staff 10-30/33/Str 20, 16 gold | Staves/GnarledStaff.cs:22-25; SBBlacksmith.cs:95
Macing | Maces (BaseBashing) and staves (BaseStaff) drain 3-5 stamina from the target on each hit (`Utility.Random(3, 3)`); the War Axe is a BaseAxe and does not | Maces/BaseBashing.cs:18-23; Staves/BaseStaff.cs:19-24; Axes/BaseAxe.cs (no OnHit)
Macing | A drained target swings slower because the delay uses current stamina | BaseWeapon.cs:1557
Macing | Teachers: Blacksmith Macing 61-93 (20.3-31.0); Warrior Guildmaster Macing 60-83 (20.0-27.7) | Blacksmith.cs:20; WarriorGuildmaster.cs:16
Macing | Blacksmith stock; Weaponsmith always carries Club, Mace, Maul, War Hammer, War Mace and the staves (before the random case) but not Hammer Pick or War Axe | SBWeaponSmith.cs:14-37 vs 39-95
Macing | Starter: Mace Fighter template gets a Club and a Wooden Shield | CharacterCreation.cs:1183-1186 (Macing), 1252-1262 (Parry); Prof.txt:169-171

## Fencing

Fencing | Dagger 3-15/55/Str 1, 21 gold | Knives/Dagger.cs:25-28, 33; SBBlacksmith.cs:62
Fencing | Kryss 3-28/53/Str 10, 32 gold | Swords/Kryss.cs:25-28, 36; SBBlacksmith.cs:66
Fencing | War Fork 4-32/45/Str 35, 32 gold, one-handed per tiledata; sold by the Weaponsmith, not the Blacksmith | SpearsAndForks/WarFork.cs:25-28; SBWeaponSmith.cs:37 (outside the random case); grep of SBBlacksmith.cs: no WarFork
Fencing | Short Spear 4-32/50/Str 15, 23 gold; Spear 2-36/46/Str 30, 31 gold; Pitchfork 4-16/45/Str 15, 19 gold; all two-handed per tiledata | SpearsAndForks/ShortSpear.cs:25-28; Spear.cs:25-28; Pitchfork.cs:25-28; SBBlacksmith.cs:101,102,75
Fencing | Teachers: Blacksmith Fencing 60-83; Warrior Guildmaster Fencing 60-83 (20.0-27.7) | Blacksmith.cs:19; WarriorGuildmaster.cs:17
Fencing | Starter: Fencer template gets a Kryss | CharacterCreation.cs:1114-1117; Prof.txt:185-187

## Archery

Archery | Bow 9-41/speed 20/Str 20/range 10 (35 at the Blacksmith, 40 at the Bowyer) | Ranged/Bow.cs:13, 31-36; SBBlacksmith.cs:57; SBInfo/Weapons/SBRangedWeapon.cs:22
Archery | Crossbow 8-43/18/Str 30/range 8 (46 at the Blacksmith, 55 at the Bowyer); Heavy Crossbow 11-56/10/Str 40/range 8 (55 and 55) | Ranged/Crossbow.cs:31-36; HeavyCrossbow.cs:31-36; SBBlacksmith.cs:59-60; SBRangedWeapon.cs:13-14
Archery | Seconds at stamina 100: Bow 3.75, Crossbow 4.17, Heavy Crossbow 7.5; Dexterity 33 archer 5.64 s, with a stamina floor of 60 4.69 s | arithmetic; Novice-Combat-Assist-Evidence.md "Verification" (5.639 s to 4.688 s)
Archery | Stationary delay: 1000 ms at Dex <= 25 to 500 ms at Dex >= 100, rounded to 50 ms; Dex 33 gives 950 ms; shooting is refused (retry in 0.25 s) until the wait has passed | Ranged/BaseRanged.cs:46-58, 65, 123-125
Archery | Needs line of sight and range | SRV/Mobiles/Mobile.cs:801-833 (`InRange(combatant, weapon.MaxRange)`, `InLOS`)
Archery | One arrow (Bow) or bolt (Crossbow) per shot, taken from the pack | BaseRanged.cs:187-216; Bow.cs:27-28 (AmmoType Arrow)
Archery | A miss drops the arrow near the target 40% of the time (not Core.SE); a hit on a monster or animal puts an arrow in its pack 40% of the time | BaseRanged.cs:128-134, 159-185
Archery | A new archer's example: Bow avg 25 x 0.5 x 1.10 = 13.75 (about 14) | arithmetic (Str 50, Anatomy 0, Tactics 0)
Archery | Butte: skill check -25..25, 2 s between shots, stand 5 or 6 tiles in a line in front, ammunition consumed, double-click next to it to gather | UOC/Items/Addons/ArcheryButteAddon.cs:11, 18-19, 61-75 (Gather), 101-146, 151, 185
Archery | Two buttes at [1468,1579,20] and [1473,1576,20] and the Bowyer's spawner at [1470,1578,20] | Alpha2b/Decoration/Britannia__britain.cfg:1431-1436; Vendors.json
Archery | Arrows 2 gold at the Bowyer and the Provisioner; bolts 3 at the Bowyer, 5 at the Provisioner | SBRangedWeapon.cs:19, 21; SBProvisioner.cs:27-28; UOC/Mobiles/Vendors/NPC/Bowyer.cs:36-37 (`SBBowyer`, `SBRangedWeapon`); Provisioner.cs:22; Vendors.json Provisioner [1602,1712,20], [1469,1668,0]
Archery | Arrows and bolts can be crafted with Bowcraft | UOC/Engines/Craft/DefBowFletching.cs:96-104
Archery | Teachers: Bowyer Archery 80-100 (26.7-33.3); Bard Guildmaster Archery 80-100 | NPC/Bowyer.cs:17; Guildmasters/BardGuildmaster.cs:11; Vendors.json Bowyer [1470,1578,20], BardGuildmaster in the Bard spawner
Archery | Shield and bows: bows are two-handed | Bow.cs:13; Crossbow.cs:13; HeavyCrossbow.cs:13
Archery | Starter: archers get the 100 arrows, leather chest and legs, 50 bandages | StarterCombatIssuance.cs:64-67, 96-100, 110

## Parry (Parrying)

Parry | Pre-AOS shield rule is in `BaseShield.OnHit`: chance = (Parry - 2 x armor rating) / 100, floor 0.01; block removes min(damage, AR/2) or AR against Archery; 25% x (0 or 1) durability loss | UOC/Items/Shields/BaseShield.cs:31-76 (55-72)
Parry | Shield armor rating = base x Parry / 200 + 1 (and durability-scaled) | BaseShield.cs:15-29; BaseArmor.cs:289-328, 986-996
Parry | `BaseWeapon.AbsorbDamage` calls the shield only for a landed hit when a BaseShield is on Layer.TwoHanded; `CheckParry` is the AOS path and is not used | BaseWeapon.cs:1722-1735, 1570-1653 (AOS only)
Parry | `damage < 1` becomes 1 afterwards | BaseWeapon.cs:1954-1957
Parry | Shield base ratings: Buckler 7, Wooden Shield 8, Bronze 10, Metal 11, Wooden Kite 12, Metal Kite 16, Heater 23 | Shields/Buckler.cs:26; WoodenShield.cs:26; BronzeShield.cs:26; MetalShield.cs:26; WoodenKiteShield.cs:26; MetalKiteShield.cs:26; HeaterShield.cs:26
Parry | Table at Parry 50 / 100: Buckler 44.5% & 1 / 91% & 2; Wooden 44% & 1 / 90% & 2; Metal Kite 40% & 2 / 82% & 4; Heater 36.5% & 3 / 75% & 6 (arrows: 2/4, 3/5, 5/9, 6/12) | arithmetic from the two formulas (scratch script, all four checked)
Parry | Shields have no Strength requirement pre-AOS (`OldStrReq` is 0 and the shields do not override it) | BaseArmor.cs:184, 393-396; Shields/*.cs (only `AosStrReq` set); BaseArmor.CanEquip 1099-1113
Parry | Shield wear: 25% x (Random(2)) per block = about 1 block in 8 | BaseShield.cs:69-72
Parry | Wooden Shield 30, Buckler 50, Bronze 66, Wooden Kite 70, Metal 121, Metal Kite 123, Heater 231 gold at the Blacksmith | SBBlacksmith.cs:19-26
Parry | The Parry skill check is `owner.CheckSkill(Parry, chance)` on each hit with a shield, so chance < 1 always: never "no challenge" | BaseShield.cs:63; arithmetic ((100 - 2 x AR)/100 < 1)
Parry | Parry does not change hit chance (defender skill = weapon skill) | BaseWeapon.cs:1281-1287
Parry | Teachers: Blacksmith Parry 61-93 (20.3-31.0); Warrior Guildmaster Parry 85-100 (28.3-33.3) | Blacksmith.cs:23; WarriorGuildmaster.cs:12
Parry | Starter wooden shield (Parry skill) | CharacterCreation.cs:1252-1262; StarterCombatIssuance.cs:102-106
Parry | Spells and poison are not weapon hits | spells/poison do not call `AbsorbDamage` (Poison.cs:139 uses AOS.Damage -> Mobile.Damage; AOS.cs:63-66)

## Tactics

Tactics | Damage x (1 + (Tactics - 50)/100): half at 0, unchanged at 50, 1.5 at 100 | BaseWeapon.cs:2693
Tactics | Checked on every landed hit: `CheckSkill(Tactics, 0, Cap)` inside `ScaleDamageOld(checkSkills: true)`, which is called from `ComputeDamage` only on a hit | BaseWeapon.cs:2674-2680, 2758-2765
Tactics | The Tactics check chance is skill/Cap, independent of the hit chance (so a certain hit still trains it) | BaseWeapon.cs:2676; SkillCheck.cs:61-80
Tactics | Hits by any weapon, ranged and unarmed included, pass through the same function | BaseWeapon.cs:2758-2765 (BaseRanged inherits)
Tactics | Monsters' Tactics shapes their blows in the same function | BaseWeapon.cs:2693 (`attacker.Skills.Tactics`)
Tactics | 2.1 times at Tactics 100, Str 100, Anatomy 100: 1.5 x 1.4 | arithmetic
Tactics | New fighter: 0.5 x (1 + 0.10 + 0.07) = 0.585 (Str 50, Anatomy 35) | arithmetic
Tactics | No stat bonus (StrScale = DexScale = IntScale = 0) | ModernUO/Distribution/Data/skills.json entry SkillID 27; SRV/Skills.cs:253-290
Tactics | Teachers: Blacksmith Tactics 60-83 (20.0-27.7); Warrior Guildmaster Tactics 85-100 (28.3-33.3) | Blacksmith.cs:22; WarriorGuildmaster.cs:14
Tactics | Novice assist: Tactics counts as at least 30 for damage, the skill itself is untouched, so the real skill must pass 30 to matter | NoviceCombatService.cs:74-76; WeaponEvents.cs:15-18; BaseWeapon.cs:2693; Novice-Combat-Assist-Plan.md "Tactics floor"
Tactics | Against a player damage is halved after all modifiers | BaseWeapon.cs:2765-2770
Tactics | No ready-made template includes Tactics | Prof.txt (0 matches); an Advanced character can still pick it (CharacterCreation.cs:75, 1290)

## Anatomy

Anatomy | +1% damage per 5 points (20% at 100), no extra at 100 | BaseWeapon.cs:2704-2710 (`Core.UOTD` false)
Anatomy | Bandage heal: min = A/5 + H/5 + 3, max = A/5 + H/2 + 10 (non-AOS) | UOC/Items/Skill Items/Misc/Bandage.cs:392-393
Anatomy | Cure needs Healing and Anatomy >= 60, resurrection both >= 80 | Bandage.cs:322, 240
Anatomy | At Healing 100 a bandage heals 23-60 with Anatomy 0 and 43-80 with Anatomy 100 | arithmetic from Bandage.cs:392-393
Anatomy | Skill use: "Whom shall I examine?", target range 8, use delay 1 s (UOR) | UOC/Skills/Anatomy.cs:14-25
Anatomy | Not on yourself; invulnerable BaseVendor refused ("That can not be inspected"); the Town Crier gets a joke | Anatomy.cs:31-56
Anatomy | Margin of error max(0, 25 - Anatomy/4) on Str, Dex and stamina percent; stamina reading only if Anatomy.Base >= 65 | Anatomy.cs:59-65, 106-114
Anatomy | Check is `CheckTargetSkill(Anatomy, target, 0, 100)`: chance skill/100, no gain at 100 | Anatomy.cs:97; SkillCheck.cs:205-222
Anatomy | Passive checks: every landed hit (0..Cap) and every bandage completion (0..120) | BaseWeapon.cs:2679; Bandage.cs:444
Anatomy | The skills window has a "use" button per skill | ClassicUO/src/ClassicUO.Client/Game/UI/Gumps/StandardSkillsGump.cs:845-848 (buttonID 0, "use")
Anatomy | Town rats, cats, dogs and birds | SPAWN/TownsLife.json [1550,1658,26] (Bird, Cat, Dog, Rat); [1340,1790,15]
Anatomy | No stat bonus (all scales 0) | skills.json SkillID 1; SRV/Skills.cs:253-290
Anatomy | Teachers: Healer Guildmaster Anatomy 85-100 (28.3-33.3); wandering healers Anatomy 75-97.5 (25.0-32.5); the town Healer does not teach Anatomy (its CheckTeach allows only Forensics, Healing, SpiritSpeak, Swords) | Guildmasters/HealerGuildmaster.cs:12; UOC/Mobiles/Healers/WanderingHealer.cs:24-34; UOC/Mobiles/Healers/BaseHealer.cs:53; Healers/Healer.cs:28-37; SPAWN/WildLife.json (179 spawners list WanderingHealer)

## Healing

Healing | Bandage range is 1 tile (non-AOS) for the double-click and for the target; the healer must stay within 1 tile or "You did not stay close enough" | Bandage.cs:16, 41-48, 84, 215-219
Healing | Self wait 9.4 + 0.6 x (120 - Dex)/10 s; others 5 s (Dex < 40), 4 s (40 to 99), 3 s (100+), +5 s if the patient is dead | Bandage.cs:492-531
Healing | Heal chance (H + 10)/100 minus 0.02 per slip; amount per formula above, minus 4 per slip, minimum 1; heal sound/gain happen either way | Bandage.cs:375-425 (377, 392-396, 409-416)
Healing | Table: H0/A0 10% for 3-10; 50/50 60% for 23-45; 100/100 always for 43-80 | arithmetic
Healing | A slip happens on every damage event > 0 while the bandage runs (pre-AOS threshold 0): "Your fingers slip!", Slips++ | UOC/Mobiles/PlayerMobile.cs:2424-2449; Bandage.cs:155-161
Healing | Poison ticks are damage (AOS.Damage -> Mobile.Damage -> OnDamage), so they slip the bandage | UOC/Misc/Poison.cs:139; UOC/Misc/AOS.cs:63-66; SRV/Mobiles/Mobile.cs:6119
Healing | Poisoned patient: only a cure attempt, needs H >= 60 and A >= 60, chance (H - 30)/50 - 0.1 x poison level - 0.02 x slips; fail "You have failed to cure your target!", bandage used | Bandage.cs:315-340
Healing | Poison levels Lesser 0, Regular 1, Greater 2, Deadly 3, Lethal 4 | UOC/Misc/PoisonKinds.cs:80-84
Healing | Cure table: at H 80 Lesser = 1.0, at H 100 Lethal = 1.0 | arithmetic
Healing | Resurrection: needs H >= 80 and A >= 80, chance (H - 68)/50 - 0.02 x slips, patient gets the ResurrectGump, +5 s wait | Bandage.cs:221-314 (239-240, 312), 492
Healing | Coming back costs no stats on this shard | SC/PostUorSystemGates.cs:21 (`ResurrectGump.StatLossEnabled = false`); SC/WelcomeGuide.GettingStarted.cs:345-348
Healing | Gain checks: Anatomy and Healing `CheckSkill(skill, 0, 120)` at completion, only when `checkSkills` (wound branch always; cure needs 60/60; resurrect 80/80); not when the patient reached full health | Bandage.cs:366-373, 442-446
Healing | A second bandage cancels the first; the first is already consumed | Bandage.cs:533-540, 98-101
Healing | A bandage on a patient at full health who is not poisoned is refused and not consumed | Bandage.cs:471-475 (BeginHeal returns null), 98-101
Healing | Bandages on tamed animals use Veterinary/Animal Lore | Bandage.cs:175-193
Healing | Bandaging a Criminal or Murderer target is a criminal act | SRV/Mobiles/Mobile.cs:8407-8417, 8422-8441; UOC/Misc/Notoriety.cs:443-453; Bandage.cs:484-486
Healing | A player with Criminal Intent on is `CanBeAttacked`, not Criminal, so helping them is not a criminal act | SC/PvpIntentService.cs:250-252, 338-353
Healing | A Knocked Out player cannot be healed, cannot be targeted beneficially and cannot act | SC/KnockedOutService.cs:42, 44, 620-650; UOC/Items/Skill Items/Misc/Bandage.cs:456
Healing | The Healer sells bandages 5 gold (stock 20); only the Healer sells them in Britain (Fortune Teller, Ranger, Variety Dealer, Veterinarian also list bandages but are not spawned) | SBHealer.cs:16; SBFortuneTeller.cs:16; SBRanger.cs:20; SBVarietyDealer.cs:16; SBVeterinarian.cs:16; SPAWN/Vendors.json (names present)
Healing | Cloth cut with scissors becomes bandages one for one; a bolt of cloth cuts into 50 cloth; Tailors sell cloth 2, scissors 11, bolt 100 | UOC/Items/Resources/Tailor/Cloth.cs:33-42; BoltOfCloth.cs:34-44; SRV/Items/Item.cs:4371-4400; SBTailor.cs:17, 50, 52; Vendors.json (3 Tailors)
Healing | Teachers: Healer Healing 75-97.5 (25.0-32.5), Healer Guildmaster 90-100 (30.0-33.3), wandering healers 75-97.5 | BaseHealer.cs:55; Healer.cs:28-37; HealerGuildmaster.cs:13; WanderingHealer.cs:24-34
Healing | Healing stat scales sum 0.2 (a stat bonus while the skill is low) | skills.json SkillID 17; SRV/Skills.cs:253-290, 395-418
Healing | Poison relief: 5 Lesser Cure potions at creation (flag on), hint once when poisoned and Healing or Anatomy < 60, grace window of 30 s for poison level 0 from a non-player source | SC/PoisonReliefService.cs:23-31, 73-86, 108-128, 168-200; shard-rules.json:136-140, 219
Healing | Lesser Cure potion 15 gold at an alchemist; alchemists are in Britain | SBAlchemist.cs:22; Vendors.json (Alchemist x3)
Healing | Heal potions do not work on a poisoned person | UOC/Items/Skill Items/Magical/Potions/Heal Potions/BaseHealPotion.cs:39-43
Healing | The Healing skill is trained on people only (animals use Veterinary) | Bandage.cs:175-183

## Gated paragraphs and flags (exact `DeferredFeatureFlags` names)

NoviceCombat (Wrestling, Swords, Macing, Fencing, Archery, Tactics) | on in shard-rules.json:218 | text gated
FaintMemories (all 9) | on, shard-rules.json:206 | text gated
PoisonRelief (Healing) | on, shard-rules.json:219 | text gated
Alpha3StarterCombatGear (Swords, Macing, Fencing, Archery, Parry, Healing) | on, shard-rules.json:204 | text gated
SafeWorld, HotZones, KnockedOut (the five weapon pages; SafeWorld also Parry and Healing; KnockedOut also Healing) | on, shard-rules.json:192, 195-196 | text gated
Nothing about CoolZones, HousingGeography, Expeditions, Pilgrimage, RoadSpeed or RetentionContent, anti-macro, Mastery rules beyond the generated block, or any post-UOR item.

## Anything the coordinator must decide

1. The generator `stats` wording for Tactics and Anatomy (first OPEN above).
2. Whether the Welcome guide's Training page should list guildmasters and wandering healers (second-to-last OPEN above), since my pages name them.
3. Whether a Weaponsmith's partial stock (random 1 in 3 of the sword and bow list) is intended.
4. The monster "sensible order" is my advice; the owner may want it changed or replaced by named hunting spots.
