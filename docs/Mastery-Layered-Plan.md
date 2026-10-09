# Mastery from 80, layered on ordinary gain: plan for sign-off

Status: **signed off by the owner on 2026-10-09 ("Ok, let's keep it at 80, approved for implementation"), taking the recommendations in section 8 as written: threshold 80, allowances 2.0 / 1.4 / 1.0 / 0.8, class rates times 0.1 above 80, Faint Memories ceiling 80, no new flag, README with the deploy and the website only when asked. A lifetime (0 to 100) version was considered and declined the same day. Build and evidence: `Mastery-Layered-Evidence.md`.** Revised 2026-10-08 for the owner's schedule: casual Grandmaster in **10 / 15 / 20 / 25 days** (Easy / Standard / Hard / VeryHard), which makes the daily allowances 2.0 / 1.4 / 1.0 / 0.8 and, as he expected, calls for a slower gain rate above 80 for everything past the allowance (section 3 has the numbers). Origin: the owner's idea of moving Mastery down to 80 ("the road to mastery starts once you're an adept"), then of layering it on top of ordinary gain so that "if I just log in every day and play for a short while, I'll be GM in a week", while a player who macros, spends resources or plays six hours a day "still has gains and an advantage". The owner's earlier ruling (Beta 2a, 2026-10-02: Mastery starts at 90 and replaces ordinary gain above it) is being changed on purpose, before launch, which is the only time the audit said it should be.

## 1. Goal and exit criteria

A player who logs in and plays each skill a little every day reaches Grandmaster from Adept in 10 to 25 days depending on the skill's class (Easy 10, Standard 15, Hard 20, VeryHard 25), without macroing and without piles of resources. A player who plays far more still gains faster, so extra play is never wasted, but the gap is an advantage and not a shortcut. Nothing about the power ceiling changes: 100.0 per skill and 700 in total.

Exit (all checked live, by script, on a disposable host):
1. A skill passing 80.0 enters Mastery; its first valid use each daily cycle claims the allowance, and the next valid, successful uses are **guaranteed** +0.1 gains until the allowance is spent.
2. Once the allowance is spent, further uses gain **by chance** (ordinary gain, at the configured rate), never more than +0.1 per use.
3. With only the allowance's worth of valid uses each day, a Standard skill goes from 80.0 to 100.0 in 15 daily cycles (Easy 10, Hard 20, VeryHard 25), driven through the staff anchor-shift probe.
4. Everything else that touches the band is consistent: Skill Bank and Faint Memories, the 700 cap, the Mastery window, `[SkillClasses`, every guide page that mentions Mastery, gain or training (section 5a), the journal lines and the README. No player-facing sentence still says that Mastery replaces ordinary gain, or that it begins at 90. Checked in the real client and the pictures shown to you.

## 2. Current state (read from the code, 2026-10-08)

- **Mastery as built** (`MasteryEngine.cs`, `MasteryProgression.cs`): threshold is the constant `ThresholdFixedPoint = 900`. From 90.0 a skill claims an allowance per 24-hour cycle with its first valid, successful use (one that had a real chance of failing); allowances are Easy 2.0 / Standard 1.0 / Hard 0.6 / VeryHard 0.4 (`mastery.allowanceTenths`), banked up to three cycles; each valid, successful use spends 0.1 and gains +0.1 through stock `SkillCheck.Gain` (so cap displacement and the Skill Bank event stay stock). **`HandleSkillGain` returns true for every use at or above the threshold, which suppresses stock gain entirely there**, even when nothing is awarded. Playing more in a day gains nothing.
- **The gain curve** (`SkillGainCurveService`): multiplies the stock gain probability by a class multiplier from 10 to the threshold, and returns 1.0 at or above it. Validation requires every band to start below the threshold.
- **Classes** (`skillGain`): Easy 1.5x all the way; Standard 1.5x to 70 then 1.0x; Hard and VeryHard 1.5x to 70, 1.0x to 80, then 0.75x.
- **Faint Memories** (free points for new characters): `faintMemories.ceiling` is 90.0 and validation requires it to be no higher than the Mastery threshold, so free points never replace earned progress.
- **No feature flag.** Mastery replaces the old mechanic in place (owner ruling). Saved state is an account tag, version 2 (anchor, per-skill claimed cycle and stored allowance).
- **Where 90 is written:** the guide's Mastery page and the getting-started pages, `[SkillClasses`, the Mastery window, the README (Skill gain, Mastery and Faint Memories lines), and the website's progression section. About 50 tests pin it.
- **The hook needs no engine change:** stock calls `SkillGainOverride` before its own gain roll. Returning false lets stock roll (and apply the class multiplier); returning true consumes the use.

