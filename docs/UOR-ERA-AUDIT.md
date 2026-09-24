# UOR combat branch audit

Pinned ModernUO integration commit: `075d7859eb9646ed681a18b064754bb066799812`
UOR baseline reference: `29a3ab1bd443b9c2a8ff6bf34f4df47d9f837895`
Recorded: 2026-09-23

## Approved shard policy

The shard uses `Expansion.UOR` as its platform baseline but has **no original automatic weapon
procs** and **no Wrestling Stun or Disarm**. Ordinary Wrestling defense, normal weapon-family
damage, weapon poison, true-mace stamina loss, and other pre-AoS passives are not changed by this
gate.

## Verified source paths and applied gate

| Behavior | Pinned source path | Gate |
| --- | --- | --- |
| Concussion Blow (axes) | `UOContent/Items/Weapons/Axes/BaseAxe.cs` | Removed automatic hit-resolution branch. |
| Concussion Blow (polearms) | `UOContent/Items/Weapons/PoleArms/BasePoleArm.cs` | Removed automatic hit-resolution branch. |
| Crushing Blow (two-handed maces) | `UOContent/Items/Weapons/Maces/BaseBashing.cs` | Removed automatic damage-resolution branch. |
| Paralyzing Blow (two-handed spears) | `UOContent/Items/Weapons/SpearsAndForks/BaseSpear.cs` | Removed automatic hit-resolution branch. |
| Wrestling Stun/Disarm client packets and AI callers | `UOContent/Items/Weapons/Fists.cs`, via `Network/Packets/IncomingExtendedCommandPackets.cs`, `Mobiles/AI/MageAI.cs`, and `Mobiles/AI/ThiefAI.cs` | `Fists.StunRequest` and `Fists.DisarmRequest` clear state and never arm a move. |
| Wrestling Stun/Disarm hit resolution | `UOContent/Items/Weapons/Fists.cs` | Every unarmed swing clears both ready states before the base swing path. |
| Saved ready states | `Server/Mobiles/Mobile.cs` | Legacy booleans are consumed for serialization compatibility and reset to false on load. |

The repository also contains AoS weapon-ability classes (including `Disarm` and
`ParalyzingBlow`) and monster abilities such as `StunAttack`. Those are separate systems, not the
original UOR automatic weapon proc or UOR Wrestling ready-state paths. They remain unavailable to
this UOR runtime through the existing expansion gate; this change does not broadly rewrite them.

## Regression evidence

`UOContent.Tests/Tests/Items/Weapons/FistsSpecialGateTests.cs` verifies that both request APIs
clear their ready states and that an unarmed swing clears stale persisted state before resolution.
`UOContent.Tests/Tests/Items/Weapons/ClassicCombatIdentityTests.cs` locks the retained
Lumberjacking, poison, mace/staff, shield, and ranged-weapon baselines described below. Build the
affected UOContent project with `--maxcpucount:1`, deploy while the server is stopped, then restart
and inspect the server log. The runtime staff command `[ShardRulesStatus` reports the disabled
combat-special policy alongside the UOR/Felucca baseline.

## Player-facing surfaces

Legacy clients can still render primary/secondary ability controls because the original UO protocol
has no server capability bit for disabling pre-AoS Wrestling Stun/Disarm. A request now receives an
explicit server message identifying the disabled move instead of silently failing. The server's
pre-AoS ConPVP ruleset no longer lists a `Combat Abilities` category or enables Stun in its default
duel templates. Client-local ability books, buttons, or hotkeys supplied by third-party clients are
not authoritative and cannot make these moves active.

## Classic combat-identity baseline

The following Alpha 1 findings are pinned to the UOR baseline reference
`29a3ab1bd443b9c2a8ff6bf34f4df47d9f837895`; the current integration checkout is
`1d3330a7517a1d290c363b370d754c38baba4e1a`. They are intentionally a **retain**
baseline: Alpha 1 does not add weapon specials, numerical class buffs, later-era
item properties, or cross-system combat tuning.

