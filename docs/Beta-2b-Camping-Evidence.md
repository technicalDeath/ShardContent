# Beta 2b item 3: Rekindled camping, evidence

Status: **signed off 2026-10-05, built, unit- and live-tested (flags on and off), committed, pushed and deployed. Both flags acknowledged and switched on 2026-10-06.** Readiness record: [Beta-2b-Camping-Readiness.md](Beta-2b-Camping-Readiness.md). Design source: [Rekindled-Camping-Design.md](Rekindled-Camping-Design.md). Code: `ModernUO/Projects/UOContent/Items/Skill Items/Camping/{Campfire,Kindling}.cs` (two narrow hooks) and `ShardContent/src/BritanniaRenaissance.Content/CampingService.cs`.

## Owner rulings (2026-10-05)

| Question | Ruling |
| --- | --- |
| Who can light a fire | **Everyone, at a 50% chance floor.** Real Camping skill and its display are unchanged; skill above 50 raises the chance. No cap, client or template change. (Not "free Camping 50 outside the cap".) |
| Starter kit | **Every new character** gets a Bedroll and Kindling, newbied, loose in the pack, not bound (the Bedroll must be dropped on the ground to be used, which a bound item cannot be). |
| Signal fire | **Dropped for now** (no party message, no map marker). |
| Power and PvP ideas (thief protection, night watch, regen perks, firelight wariness) | No preference; recommendation applied: **all left out**. |
| Flavor ideas (colored flames, cold ashes, ask the embers, harmless visitors) | None chosen; **core only**. May return as a later slice. |
| Persistent fuelable fire, camp stall, housing hearth, carry the flame | **After house zoning** (the torch after Pilgrimage, Beta 2c); deferred, not rejected. |
| Camp travel (party members travel to a secure campfire; the owner's idea) | **Its own item later in Beta 2b**, with guardrails (accepted by the traveler, party only, lit and secure fire, neither end in a dungeon or Hot Zone, no criminals/murderers/Knocked Out/combat, long cooldown, Kindling cost, no cargo, reuse the stock Recall/Gate checks). Not built here. |
| **Burn-time scaling** (owner, decided after the build) | **Real Camping skill**, not max(skill, 50): the 50% floor applies to lighting only, so every point of Camping from zero lengthens a fire. Replaces the signed-off max(skill, 50). |
| **Feeding the fire** (owner, added mid-build) | Kindling used **within 1 tile of a campfire resets its duration.** Built as the rekindle rule: works on a burning, dim or ember fire. |

## What it does

Behind `featureFlags.campingStarterKit` and `featureFlags.campingFires`, both **off** in source until acknowledged. With a flag off the stock behavior returns exactly.

- **Kit:** a Bedroll if the character has none, and Kindling up to 5 in total (stock Camping gives a Bedroll and 5; stock Cooking gives 2; those are topped up, not doubled). The default was briefly 3 (2026-10-05) because five Kindling (25 stones) put a weight-check test start over its limit; that start was stock profession 1, an alchemy-heavy forged-packet character, not a Warrior (the real Warrior templates carry about 95 stones of 229), and the weight budget now trims bulk supplies to make room for the kit, so the approved 5 was restored on 2026-10-06.
- **Lighting:** chance = max(Camping, 50) percent, so everyone can light a fire. Skill gains follow the normal roll.
- **Burn time** (real Camping skill, 0 to 100): lit for 100 s + 2 s per point (100 s at 0, 200 s at 50, 300 s at 100), the last third dim; then embers for 60 s + 1.2 s per point (60 to 180 s). Stock is 90 s lit and 10 s of embers. Embers are the stock "Off" fire graphic; they are not a secure camp. The 50% floor does not apply here, so a new character's fire is close to stock's and training Camping pays off from the first point.
- **Feeding:** Kindling used within 1 tile of a campfire (instead of lighting a new one) restarts its burn from now for the feeder's timing, never shortening a longer one the fire already has; embers light again, no roll. One Kindling per feed. A fire lit or fed in the last 5 s is not fed again (no Kindling used). To light a second fire, stand 2 tiles away.
- **Unchanged (stock):** the 30 s secure camp, Bedroll logout, dungeon refusal, fires not saved across restarts, NPC camp fires.
- **Diagnostics:** staff `[CampStatus` (flags, numbers, campfires within 40 tiles with state, lighter, age and timing).

Two readings of the signed-off numbers, recorded so they are not reopened: the plan text said phases "keep the stock proportions" and embers last 60 s + 1.2 s per point; implemented as lit period (two thirds burning, one third dim) followed by the ember period. All numbers are in the `camping` section of `shard-rules.json`.

## Player-facing text (for the owner's release review)

- "You feed the fire."
- "The embers flare back to life."
- "The fire has only just been tended."
- Stock messages unchanged: "You fail to ignite the campfire.", "There is not a spot nearby to place your campfire.", "The camp is now secure."

## Acceptance matrix

Live runs used disposable hosts built from a copy of the deployed distribution with the hooked `UOContent.dll` and the shard DLL overlaid and the source `shard-rules.json` (flags on, timings scaled down so a fire's whole life is about a minute: `litBaseSeconds` 20, `litPerSkillSeconds` 0.3, `emberBaseSeconds` 15, `emberPerSkillSeconds` 0.2). Driver `tests/scenarios/camping/camping_live.py` (stages `kit`, `fires`, `off`). Fires are read with the new `[CampStatus` because the test client cannot see immovable items. The dev distribution and dev saves were not touched; hosts, accounts and sessions were removed.

| ID | Case | How | Result |
| --- | --- | --- | --- |
| U1 | Ignition chance floor and slope | unit (`CampingServiceTests`) | pass |
| U2 | Burn and ember timing at skill 0, 50, 100; strictly longer with every point of skill from 0; skill clamped to 0 to 100 | unit | pass |
| U3 | Kit top-up (none, cook, camper, both) | unit | pass |
| U4 | Config defaults, ranges, shipped file, flags listed | unit | pass |
| U5 | Campfire phases at stock ages, longer timing, feed keeps the longer timing and relights embers | unit (`UorCampfireTests`, UOContent) | pass |
| L1 | Kit for the profession-1 test start (`KitWar`, not a real Warrior), Pure Mage, Blacksmith, a cook and a camper: one Bedroll, 5 Kindling in all (nobody doubled), newbied, not bound, nothing doubled | live, flags on | pass (5 characters, server-side `TestOnlyInventoryInspect`) |
| L2 | The kit does not push a character over its weight limit | live | pass: profession-1 test start (`KitWar`) 183/187, Mage 120/208, Blacksmith 121/229, camper 76/187. The Cook-and-Alchemist test character is 238/187 before the kit (existing starter materials) and was not asserted. |
| L3 | Camping at base 0 lights some fires and fails others | live | pass (1 lit, 1 failed in 2; earlier runs similar) |
| L4 | Fire timeline at Camping 100 (dim 33 s, embers 50 s, gone 85 s), and for a base-0 camper (Camping 20.5 with the stat bonus) the formula's numbers (dim 17 s, embers 26 s, gone 45 s), shorter than the 60 s a skill-50 fire would have had: every observed (age, state) matches, embers seen, gone on time (the 1 s fire timer can leave a fire one second past its end) | live | pass (both) |
| L5 | Feeding a burning fire resets its duration, uses one Kindling, lights no second fire | live | pass |
| L6 | Feeding a dim fire returns it to burning; Kindling on embers relights it, "The embers flare back to life." | live | pass |
| L7 | A fire lit or fed in the last 5 s refuses a feed: "The fire has only just been tended.", no Kindling used, no second fire | live | pass |
| L8 | A weaker feeder (effective 50) resets the burn but the Grandmaster's longer timing is kept | live | pass |
| L9 | "The camp is now secure." arrives at about 30 s (29.2 s); embers are not a secure camp (no logout gump) | live | pass |
| L10 | The Bedroll offers the safe-logout gump at a secure camp and CONTINUE logs the character out | live | pass |
| O1 | Flags off: the profession-1 test start (`OffWar`) gets no kit; a camper-cook has exactly stock's Bedroll and 5 + 2 Kindling; stock timing (60, 90, 100 s); Kindling beside a fire lights a new fire instead of feeding it | live, flags-off host | pass |
| O2 | No save-format change; fires still vanish on restart | by construction (fires are not serialized); no restart test | n/a |

Suites: full Shard suite 541 pass (this item adds the camping tests); full UOContent suite 1358 pass, 2 skipped (this item adds 12 `UorCampfireTests`; no ModernUO change since that run).

The burn-time tweak (real Camping skill, ruled after the first full pass) was verified by rerunning the `kit` and `fires` stages on a fresh host with the final DLL, plus the unit tests; the flags-off baseline (O1) is unaffected by it, since the tweak is behind `campingFires`, and was not rerun. Across all live passes the `fires` stage needed driver fixes, never game fixes: timeline checks that timed from when polling began, a "stand beside the fire" step that stopped a tile short, a feeding stage placed after a stage that moved the tester, zero-skill attempts made beside a live fire (where Kindling correctly feeds it), and a one-second timer tolerance.

**Re-run 2026-10-06 (Kindling restored to 5, starter weight budget in):** the `kit` stage was rerun on a fresh host with seven real starts (Mace Fighter, Pure Mage, Blacksmith, an Advanced cook, an Advanced camper, Archer, Carpenter): all have exactly one Bedroll and 5 Kindling in total (nobody doubled), newbied and not bound, and none is overloaded (118/229, 120/208, 132/229, 158/187, 77/187, 194/229, 194/229).

## Findings

- **Kit weight.** Kindling and the Bedroll weigh 5 stones each. The default was briefly 3 because five Kindling (25 stones) put the profession-1 test start over its limit; that start was an alchemy-heavy forged-packet character, not a Warrior, so the approved 5 was restored on 2026-10-06 (the starter weight budget now trims bulk supplies to make room).
- **Existing overweight starter.** An Alchemy and Cooking character starts at about 228 of 187 stones with no camping kit at all (starter reagents, bottles, raw meat top-ups). Not caused by this item; reported for the owner.
- **Effective skill.** A character's skill value includes a stat bonus (base 0 reads about 19 to 20), so below-floor ignition never reads as 0 in practice.