## 3. What the model says about the dials (read this before the questions)

From the Beta 1 gain model (`work/gain-model`, rerun 2026-10-08 as `layered.py`): stock gain probability per check at 80 to 100 is about 0.26 falling to 0.22 (success chance 0.5, a half-built character; about 0.17 to 0.13 for a character near the 700 cap). Hours to climb 80.0 to 100.0 by ordinary gain, by check cadence and by the multiplier applied above 80:

| Checks per hour | 1.5x (Easy today) | 1.0x (Standard today) | 0.75x (Hard today) | 0.5x | 0.25x | **0.1x** |
| --- | --- | --- | --- | --- | --- | --- |
| 120 (slow skills) | 4.7 | 7.1 | 9.4 | 14 | 28 | 71 |
| 360 (one check every 10 s) | 1.6 | 2.4 | 3.1 | 4.7 | 9.4 | 24 |
| 1,200 (fast crafts) | 0.5 | 0.7 | 0.9 | 1.4 | 2.8 | 7.1 |

These are best cases for time (every check is a real check; crafts and gathering are limited by resources as well). **The point: at today's class rates a dedicated player can climb the whole band in a few hours, so the layered system would leave the casual schedule looking slow and make macro the obvious strategy.** The contract's original targets (7.5 and 12.5 focused hours to 90 and 95) were replaced by the owner's simpler stock-relative rule on 2026-10-01 and are not what the shard does; I quoted them in error when we last discussed this. With a casual schedule of 10 to 25 days rather than a week, the multiplier has to be lower than the 0.25 I first suggested, or the dedicated player's advantage swallows the schedule (a one-hour-a-day player would be done in 5 to 9 days, a third to a half of the casual time).

**The casual side, your schedule.** The 20 points of the band are 200 tenths, so 10 / 15 / 20 / 25 days means allowances of **2.0 / 1.4 / 1.0 / 0.8** a day (20, 14, 10 and 8 valid, successful uses). 1.4 is the whole-tenth value that gives 15 days (14 cycles give 19.6, the fifteenth finishes it; 1.3 would give 16). Today's allowances of 2.0 / 1.0 / 0.6 / 0.4, applied over these 20 points, would take 10 / 20 / 34 / 50 days, so your schedule keeps Easy as it is and raises the other three (Standard 1.0 to 1.4, Hard 0.6 to 1.0, VeryHard 0.4 to 0.8).

**The dedicated side, with that schedule.** Model: days to Grandmaster when a player does a fixed number of checks a day (half of them successes, a half-built character), spending the allowance first and chancing the rest. The multiplier is applied to each class's own rate (Easy 1.5, Standard 1.0, Hard and VeryHard 0.75):

