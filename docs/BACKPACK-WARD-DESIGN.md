# Backpack Ward — Revised Full Design

Status: approved design, supersedes the Backpack Ward design previously inlined in the
[phased roadmap](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md) (Alpha 2, item 4) and the
[alternative plan](ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md) ("Consumable Backpack Wards").
This is now the sole source of truth for Backpack Ward mechanics; do not redefine them elsewhere —
reference this document instead. It does not cover the separate **Invisible Loot Protection Ward**
(monster-corpse anti-harassment), which remains defined in the alternative plan.

The most significant change from the prior design: the previous **120-second all-thief victim
immunity** on Ward trigger is replaced by a **Primed / Activated** per-thief state machine (Sections
2, 10). A thief the Ward has **caught** on a successful theft is **blocked from every theft attempt
against the protected character for the Ward's 30-minute window**; thieves it has not caught are not
blocked, and each caught thief is blocked separately. There is no blanket protection against unrelated
thieves.

**Revision 2026-10-01 (owner):** the earlier draft of this document only detected known thieves and
never blocked them ("a Ward never stops a theft"). That was a mistake. A caught thief is blocked for
the encounter (Sections 10, 11, 13, 22, 23, 25). **Built 2026-10-02 (Beta 2a item 1; evidence in `Beta-2a-Ward-Readiness.md`).**
`BackpackWardState.cs` holds the rules, `BackpackWardService.cs` runs them in the game, `BackpackWard.cs` is the
item, and `TheftProtectionService.cs` calls them through the stock `Stealing.TheftEligibility` and
`Stealing.TheftResolved` hooks. Choices made while building:

- **Hot Zones** (outdoor, and Hythloth since Beta 2a): a Ward does nothing there. No priming, no blocking, no timer refresh, as before.
- **Ward-detected thefts** carry the ordinary detected-theft consequences: the thief turns criminal, is told
  "You have been caught stealing!", and bystanders within 8 tiles are told what they noticed.
- **Old Wards:** a Ward saved under the earlier model (120-second immunity, account binding, per-thief counts) loads as
  a fresh Unprimed Ward. Only its starter marking carries over. Saves are now Ward version 3, which older builds cannot read.
- **Only genuine attempts count.** Stock calls its theft hook even for attempts it refuses before the skill roll, so a
  ModernUO hook now reports whether the roll ran (`Stealing.TheftResolved`, `rolled`). Refused and blocked attempts never
  restart a Ward's window.
- **Double-click feedback (Section 5, built 2026-10-04):** double-clicking a Ward tells the player what it is (the starter
  Ward says it is bound to them), its phase, and the whole minutes left before a Primed Ward resets or an Activated one is
  used up. Two lines then explain how it works (changed 2026-10-05, not yet deployed): it activates when a theft against
  the player is noticed, by the player or by the Ward; once activated it blocks every thief it caught until 30 minutes pass
  with no theft attempt against the player, then it is used up; thieves it has not caught can still try. They state the
  rolling window and the per-thief block of Sections 10 and 12 and promise no blanket protection. It adds a line when the
  Ward is outside the equipped backpack (not protecting; the timer keeps running) or the
  player stands in a Hot Zone (Wards do nothing there). A Ward tracking for someone else says only that. Expired time is
  applied first. No thief names or counts are shown. `WardDescription` holds the wording; `BackpackWardService.Inspect` runs it.
  Snooping a Ward in another player's pack does not reach it (stock calls `OnSnoop` instead of `OnDoubleClick`).
  Deployed 2026-10-05 and checked live (`tests/scenarios/ward/ward_inspect_live.py`: starter and regular Wards, Primed with 30 and then 20 minutes left, dropped on the ground, and a Primed Ward whose window ran out resetting when inspected). The Activated wording and the consumed-on-inspect path are covered by unit tests only.
