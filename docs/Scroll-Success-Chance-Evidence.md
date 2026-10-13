# Scroll success chance in the name (evidence)

Owner request 2026-10-11 ("for later", then "we can do it now"): a single click on a spell scroll shows the viewer's chance of casting it after the scroll's name. Flag `featureFlags.scrollSuccessChance`: **activated 2026-10-13** on the owner's "activate anything that hasn't been yet" (on in the source, deployed to dev).

## Built
- **Engine hook** (ModernUO, uncommitted): `SpellScroll.SingleClickPostfixHandler` and a `SpellScroll.OnSingleClick` override that appends the handler's text to the stock label (`Items/Skill Items/Magical/Scrolls/SpellScroll.cs`). A scroll with its own name, or no handler text, keeps the stock label. Same engine cycle as the Help hook: commit, rebuild `UOContent.csproj` into Distribution, bump the pin in three places, deploy.
- **Shard** `ScrollChanceService.cs`: builds the scroll's spell, reads its cast range with `GetCastSkills` (a scroll's range already starts 20 lower than a book's, 40 in the second circle, 50 in the first) and the viewer's current `Skills[CastSkill].Value`, and shows ` (NN% chance)` as `floor((value - min) / (max - min) * 100)`: 0 below the range, 100 at or above its end. Rounded down so 100 always means certain.
- Tests: `tests/ScrollChanceTests.cs` (the percent rule, and the flag off in the shipped rules).

## Real client (disposable host, flag on there only, 2026-10-11)
"Recall (0% chance)" for a character with no Magery; "Recall (94% chance)" at Magery 47.7 (Recall range 10 to 50). The menu still offers Add To Spellbook and Help. Two pictures sent to the owner.

## Not done
Help text: a gated sentence on the Spell scrolls topic and the Magery page ("click a scroll once to see your chance"), to add at activation. Checked live: only the Recall scroll; other circles use the same code path.
