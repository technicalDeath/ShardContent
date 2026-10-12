# Help text: writing brief

For whoever writes the text of the item Help windows and the Skill Guide (`docs/Help-Gumps-Plan.md` is the design; this is the working brief).
The text is data, `data/help/skills.json` and `data/help/items.json`, and it is what a **new player** reads in a window in the game. Accuracy is the whole point:
a wrong number or a feature the shard does not have is worse than no text.

## The shard (read this first)

- **UO Rekindled**, a Renaissance-era (UOR, April 2000) Ultima Online shard on ModernUO, **Felucca only**, "Felucca, without the griefing". Never write "Britannia Renaissance" (tests fail on it), and never name Trammel, Age of Shadows, Mondain's Legacy, Samurai Empire or any later expansion.
- **Era = UOR.** `Core.Expansion` is `UOR`. Anything ModernUO gates on `Core.AOS`, `Core.SE`, `Core.ML`, `Core.SA`, `Core.HS`, `Core.TOL` or an `Expansion` later than UOR **does not exist here**: do not describe it, and read the code path that is actually taken. Resources beyond the ones UOR had (Valorite ore was UOR-era; check each), runic tools, enhanced bandages and so on may be coded but not reachable; verify.
- A thing is **in this world** only if the world has it: a vendor type that is coded but not spawned, a monster that is not in the spawn data, or an item no vendor/loot/craft produces must not be advertised ("buy it from X"). Spawn and vendor data: `ModernUO/Distribution/Data/Spawns`, `ModernUO/Distribution/Data/Decoration`, `ShardContent/data/world-generation/alpha2b`, the `SBInfo` lists (`ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo`), and loot in `ModernUO/Projects/UOContent/Mobiles/Monsters` and `Misc/LootPack*`. When unsure, leave the claim out and say so in your notes.
- **Shard rules** are in `ShardContent/data/configuration/shard-rules.json` (flags under `featureFlags`, skill gain classes under `skillGain`, caps) and explained in `ShardContent/docs/`. Useful: `Alpha-3-Player-Skill-Audit.md`, `Alpha-3-UOR-Pre-AoS-Skills-Readiness.md`, `UOR-ERA-AUDIT.md`, `Guide-Getting-Started-Pages.md`, `Skill-Bank-Faint-Memories.md`, `Mastery-Layered-Evidence.md`, `Beta-1-Skill-Gain-Curve-Audit.md`, and the Welcome guide's own text in `src/BritanniaRenaissance.Content/WelcomeGuide.cs` (the shard rules a new player already reads there: stay consistent with it).
- **Stock first.** Where the shard has no special rule, the behavior is ModernUO's stock behavior with the UOR gates applied. Describe what the **code does**, not what the wiki or your memory of the game says; use online sources only to confirm a UOR-era date or rule, and then still check the code.
- **Shard-specific features** that exist behind a flag (see `GateNames`: for example `SkillBank`, `FaintMemories`, `HarvestAutoRepeat`, `ActionAutoRepeat`, `CampingStarterKit`, `CampingFires`, `CampingTravel`, `PoisonRelief`, `NoviceCombat`) may be described only in a paragraph carrying `"requires": "<FlagName>"` (exact property name, as in `DeferredFeatureFlags`), so the text vanishes if the flag is off. **Flags that are off in `shard-rules.json` (`CoolZones`, `HousingGeography`, `Expeditions`, `Pilgrimage`, `RoadSpeed`, `RetentionContent`, ...) must not be mentioned at all.** Anti-macro is **disabled** here; do not mention it as active.

## Where the text appears

- Click an item you carry, or that lies within reach on the ground and can be picked up, and choose **About** in its menu: that opens the item's window (`items.json`). It has the item's picture and name at the top, the text on the right, and up to **four** buttons on the left that open skill pages or other item topics. A topic can serve one exact item (`types`) or a whole group (`inherits` a base type).
- `[SkillGuide` opens the **Skill Guide** (`skills.json`): six category tabs, a button for each skill, and one page per skill (49 pages, the UOR skills). The categories are fixed already (see `categories` in `skills.json`).
- The text scrolls, so a page may be long, but every paragraph should earn its place. The reader is a new player at the keyboard in the middle of the game.

## File formats

`data/help/skills.json` (`"skills"` array; the 6 `"categories"` already exist, do not change them):

```json
{
  "skill": "Alchemy",                       // SkillName enum name, exactly as in "categories"
  "items": [],                              // optional: item-topic keys to list first; the page lists every topic that names the skill anyway
  "paragraphs": [
    "# What it is",                         // a paragraph that starts with "# " is a heading (the rest is the heading text)
    "Plain text. Use <BR> inside a paragraph for a line break, for a short list.",
    { "generate": "craft:Alchemy" },        // a block read from the game (see below)
    { "text": "A paragraph shown only when a flag is on.", "requires": "SkillBank" }
  ]
}
```

`data/help/items.json` (`"items"` array):

