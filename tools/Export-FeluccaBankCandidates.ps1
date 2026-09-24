param(
    [string]$ModernUOPath = (Join-Path $PSScriptRoot '..\..\ModernUO'),
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$modernUOPath = (Resolve-Path -LiteralPath $ModernUOPath).Path
$vendorsPath = Join-Path $modernUOPath 'Distribution\Data\Spawns\shared\felucca\Vendors.json'
if (-not (Test-Path -LiteralPath $vendorsPath)) {
    throw "Felucca vendor spawn data was not found: $vendorsPath"
}

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $outputFullPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$sourceBytes = [System.IO.File]::ReadAllBytes($vendorsPath)
$sourceHash = ([System.Security.Cryptography.SHA256]::Create()).ComputeHash($sourceBytes)
$sourceSha256 = ([System.BitConverter]::ToString($sourceHash)).Replace('-', '').ToLowerInvariant()
$spawners = Get-Content -LiteralPath $vendorsPath -Raw | ConvertFrom-Json

$candidates = @(
    foreach ($spawner in $spawners) {
        if (-not [string]::Equals([string]$spawner.map, 'Felucca', [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }

        $bankerEntries = @($spawner.entries | Where-Object {
            [string]::Equals([string]$_.name, 'Banker', [System.StringComparison]::OrdinalIgnoreCase)
        })
        if ($bankerEntries.Count -eq 0) {
            continue
        }

        [pscustomobject]@{
            spawnerGuid = [string]$spawner.guid
            location = @([int]$spawner.location[0], [int]$spawner.location[1], [int]$spawner.location[2])
            bankerCount = [int]($bankerEntries | Measure-Object -Property maxCount -Sum).Sum
            sourceEntries = @($spawner.entries | ForEach-Object { [string]$_.name } | Sort-Object -Unique)
        }
    }
)

$result = [ordered]@{
    generatedUtc = [DateTime]::UtcNow.ToString('o')
    source = 'ModernUO/Distribution/Data/Spawns/shared/felucca/Vendors.json'
    sourceSha256 = $sourceSha256
    purpose = 'Review candidates only; this output is not a theft-region configuration.'
    candidateCount = $candidates.Count
    candidates = @($candidates | Sort-Object @{ Expression = { $_.location[1] } }, @{ Expression = { $_.location[0] } })
}

$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outputFullPath -Encoding utf8
Write-Host "Wrote $($candidates.Count) Felucca banker candidates to $outputFullPath"
Write-Host "Source SHA-256: $sourceSha256"
