param(
    [string]$ModernUOPath = (Join-Path $PSScriptRoot '..\..\ModernUO'),
    [string]$OutputDistributionPath
)

$ErrorActionPreference = 'Stop'

$contentRoot = Split-Path $PSScriptRoot -Parent
$modernUOPath = (Resolve-Path -LiteralPath $ModernUOPath).Path
$distributionPath = if ($OutputDistributionPath) {
    (Resolve-Path -LiteralPath $OutputDistributionPath).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $modernUOPath 'Distribution')).Path
}
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

function Get-TextSha256([string]$Text) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        return [Convert]::ToHexString($sha256.ComputeHash($bytes)).ToLowerInvariant()
    } finally {
        $sha256.Dispose()
    }
}

function Get-FileSha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
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

$inputs = [System.Collections.Generic.List[object]]::new()
$outputs = [System.Collections.Generic.List[object]]::new()
$inputs.Add([ordered]@{
    kind = 'manifest'
    source = 'ShardContent/world-generation.json'
    sha256 = Get-FileSha256 $manifestPath
})

$doorSourceText = Get-PinnedModernUOText ([string]$manifest.doorGeneration.sourceFile)
$inputs.Add([ordered]@{
    kind = 'door-generator-source'
    source = $manifest.doorGeneration.sourceFile
    sha256 = Get-TextSha256 $doorSourceText
})

foreach ($relativePath in $manifest.decorationFiles) {
    $safeName = $relativePath.Replace('/', '__').Replace('\', '__')
    $target = Join-Path $decorationTarget $safeName
    $sourcePath = "Distribution/Data/Decoration/$($relativePath.Replace('\', '/'))"
    $sourceText = Get-PinnedModernUOText $sourcePath
    $sourceSha256 = Get-TextSha256 $sourceText
    $appliedRewrites = [System.Collections.Generic.List[object]]::new()
    foreach ($rewrite in @($manifest.decorationRewrites | Where-Object { $_.source -eq $relativePath })) {
        $pattern = "(?m)^$([regex]::Escape([string]$rewrite.match))$"
        $matches = [regex]::Matches($sourceText, $pattern).Count
        if ($matches -ne [int]$rewrite.expectedMatches) {
            throw "Decoration rewrite for $relativePath expected $($rewrite.expectedMatches) match(es) for '$($rewrite.match)' but found $matches."
        }

        $sourceText = $sourceText.Replace([string]$rewrite.match, [string]$rewrite.replacement)
        $appliedRewrites.Add([ordered]@{
            match = $rewrite.match
            replacement = $rewrite.replacement
            matches = $matches
            reason = $rewrite.reason
        })
    }

    $sourceText | Set-Content -LiteralPath $target -Encoding utf8
    $inputs.Add([ordered]@{ kind = 'decoration'; source = $sourcePath; sha256 = $sourceSha256 })
    $outputs.Add([ordered]@{
        kind = 'decoration'
        source = $relativePath
        output = $safeName
        sha256 = Get-FileSha256 $target
        rewrites = $appliedRewrites
    })
}

foreach ($fileName in $manifest.customDecorationFiles) {
    $source = Join-Path $sourceRoot $fileName
    $target = Join-Path $decorationTarget $fileName
    Copy-Item -LiteralPath $source -Destination $target
    $inputs.Add([ordered]@{ kind = 'decoration'; source = "ShardContent/$fileName"; sha256 = Get-FileSha256 $source })
    $outputs.Add([ordered]@{
        kind = 'decoration'
        source = "ShardContent/$fileName"
        output = $fileName
        sha256 = Get-FileSha256 $target
    })
}

$signTarget = Join-Path $generatedRoot $manifest.signsFile
$signLines = [System.Collections.Generic.List[string]]::new()
$excludedSigns = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($sign in $manifest.excludedSigns) {
    [void]$excludedSigns.Add("$($sign.mapCode)|$($sign.itemId)|$($sign.x)|$($sign.y)|$($sign.z)")
}

$signSourcePath = 'Distribution/Data/signs.cfg'
$signSourceText = Get-PinnedModernUOText $signSourcePath
$inputs.Add([ordered]@{ kind = 'signs'; source = $signSourcePath; sha256 = Get-TextSha256 $signSourceText })
foreach ($line in $signSourceText -split "`r?`n") {
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
$outputs.Add([ordered]@{
    kind = 'signs'
    source = 'Data/signs.cfg'
    output = $manifest.signsFile
    records = $signLines.Count
    sha256 = Get-FileSha256 $signTarget
})

$teleporterTarget = Join-Path $generatedRoot $manifest.teleportersFile
$teleporterSourcePath = 'Distribution/Data/teleporters.json'
$teleporterSourceText = Get-PinnedModernUOText $teleporterSourcePath
$inputs.Add([ordered]@{
    kind = 'teleporters'
    source = $teleporterSourcePath
    sha256 = Get-TextSha256 $teleporterSourceText
})
$teleporters = @($teleporterSourceText | ConvertFrom-Json)
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
    sha256 = Get-FileSha256 $teleporterTarget
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
    $sourcePath = "Distribution/Data/Spawns/shared/felucca/$fileName"
    $sourceText = Get-PinnedModernUOText $sourcePath
    $inputs.Add([ordered]@{ kind = 'spawners'; source = $sourcePath; sha256 = Get-TextSha256 $sourceText })
    $sourceSpawners = @($sourceText | ConvertFrom-Json)
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
        sha256 = Get-FileSha256 $target
    })
}

foreach ($fileName in $manifest.customSpawnerFiles) {
    $source = Join-Path $sourceRoot $fileName
    $customSpawners = @(Get-Content -LiteralPath $source -Raw | ConvertFrom-Json)
    $target = Join-Path $spawnerTarget $fileName
    Copy-Item -LiteralPath $source -Destination $target
    $inputs.Add([ordered]@{ kind = 'spawners'; source = "ShardContent/$fileName"; sha256 = Get-FileSha256 $source })

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
        sha256 = Get-FileSha256 $target
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
    schemaVersion = 2
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
    doorScanRegions = @($manifest.doorGeneration.regions).Count
    expectedDoorPlacements = [int]$manifest.doorGeneration.expectedPlacements
    inputs = $inputs
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
