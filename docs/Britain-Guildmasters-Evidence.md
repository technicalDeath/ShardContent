# Britain's missing guildmasters and trade vendors (2026-10-13)

Owner request, 2026-10-13: "update the spawn config data to add the missing guildmasters and verify they are in the world." The gap was recorded in `Help-Gumps-Findings.md` items 1, 2 and 31: stock ModernUO spawns a Thieves', Rangers' and Fishermen's Guildmaster only in other towns, and no plain Tinker or Miner in Britain, and world generation keeps only Britain's vendors.

## What was added

Five spawners in `data/world-generation/alpha2b/britain-vendor-overrides.json` (the shard's own Britain spawn file, listed in the manifest's `customSpawnerFiles`; stock spawn data is not touched). Each is one NPC, `count` 1, `homeRange` 0, `walkingRange` 5, the same shape as the stock vendors, with a fixed GUID (a name-based UUID, so the same ids come out every time) and a floor read from the map data.

| NPC | Where (x, y, z) | Why there |
| --- | --- | --- |
| `ThiefGuildmaster` | 1571, 1746, 15 | The middle room of the Bay Side Road warehouse in the south-east of Britain: a back-street warehouse, away from the banks, unlike the stock guildmaster, who stands in Buccaneer's Den (a Hot Zone) |
| `RangerGuildmaster` | 1584, 1565, 20 | The Cavalry Guild hall on River Road, which has no NPC and is the natural home of a ranger |
| `FisherGuildmaster` | 1441, 1760, -2 | The Britain docks, among the Fishermen |
| `Tinker` | 1427, 1650, 10 | Inside The Tinkers' Guild, which until now had only the guildmaster, who sells nothing |
| `Miner` | 1420, 1580, 30 | Beside the Miners' Guildmaster, so shovels and pickaxes can be bought |

Why the plain Tinker and Miner: they are the vendors, where the guildmasters only teach and take members (`BaseGuildmaster.IsActiveVendor` is false). The Backpack Ward vendor sale is for a plain `Tinker`, so the Ward could not be bought in the real world before; the Welcome guide's and README's lines about Tinkers selling and buying back Wards are now true.

