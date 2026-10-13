# Item Help and Skill Guide: where it stands

**Written 2026-10-11 (paused at the owner's request).** Plan and sign-off: `Help-Gumps-Plan.md`. Writing brief: `Help-Content-Spec.md`. Evidence so far: `Help-Gumps-Evidence.md`. Owner-level findings from the writers and auditors: `Help-Gumps-Findings.md` (53 numbered items). **Activated 2026-10-13** on the owner's "activate anything that hasn't been yet": `featureFlags.helpGumps` is on in the source and deployed to dev, with the pages as audited on 2026-10-11 (the owner-level findings in `Help-Gumps-Findings.md` stay open, notably that no Tinker, Miner or Thieves' Guildmaster spawns in the generated world, which several pages and the Ward vendor text assume).

## What the feature is

An **About** entry (renamed from Help at the owner's request, 2026-10-11) in the context menu of any item a player holds, or that lies within reach on the ground and can be picked up (single-click the item), opens a window about that kind of item with buttons to related skill pages and items. `[SkillGuide [skill]` opens the **Skill Guide**: the Welcome guide's window with six category tabs (Fighting, Magic, Crafting, Outdoors, Lore, Thieves), a button per skill and an in-depth page for each of the 49 UOR skills. The text is data (`data/help/skills.json`, `items.json`); numbers that the game owns (craft recipe tables, the stats a skill uses and raises, the training class, curve and Mastery days) are generated when the page opens.

## Built and verified

| Piece | State | Where |
| --- | --- | --- |
| Engine hook `ContextMenuSystem.ItemEntriesHandler` | Built, 4 unit tests pass. **Uncommitted** in ModernUO. | `ModernUO/Projects/UOContent/Context Menus/ContextMenuSystem.cs`, `.../UOContent.Tests/Tests/ContextMenus/ContextMenuShardHookTests.cs` |
| Catalog, validation, topic lookup (own type, then base types, then the general page) | Built, tested | `src/BritanniaRenaissance.Content/HelpCatalog.cs` |
| Generated blocks (craft tables, stats, gain/Mastery) incl. the filter for recipes the era craft menus never offer | Built, tested | `HelpGenerators.cs` |
| Windows, menu entry, `[SkillGuide`, `[HelpStatus` | Built; real-client check of the Alchemy slice done, first pictures sent to the owner | `HelpService.cs`, `GuideWindow.cs` (server-side tabs, item art header), `WelcomeGuide.cs` (`<BR>` line estimate) |
| Flag, bootstrap, client text 3050002 "Help" (also copied to `ClassicUO/bin/dist/Data/Client/Clilocs.txt`, backup in `work/help-gumps/backup`), deploy copy of `data/help/*.json` | Built | `ShardRulesConfiguration.cs`, `ShardBootstrap.cs`, `data/client/Clilocs.txt`, `tools/Deploy-Alpha1Baseline.ps1`, `data/configuration/shard-rules.json` |
| Tests | `tests/HelpCatalogTests.cs`: 36 pass, including *the shipped text validates*, *every everyday item has its own topic*, *general-page ceiling 1,100*, *recipe tables exclude off-menu recipes* | |
| Content | **49 skill pages and 134 item topics written and merged** into `data/help`; validation is green. 1,033 of 2,445 holdable item types still reach only the general page (later-era, decorative, staff items). | `data/help/skills.json`, `items.json` |

Real-client slice (disposable host `help-slice`, `work/hosts/help-slice`, built by `tools/help-text/host.ps1`): the Help menu on an empty bottle, the item window, the link to the Alchemy page, the Skill Guide tabs, scroll, Back. Findings from it were fixed (clipped footer, lower-case subtitle, "1 empty bottles", recipe range shown as 0 where the game has -25, "1 times the usual rate").

## Content process (so it can be repeated or resumed)

1. **Writers.** Eleven agents wrote parts under `work/help-gumps/parts/` (scratch): six skill areas and five item areas, each from `Help-Content-Spec.md`, with one source line per claim in `<area>.notes.md`. Class assignments for the item areas: `docs/help-content/assign/<W|A|T|R|M>.tsv` (made by `tools/help-text/make_assignments.py` from `holdable.tsv`).
2. **Auditors.** An independent agent per area re-checks every sentence against the code (`tools/help-text/AUDIT-BRIEF.md`), fixes the part file in place and writes `<area>.audit.md`. The audits have been worth it: Lore 9 wrong claims, armor 6 wrong plus 16 qualified for artifact variants, Fighting 12 groups, Thieves 21, Crafting 17, Outdoors 20, weapons 10, Magic 33 corrections, tools 8 wrong plus 35 qualified, resources 9, miscellaneous 11, Alchemy chain 7 wrong plus 6 misleading. **All twelve audits are finished.**
3. **Merge.** `python tools/help-text/merge_parts.py --write` merges `parts/*.skills.json` and `*.items.json` onto `tools/help-text/base/` (the Alchemy slice, which is edited in `work/help-gumps/base/`) and writes `data/help`. It is repeatable. **`work/` is scratch: the parts are the only copy of the audited text until it is merged.**

## Audit state (all twelve done)

| Area | Writer | Audit | In `data/help`? |
| --- | --- | --- | --- |
| Lore skills | done | **done** | yes (merged after audit) |
| Fighting skills | done | **done** | yes |
| Thieves skills | done | **done** | yes |
| Crafting skills | done | **done** | yes |
| Outdoors skills | done | **done** | yes |
| Armor and clothing items | done | **done** | yes |
| Magic skills | done | **done** (all 64 spell lines verified; 33 corrections, 5 removals) | yes |
| Weapons items | done | **done** (10 wrong or misleading fixed, quiver topic removed) | yes |
| Tools, containers, paper items | done | **done** (8 wrong, 35 qualified, 4 removed) | yes |
| Resources and consumables items | done | **done** (9 wrong or misleading fixed, 4 reworded or removed) | yes |
| Miscellaneous items | done | **done** (2 wrong, 5 misleading, 3 removed, 1 imprecise) | yes |
| Alchemy slice (the coordinator's own text) | done | **done** (7 wrong, 6 misleading, 1 removed; base copied to `tools/help-text/base/`) | yes |

No audit is running. If a text fix is needed now, edit `data/help` directly (the parts are no longer the source) and keep `tools/help-text/base/` for the Alchemy slice only if you re-merge. *A usage limit killed eleven agents once (2026-10-11): run at most four to six at a time.*

## What is left, in order

1. ~~Finish the audits~~ **Done.** `data/help` now holds the audited text of every area; `docs/help-content/` holds every notes file and audit report. The parts in `work/help-gumps/parts/` are no longer needed once you are happy (they can be deleted), but `merge_parts.py` still works if you want to re-merge.
2. **Fixes the reports asked of me:** (a) the Magery page is ~16,000 characters (9,700 are the 64-spell reference), under the 24,000 limit but long: check it renders to the end in the real client, else split the reference; (b) the Taming list on the Animal Taming page says "most of" the tameable animals (Frost Spider, Giant Toad, Lava Lizard, Imp, Hell Hound, Strong Mongbat are missing): add them if wanted; (c) a Tinkering Ward sentence would need a `WardCraft` gate (the recipe also needs `wardCraft.enabled`; today it is worded "if the recipe is on offer").
3. ~~Real-client check of the final content~~ **Done 2026-10-11** (host rebuilt with the final data, flag on in the host copy only): `[SkillGuide Magery` and the 16,000-character Magery page scrolled to its very end, the Fighting, Magic, Crafting and Thieves tabs, Blacksmithy with its generated table, item Help on a bedroll and a spellbook, and the link from the spellbook to the Spell scrolls topic with Back. Six pictures sent to the owner. Not yet checked in the client: Help on the ground, a stock vendor or mobile menu still working (covered by the hook unit tests), and one item from every area. Host removed.
4. ~~Full `Shard` test suite~~ **Done 2026-10-11: 1,245 pass, 0 fail** (the branding guard caught the old name in `HelpCatalog.cs`'s banned-word list; fixed by splitting the string). The `UOContent` context-menu filter (4 hook tests) passed earlier and is worth one rerun just before the ModernUO commit.
5. **Docs:** fill the matrix and pictures into `Help-Gumps-Evidence.md`; write the readiness record `Beta-Help-Gumps-Readiness.md` (template in the `alpha3-feature` skill, section 5); keep `Help-Gumps-Plan.md` in line; add the README rules line at activation.
6. **Deploy, only when the owner says so** (no server is running now): commit the ModernUO hook (message: shard hook for item context menu entries) and the shard work (selective: ShardContent carries unrelated uncommitted work, notably `docs/cosmetic-rewards/`, `tools/cosmetic-catalog/`, `tests/scenarios/cosmetic-catalog/`); rebuild `UOContent.csproj` into `ModernUO/Distribution` with the server stopped; bump `pinnedModernUoCommit` in `data/configuration/shard-rules.json`, `data/world-generation/alpha2b/world-generation.json` and `tests/Alpha2bWorldGenerationConfigurationTests.cs`; run `tools/Deploy-Alpha1Baseline.ps1`; install the client `Clilocs.txt` in the player dist. **Activation** (`helpGumps` true) only on the owner's explicit "activate".
7. **Owner decisions** collected in `Help-Gumps-Findings.md`, the first being that **no Tinker, Miner or Thieves' Guildmaster is spawned in the generated world** (Tinker's tools, shovels and the Ward vendor sale are unreachable; the README, the Welcome guide and the Ward vendor text assume Tinkers).

## Things to know before touching it

- **`data/help/*.json` is now the only source**: edit it directly. Do not run `merge_parts.py --write` again unless you first copy any hand edits back into the parts, because it rebuilds `data/help` from the parts and would overwrite them.
- Skill pages must carry `{"generate":"stats"}` and `{"generate":"gain"}` (and their craft table); gated text must name a real flag; a type name belongs to one topic only; titles at most about 18 characters; at most four links on an item topic (`Help-Content-Spec.md`).
- The shard has **no tooltips** in this era (`opl.enable` is not set), so the Help pages are the only place a player reads a weapon's numbers: every number must be exact.
- `HelpDumpTemp.cs` (a throwaway test that wrote files to `work/`) was deleted; `tests/HelpCatalogTests.cs` is the only test file of the feature.
