# Alpha 3 starter package audit

> **Superseded death rules (owner ruling, 2026-09-28).** The four-logged-in-hour Starter Protection, the bound `StarterBag`, the Ward's nested-bag exception and its destroy-on-death rule no longer exist. Death and bag results below that depend on them are historical; see [Owner rulings and Phase E closure](#owner-rulings-and-phase-e-closure--september-28-2026). Economy results (sale, trade, vendor, salvage, crafting) are unaffected.

## Economy route checkpoint — September 28, 2026

| Case | Expected behavior | Setup and effective configuration | Source/test | Observed result | Remaining limitation |
| --- | --- | --- | --- | --- | --- |
| ST-ECON-NPC-POLICY-41 | Every bound starter type is ineligible for NPC sale and resale, even when its concrete type is explicitly present in a vendor's sell-info table; ordinary outputs remain eligible. A container holding a bound starter item is ineligible for both routes. | Isolated test hosts; each concrete type represented as an uninitialized test item without world/account state. `BackpackWard` receives its starter-issued marker; remaining types must implement `IStarterIssued`. Nested case uses an ordinary Bag with a bound Katana. | Shard `tests/StarterSaleEligibilityMatrixTests.cs` enumerates 41 types and checks `Nontransferable`, `GenericSellInfo.IsSellable`, and `IsResellable`; ModernUO UOContent `Tests/Items/StarterBoundVendorTests.cs` checks bound/ordinary sale and resale and nested-container sale/resale. Full Shard result `20260928T075246785Z-0ef67e` (219/219); focused UOContent result `20260928T071525971Z-245d1c` (8/8). | All 41 explicit-list probes rejected both routes. Bound Katana and its containing ordinary Bag were rejected for both; ordinary Katana remained eligible. The separate live Blacksmith session omitted the bound ingot and sold the ordinary two-ingot control. | Live NPC sell-list/sale evidence covers Blacksmith ingots and legacy Wards, Tinker Scissors, and Tailor Shirts; broader vendor families and item coverage remain unobserved. |
| ST-ECON-NPC-TAILOR-BUYBACK | Stock Tailor lists an ordinary crafted Shirt for sale, sells it at the listed price, then offers the same item back at its stock buyback price. | Disposable host PID 20960 on port 2595; staff PID 43348; fresh ordinary P2 PID 20512 in a separate role directory with absolute command/log/state/world paths. Alpha 3 flags and acknowledgment false. Probe seeds 100 bound StarterCloth and bound Sewing Kit; 100 Tailoring; fixture Tailor adjacent to player. | Test-only `StarterEconomyProbe` `craftcloth`/`makecloth`/`tailornpc`/`item`; `tests/scenarios/starter-economy/npc_tailor_buyback_live.py`; stock `TailoringMenu.ResourceSelection`, `DefTailoring.CraftSystem.CreateItem`, `SBTailor.InternalSellInfo`, and `SBTailor.InternalBuyInfo`. | Stock Shirt created; bound cloth 100→92. Tailor sell list offered same Shirt serial `0x4007E6A1` for 6 gp; sale raised gold by 6. Buy list offered that serial for 11 gp; buyback charged 11 gp and returned same Shirt. Staff verified `type=Shirt`, `nontransferable=False`, root PlayerMobile after repurchase. | Other vendor families and additional item types remain unobserved. The first driver assertion expected six cloth; the stock recipe consumed eight. A contaminated retry hit an earlier stack, so the passing clean run used a separate fresh account/client role. |
| ST-ECON-NPC-SALE | Bound items and containers holding them cannot be sold or resold to NPCs; ordinary output stays eligible. | Disposable clone, ordinary P1 at (633,858), staff client beside a test-named Blacksmith at (634,858); server PID 36112, admin client PID 24016, P1 PID 24504. Each client has separate `cmd2.txt`, `client2.log`, `state2.json`, `world2.json` paths under its role directory. `[ShardRulesStatus` reported Alpha 3 acknowledgment false, UOR/Felucca, and only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut configured; Alpha 2 acknowledgment remained true. No Alpha 3 override was used. | `GenericSellInfo.IsSellable` recursive policy; `StarterBoundVendorTests` focused run `20260928T071525971Z-245d1c` (8/8); live driver `tests/scenarios/starter-economy/npc_sale.py` with the test-only `StarterEconomyProbe` SHA-256 `62FA0875E6515C476807D97A4DF2F8415192864CAAA9916974356C48338FDE73`. Clone `UOContent.dll` SHA-256 `D9A87A65CCD37E3360F76807B140D5BF9FAE0065E6F440F207304712C538E24E`. | P1 said `vendor sell`; the server sent an NPC sell list with exactly one entry: ordinary `IronIngot` stack, two units at 4 gp each. Bound `StarterIronIngot` was absent and remained in the backpack. Selling the ordinary stack removed it and increased P1's gold by 8. The paired client state and `[SHOP]` log confirmed the transaction. | Blacksmith sell-list coverage also includes a legacy Ward, and separate Tailor/Tinker rows record live repurchase interactions. Broader vendor families and item coverage remain live-evidence gaps; direct item/container eligibility is covered by the mapped tests above. |
| ST-ECON-PLAYER-VENDOR | Bound items and containers holding them cannot enter player-vendor stock; ordinary output remains accepted and owner-retrievable. | Paired ordinary clients, distinct accounts/directories and four absolute session paths each; disposable host `work/alpha3-starter-economy-host`; test fixture seeded six bound families plus nested ingot; flags and acknowledgment false. | `PlayerVendor.OnDragDrop`, `NontransferableItemPolicy`; 5/5 focused tests above; credential-free Navrey driver `tests/scenarios/starter-economy/paired_economy_cases.py`; server probe `StarterEconomyProbe verify`. | Six bound item families and a Bag with nested bound ingot stayed with owner on attempted intake. Ordinary Katana entered stock, was retrieved by vendor owner, and server probe confirmed its final backpack parent. | Ward legacy population/migration and full families/other sell targets remain open. |
| ST-ECON-TRADE | Bound items cannot enter secure trade, including nested starter material; ordinary output trades both directions. | Same isolated paired-client session and effective flags as ST-ECON-PLAYER-VENDOR. Clients: server PID 6648; admin PID 25872; ordinary players P1 PID 18764 and P2 PID 11756, each isolated path set `cmd2.txt` / `client2.log` / `state2.json` / `world2.json`. | `PlayerMobile.CheckTrade` recursive contents check; same Navrey driver and server probe; deployed clone `UOContent.dll` SHA-256 `C51245EE72336426E7EED29AF14671A42CEBB3E0315D23CC4E8D946CDF7931D2`. | Direct Bag, scissors, full 10-ingot stack, Tinker Tools, Katana and marked Ward attempts did not open trade or leave owner backpack. An ordinary Bag containing bound ingot was blocked. Ordinary Katana traded to P2 and back after both clients accepted; server probe confirmed destination parents. | More distinct bound families and loss/death paths remain open. |
| ST-ECON-TRANSFER-MATRIX-41 | Each direct bound starter implementation remains with its owner and outside secure trade and player-vendor stock; no recipient receives it. | Disposable host `work/alpha3-starter-economy-host`, server PID 26768, staff client PID 38568, P1/P2 PIDs 36112/37388; separate role directories and all four absolute file paths; ordinary paired characters at Yew (633,858). Effective rules were UOR/Felucca, Alpha 3 acknowledgment false, only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut configured. Test setup set P1 Strength to 55 (max weight 232); no feature override. | Test-only `StarterEconomyProbe` SHA-256 `2A6F619FDD5A78D32B97A552587D06E8484D31E4F7D4534CC0B698E0E4844EF7`; clone `UOContent.dll` SHA-256 `D9A87A65CCD37E3360F76807B140D5BF9FAE0065E6F440F207304712C538E24E`; `tests/scenarios/starter-economy/transfer_matrix.py` using Navrey `Client` API. | All 41 emitted types were attempted by direct drop to P2 and vendor. Every item stayed in P1's backpack; `trades` reported no secure-trade window; final staff probe reported `ownerBackpack=True; vendorStock=False; inTrade=False` for all 41. Recipient inventory did not acquire any item. No refusal narration was observed during this run, so acceptance rests on live client inventory/trade state plus the authoritative server parent/stock/trade invariants. Cleanup command removed the two matrix characters/accounts and vendor at 04:11; autosave completed at 04:15 (server PID 39296) and the disposable host was stopped after save. | Covers direct transfer for this emitted 41-type set. Nested wrapper and ordinary control routes rely on the earlier paired session; other vendor/sale targets, legacy unmarked Ward and death/loss routes remain open. |
| ST-ECON-SALVAGE | Bound scissorable items cannot be converted into unrestricted outputs through direct scissors or Salvage Bag; bound metal gear cannot be resmelted into ordinary ingots; ordinary controls still convert. | Disposable clone `work/alpha3-starter-economy-host`, effective flags reported by `[ShardRulesStatus`: SafeWorld, AutomaticMurderAdjudication, TheftProtection, KnockedOut; all Alpha 3 flags and acknowledgment false. Server PID 9724, staff client PID 38968, ordinary client PID 35184. Four distinct absolute session files per client under `work/alpha3-starter-economy-clients/{admin,player1}`. Probe placed the character at the Britain forge/anvil station (1354,1778,15), with Tongs and a test Salvage Bag; bound fixtures were inserted server-side because ordinary drops reject them. | Direct scissors and Salvage Cloth/Ingots through `tests/scenarios/starter-economy/scissor_conversion.py`; test-only `StarterEconomyProbe` SHA-256 `2BEF0637996056343EB0EED0CA17BFD9A83359C4872EB4657A57F4EC513BA3B0`; production `SalvageBag.Resmelt` calls recursive `NontransferableItemPolicy.Contains`; `Resmeltables` now scans past ineligible earlier items. UOContent run `20260928T071525971Z-245d1c` passed 8/8; `UOContent.dll` SHA-256 `D9A87A65CCD37E3360F76807B140D5BF9FAE0065E6F440F207304712C538E24E`. | Direct StarterCloth and StarterStuddedChest targeting retained both items without outputs; ordinary Cloth produced two bandages. Salvage Cloth returned/stacked bound cloth, retained bound armor, and produced no bandages. Context action then reported `You cannot salvage a nontransferable item.` twice and `Salvaged: 1/3 blacksmithed items`; bound StarterKatana and StarterStuddedChest remained in the bag, ordinary Katana disappeared, and two ordinary iron ingots appeared in P1's backpack. Client state confirmed location and updated inventory. | This live case covers cloth and starter metal gear with the ordinary Katana control. Remaining distinct bound families, other conversion tools and post-protection loss/death remain open. |
| ST-ECON-CRAFT-IRON | Blacksmith crafting can consume bound starter ingots and owner-bound Tongs; the resulting normal recipe output remains an ordinary, unrestricted item. | Disposable host `work/alpha3-starter-economy-host`, server PID 43968, staff PID 16784, ordinary P1 PID 33200, four separate absolute session paths. P1 at map-data station pair `(3704,2245,20)`; probe verified `anvil=True; forge=True`. Probe set Blacksmith 100, Strength 100 and temporary `Blessed=true` for the test character. It seeded StarterIronIngot stacks and StarterTongs; the ordinary 47-ingot stock stack was deleted before the bound-input attempt. `[ShardRulesStatus` reported UOR/Felucca, Alpha 3 acknowledgment false, and only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut configured. | Test-only `StarterEconomyProbe` SHA-256 `D8566DEBC2C270009C29347FE5B1FA8FE225444E334C67461E776F53C82B1EA1`; exact stock `BlacksmithMenu.ResourceSelection` and `DefBlacksmithy.CraftSystem.CreateItem` callback; `DefBlacksmithy` Dagger recipe consumes 3 IronIngots; UOContent ordinary item defaults and sale policy. Navrey driver used `Client` with the same role paths. | Resource selection accepted a `StarterIronIngot` instance as `IronIngot`; after removing the ordinary stack, the starter stack changed from 100 to 97. The ordinary client observed and accepted the stock maker's-mark prompt, then received Dagger serial `0x4007D080`; client log reported an exceptional marked item. The recipe output type was stock `Dagger`, not a starter subclass. Cleanup removed the test character/account and fixtures at 05:39; autosave completed at 05:40 before shutdown. | Navrey exposes server gumps but not T2A item-list menu selection. The test-only staff action ran the same stock resource-selection callback and `CreateItem` route after the client opened Tongs; an ordinary client did not select the item-list menu itself. This covers only Blacksmith ingots; other material categories, ordinary output transfer/sale in this same session and save/restart consumption remain open. |
| ST-ECON-CRAFT-WOOD | Carpentry can consume owner-bound starter boards with owner-bound Saw; stock recipe output remains an ordinary item. | Disposable host `work/alpha3-starter-economy-host`, server PID 22020, staff PID 24024, ordinary P1 PID 25552; distinct absolute session files. Ordinary Advanced character at `(3704,2245,20)`. Test probe set Carpentry/Strength to 100 and temporary `Blessed=true`; seeded 100 StarterBoards and StarterSaw. `[ShardRulesStatus` reported UOR/Felucca, Alpha 3 acknowledgment false, only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut configured; no feature overrides. | Test-only `StarterEconomyProbe` SHA-256 `9A55D4704B08AED1BDDD03462909BC0C6037E9177D2ECA8BC2BA189AD2A4212B`; stock `DefCarpentry.CraftSystem.CreateItem`, `CraftItem.ConsumeRes` and WoodenChair recipe, which consumes 13 Log/Board inputs; Navrey `Client` with the role paths above. | Owner-bound StarterSaw produced the stock T2A target request. The test-only staff action invoked the stock WoodenChair recipe. Client inventory changed from 100 to 87 StarterBoards and received stock chair serial `0x4007CDCC`; client log said `You create the item.` Cleanup removed the test character/account and fixtures at 05:51; after stopping admin, the autosave completed at 05:55 before server shutdown. | The T2A item-list response was not selected by the ordinary client because Navrey's API lacks that control; the recipe was invoked through the same stock `CreateItem` route by a test-only staff command. Output direct transfer/sale, save/restart, and other craft material categories remain open. |
| ST-ECON-CRAFT-TAILOR | Tailoring consumes owner-bound starter cloth with an owner-bound Sewing Kit; the stock Shirt recipe yields ordinary stock clothing. | Disposable host `work/alpha3-starter-economy-host`, server PID 8092, staff client PID 21008, ordinary P1 PID 20652; each role used distinct absolute `cmd2.txt`, `client2.log`, `state2.json`, and `world2.json`. New ordinary character `StarterTailor` at `(633,858)` was moved by the test-only fixture to `(3704,2245,20)`, set to Strength/Tailoring 100 and temporarily Blessed. Fixture seeded 100 StarterCloth and a bound StarterSewingKit. Runtime reported UOR/Felucca, Alpha 3 acknowledgment false, only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut configured; no Alpha 3 override. | Test-only `StarterEconomyProbe` SHA-256 `717A089C2D0F6533397FA936B8436B15CDFD96CD0D3C63EB3B0AE7BD0C965697`; `TailoringMenu.ResourceSelection` and `DefTailoring.CraftSystem.CreateItem` for stock `Shirt` recipe (8 Cloth); `tailoring_live.py` plus recorded Navrey client state/log and staff probe log. | P1 targeted its bound Sewing Kit at StarterCloth and received the stock tool target request. Staff test callback selected `Shirt`/Cloth and ran `CreateItem`; P1 observed the maker's-mark gump, accepted button 1, then logged exceptional quality creation. Backpack changed from StarterCloth x100 and Sewing Kit x1 to StarterCloth x92, Sewing Kit x1 and ordinary Shirt x1 (`0x4007CE59`). Cleanup removed the character/account and probe fixtures after P1 PID 20652 stopped; client-observed world save completed at 06:05, after cleanup, before admin and host shutdown. | Navrey cannot select the T2A item-list menu, so a test-only staff callback ran the same stock resource-selection and `CreateItem` path. This proves cloth input only, not leather, failure handling, transfer/sale, or persistence of post-consumption state. |
| ST-ECON-CRAFT-TINKER | Tinkering consumes owner-bound starter iron with owner-bound Tinker Tools; the stock Gears recipe yields ordinary stock components. | Disposable host `work/alpha3-starter-economy-host`, server PID 32888, staff client PID 4188, ordinary P1 PID 20176; distinct absolute `cmd2.txt`, `client2.log`, `state2.json`, and `world2.json` per client. Ordinary `StarterTinker` at `(633,858)` was moved by the test-only fixture to `(3704,2245,20)`, set to Strength/Tinkering 100 and temporarily Blessed. Seeded 100 StarterIronIngot and StarterTinkerTools. `[ShardRulesStatus` showed UOR/Felucca, Alpha 3 acknowledgment false, Alpha 2 acknowledgment true, only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut configured; no Alpha 3 override. | Test-only `StarterEconomyProbe` SHA-256 `354C75701CCE5DCF7ADF7336741FF139985F245613AECB1393DD6B46D86D7123`; stock `TinkeringMenu.ResourceSelection` and `DefTinkering.CraftSystem.CreateItem` for Gears (2 IronIngots); `tinkering_live.py` with Navrey `Client`. | P1 used bound Tinker Tools, accepted its target cursor on the bound ingot, and opened the stock item-list menu. The callback selected Gears/IronIngot and ran `CreateItem`. Client inventory changed from StarterIronIngot x100 to x98 and gained stock Gears x1 (`0x4007CE97`). The initial attempt was denied by the ordinary action cooldown; after a 3-second wait, the live rerun passed. Cleanup removed the character/account and fixtures after P1 PID 20176 stopped; autosave completed at 06:20 before admin and host shutdown. | Navrey cannot select T2A item-list menus; test-only staff callback used the same stock resource selection/recipe path. Only the Gears recipe on starter iron is covered; other Tinkering recipes/tools, failure behavior, sale/transfer and restart persistence remain open. |
| ST-ECON-CRAFT-LEATHER | Tailoring consumes owner-bound StarterLeather through the stock LeatherCap recipe and creates an ordinary stock cap. | Disposable host `work/alpha3-starter-economy-host`; server PID 44640, admin PID 17696, ordinary P1 PID 26008 with separate four-path sessions. `StarterTailor` at the tailoring station, Tailoring 100, temporary Blessed state; fixture seeded StarterLeather x20 and bound Sewing Kit. Alpha 3 flags/acknowledgment stayed off. | Test-only `StarterEconomyProbe`; `craft_families_live.py`; stock `DefTailoring.CraftSystem.CreateItem` and maker's-mark response. | Client targeted bound kit to bound leather and accepted the maker's-mark prompt. StarterLeather changed 20→18 and ordinary exceptional LeatherCap `0x4007D1C8` appeared. Cleanup confirmed; save completed at 06:45. | Navrey cannot select the T2A recipe list; test callback used the stock recipe/resource path. LeatherCap loss, sale and post-consumption restart remain open. |
| ST-ECON-CRAFT-BOWYER | Bowyer consumes bound StarterBoard for a stock Shaft, then bound StarterFeather plus that Shaft for an ordinary stock Arrow. | Disposable host `work/alpha3-starter-economy-host`, server PID 39104, admin PID 24252, ordinary P1 PID 29624, each with distinct absolute command/log/state/world paths. Fresh `StarterTinker` at `(633,858)`; fixture moved it to `(3704,2245,20)`, set Bowcraft/Strength 100 and temporary Blessed state. Runtime `[ShardRulesStatus`: UOR/Felucca, Alpha 3 acknowledgment false, only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut enabled. | Test-only `StarterEconomyProbe` SHA-256 `204DF9A23DB9CA120C1158A730C403C14ECD1FD4A5924761B449BA73300B04B7`; `craft_bowyer_live.py`; stock `DefBowFletching` Shaft and Arrow recipes, `T2ACraftSystem.ShowMenu`, and `CraftSystem.CreateItem`. | A prior attempt on this host failed with no consumption; after rebuild, bound StarterBoard x1→0 produced stock Shaft x1, then bound StarterFeather x1 and that Shaft x1→0 produced ordinary Arrow x1. Server logged Shaft recipe/resource Board and Arrow recipe selections; client inventory confirmed both outputs and exact inputs. | Navrey cannot select the T2A recipe list; staff probe invoked the stock resource and recipe path. Output transfer/sale and consumed-state restart remain open. |
| ST-ECON-CRAFT-SCRIBE | Stock Runebook recipe consumes bound StarterBlankScrolls and ordinary recipe-required inputs, yielding an unrestricted UOR Runebook. | Same disposable host, server PID 39104, admin PID 24252, P1 PID 29624. Fixture set Inscription 100 at the crafting station and seeded StarterBlankScroll x8, bound ScribesPen, RecallScroll, GateTravelScroll, and an ordinary blank RecallRune. Effective rules matched the Bowyer row; no Alpha 3 override. | Test-only `StarterEconomyProbe` SHA-256 `204DF9A23DB9CA120C1158A730C403C14ECD1FD4A5924761B449BA73300B04B7`; `craft_remaining_live.py`; stock `DefInscription` Runebook recipe and `CraftSystem.CreateItem`. | Client used the bound pen on the bound scrolls. Server selected stock `Runebook` with blankBefore=8 and blankRequired=8. Client observed output graphic `0x0EFA` (“spellbook” label in this UOR client); source `Runebook` constructor uses that UOR graphic. StarterBlankScroll x8, RecallScroll, GateTravelScroll, and ordinary blank RecallRune were consumed; an ordinary stock Runebook was created. | The UOR client label for graphic `0x0EFA` is “spellbook”; recipe type and stock `Runebook` constructor establish the item class. Staff callback selected the stock recipe. Post-consumption restart and transfer/sale remain open. |
| ST-ECON-CRAFT-ALCHEMY | Alchemy consumes bound StarterBottle and one bound reagent for a stock potion. | Same disposable host and paired session as Bowyer. Fixture seeded StarterBottle x1, StarterGinseng x3, bound Mortar and Pestle and Alchemy 100; Alpha 3 flags/acknowledgment false. | Test-only `StarterEconomyProbe` SHA-256 `204DF9A23DB9CA120C1158A730C403C14ECD1FD4A5924761B449BA73300B04B7`; `craft_remaining_live.py`; stock `DefAlchemy` Lesser Heal Potion recipe and `CraftSystem.CreateItem`. | Client targeted the bound mortar at bound Ginseng. Server selected LesserHealPotion; bottle 1→0, Ginseng 3→2, and ordinary Yellow Potion x1 appeared. | Callback invoked the stock recipe; the ordinary client performed the target action. Other potion/reagent recipes and post-consumption restart remain open. |
| ST-ECON-CRAFT-COOKING | Cooking consumes bound raw fish using stock Skillet at a heat station; bound kindling is not consumed when the stock recipe does not require it. | Disposable host PID 39104, admin PID 24252, P1 PID 29624; ordinary character at `(3704,2245,20)`, Cooking 100; seeded StarterRawFishSteak x1, StarterKindling x1 and ordinary Skillet. Alpha 3 flags/acknowledgment false. | Test-only `StarterEconomyProbe` SHA-256 `204DF9A23DB9CA120C1158A730C403C14ECD1FD4A5924761B449BA73300B04B7`; `craft_cooking_live.py` and `craft_remaining_live.py`; stock `DefCooking` FishSteak recipe and `CraftSystem.CreateItem`. | At the heat station, StarterRawFishSteak x1→0 produced ordinary FishSteak x1; StarterKindling stayed x1 and the ordinary Skillet remained. A later grouped rerun independently repeated the exact deltas. | Staff callback invoked the stock recipe; stock output was client-observed. Additional cooking routes and post-consumption save/restart remain open. |
| ST-ECON-CRAFT-TINKER-SCISSORS-PERSIST | A stock Tinkering Scissors craft consumes bound iron; the ordinary output cannot convert bound StarterCloth; post-consumption material and output survive save/restart. | Disposable host first run server PID 29244, admin PID 16020, P1 PID 37620; after restart server PID 3900, admin PID 35488, P1 PID 41644. Four absolute client paths remained distinct. New `StarterTinker` at `(633,858)` was moved to `(3704,2245,20)`, Tinkering 100 and temporarily Blessed. Seeded StarterIronIngot x6, bound Tinker Tools and StarterCloth x5. Script verified Alpha 3 acknowledgment false. | Test-only `StarterEconomyProbe` SHA-256 `9A4C65673820B19C0F7497021381AF928223FA6717E8B868008CA5D26E0BC4FF`; `tinkering_conversion_live.py`; stock `DefTinkering` Scissors recipe (2 IronIngots), `CraftSystem.CreateItem`, and `Scissors.CanScissor`. | P1 targeted bound tools at the bound ingot; stock recipe produced ordinary Scissors and consumed ingots 6→4. P1 targeted those scissors at StarterCloth; client reported “Scissors cannot be used on that to produce anything” and cloth stayed x5. After world save at 07:25, exact host shutdown/restart and ordinary account login restored the same character and backpack serials/amounts: StarterIronIngot x4, Scissors x1 and StarterCloth x5. This is a real consumed-state save/restart pass. | Test-only staff callback selected the stock Tinkering recipe because Navrey cannot select its T2A item-list menu. No ordinary trade/vendor/sale route for this particular Scissors output was rehearsed; existing ordinary-control trade and class/policy evidence covers the unrestricted output boundary. Cleanup removed the test character, fixtures, and account after P1 stopped; the disposable host saved at 07:30 before admin and host shutdown. |
| ST-ECON-CRAFTED-SCISSORS-TRANSFER | Ordinary Scissors crafted from bound iron remain unrestricted and can be traded between ordinary clients and offered for sale through an owner-operated player vendor. | Disposable UOR/Felucca host PID 45212; staff PID 15868, seller P1 PID 39168, buyer P2 PID 16348. Separate accounts, working directories and all four absolute command/log/state/world paths. Both ordinary characters were moved to `(3704,2245,20)`; P1 Tinkering 100, Blessed temporarily, seeded StarterIronIngot x6 and bound Tinker Tools. Runtime `[ShardRulesStatus`: Alpha 3 acknowledgment false; only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut enabled. | Test-only `StarterEconomyProbe` SHA-256 `3835D482A182595F0096BA512B98ABBADACBCF8034A407ECCD3116642248A48E`; `craft_output_transfer_live.py`; stock `DefTinkering` Scissors recipe, secure-trade callbacks and `PlayerVendor.OnDragDrop` / `VendorPricePrompt`; staff `item` probe. | Bound iron x6→4 yielded stock Scissors `0x4007DD61`. Two ordinary clients accepted secure trade and the buyer received the same serial; they returned it to the seller. Seller placed it on owner-operated vendor `0x0001C4C5`, answered the price prompt with `100 Crafted Scissors`, and staff confirmed `type=Scissors`, `parent=VendorBackpack`, `root=PlayerVendor`, `nontransferable=False`, `vendorStock=True`, `inTrade=False`. Cleanup removed both named characters/accounts, vendor and fixtures after the clients stopped; cleanup completed at 07:41, with autosave at 07:45 pending. | This live transfer/sale case covers stock Scissors as one ordinary crafted output. It does not prove direct sales to NPCs or every crafted-item family. |
| ST-ECON-NPC-TINKER-BUYBACK | An ordinary Scissors crafted from bound iron is accepted by a stock Tinker NPC sell list, enters its inventory, and can be bought back at the listed price. | Disposable UOR/Felucca host PID 37352; admin PID 41580, ordinary P1 PID 28736; four absolute role paths. Fresh `StarterTinker` at Yew, fixture moved it to `(3704,2245,20)`, Tinkering 100 and temporarily Blessed; stock Tinker NPC spawned adjacent at `(3705,2245,20)`. StarterIronIngot x6 and bound Tinker Tools produced the Scissors. `[ShardRulesStatus` reported Alpha 3 acknowledgment false; only SafeWorld, AutomaticMurderAdjudication, TheftProtection and KnockedOut enabled. | Test-only `StarterEconomyProbe` SHA-256 `0117501FE568D226FA9D584F9CEBE3FB83E68A50C9D03863A9945C4BE17E0055`; `npc_tinker_buyback_live.py`; stock `SBTinker.InternalSellInfo` (Scissors value 6), `BaseVendor.OnSellItems`, vendor buyback and stock buy request. | Ordinary client saw Scissors serial `0x4007E3DF` on Tinker sell list at 6 gp, sold it, and gold changed 1000→1006. Staff confirmed it was an ordinary item in a stock Tinker backpack (`root=Tinker`, `nontransferable=False`). The Tinker buy list then included that same serial at 11 gp; ordinary client bought it back and the same item returned with gold 995. This proves one non-Blacksmith NPC sale and repurchase route end to end. Cleanup removed the test character, fixture items and test-named Tinker; cleanup was confirmed after P1 stopped and the world saved at 07:55 before admin and host shutdown. | This is one Tinker family and one crafted item; other vendor-family sell lists and repurchase cases remain open. Cleanup was confirmed after P1 stopped and the world saved at 07:55 before admin and host shutdown. |
| ST-ECON-CRAFT-FAILURES | Stock crafting fails safely when the required recipe resource/tool/input is unavailable: no output is minted and unrelated or bound inputs are not consumed. | Four disposable UOR/Felucca rehearsals with Alpha 3 flags/acknowledgment off: (1) Bowyer with StarterBoard x1 but the test callback selected `Log`; (2) Inscription Runebook without the ordinary blank RecallRune; (3) Cooking FishSteak without Skillet; (4) Tinkering after its ordinary action cooldown. Characters had the needed base skills and were at the relevant stations. | Test-only probe and ordinary Navrey sessions: `craft_bowyer_live.py`, `craft_remaining_live.py`, `craft_alchemy_cooking_live.py`, `tinkering_live.py`; stock `DefBowFletching`, `DefInscription`, `DefCooking`, `DefTinkering` and `CraftSystem.CreateItem` paths. Exact failed runs are retained in the scenario/client/server records from the September 28 rehearsals; each corrected setup subsequently passed its stock recipe. | Bowyer produced no Shaft and kept StarterBoard x1 when `Log` was selected; adding the correct stock `Board` selection then consumed it and made Shaft. Runebook attempt lacking the blank rune produced no book and kept the seeded scroll/tool inputs; adding a blank Rune then consumed the required inputs and created stock Runebook. Cooking attempt lacking Skillet left StarterRawFishSteak x1 and StarterKindling x1 unchanged; adding ordinary Skillet then consumed only raw fish and made FishSteak. First Tinkering attempt during action cooldown produced no Gears and consumed no ingots; after waiting 3 seconds, Gears succeeded with 100→98. | These are representative missing-resource/cooldown guards, not an exhaustive negative test for every recipe and skill. The first Bowyer callback was corrected; its failure does not imply the bound Board subtype itself was rejected. |
| ST-CRAFT-OTHER-MATERIALS | Actual craft/use consumes each remaining bound starter input as designed and produces only normal unrestricted outputs; failed attempts do not mint outputs or consume the wrong item. | Disposable ordinary accounts/characters, seeded one bound resource category and matching bound tool/skill per route; effective Alpha 3 flags/acknowledgment remained off. | `StarterCraftMaterials`, `StarterWoodAndTailorMaterials`, `StarterScribeAndAlchemyMaterials`, `StarterReagents`, `StarterCraftTools`; `tinkering_live.py`, `tailoring_live.py`, `craft_families_live.py`, `craft_bowyer_live.py`, `craft_remaining_live.py`, `craft_cooking_live.py`, `tinkering_conversion_live.py`; corresponding stock `Def*` craft systems. | Accepted live recipes now include Blacksmith Dagger, Tinkering Gears and Scissors, WoodenChair, Shirt, LeatherCap, Shaft, Arrow, Runebook, Yellow Potion and FishSteak. One missing-resource Bowyer attempt failed without consuming its bound board. The Scissors attempt against bound cloth was refused without changing cloth. A Tinkering consumed-input/output state survived actual save/restart. Exact setup and deltas are in rows above and earlier material rows. | Still open: additional Tinkering recipes/tools, more per-category failure paths, ordinary output transfer/sale, and save/restart for other consumed material/output paths. Navrey cannot select T2A recipe-list menus; callback-driven cases are identified above. |
| ST-ECON-LEGACY-WARD | Legacy free Wards keep their existing behavior; new starter Wards remain owner-bound and cannot be sold/transferred. | Disposable host `work/alpha3-starter-economy-host` on port 2595. Before fixture creation: 10 loaded Wards (8 marked, 2 unmarked), both unmarked in containers and none in the world. After cleanup and save/restart: 8 loaded Wards (6 marked, the same 2 unmarked), both unmarked in containers and none in the world. Alpha 3 flags/acknowledgment stayed off. | `BackpackWard` `Deserialize` (v0/v1 leaves `_starterIssued` false; v2 reads persisted marker), `TheftProtectionService.Configure`/`IssueStarterWard` (issuance is a character-creation callback); `StarterSaleEligibilityMatrixTests.UnmarkedBackpackWardRemainsEligibleForNpcSaleAndResale`; test-only `StarterEconomyProbe wardscan|legacyward|place|vendor|item|cleanup`; `legacy_ward_live.py`; two independent ordinary clients with distinct absolute session paths. Shard focused run `20260928T124036175Z-4f5389` passed 2/2. | The source-policy test explicitly listed `BackpackWard` with positive `GenericSellInfo` value and confirmed the unmarked instance remains sellable/resellable; the 41-type starter matrix confirms its marked form remains ineligible. The live probe seeded a fresh unmarked ordinary Ward; clients completed secure trade owner→buyer and buyer placed the same serial in player-vendor stock. Staff confirmed `type=BackpackWard`, `nontransferable=False`, `root=PlayerVendor`, `vendorStock=True`. The first driver attempt had the clients apart; after placing both together the stock secure trade passed. Cleanup removed the fixture and two test characters, including their marked starter Wards. After the 08:10 UTC save and exact server restart, the read-only scan returned 8/6/2 and the two unmarked Wards remained in containers. | Live NPC acceptance is recorded in the following `ST-ECON-NPC-LEGACY-WARD` row. Broader old-world production population/location review remains open. |

