#requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
. (Join-Path $PSScriptRoot '../AgentVerificationInputs.ps1')
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$testRoot = Join-Path $workspace ('work/verification-input-tests/' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $testRoot 'src'), (Join-Path $testRoot 'docs') -Force | Out-Null
function Invoke-TestGit([string[]]$Arguments) {
    & git -C $testRoot @Arguments | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Fixture git command failed: $($Arguments[0])" }
}
function Snapshot { Get-VerificationSourceSnapshot $testRoot @('src') }
function Assert-Changed($Before, $After, [string]$Case) {
    $rejected = $false
    try { Assert-VerificationSourceStable $Before $After }
    catch { if ($_.Exception.Message -notlike 'Source inputs changed*') { throw }; $rejected = $true }
    if (-not $rejected) { throw "$Case was not detected." }
}
Invoke-TestGit @('init', '--quiet')
Set-Content -LiteralPath (Join-Path $testRoot 'src/example.cs') -Value 'baseline' -NoNewline
Set-Content -LiteralPath (Join-Path $testRoot '.gitignore') -Value 'src/ignored.bin'
Invoke-TestGit @('add', '.')
Invoke-TestGit @('-c', 'user.name=Verification Fixture', '-c', 'user.email=fixture@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', 'Fixture baseline')
$baseline = Snapshot
Assert-VerificationSourceStable $baseline (Snapshot)
Set-Content -LiteralPath (Join-Path $testRoot 'docs/note.md') -Value 'outside input scope'
Set-Content -LiteralPath (Join-Path $testRoot 'src/ignored.bin') -Value 'ignored input'
Assert-VerificationSourceStable $baseline (Snapshot)
Set-Content -LiteralPath (Join-Path $testRoot 'src/example.cs') -Value 'changed tracked source' -NoNewline
$modified = Snapshot
Assert-Changed $baseline $modified 'Unstaged source edit'
Invoke-TestGit @('add', 'src/example.cs')
Assert-VerificationSourceStable $modified (Snapshot)
Set-Content -LiteralPath (Join-Path $testRoot 'src/new file.cs') -Value 'new source one' -NoNewline
$newFile = Snapshot
Assert-Changed $modified $newFile 'Untracked source addition'
Set-Content -LiteralPath (Join-Path $testRoot 'src/new file.cs') -Value 'new source two' -NoNewline
Assert-Changed $newFile (Snapshot) 'Untracked content change'
Write-Host "PASS: stable source, scoped exclusions, tracked edit, staging equivalence, new file and new-file edit. Fixture: $testRoot"
