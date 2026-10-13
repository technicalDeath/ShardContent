# Damage and heal numbers over heads

Owner request, 2026-10-13 (after the question "does ClassicUO have overhead damage and heal numbers that can be enabled?"): "do both damage and heal numbers". Built behind two new server flags. **Activated 2026-10-13 on the owner's "activate anything that hasn't been yet"**: both flags are on in the source and deployed to dev, with the engine hook committed (ModernUO) and the pin bumped.

## What exists and what was missing

| | ClassicUO | ModernUO |
| --- | --- | --- |
| Damage | Draws floating numbers (yellow on you, red on others) whenever the server sends the damage packet (0x0B, or the 0xBF sub-command 0x22 for old clients). There was no on/off switch, only a "(DPS: n)" suffix option, default on. | Has the stock `Mobile.VisibleDamageType` (None, Related, Everyone, Selective). `ExpansionConfiguration` sets it from the `visibleDamage` setting, which defaults to `Core.AOS`, so this UOR shard sent none. |
| Heal | Nothing. | The protocol has no heal packet, and `Mobile.Heal` told no one the amount (a bandage even passes `message: false`). |

## Design

- **Damage numbers** (`featureFlags.damageNumbers`). With the flag on, `CombatNumbersService` sets `Mobile.VisibleDamageType = Related` once the server has started (after ExpansionConfiguration). "Related" is the stock behaviour: the damage packet goes to the client of whoever took the damage and the client of whoever dealt it (or the master of a pet that did either). Nobody else sees a number.
- **Heal numbers** (`featureFlags.healNumbers`).
  - **Engine hook:** `Mobile.HealApplied` (an event; `ModernUO/Projects/Server/Mobiles/Mobile.cs`), raised from `Mobile.Heal` after the heal has been applied, with the mobile healed, who healed it, and the hit points **really restored** (after the region, `OnHeal` and the maximum), never zero. Tests: `MobileHealHookTests` (5). `Mobile.HealHandler` could not be used, because it is one delegate that `KnockedOutService` already assigns, and it runs before the amount is final.
  - **Shard command:** extended command 0xAB (`CombatNumbersService.HealPacket`): the serial of the mobile healed and the hit points restored, two bytes. It goes to the healed player and to the healer (a pet's master counts as the pet's player), the same two parties as damage. Potions, bandages and spells all end in `Mobile.Heal`, so all three show. Regeneration is not a heal and shows nothing.
- **Client** (ClassicUO): a green "+N" (hue 0x44) floats up like a damage number but is not counted towards DPS. One new profile switch, `show_overhead_numbers` (default true), in **Options, Combat-Spells, "Show damage and healing numbers over heads"**, hides both kinds. A new profile also starts with the "(DPS: n)" suffix **off** (`show_d_p_s_with_damage_numbers` false in `default-profile.json`): it is combat analytics and clutter for a new player.
- **Era note.** ModernUO ties visible damage to AOS, and a UOR-era client had no floating numbers. The owner asked for them, so they are a deliberate departure, behind a flag, and only on the client's own damage and heals.

## Files

Engine: `Mobile.cs` (the event), `UOContent.Tests/Tests/Mobiles/MobileHealHookTests.cs`. Server (ShardContent): `CombatNumbersService.cs`, `ShardRulesConfiguration.cs` and `shard-rules.json` (`damageNumbers`, `healNumbers`), `ShardBootstrap.cs`, `tests/CombatNumbersTests.cs` (5), `tools/help-text/host.ps1` (turns both on for the test host and copies the engine DLL). Client (ClassicUO): `Game/Managers/OverheadNumbers.cs` (new), `Profile.cs`, `PacketHandlers.cs`, `EntityTextContainer.cs`, `WorldTextManager.cs`, `OptionsGump.cs`.

## Evidence

Real client (ClassicUO from `ClassicUO/bin/dist`), disposable host with both flags on (host only; the source flags stay false), a new character, 2026-10-13. Screenshots in `work/player-client/HelpAlpha/shots/` and contact sheets in `work/help-gumps/` (`p1-sheet2`, `h1-sheet2`, `q1-sheet`), sent to the owner.

| # | Case | Result |
| --- | --- | --- |
| 1 | Damage taken: a Greater poison ticking on the character | A yellow number floats over the character on each tick ("6 (DPS: 6)", then the running DPS) |
| 2 | Heal: wounded to 15 hit points with a Lesser Heal potion and a bandage in use | A green "+9" and later "+15" float over the character; the health bar rises with them |
| 3 | The Options switch | Present on Combat-Spells, ticked by default. Unticked and OK: the same poison drains the health bar and no number shows |
| 4 | Engine hook | `MobileHealHookTests`: who and by whom; the real amount after the maximum (asked 50, 7 restored, reported 7); a self heal names the mobile as its own healer; nothing is reported for a full or a dead mobile |
| 5 | Packet | `CombatNumbersTests`: layout, two-byte clamp, extended-command length, no clash with 0xA7 to 0xAA |

Not observed in the real client: damage **dealt** to a creature (the number the attacker sees over its target; the staged rat died before a screenshot, the cow was not engaged), a heal on **another** player, and a pet's master. They use the same packets and drawing as the cases above; the recipients are the stock "Related" rule and `CombatNumbersService.OnHealApplied`.

## Activation (2026-10-13)

Both flags are on in `shard-rules.json`. Because of the engine hook the deploy needed: commit the ModernUO change and bump `pinnedModernUoCommit` in the three places (`skill shard-server`), rebuild `UOContent.csproj` (which also rebuilds `Server.dll`) into `Distribution` with the server stopped, then `Deploy-Alpha1Baseline.ps1`. Add the numbers and the new Options switch to the root `README.md` rules section at that point.
