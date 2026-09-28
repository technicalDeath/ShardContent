#requires -Version 7.0
<#
.SYNOPSIS
Build current ModernUO references and run tests without deploying to the shared host.
.EXAMPLE
./tools/Invoke-AgentVerification.ps1 -Suite Shard -Filter 'FullyQualifiedName~SkillBankLedgerTests'
.EXAMPLE
./tools/Invoke-AgentVerification.ps1 -Suite UOContent -Filter 'FullyQualifiedName~Uor'
.EXAMPLE
./tools/Invoke-AgentVerification.ps1 -Suite All
#>
[CmdletBinding()]
param(
    [ValidateSet('Shard', 'UOContent', 'All')][string]$Suite = 'Shard',
    [string]$Filter,
    [switch]$Restore
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot 'AgentVerificationInputs.ps1')
if ($Suite -eq 'All' -and $Filter) {
    throw 'Use a single suite with -Filter, or All without a filter.'
}
$contentRoot = Split-Path $PSScriptRoot -Parent
$workspaceRoot = Split-Path $contentRoot -Parent
$modernRoot = Join-Path $workspaceRoot 'ModernUO'
$dotnet = Join-Path $workspaceRoot 'dotnet/dotnet.exe'
$cache = Join-Path $workspaceRoot 'work/agent-verification'
$engineOutput = Join-Path $cache 'modernuo-output'
$referenceRoot = Join-Path $cache 'references'
if (-not (Test-Path -LiteralPath $dotnet)) { throw "Missing workspace SDK: $dotnet" }
New-Item -ItemType Directory -Path $cache -Force | Out-Null

