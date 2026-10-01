# Beta 1 item 1: cosmetic Elf, plan and evidence

Roadmap: [Beta 1](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md), scope item 1. Design contract: Hot Zones plan §5 "Cosmetic Elf appearance". Readiness record: [Beta-1-Cosmetic-Elf-Readiness.md](Beta-1-Cosmetic-Elf-Readiness.md).

## Owner sign-off (2026-09-30)

The plan was presented first and approved as written. Decisions:
- **Activation:** turn Elf creation on when verified. Done at the end of this item (`CharacterListFlags.ML` true in source and deployed `expansion.json`; `SupportedFeatures.ML` and `SA` stay false).
- **Commits:** local commits per repo, no push.
- **Edge cases left stock:** Disguise Kit (temporarily offers human hair and beards), Polymorph skin hue on human bodies, and the NPC hairstylist that refuses elves. No defensive re-routing of ML-gated racial code; parity tests guard it instead.

## What existed before this pass

- ModernUO `CosmeticElfPolicy` routes equipment and Cu Sidhe checks through the Human gameplay race for player Elves under UOR; `CosmeticElfCreationService` converted a stock Human to Elf after creation. Both were inert while the `CharacterListFlags.ML` bit was false.
- Every ML racial bonus (Human carry weight and Jack of All Trades, Elf +20 mana, +5 energy resist, night sight, regen, harvest, tracking, carving) is guarded by `Core.ML` or `HarvestDefinition.RaceBonus`, so inert under UOR.
- `Body.IsHuman/IsMale/IsFemale/IsGhost` already cover bodies 605-608 via `bodyTable.cfg`.
- ClassicUO gating existed only as an uncommitted edit; Navrey `createcharacter` was Human-only; no Elf tests.

## Changes in this pass

| Repo | Change |
| --- | --- |
| ShardContent | `CosmeticElfCreationService`: pure `AppliesTo` and `ResolveAppearance`; `Configure` renamed `Register` and called last in `ShardBootstrap`, because ModernUO's `Configure` sweep order is unspecified and this observer must run after every starter handler. Tests: `CosmeticElfCreationServiceTests`. `expansion.json` `CharacterListFlags.ML` = true (activation). Test-only probe and drivers in `tests/scenarios/cosmetic-elf/`. |
| ModernUO | Tests only: `UOContent.Tests/Tests/Misc/CosmeticElfParityTests.cs`. No engine change. |
| ClassicUO | `CreateCharAppearanceGump.cs`: Elf button offered on the character-list 0x100 bit alone (no ML feature bit), Gargoyle only with the SA feature, null guards. Fresh NativeAOT `cuo.dll`/`cuo.pdb` in `bin/dist` (old pair backed up under `work/client-dist-backup-20260930/`). |
| Navrey | Same gump change ported. `createcharacter` takes `elf\|human\|gargoyle`, `female`, `hue= hair= hairhue= beard= beardhue=`. New `charraces` probe. |
| Tooling | `New-TestCharacter.ps1 -Appearance`; `Use-Toolchain.ps1` puts `vswhere` on PATH for NativeAOT; `BRCommon.ps1` no longer mistakes a reused PID for a live server. Skills and `CLAUDE.md` updated. |

## Acceptance matrix and results

Dist `cuo.dll` SHA-256 `8459AC76B7569832355E385B27A88BF43C5458DBA4C2F516F51B85CFDC30EB83`. Deployed `BritanniaRenaissance.Content.dll` SHA-256 `B7218896BD70827E8C6716E5BA4FF6F04E1BEA555A9B475A29685E24C7F15D1D`.

| Case | Verified by | Result |
| --- | --- | --- |
| Elf applies only to Player + UOR + char-list bit + Elf request; Human, Gargoyle, staff, ML era do not | unit (`AppliesTo`) | pass |
| Skin hue clipped to Elf table (invalid, 0, high bits); hair valid per gender kept, wrong-gender/Human/out-of-range hair becomes bald; hair hue clipped; no facial hair | unit | pass |
| `Register` idempotent; Elf bodies 605-608 | unit | pass |
| `expansion.json`: ML char-list bit true, ML and SA feature bits false, SE false | unit (reads source file) | pass |
| UOR Elf and Human derive identical MaxWeight, hits/stam/mana max, racial skill bonus, skills, all resistances (max and current), light levels, hit/stam/mana regen | unit | pass |
| Same comparison under ML differs (mana +20, weight), so the parity test is not vacuous | unit | pass |
| Elf body/ghost/resurrect (605/607/605, 606/608/606), hue and hair kept; Serialize/Deserialize round trip | unit | pass |
| Elven-only gear refused for a UOR Elf, plain gear allowed (`CheckRace`) | unit | pass |
| Bit **off**: Elf request becomes a stock Human (body 400, no Elf hair) | live, disposable host, Navrey packet | pass |
| Bit **on**: male and female Elf per profession (Warrior, Mage, Blacksmith, Advanced): race Elf, body 605/606, exact skin hue, hair, hair hue, no facial hair | live, server report + client state | pass (12/12 appearance) |
| Elf vs Human, 4 professions: raw stats, skills, gold, derived stats equal; equipped and pack kits equal after normalising stock-random items (shirt/pants/scroll/tinker part) | live | pass (12/12) |
| Forged packets: Human skin hue, Human hair, beard, female-only hair on male Elf: clipped/dropped; Gargoyle request: Human | live | pass |
| No ML racial bonus on Elves | live | pass |
| Another client sees Elf bodies 605/606 and Human 400 | live (observer world file) | pass |
| Elf killed: ghost 607/608, still Elf; resurrected: 605/606, hue, hair, facial hair unchanged (male and female) | live | pass |
| Save, full server restart, all 12 characters re-login: race and appearance equal | live | pass (12/12) |
| Elven shirt/boots refused for Elf and for Human; plain Cloak equipped by both | live (`EquipItem` path) | pass (6/6) |
| Real creation gump (Navrey, same source as dist) offers Human and Elf with Next enabled, preview body 0x25D; Gargoyle absent | live probe `charraces` | pass |
| Dev host boots with activated config; era gates validate | live | pass |

Runs: Shard filtered `20260930T234348579Z-35013e` (23/24, the one expected failure was the activation assertion before the flip); UOContent filtered `20260930T234423881Z-48b9ec` (9/9); full Shard `20261001T002707995Z-fbabc7` (267/267, after activation); full UOContent `20261001T002735110Z-635aa6` (1242 pass, 2 fail, 2 skipped).

**Two UOContent failures are not from this item.** `AdvancedSearchTypesTests.Poison_ReferenceTypeParsedViaTypes` and `FamiliarAITests.HiddenCaster_FamiliarRefusesRetaliation` fail identically with the Elf tests excluded (run `20261001T002752861Z-67bf84`, 1235 pass), on ModernUO HEAD `d95d50391`. Left for the owner to prioritise.

Live driver output (reports, results JSON) is under `work/elf-live/` (scratch). Drivers: `tests/scenarios/cosmetic-elf/elf_live.py` (`create`, `death`, `persist`), `elf_equip_live.py`.

## Observations worth keeping

- A character killed and resurrected passively gains Meditation afterwards. A Human control (kill and `[res`) did the same, so it is stock behavior, not race.
- Stock profession kits roll random shirts, pants, scrolls and tinker parts, so two Humans differ too; parity compares everything else exactly.
- `New-TestCharacter.ps1` with many `-NoRestart` calls takes about 25 s per character.

## Player-facing text

README rules section gained a "Human or Elf" line. No new in-game strings.
