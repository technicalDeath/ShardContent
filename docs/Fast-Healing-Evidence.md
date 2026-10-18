# Fast Healing and Meditation to 40, and the Meditate button

Flag: `featureFlags.fastHealing`. It is **off** and held for the owner's batch test. Nothing is committed or deployed.

## Why

Item 12 on the bot-farm QoL list: bandages barely help without the Healing skill.

Under stock pre-AOS rules (`Bandage.cs`):
- A bandage works with a chance of (Healing + 10) / 100.
- At 0 Healing it fails 9 times in 10 and heals nothing.

The owner (2026-10-17): "Have healing skill gain go very fast until 40 skill to help make it effective faster."

He then set the numbers: "Below 20 it gains 5.0 to 10.0, and below 40 1.0 to 5.0" (whole points).

## Today, without the flag

Simulated with the real formulas: stock skill checks, plus the shard's ×1.5 "standard" curve below 70.

| | |
| --- | --- |
| Bandages from 0 to 40 | about 460 |
| Time spent bandaging yourself (14.5 s each) | about 1 h 50 min, while hurt |
| Time spent bandaging a hurt friend (4 s each) | about 31 min |
| Cost of the bandages | about 2,300 gold |

Britain's Healer Guildmaster also teaches Healing to about 30, at stock prices.

## What it does

- **When it applies:** every Healing check that would roll for a gain, which means a bandage finished on a patient who needs it.
- **What it gives:** a sure gain instead of the roll:
  - 5.0–10.0 below 20;
  - 1.0–5.0 from 20 to 40.
- **From 40 up:** stock gain and the shard's curve apply unchanged.
- **Who it applies to:** every player alike.
- **Configuration:** the bands are in `shard-rules.json` under `fastHealing.bands`, in tenths, so they can be tuned without code.
- **Code:** `FastSkillStart.TryGain`. It runs inside the shard's single gain-override handler (`MasteryProgression.HandleSkillGain`), after Skill Bank restoration. It respects:
  - the skill cap;
  - the total cap;
  - skills set to go down, which give way as in stock;
  - the Skill Bank, which keeps a displaced point.
- **Estimate:** about 9 bandages from 0 to 40 (6 to 14 in a simulation).

## Verification

| Case | Setup | Observation | Result |
| --- | --- | --- | --- |
| Unit tests (`FastHealingGainTests`, 8) | n/a | <ul><li>The bands match the owner's numbers.</li><li>No band applies from 40.</li><li>The config validates, and backwards amounts are refused.</li><li>The flag is off by default.</li></ul> | Pass; run `20261017T202903906Z-f229e2` (shard 1,651) |
| Bandaging a hurt patient from 0 | Disposable host `batch`, flag on there only; Healing and Anatomy set to 0; patient set to 5 hits before each bandage. Driver: `work/batch-test/s10_heal.py` | Base Healing after each bandage: 5.9, 11.5, 19.9, 26.8, 31.4, 33.8, 35.8, 37.3, 39.4, 43.7. The gain message comes whether or not the bandage worked. | Pass: **10 bandages** from 0 to 43.7 |
| Real client | The same, three bandages | "Your skill in Healing has increased by 7.6. It is now 32.0" (the shown value includes the stat bonus). The shard's own hint follows a failed bandage. | Pass (`images/fast-healing/bandage-gain.png`) |

## Notes

- A gain can carry a little past a band edge, and the last one past 40: 39.4 went to 43.7 in the run.
- Only a bandage on a patient who needs healing counts. A full-health patient gets "not damaged" and no check.
- A dead patient is a resurrection attempt, which needs Healing 80, so it doesn't count either.
- **Deploy:** shard code only (no engine change), through the usual Deploy-Alpha1Baseline.

## Meditation (item 13), 2026-10-17

**The owner's choices:**
- "Faster Meditation start" with Healing's bands from any Meditation check;
- a "Meditation pointer";
- "a meditate button on the spell hotbar so the meditation skill is discoverable, with a tooltip that says what it does".

**Why:**
- A new caster has Int 25 (25 mana) and 0 Meditation (Sorcerer, Pure Mage and Warlock alike).
- Pre-AOS mana returns one point every 5.8 s at that level, about 2.5 minutes from empty to full.
- Nothing mentions Meditation.

**What was built:**

- **`fastMeditation`** (off): the same `FastSkillStart` code and bands as Healing, in `fastMeditation.bands`.
  - Below 20 each Meditation check gains 5.0–10.0; below 40, 1.0–5.0.
  - Checks come passively as mana refills and from active meditation.
- **`meditationTip`** (off): when a cast is refused for want of mana and the caster is not meditating, one line is sent, at most every ten minutes for a character:
  > "Out of mana? Press Meditate on the spell bar (or use Meditation from your skills) with your hands free and keep still: your mana comes back twice as fast, and the Meditation skill rises as it does."
  - It hangs on a new engine event, `Spell.InsufficientMana`, raised at the three "Insufficient mana" lines.
- **Meditate button** (client, no flag): it sits on the spell hotbar after the spells and uses skill 46. Its tooltip:
  > "Meditate: rest, and your mana comes back twice as fast. Your hands must be free (no weapon or shield) and you must keep still: moving, casting or fighting ends it. It can fail at low skill. The Meditation skill rises as your mana comes back."

  These are the stock pre-AOS rules from `Meditation.cs` and `RegenRates.cs`.

**Checks:**

| Case | Observation | Result |
| --- | --- | --- |
| Unit tests (`FastSkillStartTests`) | <ul><li>Bands as for Healing.</li><li>The tip waits ten minutes, including across a tick-count wrap.</li><li>Both flags are off by default.</li></ul> | Pass; run `20261017T210349829Z-865a84` (shard 1,656; UOContent 1,404); after the tip wording change, run `20261017T210822742Z-56f5a3` |
| Navrey (`work/batch-test/s11_med.py`): Meditation 0, mana 0 | Meditation 8.8, 24.5, 34.9, 42.8 at 8, 17, 27, 36 s, then the stock rate (43.4 at 92 s) | Pass |
| Navrey: two casts with no mana | Tip on the first, none on the second | Pass |
| Real client: the hotbar | The Meditate button and its tooltip | Pass (`images/fast-healing/meditate-button.png`) |
| Real client: casting with no mana, then Meditate with sword and shield held | <ul><li>"Insufficient mana" overhead.</li><li>The tip.</li><li>Meditation +9.8.</li><li>The stock "Your hands must be free" line.</li></ul> | Pass (`images/fast-healing/meditation-tip-and-gain.png`; the live tip was the wording before "with your hands free" was added) |

**Deploy:**
- `UOContent.csproj` rebuilt into Distribution, for the engine event;
- a ModernUO commit and a pin bump;
- the usual deploy;
- the client `cuo.dll` into `ClassicUO/bin/dist`.
