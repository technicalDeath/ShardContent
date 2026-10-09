# Mastery from 80, layered on ordinary gain: evidence

Plan: [`Mastery-Layered-Plan.md`](Mastery-Layered-Plan.md). Readiness: [`Mastery-Layered-Readiness.md`](Mastery-Layered-Readiness.md). Built 2026-10-09 after the owner's sign-off ("Ok, let's keep it at 80, approved for implementation"). **Committed (`270c94b`), pushed and deployed to the dev host on 2026-10-09** on the owner's "Push and Deploy and activate". Mastery has no flag, so deploying is what activates it; the dev server booted clean on the deployed build (no warnings or errors, shard rules and era gates validated) and was stopped again. The root `README.md` lines were updated with the deploy.

## Sign-off and decisions

| Date | Decision |
| --- | --- |
| 2026-10-08 | Idea (owner): Mastery from Adept (80), layered on ordinary gain; the casual player is Grandmaster on a schedule, a heavier player is faster |
| 2026-10-08 | Schedule (owner): casual Grandmaster in **10 / 15 / 20 / 25 days** (Easy / Standard / Hard / VeryHard), "even slower post 80 gain rate to compensate". Allowances become 2.0 / 1.4 / 1.0 / 0.8 (whole tenths; 1.4 is the value that gives 15) |
| 2026-10-09 | Question (owner): should the guaranteed gains run for the whole life of the character, 0 to 100? Answer given: not as a first step (the grind is at the top; a guarantee costs about 2 attempts per +0.1 so it saves no resources lower down; it would make every character Grandmaster in weeks before the ceiling content exists; widening later is easy, narrowing strands players). **Owner: keep it at 80.** |
| 2026-10-09 | Sign-off on the plan with its recommendations: threshold 80.0; class rates times 0.1 from 80 (Easy 0.15, Standard 0.10, Hard and VeryHard 0.075); Faint Memories ceiling 80.0; no new flag; README with the deploy, website only when asked |

## What changed

| Where | Change |
| --- | --- |
| `MasteryEngine.cs` | Threshold 800. New pure `Decide` (not Mastery / finished / chance roll / guaranteed), `MinimumCycles`, `UseOutcome` |
| `MasteryProgression.cs` | `HandleSkillGain` returns true only when a guaranteed gain is made (or a skill is at 100.0); every other use is handed back to the stock roll. Entry line, defaults 20 / 14 / 10 / 8, login reminder counts only skills set to Up |
| `SkillGainCurveService.cs` | The curve runs 10 to 100 (`CurveCeiling`); validation, `Describe`, `SpeedLines`, `SpeedSummary` follow; speeds print to three decimals (0.075x) |
| `data/configuration/shard-rules.json` | `mastery.allowanceTenths` 20 / 14 / 10 / 8; class bands from 80: easy 0.15, standard 0.1, hard and veryHard 0.075; `faintMemories.ceiling` 80.0 (code default too) |
| `MasteryGump.cs` | New subtitle, explanation and footnote (public builders, so tests pin them); bar 80 to 100 follows the constant |
| `WelcomeGuide.cs`, `WelcomeGuide.GettingStarted.cs` | Mastery page rewritten; Training, Skill locks 101, Your first hour, Commands line; the Very Hard class is named only when a skill is in it (`VeryHardInUse`) |
| `SkillClassesGump.cs` | Overview and per-class Mastery paragraph |
| Docs | `Beta-2a-Mastery-Audit.md` and the roadmap carry a superseded-by note; `Skill-Bank-Faint-Memories.md` ceiling 80.0; `To-Do-List.md` |
| Tests and tools | `MasteryEngineTests`, `SkillGainCurveTests`, `FaintMemoriesTests`, `StatusWindowTests`, `WelcomeGuideTests`, `GuideGettingStartedTests`; `mastery_live.py`, `MasteryProbe.cs` (new verb `TestOnlyMasteryRolls`), `mastery_layered_shots.py`, `faint_live.py` (G1 to G3 at 80.0), `gain_live.py` (rates below 80; the 80 and above rates moved to the Mastery driver) |

