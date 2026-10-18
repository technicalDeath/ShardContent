# Corpse timer notice

**Flag:** `featureFlags.corpseTimerNotice`, built 2026-10-17. **Off**: not activated, not deployed, not committed. Live testing is held for the owner's batch test.

**The owner's ruling (2026-10-17):** "Show the player the message about how long they have."

## Stock behaviour, from the code

`Items/Misc/Corpses/Corpse.cs`:
- A corpse decays after `_defaultDecayTime`, 7 minutes.
- A player's corpse then turns to bones and keeps everything it holds (`TurnToBones`).
- The bones are deleted with their contents after `_boneDecayTime`, a further 7 minutes. That makes 14 minutes in all.
- Nothing told the player any of this.

## What it does

- **Engine:** read-only `Corpse.DefaultDecayTime` and `Corpse.BoneDecayTime`, so the line quotes the real times. The engine's behaviour is unchanged.
- **Shard** (`CorpseTimerNoticeService`): 3 seconds after a player dies (`PlayerMobile.PlayerDeathHandler`, registered with `+=`), while the corpse exists, the player is told in yellow (0x35): "Your corpse will turn to bones in 7 minutes, and the bones and everything in them will be gone 7 minutes after that."
- It applies to every player. It comes ahead of the healer reminder, which is sent at 4 seconds.

## Checks

- `CorpseTimerNoticeTests`, 4 cases: the text, a single minute, the engine times are 7 and 7, and the flag defaults to off.
- Full suites (run `20261017T124942803Z-19989c`): shard 1,580 passed; UOContent 1,404 passed, 2 skipped.
- **Not yet checked live:** the line in the real client after a death.
