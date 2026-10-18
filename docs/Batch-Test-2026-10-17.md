# Batch live test, 2026-10-17

The owner's request: "Resume testing of the new features and changes so far."

This covers the flags built 2026-10-16/17, all **on** in a disposable host's own config: `townGuardsKillMonsters`, `staminaRelief`, `staminaNumbers`, `ghostHealerReminder`, `corpseTimerNotice`, `longerPlayerCorpses`, `corpseCompass`, `blueSelfLoot`, `killerGoesHome`, `materializing`.

In source config every one of these flags stays **off**. Nothing was deployed to dev, committed or pushed.

**Host:** `work/hosts/batch`, a copy of the dev distribution.
- `UOContent.dll` and the shard DLL were built from today's source by the verification runner; `Server.dll` is byte-identical.
- The source `shard-rules.json` was used, with the ten flags on.
- The moved `britain-beginner-hunting.json` was copied in.

**Characters:** fresh, not Young:
- three Swordsmen (Gtest, Stest, Dtest);
- one Pure Mage (Mtest), used where armour would hide damage.

**Drivers:** `work/batch-test/*.py`, with the shared helpers in `rig.py`.

**Real-client shots:** a copy of the player client with the new `cuo.dll`, `work/player-client-dist-batch`. `ClassicUO/bin/dist` was not touched.

The bot farm runs after this. Its stamina and death-recovery before/after reads are with the BotFarm Watcher.

## Results