```json
{
  "key": "potion-heal",                     // unique, kebab-case; use your area prefix (see your assignment)
  "title": "Heal potions",                  // the name in the list and when linked; at most 18 characters, sentence case
  "art": 3852,                              // the item graphic id (decimal) shown when the topic is opened from a link: read it from the item's constructor, base(0x0F0C) -> 3852
  "types": ["LesserHealPotion"],            // exact item class names (as in your assignment file)
  "inherits": ["BaseWeapon"],               // base class names: every item derived from them that has no better topic uses this one
  "skills": ["Alchemy", "Healing"],         // SkillName enum names, shown as buttons "Alchemy skill" ... and used to list the topic on those skill pages
  "related": ["potion-cure"],               // keys of other topics, shown as buttons (skills + related together: at most 4)
  "paragraphs": [ "# What it is", "...", "# What it does", "...", "# Good to know", "..." ]
}
```

Rules the validator enforces (a failure stops the shard from loading the help, so they matter): every `types`/`inherits` name must be **exactly one** item class (see the assignment files, they are the holdable classes plus their bases); **a class name may appear in only one topic** across all files; keys unique; `skills` must be UOR skills; at most 4 links; title at most about 18 characters; no empty paragraph; no banned words (Britannia Renaissance, Age of Shadows, Trammel); `requires` must be a real flag name; every skill page needs the two generated blocks below, at least 3 headings and 900 characters of its own text (a page that short is a stub).

**Generated blocks** (put them where they read best; they are filled in from the game when the page opens, so their numbers cannot drift):

- `{ "generate": "stats" }`: the stats the skill leans on and raises. **Required on every skill page.**
- `{ "generate": "gain" }`: the skill's training class and speed on this shard (curve and Mastery). **Required on every skill page.**
- `{ "generate": "craft:<Name>" }`: the full recipe table (name, skill range, materials) of a craft. **Required on its skill page:** `craft:Alchemy`, `craft:Blacksmithing`, `craft:Bowcraft`, `craft:Carpentry`, `craft:Cartography`, `craft:Inscription`, `craft:Tailoring`, `craft:Tinkering`. Do not retype recipe numbers; explain how to read the table and what to make when.

## Style

- Second person, plain words, short sentences. Explain every game word the first time ("reagent", "Hot Zone", "Mastery"). Lead with what the reader needs to do or know; put the long rules lower.
- ASCII only: straight quotes, a plain hyphen, no em dashes, no curly quotes, no `<` or `>` except `<BR>`, no emoji.
- Item topics: roughly 400 to 900 characters; headings such as "What it is", "What it is for" / "What it does" / "How to use it", "Where to get it", "Good to know". Skill pages: roughly 2,500 to 5,000 characters of own text: "What it is", "How to use it", "Training it" (how a beginner actually goes from 0 to 100: what to do at which skill level, and what stops working), the generated blocks, "What you need" (tools, where to buy and for how much, how to make them), "Good to know" (traps, shard rules, surprises). Match the tone and shape of the Alchemy page and the 14 Alchemy-chain item topics already in the files (read them first).
- Say **numbers** where the code has them (damage, weight, charges, delays, ranges, prices "about N gold"), and only those. Round honestly. Never say "usually" when the code says exactly.
- Do not write marketing, lore or jokes. Do not mention commands or windows that do not exist; `[SkillGuide`, `[SkillClasses`, `[Mastery`, `[SkillBank`, `[Welcome`, `[HotZoneStatus` do.
- A claim about the **client** (what a click does) must be one you can verify in `ClassicUO/` or already stated in `WelcomeGuide.cs`; otherwise leave it out.

## Accuracy protocol (not optional)

1. For every fact you write, find it in the code (or in a shard doc/config) and read it there. Do not trust the existing text of any other page, a wiki or memory.
2. In your notes file write **one line per claim**: `topic-or-skill | claim | source file:line`. An independent auditor will re-check each line against the code, so a claim without a source is treated as wrong.
3. Check the era gate on every code path you rely on (`Core.AOS`, `Core.Expansion`, flags). If the path is gated off, the claim is false here.
4. If something is uncertain, contradictory, or looks like a bug or a design question for the owner, **do not guess**: leave it out of the text and put it under `OPEN:` in your notes with what you found.
5. Never say a feature works a certain way in the shard because the design docs say so: read the code that runs.

## Your output

Write only into `work/help-gumps/parts/` (create it if missing). Do not edit anything else, do not build or run tests (one run at a time is allowed on this machine and the coordinator holds it), do not start servers or clients.

- Skill writers: `parts/<area>.skills.json` containing `{ "skills": [ ... ] }` with one entry per skill of your assignment.
- Item writers: `parts/<area>.items.json` containing `{ "items": [ ... ] }`.
- Both: `parts/<area>.notes.md` with the claim lines, `OPEN:` items, and (item writers) the list of assigned class names you deliberately left to the general page and why (post-UOR, not in this world, staff/quest/system item, pure decoration).
- Check your JSON parses (`python -c "import json; json.load(open(...))"`).

Item writers: your assignment file lists the holdable classes of your area, `name<TAB>namespace<TAB>base chain`. Cover the classes a UOR player can actually meet (bought, dropped, crafted, found, used) with **topics that are as few and as meaningful as possible**: one topic per kind of thing, using `inherits` for a family and `types` for the exceptions or for single items. Give a pure decoration family one short group topic rather than one per piece. Classes you leave out fall to the general item page, which is fine for the ones that are not in this world. Unique-claim rule: every class name once, across all areas, so stay inside your assignment and use the exact names in your file.

Area prefixes for item keys: `w-` weapons, `a-` armor and clothing, `t-` tools and paper, `r-` resources and consumables, `m-` miscellaneous.
