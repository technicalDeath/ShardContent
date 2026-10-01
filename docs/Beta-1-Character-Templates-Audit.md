# Beta 1 item 4: era-appropriate character templates, survey, plan and evidence

Roadmap: [Beta 1](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 4. Readiness record: [Beta-1-Character-Templates-Readiness.md](Beta-1-Character-Templates-Readiness.md).

**Status: closed 2026-10-01. Design signed off by the owner, built, verified, and the client published to `ClassicUO/bin/dist`.**

## Decision record (owner, 2026-10-01)

The first plan kept Warrior, Mage and Blacksmith and added four playstyle templates. Two rulings changed it, in order:

1. The templates should use **stock ModernUO skills**, and new ones should mirror them. I built that (Tactics 50 / Healing 45 / Swords 5 and so on), and the owner then said those values did not look right and asked for UOR information from online sources.
2. After the research below, the owner chose **the era tree, without Field Medic and Battle Mage**, and accepted building on the community source with its caveat flagged.

Standing rulings that still apply: templates are shown by a **rule** (a template appears only if every skill it grants is allowed by the server's feature flags), a creation packet naming a profession the shard does not define falls back to Advanced (stock), and the client is published when verified.

## What the era actually had (research)

- **Structure.** The 25 August 1999 publish replaced the old character templates with three choices, **Adventurer, Merchant and Advanced**. Adventurer holds Archer, Magician and Warrior folders; Merchant holds Craftsman and Tradesman folders; each folder holds professions with a symbol ([uo.com, Publish 25 Aug 1999](https://uo.com/wiki/ultima-online-wiki/technical/previous-publishes/1999-2/1999-07-25th-august/)). The Renaissance publish (27 April 2000) does not mention character creation, so no change to that tree is recorded by then ([uo.com, Renaissance publish](https://uo.com/wiki/ultima-online-wiki/technical/previous-publishes/2000-2/2000-publish-05-27th-april/)).
- **Values.** A UO Second Age forum thread posts a full reconstruction of the era `Prof.txt` ([UO Second Age forum](https://forums.uosecondage.com/viewtopic.php?t=10088)): each profession is **three skills totalling 100 points and 80 stat points**. The shard scales the skill points to 120 (see below). The shard scales the skill points to 120 (see below).
- **Caveat.** That thread is a community reconstruction, not an Origin file. Its names and structure agree with the 1999 publish notes, but individual values are not independently verified. The 1999 notes list a fourth Warrior-folder entry called "Bard" that has no values in the thread, so it is not built. Field Medic and Battle Mage exist in the source and were removed by the owner. No source found says when the single-level Warrior, Mage and Blacksmith screen replaced the tree; the later official values (four skills at 30) and ModernUO's stock UOR values (50/45/5) do not match the tree.
- **Art.** The original card pictures are still in the client's `gumpartLegacyMUL.uop` (IDs 5545 to 5592, 60x60 medallions) and match the symbols named in the 1999 notes: bow and arrow, lute, anvil, saw, fencer in a lunge, scissors, gears, scales, horse, fish, pack mule, feathered-cap head, flaming sword, helm, crossed swords, mace arm, wizard hat. Card art is assigned from those; two (Adventurer, Merchant) are best guesses.

## Current behavior before this item (verified in source, data and a live probe)

**Client (ClassicUO fork, client 7.0.117.0).** The loader read `Prof.txt` from the player's UO data folder, which lists Samurai, Ninja, Paladin, Necromancer, Warrior, Mage and Blacksmith. The template screen showed all of them with no era filter (only Samurai and Ninja showed a message when picked). The loader supported one level of folders. The Advanced skill list already filtered by the server's feature flags.

**Server (ModernUO).** The server read `prof.txt` with `Core.FindDataFile`, which searches the data directories (here `UOData`, the same official client file) **before** its own UOR profession file. The data directories are an unordered set, so no file could be put first. A live probe (one character per profession ID 1 to 7) showed the server **defined and used Necromancer, Paladin, Samurai and Ninja** (their official skills with the later-era ones dropped, the Alpha 3 stat allocator on their official stats, and their stock profession-gear branches), and gave Warrior, Mage and Blacksmith four skills at 30. Earlier Alpha 3 audit text quoting "Warrior Tactics 50, Healing 45, Swords 5" describes the stock `Data/Professions/None` file, which this server never used here.

## Design (as built)

1. **One shard-owned profession file.** `ShardContent/data/professions/Prof.txt` defines the era tree once: two top-level folders (Adventurer, Merchant), five sub-folders, 16 professions with IDs 8 to 23, and the built-in Advanced. IDs 1 to 7 stay undefined. The deploy copies it to `Distribution/Data/BritanniaRenaissance/Professions/Prof.txt` and sets the ModernUO setting `characterCreation.professionFile` (in `modernuo-era-gates.json`). The client ships the same file beside its executable as `BritanniaRenaissance.Prof.txt`, which wins over the UO folder's `Prof.txt`.
2. **ModernUO: one narrow setting.** `ProfessionInfo` (static constructor) uses the file named by `characterCreation.professionFile`, relative to the server's base directory, before it searches the data directories. Unset, it behaves as stock.
3. **Era rule in the client**, shared by both screens (`CharCreationEra`): a later-era skill needs its expansion's flag; a profession is offered only when all its skills are in era; a folder only when one of its professions is, at any depth. The Advanced skill list uses the same predicate.
4. **Two-level folders.** The loader now registers sub-folders with their own children and a parent link; the first screen lists top-level entries only; Back goes up one level. Cards show a profession's own name and `DescText` tooltip when it has no string-table entry (multi-word names are quoted in the file).
5. **120-point stats.** Every profession (and Advanced) spreads 120 points in proportion to its own stat points above 10, 30 minimum and 60 maximum per stat (Archer 54/33/33, Pure Mage 48/33/39, Prospector 57/33/30). The old per-name table is gone.
6. **Boot check.** After the server has started, the server verifies that IDs 8 to 23 are defined and 1 to 7 are not, and stops itself otherwise. It must run after startup: ModernUO loads the profession file once, in a static constructor, resolving aliased skill names (Swordsmanship, Parrying, Mace Fighting, Resisting Spells, Bowcraft, Inscription) through the skill table, so touching it during `Configure` silently dropped every profession using one. Any other early use of `ProfessionInfo` would do the same.

## The professions

Each is three skills totalling **120 points**: the era's 100 points scaled proportionally, with no skill above 50 (ModernUO's stock creation rule rejects a higher starting skill), so Advanced (four skills at 30) and every profession start with 120 skill points. Where the cap bites, the 50/25/25 professions became 50/35/35, and Bard, Carpenter, Tailor, Fisherman and Blacksmith became 50/50/20 (their small third skill rose to 20; the era Blacksmith's Tinkering 0 became 20). Warlock, Prospector and Sorcerer scale exactly. The era values are shown in brackets. Starting gear is not special-cased: stock and Alpha 3 starter grants follow from the skills.

| ID | Folder | Profession | Skills | STR / DEX / INT (template, then 120-point spread) |
| ---: | --- | --- | --- | --- |
| 8 | Adventurer / Archer | Archer | Archery 50, Bowcraft 35, Lumberjacking 35 (era 50/25/25) | 50/15/15, then 54/33/33 |
| 9 | | Bard | Musicianship 50, Provocation 50, Archery 20 (era 50/40/10) | 50/15/15, then 54/33/33 |
| 10 | | Ranger | Archery 50, Tracking 35, Animal Taming 35 (era 50/25/25) | 50/15/15, then 54/33/33 |
| 11 | Adventurer / Magician | Pure Mage | Magery 50, Evaluating Intelligence 35, Resisting Spells 35 (era 50/25/25) | 40/15/25, then 48/33/39 |
| 12 | | Warlock | Swordsmanship 48, Magery 48, Resisting Spells 24 (era 40/40/20) | 40/15/25, then 48/33/39 |
| 13 | Adventurer / Warrior | Mace Fighter | Mace Fighting 50, Parrying 35, Anatomy 35 (era 50/25/25) | 50/15/15, then 54/33/33 |
| 14 | | Fencer | Fencing 50, Parrying 35, Anatomy 35 (era 50/25/25) | 50/15/15, then 54/33/33 |
| 15 | | Swordsman | Swordsmanship 50, Parrying 35, Anatomy 35 (era 50/25/25) | 50/15/15, then 54/33/33 |
| 16 | Merchant / Craftsman | Blacksmith | Blacksmith 50, Mining 50, Tinkering 20 (era 50/50/0) | 50/15/15, then 54/33/33 |
| 17 | | Carpenter | Carpentry 50, Lumberjacking 50, Bowcraft 20 (era 50/40/10) | 50/15/15, then 54/33/33 |
| 18 | | Tailor | Tailoring 50, Tracking 50, Healing 20 (era 50/40/10) | 50/15/15, then 54/33/33 |
| 19 | | Tinker | Tinkering 50, Mining 35, Lumberjacking 35 (era 50/25/25) | 50/15/15, then 54/33/33 |
| 20 | Merchant / Tradesman | Animal Tamer | Animal Taming 50, Tracking 35, Animal Lore 35 (era 50/25/25) | 50/15/15, then 54/33/33 |
| 21 | | Fisherman | Fishing 50, Cooking 50, Camping 20 (era 50/45/5) | 50/15/15, then 54/33/33 |
| 22 | | Prospector | Mining 48, Lumberjacking 48, Hiding 24 (era 40/40/20) | 55/15/10, then 57/33/30 |
| 23 | | Sorcerer | Alchemy 42, Inscription 42, Magery 36 (era 35/35/30) | 40/15/25, then 48/33/39 |

Advanced is built into the client and unchanged: three skills chosen from the era-filtered list, the player's stat choices spread to 120.

**Card art** (client gump IDs): Adventurer 5547 (rider with lance, a guess), Merchant 5571 (rings, a guess), Archer folder and Archer 5551, Magician folder and Pure Mage and Sorcerer 5569, Warrior folder 5587, Craftsman folder and Carpenter 5559, Tradesman folder 5583, Bard 5553, Ranger 5575, Warlock 5585, Mace Fighter 5567, Fencer 5561, Swordsman 5577, Blacksmith 5555, Tailor 5579, Tinker 5581, Animal Tamer 5549, Fisherman 5565, Prospector 5573.

**Player text for review with the release.** Tooltips: Archer "Archers fight at range with a bow and make their own arrows."; Bard "Bards play music to provoke and inspire, with a bow for company."; Ranger "Rangers hunt with a bow, track their quarry and tame animals."; Pure Mage "Pure mages master magic and the knowledge that guards against it."; Warlock "Warlocks blend swordplay with spellcasting."; Mace Fighter "Mace fighters crush with maces and staves and hold a shield."; Fencer "Fencers fight with quick piercing weapons and hold a shield."; Swordsman "Swordsmen fight with blades and hold a shield."; Blacksmith "Blacksmiths mine ore and forge weapons and armor."; Carpenter "Carpenters cut wood and build furniture and chests."; Tailor "Tailors sew clothing and leather armor."; Tinker "Tinkers build tools, keys and gadgets."; Animal Tamer "Animal tamers train wild creatures as companions."; Fisherman "Fishermen catch fish and cook them."; Prospector "Prospectors gather ore and lumber."; Sorcerer "Sorcerers brew potions, scribe scrolls and cast spells." Folders: Adventurer, Merchant, Archer, Magician, Warrior, Craftsman, Tradesman, each with a one-line tooltip (see the file).

## Work breakdown

- **ShardContent:** `data/professions/Prof.txt`, `ShardProfessions` (IDs and names), `Alpha3StartingStats` (proportional spread), boot check in `EraGateConfiguration`, deploy copies the file, `modernuo-era-gates.json` setting, tests (`ShardProfessionsTests`, `Alpha3StartingStatsTests`).
- **ModernUO:** `ProfessionInfo` reads `characterCreation.professionFile`.
- **ClassicUO:** `CharCreationEra`, nested-folder loader and screen, shard file and `DescText`, tests (`CharCreationEraTests`), rebuilt `cuo.dll` published to `bin/dist` with the shard file beside it.
- **Navrey:** the same client changes, `chartemplates` (prints the offered tree) and `charskills` probes, `createcharacter` accepts any profession ID 0 to 255 and later-era skill IDs up to 57 for forged tests, `New-TestCharacter.ps1` follows, the csproj copies the shard file beside the build output.
- **Tooling:** `Get-ShardStatus.ps1` compares the four copies of the profession file.

## Verification evidence (2026-10-01)

**Unit tests.** Shard `ShardProfessionsTests` (file defines exactly IDs 8 to 23 and none of 1 to 7; names and order; Field Medic and Battle Mage absent; the era skills and stats for each profession; three UOR skills totalling 120 (the era's 100 scaled, none above 50) and 80 stat points; the folder tree, parents before children, every profession reachable once; folders invisible to the server parser; text and art on every card; every profession's 120-point spread within 30 to 60), `Alpha3StartingStatsTests`; ClassicUO `CharCreationEraTests` (later-era professions hidden under UOR flags and back under AOS or SE, flat and nested folders, the Advanced list). Full results: Shard suite 327/327, ModernUO Skill/Pet/Elf/Profession/Character subset 205/205, all ClassicUO unit tests 210/210.

**Live, disposable host with the shard file in use** (`tests/scenarios/templates/templates_live.py`, 60/60 passed):
- The real creation screens (built by Navrey the way the client builds them) offer exactly: Adventurer [Archer [Archer, Bard, Ranger], Magician [Pure Mage, Warlock], Warrior [Mace Fighter, Fencer, Swordsman]]; Merchant [Craftsman [Blacksmith, Carpenter, Tailor, Tinker], Tradesman [Animal Tamer, Fisherman, Prospector, Sorcerer]]; Advanced. No Necromancer, Paladin, Samurai, Ninja, Field Medic or Battle Mage.
- The Advanced skill list has 47 skills, including Alchemy, Archery, Magery and Swordsmanship, and none of Necromancy, Chivalry, Focus, Bushido, Ninjitsu, Spellweaving, Mysticism, Imbuing or Throwing.
- Each of the 16 professions created with exactly its scaled 120-point skills and its proportional 120-point stats (Archer 54/33/33, Pure Mage 48/33/39, Prospector 57/33/30, and so on). An Elf Ranger created the same way.
- Forged packets for profession 1 (the later official Warrior) and 4 to 7 (naming Necromancy, Chivalry, Focus, Bushido and Ninjitsu): a valid ordinary character with no later-era skill or gear and stats 42/42/36.
- Gear follows the skills: Archer a bow, arrows and a leather tunic; Fencer a kryss, wooden shield and studded armor; Mace Fighter a club and shield; Pure Mage a spellbook, robe and hat; Blacksmith an apron.
- Server boot check: "Validated shard character-creation templates" at startup; with the setting removed from a host's configuration the server logs the error and stops by itself (negative test, run earlier with the same code path).

**Found and fixed during the work.** (1) The first boot check ran before the skill table existed and silently dropped five templates (see Design 6). (2) Multi-word names such as "Pure Mage" showed as "Pure" on the cards because the client's parser reads an unquoted name as one word; names are now quoted. (3) The server read the client's official `Prof.txt` first and defined the later-era templates; the shard file and setting fix it.

**Test-tooling notes.** `createcharacter` sends any profession ID (0 to 255), `New-TestCharacter.ps1` follows, Navrey copies the shard file beside its build output, `Get-ShardStatus.ps1` has a profession-file section, and a cycle script must guard `Stop-NavreySession`, `Stop-DevServer` and `Remove-DisposableHost`, which throw when there is nothing to stop.

## Advanced stat points (owner report, 2026-10-01)

The owner found the Advanced screen let a player assign only 90 stat points. Cause: the client's Advanced stat sliders are hard-coded to a 90-point total (60/15/15, 10 to 60 each), and the server then rescaled whatever was chosen to 120, so the player never assigned the 120 directly. Fix: the Advanced sliders are now **30 to 60 each with a fixed total of 120, starting at 40/40/40** (`CharCreationEra.AdvancedStat*`, mirroring the server rule), and the server **keeps an exact 120-point choice as chosen** (30 to 60 in each stat); an old-style 90-point packet or an out-of-range choice is still rescaled in proportion to 120. Verified live on the real screen (`charstats`: range 30-60, start 40/40/40, total 120 holds as sliders move to their limits) and by creation: 60/30/30, 40/40/40 and 30/30/60 are kept exactly, a 60/15/15 packet becomes 55/33/32, an out-of-range 61/30/29 becomes 47/37/36 (120, 30 minimum), and the Archer template is unchanged. Tests: `Alpha3StartingStatsTests` (exact choices kept, invalid ones rescaled) and `CharCreationEraTests` (the stat rule). Observation, not changed: the Advanced skill sliders are still the client's four skills at 30 (120 skill points, 0 to 50 each), where the era Advanced was three skills totalling 100; the server accepts either.

## Skill points scaled to 120 (owner request, 2026-10-01)

The owner asked whether the templates and Advanced both give 120 skill points. Advanced did (four skills at 30); the templates gave the era's 100. The owner chose to scale the templates proportionally to 120 while keeping every skill at 50 or less (the stock cap), rather than raising the cap or leaving them at 100. Resulting values are in the table above. Verified: the profession file loads (server boot check passes), all 16 professions created live with exactly these skills (60/60), and a Ranger created through the real screens starts with Archery 50, Tracking 35, Animal Taming 35.

## Skill points scaled to 120 (owner request, 2026-10-01)

The owner asked whether the templates and Advanced both give 120 skill points. Advanced did (four skills at 30); the templates gave the era's 100. The owner chose to scale the templates proportionally to 120 while keeping every skill at 50 or less (the stock cap), rather than raising the cap or leaving them at 100. Resulting values are in the table above. Verified: the profession file loads (server boot check passes), all 16 professions created live with exactly these skills (60/60), and a Ranger created through the real screens starts with Archery 50, Tracking 35, Animal Taming 35.

## Out of scope

Item 5 (the live-client 120-stat test through the real creation screens), the fourth Warrior-folder "Bard" the 1999 notes mention, Field Medic and Battle Mage, new art, changing starting gear rules, the starter-package economy, skill or stat rules.

## Risks

The values rest on one community reconstruction; each is a single line in one file. The file not being found is turned into a loud startup failure by the boot check. The era filter reads the server's locked-feature flags, which must already be known when the creation screen opens; the live probe checks that on a real login.
