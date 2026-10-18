# Item tooltip: where it sells and for how much: work plan for sign-off (2026-10-18)

From the owner's to-do (2026-10-18, "Later"): the item tooltip says where an item sells and for how much, for example "Sells to Butcher for 3gp". **Nothing is built.** This plan settles the open questions from that entry with recommendations.

## Goal and exit criteria
A new player who hovers over loot or a crafted item learns, without asking anyone or walking round the shops, which Britain vendor pays the most for it and how much. Exit: unit tests for the price table and the wording, a live check on a disposable host (a monster drop, a crafted item, a starter item, an item nobody buys, a weapon at two qualities), real-client pictures of each, and the flag off until the owner says "activate".

## Current state (read 2026-10-18)
- **Tooltips:** `ItemTooltipService` (flag `itemTooltips`, on) writes the shard's own lines between the name and the weight: maker, quality, loot type, a weapon's or armor's kind numbers. A tooltip is built from the item, and is the same for everyone who hovers it.
- **What a vendor pays** comes from three layers, all in shard code or stock lists already audited:
  1. The stock shop lists (`SBInfo` sell lists, `GenericSellInfo`).
  2. The crafted-goods pricing (`CraftedGoodsPricing`, flag `craftedGoodsPricing`): material cost plus 25% for crafted goods.
  3. The extra buyers (`ExtraVendorBuyers`, flag `extraVendorBuyers`): vendors that buy what a craft recipe makes.
- `VendorResaleAuditTests` already walks every list with those layers applied and knows which shop lists never spawn in this world (`NotInThisWorld`), so the price table has a tested source.
- Stock `GenericSellInfo.GetSellPriceFor(item)` takes the item, not just its type, so a weapon's or armor's quality and durability already change the price it works out.

## Design
| Rule | Proposal |
| --- | --- |
| Source of truth | The price the vendor would actually pay for that exact item, asked of the same sell-info object the vendor uses, so the tooltip cannot disagree with the sale |
| Which vendors | Only vendor types that spawn in the generated world data (Britain's shops today); the test's `NotInThisWorld` idea, read from the spawn files so a moved or added shop updates itself |
| Several buyers | The best price and its vendor, then "and N other shops" only when more than one buys it: one line, never a list |
| Wording | `Sells to <Vendor> for <N>gp` (a stack: the price for one, with "each" when the amount is more than one); vendor named as the player knows the shop (Butcher, Blacksmith, Provisioner) |
| Nobody buys it | No line at all (silence is not a claim). A magic or unidentified piece: no line, so it never hints at what Item Identification would tell |
| Newbied or blessed | If the vendor refuses it, no line. If it can be sold, the usual line (the owner can say if starter gear should say "cannot be sold") |
| Quality and condition | Priced as the vendor prices that item; the tooltip says "about" nothing, it states the number the vendor will offer for this item as it stands. Wear is not shown anywhere else, so a damaged item's lower price is the only hint, which is the stock behaviour |
| Cost | A table keyed by item type, built once at server start and rebuilt when the pricing flags change; per hover it is a dictionary lookup plus the quality factors |
| Where it shows | Everywhere a tooltip does: the pack, the ground, the bank, shop windows (a vendor's own stock does not need the line, so shop windows skip it) |
| Switch | A new flag `sellPriceTooltips`, off until the owner says "activate"; the Welcome guide's Money and shops page gets a gated sentence |

## Work breakdown
1. **ShardContent** `SellPriceTable.cs`: build the type to (vendor, price) table from the stock lists, the crafted-goods adjustment and the extra buyers, for the vendor types in the spawn data; a function that prices a given item the way `GenericSellInfo` does.
2. `ItemTooltipService`: one more line source, behind the flag, after the loot-type lines.
3. Flag `sellPriceTooltips` (config, validator, status line), guide sentence, tests, evidence doc.
4. No ModernUO hook is expected (the sell-info objects and `GetSellPriceFor` are public); if the price calculation needs one, it will be named and justified before it is added.

## Verification
- Unit tests: the table agrees with `VendorResaleAuditTests`' view of every list; wording; stack and "each"; no line for unbought, magic or refused items.
- Live on a disposable host: hover over a monster drop, a crafted dagger at two qualities, a starter item, a gem nobody buys; then actually sell each and check the vendor pays the number the tooltip gave.
- Real client: pictures of the tooltip for each case, shown to the owner.

## Activation
Flag `sellPriceTooltips`, off. Needs the owner's explicit "activate".

## Open questions (recommendation first)
1. **Several buyers:** best price and its vendor, plus "and N other shops". Recommend this.
2. **Items nobody buys:** say nothing. Recommend nothing; the alternative is "No shop buys this", which is a claim a future shop could make false.
3. **Starter (newbied) gear:** say nothing if the vendor refuses it. Recommend nothing.
4. **Wording of the vendor:** the shop's job ("Butcher") or its title? Recommend the job.

## Out of scope
Showing prices of items a player could buy (shop windows already show them), what vendors will pay in the future, selling advice, per-viewer prices (none exist).
