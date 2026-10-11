# world-decorating

Tools for furnishing and decorating real places in the shard's world. The method (semantic reasoning about each object, its group and the space), the workflow and every trap are in the skill `.claude/skills/world-decorating/SKILL.md`; this is only the file map. All scripts run from the workspace root after `. .\.claude\scripts\Use-Toolchain.ps1`.

| File | What |
| --- | --- |
| `uo_world.py` | Offline map survey: `buildings`, `plan`, `open`, `signs` (reads `UOData` map and statics plus the shard's generated world data). |
| `cliloc.py` | Reads the client text table (BWT compressed) to name shop signs. |
| `planner.py` | Checks a layout against the server's real floor and against the declared meaning of each piece (`against`, `serves`, `on`, `group`, `role`), draws the plan, writes the placement file; `facings` and `sheet` commands show a piece's facings. |
| `sites/*.json`, `sites/*.walkgrid.json` | Site configs and the server walk grids they use (Counselor's Guild east, Britain). |
| `layouts/*.json` | Layouts as data: `[piece, facing, x, y, {semantic fields}]` per piece. `counselor-guild-east.json` is the owner-approved Furnisher showroom (37 pieces). |
| `build_furnishers_config.py` | Builds the shard's Furnisher data (`ShardContent/data/configuration/furnishers.json`: the 37 pieces, their prices and facings, the vendor's spot and the 229 hall display items) from the approved selection and the showroom layout, after `planner.py` has checked the layout. Run it again after any change to either source. |
| `rig/Start-DecorRig.ps1`, `rig/Stop-DecorRig.ps1` | One command each to start and stop the disposable host, camera character and real client. `-PrepareHost { param($h) ... }` runs before the server starts, to swap in a build under test, add data files or flags, and add probes (as used for the Furnisher: `ShardContent/tests/scenarios/furnishers/`). |
| `rig/rig.py`, `rig/lay.py`, `rig/tp.py`, `rig/shoot.py` | Rig helpers: staff commands, laying a layout, moving the camera, taking cropped client shots. |

The test probe (`[TestOnlyDecor`, `[TestOnlyWalkGrid`) is `ShardContent/tests/scenarios/cosmetic-catalog/DecorProbe.cs`; it is test-only and never ships.

Outputs go to `work/decorating/` (plans, shots, rig record) and `work/cosmetics/layouts/` (placement files); both are scratch.
