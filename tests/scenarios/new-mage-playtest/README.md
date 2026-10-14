# New-mage playtest bot

A decision-tree bot that plays a brand-new Pure Mage through Navrey so the shard can be watched as a new player meets it. Findings: `docs/New-Mage-Playtest-QoL.md`.

## Run it

1. A disposable host with a new mage still logged in as a Navrey session (Young kept, template 11 = Pure Mage):

   ```powershell
   & .\.claude\scripts\New-DisposableHost.ps1 -Name magetest
   & .\.claude\scripts\New-TestCharacter.ps1 -HostName magetest -Name MageP -Profession 11 -KeepYoung
   ```

   (If the staff session fails to start, stop it and delete `work/navrey-sessions/admin`; restart a session for the mage with its own account: `Start-NavreySession.ps1 -Name MageP -EnvFrom work\accounts\MageP.env`. Without `-EnvFrom` it logs in as the staff account.)

2. Start the bot (any number of seconds; it stops by itself):

   ```powershell
   & .\ShardContent\tests\scenarios\new-mage-playtest\run_bot.ps1 -Seconds 900
   ```

   It writes `work/mage-playtest/run.log` (what it did), `notes.jsonl` (what it found, one line each) and `knowledge.json` (places that killed it, kept between runs). The staff session `admin` is used only to resurrect a ghost that the healer could not help in four minutes, and that use is itself a note.

## What it knows

`make_game_data.py` reads the server's source and writes `game_data.json`: every creature's hit points, damage, armor and fame, and every Magery spell's circle, mana, reagents, skill window and (for the attack spells) damage. `knowledge.py` turns those numbers into decisions:

- **Which spell.** Every attack spell the mage has mana and reagents for, scored by damage per second and per gold. The check passes with chance (skill - min) / (max - min); at or above the window's top it always passes and never teaches. At Magery 50 to 60 that makes Fireball (circle 3, one Black Pearl) the best reliable attack, and Lightning (circle 4) the best teacher.
- **Which fights.** `assess(monster)` works out how many casts it takes to kill it, how long that is, and how much the monster hits for in that time; below 60 percent of the mage's health and within its mana, it is prey, otherwise a danger. An unknown monster falls back to a short list of animal names.
- **What teaches.** An easy target is a free lesson: the bot casts the highest circle that can still raise Magery (success at least 50 percent) instead of the cheapest spell. Hard fights open with Reactive Armor.
- **What it measures.** `stats.json` keeps, per spell, the casts, the damage the game showed (it replaces the formula once there are three samples: Evaluating Intelligence scales it) and every skill gain with the spell cast just before it.

## The tree

`RULES` in `mage_bot.py`, first rule that acts wins each tick:

| Rule | Does |
| --- | --- |
| `r_dead` | A ghost walks to the healer and accepts the Resurrection gump (found by its text, answered by its server serial). |
| `r_flee` | Below 40 percent health with something close: heal, drink an unknown potion, else run to town. |
| `r_avoid` | A monster the numbers say is too strong: fight it from range if cornered, otherwise move away from it. |
| `r_heal` | Heal below 55 percent (45 with enemies near). |
| `r_fight` | The best attack spell at prey (weak prey is a lesson); skips when out of reagents. |
| `r_loot` | A corpse in reach, no danger near: stands on it, opens it, takes gold, reagents, potions, scrolls and gems (retrying while the server says it must wait), leaves equipment and parts, gives up on a corpse it cannot reach. |
| `r_bank` | When rich (450 gold or more), heavy with leftovers, or too poor to shop: walks to the nearest bank, says "bank", drags junk and the gold above a 200 reserve into the box, reads the balance, and says "withdraw N" when it needs gold. |
| `r_resupply` | Out of reagents, or low on the plan (Black Pearl, ash, the heal set, mandrake): to the Mage shop, tries each person with "<name> buy", buys what the plan lacks within the gold it has, reads the sell list when broke. |
| `r_train` | Once: asks each person at the Mage shop what they will train. |
| `r_hunt` | Walks up to prey that is in view but out of range, never near a place that killed it. |
| `r_rest` | Safe but hurt or out of mana: heals and uses Meditation. |
| `r_explore` | A ring of waypoints in short hops, skipping places that killed it. |
## Adding a scenario

When a run ends in `stuck`, an `EXCEPTION` note or a death the bot could have avoided, add a rule (a method returning True when it acted), put it in `RULES` where its priority belongs, and say in the module header which run taught it. Keep rules small and give each a note (`self.notes.add(category, text, key=...)`) for anything a player would have to work out alone.

## Limits

The bot sees what Navrey sees: names, positions, the journal, gump text. It cannot judge the look of a screen (use `player-client-shots` for that), and its travel runs, so its stamina says nothing about a walking player.

## Result of the first three hours

About 26 kills, 13 deaths (all recovered through the healer, one staff rescue early on), Meditation 14 to 32, Evaluating Intelligence 35 to 42, Magery stuck at 50, gold 500 to 9. The list it produced is in docs/New-Mage-Playtest-QoL.md.

## Second bot (2026-10-14, knowledge-driven)

13 minutes: 0 deaths, 9 kills, 29 attack casts (6 Fireball, 23 Lightning), Magery 52.9 to 54.4, gold untouched. The comparison with the first bot is in docs/New-Mage-Playtest-QoL.md.