| ST-ECON-NPC-LEGACY-WARD | An unmarked legacy Ward is listed and sold by an ordinary Blacksmith; the same serial enters buyback stock and can be repurchased. A marked starter Ward is excluded. | Disposable UOR/Felucca host on `127.0.0.1:2595` (host PID 21776), fresh ordinary `StarterWardSale` at Yew, admin PID 13900 and player PID 9776. Dedicated role directories `work/alpha3-legacyward-sale-20260928/{admin,player}` with separate four-file Navrey sessions (`client4.*`). `[ShardRulesStatus` showed Alpha 3 acknowledgment false and baseline flags only. Cleanup removed fixture/character/account and a new save snapshot was published at 09:30:17 before exact-process shutdown. | Test-only `StarterEconomyProbe` SHA-256 `E0FE19954DB01CF5E4987C2ADBE0BA12E4509659D741D4D41881B8E807D07A07`; `tests/scenarios/starter-economy/npc_legacy_ward_sale_live.py` run against the dedicated `client4` file set; production `BaseVendor.VendorSell`, `OnSellItems`, Blacksmith `GenericSellInfo`, and NPC buyback. | Ordinary client listed unmarked Ward serial `0x4007E840` at 10 gp and sold it (gold +10); marked starter Ward did not appear. The same serial entered Blacksmith stock at 19 gp and was bought back (gold -19). Staff verified `BackpackWard`, `nontransferable=False`, root `PlayerMobile`, `vendorStock=False`. The first run exposed a fixture-order defect: moving the Blacksmith reloads its sell list. The probe now places it before adding the test type; the diagnostic verified live pack enumeration and actual sell-info state. Final ordinary-client case passed. | Closes live NPC sell/repurchase for legacy Wards. Does not close broader old-world production population/location review. |


