# Town guards kill monsters

**Flag:** `featureFlags.townGuardsKillMonsters`, built 2026-10-16. **Off**: not activated, not deployed, not committed. Live and real-client testing is held for the owner's batch test.

## The owner's rulings (2026-10-16)

- "Monsters in town should be killed by guards regardless of who attacks first."
- **Guards come only when a player calls them**, but they come whoever attacked first ("Change the logic so that guards only come if a player calls them, but they come regardless of who attacked first"). This replaced the first ruling of the same day, that guards act automatically with no call.
- **Only creatures that attack on sight** count. Town animals that only fight back, and pets and summons, are left alone.
- "Shrink the guard zone. Monsters should not spawn inside one."
- "Shrink the guard zone only where there are no vendors."
- Build it behind a flag, and hold the testing so many changes can be tested together.

## Why (stock behaviour, checked in code)

A stock guard acts only on a criminal or a murderer (`GuardedRegion.IsGuardCandidate`).

A monster turns criminal when it hurts a player who had not struck it (`Mobile.IsHarmfulCriminal`, then `CriminalAction`, then `GuardedRegion.OnAggressed`). Inside a town that makes it a guard target for 15 seconds, and "guards" kills it. The owner's own test and the bot farm's helper (about 8 s) both saw this.

A player who struck the monster first is its aggressor. Its hits are then self-defence, and the guards do nothing. The bot farm's town deaths came from this, because the bots always fought back. Its first report wrongly said guards ignore monsters altogether.

## What it does

- **Engine hook** (ModernUO `UOContent/Regions/GuardedRegion.cs`): `GuardedRegion.AlwaysGuardTarget`, a static `Func<Mobile, GuardedRegion, bool>`, null by default.
  - A mobile the hook returns true for counts as an always-candidate, as a murderer does before AOS, so a "guards" call (`CallGuards`, 14 tiles around the caller) kills it whoever struck first. It must stand inside the guarded region.
  - Nothing is sent without a call. Stock still has one case of its own: a monster that hurts a player unprovoked turns criminal, and a human townsperson within 8 tiles may call the guards on it (`CheckGuardCandidate`). That is unchanged.
  - With the hook null, stock behaviour is unchanged.
- **Shard rule** (`TownGuardsService`): a creature is a target when all of these hold:
  - it is alive;
  - it is not controlled, summoned or anyone's pet;
  - it is not invulnerable or blessed;
  - it is not a vendor or a blue-named NPC (`InitialInnocent`);
  - its `FightMode` is Closest, Strongest or Weakest, meaning it attacks unprovoked;
  - the innermost guarded region where it stands has guards working.

  Every town animal, vendor, hireling, escort and Order or Chaos guard is Aggressor or None, so none is a target (checked in each base class).
- **Smaller zones:** the `townGuards.unguardedAreas` are registered at server start, only while the flag is on. Each is a top-level `NoHousingRegion` at priority 51, above the towns' 50. A point in one belongs to no town region at all: no guards for anyone, and still no housing, as before.
  - **Britain Outskirts:** x 1093-1287 × y 1538-1906, the woods and farmland west of Castle British. Also x 1288-1415 × y 1841-1906, the fields south of the south-west houses.
  - **Moonglow Zoo:** x 4479-4540 × y 1352-1402. Its 11 caged-monster spawners sat inside Moonglow's zone, so the guards would have emptied the zoo. No vendors stand outside Britain on this shard.

  Neither area holds a vendor or townsperson spawner; the test `TheGuardZoneShrinksOnlyWhereNoVendorOrTownspersonStands` pins this. Castle British's west wall is at x 1295 and stays guarded.
- **Beginner hunting moved** (`data/world-generation/alpha2b/britain-beginner-hunting.json`). Each spawner's whole home square must now lie in Britain Outskirts; the test `EveryBeginnerSpawnerSpawnsOnlyOnUnguardedGround` pins this.
  - "North fields" (1519,1531) stood among the north stables; it is renamed "castle woods" and moved to 1240,1600.
  - "Farm vermin" (1301,1760) stood under a thatch roof beside the south-west animal trainer; it moved to 1265,1770.
  - "South-west forest" (1329,1849) reached into the south-west district; it moved to 1340,1868.
  - The other three already qualified.
  - The dev world has none of these spawners yet, so `[Alpha2bWorldGen addspawners` places them at the new spots. The farm host has them at the old spots.
