<#
.SYNOPSIS
Stops the decorating test rig: the real client, the staff Navrey session, the server (no save), and removes the disposable host. Only the
processes this rig recorded are stopped; nothing else.
#>
$ErrorActionPreference = 'Continue'
$ws = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
Set-Location $ws
. .\.claude\scripts\Use-Toolchain.ps1
$f = Join-Path $ws 'work\decorating\rig.json'
if (-not (Test-Path $f)) { throw 'no rig record (work\decorating\rig.json)' }
$s = Get-Content $f -Raw | ConvertFrom-Json
& .\.claude\scripts\Stop-PlayerClient.ps1 -Name $s.camera 2>&1 | Select-Object -Last 1
& .\.claude\scripts\Stop-NavreySession.ps1 -Name admin 2>&1 | Select-Object -Last 1
& .\.claude\scripts\Stop-DevServer.ps1 -NoSave -DistributionPath (Join-Path $ws "work\hosts\$($s.host)") 2>&1 | Select-Object -Last 1
Start-Sleep -Seconds 3
& .\.claude\scripts\Remove-DisposableHost.ps1 -Name $s.host 2>&1 | Select-Object -Last 1
Remove-Item $f -ErrorAction SilentlyContinue
& .\.claude\scripts\Get-ShardStatus.ps1 2>&1 | Select-String -Pattern 'port 2593|server:|navrey:'
