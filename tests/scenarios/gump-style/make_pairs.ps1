$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\work\gump-style-pass")).Path
$out = Join-Path $root 'pairs'
New-Item -ItemType Directory -Force $out | Out-Null

# Crop rectangles (x, y, w, h) in the screenshot: the large windows, and the smaller dialogs.
$large = @(40, 55, 660, 515)
$small = @(50, 85, 540, 365)
$windows = [ordered]@{
    'welcome' = $large; 'welcome-fighting' = $large; 'welcome-commands' = $large; 'skillclasses' = $large
    'skillbank' = $large; 'mastery' = $large
    'intent-off' = $small; 'intent-on' = $small; 'travelwarning' = $small; 'ward' = $small
    'discard' = $small; 'camplist' = $small; 'campconfirm' = $small; 'campconfirmhot' = $small; 'hotzone' = $small
}

$labelFont = New-Object System.Drawing.Font('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)
$white = [System.Drawing.Brushes]::White
$bg = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(24, 24, 24))
$header = 30
$gap = 12

foreach ($name in $windows.Keys) {
    $r = $windows[$name]
    $rect = New-Object System.Drawing.Rectangle ($r[0], $r[1], $r[2], $r[3])
    $width = 2 * $r[2] + $gap
    $height = $r[3] + $header
    $canvas = New-Object System.Drawing.Bitmap ($width, $height)
    $g = [System.Drawing.Graphics]::FromImage($canvas)
    $g.FillRectangle($bg, 0, 0, $width, $height)
    $i = 0
    foreach ($label in 'Before', 'After') {
        $src = [System.Drawing.Bitmap]::FromFile((Join-Path $root "restyle-$($label.ToLower())\$name.png"))
        $x = $i * ($r[2] + $gap)
        $g.DrawString($label, $labelFont, $white, $x + 6, 4)
        $g.DrawImage($src, (New-Object System.Drawing.Rectangle ($x, $header, $r[2], $r[3])), $rect, [System.Drawing.GraphicsUnit]::Pixel)
        $src.Dispose()
        $i++
    }
    $g.Dispose()
    $canvas.Save((Join-Path $out "$name.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $canvas.Dispose()
    Write-Host "pair $name"
}
