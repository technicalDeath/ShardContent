# Status windows: [SkillClasses, [SkillBank, [Mastery, [IntentStatus, [TravelWarning and the Ward

Status: **built and checked in the real client 2026-10-06 (owner requests, same day); local only, not committed or deployed.**

The owner asked for a batch of player-facing changes. Everything a player sees was looked at in the real ClassicUO client (skill `player-client-shots`).

## What the owner asked for, and what was done

| Request | Result |
| --- | --- |
| Ward text: "detected", not "noticed" | The Welcome Ward page and the Ward item's own description now say detect and detected throughout. A test fails if the Ward page says "notice" |
| Mastery text said a cycle not used "is lost" | The page now says "Nothing you have gained is ever taken away. A cycle in which a skill is not used simply gives that skill no allowance, and it is not made up later." The window says the same. **This is not a delay**: a missed cycle's allowance is never granted later (see Named limits) |
| `[SkillClasses` as a window in the guide's style | One window: an overview of the classes and their speeds, then a page per class with its speeds, its Mastery allowance and its skills; a button opens `[Mastery` |
| `[SkillBank` and its settings as a window with buttons | One window: how full the bank is (with a bar), each banked skill with the skill now, what is banked, and tick-boxes to set it Locked or Down (saved at once, with a line saying what changed), six skills to a page, a warning line when the bank is nearly full, and a "How it works" button into the guide. The typed `[SkillBank lock <skill>` forms still work and open the window. **Later the same day** (see `Skill-Bank-Faint-Memories.md`): a Faint Memories banner for new characters (four rows a page while it shows), restores of 0.2, and a Discard button on each row that asks the player to type `discard` |
| `[MasteryStatus` as a window, and rename the command to `[Mastery` | `[Mastery` opens a window: when the next cycle begins, then one row per Mastery skill with where it stands between 90.0 and 100.0 (a bar), the allowance stored, whether it has claimed this cycle, and how far it has to go; six to a page; buttons into the guide and `[SkillClasses`. `[MasteryStatus` no longer exists. Staff may name a player by serial and get that player's window |
| `[IntentStatus` showed developer detail | A player gets a Criminal Intent window (ON or OFF, what that means, a button to switch it). Staff still get the policy diagnostics as text |
| Criminal Intent should explain that you do not take on a criminal's consequences until you commit a criminal act | The window (ON or OFF) and the guide's Fighting page say: "Criminal Intent does not make you a criminal: guards will not attack you, and you can still use Recall and gates, until you commit a criminal act such as stealing." (`PvpIntentService.NotACriminalNote`). Left out for someone who is already a criminal or a murderer, for whom it would not be true. Checked against the code: guards act only on the Criminal flag (`GuardedRegion.IsGuardCandidate`) and Recall, Gate Travel and public moongates refuse only a `Criminal` caster; Intent only changes the notoriety other players see and the attack rules |
| A Camping section in the guide | New page, shown when either camping switch is on: the kit, lighting, how long a fire burns, feeding it, the secure camp and Bedroll logout. Every number comes from the camping rules and the stock fire |
| Do not repeat the tagline in the welcome text | The first page says "Welcome to UO Rekindled." and the window header carries the tagline |

## The other commands, evaluated (owner request: "evaluate what other commands should have their own gump ... and make them")

| Command or interaction | Verdict |
| --- | --- |
| `[IntentStatus` / `[Intent` | **Window** (done). It is a state with a switch. `[Intent` stays a one-keystroke toggle for people who type it |
| `[TravelWarning` | **Window** (done): the warning ON or OFF, what it does, a button to flip it. `[TravelWarning on` and `off` still work |
| A Backpack Ward's double-click | **Window** (done): the Ward's phase as a coloured headline and its sentences. It used to scroll past as overhead lines |
| `[CampTravel` | Already a window (the camp list, the confirmation) |
| `[Welcome` | Already a window |
| `[Execute` | **No window.** It needs a target cursor on the player in front of you; a window would only add a step |
| Staff status commands (`[ShardRulesStatus`, `[SkillBankStatus`, `[HotZoneStatus`, `[CampStatus`, `[TheftStatus`, `[KnockedOutStatus`, `[MurderStatus` and the others) | **No window.** Staff read them as text and the live drivers parse that text |
| One-line messages (Mastery login reminder, Knocked Out, fire feeding) | **No window.** A short message is the right size |

## How it is built

- `GumpStyle`: the frame, colours, footer button and bar shared by all of them (and by the guide). `GuideWindow`: the topic window the guide and `[SkillClasses` share (topics on the left, text on the right, any topic can be first). `StatusWindow` and `StatusWindows`: the small ones. `SkillBankGump`, `MasteryGump`, `SkillClassesGump`: the three table windows.
- What each window says is worked out by pure methods (`SkillBankService.GetView`, `MasteryProgression.BuildView`, `SkillClassesGump.BuildViews`, `StatusWindows.Describe*`) so unit tests pin it. The drawing is checked in the real client.
- Test-only probes (disposable hosts): `TestOnlySkillBankSeed`, `TestOnlyMasterySeed`, `TestOnlyDoubleClick`. The Mastery and skill-gain live drivers read the windows (`window_lines`) instead of text.

## Evidence

- Unit: Shard 792 pass (the new `StatusWindowTests`, `StatusWindowsViewTests`, `WelcomeGuideTests` additions, `SkillBankLedgerTests` fullness text).
- Real client (ClassicUO 1.1.0.0, disposable host `status-windows`): every window and page above, with clicks on the Locked and Down boxes, paging, the Intent and travel-warning buttons, and the Ward's window. Screenshots under `work/player-client/Rowan/shots/` (scratch).
- Found and fixed on the way: the row shading used a "checker transparency" element, which made the whole panel see-through in this client (taken out; the older Camp travel list and confirmation and the Hot Zone warning use the same element and were not changed here, so they are worth a look the next time they are opened); the first progress bar was thin (now bold).

## Named limits

- **A missed Mastery cycle gives no allowance and is not made up.** The wording now says exactly that and that nothing already gained is taken away. If the owner wants a missed cycle to be made up on the next login, that is a rule change in `MasteryEngine` (claim every missed cycle, up to the stored cap), not a text change.
- The Camping page's numbers on the test host differ from the real ones because that host scales fire times; the real numbers are pinned in `WelcomeGuideTests`.
- `[IntentStatus` for staff still prints the diagnostic lines.
- The Ward window was opened with a test-only double-click, not by finding the item on screen; the window and the double-click path are the same code a player's double-click reaches.
- A window never asks the server for fresh data by itself: a player who leaves one open sees the state it opened with until they press a button or reopen it.
