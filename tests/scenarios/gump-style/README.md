# Gump style sampler

Test-only tooling behind `docs/Gump-Style-Guide.md`. Nothing here ships.

- `../alpha3-tools/GumpScriptProbe.cs` and the command `[TestOnlyGump <player-serial> <script>` (loaded on a disposable host with the TestOnlyProbe) draw a window from a `.gs` text file with no rebuild. The scripts folder is `work/qol/gump-scripts` (override with the environment variable `QOL_GUMP_SCRIPTS`); copy the `.gs` files there. The syntax is at the top of `GumpScriptProbe.cs`.
- `gump_show.ps1 -Script a,b -Serial 0x...` sends each script to a real-client character (Start-PlayerClient.ps1) and takes a screenshot of each.
- `gen_sheets.py` regenerates the art sheets (`bg*.gs`, `arts_*.gs`); `gumpscan.py` lists the size of every gump art id from `gumpartLegacyMUL.uop`.
- The client remembers each gump type's position, so every sampler window opens where the first one did; delete the client profile (`ClassicUO/bin/dist/Data/Profiles/<name>`) to move it.
- `gen_windows.py` writes `ref.gs`, `mock*.gs`, `buttons.gs` and `radioCompare.gs`; with `fonts.gs` they are the windows pictured in the guide. They use the shard's button art, blue ovals 62010-62019, purple ovals 62020-62029, amber ovals 62030-62039 and stone ovals 62040-62049 (made by `tools/gump-art/make_window_buttons.py`; copy `data/client/gumps/62*.gump` into the client's `Data/Gumps` before drawing them).