Not spawned, deliberately: a Veterinarian (it is on the manifest's excluded list) and the other missing plain trades (Farmer, Rancher, Ranger, Vagabond, Beekeeper, Miller, Glassblower, StoneCrafter); the owner asked for the guildmasters, and the Tinker and Miner close the two gaps the findings called out by name.

## Code

- `Alpha2bWorldGenerationCommands.cs`: a new subcommand `[Alpha2bWorldGen addspawners CONFIRM-UOR-FELUCCA`. A world that was generated earlier and is in use cannot be regenerated to gain a spawner, and `apply` refuses a non-fresh world. `addspawners` adds only the canonical spawners the world lacks (the audit's own test: the GUID once, at its place), through the same spawner pass generation uses, saves only when every canonical spawner is then exact, and prints the full audit. Run again with nothing missing it reports so and does nothing.
- `tests/BritainGuildmasterSpawnTests.cs` (10): each missing type is spawned exactly once in Britain; every override is inside Greater Britain on Felucca; GUIDs and places are unique; each new spawner holds one NPC that stays put; no override is a type the era excludes; the file is still in the manifest.
- Probe, test host only: `tests/scenarios/alpha3-tools/TestOnlyProbe.cs` gained `[TestOnlyPartyInvite`.

## Evidence

Counts come from `[global count where <Type>` and `[Alpha2bWorldGen audit`.

| # | Case | Result |
| --- | --- | --- |
| 1 | Preview on an empty disposable world (accounts index only, as the runbook's reset) | UOR / Felucca; 1,551 spawners (was 1,546); 0 roots |
| 2 | `apply CONFIRM-UOR-FELUCCA` | 13,970 decorations, 385 teleporters, 1,551 spawners, 410 signs, 1,215 doors (130 existing); audit passed; saved |
| 3 | Counts in that world | exactly 1 each of ThiefGuildmaster, RangerGuildmaster, FisherGuildmaster, Tinker, Miner; TinkerGuildmaster and MinerGuildmaster still 1 each; 17 guildmasters in all (was 14) |
| 4 | After a restart from the saved world: `audit` | passed: 410 signs, 385 teleporters, 1,551 spawners, 1,345 doors, 9 moongates, 63 Khaldun items; counts unchanged |
| 5 | Convergence `rerun` | 0 decorations, 0 doors (1,345 existing); audit passed; counts unchanged |
| 6 | Standing at each spawner in that world | an NPC is on each spot (names are random per spawn) |
| 7 | Real client, that world: each guildmaster addressed by name with "join" | all three answer "You are too young to join my guild..." (the stock age gate for a new character); Tinker's buy list shows clocks, nails, gears, hinges and tools; Miner's shows bags, candles, torches, lanterns, a pickaxe (25 gp) and a shovel (12 gp) |
| 8 | **The real dev world** (`ModernUO/Distribution`, snapshot `work/save-snapshots/saves-20261013-130854-before-guildmasters`): `audit` before | **failed: 1,543/1,551**: the five new ones plus three that were already missing (the Mongbat and Orc spawner at 1750,1250, the Corpser group at 2000,1210 and a reagent spawner at 1938,1220: the 1,543/1,546 recorded in `Furnisher-Evidence.md`, never explained) |
| 9 | `addspawners` on the real dev world | added 8 spawners, replaced 3 stale ones (a spawner of the same type at the same place), saved; the audit passed with all 1,551 |
| 10 | A restart of the real dev world, then `audit` and the counts | audit passed; 1 of each new type; 17 guildmasters; `addspawners` a second time: "all 1551 canonical spawners are already in the world; nothing to add" |

The audit failure in case 8 was a difference in the dev world, as `Furnisher-Evidence.md` said: it was generated before three spawners were added to the canonical set. It is now repaired and the dev world passes the audit for the first time since then.

## Effects to know

- **Player theft is now possible.** With a Thieves' Guildmaster in Britain a character can join the guild (500 gold; at least 7 days old, 2 days played, not Young, no murder counts, Stealing 60.0) and then steal from other players, under the shard's existing rules (Criminal Intent or a lawful target under Safe World, bank protection areas, Backpack Wards, Hot Zones, Knocked Out). This is the owner's instruction carried out, and it is also what the Alpha 2 theft protection was built for; but it is a change players will notice, so it belongs in the release notes.
- **Help text.** The Stealing and Snooping pages had been written for a world with no guildmaster ("you cannot steal from other players here"). They were restored from the audit's saved paragraphs (`help-content/thieves.audit.md`, OWNER 1), plus one paragraph on how to join; deployed and checked in the real client.
- **What they teach** (`SetSkill` in each class; a guildmaster's lesson is a third of its skill, from 60 up): the Thieves' Guildmaster Detecting Hidden (75 to 98, which closes the gap in `Help-Gumps-Findings.md` item 31: Britain had no Detecting Hidden trainer), Hiding, Lockpicking, Snooping, Poisoning, Stealing, Fencing, Stealth and Remove Trap; the Rangers' Guildmaster Animal Lore, Camping, Hiding, Magic Resist, Tactics, Archery, Tracking, Stealth, Fencing, Herding and Swords; the Fishermen's Guildmaster Fishing. The Welcome guide's Training page used to name a plain Ranger for Detecting Hidden; that NPC is still not spawned, the Thieves' Guildmaster fills the role, and the guide now has a **Who teaches what** page (Skills tab) listing every trainer in Britain by what each teaches (below).
- **Open question: was there a Rangers' Guildmaster in UO:R?** I could not confirm it from an online source (the usual wikis refuse automated requests, and a general search found nothing on a Rangers' Guild in Ultima Online). The stock ModernUO server has a `RangerGuildmaster` that it spawns in Skara Brae, not Britain, and the NPC class carries no era marker, so its presence in stock data does not date it. The owner asked for the missing guildmasters, so one stands in Britain's Cavalry Guild hall, and the help text names it (the Rangers' lines on the Tracking, Camping, Hiding, Stealth, Archery, Tactics and Resisting Spells pages and the Who teaches what page). If it did not exist in April 2000 it is one spawner entry in `britain-vendor-overrides.json` and those text lines to remove; nothing else depends on it.
- **Existing worlds.** A new world gets all five from `apply`; a world in use gets them with `addspawners`. A world whose Britain spawners are later removed by hand loses them until `addspawners` is run again.

## Help text for the new NPCs

- **Who teaches what** (Skills tab of the Welcome guide, `WelcomeGuide.GettingStarted.cs`, `TrainersTopic`): the shops and workshops with the skills each teaches, then the guildmasters, read from the NPC classes (a town NPC's menu offers any skill it has at 60.0 or more; only a Healer limits itself to four). The Training page keeps the rules (one third of the NPC's skill, 1 gold per 0.1 point) and a "Finding a trainer" line pointing to it. Stealth is taught only to someone with 80.0 Hiding; Remove Trap needs 50.0 in Lockpicking and in Detecting Hidden; a few trainers know some other skill only part of the time.
- **Skill pages** (`data/help/skills.json`): a line on each of Tinkering, Mining, Lockpicking, Remove Trap, Archery, Tactics, Fencing, Resisting Spells, Tracking, Camping, Hiding, Stealth, Poisoning, Snooping, Stealing and Detecting Hidden saying which Britain NPCs teach it and the range a lesson gives.
- **Item pages** (`data/help/items.json`): shovels, Tinker's Tools and pickaxes had been written as "no shopkeeper sells them"; the Tinker sells the tools (about 7 gold) and the Miner and Tinker sell a Shovel (about 12) and a Pickaxe (about 25).
- Checked in the real client on a disposable host: the Skills tab, the Who teaches what page and its Guildmasters section, and the Tracking page's new line. Tests: `GuideGettingStartedTests`, `WelcomeGuideTests` and `HelpCatalogTests` (the page lengths, the topic order, the gating).

## Files

`data/world-generation/alpha2b/britain-vendor-overrides.json`, `src/BritanniaRenaissance.Content/Alpha2bWorldGenerationCommands.cs`, `tests/BritainGuildmasterSpawnTests.cs`, `tests/scenarios/alpha3-tools/TestOnlyProbe.cs`, `data/help/skills.json` (Stealing, Snooping), `docs/Alpha-2b-World-Generation-Runbook.md`, `docs/Help-Gumps-Findings.md`.
