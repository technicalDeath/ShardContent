# House lockdown reminder: work plan for sign-off (2026-10-13)

Drafted autonomously while the owner was away; **nothing is built.** From the To-Do list (2026-10-08): a player who is in a house they own, puts an item down, and does not lock it down or secure it within about 10 seconds gets a reminder; a cooldown (about once a day) keeps it from nagging.

## Goal and exit criteria
A new house owner who drops an item on the floor learns, once, that it will decay or can be taken unless it is locked down, and how to do it. Exit: verified live (drop, wait, reminder; lock down in time, no reminder; second drop within the cooldown, no reminder), real-client picture of the message, flag off until the owner says activate.

## Current state (read 2026-10-13)
- Stock has `BaseHouse` (`UOContent/Multis/Houses/BaseHouse.cs`) with lock-down and secure handling and `IsOwner`/`IsInside` style checks, but **no event for "an item was just put on the floor"**. `Item.DropToWorld` / `OnDroppedToWorld` (`Server/Items/Item.cs`) are the place; nothing observes them.
- Unlocked items in a house decay and can be taken by others who enter, which is why the owner wants the reminder.
- The Welcome guide has no house page; housing rules are still in flux (`Beta-2b-Settlement-Housing-Notes.md`).

## Design
| Rule | Proposal | Stock |
| --- | --- | --- |
| Who | The owner (and co-owners) standing inside their own house | n/a |
| Trigger | The player drops a movable item on the house floor | no trigger |
| Wait | 10 seconds; if the item is still loose (not locked down, not secured, not picked up, not in a container) the reminder is sent | n/a |
| What counts | A single loose item. Not a container already locked down or secured, not a placed addon, not trash in a trash barrel, not items dropped into containers (a possible second stage) | n/a |
| Message | One line, system colour, in the style of the other tips: "That item is not locked down. Use the house sign's menu or say I wish to lock this down, then target it, or it may decay or be taken." (wording to be confirmed against the real commands) | n/a |
| Cooldown | Once per account per 24 hours (the travel warning is per account) | n/a |
| Off switch | `[HouseReminder off` command and a guide line, as for the travel warning | n/a |

## Work breakdown
1. ModernUO: one static event `Item.DroppedToWorld(Mobile from, Item item)` raised at the end of a successful `DropToWorld` (the narrowest hook; no behaviour change).
2. ShardContent: `HouseReminderService` (flag, registration with `+=`, the timer, the checks above, the cooldown stored as an account tag, the command), tests, a one-line mention in the guide's Commands page.
3. Verification: unit tests for the decision table; live on a disposable host with a built house (the Furnisher probe already builds one: `tests/scenarios/furnishers/FurnisherProbe.cs`); real-client picture.

## Activation
New flag `houseReminder`, off. Needs the owner's explicit "activate".

## Open questions (with recommendations)
1. Per account or per character cooldown? Recommend per account.
2. Remind also for items dropped into an unsecured container? Recommend no for the first version.
3. Remind co-owners and friends too, or owners only? Recommend owners and co-owners (the people who can lock down).
4. Wording and whether to name the exact commands: recommend naming them, after checking the sign's menu text in the real client.

## Out of scope
House zoning, the settlement housing idea, any change to decay times.

## Built 2026-10-14 (autonomously, owner away; recommendations above taken as the design) 
Engine: `Item.DroppedToWorld` (static event, raised at the end of a successful `DropToWorld`; `ModernUO/Projects/Server/Items/Item.cs`, uncommitted, **Distribution not rebuilt, so the dev server does not have it yet**). Shard: `HouseReminderService.cs` (flag `houseReminder` OFF, owner or co-owner, 10 s wait, once per 24 h per character via an account tag, `[HouseReminder on|off`), `HouseReminderTests.cs` (13 pass). Deviation: the cooldown is per character (the account tag is keyed by the character serial, as the other hints are), not per account. **Not verified live** (needs a built house and the rebuilt engine; the Furnisher probe's `[TestOnlyFurnisherHouse` can build one). Deploy needs: rebuild UOContent into Distribution, a pin bump after committing ModernUO (3 places), then Deploy-Alpha1Baseline. Activation needs the owner's "activate".

**Live check 2026-10-14 (disposable host, FurnisherProbe house, Navrey, no real-client picture):** a loose item dropped by the owner inside their own house got the reminder about ten seconds later; a second loose drop straight after got nothing (the daily cooldown); `[HouseReminder off` answered as designed. Not exercised: a locked-down item (no reminder), a non-owner, a co-owner, an item picked up within the wait (all decided by `ShouldWatch` and `ShouldRemind`, which are unit-tested). The engine event fired in the real server. Supersedes "not verified live" above.

**Activated 2026-10-14** with the deploy, on the owner's "commit deploy and activate all work" (flag `houseReminder` ON; the engine event is in ModernUO `4fbc58cfb`).
