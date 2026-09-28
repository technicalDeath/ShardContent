# Stock ModernUO defaults on a UOR shard

**Status:** awaiting owner rulings, prepared 2026-09-28.

**Findings are from reading code**; confirm each before changing it. This audit looks for stock ModernUO systems and settings that are active on this shard although they are probably later than UOR (April 2000) and were never reviewed. It started when we found the Young player system running.

Paths are in `ModernUO/Projects/UOContent` unless noted.

## How these are switched

- **Content feature flags** are seeded into `Distribution/Configuration/FeatureFlags/flags.json`. The file then overrides the code defaults (`Engines/FeatureFlags/FeatureFlagManager.cs:751-803, 900-907`). Change them with `[FF <key> <true|false>` or `[FeatureAdmin` (Administrator), or by editing the deployed `flags.json`. The shard's era-gates file cannot change them.
- **Shard control:** `flags.json` is not deployed from source today. If the owner rules on flags, add the flags to `ShardContent/data/configuration` and to `Deploy-Alpha1Baseline.ps1`, so the ruling can't be lost with a runtime file.

## Decisions (most gameplay impact first)

| # | System | What it does now | Evidence | Assessment | How to change | Ruling |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Young player system** (`young_player_system`, default on) | New accounts, for 40 h or until 450 total skill: keep all items on death; ghost teleported to a healer; poison immunity; instant logout; "(Young)" suffix; **monsters won't attack them** in Young-protected regions (Felucca towns and wilderness by default); can't help non-Young players | `Accounting/Account.cs:254`, `Mobiles/PlayerMobile.cs:688, 2470, 2493, 2587, 3795, 4027, 4035`, `Regions/BaseRegion.cs:43` | Likely post-UOR. Contradicts design §16 ("no account-age immunity") | `[FF young_player_system false` | |
| 2 | **Passive Detect Hidden** (`passive_detect_hidden`, default on) | A moving player with Detect Hidden automatically reveals nearby hidden players, Felucca only | `Skills/DetectHidden.cs:63-72`, `PlayerMobile.cs:3494-3499` | Likely post-UOR; also skill audit SK-007 | `[FF passive_detect_hidden false` | |
| 3 | **Honor virtue** | Honoring a full-HP target gives a "perfection" damage bonus, and Embrace Honor +25% melee. It works in PvP pre-ML and affects taming | `Engines/Virtues/Honor.cs:16`, `Items/Weapons/BaseWeapon.cs:1911-1921`, `Skills/AnimalTaming.cs:230` | Post-UOR (Samurai Empire era) | Code gate: no effect unless `Core.SE` | |
| 4 | **Sacrifice and the rest of the virtues** (Justice, Compassion, Valor) | Sacrifice lets a dead player **self-resurrect** by trading fame. Justice awards for killing murderers. The virtue gump opens from any client | `Engines/Virtues/Sacrifice.cs:17, 32`, `Justice.cs:85`, `PlayerMobile.cs:2536-2569`, virtue packet handler `IncomingPlayerPackets.cs:229` | Post-UOR | One gate at the virtue packet or gump registration disables them all | |
| 5 | **One house per account** | Blocks placing, transferring or claiming a second house on an account | `Multis/Houses/BaseHouse.cs:3541` and callers (`HouseDeed.cs`, `HousePlacementTool.cs`) | Likely post-UOR (UOR allowed several). May suit the Beta 2 housing design | Code change in the `HasAccountHouse` callers, or keep as a deviation | |
| 6 | **Mount stamina** (`stamina.enableMountStamina`, default on) | Running while mounted drains the mount's stamina | `Misc/StaminaSystem.cs:51` | Unsure; possibly post-UOR | Setting `stamina.enableMountStamina = False` via the era-gates file | |
| 7 | **Insta-hit** (`melee.enableInstaHit`) | The stock UOR default is **off**; the shard's era-gates file turns it **on** | `Items/Weapons/BaseWeapon.cs:38`; `data/configuration/modernuo-era-gates.json` | A deliberate shard deviation; confirm it (also contract review J-1) | Era-gates file | |
| 8 | **Insurance flag check gap** | `EraGateConfiguration` validates `insurance.enable`, but the live switch is the `insurance` content feature flag (currently off), so turning the flag on wouldn't be caught | `Misc/Insurance.cs:18-19`; `ShardContent/.../EraGateConfiguration.cs:83-89` | A tooling gap, not live behavior | Validate the feature flag too | |
| 9 | Party system; duel gump ("i wish to duel") | Parties with shared looting; a non-OSI duel setup gump (duels can't start with no arenas) | `Engines/Party/*`; `Engines/ConPVP/DuelContext.cs:1242, 1399` | Low impact; party timing unsure | Leave, or block the duel speech hook or gump | |

## Already handled (no action)

- **Era-gates file** (validated false): insurance setting, veteran rewards and skill-cap rewards, ML quests, pet bonding, pets stand down on command.
- **`expansion.json`:** UOR, Felucca only; AoS/SE/ML feature bits off.
- **Alpha 2b world generation:** asserts zero champion spawns and no Faction infrastructure, and excludes post-UOR spawner types. This neutralizes champions, power scrolls, Valor and most later quest NPCs.
- **Anti-macro:** disabled by the shard's `antimacro.json` (its owner ruling is SK-004).
- **Smith BODs:** an owner-approved deviation; see contract review I-1 to I-4.
- **Era-correct by stock `Core` checks:** property lists, visible damage, stealing, stat caps, murder bounties, buff icons, account gold, T2A craft menus.
- **Off by default:** factions, ethics, chat, auto-restart.
