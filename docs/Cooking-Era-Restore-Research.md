# Cooking: era research and plan (2026-10-05)

Status: **Part A signed off 2026-10-05, built and verified live; not committed or deployed.** Result and evidence: [Cooking-Era-Restore-Readiness.md](Cooking-Era-Restore-Readiness.md). Origin: the owner asked for new Cooking characters to start with "a tool to cook food". Research showed UO:R cooking has no tool, and this build cannot cook at all.

## What this build does today (source trace; dev server was running, nothing run live)

- `ModernUO/Projects/UOContent/Items/Food/CookableFood.cs` holds the heat-source list and each food's `Cook()`, but nothing starts the "use raw food on a heat source" action. Upstream ModernUO never wired it to a double-click; the dead target and timer code was deleted in 2022 (`864440a05`).
- The only cooking route in the build is the Skillet / Rolling Pin / Flour Sifter craft menu. This shard runs T2A craft menus (`expansion.json`: `UOTD` false, so `t2aCraftMenus` defaults on) and `T2ACraftSystem.ShowMenu` has no Cooking branch, so those tools open nothing.
- `Dough` and `SweetDough` are plain items (not `CookableFood`, not stackable before ML). Nothing combines flour, water, dough or fillings outside the craft menu.
- Net: no character can cook anything today, with or without a tool. This is the open "Cooking menu reachability" live check from Alpha 3, now resolved by source.

## Era findings

**The tools do not belong in UO:R.** The Renaissance expansion shipped 3 April 2000 (Publish 5, with Trammel/Felucca). The Skillet, Flour Sifter and Rolling Pin, with the cooking menu, arrived in the Crafting System Overhaul in **Publish 14, November 2001** ([UO.com Publish 14](https://uo.com/wiki/ultima-online-wiki/technical/previous-publishes/2001-2/2001-publish-14-14th-november/)). I read the UO.com notes for Publishes 3 to 13 (24 Jan 2000 to Aug 2001): none changes cooking. Publish 4 says crafting skills including cooking are exempt from the new anti-macro rules; Publish 13 mentions fixing pie baking in the Haven tutorial ovens. [UOGuide's Cooking history](https://www.uoguide.com/Cooking) agrees: before the menu, "a player simply used raw food items on heat sources to cook them or on each other to combine ingredients."

**Mechanics** (from the [UO Second Age wiki guide](https://wiki.uosecondage.com/Cooking) and [forum thread](https://forums.uosecondage.com/viewtopic.php?t=5751): a T2A-accurate community, written 2009-2010, not first-party documentation; the Publish notes support carrying them into UO:R):

| Rule | Era behavior |
| --- | --- |
| Cook raw food | Double-click the food, target a heat source. A cooking sound plays, then a result message. |
| Success chance | Your Cooking skill is the percent chance (50 skill is about 50%). Every food can be attempted at 0 skill and trains from 0 to GM. NPC cooks train to about 30. |
| Failure | Food is lost: "You burned the food to a crisp! It's ruined!" |
| Success | The cooked food goes to the pack. |
| Stacks | Targeting a stack cooks the whole stack on success; on failure about half the stack is lost and the rest is returned. Skill gain is the same as for one item. |
| Heat sources | Campfire, Field of Fire spell, fire pit, fireplace, **forge**, heating stand, oven. Barbecued and baked foods both cook on any of them. |
| Campfires | Kindling (from a bladed item on a tree) lit by double-click; "may require some use of the Camping skill". Many fireplaces and ovens stand in towns (Minoc's fireplace is named). |
| Preparation | Wheat sheaves at a mill make flour; water + flour make dough; dough + honey/egg/meat/fruit/cheese/sausage make unbaked foods. Double-click the base item (dough), then target the filler. |

**Not found:** the length of the cook delay (the stock 5 seconds is unverified), the exact fraction lost on a stack failure, and the starting items of a UO:R cook. Sources that failed: Stratics (bot-check page, not bypassed), uorenaissance.com (connection refused), the Codex (describes the modern menu). The uorenn.com wiki describes a modern 55-skill shard and was discarded.

## Plan

**Goal:** a Cooking character can cook raw food on a heat source, as in UO:R. No tool.

**Part A (this item):**
1. ModernUO hook, `CookableFood.cs`: double-click starts a target; a valid heat source consumes the food and starts a cook timer; the result is cooked food (success) or "You burn the food to a crisp! It's ruined." (failure). One cook at a time ("You must wait to perform another action"). Moving more than 3 tiles away, or changing map, burns the food.
2. Heat sources: stock `IsHeatSource` plus large and small forges (era sources and stock's own cooking-menu list both include forges). Pure `IsHeatSource(int itemId)` overload for unit tests.
3. ShardContent: no code change. Starter pack unchanged (stock Kindling x2, raw lamb/chicken/fish topped up to 20, flour sack, pitcher).
4. Docs: this file becomes the evidence doc, plus a readiness record; resolve the Alpha 3 "Cooking menu reachability" lines; a README line on deploy.

**Part B (separate item, own plan):** the preparation chain (flour + water, dough + filler) and baking Dough/SweetDough, which are not `CookableFood` today. Needs more stock item classes touched, so it is not bundled.

**Verification** (disposable host; no save-format change, so no restart test):

| Case | How |
| --- | --- |
| Heat-source IDs, forges included | unit test (UOContent.Tests) |
| Raw fish on a campfire gives a fish steak | live |
| Non-heat target consumes nothing | live |
| Walking away burns the food | live |
| Second double-click during the cook says "wait" | live |
| Forge, oven or fireplace as target | live |
| Lamb, chicken and fish from a fresh starter cook | live |
| Cooking skill rises over repeated cooks | live |

**Risks:** the cook delay is unverified; time to train Cooking will be longer than the Beta 1 gain-curve audit's menu-based figures (1.25 s per attempt); pies and pizzas are also `CookableFood` and would cook on any heat source (not obtainable until Part B). Deploy needs the dev server stopped and a `UOContent.csproj` rebuild into Distribution; that rebuild also carries the unpushed upstream merge `9006a252c` (re-checked: the source trace above still holds at that HEAD) and its `BaseCreature` v24 save bump, so snapshot `Distribution/Saves` first. A ModernUO commit means bumping the pinned ModernUO commit in three places. Nothing is committed or pushed without being asked.

## Decisions requested

1. **Scope:** Part A now, Part B later (recommended), or both together.
2. **Success chance:** era (chance = skill %, usable at 0 skill) or stock RunUO (each food has a minimum skill of 10 to 40). Recommended: era.
3. **Stacks:** one item per cook (stock; recommended) or era whole-stack cooking (success cooks all, failure loses about half, loss fraction unverified).
4. **Activation:** ungated (deploy turns it on; recommended) or behind a new feature flag.

Recommendations used if unanswered: forges included; starter pack unchanged; stock 5-second cook.

## Sign-off (owner, 2026-10-05)

Part A approved with all four recommendations: Part A now and Part B later; era chance (skill %, usable at 0 skill, the per-food `CookingLevel` minimum is not used); one item per cook; ungated. Defaults named in the plan stand: forges are heat sources, starter pack unchanged, stock 5-second cook. Autonomous run follows; dev server stays untouched (live checks on a disposable host).
