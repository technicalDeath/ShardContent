param([string]$OutDir = '', [switch]$DryRun)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\work\gump-style-pass')).Path

# window class -> (screen x, screen y, width). The client's game area starts 8 px right of and 32 px below the screenshot's corner.
$classes = @{
    Large  = @(48, 61, 640, 500)
    Medium = @(88, 91, 480, 0)
    Dialog = @(108, 101, 440, 0)
}

# output name, shot name, class, known height (0 = find it)
$windows = @(
    @('guide-start-here',               'welcome',            'Large', 500),
    @('guide-rules-fighting',           'welcome-fighting',   'Large', 500),
    @('guide-commands',                 'welcome-commands',   'Large', 500),
    @('skill-training-speeds',          'skillclasses',       'Large', 500),
    @('skill-bank',                     'skillbank',          'Large', 500),
    @('mastery',                        'mastery',            'Large', 500),
    @('criminal-intent-off',            'intent-off',         'Medium', 0),
    @('criminal-intent-on',             'intent-on',          'Medium', 0),
    @('hot-zone-travel-warning-setting', 'travelwarning',     'Medium', 0),
    @('backpack-ward',                  'ward',               'Medium', 0),
    @('camp-travel-list',               'camplist',           'Medium', 316),
    @('skill-bank-discard',             'discard',            'Dialog', 320),
    @('camp-travel-confirm',            'campconfirm',        'Dialog', 240),
    @('camp-travel-confirm-hot-zone',   'campconfirmhot',     'Dialog', 312),
    @('hot-zone-travel-warning',        'hotzone',            'Dialog', 270)
)

function Find-Bottom($bmp, $x, $top) {
    # Down the column just inside the frame (nothing is drawn there): the first bright pixel is the stone border.
    for ($y = $top + 40; $y -lt $bmp.Height; $y++) {
        $c = $bmp.GetPixel($x + 16, $y)
        if ([Math]::Max($c.R, [Math]::Max($c.G, $c.B)) -gt 70) { return $y + 10 }
    }
    return -1
}

foreach ($w in $windows) {
    $name, $shot, $class, $known = $w
    $x, $y, $width, $_h = $classes[$class]
    $bmp = [System.Drawing.Bitmap]::FromFile((Join-Path $root "restyle-after\$shot.png"))
    $found = Find-Bottom $bmp $x $y
    $height = $found - $y
    $note = if ($known -gt 0) { if ($height -eq $known) { 'matches' } else { "MISMATCH, code says $known" } } else { 'detected' }
    '{0,-34} {1,-6} x={2} y={3} w={4} h={5}  {6}' -f $name, $class, $x, $y, $width, $height, $note
    if (-not $DryRun) {
        if ($known -gt 0) { $height = $known }
        $crop = New-Object System.Drawing.Bitmap ($width, $height)
        $g = [System.Drawing.Graphics]::FromImage($crop)
        $g.DrawImage($bmp, (New-Object System.Drawing.Rectangle (0, 0, $width, $height)), (New-Object System.Drawing.Rectangle ($x, $y, $width, $height)), [System.Drawing.GraphicsUnit]::Pixel)
        $g.Dispose()
        $crop.Save((Join-Path $OutDir "$name.png"), [System.Drawing.Imaging.ImageFormat]::Png)
        $crop.Dispose()
    }
    $bmp.Dispose()
}
