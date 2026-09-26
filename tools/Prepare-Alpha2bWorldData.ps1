param(
    [string]$ModernUOPath = (Join-Path $PSScriptRoot '..\..\ModernUO')
)

$ErrorActionPreference = 'Stop'

$contentRoot = Split-Path $PSScriptRoot -Parent
$modernUOPath = (Resolve-Path -LiteralPath $ModernUOPath).Path
$distributionPath = (Resolve-Path -LiteralPath (Join-Path $modernUOPath 'Distribution')).Path
$sourceRoot = Join-Path $contentRoot 'data\world-generation\alpha2b'
$manifestPath = Join-Path $sourceRoot 'world-generation.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable

function Resolve-GitCommit([string]$RepositoryPath) {
    $gitPath = Join-Path $RepositoryPath '.git'
    $head = (Get-Content -LiteralPath (Join-Path $gitPath 'HEAD') -Raw).Trim()

    if ($head -notlike 'ref: *') {
        return $head
    }

    $reference = $head.Substring(5)
    $looseReference = Join-Path $gitPath $reference
    if (Test-Path -LiteralPath $looseReference) {
        return (Get-Content -LiteralPath $looseReference -Raw).Trim()
    }

    $packedReferences = Join-Path $gitPath 'packed-refs'
    if (Test-Path -LiteralPath $packedReferences) {
        foreach ($line in Get-Content -LiteralPath $packedReferences) {
            if ($line -match "^([0-9a-fA-F]{40}) $([regex]::Escape($reference))$") {
                return $Matches[1]
            }
        }
    }

    throw "Unable to resolve Git reference $reference in $RepositoryPath."
}

$currentCommit = Resolve-GitCommit $modernUOPath

if ($currentCommit -notmatch '^[0-9a-fA-F]{40}$') {
    throw "ModernUO HEAD is not a full commit hash: $currentCommit"
}

