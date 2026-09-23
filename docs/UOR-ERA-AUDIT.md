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
| Archery | `Items/Weapons/Ranged/{BaseRanged,Bow,Crossbow,HeavyCrossbow}.cs`; `Items/Weapons/BaseWeapon.cs` | Pre-AoS ranged attacks require one second since the last move, use each weapon's old damage/speed/range profile, consume arrows or bolts when fired, and retain ordinary hit checks and two-handed equipment requirements. Bow/crossbow/heavy-crossbow profiles are respectively 9–41/20/10, 8–43/18/8, and 11–56/10/8 (damage/speed/range). | Retain | Archery keeps range, ammo, cadence, and positioning as its differentiators; no blanket accuracy, speed, or damage buff is enabled. | `ClassicCombatIdentityTests.UorRangedWeapons_PreserveClassicProfilesAndConsumeTheirAmmo`; manual movement/cadence matrix required below. |

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
   the one-second movement restriction, cadence, range, hit/miss outcomes, and arrow/bolt use in
   PvP and PvM.