- **Housekeeping (owner: no preference, recommendations applied):** F-3 account binding and F-7 loot-type fixup are
  removed; the unused Loot Protection entitlement, its world-load migration and its login hook are removed, and the
  10-minute repeat-looting rule stays (it never needed them).

## Consumable Backpack Wards — Theft Detection and Anti-Harassment

### Design intent

Backpack Wards provide prepared players with escalating detection of repeat thieves, and a block against every thief the Ward has caught, without weakening the underlying Stealing skill or creating blanket immunity from thieves.

The system preserves ordinary era-appropriate:

- Stealing success/failure;
- item eligibility;
- skill investment;
- cooldowns;
- ordinary theft detection;
- criminality;
- guard behavior;
- snooping.

A Ward does **not** reduce the chance that a thief who has not been caught succeeds at stealing an item. It does not undo the theft that catches a thief, but it stops that thief's later attempts (Section 10).

The design does not include:

- Awareness skill;
- reaction or key-sequence minigames;
- special Bless spell interactions;
- special Magic Trap or Magic Untrap behavior;
- theft-triggered stun or damage;
- Wardbreakers;
- universal post-trigger theft immunity.

The central goal is:

> **A Ward remembers and increasingly detects thieves involved in an ongoing theft episode, and once it catches a thief on a successful theft it blocks that thief from stealing from the protected character for the rest of the episode. It does not make the victim globally immune to thieves it has not caught.**

---

## 1. Physical Backpack Ward

A normal Backpack Ward is an obtainable physical **single-use consumable**.

It requires:

- no Magery;
- no combat skill;
- no minimum skill level;
- no manual activation.

There are no Ward power tiers.

Its sources (owner ruling, 2026-10-05, see [Beta-2a-Ward-Vendor-Readiness.md](Beta-2a-Ward-Vendor-Readiness.md) and [Beta-2d-Ward-Crafting-Readiness.md](Beta-2d-Ward-Crafting-Readiness.md)):

- **Purchase (built):** plain Tinker vendors sell it for gold. The price (`wardVendor.price`, 2,000 gp) is a **ceiling** for the crafted Ward to undercut, because Wards have no power tiers and crafters can only compete on price and availability. Each Tinker's shelf is deep (`wardVendor.stockPerVendor`, 20) so sweeping it for resale or denial costs far more gold than a launch-week character has; the stock-vendor engine doubles a shelf that sells out and halves one that sells under half. Every purchase is audit-logged (`theft ward-bought`). The sale follows `featureFlags.theftProtection`, and a stock of 0 takes it off sale.
- **Buy-back (built):** Tinkers pay a small fixed price (`wardVendor.buyBackPrice`, 110 gp; 0 turns it off) for an **unused** Ward, so a crafter who overestimated the player market still comes out slightly ahead of the ingots (20 ingots cost about 100 gp). It must stay below the sale price. Only an Unprimed, non-starter Ward qualifies; the starter Ward and any Ward tracking thieves are bound to their character and never sell. Tinkers do **not** re-list what they buy (stock vendors resell at 1.9 times what they paid, which would put a cheap Ward back on the shelf and undercut crafters again), so a bought-back Ward is deleted, a small gold sink. Buy-backs are audit-logged (`theft ward-sold`).
- **Crafting (built):** a Tinkering recipe in the Miscellaneous list with Key, Lantern and Scales (`wardCraft`: Tinkering 45.0 to 95.0, 20 iron ingots, `enabled`). The ingot count sets the market's price floor (NPCs sell iron ingots for 5 gp). A Ward has no quality grades, so the recipe offers no exceptional and no maker's mark. This era's Tinkering is a legacy item-list menu, so the recipe is added to the craft list and to that menu's Miscellaneous list at server start. It pulls one recipe forward from the Beta 2d crafting overhaul and does not depend on it. The vendor stays at 2,000 gp and 20 per shelf; once crafters exist its stock can be cut or its price raised through configuration so it is only a fallback for towns without one.

A Ward functions only while physically located within:

- the character's equipped paperdoll backpack; or
- any nested container inside that backpack.

A Ward stored in a:

- bank;
- house container;
- ground container;
- corpse;
- pet pack;

does not currently protect the character.

---

## 2. Ward states

Every regular Ward exists in one of three states:

### Unprimed

The Ward has no active theft history.

It is:

- an ordinary physical item;
- not blessed;
- not tracking thieves.

### Primed

The Ward has begun tracking theft activity.

A Primed regular Ward:

- maintains per-thief-account history;
- receives the 25% / 50% / 100% extra detection progression;
- becomes **character-blessed to its current protected character**;
- remains a physical item;
- is not yet committed to consumption.

If theft activity stops for 30 minutes, a Primed Ward simply resets to Unprimed.

### Activated

A Primed Ward becomes Activated when its detection effect actually detects a theft attempt.

An Activated Ward:

- remains physically present;
- remains character-blessed;
- retains its thief histories;
- continues applying the same per-thief detection mechanics as a Primed Ward;
- continues accepting new thief histories;
- **blocks every thief account it has caught** from attempting theft against the protected character (Section 10);
- does **not** create blanket immunity against thieves it has not caught.

An Activated Ward is consumed after **30 consecutive minutes without a qualifying theft attempt**.

The distinction is therefore:

> **Primed + 30 minutes quiet → reset and retain the Ward.**

> **Activated + 30 minutes quiet → consume the Ward.**

---

## 3. Lazy priming

An Unprimed Ward does not require manual preparation.

It primes automatically when the system first needs to record meaningful theft activity.

Qualifying events are:

1. an otherwise-valid theft attempt that the victim ordinarily detects, including a detected failed attempt; or
2. a successful theft that escapes ordinary victim detection and therefore requires the Ward's additional detection logic.

Events that do **not** prime a Ward include:

- snooping;
- merely opening the backpack;
- login;
- moving the Ward;
- ordinary inventory management;
- an invalid theft target;
- an interrupted theft;
- an undetected failed theft.

---

## 4. Selecting the active Ward

A character may carry multiple Backpack Wards.

However:

> **Only one Ward belonging to that character may be Primed or Activated at a time.**

When qualifying theft activity occurs:

1. If an Activated Ward exists, use it.
2. Otherwise, if a Primed Ward exists, use it.
3. Otherwise, select one eligible Unprimed Ward deterministically.
4. Prime that exact physical item.

A deterministic selection such as lowest stable item serial should be used.

Spare Wards remain Unprimed.

Inventory rearrangement cannot switch which Ward is active.

Multiple Wards cannot:

- contribute detection rolls simultaneously;
- combine thief histories;
- extend one another's timers;
- chain together automatically.

---

## 5. Ward visibility

The item's visible properties should reflect its state:

- `Backpack Ward — Unprimed`
- `Backpack Ward — Primed`
- `Backpack Ward — Activated`

The owner should be able to inspect:

- current Ward state;
- whether the Ward is currently eligible in the equipped backpack;
- remaining inactivity time for Primed or Activated state.

Do not display thief identities or counters.

A snooper may see:

- that the Ward exists;
- whether it is Unprimed, Primed or Activated.

A snooper may **not** see:

- which thief accounts are tracked;
- individual successful-theft counts;
- remaining detection progression for another thief.

---

## 6. Ordinary theft resolves first

A Ward never prevents or reverses the theft attempt that causes its detection effect to occur. It does block that thief's later attempts (Section 10).

The order is:

### Step 1 — Validate the theft

Check ordinary:

- range;
- target eligibility;
- item eligibility;
- inventory state;
- cooldown;
- theft-permitting region;
- whether the thief's account has been **caught** by the target character's Activated Ward (Section 10). If it has, reject the attempt before resolution.

Reject the attempt before resolution where stealing is prohibited, including:

- mapped bank theft-protection regions;
- the active Cool Dungeon;
- any other explicitly configured no-Stealing region.

