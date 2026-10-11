# Novice hit-chance lift: work plan for sign-off

Status: **signed off by the owner on 2026-10-10 ("Go") with his aggressive numbers; built the same day, flag `featureFlags.noviceCombat` OFF. Where sections 3 to 7 below still show the first proposal (strength 0.55, flag `noviceHitLift`, service `NoviceCombatService`, hit lift only), the as-built values in the box below win.** Origin: the owner played a new archer on 2026-10-10: arrows fire slowly and miss too much. Analysis and model: `work/combat-model/` (scratch); era check against the UO Second Age wiki is recorded in the assistant's notes and summarized in section 2.

> **As built (2026-10-10).** Flag `featureFlags.noviceCombat` (off), settings `noviceCombat { hitLiftStrength 0.66, tacticsFloor 30, staminaFloor 60 }`, service `NoviceCombatService`, staff command `[NoviceCombatStatus`. Three parts for an ordinary player (`PlayerMobile`, `AccessLevel.Player`) against every target: a missed swing gets a second roll so the hit chance becomes `raw x (1 + 0.66 x (1 - skill/100))`; Tactics counts as at least 30 for the damage modifier; stamina counts as at least 60 for the swing delay. Monsters, pets and staff are untouched; at skill 100 with Tactics 30+ and stamina 60+ nothing differs from stock. Engine side: `Server.Items.WeaponEvents` (three delegates) and three call sites in `BaseWeapon`. Estimated Orc kill for a start archer 86 s to 28 s, for a swordsman 55 s to 17 s (armor-corrected model). Skill used for the lift is the attacker's effective skill value (base plus the engine's stat bonus), so a starter's real numbers sit a little above the base-skill tables below.

## 1. Goal and exit criteria

Lift the **floor** of weapon hit chance for new characters fighting monsters, widen nothing at the top: a Grandmaster's numbers do not change at all.

Exit (checked by unit tests, a live run on a disposable host and the real client):
1. For a player attacker and a defender that is not a player or a player's pet or summon, hit chance is `raw x (1 + S x (1 - skill/100))` capped at 100%, where `raw = (skill + 50) / ((defender skill + 50) x 2)` is the unchanged pre-AOS formula and `S` is the configured strength (0.66).
2. At weapon skill 100 the result equals `raw` exactly; when the attacker is not a player the result equals `raw` exactly (monsters and pets attacking are untouched). The lift applies against every kind of defender.
3. Hit chance never falls as the attacker's skill rises, for any defender skill.
4. Archery (and every weapon skill) gain odds are unchanged by the lift.
5. The flag ships off; with it off nothing differs from today.

## 2. Current state (read from the code, verified against the era)

- Engine: `BaseWeapon.CheckHit` (pre-AOS branch) computes `chance = (atk + 50) / ((def + 50) x 2)` and returns `attacker.CheckSkill(weaponSkill, chance)`. The shard changes none of it. `ModifyHitChance` exists but is per weapon class (not reachable from shard code without touching every weapon).
- **Which skill the defender contributes:** the skill of the weapon the defender holds (`GetUsedSkill`), Wrestling when unarmed. Every monster in the tables (Mongbat 5-10, Zombie 35-50, Skeleton 45-55, Orc and Lizardman 50-70, Ettin 50-60, Daemon 60-80, Dragon 90-92, Ogre Lord 90-100, using the midpoints) holds no weapon, so it is its Wrestling value from the monster definition; each spawn rolls its own value in that range. Monster Tactics only affects their damage; Parry is a separate later check. Unaudited: a monster whose definition sets only a weapon skill and holds no weapon (the Orc Captain sets Swords 70-95 and no Wrestling) would defend with Wrestling 0 and be hit almost always.
- The UO Second Age (T2A) wiki documents the same formula (its table: 100 vs 5 = 136%, 5 vs 100 = 18%, equal skills = 50%), the same swing delay (`15000 / ((stamina + 100) x speed)`) and the same Bow numbers (9 to 41, speed 20). It is community documentation of the pre-AOS ruleset, the documented predecessor of UO:R; I found no source saying UO:R changed it, and no UO:R-specific source either. Stratics uses a +20 constant (AOS era).
- The approved combat contract keeps ordinary pre-AoS archery, defers blanket buffs and allows "narrow PvM-only archery improvements after measuring". This is that: narrow, PvM-only, fading to nothing, with the owner's play report as the first measurement.

