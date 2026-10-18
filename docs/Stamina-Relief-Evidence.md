# Stamina relief

**Flag:** `featureFlags.staminaRelief`, built 2026-10-16. **Off**: not activated, not deployed, not committed. Live testing is held for the owner's batch test.

## The owner's rulings (2026-10-16)

- "I dont want to make new player only fixes."
- "The stamina lost at low health when taking hits seems like the most obvious problem. Let's tune that down so that you lose at most 3 stamina per hit."
- "Also fix the message."

## Stock behaviour, from the code

- **Hit fatigue** (`StaminaSystem.FatigueOnDamage`, pre-AOS Standard): damage × (100 ÷ hit points before the hit) × (stamina ÷ 100) − 5.
  - At 30 stamina, a 12-point hit costs 1 at 60 hit points, 7 at 30 and 19 at 15.
  - A hurt character therefore loses most of what is left in two or three hits, just when it needs to run.
  - Players (`PlayerMobile.OnDamage`) and creatures (`BaseCreature.OnDamage`) both pay it.
- **At 0 stamina** a run attempt is refused (`stamina.cannotRunWhenFatigued`, pre-AOS). The message is "You are too fatigued to move." (cliloc 500110), though walking still works.

## What changes

- **Engine hooks** (ModernUO `UOContent/Misc/StaminaSystem.cs`), both null by default:
  - `DamageFatigueFilter(mobile, stockLoss) → loss`;
  - `TooTiredToRunNotice(mobile) → handled`.
- **Shard** (`StaminaReliefService`):
  - A player loses at most `staminaRelief.maxLossPerHit` (3) per hit. Creatures keep the stock drain.
  - A refused run says "You are too tired to run, but you can still walk. Your stamina comes back as you go." The client retries a blocked run on every step, so the line is sent at most once every 5 seconds.
  - It applies to every player.
- **Unchanged:**
  - running costs 1 point per 16 steps;
  - below 10%, each running step costs 1 more;
  - no running at 0;
  - stamina comes back 1 point every 7 seconds;
  - shoving needs full stamina and costs 10;
  - weight fatigue.
  - The mace and staff drain of 3–5 per hit (`BaseBashing`, `BaseStaff`) is a weapon trait, separate from the hit fatigue, and stays. The bot farm watcher found that no stock creature wields a mace or staff, apart from wandering healers, the harbormaster and the mage guildmaster, so in PvE the cap applies in full. In PvP a mace hit can still cost up to 3 + 5.

## Checks

- `StaminaReliefTests`, 11 cases:
  - the stock formula at the four example hits, and the capped results;
  - creatures and the flag off keep the stock loss;
  - the message text and its 5-second throttle;
  - the flag defaults to off;
  - the config validates, and caps outside 0–30 are refused.
- Full suites: shard 1,576 passed; UOContent 1,404 passed, 2 skipped (runs `20261016T194824934Z-d1cc99` and `20261016T195021194Z-b3ed87`).
- **Not yet checked live:**
  - a hurt character's stamina after several hits;
  - the new line in the real client;
  - the bot farm's before/after read. The watcher's `work/botfarm-watch/stamina.py` holds the baseline: 0.25 fighter deaths per bot-hour, and 27% of flights ending in death. It waits for the Operator to deploy to the farm host.
