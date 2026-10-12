# Combat bar

Signed off 2026-10-12 by the owner ("Yes to all", Shift-click tooltip must mention itself). Client only: no server flag, no packet. On for new profiles (`combat_bar_enabled` in `data/client/default-profile.json`, pinned by `ClientDefaultsTests`).

## Design
- `CombatBarGump` (ClassicUO fork), just under the potion bar (below the game window when the potion bar is not showing; hidden when there is no room; stays where the player drags it).
- Slots: Bandages; Arrows, Bolts; the eight reagents; two equipment slots (the weapon or tool held last, and the one before it).
- Bandages: click = double-click the bandage and answer the target cursor with yourself; Shift-click = leave the cursor open. The tooltip says so.
- Equipment slots: click equips (taking off what blocks it: a two-handed weapon clears both hands, a one-handed one its own hand and any two-handed weapon), click on the one in hand puts it away. Serials are kept in the profile (`CombatBarLast`, `CombatBarPrevious`).
- Modes like the potion bar: every item (default), only the items you have, docked to one bandage icon (`CombatBarMode`).
- Counts read the pack tree on the client. Items in bags the client has not seen are known after the potion bar's silent bag opening at login.

## Evidence
Owner additions: reagents show only for a character with Magery, Alchemy or Inscription above 0; Shift-click tooltip on the bandages; the hotbar word is "item shortcut".

- Unit: full shard suite 1280 passed (run 20261012T143402400Z-9a3fa1); `ClientDefaultsTests` pins `combat_bar_enabled`.
- Real client (ClassicUO, disposable host, test-only commands `TestOnlyGive` and `TestOnlyHold` added to `tests/scenarios/alpha3-tools/TestOnlyProbe.cs`): counts for bandages, ammo and reagents match the pack; bandage click answered "Who will you use the bandages on?" and self-targeted ("That being is not damaged!"); tooltip reads "Click to bandage yourself. Shift-click to choose who to bandage."; the held-slot showed the club (a shield is not counted: tile data flags shields as weapons, so shields are told apart by graphic); click put the club away and back; halberd (two-handed, shield cleared by the server command) swapped to the longsword from the bar with the slots exchanging places; shrunk, docked and restore states; the Armsman has no reagents, a Magery character shows all eight.
- Screenshots in `work/player-client/HelpAlpha/shots/` (cb-bandage, cb-swap, cb-shrunk, cb-docked, cb2) and `work/help-gumps/cbcrop-*.png`; sent to the owner.
- Not exercised: relog persistence of the two slots (profile fields `CombatBarLast`/`CombatBarPrevious`), a real bandage heal, ammunition in a quiver.

## Files
`CombatBarGump.cs` (new), `Profile.cs`, `GameScene.cs`, `default-profile.json`; `cuo.dll` republished into `ClassicUO/bin/dist`, `Data/Profiles/default.json` recopied.

## Hand items (second real-client run, 2026-10-12)
Checked after the owner asked about shields and two-handed items. Every shield the server makes (BaseShield: 0x1B72-0x1B76, 0x1B79-0x1B7B, 0x1BC3-0x1BC4) is inside the graphic ranges IsShield uses; Spellbook and Runebook (0x0EFA, 0x22C5) sit on the one-handed layer and are ignored; a fishing pole (0x0DC0/0x0DC1, two-handed, not flagged as a weapon) counts as a tool. Real client: a worn Spellbook and a worn Buckler are not tracked; a Pickaxe and a FishingPole are tracked as held; the Pickaxe slot cleared the two-handed pole; the Pickaxe equipped with a Buckler worn and the Buckler stayed; the Halberd slot (two-handed) cleared both the Pickaxe and the Buckler and equipped the Halberd. Not tested: shields other than the Buckler, torches and lanterns (two-handed layer, deliberately ignored), a tool other than the Pickaxe and pole.

A weapon or tool slot whose item is not in hand is labelled `equip` (held: `held`, no item: `empty`); checked in the real client 2026-10-12 (pickaxe held, longsword equip, then swapped by a click).

## Three slots (2026-10-12, owner request)
Replaces the two "last / previous" slots: a main-hand weapon slot, a shield slot and a tool slot, each remembering the last item of its kind (`CombatBarMain`, `CombatBarShield`, `CombatBarTool`). A slot with no item shows its name (weapon, shield, tool); an item in hand shows `held`, one not in hand shows `equip`. Tools: pickaxe, hatchet (also an axe, so it goes here), shovel, fishing pole, smith's and sledge hammers, tongs. Spellbook and runebook are ignored. Conflicts: two-handed weapon or pole clears both hands; a shield clears the two-handed layer; a one-handed item clears the one-handed layer and any two-handed weapon or pole but keeps a shield.
Real client (disposable host, 2026-10-12): pickaxe goes to the tool slot while club and shield stay; spellbook in hand is ignored; club over a spellbook; fishing pole clears the shield; shield clears the pole; pole clears the shield; club clears the pole; shield clears a halberd. Not tested: hatchet, shovel, hammers, tongs, relog persistence of the three slots, other shields than the starter round shield and the Buckler.
