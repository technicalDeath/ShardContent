param(
    [string]$ModernUOPath = (Join-Path $PSScriptRoot '..\..\ModernUO'),
    [string]$ShardContentPath = (Join-Path $PSScriptRoot '..'),
    [string]$RulesPath
)

$ErrorActionPreference = 'Stop'

$modernUOPath = (Resolve-Path -LiteralPath $ModernUOPath).Path
$shardContentPath = (Resolve-Path -LiteralPath $ShardContentPath).Path
$rulesPath = if ([string]::IsNullOrWhiteSpace($RulesPath)) {
    Join-Path $shardContentPath 'data\configuration\shard-rules.json'
} else {
    (Resolve-Path -LiteralPath $RulesPath).Path
}
$rules = Get-Content -LiteralPath $rulesPath -Raw | ConvertFrom-Json

function Get-GitValue([string]$repository, [string[]]$arguments) {
    $value = (& git -C $repository @arguments 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "git $($arguments -join ' ') failed for ${repository}: $value"
    }

    return $value
}

$actualModernUOCommit = Get-GitValue $modernUOPath @('rev-parse', 'HEAD')
$modernUOClean = [string]::IsNullOrWhiteSpace((Get-GitValue $modernUOPath @('status', '--porcelain')))
$shardContentClean = [string]::IsNullOrWhiteSpace((Get-GitValue $shardContentPath @('status', '--porcelain')))
$alpha2Flags = @(
    if ($rules.featureFlags.safeWorld) { 'safeWorld' }
    if ($rules.featureFlags.automaticMurderAdjudication) { 'automaticMurderAdjudication' }
    if ($rules.featureFlags.theftProtection) { 'theftProtection' }
    if ($rules.featureFlags.knockedOut) { 'knockedOut' }
)

$bankPolygonCount = @($rules.theftRegions.bankProtectionPolygons).Count
$coolPolygonCount = @($rules.theftRegions.coolDungeonPolygons).Count
$blockers = [System.Collections.Generic.List[string]]::new()

if (-not [string]::Equals($rules.pinnedModernUoCommit, $actualModernUOCommit, [System.StringComparison]::OrdinalIgnoreCase)) {
    $blockers.Add("shard-rules pins ModernUO $($rules.pinnedModernUoCommit), but checkout is $actualModernUOCommit")
}

if (-not $modernUOClean) {
    $blockers.Add('ModernUO working tree is dirty')
}

if (-not $shardContentClean) {
    $blockers.Add('ShardContent working tree is dirty')
}

if ($alpha2Flags.Count -gt 0 -and -not $rules.alpha2EnablementAcknowledged) {
    $blockers.Add('Alpha 2 flags are enabled without alpha2EnablementAcknowledged')
}

if ($bankPolygonCount -eq 0) {
    $blockers.Add('approved bank-protection polygons are not configured')
}

if ($coolPolygonCount -eq 0) {
    $blockers.Add('approved Cool-Dungeon polygons are not configured')
}

[pscustomobject]@{
    ModernUOCommit = $actualModernUOCommit
    PinnedModernUOCommit = $rules.pinnedModernUoCommit
    ModernUOClean = $modernUOClean
    ShardContentClean = $shardContentClean
    Alpha2EnablementAcknowledged = [bool]$rules.alpha2EnablementAcknowledged
    Alpha2Flags = if ($alpha2Flags.Count -eq 0) { 'none' } else { $alpha2Flags -join ',' }
    BankProtectionPolygonCount = $bankPolygonCount
    CoolDungeonPolygonCount = $coolPolygonCount
    ReadyForEnablement = ($blockers.Count -eq 0)
    Blockers = if ($blockers.Count -eq 0) { 'none' } else { $blockers -join ' | ' }
} | Format-List
