# Alpha 3 contract review (features F–K)

**Status:** awaiting owner rulings, prepared 2026-09-28.

**Why this exists.** Much of the design doc (`ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md`, "DD") and of the implemented behavior was written by an AI, and the owner does not want all of it. Phase E's four-hour starter timer was one such invention.

This page lists every **custom (non-stock)** rule the remaining letters depend on, so the owner can rule on each once instead of meeting them one feature at a time.

**How to use it:**
- Work each letter only against items ruled **keep**.
- **simplify** means replace the item with stock UOR/ModernUO behavior.
- An **open** item must be ruled on before its letter starts.
- Record each ruling in the *Ruling* column with a date.

**Already settled; don't list or reopen:**
- Starter items are newbied and permanently bound, loose in the backpack and kept on every death.
- The starter bag is a plain `Bag`.
- Newbied items in bags are kept.
- There is no starter timer.

**Tracked elsewhere:** skill ID 15, the 222,222 BOD cap, anti-macro (SK-004), and Young (plan L). Stock ModernUO defaults that may be post-UOR are in [Alpha-3-Stock-Default-Audit.md](Alpha-3-Stock-Default-Audit.md).

In the tables, *Rec.* is the reviewer's recommendation. Paths are relative to `ShardContent/src/BritanniaRenaissance.Content/` unless they start with `UOContent/`.

## Bugs found during the review (fix whatever the rulings)

| ID | Problem | Where |
| --- | --- | --- |
| G-5 | A character who picks Archery as a **secondary** skill loses the stock 25 arrows and gets no replacement. Arrows are only reissued for an archer primary. | `StarterCombatIssuance.cs:100-107` |
| H-2 | Stock craft materials are removed **before** the per-account claim. A second same-profession character on an account gets zero, which is less than stock. | `StarterCraftMaterialIssuance.cs:65-69` (same pattern for every package) |

## F. Welcome and Backpack Ward compatibility

| ID | Custom rule | Built? | Rec. | Ruling |
| --- | --- | --- | --- | --- |
| F-1 | One free starter Backpack Ward per new character, bound to that character and never replaced. | yes | keep, if Wards stay | |
| F-2 | Wards have no source except the starter grant (no vendor, recipe or loot). The contract's "purchased/crafted Wards" and all multi-Ward rules (choosing among spares, one primed Ward per character, reconciliation; DD 504-530) are dead weight. | partial | owner call: if Wards are never sold, collapse to one single-charge Ward and drop the multi-Ward rules and tests | |
| F-3 | An ordinary (unmarked) Ward silently binds to the first account seen during a theft, and does nothing for anyone else afterward. | yes | simplify: remove, or make moot via F-2 (only 2 unmarked Wards exist) | |
| F-4 | Ward mechanics: lazy priming, escalating 25/50/100% per-thief detection, consumed on detection, 120 s of victim theft immunity. | yes (Alpha 2) | owner call: a core pillar, never reviewed by the owner | |
| F-5 | Invisible Loot Protection: after one unlawful monster-corpse transfer, that offender's account is blocked for 10 minutes on the victim's corpses. Needs a world-load migration. | yes (Alpha 2) | owner call | |
| F-6 | `[Welcome` command and creation prompt. | yes | keep | |
| F-7 | Pre-ruling marked Wards become newbied on load. | yes | keep | |

## G. Starter combat gear and consumables