These cases close direct and nested bound-item secure-trade/player-vendor routes for the 41 emitted starter types and earlier tested wrappers, prove direct scissors/Salvage Cloth/Salvage Ingots behavior for covered outputs, and prove live NPC sales of ordinary Blacksmith ingots, Tinker Scissors, and Tailor Shirts while bound inputs remain protected. The transfer matrix found the seed capacity shortfall before any acceptance result; the disposable setup now raises P1 Strength to 55. The 41-case run used state and server invariants because refusal narration did not appear. Its paired characters/vendor/items were removed by the reviewed test-only cleanup command and the host autosaved at 04:15. The legacy Ward row additionally closes ordinary-client trade/player-vendor intake, disposable save/restart no-op preservation, and live Blacksmith sell/same-serial repurchase for unmarked Wards; automated policy confirms the unmarked form remains NPC-sale eligible while the marked form remains excluded. Still open: a broader old-world production population/location review; NPC gump/sale and repurchase interactions for remaining distinct vendor families; other conversion tools and material consumption; and post-protection loss/death paths.

The approved package contract is in Section 16.1 of
`ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md`. The active UOR character-creation
path in ModernUO begins by adding a backpack, a red book, **1,000 gold per character**, a dagger
and a candle. Profession-specific stock equipment is added later. The repeatable gold stack is
incompatible with the approved approximately 500-gold **once-per-account** grant.

