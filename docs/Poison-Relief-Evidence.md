# Poison relief: evidence

Plan: `Poison-Relief-Plan.md`. Readiness: `Poison-Relief-Readiness.md`. Built and verified 2026-10-11. **Committed (ModernUO `435d1c081`, ShardContent `e337c7e`) and deployed to the dev host on 2026-10-11 with the flag off; **activated the same day** on the owner's "activate poison relief" (`featureFlags.poisonRelief` true, redeployed, `[PoisonReliefStatus` reads ON).**

## Decisions (owner, 2026-10-11)

- Ideas 1 to 3 wanted, idea 4 (shorter poison for novices) not.
- 5 Lesser Cure potions for every new character; a 30 second grace window; the grace covers Lesser poison only (a setting, `graceMaxLevel`); the hint shows once per character.
- One flag, `featureFlags.poisonRelief`, off until the owner says "activate".

## Build

- **ModernUO:** `PlayerMobile.PoisonImmunityHandler` and its use in `PlayerMobile.CheckPoisonImmunity`; four tests added to `PlayerMobileShardHookTests`.
- **ShardContent:** `PoisonReliefService.cs` (rules, starter potions, the watch, the hook, `[PoisonReliefStatus`), `poisonRelief` settings and the flag in `ShardRulesConfiguration.cs`, registration in `ShardBootstrap.cs` before `StarterWeightBudget.Register`, the shipped settings and flag in `shard-rules.json`, the poison tooltip line (`buff-icons.json`, a `relief` value in `BuffIconRules.cs` and `BuffIconService.cs`), `tests/PoisonReliefTests.cs`, the live probe and driver in `tests/scenarios/poison-relief/`.

## Verification

- **Engine tests:** `PlayerMobileShardHookTests` 13/13 (run `20261011T150241996Z-c49964`): with no handler a poison lands as before; the handler is given the player, the source and the poison and can refuse it (`ApplyPoison` returns Immune and the player is not poisoned); a handler that accepts leaves the poison to land; the handler is not asked when an equal or stronger poison is already active.
- **Shard suite:** 1198/1198 (run `20261011T150521433Z-b5da4e`), 39 new tests: the grace decision table (inside and outside the window, the cap, a stronger poison, a player source, staff, the flag off, a window of zero), the hint rule, the potion count, validation, the shipped configuration, the tooltip line shown only while relief is on.
- **Live, disposable host `poison-relief`** (flag on in the host's copy, the hooked engine, real server code; `poison_live.py`, run `work/poison-relief/run1.log`), **18/18**:
  - Potions: Pip and Pam each start with 5 newbied Lesser Cure potions and a load of 183 of 229 (inside the 85% starter budget of 194); the potions survive a death.
  - Hint: a Lesser poison from a monster lands on a fresh character; the hint appears in the journal; it is shown once across a whole run of five poisonings; a character with Healing and Anatomy 60 is poisoned and not told.
  - Grace: inside the window a Lesser poison from a monster is refused (result Immune) and the player is told; a Regular poison lands; a Lesser poison from a player lands; after 33 seconds a Lesser poison from a monster lands again.
  - Flag off: a Lesser poison lands straight after a cure and nothing is said.
- **Real client (ClassicUO 1.1.0.0), shown to the owner:** a new archer poisoned by a monster gets the hint (on screen and in the journal, text unchanged from the code); hovering the Poisoned buff icon shows "Poisoned / Lesser poison. / You lose health until it wears off or you are cured. / A bandage only tries to cure you, and that needs Healing and Anatomy 60." Four frames of the hover showed the tooltip steady (the owner's separate report of a flickering buff tooltip is on the to-do list and was not seen in these frames).

## New player text (for the owner's review)

- Hint: "You are poisoned. While you are poisoned a bandage only tries to cure you, and that takes Healing and Anatomy of 60 or more, so it will not heal you. A Cure potion (alchemists sell Lesser Cure for 15 gold), the Cure spell, or waiting it out will end the poison."
- Grace: "You are still shaking off the last poison, and this one finds no hold." (the stock overhead "* The poison seems to have no effect. *" also appears)
- Tooltip line: "A bandage only tries to cure you, and that needs Healing and Anatomy 60."

## Named limits

- The grace window is held in memory: a server restart forgets it (it lasts 30 seconds, so the effect is negligible). The watch runs once a second, so the window starts up to a second after a poison ends.
- Potions go only to characters created while the flag is on; existing characters are not given any (no staff grant command was built).
- The hint is per character and shown once; a character who later trains Healing and Anatomy to 60 is never told, by design.
- The grace window is for ordinary players only and for Lesser poison only. Raising `graceMaxLevel` widens it without code.
- The graveyard still hurts: 4 hit points every 3 seconds for about 35 seconds on a 78 hit point character, and bandages still heal nothing while poisoned. The relief is the potions, the explanation and no chain-poisoning, not immunity.
- The Poisoned tooltip line is in the shipped `buff-icons.json` but is dropped while the flag is off.
