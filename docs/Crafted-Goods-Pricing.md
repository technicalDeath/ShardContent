# Crafted-goods pricing

**Status:** built 2026-10-14 on the owner's authority ("I give you the authority to tune the shard's vendor buy prices and sell prices so that crafters can make a small profit on crafted items"). Flag `craftedGoodsPricing` is on in `data/configuration/shard-rules.json`. It is deployed and live on the bot farm's disposable host (`work/hosts/farm`) only, **not yet on the dev world**. Player docs (`README.md`) are not updated yet, because the dev world does not run it.

## Why

The bot farm found that crafting at starting skill loses money (`docs/Bot-Farm-Tuning-Notes.md`, item 1). A cloak costs 28 gold in cloth and the Tailor paid 4 for it. A mace costs 30 gold in ingots and the Blacksmith paid 14. Crafters went broke within the hour and could not buy material again.

## The rule

For every item made by blacksmithing, tailoring, tinkering, carpentry or bowcraft:

- **Material cost** is each resource in the server's own recipe at what vendors charge for it: iron ingot 5, cut cloth 2, cloth 2, bolt of cloth 100, leather 6, hides 4, board 3, log 2, feather 2, shaft 3. A part with no known price, such as gears, adds nothing.
- **What a vendor pays** for it is at least material cost × 1.25, rounded up. If the stock price is higher, the stock price stays.
- **What a vendor charges** for its own stock of it is at least 1.5 × that floor, so buying from a vendor to sell back never pays. A vendor's resale of goods players sold it is already 1.9 × what it paid (stock rule).
- **Prices are never lowered.** An item no vendor buys stays unbuyable, because the hook only changes prices of items already on a vendor's list.
- **Kept at stock prices, on both sides:**
  - the tools a crafter wears out: every tool kit, harvest tool, pickaxe, hatchet and scissors;
  - the consumables everyone buys in bulk: arrows, bolts, bandages, kindling.
  
  Raising these would eat the crafter's profit and hurt new players. The first build did raise them (sewing kit 3 → 20, and arrows would have gone from about 2 to 11 each), and the second build fixed that.
- Materials that are made from other materials (boards from logs, cloth cut from a bolt) are conversions, not products, and keep stock prices.

Exceptional and low quality still scale the price (×1.25 and ×0.6, stock rule).

## Examples (seen in game on the farm host, 2026-10-14)

| Item | Materials | Vendor paid before | Vendor pays now | Vendor charged before | Vendor charges now |
| --- | --- | --- | --- | --- | --- |
| Cloak | 14 cut cloth = 28 | 4 | 35 | 8 | 53 |
| Robe | 16 cut cloth = 32 | 9 | 40 | 18 | 60 |
| Shirt | 8 cut cloth = 16 | 6 | 20 | 12 | 30 |
| Mace | 6 ingots = 30 | 14 | 38 | 28 | 57 |
| Cutlass | 8 ingots = 40 | 12 | 50 | 24 | 75 |
| Ringmail tunic | 18 ingots = 90 | 60 | 113 | 121 | 170 |
| Sewing kit, scissors, tongs, pickaxe | tool | stock | stock | 3, 11, 13, 25 | 3, 11, 13, 25 (unchanged) |

The vendor's stock lists ("Shop Inventory") for the Tailor were photographed in the real client on the farm host: `work/player-client/BotTailorA/shots/20261014-215458-tailor-buy-final.png` (tools at stock, shirt raised) and `...-215510-tailor-buy-final-2.png` (robe 60, cloak 53). Both were sent to the owner. What the Blacksmith pays (mace 38, cutlass 50, tongs 7 in the first build) was read through Navrey's sell list.

## How it is built

- **Engine hooks (ModernUO, narrow):**
  - `GenericSellInfo.SellPriceAdjust` is a `Func<Type, int, int>` applied to the base price a vendor's table pays, before quality, only for items in the table.
  - `GenericBuyInfo.BuyPriceAdjust` is applied to a vendor list's price when it is read.
  - Both default to null (stock prices).
- **Shard code:** `src/BritanniaRenaissance.Content/CraftedGoodsPricing.cs`, registered in `ShardBootstrap`. It builds the cost table once from the craft systems' recipes and reads the flag on every price, so turning the flag off restores stock prices at once, without a restart.
- **Staff command:** `[CraftPricingStatus [TypeName]` shows whether it is on, how many item types are priced, and the floors for one type.
- **Tests:** `tests/CraftedGoodsPricingTests.cs` covers the arithmetic, that the vendor always charges more than it pays, that tools and consumables are kept at stock, and that the flag defaults off. The full shard suite passes (1,513 tests).

## Open questions for the owner

1. **Dev world:** deploy to the dev world? It needs the engine hook (UOContent rebuild) and the shard DLL, through the usual deploy path, and a `README.md` line on vendor prices.
2. **Margin and spread:**
   - Margin 1.25 covers the material lost on failed crafts only at success rates above about 60%. At 50% the crafter roughly breaks even.
   - Spread 1.5 makes NPC-bought finished goods 3 to 7 times dearer than before (a shirt 12 → 30, a cloak 8 → 53). Players who buy clothing or weapons from NPCs pay more. That is the intended shift to crafters, but it is a visible change.
3. **Not covered:** alchemy, inscription, cooking and cartography are left out for now (potions and scrolls are sensitive economy items). Should they follow the same rule?
4. **Ore** still has no NPC buyer (tuning note 4). This change does not address gatherers.
