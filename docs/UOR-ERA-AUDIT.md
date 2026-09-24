# UOR combat branch audit

Pinned ModernUO commit: `29a3ab1bd443b9c2a8ff6bf34f4df47d9f837895`  
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

The following findings are pinned to ModernUO commit
`29a3ab1bd443b9c2a8ff6bf34f4df47d9f837895`. They are intentionally a **retain**
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
relationship. Criminal/murderer players cannot change Intent, and safe-zone restrictions remain
authoritative. A short-lived encounter snapshot is captured from `EventSink.AggressiveAction` so
later Intent changes do not reclassify an active pair. The snapshot is also persisted in the
attacker account tag layer and restored after logout/restart; it expires with the ordinary
two-minute encounter window. Hot-zone regions and Knocked Out remain separate Alpha 2 work and
are not enabled by this slice.

`KnockedOutService` now provides the gated resolution boundary for the next Alpha 2 slice. When
enabled with SafeWorld, a qualifying ordinary-blue player intercepted at lethal damage is persisted
for 90 seconds, has combat and targeting cleared, and is protected from additional damage. The
ModernUO fork exposes only the narrow lethal-damage and damageability delegates required by this
service (`Mobile.LethalDamageHandler` and `Mobile.CanBeDamagedHandler`, fork revision
`8dcbd1c4081771bd1b399f7565760ade3340e0ba`). `[KnockedOutStatus` is staff-only. Encounter-authorized no-skill looting, execution,
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
including administrator-only `[KnockedOutRecover`, provide the staff inspection/recovery surface;
public enablement still requires migration rehearsal and complete encounter procedures.

When the custom flag is true, the fork also suppresses legacy `Kills >= 5` and short-term
PingPong red decisions without deleting historical values; the account-tag UTC expiry becomes
the custom red-status source. This migration hook is not active in the current Alpha 1 profile.

The theft boundary now has a feature-gated physical `BackpackWard` and stock Stealing hooks.
Stock success, failure, criminality and snooping remain unchanged. An eligible Ward is selected
deterministically from the equipped backpack, tracks undetected successful thefts per thief
account at 25%/50%/100% detection, is consumed after ordinary detection, and persists the
victim-wide 120-second protection window through account tags. The same feature-gated service now
allows the first unlawful non-Hot monster-corpse transfer, then blocks that offender account from
repeating against the same corpse for ten minutes. Bank/Cool region restrictions remain deferred;
`theftProtection` is false in Alpha 1 and automatically bypasses corpse protection while
`hotZones` is enabled.

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
