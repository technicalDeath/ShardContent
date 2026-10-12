# Audit: parts/a.items.json (area A, armor, shields, clothing, jewelry; 18 topics)

Auditor pass on the writer's 18 item topics. Every number and claim was re-read in the code that runs (UOR, T2A craft menus, no tooltips). The file was edited in place; it parses, is ASCII only, has no banned words, titles are 18 characters or fewer, each topic has 4 or fewer links, every `related` key exists, and no class name appears twice in any `parts/*.items.json`.

## Counts

- Checked: 18 topics, about 170 sentences, about 430 individual facts (every rating, Strength, Dexterity, weight, durability range, price, slot, vendor, craft route, repair rule, formula).
- Wrong and fixed: 6 (magic hat hit points, "every piece needs Strength", "Ringmail weighs more than plate", "Metal and bone pieces take Dexterity", "Pieces named female", tanner studded stock).
- Misleading and fixed or removed: 1 removed ("It is for looks" on clothing, see OWNER 1); 3 reworded for precision (Item Identification, Arms Lore, "leather armor" repair line).
- Qualified for inherited use (the family topic is also shown for artifacts derived from the listed classes): 16 edits ("ordinary", "plain", "most").
- Added (verified, useful): tanners sell the female plate chest (207 gold); scissors give leather from shoes and boots.
- Left alone: everything else (all other numbers matched the code exactly).

## Changes

