# World actions: plan for the next set (2026-11-01; wave 1 signed off and built)

The owner's answers (2026-11-01): items in the backpack get actions too; an action never walks the player; wave 1 first. Wave 1 is recorded in `World-Actions-Evidence.md`.

The proof of concept (a tree: Chop wood) is in `World-Actions-Evidence.md`. This plan covers the next actions, grouped into waves. Each wave is built, unit-tested and photographed in the real client, then goes on the farm for the owner to try. Every rule and message below comes from the stock code (file references in the research notes at the end), not from guesses.

## Two channels, one look

| What is clicked | Has a serial? | Channel |
| --- | --- | --- |
| Map statics and ground: trees, rock, cave floor, water, town forges, anvils and ovens | No | The shard's own menu, command 0xB1 (built for Chop). The client must also ask for **land** tiles (mountain, cave floor and water are land), which today it does only for statics. |
| Items (in the pack or the world), addons (spinning wheels, looms), corpses, creatures | Yes | The stock context menu, which the client already opens on a left click. Shard entries are added through `ContextMenuSystem.ItemEntriesHandler` (the hook the About entry uses). Creatures need one small engine hook of the same kind. |

To make both channels look the same:
- **Greyed:** the stock menu already greys an entry (flag 0x01).
- **Sorted:** the client will sort greyed entries to the bottom.
- **Reason as tooltip:** the stock menu has no tooltips. The server will send the reasons alongside the menu (0xB1, keyed by serial and entry), and the client will attach them as tooltips.
- **Text:** stock menu labels are client text numbers, so each new label gets a line in the shard's `Clilocs.txt`.

## Wave 1: gathering on the map (statics and land; the same harvest code as Chop)

| # | Clicked | Action | Can't, because (tooltip) |
| --- | --- | --- | --- |
| 1 | Tree | Cut kindling | "Requires a knife, dagger or sword." / too far (2 tiles) / "There's not enough wood here to harvest." |
| 2 | Mountainside, cave floor, cave rock | Mine | "Requires a pickaxe or shovel." / "You can't mine while riding." / too far (2) / "There is no metal here to mine." |
| 3 | Water (land or static) | Fish | "Requires a fishing pole." / "You can't fish while riding." / too far (4) / fished out: "The fish aren't biting here. Try water 8 or more tiles away." |

- Fish answers QoL item 28. A fishing spot is an 8x8 square of water, chosen by where you cast rather than where you stand, so the reason can say how far to move.
- Neither a pickaxe, shovel nor fishing pole has to be equipped, so these actions just use the tool from the pack. Each starts the stock harvest directly (`StartHarvesting`), so skill, yields and the gathering repeat are unchanged.
- Kindling has no direct method. It runs the stock bladed-item cursor and answers it in code, the way the shard's action repeat already answers cursors.

## Wave 2: workstations

| # | Clicked | Action | Can't, because |
| --- | --- | --- | --- |
| 4 | Forge (static or item) | Smelt ore | "Requires ore." / "You need more Mining to smelt this ore." (coloured ore) / too far (2) |
| 5 | Anvil, with a forge near | Smith | "Requires a smith's hammer or tongs." / "You need a forge nearby as well." |
| 6 | Heat source: campfire, oven, fireplace, forge | Cook | "Requires raw food." / too far (1). One entry per kind of raw food carried, e.g. "Cook raw ribs (3)". |
| 7 | Spinning wheel (addon, has a serial) | Spin | "Requires wool, cotton or flax." / "That spinning wheel is being used." / too far (3) |
| 8 | Loom (addon) | Weave | "Requires yarn or thread." / too far (3) |

- Smelting and cooking have no direct method, so they answer the stock cursor in code.
- Smithing opens the stock T2A smithing menu, which still asks which metal.
- Spinning calls the stock `SpinOn`.

## Wave 3: things you carry (the stock menu on a left click)

