# Top bar (menu bar) revamp

Signed off and activated 2026-10-12 by the owner ("Agreed", then "Activate"). Flag `featureFlags.menuBar` is ON; deployed to dev the same day; uncommitted.

## Design (owner-agreed)
- Horizontal strip, brass style, minimise arrow kept.
- Removed: Chat (the server disables it), Info (no handler in the client), Debug and Connection (developer windows; reach them with `-debug` and `-netstats`), UO Store, Global Chat.
- Buttons: Character, Backpack, Skills, Journal, Map, Camp, Guild chat, About, Options. Map opens the mini-map, the next click opens the world map. About opens `[SkillGuide`; until `helpGumps` is on, the button is the stock Help.
- The Skill Guide window has a **Page staff** button (stock help request).
- Server-driven: extended command 0xA8. Server to client: `0xBF len(2) 0x00A8 mask(2)`. Bit 15 shard bar, bit 1 Camp, bit 2 Guild chat, bit 3 About. The client asks (same command, empty) when it builds the bar and the server also pushes at login. Until a mask arrives the client keeps the stock bar. The mask is reset when the login scene loads.
- Debug/Connection checkboxes in Options were replaced by client commands `-debug` and `-netstats` (smaller change, same effect).

## Also in this change: blank hotbar (called "item shortcuts" in the client) by default
- `default-profile.json` gets `counter_bar_enabled: true`; `GameScene.OfferBlankHotbar` opens one empty counter bar beside the game window once per new profile (`Profile.CounterBarOffered`), with the stock hint "Drop an item here to make an item shortcut". It is an item-counter bar, not a spell or macro bar.

## Evidence
- Unit tests `MenuBarTests` (masks, packet bytes, flag on in shipped rules) and `ClientDefaultsTests`; full shard suite 1279 passed (run 20261012T135923613Z-7532c3).
- Real client (ClassicUO, disposable host): bar with every button; About opened the Skill Guide with Page staff; Skill Bank opened its window; Guild chat opened the `[Guild]:` prompt; Map opened the world map on the second click; Skills and Options opened their windows; blank hotbar (called "item shortcuts" in the client) with its hint. Screenshots in `work/player-client/HelpAlpha/shots/` (bar4, btn-about, btn-skillbank, btn-guild, after-close, skills-options, hotbar1) and sent to the owner.
- Not exercised in the real client: Camp button (it only sends `[CampTravel`).
- Deploy: `Deploy-Alpha1Baseline.ps1` ran clean; the dev server booted with no errors; stopped after a save.

## Client files
`TopBarGump.cs`, `PacketHandlers.cs`, `OutgoingPackets.cs` (`Send_MenuBarRequest`), `CommandManager.cs` (`-netstats`), `LoginScene.cs` (reset), `Profile.cs`, `GameScene.cs`; `cuo.dll` republished into `ClassicUO/bin/dist` (backup of the previous one: `work/cuo-before-menubar.dll`), `Data/Profiles/default.json` recopied.

## Change 2026-10-12
The Skill Bank button was removed at the owner's request (the window stays reachable with `[SkillBank`). Bar: Character, Backpack, Skills, Journal, Map, Camp, Guild chat, About, Options.