| System | Pinned code path | UOR result | Classification | Player-visible result | Regression coverage |
| --- | --- | --- | --- | --- | --- |
| Weapon families and Lumberjacking | `UOContent/Items/Weapons/BaseWeapon.cs`; `Axes/BaseAxe.cs`; `PoleArms/BasePoleArm.cs` | Classic old damage/speed/handedness are selected while AoS is off. The UOR Lumberjacking modifier applies only to `WeaponType.Axe`, scales at 1% per five skill points, and is +20 percentage points at 100.0. The additional +10 requires UOTD and is therefore absent. Polearms may be harvesting tools but are `WeaponType.Polearm`, not axes. | Retain | Axe specialization is present without a +30 GM spike or polearm/mace leakage. | `ClassicCombatIdentityTests.UorLumberjacking_IsAxeOnly_AndCapsAtTwentyPercent` |
| Weapon poison | `Skills/Poisoning.cs`; `Items/Weapons/{Swords/BaseSword,Knives/BaseKnife,SpearsAndForks/BaseSpear}.cs`; `Misc/{Poison,PoisonKinds}.cs` | Pre-AoS application permits one-handed slashing or piercing weapons; a successful application grants `18 - 2 × poison level` charges. Eligible hits consume a charge and make the existing 50% delivery roll. Standard poison tiers, cure behavior, and damage timer are retained. No separate corrosion mechanic exists in this pinned path. | Retain | Poison remains a resource- and skill-based weapon specialization; no new spell scaling or healing-denial rule is introduced. | `ClassicCombatIdentityTests.UorBladedAndPiercingWeapons_ConsumePoisonChargesOnHit`; manual cure/healing matrix required below. |
| Maces and staves | `Items/Weapons/Maces/BaseBashing.cs`; `Items/Weapons/Staves/BaseStaff.cs`; `Items/Armor/BaseArmor.cs` | `WeaponType.Bashing` is used by true maces and receives Bashing-specific armor wear when armor absorbs a hit. Stock `WeaponType.Staff` remains distinct and does not take that Bashing wear branch. Both current stock base classes apply the ordinary 3–5 stamina hit effect; this is recorded, not broadened or tuned. | Retain | Maces and staves keep their existing separate classifications. | `ClassicCombatIdentityTests.UorMacesAndStaves_KeepTheirDistinctWeaponTypesAndStaminaHitEffect` |
| Shields and Parrying | `Items/Shields/BaseShield.cs`; `Items/Weapons/BaseWeapon.cs`; `Items/Armor/BaseArmor.cs` | A shield equipped in the two-handed layer scales its AR by the holder's Parrying skill. In the pre-AoS absorption branch, a successful shield Parry reduces melee damage by half shield AR and Archery damage by full shield AR; shield durability may wear. Armor continues to absorb and wear through its own path. | Retain | Shield defense requires an equipped shield; two-handed weapons cannot use it at the same time. | `ClassicCombatIdentityTests.UorShieldParrying_ScalesShieldArmorAndRequiresAShield`; manual block/durability matrix required below. |
| Archery | `Items/Weapons/Ranged/{BaseRanged,Bow,Crossbow,HeavyCrossbow}.cs`; `Items/Weapons/BaseWeapon.cs` | Pre-AoS ranged attacks use a Dex-scaled stationary delay in both PvM and PvP: 1.0s at 25 Dex or below, 0.5s at 100 Dex or above, rounded to 50ms steps. They retain each weapon's old damage/speed/range profile, consume arrows or bolts when fired, and use ordinary hit checks and two-handed equipment requirements. Bow/crossbow/heavy-crossbow profiles are respectively 9–41/20/10, 8–43/18/8, and 11–56/10/8 (damage/speed/range). | Approved hybrid compatibility change | Archery keeps range, ammo, cadence, and positioning as its differentiators; only the stationary timing curve is adjusted toward the selected Outlands interaction. No damage delay, setup bonus, custom special, or crossbow hand change is enabled. | `ClassicCombatIdentityTests.UorRangedWeapons_PreserveClassicProfilesAndConsumeTheirAmmo`; `UorRangedStationaryDelay_ScalesWithDexInPvmAndPvp`; `UorRangedMovementAttempt_DoesNotAdvanceTheSwingAnchor`. |

## Alpha 1 Mastery progression

Mastery is a shard-owned progression layer implemented in `ShardContent` with one narrow
ModernUO gain-override hook. Ordinary stock skill checks and gain factors remain unchanged below
95.0; the hook suppresses stock gains at 95.0+ and lets the shard consume pending increments.

| Rule | Source/implementation | Decision | Player-visible behavior | Coverage |
| --- | --- | --- | --- | --- |
| Threshold | `ShardContent/src/BritanniaRenaissance.Content/MasteryProgression.cs` | Retain: ordinary gain stops at 95.0; Mastery ends at 100.0. | A skill enters Mastery at 95.0 and cannot advance through ordinary random gains. | Engine gain-override regression; live skill-use check. |
| Global schedule | Same path; `GetPeriodId` uses `DateTime.UnixEpoch` and four-hour UTC periods. | Retain: boundaries are 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00 UTC for every player. | `[MasteryStatus` reports server UTC time and the next shared boundary. | `MasteryPeriodScheduleTests`. |
| Login qualification | Per-character persisted UTC day set in the account tag state. | Retain: one login qualifies that UTC date; dates with no login produce nothing. | The status command reports whether today is qualified. | Login/reconciliation integration matrix. |
| Offline reconciliation | Per-skill processed-period cursor and persisted qualified dates. | Retain: offline completed periods reconcile once at login; period IDs cannot duplicate. | Login reports reconciled pending skill. | Restart, logout/reconnect and missed-date tests. |
| Pending award | One fixed-point tenth per completed qualified period. | Retain: 0.1 increments only; no random chance, bracket cost, or one-award-per-day throttle. | Online players receive a period-award message and can consume multiple increments in one day. | Pending increment and same-day consumption tests. |
| Pending cap | Six tenths per skill. | Retain: cap is 0.6, and full-bank periods are consumed without adding more. | Players must use pending points before later periods can bank additional points. | Cap and overflow tests. |
| Valid consumption | ModernUO hook runs after region and anti-macro eligibility checks. | Retain: a valid non-trivial use at 95.0–99.9 consumes one pending tenth and grants +0.1; invalid, trivial, locked, capped or blocked uses consume nothing. | Multiple eligible uses can advance the skill on the same day. | Gain-override and skill-use tests. |
| Completion | 50 increments from 95.0 to 100.0. | Retain: 200 elapsed hours, eight complete six-period days plus two periods on the final day. | The last day has only the remaining two awards. | Schedule simulation and final-period tests. |

