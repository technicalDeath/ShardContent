# Mastery from 80, layered: readiness record

Date: 2026-10-09. Plan: [`Mastery-Layered-Plan.md`](Mastery-Layered-Plan.md). Evidence: [`Mastery-Layered-Evidence.md`](Mastery-Layered-Evidence.md).

**State: built and verified, uncommitted, not deployed.** Mastery has no feature flag, so the change reaches players only at the next deploy (`Deploy-Alpha1Baseline.ps1`), which is the owner's call. No ModernUO change (no engine rebuild or pin bump needed), no client change, no save-format change (no snapshot needed).

| Gate | Status |
| --- | --- |
| Owner sign-off on the plan and its recommendations | Done 2026-10-09 |
| Unit tests | 1085 passed, 0 failed (`20261009T145545121Z-3bc3d6`) |
| Live on a disposable host with the final build | See the evidence document (final run, all stages plus the restart check) |
| Real-client pictures read and sent to the owner | Done (Mastery window two pages, journal, guide pages, [SkillClasses) |
| Independent text audit | Done; seven findings fixed, three low ones left and listed |
| Activation | Not applicable (no flag) |
| README | **Waits for the deploy**; the new lines are written in the evidence document |
| Website | Unchanged; only when the owner asks |

**What the deploy changes for existing characters:** a skill at 80.0 to 89.9 enters Mastery on its next valid use (one entry message per skill); a skill at 90 or more keeps its stored allowance and claims the new, different amounts from its next claim; Faint Memories now stops at 80.0 (a character whose free points were still to be spent keeps them, and they now return only below 80.0).

**Decisions left with the owner:** none required to deploy. Worth knowing: no skill is in the VeryHard class today (so the 25-day tier is empty); the dedicated-player speed is one number per class in `shard-rules.json` (`skillGain.classes`, bands from 80), and the allowances are `mastery.allowanceTenths`, both changeable without code.

**Next:** deploy when the owner says so (stop the server, `Deploy-Alpha1Baseline.ps1`, start, check the log and `[ShardRulesStatus`), then update the README lines.