if (-not [string]::Equals($currentCommit, [string]$manifest.pinnedModernUoCommit, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Alpha 2b data is pinned to $($manifest.pinnedModernUoCommit), but ModernUO is $currentCommit."
}

if ($manifest.era -ne 'UOR' -or $manifest.targetMap -ne 'Felucca') {
    throw 'Alpha 2b world data must target UOR and Felucca.'
}

function Get-PinnedModernUOText([string]$RelativePath) {
    $gitPath = $RelativePath.Replace('\', '/')
    $lines = @(& git -c "safe.directory=$modernUOPath" -C $modernUOPath show "$currentCommit`:$gitPath")
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read pinned ModernUO input $gitPath at $currentCommit."
    }

    return $lines -join "`n"
}

$generatedRoot = [IO.Path]::GetFullPath((Join-Path $distributionPath $manifest.generatedDataRoot))
$allowedRoot = [IO.Path]::GetFullPath((Join-Path $distributionPath 'Data\BritanniaRenaissance'))

if (-not $generatedRoot.StartsWith($allowedRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing generated-data path outside $allowedRoot`: $generatedRoot"
}

if (Test-Path -LiteralPath $generatedRoot) {
    Remove-Item -LiteralPath $generatedRoot -Recurse -Force
}

$decorationTarget = Join-Path $generatedRoot $manifest.decorationsDirectory
$spawnerTarget = Join-Path $generatedRoot $manifest.spawnersDirectory
New-Item -ItemType Directory -Path $decorationTarget -Force | Out-Null
New-Item -ItemType Directory -Path $spawnerTarget -Force | Out-Null

$outputs = [System.Collections.Generic.List[object]]::new()

foreach ($relativePath in $manifest.decorationFiles) {
    $safeName = $relativePath.Replace('/', '__').Replace('\', '__')
    $target = Join-Path $decorationTarget $safeName
    $sourcePath = "Distribution/Data/Decoration/$($relativePath.Replace('\', '/'))"
    Get-PinnedModernUOText $sourcePath | Set-Content -LiteralPath $target -Encoding utf8
    $outputs.Add([ordered]@{ kind = 'decoration'; source = $relativePath; output = $safeName })
}

foreach ($fileName in $manifest.customDecorationFiles) {
    $source = Join-Path $sourceRoot $fileName
    $target = Join-Path $decorationTarget $fileName
    Copy-Item -LiteralPath $source -Destination $target
    $outputs.Add([ordered]@{ kind = 'decoration'; source = "ShardContent/$fileName"; output = $fileName })
}

$signTarget = Join-Path $generatedRoot $manifest.signsFile
$signLines = [System.Collections.Generic.List[string]]::new()
$excludedSigns = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($sign in $manifest.excludedSigns) {
    [void]$excludedSigns.Add("$($sign.mapCode)|$($sign.itemId)|$($sign.x)|$($sign.y)|$($sign.z)")
}

foreach ($line in (Get-PinnedModernUOText 'Distribution/Data/signs.cfg') -split "`r?`n") {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $columns = $line -split ' ', 6
    $parts = $line -split ' ', 2
    $mapCode = [int]$parts[0]
    $signKey = "$mapCode|$($columns[1])|$($columns[2])|$($columns[3])|$($columns[4])"
    if (($mapCode -eq 0 -or $mapCode -eq 1) -and -not $excludedSigns.Contains($signKey)) {
        $signLines.Add("1 $($parts[1])")
    }
}

$signLines | Set-Content -LiteralPath $signTarget -Encoding utf8
$outputs.Add([ordered]@{ kind = 'signs'; source = 'Data/signs.cfg'; output = $manifest.signsFile; records = $signLines.Count })

$teleporterTarget = Join-Path $generatedRoot $manifest.teleportersFile
$teleporters = @(Get-PinnedModernUOText 'Distribution/Data/teleporters.json' | ConvertFrom-Json)
$eraTeleporters = @(
    $teleporters | Where-Object {
        $_.src.map -eq $manifest.targetMap -and
        $_.dst.map -eq $manifest.targetMap -and
        [int]$_.src.loc[0] -lt [int]$manifest.maximumEraMapXExclusive -and
        [int]$_.dst.loc[0] -lt [int]$manifest.maximumEraMapXExclusive
    }
)
$eraTeleporters | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $teleporterTarget -Encoding utf8
$teleporterPlacementCandidates = ($eraTeleporters | ForEach-Object { if ($_.back) { 2 } else { 1 } } | Measure-Object -Sum).Sum
$canonicalTeleporters = [System.Collections.Generic.List[object]]::new()

function Add-CanonicalTeleporterPlacement($Source, $Destination) {
    for ($index = $canonicalTeleporters.Count - 1; $index -ge 0; $index--) {
        $existing = $canonicalTeleporters[$index].source
        if ([int]$existing.loc[0] -eq [int]$Source.loc[0] -and
            [int]$existing.loc[1] -eq [int]$Source.loc[1] -and
            [Math]::Abs([int]$existing.loc[2] - [int]$Source.loc[2]) -le 12) {
            $canonicalTeleporters.RemoveAt($index)
        }
    }

    $canonicalTeleporters.Add([ordered]@{ source = $Source; destination = $Destination })
}

foreach ($teleporter in $eraTeleporters) {
    Add-CanonicalTeleporterPlacement $teleporter.src $teleporter.dst
    if ($teleporter.back) {
        Add-CanonicalTeleporterPlacement $teleporter.dst $teleporter.src
    }
}

$teleporterPlacements = $canonicalTeleporters.Count
$outputs.Add([ordered]@{
    kind = 'teleporters'
    source = 'Data/teleporters.json'
    output = $manifest.teleportersFile
    definitions = $eraTeleporters.Count
    placementCandidates = $teleporterPlacementCandidates
    placements = $teleporterPlacements
})

$excludedTypes = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($typeName in $manifest.excludedSpawnerTypes) {
    [void]$excludedTypes.Add($typeName)
}

$britainOnlyFiles = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($fileName in $manifest.britainOnlySpawnerFiles) {
    [void]$britainOnlyFiles.Add($fileName)
}

$totalSpawners = 0
$allFilteredSpawners = [System.Collections.Generic.List[object]]::new()
foreach ($fileName in $manifest.spawnerFiles) {
    $sourceSpawners = @(Get-PinnedModernUOText "Distribution/Data/Spawns/shared/felucca/$fileName" | ConvertFrom-Json)
    $filteredSpawners = [System.Collections.Generic.List[object]]::new()

    foreach ($spawner in $sourceSpawners) {
        if ($spawner.map -ne $manifest.targetMap) {
            continue
        }

        if ($britainOnlyFiles.Contains($fileName)) {
            $x = [int]$spawner.location[0]
            $y = [int]$spawner.location[1]
            if ($x -lt [int]$manifest.britainBounds.xMin -or $x -gt [int]$manifest.britainBounds.xMax -or
                $y -lt [int]$manifest.britainBounds.yMin -or $y -gt [int]$manifest.britainBounds.yMax) {
                continue
            }
        }

        $entries = @($spawner.entries | Where-Object { -not $excludedTypes.Contains([string]$_.name) })
        if ($entries.Count -eq 0) {
            continue
        }

        $spawner.entries = $entries
        $maximumCount = ($entries | Measure-Object -Property maxCount -Sum).Sum
        if ([int]$spawner.count -gt [int]$maximumCount) {
            $spawner.count = [int]$maximumCount
        }

        $filteredSpawners.Add($spawner)
        $allFilteredSpawners.Add($spawner)
    }

    $target = Join-Path $spawnerTarget $fileName
    $filteredSpawners | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $target -Encoding utf8
    $totalSpawners += $filteredSpawners.Count
    $outputs.Add([ordered]@{
        kind = 'spawners'
        source = "Data/Spawns/shared/felucca/$fileName"
        output = "$($manifest.spawnersDirectory)/$fileName"
        sourceRecords = $sourceSpawners.Count
        records = $filteredSpawners.Count
    })
}

foreach ($fileName in $manifest.customSpawnerFiles) {
    $source = Join-Path $sourceRoot $fileName
    $customSpawners = @(Get-Content -LiteralPath $source -Raw | ConvertFrom-Json)
    $target = Join-Path $spawnerTarget $fileName
    Copy-Item -LiteralPath $source -Destination $target

    foreach ($spawner in $customSpawners) {
        $allFilteredSpawners.Add($spawner)
    }

    $totalSpawners += $customSpawners.Count
    $outputs.Add([ordered]@{
        kind = 'spawners'
        source = "ShardContent/$fileName"
        output = "$($manifest.spawnersDirectory)/$fileName"
        sourceRecords = $customSpawners.Count
        records = $customSpawners.Count
    })
}

$canonicalSpawnerLocations = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$canonicalSpawnerGuids = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$canonicalSpawnerCount = 0
for ($index = $allFilteredSpawners.Count - 1; $index -ge 0; $index--) {
    $spawner = $allFilteredSpawners[$index]
    $locationKey = "$($spawner.'$type')|$($spawner.map)|$($spawner.location[0])|$($spawner.location[1])|$($spawner.location[2])"
    if ($canonicalSpawnerLocations.Add($locationKey) -and $canonicalSpawnerGuids.Add([string]$spawner.guid)) {
        $canonicalSpawnerCount++
    }
}

$report = [ordered]@{
    schemaVersion = 1
    pinnedModernUoCommit = $currentCommit
    generatedUtc = [DateTime]::UtcNow.ToString('O')
    targetEra = $manifest.era
    targetMap = $manifest.targetMap
    decorationFiles = @($manifest.decorationFiles).Count + @($manifest.customDecorationFiles).Count
    signRecords = $signLines.Count
    teleporterDefinitions = $eraTeleporters.Count
    teleporterPlacementCandidates = $teleporterPlacementCandidates
    teleporterPlacements = $teleporterPlacements
    spawnerRecordCandidates = $totalSpawners
    spawnerRecords = $canonicalSpawnerCount
    outputs = $outputs
}

$reportPath = Join-Path $generatedRoot 'generation-report.json'
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding utf8

$targetManifest = Join-Path $distributionPath 'Configuration\alpha2b-world-generation.json'
Copy-Item -LiteralPath $manifestPath -Destination $targetManifest -Force

Write-Host "Prepared Alpha 2b UOR/Felucca data at $generatedRoot"
Write-Host "Decoration files: $($report.decorationFiles)"
Write-Host "Signs: $($report.signRecords)"
Write-Host "Teleporters: $($report.teleporterDefinitions) definitions / $($report.teleporterPlacements) canonical placements"
Write-Host "Spawners: $($report.spawnerRecords) canonical records"
