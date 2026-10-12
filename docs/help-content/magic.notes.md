# Magic skill pages: claim sources and open items

Pages (5) in `magic.skills.json`: Magery, EvalInt, Meditation, MagicResist, SpiritSpeak. Each carries the `stats` and `gain` blocks.
Own-text sizes (characters, all paragraphs): Magery 15,829 (14,714 ungated; the tail from the heading "The spells" to the end is 9,745), EvalInt 2,769, Meditation 3,235, MagicResist 3,645 (3,466 ungated), SpiritSpeak 1,723.
Gated paragraphs: Magery uses `Alpha3StarterCombatGear`, `PetRestrictions`, `HotZoneTravelWarning`, `SafeWorld`, `HotZones`, `KnockedOut`; MagicResist uses `SafeWorld`. No other flag is named.
Paths are relative to the workspace root. Abbreviations: UOC = `ModernUO/Projects/UOContent`, SRV = `ModernUO/Projects/Server`, SC = `ShardContent`, CFG = `ModernUO/Distribution/Configuration`. Client text (CL) was read from `UOData/Cliloc.enu` with `SC/tools/world-decorating/cliloc.py`; the number is given.
Era: Expansion UOR (`CFG/expansion.json:8`, `SRV/Main.cs:324-332`, enum order `SRV/ExpansionInfo.cs:24-38`): Core.UOR and Core.T2A true; Core.UOTD, LBR, AOS and later false. Every path below is the non-AOS branch. The stats text is no longer written by hand: the page does not describe stat leaning (the Intelligence bonus to the Magery number was cut for that reason).

## Common to all five

- All | The skills window has a use button beside a usable skill; clicking it uses the skill | `ClassicUO/src/ClassicUO.Client/Game/UI/Gumps/StandardSkillsGump.cs:845-849`, `SkillGumpAdvanced.cs:381-386`
- All | A skill can be used only while alive and with no spell in progress; the callback's return value is the wait before any skill can be used again | `SRV/Skills.cs:773-805`
- All | Chance of a min/max check = (skill - min) / (max - min); below min it fails with no gain, at or above max it succeeds with no gain | `UOC/Skills/SkillCheck.cs:61-75, 205-222`
- All | Below 10.0 skill every check gains | `UOC/Skills/SkillCheck.cs:130-141`
- All | Anti-macro is disabled (not mentioned in the text) | `CFG/antimacro.json:4`
- Trainers | An NPC teaches up to a third of its own skill (at most 42.0, at least 20.0 needed), 1 gold per 0.1 point; any vendor can teach | `UOC/Mobiles/BaseCreature.cs:4754-4762, 4880-4890`, `UOC/Mobiles/Vendors/BaseVendor.cs:114`, `SC/src/BritanniaRenaissance.Content/WelcomeGuide.GettingStarted.cs:186-212`
- Trainers | The Welcome guide's Training page lists Mage (Magery, Evaluating Intelligence, Meditation, Resisting Spells) and Healer (Spirit Speak) | `WelcomeGuide.GettingStarted.cs:200-201`
- Trainers | Mage NPC: Magery 64-100 (21.3 to 33.3), Evaluating Intelligence 65-88, Meditation 60-83, Resisting Spells 65-88 | `UOC/Mobiles/Vendors/NPC/Mage.cs:15-19`
- Trainers | Mage guildmaster: Magery 90-100, Evaluating Intelligence 85-100, Resisting Spells 64-100, Meditation 85-100 (28.3 to 33.3) | `UOC/Mobiles/Vendors/NPC/Guildmasters/MageGuildmaster.cs:12-17`
- Trainers | Scribe: Evaluating Intelligence 60-83 (20.0 to 27.7) | `UOC/Mobiles/Vendors/NPC/Scribe.cs:19`
- Trainers | Healer: Spirit Speak 80-100 (26.7 to 33.3), teaches only Forensics, Healing, Spirit Speak, Swordsmanship; healer guildmaster Spirit Speak 65-88 (21.7 to 29.3) | `UOC/Mobiles/Healers/Healer.cs:19, 35`, `UOC/Mobiles/Vendors/NPC/Guildmasters/HealerGuildmaster.cs:16`
- Vendors | Vendors exist only in Britain; the generated vendor data has 3 Mage, 2 Mage guildmaster, 3 Alchemist, 2 Scribe, 1 Healer, 1 Healer guildmaster spawn entries | `SC/data/world-generation/alpha2b/world-generation.json:98-101`, `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json`
- Links | "Training", "Dying", "Fighting other players" are Welcome guide topics | `WelcomeGuide.GettingStarted.cs:178-212, 329-367`, `WelcomeGuide.cs:268`

## Magery: casting

