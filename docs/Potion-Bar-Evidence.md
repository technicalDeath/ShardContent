# Potion bar (evidence)

Owner request 2026-10-12. A bar of potion cells below the game window: each with the potion's art and a count, lesser / regular / greater told apart by size, a left click drinks one (taking the weapon off first when both hands are busy and putting it back after), shrink/expand buttons, a docked state, and three Lesser Heal and three Refresh potions for every new character. Server half behind `featureFlags.potionBar` (**off** until the owner says "activate"); the bar itself is client-side and opens by default for **new** profiles (`default-profile.json` `potion_bar_enabled`).

## Research first (before building)
- ClassicUO already has a counter bar (`CounterBarGump`): cells with an item graphic and a count, click or double-click to use, off by default, counts by graphic plus hue. It cannot tell strengths apart (all strengths of a potion share graphic **and** hue: heal 0xF0C, cure 0xF07, refresh 0xF0B, agility 0xF08, strength 0xF09) and does not free a hand.
- Razor (community edition, GPLv3, a ClassicUO plugin on Windows) offers counters and hotkeys, but I could not confirm a graphical potion bar, a forum report says its unequip-drink-re-equip needs hand-tuned delays, and its agents (autoloot, restock, scripting) conflict with the assistant policy (QoL item D). Not bundled. Owner chose: extend ClassicUO, and have the server tell the client each potion's strength.

## Built
| Piece | Where |
| --- | --- |
| Strength channel: the client asks (extended command 0xA7, the serials of potions it found); the server answers with a code per potion (10 x kind + strength 0/1/2), only for the asker's own backpack and only for the 12 potions of the bar | `ShardContent/src/BritanniaRenaissance.Content/PotionBarService.cs` (needs `AllowUnsafeBlocks` in the shard csproj) |
| Starter potions: 3 Lesser Heal and 3 Refresh (the weakest refresh there is; there is no "lesser refresh"), newbied, once per character | same file, `CharacterCreated` |
| Flag `featureFlags.potionBar` | `ShardRulesConfiguration.cs`, `shard-rules.json` |
| Tests | `tests/PotionBarTests.cs` (codes, reply bytes, flag off), `ClientDefaultsTests` pins `potion_bar_enabled` |
| The bar | `ClassicUO/.../Game/UI/Gumps/PotionBarGump.cs`; hooks in `GameScene.Load`, `PacketHandlers.ExtendedCommand` (case 0xA7), `OutgoingPackets.Send_PotionStrengthRequest`, `Profile` (`PotionBarEnabled`, `PotionBarMode`) |

Behavior: placed just below the game window when there is room (hidden when there is not; once dragged it stays); the pack is opened silently once at login so the bar knows what is in it (its window is closed at once); counts follow the pack and its bags that have been opened; the free-hand rule mirrors `BasePotion.HasFreeHand` (a hand is free unless both are in use; a two-handed weapon uses both) and takes off the right-hand weapon (or the two-handed one), waits for the server between steps, drinks, and re-equips even if the drink failed; three states (every potion, only the ones you have, docked to a small bar with an empty bottle). Cells are 29 / 36 / 43 px (lesser / regular / greater), about 10% smaller than the first version.

## Real client (disposable host, flags on there only, 2026-10-12)
New profile: the bar opened below the game window by itself; counts 3 / 5 / 3 appeared at login with the pack never opened by the player; a sword-and-buckler character, hurt, clicked Lesser Heal: drank ("healed : 4"), count 3 to 2, weapon and shield back in their slots; shrunk, docked, reopened and expanded; hover shows name and count. Pictures sent to the owner.

## Known limits / not done
- ~~Potions inside never-opened bags~~ **Fixed 2026-10-12:** the bar opens each plain bag, pouch, box and chest in the pack once, one at a time, and closes its window at once (kegs, books and runebooks are left alone: a keg pours when double-clicked). Checked with a fresh login and potions inside a bag.
- The intermediate frame of the unequip step was not photographed (the shots are about a second apart); the drink succeeding with both hands busy shows it happened.
- Help text: a gated sentence about the bar on the potion topics, to add at activation. No options-window checkbox for the bar yet.

## Activated 2026-10-12
Owner: "Fix potions in bags. Activate". `featureFlags.potionBar` is now true in source and deployed (dev distribution, `Deploy-Alpha1Baseline.ps1`; ModernUO's UOContent was rebuilt into Distribution first because the same deploy carries the Help and scroll-chance code, whose engine hooks are uncommitted). Saves snapshotted first (`work/save-snapshots/saves-20261012-083338-before-potionbar-deploy`). Boot checked: world loaded, no errors, saved on shutdown. Full Shard suite 1,273 passing. Client: `cuo.dll` and `Data/Profiles/default.json` are installed in `ClassicUO/bin/dist`; the bar opens for new profiles (existing profiles keep their setting). Nothing committed or pushed.
