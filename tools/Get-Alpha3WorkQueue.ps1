#requires -Version 7.0
<# .SYNOPSIS
Read the active lettered Alpha 3 feature plan, separating executable work from owner decisions and release gates.
#>
[CmdletBinding()]
param(
    [ValidateSet('Actionable', 'Decisions', 'Deferred', 'Invariants', 'Release', 'All')][string]$View = 'Actionable',
    [switch]$Next,
    [switch]$NextPerSection,
    [string]$Section,
    [switch]$AsJson
)
$ErrorActionPreference = 'Stop'
$ledger = Join-Path $PSScriptRoot '../docs/Alpha-3-Feature-Enablement-Plan.md'
$lines = @(Get-Content -LiteralPath $ledger)
$currentSection = ''
$inTodo = $false
# The plan's line order is its alphabetical phase order.
if ($Next -and $View -ne 'Actionable') { throw '-Next selects actionable work; omit it for other views.' }
if ($NextPerSection -and ($View -ne 'Actionable' -or $Next)) { throw '-NextPerSection requires Actionable and cannot be combined with -Next.' }
$rows = @(
    for ($index = 0; $index -lt $lines.Count; $index++) {
        $line = $lines[$index]
        if ($line -eq '## Todo') { $inTodo = $true; continue }
        if ($inTodo -and $line -match '^## ') { break }
        if (-not $inTodo) { continue }
        if ($line -match '^### (.+)$') { $currentSection = $Matches[1]; continue }
        if ($line -match '^- \[([x~ ?>!g])\] (.+)$') {
            $state = $Matches[1]
            $task = $Matches[2]
            $kind = switch ($state) {
                'x' { 'Complete' }
                '?' { 'Decision' }
                '>' { 'Deferred' }
                '!' { 'Invariant' }
                'g' { 'Release' }
                default { 'Actionable' }
            }
            if ($View -eq 'All' -or $View -eq $kind -or
                ($View -eq 'Decisions' -and $kind -eq 'Decision') -or
                ($View -eq 'Invariants' -and $kind -eq 'Invariant')) {
                $rank = if ($currentSection -match '^([A-L])\. ') { [int][char]$Matches[1] - 64 } else { 99 }
                [pscustomobject]@{ kind = $kind; state = $state; section = $currentSection; priority = $rank; line = $index + 1; task = $task }
            }
        }
    }
)
if ($View -eq 'Actionable') { $rows = @($rows | Sort-Object line) }
if ($Section) { $rows = @($rows | Where-Object section -eq $Section) }
if ($NextPerSection) {
    $seenSections = @{}
    $rows = @($rows | Where-Object {
        if ($seenSections.ContainsKey($_.section)) { $false }
        else { $seenSections[$_.section] = $true; $true }
    })
}
if ($Next) { $rows = @($rows | Select-Object -First 1) }
if ($AsJson) { ConvertTo-Json -InputObject $rows -Depth 4 }
else {
    Write-Host 'Alpha 3 feature plan (counts are checklist entries, not a completion percentage).'
    Write-Host 'Use its alphabetical phase order, one feature at a time; activation tasks depend on completed release evidence.'
    Write-Host 'A broad entry is not a single runtime session. -NextPerSection is a read-only overview.'
    $rows | Format-List section, state, line, task
}