| ID | Custom rule | Built? | Rec. | Ruling |
| --- | --- | --- | --- | --- |
| G-1 | One combat package by the highest selected skill (melee weapon plus studded armor and shield; archer bow, leather, 100 arrows; mage spellbook and 50 of each reagent). It replaces stock profession gear. | yes | simplify toward stock: stock already gives newbied profession gear; only raise quantities | 2026-09-28: drop the custom selection/replacement entirely. Stock `CharacterCreation.cs` grants (profession block + per-skill `AddSkillItems`) run untouched; only raise two quantities (25→100 arrows, 30→50 per reagent). An Advanced pick with two weapon skills keeps both, matching ordinary stock behavior. Two stock gaps get narrow, targeted patches (not a package system): Standard leather chest+legs when Archery is the strongest selected combat skill (stock gives archers no armor), and a Standard wooden shield when Parry is selected with a melee package (stock never grants a shield to anyone). A third gap — stock only grants bandages via Healing/Veterinary/Anatomy — gets the same treatment: top up to 50 stock Bandages for a Melee/Archer package that doesn't already have them. |
| G-2 | Every character's stock dagger becomes a bound `StarterDagger`. | yes | simplify: a stock newbied dagger | 2026-09-28: drop `StarterDagger`. The stock `Dagger` from `CharacterCreation.AddBackpack` is already Newbied with zero shard code — `EquipItem`/`PackItem` auto-stamp `LootType.Newbied` whenever `!Core.AOS`, and this shard runs UOR. No shard code needed for the dagger at all. |
| G-3 | Bound subclasses for all gear and consumables: owner serial, no stacking with ordinary items, no commodity deeds. About 20 types, each with its own serializer and every conversion route needing a test. | yes | owner call: binding versus a few gold of resale value | 2026-09-28: newbied only, no `Nontransferable`, for all starter combat gear/consumables. Delete `StarterCombatGear.cs` and `StarterCombatConsumables.cs` (13 bound types). Plain stock item types are used directly; stock's UOR-era auto-newbie behavior (see G-2) already satisfies the newbied requirement. To close the resulting vendor-resale faucet without reintroducing binding, `LootType.Newbied` items are added to the existing shard-added vendor-sale guards (`GenericSell.cs`'s `NontransferableItemPolicy`, `PlayerVendor.cs:549`) alongside `Nontransferable` — blocks NPC/player-vendor sale only; trade, drop, and banking stay open. Salvage (`SalvageBag.CanResmelt`) and BOD (`SmallBOD.EndCombine`) guards are left keyed on `Nontransferable` only, unchanged. **Named exception:** the mage `Spellbook` grant is stock `LootType.Blessed` (owner ruling: spellbooks stay blessed, matching convention and giving stronger death protection than Newbied), which the vendor-sale guard doesn't cover — it remains vendor-sellable. Broadening the guard to include `Blessed` was considered and rejected: `LootType.Blessed` is set unconditionally by ~200 unrelated stock types (veteran rewards, quest items, holiday items), so blocking it shard-wide would be a large, unrelated economy change. |
| G-4 | The grant is per character, not per account. Mage reagents (400 per character) can be converted to sellable potions or scrolls; recreation repeats it. | yes | keep; document the residual route | 2026-09-28: kept, but the scope is now larger than originally documented — see Readiness Limits in the G readiness record. Newbied-only (G-3) means a full starter kit (weapon, armor, bandages, reagents) has direct NPC resale value via vendor sale... except vendor sale is now blocked by the G-3 guard, so the residual faucet is limited to what the vendor-sale guard doesn't cover: player-to-player trade/drop/bank (no gold extracted directly) and reagent-to-potion/scroll conversion (unchanged from the original G-4 concern). |
| G-5 | *(bug; see above)* | | | 2026-09-28: fixed structurally by the G-1 redesign — arrows are topped up to 100 whenever Archery is selected in any position (no more primary-only gate), matching how stock's `AddSkillItems` already grants arrows per selected skill regardless of primary/secondary. |
| G-6 | `RemoveArmor` deletes stock creation armor before issuing the package. | yes | owner call | 2026-09-28: `RemoveArmor` is deleted along with the rest of the custom package-replacement logic (see G-1). Nothing removes stock-granted armor anymore; the two/three targeted patches (archer leather, Parry shield, bandage top-up) only add what stock is missing. |
| G-7 | Bound items can never be discarded (no ground, bag, bank or trash), and refusals are silent. Outgrown gear stays in the pack forever. | side effect of the E ruling | owner call: add drop-to-destroy or a discard option; refusal text is Beta 1 | 2026-09-28: closed for G — G no longer has any bound items (G-3). The general discard-path question is left open for whichever letters still have bound items (D's scissors, F's Ward). |
| G-8 | Shard guards in stock content refuse `Nontransferable` items at NPC sale, player vendors, trade, salvage and BOD combine. | yes | keep; the checks for items nested in containers are now redundant, so write no more tests for those | 2026-09-28: kept as-is for still-bound systems (D, F, H). No longer applies to G's own items, since none of them are `Nontransferable` anymore — they're blocked from vendor sale only, by the separate Newbied guard added under G-3. |
| G-9 | Fired starter arrows become ordinary arrows (stock ammo recovery). | stock | accept | 2026-09-28: accepted, verified. `BaseRanged.Ammo` always returns a fresh plain `Arrow()` regardless of the consumed stack's actual type (`Bow.cs:20`), so this holds for any starter arrow type, era-independent. Under this shard's UOR era (`!Core.SE`), a miss drops that ordinary arrow on the ground near the defender rather than SE's auto-bank-and-recover-to-shooter's-pack mechanic (`BaseRanged.OnMiss`) — worth noting in the evidence doc as a minor era-accurate difference from SE-era expectations, not a gap. |

