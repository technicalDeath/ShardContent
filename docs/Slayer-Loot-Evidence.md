# Monster-dropped weapons: Silver slayers only (2026-10-13)

Owner rulings, 2026-10-13: "I don't think we want slayer levels? I don't remember them from my time playing UOR", then (asked what to do with the slayer weapons that still drop) **"Keep only silver weapons. We can add slayer type weapons later as craftable items."** Built, tested live on a disposable host, deployed to the dev distribution (server stopped). Uncommitted. No flag: it is an era ruling, like the Mastery change.

## What slayers are

A slayer is a property on a weapon (and, in this code, on musical instruments) naming a group of monsters. A hit on a monster of that group does double damage (+100%) with a small flash; everything else is unchanged. Groups: humanoid (Orc Slaying, Troll Slaughter, Ogre Thrashing, and Repond for the whole group), undead (Silver), elemental, daemon, spider and scorpion, reptilian (dragons, lizardmen, snakes) and fey. Humanoid and undead oppose each other: a wielder of a slayer weapon takes double damage from the opposing group. Source: `Items/Weapons/SlayerGroup.cs`, `SlayerEntry.cs`, `BaseWeapon.CheckSlayers`.

The date slayers entered UO could not be confirmed online (2026-10-13); a 2004 forum post confirms they existed before Age of Shadows. The owner's memory of UO:R is the era evidence used.

## How they dropped here

Only from monster loot, through the stock pre-AoS branch of `Misc/LootPack.cs`: a magic weapon has a 5% chance of **Silver**; failing that, a weapon with no other magic has a 5% chance of the slayer of the dropping monster's group (`SlayerGroup.GetLootSlayerType`, which gives Silver for any monster not listed under a group). Nothing crafts them.

## What changed

- ModernUO `LootPackEntry.WeaponLootSlayerAllowed` (new, `Misc/LootPack.cs`): an optional filter on the second branch. A slayer it refuses is not given. No filter, no change (2 tests, `LootPackWeaponSlayerTests`).
- `SilverOnlyWeaponLoot` (new, registered in `ShardBootstrap`): allows Silver and nothing else. Tests: `SilverOnlyWeaponLootTests` (9).
- The first branch (a plain 5% Silver) is untouched.

## Evidence

- Live, disposable host, test-only probe `[TestOnlySlayerLoot <rolls> [stock]` (rolls the Average and Meager loot packs for a Bone Knight, a monster whose own slayers are the humanoid ones): **400,000 rolls with the stock loot: 15,172 weapons, 803 Silver and 34 other slayers (OrcSlaying 7, TrollSlaughter 9, OgreTrashing 10, Repond 8). The same with the shard's filter: 15,064 weapons, 762 Silver and none.** Silver stays at about 5%.
- Shard suite 1405 passed (run `20261013T214146472Z-96c0d0`); engine tests 2 of 2.
- Deployed: ModernUO rebuilt into `Distribution`, shard deployed, dev server boot-checked (world loaded, no errors) and stopped.

## Limits

- **Not touched:** weapons that already carry another slayer (the dev world's existing weapons were not examined); slayer **instruments** (monsters drop instruments with the slayer from `GetLootSlayerType`, which is Silver for nearly every monster); the creature magic-item pack in `BaseCreature.cs`, which gives Silver only (5%); artifacts such as the Tokuno ones, which carry their own slayers and are not in this era's loot (not checked in the world).
- The tooltip lists no slayer (owner), and the identified single-click label still names one.
- A rare drop (about 1 in 400 magic weapons) is all this removes: the visible effect is small.

## Files

ModernUO: `Projects/UOContent/Misc/LootPack.cs`, `Projects/UOContent.Tests/Tests/Misc/LootPackWeaponSlayerTests.cs`. ShardContent: `src/BritanniaRenaissance.Content/SilverOnlyWeaponLoot.cs`, `ShardBootstrap.cs`, `tests/SilverOnlyWeaponLootTests.cs`, `tests/scenarios/alpha3-tools/TestOnlyProbe.cs` (`[TestOnlySlayerLoot`).
