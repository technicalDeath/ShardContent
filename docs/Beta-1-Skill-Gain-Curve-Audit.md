# Beta 1 item 3: sub-95 skill-gain curve, survey, plan and evidence

Roadmap: [Beta 1](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 3 (deferred from Alpha 3 J-4). Design contract: Hot Zones plan, "Skill gain" (the Standard pre-Mastery curve, difficulty classes, tuning workflow). Readiness record: `Beta-1-Skill-Gain-Curve-Readiness.md` (written at close).

**Status: closed 2026-10-01. Design signed off by the owner, built, verified and activated on the dev host. See the readiness record.**

## Current behavior (verified in source)

- **One probability per check.** `SkillCheck.CheckSkill` (ModernUO `Skills/SkillCheck.cs`) for a skill at 10.0 or above, with AoS off:
  `gc = ((Cap - Total)/Cap + (SkillCap - Base)/SkillCap) / 2`, then `gc = (gc + (1 - chance) * (success ? 0.5 : 0.2)) / 2`, then `gc *= skill.Info.GainFactor`, floored at 0.01, and a gain happens when `gc >= random`. A gain is **+0.1** (one tenth). Below 10.0 every eligible check gains 0.1 to 0.4 with no roll.
- **`GainFactor` is 1.0 for all 58 skills** in `Distribution/Data/skills.json`. It is the only existing per-skill knob and it is a single flat multiplier.
- **Anti-macro is disabled** (`antimacro.json` `Enabled: false`); its per-skill list is inert.
- **Mastery and Skill Bank act first.** `SkillEvents.SkillGainOverride` runs before the stock roll. Skill Bank restoration (`SkillBankService.TryRestore`) returns "handled" and restores 0.1 on every eligible check for a banked skill, so it is independent of the probability roll. Mastery (`MasteryProgression.HandleSkillGain`) suppresses stock gain from 95.0. A change to the stock roll therefore cannot affect either, provided the new code lives only in the stock-roll branch.
- **Stat gain** rides on the same check (`LegacyGain`, 10-minute delay) and is out of scope.

## What the contract asks for

Standard skill, focused training, no bonuses: 0-50 in 1 h, 50-70 in 1.5 h, 70-80 in 2 h, 80-90 in 3 h, 90-95 in 5 h (cumulative 1 / 2.5 / 4.5 / 7.5 / 12.5 h). Easy / Standard / Hard / VeryHard classes with per-skill overrides, preserving era-relative difficulty (Animal Taming stays distinctly slower), calibrated against measured time per skill, classification owned by shard configuration and visible to players. The same four class names drive Mastery in Beta 2a (1.0 / 0.5 / 0.3 / 0.2 per cycle; 5 / 10 / 17 / 25 cycles).

## Finding 1: stock has the wrong shape, so one factor cannot do it

A model of the stock formula (check chance 0.5, total skill 350/700) gives mean gain probability per check of 0.39 at 10-50, 0.31 at 50-70, 0.28 at 70-80, 0.25 at 80-90 and 0.23 at 90-95. The contract's targets need, for a skill with 360 checks per hour, probabilities of about 1.1 / 0.37 / 0.14 / 0.09 / 0.03 in those bands: **faster than stock early, much slower than stock late** (multipliers of roughly 2.9, 1.2, 0.5, 0.4 and 0.12). A single `GainFactor` per skill cannot produce that, so the multiplier has to depend on the skill's current value (the band).

## Finding 2: the targets are capped by how often a skill can be checked

A check gains at most 0.1, so 50 points need at least 500 eligible checks. At 360 checks per hour the best possible 0-50 time is 1.4 h even at 100% gain probability; at 120 per hour it is 4.2 h. The 1 h Standard target for the first band is only reachable by skills that offer roughly 560 or more eligible checks per hour. Per-skill cadence therefore decides which bands the Standard targets are achievable in; the survey below records it.

(Model files: `work/gain-model/model.py`, `bands.py`; scratch, to be replaced by the calibration test described in the plan.)

## Survey: how each skill is trained

(Filled from the three read-only source surveys.)

### Stealth, bard and utility skills (source survey, UOR branches only)

"Gap" is the shortest time between gain-eligible checks from the code's use delay; real cycles also include double-click and target round trips. A check gains on success or failure. Chance is `(skill - min) / (max - min)`; a range of 0 to 100 means chance equals skill/100.

| ID | Skill | Check and range | Gap | Notes |
| ---: | --- | --- | --- | --- |
| 2 | Animal Lore | target, 0-120 | ~1 s | needs a tamed pet below skill 100 |
| 6 | Begging | target NPC, 0-100 | ~10 s | non-player human within 2 tiles; bad karma can refuse before the check |
| 9 | Peacemaking | self 0-120 (plus a Musicianship check each use) | 5 s on success, 10 s on failure | trains on yourself with no creature; two gain checks per use |
| 14 | Detect Hidden | 0-100 on self or ground | ~1 s (UOR) | no hidden person needed |
| 15 | Discordance | target, difficulty-based (+/-25) | 12 s | needs a creature; instrument charges |
| 19 | Forensic Evaluation | corpse 0-100 (mobile only from 40) | ~1 s | needs corpses |
| 21 | Hiding | location 0-100 | 10 s | blocked near houses and combat |
| 22 | Provocation | two creatures, difficulty-based | 5 s fail / 10 s success | needs two monsters |
| 24 | Lockpicking | lock level range | ~3-4 s (inferred) | needs re-lockable boxes; consumes picks |
| 28 | Snooping | container 0-100 | not in code | needs a hostile target; karma loss |
| 29 | Musicianship | 0-120 | 6 s | also checked inside every bard skill |
| 30 | Poisoning | per-potion band | 10 s | consumes a potion per attempt |
| 33 | Stealing | item-weight band | ~10 s | needs a pack and low-weight items |
| 38 | Tracking | two checks: 0-21.1 then 21.1-100 | 10 s | works with no creature present |
| 47 | Stealth | -20..80 (armor shifts it) | 10 s success, ~20 s after a failure | needs Hiding 80 |
| 48 | Remove Trap | trap-power band | 10 s | needs Lockpicking 50 and Detect Hidden 50; one trap per box |

### Combat and magic skills (source survey)

Shared facts: every check ends in `SkillCheck.CheckSkill`; a min/max check at or above its max auto-succeeds **with no gain**, so a skill stops gaining from that check once it passes the range. No gain while dead or in a jail region. Anti-macro is off, so no per-target or per-location limits.

| ID | Skill | Check and range | Gap | Notes |
| ---: | --- | --- | --- | --- |
| 1 | Anatomy | hit path 0-cap; button on a mobile 0-100 | button 1 s; hit path = swing delay | button cannot target self; Healing also checks it |
| 5 | Parrying | chance `(Parry - 2*ShieldAR)/100`, floor 0.01 | attacker's swing delay | only on a landed hit against a shield wearer |
| 17 | Healing | min/max 0-120, on bandage completion | 3-4 s others, ~10.6 s self | needs a damaged patient; consumes a bandage |
| 26 | Magic Resist | 0-cap, only if MR is under the circle cap (35/45/55/65/75/85/120/130 for circles 1-8) | caster's cycle, 2.5-2.75 s at 6th/7th | needs a landed harmful spell; gain stops above the circle cap |
| 27 | Tactics | 0-cap on each landed hit | swing delay | trains alongside any combat |
| 31 | Archery | to-hit chance `(atk+50)/((def+50)*2)`; butte -25..25 | 1.8-7.5 s (bow 3.75 s) | butte only to 25; ammo consumed per shot |
| 40 | Swords | same to-hit chance; dummy -25..25 | 1.3-2.5 s (katana 1.29 s) | dummy to 25, lockout 3 s |
| 41 | Macing | same | 1.9-2.5 s | slower swings, slower training |
| 42 | Fencing | same | 1.41 s with a kryss | other speeds not read |
| 43 | Wrestling | same, no weapon or fists | 2.5 s | slowest melee swing |
| 25 | Magery | min/max per circle: min 0/10/.../70 for circles 1-8, max = min+40 | 1.25 s (1st) to ~3.2 s (8th) | reagents spent before the roll; EvalInt checked on every cast |
| 16 | Evaluating Intelligence | button 0-120; passive on every cast | button 1 s | cannot target self |
| 46 | Meditation | pre-roll then 0-100 | 10 s (5 s if mana full) | gains only if the pre-roll passes |
| 32 | Spirit Speak | 0-100 | 1 s | no cost |
| 39 | Veterinary | min/max, bandage code; Animal Lore secondary | 3-5 s | needs an injured animal |
| 35 | Animal Taming | window `[MinTame-0.1, MinTame+49.9]`, +6 per previous owner | 9-12 s per attempt | skill below `MinTameSkill` cannot try; creature must be calm |
| 20 | Herding | `MinTame-30` to `MinTame+30+rand(10)` | no code delay (click-limited) | tamable animals only |

Not confirmed (inferred): Herding delay, bandage consumption, Parrying base AR, other fencing speeds, `Core.ML` (non-ML Magery table assumed).

### Crafting, gathering and identification skills (source survey)

Crafts check the gain **at craft completion, before resources are consumed**, and once per skill the recipe lists. The craft's own success roll is separate. Every craft system uses a 1.25 s craft delay, so a Make Last cycle is about 1.25 s plus click latency. Gain checks are `(skill - min) / (max - min)`; at or above the recipe's max there is no gain, and a recipe whose min equals its max never gains (Kindling 0-0).

| ID | Skill | Check and range | Gap | Notes |
| ---: | --- | --- | --- | --- |
| 0 | Alchemy | per potion, e.g. -25..25 up to 90..140 | 1.25 s | reagents burn on failure, bottle returned |
| 7 | Blacksmithy | per item, e.g. dagger -0.4..49.6 up to plate 66..116 | 1.25 s | needs anvil and forge; failure costs half the ingots |
| 8 | Bowcraft/Fletching | shaft/arrow/bolt 0-40, bow 30-70, crossbow 60-100, heavy 80-120 | 1.25 s | stack recipes consume the whole stack per check |
| 11 | Carpentry | staves 0-25 up to armoire 84-109 | 1.25 s | cheapest per check in the 0-50 band |
| 12 | Cartography | maps 10-70 / 25-85 / 35-95 / 39.5-99.5 | 1.25 s (+1 s button) | cannot start below 10 |
| 13 | Cooking | essentially every recipe 0-100 | 1.25 s | needs oven or heat for baked goods |
| 23 | Inscription | one scroll per spell, circle 1 -10.8..39.2 up to circle 7 75-125 | 1.25 s | mana and spell in book required |
| 34 | Tailoring | cloth 0-25 up to studded chest 94-119; leather by item | 1.25 s | leather type gates at 65/80/99 |
| 37 | Tinkering | utensils 0-50, gears/tools 5-60, lockpick 45-95, scales 60-110 | 1.25 s | |
| 10 | Camping | 0-100 | none coded | needs kindling (from Bowcraft) |
| 18 | Fishing | 0-100 | 8 s | fish banks 5-15 per 8x8 tiles |
| 44 | Lumberjacking | 0-100 | ~2.5 s average | banks give only 2-4 successes per spot |
| 45 | Mining | 0-100 | ~0.9 s plus retarget | banks 10-34 per 8x8 tiles |
| 3 | Item Identification | target weapon/armor 0-100 | 1 s | other targets give no check |
| 4 | Arms Lore | target weapon/armor 0-100 | 1 s | |
| 36 | Taste Identification | target food 0-100 | 1 s | |

Not confirmed: Cooking gump flow, circle 8 scroll ranges, exact anti-macro line numbers (it is off). Anti-macro, if ever enabled, caps gain per 5x5 tile cell or per target, so the gain curve and anti-macro are independent: leave it off.

## Survey conclusions

1. **Cadence is not a problem for most skills.** Crafts, mining, the 1 s skills and all combat skills offer well over 560 eligible checks per hour, so the Standard 1 h first band is reachable by them.
2. **These cannot reach the Standard hours by probability alone** (10 s or longer between checks): Hiding, Stealth, Begging, Tracking, Poisoning, Stealing, Remove Trap, Discordance, Meditation (also gated by a pre-roll), Animal Taming (9-12 s per attempt), Fishing (8 s). At 360 checks per hour the floor for 0-50 is 1.4 h, at 120 per hour 4.2 h.
3. **Several skills train on a range that ends below 100**, so they stop gaining from that activity and the player must change method: Archery butte and melee dummies (25), Magic Resist (circle cap), Herding and Taming (window around the creature's `MinTameSkill`), recipe ladders. The curve controls the probability only; it cannot extend a range. Not changed here.
4. **Skills that train from hits taken or dealt** (Tactics, Parrying, Anatomy on hit, Magic Resist) get their check rate from the fight, not from the player, so a measured hour of "focused training" differs by partner. The calibration assumes the quoted swing or cast delay.

## Signed-off design (owner, 2026-10-01)

The first plan (hour targets calibrated by simulation, bigger gains for slow skills, a VeryHard schedule for Alchemy and Blacksmithy) was **replaced** by the owner's simpler stock-relative rule. The owner reviewed the survey, the class table and the cadence matrix, and approved the design below. Findings 1 and 2 above explain why the contract's Standard hour targets are no longer used.

**Rule.** The gain probability of a stock skill check is multiplied by the class multiplier for the skill's current value. Stock means unmodified ModernUO (`GainFactor` 1 for every skill).

| Class | 10 to 70 | 70 to 80 | 80 to 95 |
| --- | --- | --- | --- |
| Easy | 1.5x | 1.5x | 1.5x |
| Standard | 1.5x | 1x (stock) | 1x (stock) |
| Hard | 1.5x | 1x (stock) | 0.75x |
| VeryHard | defined (copy of Hard), no skills | | |

- **Below 10.0:** stock (every eligible check gains 0.1 to 0.4 with no roll). **95.0 and above:** the curve is not consulted; Mastery owns it.
- **Players only** (`AccessLevel.Player`). Creatures, pets and staff get stock.
- **Classes (49 UOR skills):** Easy (19): Anatomy, Animal Lore, Archery, Arms Lore, Begging, Camping, Cartography, Cooking, Detect Hidden, Evaluating Intelligence, Fishing, Forensic Evaluation, Hiding, Item Identification, Lumberjacking, Mining, Spirit Speak, Taste Identification, Tracking. Hard (4): Alchemy, Animal Taming, Blacksmithy, Poisoning. Standard (26): everything else.
- **Passive gain** (Tactics and Anatomy on hits, Evaluating Intelligence on casts, and so on) goes through the same roll, so each skill follows its own class, not the class of the skill that triggered it.
- **Owner rulings recorded:** Hard skills moved to Standard, then Animal Taming, Blacksmithy, Alchemy and Poisoning moved to Hard and Archery to Easy; Alchemy and Blacksmithy stay Hard (no VeryHard schedule); "1.5x faster" means 1.5x the gain probability per check; flag turned on for the dev host once verified.
- **Out of scope:** stat gain, gain range limits (dummy and butte at 25, Magic Resist circle caps), anti-macro (off), Mastery (Beta 2a), Skill Bank changes, resource costs of crafts.

**Changes.**
- ModernUO: `SkillEvents.GainChanceMultiplier` (null by default) applied in `SkillCheck.CheckSkill` after `GainFactor`, before the 0.01 floor and the controlled-pet doubling. Reached only on the stock roll, so Skill Bank restoration and Mastery (both `SkillGainOverride`) and the sub-10 unconditional gain never see it.
- ShardContent: `SkillGainCurveService` (registers once, chains the previous delegate, `[SkillClasses` command for players), `skillGain` section and `featureFlags.skillGainCurve` in `shard-rules.json` and `ShardRulesConfiguration` (validated: all 49 skills assigned, known classes, ascending bands, multipliers above 0 and at most 5).

**Verification matrix.**

| Case | How |
| --- | --- |
| Hook default is stock; multiplier scales the stock roll; not consulted by an override or below 10 | ModernUO unit tests (`SkillEventsTests`) |
| Class table matches the approved assignment; band edges (9.9, 10, 69.9, 70, 79.9, 80, 94.9, 95); validation rejects malformed tables; curve ends where Mastery begins | Shard unit tests (`SkillGainCurveTests`) |
| Measured gain rate ratio equals the multiplier per class and band; sub-10 unchanged; 95.0 no stock gain; staff stock; Skill Bank restore exact with the curve on and off; flag off is stock; `[SkillClasses`; real training gains | Live, disposable host (`tests/scenarios/skill-gain/gain_live.py`) |

## Estimated resource cost to reach 95 (owner request, 2026-10-01)

Model: `work/gain-model/cost.py` (scratch). Parses the stock craft definitions (UOR branches), assumes an efficient player who always crafts the cheapest recipe that still gains, total skill 350, failure burns half the resources, nothing recovered from selling the products. Real cost is higher for players who do not pick the cheapest recipe. The gain-eligible checks to 95 are about 2,000 (Easy), 2,350 (Standard) and 2,600 (Hard) under the planned curve; stock is about 2,900.

| Skill (class) | Resource | Stock | Planned curve | Alchemy/Blacksmithy as VeryHard "C" |
| --- | --- | ---: | ---: | ---: |
| Alchemy (Hard) | Nightshade / bottles / bloodmoss / mandrake | 2,900 / 2,400 / 1,200 / 860 | 3,600 / 2,100 / 770 / 730 | 16,300 / 7,200 / 2,000 / 2,100 |
| Blacksmithy (Hard) | Iron ingots | 11,500 | 11,300 | 43,200 |
| Bowcraft (Standard) | Logs | 12,800 | 10,750 | n/a |
| Carpentry (Standard) | Logs (+ barrel parts ~800) | 10,700 | 8,500 | n/a |
| Cartography (Easy) | Blank maps | 2,670 | 1,780 | n/a |
| Cooking (Easy) | Dough (plus its flour and water) | 2,350 | 1,575 | n/a |
| Inscription (Standard) | Blank scrolls / reagents | 3,090 / 6,180 | 2,460 / 4,920 | n/a |
| Tailoring (Standard) | Leather / cloth | 4,290 / 3,000 | 3,060 / 2,250 | n/a |
| Tinkering (Standard) | Iron ingots | 2,070 | 1,740 | n/a |

## Verification evidence (2026-10-01)

**Unit tests.** ModernUO `SkillEventsTests` 24/24 (3 new: default is stock, the multiplier scales the stock roll and is skipped below 10, an override that handles the attempt never reaches it). ShardContent `SkillGainCurveTests` plus config tests 62/62 (shipped config valid and equal to the approved class table, 19/26/4/0 split, band edges 9.9/10/69.9/70/79.9/80/94.9/95, malformed tables rejected, curve ends where Mastery begins). Full suite results are in the readiness record.

**Live, disposable host with the flag on** (`tests/scenarios/skill-gain/gain_live.py`, 34/34 passed, final run 15:01 local). The probe runs 6,000 real `SkillCheck.CheckSkill` calls per case on a Player-level character, once with the curve on and once with the flag switched off in memory, so the control shares the server, character and total skill. Gain rate with the curve over gain rate at stock:

| Class | Skill | Expected | Measured (curve / stock rate) |
| --- | --- | ---: | --- |
| Easy | Archery 30 | 1.5 | 1.517 (0.681 / 0.449) |
| Easy | Archery 85 | 1.5 | 1.503 (0.446 / 0.297) |
| Standard | Swords 30 | 1.5 | 1.492 (0.652 / 0.437) |
| Standard | Swords 65 | 1.5 | 1.464 (0.501 / 0.342) |
| Standard | Swords 75 | 1.0 | 0.981 (0.306 / 0.312) |
| Standard | Swords 90 | 1.0 | 0.993 (0.267 / 0.269) |
| Hard | Blacksmithy 30 | 1.5 | 1.489 (0.604 / 0.406) |
| Hard | Blacksmithy 75 | 1.0 | 0.984 (0.284 / 0.288) |
| Hard | Blacksmithy 85 | 0.75 | 0.753 (0.190 / 0.252) |
| Hard | Blacksmithy 94.9 | 0.75 | 0.722 (0.161 / 0.223) |

Pass tolerance was 12%; sampling error on these ratios is about 4%.

Other live cases: sub-10 gain is 500 of 500 checks in both modes; at 95.0 there is no stock-roll gain over 3,000 checks in either mode, for Swords and Archery (Mastery owns it); a staff character gets multiplier 1.0 and the staff flag path is stock; Skill Bank restores exactly the 20 banked tenths over 20 checks with the curve on and off and leaves a zero balance; with the flag off the multiplier is 1.0, the gain rate equals stock (0.421 vs 0.414) and `[SkillClasses` says gain is stock; `[SkillClasses` for a player lists Easy, Standard and Hard with their bands and names Animal Taming, Blacksmithy, Alchemy, Poisoning, Archery, Magery and Swords, and no VeryHard line; 120 real Spirit Speak uses through the client gained 8.3 skill points with the multiplier at 1.5.

**Test-tooling notes** (for the next scenario): the cycle script must guard `Stop-NavreySession`, `Stop-DevServer` and `Remove-DisposableHost`, which throw when there is nothing to stop; ModernUO must be rebuilt into `Distribution` (`UOContent.csproj`, Release) before the shard deploy when an engine hook changed, or the deploy build fails with missing members; the probe's "curve" mode forces the flag on, so a flag-off control needs the "asis" mode.

## Player-facing text (for owner review with the release)

- `[SkillClasses`: "Skill gain speed, compared with stock, from skill 10 up to 95:", then one line per class such as "Easy: 1.5x from 10 to 95" and "Hard: 1.5x from 10 to 70, 1x from 70 to 80, 0.75x from 80 to 95", each followed by its skills. With the flag off: "Skills gain at the stock rate on this shard."
