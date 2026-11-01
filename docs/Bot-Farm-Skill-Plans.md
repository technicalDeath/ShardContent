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
