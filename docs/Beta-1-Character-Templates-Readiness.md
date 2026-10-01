# Beta 1: character templates readiness

**Decision:** Ready and **published** (owner sign-off 2026-10-01: the era tree without Field Medic and Battle Mage, "publish when verified"). The rebuilt player client (`cuo.dll`) and the shard profession file (`BritanniaRenaissance.Prof.txt`) are in `ClassicUO/bin/dist`; the shard file is deployed to the dev distribution and the deployed `modernuo.json` names it. There is no feature flag. This closes Beta 1 scope item 4; the live-client 120-stat test (item 5) remains.

## Reused accepted evidence
- The Alpha 3 starting-stats rule (120 points, 30 minimum) and the starter-gear grants are unchanged and apply to every profession by its stat points and skills.
- Advanced creation: its skill list shares the era rule (it was already era-filtered), and its stat sliders now assign exactly 120 points (30 to 60 each, total fixed at 120, starting 40/40/40); the server keeps that choice as chosen. This fixed the owner's report that the screen allowed only 90.

## Current-source review
Full survey, research, design and corrections are in [the audit](Beta-1-Character-Templates-Audit.md). Summary: the server read `UOData/Prof.txt` before its own UOR file, so it defined Necromancer, Paladin, Samurai and Ninja and granted them. Research found that the era (August 1999 publish, in force through Renaissance) used an Adventurer and Merchant folder tree of professions, three skills (the era's 100 skill points, scaled by the shard to 120 with no skill above 50) and 80 stat points each, not Warrior, Mage and Blacksmith. The shard now owns one profession file with that tree (16 professions, IDs 8 to 23), shipped to the server and the client, selected by one new ModernUO setting (`characterCreation.professionFile`). The client supports two folder levels, hides later-era entries by an era rule shared with the Advanced skill list, and uses the original card art from the client's own data. The server stops after startup if the shard file is not in use.

## New verification
Shard suite 327/327, ModernUO Skill/Pet/Elf/Profession/Character subset 205/205, all ClassicUO unit tests 210/210. Live on a disposable host: 60/60 (the offered tree and Advanced list on the real screens, all 16 professions' skills and stats, an Elf Ranger, forged packets for profession 1 and 4 to 7, gear). Details in the audit.

## Gate and validator
No flag. `modernuo-era-gates.json` gains `characterCreation.professionFile`; the deploy copies the profession file to `Distribution/Data/BritanniaRenaissance/Professions/Prof.txt`. `Get-ShardStatus.ps1` compares the four copies of the file (source, deployed, player client dist, Navrey): all four match.

## Readiness limits
- **The values come from one community reconstruction** of the era `Prof.txt` (UO Second Age forum), not an Origin file; names and structure agree with the 1999 publish notes. Each value is one line in `ShardContent/data/professions/Prof.txt` and can be changed there. Field Medic and Battle Mage were left out by the owner. The fourth Warrior-folder entry the 1999 notes call "Bard" has no source values and is not built.
- **Card art:** Adventurer (rider) and Merchant (rings) are guesses; the rest match the symbols in the 1999 notes. The client can load pictures of its own later.
- **The published client was not played.** `cuo.dll` was built and confirmed to contain the new loader, but the screens were verified through Navrey, which builds them with the same code. Open the player client at the creation screen once and click through the folders, including Back.
- **Player text** (names and tooltips) is in the audit and needs the owner's review with the release.
- **Existing characters are unaffected.** Only creation changes.
- **Players need the new client files.** A client without `BritanniaRenaissance.Prof.txt` still hides the later-era templates (the era rule) but shows the UO folder's own list, and the server treats a creation packet for an undefined profession ID (1 to 7, such as the later official Warrior) as Advanced with the skills in the packet.
- **Committed and pushed 2026-10-01** to the owner's forks: ModernUO 5463a9449 (gain hook) and 8867dda13 (profession-file setting), ShardContent e48fb68 (gain curve, pin bump) and 4cdbca1 (templates), ClassicUO 46f02eca9, Navrey e2a20335e. The ClassicUO `README.md` and `ROADMAP.md` edits are not part of this work and stay uncommitted. The pinned ModernUO commit is bumped to 8867dda13.
- **The 1999 professions differ from the Alpha 3 starter-package audit's template rows** (which quoted Warrior, Mage and Blacksmith); starter grants still follow from skills, so the Alpha 3 rules apply unchanged.
- Two UOContent tests fail on ModernUO HEAD independent of this item (see the Elf audit).