Revalidate region legality at commit.

### Step 2 — Resolve ordinary Stealing

Resolve:

- ordinary success/failure;
- ordinary victim detection;
- existing witness/criminal/guard rules.

The Ward does not alter the normal Stealing skill check.

If the theft succeeds, transfer the item normally before Ward detection processing.

A thief whose triggering theft succeeds **keeps the stolen item**, even if the Ward detects them afterward.

---

## 7. Ordinary victim detection

If the victim detects the attempt through the normal theft system:

1. resolve the theft attempt normally;
2. acquire the existing Primed/Activated Ward or lazily prime one;
3. record the thief account as Ward history if necessary;
4. transition the Ward to **Activated**;
5. if the detected theft was a **success**, mark the thief account as **caught** (Section 10).

This includes:

- detected successful thefts;
- detected failed thefts.

A failed theft does not increment the thief's successful-theft count. A detected **failed** attempt activates the Ward but does **not** make the thief caught, so it does not block that thief.

Bystander-only detection does not activate the Ward.

Ordinary witness, criminality and guard consequences remain independent.

---

## 8. Extra Ward detection

When a theft:

1. successfully transfers an eligible item; and
2. escapes ordinary victim detection;

the Ward performs an additional victim-detection roll.

Progress is stored per:

> **Ward + victim character + thief account**

All characters on the same thief account share the same progression against that victim/Ward.

Separate accounts have independent progression regardless of IP address.

The progression is:

| Successful undetected theft | Additional Ward detection |
|---|---:|
| First | 25% |
| Second | 50% |
| Third | 100% |

The successful theft count increments before the extra roll.

Therefore:

- first successful undetected theft → count 1 → 25%;
- second → count 2 → 50%;
- third → count 3 → guaranteed detection.

If the Ward detects the theft:

- the completed theft remains completed;
- the thief keeps the transferred item;
- the victim is notified;
- ordinary detected-theft consequences apply;
- the Ward transitions to **Activated**;
- the thief account is **caught** and blocked from further attempts against the protected character (Section 10).

If the roll misses:

- the Ward remains Primed or Activated;
- the thief's increased history is retained.

---

## 9. Different thieves

Each thief account has independent history.

Example:

Thief A:

- first successful undetected theft → 25%;
- second → 50%.

Thief B then attempts a successful undetected theft:

- B begins at 25%;
- B does not inherit A's 50% progression.

If A returns:

- A's next successful undetected theft is the third and therefore guaranteed detected.

The Ward therefore targets **repeat behavior by individual thief accounts**, not all thieves collectively. Being caught is also per thief account: catching A blocks A only.

---

## 10. Caught thieves are blocked; there is no universal immunity

A thief account is **caught** by a Ward when one of its **successful** thefts against the protected character is detected, either by ordinary victim detection (Section 7) or by the Ward's extra detection (Section 8). A detected failed attempt does not make a thief caught.

While the Ward is Activated:

- every caught thief account is **blocked** from any theft attempt against the protected character, for **all characters on that account**;
- a blocked attempt is rejected before resolution (Section 6, Step 1): no skill check, no skill gain, no criminality or other consequence, no change to the thief's counters, and it does **not** refresh the inactivity timer (Section 13). The thief is told the attempt is not possible right now;
- the block lasts until the Ward is consumed, which happens after 30 consecutive minutes without a qualifying theft attempt (Section 12). If nothing else happens after the catch, the thief is blocked for 30 minutes from the catch;
- if several thieves are caught, **each is blocked**; the Ward protects against every thief it has caught, not only the first.

A thief the Ward has **not** caught is not blocked. A new thief encountering an Activated Ward starts with their own fresh history (Section 9).

Activation does **not** grant:

- blanket immunity against thieves the Ward has not caught;
- two minutes or thirty minutes of automatic rejection of all new thieves.

This explicitly replaces the previous 120-second all-thief protection mechanic.

For example:

- Friend A deliberately gets caught to activate the Ward.
- A is blocked for the window.
- Stranger B attacks five minutes later. B is **not** blocked, because B has not been caught. B begins their own Ward history normally.

This keeps the incentive to trigger a Ward deliberately before transporting valuable goods small: it blocks only the friend who triggered it, not the thieves you are worried about.

---

## 11. Activated Ward behavior against known thieves

An Activated Ward retains existing thief histories.

- A **caught** thief is blocked (Section 10). Their counter stays as it was.
- A thief **not caught** keeps their counter:
  - count 1 remains at the next 50% stage;
  - count 2 remains at the next guaranteed-detection stage.

Activation does not reset these counters. A thief who reaches a detected successful theft becomes caught and is blocked from then on.

New thieves may also become tracked while the Ward is Activated.

---

## 12. Thirty-minute inactivity model

Both Primed and Activated Wards use a **30-minute rolling inactivity window**.

The purpose is to approximate a coherent:

- dungeon run;
- gathering run;
- town visit;
- travel session;
- other continuous play encounter.

It is not intended to preserve thief history across unrelated sessions indefinitely.

### Primed Ward timeout

If 30 consecutive minutes pass without qualifying Ward theft activity:

- Primed → Unprimed;
- all per-thief history for that protected character is erased;
- temporary character blessing ends;
- the physical Ward remains;
- the Ward is not consumed.

### Activated Ward timeout

If 30 consecutive minutes pass without qualifying Ward theft activity:

- the Activated Ward is consumed;
- all associated history disappears with it.

This makes activation the point at which the consumable has actually "committed" to the theft encounter.

---

## 13. What refreshes the 30-minute timer

Only an otherwise-valid Stealing attempt against an eligible target should refresh the encounter timer.

This can include:

- successful theft;
- failed theft;
- ordinarily detected theft;
- Ward-detected theft.

It should **not** include:

- snooping;
- invalid Stealing targets;
- attempts while out of range;
- attempts blocked by protected-region rules;
- attempting to steal the Ward itself;
- an attempt rejected because the thief is blocked by this Ward (Section 10);
- spammed invalid targets;
- merely targeting the player;
- login/logout;
- movement;
- combat;
- opening containers.

The intent is:

> A thief can keep an encounter active by continuing to make genuine theft attempts, but cannot keep a Ward permanently active using trivial invalid actions.

---

## 14. Blessing rules

### Regular Ward

An **Unprimed regular Ward is not blessed**.

Once the Ward becomes Primed:

> It becomes character-blessed to the currently protected character.

It remains character-blessed while:

- Primed; or
- Activated.

The temporary blessing prevents unrelated death or corpse looting from destroying the theft-history state during an active encounter.

If the Primed Ward resets to Unprimed after 30 minutes:

- blessing is removed.

If an Activated Ward times out:

- the Ward is consumed.

---

## 15. Transfer to another character

If a Primed or Activated regular Ward enters another character's possession:

> **It immediately resets completely.**

Specifically:

- state becomes Unprimed;
- character blessing is removed;
- all previous thief histories are erased;
- prior victim association is erased;
- previous inactivity state is erased.

This applies even if the receiving character is:

- on the same account;
- an alternate character belonging to the same player.

The Ward does not restore old history if later returned to its former owner.

Once ownership changes, that history is gone permanently.

This keeps Ward state associated with:

> **this physical Ward protecting this character during this encounter**

rather than turning the item itself into a transferable database of old theft relationships.

---

## 16. Moving a Ward without transferring ownership

Inventory movement belonging to the same character does not reset the Ward.

Examples:

- moving between nested bags in the equipped backpack;
- changing organization pouches;
- replacing the backpack;
- temporarily moving the Ward elsewhere in the same character's possession.

If a Primed or Activated Ward leaves the equipped backpack:

- its theft-protection eligibility is suspended;
- its existing state remains;
- its 30-minute inactivity timer continues running.