## Starter gold integration

`CharacterCreation.StartingGoldAmount` is a narrow optional resolver at the stock backpack
creation point. When unset, stock creation still grants 1,000 gold; a zero result suppresses the
gold stack without changing the other starting items. ShardContent installs
`StarterGoldPolicy.ResolveAmount` at startup. Its `alpha3StarterGold` feature flag defaults to
false and requires `alpha3EnablementAcknowledged` to enable. While disabled, it preserves stock
behavior.

When enabled for an ordinary player, the policy grants 500 only when the account has no recorded
starter-gold entitlement, no other current character and no prior recorded game time. It records
the account-level entitlement whether it grants the 500 or finds evidence of an earlier start.
The account tag remains after character deletion and is saved with the account. Staff creation
retains stock behavior. A missing account reference grants zero, avoiding an untracked grant.

Focused tests cover the amount/eligibility table, explicit flag acknowledgement, and the actual
stock backpack path with both a 500-gold result and a suppressed stack. The full ShardContent
suite passes.

On September 27, 2026, a disposable copy of the accepted Alpha 2b world loaded current content
assemblies with `alpha3StarterGold` and the Alpha 3 acknowledgment enabled only in that copy.
A temporary administrator probe created a synthetic ordinary account and called the installed
creation resolver for two characters. The first returned 500; the second returned zero. Both
characters were deleted, the disposable world saved and restarted, and a replacement character
on the reloaded account still returned zero. The synthetic account was deleted and the disposable
world saved again. The temporary probe assembly was removed and the scratch configuration was
restored to the source-disabled flag state. No shared world or account was changed.

The same disposable host then accepted a fresh account through Navrey's normal login and
`createcharacter` packet path. The resulting ordinary character entered Felucca with 500 gold;
opening the backpack and reading its contents showed exactly one 500-gold stack alongside the
stock book, dagger, candle and profession items. The client disconnected, the disposable world
saved and shut down, and the scratch configuration was restored to source defaults. The shared
world was untouched. This proves the new-account client creation and backpack result as well as
the earlier synthetic account-tag deletion/save/restart boundary; a second real-client creation
on the same account has not been rehearsed. The source flag remains **off**. Review of pre-existing accounts with deleted characters also remains required before
enablement. In particular, a pre-existing account whose last character was deleted before this
entitlement existed and whose saved game time is zero cannot be classified from the current
character count alone; the account population must be reviewed when scheduling activation.

## Archetype package selection and stock overlap

The active UOR profession file exposes Warrior, Mage and Blacksmith; Advanced supplies its own
selected skills. `StarterPackagePlanner` now maps those selected skills to one primary combat
package and an ordered set of craft categories. The highest selected Archery, Magery, Swords,
Macing or Fencing value wins; an equal value keeps the first selected skill. Parry requests a
shield only when the selected combat package is melee. Blacksmith, Tinkering, Tailoring,
Carpentry, Fletching, Inscribe, Alchemy and Cooking each identify an independent one-time craft
category. The gated issuance observers use this selection to choose the actual grants.

| Active creation choice | Stock selected-skill grants relevant to Alpha 3 | Approved-package gap |
| --- | --- | --- |
| Warrior (Tactics 50, Healing 45, Swords 5) | Tactics and Swords each ask for a sword; Healing adds 50 bandages and scissors; the profession path equips studded armor. | Select one appropriate Standard sword, preserve modest armor, bind the 50 bandages and issued gear, and avoid duplicate scissors. |
| Mage (Magery 50, Meditation 50) | Magery adds a 30-each reagent bag, three low-circle scrolls, a low-circle spellbook, robe and hat. | Replace the reagent grant with 50 each of the classic reagents under nonmergeable starter provenance; keep the book low-circle and ordinary. |
| Blacksmith (Blacksmith 50, Tinkering 45, Mining 5) | Blacksmith adds 50 iron ingots, tongs and two pickaxes; Tinkering adds tools and three random parts; Mining adds another pickaxe. | Grant the selected craft categories once per account, tune the approved material quantities, mark unconsumed inputs, and prevent free tool/material extraction. |
| Advanced | Each positive selected skill runs its stock `AddSkillItems` branch, so hybrid selections may stack overlapping weapons, tools or consumables. | Apply the same selected-skill plan after stock skill validation and replace overlapping stock grants with the approved bounded package. |

