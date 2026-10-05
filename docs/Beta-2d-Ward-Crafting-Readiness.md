# Beta 2d (pulled forward): Backpack Ward crafting and Tinker buy-back

**Decision:** Ready and deployed to the dev distribution (2026-10-05). Built, unit-verified and live-verified on a disposable host; no flag changed (the recipe and buy-back follow the existing `featureFlags.theftProtection`, with `wardCraft.enabled` and `wardVendor.buyBackPrice` as configuration switches). Evidence, matrix and readiness record for the Ward recipe and the Tinker buy-back. Follows [Beta-2a-Ward-Vendor-Readiness.md](Beta-2a-Ward-Vendor-Readiness.md). Price, stock, ingot count and buy-back are placeholders for the economy audit.

## Why

The Tinker vendor now sells the Ward at a 2,000 gp ceiling, but only a vendor could supply one. The design calls a regular Ward "obtainable ... crafting/purchase" ([BACKPACK-WARD-DESIGN.md](BACKPACK-WARD-DESIGN.md) Section 1), and the owner's goal for the vendor price was a ceiling crafted Wards undercut. This adds the crafted half and a small buy-back so a crafter who overestimated the player market still comes out slightly ahead.

## Sign-off (owner, 2026-10-05, in chat)

Plan presented 2026-10-05; the owner then raised the buy-back ("Should we have NPCs buy them?" and "so the player makes a small profit"), the plan was revised, and the owner said "Go, and you're allowed to commit, push, and deploy". Decisions:

| Decision | Ruling |
| --- | --- |
| Build now | Yes. This pulls **one recipe** forward from Beta 2d; it does not depend on the 2d overhaul (grades, tinker tools) and stays a one-method change if 2d reworks Tinkering. |
| Recipe | Tinkering **45.0 to 95.0** (the stock Lockpick tier), **20 iron ingots**, in the stock Tinkering group with Key, Lantern and Scales. Result: the same regular Unprimed Ward the vendor sells. |
| Price floor | The ingot count sets it: NPCs sell iron ingots for 5 gp, so 20 ingots cost about 100 gp. |
| Quality | None. A Ward has no power tiers, so the recipe forces no exceptional and no maker's mark (`CraftItem.ForceNonExceptional`). |
| Activation | `wardCraft.enabled` true (a configuration value, not a feature flag), and the whole thing still follows `featureFlags.theftProtection`. |
| Vendor | Unchanged: 2,000 gp, 20 per shelf. Both stay placeholders for the economy audit. |
| Buy-back | Tinkers pay **110 gp** for an unused (Unprimed, non-starter) Ward: a small guaranteed profit over the 100 gp ingot cost, and below the stock Lockpick's yield (6 gp per ingot, 120 gp for 20). Stock has the same pattern (Lockpick 6 gp from 5 gp of ingots). `wardVendor.buyBackPrice`, 0 turns it off, validated to stay below `wardVendor.price` (a buy-back at or above the sale price would pay gold for nothing). |
| No re-listing | Stock vendors resell what they buy at 1.9 times the price paid, here about 209 gp, which would put a cheap Ward back on the shelf and undercut crafters again. The buy-back sell list is not resellable, so a bought-back Ward is deleted (a small gold sink). The 2,000 gp shelf stays the only NPC sale. |
| Who is refused | The engine already refuses newbied, blessed and bound items to vendors (`IsStandardLoot`), so the starter Ward and any Primed or Activated Ward can never be sold; the sell list also checks it explicitly. |
| Audit | Buy-backs are logged like purchases (`theft ward-sold`: vendor serial, count, gold paid), so staff can watch the volume. |
| Hoarding lever held back | No per-account cap. Add one, with a pre-purchase ModernUO hook, only if the audit log shows real hoarding. |
| Out of scope | Craft quality grades and signatures (Beta 2d), salvage (Beta 2c), ward drops, regional prices, any change to the vendor's numbers. |

