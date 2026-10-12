# Audit: crafting skill pages (Blacksmith, Fletching, Carpentry, Cartography, Cooking, Inscribe, Tailoring, Tinkering, Poisoning)

File audited and fixed in place: `work/help-gumps/parts/crafting.skills.json` (valid JSON, ASCII, 9 pages; every page still has 3+ headings and 900+ characters of own text: Blacksmith 5.7k, Tailoring 4.1k, Tinkering 4.0k, Fletching 3.4k, Inscribe 3.3k, Carpentry 3.4k, Cooking 2.9k, Poisoning 2.4k, Cartography 2.1k). A copy of the file before my edits is in the audit session scratch folder only.

Path shorthand: UOC = `ModernUO/Projects/UOContent`, CRAFT = `UOC/Engines/Craft`, T2A = `CRAFT/T2A`, SB = `UOC/Mobiles/Vendors/SBInfo`, SHARD = `ShardContent/src/BritanniaRenaissance.Content`.

## Counts

- Sentences of page text checked against code: 321 (about 340 separate factual claims, counting each price, range and vendor).
- Wrong or misleading, corrected to what the code does: 17 sentences.
- Removed as unsupported: 3 phrases/sentences.
- Removed because they only name menu-excluded recipes (coordinator request): 4 sentences.
- Left alone (verified): the rest (about 295). Those include every price, every skill range, every vendor claim, the trainer claims, the bulk order flow, the Camping/Kindling claims, the Runebook recipe, mana per circle, poison charges and potion ranges.
- Could not verify (left as written, flagged below): see "Not checked".

## Craft flow, checked against the code (all nine pages now describe this exactly)

Double-click tool (`BaseTool.cs:149-176`): needs the tool in the pack or worn, then the cursor message "Target this tool to make last item, or any other target to begin crafting." The cursor is `T2ACraftToolTarget` (range 2). Target the tool: repeats the last item (`T2ACraftToolTarget.cs:19-57`), or "You have not yet crafted anything." and opens the menu. Any other target goes to `T2ACraftSystem.ShowMenu`:

| Craft | What the first target must be | Anything else |
| --- | --- | --- |
| Blacksmithing (`BlacksmithMenu.ResourceSelection`, 474-532) | an ingot pile (its metal is used), or a metal weapon/armor the smith list knows (iron is used) | another item: "Target the ingots you wish to use." and ask again; a non-item target (ground, mobile) opens the menu at once if you carry at most one ingot type, otherwise asks for ingots |
| Bowcraft (`T2ACraftSystem.cs:52-63`) | log, board, feather or shaft | another item: "Target the wood or feathers you wish to use." and ask again; a non-item target opens the menu |
| Carpentry (`:64-75`) | log or board | same pattern, "Target the wood you wish to use." |
| Tailoring (`TailoringMenu.ResourceSelection`, 311-374) | cloth/uncut cloth (hue of the pile decides the color), or leather/hides | anything else: "Select the resource you wish to use (cloth, leather, or hides)." and ask again |
| Tinkering (`TinkeringMenu.ResourceSelection`, 403-479) | log/board, any ingot, or a keg | anything else: "Select the resource you wish to use (wood or ingots)." and ask again |
| Cartography, Inscription | no tool: the skill itself opens the menu (`UOC/Skills/Cartography.cs:14-24`, `UOC/Skills/Inscribe.cs:19-27, 100-129`); a Mapmaker's Pen or Scribe's Pen double-click would reach the same menu but is not needed | |

The menu is a packet item list that lists only what the character has skill and materials for (`T2ACraftSystem.CanCraftItem`, 194-248; a recipe at exactly its lower number has chance 0 and is hidden). After a craft the menu does not reopen (`CraftItem.cs:1977-1995`). One attempt = 2 timer ticks, first at once and one after 1.25 s (`CraftItem.cs:1008-1012, 1850-1853`).

## Changes