Both new starter gates remain off, so the ordinary server still issues stock archetype gear and
materials. The planner supplies the selection policy for the gated replacements below; their
remaining consumption and economy checks prevent activation.

The disabled and validation-blocked `alpha3StarterCombatGear` gate now replaces the stock dagger
with a character-owned fallback and uses the selected strongest combat skill for one primary
package. Melee receives a Standard Katana, Club or Kryss, two modest Studded pieces, an optional
Wooden Shield for Parry and 50 bound bandages. Archer receives a Standard Bow, two Leather pieces,
100 bound arrows and 50 bound bandages. A character that selected Magery receives the stock
low-circle spellbook content in a bound book and 50 of each classic bound reagent; the stock
reagent bag and three stock scrolls are removed. The stock combat weapon and armor overlaps are
removed before issuing the primary package. A separate per-character account tag prevents
duplicate callback grants or replacement after loss. Equipment has a persisted owner, remains
nontransferable, and moves with that owner through death for four logged-in hours; bound
consumables do not mix with ordinary stacks and cannot enter commodity deeds.

A single disposable server probe on September 27, 2026 enabled both starter gates in memory and
checked all eight craft material/tool categories plus synthetic Warrior, Archer and Mage paths.
The combat checks found exactly one intended weapon, expected armor, shield, ammunition,
bandages, low-circle book and reagents; no tested unrestricted stock overlaps remained. Repeating
the Warrior callback did not duplicate its package. The probe deleted its account and characters,
saved, shut down, and restored the scratch assembly list. This is an issuance check; ordinary
client creation, real combat, spellcasting, healing, ammunition use, save/restart of new equipment,
death timing, transfer, vendor, salvage and other economy paths remain release checks. The source
flag is off and validation rejects enabling it.

The stock small BOD combine path accepted subclasses of requested equipment and did not inspect
the permanent transfer marker. UOContent now rejects `Nontransferable` equipment before combining
it. A focused test proves a bound Katana subclass leaves the deed and item intact while an
ordinary Katana still advances the deed. Normal crafted output from starter inputs has no bound
marker, so this guard does not reduce its ordinary BOD eligibility. Other economy routes still
need the combined release matrix.

The material implementation covers Blacksmith, Tinker, Tailor, Carpenter, Bowyer, Scribe,
Alchemist and Cook.
A creation observer uses selected skills and their initialized base values, removes their
unrestricted stock ingots, parts, cloth bolt, boards, feathers and shafts, then grants the
approved 250/200 ingots, 300 cloth with 50 leather, 250 boards, 200 boards with 100 feathers,
75 blank scrolls with 50 of each classic reagent, 75 bottles with 50 of each classic reagent,
or 60 raw fish-steak attempts with two kindling.
Separate once-per-account category tags prevent later characters from reclaiming each package;
a per-character processing tag prevents a repeated callback from deleting materials acquired
after creation. Starter material subtypes retain character ownership through serialization,
refuse transfer and ordinary-stack merging, stay with the character on death, and cannot enter
commodity deeds. Stock scissors refuse to convert the bound cloth because it is nontransferable.
The T2A blacksmith resource selector accepts ingot subclasses for crafting. The new
`alpha3StarterCraftMaterials` flag is false and validation refuses enabling it while
economy routes remain unfinished. The same creation observer now replaces stock Tongs,
Pickaxes, Tinker Tools, Sewing Kits, Saws and Mortar/Pestles with owner-marked Standard
tools, and supplies a Fletcher's Tool or Scribe's Pen when those craft skills were selected.
It removes stock tool duplicates, runs once per character, and supplies a bound tool on a later
character even when that account's one-time material entitlement was already claimed. Tool
types retain their stock craft/harvest behavior, refuse direct transfer, and use the owner's
logged-in four-hour timer for death protection. The combined disposable creation probe passed
all eight material quantities and found exactly one corresponding bound tool, with no stock
tool left, for Blacksmith, Tinker, Tailor, Carpenter and Alchemist. Bowyer and Scribe each
received the new tool absent from stock creation. A second Blacksmith on the same account
received no second material grant but did receive bound tools. The scratch account and
characters were removed before save, the server shut down, and the probe assembly list was
restored. The tool path has not passed a craft-menu or economy rehearsal.
Craft-menu acceptance,
save/restart, account deletion/recreation and consumption need a disposable runtime rehearsal.

On September 27, 2026, a disposable copy of the accepted Alpha 2b world loaded the current
content assembly and a temporary probe. The probe temporarily enabled the craft flag in memory,
issued each of the first five supported packages to synthetic characters, and verified all stated
quantities and removal of stock unrestricted resources. Calling issuance twice did not increase
the first Blacksmith grant; after deleting that character, a second Blacksmith on the same
account received zero ingots and zero stock ingots. The probe removed its characters and account
before the scratch world's save. The server shut down, and its temporary assembly list was
restored. This covers creation-time grant and account-tag behavior, not resource consumption,
save/restart of bound items or all trade/conversion routes.

A second scratch run on September 27 extended the probe to Scribe and Alchemist. It confirmed
75 bound scrolls or bottles, 50 each of all eight classic reagents for each category, and
removal of the stock two scrolls or four bottles. The scratch server was shut down and its
temporary assembly list restored. These are issuance checks; consuming the subclasses through
actual inscription, alchemy and spellcasting remains open.

A third scratch run on September 27 confirmed the Cook category: the probe received 60 bound
raw fish steaks and two bound kindling, and no unrestricted stock cooking ingredients remained.
Its character and account were removed, the server shut down, and its temporary assembly list
was restored. Cooking on a heat source and the fate of the produced ordinary food still need
gameplay verification.

A separate fresh Navrey account used the ordinary `createcharacter` packet on the disposable
host with the craft and combat starter flags enabled in memory only. Navrey's fixed Advanced
selection chose Alchemy and Anatomy. After opening the backpack, the client saw 75 empty bottles
and 50 of each classic reagent, matching the Alchemist grant; no second combat package appeared.
The client inventory reports stock item names, so it cannot establish the bound item subtype.
The earlier server probe establishes that subtype for a synthetic creation. The client stopped,
the disposable world saved and shut down, and the temporary flag assembly and credential file
were removed; the source flags remain disabled.

## Remaining package work

The player-facing `[Welcome` command now explains physical Backpack Ward priming, consumption
and two-minute theft protection separately from the permanent invisible Loot Protection
entitlement and its ten-minute per-offender monster-corpse restriction. A creation hook prompts
new ordinary characters to read it after entering the world. An isolated Navrey login confirmed
that the command delivered all five lines to a player; a later fresh-client creation received the
creation-time prompt after entering Felucca.

The shard-owned post-creation hook replaces stock `Scissors` pairs from selected skill packages
with one protected, permanently marked `StarterScissors` pair when `alpha3StarterScissors` is
enabled. A persisted per-character account tag prevents repeat callback issuance and replacement
after the pair is lost. A disposable rehearsal began with two stock pairs, invoked the hook twice,
and found exactly one marked pair and no stock pair. After deleting the marked pair and saving
and restarting, another invocation granted none; the test account was then removed. The ordinary
Healing-selected creation, transfer, owner movement, and death-boundary cases are recorded in the
[Phase D readiness checkpoint](Alpha-3-Starter-Scissors-Readiness.md).
The Alpha 2 physical Ward creation hook now
marks its one free newly issued Ward with a persistent character owner, an account issuance tag,
and permanent `Nontransferable` status. The marked Ward can move among nested containers in its
owner's equipped backpack, but player movement to another mobile, the ground, another backpack,
or a bank is denied. The player-death callback deletes unused marked Wards. Ordinary purchased or
crafted Wards retain their prior account-binding and death rules. A disposable administrator
probe exercised duplicate issuance, same-account sibling binding refusal, world/mobile/other-backpack transfer refusal,
nested-bag movement, ordinary-Ward behavior and death-callback deletion; all reported true. The
probe account was removed, the disposable world saved and shut down, and the temporary probe
assembly was removed. A separate fresh-client character creation delivered a marked Ward. An
administrator read the owner and nontransferable marker, saved the world, restarted the disposable
server, and confirmed the same Ward still had its valid marker. An actual `PlayerMobile.Kill()` then
left the character dead, deleted the unused Ward, and left no marked Ward on the corpse. The
disposable character, account and corpse were removed, followed by a final save and shutdown.
The Ward's existing rune artwork appears as "recall rune" in Navrey's initial inventory listing;
single-click returns "a backpack ward". This presentation should be reviewed before release.
Legacy free Wards issued before the new marker are not retroactively marked; review of that
existing population remains a release check.

The universal organization bag is now implemented as `StarterBag`, gated by the disabled
`alpha3StarterBag` flag and the Alpha 3 acknowledgment. It is issued once to an ordinary new
character, is permanently nontransferable, and follows four logged-in hours of death protection.
Its contents are routed by each item's ordinary death rule: the protected bag cannot shelter
ordinary loot, and a blessed item is retained even when the bag itself goes to a corpse. A
disposable shard probe invoked issuance twice and killed synthetic characters before protection
expired and at exactly four hours. It confirmed one bag per character, the bag's expected death
destination, and ordinary and blessed contents inside both direct and nested containers. The
scratch flag and assembly list were restored after the probe.

A second disposable rehearsal created an ordinary synthetic account and player with one issued
bag containing two daggers with different loot types and a nested bag holding gold. The world
saved and shut down; after restart, the administrator probe found the same player and bag serials,
one bag after invoking issuance again, the persisted owner marker, contents, nontransferable
status, and active death protection. The probe account and player were deleted, the world saved
again, and the scratch server shut down. Its temporary probe assembly and enabled flag were
removed. This verifies the bag's save/restart boundary.

