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

## The tree

`RULES` in `mage_bot.py`, first rule that acts wins each tick:

| Rule | Does |
| --- | --- |
| `r_dead` | A ghost walks to the healer and accepts the Resurrection gump (found by its text, answered by its server serial). |
| `r_flee` | Below 40 percent health with something close: heal, drink an unknown potion, else run to town. |
| `r_avoid` | A monster that is not safe prey: fight it from range when there is mana and health, otherwise move away from it. |
| `r_heal` | Heal below 55 percent (45 with enemies near). |
| `r_fight` | Magic Arrow at safe prey (animals, named "a ..."), keeping its distance; skips when out of reagents. |
| `r_loot` | Opens a nearby corpse once and notes whether it was empty. |
| `r_resupply` | Out of reagents (or once after three kills): to the Mage shop, tries each person with "<name> buy", buys reagents within the gold it has. |
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
