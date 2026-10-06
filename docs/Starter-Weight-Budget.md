# Starter weight budget: plan and evidence

Status: **plan written, implemented and verified live 2026-10-06 at the owner's direction ("write the plan and implement it, then commit and recap"); committed, not pushed, not deployed.** Origin: the owner asked how to resolve the Alchemy plus Cooking starter being overweight; the survey showed the problem is wider.

## Problem (measured 2026-10-06)

Server-side probe on a disposable copy of the deployed build. Client-reported weight is carried plus 11 stones of body weight; a character is overloaded above `MaxWeight + 4`, where `MaxWeight = 40 + 3.5 x STR` (187 at STR 42, 229 at STR 54).

| Starter | Weight vs limit | Heavy items |
| --- | --- | --- |
| Archer (era template) | 306 vs 229 | 200 Boards, 100 Feathers |
| Carpenter (era template) | 343 vs 229 | 264 Boards |
| Advanced Carpentry | 316 vs 187 | 250 Boards |
| Advanced Fletching | 275 vs 187 | 200 Boards, 100 Feathers |
| Advanced Alchemy + Cooking | 247 vs 187 | 75 Bottles, reagent bag 42, 20 lamb legs (2 stones each), 20 chicken legs |

Under the limit and unaffected: Alchemy alone, Cooking alone, Scribe, Blacksmith, Tailor, Tinker, Fisherman, Ranger, Prospector, Mage, and the Warrior-folder templates (Mace Fighter, Fencer, Swordsman: about 95 stones carried of 229).

Consequence in this build (`StaminaSystem`): every step costs 5 + (stones over) / 25 stamina, doubled when running, and at zero stamina the character cannot move; Recall is refused while overloaded. These characters start close to immobile.

Cause: the Alpha 3 Phase H quantities (owner rulings H-1 to H-6, 2026-09-28) were chosen as practice supplies with no weight check. A Board and a Bottle weigh 1 stone each, a raw lamb leg 2. The camping kit (Bedroll and 5 Kindling) adds 30 stones but is not the cause.

## Owner decision

Of three options (a weight budget, lower fixed quantities, bulk to the bank) the owner took the recommendation: **a weight budget.** The quantities in the Phase H rulings become ceilings, not promises.

## Design

After every starter issuer has run, a new character whose load (body weight plus carried) is above **85% of its carry limit** has its *bulk supply stacks* scaled down together until it fits.

- **Bulk supply stacks** (anywhere in the pack tree, including inside the reagent bag): Boards, Bottles, Blank Scrolls, raw lamb and chicken legs and fish steaks, Cloth, Leather, Feathers, Iron Ingots and every reagent. Tools, the Ward, scissors, gold, the camping kit, armor and weapons are never touched.
- **Rule:** let `over` = load - 85% of the limit. Each stack becomes `max(min(amount, minimumUnits), floor(amount x f))` for one factor `f`, chosen as the largest that brings the bulk stacks' weight down by `over`. The engine rounds each stack's weight up (`Item.PileWeight`), so the planner weighs stacks the same way: 21 reagents at 0.1 stones count as 3, not 2.1. (A first version used a plain proportional cut and left Alchemy plus Cooking 10 stones over budget in the live run; weighing stacks as the engine does fixed it.) No stack grows, none is removed, and every stack keeps at least `minimumUnits` (10) so a crafter always has something to start with. If every stack at its floor is still over the budget, it stays over; nothing else is trimmed.
- **Untouched cases:** characters already within the budget (Blacksmith, Tailor, Tinker, Scribe, Fisherman, the Mace Fighter, Fencer and Swordsman, Mage and so on) get exactly what they got before. Only new characters are affected, at creation.
- **Order:** registered last among the creation observers (before `CosmeticElfCreationService`, which stays last) through a `Register()` method that ModernUO's `Configure` discovery cannot run early, so it sees every issuer's grants.
- **Expected effect:** an Archer starts with about 83 Boards and 41 Feathers (not 200 and 100), a Carpenter about 110 Boards, Alchemy plus Cooking about 30 Bottles and 10 each of lamb and chicken, all under the limit with room for the first haul.

## Changes

