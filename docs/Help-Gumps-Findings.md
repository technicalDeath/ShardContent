# Help text: findings for the owner

Collected 2026-10-11 while writing and auditing the item Help topics and the Skill Guide (`Help-Gumps-Plan.md`, `Help-Content-Spec.md`). These are **facts the writers found in the code, data and docs that look wrong or undecided**. None of them was changed; the help text says only what is true now, or leaves the point out. Each line names where the writer found it; the per-area notes are under `work/help-gumps/parts/*.notes.md` and `*.audit.md` (scratch).

## The world has gaps that the text had to work around

1. **No plain Tinker (or Miner, Farmer, Rancher, Ranger, Vagabond, Beekeeper, Miller, Glassblower, StoneCrafter) is spawned in Britain.** The generated Britain vendor list (`ModernUO/Distribution/Data/Spawns/shared/felucca/Vendors.json` inside Britain's bounds) has only a **Tinker Guildmaster**, who sells nothing. So nobody sells Tinker's tools, shovels, sextants, clocks or key rings, and the **Backpack Ward vendor sale (`BackpackWardVendor`, plain `Tinker` only) cannot happen in the real world**. The Ward evidence (`Beta-2a-Ward-Vendor-Readiness.md`) used a Tinker spawned by hand on a disposable host. README line 35 and the Welcome guide's trainer list name a Tinker. Decide: spawn a Tinker in Britain (and a Miner, for shovels and pickaxes), or change those texts.
2. **Nobody can join the Thieves' Guild in the generated world, and stock Stealing requires it to steal from another player.** `Stealing.cs:139` refuses with "You must be in the thieves guild to steal from other players" unless `NpcGuild == ThievesGuild`; the guild is joined only through a Thieves' Guildmaster NPC (`BaseGuildmaster.cs:150`). The only Felucca Thieves' Guildmaster in the stock data is at Buccaneer's Den (2659, 2194), outside Britain, and world generation keeps vendor spawners inside Britain, so none is generated. The Alpha 2 theft rehearsals gave the thief the guild by hand (`UOR-ERA-AUDIT.md`). Checked in the code and data files, not in the live dev world. Other player-versus-player routes do not need the guild (Knocked Out looting, Snooping). Decide whether the guildmaster should exist (Buccaneer's Den is a Hot Zone); the Stealing page now says one sentence about it, and the audit report holds the five removed paragraphs ready to restore.
3. **The Weaponsmith stocks swords, axes, daggers and bows only about 1 shop time in 3** (a stock `SBWeaponSmith` random switch with one case). Blacksmiths stock everything.
4. **Special leathers (spined, horned, barbed), dragon scale armor and bone armor cannot be made.** The era's tailoring menu accepts only plain leather or hides, and the era blacksmith/tailor menus have no dragon or bone armor. The hides still drop and Smith bulk orders can ask for them. Granite and sand are unreachable (the Glassblower and StoneCrafter are not spawned).
5. **Later-era things are for sale or drop:** the Fisherman sells aquarium deeds and creatures; the Provisioner sells a plant bowl; golems drop a clockwork assembly that builds a Golem pet at Tinkering 60; the Jeweler sells communication crystals; the Shipwright sells dragon-prow ships; the Provisioner's oil flask refills a lantern that never burns out. The text names none of them except where they matter.

## Text elsewhere that the findings contradict

6. **Welcome guide, Camp travel page and the confirmation window:** "Bonded pets come too", but pet bonding is off here, so no pet can be bonded.
7. **`Novice-Combat-Assist-Evidence.md`** says an Orc has 96-120 hit points; the code has `SetHits(58, 72)`. **`Guide-Getting-Started-Pages.md`** says Knocked Out lasts 90 s; the code (`KnockedOutService.cs:18`) says 30 s.
8. **`CLAUDE.md` and design notes** call starter items "permanently bound"; the code and docs say newbied (kept on death unless the player is a murderer; shopkeepers refuse them). The text follows the code.
9. **The generated recipe tables list recipes the era's craft menus never offer** (dragon armor, bone armor, orc helm, oil cloth, bolts of cloth, skillet, flour sifter, pens, bolas, faction traps, clock and sextant assemblies). The audit lists them per craft so the generator can exclude them.

## Rules the code has that may not be intended (not described in the text)

10. **Mass Curse** (non-AoS branch) curses everyone within 2 tiles with no harm check, so it seems to bypass Safe World.
11. **Same-guild players count as guild war** under Safe World (`PvpIntentService`), so guildmates may cast harmful spells on each other.
12. **`BaseClothing.OnHit`** caps damage taken to the clothing at 1-4 (an upstream change), so a blow on a hat or shirt is very small; no text depends on it.
13. **Jewelry crafting consumes the whole stack of the gem you target** (the text warns players to split off one gem).
14. **Carving a human corpse** costs karma and can make an innocent's corpse a criminal act, as stock; confirm it is wanted on a safe-world shard.
15. **Pets lose 10 loyalty an hour even while the owner is logged out** (auto-stable is SE-only), so a pet left about 10 hours goes wild.
16. **A successful theft from a non-guild player sets permanent flags** (stock classic mode): not verified under Safe World, not described.
17. **Bought and crafted tools get a random 25-75 charges; starter tools exactly 50.**
18. **Detecting Hidden has almost no wait between uses** in UOR (the target handler resets the timer), against the 1 s design (audit item SK-007).
19. **Orc and savage `BolaBall` drops are dead** (the era tinker menu has no Bola recipe): your pending bola ball ruling.
20. **The spyglass prints "Trammel : <phase>"** to the player.
21. **`Runebook`** is ungated (owner ruling SK-010) though it did not exist in April 2000.
22. **No tooltips in this era** (`opl.enable` is not set): players cannot see a weapon's numbers except in the Help pages and through Arms Lore.

## Added by the audits (each line was checked in the code)

23. **A failed Tailoring attempt with cloth takes all of it**; every other craft takes half rounded up, and the code comment says "half on failure" (`CraftItem.cs:1807-1810`): looks like a bug. Also `CraftContext.LastHue` is never reset, so "make last" on leather after cloth may take the wrong path (not tested).
24. **Colored leather** (spined, horned, barbed) is unusable because the tailoring menu accepts only plain leather and hides; **oil cloth cannot clean poison** because poison corrosion is off (audit item SK-005 calls it a Publish 5 feature).
25. **Corpse carving doubles feathers, wool and hides** in Felucca (`BaseCreature.cs:2030-2036`), though SK-012 made mining and logs single yield before AoS.
26. **Hatchets never wear out chopping** (`BaseAxe` has no `IUsesRemaining`) while pickaxes, shovels, bardiches and halberds do.
27. **Animal Lore 110 on wild creatures that cannot be tamed is unreachable** under the 100 skill cap (SK-011); **deep-sea fishing prizes are live** because the catch table stays stock (SK-008), and the Fishing page advertises them; the stable's message promises a pet is sold after a real week, but nothing enforces it.
28. **Clubs, staves, bows and crossbows cannot be repaired at all** in UOR (Carpentry and Bowcraft have `Repair = Core.AOS`), while a worn weapon loses up to half its damage; leather, studded and bone armor and the wooden shield cannot be repaired either.
29. **Safe World lets guildmates and allied guilds harm (and so snoop) each other**, not only guilds at war (`PvpIntentService.cs:442-460`).
30. **Shopkeepers are not invulnerable** (`vendor.isInvulnerable` is false under UOR): they can be stolen from, snooped and set on a player; Provocation aimed at one costs 75 karma. The pages say so.
31. **Remove Trap can only be started from the Britain Tinkers' Guildmaster lesson** (about skill 28 to 33), and there is no Detecting Hidden trainer in Britain (the Ranger is not spawned). The Welcome guide's "Training" page lists trainers that are not spawned (Miner, Ranger, Tinker, Veterinarian) and omits the guildmasters and wandering healers who do teach, and Jewelers (who teach Item Identification).
32. **The skills window shows effective skill (with the stat bonus); gain and trainer limits use the trained skill.** For Lockpicking, Snooping and Stealing the two differ.
33. **Passive Detecting Hidden runs** because you kept it on 2026-09-30 while its era is unresolved.
34. **Hot Zones text names Hythloth** but is gated only on `HotZones`, not `HythlothHotZone`.

35. **An exceptional pickaxe very likely has 150 uses, not 100** (the axe base class doubles the uses, then `Pickaxe.OnCraft` adds 50); a live check of `usesRemaining` would settle it. The text gives no number.
36. **The Novice Combat sentences hard-code 60 (stamina floor) and 30 (Tactics floor)** in the weapon topic and the fighting pages; if `noviceCombat.staminaFloor` or `tacticsFloor` change in `shard-rules.json`, the text must change too.

37. **In a Hot Zone single-target spells hit anyone in the zone, but fields, Chain Lightning, Meteor Swarm and Earthquake still skip blue players without Intent** (Hot Zones do not change notoriety): confirm that is intended. The Magic pages say "aim a spell" and name the skipped spells.
38. **Spell names in the client differ from the server's**: the client spellbook says "Flamestrike" and "Magic Untrap" (the server says "Flame Strike" and "Remove Trap"); other text should use the client names.
39. **Resisting Spells can be trained by casting Mana Drain on yourself** (the code allows it; not run live): decide whether to advertise it (the page suggests it).

40. **Under UOR any damage the healer takes slips a bandage** (threshold 0, where AoS uses 18/25): confirm that is intended. Each hit taken while bandaging lowers the chance by 2 percent and the heal by 4.
41. **Pens are optional** (Cartography and Inscription open their menus without a tool; a pen only wears out): only the make-last click makes a pen worth owning.
42. **Smith bulk-order rewards under UOR still include post-UOR items** (sturdy shovel and pickaxe, gloves of mining, colored anvil, ancient smithy hammer): the already-accepted Contract-Review I-4.
43. **Deep-water fishing at Fishing 80+ can raise a sea serpent carrying a treasure map, a message in a bottle or a special net** (stock, no shard exemption checked). A treasure map is never handed over directly.
44. **The Fisherman sells post-UOR aquarium goods** (fish bowl 6,312 gold, aquarium deeds 250,002 gold) with no era gate (`SBFisherman.cs:25-31`).

45. **Cow milking is ungated stock code and still works**; the help text no longer mentions it (whether it belongs in a UOR world is your call). Tailors sell cotton and flax at 102 gold but a bolt of cloth at 100 (stock pricing).
46. **The Britain Provisioner sells a plant bowl** (`SBProvisioner.cs:25`), a post-UOR item (with the Fisherman's aquarium goods, item 44).
47. **Carving another player's corpse works in Felucca and costs karma, plus a criminal flag on an innocent's corpse**; the Body parts topic states the rule without numbers. Intended for "without the griefing"?

48. **The Shipwright sells dragon-prow ship deeds at the same price as plain ones**; no source dates them to UOR, so the topic no longer mentions them. Decide whether they stay on sale.
49. **The communication-crystal 10-receiver cap may be later than UOR** (an uo.com Publish 7 note, September 2000, says crystals were revised then); the text follows the code.
50. **One house per account is a stock rule you kept "for now" on 2026-09-30, to be revisited in Beta 2b**: the house topics state it, so re-read them when it changes. The same goes for house decay (a 5-day manual refresh, `houseDecay.enable` true).
51. **Barkeepers' "latest news" only exists if staff post Town Crier entries**, and none exist; the Provisioner buys the Guild Deed back for 6,225 gold (not in the text).

52. **The shipped code refuses to drink any potion except explosion, Conflagration and Confusion Blast unless one hand is free.** A warrior with weapon and shield, or anyone holding a bow or another two-handed weapon, cannot drink a heal or cure potion. The era of that rule could not be confirmed online. The six potion topics (heal, cure, refresh, agility, strength, night sight) say so in one sentence each, because the code does it; if it should not apply, the shard needs a `RequireFreeHand` override and those sentences deleted.
53. **Melisande's Fermented Wine** (a later-era quest item derived from `GreaterExplosionPotion`) shows the explosion page; it is unobtainable here.

## Open points in the help text itself

- Discordance: the page describes what the code does (the owner ruled for Discordance, 2026-09-28); confirm it is final.
- The Magery page is long (about 16,000 characters, 9,700 of them the 64-spell reference).
- The Weaponsmith / trainer / hunting-advice lines are only as good as the code reading; each was audited against the code, none was tried in a game.