- Magery | 64 spells in eight circles, ids 0-63 | `UOC/Spells/Initializer.cs:21-100`
- Magery | Mana per circle 4, 6, 9, 11, 14, 20, 40, 50, the same from a book or a scroll | `UOC/Spells/Base/MagerySpell.cs:8, 45`; scroll consumes mana: `UOC/Spells/Base/Spell.cs:759-775`
- Magery | Skill range: book index = circle + 2 in {-50,-30,0,10,20,30,40,50,60,70}, scroll index = circle, max = min + 40; book 0-40 ... 70-110, scroll -50 to -10 ... 50-90 | `MagerySpell.cs:15-17, 30-43`
- Magery | Below the first number the check fails without gain; the first number is reached with chance 0 and may gain; above the second it succeeds without gain | `SkillCheck.cs:61-75`; cast check `Spell.cs:619-634`
- Magery | Cast time 0.5 + 0.25 per circle (0.5 to 2.25 s) | `MagerySpell.cs:101-114`
- Magery | Blade Spirits and Summon Creature take four times as long (6 s) | `UOC/Spells/Fifth/BladeSpirits.cs:42-58`, `UOC/Spells/Fifth/SummonCreature.cs:91-100`
- Magery | Next spell may start 0.75 s after the cast time ends ("You have not yet recovered from casting a spell", CL 502644) | `Spell.cs:19, 506-509, 674-679, 971-972`
- Magery | You cannot move while casting | `Spell.cs:108-117`, `SRV/Mobiles/Mobile.cs:4198`
- Magery | Casting puts weapons/shields in hand into the backpack except items that allow equipped cast (spellbook, runebook); casting reveals | `Spell.cs:535-538, 565-568, 800-803`, `SRV/Mobiles/Mobile.cs:3786-3805`, `UOC/Items/Skill Items/Magical/Spellbook.cs` (`AllowEquippedCast` true), `Runebook.cs:118`
- Magery | Double-clicking a spell in the open spellbook casts it | `ClassicUO/src/ClassicUO.Client/Game/UI/Gumps/SpellbookGump.cs:766-776, 1229-1240`
- Magery | The book must hold the spell and be equipped or directly in the backpack | `UOC/Items/Skill Items/Magical/Spellbook.cs:299-343, 450-452`
- Magery | A scroll must be in the backpack (nested is fine) and is cast by double-click | `UOC/Items/Skill Items/Magical/Scrolls/SpellScroll.cs:46-50`
- Magery | Target range default 10 in this era; Night Sight 12; Wall of Stone, Fire, Poison, Paralyze, Energy Field and Dispel Field 15; Resurrection 1 | `UOC/Spells/Targeting/ITargetingSpell.cs:8`, `UOC/Spells/First/NightSight.cs:19`, `Third/WallOfStone.cs:26`, `Fourth/FireField.cs:29`, `Fifth/DispelField.cs:25`, `Fifth/PoisonField.cs:29`, `Sixth/ParalyzeField.cs:28`, `Seventh/EnergyField.cs:29`, `Eighth/Resurrection.cs:26`
- Magery | 30 seconds to pick a target | `Spell.cs:980-983`
- Magery | A book spell burns one of each reagent, from the backpack or any bag in it, all or nothing | `Spell.cs:260-263`, `SpellInfo.cs:85-90`, `SRV/Items/Container.cs:770-790` (recurse default true)
- Magery | A scroll is consumed only when the spell works and burns no reagent | `Spell.cs:260-262, 773-780`
- Magery | Reagents are consumed before the mana check and the skill check; mana is deducted only on success; a fizzle costs the reagents | `Spell.cs:741-775`
- Magery | "More reagents are needed for this spell" (CL 502630), "The spell fizzles." (CL 502632) | `Spell.cs:375-377, 757`
- Magery | Click a scroll once, Add To Spellbook (CL 3006144), then click the book | `UOC/Context Menus/AddToSpellbookEntry.cs:8-51`; single-click menu: `SC/docs/Help-Gumps-Plan.md` section 2 and `WelcomeGuide.cs:237-241` (the Execute menu)
- Magery | Damage ruins a spell only while casting; first-circle spells are exempt; Protection chance; poison and any damage count | `Spell.cs:85-96, 397-432`, `SRV/Mobiles/Mobile.cs:6065-6090`
- Magery | Equipping while casting disturbs; using an object during targeting cancels the spell | `Spell.cs:119-137`, `Mobile.cs:5007-5009, 5080-5082, 7934`
- Magery | Disturb recovery max(1 - sqrt(elapsed / cast time), 0.2) s | `Spell.cs:659-672`
- Magery | Protection (UOR) is self only, chance (Evaluating Intelligence + Meditation + Inscription) / 4 percent, max 75, duration 2 x Magery clamped 15 to 240 s | `UOC/Spells/Second/Protection.cs:92-179` (OnCast UOR branch)
- Magery | Reactive Armor, Protection and Magic Reflection share the DefensiveSpell action lock, freed one minute after they end or are used up ("The spell will not adhere to you at this time", CL 1005385) | `Second/Protection.cs:112-128`, `First/ReactiveArmor.cs:103-123, 224-255`, `Fifth/MagicReflect.cs:28-45, 124-152`, `UOC/Spells/Base/SpellHelper.cs:23-48`
- Magery | Reactive Armor pool (Magery + Meditation + Inscription) / 3 clamped 1 to 75, no timer; reflects a fifth (min 1) of each absorbed blow; a blow larger than the rest of the pool goes through and ends it | `First/ReactiveArmor.cs:41-100, 236-243`
- Magery | Damage scalar 1 + (EI - MR)/500 or /200 when EI is not above MR, + (Magery - 100)/400, doubled for targets that are not players and not human bodies | `Spell.cs:275-306`
- Magery | Resist: cut to 0.75 for Magic Arrow, Harm, Fireball, Lightning, Energy Bolt, Explosion; Flame Strike 0.6; Mind Blast half; Chain Lightning and Meteor Swarm half | the spell files `First/MagicArrow.cs:52-57`, `Second/Harm.cs:42-47`, `Third/Fireball.cs:43-48`, `Fourth/Lightning.cs:42-47`, `Sixth/EnergyBolt.cs:44-49`, `Sixth/Explosion.cs:88-93`, `Seventh/FlameStrike.cs:42-47`, `Fifth/MindBlast.cs:96-100`, `Seventh/ChainLightning.cs:78-83`, `Seventh/MeteorSwarm.cs:87-92`
- Magery | Spell damage goes through `AOS.Damage`, which in a non-AOS world is plain `Damage` (armor does not reduce it) | `UOC/Misc/AOS.cs:59-78`
- Magery | Stat spells: 1 + (int)(Magery x 0.1) points, duration 6 x Magery / 5 s (1.2 s per point); Clumsy, Feeblemind, Weaken, Curse, Mass Curse have no resist roll | `UOC/Spells/Base/SpellHelper.cs:378-407`; `First/Clumsy.cs:24-50`, `First/Feeblemind.cs`, `First/Weaken.cs`, `Fourth/Curse.cs`, `Sixth/MassCurse.cs:23-59`
- Magery | Four mage skills = 400 of 700 | `SC/data/configuration/shard-rules.json:9`
- Magery | Intelligence is the mana pool (ManaMax = Int); stat max 100 | `SRV/Mobiles/Mobile.cs:2221`, `CFG/modernuo.json:95`