| Case | Driver | Observation | Result |
| --- | --- | --- | --- |
| G1 `[TownGuardStatus` in Britain, Britain Outskirts and Moonglow Zoo | `t1_guards.py` | "Here (Britain): guarded"; "Here (Britain Outskirts): not guarded"; "Here (Moonglow Zoo): not guarded"; both areas registered | PASS |
| G2 A troll Gtest struck first: no guard unasked | `t1_guards.py` | It fought Gtest for 12 s and no guard came | PASS |
| G3 The same troll, on Gtest's "guards" | `t1_guards.py` | Guard Catriona: "Thou wilt regret thine actions, swine!"; the troll died within a second | PASS |
| G4 A cat beside the troll | `t1_guards.py` | Still alive after the call | PASS |
| S1 Hit stamina cap: Mtest (no armour) held at 8-12 health, full stamina, beside an ettin | `t2c_cap.py` | 11 hits of 1-9 damage, where the stock rule costs up to about 19 a hit. Every stamina drop was 3 or less (3, 2, 3, 3, 3, 3, 3), 33 to 17 | PASS |
| S2 Too-tired line when running runs out | `t2b_stamina.py` | "You are too tired to run, but you can still walk. Your stamina comes back as you go." | PASS (after a fix, below) |
| N1 Stamina-lost number (real client) | `s1_numbers.py` | A blue "-3 stam" under the yellow damage number over Mtest | PASS, `images/batch-test-2026-10-17/stamina-lost-numbers.png` |
| N2 Refresh-potion number (real client) | potion bar click | A blue "+8 stam" (a quarter of 33) | PASS, `stamina-refresh-number.png` |
| N3 The two Options switches (real client) | Options > Combat-Spells | "Show stamina lost to hits over your head" and "Show stamina from refresh potions over your head", ticked by default | PASS, `options-two-switches.png` |
| N4 "Show stamina lost" unticked (real client) | `s2_off.py` | Damage numbers still show and no "stam" text appears, while the server shows Mtest's stamina falling 33 to 20 | PASS, `stamina-lost-switched-off.png` |
| D1 Corpse timer at death | `t3_death.py` | "Your corpse will turn to bones in 10 minutes, and the bones and everything in them will be gone 7 minutes after that." (also in the real client's journal) | PASS, `journal-corpse-timer.png` |
| D2 War-mode reminder, ghost in peace mode beside the Britain healer | `t3_death.py` | The reminder arrived; none after war mode was on | PASS |
| D3 War mode, step back, walk up | `t3_death.py` | The Resurrection gump (CONTINUE / CANCEL) | PASS |
| D4 Materializing starts on resurrection (healer, and staff `[Resurrect`) | `t3b`, `t4` | The start line; a stealth buff icon counting down from 10:00 (real client) | PASS, `materializing-start-and-buff.png` |
| D5 A potion while materializing | `t3b`, real client | "That will end your materializing, and monsters will see you. Do it again within a few seconds to go ahead." The potion was not drunk | PASS, `materializing-warning-pale-hue.png` |
| D6 Speech, guide windows and gump buttons while materializing | real client | `[Welcome` and its tabs did not end it | PASS |
| D7 Blue self-loot | `t3b_materialize.py` | One double-click: "You quickly gather all of your belongings."; katana, shield and all armour back on | PASS |
| D8 Materializing ends 60 s after the corpse is opened | `t3b_materialize.py` | "You have fully materialized." at 60 s | PASS |
| D9 A confirmed action ends materializing | `t4_killer.py` | A second potion use: the end line | PASS |
| K1 The killer drops the fight | `t4_killer.py` | After the troll killed Dtest: troll FocusMob null, Warmode False | PASS |
| K2 The killer cannot see a materializing player | `t4_killer.py` | No troll hit for 20 s beside it | PASS |
| K3 The killer spares the player 2 minutes after first seeing them again | `t4_killer.py` | First troll hit 125 s after materializing ended | PASS |
| C1 Corpse arrow (real client) | `s4_stage.py` | The gold Tracking arrow at the screen edge, pointing to the corpse 10 tiles away | PASS, `corpse-arrow-zoom.png` |
| C2 No arrow for an empty corpse | `s3_death.py` | A corpse with nothing on it (starting gear is kept) gets no arrow | as designed |
| H1 The guide's Dying page with the flags on (real client) | `[Welcome` > Rules > Dying | 10 minutes, the arrow, the war-mode tip, materializing, the killer going home | PASS, `guide-dying-materializing.png` |

## Faults found and fixed during the test

1. **The too-tired line could never reach a ClassicUO player.**
   - ClassicUO switches to walking by itself once stamina is 1 or less (`PlayerMobile.cs:532`), so it never sends the run the server would refuse.
   - The stock message (500110) and its replacement were therefore never seen.
   - Fix: `StaminaReliefService` also sends the line when a running step starts at 2 stamina or less (`EventSink.Movement`, `RunningOutOfBreath`, 3 new tests). Re-checked live: S2.
2. **The client's auto-use ended materializing by itself.**
   - Resurrected at low health, auto-bandage fired twice: the warning, then the confirm. Materializing ended within a second with no choice by the player (`autouse-ended-materializing-bug.png`).
   - Fix (ClassicUO `AutoUse.Tick`): nothing is used automatically while the player has the materializing buff, recognised by its "Materializing" text on the stealth icon.
   - Re-checked in the real client: D4 at low health, no warning.
3. **0x4001 was not a ghostly hue.**
   - ClassicUO's spectral shader draws it as a black see-through shadow, black even in the paperdoll.
   - Five candidates were compared from another player's view (`materializing-hue-candidates.png`). The shipped `deathRecovery.materializingHue` is now 0x047E (1150), a pale silver.
4. **Guide wording:** "about 10 minutes" sat beside "about seven minutes". With the flag on, both now use digits.

The shard suite after the fixes: 1,613 passed (run `20261017T154712363Z-60945e`). The client NativeAOT `cuo.dll` with the auto-use fix is in `work/player-client-dist-batch`; `ClassicUO/bin/dist` is not updated.

## Seen, not changed (for the owner)

- **Starting armour makes most monster hits do 1 damage.** A Swordsman in starting armour took 1 damage from every troll and ettin hit (7 of 7). The unarmoured mage took 1-11 from the same ettin. That's stock pre-AOS armour absorption, and it hides any stamina effect for armoured characters.
- **A monster that hits an innocent in town can still be guard-called by a townsperson** (stock `CheckGuardCandidate`). It didn't happen in G2, where the townsfolk were too far away.
- **The corpse arrow at the screen's top edge sits partly under the shard's top bar** (`corpse-arrow-zoom.png`).

## Not covered live

- The Moonglow Zoo keeping its animals over time; only its unguarded status was checked.
- `blueSelfLoot` refusing a criminal or murderer (unit-tested).
- `killerGoesHome` with a killer that is fighting someone else (unit-tested).
- The arrow surviving a relog.

## Clean-up

- The clients, Navrey sessions and the host's server are stopped, and port 2593 is free for the farm.
- `work/hosts/batch` and its test accounts are kept for any re-check; `Remove-DisposableHost.ps1 -Name batch` removes them.

## Afterwards: the materializing warning is a dialog (owner, same day)

The owner's ruling: "The materializing warning should be a dialog like the criminal action warning."

**What changed:**
- The chat warning and the do-it-twice confirm are gone. An ending action is now held, and a shard dialog opens: "Materializing" / "End materializing?", a danger line "This will end your materializing, and monsters will be able to see you again.", and OKAY / CANCEL. It is built with `GumpStyle`, like the Hot Zone travel warning, and passes the style-guide test.
- **OKAY** ends materializing and replays the action: an item use, a skill, a spell, an attack, or the vendor's buy or sell list.
- **Lifting** an item cannot be replayed from the server, so OKAY says "Pick it up again."
- **CANCEL** says "You stay materializing."
- The engine's `PlayerAction.Trade` is split into `Buy` and `Sell`, and `deathRecovery.confirmSeconds` is removed.

**Checks:**
- Suites (run `20261017T171232292Z-afae3b`): shard 1,614 passed; UOContent 1,404 passed.
- In the real client:
  - a potion opened the dialog and was not drunk (`images/batch-test-2026-10-17/materializing-confirm-dialog.png`);
  - CANCEL kept materializing;
  - OKAY ended it and replayed the potion: "You are not poisoned." (`materializing-confirm-okay.png`).

## Afterwards: renamed Between Worlds, and the corpse-items rule (owner, same day)

**Rename.** The owner: "Rename materializing to between worlds with the b and in the w capitalized." Every line a player sees now says Between Worlds:
- the start message, the buff, the dialog ("Between Worlds" / "Come fully back?"), "You stay Between Worlds." and "You are fully back in the world.";
- the guide;
- the client auto-use check, which now looks for "Between Worlds".

The code, the flag `materializing` and the `deathRecovery.materializing*` keys keep their names.

**Exploit.** Without limits, Between Worlds could carry an armed player unseen past monsters: gear up from the bank first, or be resurrected at a dungeon entrance and walk down. Moongates and dungeon teleporters do not end it. The owner's rulings:
- "only allow them to pick up items from their corpse that way they can't equip a bunch of stuff they want to use after dying and while in the between world state to go where they want to go";
- then "Equipping items from your own inventory / pack should not take you out of it this way you can get your corpse items and get situated".

**The rule as built:**
- **Free, no dialog:** doors; looking in your pack, bank or corpse; taking items from your own corpse; sorting your own pack; putting on or taking off your gear.
- **Asks first:** anything taken from the bank, and every other action, as before.

After a death the pack holds only kept starting items and what came off the corpse, so the bank was the remaining way to arm yourself. Walking unseen with kept starting tools (a Prospector's pickaxe, for instance) stays possible; the owner chose this rule over a corpse-distance tie.

**Bug found and fixed.** Between Worlds hid the player from townsfolk too, so a banker ignored "bank" and healers could not see you. It now hides you only from monsters: not vendors (healers and bankers are vendors), not Order or Chaos guards, not blue-named NPCs (`DeathRecovery.IsMonster`).

**Navrey (the owner: "You could also update navrey").** The state file now carries `bank`, `bankOpened` and `bankID`: the opened bank box's contents, in the same shape as `backpack` (`Agent/Files/StateFile.cs`, `Navrey/CLAUDE.md`). It is built into `Navrey/bin/Debug` and uncommitted; the farm's Lean builds need a rebuild to get it.

**Checks:**
- Shard suite (run `20261017T175013480Z-c14e93`): 1,618 passed.
- Live: `t5_corpse_only.py` (the stricter rule), `t7_bank.py` and `t8_bank_nav.py`. On the final rule:
  - a pack move keeps Between Worlds;
  - a bank item opens the dialog, and CANCEL keeps the item in the bank;
  - the banker still answers.
- Real client: dragging the katana out of the bank opens the dialog (`images/batch-test-2026-10-17/between-worlds-bank-asks.png`).