The persisted state is character-specific and stored through the account save layer under a serial-keyed
shard tag. It includes qualified UTC dates, each skill's pending tenths and the last processed period
ID. The state survives logout, death, restart and save/load; unused pending tenths are discarded at
100.0. Temporary gain bonuses, anti-macro configuration, combat rules and deferred Alpha 2/3 systems
do not change period length, award size or the 0.6 cap.

### Alpha 2 hostility foundation (implemented, feature-gated)

`PvpIntentService` is the first Alpha 2 slice. It persists a blue player's voluntary PvP Intent
through the account-tag layer and exposes `[Intent` and `[IntentStatus` commands. When the
`safeWorld` feature flag is disabled, it delegates entirely to the pinned ModernUO hostility
handler. When enabled, it preserves stock blessedness, region, duel and guild checks. Because
Felucca's stock handler intentionally allows every player pair, the service replaces that
unrestricted result with only explicit safe-world reasons for direct player hostility: an ordinary blue targeting a
criminal/murderer or an opted-in `[Intent]` target, mutual Intent, or an existing aggression
relationship. Controlled creatures resolve their attacking player master through the same policy,
so pets cannot bypass safe-world consent. Criminal/murderer players cannot change Intent, and
safe-zone restrictions remain authoritative. A short-lived encounter snapshot is captured from `EventSink.AggressiveAction` so
later Intent changes do not reclassify an active pair. The snapshot is also persisted in the
attacker account tag layer and restored after logout/restart; it expires with the ordinary
two-minute encounter window. Hot-zone regions and Knocked Out remain separate Alpha 2 work and
are not enabled by this slice.

`KnockedOutService` now provides the gated resolution boundary for the next Alpha 2 slice. When
enabled with SafeWorld, a qualifying ordinary-blue player intercepted at lethal damage is persisted
for 90 seconds, has combat and targeting cleared, and is protected from additional damage. It
retains a separate completed-encounter account record after recovery/expiry for later
encounter-authorized loot and execution checks.
ModernUO fork exposes only the narrow lethal-damage, damageability, targetability, recovery, and
Stealing delegates required by this service (`Mobile.LethalDamageHandler`,
`Mobile.CanBeDamagedHandler`, `Mobile.CanTargetHandler`, `Stealing.KnockedOutLoot`,
`Mobile.HealHandler`, and `Mobile.CurePoisonHandler`, fork revision
`075d7859eb9646ed681a18b064754bb066799812`). The same fork now supplies explicit
`PlayerMobile.PlayerDeathHandler` and `CharacterCreation.CharacterCreatedHandler` observers, plus
an `EventSink.Connected` bridge used by the external assembly for login reconciliation. These
observers are invoked after the stock engine handlers and remain inert unless the corresponding
shard feature is enabled. `[KnockedOutStatus` is staff-only. No-skill looting now
uses the stock Stealing boundary and requires the recorded criminal/red
engagement holder outside Hot Zones; controlled-creature lethal damage resolves its player master
as that holder. KO entry clears poison, paralysis, bleeding, Mortal Strike, and active casting;
heals/cures are blocked while active, and expiry/login wake-up restores half health. Item range,
movability, bindings, Wards, and post-resolution handling remain active.
Encounter-authorized `[Execute` clears the active state, resolves through
the same automatic murder ledger, and is gated on the recorded criminal/red engagement holder.
Hot/Cool resolution, migration rehearsal, and public enablement remain deferred until the full
Alpha 2 matrix and region policy are implemented.

When enabled, the same service wraps the stock notoriety handler so an otherwise-blue Intent
character is presented with the attackable/grey hue while genuine criminal or murderer status
continues to take precedence. The wrapper is inert while SafeWorld is disabled.

The next law-system boundary is `MurderAdjudicationService`. Its policy and account-tag ledger
are implemented but remain disabled behind `featureFlags.automaticMurderAdjudication`.
Administrator `[MurderStatus` exposes the feature gate and any recorded ledger values. When the
flag is enabled, its `PlayerDeathEvent` hook classifies an ordinary-blue victim
independently from attack legality, excludes an encounter already classified as Intent-exposed,
deduplicates a victim/death timestamp, and extends the killer's UTC red timer by 24 hours from
the later of the current time or prior expiry. Stock murder reports, five-count thresholds and
decay therefore remain the only live behavior until their replacement and encounter snapshots
are ready to be enabled together.

The ModernUO fork now provides the narrow integration boundary: custom configuration can disable
legacy report/decay hooks and supply an additional red-status handler without changing stock
behavior while the flag is false.

`ShardAuditLog` records low-volume Alpha 2 decisions with stable character serial/account
identifiers: Intent changes and encounter snapshots, denied safe-world hostility, automatic murder
counts, Ward/corpse enforcement, and Knocked Out entry/recovery. The existing diagnostic commands,
including administrator-only `[MurderMigrationAudit` and `[KnockedOutRecover`, provide the staff
inspection/recovery surface; the migration audit is read-only and reports legacy threshold versus
custom ledger state. It now emits bounded per-character serial/name rows for non-neutral
legacy-only, custom-only, and overlapping red state, with an explicit truncation count. Public
enablement still requires migration rehearsal and complete encounter procedures.