| Play a day (one check every 10 s) | **x0.1** (Easy 0.15 / Std 0.10 / Hard and VH 0.075 of stock) | x0.25 | x0.05 |
| --- | --- | --- | --- |
| The allowance and stop (a few minutes: about 40 / 28 / 20 / 16 checks) | 10 / 15 / 20 / 25 | 10 / 15 / 20 / 25 | 10 / 15 / 20 / 25 |
| 1 hour | 7 / 10 / 13 / 15 | 5 / 7 / 9 / 9 | 8 / 12 / 16 / 19 |
| 3 hours | 4 / 6 / 8 / 8 | 2 / 3 / 4 / 4 | 6 / 8 / 10 / 11 |
| 6 hours | 3 / 4 / 5 / 5 | 1 / 2 / 2 / 2 | 4 / 6 / 7 / 7 |
| Chance only, no allowance, 360 checks an hour (hours of play) | 16 / 24 / 32 / 32 | 6 / 9 / 13 / 13 | 32 / 47 / 55 / 55 |
| Chance only, 1,200 checks an hour, e.g. a fast craft (hours of play) | 5 / 7 / 9 / 9 | 2 / 3 / 4 / 4 | 9 / 14 / 16 / 16 |

(Each cell is Easy / Standard / Hard / VeryHard, in days unless marked hours.) Reading it: at **x0.1** a one-hour-a-day player finishes in about two-thirds of the casual time, a six-hour player in a fifth to a third of it, and a macroer who ignores the allowance still needs 5 to 9 hours of non-stop play even at 1,200 checks an hour. That is "an advantage" without making the casual schedule look pointless. **x0.05** nearly erases the advantage (a six-hour player still needs 4 to 7 days) and for a character near the 700 cap it runs into stock's 1% minimum chance per check (the model puts a Standard skill at exactly that floor), so the setting would stop doing anything there. **x0.25** gives the six-hour player the whole band in 1 to 2 days.

## 4. Design, rule by rule (current behavior beside each)

