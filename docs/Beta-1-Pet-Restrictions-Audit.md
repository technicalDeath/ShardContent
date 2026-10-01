# Beta 1 item 2: pet combat restrictions, plan and evidence

Roadmap: [Beta 1](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 2 (deferred from Alpha 3 J-5). Design contract: Hot Zones plan §8 "Pets and Taming". Readiness record: [Beta-1-Pet-Restrictions-Readiness.md](Beta-1-Pet-Restrictions-Readiness.md) (written at close).

## Owner sign-off (2026-09-30)

Plan presented and approved. Decisions:
- **Which pets:** tamed pets only. Spell summons, familiars, hirelings and pack animals (pack llama, pack horse) are exempt from the dungeon ban. Ridden mounts are always fine.
- **Pet PvP:** **no tamed pet ever attacks a player**, for any reason. This replaces the contract's lawful-target rule. Pets still fight monsters. Summons, familiars and hirelings are not covered (they remain ordinary owner-permission tools); flagged to the owner in the readiness record.
- **When a tame or dismount puts a pet in a dungeon:** the pet is put in the owner's pack as a **shrunken pet** item. The owner said they had played shards with shrunken pets and asked if it would be hard; it is not, in its forced-only form. Scope kept narrow: shrinking happens only as this safety outcome, never at will. Item rules (mine, flagged for review): Blessed and Nontransferable (survives death, can't be looted, stolen, traded or sold), unshrunk by double-click from the owner's backpack only, refused in dungeons, refused if the owner has no free follower slots, deleting the item deletes the pet.
- **Mount exception (2026-10-01, owner):** an owner may ride **one** mount into a dungeon, dismount, and keep it there. It fights monsters but never players. It stays only if the owner is not riding another mount and no other mount of theirs is already standing in a dungeon; any other pet, a second mount, or a mount tamed while the owner rides one is shrunk as above. Taming a lone mount inside is allowed. A standing mount is left alone by the boot sweep. Unshrinking inside a dungeon stays refused.
- **Activation:** turn `featureFlags.petRestrictions` on when verified (source and deployed config), as with Elf.
- **Commits:** local only, no push (standing instruction from the Elf item).

## Audit findings (before this pass)

- No dungeon pet rule existed. `BaseCreature.TeleportPets` (ModernUO, `Mobiles/BaseCreature.cs`) is the single routine that carries followers through teleporters, moongates, Gate Travel, public moongates and house teleporters, with no region check. Recall carries only *bonded* pets, and bonding is era-gated off, so Recall carries none.
- Pets cannot walk through teleporters (the Creatures flag is off). Other entries: summons, taming, dismounting (a ridden mount is on the Internal map; dismount re-enters the world through a region change), and a pet already in a dungeon when the server loads. Stock auto-stable on logout is Core.SE-gated, so inactive.
- 18 `DungeonRegion` records on Felucca (`Distribution/Data/regions.json`).
- Alpha 3 only denied pets the Hot-only initiation permission (`PvpIntentService.IsOutdoorHotInitiationAllowed(from == attacker, ...)`). Through their owner, pets could still attack `[Intent]`-greys, guild-war enemies, criminals, reds and the owner's aggressors, and with SafeWorld off stock lets a pet attack anyone on Felucca (the owner turns criminal).
- Every pet attack route (Attack, All Kill, Guard, auto-acquire, retaliation, area attacks) funnels through `Mobile.CanBeHarmful`, which calls `Mobile.AllowHarmfulHandler`, the ShardContent `PvpIntentService.AllowHarmful`. One gate covers all.
- No pet tests existed in ShardContent.

## Design

| Piece | Where | Rule |
| --- | --- | --- |
| Flag | `featureFlags.petRestrictions` | Both rules below run only when on. |
| Restricted pet | ShardContent `PetRestrictionService.IsRestrictedPet` | `Controlled`, not `Summoned`, owner is a player, and not a `BaseHire`, `BaseFamiliar`, `BaseEscortable`, `PackLlama` or `PackHorse`. |
| Pet PvP | `PvpIntentService.AllowHarmful`, first branch | Restricted pet and target is a `PlayerMobile`: harmful action refused. Independent of SafeWorld. |
| Follow filter | New ModernUO delegate `BaseCreature.CanFollowOwnerHandler`, called in `TeleportPets` | A restricted pet is not carried to a destination inside a `DungeonRegion`; the owner is told. |
| Mount exception | `PetRestrictionService.MountMayStay`, checked on the next tick | See sign-off. |
| Placement | New ModernUO delegate `BaseCreature.PetPlacementChangedHandler`, raised from `OnRegionChange` (controlled only) and `SetControlMaster` | A restricted pet found in a dungeon region is shrunk into the owner's pack on the next tick. Covers walking in, dismounting, taming and any other placement. |
| Boot sweep | Server start | Every restricted pet already inside a dungeon region is shrunk. |
| Shrunken pet | ShardContent `ShrunkenPet` item | See sign-off item rules. |

## Changes in this pass