## Magery: training, buying, starting kit

- Magery | Starting skills: Pure Mage 50, Warlock 48, Sorcerer 36 | `SC/data/professions/Prof.txt:137, 154, 331`
- Magery | Ladder: circle = skill / 10 gives a 25 to 50 percent base chance from the book ranges (before any stat bonus); spell costs: Night Sight SA SS = 6 gp, Strength MR NS = 6, Bless GA MR = 6, Arch Cure GA GI MR = 9, Poison Field BP NS SS = 11, Reveal BM SA = 8, Mass Dispel GA MR BP SA = 14, Magic Arrow 3, Flame Strike SS SA = 6 (prices below) | spell files (reagents) and `UOC/Mobiles/Vendors/SBInfo/SBMage.cs:40-47`
- Magery | Night Sight, Strength, Bless, Arch Cure, Reveal, Mass Dispel can be cast on yourself or the ground with nothing to hit; a repeat cast still runs the skill check (the "already" tests come after `CheckBSequence`) | `First/NightSight.cs:32-60`, `Second/Strength.cs`, `Third/Bless.cs`, `Fourth/ArchCure.cs:28-96`, `Sixth/Reveal.cs`, `Seventh/MassDispel.cs`
- Magery | Poison Field and the other field spells cannot be cast in town; Reveal and Mass Dispel can | `Fifth/PoisonField.cs:17`, `Sixth/Reveal.cs:7-14`, `Seventh/MassDispel.cs:9-18`
- Magery | Every cast that reaches the fizzle check trains Evaluating Intelligence | `Spell.cs:628-631`
- Magery | Mastery's valid use is a success that could have failed | `SC/src/BritanniaRenaissance.Content/WelcomeGuide.cs:~395-405` (Mastery page), `MasteryEngine.cs:89-106`
- Magery | Mage vendor sells Spellbook 18, scrolls of circles 1-3 at 12/22/32, Recall Rune 15, Black Pearl and Bloodmoss 5, the other six reagents 3; Alchemists sell the reagents at the same prices | `UOC/Mobiles/Vendors/SBInfo/SBMage.cs:16, 29, 40-47, 58-76`, `SBAlchemist.cs:26-33`
- Magery | Price scalar is 100 plus a faction tax (none here) | `UOC/Mobiles/Vendors/BaseVendor.cs:1384`
- Magery | Scrolls of circles 4-8 are not sold; Inscription crafts spell scrolls | `SBMage.cs:60-62`, `UOC/Engines/Craft/DefInscription.cs:258-420`
- Magery | Reagents are spawned in the wild | `SC/data/world-generation/alpha2b/world-generation.json:87` (Reagents.json in the spawner files); `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Reagents.json`
- Magery | A starting Magery character gets a Spellbook with content 0x382A8C38 = spell ids 3, 4, 5, 10, 11, 15, 17, 19, 21, 27, 28, 29 = Heal, Magic Arrow, Night Sight, Cure, Harm, Strength, Fireball, Poison, Teleport, Fire Field, Greater Heal, Lightning; three random scrolls; a Bag of Reagents (30 of each) | `UOC/Engines/Character Creation/CharacterCreation.cs:1188-1217`, ids `Initializer.cs:21-100`
- Magery | The shard raises each reagent stack in the bag to 50 (flag `Alpha3StarterCombatGear`) | `SC/src/BritanniaRenaissance.Content/StarterCombatIssuance.cs:20, 69-83`
- Magery | The Spellbook is blessed and kept on death | `UOC/Items/Skill Items/Magical/Spellbook.cs:122`, `SC/src/BritanniaRenaissance.Content/KeptItemDeathRouting.cs:10`

## Magery: the spell lines (reagents, effect, target; mana and ranges are per circle above)

