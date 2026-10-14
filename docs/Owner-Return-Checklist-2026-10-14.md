> **Superseded 2026-10-14:** the owner said "commit deploy and activate all work"; everything below was committed, deployed to dev and activated. The commits are not pushed.

# Owner return checklist (2026-10-14)

What was built while you were away, what is live where, and the decisions only you can make. Nothing below is committed or pushed. Details: `Commit-Plan-2026-10-13.md`, `New-Player-Pass-2026-10-13.md`.

## Decisions waiting on you
| Item | Where it stands | You say |
| --- | --- | --- |
| **Commit and push** | ModernUO has four small engine hooks (`Item.PropertyListBuilder`, `CharacterCreation.StartingCitiesFilter`, `LootPackEntry.WeaponLootSlayerAllowed`, `Item.DroppedToWorld`); the pin must be bumped in 3 places after the ModernUO commit | "commit" (order in the commit plan) |
| **Deploy to dev** | The dev Distribution has the 2026-10-13 work; it does **not** have `Item.DroppedToWorld`, the new shard DLL, or the new config (three new flags, all off) | "deploy" |
| **Activate `newPlayerTips`** | Out of ammunition, badly hurt, first death, first resurrection, tired, 2,000+ gold in the pack, first pet; one Journal note after the first; `[Tips off`. Live-checked except tired and first pet | "activate newPlayerTips" |
| **Activate `autoPickup`** | Arrows, bolts and reagents your skills use (30+) are picked up within one tile; `[Pickup off`. Live-checked. At activation: README rules line | "activate autoPickup" |
| **Activate `houseReminder`** | Owner or co-owner leaves an item loose in their house: one reminder a day; `[HouseReminder off`. Live-checked. Needs the engine event deployed | "activate houseReminder" |

## Already live on the dev host (from earlier today, your words)
Item tooltips, Britain-only start, silver-only slayers, health-bar declutter, potion and cure hotkeys, Britain map markers, combat bar caption.

## Client-only, installed in `ClassicUO/bin/dist` now
Combat bar seeds empty weapon and tool slots from the pack; three clearer bandage messages (`Clilocs.txt`).

## Not planned, no decision needed yet
Criminal notice (stock already says You've committed a criminal act!! and the confirm boxes exist; only an optional reworded line through Clilocs.txt remains), hits/mana/stamina numbers (you said later), craftable slayer weapons (later), a server message so monster health bars show at full health.