If returned before timeout:

- its prior state resumes.

A player therefore cannot reset counters by taking the Ward out and putting it back.

---

## 17. Death behavior

### Regular Unprimed Ward

Uses ordinary item-loss rules.

It may be:

- left on the corpse;
- looted normally;
- transferred normally.

### Regular Primed Ward

Because it is temporarily character-blessed:

- it remains with its protected character through death;
- thief history survives;
- its inactivity timer continues.

### Regular Activated Ward

Also remains character-blessed.

It remains with the character until:

- consumed after 30 minutes of inactivity; or
- consumed/deleted by another explicit Ward rule if one is later added.

Death does not itself reset or consume it.

---

## 18. Starter-Issued Backpack Ward

Every newly created character receives exactly **one Starter-Issued Backpack Ward**.

It uses all normal Ward mechanics:

- Unprimed;
- Primed;
- Activated;
- 25% / 50% / 100%;
- 30-minute Primed reset;
- 30-minute Activated consumption.

However, its blessing is different.

### Starter Ward blessing

The Starter-Issued Ward is:

> **character-blessed from creation until it is consumed.**

Its blessing does not depend on Primed or Activated state.

Therefore:

- Primed → Unprimed reset does not remove starter blessing;
- death does not destroy it;
- it remains until its normal Ward lifecycle eventually consumes it.

### Starter anti-farming restrictions

The Starter Ward is:

- character-bound;
- unstackable;
- nontradeable;
- nondroppable;
- unbankable;
- unvendorable;
- non-salvageable;
- non-mailable;
- unable to enter pet inventory;
- unable to enter shared containers;
- unable to enter another character's inventory;
- unable to generate economic value.

It may move freely among nested containers inside its owner's equipped backpack.

It is granted exactly once.

It is not replaced through:

- death;
- resurrection;
- relogging;
- deleting/recreating a starter package;
- other entitlement manipulation.

Unlike the prior design, an unused Starter Ward is **not destroyed on death**.

---

## 19. Wards themselves cannot be stolen

Backpack Wards cannot themselves be targeted successfully with the Stealing skill.

This applies to:

- Unprimed;
- Primed;
- Activated;
- Starter-Issued Wards.

Normal death/corpse rules still apply to ordinary **Unprimed regular Wards**.

Primed/Activated regular Wards remain with the character because of temporary blessing.

Starter Wards remain because of permanent character binding/blessing.

---

## 20. Criminality and consequences

Ward detection counts as the victim detecting the theft.

Use the game's ordinary consequences for a detected theft.

The Ward itself does not directly:

- stun;
- damage;
- paralyze;
- kill;
- assign murderer status;
- confiscate the stolen item.

If a theft succeeded before detection:

> The thief keeps the stolen item.

The normal criminal/notoriety/aggression/guard systems determine all subsequent consequences.

---

## 21. Region boundaries

Backpack Wards do not override regions in which player stealing is prohibited.

Attempts must be rejected before theft resolution inside:

- the active Cool Dungeon;
- explicitly mapped bank theft-protection regions;
- any future configured theft-prohibited region.

Snooping remains governed independently.

**Hot Zones.** A Ward has no effect while the protected character is inside a Hot Zone (Fire Island, Buccaneer's Den
island, and since Beta 2a the Hythloth dungeon). There the Ward neither primes, activates, refreshes nor blocks, and a thief who was caught elsewhere
may steal from that character until they leave. The Ward's own clock keeps running meanwhile.

If a valid theft begins outside such a region but either relevant participant crosses into a protected region before commit:

- revalidate;
- reject the transfer.

A region transition does not erase existing criminal/aggression rights.

---

## 22. Persistence

Persist enough information to survive:

- logout;
- server restart;
- world save;
- backpack replacement;
- container rearrangement;
- region transitions.

For each active Ward, persist:

- stable Ward item identity;
- current state: Unprimed / Primed / Activated;
- current protected character identity;
- temporary blessing association;
- last qualifying Ward activity UTC timestamp;
- per-thief-account successful-undetected-theft counts;
- which thief accounts the Ward has **caught** (so blocks survive logout and restart).

Suggested conceptual key:

`(WardId, VictimCharacterId, ThiefAccountId) -> (SuccessfulUndetectedCount, Caught)`

A block ends only when the Ward is consumed, or reset by a transfer.

Transfer to another character explicitly deletes/reset this state as described above.

---

## 23. Atomic theft resolution

Ward processing must be serialized per victim.

The following operations should behave atomically:

1. validate theft, including the caught-thief block;
2. choose existing Ward or prime one;
3. perform ordinary Stealing;
4. transfer item if successful;
5. perform ordinary detection;
6. update thief history;
7. perform Ward detection;
8. transition Primed → Activated when applicable, and mark the thief caught when a successful theft was detected;
9. refresh inactivity timestamp.

Two simultaneous thieves must not:

- prime two different spare Wards;
- overwrite one another's histories;
- perform duplicate detection rolls;
- create inconsistent state.

---

## 24. Important examples

### Example A — isolated theft

Alice carries one regular Unprimed Ward.

Bob successfully steals an item and escapes ordinary detection.

- Ward becomes Primed.
- Bob count = 1.
- Ward rolls 25%.
- Roll misses.
- Alice loses the item.
- Ward becomes temporarily blessed.

Nothing else happens.

Thirty minutes later:

- Ward resets to Unprimed.
- Bob's history disappears.
- blessing is removed.
- Alice still owns the Ward.

### Example B — repeated thief

Bob steals successfully:

- Bob = 1 → 25% misses.

Ten minutes later:

- Bob steals again.
- Bob = 2 → 50% misses.

Ten minutes later:

- Bob steals again.
- Bob = 3 → 100%.

The third theft completes first.

Then:

- Alice detects Bob;
- Bob keeps the third stolen item;
- ordinary criminal rules apply;
- Ward transitions to Activated;
- Bob is **caught**: every later theft attempt by Bob (any character on his account) is rejected until the Ward is consumed.

### Example C — Activated Ward and a new thief

Alice's Ward is Activated because Bob was caught.

Carol attempts theft.

Carol has no history and has not been caught, so her attempt is allowed and resolves normally.

If Carol successfully steals undetected:

- Carol = 1;
- Carol receives the normal 25% Ward detection roll.

If Carol is then detected, Carol is caught and blocked too. Carol is **not** blocked merely because Bob was caught.

### Example D — deliberate friend activation

Alice is transporting valuable goods.

Her friend Bob deliberately gets himself detected on a successful theft to activate the Ward.

This blocks Bob, and only Bob. A real thief, Carol:

- can still steal;
- begins with her own fresh history;
- receives only the normal Ward progression applicable to her.

Therefore deliberate activation offers little exploitable transport advantage.

### Example E — Primed inactivity

Bob steals once at 7:00 PM and is not detected.

No valid theft attempt occurs afterward.

At 7:30 PM:

- Ward resets to Unprimed;
- Bob's history is deleted;
- regular Ward loses temporary blessing.

Bob returns at 8:00 PM.

His history starts from zero.

### Example F — Activated inactivity

Bob steals successfully at 7:00 PM and Alice detects it.

The Ward becomes Activated and Bob is caught.

Bob tries again at 7:10 PM. The attempt is rejected, and it does not move the Ward's deadline.

No valid theft attempts occur after that.

At 7:30 PM:

- the Activated Ward is consumed;
- Bob's block ends with it.

### Example G — continuing theft episode

The Ward activates at 7:00 PM when Bob is caught.

Carol makes a genuine theft attempt at 7:20 PM.

The Activated Ward's inactivity deadline moves to 7:50 PM.

Bob tries again at 7:40 PM. He is blocked, and the deadline does not move.

