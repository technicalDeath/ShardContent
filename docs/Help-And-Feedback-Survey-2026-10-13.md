# What is off that could help players: survey and what was done (2026-10-13)

The owner asked (after the damage-number question): "investigate what other non-mechanics-changing UI and feedback enhancements are turned off that could be enabled in modernuo/classicuo to help players". Two read-only audits (ClassicUO's profile options and Options window; ModernUO's settings, packets and messages) produced about 45 candidates. The owner then said "do all of the ones you recommend", asked for an obvious way to show all names, and to activate anything not yet active. This record keeps the reasoning so it is not redone.

## Done (all in the 2026-10-13 batch)

| Item | What | Where |
| --- | --- | --- |
| Damage and heal numbers | Floating red/yellow damage and green heal numbers, one Options switch | `Combat-Numbers-Evidence.md` |
| Confirm before helping a grey, criminal or red player | `enabled_beneficial_criminal_action_query` true. Stock ModernUO flags the helper (`Mobile.cs` beneficial-act check) | `Client-Defaults.md` item 13 |
| Party invitation window | `party_invite_gump` true (the server sends the standard invite packet; camp travel needs a party) | same |
| Buff icon countdowns | `buff_bar_time` true | same |
| One-click spell, skill and macro buttons | `cast_spells_by_one_click` true, so a spell dragged off the spell bar acts like the bar | same |
| Item shortcut turns red when low | `counter_bar_highlight_on_amount` true (at 5 or fewer) | same |
| Tab toggles war mode | `hold_down_key_tab` false; the guide's Keys paragraph says so | same |
| Info bar | Hits, Mana, Stamina as numbers, opened once beside the potion bar (`GameScene.OfferInfoBar`); `InfoBarManager.CreateDefault` lists only those three because the combat bar already shows the weight | client |
| Names on demand | A **Names** button on the top bar (white, green while names are on) next to Map, Alt+N for a new profile, and the stock Ctrl+Shift; `name_overhead_type_allowed` 510 (mobiles and corpses, not items on the ground); the guide's top-bar paragraph says all three. Also the macro `NamesOnOff` is bindable in Options | `TopBarGump.cs`, `MacroManager.cs` |
| Containers in the dark column | The backpack, a bag on the ground and a corpse open under the paperdoll and other docked windows while there is room (`ShardLayout.Dock`); a container the player already placed, and a bag inside a bag, keep their place | `PacketHandlers.cs` |
| Vendor buy-list tooltips | The client now shows what the server describes in a vendor's buy list (damage, speed, strength, skill, durability). The server already sent the property lists with the buy list; the client threw them away because the tooltip bit is off in this era | `ShopGump.cs`, `GameCursor.cs` |
| **Leak closed with it** | `BaseVendor.SendBuyList` used to send the property list of every item a **player sold** to an NPC vendor (an unidentified magic item's properties) when the vendor re-listed it. It now sends property lists for the vendor's own display stock only | ModernUO `BaseVendor.cs` |
| Buff icons for Hot Zone and secure camp | A flame (Hot Zone: names the zone, says what applies) and a tent (secure camp: countdown to the fire going out, the Bedroll hint) | `buff-icons.json`, `BuffIconService.cs`, `make_buff_icons.py` |
| Paperdoll virtue emblem | Hidden on the shard's bar: its double-click opens the virtue gump, which is off here, so it did nothing | `PaperDollGump.cs` |
| Guide text | Names, the info bar, Alt+N, Tab, `[HelpInfo`, the shop hover, the Ignore List and the Page staff button | `WelcomeGuide.GettingStarted.cs` |
| Activated | `helpGumps` (item About and the Skill Guide), `scrollSuccessChance`, `damageNumbers`, `healNumbers` | `shard-rules.json` |

## Deliberately not done (each is an advantage, automation, or needs an owner ruling)

- **Raw hover tooltips (`opl.enable`).** *Done safely on 2026-10-13 on the owner's word: item tooltips replace the stock lists with the shard's own (`Item-Tooltips-Evidence.md`).* Never flip it raw: the property lists for weapons, armor, wands and spellbooks print exact damage, resists, charges, poison and slayer without Item Identification or Arms Lore (`BaseWeapon.cs`, `BaseArmor.cs`, `BaseWand.cs`, `Spellbook.cs`; 136 files override `GetProperties` and only these were audited). A safe version is a **name-only filter**, which needs an engine filter hook in `Item.GetProperties` / `InitializePropertyList` and a client change to split the paperdoll's ability book from the tooltip bit (`ClientFeatures.cs:57-59`). Setting the AOS list bit without `opl.enable` also removes every name label, because the client stops single-clicking when tooltips are on and the server answers hover only through OPL.
- **Weight line in tooltips** (`Item.DisplayWeight => Core.ML`): only after name-only tooltips exist.
- **Stock chat window** (`chat.enabled` false): an owner decision with a moderation cost (`Quality-of-Life-Research.md` section 6).
- **Always-on names** (`name_overhead_toggled`): kept off; the Names button is the easy trigger.
- **Advantages or automation:** zoom, light override, hide-roofs/trees/vegetation, show house content, auras under feet, overhead spell format, click-to-pathfind, drag-select health bars, grid loot and Sallos easy grab, target range indicator, screen scale, sound while unfocused, the "Close Gumps" macro (it would also close the shard's bars), auto-reconnect and auto-login.
- **Not worth doing:** autosave warning delay (leave; the two stock lines already announce a save), the login "N users online" line (nothing calls it and its stock text prints item and mobile counts), the alternate resizable journal (it makes a new window on every call and skips docking), smooth boat movement (untested against ModernUO boats).
- **Left for an owner decision:** a Discord webhook for pages (it is a secret: never commit it), Default hotkeys for Target Self and Last Target.

## Warnings worth keeping

- Do not raise `MobileStatusVersion` or the expansion: version 4 and up would send resists, damage range, luck and tithing.
- Keep `visibleDamage` at "Related". "Everyone" and "Selective" would show other people's damage, and exact damage lets players infer armor and resists.
- Guild and party positions on the client world map (`WorldMapEntityManager`, query 0xF0) are not implemented by ModernUO; a future implementation would be an ally-tracking advantage.
- `Help-Gumps-Findings.md` records that the Help pages assume there are no tooltips. If name-only tooltips ever ship, re-audit them.
