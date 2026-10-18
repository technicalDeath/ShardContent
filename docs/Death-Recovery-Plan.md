# Death recovery: work plan

**Status:** signed off with changes, then **built 2026-10-17**. Every flag is **off**; nothing is deployed or committed. Live and real-client testing is held for the owner's batch test.

## The owner's rulings at sign-off (2026-10-17)

These replace the plan's numbers where they differ.
- **Corpse time:** "the timer for a corpse turning to bones should be raised to 10 minutes". This applies to player corpses only, under the new flag `longerPlayerCorpses`; monster corpses keep the stock 7. Bones still last 7.
- **Materializing:**
  - "should last 10 minutes";
  - it "should end based on the actions listed, but also 60 seconds after you open your corpse", not after emptying it;
  - other players see it in a ghostly hue: `SolidHueOverride` 0x047E, a pale silver picked in the real client (0x4001 draws as a black shadow), which is not saved;
  - buying and selling end it, with a warning.
- **Killer goes home:** its 2 minutes start "when the monster first sees the player" again.
- **Blue self-loot:** Criminal Intent counts as blue, so blue means not a murderer and not a criminal.

**Owner's choice (2026-10-17):** all four ideas, A to D. D applies "only if the monster is not engaged in combat with someone else". Self-loot (C) is "enabled only for players who are blue". These are for every player, with no new-player systems. It follows the corpse timer notice (`Corpse-Timer-Notice-Evidence.md`).

Each idea gets its own flag, built **off**, and is held for the owner's batch test. They are listed in build order, smallest first.

## B. Corpse compass (`corpseCompass`)

- **Design:** while you are a ghost, and after you are resurrected, an on-screen arrow points to your own corpse.
  - It is the arrow the Tracking skill uses: server `NetState.SendSetArrow`, packet 0xBA. ClassicUO already draws it.
  - It stops when the corpse is emptied (`Corpse.LootResolved`), rots away, or you are within 2 tiles of it.
  - It starts again after a relog while the corpse is still there.
- **Changes:** shard service only. The death hook, a lift hook and a short refresh timer. No engine change.
- **Verification:**
  - unit tests for the start and stop rule;
  - live: die, then check the arrow as a ghost and after resurrection, and that it stops on emptying;
  - a real-client screenshot.

## C. One-click self-loot for blue players (`blueSelfLoot`)

- **Design:** the stock Age of Shadows behaviour, already in ModernUO and switched off before AOS.
  - Double-clicking your own corpse takes everything back into your pack, in its old places.
  - Gear you wore at death goes back on, if the slot is free (`Corpse.Open` with `checkSelfLoot`, `RestoreEquip`).
  - It is available only while you are **blue**: not a murderer, not a criminal, and not showing Criminal Intent.
  - Anyone else opens the corpse as before, item by item.
- **Changes:**
  - one engine hook, `Corpse.SelfLootAllowed(owner, corpse)`, null by default. Where set, it replaces the three `Core.AOS` checks:
    - recording item places at death;
    - recording the worn-gear list;
    - self-loot on double-click.
  - `PlayerMobile.EquipSnapshot` is already recorded in every era.
- **Verification:**
  - unit tests for the blue rule;
  - live: a blue character, a criminal and an Intent character each double-click their own corpse; gear goes back on; a full pack leaves the rest in the corpse with the stock "didn't fit" path;
  - a real-client screenshot.

## D. The killer goes home (`killerGoesHome`)

- **Design:** when a wild monster kills a player and is **not fighting anyone else** at that moment, it:
  - drops the fight;
  - walks back toward its spawn home;
  - ignores that player for 2 minutes after they are resurrected.

  "Not fighting anyone else" means it has no living combatant, aggressor or opponent other than the dead player. If it is fighting someone else, nothing changes. Pets, summons and townsfolk are never affected.
- **Changes:**
  - one engine hook on creatures' sight, `BaseCreature.TargetFilter(creature, target)`, null by default. It is consulted in `BaseCreature.CanSee` for wild creatures only, so pets still see their owners. Every AI check that uses `CanSee` follows it: new targets, keeping a target, and spells.
  - The shard keeps a short "spared" list of creature, player and time.
- **Verification:**
  - unit tests for the engaged rule and the time limit;
  - live on a disposable host: a troll kills a test character and walks home; after resurrection the character walks past it unharmed for 2 minutes;
  - a second case with two players, where the troll keeps fighting the other one.

## A. Materializing (`materializing`)