Player constraints checked (owner's seven rules): classic UO:R (a tinker-made item, no power creep); keeps thieves (a Ward still blocks only caught thieves); every role has an on-ramp (anyone with gold buys, a tinker crafts, nobody is gated behind another role); roles help each other (miners supply ingots, tinkers supply victims, thieves create demand); works for a small launch population (the vendor always has stock, the recipe needs no other player).

## What was built

- **ModernUO hooks**:
  - `BaseVendor.SellInfoLoaded(vendor, sellInfo)` fires right after `BuyInfoLoaded`, so shard code can add what a vendor buys; `BaseVendor.ItemsSold(vendor, seller, item, count, gold)` fires for each line a vendor buys, after the item changed hands.
  - `TinkeringMenu.AddMiscType(type)` (`Engines/Craft/T2A`): adds a type to the Miscellaneous list of the legacy Tinkering menu. **The plan assumed crafting needed no ModernUO change; the first live run showed otherwise.** This era's Tinkering is not the modern craft gump but a packet-based item-list menu (use the tools, target the ingots, answer the menus), and its categories are fixed type arrays, so a recipe added through `AddCraft` alone is never offered. The recipe, numbers and skill range are unchanged; only the mechanism gained this one idempotent hook.
- **ShardContent**:
  - `BackpackWardCraft.cs`: adds the recipe through stock Tinkering's public `AddCraft` (the craft list the later eras' gump uses) and lists the Ward in the legacy menu through `AddMiscType`, both when the server starts, behind the same flag and `wardCraft.enabled`.
  - `BackpackWardVendor.cs`: registers the two new hooks, adds `WardBuyBackSellInfo` (price from `buyBackPrice`, never resellable, only an Unprimed non-starter Ward) to plain Tinkers, and logs buy-backs.
- **Configuration** (`shard-rules.json`): `wardCraft` (`enabled`, `minSkill`, `maxSkill`, `ingots`) and `wardVendor.buyBackPrice`, validated at startup.

## Acceptance matrix

| # | Case | Entry point | Expected | Verified by | Restart |
| --- | --- | --- | --- | --- | --- |
| 1 | Config bounds | `BackpackWardCraft.Validate`, `BackpackWardVendor.Validate` | skill range 0 <= min < max <= 120 and ingots 1..200 accepted, anything else rejected by name; buy-back 0..1,000,000 and below the sale price | unit test | no |
| 2 | Shipped values and price band | shipped `shard-rules.json` | recipe 45/95/20 enabled; buy-back 110, inside (ingots x 5, ingots x 6) | unit test | no |
| 3 | Recipe shape | `BackpackWardCraft.AddRecipe` on a Tinkering-shaped `CraftSystem` | a Ward from the configured ingots across the configured skill range, in group 1044050, no exceptional. This checks the craft list only; the menu this era actually shows is covered live (L1 to L4) | unit test | no |
| 4 | Hooks registered once | `Configure` twice | one handler per hook | unit test | no |
| 5 | Buy-back sell list | `CreateBuyBack`, `WardBuyBackSellInfo` | pays the configured price, never resellable, off when the flag is off or the price is 0, independent of the stock switch | unit test | no |
| L1 | Recipe is in the Tinkering menu | use the tools, target the ingots, Miscellaneous (legacy item-list menus) | the list offers "backpack ward" | disposable host, Navrey | no |
| L2 | Its label | same list | "backpack ward (20 ingots)" | same | no |
| L3 | Crafting at skill 100 | pick the ward | exactly 20 ingots spent, one regular Unprimed Ward, no maker's-mark prompt | same | no |
| L4 | Below the minimum skill | the same list at skill 30 | the menu does not offer the ward (this era filters by what you can make) | same | no |
| L5 | Setup: a second crafted Ward, one Primed with the probe | `[TestOnlyWardPrime` | a Primed Ward and an Unprimed one in the pack | same | no |
| L6 | The sell list | `<Tinker> sell`, `selllist` | the Unprimed crafted Ward at 110 gp | same | no |
| L7 | Who is refused | `selllist` | the Primed Ward and the starter Ward are not listed | same | no |
| L8 | Selling | `sell` | +110 gp, the Ward leaves the pack | same | no |
| L9 | Not re-listed | `shop` after the sale | still exactly the 2,000 gp x20 entry | same | no |
| L10 | Audit | server log | one `theft ward-sold` line: vendor, count 1, paid 110 | same | no |
| L11 | Recipe survives a restart | menu after save and restart | still listed | same | one |
| L12 | Buy-back survives a restart | `selllist` after restart | the same Tinker still buys an unused Ward for 110 | same | same |
| L13 | Recipe off | `wardCraft.enabled` false in the host config | no group lists a backpack ward after a restart | same | one |
| L14 | Buy-back off | `buyBackPrice` 0 in the host config | the Tinker sends no sell list for a Ward, which stays in the pack | same | same |

