param(
    [string]$ModernUOPath = (Join-Path $PSScriptRoot '..\..\ModernUO'),
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$modernUOPath = (Resolve-Path -LiteralPath $ModernUOPath).Path
$regionsPath = Join-Path $modernUOPath 'Distribution\Data\regions.json'
if (-not (Test-Path -LiteralPath $regionsPath)) {
    throw "ModernUO region data was not found: $regionsPath"
}

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$outputDirectory = Split-Path -Parent $outputFullPath
if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$sourceBytes = [System.IO.File]::ReadAllBytes($regionsPath)
$sourceHash = [System.Security.Cryptography.SHA256]::HashData($sourceBytes)
$sourceSha256 = ([System.BitConverter]::ToString($sourceHash)).Replace('-', '').ToLowerInvariant()
$classicNames = @('Covetous', 'Deceit', 'Despise', 'Destard', 'Fire', 'Hythloth', 'Ice', 'Khaldun', 'Shame', 'Wrong')
$regions = Get-Content -LiteralPath $regionsPath -Raw | ConvertFrom-Json

$candidates = @(
    foreach ($region in $regions) {
        if (-not [string]::Equals([string]$region.'$type', 'DungeonRegion', [System.StringComparison]::OrdinalIgnoreCase) -or
            -not [string]::Equals([string]$region.Map, 'Felucca', [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }

        [pscustomobject]@{
            name = [string]$region.Name
            uorEraCandidate = $classicNames -contains [string]$region.Name
            entrance = if ($null -eq $region.Entrance) { $null } else { @([int]$region.Entrance.x, [int]$region.Entrance.y, [int]$region.Entrance.z) }
            goLocation = if ($null -eq $region.GoLocation) { $null } else { @([int]$region.GoLocation.x, [int]$region.GoLocation.y, [int]$region.GoLocation.z) }
            areas = @($region.Area | ForEach-Object {
                [pscustomobject]@{
                    x1 = [int]$_.x1
                    y1 = [int]$_.y1
                    x2 = [int]$_.x2
                    y2 = [int]$_.y2
                }
            })
        }
    }
)

$result = [ordered]@{
    generatedUtc = [DateTime]::UtcNow.ToString('o')
    source = 'ModernUO/Distribution/Data/regions.json'
    sourceSha256 = $sourceSha256
    purpose = 'Review candidates only; this output is not a Cool-Dungeon configuration.'
    candidateCount = $candidates.Count
    candidates = @($candidates | Sort-Object name)
}

$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $outputFullPath -Encoding utf8
Write-Host "Wrote $($candidates.Count) Felucca dungeon candidates to $outputFullPath"
Write-Host "Source SHA-256: $sourceSha256"
