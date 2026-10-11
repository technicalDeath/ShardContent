# Novice combat assist: evidence

Plan: `Novice-Combat-Assist-Plan.md`. Readiness: `Novice-Combat-Assist-Readiness.md`. Built, verified and deployed (flag OFF) on 2026-10-10.

## Decisions

- **Owner, 2026-10-10:** design approved ("This looks great"), then the most aggressive numbers, then "Go". Later the same day: "go, build it, commit push deploy". Deploy does not activate; the flag changes only on his explicit "activate".
- **Hit lift strength 0.66** (the validator caps it at 2/3: above that, hit chance could fall as skill rises), **Tactics counts as at least 30** for the damage modifier, **stamina counts as at least 60** for the swing delay. All weapon skills, all targets (monster or player), whenever the attacker is an ordinary player (`PlayerMobile` with `AccessLevel.Player`). Monsters, pets and staff are never touched. At weapon skill 100 with Tactics 30+ and stamina 60+ nothing differs from stock.
- The lift is a **second roll after a stock miss**, so the stock skill check, and with it skill-gain odds, is unchanged.
- Flag `featureFlags.noviceCombat` (off), settings `noviceCombat { hitLiftStrength, tacticsFloor, staminaFloor }` in `shard-rules.json`, service `NoviceCombatService`, staff command `[NoviceCombatStatus`.

## Build

- **ModernUO `6cc334a63`:** `Server.Items.WeaponEvents` (three delegates, null by default) and three call sites in `BaseWeapon` (second roll in `CheckHit`, Tactics in `ScaleDamageOld`, stamina in the pre-AOS `GetDelay`). Engine tests `WeaponShardHookTests` (8).
- **ShardContent:** `NoviceCombatService.cs`, `NoviceCombatRules`, validation and flag in `ShardRulesConfiguration.cs`, registration in `ShardBootstrap.cs`, `tests/NoviceCombatTests.cs`, live tooling in `tests/scenarios/novice-combat/` (`NoviceCombatProbe`, `combat_live.py`).
- Pin bumped to `6cc334a63` in `shard-rules.json`, `world-generation.json` and `Alpha2bWorldGenerationConfigurationTests.cs`.

## Verification

