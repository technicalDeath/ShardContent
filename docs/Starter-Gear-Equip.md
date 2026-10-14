# New characters wear their starter gear

**2026-10-14.** The owner started a Mace Fighter and it was not wearing its armor.

## Cause

Stock creation (`CharacterCreation.GiveProfessionItems`) hands out each template's armor with `EquipItem`, which quietly drops an item into the backpack when it cannot be worn. It does this while the character still has the packet's stat spread. The 7.0 client's new-character screens send a spread that does not add up to the 90 points stock expects, so stock falls back to 10/10/10 (`SetStats`). Studded armor needs 25 to 35 Strength, so only the Bascinet and the boots were worn; the gorget, tunic, sleeves, gloves and leggings sat in the pack. The shard sets the real starting stats a moment later (`Alpha3StartingStats`, 54/33/33 for a Mace Fighter), too late for the equip.

The same gap hit every template: the Archer's bow (Strength 20), the Fencer's and Swordsman's studded suits, and so on.

## Fix

`StarterGearEquip` (`src/BritanniaRenaissance.Content/StarterGearEquip.cs`, registered after `StarterCombatIssuance`) runs after the shard has set the real stats and wears, from the backpack, into free slots:

1. every armor piece (plain clothing in the same layer, such as the stock pants under the leggings, goes to the pack and is put back if the armor cannot be worn),
2. a shield,
3. the weapon the character is best at: a worn weapon gives way only to one of a strictly higher skill (an Archer's bow, not the dagger or skinning knife that came with another skill) and returns if the better one cannot be worn.

It never takes anything off otherwise and never touches an occupied slot. It does not depend on a feature flag.

## Checked (disposable host with the deployed build, real creation packets)

| Template | Worn after creation |
| --- | --- |
| Mace Fighter | club, wooden shield, helm, studded gorget, tunic, sleeves, gloves, leggings (before: club, shield, helm, boots only) |
| Fencer | kryss, shield, full studded suit |
| Swordsman | katana, shield, full studded suit |
| Archer, Ranger, Bard | bow (two-handed), leather tunic, leather leggings (Ranger had a skinning knife in hand and the bow in the pack before the best-skill rule) |
| Pure Mage, Warlock | robe, hat, clothing; Warlock's katana |

Pass on every row after two iterations: the first build left the Archer holding a dagger, the second the Ranger holding a knife.

## Limits

No unit test: the logic needs live mobiles and items. The disposable-host runs above are the evidence. Gear in the pack that is not starter gear is not a case here, since it only runs at creation.