Each entry: spell file, reagents at the SpellInfo lines, effect in the body lines. Target types are read from `Caster.Target = new SpellTarget<T>` in OnCast.
- First | Clumsy (BM NS, Dex curse, Mobile), Create Food (GA GI MR, no target, random of ten foods), Feeblemind (GI NS, Int curse), Heal (GA GI SS, (int)(Magery x 0.1) + Random(1,5) = 1 to 5, refuses poisoned), Magic Arrow (SA, Random(4,4) = 4 to 7), Night Sight (SA SS, range 12, 15 to 39 min, light level = 26 x Magery / 100), Reactive Armor (GA SS SA, self), Weaken (GA NS, Str curse) | `UOC/Spells/First/Clumsy.cs:9-16`, `CreateFood.cs:7-15, 17-31`, `Feeblemind.cs:9-16`, `Heal.cs:10-18, 26-70`, `MagicArrow.cs:8-14, 50-60`, `NightSight.cs:10-17, 34-48`, `ReactiveArmor.cs:12-20`, `Weaken.cs:9-16`, duration `UOC/Misc/LightCycle.cs:115`
- Second | Agility (BM MR), Cunning (MR NS), Cure (GA GI; chance (10000 + 75 x Magery - 1750 x (level + 1)) / 100), Harm (NS SS, Random(1,15)), Magic Trap (GA SS SA, TrappableContainer, power 1 = 1 damage within 1 tile), Protection (GA GI SA), Remove Trap (BM SA, fizzles unless trap is none or magic), Strength (MR NS) | `UOC/Spells/Second/Agility.cs:10-17`, `Cunning.cs:10-17`, `Cure.cs:8-15, 29-45`, `Harm.cs:7-14, 38-45`, `MagicTrap.cs:7-15, 25-36`, `Protection.cs:12-20`, `RemoveTrap.cs:7-14, 26-35`, `Strength.cs:10-17`; trap damage `UOC/Items/Containers/TrappableContainer.ExecuteTrap.cs:83-95`
- Third | Bless (GA MR, Str, Dex, Int), Fireball (BP, Random(10,7) = 10 to 16), Magic Lock (GA BM SA; not on locked-down or secure items; lock level MagicLock), Poison (NS; thresholds 130.2 / 170.2 / 199.8 with 1 in 10 Deadly; -10 per tile beyond 3), Telekinesis (BM MR; doors, trappable containers, dice, any container), Teleport (BM MR), Unlock (BM SA; (int)(Magery x 0.8) - 4 >= RequiredSkill; treasure map chests above level 2 refuse), Wall of Stone (BM GA; three stones, 10 s) | `UOC/Spells/Third/Bless.cs:10-17, 28-36`, `Fireball.cs:7-13, 34-40`, `MagicLock.cs:8-16, 28-60`, `Poison.cs:9-15, 38-90`, `Telekinesis.cs:7-14, 24-73`, `Teleport.cs:14-21, 33-90`, `Unlock.cs:8-15, 27-85`, `WallOfStone.cs:10-18, 28-100`; lockpicks cannot open a magic lock `UOC/Items/Skill Items/Thief/LockPick.cs:144-150`, a key resets it `UOC/Items/Misc/Key.cs:201-203`; Telekinesis users `ITelekinesisable` in `Items/Construction/Doors/BaseDoor.cs`, `Items/Containers/TrappableContainer.cs:36`, `Items/Games/Dices.cs`; trap ranges `TrappableContainer.ExecuteTrap.cs:59, 86, 105, 122`
- Fourth | Arch Cure (GA GI MR; radius 2; chance minus 1 point and one more poison level than Cure), Arch Protection (GA GI MR SA; radius 3; (int)(Magery/10 + 1) armor; min(144, 1.2 x Magery) s), Curse (NS GA SA; all three stats), Fire Field (BP SS SA; 5 tiles; duration Magery s below LBR; damage 2, 1 on an MR check 0 to 30), Greater Heal (GA GI MR SS; (int)(0.4 x Magery) + Random(1,10)), Lightning (MR SA; Random(12,9) = 12 to 20), Mana Drain (BP MR SS; resist percent 99; drains Random(1, min(mana,100))), Recall (BP BM MR) | `Fourth/ArchCure.cs:9-17, 44-72`, `ArchProtection.cs:11-20, 41-116`, `Curse.cs:11-19, 40-85`, `FireField.cs:12-21, 38-52, 118-148`, `GreaterHeal.cs:10-19, 40-60`, `Lightning.cs:7-14, 34-52`, `ManaDrain.cs:9-17, 55-78, 96`, `Recall.cs:11-19`
- Fifth | Blade Spirits (BP MR NS; 80 to 119 s; 1 follower; ground), Dispel Field (BP SS SA GA; DispellableField types incl. Gate Travel gates), Incognito (BM GA NS; min(1.2 x Magery, 144) s), Magic Reflection (GA MR SS; pool (int)(8 + (Magery + Inscription) / 200 x 7)), Mind Blast (BP MR NS SA; min(scalar x (high - low) / 2, 45), resisted halves), Paralyze (GA MR SS; 7 + 0.2 x Magery s, 0.75 if resisted; damage frees), Poison Field (BP NS SS; 15 + 0.4 x Magery s; Regular poison), Summon Creature (BM MR SS; needs Followers + 2; 4 x (int)Magery s) | `Fifth/BladeSpirits.cs:8-17, 25-40`, `DispelField.cs:8-17, 27-50`, `Incognito.cs:14-22, 105-130`, `MagicReflect.cs:10-18, 112-148`, `MindBlast.cs:8-17, 62-104`, `Paralyze.cs:10-18, 56-70`, `PoisonField.cs:12-21, 38-60, 100-122`, `SummonCreature.cs:8-16, 55-90`; reflect cost `SpellHelper.cs:861-896`; damage frees paralysis `SRV/Mobiles/Mobile.cs:6098`
- Sixth | Dispel (GA MR SA; chance (50 + 100 x (Magery - difficulty) / (focus x 2)) / 100, focus 20), Energy Bolt (BP NS; Random(24,18) = 24 to 41), Explosion (BM MR; Random(23,22) = 23 to 44 after 2.5 s), Invisibility (BM NS; 1.2 x Magery s; not vendors), Mark (BP BM MR), Mass Curse (GA NS MR SA; radius 2, no harm checks in the non-AOS branch), Paralyze Field (BP GI SS; 15 + Magery / 3 s; 7 + Magery / 5 s), Reveal (BM SA; 1 + (int)(Magery / 20) tiles, always succeeds in UOR) | `Sixth/Dispel.cs:9-17, 32-55`, `EnergyBolt.cs:7-14, 34-52`, `Explosion.cs:8-15, 63-100`, `Invisibility.cs:13-20, 36-70`, `Mark.cs:8-16, 24-60`, `MassCurse.cs:5-15, 27-55`, `ParalyzeField.cs:11-20, 36-50, 150-170`, `Reveal.cs:7-14, 22-80`; dispel numbers `UOC/Mobiles/BaseCreature.cs:989`, `Monsters/Misc/Melee/BladeSpirits.cs:52`, `EnergyVortex.cs:58`, `Monsters/Summons/SummonedAirElemental.cs:80` (117.5, same for Earth, Fire, Water), `SummonedDaemon.cs:72`
- Seventh | Chain Lightning (BP BM MR SA; Random(27,22), divided when more than two, caster not excluded), Energy Field (BP MR SS SA; 0.28 x Magery + 2 s), Flame Strike (SS SA; Random(27,22), x0.6 resisted), Gate Travel (BP MR SA; gates 30 s), Mana Vampire (BP BM MR SS; resist percent 98; takes all mana), Mass Dispel (GA MR BP SA; radius 8), Meteor Swarm (BM MR SA SS; Random(27,22) divided by count, caster excluded), Polymorph (BM SS MR; 18 forms; duration max(Magery, 120) s) | `Seventh/ChainLightning.cs:7-17, 31-95`, `EnergyField.cs:11-21, 38-55`, `FlameStrike.cs:7-14, 34-52`, `GateTravel.cs:12-20, 70-100, 142-165`, `ManaVampire.cs:8-17, 30-80`, `MassDispel.cs:9-18, 30-70`, `MeteorSwarm.cs:7-17, 37-100`, `Polymorph.cs:14-22, 85-200`, forms `UOC/Gumps/PolymorphGump.cs:10-27, 51-80`
- Eighth | Earthquake (BM GI MR SA; radius 1 + (int)(Magery / 15); 60 percent of Hits, min 10 for non-players, max 75; caster excluded), Energy Vortex (BM BP MR NS; 90 s), Resurrection (BM GA GI; dead player within 1; refuses self, Khaldun), Air and Earth Elemental (BM MR SS), Water Elemental (BM MR SS), Fire Elemental and Summon Daemon (BM MR SS SA; 70 karma), duration 4 x max(5, Magery) s | `Eighth/Earthquake.cs:8-18, 28-75`, `EnergyVortex.cs:8-18, 26-50`, `Resurrection.cs:10-18, 26-82`, `AirElemental.cs:8-17, 41-58`, `EarthElemental.cs:8-17`, `WaterElemental.cs:8-17`, `FireElemental.cs:8-18`, `SummonDaemon.cs:9-19, 43-62`
- Eighth | Control slots: Blade Spirits 1, Energy Vortex 1, Air 2, Earth 2, Water 3, Fire 4, Daemon 5; Summon Creature precheck is 2 free slots; 5 follower slots per mobile | `Monsters/Misc/Melee/BladeSpirits.cs:43`, `EnergyVortex.cs:51`, `Monsters/Summons/SummonedAirElemental.cs:70`, `SummonedEarthElemental.cs:60`, `SummonedWaterElemental.cs:66`, `SummonedFireElemental.cs:65`, `SummonedDaemon.cs:66`, `UOC/Mobiles/BaseCreature.cs:3836-3841`, `SRV/Mobiles/Mobile.cs:7952`
- Eighth | Spell summons are controlled (obey orders) except Blade Spirits and Energy Vortex (summoned with controlled false) | `UOC/Mobiles/BaseCreature.cs:3818-3860`, `Spells/Base/SpellHelper.cs:472-500`, `Fifth/BladeSpirits.cs:35`, `Eighth/EnergyVortex.cs:40`
- Town | Spells whose SpellInfo has allowTown false cannot be cast in a guarded region: Wall of Stone, Fire Field, Blade Spirits, Poison Field, Summon Creature, Mass Curse, Paralyze Field, Energy Field, Chain Lightning, Meteor Swarm, Earthquake, Energy Vortex, the four elementals, Summon Daemon; message CL 500946 | `UOC/Regions/GuardedRegion.cs:140-148`, `Spell.cs:139`, the `false,` argument in each SpellInfo (list above)
- Fields | Lines of 3 (Wall of Stone) or 5 tiles, appear after `|i| x 0.2` s, deleted if not in sight or no room; harmful fields use `ValidIndirectTarget` and `CanBeHarmful`, the caster is not excluded in UOR | `Third/WallOfStone.cs:30-50`, `Fourth/FireField.cs:38-52, 82-110`, `UOC/Spells/Base/SpellHelper.cs:413-470`
- Areas | Fire Field, Chain Lightning, Meteor Swarm, Earthquake skip party, guild, own pets and innocents through `ValidIndirectTarget`; Arch Cure and Arch Protection filter only on `CanBeBeneficial` | `SpellHelper.cs:413-470`, `Fourth/ArchCure.cs:44-90`, `Fourth/ArchProtection.cs:50-90`
- Tame pets | "Spell summons ... are not affected" by the dungeon rule | `WelcomeGuide.GettingStarted.cs:315` (flag `PetRestrictions`)

