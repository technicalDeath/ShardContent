# Carry weight: base 100, worn backpack 550

Owner, 2026-11-01. He asked how a player's carry limit is worked out and chose to raise it, mainly so new characters are not overweight so soon. He signed off on the plan below, with one change: keep the starting kits exactly as they are today. He then chose "exact: today's limit" over a single lower percentage. Data, no flag (like the small-house price).

## What changed

| | Before (stock UO:R) | Now |
| --- | --- | --- |
| Carry limit | 40 + 3.5 x Str | **100 + 3.5 x Str** (`carryWeight.base`, `carryWeight.perStrength`) |
| A player's own worn backpack holds | 400 stones | **550** (`carryWeight.playerBackpackMaxWeight`) |
| Bags, pouches, pack animals (1,600), bank | stock | unchanged |
| Overload penalty (`stamina.*`: 4-stone grace, then 5 + over/25 stamina a step, x2 running) | stock | unchanged, from the new limit |
| Starter weight budget | 85% of the limit | 85% of the **stock** limit (40 + 3.5 x Str), so every kit is what it was |

Limits by Strength: Str 10 75 -> 135, 40 180 -> 240, 50 215 -> 275, 54 229 -> 289, 80 320 -> 380, 100 390 -> 450. Equipped gear counts toward the carry limit but not the backpack.

## How it is built

- **Engine (ModernUO, uncommitted).** Two hooks, null by default:
  - `PlayerMobile.MaxWeightAdjust` (player, stock limit) -> limit, with `PlayerMobile.StockMaxWeight` for the stock sum.
  - `Backpack.PlayerMaxWeightAdjust` (player, stock most) -> most. It applies only to the backpack a player is wearing.
  - Test: `UOContent.Tests/Tests/Misc/PlayerCarryWeightHookTests.cs`.
- **Shard.** `CarryWeight.cs` (rules, the two hooks, `[CarryWeightStatus`, the client command) and the `carryWeight` section in `shard-rules.json`.
  - The rules are checked by `ShardRulesConfiguration`: base 0-400; perStrength 0-10 in steps of 0.1; backpack 0 (stock) or 400-1600.
  - `StarterWeightBudget` now weighs a new character against `StockMaxWeight`. Its audit line reads `... of stock limit 229 (carry limit 289)`.
- **Client (ClassicUO, uncommitted).** The era's status packet (version 3) has no carry limit, so the client works out the stock one itself (`7 x (Str / 2) + 40`).
  - The server sends extended command **0xB3** (base, then stones per Strength in tenths) at login, and again when the client asks with 0xB3 once its game scene is up.
  - The login copy alone did not reach the bar in the real client; the request is what made it work, as with the top bar's 0xA8.
  - `Game/Data/CarryWeight.cs` holds the values, and the status handler uses them. Stock servers never send it, so stock behaviour stays.
  - The server's sum is whole-number tenths too, so both sides agree.
- **Navrey (committed `670d4c999`, not pushed).** `Agent/CarryWeight.cs`, called each frame from `AgentHost`.
  - It wraps the 0xBF handler at runtime (as `Narrator` does) and reads the base and tenths from the whole packet.
  - It asks with 0xB3 once the world is up and puts the shard limit back in `WeightMax` after any status packet sets the stock one.
  - It clears on logout. A server that never answers leaves the stock sum.
  - It is in the farm build `bin/Lean13`, not yet in `bin/Debug`, which `Start-NavreySession` test sessions run. Rebuild that when no session has it loaded (`navrey-test` skill). Until then a test session's `maxWeight` is the stock sum.

## Evidence

| Check | Result |
| --- | --- |
| Engine hooks: stock without hooks (215, pack 400, bag 400); with hooks player 275, worn pack 550, bag in it 400, loose backpack 400, pack animal 1,600; Elf parity tests | pass (UOContent, 11 tests) |
| Shard unit tests: limits by Strength, stock defaults, backpack, validator, 0xB3 bytes, client sum = server sum, shipped config | pass; full shard suite 1,905/1,905 |
| Live (disposable host on port 2594, beside the bot farm): `[CarryWeightStatus` | `100 + 3.5 x Str; worn backpack holds 550`; admin Str 100 limit 450 |
| Live: Warrior Str 42 pushed to 248 | server message `Carrying stones / Max stones : 248 / 247` |
| Live: at 248 (within the 4-stone grace) | 4 steps, stamina 42 -> 42 |
| Live: at 252 (past the grace) | stamina 42 -> 32: 5 a step (two steps counted; the first command after turning around only turns) |
| Live: worn backpack above 400 (load 492) | a player's own drop is accepted |
| Live: worn backpack above 550 | refused: `That container cannot hold more weight.` |
| Live: Archer Str 54 starting kit | `load 326 -> 194 of stock limit 229 (carry limit 289)`. The bot Archers made this morning on the old build: `327 -> 194 of limit 229`. Same kit (74 Boards, 37 Feathers). |
| Real client (`player-client-shots`): new Archer | combat bar and Status window `194/289` (were `194/229`) |
| Real client: one stone over | message `290 / 289`, bar red `290/289`, Status `290/289` |
| Farm (2026-11-01, after the 21:48 redeploy): `[CarryWeightStatus` | `100 + 3.5 x Str; worn backpack holds 550`; Str 100 limit 450 (stock 390). The bots' state files still said 390: Navrey worked out the stock sum itself |
| Navrey with `Agent/CarryWeight.cs` (scratch build, one headless client on the farm) | state file `str=100 maxWeight=450` |
| Farm on `Navrey/bin/Lean13` (22:50, full client restart; read by the Watcher) | BotCarpAR `str 100, maxWeight 450` a few seconds after entering the world. The first reads after login show 390 until the 0xB3 answer arrives, which errs on the safe side |

Screenshots: `work/player-client/CarryArch/shots/20261101-191516-status-window.png`, `20261101-191603-overloaded.png`.
Live driver: `work/carry-weight/live_check.py`.

## State (2026-11-01)

- **Committed, not pushed:** ModernUO `614a0fda9` (hooks), ShardContent `1ab1bf8` (pin bumped to it), ClassicUO `80200c1df` (0xB3).
- **Live on the farm host** since the 21:48 redeploy.
- **Not deployed to dev.** The dev server's shard DLL and config are unchanged, and the new `cuo.dll` is not yet in `ClassicUO/bin/dist`.
- **Navrey** reads 0xB3 in `Agent/CarryWeight.cs`, uncommitted. It wraps the 0xBF handler at runtime the way `Narrator` does, asks once in the world, and puts the shard limit back each frame after a status packet. The farm runs it from `Navrey/bin/Lean13`, built by the Watcher.
- **To deploy to dev:**
  1. Run the normal deploy.
  2. Copy the rebuilt `cuo.dll`/`cuo.pdb` into `ClassicUO/bin/dist`, with a backup under `work/cuo-backups`.
  3. Add a README rules line.

## Deployed to dev (2026-11-03)

Pushed and deployed to dev with the progress-bar deploy (pin `67b29ab34`), after the snapshot
`work/save-snapshots/saves-20261103-121627-before-progress-bars-deploy`. The new `cuo.dll` is in `ClassicUO/bin/dist` and the README has a
Carrying line. Navrey `670d4c999` is pushed.
