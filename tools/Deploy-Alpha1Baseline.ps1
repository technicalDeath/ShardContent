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
$targetRules = Join-Path $modernUOPath 'Distribution\Configuration\shard-rules.json'
$targetExpansion = Join-Path $modernUOPath 'Distribution\Configuration\expansion.json'
$modernUOConfiguration = Join-Path $modernUOPath 'Distribution\Configuration\modernuo.json'
$targetEraGates = Join-Path $modernUOPath 'Distribution\Configuration\modernuo-era-gates.json'
$assemblyRegistry = Join-Path $modernUOPath 'Distribution\Data\assemblies.json'
$contentAssembly = 'BritanniaRenaissance.Content.dll'

if (-not (Test-Path -LiteralPath $dotnet)) {
    throw "Workspace .NET SDK was not found: $dotnet"
}

# The local SDK's shared compiler pipe can be inaccessible from a different integrity level.
# A single MSBuild node keeps this deployment repeatable in that environment.
& $dotnet build $project -c Release --maxcpucount:1 "-p:ModernUOPath=$modernUOPath"
if ($LASTEXITCODE -ne 0) {
    throw 'Shard content build failed.'
}

Copy-Item -LiteralPath $sourceRules -Destination $targetRules -Force
Copy-Item -LiteralPath $sourceExpansion -Destination $targetExpansion -Force
Copy-Item -LiteralPath $sourceEraGates -Destination $targetEraGates -Force

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
Write-Host 'Restart ModernUO to load the updated content assembly and rules.'
