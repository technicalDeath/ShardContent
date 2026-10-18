# Craft and spell chances in tooltips

Flag: `featureFlags.craftChances`. It is **off** in the source config and held for the owner's batch test. Nothing is committed or deployed.

## What the owner asked for

1. On 2026-10-17: "I like the idea of a ? Icon on the craft menu that toggles on the gain % chance right on the menu." He signed off "Yes, build it", showing both the gain and the make chance.
2. Later the same day, after seeing the numbers drawn under the pictures: "I realize this info would do better in the existing tooltip." The numbers now go in the tooltip, and the "?" button is gone, since nothing is left on the menu for it to switch.

## What a player sees

When a player hovers an item on a craft menu page (the old T2A picture menus: blacksmith, tailoring, carpentry, tinkering, bowcraft, alchemy, cartography, inscription), the tooltip shows the item's name and materials, as before, followed by two lines:

- Chance to raise your skill: N%
- Chance to make it: N%

Category pages, repair and smelt entries carry no numbers. Crafting itself is unchanged.

## How it works

- **Engine (ModernUO, UOContent only).**
  - `Engines/Craft/T2A/T2ACraftMenu.cs` is the new base of the eight T2A menus. It knows the menu's craft system, the item types on the page, and the chosen resource (ingot colour).
  - `ItemFor(entry)` returns the craft item behind an entry. Cartography and Inscription override it, because their entries index differently.
  - The static event `Sent` fires after a page is sent.
- **Shard.** `CraftChancesService.cs` handles `Sent` and sends extended command **0xAE** with:
  - the menu serial;
  - a count;
  - a gain byte and a make byte per entry (255 for an entry that is not an item).
- **How the numbers are worked out.**
  - **Make chance:** stock `CraftItem.GetSuccessChance`. It is 0 if the player lacks a required skill.
  - **Gain chance:** what stock `SkillCheck` gives for one attempt at the item's main skill. It weights the success and failure gain rolls by the make chance, and applies the gain factor and the shard's gain curve (`SkillEvents.InvokeGainChanceMultiplier`).
  - The gain chance is 0 in these cases:
    - the check is no challenge (always made);
    - the check is out of reach;
    - the skill is locked;
    - the skill is at its cap;
    - the skill total is full and no other skill is set to go down.
  - Below 10 skill the gain chance is 100%.
  - A gain rounds up, so a real chance never shows as 0%. A make chance rounds down.
- **Client (ClassicUO fork).** `MenuGump.SetChances` appends the two lines to each entry's tooltip. The 0xAE case is in `PacketHandlers` (extended command switch).

## Verification

| Case | Setup | Observation | Result |
| --- | --- | --- | --- |
| Unit tests (`tests/CraftChancesTests.cs`, 10) | n/a | <ul><li>Always-made and out-of-reach items give 0.</li><li>A harder item teaches more.</li><li>The result matches a hand-worked stock roll.</li><li>Below 10 gives 1.0; a locked skill gives 0; the curve scales it.</li><li>Rounding is as described.</li><li>The packet bytes are correct.</li><li>The flag is off by default.</li></ul> | Pass; run `20261017T191626511Z-6cfb98` (`-Suite All`; shard 1,641 passed) |
| Category page | Real client, host `batch`, flag on in the host config only; a tailor at about 55 with a sewing kit, cloth and leather | No numbers on a page of categories | Pass (`images/craft-chances/category-page.png`) |
| Easy item | Same; shirts page | Doublet tooltip: 0% to raise, 100% to make | Pass (`images/craft-chances/tooltip-doublet-no-gain.png`) |
| Item in range | Same; leather armour page | Leather gloves tooltip: 60% to raise, 64% to make | Pass (`images/craft-chances/tooltip-gloves-gain.png`) |

- All screenshots were taken in the real ClassicUO client, using a build from `work/player-client-dist-batch`; `ClassicUO/bin/dist` was not updated.
- The first version, with numbers under the pictures and a "?" toggle, was also photographed before the owner moved the numbers to the tooltip. That version's code is gone.

## Spell tooltips (`featureFlags.spellChances`, off)

After the craft menu, the owner (2026-10-17): "Also add this info to spell tooltips", and then "Also test the hotbar and loose spell shortcut icons".

- **What a player sees.** Every Magery spell tooltip ends with two lines:
  - "Chance to raise Magery: N%"
  - "Chance to cast it: N%"

  The tooltip can be in three places:
  - the spell icon in the spellbook;
  - the shard's spell hotbar under the potion and combat bars;
  - a loose spell icon dragged onto the screen.
- **How the numbers are worked out.**
  - The cast chance is the book cast's own range (`GetCastSkills`, the same as the fizzle check) against the current Magery value.
  - The gain chance is the craft formula for that check.
  - Casting from a scroll has a lower range; the scroll's single-click name already shows its own chance (`scrollSuccessChance`).
- **Engine.** The event `Spellbook.Displayed` is raised after a spellbook is sent.
- **Shard.** `SpellChancesService` sends extended command **0xAF**: a count, then per spell its client number (from 1), a gain byte and a cast byte. It sends:
  - 3 seconds after login (sent at the moment of connection, the client was still entering the world and lost it; seen in the live test and fixed);
  - when a spellbook opens;
  - after a Magery check, if a number changed.
- **Client.**
  - `Game/Managers/SpellChances.cs` holds the numbers.
  - `SpellbookGump`, `UseSpellButtonGump` and `SpellBarGump` add them to their tooltips.
  - New numbers refresh an open book and the loose icons at once; the hotbar refreshes itself.

| Case | Observation | Result |
| --- | --- | --- |
| Unit tests | The spell packet numbers spells from 1; the flag is off by default | Pass; run `20261017T200334341Z-471ffb` (shard 1,643) |
| Spellbook, Heal (57 Magery) | 0% to raise, 100% to cast | Pass (`images/craft-chances/spellbook-heal.png`) |
| Spellbook, Paralyze | 56% to raise, 43% to cast | Pass (`images/craft-chances/spellbook-paralyze.png`) |
| Hotbar, straight after login | Dispel: 58% to raise, 18% to cast | Pass, after the login fix (`images/craft-chances/spell-hotbar-after-login.png`) |
| Loose icon dragged off the hotbar | Dispel: 58%, 18% | Pass (`images/craft-chances/loose-spell-icon.png`) |

Not checked live: a number changing after a cast raises Magery. The resend is coded, and the packet is unit-tested.

## Activation

- Activation needs the owner's word.
- Deploying it needs three things:
  - a UOContent rebuild into `Distribution`, because the engine changed;
  - a shard deploy;
  - the rebuilt `cuo.dll` in `ClassicUO/bin/dist`.
- An old client ignores 0xAE.
