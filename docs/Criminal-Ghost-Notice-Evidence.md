# Criminal ghost notice

**Flag:** `featureFlags.criminalGhostNotice`, built 2026-10-17. **Off**: not activated, not deployed, not committed.

**The owner's ruling (2026-10-17):** "Both". Item 8 of the bot-farm QoL list: a criminal ghost is refused by the healer with no word on how long to wait.

## Stock behaviour, from the code

- A healer refuses a criminal with "Thou art a criminal. I shall not resurrect thee." (`Healer.CheckResurrect`, `WanderingHealer`; the evil healers do it only in later eras).
- The criminal flag ends `Mobile.ExpireCriminalDelay`, 2 minutes, after the last criminal act.
- Nothing told the ghost either fact.

## What it does

- **Engine (UOContent):**
  - `BaseHealer.RefusedCriminal`, raised by a new `RefuseCriminal(m)` helper that all four healers now use (the stock line is unchanged);
  - `PlayerMobile.CriminalChanged` and `PlayerMobile.CriminalSince`, from a `Criminal` override that keeps the staff property attribute;
  - `Server` is untouched.
- **Shard** (`CriminalGhostNotice`):
  - On a refusal, the ghost is told "You will be a criminal for about N more. Come back then, and a healer will bring you back." N is rounded up to the next 10 seconds, and the line is sent at most every 10 seconds.
  - When the flag ends while the player is a ghost: "You are no longer a criminal. A healer will bring you back now."
  - It applies to every player.

## Checks

- `CriminalGhostNoticeTests`, 10 cases: the wording of the time left, the wait line, the time counted from the last act, the end line, and the flag defaulting to off.
- Suites (run `20261017T180452436Z-99dd6e`): shard 1,628 passed; UOContent 1,404 passed.
- **Live** (`work/batch-test/t9_criminal_ghost.py`, Navrey, on the disposable host `batch`):
  - the healer refused, and the wait line said "about 2 minutes";
  - the flag ended at 119 s and the end line came;
  - walking back in brought the resurrection offer.
- **Real client:** not photographed. The staged ghost was out of the healer's line of sight. The lines are ordinary yellow system messages, like the corpse-timer line photographed in `Batch-Test-2026-10-17.md`.
