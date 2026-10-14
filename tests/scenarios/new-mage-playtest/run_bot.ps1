# Runs mage_bot.py with the workspace's python and the Navrey library on the path. Output goes to work/mage-playtest/run.log (and the console).
#   & .\ShardContent\tests\scenarios\new-mage-playtest\run_bot.ps1 -Seconds 600
param([string] $Name = 'MageP', [int] $Seconds = 600)

$root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
Set-Location $root
. .\.claude\scripts\Use-Toolchain.ps1

$py = (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1 | ForEach-Object { Join-Path $_.FullName 'python.exe' })
if (-not $py -or -not (Test-Path $py)) { throw 'No python found under %LOCALAPPDATA%\Programs\Python.' }

$env:PYTHONPATH = "$root\Navrey\cli;$root\.claude\scripts"
& $py -u "$PSScriptRoot\mage_bot.py" --name $Name --for $Seconds
