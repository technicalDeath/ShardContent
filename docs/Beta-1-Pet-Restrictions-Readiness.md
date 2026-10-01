# Beta 1: pet combat restrictions readiness

**Decision:** Ready and **activated** (owner sign-off 2026-09-30, "turn on when verified"): `featureFlags.petRestrictions` is true in source and deployed `shard-rules.json`. This closes Beta 1 scope item 2; the sub-95 gain curve and the two client-creation items remain.

## Reused accepted evidence
- Alpha 3 denied pets the Hot-only initiation permission (`PvpIntentService.IsOutdoorHotInitiationAllowed(from == attacker, ...)`). It is now superseded by the stricter rule below for tamed pets, and the pure-predicate tests remain valid.

## Current-source review
All hooks are described in [the audit](Beta-1-Pet-Restrictions-Audit.md). ModernUO gained two optional, null-by-default delegates on `BaseCreature` and tests; shard policy, the shrunken-pet item and the harm-gate check live in ShardContent. The owner's rule changes from the contract: **no tamed pet ever attacks a player** (the contract allowed criminals, murderers and the owner's aggressors), and the dungeon outcome is a shrunken pet in the pack instead of relocation.

## New verification
4 ModernUO hook tests, 12 ShardContent tests, full Shard suite 279/279, and live tamer runs on a disposable host with positive and flag-off controls (PvP victim table, real Deceit teleporter, tame, dismount, exemptions, unshrink rules, death, save/restart boot sweep). See the audit for the matrix and run IDs.

## Gate and validator
Source and deployed `shard-rules.json` match with `petRestrictions` true; the validator needs no rule for it. The dev host boots with it on.

## Update 2026-10-01 (later)
Unshrinking a mount inside a dungeon is allowed when none is standing and the owner is on foot. Taming inside a dungeon follows the same rule and is refused up front if the shrunken pet would not fit in the pack. Both verified live, the second with real Animal Taming.

## Update 2026-10-01
Owner mount exception added (one mount may be dismounted in a dungeon and fights monsters, never players; see the audit). A restart bug in shrunken pets (lost stabled flag, exposure to the 3-day delete timer) was found by the restart test and fixed before it could matter.

## Readiness limits
- **Summons, familiars and hirelings are exempt from both rules** by the owner's decision on the dungeon ban; the PvP rule was worded for "pets", so they remain ordinary owner-permission tools in PvP. Say so if you want them covered too.
- Feedback: an Attack or All Kill order against a player the owner may attack (criminal, red, `[Intent]`) makes each pet say "Your pet refuses to attack other players." and keeps its standing order. Verified live. Against an innocent the owner's own harm check stops the cursor first, so the pet is never asked. Guard-mode and auto-acquire refusals are silent: there is no command to answer.
- Gate Travel, public moongates, house teleporters and Recall use the same `TeleportPets` filter and are covered by the hook unit tests and the probe move, not walked live. Recall carries only bonded pets and bonding is disabled.
- Taming was exercised through `SetControlMaster` (the single point real taming calls), not with a full skill-based tame.
- The pack-room check happens when the taming target is chosen. The tame itself takes a few seconds, so if the pack fills or another mount appears in that window the shrunken pet is dropped at the owner's feet (never the bank) rather than the tame failing.
- Shrunken pets are only created as this safety outcome; there is no at-will shrinking. They are Blessed and Nontransferable, so they can't be traded; deleting the item deletes the pet.
- Staff-owned pets are exempt so staff can test.
- Two UOContent tests fail on ModernUO HEAD independent of this item (see the Elf audit).
