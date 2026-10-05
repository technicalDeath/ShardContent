# Era cooking restore (Part A) readiness

**Decision:** Built and verified live on a disposable host (2026-10-05). **Not committed, not pushed, not deployed.** No flag; deploying turns it on. Closes the Alpha 3 open live check "Cooking menu reachability". Research, sources and the owner's sign-off are in [Cooking-Era-Restore-Research.md](Cooking-Era-Restore-Research.md). Part B (flour, water, dough and baking) is a separate item.

## What cooking does now
Double-click raw food, then target a heat source within one tile. After five seconds the Cooking skill decides the result: success puts one cooked food in the pack, failure burns the food. Walking more than three tiles from the heat source (or changing map) in that time burns it. A second attempt during the five seconds is refused. One item is used per attempt, even from a stack. No tool is needed; the starter pack is unchanged.

| Rule | Value | Source |
| --- | --- | --- |
| Heat sources | campfire, sandstone and stone ovens/fireplaces, fire pit, heating stand, Field of Fire, **small and large forges** | stock `IsHeatSource` list plus forges (era sources; stock's cooking-menu list also has them) |
| Success chance | the Cooking skill itself (`CheckSkill(Cooking, 0, 100)`); every food can be tried at 0 skill | era, owner ruling; the per-food `CookingLevel` minimum is no longer used |
| Stacks | one item per cook | stock, owner ruling |
| Delay, target range, walk-away distance | 5 s, 1 tile, 3 tiles | stock RunUO values, not era-verified |
| Reach | food must be in your pack or within two tiles, and not in another character's hands | added, mirrors `Kindling` |
| Messages | stock localized text: "I can't reach that." (1019045), "You must wait to perform another action." (500119), "You burn the food to a crisp! It's ruined." (500686) | stock |

## Build
- **ModernUO hook (the only engine change):** `Projects/UOContent/Items/Food/CookableFood.cs`: `OnDoubleClick`, a `CookTarget`, `FinishCooking`, a `CanCook` check run at both steps, and a pure `IsHeatSource(int)`. No save-format change (the class is source-generated and no field changed). Upstream ModernUO has never had the double-click; the dead target code was deleted in 2022 (`864440a05`). Nothing leaves the fork.
- **ShardContent:** no code change. New live driver `tests/scenarios/cooking/cooking_live.py`; docs.
- **Tests:** `ModernUO/Projects/UOContent.Tests/Tests/Items/UorCookableFoodTests.cs`.

## Verification
- **Unit:** `UorCookableFoodTests` 23/23 (heat-source ID ranges and neighbors, `Item` target reading, each raw food cooks to its counterpart). Full UOContent suite 1345 pass, 2 skipped, 1 fail: `AdvancedSearchTypesTests.Poison_ReferenceTypeParsedViaTypes`, the known fork test-registration clash, not from this work. Shard suite 424/424 earlier today (ShardContent unchanged by this item).
- **Live, disposable host `cook`** (copy of the dev distribution at ModernUO `eba68d2be` with `UOContent.dll` rebuilt from an isolated clone at that commit plus the cooking file; Advanced test character with Cooking and Camping, stock starter pack; driver `cooking_live.py`, run log `work/cook-live/run1.log`, scratch):

| Case | Result |
| --- | --- |
| H1-H8: campfire, sandstone oven, stone oven, fire pit, heating stand, fire field, small forge, large forge each turn 1 raw fish steak into 1 fish steak | pass (8/8; raw 20 down to 12, cooked 0 up to 8) |
| N1: an anvil as target consumes nothing | pass |
| W1: a second cook during the five seconds is refused with the wait message; one raw fish steak used | pass |
| M1/M2: raw lamb leg and raw chicken leg cook | pass |
| R1: raw food six tiles away gives "I can't reach that" and no cook | pass |
| B1: walking six tiles away burns the food (raw -1, no cooked food) | pass |
| E1: at base Cooking 0 a cook succeeds (first success on attempt 8 of 8 tried) | pass |
| E2: attempts at base 0 raise the skill (base 0.0 to 2.1) | pass |

Dev distribution, dev saves and the owner's accounts were not touched; the host and its accounts were removed.

## Named limits
- **Heat sources in the live run were movable items given the right graphic** (`[add item <graphic>`), because the test client can only target things by serial. A campfire lit from Kindling and a real town oven or fireplace (a map static, targeted by tile) were not exercised live. They use the same `IsHeatSource(int)`, which the unit test covers.
- **E1 does not separate the era formula from stock.** A character's effective skill includes a stat bonus (base 0 read as 19.2 here), so it never fell below stock's minimum of 10. The formula (`CheckSkill(Cooking, 0.0, 100.0)`, `CookingLevel` unused) is confirmed from the source.
- **Era-unverified values:** the five-second cook, the one-tile target range, the three-tile walk-away limit, and the failure fraction of an era stack cook (not built).
- **Eggs, pies, pizzas and mixes** are also `CookableFood` and now cook on any heat source. Only eggs are obtainable today; the rest need Part B.
- **Training time:** at five seconds per attempt, Cooking trains slower than the Beta 1 gain-curve audit assumed for the menu (1.25 s).
- **Runs against ModernUO `eba68d2be`.** The unit and full-suite runs used current HEAD `9006a252c` (the unpushed upstream merge); the cooking file is identical on both.

## Deploy and activation
Nothing is deployed. To ship: commit the ModernUO change, bump `pinnedModernUoCommit` in the three places, snapshot `Distribution/Saves` (the rebuild also carries the upstream merge `9006a252c` and its `BaseCreature` v24 save bump), stop the server, rebuild `UOContent.csproj` into `Distribution`, run `Deploy-Alpha1Baseline.ps1`, add one line about cooking to the root `README.md` rules section, then start the server. No flag to acknowledge. No new player-facing strings (all stock messages).

## Next
Part B: the era preparation chain (flour and water make dough; dough and a filler make unbaked food; baking Dough and SweetDough), which also gives the starter flour sack and pitcher a use. Needs its own plan and sign-off.
