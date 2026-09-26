---
name: britannia-renaissance
description: Orient agents working in the Britannia Renaissance multi-repository ModernUO workspace; identify repository ownership, source of truth, local runtime, and project safety boundaries before cross-repository changes.
---

# Britannia Renaissance workspace

Use this skill when a request spans the shard, server, clients, or local tooling. Read only the specialized skill needed for the next operation: [shard-content-workflow](../shard-content-workflow/SKILL.md) for content/build/server work, or [navrey-shard-test](../../../../Navrey/.agents/skills/navrey-shard-test/SKILL.md) for agent-driven client tests. Resolve paths from the workspace root (the parent of `ShardContent`); do not assume this machine's username or path on another checkout.

## Ownership and layout

These are adjacent checkouts, not one source tree. Check `git -C <repo> status --short` and `git -C <repo> remote -v` for each repository you touch; the outer workspace also has a separate Git index, so never use an outer `git add .` for work in a nested repository.

| Path | Role |
| --- | --- |
| `ShardContent/` | `technicalDeath/ShardContent`; shard-owned C# extension, policy/configuration sources, tests, design docs, deployment tooling. Put new shard behavior here where an extension point permits it. |
| `ModernUO/` | `technicalDeath/ModernUO` fork; engine and stock content. Change it only for required integration or engine behavior, following its `AGENTS.md` and `CLAUDE.md`. |
| `Navrey/` | `technicalDeath/navrey` fork of ClassicUO; agent-controlled graphical/headless client and CLI. Its `.claude/skills/` contain detailed gameplay guides; the Codex skill in this checkout covers local verification. |
| `ClassicUO/` | `technicalDeath/ClassicUO`; separate player client checkout. Root launchers target local client builds. |
| `Navrey-before-fork/` | Upstream `johnpwrs/navrey` reference checkout; do not treat it as the active client. |
| `website/` | Local static shard site in a separate repository; no configured remote at time of mapping. Its copy may describe planned features, so verify active flags before publishing claims. |
| `CodexLoopHarness/` | Portable local Codex goal/heartbeat harness; not currently its own Git repository. |
| `UOData/`, `dotnet/`, `work/` | Local game assets, portable .NET SDK, and scratch/staging evidence. Do not commit these or use `work/` as authoritative source. |

`ShardContent/docs/ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md` and the alternative plan describe intended phases. `ShardContent/data/configuration/shard-rules.json` plus actual source and live diagnostics establish enabled behavior. Some older docs and root launch guidance predate Alpha 2; check the current configuration and implementation before claiming a feature exists.

Check that a root launcher exists and its arguments match the active server's client-version gate before relying on older launch instructions. Use Navrey for agent smoke tests.

## Current integration

The shard runs UOR rules on Felucca, including its Lost Lands, using local official client data. ShardContent builds `BritanniaRenaissance.Content.dll` into `ModernUO/Distribution/Assemblies`; `ModernUO/Distribution/Data/assemblies.json` registers it beside `UOContent.dll`. The deployed configuration is in `ModernUO/Distribution/Configuration`; source-controlled policy is in `ShardContent/data/configuration`. ModernUO reads the deployed copies, not the source files directly.

The Alpha 2 gates cover Safe World, automatic murder adjudication, theft protection, and Knocked Out; later roadmap systems have separate flags. Re-check the current flags for every task. The world saves and accounts under `ModernUO/Distribution/Saves` are local mutable state; use a disposable distribution for destructive gameplay tests, migrations, and multi-account matrices. Do not disclose credentials or copy `.env`, accounts, saves, or raw private logs into skills or commits.

Before launching ModernUO against the shared distribution, verify both that `127.0.0.1:2593` is free and that no process has that distribution's `ModernUO.dll`, `Server.dll`, or `Assemblies/UOContent.dll` loaded. A server process can lose or lack its game listener while its world loop and autosaves remain active, so a port-only check can permit concurrent writers to `Distribution/Saves`. Reuse the loaded-module scan in `ShardContent/tools/Deploy-Alpha1Baseline.ps1`; do not start a second instance or modify saves until the existing process is intentionally stopped.

Do not use ModernUO Admin -> World Building -> `Do everything` on this UOR/Felucca shard. Stock `Decorate`, `SignGen`, `TelGen`, and `DoorGen` populate disabled facets in whole or in part, while the Admin spawner action imports every file under `Data/Spawns/shared/felucca`, including post-UOR locations. Plan initial-world generation per system and facet on a disposable save, with an explicit era-reviewed spawner allowlist. Factions are disabled for initial launch, and champion-style systems require an owner design decision.

Alpha 2b initial-world generation is shard-owned. Its source manifest and overrides are under `ShardContent/data/world-generation/alpha2b`; `ShardContent/tools/Prepare-Alpha2bWorldData.ps1` validates the ModernUO pin, reads stock inputs from that pinned Git commit rather than the working tree, and produces alternate, disposable runtime inputs under `ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b`. `Deploy-Alpha1Baseline.ps1` runs that preparation step. Use the owner-only `[Alpha2bWorldGen preview`, `[Alpha2bWorldGen apply CONFIRM-UOR-FELUCCA`, and `[Alpha2bWorldGen audit` workflow instead of stock cross-facet commands. The optional trailing `rerun` argument is reserved for an intentional convergence rehearsal over an already generated baseline. The command saves only after its facet/content audit passes.

## Maintenance

Update this skill when repository ownership, remotes, layout, integration, runtime configuration, or project safety constraints change. Record a temporary test outcome in the task response or appropriate test log, not as a timeless skill rule.