`[TheftStatus` also reports Loot Protection migration processed/total/granted counts, queue depth,
schedule state, and start/completion timestamps, allowing a rehearsal to prove that the world-load
sweep drained.

When the custom flag is true, the fork also suppresses legacy `Kills >= 5` and short-term
PingPong red decisions without deleting historical values; the account-tag UTC expiry becomes
the custom red-status source. The custom red handler is explicitly inert while the flag is false,
so stale account tags from a rehearsal cannot affect the Alpha 1 profile. This migration hook is
not active in the current Alpha 1 profile; `MurderAdjudicationTests.AutomaticRedSourceHonorsFeatureGateAndExpiry`
covers the boundary.

The theft boundary now has a feature-gated physical `BackpackWard`, a permanent invisible
character-specific Loot Protection entitlement, and stock Stealing hooks. Existing characters are
migrated idempotently in bounded world-load batches; login, character creation and the first
eligible corpse action are safe fallbacks if a character was not present during the sweep.
Stock success, failure, criminality and snooping remain unchanged. An eligible Ward is selected
deterministically from the equipped backpack, tracks undetected successful thefts per thief
account at 25%/50%/100% detection, is consumed after ordinary detection, and persists the
victim-wide 120-second protection window through account tags. When enabled, character creation
issues one ward and binds it durably to the character account; transferred wards are ignored by
the protection selector. The same feature-gated service now
allows the first unlawful non-Hot monster-corpse transfer, then blocks that offender account from
repeating against the same corpse for ten minutes. Bank/Cool region restrictions remain deferred;
`theftProtection` is false in Alpha 1 and automatically bypasses corpse protection while
`hotZones` is enabled.

The theft-region policy now loads explicit `map`/point polygons from `shard-rules.json`. Bank
polygons deny direct player stealing only; Cool-Dungeon polygons deny direct player stealing while
leaving snooping and combat decisions untouched. The runtime policy now contains 18 banker
envelopes and the stock rectangles for the ten UOR-era dungeons. Bank envelopes are compact
24-by-24-tile survey areas around each observed banker spawner/approach tile, selected to provide
approximately a 5–6 tile apron without creating a town-wide combat bubble. Entering or leaving a
bank or Cool Dungeon emits one player-facing explanation; blocked movement does not emit a false
transition.

The theft boundary rechecks both participants at the target-selection boundary: a direct player
steal is denied when either the thief or the intended victim is inside a configured bank/Cool
polygon. Map names are compared case-insensitively, and empty/invalid polygons remain inert.

The next Alpha 2 geography gate is now reproducible: `tools/Export-FeluccaBankCandidates.ps1`
extracts Banker spawner coordinates from the pinned ModernUO
`Distribution/Data/Spawns/shared/felucca/Vendors.json`, records the source SHA-256 and spawner
GUIDs, and writes a review-only candidate file. The Navrey client then queried the center tile of
all 18 candidates (static/roof/wall flags are retained in `work/alpha2-bank-survey.log`); the
resulting polygons are recorded explicitly rather than inferred at runtime.

`tools/Export-FeluccaDungeonCandidates.ps1` provides the matching review surface for Cool-Dungeon
selection. It extracts the pinned `DungeonRegion` rectangles, identifies the ten UOR-era dungeon
names as candidate-compatible, and preserves later-era/special regions for explicit review. The
ten UOR-era candidates' stock rectangles are now active Cool-Dungeon polygons; later-era/special
regions remain deferred.

The 2026-09-24 review export found 18 Felucca Banker spawners and 18 Felucca dungeon regions.
The bank source hash was `acc0d004ead4d81e681eefeae62e54dfb3fe8420c4067dc83a3fc3271c9bd31d`;
the dungeon-region source hash was
`cbfe5df4097d16185ce3fd9b902b42f71029227c366247214ca16a401340687d`. Ten dungeon names were
marked UOR-era candidates (Covetous, Deceit, Despise, Destard, Fire, Hythloth, Ice, Khaldun,
Shame and Wrong). The 18 bank envelopes and 14 split rectangle polygons for those ten dungeons are
recorded in the shard policy. The reproducible review exports remain committed under
`docs/generated/alpha2/` alongside the final configuration.

The shard-rules validator permits explicit Alpha 2 flags only when their dependencies are declared
and `alpha2EnablementAcknowledged` is explicitly true:
automatic murder adjudication and theft protection require SafeWorld, while Knocked Out also
requires automatic murder adjudication. Alpha 3+ flags remain rejected. The checked-in Alpha 1
profile keeps every Alpha 2 flag false.

### Manual Alpha 1 validation matrix

After the automated suite passes and the server is restarted with the UOR/Felucca profile,
run the following controlled cases with ordinary equipment and record results in the release
test log. Use the tank mage, sword/shield, axe, poison fencer, macer, archer, and an ordinary
monster target. These are observation checks, not authorization to retune any result.

1. Compare axe versus polearm/mace swings at 0, 50, and 100 Lumberjacking; confirm only the axe
   changes and that the 100.0 result is the approved +20-point modifier.