- **Guide:** the first-hour page now says what the guards do.
  - With the flag off, it gives the stock behaviour: shout guards on a monster that attacks you in town; they won't help if you struck first. This corrects the 2026-10-15 line, which said guards never stop monsters.
  - With the flag on: shout guards and the guards kill a monster that follows you into a guarded town, even if you struck it first. Britain's woods and fields west of the castle, and south of the south-west houses, are not guarded.
- **Staff:** `[TownGuardStatus` shows the flag, the unguarded areas, and whether the spot you stand on is guarded.

## Checks so far

- Unit tests: `TownGuardsTests`, 16 cases.
  - The target rule's truth table, including every FightMode.
  - The flag defaults to off.
  - The config validates, and bad areas are refused.
  - The vendor-free shrink.
  - The beginner spawners are on unguarded ground.
  - The guide text, with the flag on and off.
- Full suites, after the change to call-only guards (run `20261016T192726305Z-6404d6`): shard 1,555 passed; UOContent 1,404 passed, 2 skipped.
- `tools/town-guards/audit_guard_zones.py`: with the shrink, **0** Felucca spawners of attack-on-sight creatures stand inside a guard zone.

## Edge spawns: no monster spawns inside a zone (2026-10-17)

The owner said yes to dealing with the 25 spawners that stand outside a zone but whose home range reaches into one (`audit_guard_zones.py --reach`). Of those:

- 11 are sea-serpent spawners along the coasts, with ranges of 100 to 175 tiles.
- The rest are stock spawns from the pinned ModernUO data: Yew, Trinsic and its moongate, Britain's north-east corner, the Lost Lands arena, and Wind.

Shrinking their ranges would empty whole coastlines. It would also need a pin bump and re-placed spawners in every world. So the rule acts at spawn time instead:

- **Engine hook:** `BaseSpawner.MobileSpawnPositionAllowed`.
  - A refused spot is drawn again up to 8 times.
  - If every redraw is refused, the spawner's own spot is used.
- **Shard rule:** `TownGuardsService.SpawnAllowed`, under the same flag.
  - It refuses a spot where guards work to any creature that would be a guard target there.
  - That covers every spawner, today's and future ones, and existing worlds as they are.

**Live check:** disposable host `batch`, flag on, 30 staff spawners at 1700,1494, with a 12-tile range crossing Britain's north edge at y 1498 (36% of the square is inside the zone).

| Creature | Spawned | Inside the zone |
| --- | --- | --- |
| Ettin (attacks on sight) | 29 | **0** |
| Horse (control, not hostile) | 20 | 6 |

- The staff character was hidden, and the walking range was raised, so the Ettins stayed where they spawned.
- Driver: `work/batch-test/s9*.py`.
- Full suites, run `20261017T194956303Z-58d5bf`: shard 1,643 passed.

## Not yet checked (held for the batch test)

- Live on a disposable host with the flag on:
  - a monster that walks into Britain is left alone until someone calls the guards;
  - a "guards" call kills a monster the player struck first;
  - the beginner spawns in the Outskirts are left alone;
  - the Moonglow Zoo keeps its animals;
  - town animals are not killed;
  - `[TownGuardStatus`.
- In the real client: the guard's lightning on a monster, and the guide's first-hour page.

## Open for the owner

- Staff-placed monsters in a town (events) are killed too when a player calls the guards, while the flag is on. Turn a town's guards off with `[SetGuarded false` for an event.
- **Deploy needs:**
  - `UOContent.csproj` rebuilt into Distribution, because of the engine hook;
  - a ModernUO commit and a pin bump;
  - the usual Deploy-Alpha1Baseline;
  - `[Alpha2bWorldGen addspawners` on the dev world, after a `Saves` snapshot, for the beginner spawners.
