# Gump style pass: evidence (2026-10-07)

The owner approved `Gump-Style-Guide.md` on 2026-10-07 ("Approved, style pass can proceed") and asked for every shard window to be restyled to it, a test that keeps them that way, and before and after pictures from the real client. No flag is involved: it is the look of windows the shard already has. It was committed (`859c31c`), pushed and deployed to the dev host on 2026-10-07, on the owner's "Commit, push, deploy".

## What changed

| Where | Change |
| --- | --- |
| `GumpStyle.cs` | Rewritten as the whole style: colours (Warning gone; Good, Danger, Note, Chosen added), window classes and origins (Large 640x500, Medium 480, Dialog 440), margins and rules, one text-width estimator (`CharsPerLine`, `LinesFor`), and the helpers `Frame`, `Footer`, `Banner`, `MenuAction`, `MenuActionHere`, `GameAction`, `OkayCancel`, `RadioChoice`, `Tick`, `SectionHeading`, `TableHeader`, `Cell`, `EmptyState`, `Pager`, `Bar` |
| `StatusWindow.cs`, `StatusWindows.cs` | Intent, Travel warning and Ward: gem banner with the state in words, purple game action, blue Close, a hint in the footer; Intent ON and the warning OFF are Danger, Ward Primed is Note |
| `SkillBankGump.cs` | Result banner (two lines, gem), radio ovals for Locked and Down, a purple Discard on each row, row rules, "Page n of m" with Back and Next, a blue "How it works" |
| `SkillBankDiscardGump.cs` | The Danger banner holds the question, typed word kept, purple "Discard points" and red CANCEL; right-click goes back to the bank |
| `MasteryGump.cs` | Columns that no longer overlap, labelled paging, an empty-state line, the footnote above the footer rule |
| `GuideWindow.cs`, `WelcomeGuide.cs` | The topic list is blue ovals (the chosen one pressed, a gold label), "Next topic" and the Action buttons are blue ovals, Close is a blue oval, topic titles that fit; chapter tabs unchanged |
| `CampTravelService.cs`, `TravelWarningService.cs` | Camp list (Select ovals, a Danger [HOT ZONE] tag, Close), camp confirm and Hot Zone warning as dialogs (Danger banner, tick box, OKAY and CANCEL); declining says "You decide not to travel." in red on all three |
| `ShardRulesCommands.cs` | The result of a rules command is a Done or Danger banner |

## Verification

- **Shard tests:** 993 passed, 0 failed (`Invoke-AgentVerification -Suite Shard`, run `20261008T015805907Z-9b18ce`). New: `StyleGuideTests` (27 tests: no `fontStyle`, italics or underline; bold only in the progress bar; no `AddAlphaRegion`; none of the retired art `4005/4007/2443/2444` or raw `620xx` ids outside `GumpStyle`; a colour only from `GumpStyle` (the chapter-tab ink `#202020/#000000` and the label emboss `#101010` excepted); distinct colours, none dimmer than `#999999`; the window classes never exceed 640x500 (the camp list at its limit of eight camps, the Hot Zone confirm, the longest status text); every button label fits its oval; every guide topic title fits the topic oval; banner words and kinds; the estimator). `StatusWindowsViewTests` updated for the new kinds and the 280 px minimum. `GumpStyleArtFilesTests` checks the blue and purple ovals in five widths and the radio ovals at 22 px.
- **No ModernUO change** in this pass, so the UOContent suite was not rerun and no engine rebuild is needed.
- **Real client, 2026-10-07:** every window (the 11 shard windows, 15 states) photographed in a real ClassicUO client on a disposable host (`work/qol/setup.ps1`, now removed) before and after the restyle, and the pairs sent to the owner. They are kept, with the before and after pictures, under `work/gump-style-pass/` (`restyle-before/`, `restyle-after/`, `pairs/`; scratch, not source of truth). The first set of "after" pictures of the four travel dialogs showed a leftover Skill Bank behind them (closing the Discard dialog by right-click re-opens the bank by design); `restyle_shots.py` now closes it, and the four were retaken on a clean screen.
- **Clicks on oval labels** (label is drawn over art, the art is the button): in the real client a click on the middle of the "Hot Zones" topic oval switched the guide to that topic (the oval pressed, the label gold) and a click on the "Close" oval closed the window.
- **Cleanup:** client, `admin` Navrey session, dev server (`-NoSave`), the `qol` disposable host and the `Gwen` client profile removed. The dev distribution and its saves were not touched.

## Named limits (unchanged from the guide, section 7)

- Esc does not close a server window in the client; right-click does (button 0), and is safe on every window (the Discard dialog returns to the bank).
- A radio oval's label is not clickable (only art can be a button); the oval is.
- The camp confirm for a camp outside a Hot Zone leaves a gap of about 36 px under its body on the usual three lines; its height is fixed at 240 because the same text can run to four.
- The restyle changes no wording except the footer hints and the cancel messages; no player-facing rule changed, so the root `README.md` is unchanged.

## Shipping

- No flag. Deployed to the dev host 2026-10-07 (`Deploy-Alpha1Baseline.ps1`; the deployed DLL is the one the tests ran against, and the ModernUO pin moved to `067802c3c`). The server started clean and was stopped again.
- The client art is already in place: `ClassicUO/bin/dist/Data/Gumps/` holds all 27 `.gump` files (`50000-50002` buff icons, `62010-62029` blue and purple ovals, `62030/62031` chosen radio, `62040/62041` stone radio), copied from `ShardContent/data/client/gumps/`, and `cuo.dll` is the build with the lying pose. A player on an older client dist would see missing buttons, so the art goes with the client whenever players are given a new dist.
- Everything is committed and pushed: ShardContent `859c31c` (the pass), with the guide, the art in `data/client/`, `tools/gump-art/` and `tests/scenarios/gump-style/`.
