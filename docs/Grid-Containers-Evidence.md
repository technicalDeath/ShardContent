# Grid containers (Grid Lite): evidence

**Built 2026-10-14 in the ClassicUO fork** (`src/ClassicUO.Client/Game/UI/Gumps/ContainerGump.Grid.cs`, small hooks in `ContainerGump.cs`, `ItemGump.cs`, `PacketHandlers.cs`, `OptionsGump.cs`, `Profile.cs`). Client only: no server, flag or engine change. Owner signed off the plan the same day ("build it, backpack included"), chose the extras (lock, auto-sort, sort orders, search "only show", corpse position) and then left the build, test and polish, and the calls, to the assistant.

## What it is

The container window has a second look. With `Profile.ContainerStyle == 1` a backpack, bag or corpse opens as a dark window with a brass frame: a header (name, item count, search box, buttons Mark/Hide, Sort, Auto, order), a scrolling grid of 48 px cells and a footer with a hint and a resize grip. It is the same `ContainerGump` class in a grid mode (a partial class file), so every place that looks a container up by serial (macros, the potion bar's silent pack open, item destroy, the big-pack switch) keeps working. `ContainerStyle` 0 is the unchanged classic window.

Idea and feature list follow TazUO's grid containers (reviewed on GitHub first); no TazUO code is copied. Cell numbers are the client's; they are never sent to the server.

## Features (built)

| Feature | How it works |
| --- | --- |
| Grid of cells, counts | One `GridSlot` background and one `GridItemGump` (the whole cell is the hit area, art centred, oversized art scaled down) per cell; a count label on stacks. |
| Tooltips, hover | The shard's item tooltip (`SetTooltip(serial)`); the hovered item tints. |
| Drag and drop | Existing `ItemHold` / `GameActions.DropItem` path. A drop remembers the cell it was aimed at; dropping on an occupied cell swaps; dropping on a bag tile puts it inside. |
| Remembered cells | `GridContainers.txt` in the character's profile folder (`D` defaults, `P` corpse position, `C` per container, `S` per item cell and lock). Saved at most every 2 s while changed and on close. A corpse keeps nothing on disk except its position and size. |
| Scroll, resize | `ScrollArea`; the grip snaps the window to whole cells (minimum 4 x 3); the last size is the default for the next container; a corpse has its own. |
| Sort, Auto, order | Sort now; Auto re-sorts on every change; the third button cycles Type (graphic, hue), Name, Wear (layer). |
| Lock | Ctrl-click an item: gold padlock and frame; Sort and Auto leave it in its cell. |
| Search | Name and tooltip text. Mark (default): matches get a gold frame, the rest dim. Hide: only matches, packed to the top. |
| Corpse | Own size, and opens where the last corpse window was closed; the docking beside the game window is the stock `ShardLayout.Dock`. |
| Switch buttons | A **Classic** button in the grid's header and a **Grid** button beside the size diamond on the classic backpack (classic-with-grid-button.png). Either one sets the style, saves the profile and reopens that container in the new style in the same place. |
| Option | Options > Containers > Container style (Original / Grid). Default Grid for a **new** profile (`default-profile.json` `container_style` 1); an existing profile keeps the classic look. |

## Calls the assistant made (owner away)

1. **Lock gesture is Ctrl-click, not Alt-click.** Alt-click raised the server's item context menu (the shard's About entry) on the item.
2. **New profiles default to Grid; existing profiles keep Original.** Reverse: `container_style` 0 in `ShardContent/data/client/default-profile.json` and `ClassicUO/bin/dist/Data/Profiles/default.json`.
3. **Grid Loot (the old corpse-only window) still wins when a player chose "Grid loot only"**; the new corpse grid is used otherwise.
4. **Left out, as listed to the owner:** bands, gear comparison, highlight rules, auto-loot marking, multi-select move, list view, rename, minimize, anchoring. No minimize in grid mode: the macro that toggles the backpack hides the window instead.
5. **Cell size 48, window minimum 4 x 3 cells, footer hint always shown.**
6. **Text:** the client strings are literal English in the client (the shard keeps its own client text in `Clilocs.txt`; these are not clilocs).

## Verification (real ClassicUO client, disposable host, test character TsSword)

Screenshots are in `docs/grid-containers/`; all the others are under `work/player-client/TsSword/shots/` (scratch). Navrey was not needed: nothing here is server state.

