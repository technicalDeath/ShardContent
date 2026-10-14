# Auto-pickup of ammunition and reagents: evidence (2026-10-14)

Plan `Ammo-Reagent-Auto-Pickup-Plan.md`, signed off by the owner 2026-10-14 ("sign off as written"). Flag `autoPickup` OFF in the shipped config; nothing deployed or committed.

**Built:** `AutoPickupService.cs`. Once a second, an ordinary living player's tile and the 8 around it are searched for one loose pile (not in a pack, movable, visible, not locked down or secured, not inside a house the player is not a friend or co-owner of) of arrows or bolts (Archery 30+) or any reagent (Magery, Alchemy or Inscription 30+); it goes into the pack if the pack stays under 85% of the carrying limit. First pickup per character says "You pick up N <thing>. Auto-pickup is on; type [Pickup off to stop it." `[Pickup on|off` per character (account tag); staff `[AutoPickupStatus`.

**Deviation from the plan:** the "an item another player dropped within 30 s is left alone" rule was dropped: the engine gives no owner or dropper for a ground item, and a character's own missed arrow is also freshly created, so the age cannot tell them apart. The house rule (foreign house piles are left alone) stays. Locked-down and secured items are never taken.

**Verification:** 17 unit tests (kinds by skill, weight share, pile wording, flag). Live on a disposable host with the flag on (Navrey, no real-client picture because the only player-visible text is one ordinary system line): arrows picked up with Archery 50 and the line shown once; BlackPearl left alone with Magery 0; nothing picked up after `[Pickup off`; after `[Pickup on` and Magery 40 the waiting arrows, black pearl and garlic were all taken silently; a Blood Moss six tiles away was left. Not exercised live: the weight limit, a foreign house, a locked-down pile (decision code is straightforward, the weight share is unit-tested).

**Activation:** owner's explicit "activate" for `autoPickup`; at activation add a line to the root README rules and a gated Welcome Commands line for `[Pickup`.

## Revised 2026-10-14 (owner: "make auto-pickup its own category in options, add toggles to the combat hotbar for arrows, bolts, reagents, so we don't need the separate command")
- The `[Pickup` command and its off tag are **gone**. The player's choice now lives in the client profile (`auto_pickup_arrows`, `auto_pickup_bolts`, `auto_pickup_reagents`, all true for a new profile) and is sent to the shard as extended command 0xAC (one byte: bit 0 arrows, bit 1 bolts, bit 2 reagents) at login and on every change. The shard keeps it in memory per online player; a client that never sends one (an unmodified client, Navrey) gets all three kinds.
- Client: the combat bar's gear button now also opens for a player without auto-use, and its panel lists the three switches; Options has a new **Auto pickup** category with the same three, kept in step with the panel. Both show only while the shard's menu mask carries bit 1 << 6 (the flag is on).
- The server splits arrows and bolts (each needs Archery 30); reagents still need Magery, Alchemy or Inscription 30.
- Real client (disposable host, Archery 50, Magery 40): the panel showed the three switches; with arrows unticked a pile of nine arrows stayed on the ground while a pile of garlic was picked up (combat bar reagent count 6); the Auto pickup page showed arrows unticked; ticking arrows there and pressing Okay collected the nine arrows (count 9). Pictures were sent to the owner.
- **Activated** with the 2026-10-14 deploy on the owner's "commit deploy and activate all work".