| # | Rule | Today |
| --- | --- | --- |
| 1 | **Mastery begins at 80.0** ("Adept" in this client's titles; Master is 90, Grandmaster 100). | 90.0 |
| 2 | **Claim and bank unchanged:** the first valid, successful use of an 80+ skill in a 24-hour cycle claims that skill's allowance; an unclaimed cycle is lost; unspent allowance carries up to three cycles; the skill must be Up; Skill Bank restoration still acts first and neither claims nor spends. | Same, from 90 |
| 3 | **Guaranteed gain:** a valid, successful use while the store holds 0.1 or more gains +0.1 and spends 0.1, with no roll. | Same, from 90 |
| 4 | **New: every other use gains by chance.** A use with the store empty, a failed check, or one Mastery does not take goes through the stock gain roll with the class multiplier for its value. Never more than +0.1 per use, so a guaranteed gain replaces the roll for that use. | Stock gain is suppressed from 90 |
| 5 | **The gain curve covers 10 to 100** (it ended where Mastery began). From 80 to 100 each class's rate is multiplied by 0.1 (question 3): Easy 0.15x, Standard 0.10x, Hard and VeryHard 0.075x of stock speed, for every use the allowance does not take. | 10 to 90 |
| 6 | **Allowances by class** (valid, successful uses a day): Easy 2.0, Standard 1.4, Hard 1.0, VeryHard 0.8 (20 / 14 / 10 / 8 uses; so 10 / 15 / 20 / 25 days from 80, your schedule). | 2.0 / 1.0 / 0.6 / 0.4 |
| 7 | **Faint Memories' ceiling becomes 80.0** (free points still stop where Mastery begins). The 5.0 pool is spent long before 80 for anyone, so nothing is lost. | 90.0 |
| 8 | **100.0 ends Mastery** for the skill and clears its store. At the 700 cap a guaranteed gain displaces a Down skill as stock does; with none, it grants and spends nothing. | Same |
| 9 | **Messages:** entry ("...has reached 80.0: Mastery begins. Your first N successful uses each day are guaranteed gains; after that gains come by chance as before. Use [Mastery to see your allowance."), claim, gain and Grandmaster lines as today with the new numbers. | "ordinary gain has ended and Mastery begins" |
| 10 | **Windows and text:** the Mastery window's bar runs 80 to 100; `[SkillClasses` shows speeds from 10 to 100 and each class's daily allowance; the guide's Mastery page is rewritten (it says "playing more in one day does not make it faster", which stops being true); the README lines and Faint Memories line follow. | 90 |
| 11 | **Existing characters:** no migration (the saved state is unchanged). A skill already at 80 to 89.9 enters on its next valid use; one at 90+ keeps its stored allowance. | n/a |

## 5. Work breakdown (all in ShardContent; no ModernUO or client change)

1. `MasteryEngine`: threshold 800, and a pure decision function (`Decide`: valid use? claimed? store? → guaranteed gain or stock roll), so rules 3 and 4 are unit-testable without game objects. Entry text.
2. `MasteryProgression.HandleSkillGain`: the layered flow (return true only when a guaranteed gain was made; false otherwise so stock rolls); entry, claim and gain messages.
3. `SkillGainCurveService`: the curve's upper limit becomes 100 (a `CurveCeiling` constant) in the multiplier, the validation and the `[SkillClasses` text.
4. `shard-rules.json`: `mastery.allowanceTenths` 20 / 14 / 10 / 8; the class bands above 80 at 0.15 / 0.10 / 0.075 / 0.075 (question 3); `faintMemories.ceiling` 80.0. `FaintMemories` validation text reads the new threshold.
5. The text and window changes in section 5a: `MasteryGump`, `MasteryProgression` journal lines, `SkillClassesGump`, `WelcomeGuide` (the Mastery page rewritten, the Commands line) and `WelcomeGuide.GettingStarted` (Training, Skill locks 101, Your first hour), the README, and a revision note in `Beta-2a-Mastery-Audit.md` ("superseded by Mastery-Layered-Plan.md").
6. Tests: `MasteryEngineTests` (threshold, the decision table, 15 / 10 / 20 / 25 cycles for Standard / Easy / Hard / VeryHard), `SkillGainCurveTests` (bands to 100, validation), `FaintMemoriesTests`, `WelcomeGuideTests`, `StatusWindowTests`, `GuideGettingStartedTests`. The probe and driver (`MasteryProbe.cs`, `mastery_live.py`) are updated for the new matrix.
7. Website copy (`index.html`: "Earned mastery" and the progression section) is changed **only when you say so**, after the deploy; it is a separate local repo that describes the shard.

## 5a. Text and window changes (the Mastery window and the Welcome guide)

Every player-facing sentence that says Mastery replaces ordinary gain, or says 90, stops being true. These are all the surfaces, what changes in each, and the proposed new wording (for your review; the final text goes in the evidence document as usual). Rule of thumb for the wording: **"allowance" stays the one word** for the daily guaranteed gains (the window, the journal, the guide and `[SkillClasses` already use it), and each place explains it as "guaranteed".

### The Mastery window (`MasteryGump`, `[Mastery`)

| Part | Today | Proposed |
| --- | --- | --- |
| Subtitle | "From 90.0 a skill grows by a daily allowance, not by chance" | "From 80.0 a skill is guaranteed gains every day, and still gains by chance" |
| Explanation under the cycle line (two lines, 36 px) | "A skill claims its allowance with its first valid, successful use in a cycle (24 hours). While it has allowance, each valid use gives +0.1, up to 100.0." | "A skill claims its allowance with its first valid, successful use in a cycle (24 hours). While it has allowance, each valid use is a guaranteed +0.1. After that, uses gain by chance as usual." |
| Bar column header | "90.0 to 100" | "80.0 to 100" (from the threshold constant, so it follows) |
| Footnote (under the table) | "Allowance is what a skill can still gain; it holds up to 3 cycles' worth. Missing a cycle never takes anything away: that cycle simply gives no allowance." | "Allowance is what a skill is still guaranteed to gain; it holds up to 3 cycles' worth. Beyond it, uses gain by chance as usual. Missing a cycle never takes anything away: that cycle simply gives no allowance." |
| Empty state and "waiting" line | "No skill is in Mastery yet. A skill at 90.0 or above..." | The same words with 80.0 (from the constant) |
| Row sub-line (per skill) | "Standard, 1.0 a cycle" | "Standard, 1.4 a cycle" (the new allowance) |
| Columns, rows per page, buttons, bar | Skill / Now / bar / Allowance / This cycle / To go; six rows a page; How it works and Skill speeds | Unchanged. The bar now spans 20 points, so one gain moves it half as far. More skills qualify at 80 than at 90, so expect more pages (the pager already handles it) |

Layout checks: the new explanation and footnote must each fit their two lines (about 83 characters a line at the window's text width; a unit test measures them with the shared line estimator) and the real-client picture checks nothing is clipped. No new data is needed in the view: "allowance stored" is the guaranteed gains left.

### The journal lines (`MasteryProgression`)

| Line | Today | Proposed |
| --- | --- | --- |
| Entry (first valid use at the threshold) | "Anatomy has reached 90.0: ordinary gain has ended and Mastery begins. Use [Mastery to see your allowance." | "Anatomy has reached 80.0: Mastery begins. Your first 14 successful uses each day are guaranteed gains, and after that gains come by chance, slowly. Use [Mastery to see your allowance." (the number is the class's allowance in tenths: 20 / 14 / 10 / 8) |
| Claim | "Mastery: Anatomy claims this cycle's allowance of 2.0." | "Mastery: Anatomy claims this cycle's allowance of 1.4." (new number only; Easy's stays 2.0) |
| Guaranteed gain | "Mastery advanced Anatomy to 90.1. Allowance left: 1.9." | Same shape with the new numbers |
| Login reminder, Grandmaster line | as they are | Unchanged |

### The Welcome guide (`[Welcome`)

| Page | What changes |
| --- | --- |
| **Mastery** (rewritten; it currently says "Below 90 a skill gains by chance... From 90 it no longer does" and "Playing more in one day does not make it faster") | See the draft below |
| **Training** | "From 90.0 a skill grows through Mastery instead." becomes "From 80.0 a skill also gains through Mastery: a daily allowance of guaranteed gains on top of ordinary gain (see the Mastery page)." |
| **Skill locks 101** | Under "Why a skill is not gaining", **remove** "It has reached 90.0: from there Mastery takes over" (a skill at 80 or more still gains, so it is no longer a reason). "Mastery allowance is spent only by a skill set to Up" becomes "Mastery's daily allowance is spent only by a skill set to Up" |
| **Your first hour** | One new sentence at the end of its "Your skills" section (after the Skill Bank, Faint Memories and `[SkillClasses` lines; no Mastery sentence is there today): "Once a skill reaches 80.0, use it a little every day: Mastery guarantees it gains, and it is the sure way to Grandmaster (see the Mastery page)." The Faint Memories sentence on that page ("between 10.0 and 90.0") follows the configured ceiling and becomes 80.0 on its own |
| **Skill Bank** and **Faint Memories** | The Faint Memories ceiling reads from the configuration, so "They never take a skill past 90.0, where Mastery begins" becomes "80.0" by itself once the ceiling is 80.0; check the wording still reads right |
| **Commands** | "[Mastery - Your Mastery cycle and what each Mastery skill can still gain." becomes "[Mastery - Your Mastery cycle and each Mastery skill's allowance." |
| **Welcome** page | No Mastery sentence today; nothing changes (the first-hour tip carries the news) |
| `[SkillClasses` window (the guide window it opens) | Overview: "Every skill trains in one of these classes. From skill 10 to 90 your skills gain faster than in stock Ultima Online..., From 90 a skill is in Mastery and grows by a daily allowance instead" becomes "Every skill trains in one of these classes. Your skills gain faster than in stock Ultima Online from skill 10 up to 80, and from 80 at the rate each class's page shows, because from 80 a skill also has a daily Mastery allowance: [Mastery shows yours." Each class page: the speed lines now run to 100 ("Skill 80 to 100: 0.1x stock speed" for Standard, from the bands), and its Mastery paragraph becomes "From 80.0 a skill in this class is guaranteed 1.4 each cycle, about 14 successful uses; beyond that it gains by chance at the rate above." |

Draft of the new **Mastery** page (numbers from the configuration, like today):

- **Why Mastery exists.** "In stock Ultima Online the last points of a skill are a grind: each one takes the most checks, and for crafters the most ingots or reagents. Mastery gives you a surer road: a daily allowance of gains that is guaranteed, so a little play each day takes a skill to Grandmaster without marathon sessions or piles of resources." / "Playing more is never wasted: once the day's allowance is spent, your uses still gain by chance, so a dedicated player is faster. The sure road is playing on more days. A day's allowance is about 20 successful uses for an easy skill, 14 for a standard one, 10 for a hard one and 8 for the hardest."
- **How it works.** "Mastery begins at 80.0 (Adept). Your character has a 24-hour cycle, which starts the first time you hold a skill at 80.0 or higher, and in each cycle a skill has an allowance: 2.0 for easy skills, 1.4 for standard ones, 1.0 for hard ones and 0.8 for the hardest. [SkillClasses lists every skill's class." / "A skill claims its allowance with its first valid, successful use in the cycle. A valid use is a success that had a real chance of failing: trivially easy actions and failed attempts count for nothing. While the allowance lasts, each valid, successful use is a guaranteed +0.1, up to Grandmaster (100.0). When it is spent, further uses still gain by chance, but slowly." / "So going from 80.0 to 100.0 on the allowance alone takes 10 days for an easy skill, 15 for a standard one, 20 for a hard one and 25 for the hardest. Playing more shortens that, but never takes it to nothing." / "Nothing you have gained is ever taken away. A cycle in which a skill is not used simply gives that skill no allowance, and it is not made up later. Allowance you claimed but did not spend carries over, up to 3 cycles' worth."
- **Good to know.** The existing Up and cap paragraph, the Skill Bank sentence ("Points held in your Skill Bank come back before Mastery applies"), and the `[Mastery` paragraph unchanged except "what is stored" becomes "what is left".

### The README and the website

The README's **Skill gain**, **Mastery** and **Faint Memories** lines are rewritten with the deploy (the deployed README describes deployed behavior): the 10-to-100 speeds, "Mastery (80.0 to 100.0): guaranteed daily gains on top of ordinary gain", the allowances, and "past 80.0". The website's "Earned mastery" card and its "Up to 90 / 90 to GM" progression section change **only when you say so**, after the deploy.

### Tests that pin this text

`WelcomeGuideTests` (24 mentions), `StatusWindowTests` (21), `GuideGettingStartedTests`, `MasteryEngineTests`, `SkillGainCurveTests`, `FaintMemoriesTests` are updated with the new wording; new tests pin that no page still says 90.0 as the threshold, that the "playing more does not make it faster" sentence is gone, that the Skill locks page no longer lists reaching the threshold as a reason a skill is not gaining, and that the window's explanation and footnote fit their lines.

## 6. Verification

- **Unit:** the decision table (valid or not, claimed or not, store empty or not, at the cap, at 100), the curve to 100, validation, config values, the committed allowances, 15 / 10 / 20 / 25 cycles to 100 from 80 (Standard / Easy / Hard / VeryHard), Faint Memories ceiling, text pins.
- **Live, disposable host, real Navrey clients** (`mastery_live.py`, with the existing anchor-shift probe):
  - L1 at 79.9 ordinary gain and no Mastery; L2 at 80.0 the first valid success gives the entry message, the claim and a guaranteed +0.1.
  - L3 the first N valid successes after a claim are all gains (ten uses give exactly +1.0, not a chance outcome, and a Standard skill's fourteen give +1.4); L4 with the store empty, 200 further valid uses gain at about the configured rate and never above +0.1 each.
  - L5 a failed check claims and spends nothing and may roll; L6 after a 24-hour shift the skill claims again; a missed cycle is lost; the store stops at three cycles.
  - L7 **the exit criterion:** a Standard skill goes 80.0 to 100.0 in fifteen shifted cycles using only the allowance (Easy 10, Hard 20, VeryHard 25), then Mastery ends. Run on a disposable host with the anchor shift, so 70 shifted cycles take minutes, not months.
  - L8 at the 700 cap a guaranteed gain displaces a Down skill and the point is banked; L9 Skill Bank and Faint Memories act first, Faint Memories stops at 80.0; L10 state survives a restart; L11 a character with an old-threshold store carries on; L12 `[Mastery`, `[SkillClasses` and the guide read right.
- **Real client, shown to you:** the Mastery window (bar 80 to 100) with a full page of skills and with none, the `[SkillClasses` overview and a class page, the guide's Mastery, Training, Skill locks 101, Your first hour and Commands pages, and the entry, claim, guaranteed-gain and chance-gain lines in the journal. Each is read for clipped or wrapped text before it is sent.
- **Text audit:** an independent read of every changed player sentence against the code, as for the earlier guide work (that audit found about 25 wrong sentences in my first draft of the guide pages), and a search of the source for any remaining "90" that means the threshold.
- No save-format change, so no snapshot is needed.

## 7. Activation

**No flag** (Mastery has none; the Beta 2a ruling replaced it in place). The change takes effect at the next deploy, which stays your call. It touches no player-visible rule that is live for real players: the world is the dev world.

## 8. Open questions (recommendation first)

1. **Threshold 80.0?** Yes (your direction). The guarantee starts at Adept.
2. **Allowances (your schedule, settled 2026-10-08):** **Easy 2.0 / Standard 1.4 / Hard 1.0 / VeryHard 0.8**, so 10 / 15 / 20 / 25 days from 80. (Standard 1.4 rather than 1.33 because allowances are whole tenths; 1.4 gives 15 days.) Not a question any more; listed so the sign-off covers it.
3. **Dedicated players' speed above 80, for every use the allowance does not take:** recommended **today's class rates times 0.1** (Easy 0.15x, Standard 0.10x, Hard and VeryHard 0.075x of stock): a one-hour-a-day player is done in about two-thirds of the casual time, a six-hour player in a fifth to a third, and chance-only play takes 16 to 32 hours at one check every 10 seconds. Alternatives: **times 0.25** (the first suggestion: a six-hour player finishes in 1 to 2 days, a one-hour player in a third to a half of the casual time), or **times 0.05** (the advantage nearly vanishes, and a character near the 700 cap already sits on stock's 1% minimum chance per check, so it cannot slow them further).
4. **Faint Memories ceiling 80.0?** Yes (see rule 7).
5. **No new flag?** Yes, as above. Alternative: a `masteryLayered` flag, off at deploy, if you want to see it on the dev host before it counts.
6. **Website and README:** the README changes with the deploy; the website only when you ask.

## 9. Out of scope / deferred

A minimum-uses claim threshold, a skill-reachability audit and a downtime credit (all declined on 2026-10-02 and still declined); anti-macro (off); stat gain; resource costs of crafts; the 0 to 80 stretch of the curve; making the threshold a config value (it stays a code constant, because the curve and the windows read it); a per-player opt-in or opt-out (the layered rule makes one unnecessary).

## 10. Risks

- **The dedicated path stays open to macro.** That is the design: extra play is rewarded. At 0.1 the advantage is a day or three of heavy play against 10 to 25 casual days, not instant, but bots and powerleveling have a reason to exist again, and the shard's gather and action repeats make the dedicated path easy.
- **A launch-week race to GM** by the most dedicated players; the gap closes in 10 to 25 days for everyone else, per skill class. Hot Zone fairness: the gap between a new character and an established one is at most the casual schedule.
- **The guaranteed gain is not a rate limit.** A player at the cap with no Down skill gets nothing from it, as today.
- **More messages:** up to 20 guaranteed-gain lines a day per skill for Easy skills, and chance gains on top. If that is too noisy the gain line can be batched later.
- **Changing it after launch strands players mid-band**: do it now, before real players, as the 2026-10-02 audit said.
- Build order: the engine's pure rule and its tests, the progression flow, the curve, the config, then the windows and text, the live pass, the real-client pictures, the evidence and readiness records.
