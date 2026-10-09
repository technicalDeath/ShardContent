# Mastery from 80, layered: readiness record

Date: 2026-10-09. Plan: [`Mastery-Layered-Plan.md`](Mastery-Layered-Plan.md). Evidence: [`Mastery-Layered-Evidence.md`](Mastery-Layered-Evidence.md).

**State: built, verified, committed (`270c94b`), pushed and deployed to the dev host on 2026-10-09** (the owner's "Push and Deploy and activate"). Mastery has no feature flag, so the deploy is the activation. Deployed shard DLL 9230BBA82BF9 and `shard-rules.json` B107654DF849 match the build and the source; the dev server booted clean on them (Loading world done, no ERR or WRN) and was stopped again. No ModernUO change (no engine rebuild or pin bump), no client change, no save-format change (no snapshot needed).

| Gate | Status |
| --- | --- |
| Owner sign-off on the plan and its recommendations | Done 2026-10-09 |
| Unit tests | 1085 passed, 0 failed (`20261009T145545121Z-3bc3d6`) |
| Live on a disposable host with the final build | See the evidence document (final run, all stages plus the restart check) |
| Real-client pictures read and sent to the owner | Done (Mastery window two pages, journal, guide pages, [SkillClasses) |
| Independent text audit | Done; seven findings fixed, three low ones left and listed |
| Activation | Not applicable (no flag): live as of the deploy |
| README | Updated with the deploy (Skill gain, Mastery and Faint Memories lines) |
| Website | Unchanged; only when the owner asks |

**What the deploy changes for existing characters:** a skill at 80.0 to 89.9 enters Mastery on its next valid use (one entry message per skill); a skill at 90 or more keeps its stored allowance and claims the new, different amounts from its next claim; Faint Memories now stops at 80.0 (a character whose free points were still to be spent keeps them, and they now return only below 80.0).

**Decisions left with the owner:** none required to deploy. Worth knowing: no skill is in the VeryHard class today (so the 25-day tier is empty); the dedicated-player speed is one number per class in `shard-rules.json` (`skillGain.classes`, bands from 80), and the allowances are `mastery.allowanceTenths`, both changeable without code.

**Next:** nothing owed. The dev server is stopped; the website's Mastery copy changes only when the owner asks; the VeryHard class has no skill in it (an owner ruling if wanted).