| Topic | Before | After | Source |
| --- | --- | --- | --- |
| a-magic-hat | "The Strength you lose costs 2 or 3 hit points" | "costs 5 hit points" | PlayerMobile.cs:549-575 (pre-AoS `HitsMax = RawStr / 2 + 50 + GetStatOffset(Str)`; the offset is the full -5), Hats.cs:505-507 |
| a-armor | "Every piece needs a minimum Strength." | "Most pieces need a minimum Strength (shields need none)." | Shields/*.cs have no `OldStrReq`; BaseArmor.cs:184,395; BaseClothing.cs `OldStrReq => 0` |
| a-armor | "Metal and bone pieces also take points off your Dexterity" | "Most metal and bone pieces (not the helmets except the plate helm) also take ..." | `OldDexBonus` exists only on plate (all, incl. plate helm), chain chest/legs, ringmail (all four), bone chest/legs/arms/gloves; none on the other helms, coif, bone helm |
| a-armor | "Pieces named female are for female characters only." | "The female chests, the bustiers, leather shorts and leather skirt are for female characters only." | `AllowMaleWearer => false` on FemalePlateChest, FemaleStuddedChest, StuddedBustierArms, FemaleLeatherChest, LeatherBustierArms, LeatherShorts, LeatherSkirt; BaseArmor.cs:1072-1084 |
| a-armor | "Leather armor, bone armor and the wooden shield cannot be repaired. Arms Lore shows how worn a piece is." | "Leather, studded leather and bone armor and the wooden shield cannot be repaired by anyone. A successful use of Arms Lore shows how worn a piece is." | Repair.cs:310-345 (armor needs a craft-list entry in the system whose menu offers Repair); only BlacksmithMenu.cs:214,431 offers Repair; DefTailoring.cs:675 and DefCarpentry.cs:595 `Repair = Core.AOS`; ArmsLore.cs:87-98 (only on a skill success) |
| a-armor | "...until the Item Identification skill reveals it" | "...until a successful use of the Item Identification skill reveals it" | ItemIdentification.cs:38-41 (`CheckTargetSkill(ItemID, item, 0, 100)`), BaseArmor.cs:1395-1404 |
| a-armor | colored ingot list of 8 values | "+2 for dull copper, rising by 2 for each ore up to +16 for valorite (Blacksmithing 65 up to 99)" (shorter, same facts) | BaseArmor.cs:306-322; DefBlacksmithy.cs:688-695; Mining.cs:109-200 (all eight ores minable, no era gate) |
| a-armor (gated) | "...are newbied: you keep them ..." | "...are newbied, which means you keep them when you die (a murderer does not) and shopkeepers will not buy them." (term explained) | Item.cs:2296,2326; GenericSell.cs:35-40; CharacterCreation.cs:727-761 |
| a-plate | "Blacksmiths always sell it and armorers sometimes" | "...sell the ordinary pieces ..." and added "Tanners sell the female plate chest for about 207." | SBTanner.cs:30 (FemalePlateChest 207); NPC/Blacksmith.cs:53; Armorer.cs:27-60 |
| a-plate, a-chain, a-ring, a-studded, a-leather, a-bone | "A new piece has N to M durability" | "A new ordinary piece ..." (artifacts derived from these classes have 150 or 255) | derived-class `InitMinHits/InitMaxHits` (HeartOfTheLion 255, GladiatorsCollar 150, ...) |
| a-chain, a-ring | "Blacksmiths always sell it" | "...sell the ordinary pieces ..." | same |
| a-ring | "Ringmail weighs more than plate (a plate chest is 10 stones)" | "Ringmail chest, legs and arms weigh more than their plate versions (a plate chest is 10 stones)" | RingmailGloves 2.0 = PlateGloves 2.0 (not heavier) |
| a-helms | "It is not sold: monsters drop it." | "The plain orc helm is not sold: monsters can drop it." | Loot.cs:118 (OrcHelm only in generic `ArmorTypes`); OrcChieftainHelm/OrcishVisage derive from it |
| a-helms | "A blacksmith makes them from iron ingots" | "A blacksmith makes the five metal helmets from iron ingots" | BlacksmithMenu.cs:37-42; the orc helm is not in the T2A tailor or smith menu |
| a-helms | "A new helmet has 45 to 60 durability" | "A new ordinary helmet ..." | derived artifacts |
| a-studded | "Armorers sell it ... Tanners sell a few pieces for less." | "Some armorers sell it ... Tanners sell it for less (chest about 75, arms 57)." | NPC/Armorer.cs:27-46 (studded in 2 of the 4 stock sets); SBTanner.cs:23-37 (all five studded pieces, female chest 62, bustier 97) |
| a-leather (gated) | "highest of your fighting and Magery skills" | "highest skill among Swordsmanship, Mace Fighting, Fencing, Archery and Magery" | StarterPackageSelection.cs:36-63 (only those five skills compete; ties go to the first listed) |
| a-clothes | "...needs no Strength. It is for looks." | "...needs no Strength." | OWNER 1: BaseClothing.OnHit (BaseClothing.cs:325-331) makes worn clothing change combat damage |
| a-clothes | "To change its color, ..." | "To change the color of most clothing, ..." | special robes and masks can override `Dye` |
| a-clothes | "Scissors turn most clothing in your pack back into cloth" | "... (leather, for shoes and boots)" | Shoes.cs:13-20 and BaseClothing.cs:238-286 (resource taken from the craft recipe; shoes are made from leather, DefTailoring.cs:367-370) |
| a-hats | "Tailors sell every hat but the bonnet" | "Tailors sell every plain hat but the bonnet" | derived hats (BurglarsBandana, CaptainJohnsHat, ...) are not sold; SBTailor.cs:37-48 |
| a-robes | "A robe or a cloak ... Tailors sell robes" | "A plain robe or cloak ... Tailors sell plain robes" | DeathRobe, AcidProofRobe, ANecromancerShroud, SamaritanRobe derive from Robe |
| a-aprons | "Tailors sell the half apron" | "Tailors sell the plain half apron" | CrimsonCincture derives from HalfApron |
| a-jewelry | "In this era they are ornaments" | "In this era the ordinary ones are ornaments" | artifact jewelry derived from GoldRing/GoldBracelet etc. is not sold or crafted; BaseJewel.cs:328-355 (`Core.AOS` gates every effect) |

## Verified and left unchanged (main items)

- Armor scalars, hit-location chances, absorb formula (half to all of the piece's own rating), minimum 1 damage, shield-first, 25 percent wear, bashing wear, 50 percent rating at 0 durability, repair rules (anvil and forge within 2 tiles, item in pack, may lower maximum durability): BaseArmor.cs:517,727-780,986-996; BaseWeapon.cs:1722-1760,1952-1957; Repair.cs.
- Mana regeneration penalty (rating x share / 4 seconds, studded half, leather none, shields full): RegenRates.cs:144-255, class `DefMedAllowance`.
- Stealth refused at armor rating 26 or more (`(int)m.ArmorRating`): Stealth.cs:38-43,91-95. Casting clears shield and weapon: Spell.cs:565-568,793-802, Mobile.cs:3787-3806.
- Shield rating, block chance (`(Parry - 2 x rating) / 100`, floor 1 percent), block removes half the rating, all of it against Archery weapons, worked example (12.5 and 75 percent): BaseShield.cs:15-72.
- Every rating, Strength, Dexterity, weight, durability and `types` entry for all 94 listed classes against each class file (script check, all matched).
- Slot layers for all 70 slot claims read from UOData/tiledata.mul (helm 6, pants 4, neck 10, shield 2, middle torso 17, outer torso 22, shirt 5, cloak 20, waist 12, outer legs 23).
- Prices and vendor lists for every "about N gold": SBBlacksmith.cs, Armors/SB*.cs, SBTanner.cs, SBTailor.cs, SBProvisioner.cs, SBCobbler.cs, SBJewel.cs, SBMage.cs, SBWeaver.cs. Vendors spawn in Britain (Armorer 4, Blacksmith 2, Tanner 1, Tailor 3, Weaver 3, Cobbler 2, Provisioner 2, Jeweler 2, Mage 3 in Vendors.json inside the Britain bounds).
- Skeletons carry one of five bone pieces (Skeleton.cs:40-67) and spawn in Outdoors, Covetous, Deceit, Graveyards, Khaldun, LostLands (spawn files in `spawnerFiles`; Skeleton not in `excludedSpawnerTypes`).
- Craft routes: BlacksmithMenu.cs (armor, helmets, shields incl. wooden kite shield, female plate chest), CarpentryMenu.cs:38 + DefCarpentry.cs:356 (wooden shield from 9 logs), TailoringMenu.cs + DefTailoring.cs (hats, clothes, shoes, leather and studded armor, hue of the cloth carried), TinkeringMenu.cs:72-82,377-378,486-540 + DefTinkering.cs:394-402 + BaseJewel.cs:186-206 (jewelry: iron ingots, gem target, whole stack consumed on success).
- Dyes: Dyes.cs:20-55, DyeTub.cs:86-125 (range 1, not worn).
- Magic wizard's hat: +5 Int, -5 Str, -5 Dex (Hats.cs:505-507), stat mods applied without an era gate (BaseClothing.cs:486-516,596); Int is max mana (Mobile.cs:2221); Dex is max stamina (Mobile.cs:2166).
- Starter gear (the three `Alpha3StarterCombatGear` blocks): flag exists (ShardRulesConfiguration.cs:797) and is true (shard-rules.json:204). Archer leather chest and legs, equipped or packed, newbied: StarterCombatIssuance.cs:93-100. Parry wooden shield: stock CharacterCreation.cs:1252-1259 (equipped, newbied); the flag only tops up a shield for the Melee package with Parry that has none (StarterCombatIssuance.cs:102-106). Newbied kept on death unless murderer, refused by vendors: engine code, not flag-gated, so those two statements are also true with the flag off; the gate is conservative but harmless. Starter armor is newbied only, **not bound**: only the starter Ward is bound (BackpackWard.cs:36 `Nontransferable`, BackpackWardState.cs:195). The text matches the code; CLAUDE.md "newbied and permanently bound" is true only for the Ward (see OWNER 4).

## Length

a-armor is about 2,700 characters of ungated text (it was about 2,540 before my accuracy edits; the two gated lines add about 180 more when the flag is on). I trimmed the ingot list; I cut nothing else because each paragraph is a verified, distinct rule that every armor piece relies on (what armor stops, where blows land, slots, stats and mana, wear and repair, magic). The topic is shown for every BaseArmor piece, so it is the shared rules page.

## OWNER

- OWNER 1: `BaseClothing.OnHit` (ModernUO Items/Clothing/BaseClothing.cs:325-331) does `damageTaken = Math.Min(absorbed, damageTaken)` with `absorbed` 1 to 4. A blow that lands on worn clothing (head 15 in 100 on a hat, chest 35 on a shirt, legs 22 on pants) is cut to 1 to 4 damage, so plain clothes protect much more than "no armor rating" suggests. The help text now says only that clothing gives no armor rating. Looks like an upstream cleanup bug (RunUO subtracted the absorbed amount); follow ModernUO/CLAUDE.md workflow rule 1 before touching it.
- OWNER 2: leather, studded, bone armor and the wooden shield cannot be repaired by anyone (tailoring and carpentry `Repair = Core.AOS`, the T2A tailoring menu has no Repair entry). The text states it. Whether tailors should repair leather is a design question.
- OWNER 3: T2A jewelry crafting consumes the whole targeted gem stack on success and needs a gem to start (TinkeringMenu.cs, BaseJewel.cs:186-206). The text warns the player; whether that is intended is the owner's call.
- OWNER 4: CLAUDE.md says starter items are "newbied and permanently bound"; the code (StarterCombatIssuance.cs:10-12, CharacterCreation.cs:727-761) makes starter combat gear and clothes newbied only (kept on death except by murderers, refused by vendors). Only the starter Ward is bound. The help text follows the code. CLAUDE.md should be corrected, or the code changed, by the owner.
- OWNER 5: the rating shares (helm 14, arms 15) differ from the hit chances (head 15, arms 14) in the stock tables (BaseArmor.cs:517 vs BaseWeapon.cs:1738-1743). The text states each correctly without comment.
- OWNER 6: bone armor (and the orc helm) are in DefTailoring but the T2A tailoring menu has no bone category, so players cannot make them; the text says only that skeletons carry bone armor and monsters drop the orc helm. Dragon and daemon armor are coded (dragon in the smith craft list) but are in no T2A menu, vendor list or loot list; they fall to the generic armor page and are not advertised.
- OWNER 7: colored leather (spined, horned, barbed; +10, +13, +16 rating) is left out because the T2A leather branch does not appear to let a player choose the sub-resource (TailoringMenu.cs:337-347).

## Could not check

- Whether the client labels the Bascinet "norse helm" and the Norse helm "bascinet": the tiledata names for 0x140C and 0x140E are swapped relative to the classes (confirmed in UOData/tiledata.mul), and the label comes from the compressed cliloc, which I did not decode. The topics use the class names, as the craft menu does.
- Which artifacts can actually be found in this world (treasure chests, champion spawns). The family topics now say "ordinary"/"plain" wherever a statement is about stock, vendors or crafting, so they stay true if an artifact derived from a family class turns up.
- The text for the Welcome guide's wording of Repair (WelcomeGuide.GettingStarted.cs:244-247) agrees with the Repair claims here.
