# Functions shared by the verification runner and its provenance regression checks.
function Get-VerificationTextHash([string]$Text) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($Text)))
}

function Get-VerificationSourceSnapshot([string]$Repository, [string[]]$Scope) {
    $head = & git -C $Repository rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw "Cannot identify source HEAD: $Repository" }
    # HEAD plus the effective working-tree diff captures staged and unstaged edits.
    # Disable user diff drivers; private configuration/account paths are not in Scope.
    $diff = @(& git -C $Repository -c core.quotePath=false diff --no-ext-diff --no-textconv --binary HEAD -- @Scope 2>$null)
    if ($LASTEXITCODE -ne 0) { throw "Cannot fingerprint tracked inputs: $Repository" }
    $untracked = @(& git -C $Repository -c core.quotePath=false ls-files --others --exclude-standard -- @Scope)
    if ($LASTEXITCODE -ne 0) { throw "Cannot enumerate new inputs: $Repository" }
    $newFiles = @(
        foreach ($relative in ($untracked | Sort-Object)) {
            $path = Join-Path $Repository $relative
            [ordered]@{ path = $relative; sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
        }
    )
    $payload = [ordered]@{ head = "$head"; trackedDiffSha256 = Get-VerificationTextHash ($diff -join "`n"); untracked = $newFiles }
    [pscustomobject]@{
        repository = $Repository; scope = $Scope; head = "$head"
        sha256 = Get-VerificationTextHash ($payload | ConvertTo-Json -Depth 6 -Compress)
        trackedDiffSha256 = $payload.trackedDiffSha256; untracked = $newFiles
    }
}

function Assert-VerificationSourceStable($Before, $After) {
    if ($Before.sha256 -ne $After.sha256) {
        throw "Source inputs changed during verification: $($Before.repository). Results cannot certify the current source; rerun the affected check after edits finish."
    }
}
