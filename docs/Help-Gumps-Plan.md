# Item help and the skills guide: work plan for sign-off

Origin: the owner, 2026-10-11, after the new-player help message list (`New-Player-Help-Messages.md`): "a context menu on all items in a player pack that can bring up a help gump for contextual information about the item. For example, empty bottles would open a gump (standard shape) that describes what empty bottles are for, with a link to another gump (Alchemy). Any alchemy related items would have their own description plus a link to alchemy. We should have a skills gump that looks a lot like the welcome gump: section headers at the top for different categories of skills, then a tab on the left for each skill. The skill pages would have in-depth info about how they work and what a player needs to know." **Nothing is built; this plan awaits the owner's sign-off.**

## 1. Goal and exit criteria

1. A single click on any item the player holds (pack, bank box, worn) offers an **About** entry in the context menu; choosing it opens a help window in the shard's standard window shape (`Gump-Style-Guide.md`) with the item's graphic and name, a plain description of what it is for, and buttons that go to related pages.
2. A **skills guide** window in the Welcome guide's shape: six category tabs along the top, the skills of that category as ovals down the left, the page on the right. Every one of the 49 skills in this era has a page.
3. Item pages link to skill pages (an empty bottle to Alchemy), and a skill page lists its related items back.
4. Everything described is true of this shard (checked against the code, as the guide pages were), and only what is switched on is described.
5. The flag ships off; with it off nothing differs from today.

## 2. Current state (read from the code)

- **The client already asks.** A lone single click on an item in a pack, on a worn item or on an item in the world sets a delayed click; after the double-click window the client sends a single click and, when the server advertised context menus (it does, the Execute entry on a Knocked Out player uses them), requests the popup menu (`DelayedObjectClickManager`, `GameActions.OpenPopupMenu`). Only the profile option `hold_shift_for_context` (off) would require Shift. So no client code change is expected.
- **The server has one central place.** `ContextMenuSystem.CreateContextMenu` (UOContent) asks the item's own `GetContextMenuEntries`; about 60 stock classes override it for special entries. There is no shard hook for items (there is one for players, `PlayerMobile.ContextMenuEntriesHandler`). The narrowest change is one delegate there, asked after the item's own entries. A menu entry's text is a client text number; the shard already adds numbers through `Data/Client/Clilocs.txt` (3050001 is Execute), so "Help" is one more line.
- **The guide window is already generic.** `GuideWindow` takes a title, a list of topics (`WelcomeGuide.Topic`: key, title, paragraphs), optional chapters (the tabs), actions (buttons under the list) and a callback. It draws up to six 88-pixel tabs across the 640-pixel window and squeezes the topic ovals to fit; about ten ovals per tab is the comfortable limit. Pages scroll. So the skills guide needs no new window code, only content and a way to open a given topic.
- **What the guide says today** about skills: Training, Skill locks 101, Money and shops, Crafting, Gathering, Pets, Dying. Nothing on bandages, stamina, poison or most individual skills.

## 3. Design

### 3.1 The Help entry

| Rule | Behaviour | Stock |
| --- | --- | --- |
| Where | Items the player holds: backpack and what is in it, bank box, worn items. (Open question 1.) | none |
| Label | "Help" (client text 3050002) | none |
| Opens | `ItemHelpWindow`, a `GuideWindow` with one page: the item's graphic and name, "What it is", "What it is for", "Where it comes from" and "Good to know" where they apply, and buttons to related pages | none |
| Without hand-written text | A generated facts page from the item itself: name, weight, whether it stacks, whether it is newbied or blessed (kept on death), what it is made from or makes (read from the craft tables), and its group. (Open question 2.) | none |
| Gating | Descriptions of switched-off systems are omitted (the same `Context` the guide uses) | n/a |

### 3.2 The data