## Magery: Recall, Gate Travel, runes

- Recall | Refused for a criminal, within 30 s of attacking a player (`CheckCombat`: Aggressed list, player defenders), overloaded; Gate Travel has the first two but no overload test | `UOC/Spells/Fourth/Recall.cs:28-60, 130-160`, `Seventh/GateTravel.cs:25-60, 120-140`, `SpellHelper.cs:68, 185-205`
- Recall | Recall From, Recall To, Gate From, Gate To and Mark are refused in the T2A lands (x 5120+, y 2304+), Khaldun, Felucca dungeon regions, Felucca wind and Solen hive areas, champion spawn | `SpellHelper.cs:107-136, 619-660, 690-760`
- Recall | Marking and recalling inside a house footprint is refused ("That location is blocked") | `Fourth/Recall.cs:78-84`, `Sixth/Mark.cs:32-36`, `SpellHelper.cs:154-175`
- Recall | Destination must be a place a mobile can spawn | `Recall.cs:73-77`, `GateTravel.cs:75-79`
- Recall | Mark needs the rune in the backpack; double-click on a marked rune renames it | `Sixth/Mark.cs:38-42`, `UOC/Items/Skill Items/Magical/Misc/RecallRune.cs:270-290`
- Recall | Gate Travel opens two gates, one at the caster and one at the rune, lasting 30 s (T2A flag true) | `Seventh/GateTravel.cs:88-96, 142-150`
- Recall | Dungeon travel: Recall and Gate do not work into or out of Felucca dungeons | `SC/docs/Beta-2a-Hythloth-Hot-Zone-Audit.md:10, 18`
- Recall | Hot Zone confirmation for a blue player entering a Hot Zone from outside (flag `HotZoneTravelWarning`), box and `[TravelWarning` | `SC/src/BritanniaRenaissance.Content/TravelWarningService.cs:43, 53-56, 130-145`

