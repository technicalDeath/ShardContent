# Poison relief for new characters: plan

Origin: the owner played a new archer on 2026-10-11 and found the Britain graveyard's Wraiths and Spectres, which cast Poison, too harsh for a character with low Healing and no Cure spell or potions. Ideas were offered the same day; the owner chose ideas 1 to 3 and rejected idea 4 (shorter poison for novices). He answered the open questions in chat (5 potions, a 30 second window, Lesser poison only, the hint once per character) and the build followed. Evidence: `Poison-Relief-Evidence.md`. Readiness: `Poison-Relief-Readiness.md`.

## What the code said (the harshness)

- Wraith and Spectre use the mage AI with Magery 55 to 70. Poison is 2 of the AI's 16 spell choices and is only cast on a target that is not already poisoned. The Britain graveyard spawner holds 9 slots of Spectre, Wraith, Skeleton and Zombie, so about half the pack casts.
- The poison level comes from the caster's Magery plus Poisoning; Regular needs more than 130. Their total is at most 70, so it is always **Lesser** poison: 4 hit points every 3 seconds, 10 times, about 40 hit points over 35 seconds, half of a 78 hit point starter.
- **The trap:** a bandage on a poisoned patient only tries to cure, and the cure needs Healing and Anatomy of 60 or more, so a new character's bandage always fails, heals nothing and is used up. No starting template has Healing. Unpoisoned, Healing 0 gives only a 10% chance per bandage.
- What cures: a Lesser Cure potion (75% against Lesser; alchemists sell them for 15 gp), the Cure spell, or 60/60 bandaging. A new character has none and nothing says so.
- Stock UO:R handled this with a Young player's full poison immunity. The Young system is off here (an earlier owner ruling), so this item is a narrower replacement.

## What was built (all behind `featureFlags.poisonRelief`, shipped off)

1. **Starter potions.** Every new character is given 5 Lesser Cure potions, newbied, loose in the backpack, once per character. They count in the starter weight budget.
2. **Telling the player.**
   - The first time a character whose bandage cannot cure (Healing or Anatomy under 60) is poisoned, one system message explains what is happening and what ends it. It is never repeated for that character.
   - The Poisoned buff-bar tooltip gets a line, "A bandage only tries to cure you, and that needs Healing and Anatomy 60.", shown only while the flag is on. The buff bar already showed "Poisoned" with the level (since 2026-10-07).
3. **Grace window.** After a poison ends or is cured, poison of Lesser strength from a non-player source (a monster, a trap, a field) cannot land on an ordinary player for 30 seconds, and the player is told "You are still shaking off the last poison, and this one finds no hold." Poison from a player (or a pet or summon a player controls) and any stronger poison are stock.

Settings: `poisonRelief { curePotions 5, graceSeconds 30, graceMaxLevel 0 }` in `shard-rules.json`, validated. Staff command `[PoisonReliefStatus`.

## How it works

- **Engine (ModernUO, one narrow hook):** `PlayerMobile.PoisonImmunityHandler`, a delegate asked once for each poison about to land, after the stock checks for a stronger poison already active and for Young immunity; returning true refuses it. Null keeps stock.
- **Shard:** `PoisonReliefService`. The decisions are pure functions (the grace rule, the hint rule, the potion count). A once-a-second watch over online players notices a poison landing (the hint) and a poison ending (the start of the grace window), like the buff-icon watch. The grace window is held in memory only.

## Not in this item

Shorter poison for novices (idea 4, rejected), a bandage floor (a separate idea: starter bandages are nearly useless at Healing 0), spawn or AI changes, potions for existing characters, changes to the Cure spell.
