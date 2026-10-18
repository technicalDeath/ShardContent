# War-mode reminder for ghosts near a healer

**Flag:** `featureFlags.ghostHealerReminder`, built 2026-10-16. **Off**: not activated, not deployed, not committed.

## The owner's rulings (2026-10-16)

- "We should just remind players players to enter war mode to get ressurected when they are near a healer."
- "The warning should be if you're not in war mode."

The rules stay stock.

## Stock behaviour, from the code

- A living mobile sees a ghost only while the ghost is in war mode (`Mobile.CanSee`).
- A healer offers a resurrection only when a ghost it can see steps into its 4-tile range from outside it (`BaseHealer.OnMovement`: `InRange(m, 4) && !InRange(oldLocation, 4)`).
- So a ghost in peace mode beside a healer waits forever. A ghost that turns war mode on while already beside one must still step back and walk up.
- On the bot farm, 30 bots in 15 professions hit this.

## What it does

- `GhostHealerReminderService` watches a player ghost that is **not in war mode** and within 8 tiles of a living healer.
- It checks each time the ghost moves (`PlayerMobile.PositionChanged`), and once 4 seconds after a death (`PlayerMobile.PlayerDeathHandler`, registered with `+=`).
- The ghost is told, in yellow (0x35), at most every 30 seconds: "A healer cannot see a ghost in peace mode. Press Tab for war mode, then walk up to the healer from a few steps away to be offered a resurrection."
- It goes to every player.

## Checks

- `GhostHealerReminderTests`, 6 cases:
  - the rule's cases, including war mode, which gets no reminder;
  - the 30-second spacing;
  - the text;
  - the flag defaults to off.
- Shard suite: 1,576 passed.
- **Not yet checked live:** the line in the real client after a death beside the Britain healer, and that it stops once war mode is on.
