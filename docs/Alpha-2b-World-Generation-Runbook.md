# Alpha 2b world-generation runbook

This is the authoritative operational procedure for rebuilding the Britannia Renaissance UOR
world. It replaces stock ModernUO **Do everything** and the unrestricted `Decorate`, `DoorGen`,
`TelGen`, `SignGen`, and folder-wide spawner actions.

The source contract is `data/world-generation/alpha2b/world-generation.json`. Stock inputs are
read from the pinned ModernUO commit, transformed only in the disposable shard namespace, and
hashed in `Distribution/Data/BritanniaRenaissance/Alpha2b/generation-report.json`.

## Safety and rollback

1. Stop every client that can mutate the selected world.
2. Prove `127.0.0.1:2593` is free **and** no process has the target distribution's
   `ModernUO.dll`, `Server.dll`, or `Assemblies/UOContent.dll` loaded. A listener check alone is
   insufficient because a listenerless server can continue autosaving.
3. Resolve the absolute `Distribution/Saves` and `Distribution/WorldStateArchive` paths and verify
   both remain under the intended distribution before moving anything.
4. Move the complete old `Saves` directory into a uniquely named archive. Do not merge old world
   files into the new save. Create a new `Saves` directory and copy only the existing `Accounts`
   index when owner authentication must be retained.
5. Record the archive path. Restoring means stopping the sole writer, moving the failed/new save
   aside, and restoring the archived `Saves` directory as one unit.

Runtime saves, accounts, generated deployment copies, reports, and credentials are local state and
must not be committed.

## Prepare and deploy reviewed inputs

From `ShardContent` with the server stopped:

```powershell
& .\tools\Deploy-Alpha1Baseline.ps1
& ..\dotnet\dotnet.exe test .\tests\BritanniaRenaissance.Content.Tests.csproj `
  -c Release --maxcpucount:1 '-p:SkipShardContentDeploy=true' --no-restore
```

Deployment must verify the ModernUO pin and prepare:

- 28 allowlisted decoration files;
- 410 Felucca signs;
- 353 teleporter definitions / 385 canonical placements;
- 1,546 canonical spawners;
- the pinned `DoorGenerator.cs` source hash, 16 Felucca scan rectangles, four stock Britannia
  exclusions, and 1,345 exact door-frame placements.

The preparation report currently contains 57 hashed inputs and 55 generated outputs. Treat any
count or hash change as a review event; do not update expectations merely to make a check pass.

## Clean generation

1. Start ModernUO from `ModernUO/Distribution` through the workspace .NET runtime. Confirm UOR
   gates, map/region/world load, and both listeners. A fresh world must load with zero items and
   zero mobiles before the owner character logs in.
2. Log in with the preserved owner account. If its previous character belonged to the archived
   world, create one temporary operator character through the normal client flow. Player mobiles
   and their parented starter inventory are excluded from the fresh-world root-object guard.
3. Run `[Alpha2bWorldGen preview`. It must report UOR/Felucca, the exact input counts above,
   1,345/1,345 expected door placements, and zero Felucca root items/non-player mobiles.
4. Run `[Alpha2bWorldGen apply CONFIRM-UOR-FELUCCA` exactly once.

The runner performs these stages in order:

1. allowlisted Felucca decorations and manifest-scoped duplicate cleanup;
2. Felucca-only town/shop door-frame scan;
3. canonical Felucca teleporters;
4. nine Felucca public moongates;
5. era-reviewed Felucca spawners;
6. 410 Felucca signs, including localized labels;
7. 63 UOR Khaldun dynamic puzzle objects.

The door stage uses the pinned ModernUO frame classifier but only the committed Felucca rectangles
and exclusions. It preserves an existing `BaseDoor` at the frame, including the stock decoration
doors whose Z differs by up to two units; creates a `DarkWoodDoor` only for a genuine empty frame;
links double doors; and fails on blocked, duplicate, or conflicting placements. It never scans an
inactive facet. The accepted clean run creates 1,215 doors and preserves 130 decoration doors,
for 1,345 audited placements and 327 linked pairs.

The command writes an execution report and saves only after the complete audit passes. On any
failure, do not save: stop the server, correct the reviewed source/configuration, and repeat from
the clean save.

## Convergence and restart acceptance

1. Without restarting, run
   `[Alpha2bWorldGen apply CONFIRM-UOR-FELUCCA rerun`.
2. Require zero new decorations, zero duplicate-cleanup removals, zero new doors, 1,345 existing
   doors, and zero operation failures. Teleporters, moongates, spawners, and signs are intentionally
   replaced by their canonical passes; Khaldun must create zero additional objects.
3. Stop the client, shut down the server cleanly, restart from the published save, and reconnect.
4. Run `[Alpha2bWorldGen audit`. Require exact counts for all layers, 1,345 doors and 327 linked
   pairs, no inactive-facet roots, no champions, and disabled/empty Faction state.
5. Run the explicit `rerun` command once more. Require the same zero-growth result and successful
   save. This first rerun after serialization is mandatory because it catches non-persistent or
   graphic-normalizing objects.

## Client checks

Use a real Navrey/ClassicUO client, not server startup alone. At minimum verify:

- a Greater Britain shop route opens its generated door and enters the shop;
- a representative secondary-town building opens its generated door, without treating that town
  as a peer service center;
- Britain services, localized signs, and its public moongate;
- peer-city service absence outside Greater Britain;
- an approved wilderness spawn and dungeon spawn/door;
- a generic teleporter pair and reciprocal boat/serpent-pillar Lost Lands travel;
- healer death and explicit resurrection acceptance on disposable staging.

The 2026-09-26 door repair rehearsal crossed the generated entrance to Britain's Lord's
Clothiers and a generated Minoc bank entrance; both routes emitted `Opening door...` and arrived
inside. The exact audit covers every other frame placement.

## Finalize

Stop the test client, issue `save`, wait for both save and snapshot completion, then issue
`shutdown`. Re-run the listener and loaded-module checks. Record the save file count, byte count,
latest write time, and SHA-256 over sorted UTF-8 lines of
`<relative-path> <per-file-sha256>` in `Alpha-2b-Release-Evidence.md`.

The authoritative accepted server is left stopped. Starting it for play is a separate deliberate
operation.
