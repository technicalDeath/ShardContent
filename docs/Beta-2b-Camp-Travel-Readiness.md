# Beta 2b item 4: Camp travel and the Hot Zone travel warning, readiness

**Decision:** Built and verified live on disposable hosts (2026-10-06) and committed locally (ModernUO `ac1d0e2c8`, then ShardContent on top of it). **Nothing is pushed, deployed or switched on.** `campingTravel` (camp travel, and the camp-travel warning) and `hotZoneTravelWarning` (the warning before Recall and gates) are both **off** in source and wait for the owner's separate acknowledgments. Closes item 4 of Beta 2b; house zoning and the rotating Hot Dungeon are the next Beta 2b items. Plan, rulings and the case table: [Beta-2b-Camp-Travel-Plan.md](Beta-2b-Camp-Travel-Plan.md).

## Rulings
Trigger `[CampTravel` and a gump; destination any secure fire lit by a party member; bonded pets travel as with Recall; places per fire from the lighter's Camping, the owner's own table (1 at 50, one more per 10, 6 at 100, none below 50), because a flat cap is easy to get around by arriving and lighting a new fire. Added by the owner during the build: tell the lighter the fire's status and the command, and warn a blue player before camp travel, Recall or a gate takes them into a Hot Zone, with a "do not show me this warning again when traveling" checkbox. Full table in the plan.

## What it does (behind the flags)
- **Camp travel** (`campingTravel`, needs `campingFires`):
  - `[CampTravel` lists the fires lit by your party members (name, distance, a one-word state, `[HOT ZONE]` where it applies). Picking one re-checks it and asks you to confirm (cost, cooldown, wait, pets, places left).
  - After a 5 s wait you arrive within 2 tiles of the fire with the Recall sound. 2 Kindling, a 30-minute cooldown per account, and each fire takes as many arrivals as its lighter's Camping allows over the fire's life.
  - Everything is checked when asked, on confirming, every quarter second of the wait and at arrival. Refused: dead, not in the lighter's party, the fire gone, embers or not yet secure (8 s on test hosts, 30 s shipped), no places, the lighter under Camping 50, criminal, murderer, Knocked Out, combat within 30 s, overloaded, unable to move, carrying the sigil, leaving a Hot Zone, either end failing the stock Recall region checks (so Felucca dungeons both ways), no open ground, cooldown, too little Kindling. The wait is cancelled by moving, damage and casting.
  - Bonded pets within 3 tiles that are following or guarding come with you, as with Recall.
- **The lighter is kept informed:** when the fire is lit (the command and how many places their Camping gives, or what it takes), when it is secure (places left), burning low, embers, relit (not echoed to the lighter who fed it themselves, except the travel news), burned out (with how many travelled), and on each arrival (count, and when full).
- **Hot Zone warning:** a blue player (not criminal, not a murderer, not staff) about to enter a Hot Zone from outside one is told what the risk is and must confirm, for camp travel (inside its confirmation), Recall (scroll, spell, runebook, rune), Gate Travel gates, other moongates and public moongates (Buccaneer's Den). The checkbox saves the choice on the account; `[TravelWarning on|off` shows and changes it. Not asked: criminals, travel from one Hot Zone to another or out of one, a destination that is not Hot, flag off.
- **Staff:** `[CampStatus` also shows each fire's travel state (secure, places used of capacity, Hot Zone), the settings and the caller's cooldown. Every arrival, and every trip refused during the wait, is written to the audit log.
- **With the flags off:** `[CampTravel` says travel is not available, the lighter is told nothing, and Recall and gates behave as stock.

## Build
- **ModernUO (commit `ac1d0e2c8`, inert by default):** `Campfire.Active` and `CreatedAt`; `SpellHelper.TravelConfirmation`, asked in `RecallSpell.Effect`, `Moongate.BeginConfirmation` and `MoongateGump`. No save-format change.
- **ShardContent:** `CampTravelService.cs`, `TravelWarningService.cs`, `OutdoorHotZonePolicy.IsHot(Map, Point3D)`, two flags and a `campTravel` section, `[CampStatus`, `[TravelWarning`, bootstrap registration. The ModernUO pin moved to `ac1d0e2c8`.
- **Tests:** `CampTravelServiceTests`, `TravelWarningServiceTests`, `UorCampfireTests` additions, `UorTravelConfirmationTests`; live driver and probe in `tests/scenarios/camp-travel/`.

## Verification
- **Unit:** full Shard suite 666/666 and UOContent suite 1362 pass (2 skipped), run `20261006T160239312Z-fd8f2d`, on the committed source.
- **Live (disposable host `camp-travel`, flags on, secure 8 s, wait 3 s, fires about two minutes):** every case in the plan's matrix passes in one pass of five stages (`work/camp-travel/final-stages.log`), listed with results in the plan's Evidence section. The dev distribution and saves were not touched.

## Named limits
- **Knocked Out and murderer refusals are unit-tested only.** Staging a Knocked Out player needs a lethal player hit in a Hot Zone, and the murderer test depends on the adjudication hook; the facts feed the same planner the unit tests cover. Staff are never warned and are not restricted by travel rules.
- **The alternate-character cooldown is by design, not a second login.** The cooldown is a tag on the account (the probe report reads it from there); a second character on the same account reads the same tag. A live two-character check was not run.
- **Capacity uses the displayed Camping skill.** The game's skill `Value` adds a stat-based offset to the trained base (about a fifth of the gap to 100 for a Mace Fighter), so a character showing 50 gets a place even if the trained base is 37. That is the number the client shows and every other Camping rule uses.
- **Live timings were scaled** (a fire lives about two minutes; the 30 s secure time was 8 s, the 5 s wait 3 s). The shipped numbers are covered by unit tests, not waited out live.
- **Hot-to-Hot is not warned.** A blue player already in a Hot Zone who travels to another Hot Zone place is not asked; the owner can change this in `TravelWarningService.ShouldWarn`.
- **A moongate confirmation replaces the stock leaving-town prompt for the warned player.** The player is asked once, with the stronger warning; criminals still see the stock prompt (verified live).
- **Not covered:** static dungeon teleporters, Sacred Journey (Chivalry is not in this era), the Bracelet of Binding (it casts the same Recall spell, so it is covered by the same hook but was not run), boats.
- **A pending Recall confirmation expires after two minutes**, and confirming while casting something else answers "too busy" and spends nothing.

## Owner actions
1. **Flag acknowledgments, separately:** `campingTravel` (camp travel and its Hot Zone warning) and `hotZoneTravelWarning` (the warning for Recall and gates). The README rules section gets the lines when each goes on.
2. **Rulings to confirm:** no warning for Hot-to-Hot travel; leaving a Hot Zone by camp travel is refused (signed off in the plan, restated because the new warning makes going *to* a Hot Zone camp allowed); the murderer rule (murderers cannot use camp travel).
3. **Player text review:** the strings listed in the plan's Evidence section.

## Deploy
The ModernUO hooks must be rebuilt into `Distribution` (server stopped), ModernUO `ac1d0e2c8` and the ShardContent commit pushed, then `Deploy-Alpha1Baseline.ps1`, as for the camping deploy. No save-format change, so no snapshot is required for this item. Nothing is deployed.

## Next
House zoning and the rotating Hot Dungeon (the rest of Beta 2b), each with its own plan and sign-off.
