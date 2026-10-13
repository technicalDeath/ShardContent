param([string] $HostName = 'help-slice', [string[]] $Names = @('HelpAlpha'))
$ErrorActionPreference = 'Stop'
$Names = @($Names | ForEach-Object { $_ -split ',' })
Set-Location "C:\Users\brend\Documents\Britannia Renaissance"
. .\.claude\scripts\Use-Toolchain.ps1 | Out-Null
Write-Host "=== build shard $(Get-Date -Format T)"
$refs = (Resolve-Path 'work\agent-verification\references').Path
& $BRDotnet build ShardContent\src\BritanniaRenaissance.Content\BritanniaRenaissance.Content.csproj -c Release --maxcpucount:1 -p:SkipShardContentDeploy=true "-p:ModernUOPath=$refs" 2>&1 | Select-String -Pattern "error CS|Error\(s\)|Warn.*\(s\)" | Select-Object -First 8

Write-Host "=== host $(Get-Date -Format T)"
& .\.claude\scripts\New-DisposableHost.ps1 -Name $HostName 2>&1 | Select-Object -Last 1
$hostDir = (Resolve-Path "work\hosts\$HostName").Path
Copy-Item work\agent-verification\modernuo-output\UOContent.dll "$hostDir\Assemblies\UOContent.dll" -Force
Copy-Item work\agent-verification\modernuo-output\Server.dll "$hostDir\Server.dll" -Force   # engine hooks live in Server.dll (Mobile.HealApplied)
Copy-Item work\agent-verification\modernuo-output\Server.pdb "$hostDir\Server.pdb" -Force -ErrorAction SilentlyContinue
Copy-Item work\agent-verification\modernuo-output\UOContent.pdb "$hostDir\Assemblies\UOContent.pdb" -Force
$shardBin = "ShardContent\src\BritanniaRenaissance.Content\bin\Release\net10.0"
Copy-Item "$shardBin\BritanniaRenaissance.Content.dll" "$hostDir\Assemblies\BritanniaRenaissance.Content.dll" -Force
Copy-Item "$shardBin\BritanniaRenaissance.Content.pdb" "$hostDir\Assemblies\BritanniaRenaissance.Content.pdb" -Force

# The source rules (with the new flag), switched on for this host only; the help text the host loads has placeholders for the skills not written yet.
$rulesPath = "$hostDir\Configuration\shard-rules.json"
$rules = Get-Content ShardContent\data\configuration\shard-rules.json -Raw | ConvertFrom-Json
$rules.featureFlags.helpGumps = $true
$rules.featureFlags.combatBar = $true
$rules.featureFlags.wearNotice = $true
$rules.featureFlags.autoUse = $true
$rules.featureFlags.damageNumbers = $true
$rules.featureFlags.healNumbers = $true
[IO.File]::WriteAllText($rulesPath, ($rules | ConvertTo-Json -Depth 30), (New-Object Text.UTF8Encoding($false)))
Copy-Item ShardContent\data\configuration\buff-icons.json "$hostDir\Configuration\buff-icons.json" -Force   # the source buff table (new states), not the deployed one
& $BRPython work\help-gumps\make_host_data.py ShardContent\data\help "$hostDir\Configuration\help"

$aj = "$hostDir\Data\assemblies.json"
$list = @(Get-Content $aj -Raw | ConvertFrom-Json)
$proj = '.\ShardContent\tests\scenarios\alpha3-tools\TestOnlyProbe.csproj'
& $BRDotnet build $proj -c Release "-p:ServerHostPath=$hostDir" 2>&1 | Select-String -Pattern "error CS|Error\(s\)" | Select-Object -First 5
Copy-Item '.\ShardContent\tests\scenarios\alpha3-tools\bin\Release\net10.0\TestOnlyProbe.dll' "$hostDir\Assemblies\" -Force
if ($list -notcontains 'TestOnlyProbe.dll') { $list += 'TestOnlyProbe.dll' }
[IO.File]::WriteAllText($aj, ($list | ConvertTo-Json), (New-Object Text.UTF8Encoding($false)))
"helpGumps in host rules: " + ((Get-Content $rulesPath -Raw | ConvertFrom-Json).featureFlags.helpGumps)

Write-Host "=== characters $(Get-Date -Format T)"
$first = $true
foreach ($n in $Names) {
    Write-Host "=== $n $(Get-Date -Format T)"
    if ($first) { & .\.claude\scripts\New-TestCharacter.ps1 -HostName $HostName -Name $n -Profession 13; $first = $false }
    else { & .\.claude\scripts\New-TestCharacter.ps1 -HostName $HostName -Name $n -Profession 13 -NoRestart }
}
$log = (Get-ChildItem work\dev-server\logs\server-*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
Write-Host "--- boot problems:"
Select-String -Path $log -Pattern "ERR\]|WRN\]|Exception|help" | ForEach-Object { $_.Line.Substring(0, [Math]::Min(220, $_.Line.Length)) }
Write-Host "=== done $(Get-Date -Format T)"