Carol makes another genuine attempt at 7:45 PM.

Deadline moves to 8:15 PM.

Bob stays blocked the whole time. Once 30 uninterrupted minutes pass with no valid theft attempt:

- Ward is consumed, and every block ends with it.

### Example G2 — two thieves caught

Bob is caught at 7:00 PM and Carol is caught at 7:12 PM.

Both are blocked, each by their own catch.

Dave, who has not been caught, can still attempt theft and starts at 25%.

### Example H — ownership transfer

Alice has a Primed regular Ward with:

- Bob = 2.

Alice gives the Ward to Carol.

Immediately:

- Primed → Unprimed;
- Bob's history is deleted;
- temporary blessing disappears.

Carol receives an ordinary fresh Ward.

Even if Carol later gives it back to Alice:

- Bob's former history does not return.

---

## 25. Required regression tests

At minimum test:

### Caught thieves

- a thief caught on a detected successful theft (ordinary detection) is blocked.
- a thief caught by the Ward's extra detection is blocked.
- a detected failed attempt activates the Ward but does not block the thief.
- a thief not caught is not blocked, even while the Ward is Activated.
- two caught thieves are each blocked.
- alternate characters on a caught thief account are blocked too.
- a blocked attempt is rejected before resolution: no skill check, no skill gain, no criminality, no counter change.
- a blocked attempt does not refresh the inactivity timer.
- blocks survive logout, world save and restart.
- consuming the Ward ends every block.
- transfer of the Ward to another character resets the caught list.

### State transitions

- Unprimed → Primed.
- Primed → Unprimed after 30 minutes inactivity.
- Primed → Activated after Ward detection.
- Activated → consumed after 30 minutes inactivity.

### Detection

- first successful undetected theft = 25%.
- second = 50%.
- third = 100%.
- different thief starts independently.
- alternate characters on same thief account share history.

### Timer behavior

- valid theft attempt refreshes timer.
- snooping does not.
- invalid theft spam does not.
- region-blocked attempts do not.
- logout does not reset timer.
- restart preserves absolute timing.

### Blessing

- regular Unprimed Ward is ordinary.
- regular Primed Ward survives death.
- regular Activated Ward survives death.
- Primed reset removes blessing.
- ownership transfer removes blessing.
- Starter Ward remains blessed while Unprimed.

### Transfer

- same-character nested movement preserves state.
- temporary removal from equipped backpack preserves state but suspends eligibility.
- different-character transfer resets all state.
- same-account alt transfer also resets all state.
- return to former owner does not restore deleted history.

### Concurrency

- only one Ward primes.
- simultaneous thieves cannot select separate Wards.
- counters are atomic.
- no duplicate detection rolls.
- ownership transfer during pending theft cannot preserve invalid state.

### Crime

- triggering successful theft is never reversed.
- thief keeps stolen item.
- ordinary criminality applies.
- Ward adds no stun/damage/murder count.

---

# Final mechanical summary

A player carries a physical Ward.

The Ward begins **Unprimed**.

The first meaningful theft activity causes one Ward to become **Primed**.

It remembers each thief account independently:

- first successful undetected theft: 25% additional detection;
- second: 50%;
- third: guaranteed.

If theft activity ends for 30 minutes while merely Primed:

> **The Ward forgets the encounter and becomes reusable.**

If the Ward actually detects a thief on a successful theft:

> **It becomes Activated, and that thief is caught.**

An Activated Ward blocks every thief it has caught from stealing from the protected character, and continues tracking other thieves exactly as before. It does not provide universal immunity against thieves it has not caught.

Once theft activity has been quiet for 30 minutes:

> **The Activated Ward is consumed.**

Regular Primed/Activated Wards are temporarily character-blessed so death cannot interrupt an ongoing theft encounter. Transfer to another character resets the Ward completely and removes that blessing.

The Starter-Issued Ward uses the same mechanics but remains character-bound and blessed from creation until eventual consumption.
