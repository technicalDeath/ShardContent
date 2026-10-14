# Item tooltips (2026-10-13)

Owner request, 2026-10-13: "Item and weapon tooltips should be turned on. Show me what they look like once you can do this work." Built, verified in the real client on a disposable host, **activated** (`featureFlags.itemTooltips` true) and deployed to the dev distribution, server stopped. The weapon stat tables were removed from the About pages the same day on the owner's word that such numbers belong on tooltips (`New-Player-Pass-2026-10-13.md` item 38).

This is a departure from the era: property lists arrived with Age of Shadows. The shard turns them on for items only, with the shard's own, smaller list.

## The risk it had to avoid

The earlier survey (`Help-And-Feedback-Survey-2026-10-13.md`, "Deliberately not done") warned never to flip `opl.enable` raw: the 136 stock `GetProperties` overrides print exact magic (damage and accuracy levels, resists, charges, slayers, poison) that Item Identification, Arms Lore and Taste Identification exist to tell. Auditing 136 overrides is not a safe plan, so the shard does not filter the stock lists, it **replaces** them.

## How it works

| Piece | What it does |
| --- | --- |
| ModernUO `Item.PropertyListBuilder` (new, `Projects/Server/Items/Item.cs`) | One optional delegate. When it is set and returns true, it has filled the item's property list and the stock `GetProperties` is not called. With no builder nothing changes (4 tests, `ItemPropertyListBuilderTests`). Uncommitted |
| `ItemTooltipService` (new) | Sets the builder and, once the server has started, turns the stock property switch on (the era's expansion setting leaves it off). The builder writes only what is in the next table and says "handled" for every item, so no override's text is ever sent |
| `MenuBarService` | The login mask (extended command 0xA8) gets a new bit, `Tooltips` (1 << 5). It is sent with or without the shard top bar, so the stock bar keeps working |
| ClassicUO `ClientFeatures.ShardTooltips` / `TooltipsActive` (new) | The era's character list leaves the client's own tooltip switch off, and that switch also changes how a single click works (it stops the overhead name), so the shard's tooltips are a separate switch: the client asks for and draws **item** property lists only, never a mobile's, and keeps the single-click name |

## What a tooltip says

Only for items a player could pick up, that are locked down or secure in a house, or that are inside something or worn. Doors, signs, corpses, the showroom's display copies and other scenery have none.

| Item | Lines |
| --- | --- |
| Any item | the stock name line (with an amount), "newbied: kept when you die" or "blessed" when it is, and its weight (a bag's contents included) |
| A weapon (not a wand) | the maker and "exceptional" when the single-click label also says them, then damage, speed, range if it shoots, Strength needed, one or two hands, the combat skill: the **numbers of the kind** (a Katana's 5 to 26), never the one in the hand |
| Armor and shields | the same, then "armor rating N" of the kind and the Strength needed (the client shows Strength in red when yours is lower) |
| A wand | name and weight only: its charges and its spell are what Item Identification tells |

**What is never said:** resist and attribute bonuses, poison and its charges, how worn a piece is (Arms Lore and the combat bar's gauge), a material's armor bonus, and, until Item Identification has been used, anything magical. A magic weapon or armor nobody has identified also loses its maker and quality, and gets a plain name line, because its single-click label says only "unidentified"; the stock name line of armor says "exceptional" and the metal.

**Once Item Identification has been used** (owner ruling, 2026-10-13: "Yes it should"), the tooltip lists what the skill found, one line each, in the words of the identified single-click label: a weapon's durability level, accuracy level and damage level ("Indestructible", "Supremely accurate", "Of vanquishing"); **slayers are deliberately not listed** (owner, 2026-10-13: he does not remember them from UO:R; the weapons still drop and still do double damage to their monster group, see the ruling in `To-Do-List.md`), armor's durability and protection level ("Of invulnerability"), and an identified wand's effect and charges ("Of fireball", "11 charges"). The lines come before the kind's numbers. Checked in the real client against the unidentified copy of the same gear.

Shop windows: the vendor's display copy gets the same tooltip. The buy list used to show the display copy's durability; it no longer does, because what a buyer receives is a separate new item with its own durability.

## Evidence

- Tests: shard suite 1391 passed (run `20261013T203402899Z-7b8316`): `ItemTooltipTests` (17 test methods, including the identified-magic lines for weapons, armor and wands: the flag, the mask with and without the shard bar, who has a tooltip, a Katana's and a Bow's lines in the stock texts, the skill texts, armor, newbied and blessed, maker and quality hidden on unidentified magic); `GuideScreenTopicTests` (the guide paragraph, gated). ModernUO `ItemPropertyListBuilderTests` 4 of 4 (run `20261013T192221184Z-e61eea`).
- Real client (ClassicUO, disposable host, character TipTest; test gear from `[TestOnlyMagic`: a Katana with Vanquishing, Supremely accurate, Indestructible, an Orc slayer, Deadly poison and exceptional; a Platemail Tunic with Invulnerability, Indestructible and exceptional; a Fireball wand), shown to the owner: the club on the paperdoll; the magic Katana and Platemail Tunic in the pack (kind's numbers only, no magic, no "exceptional"); the wand (name and weight); a Chainmail Tunic; a starter Studded Tunic (newbied); a Mace in the weaponsmith's buy list; a Katana on the ground; single-click still names the item overhead and opens About; hovering a character shows nothing.
- Deployed: ModernUO rebuilt into `Distribution` (Server.dll, UOContent.dll), shard deployed, help text identical to source, dev server boot-checked (world loaded, no errors) and stopped.

## Files

ModernUO: `Projects/Server/Items/Item.cs`, `Projects/UOContent.Tests/Tests/Items/ItemPropertyListBuilderTests.cs`. ShardContent: `src/BritanniaRenaissance.Content/ItemTooltipService.cs`, `MenuBarService.cs`, `ShardRulesConfiguration.cs`, `ShardBootstrap.cs`, `WelcomeGuide.cs`, `WelcomeGuide.GettingStarted.cs`, `data/configuration/shard-rules.json`, `data/help/items.json` (the two gated sentences on A weapon and Armor), `tests/ItemTooltipTests.cs`, `tests/scenarios/alpha3-tools/TestOnlyProbe.cs` (`[TestOnlyMagic <serial> [identified]`). ClassicUO: `Game/Data/ClientFeatures.cs`, `Game/GameCursor.cs`, `Game/UI/Gumps/TopBarGump.cs`, `GridLootGump.cs`, `ShopGump.cs`, `Network/PacketHandlers.cs`. Tooling: `Send-PlayerClientInput.ps1 -Hover`.

## Limits

- The ModernUO hook, the shard code and the client change are **uncommitted**; the new client is installed in `ClassicUO/bin/dist` (backup in `work/cuo-backup-*-before-tooltips`). A committed ModernUO means a pin bump in `shard-rules.json`, `world-generation.json` and `Alpha2bWorldGenerationConfigurationTests.cs` before the next deploy.
- Mobile tooltips (names, health, pets' details) stay off.
- Not exercised: a tooltip in a locked-down house item, a corpse's contents, the grid container view, and a second character.
- The same combat-bar change put "stones (weight)" on the weight readout.
