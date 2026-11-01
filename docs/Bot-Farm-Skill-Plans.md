# Bot skill plans: a full 700-point set per bot type (2026-11-01)

**Owner, 2026-11-01:** "Do a pass at giving each bot type a full set of skills to fill out their 700 points that will help them in their goals, and give them the behavior and logic to use them." His example: "A tamer could use their pets to hunt, and hunt themselves with a weapon, so them plus pets hunt to get gold."

## Where the bots stand

Measured from each bot's skill list.
- **Base totals** are 280-490 of 700. The display values look higher because they include stat bonuses.
- **Room:** every bot has 200-400 points free.
- **Locks:** no bot has ever changed a lock (all are "up").
- **Drift:** points went into whatever the bot happened to use: Camping and Cooking on fighters, Wrestling on archers, Meditation almost everywhere.
- **The real gap is behaviour.** The bots use two or three skills.

## Era rules the plans follow

Research report, with sources: the official publish notes (Publish 1, 4 and 5), Stratics, UOSA and Lost Lands.
- **Skill locks** (up / down / locked) arrived in Publish 1 (1999), with the 700 cap.
  - A skill set down loses points only while another one gains past the cap.
- **Publish 5 (UOR, April 2000):** damage done by tamed or provoked creatures counts toward the tamer's or bard's loot rights.
- **Veterinary** heals a pet with bandages (there is no bonding or pet resurrection in UOR).
- **Healing** cures poison at 60 Healing / 60 Anatomy.
- **This engine, from code:**
  - Lumberjacking adds up to +20% damage with axes (`BaseWeapon`, `Core.UOR`).
  - Arms Lore gives crafted gear nothing before ML, so no plan uses it.
- **Not used (AOS or later):** Chivalry, Necromancy, Bushido, Focus, power scrolls, Discordance.

## The plans (7 skills at 100 = 700)

Mechanics: `skillplan.py`, feature `skill_plan`. Every 30 minutes the bot reads its skills and sets each lock: up below the target, locked at it, down for everything else. A skill set down only falls while another rises past the cap.

