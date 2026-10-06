# Beta 2b item 3: Rekindled camping, readiness

**Decision:** Core camping is built and verified live on disposable hosts with its flags on and off (2026-10-05), committed and pushed (ModernUO `e69d6fadb`, ShardContent `9a19e4a`) and deployed with the flags off (2026-10-06). **The owner acknowledged both flags on 2026-10-06 and approved the three new strings**; `campingStarterKit` and `campingFires` are now **on** in source and deployed (config redeploy, server stopped). Closes the core package of Beta 2b item 3; camp travel (your idea) is a separate later 2b item. Evidence and the case table: [Beta-2b-Camping-Evidence.md](Beta-2b-Camping-Evidence.md). Design source: [Rekindled-Camping-Design.md](Rekindled-Camping-Design.md).

## Rulings
Core only: everyone lights Kindling at a 50% floor; every new character gets a Bedroll and Kindling (newbied, not bound); signal fire dropped; power and PvP ideas and flavor ideas left out; persistent fire, camp stall and housing hearth after house zoning; camp travel its own later 2b item; **feeding the fire** added by the owner during the build. Full table in the evidence doc.

## What it does (behind the flags)
- **Kit** (`campingStarterKit`): a Bedroll if the character has none, and Kindling topped up to 3 in all. Stock campers keep their Bedroll and 5; cooks get stock's 2 topped up. Five overloaded the test start used for the weight check (162 of 187 stones before the kit), hence three. Correction 2026-10-06: that start was stock profession 1, an alchemy-heavy forged-packet start the shard does not offer, not a Warrior; the real Warrior templates carry about 95 of 229, so 3 is cautious and the approved 5 can return.
- **Fires** (`campingFires`):
  - Everyone lights at a chance of at least 50%; skill above 50 raises it.
  - A fire is lit for 100 s + 2 s per point of the lighter's real Camping (100 s at 0, 200 s at 50, 300 s at 100), the last third dim, then embers for 60 s + 1.2 s per point (60 to 180 s). The 50% floor applies to lighting only, so training Camping pays off from the first point. Stock is 90 s lit and 10 s embers.
  - **Feeding:** Kindling used within 1 tile of a campfire resets its duration for the feeder's timing (never shortening a longer one), burning, dim or embers, one Kindling each; a fire lit or fed in the last 5 s is not fed again. To light a second fire, stand 2 tiles away.
- **Unchanged (stock):** the 30 s secure camp, Bedroll logout, dungeon refusal, fires not saved on restart. Embers are not a secure camp.
- **Staff:** `[CampStatus` (flags, numbers, campfires within 40 tiles with state, lighter, age and timing).
- **With a flag off** stock behavior returns exactly (verified live).

## Build
- **ModernUO (two narrow hooks):** `Campfire.cs` (`CampfireTiming`, `TimingProvider`, `Lighter`, `LitAt`, `Feed`) and `Kindling.cs` (`FeedHandler`, `IgniteCheck`, the lit fire remembers its lighter). Stock hard-codes the durations and the ignition roll, and shard code cannot intercept a stock item's double-click. No save-format change.
- **ShardContent:** `CampingService.cs`, a `camping` section and two flags in `shard-rules.json` and `ShardRulesConfiguration.cs`, registered in `ShardBootstrap`, `[CampStatus` in `ShardRulesCommands.cs`.
- **Tests:** `CampingServiceTests` (31), `UorCampfireTests` (12); driver `tests/scenarios/camping/camping_live.py`.

## Verification
Unit: Shard suite 541/541, UOContent suite 1358 pass (2 skipped). Live (flags on, timings scaled): the kit for five templates, lighting at base 0, the fire timeline at skill 100 and 50, feeding (burning, dim, embers, cooldown, weaker feeder), the 30 s secure camp, embers not secure, Bedroll logout. Live (flags off): no kit, stock Bedroll and Kindling, stock 60/90/100 s timing, no feeding. All pass. The dev distribution and saves were not touched.

## Named limits
- **The live runs scaled the timings** (a fire lives about a minute) so they fit a session; the default numbers are covered by unit tests, not waited out live.
- **The `fires` stage ran in two passes** on one build (driver faults fixed between them; see the evidence doc).
- **Stat bonus.** A base-0 character's Camping reads about 19 to 20, so the live "lights some and fails some" check does not distinguish the 50% floor from the stock chance by itself; the floor is proven by the unit tests.
- **Not exercised live:** dungeon refusal and restart behavior (both untouched stock code), Hot Zones, and long-duration (real-number) fires.
- **Skill benefit is modest by design.** Skill buys a better chance to light (50% at the floor up to 100%) and fires about three times as long from 0 to 100, and a skilled camper's Kindling resets a fire to a longer burn than a novice's. No power, no PvP effect.
- **The tweak was verified on the final build** (unit plus a fresh live `kit` and `fires` pass); the flags-off baseline was run before it and is unaffected.

## Owner actions
1. **Flag acknowledgments (done 2026-10-06):** `campingStarterKit` and `campingFires`, each separately. The README rules section has the camping line.
2. **Player text review (approved 2026-10-06):** "You feed the fire.", "The embers flare back to life.", "The fire has only just been tended."
3. **Still open, existing starter overweight:** the Alchemy and Cooking starter is about 228 of 187 stones with no kit. Not this item; flagging it.

## Deploy
The change needs the ModernUO hooks rebuilt into `Distribution` (server stopped), a commit and pin bump in ModernUO first, then `Deploy-Alpha1Baseline.ps1`, as for the cooking deploy. No save-format change, so no snapshot is required for this item. Nothing is deployed.

## Next
Camp travel (its own plan and sign-off, later in Beta 2b), then house zoning and the rotating Hot Dungeon.
