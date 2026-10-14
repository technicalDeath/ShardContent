# Auto-pickup of ammunition and reagents: work plan for sign-off (2026-10-14)

Drafted autonomously from the owner's to-do (2026-10-14: "auto pickup arrows or bolts or reagents based on user skill levels ... with option to toggle on off"). **Nothing is built.**

## Goal and exit criteria
An archer or crossbowman who walks over their fallen arrows or bolts, and a caster, alchemist or scribe who walks over loose reagents, collects them without double-clicking each pile, only the kinds their skills use, with a switch to turn it off. Exit: unit tests for the decision table, a live run on a disposable host (pickup, wrong skill refused, switch off, someone else's item refused, overload refused), a real-client picture of the switch and the pickup line, flag off until the owner says "activate".

## Current state (read 2026-10-14)
- **Stock engine:** `AmmoRecovery` gathers missed ammunition for the shooter, but only when `Core.SE`; it is inactive on this UOR shard. Nothing picks up reagents.
- **Client:** the combat bar already shows ammunition and reagent counts and knows which a character uses (reagents only with Magery, Alchemy or Inscription; ammunition dimmed for the wrong weapon). A pickup is a drag-to-pack or double-click on the pile.
- **Era:** UOR has no auto-pickup of any kind; this is a shard convenience, so it needs the owner's design test ("does not automate play"). It automates a chore, not a decision.

## Design
| Rule | Proposal | Stock |
| --- | --- | --- |
| Where | Server side. A once-a-second watch (as the tips service does) looks at items within 1 tile of an online ordinary player. Server side so it cannot be driven faster than a hand and needs no client change | none |
| What | Arrows and bolts (stock `Arrow`, `Bolt`); the eight stock reagents | none |
| By skill | Arrows if Archery is at least 30, bolts if Archery is at least 30 (crossbows use Archery); reagents if Magery, Alchemy or Inscription is at least 30. Below that the character is not a user of the kind | none |
| Whose | Only items lying loose on the ground that the player may pick up: not in a house the player is not allowed in, not locked down, not a vendor's stock, not another player's corpse. An item another player dropped within the last 30 s is left alone (a thief cannot be farmed, and a trade drop is not swept up) | none |
| Weight | Stops when the pickup would overload the player (the starter weight budget rule, 85% of the limit) and says so once | none |
| Range and rate | The tile the player stands on and the 8 around it, at most one pile per second | none |
| Message | One line the first time: "You pick up N arrows. Auto-pickup is on; type [Pickup off to stop it." Later pickups are silent except the stock pile-in-pack sound | none |
| Switch | `[Pickup on|off` per character (account tag), default on for new characters when the flag is active, plus a tick box on the combat bar's gear panel later | none |
| Hot Zones | Allowed (it is a chore, not an advantage in a fight) | none |

## Work breakdown
1. `AutoPickupService.cs` (ShardContent only, no engine hook): flag, a `+=` guarded `Configure`, the watch, pure decision functions, the tag and the command.
2. Flag `autoPickup` in `ShardRulesConfiguration` and `shard-rules.json`, off; `[AutoPickupStatus` staff command.
3. Tests `AutoPickupTests.cs` for the decision table (skill thresholds, kinds, drop age, weight, switch).
4. Guide: a line in the Welcome Commands page (gated) and the combat-bar page.
5. Evidence document, README rules line at activation.

## Verification
Unit tests; one disposable-host session: drop arrows and a reagent pile next to an archer, an archer with Archery 0, a caster; a pile dropped by another player; an overloaded player; `[Pickup off`. Real-client picture of the line. No shared world state is touched.

## Activation
New flag `autoPickup`, off. Needs the owner's explicit "activate".

## Open questions (recommendation first)
1. Server side, as above? Recommend yes.
2. Skill threshold 30, or any skill above 0? Recommend 30 so a character who has never shot is not swept.
3. Include other chores later (gold, gems, bandages dropped)? Recommend not in the first version.
4. Default on or off for a character? Recommend on, with the message naming the switch.

## Out of scope
Looting corpses automatically (the QoL research ruled autoloot out), pet or vendor interactions, any change to ammunition recovery chance.
