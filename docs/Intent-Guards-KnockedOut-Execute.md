# Intent, guards, Knocked Out and Execute: the 2026-10-07 changes

Status: **built 2026-10-07; local only, not committed or deployed.** No flag: Intent (`safeWorld`) and Knocked Out (`knockedOut`) are already on, so everything below takes effect at the next deploy. Owner sign-off 2026-10-07 on the plan, with these answers: the guard-call text is shown to the caller only; walking out of adjacency cancels an Execute and a hit does not; the Execute countdown is public; plus three additions (a recovery countdown everyone can read, every Execute check made before the countdown starts, and Execute in the context menu as well as the command).

## 1. The five asks and what was done

| Ask | Finding | Done |
| --- | --- | --- |
| An Intent player a blue hit first should not become criminal by hitting back | Already true by the engine's own rule: attacking someone who is "innocent" to you makes you criminal (`IsHarmfulCriminal`), and a blue who hit you first is in your aggressor list, so is not innocent to you (`Notoriety.CheckAggressor`); the shard lets you strike back through the same list (`HasExistingRelationship`, about two minutes) | Verified live (case I1) and pinned in `exec_live.py`; no code change |
| Guards will not come for an Intent grey; players who call guards on one are confused | Guards act on the `Criminal` flag or reds only (`GuardedRegion.IsGuardCandidate`), so calling guards next to an Intent player did nothing and said nothing | `GuardCallNotice`: when someone calls guards in a guarded town, each Intent player they can see within 14 tiles (the call's own range) shows "This player has not yet performed a criminal act." to the caller only. No engine change (an `EventSink.Speech` handler) |
| An `[Intent]` tag | **Did not exist.** The player showed grey and nothing else | `[Intent]` after the name (and any title) in the single-click label and the tooltip, while Intent counts (on, not criminal, not murderer: the same rule as the grey). One narrow engine hook: `PlayerMobile.NameSuffixHandler` |
| Knocked Out is too long: 30 seconds | `KnockedOutService.Duration` was 90 s | 30 s. The two message lines now read the constant; the guide pages already did |
| Execute takes 5 seconds next to the victim, with countdown text that cancels on walking away | `[Execute` targeted at any distance and killed at once | `KnockedOutService.BeginExecution`: see section 2 |
| (added) a countdown for everyone when a Knocked Out player will get up | none | `KnockedOutCountdown`: a public label over the Knocked Out player every 5 seconds, then every second for the last 5 ("Knocked Out: 25"); the Execute's own label replaces it while someone is executing |
| (added) Execute checks before the countdown | all checks ran at the end | `KnockedOutExecution.Check`, run at the start; a refusal is told at once and nothing starts |
| (added) Execute as a contextual action | none | An "Execute" entry in the menu you get by clicking a Knocked Out player: offered only to a criminal or murderer with the right to execute, greyed until they stand next to the victim. Needs one narrow engine hook (`PlayerMobile.ContextMenuEntriesHandler`) and the shard's own client text (`Clilocs.txt`) |

## 2. How Execute works now

1. **Start (command or menu).** `PlanExecution` gathers the facts and `KnockedOutExecution.Check` returns the first refusal, in the order a player should hear it: not switched on; yourself; not Knocked Out; not a criminal or murderer; no right (you did not fight them); you are already executing someone; someone is already executing them; **not adjacent**; **they will wake before you could finish** (5 seconds or less left). A refusal is a message at once and an audit line; no timer starts.
2. **Countdown.** The executor is told "You begin to execute X. Stay next to them for 5 seconds."; the victim "X is executing you!"; a public label over the victim reads "Execution: 5" down to 1.
3. **Cancelled** (checked four times a second) when the executor is no longer within one tile ("You step away, and the execution is cancelled."), the victim is no longer Knocked Out ("They are no longer Knocked Out, and the execution is cancelled."), or the executor dies or logs out. A hit on the executor does not cancel it.
4. **At five seconds** the existing `Execute` runs, so its checks, the murder rule (`ExecutionMurderRule`) and the report are unchanged; if it now fails the executor is told "They can no longer be executed."

## 3. Engine and client changes

- **ModernUO** (`UOContent`, `PlayerMobile`, uncommitted): `NameSuffixHandler` (added to the existing `ApplyNameSuffix`) and `ContextMenuEntriesHandler` (called at the end of `GetContextMenuEntries`). Both are optional shard-owned hooks in the style of `NonlocalLiftHandler`. Tests: `PlayerMobileShardHookTests`.
- **Client fork** (uncommitted): `ClilocLoader` also reads the shard's own text from the client's `Data/Client/Clilocs.txt` (it only looked in the Ultima Online folder, the player's own install). The shard's file is `ShardContent/data/client/Clilocs.txt` (`3050001 Execute`); copy it to the player dist with `cuo.dll`.
- The context entry's number, 3,050,001, is above every number the stock client has and inside what the older menu packet can carry.

## 4. Player-facing text for review

- Guard call (to the caller, over each Intent player): "This player has not yet performed a criminal act."
- Tag: "[Intent]" after the name.
- Knocked Out start: "You have been Knocked Out for 30 seconds." Recovery label: "Knocked Out: N".
- Execute: "You begin to execute X. Stay next to them for 5 seconds." / to the victim "X is executing you!" / label "Execution: N" / "You step away, and the execution is cancelled." / "They are no longer Knocked Out, and the execution is cancelled." / "X stops executing you." / "They can no longer be executed." / success "The Knocked Out player has been executed."
- Refusals: "Knocked Out is not switched on, so there is nothing to execute." / "You cannot execute yourself." / "They are not Knocked Out." / "Only a criminal or a murderer can execute a Knocked Out player." / "You can only execute a player you have been fighting." / "You are already executing someone." / "Someone is already executing them." / "You must stand next to them to execute them." / "They will get up before you could finish."
- Hot Zone entry (corrected, section 7): "You have entered <zone>, an outdoor PvP Hot Zone. Players may initiate combat freely here. Killing an ordinary blue is still murder: the victim can report you for a murder count."
- Guide (Fighting other players, Commands, Dying): the Intent paragraph gained "An [Intent] tag also shows after your name when someone clicks you." and a paragraph "Calling guards on such a player does nothing: the caller is told that the player has not yet performed a criminal act."; Knocked Out gained "A countdown over you shows everyone nearby when that will be."; Execute reads "...may [Execute them, or choose Execute from the menu you get by clicking them. It takes 5 seconds with a countdown over the victim, and the executor must stay next to them: walking away cancels it."; the command line reads "[Execute - Execute a Knocked Out player you are allowed to, next to them, in five seconds."
- **Root `README.md`, to apply at the deploy** (it describes deployed behavior): in the Knocked Out line "for 90 seconds" becomes "for 30 seconds, with a countdown over them that everyone nearby can read"; after "may `[Execute` them" add " (or choose Execute from the menu you get by clicking them): the executor must stand next to them for 5 seconds while a countdown runs over the victim, and walking away cancels it."; in the Opt-in PvP line add "An `[Intent]` tag shows after your name when someone clicks you." and "a player who calls guards on you is told you have not yet performed a criminal act".

## 5. Named limits

- The tooltip's `[Intent]` is rebuilt when the tooltip is next requested; the click label is always current. A player who turns criminal while Intent is on loses the tag at the next refresh.
- Guards still do nothing about an Intent-only grey; only the message is new.
- Under fire the executor is not interrupted by a hit; a rescuer must kill the executor, or the victim must wake.
- Hot Zone scripts under `tests/scenarios/hot-zones` that call `[Execute` expect an instant execute and a 90-second window; their `execute` helpers were updated, but only `execute_countdown_live.py` was re-run for this change.
- The real-client Knock Outs were produced with the probe verb `kofrom` (the real service entry, the attacker recorded), not with a keyboard attack: the client's double-click attack did not reach the server in this harness (the Navrey cases cover real blows). Nothing player-facing depends on that.

## 6. Evidence (2026-10-07, disposable host `qol`)

**Navrey, `execute_countdown_live.py`, 8 of 8:** I1 an Intent player the blue hit first hits back and is not criminal; K1 Knocked Out lasts 30.1 s with labels 30, 25, 20, 15, 10, 5, 4, 3, 2, 1; E3 next to the victim the countdown runs 5 to 1 and the victim dies; E1 not adjacent is refused at once; E2 a blue is refused at once; E4 walking away cancels; E5 the victim waking cancels; E6 a victim who would wake first is refused at once.

**Unit tests:** Shard suite 960 passed, 0 failed (isolated run `20261007T202144484Z-ac45cd`, after the Hot Zone text correction); the UOContent suite with the two `PlayerMobile` hook tests passed earlier the same day.

**Real ClassicUO client (screenshots sent to the owner, in `work/player-client/{Bea,Eda}/shots`):**

| Shot | What it shows |
| --- | --- |
| `20261007-155501-guards-called` (Bea) | "This player has not yet performed a criminal act." over the Intent player, to the caller |
| `20261007-155633-intent-click` (Bea) | the single-click label "Pru [Intent]" |
| `20261007-161816-bystander-ko-0`, `-161822-bystander-ko-5` (Bea, a bystander) | "Knocked Out: 30", then "Knocked Out: 25" over the victim |
| `20261007-161820-executor-menu-menu` (Eda) | the menu on a Knocked Out player: Open Paperdoll, **Execute**; the recovery label "Knocked Out: 25" beside it |
| `20261007-161859-executor-countdown` (Eda), `-161900-bystander-countdown` (Bea) | the countdown over the victim (these shots predate the rename, so they read "Being executed: 5, 4, 3" and "4, 3, 2, 1"; the label is now "Execution: N", changed at the owner's request the same day, with only the text changing), and "You begin to execute Vik. Stay next to them for 5 seconds." |
| `20261007-161905-executor-after` (Eda) | "The Knocked Out player has been executed." and the corpse |
| `20261007-161957-executor-cancelled` (Eda) | the executor moved away mid-countdown: "You step away, and the execution is cancelled." in red, the victim's "Knocked Out: 20" back |

Not captured in the real client: the greyed-out Execute entry for a non-adjacent executor (the entry's enabled state is covered by the unit tests and by E1's refusal), and the tooltip's `[Intent]` (the single-click label is shown; the tooltip is the same name line).

## 7. Correction made at the owner's request (2026-10-07)

The Hot Zone entry message ended "Murdering an ordinary blue still adds a murder count and 24 hours of red time." The 24 hours belonged to the automatic murder ledger (`automaticMurderAdjudication`, off since the 2026-09-30 ruling that stock murder reports return). It now reads: "Players may initiate combat freely here. Killing an ordinary blue is still murder: the victim can report you for a murder count." (`OutdoorHotZoneBoundaryService.cs`, pinned in `OutdoorHotZonePolicyTests`). The 24-hour wording remains only in the historical contract and audit documents and in `MurderAdjudicationService` (inert while the flag is off).