2. Apply Lesser through Lethal poison to eligible blades, verify charge consumption and delivery,
   then exercise cure potions, bandage healing, and magical healing in both PvP and PvM. Record
   observed stock healing behavior; do not add or remove poison healing denial.
3. Strike armor-equipped player and creature targets with a War Mace and QuarterStaff. Record
   stamina effects, armor durability, and the separate Bashing versus Staff classification.
4. Compare one-handed weapon plus shield against a two-handed weapon for shield blocking,
   damage absorption, and durability. Confirm equipping a two-handed weapon removes ordinary
   shield mitigation.
5. Fire bow, crossbow, and heavy crossbow while stationary and immediately after moving. Record
   the Dex-scaled 1.0-to-0.5-second movement restriction, cadence, range, hit/miss outcomes, and
   arrow/bolt use in PvP and PvM.

## Alpha 1 Step 2 — instant-hit and classic precasting

Implementation evidence is pinned to ModernUO `6544ba825a5493329e6c800f2107468f1ab13a50` and
the ShardContent baseline at `3aebbadc143055e85722c70611bb3bb4b13692ba`. The only behavior change in
this step is
the narrow UOR timer restoration described below; no Outlands-only balance systems are imported.

| System | Exact source path | Finding | Classification | Player-visible | Coverage |
| --- | --- | --- | --- | --- | --- |
| Insta-hit enablement | `UOContent/Items/Weapons/BaseWeapon.cs`; `data/configuration/modernuo-era-gates.json` | `melee.enableInstaHit` is explicitly enabled by the shard configuration. The stock equip path is retained for the first legal swing. | Configuration-only / retain | Yes: the first legal swing is no longer delayed by equip. | `ClassicCombatIdentityTests.UorInstaHit_QuickSwitchUsesLastSwingAndCurrentWeaponDelay` |
| Last-swing anchor and quick switching | `Server/Mobiles/Mobile.cs`; `UOContent/Items/Weapons/BaseWeapon.cs` | The last resolved swing anchors the next deadline. A faster weapon may become ready on its own delay; a slower weapon cannot bypass the slower deadline. Equip/unequip does not create a free swing, and legality is still checked by the normal combat path. | Defect to restore pinned UOR baseline | Yes: halberd/katana swaps change readiness without granting an extra attack. | The same test covers immediate first equip, fast and slow swaps. |
| Miss/disarm/death/logout cleanup | `Server/Mobiles/Mobile.cs`; `UOContent/Items/Weapons/Abilities/DoubleStrike.cs` | Swing resolution refreshes `LastSwingTime` even on a miss; disconnection and death clear transient combat deadlines. Existing disarm and target legality checks remain authoritative. | Defect to restore pinned UOR baseline | Yes: no queued swing survives a disconnect or death. | Focused timer test plus existing combat and disarm-gate suites. |
| Equip while casting | `Server/Spells/Spell.cs`; `Server/Mobiles/Mobile.cs` | Equipping during `Casting` invokes `OnCasterEquipping` and interrupts. An equip after the cast reaches `Sequencing` preserves the held spell. | Retain | Yes: classic precast weapon swap remains usable. | `ClassicCombatIdentityTests.ClassicPrecast_EquipAndUseCancellationMatchesUorStateFlow` |
| Object/potion use after precast | `Server/Spells/Spell.cs` | Object use during `Casting` is allowed; object use after `Sequencing` cancels the pending spell. This preserves the existing UOR cancellation boundary. | Retain | Yes: potion/object use cannot silently release a held spell. | `ClassicCombatIdentityTests.ClassicPrecast_EquipAndUseCancellationMatchesUorStateFlow` |
| Held-spell release | `Server/Spells/Spell.cs`; `Server/Spells/SpellHelper.cs` | Release continues to recheck target, range, line-of-sight, region, and harmful authorization. The existing 30-second held-target timeout remains unchanged. | Retain | Yes: invalid or unsafe releases fail instead of bypassing authorization. | Existing spell and region tests; live release check required. |
| Recovery and interruption cadence | `Server/Spells/Spell.cs` | The pinned UOR recovery and disturbance timing remains in force. Outlands' published 0.2-second recovery and circle-specific five-second interrupt windows are documented as compatibility differences, not silently imported. | Deferred | Yes: players may notice cadence differences from Outlands. | Record live cast/recovery observations; no balance change in Alpha 1. |
| Disarm/re-arm and dungeon-transition rules | `UOContent/Items/Weapons/Fists.cs`; `Server/Spells/Spell.cs` | Wrestling Stun/Disarm remains explicitly disabled. Outlands' five-second re-arm cooldown, custom `UnequipOnCast`, and dungeon-transition damage reduction are not part of this step. | Deferred | Yes: the shard intentionally differs from Outlands in these excluded systems. | Existing `FistsSpecialGateTests`; no new rule imported. |

### Outlands compatibility notes

