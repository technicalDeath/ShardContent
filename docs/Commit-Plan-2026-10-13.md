# Commit plan for the 2026-10-13 work (nothing committed; for the owner to say go)

Written so a later session can commit in a sensible order when asked. Verified state when written: full suites pass (ModernUO UOContent 1,404 with 2 skipped, shard 1,406, client 250); everything below is deployed to the dev distribution (server stopped) and the new `cuo.dll` is in `ClassicUO/bin/dist`.

## Order matters: ModernUO first, then the pin

1. **ModernUO** (three small engine hooks and their tests; no save-format change):
   - `Projects/Server/Items/Item.cs`: `Item.PropertyListBuilder` (item tooltips).
   - `Projects/UOContent/Engines/Character Creation/CharacterCreation.cs`: `StartingCitiesFilter` (Britain-only start).
   - `Projects/UOContent/Misc/LootPack.cs`: `LootPackEntry.WeaponLootSlayerAllowed` (Silver-only drops).
   - Tests: `ItemPropertyListBuilderTests`, `CharacterCreationStartingCitiesTests`, `LootPackWeaponSlayerTests`.
   - Leave out `Distribution/Configuration/` (deployed copies, untracked as before).
2. **Bump the pin** to the new ModernUO commit in all three places, or the deploy refuses: `ShardContent/data/configuration/shard-rules.json` (`pinnedModernUoCommit`), `ShardContent/data/world-generation/alpha2b/world-generation.json`, and the `Commit` constant in `ShardContent/tests/Alpha2bWorldGenerationConfigurationTests.cs`. Then redeploy once (Deploy-Alpha1Baseline) and run the shard suite.
3. **ShardContent**, suggested split:
   - *Help text and guide*: `data/help/*.json`, `WelcomeGuide*.cs`, the guide and help tests (Who teaches what, Wear and repair, Moongates, Bars and numbers, Furnisher paragraph, weapon and armor stat tables removed).
   - *Item tooltips*: `ItemTooltipService.cs`, `MenuBarService.cs`, flag in `ShardRulesConfiguration.cs`/`shard-rules.json`, `ShardBootstrap.cs`, `ItemTooltipTests.cs`.
   - *Britain-only start*: `BritainStartService.cs`, flag, `BritainStartTests.cs`.
   - *Silver-only slayers*: `SilverOnlyWeaponLoot.cs`, `SilverOnlyWeaponLootTests.cs`.
   - *Client defaults*: `data/client/default-profile.json`, `tests/ClientDefaultsTests.cs`.
   - *Probe*: `tests/scenarios/alpha3-tools/TestOnlyProbe.cs` (`[TestOnlyMagic`, `[TestOnlySlayerLoot`).
   - *Docs*: the evidence files (`Item-Tooltips`, `Britain-Start`, `Slayer-Loot`, `Health-Bar-Declutter`, `Moongates`, `Wear-And-Repair`), `House-Lockdown-Reminder-Plan.md`, this file, and the edited To-Do, New-Player-Pass, Client-Defaults and audit docs.
   - Do not sweep in `docs/cosmetic-rewards/` and `tools/cosmetic-catalog/` unless the owner wants them (they were untracked before today).
4. **ClassicUO** (the client; one commit or a few): tooltip switch (`ClientFeatures`, `GameCursor`, `GridLootGump`, `ShopGump`, `TopBarGump`, `PacketHandlers`), health bars (`FriendlyHealthTracker`, `HealthLinesManager`, `Profile`, `OptionsGump`), body pin (`WorldMapGump`), potion hotkeys (`MacroManager`, `AutoUse`), the combat bar caption ("stones (weight)"), and the player-bar offer (`GameScene`), plus `tests/ClassicUO.UnitTests/Game/Managers/FriendlyHealthTrackerTests.cs`.
5. **Navrey**: only `Agent/Commands/CommandEngine.Actions.cs` (`city=N`) is from today; `VendorStock.cs` and `Narrator.cs` were already modified before and are not mine.
6. **Workspace files outside git**: `CLAUDE.md`, the root `README.md` and `.claude/` are not in a repository (by design); they were updated and need nothing.

## Flags that went live on the dev host today (all on the owner's word)
`itemTooltips`, `startInBritainOnly`. (Silver-only slayers has no flag.) Earlier today `autoUse`, `damageNumbers`, `healNumbers`, `helpGumps`, `scrollSuccessChance` were activated and are already committed except the later tweaks listed above.

## Still unpushed before today
ModernUO `136e573c8`, ShardContent `9e3163b` and `f2bcfbf`, ClassicUO `de9aabeba`.

## Added later on 2026-10-14 (all ShardContent unless noted; full suites then: UOContent 1,404 with 2 skipped, shard 1,457)
- *One-time tips*: `NewPlayerTipsService.cs`, `NewPlayerTipsTests.cs`, flag `newPlayerTips` (OFF) in `ShardRulesConfiguration.cs` and `shard-rules.json`; commit with the Britain-only/tooltips group or its own.
- *Poison hint names cure potions held*: `PoisonReliefService.cs` and `PoisonReliefTests.cs` (flag `poisonRelief`, already on).
- *Auto-pickup*: `AutoPickupService.cs`, `AutoPickupTests.cs`, flag `autoPickup` (OFF), `Ammo-Reagent-Auto-Pickup-Plan.md` and `-Evidence.md`.
- *Guide Commands page*: `[Tips` and `[Pickup` lines (gated), in `WelcomeGuide.cs`.
- *Client text*: three bandage lines in `data/client/Clilocs.txt` and `ClientDefaultsTests.cs` (the client copy in `ClassicUO/bin/dist` is already updated).
- *ClassicUO*: combat bar seeds empty weapon and tool slots from the pack (`CombatBarGump.cs`).
- *Tool*: `tools/help-text/host.ps1` switches the two new flags on for test hosts.
- *Docs*: `New-Player-Help-Messages.md` (updates at the bottom), `To-Do-List.md`, `New-Player-Pass-2026-10-13.md` rows 47 and 48.
No ModernUO change was needed for any of these. Deploy would also need a Deploy-Alpha1Baseline run for the shard DLL and config (both new flags ship off).

## Also added 2026-10-14 (late): house lockdown reminder
- **ModernUO** (one more engine hook, commit with the three above and include it in the pin bump): `Projects/Server/Items/Item.cs` adds `Item.DroppedToWorld`.
- **ShardContent**: `HouseReminderService.cs`, `HouseReminderTests.cs`, flag `houseReminder` (OFF), `House-Lockdown-Reminder-Plan.md` (build note at the end).
- The dev Distribution needs a UOContent/Server rebuild before the shard DLL that references the event is deployed.
