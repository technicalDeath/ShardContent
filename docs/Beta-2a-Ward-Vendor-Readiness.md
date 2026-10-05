# Beta 2a follow-up: Backpack Ward vendor supply

**Decision:** Ready and deployed to the dev distribution (2026-10-05). Built, unit-verified and live-verified on a disposable host; no flag changed (the sale follows the existing `featureFlags.theftProtection`). Evidence, matrix and readiness record for the Tinker Ward sale. Price and stock are placeholders for the economy audit; they are configuration values.

## Why

A character gets exactly one free starter Ward (`TheftProtectionService.IssueStarterWard`, design Section 18), bound to them and never replaced. An Activated Ward is consumed after 30 quiet minutes. The design calls a regular Ward "an obtainable physical single-use consumable" whose "crafting/purchase sources and price should be determined by the economy audit" (design Section 1, Hot Zones plan configuration list). That was never built: once the starter Ward was spent a player had no way to get another (only staff `[add BackpackWard`).

## Sign-off (owner, 2026-10-05, in chat)

Plan presented 2026-10-05 and revised twice on the owner's economy concerns; the owner then said "Go". Decisions:

| Decision | Ruling |
| --- | --- |
| Source | NPC vendors for gold (the "purchase" half). Crafting stays deferred: the Tinkering recipe is planned separately, after this ships. |
| Vendor | Tinkers only (plain `Tinker`; the Mondain's Legacy quest tinkers derive from it and are excluded). Recommended; the owner approved the plan as written. |
| Price | 2,000 gp, a configuration value. A **ceiling**: wards have no power tiers, so crafters can only compete on price and availability, and the vendor must not be the cheapest source. (The first placeholder, 500 gp, was a new account's whole starter gold.) |
| Stock | 20 per Tinker. Deep, not thin: thin stock is what makes sweeping a shelf and reselling profitable. The engine doubles a shelf that sells out (to 999) and halves one that sells under half (while above 20), so an unsold shelf of 20 stays at 20. Clearing one shelf costs 40,000 gp against 500 gp of starter gold per account. |
| Sell-back | None at the time: no stock sell list names the Ward, so vendors never bought one. **Superseded the same day** by the owner-approved Tinker buy-back of unused Wards at 110 gp, never re-listed; see [Beta-2d-Ward-Crafting-Readiness.md](Beta-2d-Ward-Crafting-Readiness.md). |
| Audit | Every purchase writes a `theft ward-bought` audit line (buyer and account, vendor serial, count, unit price) so staff can spot hoarding. |
| Hoarding lever held back | A per-account purchase cap needs a pre-purchase ModernUO hook and is not built. Add it only if the audit log shows real hoarding. |
| Activation | No new flag. The sale follows `featureFlags.theftProtection` (already true); `wardVendor.stockPerVendor: 0` takes it off sale. |
| Out of scope | The crafted Ward (Tinkering recipe, Beta 2d), any Ward drops, price changes by region, a second vendor type. |

Player constraints checked (owner's seven rules): classic UO:R (a vendor sale of a custom item, no power creep); keeps thieves (a Ward blocks only caught thieves, unchanged); every role has an on-ramp (anyone with gold can buy, no crafter needed); works for a small launch population (a vendor always has stock).

## What was built

- **ModernUO hooks** (`BaseVendor`, the narrowest that let shard code add an entry for a type UOContent cannot reference):
  - `BuyInfoLoaded(vendor, buyInfo)` fires at the end of `LoadSBInfo()`, which runs in the vendor constructor and after load, so a restart rebuilds the shelf.
  - `ItemsBought(vendor, buyer, info, amount)` fires after a buy-list purchase is delivered, with the quantity actually bought. `ProcessValidPurchase` became an instance method to carry the vendor.
- **ShardContent** (`BackpackWardVendor.cs`): registers both hooks once (guarded, `+=`), adds the entry for plain `Tinker` vendors when theft protection is on and the stock is above zero, and logs the audit line. `BackpackWard.DefaultItemId` holds the Ward's item ID.
- **Configuration** (`shard-rules.json`, `wardVendor`): `price` (1 to 1,000,000) and `stockPerVendor` (0 to 999), validated at startup.

## Acceptance matrix

| # | Case | Entry point | Expected | Verified by | Restart |
| --- | --- | --- | --- | --- | --- |
| 1 | Config bounds and defaults | `BackpackWardVendor.Validate`, `ShardRulesConfiguration.Validate` | price 1..1,000,000 and stock 0..999 accepted; anything else rejected by name; shipped file valid with 2000/20 | unit test | no |
| 2 | Only plain Tinkers sell | `BackpackWardVendor.Sells` | Tinker yes; ML quest tinker, Alchemist, Mage, Provisioner no | unit test | no |
| 3 | Entry content | `CreateEntry` | Ward type, configured price and stock, item ID 0x1F14; null when theft protection is off or stock is 0 | unit test | no |
| 4 | Shelf dynamics with this entry | `GenericBuyInfo.OnRestock` | unsold 20 stays 20; sell-out doubles to 40 and caps at 999; 35 of 40 left shrinks back to 20 | unit test | no |
| 5 | Hooks register once | `Configure` twice | one handler per hook | unit test | no |
| 6 | A live Tinker offers the Ward | `BuyInfoLoaded` on construct | `shop` lists "backpack ward" at 2000 gp, stock 20; a non-Tinker vendor does not list it | disposable host, Navrey | no |
| 7 | Buying works | `OnBuyItems` / `ProcessValidPurchase` | gold drops by the price, one Ward arrives in the pack, Unprimed, not starter-issued, tradable | disposable host, Navrey | no |
| 8 | Stock decrements | `bii.Amount` | the shelf shows 19 after one purchase | disposable host, Navrey | no |
| 9 | Vendor will not buy it back | `OnSellItems` | selling a Ward to the Tinker is refused | disposable host, Navrey | no |
| 10 | Insufficient gold | stock vendor path | refused, no Ward, no gold taken | disposable host, Navrey | no |
| 11 | Audit line | `ItemsBought` | `Alpha2 theft ward-bought: subject=<buyer, account>; details=vendor=<serial>; count=1; unitPrice=2000` in the server log | disposable host log | no |
| 12 | Restart rebuilds the shelf | `LoadSBInfo` after deserialize | after save and restart the same Tinker lists the Ward again | disposable host | one |
| 13 | A bought Ward works | existing Ward code | double-click shows the Unprimed description with the activation lines | disposable host, Navrey | no |
| 14 | Off sale | `stockPerVendor: 0` | no Ward listed after restart | disposable host | one |

## Results

| Cases | Result | Run |
| --- | --- | --- |
| 1 to 5 (unit) | Pass. `BackpackWardVendorTests` (config bounds and shipped file, who sells, entry content, shelf dynamics, one registration per hook). | `Invoke-AgentVerification -Suite All`, run `20261005T190446328Z-12a348`: ModernUO UOContent 1346 passed, 0 failed, 2 skipped; ShardContent 463 passed, 0 failed |
| 6 | Pass. A fresh Tinker's buy list offered "backpack ward" at 2000 gp, stock 20; a fresh Alchemist's list did not. | `ward_vendor_live.py buy`, clean disposable host, 2026-10-05 |
| 7 | Pass. Buying took exactly 2000 gp (5000 to 3000) and delivered one Ward; double-click showed the regular Unprimed text (not the starter text). | same |
| 8 | Pass. The shelf read 19 after one purchase. | same |
| 9 | Pass. Control: with Tongs in the pack the Tinker sent a real sell list that took the Tongs and omitted the Ward; forcing `sell` of the Ward with that list open changed nothing (no gold, Ward kept). | same |
| 10 | Pass. A character with 500 gp bought nothing: gold unchanged, no Ward delivered. | same |
| 11 | Pass. Exactly one audit line: `Alpha2 theft ward-bought: subject=<character>/<name>; details=vendor=<serial>; count=1; unitPrice=2000`. | same |
| 12 | Pass. After a save and restart the same persisted Tinker listed the Ward again at the full 20. | `ward_vendor_live.py shelf` |
| 13 | Pass. The bought Ward's double-click text carried both new "how it works" lines (activation, 30 minutes, "Thieves it has not caught can still try"). | `buy` |
| 14 | Pass. With `wardVendor.stockPerVendor` 0 in the host's copy of the config, after a restart the Tinker listed its usual stock and no Ward. | `ward_vendor_live.py shelf ... absent` |

The first live attempt stopped at case 9 on a driver defect, not a feature defect: a Tinker sends no sell list when you hold nothing it buys ("You have nothing I would be interested in"), which is itself the intended answer. The driver now gives the buyer Tongs so a real list exists, and the whole pass was rerun from a fresh host and fresh characters.

ModernUO hooks committed as `afacbf043`. The deploy script requires the pinned ModernUO commit to equal ModernUO `HEAD`, so the pin moved to `afacbf043` in the three places (`shard-rules.json`, `world-generation.json`, `Alpha2bWorldGenerationConfigurationTests.cs`). Distribution snapshot before the deploy: `work/save-snapshots/dist-20261005-151506-pre-ward-vendor`.

**Other uncommitted work the deploy carried.** The working trees also held the harvest auto-repeat work (ShardContent `HarvestRepeatService.cs`, `featureFlags.harvestAutoRepeat` set false, and a ModernUO `HarvestSystem.StageChanged` event hook). It is behind a false flag and its tests pass, so the deploy shipped it inert. It is not part of this item and was not committed with it.

## Readiness limits

- Price (2,000 gp) and stock (20) are placeholders; the economy audit sets the real values. They are configuration, no rebuild needed.
- Hoarding resistance rests on the engine's shelf rules, proven by unit tests of `GenericBuyInfo.OnRestock` with this entry. The hourly restock and a real sell-out were not waited for live.
- A bad `wardVendor` value stopping the server at startup, and the sale going off when `featureFlags.theftProtection` is false, are covered by unit tests only.
- The vendor gump's item tooltip was not inspected.
- No per-account purchase cap. Add it, with a second pre-purchase ModernUO hook, only if the `ward-bought` audit lines show real hoarding.

## New player-facing text

None beyond the vendor's list entry, "backpack ward", at 2,000 gp. The README's Theft line is updated at deploy.
