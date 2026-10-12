# Cosmetic catalog gallery (test-only)

Nothing here ships. `DecorProbe.cs` adds the staff command `[TestOnlyDecor <player-serial> <layout-name|clear>` to a **disposable host**. It lays the items of a catalog gallery page on the ground around that player so the real ClassicUO client can photograph them. Layouts are made by `ShardContent/tools/cosmetic-catalog/galleries.py plan` into `work/cosmetics/layouts/` (override with `COSMETIC_LAYOUTS`).

## Run it

```powershell
. .\.claude\scripts\Use-Toolchain.ps1
& .\.claude\scripts\New-DisposableHost.ps1 -Name decor
$h = "$BRWorkspace\work\hosts\decor"
& $BRDotnet build .\ShardContent\tests\scenarios\cosmetic-catalog\DecorProbe.csproj -c Release "-p:ServerHostPath=$h"
Copy-Item .\ShardContent\tests\scenarios\cosmetic-catalog\bin\Release\net10.0\DecorProbe.dll "$h\Assemblies\"
# add "DecorProbe.dll" to $h\Data\assemblies.json (after BritanniaRenaissance.Content.dll)
& .\.claude\scripts\New-TestCharacter.ps1 -HostName decor -Name DecorCam -Profession 8
& .\.claude\scripts\Stop-NavreySession.ps1 -Name DecorCam
& .\.claude\scripts\Start-PlayerClient.ps1 -Name DecorCam
```

Then stage the camera (the staff session is `admin`; the serial is the one `New-TestCharacter` printed):

* `[set Location "(5632, 2188, 0)"` on the camera character (via `staff_command.staff_target`), a flat empty patch of Felucca found with `tools/cosmetic-catalog/flatspots.py`; move `admin` away from it (`[go 5600 2150 0`).
* `[GlobalLight 0` (daylight) and `[AutoSave false` (no "world is saving" text in shots).
* Close the paperdoll (`Send-PlayerClientInput.ps1 -Name DecorCam -X 240 -Y 330 -Right`).

Run the pages and write the legend:

```powershell
& $BRPython .\ShardContent\tools\cosmetic-catalog\galleries.py plan
& .\ShardContent\tools\cosmetic-catalog\Run-GalleryShots.ps1 -Serial 0x0000A705          # all pages, or -Category FIG / -Pages FIG-01,FIG-02; -Category GS for the gold-sink showroom pages, planned by sinkplan.py showroom; -Category CN-FIG for the neutral figurines
& $BRPython .\ShardContent\tools\cosmetic-catalog\galleries.py index
```

Clean up: `Stop-PlayerClient.ps1`, `Stop-NavreySession.ps1 -Name admin`, `Stop-DevServer.ps1 -NoSave`, `Remove-DisposableHost.ps1 -Name decor`.

## Notes

* Felucca runs the Desolation season, so the client hides foliage tiles; the screenshots show exactly that.
* The client crop (`15,58 - 918,603` of a 1296x839 shot) and the screen position of the player's tile are constants in `galleries.py`; re-measure them if the client window layout changes.
* The runner takes over the screen while it works (about five minutes for 74 pages).