# The ordinary project obj/bin caches are shared. A file handle releases on process exit,
# including crashes; a leftover lock file is harmless and must not be deleted to bypass it.
try {
    $lease = [IO.File]::Open((Join-Path $cache 'verification.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
} catch {
    throw 'Another verification run holds the build lease. Wait for that run; do not delete the lock file.'
}
$oldData = $env:MODERNUO_TEST_DATA_DIR
$oldDotnet = $env:DOTNET_ROOT
$runPath = Join-Path $cache ('runs/' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 6))
$report = [ordered]@{
    schemaVersion = 2; startedUtc = [DateTime]::UtcNow.ToString('o'); status = 'running'
    suite = $Suite; filter = $Filter; deployed = $false; steps = @(); assemblies = @(); repositories = @()
}

function Invoke-DotnetStep([string]$Name, [string[]]$Arguments) {
    $logPath = Join-Path $runPath "$Name.log"
    Write-Host "$Name ..."
    $timer = [Diagnostics.Stopwatch]::StartNew()
    & $dotnet @Arguments *> $logPath
    $code = $LASTEXITCODE
    $timer.Stop()
    $report.steps += [ordered]@{ name = $Name; seconds = [math]::Round($timer.Elapsed.TotalSeconds, 2); exitCode = $code; log = $logPath }
    if ($code -ne 0) {
        Get-Content -LiteralPath $logPath -Tail 35 | Write-Host
        throw "$Name failed (exit $code). See $logPath. For missing assets restore once with -Restore; do not redirect obj or use shared Distribution output."
    }
    Get-Content -LiteralPath $logPath -Tail 5 | Write-Host
}

function Assert-TestResults([string]$Name) {
    $trx = Join-Path $runPath "$Name.trx"
    if (-not (Test-Path -LiteralPath $trx)) { throw "No TRX produced for $Name; this is not a passing test run." }
    [xml]$document = Get-Content -LiteralPath $trx -Raw
    $counters = $document.SelectSingleNode("//*[local-name()='Counters']")
    if ($null -eq $counters -or [int]$counters.total -eq 0 -or [int]$counters.executed -eq 0) {
        throw "No tests executed for $Name. Check the filter."
    }
    $report["${Name}Results"] = [ordered]@{
        total = [int]$counters.total; executed = [int]$counters.executed
        passed = [int]$counters.passed; failed = [int]$counters.failed; trx = $trx
    }
    if ([int]$counters.failed -ne 0) { throw "$Name has failed tests." }
}

try {
    New-Item -ItemType Directory -Path $runPath, $engineOutput, (Join-Path $referenceRoot 'Distribution/Assemblies') -Force | Out-Null
    foreach ($repo in @($contentRoot, $modernRoot)) {
        $head = & git -C $repo rev-parse HEAD
        if ($LASTEXITCODE -ne 0) { throw "Cannot identify repository $repo" }
        $status = @(& git -C $repo status --short)
        $report.repositories += [ordered]@{ path = $repo; head = "$head"; workingTree = $status }
    }
    $inputScopes = @(
        @{ Repository = $modernRoot; Scope = @('Projects', 'Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', 'NuGet.Config', 'nuget.config', 'version.json', 'Rules.ruleset', 'Distribution/Data') },
        @{ Repository = $contentRoot; Scope = @('src', 'tests', 'data/configuration', 'Directory.Build.props', 'Directory.Build.targets', 'Directory.Packages.props', 'global.json', 'NuGet.Config', 'nuget.config') }
    )
    $report['sourceBefore'] = @($inputScopes | ForEach-Object { Get-VerificationSourceSnapshot @_ })
    $report['tooling'] = @('Invoke-AgentVerification.ps1', 'AgentVerificationInputs.ps1') | ForEach-Object {
        [ordered]@{ name = $_; sha256 = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $_) -Algorithm SHA256).Hash }
    }
    $report['sdkVersion'] = (& $dotnet --version)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot identify the workspace SDK.' }
    $env:DOTNET_ROOT = Split-Path $dotnet -Parent
    $env:MODERNUO_TEST_DATA_DIR = Join-Path $workspaceRoot 'UOData'
    $common = @('-c', 'Release', '--maxcpucount:1', '-p:UseSharedCompilation=false')
    if (-not $Restore) { $common += '--no-restore' }
    # OutDir is a global MSBuild property: it also redirects Server/Logger references.
    # SolutionDir supplies the stock tests' complete Data fixture copy target.
    $modernProperties = @("-p:OutDir=$engineOutput/", "-p:SolutionDir=$modernRoot/")
    $modernProject = Join-Path $modernRoot 'Projects/UOContent/UOContent.csproj'
    if ($Suite -in @('UOContent', 'All')) {
        $modernProject = Join-Path $modernRoot 'Projects/UOContent.Tests/UOContent.Tests.csproj'
    }
    Invoke-DotnetStep 'modernuo-build' (@('build', $modernProject) + $common + $modernProperties)
    foreach ($name in @('Server.dll', 'UOContent.dll', 'Logger.dll', 'ModernUO.CodeGeneratedEvents.Annotations.dll')) {
        $source = Join-Path $engineOutput $name
        $relative = if ($name -eq 'Server.dll') { "Distribution/$name" } else { "Distribution/Assemblies/$name" }
        Copy-Item -LiteralPath $source -Destination (Join-Path $referenceRoot $relative) -Force
        $report.assemblies += [ordered]@{ name = $name; sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash }
    }
    if ($Suite -in @('UOContent', 'All')) {
        foreach ($fixture in @('skills.json', 'npc-speeds.json', 'bodyTable.cfg')) {
            if (-not (Test-Path -LiteralPath (Join-Path $engineOutput "Data/$fixture"))) {
                throw "Stock CopyData target did not stage Data/$fixture. Check SolutionDir before running tests."
            }
        }
        $testArguments = @('test', $modernProject) + $common + $modernProperties + @('--no-build', '--results-directory', $runPath, '--logger', 'trx;LogFileName=uo-content.trx')
        if ($Filter) { $testArguments += @('--filter', $Filter) }
        Invoke-DotnetStep 'uo-content' $testArguments
        Assert-TestResults 'uo-content'
    }
    if ($Suite -in @('Shard', 'All')) {
        # Preserve normal ShardContent output layout: a flattened global OutDir has
        # previously broken its project-reference resolution. Deployment is always off.
        $testArguments = @('test', (Join-Path $contentRoot 'tests/BritanniaRenaissance.Content.Tests.csproj')) + $common + @(
            "-p:ModernUOPath=$referenceRoot", '-p:SkipShardContentDeploy=true',
            '--results-directory', $runPath, '--logger', 'trx;LogFileName=shard.trx'
        )
        if ($Filter) { $testArguments += @('--filter', $Filter) }
        Invoke-DotnetStep 'shard' $testArguments
        Assert-TestResults 'shard'
        $shardDll = Join-Path $contentRoot 'tests/bin/Release/net10.0/BritanniaRenaissance.Content.dll'
        $report.assemblies += [ordered]@{ name = 'BritanniaRenaissance.Content.dll'; sha256 = (Get-FileHash -LiteralPath $shardDll -Algorithm SHA256).Hash }
    }
    $report['sourceAfter'] = @($inputScopes | ForEach-Object { Get-VerificationSourceSnapshot @_ })
    for ($index = 0; $index -lt $inputScopes.Count; $index++) {
        Assert-VerificationSourceStable $report.sourceBefore[$index] $report.sourceAfter[$index]
    }
    $report.status = 'passed'
} catch {
    $report.status = 'failed'
    $report['error'] = $_.Exception.Message
    throw
} finally {
    try {
        $env:MODERNUO_TEST_DATA_DIR = $oldData
        $env:DOTNET_ROOT = $oldDotnet
        $report['finishedUtc'] = [DateTime]::UtcNow.ToString('o')
        if (Test-Path -LiteralPath $runPath) {
            $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runPath 'summary.json') -Encoding utf8
            Write-Host "Verification $($report.status): $runPath"
        }
    } finally {
        $lease.Dispose()
    }
}