- `StarterWeightBudget.cs`: the pure planner (`Plan`), the in-game pass, validation, `Register()`.
- `ShardRulesConfiguration.cs` and `shard-rules.json`: a `starterWeight` section: `enabled` (true), `maxLoadPercent` (85), `minimumUnits` (10).
- `ShardBootstrap.cs`: `StarterWeightBudget.Register()` before the Elf observer.
- Tests: `StarterWeightBudgetTests` (planner cases, validation, shipped file). Live driver `tests/scenarios/starter-weight/weight_live.py`.
- No ModernUO change.

## Activation

No feature flag: this repairs the already-enabled `alpha3StarterCraftMaterials` grants. `starterWeight.enabled` is a kill switch (false restores the old quantities). No flag changes.

## Verification

| ID | Case | How |
| --- | --- | --- |
| U1 | Within budget: nothing changes | unit |
| U2 | Over budget: stacks scale together, floors hold, nothing grows, matches the expected Archer, Carpenter and Alchemy plus Cooking figures | unit |
| U3 | Disabled, zero bulk, or the floors alone keep it over: no crash, sensible result | unit |
| U4 | Config defaults, ranges and the shipped file | unit |
| L1 | Archer, Carpenter, Advanced Carpentry+Fletching and Alchemy+Cooking now start at or under 85% of the limit (and so not overloaded) | live, disposable host |
| L2 | Blacksmith, Tailor and Tinker are byte-for-byte as before (same stack amounts) | live |
| L3 | The Archer can walk a long way without stamina trouble | live |
| L4 | The camping kit and Bedroll are intact on every one | live |

## Results (2026-10-06)

Unit: `StarterWeightBudgetTests` 20 pass; full Shard suite 561 pass. Live on a disposable host (copy of the deployed build with the new shard DLL and the source config; fresh characters; drivers `tests/scenarios/starter-weight/weight_live.py` and the kit stage of `tests/scenarios/camping/camping_live.py`; host and accounts removed, dev saves untouched). Run with the camping kit at its approved 5 Kindling and the rounding-aware planner:

| ID | Result |
| --- | --- |
| L1 | **Pass.** Archer 194 of 229 (83 Boards, 41 Feathers; was 306), Carpenter 194 of 229 (110 Boards, 42 Feathers; was 343), Advanced Carpentry + Fletching 158 of 187 (80 Boards, 30 Feathers; was about 316), Advanced Alchemy + Cooking 158 of 187 (30 Bottles, 10 lamb and 10 chicken; was 247). Every one sits exactly on its 85% budget. |
| L2 | **Pass.** Blacksmith (450 ingots), Tailor (300 Cloth, 50 Leather) and Tinker (200 ingots) are untouched. The kit stage also shows the Mace Fighter at 118 of 229, Pure Mage 120 of 208, Blacksmith 132 of 229 and a camper 77 of 187, all unchanged in what they hold. |
| L3 | **Pass.** The Archer walked 13 tiles with stamina unchanged (33 before and after). Before the fix, 73 stones over meant 5 + 2 = 7 stamina a step and about five steps before being stuck. |
| L4 | **Pass.** Bedroll and 5 Kindling intact on every start (seven kit characters and the four budgeted ones). |

An earlier live run found a flaw the unit tests had not: with the kit's extra weight, Alchemy plus Cooking ended at 168 of 187, 10 stones over budget, because the planner used continuous weights while the engine rounds each stack up. The planner now weighs stacks as the engine does, and a unit test pins that case.

The audit log records each trim (`starter weight-budget`: stacks trimmed, load before and after).

## Deferrals and risks

- **Crafters start with fewer materials** than the Phase H rulings listed; they buy more from NPCs. This is the intended trade for being able to move.
- **Warriors need nothing.** The Warrior-folder templates carry about 95 stones of 229 (studded leather set 19, Bascinet 5, shield 5, a weapon 2 to 9, bandages 5, plus the usual kit). An earlier version of this plan called Warriors heavy at 183 of 187; that came from stock profession 1, a forged-packet test start (Alchemy and Anatomy at 50, 75 Bottles and a reagent bag) that the creation screen never offers.
- **Bank delivery** (the third option) is not built and stays available if the owner wants the full quantities back.
- Not pushed and not deployed; the owner decides when.