Outlands' public [Combat Overview](https://wiki.uooutlands.com/Combat_Overview) and
[Armor & Weapons](https://wiki.uooutlands.com/Armor_&_Weapons) describe the player-visible
interaction this step targets: the timer is based on the last weapon swung rather than the
currently equipped weapon, quick switching uses each weapon's own delay, and equipping during a
cast interrupts while a post-cast weapon swap preserves a held spell. The published
[Magery](https://wiki.uooutlands.com/Magery) page additionally documents a 0.2-second cast
recovery and circle-dependent interrupt windows. Those timings, Outlands armor systems, custom
disarm cooldowns, `UnequipOnCast`, and dungeon-transition reductions are measured for future
compatibility work only; importing them would be an unapproved Alpha 1 balance change.

The one selected ranged compatibility rule is narrower: the stationary delay now follows the
published Outlands 1.0-to-0.5-second Dexterity curve in both PvM and PvP. Outlands' separate PvP
damage delay, one-handed crossbow classification, weapon-role rebalance, setup bonuses, and
custom Archery specials remain intentionally excluded.

### Verification record

- Focused ModernUO suite: **9 passed, 0 failed** (`ClassicCombatIdentityTests` and
  `FistsSpecialGateTests`), built with `--maxcpucount:1`.
- The server was stopped before deployment. The Alpha 1 content build completed with 0 warnings
  and 0 errors; the deployed configuration contains `melee.enableInstaHit=True`.
- Restart log evidence at 2026-09-23 16:51:46–16:51:47: `Loaded shard rules schema 1: UOR /
  Felucca`, `Validated UOR era gates ... melee.enableInstaHit`, and listeners on
  `127.0.0.1:2593` and `127.0.0.1:12000`.
- Controlled client evidence at 16:57:17–16:57:34: the Navrey client loaded UOData client
  version `7.0.117.0`, connected to `127.0.0.1:2593`, authenticated the `Administrator` account,
  entered the world as `Generic Player` at `(5445, 1153, 0)`, and completed a movement/speech
  command. `[ShardRulesStatus` returned schema 1, `UOR / Felucca`, caps `700/100/225`, combat
  specials disabled, deferred features none, and the expected runtime era-gate key list. The
  effective `melee.enableInstaHit=True` value was separately verified in the deployed
  `modernuo.json` and by the passing timer regression test.
- The headless client emitted state/world-file permission warnings for its default `C:\tmp`
  paths; these are workstation-local telemetry paths and do not affect login, world entry, or
  shard behavior. The custom command and log files under `work/` were healthy.

### Mastery implementation verification

- `ModernUO` `Application.csproj` and `ShardContent` content assembly build with
  `--maxcpucount:1`, `UseSharedCompilation=false`, 0 compiler warnings and 0 errors.
- `UOContent.Tests` focused `SkillEventsTests`: **5 passed, 0 failed**.
- `ShardContent` `BritanniaRenaissance.Content.Tests`: **6 passed, 0 failed**. NuGet vulnerability
  metadata was unavailable in the restricted environment (`NU1900`); package restore used the
  existing local cache.
- The online Mastery sweep is boundary-driven: the ten-second observer returns without scanning
  players until a completed UTC period changes, then reconciles online characters in bounded
  main-loop batches (64 players or approximately 2 ms per tick). It never mutates player or
  account state from a background thread. Long offline catch-up counts qualified UTC dates up to
  the six-tenth pending cap and advances the processed-period cursor directly instead of walking
  every missed four-hour period. Account tags are written only when Mastery state changes.
- After deployment with the server stopped, the restarted runtime loaded the shard assembly,
  validated UOR/Felucca and the existing era gates, and listened on `127.0.0.1:2593` and
  `127.0.0.1:12000` at the final verification restart. The server remains running for client testing.

### Alpha 2 isolated staging verification

The current Alpha 2 implementation was rebuilt in an isolated staging host on 2026-09-23 so
the production/Alpha 1 process and configuration were not changed. The bundle used ModernUO
`8e733f5cf48faa0085e92d385f956b8854e9e9d2` and ShardContent `723ba49`.

- ModernUO `Application.csproj` completed with `--maxcpucount:1`, 0 warnings and 0 errors.
- ShardContent compiled against that bundle with 0 warnings and 0 errors.
- `BritanniaRenaissance.Content.Tests` passed **67/67** for that staged bundle; the only output was the offline NuGet
  vulnerability-metadata warning (`NU1900`).
- The current post-staging Alpha 2 source revision passes **71/71** focused tests, including the
  attributable-player/active-encounter Knocked Out cases; the only output remains `NU1900`.
- The ModernUO recovery/targetability regression suites pass **5/5** in an isolated worktree for
  integration commit `1d3330a7517a1d290c363b370d754c38baba4e1a`; the live server was not stopped.
- The complete isolated ModernUO `Server.Tests` suite passes **896/896** with **17** environment-gated
  map tests skipped (913 total) at the same integration commit.
- A fresh matching worktree at `1d3330a7517a1d290c363b370d754c38baba4e1a` was rebuilt with
  `--maxcpucount:1` (0 warnings, 0 errors), and `BritanniaRenaissance.Content.Tests` passed
  **71/71** against that exact engine output. This closes the content-test evidence gap after
  the targetability regression revision was published.
- The follow-up lifecycle-hook revision `075d7859eb9646ed681a18b064754bb066799812` builds with
  `--maxcpucount:1` at 0 warnings and 0 errors. Its focused ModernUO regression set passes **5/5**
  (targetability plus the PlayerDeath/CharacterCreated bridge tests), and the content assembly
  builds against that exact output with **71/71** focused tests passing. The explicit engine
  observers close the external-assembly event-dispatch gap found during live staging: connected
  players now receive login reconciliation, character creation can issue the starter Ward, and
  player death reaches automatic murder adjudication without relying on generated event metadata.
- The complete isolated ModernUO `Server.Tests` suite also passes **898/898** with **17**
  environment-gated map tests skipped (915 total) against the same `075d7859...` revision. The
  test run used the matching built `Distribution/Data` fixture set; no source or checked-in
  runtime configuration was changed.
- Knocked Out now uses the targetability hook as well as damage, healing, and curing guards, so
  target requests are rejected while the state is active and the existing timer/expiry recovery
  path remains authoritative.
- The isolated server loaded the current `shard-rules.json`, reported `UOR / Felucca`, loaded
  385 regions and listened on `127.0.0.1:2594`.
- The Alpha 1 profile kept all Alpha 2 flags disabled (`deferred features: none`); no live
  Alpha 2 behavior was enabled by this smoke test. Client login and the full real-client Alpha 2
  matrix remain the next gated verification step after approved bank/Cool geometry and migration
  rehearsal are available.

For the follow-up feature-gated rehearsal, only the isolated host configuration was changed to
acknowledge Alpha 2 and enable `safeWorld`, `automaticMurderAdjudication`, `theftProtection`, and
`knockedOut`; the checked-in Alpha 1 profile was not changed. After restart, the Navrey headless
client authenticated the `Administrator` account, entered the world as `Generic Player` at
`(5445, 1153, 0)`, and reported:

- `[ShardRulesStatus`: Alpha 2 acknowledged and all four flags enabled.
- `[IntentStatus`: Safe-world policy enabled.
- `[MurderStatus`: automatic adjudication enabled; legacy reporting and legacy red source disabled.
- `[TheftStatus`: Backpack Ward protection enabled; bank/Cool polygon counts both zero.
- `[KnockedOutStatus`: Knocked Out enabled.

`[Intent` was toggled once and the server audit log recorded the stable Administrator identity.
The staging server and client were then stopped, and the workstation-local Navrey settings were
restored to the normal 2593 profile. This proves startup, login, command registration, feature
gate wiring, and audit logging; it does not prove the missing map geometry, cross-character combat
matrix, or production enablement.

The readiness tooling now accepts a separate `-RulesPath` for disposable hosts. A 2026-09-24
rehearsal against the current `5fba7cc393112170536aac250086e451e0a0b149` worktree used one
synthetic bank polygon and one synthetic Cool-Dungeon polygon only in the copied staging policy.
The verifier reported matching pin, clean repositories, all four Alpha 2 flags acknowledged, and
`ReadyForEnablement: True`. The synthetic geometry was not written to the checked-in Alpha 1
policy and is not a substitute for staff-approved geography.

### Alpha 2 lifecycle-hook live rehearsal (2026-09-24)

The lifecycle-hook revision was rebuilt and run in a fresh disposable host using ModernUO
`075d7859eb9646ed681a18b064754bb066799812`, the matching ShardContent assembly, and a copied
world save. The host listened on `127.0.0.1:2594`; the checked-in Alpha 1 configuration was not
changed. The disposable policy acknowledged Alpha 2, enabled SafeWorld, automatic murder
adjudication, theft protection, and Knocked Out, and supplied one synthetic bank polygon and one
synthetic Cool-Dungeon polygon.

- Navrey authenticated the Administrator account and entered the world as `Generic Player` at
  `(5445, 1153, 0)`.
- `[ShardRulesStatus` reported the matching ModernUO pin, `UOR / Felucca`, Alpha 2 acknowledged,
  all four staged flags enabled, and the automatic weapon/Wrestling special exclusions intact.
- `[MurderStatus` reported the custom UTC ledger enabled with stock murder reporting, five-count
  threshold, and decay disabled; `[MurderMigrationAudit` scanned one player with no legacy-only,
  custom-only, or overlapping state and performed no mutation.
- `[TheftStatus` reported one bank polygon, one Cool polygon, migration `processed=1/1`,
  `pending=0`, and the Loot Protection entitlement present after connected-login reconciliation.
- `[KnockedOutStatus` reported the state enabled with no active encounter and encounter-authorized
  looting/execution active outside Hot Zones.

This proves the new external-assembly lifecycle bridge through a real client login and live status
surface. Character-creation and death-event paths remain covered by the focused engine bridge tests
and the 72/72 content suite; the full multi-character combat matrix is still required before public
enablement.

### Alpha 2 two-account SafeWorld rehearsal (2026-09-24)

A disposable two-account host also exercised the ordinary-blue hostility boundary with two Navrey
clients. Both accounts entered the world at the same location. Before the refresh correction,
`attack` against the other ordinary-blue player was refused by the client as `Innocent (blue)`, and
both characters successfully toggled and reported `[Intent]` enabled. The server audit recorded both
intent changes, but the already-visible target remained cached as Innocent in the client world
snapshot. This paragraph is retained as the pre-fix failure evidence and does not count as proof
that the opted-in attack is accepted.

`PvpIntentService.ToggleIntent` now re-sends the normal mobile-incoming packet to nearby observers
after an Intent change. That packet recomputes the observer-specific notoriety and remains part of
the current implementation. The post-startup lifecycle correction and successful two-account
matrix are recorded in the following section; this older paragraph must not be used as the current
acceptance result.

### Alpha 2 notoriety lifecycle correction (2026-09-24)

The stale-client result exposed an initialization-order defect: ModernUO's stock notoriety and
harmful-action initializers ran after the external shard bridge and replaced the custom delegates.
The bridge now registers a one-shot `ServerStarted` callback and rebinds both delegates after every
stock `Initialize` method; the existing `Server.CallPriority(1000)` boundary remains as a fallback
for world-dependent setup.
The corrected assembly was rebuilt against pinned ModernUO
`075d7859eb9646ed681a18b064754bb066799812` and loaded by a fresh disposable host on
`127.0.0.1:2598`; startup completed with the UOR/Felucca policy and all staged Alpha 2 systems
recognized. The checked-in policy and production runtime were not changed.

The focused content suite passes 72/72 tests. A post-fix Navrey run authenticated two disposable
accounts (`FreshD`, `FreshE`; serials `0x00000002` and `0x00000003`) and entered the world on both
clients. `[IntentStatus` reported `PvpIntentService.ComputeNotoriety` and `CanBeAttacked` for the
nearby opted-in player on both observers; both client world snapshots rendered the other player
as `Gray`. `FreshD` then issued `attack 0x00000003`; the client confirmed the attack, the server
completed a `FreshD -> FreshE` swing, and `FreshE`'s observed hits fell from 100 to 98. This is
the first live proof that the post-startup handler, packet presentation, and opted-in hostility
path agree. Toggling `FreshE` off afterward retained the already-established aggression relationship,
as required by the encounter rule; a fresh no-encounter denial matrix remains deferred before
public Alpha 2 enablement.

A second fresh two-account matrix (`DenyF`, `DenyG`) then verified the harmful-action boundary.
`DenyF` opted in while `DenyG` remained ordinary blue: the client refused the attack as
`Innocent (blue)`, and no encounter was logged. After `DenyG` opted in, `[IntentStatus` reported
both custom delegates, the attack was confirmed, the server recorded an `intent-classified`
encounter, and the swing completed. This proves both lifecycle rebinding paths in the same staged
host; murder, theft and Knocked Out resolution remain separately gated.

The same startup audit found that ModernUO's stock `NotorietyHandlers.Initialize` also assigns
`Mobile.AllowBeneficialHandler`. Because the safe-world Knocked Out service installs its recovery
guard before stock content initialization, the Alpha 2 `ServerStarted` callback now rebinds that
handler as well, preserving the stock delegate for ordinary beneficial checks while rejecting
heals and cures on a Knocked Out target. The callback also reasserts the remaining Knocked Out
damage, targetability, and no-skill-loot hooks; this is covered by the focused content suite and
the disposable all-feature staging boot. This historical staging note predates the approved
geography; the current live profile enables only SafeWorld and TheftProtection.

### Alpha 2 geography review exports (2026-09-24)

The review-only geography tools were run against the pinned checkout's current ModernUO data.
The bank export produced 18 Felucca banker candidates from `Vendors.json` (source SHA-256
`acc0d004ead4d81e681eefeae62e54dfb3fe8420c4067dc83a3fc3271c9bd31d`); the dungeon export produced
18 Felucca dungeon-region candidates from `regions.json` (source SHA-256
`cbfe5df4097d16185ce3fd9b902b42f71029227c366247214ca16a401340687d`), including the ten named
UOR-era candidates Covetous, Deceit, Despise, Destard, Fire, Hythloth, Ice, Khaldun, Shame, and
Wrong. The JSON outputs are retained in local `work/alpha2-review/` as source evidence. The
subsequent Navrey tile survey queried all 18 banker candidates; the checked-in policy now contains
18 bank envelopes and 14 stock-area polygons for the ten UOR-era dungeons. The readiness gate
passes with SafeWorld and TheftProtection enabled; automatic murder adjudication and Knocked Out
remain separate deferred gates.

### Alpha 2 Knocked Out two-account rehearsal (2026-09-24)

On the disposable all-feature host, an Administrator test character was made non-invulnerable and
criminal for the rehearsal while a second ordinary-blue player opted into `[Intent]`. The Navrey
clients entered the same location, the attack was confirmed, weapon swings reduced the victim to
zero-health resolution, and the victim received `You have been Knocked Out for 90 seconds.` The
server audit recorded the encounter and `knocked-out entered` transition. This confirms the
attributable-player-damage and active-encounter gates in a real client session without enabling the
feature on production.

The first execution attempt also found a narrow command-path defect: the global Knocked Out
untargetable guard rejected the `[Execute` target cursor before the encounter-authorized execution
check could run. `ExecuteTarget` now permits only an already Knocked Out player through that target
cursor; `KnockedOutService.Execute` remains authoritative for feature, region, criminality and
recorded-attacker rights. The content suite passes 73/73 after this correction. Production remains
on SafeWorld + TheftProtection only; Murder and Knocked Out still require their migration and full
live matrices before enablement.