- **Unit:** the full Shard suite 1159/1159 (run `20261011T021207501Z-5b5770`, after the pin bump); UOContent `WeaponShardHookTests` 8/8. Covered: the lift table, the top end exactly stock at skill 100 and above, hit chance never falling as skill rises for any defender up to 200 while strength is within the limit (and falling at 0.9, which is why the validator stops at 2/3), the two-roll process giving the lifted chance with unchanged first-roll odds (Monte Carlo, 400,000 trials), who the assist applies to, the floors, validation, the shipped configuration.
- **Live, disposable host `novice-combat`** (real engine formulas through `NoviceCombatProbe`; the flag switched in memory per call; expected values use the engine's effective skills, see the second limit below). Run 2 (`work/novice-combat/run2.log`), 32 cases, every hit-rate, delay, damage (except M2, see below) and not-for case passing:
  - Baseline, flag off: a fresh archer's Bow swing is 5.639 s at stamina 33 (stock formula); hit rate against an Orc equals the stock chance.
  - Swing delay, flag on: Bow 5.639 s to 4.688 s at stamina 33 and 6.818 s to 4.688 s at stamina 10; Katana 1.945 s to 1.616 s and 2.351 s to 1.616 s; Dex 100 (stamina 100) 3.75 s either way; a monster's swing unchanged.
  - Damage modifier on 100: Tactics 0 gives 55 stock and 88 with the assist; 20 gives 77 and 88; 30, 40 and 100 are identical (88, 99, 166).
  - Hit rate (20,000 real `CheckHit` calls each, stock expectation in brackets): Archery 0 vs a monster at 60: 23.8% off (23.6), 38.4% on (38.6); 20: 31.7% / 48.0%; 50: 44.7% / 59.0% (58.9); 70: 52.5% / 63.5%; 90: 62.0% / 65.9%; 100: 65.3% / 66.0% (65.7 both). Against a monster at 91: 0: 19.0% / 31.0%; 50: 35.8% / 46.9%; 100: 52.8% / 52.8%. Against a player (weapon skill 55): Archery 50: 49.1% / 63.7%; 70: 57.8% / 69.4%. A Swordsman's Katana at 50: 44.4% / 58.9%. Grandmaster Archery against a 91: 52.7% off, 53.2% on (the same within sampling error).
  - A monster attacking a player is never lifted: Wrestling 0: 29.3% / 29.9%; 50: 50.9% / 51.4%.
- **Timed fights** (`fights` stage; a fresh archer with a Bow against a Wrestling-60 Orc spawned three tiles away; the archer topped up to full health every 8 s because a fresh unarmored archer loses to an Orc in under a minute): see the table below.
- **Owner's own playtest, real ClassicUO client** (2026-10-10, about 21:58 to 22:02, a new archer on a disposable copy of his world with the assist on). No new text or window exists, so there is nothing to photograph.

### Timed fights

A fresh archer (Archery 50, Dex 33, 78 hit points, no armor) with a Bow and plenty of arrows, against a Wrestling-60 Orc (96 to 120 hit points) spawned three tiles away. Kill time is the first attack to the last swing, read from the client's log (`work/novice-combat/fights_table.py`); the swing counts match the intervals exactly (5.60 s per shot off, 4.69 s on).

| assist | shots | seconds |
| --- | --- | --- |
| off | 12 | 62 |
| off | 17 | 89 |
| on | 11 | 47 |
| on | 10 | 42 |

Mean 75 s off, 44 s on, 1.7 times faster. Two fights each is too few to separate from chance, so read it as indicative only; the exact parts say what to expect: per shot the assist gives 1.32 times the hit rate (59.0% against 44.7%) and 1.6 times the damage before armor (90 against 56 on a base of 100), shots come 1.19 times as often, so the damage rate is about 2.5 times stock before the Orc's armor, which takes a flat share off every hit and hurts the smaller stock hits more.

Earlier runs of the same stage (`run3`, `run7`) timed the kill by watching for the dead Orc in the client's world file, which can keep it for up to a minute; those times (175 s off against 43 s on, 111 s against 106 s, 97 s against 109 s) overstate the kill by that lag and are not used. Three attempts at more fights were lost to harness faults and not repeated for time: the archer ran out of arrows (a shot costs one and a fresh archer carries about 75), then died and lost her Bow. The driver now tops up arrows, times from the swing log and ends a fight when the archer stops shooting.

## Named limits

- **The Orc's 96-120 hit points.** My earlier kill-time tables (86 s, 28 s) used 58-72 hit points for an Orc, which is a Lizardman's range. The engine's Orc has 96-120, so absolute kill times are about 1.6 times those tables; the ratio is what the assist changes.
- **Effective skills.** The engine rolls with `Skill.Value`, the base plus a stat bonus (about 3 to 6 points at low skill, 0 at 100; monsters get it too: an Orc with Wrestling 60 reads 63.9). Real starter numbers therefore sit a few points above the base-skill tables in the plan (a Dex 33 archer at Archery 50 reads 51.9 and hits a 60-skill Orc 44.7% stock, not 43.8%). The lift fades with the effective value, which keeps it monotone.
- **Gain odds are proved structurally**, not only live. The first live attempts could not measure them: Archery is under the stock anti-macro limiter (repeat gains at one spot are refused after a few, so 40,000 calls from one place gain nothing), and a dead character gains nothing. The engine test shows the lift is consulted only after the stock `CheckSkill` has run and returned false, and the live gain case (24,281 gains in 40,000 calls with the assist off, 24,151 on: 60.7% against 60.4%, inside the 1.6-point 4.5-sigma limit) repeats the check with an unarmed character, whose Wrestling is not limited.
- **A fresh archer still loses to an Orc.** A start archer without armor has 78 hit points and dies in under a minute against an Orc; the assist cuts the time to kill from about three minutes to about one, it does not make a new archer safe.
- **Starter Bow.** A new character carries the Bow in the backpack and must equip it.
- **Test tooling lessons.** A fresh archer holds fists; the disposable host copy needs `Configuration/furnishers.json` (copy it from `ShardContent/data/configuration/`); the probe's throwaway Orcs now delete themselves (the first live run leaked some, which attacked idle test characters); never rebuild probe or shard DLLs into a running host.

## Not done / needs the owner

- **Activation.** The flag ships OFF. Saying "activate" turns it on in `shard-rules.json` (a README rules line is added then).
- The deployed shard DLL also contains the uncommitted Furnishers code from another session (its flag is OFF, and with the flag off its startup check only removes a vendor and hall that do not exist in the dev world).
