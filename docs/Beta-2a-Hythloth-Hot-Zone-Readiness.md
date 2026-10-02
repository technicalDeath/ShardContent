# Beta 2a item 3: Hythloth joins the permanent Hot Zones (readiness)

**Decision:** Ready and **activated** (owner sign-off 2026-10-02, "turn it on when verified"): `featureFlags.hythlothHotZone` is true in source and deployed `shard-rules.json`. This closes Beta 2a scope item 3 and, with the Ward and Mastery items, Beta 2a.

## Reused accepted evidence
- The outdoor Hot Zone rules (K-1 to K-6, K-10) and their Alpha 3 evidence apply unchanged; this item only widens the membership check to one stock dungeon region.

## Current-source review
Design and results are in [the audit](Beta-2a-Hythloth-Hot-Zone-Audit.md). `OutdoorHotZonePolicy` returns `Hythloth` inside that stock dungeon region when the flag is on; config `hotZones.dungeonRegions`; a post-boot check stops the server if a listed region does not exist. No ModernUO change.

## New verification
`HythlothHotZoneTests` (Shard suite 408/408); live on a disposable host, 18 cases passed plus one observation: the real entrance teleporter both ways, Knocked Out loot and Execute, theft with a Ward, Shame and Ice controls, login and restart, and a flag-off control.

## Gate and validator
Source and deployed `shard-rules.json` match with `hythlothHotZone` true. The validator requires `hotZones` and a Hythloth entry for the flag. The dev server has not been started since the deploy; the same build and data booted on the disposable copies and logged "Validated Hot Zone dungeon regions: Hythloth (Felucca)."

## Readiness limits
- **Owner ruling: Hythloth is a Hot Zone, not a Hot Dungeon.** It has no reward premium (K-11). The Beta 2b rotating Hot Dungeon remains a separate system; it can reuse the dungeon-region membership built here.
- Travel is stock: no Recall or Gate into or out of Felucca dungeons, so every exit is the walk out onto Fire Island, which is also Hot.
- Automatic murder adjudication is off, so an Execute of a blue in Hythloth leads to the stock murder report, exactly as outdoors.
- Not exercised live: delayed spells, fields and poison across the entrance (the teleporter moves players far apart, so nothing can be targeted across it), and pets entering Hythloth (unchanged code path).
- New player text (the Hythloth entry line, the Ward lines in `[Welcome` and `[TheftStatus`, the README Hot Zones bullet) is for the owner's review with the release.
- Two UOContent tests fail on ModernUO HEAD independent of this item (see the Elf audit).
- Nothing is committed or pushed.