## 3. Design

| Rule | Behaviour | Stock |
| --- | --- | --- |
| Lift | Accuracy up to 66% better than the formula at weapon skill 0, fading in a straight line to nothing at skill 100 | none |
| Who | **Revised 2026-10-10 on the owner's challenge: every target.** The lift applies whenever the attacker is a player, whatever the defender is (monster, player, pet, summon). Monsters and pets attacking are untouched. One rule keyed only on the attacker's own weapon skill: no PvM/PvP distinction, no pet or summon leak | n/a |
| Which weapons | Every weapon skill (bows, swords, maces, wrestling, ...): one formula for everyone | n/a |
| How | A second roll after a normal miss, with probability `(lifted - raw) / (1 - raw)`, so the skill check that feeds skill gain still uses `raw` and gain odds do not change | n/a |
| Strength | One number in configuration, `noviceCombat.hitLiftStrength`, validated between 0 and 2/3 (above 2/3 hit chance could fall as skill rises) | n/a |

Result (hit chance now to lifted): Archery 50 vs an Orc (60) 45% to 58%; vs a Dragon (90) 36% to 46%; Archery 0 vs a Dragon 18% to 28%, and 54% at Grandmaster either way; the lowest hit chance anywhere goes from 17% to 26%. Alone it shortens a start archer's Orc kill from about 61 s to 47 s.

## 4. Work breakdown

1. **ModernUO, one narrow hook** (the smallest that reaches `CheckHit`): a shard-owned delegate on `BaseWeapon`, called after a miss in `CheckHit`, returning whether to convert the miss; null keeps the stock path. A test in the UOContent suite. This needs the usual cycle: commit ModernUO, rebuild `UOContent` into `Distribution`, bump the pin in the three places, redeploy.
2. **ShardContent:** `NoviceCombatService` (the pure lift function and the registration, once, behind a guard), `noviceCombat` settings and validation in `ShardRulesConfiguration`, the flag `featureFlags.noviceCombat` (off), a staff status command `[NoviceCombatStatus` showing the strength and a sample table.
3. **Text:** a README line when it is activated. No guide page change (nothing a player has to learn).
4. **Tests:** the lift table, the monotone property over every defender skill, the top-end identity, the PvM-only conditions, the cap, validation; the engine hook test.

## 5. Verification

- **Unit:** as above, plus a Monte Carlo of the shard's second-roll against the closed-form chance.
- **Baseline first:** with the flag off, measure a fresh archer's real shot interval and hit rate against an Orc, standing still and while moving, to confirm the model against the live server.
- **Live, disposable host, Navrey:** a probe that makes thousands of real `CheckHit` calls at fixed skill values against a creature and against a player, comparing the measured hit rate to the formula within 4 sigma, flag on and off; Archery gain odds measured with the lift on and off must match; a Hot Zone PvP check shows no change.
- **Real client, shown to the owner:** a fresh archer fighting an Orc with the flag on and off, with the kill times and the journal.
- Snapshot: no save-format change, none needed.

## 6. Activation

The new flag `noviceCombat` is **off when deployed**. Turning it on needs the owner's explicit "activate".

## 7. Open questions (recommendation first)