- **A data file, not code.** `data/help/items.json` maps an item type (or a base type, so one entry covers the eight reagents, with per-type overrides) to a topic: title, paragraphs, related links (a skill, another item topic). `data/help/skills.json` holds the 49 skill pages. Deployed with the other configuration; validated at start (every link resolves, every skill has a page, no text over the page limit, no Age of Shadows skill or item, no forbidden brand name). The owner can edit wording without a build.
- **Generated sections** on skill pages, from the code tables, so they cannot drift: the training ranges of a craft (each recipe's minimum and maximum skill from `DefAlchemy` and the other craft systems), the tools and resources each needs, the skill's gain class and Mastery band from `shard-rules.json`, the stat that helps it. Hand-written prose explains how it works and what to watch for.
- **The skill categories (six tabs, ten or fewer skills each; as built, `data/help/skills.json`):** Fighting (Wrestling, Swordsmanship, Mace Fighting, Fencing, Archery, Parry, Tactics, Anatomy, Healing); Magic (Magery, Evaluating Intelligence, Meditation, Resisting Spells, Spirit Speak); Crafting (Alchemy, Blacksmithy, Bowcraft and Fletching, Carpentry, Cartography, Cooking, Inscription, Tailoring, Tinkering, Poisoning); Outdoors (Mining, Lumberjacking, Fishing, Camping, Tracking, Herding, Animal Taming, Animal Lore, Veterinary); Lore (Item Identification, Arms Lore, Taste Identification, Forensic Evaluation, Musicianship, Peacemaking, Provocation, Discordance); Thieves (Hiding, Stealth, Stealing, Snooping, Lockpicking, Remove Trap, Detecting Hidden, Begging). That is all 49. (Changed from the first draft, which had "Survival and Lore" and "Animals and Music": the pets moved with the other outdoor skills and the bard skills with the lore skills so that no tab holds more than ten.)

### 3.3 Opening and linking

- `[SkillGuide` opens the guide; `[SkillGuide alchemy` opens that page. The Welcome guide's Training and Crafting pages and the new-player tips (`New-Player-Help-Messages.md`) gain a "Learn more" button into it.
- Item pages and skill pages are one window kind, so a button is just "open that topic"; the window is a singleton, so it replaces itself, and a **Back** button returns to the page you came from.

### 3.4 What a skill page covers

What the skill is for in this era and on this shard; how it is used (the action, the tool, the target); how to train it, with the generated training table and where to practise; what limits it (stamina, reagents, resources, the anti-macro limit on repeating from one spot); how it gains here (its class and the 1.5x or slower curve, Mastery from 80, the Skill Bank and Faint Memories where they matter); the common mistakes; related skills and items.

## 4. Work breakdown (smallest first)

1. **Engine, one narrow hook** in UOContent: a delegate on `ContextMenuSystem` asked after `item.GetContextMenuEntries`. A UOContent test. The usual cycle: ModernUO commit, rebuild `UOContent` into `Distribution`, pin bump in three places, redeploy.
2. **Client text:** the "Help" entry text.
3. **ShardContent:** `HelpCatalog` (loader and validator), `ItemHelpService` (the entry, the generated facts page), `ItemHelpWindow` and `SkillGuide` on `GuideWindow`, `[SkillGuide`, a `helpGumps` flag and `[HelpStatus`, `data/help/*.json`.
4. **Content, in batches the owner reviews:** the Alchemy chain first as the model (the Alchemy page, empty bottle, reagents, potions, mortar and pestle), then each category; item coverage by group, then by item.
5. **Tests:** every skill has a page; links resolve; pages fit; generated tables match the craft code; gating; the data validates; the Help entry only for held items, never for staff-only ones, never with the flag off.
6. **Docs:** this plan, an evidence document, a readiness record, the README line at activation.

## 5. Verification

- **Unit:** the validator and the generated sections (training ranges read from the craft tables and compared with the code), link resolution, item-to-group mapping, gating, the hook (null changes nothing).
- **Live, disposable host, Navrey:** a character with an empty bottle, a reagent, a potion and a tool: the Help entry appears for each and not for another player's item or with the flag off; choosing it opens the right page; the skill pages open with `[SkillGuide`.
- **Real client, shown to the owner:** a lone click on a pack item gives the menu; the item window; the skills guide in each of the six tabs (the longest page of each, to check scroll and fit); a button from an item to its skill and back. These are the first things to check, before any content is written: if the client does not show the menu for pack items as the code says, the plan changes.
- **Accuracy audit:** every factual sentence read against the code; then an independent read-only audit per batch, as for the guide pages (which found errors in every draft).
- **Snapshot:** no save-format change.

## 6. Activation

New flag `featureFlags.helpGumps`, **off when deployed**. Turning it on needs the owner's explicit "activate". The client text ships regardless and does nothing without the menu entry.

## 7. Open questions (recommendation first)

1. **Which items get Help?** Recommended: items the player holds (pack, bank box, worn). Alternatives: also items on the ground and in shops; pack only.
2. **Items without hand-written text.** Recommended: a generated facts page, so the menu is on everything as asked. Alternative: no Help entry until an item has text.
3. **Generated training tables on the skill pages?** Recommended: yes, so the numbers cannot drift from the code. Alternative: prose only.
4. **Build order.** Recommended: engine hook, windows and the Alchemy chain end to end first, shown to the owner in the real client; then the other categories in batches. Alternative: everything, then review.

## 8. Out of scope / deferred

Spell pages (a Magery page would link to a spell list later), monster and region pages, a search box, per-item pages for decorative items, translation, and any change to how skills work.

## 9. Risks

- **A menu on every lone click.** A single click on any held item will pop the menu (only when the item has an entry, which is now every one). That is what was asked, but players who single-click to read an item's name will see a menu each time; the client option "hold Shift for context menus" turns it off but also affects the Execute entry. Judge it in the first real-client session.
- **Volume.** Roughly 49 skill pages of several hundred words each and a few hundred item topics. The generated sections and the base-type mapping keep the hand-written part small, but the writing and the audits are the long part, which is why the order is one chain first.
- **Drift.** Hand-written prose can go stale if a rule changes; the generated sections and the validator catch numbers and links, not wording.
