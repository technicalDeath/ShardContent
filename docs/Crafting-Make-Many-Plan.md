# Crafting "make this many": work plan for sign-off (2026-10-14)

Drafted autonomously. **Nothing is built.** From the To-Do list ("the agreed next item after the action repeat; also Beta 2d") and `Action-AutoRepeat-Evidence.md` ("crafting is a separate item"). It overlaps the Beta 2d crafting overhaul, so the owner should confirm it is wanted now, as a small standalone convenience, before any code.

## Goal and exit criteria
A new crafter who opens a smithing, tailoring, carpentry, tinkering, fletching, inscription or alchemy menu can make an item N times with one click instead of clicking Make Last N times, and can stop it at any time. Exit: unit tests for the stop rules, a live run on a disposable host (a loop of ten, a stop on out-of-material, a stop on cancel), a real-client picture of the control, flag off until the owner says "activate".

## Current state (read 2026-10-14)
- Stock `CraftGump` has item buttons and "Make Last" (`CreateMakeLastList`); each click makes one attempt (stock timers, sounds, skill gain, "You failed" / "You create" lines) and re-opens the menu. Nothing repeats.
- The shard already has `ActionRepeatService` (flag `actionAutoRepeat`, ON) with the pattern to reuse: restart the stock action after each attempt, cancel on any move, cast, war mode, fight, hurt, death, disconnect or open cursor, one loop per player, silence on cancel. Gathering and five other actions use it.
- Era: UOR has no make-N; this is a shard convenience in the same class as the gathering repeat, which the owner approved.

## Design
| Rule | Proposal | Stock |
| --- | --- | --- |
| Control | A text-entry box beside Make Last in the craft gump: "Make how many?" with a number 1 to 20 (default 1). Delivered through the existing gump class by a narrow ModernUO hook (the gump is stock) | none |
| Loop | After each attempt, the same recipe is made again until N attempts are done | one attempt per click |
| Counting | Counts attempts, not successes (a failure still uses time and sometimes material), so the loop is bounded and predictable | n/a |
| Natural stops | Not enough material or tool worn out or "you cannot make that" (the stock refusal ends it), a full pack, or reaching N | stock refusals |
| Cancel (silent) | Same list as the other repeats: move, cast, another skill, war mode, fight or being hurt, death, disconnect, an open cursor, closing the craft gump | n/a |
| Messages | One line at the start ("Making 10. Move or act to stop.") and one at the end ("Done: 7 made, 3 failed.") | none |
| Not covered | Repair, enhance, smelt, recycle, and any recipe that asks for a resource target (the loop stops there) | n/a |

## Work breakdown
1. ModernUO: a hook in `CraftGump`/`CraftItem` for a per-player "after attempt" notification and a way to add the count control (smallest possible: an event `CraftSystem.AttemptFinished(Mobile, CraftItem, CraftResult)` and a virtual that lets the shard add controls). To be justified in the sign-off.
2. ShardContent: `CraftRepeatService` reusing `ActionRepeatService`'s cancel rules, flag `craftRepeat` (off), a gump extension for the count box, tests.
3. Guide: a line on the Crafting page (gated) and the README at activation.

## Verification
Unit tests for count, stop rules and the line wording; a live run on a disposable host (blacksmith: 10 daggers with enough ingots, a run that ends on material, a cancel by moving); real-client picture of the gump with the box and the end line.

## Activation
New flag `craftRepeat`, off. Needs the owner's explicit "activate".

## Open questions (recommendation first)
1. Wanted now as a standalone item, or left inside Beta 2d? Recommend now, small.
2. Maximum 20 per click? Recommend 20.
3. Count attempts or successes? Recommend attempts.

## Out of scope
The Beta 2d overhaul (recipes, exceptional chances, material changes), bulk orders, auto-restock of material.