A fresh account then used Navrey's normal `createcharacter` packet on the disposable shard with
only `alpha3StarterBag` and its acknowledgment enabled. The character entered Felucca, opened a
backpack containing one bag, and a single click identified it as "a starter bag." A client
ground-drop attempt returned that same bag to the backpack. The administrator probe inspected
the actual created character and confirmed exactly one `StarterBag` with the character's owner
serial, permanent nontransferable status, and active death protection. The test account and
character were deleted, the disposable world saved and shut down, and its probe assembly and
configuration were restored.

A third disposable probe exercised a `StarterBag` instance through the stock item callbacks.
Direct drops to the world or another mobile and moves into an ordinary nested bag or bank box
were refused, leaving the bag in its owner's backpack. `GenericSellInfo` rejected it for both
sale and resale even with `StarterBag` explicitly listed at a positive price. The bag does not
implement the stock scissor-conversion interface. This covers the direct item and NPC resale
boundaries; actual two-client secure trade, player-vendor flow, other conversion tools, and
post-protection corpse acquisition still require their full release matrix. The scratch probe
assembly was removed after the world save and shutdown.

The gated archetype equipment, consumables and materials exist, but their actual crafting,
combat, transfer, salvage and death matrices remain release work. Stock profession items still
need review against the Standard-quality, Starter Protection, resale and account-level material
entitlement rules. Remaining Ward transfer routes and unconsumed crafting inputs need their full
economy and death matrices; normal crafted outputs must remain unrestricted. These are release
blockers, not effects of enabling the starter-gold or scissors flags by themselves.

## Combined ordinary creation packet matrix, September 27

A disposable accepted-world shard enabled only the Alpha 3 stats, scissors, bag and gold flags
with its test-only acknowledgment. The Navrey creation command now accepts profession IDs 0–3
and, for Advanced, two UOR skill IDs. Four fresh ordinary accounts used normal creation packets:

| Creation choice | Observed STR/DEX/INT | Gold | Scissors and starter bag |
| --- | --- | ---: | --- |
| Warrior (1) | 50/40/30 | 500 | One scissors pair, one bag |
| Mage (2) | 30/30/60 | 500 | One scissors pair, one starter bag alongside the stock Mage bag |
| Blacksmith (3) | 60/30/30 | 500 | One scissors pair, one bag |
| Advanced (0), Healing 50 and Anatomy 50 | 42/42/36 | 500 | One scissors pair, one bag |

The Advanced Healing selection is the ordinary client path that could include stock scissors;
its backpack had exactly one pair. Single-click identified its bag as “a starter bag.” The
client's inventory uses ordinary item names, while the earlier server probes verify the bound
subtypes. A first Warrior packet exposed a callback-registration ordering defect: a later Ward
`CharacterCreatedHandler =` assignment removed earlier stat, scissors and bag callbacks while
the separate gold hook still ran. Changing that registration to guarded `+=` allowed all four
hooks and the Ward callback to coexist. The corrected ShardContent suite passed 210 tests, and
all four fresh client creations then matched the table. The test-only flags were removed from
the disposable host after the matrix; source flags remain off. Transfer, death and economy
matrices remain as listed above.

The same registration audit found that the automatic murder service used `=` for the shared
`PlayerMobile.PlayerDeathHandler` and lacked a Configure guard. It now registers once with
`+=`, preserving the starter Ward and bag death observers regardless of Configure order. The
210-test content suite still passes. On a disposable accepted-world shard with the starter-bag
gate enabled only in its local copy, an administrator client ran both death observers together.
The Ward probe reported one issued bound Ward, transfer refusals, permitted nested movement,
ordinary-Ward separation and destruction at the death callback. The bag probe used actual
`PlayerMobile.Kill()` for protected and exactly four-hour cases: the bag stayed in the backpack
before expiry and moved to the corpse at expiry; ordinary direct and nested contents moved to
the corpse, blessed contents stayed in the backpack, and the bag emptied in both cases.
The bag transfer matrix also passed. The scratch server was saved and stopped, and its rules
copy was restored to the disabled source flags. Raw client evidence is in
`work/alpha3-housing-client/deathprobe3.log`; broader real-client death coverage remains open.

## Phase D starter-scissors movement and death checkpoint — September 28, 2026

The accepted combined ordinary-creation packet matrix above already used Advanced with Healing
selected and observed exactly one pair despite the stock Healing scissors. It also records the
paired trade/vendor result from the 41-type bound-item matrix: `StarterScissors` stayed in its
owner's backpack and did not enter trade or player-vendor stock. The earlier issuance rehearsal
already deleted the pair, saved/restarted, invoked issuance again, and verified no replacement.
Those accepted cases were reused without repeating their clients or server runs.

For the missing movement and death routes, a separate copy of the disposable Alpha 2b rehearsal
host was run on loopback port 2595 with `alpha3StarterScissors` and its acknowledgment enabled
only in that copy. A one-use probe exercised the actual `Item.OnDroppedInto` callback and actual
`PlayerMobile.Kill()` pipeline; it created only synthetic players and removed them and their
corpses before a confirmed world save. The probe source SHA-256 is
`53D4383427799EA078A1BA93A36414B10ECCF1F4E016595C728F17AAEAF99103`.

- The owner could move the pair from an owned nested container back to the equipped backpack;
  moving it into a nested container was refused, matching the stock `Nontransferable` movement
  callback.
- With `PlayerMobile.GameTime` set to 14,399 seconds, actual death left the scissors in the
  backpack. At exactly 14,400 seconds, actual death moved it to the corpse.
- At and beyond the protection boundary, `Nontransferable` remained true, `OnDroppedToMobile`
  refused the pair, and an explicit `GenericSellInfo` list still rejected sale and resale.
- Both death cases completed with the player dead and the pair at its expected destination. The
  synthetic player's normal body ID avoided malformed-corpse diagnostics. The confirmed save
  completed after fixture cleanup; the exact scratch server process stopped and the clone's
  original disabled feature flags and assembly list were restored.

The death timing test sets the persisted game-time value directly to each boundary instead of
waiting four wall-clock hours. It exercises the real death routing method at both values; the
existing unit boundary test separately checks 14,399, 14,400, and 14,401 seconds. No source or
deployed feature flags were enabled by this rehearsal.

## Owner rulings and Phase E closure — September 28, 2026

### Rulings

**Starter-issued items** (40 types, including the free starter Backpack Ward) are stock UOR newbied and permanently nontransferable. Stock ModernUO then keeps them:
- loose in the owner's backpack only, never in a bag;
- through every death, murderer or not.

The owner chose the stock no-bags rule deliberately: a bag can travel, and bound contents would otherwise need checks on every route a bag can take.

**The starter bag** is an ordinary stock `Bag`.

**Ordinary newbied items** stay protected inside bags (`KeptItemDeathRouting`), except for murderers, as stock UOR. This rule is always on; it has no feature flag.

### Code

- The timer and the custom death overrides are removed. So are the `StarterBag` class, the Ward's nested-bag exception and the Ward's destroy-on-death handler.
- Existing marked Wards become newbied when loaded.
- The test `StarterDeathRuleTests` fails if any starter type overrides death routing again. It also confirms the `StarterBag` type is gone.
- Full Shard suite: 263/263, run `20260928T170808008Z-8da2fd` (the final source, including the Ward change).

### Live cases

**Setup:**
- A disposable copy of the dev distribution with Alpha 3 acknowledgment, `alpha3StarterBag` and `alpha3StarterScissors` on.
- `automaticMurderAdjudication` and `knockedOut` were off in the copy only, so `[set Kills 5` produces a murderer.
- Fresh ordinary account and character (Warrior, profession 1), created through the shard account request and Navrey `createcharacter`.
- A staff Navrey session issued `[kill`, `[res` and `[set`.
- The ModernUO Young system (on by default) was cleared on the test character with `[set Young false`, because Young keeps every item on death.

**Driver:** `tests/scenarios/starter-death/starter_death_live.py`.

**Cleanup:** the copy and its throwaway accounts were deleted afterwards.

| Case | Expected | Observed |
| --- | --- | --- |
| E-ISSUE | One plain bag, scissors and Ward at creation | Pass. One regular `bag`, one pair of scissors, one marked Ward |
| E-NOBAG | Starter items refused by any bag | Pass. Scissors and Ward refused by the plain bag; both stayed loose |
| E-DEATH | Ordinary death: starter items and newbied items kept, even from inside a bag; regular bag to corpse | Pass. Newbied katana moved into the bag returned to the backpack. Dagger, scissors and Ward kept. Regular bag went to the corpse |
| E-MURDERER | Murderer death: newbied items drop; bound starter items kept | Pass. Katanas and dagger went to the corpse; scissors and Ward kept |

### Limits

- The murderer case ran as a continuation after a notoriety-check bug in the first script version: it read `6` instead of `"Murderer"`. The script is fixed.
- Save/restart was not repeated. Loot type is saved by stock code, and issuance persistence was accepted earlier.
- Blessed items inside bags follow the same code path as newbied, but no blessed case was run.

## Owner rulings and Phase G closure — September 28, 2026

### Rulings

Full text and the reviewer's stock-comparison reasoning for each is in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md) (G-1 through G-9); design doc §16.1 is updated to match. Summary:

- **G-1/G-6 (package selection and armor):** the custom "one combat package" selection and its `RemoveArmor`/`RemoveExact` deletion logic are gone entirely. Stock `CharacterCreation.cs` grants (profession block + per-skill `AddSkillItems`) run untouched. Two quantities are raised (25→100 arrows, 30→50 per reagent), and two stock gaps are patched narrowly: a Standard leather chest+legs when Archery is the strongest selected combat skill (stock gives archers no armor), and a Standard wooden shield when Parry is selected with a melee package (stock never grants one). A third gap is patched the same way: 50 stock Bandages when a Melee/Archer package doesn't already have them from Healing/Veterinary/Anatomy.
- **G-2 (dagger):** the universal stock `Dagger` stays exactly as stock grants it. `StarterDagger` is deleted.
- **G-3 (binding):** newbied only, not `Nontransferable`, for all combat gear/consumables. `StarterCombatGear.cs` and `StarterCombatConsumables.cs` (13 bound types) are deleted. A `LootType.Newbied` item is now also blocked from vendor sale (alongside `Nontransferable`) by the existing shard-added guards in `GenericSell.cs`/`PlayerVendor.cs`, closing the resale faucet without reintroducing binding; trade, drop and banking stay open. Named exception: the mage `Spellbook` stays stock `LootType.Blessed` (owner ruling: spellbooks stay blessed) and is not covered by the vendor-sale guard, so it remains vendor-sellable — a minor accepted residual, not a gap to close by weakening its death protection.
- **G-7:** closed — G has no bound items left to discard. The general discard-path question stays open for D's scissors and F's Ward.
- **G-5 (bug):** fixed structurally. The arrow top-up is gated only on "was Archery selected" (any position), never on which combat package is primary, so a secondary Archery pick can no longer lose its arrows.

