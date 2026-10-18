<#
.SYNOPSIS
Photographs the cosmetic reward catalog in the real ClassicUO client.

.DESCRIPTION
Needs: a disposable host (New-DisposableHost.ps1 -Name decor) carrying DecorProbe.dll (see README in
tests/scenarios/cosmetic-catalog), already running, with the camera character logged in through the REAL client
(Start-PlayerClient.ps1 -Name DecorCam) and an `admin` Navrey staff session. The camera character stands on the flat
Felucca patch (5632,2188,0). For each page layout under work/cosmetics/layouts (made by galleries.py plan), this script has
admin place the page's items around the camera character, takes a client screenshot, crops it to the game view and numbers
the items, and saves the result under ShardContent/docs/cosmetic-rewards/client-shots/.

Takes over the screen while it runs (the client window is brought to the front for every shot).

.EXAMPLE
& .\ShardContent\tools\cosmetic-catalog\Run-GalleryShots.ps1 -Serial 0x0000A705 -Pages FIG-01,FIG-02
& .\ShardContent\tools\cosmetic-catalog\Run-GalleryShots.ps1 -Serial 0x0000A705 -Category FIG
#>
param(
    [Parameter(Mandatory)] [string] $Serial,
    [string[]] $Pages = @(),
    [string] $Category = '',
    [string] $Camera = 'DecorCam',
    [int] $SettleMs = 1800
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\..\..\.claude\scripts\Use-Toolchain.ps1')
$ws = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$layouts = Join-Path $ws 'work\cosmetics\layouts'
$out = Join-Path $ws 'ShardContent\docs\cosmetic-rewards\client-shots'
New-Item -ItemType Directory -Force -Path $out | Out-Null

if ($Pages.Count -eq 0) {
    $filter = if ($Category) { "$Category-*.json" } else { '*.json' }
    $Pages = Get-ChildItem $layouts -Filter $filter | Where-Object { $_.Name -notlike '*.meta.json' } |
        ForEach-Object { $_.BaseName } | Sort-Object
}

$navrey = Join-Path $ws '.claude\scripts\navrey_session.py'
$shot = Join-Path $ws '.claude\scripts\Get-PlayerClientShot.ps1'
$gal = Join-Path $ws 'ShardContent\tools\cosmetic-catalog\galleries.py'

function Say([string] $text) {
    & $BRPython $navrey admin "say $text" | Out-Null
}

Say '[GlobalLight 0'
foreach ($page in $Pages) {
    Say '[GlobalLight 0'
    Say "[TestOnlyDecor $Serial $page"
    Start-Sleep -Milliseconds $SettleMs
    $path = (& $shot -Name $Camera -Label $page | Select-Object -Last 1).ToString().Trim()
    if (-not (Test-Path -LiteralPath $path)) { throw "No screenshot for $page ($path)" }
    $dest = Join-Path $out "$page.png"
    & $BRPython $gal finish $path $page $dest | Out-Null
    Write-Host "shot $page -> $dest"
}
Say "[TestOnlyDecor $Serial clear"