| Page | Before | After | Source |
| --- | --- | --- | --- |
| Cooking | "cut a fish with scissors for four raw fish steaks" (WRONG, scissors do nothing to a fish) | "carve a fish you caught with a knife or sword for four raw fish steaks" | `Fish.cs:6-20` (Fish is `ICarvable`, not `IScissorable`); `Scissors.cs:66` (only `IScissorable`); `BladedItemTarget.cs:34`; knives and swords open it: `BaseKnife.cs:20-25`, `BaseSword.cs:17-22` |
| Cooking | skillets, rolling pins, flour sifters "open nothing" | "open no menu here" (the double-click still shows the target cursor, then nothing happens) | `BaseTool.cs:162-166`; `T2ACraftSystem.cs:18-108` (no cooking branch) |
| Poisoning | "(its tooltip shows them)" for the charges (WRONG here: no item tooltips in this era) | removed | `ExpansionConfiguration.cs:10` (`opl.enable` defaults to `Core.AOS`; no override in `Distribution/Configuration`); `BaseWeapon.cs:3304-3395` (the UOR single-click label has no poison text) |
| Poisoning | "Only a weapon you hold in one hand, with a blade or a point" | "Only a one-handed weapon with a blade or a point can be poisoned (it does not have to be in your hand). Axes, maces, bows and two-handed weapons cannot" (the check is the item's layer, not whether you wield it) | `Poisoning.cs:67-72` |
| Poisoning | "Training is slow and every try spends a potion." (unsupported; class is hard but x1.5 below 70) | "Every try spends a potion." | `shard-rules.json` skillGain classes; generated gain block |
| Tailoring | "A failed attempt costs about half the cloth or leather (rounded up)." (WRONG for cloth) | "A failed attempt with leather costs about half of it (rounded up)." Cloth is OWNER item 2 | cloth takes the hue-aware path: `CraftItem.cs:1807-1810` (`ConsumeHuedRes` with `ConsumeType.All` takes the full amount, no halving) vs the leather path `CraftItem.cs:681-688` |
| Tailoring | "Leather is the cheaper road" and cloth items "use more cloth for each point" (unsupported; in gold cloth is the cheaper material: cloth 2 gp, leather 6 gp) | both removed | `SBTailor.cs:52`, `SBTanner.cs:42` |
| Tailoring | "From about 50 make leather gloves"; "From about 80 the studded gorget"; cloth "up to about 80" | about 52 / about 79 / about 79 (ranges 51.8, 78.8 and 78.9) | `DefTailoring.cs:431, 563, 151` |
| Tailoring | scissors "on clothing or leather armor you made" | "that a player made" (the flag is `PlayerConstructed`, any player) | `BaseArmor.cs:632-662`, `BaseClothing.cs:238-282` |
| Tailoring | "The table also lists bolts of cloth, oil cloth and bone armor, which the Tailoring menu does not offer." | sentence removed (kept "The menu works with ordinary cloth, leather and hides.") | see Menu-excluded recipes |
| Blacksmith | "The table also lists dragon scale armor ... cannot be made." | sentence removed | see Menu-excluded recipes |
| Tinkering | "Fletcher's Tools, pens, skillets and flour sifters are not in the menu." | removed | see Menu-excluded recipes |
| Tinkering | "The table also lists a few things the menu does not offer: the Skillet, ..." | removed (kept "The Tinkering menu has no Repair.") | see Menu-excluded recipes |
| Tinkering | Tinker's Tools: "a worn-out set has to be replaced by making another" with no word on buying | adds "no shop in Britain sells them" | only `Tinker`, `Vagabond` and `GolemCrafter` use `SBTinker` (`SBInfo/SBTinker.cs:34`; `NPC/Tinker.cs:25`, `Vagabond.cs:22`, `GolemCrafter.cs:23`); none is spawned in Britain (see Vendor check) |
| Tinkering | Ward: "A Tinker can also make the Backpack Ward (it is in the Miscellaneous list; ...)" gated only on `TheftProtection` | "A Tinker may also be able to make the Backpack Ward: if the recipe is on offer, it is in the Miscellaneous list and the table shows what it takes." Still `requires: TheftProtection` | the recipe is added only when `wardCraft.enabled` AND `TheftProtectionService.Enabled`: `SHARD/BackpackWardCraft.cs:79-87`; the config value is `shard-rules.json` `wardCraft` (true today). `requires` can only name a feature flag (`HelpService.cs:130-141`, `HelpCatalog.cs:198-203`), so the config switch cannot be expressed; see OWNER item 5 |
| Blacksmith | Smelting "is a Mining skill check, and a failure burns away half the pile" (true but misleading) | "with iron ore it cannot succeed below Mining 25 and is certain from 75, and a failure burns away half the pile" | `Ore.cs:168-203` (iron difficulty 50, check range 25 to 75; below the lower number the check cannot pass: `SkillCheck.cs:205-217`); failure halves the pile: `Ore.cs:247-256` |
| Blacksmith | Repair: "target a weapon or armor piece" | "a metal weapon or armor piece" (only items in the smith's own recipe list can be repaired) | `Repair.cs:263, 337` (`SearchForSubclass` in the Blacksmithy list) |
| Blacksmith | Smelt gives "half the ingots it cost if you made it, or one ingot if it came from a shop"; practice-smelting "half the ingots back" | "half ... (rounded down) if a player made it, or one ingot if not (a piece bought in a shop, for example)"; "about half" | `Resmelt.cs:93-107` (`PlayerConstructed`, `Amount / 2`) |
| Blacksmith | Bulk orders: "A deed asks for 10, 15 or 20 pieces of one armor or weapon type" (only true of a small deed) | "A small deed asks ..." plus "From skill 70.1 you may be offered a large deed instead: it names several different pieces, and you fill it by combining completed small deeds into it." | `NPC/Blacksmith.cs:90-103` (a `LargeSmithBOD` from 70.1 with chance (skill-40)/300); `LargeBOD.cs:97-140` (`EndCombine` takes completed small deeds) |
| Fletching | "(anything else and the game asks again)" | "(if you target some other item, the game asks again)" (a non-item target opens the menu) | `T2ACraftSystem.cs:52-63`, `T2ACraftToolTarget.cs:68` (`targeted as Item`) |
| Carpentry | list "holds only what your skill and wood allow" | "your skills and materials" | second skills and other materials gate many entries: `DefCarpentry.cs:404-592`; `T2ACraftSystem.cs:204-245` |
| Carpentry | wooden shield "from about 50", quarterstaff "from about 70" | "about 53", "about 74" (ranges 52.6, 73.6) | `DefCarpentry.cs:356, 306` |
| Carpentry | "A keg takes 3 barrel staves" | adds the barrel lid and barrel hoops (hoops are a Tinkering part) | `DefCarpentry.cs:253-255` |
| Carpentry | add-ons listed with no mention of other requirements | adds: "Instruments, the fishing pole and many add-ons also need a second skill (between 40 and 80, depending on the item) and other materials such as cloth or ingots, and the menu lists them only when you have both." | instruments Musicianship 45 + cloth (`:404-421`); fishing pole Tailoring 40 + cloth (`:311-314`); beds, dummies, dress form, wheels, looms Tailoring 50 to 75 + cloth (`:482-578`); forges, anvils Blacksmithy 75/80 + ingots (`:512-526`); ovens, mills Tinkering 50 + ingots (`:579-590`); Pentagram, Abbatoir Magery 75/50 + ingots (`:497-502`) |

## MENU-EXCLUDED RECIPES

For each craft: item class names (as in the code) of every recipe in the `DefXxx.CraftSystem` with `RequiredExpansion <= UOR` that the era T2A menu cannot offer. Method: read each Def file with the `Core.AOS/SE/ML/SA` gates false (those recipes are never added, and the generator's `IsOfTheEra` already drops anything with a later `SetNeededExpansion`), then compared with the static type lists of the menu class (a type is offered only if it is in a list and `CraftItems.SearchFor` finds it).

| Craft (generator name) | Menu class | Excluded class names |
| --- | --- | --- |
| Blacksmithing (`craft:Blacksmithing`) | `BlacksmithMenu` | DragonGloves, DragonHelm, DragonLegs, DragonArms, DragonChest (group "Dragon Scale Armor", scales via SubRes2; the menu has no category for them) |
| Bowcraft (`craft:Bowcraft`) | `BowFletchingMenu` | none (Kindling, Shaft, Arrow, Bolt, Bow, Crossbow, HeavyCrossbow are all offered) |
| Carpentry (`craft:Carpentry`) | `CarpentryMenu` | none (all 13 furniture, 9 container, 4 weapon/shield, 6 instrument, 6 misc and 29 add-on recipes are listed; `Board` is only added under AOS/SE) |
| Cartography (`craft:Cartography`) | `CartographyMenu` | none (LocalMap, CityMap, SeaChart, WorldMap) |
| Inscription (`craft:Inscription`) | `InscriptionMenu` | none (the 64 scrolls and Runebook are all reachable; each is listed only when the spell is in a carried spellbook) |
| Tailoring (`craft:Tailoring`) | `TailoringMenu` | BoltOfCloth, OilCloth, BoneHelm, BoneGloves, BoneArms, BoneLegs, BoneChest, OrcHelm |
| Tinkering (`craft:Tinkering`) | `TinkeringMenu` | Skillet, FlourSifter, FletcherTools, MapmakersPen, ScribesPen, BolaBall, Bola, FactionGasTrapDeed, FactionExplosionTrapDeed, FactionSawTrapDeed, FactionSpikeTrapDeed, FactionTrapRemovalKit |
| Alchemy (`craft:Alchemy`, not my page; checked for completeness) | `AlchemyMenu` | none (all 20 potions are in the menu lists) |

Two traps for the exclusion code:

1. **Duplicate class names in Tinkering.** `ClockParts` and `SextantParts` are in the craft system twice. The first entry of each (group "Parts", made from iron ingots, skill 25 to 75 and 30 to 80) is what the menu offers (`SearchFor` returns the first match). The second entry of each (group 1044051, no skill range "0 to 0", made from `AxleGears` plus `Springs` / `Hinge`, `DefTinkering.cs:408-412`) is NOT offered. Excluding by class name alone would drop both lines, so exclude by group or by index, or leave both lines. The same group 1044051 also holds `AxleGears`, `ClockRight`, `ClockLeft`, `Sextant`, `PotionKeg`, which ARE offered (Parts, Miscellaneous, and the keg path), and `Bola`, which is not.
2. **Items that are listed but only conditionally.** Most Carpentry add-ons, instruments and the fishing pole also need a second skill; the generated table shows only the Carpentry range. This is not an exclusion, but the new Carpentry sentence covers it.

The `Ward` (`BackpackWard`) is added to the Tinkering craft list and to the Miscellaneous menu list at server start only when `wardCraft.enabled` and theft protection are on, so it is neither excluded nor missing when it is present.

## Vendor check (task item 3)

Britain bounds x 1280-1750, y 1400-1900. Spawn files read: `ModernUO/Distribution/Data/Spawns/shared/felucca/Vendors.json` (stock, 58 spawners in the box), `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns/Vendors.json` (the shard's own, 57 spawners, all in Britain), and `britain-vendor-overrides.json` (2 spawners: Herbalist, Alchemist x2, Mage x2, MageGuildmaster). Types spawned in Britain (union): Alchemist, AnimalTrainer, Architect, Armorer, Artist, Baker, Banker, Bard, Blacksmith, Bowyer, Butcher, Carpenter, Cobbler, Cook, Fisherman, Furtrader, Healer, Herbalist, InnKeeper, Jeweler, Mage, Mapmaker, Merchant, Minter, Peasant, Provisioner, RealEstateBroker, Scribe, Shipwright, Tailor, Tanner, TavernKeeper, Waiter, Weaponsmith, Weaver, plus guildmasters (they sell nothing, `BaseGuildmaster` is not an active vendor) and hirelings. **No Tinker, Miner, Farmer, Rancher, Ranger, Vagabond, Beekeeper, Miller, Glassblower, StoneCrafter.** (The stock file has one `Tinker` at 5726,3243, far outside Britain, and the shard's file does not carry it.) The only Tinker-area NPC is a `TinkerGuildmaster` at 1422,1654.

Every "buy it from / sold by" claim left on the pages, checked to a spawned type and its SBInfo:

| Page | Claim | Vendor spawned (count) | SBInfo line |
| --- | --- | --- | --- |
| Blacksmith, Tinkering | Tongs 13, Smith's Hammer 21, iron ingot 5 (16 on shelf) at a Blacksmith; Blacksmith pays 25 for a Buckler, 7 for Tongs, 10 for a Smith's Hammer | Blacksmith (2) | `SBBlacksmith.cs:16-17, 100, 121, 118` |
| Fletching | Fletcher's Tools 2, feathers 2, arrows 2, bolts 3 at a Bowyer; Bowyer pays 17/25/27 for Bow/Crossbow/Heavy Crossbow | Bowyer (1) | `SBBowyer.cs:16`, `SBRangedWeapon.cs:24-43` |
| Fletching, Cooking | arrows 2 / bolts 5 / Kindling 2 at a Provisioner | Provisioner (2) | `SBProvisioner.cs:27-28, 81` |
| Fletching, Carpentry | boards 3, Saw 15 at a Carpenter; pays 15/10/9/6 for wooden shield/crook/quarterstaff/stool; 14 for Hammer, 9 for Saw | Carpenter (1) | `SBCarpenter.cs:18, 24`, `SBWoodenShields.cs:24`, `SBStavesWeapon.cs:56-58` |
| Cartography | blank map 5 at a Mapmaker; pays 3 for local/city/world map, nothing for a sea chart; blank scroll 12 | Mapmaker (1, 1416,1754) | `SBMapmaker.cs:16-36` |
| Cooking | Butcher: raw chicken leg 6, bird 9, lamb leg 9, ribs 16; Cook pays chicken leg 3, bird 8, lamb leg 4 | Butcher (1), Cook (4) | `SBButcher.cs:19-22`, `SBCook.cs:53, 59-60` |
| Inscribe | blank scroll 5 at Scribe/Mage; Mage: rune 15, spellbook 18, reagents 3 (5 for black pearl and bloodmoss), scrolls of circles 1-3, pays 4 to 18 per scroll; Alchemist reagents | Scribe (2), Mage (5), Alchemist (5) | `SBScribe.cs:17`, `SBMage.cs:16-67, 100-127`, `SBAlchemist.cs:28-35` |
| Tailoring | Sewing Kit 3, cloth 2 at a Tailor; Tanner: leather 6, pays 30/37/40 for gloves/gorget/sleeves | Tailor (3), Tanner (1) | `SBTailor.cs:16, 52`, `SBTanner.cs:42, 58-64` |
| Tinkering | Jewelers sell gems | Jeweler (2) | `SBJewel.cs:59-67` |
| Poisoning | Lesser poison potion 15 and nightshade 3 at an Alchemist or Mage | Alchemist, Mage | `SBAlchemist.cs:21, 28`, `SBMage.cs:36, 54` |
| all trainers | Armorer, Weaponsmith, Blacksmith (Blacksmithy); Bowyer (Bowcraft); Carpenter; Mapmaker; Cook, Herbalist; Mage, Scribe; Tailor | all spawned; same list as `WelcomeGuide.GettingStarted.cs:187-203` | |

Not on any page now: a buy claim for Tinker's Tools (nobody sells it), a Tinker trainer, a Miner/pickaxe seller. Ovens (1424,1712 and 1448,1615) stand beside the Cook (1427,1716) and Baker (1450,1617) spawns; forges and anvils stand at the smithies (1353-1356,1776-1786 and 1361-1363,1574): `Decoration/Britannia__britain.cfg:115-118, 1412-1430, 1735-1743`.

## Other items verified without change (selection)

- Special metals 65/70/75/80/85/90/95/99 for both Blacksmithy and Mining, armor rating +2 to +16, weapons get nothing in UOR: `DefBlacksmithy.cs:687-695`, `Ore.cs:164-176`, `BaseArmor.cs:305-323`, `BaseWeapon.cs:702-756`.
- Exceptional: chance = success chance minus 0.60 (Blacksmith/Tailoring easing to 0.45 between 95 and 100; Bowcraft half the chance minus 0.10), +8 armor rating, +20% weapon damage, +20% durability, shops pay x1.25: `CraftItem.cs:812-839`, `BaseArmor.cs:325`, `BaseWeapon.cs:2729-2732`, `GenericSell.cs:72-90`. Maker's mark prompt only at Base 100.0, CONTINUE marks, CANCEL still makes the piece: `CraftItem.cs:1936-1955`, `QueryMakersMarkGump.cs:38-62`.
- Tool charges 25 to 75 random, 100 exceptional, one per attempt win or lose, 50 for starter tools: `BaseTool.cs:29, 71-76`, `CraftItem.cs:1411, 1611, 1710, 1814`, `StarterCraftMaterialIssuance.cs:24, 57-146`.
- Failure cost: half rounded up, except batch crafts (shafts, arrows, bolts take half of the whole batch) and one-item recipes (lose it): `CraftItem.cs:681-688, 1585`.
- Skill gain only strictly between the two numbers: `SkillCheck.cs:205-217, 63-72`.
- Repair weakening 3/2/1 points (Base below 70 / 70 / 90), chance 40 + damage - skill/10, refusal when too worn, poisoned weapons refused: `Repair.cs:41-45, 232-310`.
- Blacksmith bulk orders: Blacksmith only (Tailor, Weaver, Weaponsmith are AOS-gated), skill above 0, waits 1/2/6 hours real time: `NPC/Blacksmith.cs:76-109`, `Tailor.cs:57-58`, `Weaponsmith.cs:81-82`, `PlayerMobile.cs:187, 293-307`, `ContentFeatureFlags.cs:14`; owner-approved: `docs/Alpha-3-Blacksmith-BOD-Readiness.md`.
- Cooking: no tool, 5 s timer, 1 tile target range, burns beyond 3 tiles, chance = skill, one piece at a time, heat-source list (campfire, ovens/fireplaces, fire pit, heating stand, Fire Field, forges): `CookableFood.cs:10-168`. Flour, dough and baking are unbuilt (Part B): `docs/Cooking-Era-Restore-Readiness.md:55`; a flour mill add-on exists but nothing in cooking uses flour.
- Cartography: map areas, treasure map levels (decode needs -3/41/51/61/70/70, fishing gives level 1 at Fishing 90, monsters 1% chance), 4 blank maps and a sextant at start: `LocalMap.cs`, `CityMap.cs`, `SeaChart.cs`, `WorldMap.cs`, `TreasureMap.cs:343-410`, `Fishing.cs:17, 221-234`, `BaseCreature.cs:3224-3255`, `CharacterCreation.cs:1076-1083`.
- Inscribe: mana per circle 4/6/9/11/14/20/40/50 taken only when the scroll works; fail ruins scroll and reagents; Runebook needs 8 blank scrolls + Recall + Gate Travel + an unmarked recall rune (or target a rune at the first prompt); book copy is a skill check 0..50 with no materials: `DefInscription.cs:253-340, 434-437`, `CraftItem.cs:704-723`, `Inscribe.cs:94-153, 237`.
- Poisoning: skill delay 10 s, potion consumed and bottle returned either way, 2 s timer, ranges 0-60/30-70/60-100/95-100, charges 18 minus 2 per level, 50% per hit on swords/knives/spears, 1 in 20 self-poison below Base 80, 20 karma, corrosion off so an oil cloth cannot clean a poisoned weapon: `Poisoning.cs`, `BaseSword.cs:23-38`, `PostUorSystemGates.cs:18`, `OilCloth.cs:69-83`.
- Tinkering: all ranges and costs quoted, the T2A jewelry flow (the whole gem stack you target is used, on success), trap flow (dart/poison/explosion; lockable, unlocked, not locked down, within 2 tiles, one trap each, "disabled until you lock the chest", power Tinkering/10 x 9): `DefTinkering.cs:228-440, 605-700`, `TinkeringMenu.cs`, `BaseJewel.cs:186-209`.
- Flags: `Alpha3StarterCraftMaterials`, `Alpha3StarterScissors`, `HarvestAutoRepeat`, `ActionAutoRepeat`, `PoisonRelief`, `TheftProtection` are real `DeferredFeatureFlags` names, all true in `shard-rules.json`. No off flag, no anti-macro text, no banned word, ASCII only.

## OWNER

OWNER 1: Tinker. No `Tinker` is spawned in the shard world (Britain), and only `Tinker`, `Vagabond` and `GolemCrafter` sell Tinker's Tools. A Tinker's last worn-out set cannot be bought, and Tinkering recipes need a Tinker's Tools set, so a Tinker or anyone who relies on crafted tools can be stuck. Also `WelcomeGuide.GettingStarted.cs:201-203` lists Tinker (Tinkering, Lockpicking, Remove Trap), Miner (Mining), Ranger (Detecting Hidden, Archery, Tracking, Veterinary) and Veterinarian (Animal Lore, Veterinary) as trainers, none of which is in Britain; `README.md` line 35 and `BackpackWardVendor` also name Tinkers. The pages say nothing about buying or training Tinkering. Decide: spawn a Tinker (and the others) or change those texts.
OWNER 2: Tailoring cloth failure. A failed attempt with cloth takes the whole amount, while every other craft (and Tailoring with leather) takes half rounded up; the code comment right above it says "half on failure" (`CraftItem.cs:1807-1810`). It looks like a bug in the hue-aware path (cloth targeted keeps its colour). The page now speaks only of leather. If it is fixed, add the cloth back. Possible related bug: `CraftContext.LastHue` is set only by cloth crafts and never reset, so "make last" on a later leather item goes through the hue path with the old hue (`T2ACraftToolTarget.cs:49-52`); not tested live.
OWNER 3: Tailoring special leather. The menu accepts only plain `Leather` and `Hides` (`TailoringMenu.cs:337`), so Spined, Horned and Barbed leather (and their armor bonus +10/+13/+16) cannot be used, although such hides can be carved and Smith bulk orders can ask for them (`SmallSmithBOD.cs`). The page says only that the menu works with ordinary cloth, leather and hides. Intended?
OWNER 4: Oil cloth versus poison. The Poisoning page says an oil cloth does not wipe poison off a weapon here (verified: poison corrosion is switched off, and `OilCloth.cs` cleans only corroded weapons in this era). `Alpha-3-Player-Skill-Audit.md` SK-005 describes the cleanup as a Publish 5 feature. Keep or drop the sentence.
OWNER 5: Ward sentence gate. The Tinkering Ward sentence is gated on `TheftProtection`, but the recipe also needs the config value `wardCraft.enabled` (`BackpackWardCraft.cs:79-87`). The help system can gate only on feature flags, so I reworded it to "if the recipe is on offer". Options: leave it, or add a small gate in `HelpService.GateOn` / `HelpCatalog.GateNames` for "WardCraft" (flag and config) and restore the plain sentence.
OWNER 6: Corpse carving doubles feathers, wool and hides in Felucca at every expansion (`BaseCreature.cs:2030-2036`), unlike the single yield the shard set for mining and lumber. The pages do not mention the doubling.
OWNER 7: Tinkering jewelry uses up the whole stack of gems you target (code comment says so, `BaseJewel.cs:186-209`) and names the piece by the count. The page warns the player to split off one gem first. Confirm this is intended.

## Not checked or only partly checked

- Real-client behavior was not run (brief says no clients). Menu text is from the code (`ItemListEntry` labels such as "ringmail gloves (10 ingots)" are lower-cased type names). The Skill Guide's "Camping", "Lumberjacking", "Mining", "Blacksmithing" cross-references assume those pages exist in the other areas.
- "Click him once and choose Bulk Order Info" and "(see Training in [Welcome)" rely on the Welcome guide's own statements about clicking an NPC for its menu (`WelcomeGuide.GettingStarted.cs:190, 228`); I did not look at ClassicUO for the context-menu click.
- Skill values: all "skill N" statements mean the skill value the game uses for its checks (`Skill.Value`, which can include a stat share); the page does not discuss stats (the generated stats block does). Not changed.
- Fletching, Carpentry and Tailoring each restate "starts you at 50%", which the generated craft table also says ("In this craft you already succeed 50% ..."). The repeat is accurate, not contradictory; left because the text also explains "first number" and "second number". The coordinator may trim it.
- Exceptional-armor "protects 8 more" and shield scaling: values read from `BaseArmor.ArmorRating` and `BaseShield.ArmorRating`, not measured in play.