## H. Starter craft materials and tools

| ID | Custom rule | Built? | Rec. | Ruling |
| --- | --- | --- | --- | --- |
| H-1 | Each craft package is claimable once per account, with large quantities (e.g. Blacksmith 250 ingots, Tailor 300 cloth and 50 leather). | yes | keep: this is the real anti-faucet control | |
| H-2 | *(bug; see above)* | | | |
| H-3 | 13 bound raw-material types (no stacking with ordinary materials, no commodity deeds). Under the E ruling they also can't be bagged or banked, so a new crafter carries 25–35 stones. Most of H's remaining work (conversion, failure and laundering routes) exists only because of them. | yes | simplify to stock materials; the per-account claim (H-1) is the doc's own "primary protection" (DD 2886) | |
| H-4 | Bound starter tools replace stock tools (8 types; Fletcher's Tools and Scribe's Pen added). | yes | simplify to stock tools; still add the two missing ones | |
| H-5 | Crafted output from starter materials is fully ordinary. | yes (stock-like) | keep; note it already undercuts H-3 | |
| H-6 | The validator hard-blocks both starter-material and combat-gear flags. | yes | keep until readiness | |

## I. Blacksmith Bulk Order Deeds

| ID | Custom rule | Built? | Rec. | Ruling |
| --- | --- | --- | --- | --- |
| I-1 | Smith BODs enabled under UOR (Publish 14, 2001); Tailor/Weaver stay AoS-gated. | yes | keep (already owner-approved) | |
| I-2 | Runic hammers excluded. Top reward tiers (500–1200 points) become gold and fame only. | yes | owner call: accept gold-only tiers or pick a non-power reward | |
| I-3 | Four Publish 16 rewards filtered out. | yes | keep | |
| I-4 | Remaining rewards (sturdy tools, mining gloves, colored anvils, Ancient Smithy Hammers) have no era classification. | open | owner call: simplest is to accept them as part of the BOD deviation | |

## J. UOR player skills and approved deviations

