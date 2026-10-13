# Auto-use options on the potion and combat bars

Owner request, 2026-10-13 (mid new-player pass): "an options button ... that pops out a panel under the combat hotbar, and one for the potions hotbar ... bandages: auto-heal at 75% health, heal potions: auto heal at 25% health, refresh potion: auto-refresh at 25% stamina ... the auto use option should use the most powerful potions first ... cure potions should have an auto use option that intelligently uses the correct cure for the level of poison."

Built behind a new server flag, `featureFlags.autoUse`. **Enabled 2026-10-13 on the owner's explicit "Commit, activate"** (flag on in the source and deployed to dev; committed, not pushed).

## A ruling to confirm

`Quality-of-Life-Research.md` (2026-10-07) lists "autoloot / loot-all / auto-bandage" among what was left out, and the owner's own test for a QoL change is "does not automate play". This request supersedes the note for these four things only. Points the owner may want to rule on before activation:

- **PvP fairness.** A client-side reflex acts faster than a hand. The flag is the switch; a finer one (no auto-use in a Hot Zone, or after attacking a player) is not built.
- **Adjustable thresholds.** The numbers are the owner's (75, 25, 25) and fixed; the panel has check boxes only.
- **Automation of play.** It drinks and bandages only; it never attacks, targets others or moves.

## What the player sees

A small brass gear at the end of the **potion bar** and of the **combat bar**, shown only when the server's menu mask carries the new auto-use bit (so with the flag off nobody sees it). Clicking it opens a panel just under the bar (above it when the window ends first); it closes on a press outside it, on the gear again, or when the bar goes away.