No ModernUO change, no client change, no save-format change (the Mastery state is the same account tag, version 2, so no snapshot was needed). A character with a skill at 90 or more keeps its stored allowance; every new cap (3 cycles of the new allowance) is at least the old one.

## Verification

### Unit (xunit, isolated runner, no engine change so no UOContent run)

| Run | Result |
| --- | --- |
| `20261009T143656580Z-3ee74b` | 21 failures, all tests that pinned the old numbers or wording (expected; each updated) |
| `20261009T144539506Z-c37706` | 1083 passed, 0 failed |
| `20261009T145545121Z-3bc3d6` (final, after the text audit fixes) | **1085 passed, 0 failed** |

New tests include: the layered decision table (below 80, at 100, a valid use with allowance, the claim, a store empty after claiming, an invalid use, a full bank, a zero allowance); a day-by-day simulation with chance gain switched off that takes Easy, Standard, Hard and VeryHard from 80.0 to 100.0 in exactly 10 / 15 / 20 / 25 daily cycles; a skipped day is never made up; `MinimumCycles`; the shipped configuration (allowances, schedule, ceiling, slower-than-before bands from 80); band validation to 100; text pins (no "90", "not by chance" or "ordinary gain has ended" anywhere in the Mastery window text; the guide pages; the window's two explanatory blocks fit their two lines).

### Live (disposable host with the final build, real Navrey clients; driver `tests/scenarios/mastery/mastery_live.py`)

Host `mastery-layered` (a copy of the dev distribution with the new shard DLL, sha 96B7A54ADE9D, and the shipped `shard-rules.json` plus one test-only change: Poisoning listed as veryHard, so the VeryHard class has a live skill). Three ordinary test characters as Navrey sessions plus `admin`, `TestOnlyProbe.dll` and `MasteryProbe.dll`. A first full pass on the build before the text-audit fixes (DLL 80077D84AD29) was 29/29 and 2/2 after a restart; the **final pass below is on the build that ships** (the sha above, the same one the real-client pictures show), **29/29, then 2/2 after a server restart**. The host was removed afterwards.

| Case | What it proves | Result |
| --- | --- | --- |
| M1 | At 80.0 the first valid use on a real Anatomy check gives the entry line ("Your first 20 valid, successful uses each day are guaranteed gains..."), claims 2.0 and gains +0.1 | pass |
| M2 | Twenty guaranteed gains empty the store: exactly 20 "Mastery advanced" lines, 0.0 stored, claimed this cycle | pass |
| M3 | With the store empty, valid uses make no Mastery gain or claim (they gain only by chance; Anatomy moved 82.0 to 82.1 in one run) | pass |
| M4 | The [Mastery window shows the cycle, the 24-hour explanation, the class and allowance, and no "90" | pass |
| M5, M6 | A shifted 24 hours lets the skill claim again; the store never holds more than three cycles (5.9 of 6.0) | pass |
| M7, M8 | Below 80.0 Mastery does not act; back at 80.0 in the same cycle: no second claim, no second entry line, a gain from the store | pass |
| M9, M10 | The earlier mechanic's saved state is discarded and Mastery starts fresh | pass |
| M11 | Each skill shows its class and allowance (Alchemy hard 1.0, Magery standard 1.4) | pass |
| C0 to C3 | At the 700-point cap: with no Down skill nothing is granted or spent; with one, the gain displaces it as stock does, the point reaches the Skill Bank | pass |
| L3 | Five sure successes with 0.5 stored are exactly five guaranteed gains and the store is then empty | pass |
| L5 | Sixty failed checks spend nothing from the store (and may still roll by chance, never above +0.1) | pass |
| L4 (x3) | 20,000 real checks per class at 85.0 with the store empty: Standard 564 gains (expected 568), Easy 854 (852), Hard 434 (426); multipliers 0.1 / 0.15 / 0.075; none above +0.1; the store untouched | pass |
| L7 (x4) | **The exit test.** With exactly the day's allowance of valid uses, shifted one daily cycle at a time: Easy 80.0 to 100.0 on day 10, Standard on day 15, Hard on day 20, VeryHard on day 25; every earlier day gave exactly the allowance (L7b) | pass |
| F0 to F3 | Faint Memories: ready after 25 hours; the last 0.2 before 80.0 comes back in one step (798 to 800, 4.8 left); at 80.0 the pool is left alone; 79.9 returns 0.1 | pass |
| R1, R2 (after a server restart) | The Mastery state survives (Anatomy claimed, 1.9 stored); the login reminder counts only the skills that can claim: "1", with Alchemy Up and unclaimed, Magery Down, Anatomy already claimed | pass |

### Rate check beyond the driver

At 40,000 real checks per class (skill held at 85.0, success chance 0.5, store empty), against the stock formula with the class multiplier: Standard 845 gains, expected 835 (z 0.3); Easy 1278, expected 1285 (z -0.2); Hard 685, expected 659 (z 1.0). None above +0.1. This is the server's own path (`SkillCheck.CheckSkill`, the gain hook, the stock roll), not the Python model.

### Real client (ClassicUO, screenshots under `work/mastery-layered/shots/`, photographed on the shipped configuration)

| Picture | Shows |
| --- | --- |
| `mastery-empty.png`, `mastery-waiting.png` | [Mastery with no skill in it, and with a skill at 80.0 waiting for its first use |
| `mastery-p1.png`, `mastery-p2.png` | The window with eight skills over two pages: bar 80.0 to 100, new subtitle, two-line explanation, two-line footnote, allowance "of 4.2" and so on |
| `journal-entry.png`, `journal-guaranteed.png` | The journal as Tactics enters Mastery at 80.0, claims 1.4 and gains 80.1 to 80.4 |
| `guide-mastery.png`, `guide-mastery-2.png` | The rewritten Mastery page (three classes named, "at least 10 active days ... 15 ... 20") |
| `guide-training.png`, `guide-locks-2.png`, `guide-firsthour-2.png` | Training, Skill locks 101 (no "reached 80.0" reason), Your first hour (the new line; Faint Memories "between 10.0 and 80.0") |
| `guide-commands-2.png` | The Commands line for [Mastery. (The Skill Bank page's Faint Memories sentence, "past 80.0, where Mastery begins", sits below the pictures I took and is pinned by a unit test; the same ceiling shows in `guide-firsthour-2.png`.) |
| `classes-overview.png`, `classes-standard.png` | [SkillClasses with the speeds to 100 and the per-class Mastery paragraph |

Every picture was read for clipping and wrapping. The window's explanation and footnote fit their two lines; the subtitle fits one.

### Text audit (independent subagent, read-only, against the code)

About 40 sentences checked true. It found and I fixed: the Mastery page named a "very hard" class no skill is in (now named only when a skill is in it); "failed attempts count for nothing" was wrong (a failed check can still gain by chance; reworded); the entry journal line said "slowly" even with the speed curve switched off (now guarded); the login reminder counted skills set to Down or Locked, which can never claim (now counts Up skills only); "Its first valid..." had no antecedent (reworded); the window subtitle read as unconditional ("has guaranteed daily gains"); "days" now reads "active days"; "successful uses" now says "valid, successful uses" in the journal, the class pages and the guide. Left as they are: two low items (the nominal speed multipliers sit under stock's 1% minimum chance per check for characters near the 700 cap; the Waiting line says "next successful use" though any eligible use starts the cycle) and the latent plurals ("1 cycles' worth" only if bankCycles were 1).

## Player-facing text (for the owner's review)

- Mastery window: subtitle "From 80.0 a skill has guaranteed daily gains, and still gains by chance"; explanation "A skill's first valid, successful use in a cycle (24 hours) claims its allowance. While it lasts, each valid use is a guaranteed +0.1; after it, by chance."; footnote "Allowance is what a skill is still guaranteed to gain; it keeps up to 3 cycles' worth. A cycle you miss gives no allowance but takes nothing away."
- Journal: "Tactics has reached 80.0: Mastery begins. Your first 14 valid, successful uses each day are guaranteed gains, and after that gains come by chance, slowly. Use [Mastery to see your allowance."; claim and advance lines unchanged in shape.
- Guide: the Mastery page (full text in the pictures), Training ("From 80.0 a skill also gains through Mastery: a daily allowance of guaranteed gains on top of ordinary gain"), Skill locks 101 ("Mastery's daily allowance is spent only by a skill set to Up"), Your first hour ("Once a skill reaches 80.0, use it a little every day: Mastery guarantees it gains, and it is the sure way to Grandmaster"), Commands ("[Mastery - Your Mastery cycle and each Mastery skill's allowance.").
- [SkillClasses: overview and per-class paragraph ("From 80.0 a skill in this class is guaranteed 1.4 each cycle, about 14 valid, successful uses; beyond that it gains by chance, at the speed above.").

## README (applied with the deploy, 2026-10-09)

- **Skill gain.** Skills train faster than stock ModernUO between 10 and 80, and slower from 80, where Mastery's guaranteed daily gains do the work. Easy skills gain 1.5x faster up to 80, then at 0.15x. Standard skills gain 1.5x faster up to 70, at the stock rate to 80, then at 0.1x. Hard skills (Alchemy, Animal Taming, Blacksmithy, Poisoning) gain 1.5x faster up to 70, at stock to 80, then at 0.075x. Below skill 10 gain is unchanged. `[SkillClasses` opens a window with every skill's class and speeds.
- **Mastery (80.0 to 100.0).** From 80.0 (Adept) a skill has a guaranteed daily allowance on top of ordinary gain. Your character has one 24-hour cycle. In each cycle, a skill claims its allowance with its first valid, successful use (one that had a real chance of failing; trivially easy actions never count, and a failed attempt claims and spends nothing): Easy skills 2.0, Standard 1.4, Hard 1.0 per cycle (the same classes as above). Each valid, successful use then gives a guaranteed +0.1 until the allowance is spent, so Grandmaster takes at least 10, 15 or 20 active days on the allowance alone. After that, uses still gain by chance, slowly. A cycle a skill isn't used in simply gives it no allowance (it isn't made up later, and nothing you've gained is taken away); unspent allowance carries up to three cycles. `[Mastery` opens a window with your cycle and every Mastery skill.
- **Faint Memories.** ... "They never take a skill past 80.0 (where Mastery begins)" ...

## Limits and notes

- **No skill is in the VeryHard class** (`skillGain.skills` assigns none), so the 25-day tier exists in the rules and was exercised live (a test-only host override put Poisoning in it) but is empty in the shipped game. The guide names a class only when it has skills. Moving a skill there is a class-assignment decision for the owner.
- The 10 / 15 / 20 / 25 are minimums on the allowance alone, at one valid, successful use per allowance point each cycle; real play is a little slower (failed checks) or faster (chance gain on top). The chance rates assume the formula the server runs; the model's hours (about 16 to 32 hours of chance-only play at one check every 10 seconds, a six-hour-a-day player in a fifth to a third of the casual time) are estimates for a half-built character.
- The real ClassicUO client prints its own blue "Your skill in X has increased by 0.1" line for some changes; it is the client's, and appears between Mastery lines in `journal-guaranteed.png`.
- The deploy rebuilt the shard DLL from the committed source (sha 9230BBA82BF9); its hash differs from the host build that was tested live (96B7A54ADE9D). The source had not changed in between (the last source edit was before that host build), so the likely cause is the commit id a build embeds; I did not diff the two files. The unit suite and the live drivers were not rerun on the deployed copy beyond the clean boot above.
- The website's "Earned mastery" and "Up to 90 / 90 to GM" copy is unchanged; the README lines above wait for the deploy.
