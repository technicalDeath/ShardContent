# Alpha 2 geography review exports

These files are reproducible, review-only extracts from the pinned ModernUO data. They identify
Felucca Banker spawners and candidate UOR-era dungeon regions so staff can survey the actual
premises and approve explicit theft-protection polygons.

They are source evidence for the runtime configuration. They do not create a combat-safe area or
change snooping. The authoritative runtime lists now contain the approved 18 compact bank
envelopes and the ten UOR-era dungeon rectangles; later-era/special regions remain deferred.

## Staff approval checklist

For each Banker candidate, the current survey uses a compact 24-by-24-tile envelope centered on
the observed banker spawner/approach tile, providing about 5–6 tiles outside the bank frontage
without creating a town-wide or neighboring-building bubble. Each boundary transition is
announced to the player. The center-tile observations are retained in `work/alpha2-bank-survey.log`.

For Cool-Dungeon selection, review the marked UOR-era candidates in the dungeon export—Covetous,
Deceit, Despise, Destard, Fire, Hythloth, Ice, Khaldun, Shame, and Wrong—and approve the exact
Felucca rectangles or polygons to use. Later-era and special regions remain review-only unless
staff explicitly approve them for a separate era decision.

Record any later map corrections in `data/configuration/shard-rules.json`, set
`alpha2EnablementAcknowledged` only after the geometry review is complete, and run:

```powershell
.\tools\Verify-Alpha2Readiness.ps1
```

The verifier must report matching ModernUO pin, clean repositories, both polygon counts greater
than zero, and `ReadyForEnablement: True`. Keep only explicitly approved theft/safe-world flags
enabled; murder and Knocked Out remain separate gates.

Regenerate with:

```powershell
.\tools\Export-FeluccaBankCandidates.ps1 -ModernUOPath ..\..\ModernUO `
  -OutputPath .\docs\generated\alpha2\felucca-bank-candidates.json
.\tools\Export-FeluccaDungeonCandidates.ps1 -ModernUOPath ..\..\ModernUO `
  -OutputPath .\docs\generated\alpha2\felucca-dungeon-candidates.json
```
