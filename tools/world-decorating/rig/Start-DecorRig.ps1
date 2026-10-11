<#
.SYNOPSIS
One command for the whole decorating test rig: a disposable host with the decor probe, a camera character, the real ClassicUO client logged in
as that character, daylight and autosave off, and the staff session ('admin') ready to lay layouts.

.DESCRIPTION
Writes work/decorating/rig.json (host, camera name, camera serial, camera position) for rig.py, lay.py, tp.py and shoot.py.
Refuses to start while ANY other server is running (another session may be using port 2593): it never stops someone else's server.
Stop it with Stop-DecorRig.ps1.

.EXAMPLE
. .\.claude\scripts\Use-Toolchain.ps1
& .\ShardContent\tools\world-decorating\rig\Start-DecorRig.ps1
& $BRPython .\ShardContent\tools\world-decorating\rig\lay.py walkgrid 1616 1648 32 36
#>
param(
    [ValidatePattern('^[a-z0-9-]+$')] [string] $HostName = 'decor',
    [ValidatePattern('^[A-Za-z]{2,16}$')] [string] $Camera = 'DecorCam',
    [int] $Profession = 8,
    # runs once the host and the decor probe are in place and before the server starts, with the host folder as its argument: swap in a
    # build under test, add data files or flags, and add probes to Data\assemblies.json
    [scriptblock] $PrepareHost
)
$ErrorActionPreference = 'Stop'
$ws = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
Set-Location $ws
. .\.claude\scripts\Use-Toolchain.ps1

# another session's server? then stop here (shared port 2593, shared Navrey session names)
$cur = Join-Path $ws 'work\dev-server\current.json'
if (Test-Path $cur) {
    $c = Get-Content $cur -Raw | ConvertFrom-Json
    if ($c.serverPid -and (Get-Process -Id $c.serverPid -ErrorAction SilentlyContinue)) {
        throw "A server is already running (PID $($c.serverPid), $($c.distribution)). Do not stop it; wait for it to exit, then start the rig."
    }
}

& .\.claude\scripts\New-DisposableHost.ps1 -Name $HostName 2>&1 | Select-Object -Last 1
$h = Join-Path $BRWorkspace "work\hosts\$HostName"
$probe = '.\ShardContent\tests\scenarios\cosmetic-catalog\DecorProbe.csproj'
& $BRDotnet build $probe -c Release "-p:ServerHostPath=$h" 2>&1 | Select-Object -Last 3
Copy-Item .\ShardContent\tests\scenarios\cosmetic-catalog\bin\Release\net10.0\DecorProbe.dll (Join-Path $h 'Assemblies') -Force
'[ "UOContent.dll", "BritanniaRenaissance.Content.dll", "DecorProbe.dll" ]' | Set-Content (Join-Path $h 'Data\assemblies.json') -Encoding UTF8
if ($PrepareHost) { & $PrepareHost $h }

$out = & .\.claude\scripts\New-TestCharacter.ps1 -HostName $HostName -Name $Camera -Profession $Profession *>&1     # it reports with Write-Host, so capture every stream
$out | Select-Object -Last 3
$m = [regex]::Match(($out -join "`n"), "$Camera`: in game as $Camera \((0x[0-9A-Fa-f]+)\) at (\d+),(\d+)")
if (-not $m.Success) { throw "could not read the camera serial from New-TestCharacter output" }
New-Item -ItemType Directory -Force (Join-Path $ws 'work\decorating') | Out-Null
@{ host = $HostName; camera = $Camera; serial = $m.Groups[1].Value; cam = @([int]$m.Groups[2].Value, [int]$m.Groups[3].Value, 0) } |
    ConvertTo-Json | Set-Content (Join-Path $ws 'work\decorating\rig.json') -Encoding UTF8

# the real client logs in as the camera character (one login per account: stop its Navrey session first; clear a stale client record)
& .\.claude\scripts\Stop-NavreySession.ps1 -Name $Camera 2>&1 | Out-Null
& .\.claude\scripts\Stop-PlayerClient.ps1 -Name $Camera 2>&1 | Out-Null
& .\.claude\scripts\Start-PlayerClient.ps1 -Name $Camera 2>&1 | Select-Object -Last 1
Start-Sleep -Seconds 18
& .\.claude\scripts\Send-PlayerClientInput.ps1 -Name $Camera -X 240 -Y 330 -Right 2>&1 | Out-Null     # close the paperdoll
& $BRPython (Join-Path $PSScriptRoot 'rig.py') say '[AutoSave false'
& $BRPython (Join-Path $PSScriptRoot 'rig.py') say '[GlobalLight 0'
Write-Host "rig ready: host '$HostName', camera '$Camera' $($m.Groups[1].Value). Layout files go in work\cosmetics\layouts; lay.py / tp.py / shoot.py are next to this script."
