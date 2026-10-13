# Client defaults: the list

The owner's running list of what the player client should do out of the box (started 2026-10-11). Items 1 to 6 were built the same day on his "complete all the quality of life notes"; each was checked in the real ClassicUO client with a brand-new profile and the pictures were shown to him.

## How a default reaches a player

- **A new profile copies `Data/Profiles/default.json`.** In the source tree that file is `ShardContent/data/client/default-profile.json`. It is a ClassicUO `Profile` written with snake_case names, so any profile option can be a default with one line of JSON, and no client rebuild is needed. The file is copied by hand into `ClassicUO/bin/dist/Data/Profiles/default.json`; `Get-ShardStatus.ps1` shows whether source and dist differ.
- **The key names are not what they look like.** The client splits an acronym letter by letter: the option `ShowMobilesHP` is `show_mobiles_h_p`, not `show_mobiles_hp`. A misspelt key is silently ignored. `tests/ClientDefaultsTests.cs` pins every name and value; to find a name, read it from a real `profile.json` under `ClassicUO/bin/dist/Data/Profiles/<account>/<server>/<character>/`.
- **Only new profiles.** A player who already has a profile keeps their own settings; nothing here reaches them unless they change it in Options.
- **Client text** (`ShardContent/data/client/Clilocs.txt`, copied to `Data/Client/Clilocs.txt`) can add or correct any client string by number; the client reads it at start.
- **A client rebuild** (`cuo.dll`, see `CLAUDE.md`) is needed only for what the profile and text cannot express.

## The list

1. **Health indicators in bar form, on by default** (owner, 2026-10-11). `show_mobiles_h_p` true, `mobile_h_p_type` 1 (0 a percentage, 1 a bar, 2 both), `mobile_h_p_show_when` 0 (always). Done: a bar shows under the character and under a monster beside them from the first frame.

2. **Close the health bar of a dead mobile by default** (found while looking at item 1, with the dead-health-bar bug). `close_health_bar_type` 2 (0 never, 1 when the mobile no longer exists, 2 when it dies). Done, in the defaults.

3. **Circle of transparency, on by default** (owner, 2026-10-11). `use_circle_of_transparency` true, with the client's own `circle_of_transparency_type` 0 (the normal circle) and radius (half the maximum). Done: standing behind a wall, the wall next to the character fades. Open and left as one number: type 1 imitates the original client's look; say if you would rather have it.

4. **Open corpses automatically, but not while hidden** (owner, 2026-10-11). `auto_open_corpses` true and `corpse_open_options` 3 (the client's own default, which skips while a target cursor is up and while hidden); range 2 tiles and "skip empty corpses" off, as the client has them. Done: a monster killed beside a new character opened its corpse by itself. Not checked: auto-opening a corpse the player may not loot (another player's protected kill, a blue player's corpse) for a criminal flag or repeated messages, and that hiding stops it (the second is the client's own rule).

5. **Anchored windows close with a plain right-click** (found with the dead-health-bar bug). `hold_down_key_alt_to_close_anchored` false. See the bug in `To-Do-List.md`: in the client, a window that has snapped to another one ignores a plain right-click unless Alt is held, and that option is on by default.

6. **The buff tooltip no longer flickers** (client fix, not a default; see below).

7. **Walking is running, but not while hidden** (owner, 2026-10-12, "client defaults pass"). `always_run` true, `always_run_unless_hidden` true. A new player no longer has to hold Shift to cross a town; a hidden player still walks, so a run does not give them away. Done in the defaults; checked in a new profile's `profile.json` and the Options window.

8. **Walking into a door opens it** (same pass). `auto_open_doors` true (`smooth_doors` is left as the client has it). Done in the defaults.

Looked at and not changed: font and window scale by resolution. The client has no profile option for a whole-UI scale (only the container scale and the tooltip zoom), so it cannot be a default without a client change; the same pass saw nothing else worth changing.

## Not in a new profile's reach: the owner's own settings

Items 1 to 5 reach only new profiles, so on 2026-10-11, on his "yes", his own profiles were edited with the client closed: `Administrator`, `bris` and `bris2` (health bars as bars, circle of transparency, auto-open corpses, a plain right-click closes anchored windows, close the health bar of a dead mobile; `bris2` already had the first three on). The originals are in `work/client-defaults/profiles-backup-20261011/`. His other test profiles (`qwer`, `zxc` and so on) were left alone. To change one by hand: "Show mobiles' HP" and the bar type, "Hold ALT key to close anchored gumps" and the "Close health bars when" drop-down in Options.

## Client changes made with these (uncommitted in the ClassicUO repo, installed in `ClassicUO/bin/dist`)

- **`Tooltip.SetText` keeps an on-screen tooltip showing while its text is refreshed.** A buff icon with a countdown rewrites its tooltip ("Time left") every second, and every rewrite restarted the 250 ms display delay, so the tooltip vanished for a quarter of every second. Reproduced in the real client before the fix (a frame with the mouse on the icon and no tooltip, the next with it) and checked after (four of fourteen dithered frames viewed, all showing the tooltip and the time counting down). The change is in `ClassicUO/src/ClassicUO.Client/Game/UI/Tooltip.cs`. `cuo.dll` and `cuo.pdb` were rebuilt (NativeAOT publish) and copied into `bin/dist`; the old pair is in `work/client-defaults/dist-cuo-backup-20261011/`.
- **Camp-secure text.** Client text 500621, "The camp is now secure.", now continues "To log off safely, put your Bedroll down by the fire, double-click it to unroll it, double-click it again and choose Continue." (`Clilocs.txt`; the first wording, one double-click, was wrong: the first unrolls the Bedroll and only the second offers the logout, corrected the same day). The safe logout is the stock Bedroll one; the line shows for each player at a fire when their own 30 seconds are up.
