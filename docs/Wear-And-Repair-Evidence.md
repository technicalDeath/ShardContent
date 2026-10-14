# Wear and repair: the durability page in About (2026-10-13)

Owner to-do of 2026-10-12 ("a durability section in the About pages"): the durability facts were scattered over the weapon, armor and shield topics. They are now one topic, **Wear and repair** (`a-wear` in `data/help/items.json`), reachable from an item's About and from the Arms Lore and Blacksmithing skill pages. Help text only: no server or client code changed, no flag added. It is live whenever `helpGumps` is on (it is).

## What the page says, and where each fact comes from

| Statement | Source (checked 2026-10-13) |
| --- | --- |
| A new ordinary piece starts full; a successful Arms Lore use tells you how worn it is | `BaseWeapon`/`BaseArmor`/`BaseShield` (`HitPoints = MaxHitPoints` on creation), `ArmsLore.cs` |
| A weapon loses a point on about one hit in 25; slimes and acid elementals cost a melee weapon a point on every hit | `BaseWeapon.cs` ~2145-2148 (`isAcidMonster || Utility.Random(25) == 0`, with `defender is Slime or AcidElemental`) |
| Armor wears when hit: a 1 in 4 chance, 1 point or none; a bashing weapon wears it by half of what the piece soaked up, at least 1 | `BaseArmor.cs` ~735-749 (`Utility.Random(4) == 0`; `Bashing ? Math.Max(1, absorbed / 2) : Utility.Random(2)`) |
| A shield wears only when it blocks, 1 time in 4, by 1 point or none | `BaseShield.cs` ~69-71 (`Utility.Random(100) < 25`, then `Utility.Random(2)`) |
| Damage and rating shrink as durability falls, to half at 0 | `BaseWeapon.ScaleDamageOld`, `BaseArmor` rating scale |
| At 0 the wear lowers the maximum; "Your equipment is severely damaged."; a piece whose maximum is used up is destroyed | `BaseWeapon`/`BaseArmor` hit-point setters |
| Only a Blacksmith repairs, and only what a Blacksmith can make; leather, studded leather, bone and clothing cannot be repaired | `Engines/Craft/Core/Repair.cs`, the T2A Blacksmith menu (the only craft menu that offers Repair) |
| A weapon with poison on it cannot be repaired | `Repair.cs` ~273 (`!Core.AOS && weapon.PoisonCharges != 0`) |
| A repair is a Blacksmithing check, harder the more worn the piece | `Repair.cs` ~75 (`mob.CheckSkill(skill, difficulty - 25.0, difficulty + 25.0)`) |
| Chance to lose maximum on repair: 40 + missing durability - Blacksmithing/10, percent; the maximum falls by 3 (below 70), 2 (70 and up), 1 (90 and up); a piece whose maximum is no more than that refuses | `Repair.cs` (message 1044278 at ~283, 353, 424) |
| Exceptional +20% durability; durable..indestructible +20/50/70/100/120% | `BaseWeapon`/`BaseArmor` durability levels |
| The combat bar's gauge and the quarter-durability notice | gated paragraphs (`requires` `CombatBar`, `WearNotice`), so the text follows the flags |

## What changed

- `data/help/items.json`: the new topic (art 5091, skills Arms Lore and Blacksmithing). The general weapon, armor and shield topics each link to it (a topic holds at most four buttons, so each gave up one other link: Arms Lore, Arms Lore, Carpentry).
- **A gap the new test found:** four weapon pages (knives, maces, staves, bows) said "See A weapon" but had no button to it, so a player on the club's page could not reach the page that holds the shared durability text. They now link to **A weapon** (instead of the sword, staff, crook and crossbow links respectively; those pages link back to the bow/mace they belong with), and A weapon links to Wear and repair.
- `tests/HelpCatalogTests.cs`: `TheWearAndRepairPageIsReachableFrom...` (the links, the two skills, the two gates) and `EveryPageThatSaysSeeAnotherPageHasAButtonToIt` (fails on any "See <Title>" with no button; it failed on the four pages first, then passed).

## Evidence

- Shard tests: 1351 passed (full suite, run `20261013T181407431Z-62e892`).
- Real client, disposable host `help-check` (deleted afterwards): About on the held club opened Maces and clubs, now with an **A weapon** button; that page shows Back, Tactics, Anatomy, Blacksmithy and **Wear and repair**; the new page read through to the end with no clipped line (shots `work/player-client/HelpTrain/shots/20261013-141440-w6-about-club2.png`, `...141452-w7-aweapon.png`, `...141504-w8-wear1.png`, `...141507-w9-wear2.png`, `...141521-w10-wear3.png`, `...141525-w11-wear4.png`). The gated paragraphs about the combat bar and the quarter notice show because both flags are on in the host.
- Deployed to the dev distribution (`ModernUO/Distribution`, help text and DLL identical to source) with the server stopped.

## Limits

- The Arms Lore and Blacksmithing skill pages list the topic through the `skills` field of the topic (a test covers it); I did not open both in the client.
- Armor and shield pages reach it directly (`a-armor`, `a-shields`); the individual armor pieces (plate, chain, ...) reach it through `a-armor`, one click further. Axes, polearms, hatchets and pickaxes do not link to A weapon (their text does not point there); the four-button limit leaves no room without dropping something useful.
- The line numbers above are as of ModernUO `136e573c8`.
