# Felucca's season: summer (2026-10-18)

The owner asked, 2026-10-18:

> "change the season of the shard so that there are leaves on the trees and such ... I want the world to feel like pre-trammel felucca"

**Built, host-tested and deployed to dev on 2026-10-18. Not committed.**

## Why the trees were bare

Stock ModernUO's `Data/map-definitions.json` gives Felucca season 4, Desolation: the look Felucca got when Trammel split off. The client draws every tree bare and swaps flowers and plants for gravestones, skulls and bones. Britannia before Trammel had ordinary seasons. Season 1, Summer, is the client's normal art: full trees, flowers and ferns, nothing swapped.

## The change

| What | Where |
| --- | --- |
| The setting | `data/configuration/shard-rules.json`: `"worldSeason": { "felucca": 1 }`. Values: 0 spring, 1 summer, 2 fall, 3 winter, 4 desolation; -1 keeps the map definition's season |
| The code | `WorldSeason.cs`: on server start it sets `Map.Felucca.Season` from the setting. The server already sends a map's season at login and on every map change (`Mobile.GetSeason`), so nothing else is needed and nothing is saved. Staff check: `[SeasonStatus`. The validator rejects values outside -1 to 4 |
| Engine | Unchanged |
| Tests | `tests/WorldSeasonTests.cs` (6). Full shard suite: 1,711 passed (`work/agent-verification/runs/20261018T140054985Z-9ffe69`) |

## Host test (`spawn-areas`)

- `[SeasonStatus`: "Felucca season: summer (configured 1, map definition desolation)."
- Real-client shots, before (desolation) and after (summer), at the same spots: Haunted Wood, Bay Marsh, Castle Woods, North Hills, Harpy Crags. Kept in `work/spawn-design/flavor-shots/` and `work/spawn-design/season-shots/` (scratch). In summer the trees have leaves, with firs, flowers and ferns, and the flowers no longer read as gravestones.

## To deploy

The setting travels with `shard-rules.json` in `Deploy-Alpha1Baseline.ps1`, and the shard DLL carries the code. Players see it at their next login.
