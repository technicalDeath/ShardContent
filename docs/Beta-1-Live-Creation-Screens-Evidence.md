# Beta 1 item 5: live creation-screen test (trimmed by the owner)

Roadmap: [Beta 1](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 5. The owner trimmed the original "every template and Advanced" matrix to **one profession template and Advanced**, so the other 15 professions were verified through the packet path in [the templates audit](Beta-1-Character-Templates-Audit.md) but not through the screens.

**Status: closed 2026-10-01.** All checks passed.

## Method

Navrey's new `createui` command drives the real character-creation gumps through their own handlers, in the order a player uses them: type the name and press Next on the appearance screen; click the folder and profession cards (or Advanced and its skill drop-downs and stat sliders); press Finish on the start-city screen, which sends the creation packet. This differs from the earlier `createcharacter` command, which builds and sends the packet directly. Navrey carries the same creation-screen code as the player client; it is not a person clicking in the `ClassicUO.exe` window.

Environment: a disposable host (`tpl`) running the deployed shard with the shard profession file in use, two fresh accounts with no character, Navrey sessions started by `New-TestCharacter.ps1 -CreateCommand`. Driver and checks: `tests/scenarios/templates/ui_live.py` (cycle script `work/templates-live/live3.ps1`).

## Results

| Case | What was driven | Result |
| --- | --- | --- |
| Profession template | Adventurer, then Archer, then Ranger, then Finish | The character entered the world with its name. Skills: Archery 50, Tracking 35, Animal Taming 35 (the era Ranger's 50/25/25 scaled to 120 points). Stats **54/33/33 = 120**, each at least 30 |
| Advanced | Advanced; drop-downs set to Magery, Meditation, Evaluating Intelligence, Wrestling; stat sliders set to 60/30/30; Finish | The screen held the four skills at 30 and stats 60/30/30 just before Next. The character entered the world with its name, stats **exactly 60/30/30 = 120**, and exactly those four skills at 30 (120 skill points) |

Earlier the same day, on the real Advanced screen (`charstats`): stat sliders 30 to 60 each, starting 40/40/40, the total holding at 120 as one slider is pulled to its limit and the others follow, none below 30. Packets with exact 120-point choices (60/30/30, 40/40/40, 30/30/60) were kept exactly; an old 90-point packet was rescaled (60/15/15 to 55/33/32); an out-of-range choice was rescaled to 120 with a 30 minimum.

## Found and fixed by this item

The Advanced screen allowed only 90 stat points (reported by the owner): its sliders were hard-coded to a 90-point total and the server rescaled the choice to 120. Now 120 points, 30 to 60 each, kept exactly by the server (see the audit).

## Limits

- Driven through Navrey's copy of the screens, not the `ClassicUO.exe` window; the player client and Navrey share the creation code, and the published `cuo.dll` was built from the same changes.
- One profession template (Ranger) and Advanced, as the owner chose. The other 15 professions' skills and stats are covered by the packet-path matrix, and the two-level folder walk and its Back button were not exercised beyond the Adventurer, Archer, Ranger path.
- The Advanced skill sliders are the client's four skills at 30 (the owner chose to leave that as is).
