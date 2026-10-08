param([string]$Out = '')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$dir = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\work\blue-fire\shots')).Path
if (-not $Out) { $Out = Join-Path $dir 'sheet-closeup.png' }

# grid as lit by TestOnlyFires (4 to a row, 3 tiles apart): fire (c, r) is drawn at (290 + 132c, 148 + 132r) in the 1296 x 839 shot
$hues = 0, 2746, 1927, 1928, 1266, 1265, 3, 93, 98, 2790, 2796, 1366, 1282, 1264, 1195, 2747
$names = @{ 0 = 'stock (unhued)'; 1266 = 'ColdWeap6'; 1265 = 'ColdWeap5'; 2790 = 'Royal Blue'; 2796 = 'Frostbite'; 1366 = 'ColdWear6'; 1264 = 'ColdWeap4'; 1195 = 'Frostwood' }
$zoom = 3
$cw = 48; $ch = 48
$cellW = 2 * $cw * $zoom + 18
$cellH = $ch * $zoom + 26
$sheetW = 4 * $cellW + 10
$sheetH = 4 * $cellH + 10

$day = [System.Drawing.Bitmap]::FromFile((Join-Path $dir 'sheet-day.png'))
$night = [System.Drawing.Bitmap]::FromFile((Join-Path $dir 'sheet-night.png'))
$sheet = [System.Drawing.Bitmap]::new($sheetW, $sheetH)
$g = [System.Drawing.Graphics]::FromImage($sheet)
$g.Clear([System.Drawing.Color]::FromArgb(30, 30, 30))
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
$font = New-Object System.Drawing.Font('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
$small = New-Object System.Drawing.Font('Segoe UI', 9)

for ($k = 0; $k -lt 16; $k++) {
    $c = $k % 4; $r = [Math]::Floor($k / 4)
    $fx = 466 + 44 * (2 * $c - 3); $fy = 324 + 44 * (2 * $r - 3)
    $sx = [int]($fx - $cw / 2); $sy = [int]($fy - 30)
    $src = [System.Drawing.Rectangle]::new($sx, $sy, $cw, $ch)
    $x0 = 5 + $c * $cellW; $y0 = 5 + $r * $cellH
    $g.DrawImage($day, ([System.Drawing.Rectangle]::new($x0, $y0 + 22, $cw * $zoom, $ch * $zoom)), $src, [System.Drawing.GraphicsUnit]::Pixel)
    $g.DrawImage($night, ([System.Drawing.Rectangle]::new($x0 + $cw * $zoom + 6, $y0 + 22, $cw * $zoom, $ch * $zoom)), $src, [System.Drawing.GraphicsUnit]::Pixel)
    $label = [string]$hues[$k]
    if ($names.ContainsKey($hues[$k])) { $label += '  ' + $names[$hues[$k]] }
    $g.DrawString($label, $font, [System.Drawing.Brushes]::White, $x0, $y0)
}
$g.DrawString('day | night', $small, [System.Drawing.Brushes]::Gray, 8, $sheetH - 16)
$g.Dispose()
$sheet.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$sheet.Dispose(); $day.Dispose(); $night.Dispose()
"$Out  ${sheetW}x${sheetH}"