### Code

- Deleted: `StarterCombatGear.cs`, `StarterCombatConsumables.cs` (13 bound types removed from the starter type census, 40→27).
- Rewritten: `StarterCombatIssuance.cs` — from full package replacement to five narrow, idempotent top-ups/patches (arrows, reagents, archer leather, Parry shield, bandage fallback), gated on `alpha3StarterCombatGear` and a per-character account tag, unchanged from the prior issuance-guard pattern.
- `GenericSell.cs` (ModernUO, shard-owned since commit `16f6189ae`): added `NontransferableItemPolicy.ContainsVendorRestricted`, checked by `GenericSellInfo.IsSellable`/`IsResellable` and `PlayerVendor.OnDragDrop` — `Nontransferable` OR `LootType.Newbied` blocks vendor sale; the original `Contains` (Nontransferable only) stays unchanged for `SalvageBag.CanResmelt`.
- Test updates: `StarterSaleEligibilityMatrixTests.cs` (27-type bound census + two new tests: Newbied-not-Nontransferable is vendor-blocked; ordinary Regular-loot items stay sellable), `StarterDeathRuleTests.cs` (27-type census), `StarterBoundVendorTests.cs` (ModernUO/UOContent.Tests — three new tests against real `PlayerVendor`/`GenericSellInfo`/`PlayerMobile.CheckTrade`/`SalvageBag` objects proving Newbied is vendor-blocked but trade/salvage-eligible), `StarterEconomyProbe.cs` (removed references to the deleted types). A pre-existing gap in `BritanniaRenaissance.Content.Tests.csproj` — Serilog wasn't copy-local, so any test touching `Server.Item`'s static members failed with `FileNotFoundException` — was fixed by adding Serilog/Serilog.Sinks.Async/Serilog.Sinks.Console references; this was blocking, not specific to G, and is now fixed for future tests too.
- Full Shard suite: 255/255. UOContent `StarterBoundVendorTests`: 11/11. Verification run `20260928T190353213Z-21b497` (Shard) and `20260928T184521390Z-b3e229` (UOContent, prior to the final spellbook-related revert, unaffected by it).

### Live cases

