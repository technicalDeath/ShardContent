# Alpha 2 geography review exports

These files are reproducible, review-only extracts from the pinned ModernUO data. They identify
Felucca Banker spawners and candidate UOR-era dungeon regions so staff can survey the actual
premises and approve explicit theft-protection polygons.

They are not runtime configuration. They do not define a bank radius, create a combat-safe area,
enable theft protection, or select Cool-Dungeon polygons. The authoritative runtime lists remain
empty in the checked-in Alpha 1 profile until surveyed geometry is approved.

Regenerate with:

```powershell
.\tools\Export-FeluccaBankCandidates.ps1 -ModernUOPath ..\..\ModernUO `
  -OutputPath .\docs\generated\alpha2\felucca-bank-candidates.json
.\tools\Export-FeluccaDungeonCandidates.ps1 -ModernUOPath ..\..\ModernUO `
  -OutputPath .\docs\generated\alpha2\felucca-dungeon-candidates.json
```
