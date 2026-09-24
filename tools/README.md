# Tooling

Add deterministic import, validation, and deployment scripts here. Scripts should accept paths as
parameters rather than assuming that contributors have the same local workspace layout.

`Export-FeluccaBankCandidates.ps1` reads the authoritative ModernUO Felucca vendor spawns and
writes a review-only JSON list of Banker coordinates. It never edits `shard-rules.json` or enables
bank protection. Supply an explicit output path, for example:

```powershell
.\Export-FeluccaBankCandidates.ps1 -ModernUOPath ..\..\ModernUO -OutputPath ..\docs\generated\felucca-bank-candidates.json
```

The output records the source SHA-256 and candidate spawner GUIDs so staff can survey actual bank
premises and approve polygons without relying on stale client POIs or invented radii.