**Setup:** disposable host `phase-g` with `alpha3EnablementAcknowledged` on (the disk copy; `alpha3StarterCombatGear` itself cannot be set on disk — the validator hard-rejects it outright, per H-6/G's plan entry). A test-only Administrator command (`tests/scenarios/starter-combat/StarterCombatFlagOverride.cs`, loaded as a scratch assembly) flips `ShardRulesConfiguration.Settings.FeatureFlags.Alpha3StarterCombatGear` to `true` in memory after the server has already booted successfully with it `false` on disk, so it never touches `Validate()` or the deployed config; discarded on restart. A companion `StarterCombatInspect` command reports every equipped/backpack item's type, `LootType` and `Nontransferable` status directly from the server, for verification independent of client tooltip text.

Seven fresh ordinary accounts used the normal Navrey `createcharacter` packet: Warrior, Mage, Archer (Advanced: Archery+Camping), Melee+Parry (Advanced: Swordsmanship+Parrying), a two-weapon hybrid (Advanced: Swordsmanship+MaceFighting), and two Archery/Swordsmanship orderings to probe G-5.

| Case | Expected | Observed |
| --- | --- | --- |
| G-CREATE-WARRIOR | Stock profession armor (full 7-piece studded suit) and per-skill weapon/bandages kept as-is, all Newbied | Pass. Bascinet/Gorget/Chest/Arms/Gloves/Legs/ThighBoots + Katana equipped; 50-bandage stack (Healing) plus a separate stock 3-bandage stack and a second stock Katana (Tactics' own skill-item grant, independent of Swords') — all Newbied, none Nontransferable. See Limits. |
| G-CREATE-MAGE | Stock spellbook/robe/hat, reagents raised 30→50 each | Pass. `BagOfReagents` present (amounts not independently re-verified live past the unit-tested top-up logic — see Limits); Spellbook equipped, stock `LootType.Blessed` (unchanged, by design) |
| G-CREATE-ARCHER | Leather chest+legs patch, 100 arrows, 50 bandages, no shield | Pass. `LeatherChest`, `LeatherLegs`, `Arrow` amount=100, `Bandage` amount=50, all Newbied; no shield |
| G-CREATE-PARRY | Shield patch, 50 bandages | Pass. `WoodenShield` equipped and Newbied; `Bandage` amount=50 |
| G-CREATE-HYBRID | Both stock weapons kept, no dedup | Pass. `Katana` equipped and `Club` in backpack, both Newbied |
| G-5-A/G-5-B | Archery selected in either input order still yields 100 arrows | Pass, both orderings (Swords,Archery) and (Archery,Swords) produced `Arrow` amount=100. Both orderings actually resolved Archery as the *stronger* selected skill (leather armor patch fired both times), so neither is a direct "Archery loses as secondary" live repro; the fix's unconditional gate (`Selected(SkillName.Archery)`, independent of `selection.Combat`) is confirmed correct by source inspection instead — see Limits. |
| G-VENDOR | Newbied combat gear blocked from vendor sale; still tradeable/droppable/salvageable | Verified via `StarterBoundVendorTests` (UOContent.Tests) against real `PlayerVendor`/`GenericSellInfo`/`PlayerMobile.CheckTrade`/`SalvageBag` objects, not a live packet click-through — see Limits. |
| G-DEATH | Ordinary death: Newbied combat gear kept, Nontransferable Ward kept | Pass, live. `starter_combat_death_live.py` against `HParry`: 50-bandage stack and `WoodenShield` (both Newbied) and the Backpack Ward (Nontransferable) all survived an ordinary `[kill`. |
| G-MURDERER | Murderer death: Newbied combat gear lost; Nontransferable Ward kept | Not run live for G's own items — see Limits. Reused: Phase E's E-MURDERER case proved the identical code path (`Item.OnInventoryDeath`'s `CheckNewbied() && !parent.Murderer`) for a plain Newbied, non-bound Katana, which is the same item classification G's gear now uses. |

**Driver:** `tests/scenarios/starter-combat/starter_combat_death_live.py` (G-DEATH); manual `StarterCombatInspect` calls for the creation cases; `StarterBoundVendorTests.cs` for the vendor cases.

**Cleanup:** all sessions stopped, `phase-g` server stopped (no save needed) and removed via `Remove-DisposableHost.ps1`; leftover `work/accounts/H*.env` and session folders removed manually (they weren't tracked in `host.json` since these accounts were created by hand, not `New-TestCharacter.ps1`, to keep the flag override active across creations — see Limits). The real dev distribution was redeployed twice during this pass (once for a spellbook fix that was then reverted per owner instruction, once for the final reverted build); `Get-ShardStatus.ps1` confirms `alpha3StarterCombatGear` source and deployed both `false`, no process holds the distribution.

### Limits

- **Duplicate stock grants are visible for the first time.** Dropping the custom package-replacement system (G-1) means a Warrior ends up with two Katanas (Tactics' and Swords' independent `AddSkillItems` grants) and two Bandage stacks (Healing's 50 plus another skill's smaller stock grant). Both are pre-existing stock behavior the old custom code silently deleted; the owner's G-1 ruling explicitly chose "use stock as-is" over reintroducing that cleanup. Named, not fixed.
- **`New-TestCharacter.ps1` couldn't be used for the gated cases.** It restarts the server for every invocation (accounts are only created via a boot-time request file), which would have discarded the in-memory flag override before `createcharacter` could run. Live characters for gated cases were created by hand, reusing the same account/session mechanics (auto-account-creation is enabled shard-wide), with the flag set once per server lifetime immediately after boot.
- **G-CREATE-MAGE's reagent quantities weren't independently re-verified live.** The 30→50 top-up logic is covered by the same mechanism already exercised structurally for arrows (both use the same `TopUp`/`TopUpOrGrant` helpers) and isn't separately unit-testable without a live `PlayerMobile`/`World` environment (see the `StarterCombatIssuance.Issue` environment note below); accepted on code-path parity with the arrow case, which was independently confirmed live.
- **G-5's live cases didn't reproduce "Archery as secondary."** Both orderings tried resolved Archery as the character's strongest selected combat skill regardless of input order; the exact Advanced-creation skill-value allocation rule wasn't reverse-engineered further given time. The fix itself is unconditional by construction (source inspection), not order-dependent, so this doesn't weaken the fix — only the live repro attempt.
- **Vendor-sale blocking has no live packet-level click-through**, only the UOContent.Tests engine-level proof (real `PlayerVendor`, `GenericSellInfo`, `PlayerMobile.CheckTrade`, `SalvageBag` objects). Considered sufficient given it exercises the exact same guard code the packet handlers call.
- **The murderer-death case for G's own items wasn't run live.** This shard's `automaticMurderAdjudication` recalculates notoriety independently of a raw `[set Kills 5` edit (unlike the Phase E setup, which explicitly disabled `automaticMurderAdjudication`/`knockedOut` on its disposable copy for this reason). Reconfiguring those two Alpha-2 systems just for this G check was judged out of scope; Phase E's own E-MURDERER case already proves the identical code path for the identical item classification (Newbied, non-`Nontransferable`).
- **`StarterCombatIssuance.Issue()`'s full integration behavior has no shard-level xunit coverage**, unlike the reused stock-mechanism cases above. `BritanniaRenaissance.Content.Tests` has no live `PlayerMobile`/`World`/`Account` environment (it uses `RuntimeHelpers.GetUninitializedObject` throughout for exactly this reason), so `Issue()`'s five patches can only be verified through source inspection and the live disposable-host cases above — this was also true of the prior implementation, which had no dedicated `Issue()` unit tests either.
- **`paired_economy_cases.py`'s hardcoded-serial Katana case and `scissor_conversion.py`'s `nestedArmor` reference are now stale**, tied to the pre-G bound `StarterKatana`/`StarterStuddedChest` and a specific past disposable-host run's serials. Left as dated historical artifacts rather than edited, since they aren't re-run automatically.

## Owner rulings and Phase H closure — September 28, 2026

### Rulings

Full text and reasoning for each is in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md) (H-1 through H-6, plus the Cooking call); design doc §16.1 is updated to match. Summary:

- **H-3/H-4 (materials and tools):** newbied only, matching Feature G. All ~17 bound material/reagent types and 8 bound tool types are deleted. Plain stock item types are used directly, already newbied for free under this shard's UOR era, and already blocked from vendor sale by the same generic Newbied guard G-3 built (no new guard code). H-1's per-account entitlement ledger is unchanged and is now the *only* anti-faucet control, since binding no longer backs it up.
- **Two collisions, both resolved as additions rather than top-ups:** stock Tinkering grants zero ingots in any era (only three random parts), but Tinkering's own recipes consume ingots, so 200 are added; stock Tailoring's own grant (`BoltOfCloth`) can't be consumed as a `Cloth` resource, so `Cloth`(300)/`Leather`(50) are added outright.
- **Tool charges:** kept a fixed 50 uses (deliberate deviation from stock's own random 25-75), applied uniformly to stock-granted tools (top-up target) and newly-added ones (Fletcher's Tools, Scribe's Pen - stock grants no tool at all for Fletching or Inscription).
- **Cooking:** owner chose to top up all three stackable stock-granted proteins (raw lamb leg, chicken leg, fish steak; each 1→20) instead of the prior fish-only replacement, leaving kindling and the flour sack/pitcher at stock quantities.
- **H-2 (bug):** fixed structurally, the same way as G-5 - the redesign never deletes anything stock granted, so a second same-profession character on the same account simply keeps its own ordinary stock allotment untouched instead of losing it to a pre-entitlement-check deletion.

### Code

- Deleted: `StarterIronIngot.cs`, `StarterCraftTools.cs`, `StarterWoodAndTailorMaterials.cs`, `StarterScribeAndAlchemyMaterials.cs`, `StarterCookingIngredients.cs`, `StarterReagents.cs` (25 bound types removed from the starter type census; only `StarterScissors` (D) and `BackpackWard` (F) remain bound, 27→2).
- Rewritten: `StarterCraftMaterialIssuance.cs` - from stock-removal-then-replace to a uniform `ClaimOnce`/`TopUp`/`SetToolUses` pattern per craft category, gated on `alpha3StarterCraftMaterials` and the existing per-account entitlement tag (bumped to a new tag version since the grant shape changed).
- Test updates: `StarterSaleEligibilityMatrixTests.cs` (2-type bound census; the Newbied-vendor-block test extended to cover all of H's plain stock types alongside G's), `StarterDeathRuleTests.cs` (2-type census), `StarterEconomyProbe.cs` (all crafting seed/craft methods now construct plain stock types with an explicit Newbied stamp instead of the deleted bound subclasses; the salvage and NPC-sale probes now test the Newbied-guard directly instead of a now-nonexistent bound/ordinary type distinction).
- The ModernUO pin (`pinnedModernUoCommit`) was bumped to the vendor-guard commit (`df67e74b4917b4630089d30d01f9fb771c202e00`) in `shard-rules.json`, `world-generation.json` and `Alpha2bWorldGenerationConfigurationTests.cs`, since `Deploy-Alpha1Baseline.ps1` refused to run against the stale pin left over from before that commit.
- Full Shard suite: 230/230, run `20260928T200647938Z-a35d89` (after the pin bump).

### Live cases

**Setup:** disposable host `phase-h`, `alpha3EnablementAcknowledged` on disk (`alpha3StarterCraftMaterials` itself is validator-hard-rejected, same as G's combat gear). The shared `TestOnlyProbe` (generalized from G's feature-specific one) supplied `[TestOnlyFlagOverride Alpha3StarterCraftMaterials` and `[TestOnlyInventoryInspect`. `New-TestCharacter.ps1 -NoRestart` created all seven characters in one continuous server run (no restart between them, so the in-memory flag override stayed live): Blacksmith profession (covers Blacksmith+Tinkering+Mining together), and six Advanced characters pairing one craft skill each with Camping as a neutral filler (Tailoring, Carpentry, Fletching, Inscribe, Alchemy, Cooking).

| Case | Expected | Observed |
| --- | --- | --- |
| H-CREATE-BLACKSMITH | 250 IronIngot, stock Tongs/Pickaxe kept | Pass. `IronIngot` amount=250 (topped up from stock's 50); `Tongs` x1, `Pickaxe` x3 (2 from Blacksmith's own grant + 1 from Mining's), all Newbied |
| H-CREATE-TINKER | 200 IronIngot added (collision H-3a), stock 3 random parts + TinkerTools kept | Pass, same character (Blacksmith profession includes Tinkering). A *separate* `IronIngot` amount=200 stack appeared (not merged with the 250 stack - `Container.DropItem` doesn't auto-merge; see Limits), `Axle` x1 + `Springs` x2 (stock's random parts, a duplicate roll), `TinkerTools` x1 |
| H-CREATE-TAILOR | 300 Cloth + 50 Leather added (collision H-3b), stock BoltOfCloth/SewingKit left alone | Pass. `Cloth` amount=300, `Leather` amount=50 (both fresh additions), `BoltOfCloth` x1 and `SewingKit` x1 untouched, all Newbied |
| H-CREATE-CARPENTER | 250 Board (topped from stock's 10), stock Saw kept | Pass. `Board` amount=250, `Saw` x1, Newbied |
| H-CREATE-BOWYER | 200 Board + 100 Feather (topped from 14/5), FletcherTools added (stock grants no tool) | Pass. `Board` amount=200, `Feather` amount=100, stock `Shaft` x5 untouched, `FletcherTools` x1 added, all Newbied |
| H-CREATE-SCRIBE | 75 BlankScroll (topped from 2), 50-each reagents added via BagOfReagents, ScribesPen added | Pass. `BlankScroll` amount=75, stock `BlueBook` untouched, `BagOfReagents` x1 added, `ScribesPen` x1 added, all Newbied |
| H-CREATE-ALCHEMIST | 75 Bottle (topped from 4), 50-each reagents added, stock MortarPestle kept | Pass. `Bottle` amount=75, `BagOfReagents` x1 added, `MortarPestle` x1 untouched, all Newbied |
| H-CREATE-COOK | RawLambLeg/RawChickenLeg/RawFishSteak topped 1→20 each; Kindling/SackFlour/Pitcher untouched | Pass. All three proteins amount=20; stock `Kindling` amount=5 (from the Camping filler skill, not Cooking - see Limits), `SackFlour` and `Pitcher` untouched, all Newbied |
| H-PERSIST | Save/restart preserves every grant exactly | Pass. Saved, stopped, restarted `phase-h`, reconnected admin (`connected` correctly read `false` on the stale session beforehand), re-inspected HBlacksmith: identical serials and amounts for every item across the restart |
| H-VENDOR/H-TRADE/H-SALVAGE | Newbied craft materials blocked from vendor sale; still tradeable/droppable/salvageable | Not re-run live for H specifically - reused the generic UOContent.Tests proof from G (`StarterBoundVendorTests`), which covers any Newbied item, not just combat gear |
| H-2 | Second same-profession character on one account keeps its own stock grant, doesn't get zero | Not run live (would need a second character on an already-used account, which this session's tooling creates via a fresh account per name) - verified by source inspection instead: `ClaimOnce` is the sole gate and no deletion code exists anywhere in the rewritten file, so a second character's stock-granted items are structurally untouched regardless of prior claims |

**Driver:** manual `TestOnlyInventoryInspect` calls per character (no new Python driver needed for the creation/persistence cases).

**Cleanup:** all sessions and the server stopped; `phase-h` removed via `Remove-DisposableHost.ps1` (fully tracked in `host.json` since `New-TestCharacter.ps1` created every character, unlike G's manual account creation).

### Limits

- **Two harmless, unexplained stock quirks observed live, not investigated further:** the Blacksmith-profession character (Blacksmith+Tinkering+Mining, no Tailoring selected) also received a stock `BoltOfCloth` and `SewingKit`; likely part of Mining's own stock skill-item grant, which wasn't in scope for this trace (Mining isn't one of H's 8 craft categories). Neither item is touched by the shard's own code, so this doesn't affect the design either way.
- **IronIngot from Blacksmith and Tinker don't merge into one stack.** `Container.DropItem` doesn't auto-merge same-type items the way player drag-drop stacking does, so a Blacksmith+Tinker character ends up with two separate IronIngot stacks (250 and 200) rather than one 450 stack. Functionally identical for crafting (`ConsumeRes`/`GetAmount` sum across all matching items in a container regardless of how many stacks), just a cosmetic difference from the old bound design, which happened to merge them the same way for the same reason.
- **Tool charge (fixed 50 uses) wasn't independently confirmed live.** `TestOnlyInventoryInspect` doesn't report `UsesRemaining`; the mechanism (`IUsesRemaining.UsesRemaining` set via the same interface `Pickaxe` itself uses for its own stock-hardcoded 50) is simple and covered by a successful build, but not visually re-verified in the live pass.
- **H-2's fix wasn't reproduced with an actual second same-account character live**, only confirmed by source inspection (see the case table above). Reconstructing a true second-character-same-account scenario would need extending the test tooling to add a character to an already-used account rather than a fresh one per name.
- **No fresh live crafting-consumption pass for the redesigned plain stock types.** The starter audit's existing `ST-ECON-CRAFT-*` rows (Blacksmith Dagger, Tinkering Gears/Scissors, Carpentry chair, Tailoring shirt/leather cap, Bowyer shaft/arrow, Scribe runebook, Alchemy potion, Cooking fish) already proved stock crafting systems accept the *bound subclasses* as valid resource inputs via subclass-inclusive matching (`CraftItem.ConsumeRes`/`Container.GetAmount` use `Type.IsAssignableFrom`, confirmed by source trace); a plain stock type is if anything a safer case (no subclass matching at all), so this evidence is treated as reused and direction-confirming rather than superseded, but wasn't independently re-run against the new plain-type grants.