- **Design:**
  - **Starts:** on any resurrection.
  - **Monsters:** cannot see you, through D's sight hook. Monsters already fighting you drop you.
  - **Players:** see you as normal. Safe World still protects innocents; in a Hot Zone you can be attacked as usual.
  - **Allowed without ending it:**
    - walking and running, and opening doors;
    - opening your backpack, your bank box and your own corpse or bones;
    - moving items between those, and putting gear on and taking it off;
    - speaking.
  - **Any other action** gets a warning first ("This will end your materializing. Do it again within 10 seconds to go ahead.", the same shape as the criminal-act confirmation). A second try within 10 seconds ends it. Those actions are:
    - attacking or entering war mode;
    - casting;
    - using a skill;
    - double-clicking anything except containers, corpses, doors and gear;
    - lifting from the ground or another container;
    - buying or selling.
  - **Ends:** 60 seconds after your corpse is emptied (at once if you have no corpse), or after 3 minutes at most, or on a confirmed action.
  - **Shown:** as a buff icon with a countdown. The shard adds its own icons through `buff-extra.txt`.
  - **Why it ends after your corpse:** so it can't serve as a free pass past monsters, for example a friend resurrecting you deep in a dungeon.
- **Changes:**
  - **Engine:** one gate hook, `PlayerMobile.ActionGate(player, action)`, null by default, which can refuse an action. It is called from:
    - `Mobile.Use` (double-click);
    - `UseSkill`;
    - `Spell.Cast`;
    - `DoHarmful`;
    - war mode;
    - `Mobile.Lift`;
    - the vendor buy and sell handlers.
  - **Shard:** the state, the warning, the buff and the timers. It uses D's sight hook.
- **Verification:**
  - unit tests for the allowed and ending action table and the timers;
  - live: resurrect at the healer, walk past a troll, open the bank, empty the corpse, re-equip, and confirm no hits;
  - each ending action: first attempt warns, second ends it;
  - the dungeon case: no corpse there, so it ends in 60 seconds;
  - real-client screenshots of the warning and the buff.

## Across all four

- **Activation:** each flag is off until the owner says activate. All four ride the batch test with the guards, stamina and corpse-timer flags.
- **Bot farm:** the watcher can measure:
  - corpse recovered vs lost;
  - deaths within 5 minutes of a resurrection;
  - time from resurrection to rearmed.

  The bots will need brain rules for the arrow, self-loot and the materializing warning.
- **Era:** C is stock code, from Age of Shadows (2003). A, B and D are new shard rules the owner asked for.

**Later the same day:** the owner ruled "The materializing warning should be a dialog like the criminal action warning". An ending action now opens an OKAY/CANCEL dialog; OKAY ends materializing and replays the action. See `Batch-Test-2026-10-17.md`.

## What was built

- **Engine hooks** (ModernUO UOContent, uncommitted), all null or empty by default:
  - `Corpse.DecayTimeOverride`, `InitialDecayTimeFor`, `RecordsRestore`, `SelfLootAllowed` and the event `OwnerOpened`;
  - `BaseCreature.SightFilter`, consulted in a new `CanSee` override;
  - `PlayerMobile.ActionGate`, with the enum `PlayerAction`. It is called from `AllowItemUse`, `AllowSkillUse`, a new `CheckSpellCast` override, a new `OnDragLift` override and a new `Attack` override, and from `BaseVendor.VendorBuy`/`VendorSell`;
  - the event `PlayerMobile.Resurrected`.
- **Shard:**
  - `DeathRecoveryRules` (the config section `deathRecovery`);
  - `DeathRecoveryServices.cs`, holding `LongerPlayerCorpses`, `CorpseCompass`, `BlueSelfLoot`, and `DeathRecovery`, which registers the parts and the one sight filter;
  - `KillerGoesHome.cs`;
  - `Materializing.cs`, which shows the stock stealth buff icon with the shard's text.
  - The guide's Dying page describes each part while its flag is on, and now always says a healer sees a ghost only in war mode.
  - The corpse notice quotes each corpse's real time.
- **Flags:** `longerPlayerCorpses`, `corpseCompass`, `blueSelfLoot`, `killerGoesHome`, `materializing`.
- **Checks:** `DeathRecoveryTests`, 29 cases. Shard suite 1,609 passed; UOContent 1,404 passed (runs `20261017T134140515Z-73c4d9`, `20261017T134311515Z-68172e`).
- **Not yet checked live:** every live and real-client step listed above under each part.

## Open questions (answered at sign-off)

1. **A:** should other players see a materializing character as normal, or in a ghostly hue so they know it can't be fought by monsters?
2. **A:** do buying from and selling to vendors end materializing, as planned, or are they allowed like the bank?
3. **D:** is 2 minutes the right time for the killer to leave the resurrected player alone?
4. **C:** is "blue" right as not a murderer, not a criminal and not showing Criminal Intent?

## Deferred

- E: corpses last while you're a ghost.
- F: healer recovery of your corpse's contents to the bank, as a gold sink.
- G: a brief grace period after resurrection, which A replaces.
