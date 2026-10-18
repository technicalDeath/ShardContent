# Stamina numbers over your head

**Flag:** `featureFlags.staminaNumbers`, built 2026-10-16. **Off**: not activated, not deployed, not committed, not installed in the player client.

## The owner's ruling (2026-10-16)

"Stamina lost should show up alongside hitpoint floaty damage with an option for players to turn it off. And also stamina from refresh potions should have floaty text, also with an option to turn it off", "This way players can see their stamina loss when they fight vs maces."

## What it does

**Engine events** (ModernUO), each raised with the stamina really changed, after the bar's ends:
- `StaminaSystem.DamageFatigueApplied`: a hit's fatigue, after the cap from `staminaRelief`.
- `BaseWeapon.HitDrainedStamina`: a mace's or staff's drain. `BaseBashing` and `BaseStaff` now drain through `BaseWeapon.DrainStamina`.
- `BaseRefreshPotion.StaminaRestored`: a Refresh or Total Refresh potion.

**Shard** (`StaminaNumbersService`):
- It sends extended command 0xAD to the player whose stamina changed, and to nobody else.
- The packet carries the serial, the kind (0 = lost to a hit, 1 = restored by a potion) and the amount.
- The losses within one game tick are added together, so a mace hit (fatigue plus drain) shows one number.

**Client** (ClassicUO `OverheadNumbers`, `OverheadDamage.AddStamina`):
- Draws "-N stam" or "+N stam" in blue (hue 0x005A) among the damage numbers over the head.
- Two Options switches on the Combat-Spells page, both on by default: "Show stamina lost to hits over your head" and "Show stamina from refresh potions over your head".
- They are independent of the damage-and-healing switch.

**Guide:** "Numbers over heads" names the stamina numbers while the flag is on.

## Checks

- `StaminaNumbersTests`, 4 cases: the packet bytes, the show rule, the flag defaults to off, and the guide text.
- The client NativeAOT `cuo.dll` builds. It is in the session scratch folder, not `bin/dist`, because the owner's two ClassicUO windows have the current one loaded.
- **Not yet checked:**
  - the blue in the real client;
  - the two switches;
  - a hit's and a potion's number;
  - that Navrey ignores the unknown subcommand.
