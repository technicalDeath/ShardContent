# Vendor stock: 30-minute restock and a larger dungeon kit

**Owner, 2026-11-02:** "Increase the number of potions at shops, and any other provisions preventing a bot from going to dungeons, and have shops restock every 30 minutes instead of 60."

## What it does

- **Restock:** every vendor restocks after 30 minutes, not the stock hour (`vendorStock.restockMinutes`).
- **Stock:** the lines below start at the stock list's amount times the multiplier (`vendorStock.stockMultipliers`). A raised line never halves below that amount. It still doubles when it sells out, up to the engine's 999.

| Item | Multiplier | Per shop (stock) | Why |
| --- | --- | --- | --- |
| Lesser Cure potion | x4 | 40-80 (10-20) | the dungeon kit takes 15; near Britain the bots know 4 sellers |
| Lesser Heal potion | x3 | 30-60 (10-20) | the kit takes 10; 7 sellers |
| Refresh potion | x2 | 20-40 (10-20) | the kit takes 2; rarely short |
| Bandage | x10 | 200 (20) | the kit takes 50; the bots know 1 seller near Britain |
| Arrow, Bolt | x5 | 100 (20); 150-300 at a variety dealer (30-60) | an archer's trip needs 60 |

The kit is `task_core.KIT` (10 Heal, 15 Cure, 2 Refresh, 50 bandages); an archer's trip also needs 60 arrows (`first_trip.trip_kit_ok`). Before the change, the bots' logs held 276 "still short of orange potion", 172 kits short of Heal and 25 short of bandages; the 20 core fighters each want a kit.

Restock is lazy in the engine: a vendor restocks when someone opens its buy list and the interval has passed. Vendors build their lines at world load, so amounts reset to these figures at every server start. The doubling a busy shop earns is lost on a restart, which is why the starting figures matter.

## How it is built

| Part | Where |
| --- | --- |
| Engine hooks | ModernUO `30e6b6e7b`: `GenericBuyInfo.StockAmountAdjust` (a line's starting stock from its type and amount; a changed line keeps it as `MinAmount`, the floor of `OnRestock`'s halving) and `BaseVendor.RestockDelayOverride` |
| Shard | ShardContent `ae95d91`: `VendorStock.cs` (`vendorStock` in `shard-rules.json`, data, no flag); validator in `ShardRulesConfiguration`; `[VendorStockStatus` (GameMaster) |
| Tests | `tests/VendorStockTests.cs`: the source amounts, every configured name is a real item type, other lines and the 999 ceiling stay stock, validation, and a raised line doubling on a sell-out and never halving below its raised stock. Full suite 1,945 passed |

## Where it is live

- **Farm host** (`work/hosts/farm`), from 2026-11-02 20:47:
  - **Deploy:** `work/vendor-stock/deploy_farm.py`, which copies the two DLLs and adds only the `vendorStock` section to the farm's own `shard-rules.json`.
  - **Rollback:** saves snapshot `work/save-snapshots/farm-saves-20261102-204716-before-vendor-stock`, old DLLs and config in `work/hosts/farm/Assemblies-backup-20261102-204716-vendor-stock`.
  - **Startup:** clean (shard rules and era gates loaded, `Listening: 127.0.0.1:2593`, no errors).
- **Dev:** not deployed. Deploying needs three steps:
  1. Bump the pin to `30e6b6e7b` in `shard-rules.json`, `world-generation.json` and `Alpha2bWorldGenerationConfigurationTests.cs`.
  2. Rebuild `UOContent` into `Distribution`.
  3. Run the standard deploy, then add a README rules line.
- **Other sessions' work:** this farm build carries their uncommitted engine and shard edits (action progress bars, drag into hands). Their flags are off, and the farm's config does not name them.

## Live results

| When | Observation |
| --- | --- |
| 2026-11-02 20:47 | Farm server back on the build; bots logging in through the night chain's supervisor |
| 20:49:20 | The stock is live. Healer Caitrin's buy list (BotHealAdvR's client log): `x40 Red Potion`, `x60 Yellow Potion`, `x200 Clean Bandage`; the stock list says 20, 20 and 20 |
| 20:51 | BotHealAdvR and BotWarAdvR: "the dungeon kit is short (orange potion, yellow potion)" with 60 Heal on the shelf |
| 20:51:22-28 | The restart's login rush: the 13 clients relaunched together reached the character list and dropped, several times each. The supervisor relaunched them at 20:51:35, but the server logged no new login from them |
| 20:55 | The 13 clients restarted one every 25 s, by checked PID (`work/vendor-stock/relaunch_dead.py`) |

**The kit shortage was in the bots, not only on the shelves.** The resupply (`errands.do_resupply`) passed `shop_at` the amount to buy (`full - carried`), but `shop_at` takes the amount to own and buys the target minus what the pack holds. A half-full kit asked for less than it already carried, so it bought nothing. BotHealAdvR held 6 of 10 Heal: it asked for 4, owned 6, and bought none. With 9 of 15 Cure it asked for 6, owned 9, and bought none at three alchemists. Ordinary restocks barely showed the fault: with 0-2 carried, the amount to buy is nearly the target. The bot-farm fix passes the target (`test_kit_topup`), and `KIT_RETRY_S` drops to 1,800 s to match the 30-minute restock.

| 21:20-21:21 | The 17 core fighters' brains restarted on the kit fix (bf47041); the kit rest the bug had set was cleared |
| 21:24:14-42 | **First full kit.** BotFairSwordNR bought 5 Heal and 2 Refresh at the healer, then 7 Cure at an alchemist. Its pack: 15 Cure, 10 Heal, 3 Refresh, 50 bandages, every kit mark met. The resupply ended "done" in 2.9 min with no "short" line. BotRangerBR (7 Cure) and BotMaceAdvR (5 Heal) the same minute |

**The login rush:** a client the server turned away keeps writing a fresh state with `connected` false, so the supervisor's stale check (state age only) never relaunches it. The supervisor change (`test_client_disconnected`) also counts 60 s of connected-false as stale.

## Deployed to dev (2026-11-03)

Pushed and deployed to dev with the progress-bar deploy (pin `67b29ab34`), after the snapshot
`work/save-snapshots/saves-20261103-121627-before-progress-bars-deploy`. The README has a Shop stock line.
