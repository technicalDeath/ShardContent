# Poison relief: readiness

**Decision:** Built and verified (unit, engine, live on a disposable host, real client) on 2026-10-11. **Nothing is committed, pushed or deployed, and `featureFlags.poisonRelief` is off.** Plan `Poison-Relief-Plan.md`, evidence `Poison-Relief-Evidence.md`.

## What it does (behind the flag)

- New characters start with 5 newbied Lesser Cure potions.
- The first time a character who cannot cure with a bandage is poisoned, one message explains what ends the poison; the Poisoned buff tooltip gains a line about bandages.
- After a poison ends or is cured, Lesser poison from a monster, trap or field cannot land on an ordinary player for 30 seconds, and the player is told. Stronger poison and poison from players are stock.

## Verification

Engine 13/13 (4 new), Shard suite 1198/1198 (39 new), live host 18/18, real-client pictures of the message and the tooltip shown to the owner. Details in the evidence.

## To ship it

1. **Commit ModernUO** (`PlayerMobile.cs` and `PlayerMobileShardHookTests.cs` only), rebuild `UOContent` into `Distribution` with the server stopped, **bump the pin** to the new ModernUO hash in `shard-rules.json`, `world-generation.json` and `Alpha2bWorldGenerationConfigurationTests.cs`.
2. **Commit ShardContent** selectively (the repo also holds the Furnisher files and the owner's housing notes): `PoisonReliefService.cs`, `PoisonReliefTests.cs`, `tests/scenarios/poison-relief/`, the `poisonRelief` and `noviceCombat`-style edits in `ShardRulesConfiguration.cs`, `ShardBootstrap.cs`, `shard-rules.json`, the buff icon edits (`BuffIconRules.cs`, `BuffIconService.cs`, `buff-icons.json`) and the three Poison-Relief docs.
3. **Deploy** with `Deploy-Alpha1Baseline.ps1` (server stopped); the flag ships off.
4. **Activate** only on the owner's explicit "activate": set `featureFlags.poisonRelief` true, redeploy, start; then add the README line below.

## README rules line, for activation

"**Poison relief.** New characters start with 5 Lesser Cure potions (newbied). The first time a character who cannot cure with a bandage is poisoned, the game explains what ends the poison. After a poison ends or is cured, Lesser poison from a monster cannot land on you again for 30 seconds; stronger poison and poison from other players are unaffected."

## Owner actions

1. Say whether to commit, push and deploy (the engine hook means a ModernUO commit and the pin bump), and later "activate".
2. Review the three player-facing texts listed in the evidence.
3. Optional: a bandage floor (starter bandages are nearly useless at Healing 0) is a separate idea, not built.
