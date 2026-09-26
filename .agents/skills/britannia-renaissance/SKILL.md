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

## Maintenance

Update this skill when repository ownership, remotes, layout, integration, runtime configuration, or project safety constraints change. Record a temporary test outcome in the task response or appropriate test log, not as a timeless skill rule.