| Bar | Option | Rule |
| --- | --- | --- |
| Combat | Bandage me when my health drops below 75% | Same steps as a click on the bandage slot, aimed at yourself. Not while a bandage is being applied (`BandageWatch`). **While poisoned** it bandages too, but only if the character's Healing **and** Anatomy are both 60 or more (the server's rule for a bandage to cure; below that a bandage does nothing against poison), and the Cure potion option goes first when it is on and has a potion that could work. |
| Potion | Drink a Heal potion when my health falls to 25% | The strongest Heal potion in the pack (Greater, then Heal, then Lesser); not while poisoned (the server refuses); one every 10.5 s (the server's own 10-second wait). |
| Potion | Drink a Refresh potion when my stamina falls to 25% | Total Refresh first, then Refresh. |
| Potion | Cure me when I am poisoned | The client asks the server (extended command 0xAA); the server answers with the cure to drink (next section). |

All four are off until ticked, and the choice is kept in the character's profile (`auto_bandage`, `auto_heal_potion`, `auto_refresh_potion`, `auto_cure`).

Common rules (`AutoUse.Tick`, four looks a second): never while dead, while an item is held on the cursor or a target cursor is up (so it cannot hijack a spell's target); at most one automatic action every 1.6 s; a potion goes through the potion bar's own drink steps (the weapon comes off first when both hands are busy, as for a click). Order: cure when poisoned, then a Heal potion at the low line, then a bandage, then a Refresh potion.

## Which cure

The client is told only that a character is poisoned, not how strongly, so the server decides (`AutoUseService`, with the era's cure table the three potion classes carry for a non-AOS server):

| Poison | Lesser Cure | Cure | Greater Cure |
| --- | --- | --- | --- |
| Lesser | 75% | 100% | 100% |
| Regular | 50% | 75% | 100% |
| Greater | 15% | 50% | 100% |
| Deadly | 0 | 15% | 75% |
| Lethal | 0 | 0 | 25% |

The reply names the **weakest cure in the backpack that is certain (100%)**, else **the one with the best chance**, else none (nothing the player holds could work: they are told once). So a Lesser poison is cured by a plain Cure rather than a Lesser one (75%), a Regular poison by a Greater Cure, and a character with only a Lesser Cure facing a Greater poison drinks it and takes the 15%.

## Files

Server (ShardContent): `AutoUseService.cs` (flag, command 0xAA, `Choose`), `MenuBarService` (mask bit 4), `ShardRulesConfiguration`/`shard-rules.json` (`autoUse`, false), `WelcomeGuide` (an "Auto options" paragraph on the Your screen page, shown only when the flag is on), tests `AutoUseTests`, `GuideScreenTopicTests`. Client (ClassicUO): `AutoUse.cs` (engine and the panel), gear buttons in `PotionBarGump` and `CombatBarGump`, `TopBarGump.AutoUseAllowed`, `Profile`, `PacketHandlers`, `OutgoingPackets`; art id 62052 (`tools/gump-art/make_pack_icons.py`, copied to the client's `Data/Gumps`).

## Two defects found and fixed on the way (client, `BandageWatch.cs`)

The first real-client run of "bandage while poisoned" burned a whole stack: three bandages in 11 seconds, none finishing. Two old assumptions in `BandageWatch`, which both bars use to know a bandage is being applied, were wrong for this shard:

1. **"Your fingers slip!" ended the watch.** On the server a slip (damage taken while healing) only counts against the bandage's chance (`BandageContext.Slip`); the bandage carries on. A poison tick is damage, so every tick made the bar think the bandage was over, and the auto-bandage started another one, which makes the server stop the old bandage (`BeginHeal` calls `StopHeal`) and use up a new one. Fixed: a slip no longer ends it.
2. **The end estimate used the later (AOS) formula.** This is a non-AOS shard, where healing yourself takes 9.4 s + 0.6 s per 10 points of Dexterity under 120 (about 14 s at Dex 45), not 5 s + 0.5 s per 10, clamped to 12. The estimate ran out about two seconds before the bandage finished, with the same result. Fixed: the server's formula plus a 3 s margin; the server's "finish applying" message still ends it as soon as it arrives.

Both also affected the manual combat bar and shortcut bar (the "applying" cue ended early after a hit), so that is fixed for them too.

## Evidence

Real client (ClassicUO from `ClassicUO/bin/dist`, rebuilt after each fix), disposable host `help-slice` with `autoUse` on (host only; the source flag stays false), character HelpAlpha, 2026-10-13. Screenshots are in `work/player-client/HelpAlpha/shots/` and were sent to the owner. Poison, skills and wounds were set with the test-only probes (`TestOnlyPoison`, `TestOnlySkillSet`, `TestOnlyHurt`).

| # | Case | Result | Shots |
| --- | --- | --- | --- |
| 1 | Bandage ticked, health under 75%, not poisoned | A bandage is applied to the character without any click | `ab1`-`ab3` |
| 2 | Heal potion ticked, health at 25%, Lesser, Heal and Greater in the pack | The Greater Heal is drunk first | `ah1`-`ah2` |
| 3 | Refresh potion ticked, stamina at 25%, Refresh and Total Refresh in the pack | The Total Refresh is drunk first | `ar1`-`ar2` |
| 4 | Cure ticked, Regular poison, Cure, Greater Cure and Lesser Cure in the pack | The Greater Cure is drunk (the weakest that is certain) | `ac1`-`ac3` (the cure line and the potion counts; the potion that went is read from the slot counts) |
| 5 | Cure ticked, Lesser poison | A plain Cure is drunk, not a Lesser one (75%) | `ac2`-`ac3` (slot counts) |
| 6 | Cure ticked, Deadly poison, only Lesser Cures (0% against Deadly), Healing and Anatomy 70 | One line, "You are poisoned, and you have no Cure potion that could cure it.", then it falls back to a bandage (Cure potion option does not waste a Lesser Cure) | `ad1`, `ad2` |
| 7 | Same, Healing at 20 (a bandage cannot cure) | The same one line, and **no bandage at all** (count steady at 25 before and nine seconds after) | `clean-before`, `clean-3s`, `clean-9s` |
| 8 | Cure unticked, Healing and Anatomy 100, Greater poison | One bandage: slips as the poison ticks, "You finish applying the bandages. You have been cured of all poisons!"; then, still hurt, a second bandage to heal. No restart in the middle (before the fixes: a new bandage every few seconds, the count fell 25 to 22 in 11 s) | `g-15`, `g-20`; before: `bandage-cure-11s`; after the first fix only: `fix-13s` |
| 9 | The gear panels | Readable, opaque, above the bar, closes on an outside press; the tick boxes persist (unticked Cure stayed unticked after a client restart) | `panel-potion-final`, `panel-combat-final`, `cure-unticked` |
| 10 | Vendor shop window default height (new-player pass item 23) | Opens about 490 px tall below the top bar, five full rows visible, the Bill of Sale beside it | `shop-default` |

Note on case 7 and the 60 line: the server compares `Skill.Value`, which includes a stat bonus (up to 10 points at 50 for Healing), not the base. The client sends and reads the same `Value`, so the rule matches; a test at base 50 can therefore still cure, which is why case 7 uses 20.

Tests: `AutoUseTests` (cure choice, replies, mask, flag off) in the shard suite; the full shard suite passes (1320 tests, run `20261013T141454654Z-cb433f`). The client has no unit tests; the cases above are its evidence.

Open for the owner: text review of the panel wording; the PvP-fairness question above; the flag (`autoUse`, off) and a deploy.
