# Circle of transparency: gradient default, staircase fix, flicker fix

**2026-10-14.** Client only (ClassicUO fork). Owner asked for the gradient as the default and to look into two bugs: the circle cutting open the higher steps of a staircase (Britain 1491,1548) and flicker while running along interior walls (1498,1553).

## Default

`circle_of_transparency_type` is 1 (gradient) in `data/client/default-profile.json`, pinned by `ClientDefaultsTests`. 0 is the full circle. New profiles only; an existing profile keeps its own choice (Options > General).

## Bug 1: the circle opened up the stairs behind the player

**Cause.** `Static.TransparentTest` and `Multi.TransparentTest` marked every object whose top is above the player's head and that "can be transparent" (height over 5, walls, roofs, surfaces) as cuttable. That includes the higher steps of a staircase that sit behind the player on screen: they were inside the circle, so the circle dissolved them and showed the floor underneath. Seen clearly in the full circle.

**Fix.** `GameObject.CanOccludePlayer()` (`View.cs`): the camera looks from the south-east, so only an object on a tile with a larger X + Y than the player's, or on the player's own tile, can hide the player. Everything behind or beside the player is never cut. Both tests call it.

**Checked in the real client** at 1491,1548 (z 30), full circle and gradient: before, a stone arc was cut out of the staircase; after, the staircase is whole (`work/player-client/MaceB/shots/20261014-144735-stairs20.png` before, `...-145119-stairs-fixed.png` and `...-145806-stairs-grad.png` after).

## Bug 2: flicker while running (gradient only)

The owner's guess was right: only the gradient flickered.

**Cause.** The gradient works out each object's alpha from its distance to the player's place on screen. `GameScene` read that place with `Player.GetScreenPosition()` before the frame's camera offset was computed, so it used the previous frame's position. Standing still the two agree; while running they disagree. A temporary log of the old value against the correct one, running south-west along the wall at 1498,1550 to 1498,1557, showed a constant error of about (20, -20) pixels on every frame while moving and 0 when still, so the circle trailed the character by roughly a tile and its edge swept across the wall pieces as the speed varied.

**Fix.** The place is now computed after `GetViewPort()` from the same frame's camera offset (`GameScene.cs`, next to `GetViewPort()`), so the circle sits exactly on the character.

**Checked:** the temporary log (removed) proves the cause and that the new value is the exact one; frame bursts of the run (`shots/burst3.png` before the fix, `burst4.png` after) look alike to the eye at 25 fps, so the visual flicker was not captured on film either way. Say if it still flickers.

## Left alone

- A wall that was cut while in front of the character becomes solid when the character walks past it (it fades back in with the client's normal fade); walking back makes it dissolve again at once. That is the price of cutting only what can hide the player.
- The shader circle (full) is centred on the screen centre and did not have the position error.
