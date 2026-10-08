# Knocked Out players lie on the ground

Status: **built, checked in the real client and DEPLOYED to the dev host 2026-10-07 18:00** on the owner's "Yes" (saves snapshot `work/save-snapshots/saves-20261007-175940-pre-lying-pose-deploy`; `UOContent` rebuilt into `Distribution` first; startup clean; `[KnockedOutStatus` shows "Drawn lying down"; README clause added; dev server left stopped; committed and pushed later the same day). The client `cuo.dll` with the pose is in `ClassicUO/bin/dist`. No feature flag: it rides on `knockedOut`, already on. Owner request 2026-10-07: "Can we have a knocked out player appear on the ground like a corpse (just visually) instead of standing?"

**Sign-off 2026-10-07:** option B (a lying flag our client fork draws, rather than a server-only animation trick) and dismount a Knocked Out rider. The design contract already said the player "lies on the ground with dead-like presentation" (Hot Zones plan, Knocked Out section).

## 1. What the client can and cannot do (research)

- The client has no flag, body or hue that draws a living human lying down. A ghost body would stand and make the player invisible to the living.
- After a Die animation the client goes back to idle. The stock "freeze on a frame" packets (BF 0x19 sub 5, BF 0x2B) set `ExecuteAnimation = false` and nothing ever sets it back, so they can never be undone on the player's own client and they would stop Execute's death animation from finishing. Rejected.
- A server-only look (the Die animation in reverse at the longest frame delay, refreshed every second) works on stock clients but shows a standing player to anyone who arrives or is teleported until the next refresh. Not chosen.

## 2. Design (as built)

- **The mark.** Mobile packet-flag bit **0x20** (`Flags.Movable` in the client's enum), which the protocol leaves unused for mobiles (items use it; the stock flags on a mobile are 0x01 to 0x10, 0x40, 0x80). It rides on every 0x77, 0x78 and 0x20, so range entry, login, teleports and re-sends carry it with nothing to refresh. A stock client ignores it and shows the player standing.
- **Server (ModernUO hook).** `PlayerMobile.ExtraPacketFlagsHandler` (a `Func<PlayerMobile, int>`, O(1), it runs for every observer on every move) and `PlayerMobile.GetPacketFlags` ORs its result in. Test: `PlayerMobileShardHookTests`.
- **Server (shard).** `KnockedOutService.Lying.cs`: a set of players being drawn lying. A player joins it where the recovery timer is scheduled (the Knock Out and a login while still Knocked Out) and leaves it in `ClearActiveState` (every exit: recovery, staff recover, expiry, Execute) and when the 1 Hz tick finds the state gone; each change sends a flags delta (`MobileDelta.Flags`). `[KnockedOutStatus` shows it.
- **Mounted riders** are knocked off first (`SetMountBlock(Dazed, what is left of the Knock Out, dismount)`, the stock "You have been knocked off of your mount!" and "too dazed to ride" texts), because a mount drawn under a lying human looks wrong.
- **Client (`ClassicUO` fork).** `LyingPose` (pure rules, tested) and `Mobile.ProcessLyingAnimation`: a flagged living human or elf body plays the human Die animation (group 21, six frames, about a second) and holds the last frame; unflagged, it plays it backwards once and returns to idle. Dead bodies and the dying copy the death animation renames are never held. The player's own client refuses to start a step while lying. `DisplayDeath` starts the death animation of an already-lying mobile at its end, so Execute turns the lying figure into the corpse without standing it up first. Nothing else about the mobile changes, so it stays clickable (the hit test uses the same frame), targetable and lootable where it is drawn.

## 3. Changed files

- ModernUO (committed in `067802c3c`): `Projects/UOContent/Mobiles/PlayerMobile.cs`; test `PlayerMobileShardHookTests.cs`.
- ShardContent (committed in `2fca57b`): `KnockedOutService.Lying.cs` (new), `KnockedOutService.cs`, `KnockedOutService.Execution.cs`; tests `KnockedOutLyingTests.cs`; probe verb `kofrom` in `tests/scenarios/alpha3-tools/TestOnlyProbe.cs`; evidence driver `tests/scenarios/hot-zones/knocked_out_lying_realclient.py`.
- ClassicUO (committed in `41a1ddccb`): `Game/GameObjects/LyingPose.cs` (new), `Mobile.cs`, `PlayerMobile.cs`, `Network/PacketHandlers.cs`; test `tests/ClassicUO.UnitTests/GameObjects/LyingPoseTests.cs`. NativeAOT build `work/client-publish-2026-10-07d` (previous `cuo.dll` kept in `work/client-dist-backups/2026-10-07-before-lying`).

## 4. Verification (disposable host `qol`, real ClassicUO clients for the executor and a bystander)

| Case | Result |
| --- | --- |
| A bystander sees the victim lying on the dock with "Knocked Out: 30" | pass |
| The executor clicks the lying figure: menu with Open Paperdoll and Execute (the hit test follows the drawn pose) | pass |
| Execute on a lying player: "Execution: 4, 3, 2, 1" over them, then the corpse on the same tile with no stand-up flash | pass |
| A mounted rider (ethereal horse): knocked off, statuette back in the pack, lying | pass |
| A player who walks into view mid-knockout sees the victim already lying | pass |
| The last seconds (5, 4, 3) still lying; standing again as the countdown ends | pass |
| Unit tests | ModernUO UOContent 1,369 passed (2 skipped); Shard 963 passed; client 20 passed (`LyingPoseTests`, `StartGameWindowSizeTests`) |

Screenshots were sent to the owner; they are in `work/player-client/{Bea,Eda}/shots` (`20261007-1707`, `-1709`, `-1712`, `-1714` stamps).

A defect found on the way, fixed: a staff recovery followed by a new Knocked Out inside the first one's 30 seconds ended the new one early, because the first timer was still running. `KnockedOutService.SupersededRecovery` makes a timer that finds a newer end stand down (`KnockedOutLyingTests`). It cannot happen in ordinary play (only staff recover early), so no live re-run was needed.

## 5. Named limits

- Stock ClassicUO clients ignore the bit and show a standing player; only the shard's client fork draws the pose. Navrey (headless) is unchanged.
- A player polymorphed into a creature, or a gargoyle, stays standing (the pose is drawn only for the four living human and elf bodies).
- A fresh viewer sees the fall animation (about a second) before the held pose.
- A dead player's pre-existing message "You recover from being Knocked Out." when an old timer fires after an Execute is unchanged (it predates this work).

## 6. To deploy

The client change is already in the dist. On the server: rebuild `UOContent.csproj` into `Distribution` first (new `PlayerMobile` hook), then `Deploy-Alpha1Baseline.ps1`. No save-format change. **Root `README.md`, to apply at the deploy:** in the Knocked Out line, after "with a countdown over them that everyone nearby can read", add "; they lie on the ground like a corpse (a rider is knocked off their mount first), as the shard's client draws it". The in-game guide's Knocked Out paragraph could gain the same clause; it was not changed.
