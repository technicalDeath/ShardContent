param(
    [string]$ModernUOPath = (Join-Path $PSScriptRoot '..\..\ModernUO')
)

$ErrorActionPreference = 'Stop'

$contentRoot = Split-Path $PSScriptRoot -Parent
$modernUOPath = (Resolve-Path -LiteralPath $ModernUOPath).Path
$dotnet = Join-Path (Split-Path $contentRoot -Parent) 'dotnet\dotnet.exe'
$project = Join-Path $contentRoot 'src\BritanniaRenaissance.Content\BritanniaRenaissance.Content.csproj'
$sourceRules = Join-Path $contentRoot 'data\configuration\shard-rules.json'
$sourceExpansion = Join-Path $contentRoot 'data\configuration\expansion.json'
$sourceEraGates = Join-Path $contentRoot 'data\configuration\modernuo-era-gates.json'
$sourceAntiMacro = Join-Path $contentRoot 'data\configuration\antimacro.json'
$targetRules = Join-Path $modernUOPath 'Distribution\Configuration\shard-rules.json'
$targetExpansion = Join-Path $modernUOPath 'Distribution\Configuration\expansion.json'
$modernUOConfiguration = Join-Path $modernUOPath 'Distribution\Configuration\modernuo.json'
$targetEraGates = Join-Path $modernUOPath 'Distribution\Configuration\modernuo-era-gates.json'
$targetAntiMacro = Join-Path $modernUOPath 'Distribution\Configuration\antimacro.json'
$assemblyRegistry = Join-Path $modernUOPath 'Distribution\Data\assemblies.json'
$contentAssembly = 'BritanniaRenaissance.Content.dll'
$distributionPath = (Resolve-Path -LiteralPath (Join-Path $modernUOPath 'Distribution')).Path
$prepareAlpha2bData = Join-Path $contentRoot 'tools\Prepare-Alpha2bWorldData.ps1'

if (-not (Test-Path -LiteralPath $dotnet)) {
    throw "Workspace .NET SDK was not found: $dotnet"
}

# Windows locks loaded assemblies. Fail before building or copying if a verified ModernUO
# process has this distribution loaded; this prevents a partial deployment that leaves the
# policy/configuration newer than the engine assemblies.
$loadedBy = [System.Collections.Generic.List[string]]::new()
foreach ($process in @(Get-Process -ErrorAction SilentlyContinue)) {
    try {
        $loaded = @($process.Modules | Where-Object {
            $_.FileName -like "$distributionPath*\ModernUO.dll" -or
            $_.FileName -like "$distributionPath*\Server.dll" -or
            $_.FileName -like "$distributionPath*\Assemblies\UOContent.dll"
        })
        if ($loaded.Count -gt 0) {
            $loadedBy.Add("PID $($process.Id) ($($process.ProcessName))")
        }
    } catch {
        # Access to another process's module list may be denied; it is safer to let the copy
        # operation fail than to stop or guess at an inaccessible process.
    }
}

if ($loadedBy.Count -gt 0) {
    throw "ModernUO distribution assemblies are loaded by $($loadedBy -join ', '). Stop the verified server and rerun deployment."
}

& $prepareAlpha2bData -ModernUOPath $modernUOPath

# The local SDK's shared compiler pipe can be inaccessible from a different integrity level.
# A single MSBuild node keeps this deployment repeatable in that environment.
& $dotnet build $project -c Release --maxcpucount:1 "-p:ModernUOPath=$modernUOPath"
if ($LASTEXITCODE -ne 0) {
    throw 'Shard content build failed.'
}

Copy-Item -LiteralPath $sourceRules -Destination $targetRules -Force
Copy-Item -LiteralPath $sourceExpansion -Destination $targetExpansion -Force
Copy-Item -LiteralPath $sourceEraGates -Destination $targetEraGates -Force
Copy-Item -LiteralPath $sourceAntiMacro -Destination $targetAntiMacro -Force

if (-not (Test-Path -LiteralPath $modernUOConfiguration)) {
    throw "ModernUO configuration was not found: $modernUOConfiguration"
}

$modernUOSettings = Get-Content -LiteralPath $modernUOConfiguration -Raw | ConvertFrom-Json -AsHashtable
$eraGateSettings = Get-Content -LiteralPath $sourceEraGates -Raw | ConvertFrom-Json -AsHashtable

foreach ($setting in $eraGateSettings.settings.GetEnumerator()) {
    $modernUOSettings.settings[$setting.Key] = [string]$setting.Value
}

$modernUOSettings | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $modernUOConfiguration -Encoding utf8

if (-not (Test-Path -LiteralPath $assemblyRegistry)) {
    throw "ModernUO assembly registry was not found: $assemblyRegistry"
}

$assemblies = @(Get-Content -LiteralPath $assemblyRegistry -Raw | ConvertFrom-Json)
if ($assemblies -notcontains $contentAssembly) {
    $assemblies += $contentAssembly
    $assemblies | ConvertTo-Json | Set-Content -LiteralPath $assemblyRegistry -Encoding utf8
}

Write-Host "Deployed shard rules to $targetRules"
Write-Host "Deployed UOR expansion and era gates to $targetExpansion and $modernUOConfiguration"
Write-Host "Registered $contentAssembly in $assemblyRegistry"
Write-Host 'Prepared the era-reviewed Alpha 2b world-generation inputs.'
Write-Host 'Restart ModernUO to load the updated content assembly and rules.'