| ID | Custom rule | Built? | Rec. | Ruling |
| --- | --- | --- | --- | --- |
| J-1 | Combat hybrid: instant-hit and precasting on; weapon specials and Wrestling Stun/Disarm off (validator-enforced). | yes | owner call: reconfirm; it shapes PvP feel most | |
| J-2 | Mastery as built: at 95.0+ stock gain is suppressed. Each 4-hour UTC period adds +0.1 pending (only on login days, capped at 0.6), and each valid use spends 0.1. | yes (Alpha 1, live) | owner call: it directly sets time-to-GM | |
| J-3 | The design doc describes a *different* Mastery: an 18-hour cycle, difficulty allowances and a 3-cycle bank (DD 837-928). It contradicts J-2. | contract only | owner call: pick one, delete the other | |
| J-4 | Accelerated gain curve below 95 with per-skill difficulty classes (DD 770-835). Actual gain factors are stock (1.0). | contract only | owner call: stock is simplest | |
| J-5 | No combat pets in dungeons; pets can't attack blues, even in Hot Zones (DD 1209-1250). | partial | owner call: large impact on tamers | |
| J-6 | Poisoned-weapon corrosion: every `max(1, 6 − level)` hits, Poisoning thresholds at 50 and 99, a new saved weapon field (v12). The formula is invented; the Publish 5 source is only qualitative. | yes | owner call | |
| J-7 | Passive Detect Hidden on movement (ModernUO default, Felucca only). | yes (stock default) | owner call; see the stock-default audit | |
| J-8 | "Forged in Danger" Hot-Zone skill veteran title (DD 1003-1041). | contract only | cut or defer: heavy test matrix for a cosmetic title | |

## K. Permanent outdoor Hot Zones

| ID | Custom rule | Built? | Rec. | Ruling |
| --- | --- | --- | --- | --- |
| K-1 | Fire Island and Buccaneer's Den island polygons allow blue-on-blue initiation; dungeon interiors excluded. | yes | keep: the shard's identity | |
| K-2 | Attacker and target must be in the same named Hot region; the attacker must be a player, not a pet. | yes | keep | |
| K-3 | A 3-tile nearshore water margin is Hot, with no height, dock, boat or house modelling. | yes | keep; accept boats in the margin as Hot | |
| K-4 | Knocked Out replaces blue death in Hot Zones too. A criminal or red may loot without skill; anyone may Execute; executing a blue earns a murder count. Hot-Zone "full loot" only happens after a deliberate Execute. | yes (Alpha 2) | owner call: consider exempting Hot Zones | |
| K-5 | Every ordinary-blue kill is a murder count plus 24 real hours of red time, with no self-defense exception, even in Hot Zones. | yes (Alpha 2) | owner call: this shapes Hot-Zone behavior most | |
| K-6 | Wards and Loot Protection do nothing in Hot Zones. | yes | keep | |
| K-7 | A theft-protected bank square at Buccaneer's Den (stealing only). | yes | owner call | |
| K-8 | Entry and exit messages. | yes | keep | |
| K-9 | Fire Island reward premium (+25% gold, +20% resources; DD 4675-4680). The plan says "no new surface premium". | contract only | owner call: remove from the doc or schedule it | |
| K-10 | Warning before Recall/Gate into a Hot Zone, a login summary, a Britain board (DD 4824-4839). | contract only | simplify: entry messages are enough | |

## Uncertain, to confirm during the letter

- ~~Whether the stock UOR creation armor counts as "stock gear" for G-6.~~ Resolved 2026-09-28: moot — G-6's ruling keeps whatever stock grants rather than deleting/replacing it, so there's no longer a boundary to classify.
- Whether the `Nontransferable` branch in `PlayerMobile.CheckContentForTrade` and in `Scissors.cs:31` is upstream or a fork addition. Resolved 2026-09-28 for the trade branch: `PlayerMobile.CheckContentForTrade`'s `Nontransferable` check is a fork addition (commit `16f6189ae`, confirmed via `git log -S "item.Nontransferable" -- PlayerMobile.cs`). `Scissors.CanScissor`'s check is genuine stock (present since commit `8ec166bcd`, 2020, predates the fork) and exists to block scissoring `QuestItem`s, not shard "starter-bound" items.
- Whether Weaponsmith BOD issuance under UOR is stock.
- The era of the I-4 rewards.
- Knocked Out's 90-second duration exists only in code; the contract gives no number.

## Stale contract text to fix when touched

- DD test list around lines 5250-5255 still describes Ward death-deletion and the protection timer.
- Player-skill audit register row BR-SK-06 still mentions four-hour protection.
- Starter audit lines ~111-114 and ~150-153 describe the old four-hour rule (flagged by the superseded note at the top of that file).
