---
name: shard-content-workflow
description: Build, test, deploy, and smoke-check Britannia Renaissance ShardContent with the adjacent ModernUO fork on Windows; use for shard C# or configuration changes and local server validation.
---

# ShardContent and ModernUO workflow

Run commands from `ShardContent/` unless noted. Read `../britannia-renaissance/SKILL.md` when repository boundaries or runtime ownership matter. `README.md`, `docs/alpha-1-engineering-baseline.md`, and `docs/ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md` give project context; distinguish active code and flags from proposed phases.

## Source of truth and edit locations

- Custom C# and tests: `src/BritanniaRenaissance.Content/` and `tests/`. The project references adjacent ModernUO distribution assemblies and copies its DLL to `../ModernUO/Distribution/Assemblies` after an ordinary build.
- Policy source: `data/configuration/shard-rules.json`, `expansion.json`, and `modernuo-era-gates.json`. The server consumes deployed copies in `../ModernUO/Distribution/Configuration`; changing source alone does not change a running or deployed server.
- The deployment tool is `tools/Deploy-Alpha1Baseline.ps1` (the historic name still handles current policy). It refuses to copy while a verified server has target assemblies loaded, prepares the pinned Alpha 2b UOR/Felucca inputs through `tools/Prepare-Alpha2bWorldData.ps1`, builds Release, copies policy, patches era gates, and registers the content assembly. Never work around its live-assembly check by copying over an active process.
- Compare the source `pinnedModernUoCommit` with the deployed `shard-rules.json` and current ModernUO HEAD before smoke testing. A server can start with an older deployed pin; startup alone does not prove that source and distribution match.
- ModernUO's `Projects/Server/` is the engine and `Projects/UOContent/` is stock content. Follow `../ModernUO/AGENTS.md` and its detailed `CLAUDE.md` before editing there. Prefer narrow extension hooks to duplicating stock systems in the shard assembly.

## Build and test

The workspace SDK is `../dotnet/dotnet.exe`; .NET 10 is required. While the server is running, avoid the build target's automatic DLL copy. A content test from this directory is:

```powershell
& ..\dotnet\dotnet.exe test .\tests\BritanniaRenaissance.Content.Tests.csproj -c Release --maxcpucount:1 '-p:SkipShardContentDeploy=true' --no-restore
```

Restore dependencies if a fresh checkout needs them. The suite proves policy and unit behavior; it does not replace live client matrices for PvP, theft, corpse rights, Knocked Out, or persistence. For release-oriented Alpha 2 preflight, inspect `tools/Verify-Alpha2Readiness.ps1` and pass explicit paths; it is read-only and may report pin or working-tree blockers after valid new work.

## Local smoke check

1. Ensure no other process owns `127.0.0.1:2593`, then use the loaded-module scan from `tools/Deploy-Alpha1Baseline.ps1` to confirm that no process has this distribution's `ModernUO.dll`, `Server.dll`, or `Assemblies/UOContent.dll` loaded. The port check alone is insufficient because a listener-less server can keep running and autosaving the same world. From `../ModernUO/Distribution`, set `DOTNET_ROOT` to the absolute workspace `dotnet` directory and run `& "$env:DOTNET_ROOT\dotnet.exe" .\ModernUO.dll` in an interactive session. The root `Start Server.cmd` does the same for a person.
2. Confirm logs show the shard rules loaded, UOR era gates validated, maps/regions/world loaded, and `Listening: 127.0.0.1:2593`. `Data/assemblies.json` must include both `UOContent.dll` and `BritanniaRenaissance.Content.dll`.
3. Use [navrey-shard-test](../../../../Navrey/.agents/skills/navrey-shard-test/SKILL.md) for actual login and read-only in-game checks. Do not infer gameplay correctness from the listener alone.
4. Stop the client, enter `save` in the server console, wait for the completed world-save message, then enter `shutdown`. Treat existing saves as user data.

For a deliberate fresh Alpha 2b world build, archive the entire prior save only after verifying there is one writer, preserve account access separately from world objects when authorized, deploy the generated inputs, then run `[Alpha2bWorldGen preview` followed by `[Alpha2bWorldGen apply CONFIRM-UOR-FELUCCA`. The command refuses an unexpected non-empty world and saves only after its UOR/Felucca audit passes. After restart, run `[Alpha2bWorldGen audit`; use the explicit trailing `rerun` argument only to rehearse convergence, never as a casual repair command.

`[ShardRulesStatus` is the registered staff baseline diagnostic. The outer README's `[Rules` example was not registered in the checked source when this skill was written. Verify command access and behavior in source before using a guide's example.
