# Bot farm

Many Navrey bots, one per profession, playing the shard unattended on a disposable host so quality-of-life problems show up without a person watching.
Findings land in `work/botfarm/notes.jsonl` (one line each, tagged with the bot and profession); `aggregate.py` folds them into `work/botfarm/report.md`.

## Run it

1. A disposable host with the server running (`New-DisposableHost.ps1 -Name farm`, then `Start-DevServer.ps1` for it). Auto account creation is on there.
2. Start the clients (about 440 MB each; the launcher stops when free memory falls under `--reserve-mb`):

   ```powershell
   python ShardContent\tests\scenarios\bot-farm\farm_launch.py --plan work\botfarm\plan-all.json --parallel 2 --reserve-mb 1100
   ```

   `plan-all.json` is a list of `{"name": "BotMaceA", "profession": 13}`. Shard profession ids: 8 Archer, 9 Bard, 10 Ranger, 11 Pure Mage, 12 Warlock,
   13 Mace Fighter, 14 Fencer, 15 Swordsman, 16 Blacksmith, 17 Carpenter, 18 Tailor, 19 Tinker, 20 Animal Tamer, 21 Fisherman, 22 Prospector, 23 Sorcerer.
3. Start the supervisor. It starts each bot's brain, restarts a dead client or brain, stops the lowest-priority bots if available memory falls under 450 MB,
   and writes `work/botfarm/dashboard.txt`, `metrics.jsonl` (one line per bot per minute) and `report.md` (every five minutes):

   ```powershell
   python ShardContent\tests\scenarios\bot-farm\supervisor.py --plan work\botfarm\plan-all.json --hours 8
   ```

`touch work/botfarm/<name>/pause` makes a bot's brain idle (for a human or a test script to use the character); delete the file to resume.

## Brains

| Brain | Professions | Does |
| --- | --- | --- |
| `hunter.py` | Mace Fighter, Fencer, Swordsman, Archer, Ranger, Bard | Fights what the server's monster table says it can beat, learns which kinds killed it, loots, bandages or drinks the Heal potion, buys arrows and bandages, banks. The bard also plays Peacemaking, Discordance and Provocation |
| `caster.py` | Pure Mage, Warlock, Sorcerer | The new-mage playtest bot (`../new-mage-playtest/mage_bot.py`) |
| `crafter.py` | Blacksmith, Carpenter, Tailor, Tinker | Learns the legacy craft menu by option text, makes the item that teaches most (`craft_data.json`), sells products, buys material and tools |
| `fisher.py` | Fisherman | Fishes at the lake south of Britain, cuts fish, cooks on a campfire |
| `miner.py` | Prospector | Mines the hills north of Britain, sells ore, drops weight when overloaded |
| `tamer.py` | Animal Tamer | Tames what `tame_data.json` says it can, uses Animal Lore, releases |

`bot_common.py` holds what every bot shares: the journal reader, notes, ghost-to-healer, bank, shop, sell, loot, travel in hops, overload handling and the status file.

## Generated data

`make_craft_data.py` reads the server's craft definitions into `craft_data.json`; `tame_data.json` was read from `ModernUO/Projects/UOContent/Mobiles` (MinTameSkill, hits, damage).
The monster table comes from `../new-mage-playtest/game_data.json`.

## Things the bots found about driving the shard (not about players)

- Navrey's `Client.items()` leaves immovable items out (campfires, dummies); the `items N` command lists them (`BotBase.ground_items`).
- The era's craft menus are filtered by skill and material, so option numbers move; match by text.
- Harvest, cooking and bandage repeat run on the server: a step cancels them.
- A ghost is offered resurrection when it walks into the healer's range, not while it stands there.