## Results

| Cases | Result | Run |
| --- | --- | --- |
| 1 to 5 (unit) | Pass: `BackpackWardCraftTests` and the extended `BackpackWardVendorTests` (bounds, shipped values and price band, recipe shape, one registration per hook, buy-back sell info). | `Invoke-AgentVerification -Suite All`, run `20261005T205903429Z-eae020`: ModernUO UOContent 1346 passed, 0 failed, 2 skipped; ShardContent 490 passed, 0 failed |
| L1, L2 | Pass. After using the tools on the ingots the Tinkering menu offered Miscellaneous, which listed "backpack ward (20 ingots)" beside Key, Scales, Lantern and the others. | `ward_craft_live.py craft`, clean disposable host, 2026-10-05 |
| L3 | Pass. Crafting at skill 100 took exactly 20 ingots (200 to 180) and delivered one regular Unprimed Ward; no maker's-mark prompt; double-click showed the regular Unprimed text. | same |
| L4 | Pass. At Tinkering 30 the Miscellaneous list was only Key Ring, Key and Lantern: no ward. | same |
| L5 | Pass. A second ward was crafted, then one was Primed with the test probe. | same |
| L6, L7 | Pass. The Tinker's sell list offered the Unprimed crafted ward at 110 gp (beside the tinker's tools at 3 gp); the Primed ward and the starter ward were not on it. | same |
| L8 | Pass. Selling paid exactly 110 gp (500 to 610) and the ward left the pack. | same |
| L9 | Pass. The Tinker's buy list afterwards still had exactly one ward entry, the 2,000 gp shelf at a full 20: nothing was re-listed. | same |
| L10 | Pass. One audit line: `Alpha2 theft ward-sold: subject=<character>; details=vendor=<serial>; count=1; paid=110`. | same |
| L11, L12 | Pass. After a save and restart the menu still offered the ward and the same Tinker still bought an unused ward for 110 (610 to 720). | `ward_craft_live.py restart` |
| L13, L14 | Pass. With `wardCraft.enabled` false and `wardVendor.buyBackPrice` 0 in the host's copy of the config, after a restart the Miscellaneous list had no ward and the Tinker's sell list held only the tinker's tools; forcing a sale of a ward changed nothing. | `ward_craft_live.py off` |

Three things the live runs corrected, none of them in the approved design:
- **The recipe never appeared at first.** The plan assumed stock `AddCraft` was enough. This era's Tinkering is a packet-based item-list menu with fixed category type lists, so the first live run found no menu gump and the unit test (which models the later gump) could not have caught it. The `TinkeringMenu.AddMiscType` hook fixed it; the numbers and the recipe are as signed off.
- **Two driver faults, not feature faults.** Right after a login the server holds actions back briefly (the driver now retries the tool use), and a character carrying tinker's tools always gets a sell list because a Tinker buys tools (L14 now checks what is on the list instead of expecting none).
- **First deploy of the sell hooks** (`1a5413bcf`) was followed by the menu hook (`fe4000571`); the pin moved twice and the last deploy carries all three. Distribution snapshot before the first deploy: `work/save-snapshots/dist-20261005-165436-pre-ward-craft`.

## Readiness limits

- Crafting is verified through the legacy item-list menus this era shows. The later-era craft gump (not used on this shard) relies on the `AddCraft` entry, covered by the unit test only.
- Only skill 100 (certain success) and skill 30 (not offered) were driven live; the success chance between 45 and 95 follows the stock formula and was not measured.
- Ingot count, buy-back price, vendor price and stock are placeholders; the audit lines (`ward-bought`, `ward-sold`) are how staff watch the real volume. The skill-gain effect of crafting wards (it trains Tinkering like any recipe) was not measured.
- Hoarding resistance and the hourly restock rest on the engine's shelf rules, as in the vendor evidence; no per-account purchase cap exists.

## New player-facing text

The Tinkering menu entry "backpack ward" and its details page; the Tinker's sell-list entry "backpack ward" at 110 gp. The README's Theft section is updated at deploy.
