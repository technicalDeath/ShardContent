# Alpha 3 Phase E: Starter Bag readiness

**Decision:** Ready for Alpha 3 enablement, with `alpha3StarterBag` still disabled. This closes feature readiness only; the combined Phase L activation decision remains outstanding.

## Owner rulings that redefined this feature (2026-09-28)

- **The bag:** the starter organization bag is an ordinary stock `Bag`, with no starter binding and no special death routing. The bound `StarterBag` class is gone, which removes every trade, vendor, sale and corpse case the plan listed for it.
- **Starter-issued items:** all 40 types, including the free starter Backpack Ward, are newbied and permanently nontransferable. Stock ModernUO keeps them:
  - loose in the owner's backpack only (no bags);
  - through every death, murderer or not.
  - The four-logged-in-hour Starter Protection timer is gone.
- **Ordinary newbied items** stay protected inside bags (`KeptItemDeathRouting`), except for murderers.

## Reused accepted evidence

- Per-character issuance with an account tag and no duplicate grant, the owner marker, save/restart and ordinary client creation (see [starter audit](Alpha-3-Starter-Package-Audit.md)). Issuance code is unchanged apart from the item it creates.

## Current-source review

**Issuance:**
- `StarterBagIssuance.Issue` drops one `new Bag()` into the backpack of an ordinary new player, once per character.
- It runs only when `featureFlags.alpha3StarterBag` is on, and it is guarded by the `BritanniaRenaissance.StarterBag.v1.<serial>` account tag.

**Death and movement:**
- Nothing in the shard overrides death routing for starter items; `StarterDeathRuleTests` enforces this for all 40 types.
- `KeptItemDeathRouting` (registered in `ShardBootstrap`) returns kept items from bags on the corpse using the player's own `GetInventoryMoveResultFor`.

**The dev world:**
- It holds no `StarterBag` instances, because the flag was never on.
- Marked starter Wards become newbied when loaded.
- The older disposable hosts under `work/`, such as `alpha3-starter-economy-host`, may contain `StarterBag` items from earlier probes. Rebuild them from a fresh copy rather than loading them with this build.

## New verification

- `Invoke-AgentVerification.ps1 -Suite Shard`: 263/263, run `20260928T170808008Z-8da2fd`.
- The live disposable-host cases E-ISSUE, E-NOBAG, E-DEATH and E-MURDERER all passed. Setup, driver (`tests/scenarios/starter-death/starter_death_live.py`) and cleanup are recorded in the [starter audit](Alpha-3-Starter-Package-Audit.md#owner-rulings-and-phase-e-closure--september-28-2026).

## Gate and validator

- Source and deployed `alpha3StarterBag` and `alpha3EnablementAcknowledged` are false. The validator requires the acknowledgment before the bag flag can be enabled.
- `KeptItemDeathRouting` and the Ward change are not flag-gated, so they are live on the dev host since this deploy.

## Readiness limits

- **Young status:** ModernUO's Young player system is on by default and keeps *every* item for new accounts through death for 40 hours. The live test cleared it on the test character. Whether Young should be on for this shard is an open owner question: the design doc §16 rejects account-age immunity.
- **Not run live:**
  - Save/restart; loot type is stock-serialized.
  - Blessed items inside bags; same code path as newbied.
- **Other features that re-verify under the new rule:** scissors (D), combat gear (G) and craft materials and tools (H) inherit the rules; their death cases re-verify when those letters are worked. Scissors was covered by E-NOBAG and E-MURDERER here.

**Phase L review (2026-09-30):** re-checked against the intervening Knocked Out corpse-style looting change (K4, `KnockedOutService.cs`/`Snooping.cs`/`Stealing.cs`/`PlayerMobile.cs`) and the post-UOR system gates (virtues/poison corrosion/duel gump). K4's new loot check is a separate, read-only mechanism gating loot from a still-alive Knocked Out victim's pack; it does not call or modify `KeptItemDeathRouting`, `Item.OnInventoryDeath` or `GetInventoryMoveResultFor`, which this evidence's E-ISSUE/E-NOBAG/E-DEATH/E-MURDERER cases depend on. CLEAN, no reopening.