| # | Item | Actions | Can't, because |
| --- | --- | --- | --- |
| 9 | Bandage | Heal yourself; Heal someone (opens the cursor) | "You are not hurt." |
| 10 | Heal / Cure / Refresh potion | Drink | "You are already at full health." / "You are not poisoned." / "You are already at full stamina." / "You are poisoned. Cure the poison first." (heal) / "You must have a free hand to drink a potion." |
| 11 | Food | Eat (stock entry) | Greyed when full: "You are simply too full to eat any more!" |
| 12 | Kindling | Light a fire; Feed the fire (when one is within 1 tile) | "You cannot light a fire in a dungeon." / "The fire has only just been tended." |
| 13 | Hides, cloth, clothing | Cut (scissors) | "Requires scissors." (before AOS, hides cut to leather) |
| 14 | Ore; raw food | Smelt; Cook | "Needs a forge within 2 tiles." / "Needs a fire or oven within 1 tile." |
| 15 | Locked container or door | Unlock (key); Pick the lock (lockpick) | "Requires its key." / "Requires a lockpick." / "This lock is beyond your skill." |

Care point: the heal potion's own check starts its 10-second wait, so a menu must not call it to test availability. The shard keeps its own copy of the rules for that test.

## Wave 4: creatures

Built 2026-11-01 on the owner's "Do wave 4", with Ride, Feed and bandaging added (see `World-Actions-Evidence.md`).

| # | Clicked | Action | Can't, because |
| --- | --- | --- | --- |
| 16 | A tamable animal | Tame (the stock entry, greyed only for one rule today) | "You need N Animal Taming to tame this." / "That animal looks tame already." / "You have too many followers." / too far (2) / "That creature cannot be tamed." |

- This answers part of QoL item 30.
- It needs a creature hook in the engine, like the item one.
- An unreachable animal can't be known ahead: the stock check needs a path. The menu says it only after an attempt.

## Questions for the owner

1. Things in the backpack: should a left click on an item there open its menu too (it already opens the stock menu), or should the actions be for the world only?
2. Which wave first? The recommendation is wave 1: it is the cheapest (same code path as Chop), and it answers QoL item 28 and the kindling question.
3. Should an action that needs walking (too far) walk the player there and then do it, instead of greying out? That is more convenient, but it moves the character on a click.

## Out of scope for now

- Sand and stone mining: they need a Mining book, and those vendors may not be on the shard.
- Lumber into boards.
- Treasure maps.
- Anything after UOR.

## Research notes

Survey of the stock rules, 2026-11-01:
- Mining: `Engines/Harvest/Mining.cs`; tools in `BaseAxe.cs` and `BaseHarvestTool.cs`.
- Fishing: `Fishing.cs`, 8x8 banks keyed by the target tile.
- Kindling from a tree: `Targets/BladedItemTarget.cs` (knives and swords, range 2, 5 wood per kindling).
- Smelting: `Ore.cs`, forge IDs and `[Forge]` types.
- Smithing: `DefBlacksmithy.CheckAnvilAndForge`, `T2ACraftSystem.ShowMenu`.
- Cooking: `CookableFood.IsHeatSource` (campfire, ovens, fireplaces, forges; range 1).
- Spinning: `Wool/Cotton/Flax.SpinOn`, `ISpinningWheel` addons only.
- Weaving: `ILoom` addons.
- Bandage: `BandageTargetRequest`, range 1 before AOS.
- Potions: `BaseHealPotion` / `BaseCurePotion` / `BaseRefreshPotion`.
- Food: `Food.Eat`.
- Kindling: `Kindling.cs` plus the shard's `CampingService`.
- Scissors: `Hides.cs` (cutting allowed before AOS).
- Locks: `LockPick.BeginPick`, `Key.UseOn`.
- Taming: `AnimalTaming.cs` and `BaseCreature` TameEntry.
- Context menus are on in this era (`expansion.json` `ContextMenus`).
