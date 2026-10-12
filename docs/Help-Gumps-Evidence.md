# Item Help and Skill Guide: evidence

Plan: `Help-Gumps-Plan.md` (signed off by the owner 2026-10-11). Writing brief: `Help-Content-Spec.md`. Flag: `featureFlags.helpGumps` (**off** until the owner says activate).

## What was built

| Piece | Where |
| --- | --- |
| Engine hook: a central item context-menu hook (`ContextMenuSystem.ItemEntriesHandler`) | `ModernUO/Projects/UOContent/Context Menus/ContextMenuSystem.cs`; tests `ModernUO/Projects/UOContent.Tests/Tests/ContextMenus/ContextMenuShardHookTests.cs` (4) |
| Help text catalog: load, validate, find the topic of an item type (own type first, then base types, then the general item page) | `src/BritanniaRenaissance.Content/HelpCatalog.cs` |
| Generated blocks read from the game: craft recipe tables, stats a skill uses and raises, training class and Mastery days from `shard-rules.json` | `HelpGenerators.cs` |
| Windows, the menu entry, `[SkillGuide [skill]`, `[HelpStatus` | `HelpService.cs`, `GuideWindow.cs` (server-side tabs, item art header) |
| Menu text "Help" (client text 3050002) | `data/client/Clilocs.txt`, copied to `ClassicUO/bin/dist/Data/Client/Clilocs.txt` |
| The text | `data/help/skills.json`, `data/help/items.json` (deployed to `Configuration/help` by `Deploy-Alpha1Baseline.ps1`) |

## Owner decisions

- Scope: items the player holds, and items on the ground that can be picked up. "You write the text" for items nobody supplied text for; generated tables yes; build order and sign-off: yes, go (2026-10-11). Flag stays off until "activate".

## Real-client check (ClassicUO, disposable host `help-slice`, 2026-10-11)

Alchemy slice (flag on in the host copy only): single-click an empty bottle in the pack opens the context menu with **Help** (since renamed **About**); Help opens the item window (picture, text, links to the Alchemy skill page, Reagents, Mortar and pestle); the Alchemy link opens the Skill Guide on the Crafting tab with the Alchemy page, its recipe table read from the game, and Back returns to the item. First pictures sent to the owner the same day. Findings fixed from them: clipped footer text, lower-case subtitle, craft names in lower case and "1 empty bottles", a recipe range shown as 0 where the game's number is -25 (a head start), a gain line reading "1 times the usual rate".

## Content (2026-10-11)

49 skill pages and 134 item topics written by eleven writer agents from `Help-Content-Spec.md`, then audited sentence by sentence against the code by independent agents (`docs/help-content/<area>.audit.md`; the claim lines are in `<area>.notes.md`). Corrected by the audits so far: Lore 9 wrong claims, armor and clothing 6 wrong and 16 qualified for artifact variants, Fighting 12 groups, Thieves 21, Crafting 17, Outdoors 20. The merged text validates (`HelpCatalogTests`, 36 passing). The audits of Magic, weapons, tools, resources, miscellaneous items and the Alchemy chain were still running at the pause. **Status and what is left: `Help-Gumps-Status.md`. Owner-level findings: `Help-Gumps-Findings.md`.**

(Real-client pictures of the final content and the full matrix: to be filled in when the work closes.)