| Repo | Change |
| --- | --- |
| ModernUO | `BaseCreature`: two optional delegates, `CanFollowMasterHandler` (called in `TeleportPets`) and `ControlledPlacementChangedHandler` (raised from `OnRegionChange` for controlled creatures and from `SetControlMaster` when a master is set). Both are null by default, so stock behavior is unchanged. Tests: `PetPlacementHookTests`. |
| ModernUO (follow-up) | `BaseCreature.AttackCommandRefusalHandler`, called first in `BaseAI.CanAttackTarget`: non-null text is said to the commanding player and the order is dropped. Tests in `PetPlacementHookTests`. |
| ShardContent | `PetRestrictionService`, `ShrunkenPet`, the pet branch in `PvpIntentService.AllowHarmful`, `featureFlags.petRestrictions` (validator-free; on at activation), `ShardBootstrap` registration. Tests: `PetRestrictionTests`. Live probe and driver in `tests/scenarios/pet-restrictions/`. |

## Acceptance matrix and results

| Case | Verified by | Result |
| --- | --- | --- |
| `TeleportPets` moves a follower by default; skips a pet the handler refuses and passes it the destination | ModernUO unit | pass |
| Placement notification fires on a new master and on a controlled creature's region change, not on release or for a wild creature | ModernUO unit | pass |
| Creature test: tamed mounts and combat pets restricted; wild, summoned, pack llama/horse, hirelings, familiars, escortees exempt (every `BaseHire`/`BaseFamiliar` subclass checked by reflection) | unit | pass |
| Flag defaults off and is listed when on | unit | pass |
| **Control:** with the flag off, the same setup attacks Intent, criminal and red players (pets via `all kill`) | live | pass (3/3) |
| Flag on: a fresh pet ordered `all kill` against a blue, an `[Intent]`-grey, a criminal grey and a red never targets them and the victims lose no hits; the same order on a monster works | live | pass (10/10 incl. control) |
| A player who strikes a pet is not fought back | live | pass |
| Real Deceit teleporter (4110,430): owner goes in, a pet standing beside the owner on Follow stays outside and under control | live | pass |
| **Control:** same walk with the flag off: the pet follows into Deceit | live | pass |
| Teleporter-style move (`TeleportPets`) into Deceit with a pet beside the owner: pet filtered | live probe | pass |
| Tame inside a dungeon: pet shrunk into the pack next tick; pet on Internal map, uncontrolled, stabled; follower slots freed; item Blessed and Nontransferable | live | pass |
| Unshrink refused inside a dungeon; owner killed and resurrected: item stays in the pack | live | pass |
| Pack llama tamed inside a dungeon stays | live | pass |
| Unshrink outside: pet back under control of the owner on Felucca, item consumed | live | pass |
| Ridden horse is not in the dungeon world | live | pass |
| Ride one mount in, dismount inside: it stays, nothing is shrunk; it attacks a monster; another pet and a second mount are shrunk while it stands; a mount tamed while the owner rides is shrunk; re-dismounting stays | live (`pet_live.py mount`) | pass (8/8) |
| A standing mount told to attack a player refuses and says so (one mount stands, the second is shrunk, so one message) | live | pass |
| Save and restart: the standing mount is untouched and the shrunken extras are still shrunk (their stabled flag is restored at boot) | live (`mountsweep`) | pass |
| A shrunken pet can be released after a restart | live | pass |
| Pet seeded inside a dungeon with the flag off, save, full restart with the flag on: shrunk by the boot sweep, item in the owner's pack, survived the save | live | pass |
| Dev host boots with the flag on | live | pass |
| Attack order on a criminal player: each pet tells the owner it refuses and keeps its order; the same order on a monster produces no refusal and the pet attacks | live (`pet_live.py refusal`) | pass (5/5) |

Runs: ModernUO hook tests `20261001T014340883Z-5f139d` (4/4); full Shard `20261001T021353003Z-3de324` (279/279); full UOContent `20261001T021417723Z-55475e` (1246 pass; the same two unrelated failures as in the Elf audit, `AdvancedSearchTypesTests.Poison_ReferenceTypeParsedViaTypes` and `FamiliarAITests.HiddenCaster_FamiliarRefusesRetaliation`). Live outputs under `work/pet-live/`; drivers `tests/scenarios/pet-restrictions/pet_live.py` (`pvp`, `pvpoff`, `dungeon`, `seed`, `sweep`).

## Bug found and fixed during the mount work

Stock does not save `IsStabled` on a creature; it rebuilds it at load from the owner's stable list. Shrunken pets are not in that list, so after a restart they lost the flag, and stock would have started its 3-day abandoned-pet delete timer on them. The restart check caught it. `ShrunkenPet` now keeps a registry of bound items and re-flags their pets at server start (`RestoreStabledFlags`), independent of the feature flag. Verified across a restart.

## Observations and test-tooling notes

- Pet area damage and auras reach players only through `CanBeHarmful`, so the one gate covers them (source inspection: `BaseCreature.AuraDamage` and the spell paths).
- `[remove` and `[delete` did not remove tamed pets in the live runs; the probe's `TestOnlyPetClear` is the reliable way to reset followers.
- A rejected `all kill` target can leave the AI-control cursor open on the server, so the next `all kill` raises no new cursor; the driver cancels the cursor first.
- Staff `[res` did not resurrect a dead player near Deceit but worked in town. Not investigated; unrelated to pets.
- Navrey's `walk` is refused after a server-side teleport and the pathfinder cannot reach every teleporter tile (Covetous); Deceit's entrance works with `gotoexact`.

## Player-facing text (for review with the Beta 1 release)

- "{pet} cannot follow you into a dungeon."
- "{pet} cannot stay in a dungeon, so it has been shrunk into your pack."
- "Your pet cannot be released inside a dungeon."
- "Your pet refuses to attack other players."
- Item name "a shrunken {pet}". README rules section gained a "Pets" line.
