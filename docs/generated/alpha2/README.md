# Alpha 2 geography review exports

These files are reproducible, review-only extracts from the pinned ModernUO data. They identify
Felucca Banker spawners and candidate UOR-era dungeon regions so staff can survey the actual
premises and approve explicit theft-protection polygons.

They are not runtime configuration. They do not define a bank radius, create a combat-safe area,
enable theft protection, or select Cool-Dungeon polygons. The authoritative runtime lists remain
empty in the checked-in Alpha 1 profile until surveyed geometry is approved.

## Staff approval checklist

For each Banker candidate, survey the actual bank building and immediate apron, then approve an
explicit Felucca polygon that blocks direct player stealing only. Do not infer a radius from the
spawner point and do not include a town, guards, vendors, combat, murder, or retaliation rule in
the polygon decision.

For Cool-Dungeon selection, review the marked UOR-era candidates in the dungeon export—Covetous,
Deceit, Despise, Destard, Fire, Hythloth, Ice, Khaldun, Shame, and Wrong—and approve the exact
Felucca rectangles or polygons to use. Later-era and special regions remain review-only unless
staff explicitly approve them for a separate era decision.

Record the approved map and point lists in `data/configuration/shard-rules.json`, set
`alpha2EnablementAcknowledged` only after the geometry review is complete, and run:

```powershell
.\tools\Verify-Alpha2Readiness.ps1
```

The verifier must report matching ModernUO pin, clean repositories, both polygon counts greater
than zero, and `ReadyForEnablement: True`. Until then, keep all Alpha 2 flags disabled; staging
may use a copied rules file, but synthetic geometry must never be committed as production policy.

Regenerate with:

```powershell
.\tools\Export-FeluccaBankCandidates.ps1 -ModernUOPath ..\..\ModernUO `
  -OutputPath .\docs\generated\alpha2\felucca-bank-candidates.json
.\tools\Export-FeluccaDungeonCandidates.ps1 -ModernUOPath ..\..\ModernUO `
  -OutputPath .\docs\generated\alpha2\felucca-dungeon-candidates.json
```