| # | Case | Result |
| --- | --- | --- |
| 1 | Options > Containers shows Container style; Grid opens the pack as a grid | pass (`options-page.png`) |
| 2 | Pack of 27 items: cells, counts, tooltips, hover tint | pass (`locks-bag-tooltip.png`) |
| 3 | Search "potion", Mark mode: matches framed, rest dimmed; Hide mode: matches packed to the top | pass (`search-mark.png`; the Hide shot is in scratch) |
| 4 | Ctrl-click locks (padlock, frame); locks survive Sort and a client restart | pass |
| 5 | Drag a potion into an empty cell: it stays there; closing and reopening keeps it | pass (after fixing a pending-drop bug found here) |
| 6 | Sort groups by type; Auto on; order Name; settings survive a restart | pass |
| 7 | Resize: drag the grip, snaps to 4 x 3 with a scrollbar, then larger | pass (the grip was redrawn inside the frame after the first run missed it) |
| 8 | Corpse (ogre lord) opens as a grid with its own size; loot dragged from the corpse into an empty pack cell lands there | pass (`corpse-and-pack.png`) |
| 9 | Nested bag opens as a grid; drag into its cell; drop one on the bag tile | pass |
| 10 | Original style: the classic pack with the shard's size switch | pass, no regression |
| 11 | A brand-new profile (profile.json removed, client restarted) gets `container_style` 1 and a grid | pass |
| 12 | Unit tests: `ClientDefaultsTests` pins `container_style` | see the commit |

| 13 | Classic button on the grid, Grid button on the classic pack: both ways, window stays in place | pass (a first build crashed on the Classic click, a null state in the grid's update; fixed and retested) |

## Bugs found and fixed during the playtest

- Cell backgrounds drew over the item art (the no-atlas pass is drawn after the atlas pass): backgrounds moved to the atlas pass, frames and padlocks stay on top.
- Only the opaque pixels of a small bottle were clickable: the whole cell is now the target.
- The resize handle sat outside the frame and was hard to hit: a drawn grip inside a footer strip.
- A drop aimed at a cell was forgotten when a refresh ran while the item was in the hand: pending drops now live until the item returns.
- Long tooltips ran off the screen: wrapped at 230 px.
- Alt-click opened the item context menu: lock moved to Ctrl-click, and the pending single click is cancelled.

## Named limits

- Layout is saved per character in the profile folder: a different computer or a deleted profile starts fresh.
- Locks and cells of items that left the container are forgotten once the client has seen them elsewhere; an item the client has not heard of yet keeps its cell.
- Mark/Hide, Sort order and Auto are per container (saved); the search text is not saved.
- The hit test inside a scrolled window relies on `ScrollArea` offsets; checked with a short list scrolled only in the 4 x 3 window.
- Not checked in the real client: a vendor's buy window, a trade window, a house chest locked down by someone else, a very long container (hundreds of items) for performance.

## Rebuilding the client

As in `CLAUDE.md`: `dotnet publish ClassicUO\src\ClassicUO.Client -c Release -p:NativeLib=Shared -p:OutputType=Library -r win-x64 -o <scratch>`, back up and copy `cuo.dll` and `cuo.pdb` into `ClassicUO/bin/dist` (the previous pair is in `work/client-dist-backups/20261014-before-grid`), and copy `default-profile.json` to `Data/Profiles/default.json`.

## Potions do not stack (owner ruling, 2026-10-14)

Potions are one item each, as in UOR: the engine stacks them only when `Core.ML` is on (`BasePotion.cs:53`). A keg weighs 20 + 0.8 per potion (100 stones full, the same as 100 loose or stacked potions), so stacking would not make kegs lighter. Asked whether to stack to 20 or to group identical items in the grid, the owner chose to leave potions as they are. Nothing is planned or built for either idea.

## Bug fixed 2026-10-15: no hover, tooltip or drag once the list is scrolled
Owner report: scrolling the grid down with the scrollbar made every item stop highlighting, show no tooltip and refuse to be dragged out; all worked again at the very top. Cause: `Control.HitTest` first tests the pointer against a child's bounds with the scroll offset allowed for, then calls `Contains` with coordinates that are not corrected for it; `GridItemGump.Contains` did its own bounds check (`x < CellSize && y < CellSize`), so once the list was scrolled past one cell height the check failed for every cell. Fix (`ContainerGump.Grid.cs`): `GridItemGump.Contains` returns `!IsDisposed` (the bounds were already tested). Verified in the real client on a disposable host with a Pure Mage whose pack was set to the 3-row minimum (24 items, so it scrolls): the unfixed build showed no highlight or tooltip on a scrolled cell, the fixed build highlighted it and showed "Refresh Potion, Newbied: Kept When You Die, Weight: 1 Stone", and dragging an item from the scrolled bag to the ground worked (24 to 23 items). Client unit suite 250 pass. Not committed; `cuo.dll` for the dist folder is built at `work/cuo-publish-gridfix/` and not yet installed because the owner's two admin clients were running from `ClassicUO/bin/dist` (the farm's own bots run Navrey's build, not dist; the bot-farm operator confirmed no conflict).
Tooling: `Start-PlayerClient.ps1` gained `-Port` (a disposable host beside the farm, which holds 2593) and `-DistPath` (run a copy of the client folder with a new `cuo.dll` before installing it).

**Installed 2026-10-15:** the fixed cuo.dll and cuo.pdb are in ClassicUO/bin/dist (hash 25F34231D7BB). The owner's two admin clients were still running from dist, so the old files were renamed to cuo.dll.replaced-<time> and cuo.pdb.replaced-<time> (Windows lets a loaded DLL be renamed) and the new ones copied in; running clients keep the old copy until restarted. The two .replaced-* files can be deleted once those clients are closed. Backup of the previous files: work/help-gumps/backup/cuo3.
