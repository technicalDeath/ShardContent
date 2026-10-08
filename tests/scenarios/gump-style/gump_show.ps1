param(
    [Parameter(Mandatory)] [string] $Script,        # script name(s) in gump-scripts, comma separated
    [string] $Name = 'Gwen',
    [string] $Serial,                               # character serial (read from the session state if omitted)
    [int] $Wait = 2
)
$ErrorActionPreference = 'Stop'
Set-Location "C:\Users\brend\Documents\Britannia Renaissance"
. .\.claude\scripts\Use-Toolchain.ps1 | Out-Null
if (-not $Serial) { $Serial = (Get-Content "work\navrey-sessions\$Name\cuostate.json" -Raw | ConvertFrom-Json).charID }
foreach ($s in ($Script -split ',')) {
    & $BRPython work\qol\admin_say.py "[TestOnlyGump $Serial $s" | Select-Object -Last 1
    Start-Sleep -Seconds $Wait
    & .\.claude\scripts\Get-PlayerClientShot.ps1 -Name $Name -Label "gump-$s" | Select-Object -Last 1
}
# Note: the workspace paths above (work\qol, admin_say.py) are the 2026-10-07 scratch locations; adjust for another checkout.
