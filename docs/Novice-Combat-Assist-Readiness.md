# Novice combat assist: readiness

**Decision:** Built, verified live and committed (ModernUO `6cc334a63`, then ShardContent on top of it) and deployed to the dev host on 2026-10-10 on the owner's "commit push deploy". **Activated 2026-10-11** on the owner's "Activate both this and furnisher": `featureFlags.noviceCombat` is true, redeployed and live on the dev host (it shipped OFF on 2026-10-10). Evidence: `Novice-Combat-Assist-Evidence.md`. Plan: `Novice-Combat-Assist-Plan.md`.

## What it does (behind the flag)

For an ordinary player (not staff, not a monster or pet), whatever weapon and whatever the target:
- **Hit chance lift.** A missed swing gets a second roll, so the hit chance becomes `raw x (1 + 0.66 x (1 - skill / 100))`, capped at 100%, where `raw` is the unchanged formula `(skill + 50) / ((defender skill + 50) x 2)`. At skill 0 that is up to 66% better than stock, fading in a straight line to nothing at 100. Against a Wrestling-60 Orc a start archer (Archery 50) goes from 45% to 59%; a Grandmaster is unchanged.
- **Tactics counts as at least 30** for the damage modifier (Tactics 0 is half damage stock; counted as 30 it is minus 20%, a 1.6 times increase). Tactics itself, and its gain, are untouched.
- **Stamina counts as at least 60** for the swing delay: a Dex 33 archer's Bow swings every 4.69 s instead of 5.64 s, a Katana swing 1.62 s instead of 1.94 s. Stamina itself is untouched.

At weapon skill 100 with Tactics 30 or more and stamina 60 or more nothing differs from stock. Monsters, pets and staff are never touched. Skill gain is unchanged, because the stock skill check runs first and only a miss gets the second roll.

Measured (real engine, a fresh archer against a Wrestling-60 Orc of 96 to 120 hit points, health topped up so she survives): two fights each gave a mean of 75 s with the assist off and 44 s on (the exact parts predict about 2.5 times the damage rate; two fights each is a small sample). The Orc's real hit points are 96 to 120, so absolute times are longer than the plan's early tables.

## Build

- **ModernUO `6cc334a63`:** `WeaponEvents` (three delegates, null by default) and three call sites in `BaseWeapon`. Inert unless a shard subscribes.
- **ShardContent:** `NoviceCombatService`, `noviceCombat` settings, flag and validator, `[NoviceCombatStatus`, tests, live tooling.

## Verification

- Full Shard suite 1159/1159 (run `20261011T021207501Z-5b5770`); UOContent `WeaponShardHookTests` 8/8.
- Live, disposable host: every case of the matrix passes (`Novice-Combat-Assist-Evidence.md`), including hit rates within sampling error of the formula for flag off and on, the top end identical, monsters never lifted, damage and swing floors, gain odds equal on and off (60.7% against 60.4%).
- The owner played it in the real client on a disposable copy of his world.
- Deployed to the dev host with the flag off: pin `6cc334a63` in all three places, the rebuilt `UOContent.dll` in `Distribution`, the shard DLL and config deployed; `[ShardRulesStatus` and `[NoviceCombatStatus` checked after the restart (see the evidence).

## Named limits

See the evidence: the Orc's real hit points (my first tables used a Lizardman's), effective skills include a stat bonus, a fresh archer still loses to an Orc, the starter Bow must be equipped, and the deployed shard DLL also carries the other session's Furnishers code (flag off).

## Owner actions

1. ~~Activate~~ done. The strength 0.66 and the two floors are in `shard-rules.json` and need no engine rebuild to change; commit the flag change when committing the Furnisher work.
2. Optional: once the flag is on, watch how a new archer and a new swordsman feel; the three numbers are the knobs.