1. **Which weapons?** Recommended: all weapon skills (one formula, melee novices benefit too). Alternative: archery only.
2. **Strength.** Recommended 0.55 (matches the owner's dragon example). Alternatives: 0.40 milder, 0.667 the maximum.
3. **The other two dials from the same complaint: swing speed and damage.** A new Dex 33 archer shoots every 5.6 s and does half damage because the Archer template has no Tactics. Options: (a) this item is the hit lift only, and speed and damage follow as their own items; (b) add two more engine hooks now, a stamina floor of 60 for the swing delay and a Tactics floor of 30 for the damage modifier (together with the hit lift they take the start archer's Orc kill to about 26 s), so one engine cycle covers all three. Recommended: (b) if the owner wants the speed and damage numbers decided now; otherwise (a).

### Which weapons: the role comparison (model `work/combat-model/roles.py`, 2026-10-10)

All four combat starts have the same stats (Str 54, Dex 33), weapon skill 50 and Tactics 0, so the hit chance problem is identical (45% against an Orc). They differ in swing time, which is why the early pain is not: Archer (Bow, speed 20) 5.6 s per swing; Swordsman (Katana, 58) 1.9 s; Fencer (Kryss, 53) 2.1 s; Mace Fighter (Club, 40) 2.8 s. Melee professions also start with the stock armor and a shield (archers get leather from the shard). Time to kill an Orc at the start of the game:

| | now | hit lift, all weapons | hit lift + Tactics floor for all, stamina floor for the Bow only |
| --- | --- | --- | --- |
| Archer | 62 s | 47 s | 24 s |
| Swordsman | 33 s | 25 s | 15 s |
| Fencer | 36 s | 28 s | 17 s |
| Mace Fighter | 45 s | 35 s | 21 s |

Reading: the hit lift is a formula-level fix, so one rule for every weapon skill is simpler and fair; it does not close the archer-versus-melee gap (still about 1.9x slower). The stamina floor helps every weapon by the same percentage, so it would not close that gap either; limiting it to bows (and the Tactics floor to everyone, since no combat template has Tactics) leaves archers a little slower than melee (24 s against 15 to 21 s), which is the intended ranged-versus-melee trade. Archery-only treatment of all three dials overshoots (the archer would kill faster than the swordsman, 24 s against 32 s).

### The Tactics floor and PvP (model `work/combat-model/tactics.py`, owner's question 2026-10-10)

- **Size and duration of the Tactics floor.** It is the largest single lever (damage x1.6 at Tactics 0, from -50% to -20%), but transient: Tactics gains one check per hit, about 300 hits to reach 30, roughly 17 to 31 minutes of fighting for melee and 50 to 60 minutes for an archer (who lands about 5 hits a minute), after which the floor does nothing. Start archer's Orc kill and the hit points an unarmored archer loses: now 62 s (55 hp); hit lift 47 s (42 hp); plus Tactics floor 20: 33 s (30 hp); floor 30: 29 s (26 hp); plus the bow stamina floor 24 s (22 hp). Swordsman: 33 s, 25 s, 18 s, 15 s. A Grandmaster archer needs 6 s. The start-to-Grandmaster ratio goes from about 10x to about 4x. Cost: a dead zone where training Tactics from 0 to 30 adds no damage (the skill still rises).
- **PvP (decided 2026-10-10: the lift applies to players too).** The owner's challenge was right: a novice (skill 50) at 58% against an Orc would meet 42% against a skill-70 player, 38% against 80 and 33% against 100 if the lift were PvM-only, a cliff of 16 to 25 points that stock does not have (stock: Orc 45%, then 42%, 38%, 33%, because an Orc's skill is like a player's). With the lift for everyone the same drop is 5, 9 and 15 points, the stock shape. Costs, accepted by the owner: hybrids with 50 to 80 weapon skill gain a few points on specialists (skill 70 against a skill-100 defender 40% to 47%), PvP between low-skill players gets faster, and the combat contract's "PvM-only" wording for archery improvements needs amending (PvP hit chance now lifted at low skill). PvP damage is already halved against players by the engine, so the damage contrast between monsters and players is stock either way; a Tactics floor applied to everyone keeps that contrast at the stock 2x.

### Owner's choices (2026-10-10): the most aggressive values, and a correction to the kill times

Chosen: **hit lift strength 0.66** (just under the 2/3 limit above which hit chance could fall as skill rises; the validator caps at 2/3), **Tactics counts as at least 30** and **stamina counts as at least 60** for the swing delay, all three for every weapon and every target, applied whenever the attacker is a player. Each is a configuration number, so later tuning needs no engine rebuild; the three engine hooks go in together in one cycle.

**Correction:** the earlier kill-time tables assumed an unarmored target. Monsters carry virtual armor that absorbs a flat 4 to 7 points per hit (Orc 28, Ettin 38, Ogre 32, Troll 40), which hurts low damage most, so the real "now" times are longer than quoted and the Tactics floor matters more (`work/combat-model/final.py`, armor included):

| Time to kill, start of game | Archer now | Archer aggressive | Archer Grandmaster | Swordsman now | Swordsman aggressive | Swordsman Grandmaster |
| --- | --- | --- | --- | --- | --- | --- |
| Zombie | 34 s | 11 s | 2 s | 20 s | 7 s | 1 s |
| Skeleton | 43 s | 14 s | 3 s | 25 s | 8 s | 2 s |
| Orc | 86 s | 28 s | 7 s | 55 s | 17 s | 4 s |
| Ettin | 137 s | 42 s | 10 s | 92 s | 27 s | 6 s |
| Ogre | 181 s | 58 s | 14 s | 117 s | 36 s | 9 s |
| Troll | 189 s | 58 s | 13 s | 128 s | 37 s | 8 s |

Start-to-Grandmaster on an Orc goes from about 12x to about 4x. An Ogre or Troll still out-damages a fresh unarmored archer over the 58 s it takes to kill one (about 1.4 hp/s against 77 hp), so the tier above Orcs stays out of reach until the character has trained.

## 8. Out of scope / deferred

PvP, Hot Zone balance, spellcasting accuracy, monster accuracy, the archer starting stat spread and template, skill training pace (already 1.5x), any change to the top end.

## 9. Risks and ordering (a review of this plan, 2026-10-10)

- **It fixes only part of the pain.** Hit chance is about a quarter of the early gap (the rest is swing speed and the half damage of Tactics 0). A start archer (77 hp) loses roughly 0.9 hp/s to an Orc, so a 47 s kill costs about 42 hp and a 26 s kill about 23 hp: survivable either way with bandages, but a two-Orc pull is still dangerous on the hit lift alone. Hence question 3.
- **Leak in "PvM only".** "Defender is not a player" would include another player's pets, summons and familiars (the stock damage halving has the same gap). Closed above: player-controlled and summoned creatures count as the player's side.
- **Side effects of more hits.** Every hit runs the passive Tactics and Anatomy gain checks (`ScaleDamageOld`) and wears the weapon, so those skills will train somewhat faster while the lift is large (about the same percentage as the extra hits, fading to none). Probably welcome (Tactics is the damage fix), but it is a training-pace change the owner should know about.
- **Tilts the early game toward weapon users.** Mages, tamers, thieves and crafters get nothing, against the design constraint that every playstyle has a working start. Not part of this item; worth a look at the mage and tamer starts next.
- **We reasoned from formulas, not from what the owner saw.** The actual shot interval, stamina while kiting and the stationary delay stacking (up to about 1 s after any step) are not yet measured. The combat contract says audit and measure first. Add a baseline probe to the live pass (real shot interval and hit rate for a fresh archer, flag off) before judging the numbers.
- **A hidden mechanic.** An unannounced accuracy bonus puzzles players who compare with other UO:R shards. Document it in the README (and consider one guide line). Whether a classic shard should smooth its early game at all is the owner's call; the ceiling and PvP are unchanged.
- **Engine merge surface.** One more hook in `BaseWeapon.CheckHit`; keep it to a single delegate call so upstream merges stay easy. Tests need an injectable random source.
- **Prove, do not assume, that skill-gain odds are unchanged** (the live pass measures Archery gain with the lift on and off).

- The hook runs on every swing, but only after a miss and only a delegate call: negligible cost. It is null unless the shard fills it.
- The lift only helps while skill is low, so it cannot raise the ceiling or change PvP; the monotone property was tested for every defender skill 0 to 200.
- Build order: the pure function and its tests, the engine hook and its test, the service and flag, the probe, the live pass, the real-client pass, the evidence and readiness records.