| Type | Skills | Era source | New behaviour needed |
| --- | --- | --- | --- |
| Animal Tamer | Animal Taming, Animal Lore, Veterinary, Archery, Tactics, Anatomy, Healing | Stratics tamer-archer, without its 8th skill (Magery) | **shoot the pet's target with a bow**; Veterinary on a hurt pet; self-Healing exists |
| Ranger | Archery, Tactics, Anatomy, Healing, Animal Taming, Tracking, Hiding | composite ranger (Archery core, Taming, Tracking, Hiding) | Hiding to escape |
| Archer | Archery, Tactics, Anatomy, Healing, Resisting Spells, Bowcraft/Fletching, Lumberjacking | light warrior, with fletching in place of Magery | fletch its own arrows from its own logs (the Bowyer's arrows sold out for hours) |
| Swordsman, Mace Fighter, Fencer | weapon, Tactics, Anatomy, Healing, Parrying, Resisting Spells, Hiding | UOSA dexxer core (Tactics, Anatomy, Healing, Resist) with Parry and Hiding | Hiding to escape |
| Bard | Musicianship, Provocation, Peacemaking, Archery, Tactics, Anatomy, Healing | composite bard-archer | provoke for loot rights (Publish 5) |
| Pure Mage | Magery, Evaluating Intelligence, Meditation, Resisting Spells, Wrestling, Tactics, Anatomy | tank-mage core | none: the casters already use these |
| Sorcerer | Magery, Evaluating Intelligence, Meditation, Inscription, Resisting Spells, Wrestling, Anatomy | Stratics pure mage with Inscription | none (`scribe.py`) |
| Warlock | Magery, Evaluating Intelligence, Meditation, Resisting Spells, Fencing, Tactics, Anatomy | UOSA tank mage | none |
| Prospector | Mining, Blacksmithy, Tinkering, Hiding, Healing, Anatomy, Wrestling | Stratics miner (Tinkering for its own shovels) + Hiding | **make its own tools** (Tinkering); Hiding; self-Healing |
| Blacksmith | Blacksmithy, Mining, Tinkering, Hiding, Healing, Anatomy, Wrestling | Lost Lands smith-miner core | make its own tongs and hammers; Hiding; Healing |
| Tinker | Tinkering, Mining, Lumberjacking, Carpentry, Hiding, Healing, Anatomy | Lost Lands tinker-smith core | Hiding; Healing |
| Carpenter | Carpentry, Lumberjacking, Swordsmanship, Tactics, Anatomy, Healing, Hiding | lumberjack-warrior (axe +20% from Lumberjacking) | fight with its axe; Healing |
| Tailor | Tailoring, Swordsmanship, Tactics, Anatomy, Healing, Tracking, Hiding | hunter-tailor (its own hides) | find animals by Tracking; Healing |
| Fisherman | Fishing, Cooking, Wrestling, Tactics, Anatomy, Healing, Hiding | fisher, who must fight sea serpents (Publish 4) | Healing; Hiding |

Magery for Recall is left out of the non-casters. Every bot would need reagents, runes and a spellbook; that is a later step if the walking times show it pays.

## Build order: biggest gold first, one A/B at a time

1. **The plan and locks for every type** (`skill_plan`). This costs nothing at play time and stops future drift.
2. **Tamer: fight beside the pet.** Buy a bow and arrows, shoot what the pet fights, bandage the pet (Veterinary) and itself (Healing). It was at about 200 gold with no armour.
3. **Shared self-Healing for gatherers and crafters.** Bandage after a fight, as the fighters already do.
4. **Shared Hiding.** Hide when a threat closes and running is not possible; practise it when idle.
5. **Tools from Tinkering** for the miners and smiths.
6. **Fletching** for the archers.

Each step is gated (`farm_release.py --check`), run on a canary for 30 minutes, and measured in gold an hour and skill points.

## Status, 2026-11-01 13:25

| Step | State |
| --- | --- |
| 1. Plans and locks | **Live on all bots** since 13:11 (`skill_plan`; tree 2bcc717fe8af). Dead weight is locked down: Meditation and Wrestling on fighters, Discordance on bards, Fletching and Tinkering on a carpenter. Hiding is set up where the plan holds it. |
| 2. Tamer fights beside its pet | **Live on BotTamerAR** (`tamer_weapon`): buys a bow and arrows once it carries the gold (no shop walk without it), shoots the pet's target, and bandages the pet from Veterinary 0. Its pet hunt also works tier-2 areas the pet can hold, and when poor it looks for a stronger pet (a grizzly beats orcs, a brown bear does not). |
| 3. Self-Healing | **Live** for miners, fishers and crafters (`basics.r_heal`); bandages are bought from Healing 0 when the plan holds Healing. |
| 4. Hiding | **Live** for miners, fishers and crafters (`basics.r_hide`, practised when idle). Engine rules (`Hiding.cs`): it fails while a monster within (100 − skill)/2 + 8 tiles has the bot as its target, the chance is the skill, and the next try is 10 s later. |
| 5. Tools from Tinkering | Not built. It needs the crafters' Tinkering menu inside the gatherer brain, and the saving is a few gold a pickaxe. |
| 6. Fletching | **Already built** (`r_fletch`, `r_wood`), now on for all five archers. |
| Fighters' Hiding, the carpenter's axe, bard provocation for loot | Next. |

## Second pass, 2026-11-01 evening (owner: "faster and more meaningful progress ... using more skills")

Measured first: the plan skills that rose less than 0.3 in four hours while still under 80, by profession. The causes, and what changed:

| Stuck skill | Cause | Change |
| --- | --- | --- |
| Parrying (all nine melee fighters) | no shield: Parrying blocks and rises only with one | `shields.py` `r_shield`: a one-handed fighter buys the best shield it can afford with 300 gold to spare (heater 231 gold, armour 23; metal kite 123/16; wooden kite 70/12; buckler 50/7; SBBlacksmith, ArmorBase) and wears it. Two swordsmen bought heaters within ten minutes. |
| Provocation, Peacemaking (bards); Bowcraft/Fletching, Lumberjacking (archers) | the decision core (`task_core`) runs only the reflex rules, so `r_music`, `r_fletch` and `r_wood` never ran: no event in four hours | `BotBase.CORE_SKILL_RULES`: the core lets these (and `r_shield`) run; each has its own limits |
| Tailoring at 75-79 (all four tailors) | above 78.9 only leather items teach (`craft_data.json`), and the tailors worked only cloth; at 79.1 they made floppy hats at 100% | leather mode in `crafter.py`: hides from the Furtrader (3 gold) or Leatherworker (4), cut with scissors, leather and studded armour in the window, sold to the Tanner |
| Archery, Veterinary (tamer) | no bow: its bank walk was refused, and then it bought "Arrow Fletching" for arrows | a withdrawal for a purchase passes the long-walk rule; arrows are bought by exact name |
| Hiding, Healing (gatherers and crafters) | live since 13:23 and starting from 0 | practising; measured over the next runs |
| Resisting Spells | rises only when spells hit you | left alone |