## Magery: Safe World, Hot Zones, Knocked Out

- SafeWorld | A harmful spell on a player passes only if the target is criminal or murderer, has Intent on, an encounter exists, or guild war / same guild; otherwise `CanBeHarmful` fails before `CheckSequence` | `SC/src/BritanniaRenaissance.Content/PvpIntentService.cs:230-243, 355-440, 442-470, 484-500`; `UOC/Spells/Base/Spell.cs:867-881`; message CL 1001018 `SRV/Mobiles/Mobile.cs:8458-8503`
- SafeWorld | Intent can be turned on with [Intent; the Welcome guide's Fighting page | `PvpIntentService.cs:85-115`, `WelcomeGuide.cs:~210-245`
- HotZones | Hot Zones are Fire Island, Buccaneer's Den island, Hythloth | `WelcomeGuide.cs:271-290`
- KnockedOut | Mana to 0 and spell lost on knock-out; wake with half mana; cannot be harmed, healed or cured | `KnockedOutService.cs:200, 606, 613, 620-646`
- General | Helping a criminal or murderer is a criminal act | `SRV/Mobiles/Mobile.cs:8407-8431`
- General | Harmful spells go through `CanBeHarmful` (self allowed) | `SRV/Mobiles/Mobile.cs:8476-8479`

## EvalInt

- EvalInt | Skill use: target within 8, 1 s wait, refusals for self, Town Crier, invulnerable shopkeeper, items | `UOC/Skills/EvalInt.cs:14-52, 25`
- EvalInt | Margin of error max(0, 20 - (int)(skill / 5)); check `CheckTargetSkill(EvalInt, 0, 120)`; mana percent from Base 76.0 | `EvalInt.cs:55-92`
- EvalInt | Every cast that reaches the fizzle check rolls EvalInt (0 to cap) before Magery, success or fizzle | `Spell.cs:619-634`
- EvalInt | Damage multiplier terms and examples (+20 percent at 100 against 0, +10 against 50, 0 against 100, -25 for 50 against 100, -50 for 0 against 100) | `Spell.cs:275-306`
- EvalInt | Duration and stat amounts use Magery in the non-AOS branch | `SpellHelper.cs:378-407`
- EvalInt | Protection chance includes it | `Second/Protection.cs:206-213`
- EvalInt | Starting skill 35 for Pure Mage | `Prof.txt:138`
- EvalInt | Easy class (generated block; not restated) | `shard-rules.json:84`

## Meditation

- Meditation | Mana point wait: medPoints = (Int + Meditation) / 2; 7 s at 0; 7 - 239 m / 2400 + 19 m^2 / 48000 up to 100; 1.0 to 120; 0.75 above; plus armor; x0.5 meditating; clamp 0.5 to 7 | `UOC/Misc/RegenRates.cs:200-220`
- Meditation | Examples: Int 40 / Med 0 = 5.17; 40 / 50 = 3.32; 60 / 60 = 2.45; 100 / 100 = 1.00 | same formula (computed)
- Meditation | Mana +1 per timer tick; interval re-read each tick | `SRV/Mobiles/Mobile.cs:9135-9150`
- Meditation | Passive check each tick when not meditating, chance n = ratio x (1 - v) + v, v = sqrt(skill x 0.005) | `RegenRates.cs:28-42, 138-141`
- Meditation | Trance conditions: no target, Hits at least a tenth, mana not full, hands free (spellbook or runebook allowed) | `UOC/Skills/Meditation.cs:17, 25-72`
- Meditation | Chance (50 + 2 x (skill - missing mana)) / 100; success calls CheckSkill(0, 100); 10 s wait after the roll; message texts CL 501851, 501850, 502626 | `Meditation.cs:76-96`
- Meditation | Use reveals | `Meditation.cs:23`
- Meditation | Trance ends on: actual step, death, using an item or mobile, lifting, damage, revealing action (casting included), any skill use, crafting, weapon swing, ranged shot, full mana ("You are at peace.", CL 501846; "You stop meditating.", CL 500134) | `SRV/Mobiles/Mobile.cs:2183-2192, 4411, 4822, 5007, 5080, 5128, 6096, 7025, 8228-8235`, `SRV/Skills.cs:798`, `UOC/Engines/Craft/Core/CraftItem.cs:1876`, `UOC/Items/Weapons/BaseWeapon.cs:924`, `Weapons/Ranged/BaseRanged.cs:88`
- Meditation | Armor penalty: sum of BaseArmorRatingScaled of shield, neck, hands, head, arms, legs, chest, divided by 4, added to the rate; allowance All (leather, cap, circlets), Half (studded, hide), None otherwise | `RegenRates.cs:223-256`, `UOC/Items/Armor/BaseArmor.cs:170-172, 287, 449-452, 517`, allowance overrides listed by `grep DefMedAllowance` in `Items/Armor/Leather`, `Studded`, `Helmets`
- Meditation | Shield scalar is 1.0 (ArmorScalars has six entries, shield is index 6); plate chest 40 x 0.35 / 4 = 3.5; wooden shield 8 / 4 = 2; heater shield 23 / 4 = 5.75; full plate sums 40 so 10 s, clamped to 7 | `BaseArmor.cs:464-472, 500-517`, `Plate/PlateChest.cs` (ArmorBase 40), `Shields/WoodenShield.cs:26`, `Shields/HeaterShield.cs:26`
- Meditation | No casting penalty for armor exists in the spell code | `Spell.cs` (none); all casting checks read
- Meditation | Reactive Armor strength includes Meditation; Protection too | `First/ReactiveArmor.cs:236-243`, `Second/Protection.cs:206-213`
- Meditation | Trainers: Mage 60-83 (20.0 to 27.7), guildmaster 85-100 (28.3 to 33.3) | `Mage.cs:18`, `MageGuildmaster.cs:17`
- Meditation | Starting skills of the Pure Mage template do not include it | `Prof.txt:137-139`
- Meditation | Standard class (generated) | `shard-rules.json`

## MagicResist

- MagicResist | Resist percent = max(MR / 5, MR - ((caster Magery - 20) / 5 + (1 + circle) x 5)) / 2; resisted if that is at least a random value | `MagerySpell.cs:61-97`
- MagicResist | Table (caster Magery 100): MR 100 = 39.5, 37, 34.5, 32, 29.5, 27, 24.5, 22; MR 75 = 27 to 9.5; MR 50 = 14.5 to 5; MR 25 = 2.5; MR 0 = 0. Caster Magery 50, MR 100 = 44.5 to 27 | same formula (computed from that formula)
- MagicResist | Training in `CheckResisted`: only when n is above 0 and below 1, and MR below (1 + circle) x 10 + (1 + circle / 6) x 25 = 35, 45, 55, 65, 75, 85, 120, 130 | `MagerySpell.cs:61-86`, `SC/docs/Beta-1-Skill-Gain-Curve-Audit.md:66`
- MagicResist | Spells that call CheckResisted in UOR: Magic Arrow, Harm, Fireball, Poison, Lightning, Mana Drain, Mind Blast, Paralyze, Energy Bolt, Explosion, Flame Strike, Mana Vampire, Chain Lightning, Meteor Swarm | grep result in `UOC/Spells` (files listed above)
- MagicResist | Mana Drain resist percent fixed 99, Mana Vampire 98, so they train at MR 0 | `Fourth/ManaDrain.cs:96`, `Seventh/ManaVampire.cs:85`
- MagicResist | Curse (Int part) and Mass Curse (Dex and Int) call `target.CheckSkill(MagicResist, 0, 120)`, no circle limit; skipped when an equal or stronger curse is on | `SpellHelper.cs:350-377`, `Fourth/Curse.cs:49-52`, `Sixth/MassCurse.cs:41-45`
- MagicResist | Fire Field check `CheckSkill(MagicResist, 0, 30)`, damage 1 instead of 2 | `Fourth/FireField.cs:144-148, 241-245`
- MagicResist | Paralyze x0.75, Poison nothing, Mind Blast half | spell files above
- MagicResist | Message "You feel yourself resisting magical energy." (CL 501783) | spell files above
- MagicResist | Damage scalar uses MR against EI | `Spell.cs:275-306`
- MagicResist | Self-cast harmful spells are allowed (`CanBeHarmful` true for self; Safe World handler returns the stock result when attacker and defender are the same) | `Mobile.cs:8476-8479`, `PvpIntentService.cs:383-386`
- MagicResist | Mana Drain on self: Magery 30 from a book / 10 from a scroll, 11 mana, BP MR SS | `MagerySpell.cs:15-17`, `Fourth/ManaDrain.cs:9-17`, `SBMage.cs`
- MagicResist | Monsters that cast (AI_Mage and present in the spawn data): evil mage, orcish mage, ratman mage, among others | `UOC/Mobiles/Monsters/**` (`AIType.AI_Mage`), spawn names from `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/*.json`
- MagicResist | Safe World: a player may be attacked only if he has Intent on (or criminal, murderer, existing encounter, guild war) | `PvpIntentService.cs:230-243, 355-440`
- MagicResist | Starting skills Pure Mage 35, Warlock 24 | `Prof.txt:139, 155`
- MagicResist | Armor does not change a resist | `MagerySpell.cs:61-97`
- MagicResist | Standard class (generated) | `shard-rules.json:103`

## SpiritSpeak

- SpiritSpeak | Under UOR the skill is the old ghost-hearing use; the heal/channel version is AOS only | `UOC/Skills/SpiritSpeak.cs:14-59` (non-AOS branch), `:16-28` (AOS branch)
- SpiritSpeak | Success chance `CheckSkill(SpiritSpeak, 0, 100)`; contact time Base / 50 x 90 s, min 15; sets CanHearGhosts | `SpiritSpeak.cs:30-50`
- SpiritSpeak | Failure sets CanHearGhosts false ("You fail your attempt at contacting the netherworld.", CL 502443); success says CL 502444; fading says CL 502445; already in contact adds no timer | `SpiritSpeak.cs:34-55, 70-74`
- SpiritSpeak | 1 s wait; reveals | `SpiritSpeak.cs:30, 58`
- SpiritSpeak | Dead players cannot use skills | `SRV/Skills.cs:775-778`
- SpiritSpeak | Ghost speech is replaced by "oOo" for living listeners without CanHearGhosts; dead listeners hear it as said | `SRV/Mobiles/Mobile.cs:1810-1813, 5604`, `UOC/Mobiles/PlayerMobile.cs:2675-2700`, `Mobile.DefaultGhostChars` `SRV/Mobiles/Mobile.cs:8258`
- SpiritSpeak | Healer 80-100 and guildmaster 65-88 | `Healer.cs:19`, `HealerGuildmaster.cs:16`
- SpiritSpeak | Easy class (generated) | `shard-rules.json:92`

## OPEN:

- OPEN: Magery is 15.8k characters against the brief's "about 9,000". The 64-spell reference (from the heading "The spells" to the end, 9.7k) is the part to move or trim: it could become the Spellbook item topic (`skills: ["Magery"]`) with only the training and shopping text left on the skill page.
- OPEN: Mass Curse (`Sixth/MassCurse.cs:27-55`) in the non-AOS branch curses every mobile within 2 tiles without `ValidIndirectTarget` or `CanBeHarmful`, so it appears to bypass the Safe World rule (blue players without Intent, party, pets). The text only says it curses everyone within 2 tiles. Owner decision, possible hook.
- OPEN: Chain Lightning's non-AOS branch includes the caster in the area; the text says so ("you too if you stand there"). Meteor Swarm excludes the caster. Meteor Swarm's resist halves `damage` (shared) rather than `toDeal`, so one resisted target halves the damage of the later ones; not described.
- OPEN: Under Safe World, `IsGuildWarOrDuel` is true for two players of the same guild, so guildmates can cast harmful spells on each other. The text says only "at guild war with you"; same-guild casting was left out as a design question.
- OPEN: The Alchemy item topic `potion-nightsight` says "15 to 25 minutes"; the code is `Utility.Random(15, 25)` minutes = 15 to 39 (`UOC/Misc/LightCycle.cs:115`, used by the potion and by the Night Sight spell). The Magery page says 15 to 39 for the spell. Check the potion text.
- OPEN: The assignment asked what Spirit Speak heals and drains; under UOR it does neither (that branch is `Core.AOS`). The page says hearing ghosts is all it does.
- OPEN: Self-targeting a harmful spell (Mana Drain at yourself) is allowed by the code (`Mobile.cs:8476-8479`) and the page recommends it for Resisting Spells up to 65; not tried in a live client.
- OPEN: "Reagents also lie in the wild" rests on `Reagents.json` being in the generation manifest (60 spawners); not seen in the world.
- OPEN: Monster names given as casters (evil mage, orcish mage, ratman mage) are `AI_Mage` creatures that appear in the generated spawn names; their locations, Magery and which spells they cast were not checked.
- OPEN: The starting Spellbook holds 12 spells including Fire Field, Greater Heal and Lightning (fourth circle). `SC/docs/Alpha-3-Starter-Package-Audit.md:96` calls it "low-circle"; the page lists the 12 decoded from `0x382A8C38`.
- OPEN: The healer guildmaster also teaches Resisting Spells (75-98, about 25 to 33) (`HealerGuildmaster.cs:15`); not mentioned.
- OPEN: The page tells the player to click a scroll once for the Add To Spellbook menu. The entry text (CL 3006144) is verified, the single-click menu on items is from the Help plan and the Execute menu, not seen on a scroll in the client.
- OPEN: Summon Creature's random animals may take more than one control slot (its precheck is 2 free); the page says only "needs 2 free followers".
- OPEN: The generated "stats" block was changed after this was written; the pages do not describe stat leaning, but check that its sentence for Magery (Intelligence adds to the skill) agrees with `SRV/Skills.cs:250-300` (Magery IntScale 0.15 in `ModernUO/Distribution/Data/skills.json`; the other four skills have no stat scale).
