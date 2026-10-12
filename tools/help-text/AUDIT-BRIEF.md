# Audit brief: help text for UO Rekindled

You are an **independent auditor**. Another agent wrote player-facing help text (Skill Guide pages or item Help topics) for a UO shard (UO Rekindled, UOR/Renaissance era April 2000, ModernUO, Felucca only). A player will believe every word. Your job is to find what is **wrong, unsupported, out of era or misleading**, and fix it in the file. Do not trust the writer's notes; use them only as a map to where to look.

## Read first
1. `C:\Users\brend\Documents\Britannia Renaissance\ShardContent\docs\Help-Content-Spec.md` (the writing brief the author followed: format, limits, era rule, flags, style).
2. The part file you audit and its notes file (paths in your assignment).

## What to check (every sentence of the JSON text)
- **Every number and every factual claim** against the code that actually runs: read the source (ModernUO under `ModernUO\Projects\UOContent`, `ModernUO\Projects\Server`; shard code under `ShardContent\src\BritanniaRenaissance.Content`; config in `ShardContent\data\configuration\shard-rules.json` and `ModernUO\Distribution\Configuration` / `Data`). Find the line yourself. A claim you cannot find in code or config is **unsupported**: remove it or reword it to what you verified.
- **Era gates.** The shard runs `Core.Expansion = UOR`. A code path behind `Core.AOS`, `Core.SE`, `Core.ML`, `Core.SA`, `Core.HS`, `Core.TOL` or a later `Expansion` is not taken. Items, monsters, vendors, spells, skills or features that do not exist in this world must not be advertised. Check where something is bought (`SBInfo` lists and the spawn/vendor data actually used: `ModernUO\Distribution\Data\Spawns`, `ShardContent\data\world-generation`) and do not leave "buy X from Y" if Y does not spawn or does not sell X.
- **Shard rules.** Features behind a flag (`DeferredFeatureFlags`, see `ShardContent\src\BritanniaRenaissance.Content\ShardRulesConfiguration.cs`) must sit in a paragraph with `"requires": "<Flag>"`; flags that are **off** in `shard-rules.json` (CoolZones, HousingGeography, Expeditions, Pilgrimage, RoadSpeed, RetentionContent) must not be mentioned at all; anti-macro is disabled here (`antimacro.json`).
- **Behavior claims about the client** (what a click or key does) must be backed by ClassicUO code or `WelcomeGuide.cs`; else remove.
- **Prices** ("about N gold") must match the vendor list, with the right unit; **where to get it** must be real.
- **Training advice** ("train at 30 to 50 by doing X") must be consistent with the skill-check range the code uses for X (`Skills.CheckSkill(skill, min, max)` / `SkillCheck`) and with the shard's gain rules in `shard-rules.json` (generated blocks print them; do not retype them in text).
- Statements that are **true but misleading** (a number without its condition, "always" where the code is probabilistic).
- **Spec compliance**: ASCII only, no banned words (Britannia Renaissance, Age of Shadows, Trammel and later expansions), titles at most 18 chars, at most 4 links (skills + related) for an item topic, each type name in one topic only, skill pages carry `{"generate":"stats"}` and `{"generate":"gain"}` (and their craft table), headings start with "# ". The generated blocks fill in the stats and the gain/Mastery rules, so text must not contradict or repeat them.
- **Clarity for a new player**: jargon explained, no wall of text; but do **not** rewrite the style. Change as little wording as accuracy requires. Keep the author's structure.

## What to do about a problem
- **Wrong**: correct it to what the code says (and keep the writing style).
- **Unsupported / cannot verify / out of era**: delete the sentence (or the whole claim) rather than guess. If a heading ends up with nothing under it, delete the heading. Keep each page at 3+ headings and 900+ characters of own text where you can (skill pages); if a page can no longer reach that, say so in your report.
- **A real design question for the owner** (the code does something odd, the shard docs conflict with the code): do not decide; leave the text neutral/omitted and list it under `OWNER:` in your audit report.
- Edit the part JSON **in place** (valid JSON, ASCII only; check it parses with `python -c "import json;json.load(open(r'<path>'))"`). Do not touch any other file except your audit report. Do not build or run tests or start servers/clients.

## Report
Write `<area>.audit.md` next to the part file: counts (sentences/claims checked, wrong and fixed, removed as unsupported/out of era, left alone), a table of each change (page/topic | before | after | source line), the `OWNER:` list, and anything you could not check. Your final reply to the coordinator: files changed, counts, the OWNER: list (one line each), and anything the coordinator must decide. Keep it short.
