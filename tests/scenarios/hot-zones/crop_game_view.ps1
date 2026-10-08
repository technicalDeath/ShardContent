# Crops real-client screenshots to the game view (inside the gold border; no title bar, menu bar or empty window space).
#   & .\crop_game_view.ps1 -OutDir <folder> -Shot @('<name>=<screenshot.png>', ...)   (from a pwsh session: an array does not bind after -File)
# Used for the Knocked Out and Execute pictures in website/reference/in-world (taken by knocked_out_lying_realclient.py).
param(
    [Parameter(Mandatory)][string]$OutDir,
    [Parameter(Mandatory)][string[]]$Shot
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

# The border measured in a 1296 x 839 client window: gold at x 14-16 and 916-918, y 602-604; the menu bar covers the top edge up to y 57.
$x, $y, $w, $h = 17, 59, 899, 543
New-Item -ItemType Directory -Force $OutDir | Out-Null
foreach ($pair in $Shot) {
    $name, $path = $pair -split '=', 2
    $src = [System.Drawing.Bitmap]::FromFile((Resolve-Path $path).Path)
    if ($src.Width -ne 1296 -or $src.Height -ne 839) { throw "$path is $($src.Width) x $($src.Height); the crop is measured for 1296 x 839" }
    $crop = New-Object System.Drawing.Bitmap ($w, $h)
    $g = [System.Drawing.Graphics]::FromImage($crop)
    $g.DrawImage($src, (New-Object System.Drawing.Rectangle (0, 0, $w, $h)), (New-Object System.Drawing.Rectangle ($x, $y, $w, $h)), [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    $crop.Save((Join-Path (Resolve-Path $OutDir).Path "$name.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $crop.Dispose()
    $src.Dispose()
    "{0}  <-  {1}" -f $name, (Split-Path $path -Leaf)
}
