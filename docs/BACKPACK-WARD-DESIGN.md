# Backpack Ward — Revised Full Design

Status: approved design, supersedes the Backpack Ward design previously inlined in the
[phased roadmap](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md) (Alpha 2, item 4) and the
[alternative plan](ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md) ("Consumable Backpack Wards").
This is now the sole source of truth for Backpack Ward mechanics; do not redefine them elsewhere —
reference this document instead. It does not cover the separate **Invisible Loot Protection Ward**
(monster-corpse anti-harassment), which remains defined in the alternative plan.

The most significant change from the prior design: the previous **120-second all-thief victim
immunity** on Ward trigger is replaced by a **Primed / Activated** per-thief state machine (Sections
2, 10) that keeps tracking known thieves without granting blanket protection against unrelated ones.

## Consumable Backpack Wards — Theft Detection and Anti-Harassment

### Design intent

Backpack Wards provide prepared players with escalating protection against repeated theft without weakening the underlying Stealing skill or creating blanket immunity from thieves.

The system preserves ordinary era-appropriate:

- Stealing success/failure;
- item eligibility;
- skill investment;
- cooldowns;
- ordinary theft detection;
- criminality;
- guard behavior;
- snooping.

A Ward does **not** reduce a thief's chance to successfully steal an item.

The design does not include:

- Awareness skill;
- reaction or key-sequence minigames;
- special Bless spell interactions;
- special Magic Trap or Magic Untrap behavior;
- theft-triggered stun or damage;
- Wardbreakers;
- universal post-trigger theft immunity.

The central goal is:

> **A Ward remembers and increasingly detects thieves involved in an ongoing theft episode. It does not make the victim globally immune to unrelated thieves.**

---

## 1. Physical Backpack Ward

A normal Backpack Ward is an obtainable physical **single-use consumable**.

It requires:

- no Magery;
- no combat skill;
- no minimum skill level;
- no manual activation.

There are no Ward power tiers.

Its crafting/purchase sources and price should be determined by the economy audit.

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
- does **not** create blanket immunity against all thieves.

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

A Ward never prevents or reverses the theft attempt that causes its detection effect to occur.

The order is:

### Step 1 — Validate the theft

Check ordinary:

- range;
- target eligibility;
- item eligibility;
- inventory state;
- cooldown;
- theft-permitting region.

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
4. transition the Ward to **Activated**.

This includes:

- detected successful thefts;
- detected failed thefts.

A failed theft does not increment the thief's successful-theft count.

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
- the Ward transitions to **Activated**.

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

The Ward therefore targets **repeat behavior by individual thief accounts**, not all thieves collectively.

---

## 10. Activated Wards do not create universal immunity

Activation does **not** grant:

- two minutes of blanket immunity;
- thirty minutes of blanket immunity;
- automatic rejection of all new thieves.

This explicitly replaces the previous 120-second all-thief protection mechanic.

An Activated Ward handles subsequent theft attempts using the **same underlying rules as a Primed Ward**.

That means an unrelated thief encountering an Activated Ward for the first time starts with their own fresh history.

For example:

- Friend A deliberately activates the Ward.
- Stranger B attacks five minutes later.
- Stranger B does **not** encounter universal theft immunity.
- B begins their own Ward history normally.

This eliminates the incentive to intentionally trigger a Ward before transporting valuable goods.

---

## 11. Activated Ward behavior against known thieves

An Activated Ward retains existing thief histories.

A thief already at:

- count 1 remains at the next 50% stage;
- count 2 remains at the next guaranteed-detection stage.

Activation does not reset these counters.

The Ward therefore continues to provide escalating protection against thieves already involved in the encounter.

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
- per-thief-account successful-undetected-theft counts.

Suggested conceptual key:

`(WardId, VictimCharacterId, ThiefAccountId) -> SuccessfulUndetectedCount`

Transfer to another character explicitly deletes/reset this state as described above.

---

## 23. Atomic theft resolution

Ward processing must be serialized per victim.

The following operations should behave atomically:

1. validate theft;
2. choose existing Ward or prime one;
3. perform ordinary Stealing;
4. transfer item if successful;
5. perform ordinary detection;
6. update thief history;
7. perform Ward detection;
8. transition Primed → Activated when applicable;
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
- Ward transitions to Activated.

### Example C — Activated Ward and a new thief

Alice's Ward is Activated because of Bob.

Carol attempts theft.

Carol has no history.

If Carol successfully steals undetected:

- Carol = 1;
- Carol receives the normal 25% Ward detection roll.

Carol is **not automatically blocked** merely because Bob activated the Ward.

### Example D — deliberate friend activation

Alice is transporting valuable goods.

Her friend Bob deliberately gets himself detected to activate the Ward.

This gives Alice no blanket protection.

A real thief, Carol:

- can still steal;
- begins with her own fresh history;
- receives only the normal Ward progression applicable to her.

Therefore deliberate activation offers little exploitable transport advantage.

### Example E — Primed inactivity

Bob steals once at 7:00 PM.

No valid theft attempt occurs afterward.

At 7:30 PM:

- Ward resets to Unprimed;
- Bob's history is deleted;
- regular Ward loses temporary blessing.

Bob returns at 8:00 PM.

His history starts from zero.

### Example F — Activated inactivity

Bob triggers detection at 7:00 PM.

Ward becomes Activated.

No valid theft attempts occur after that.

At 7:30 PM:

- the Activated Ward is consumed.

### Example G — continuing theft episode

Ward activates at 7:00 PM.

A genuine theft attempt occurs at 7:20 PM.

The Activated Ward's inactivity deadline moves to 7:50 PM.

Another genuine attempt happens at 7:45 PM.

Deadline moves to 8:15 PM.

Once 30 uninterrupted minutes pass with no valid theft attempt:

- Ward is consumed.

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

If the Ward actually detects a thief:

> **It becomes Activated.**

An Activated Ward continues tracking thieves exactly as before. It does not provide universal immunity.

Once theft activity has been quiet for 30 minutes:

> **The Activated Ward is consumed.**

Regular Primed/Activated Wards are temporarily character-blessed so death cannot interrupt an ongoing theft encounter. Transfer to another character resets the Ward completely and removes that blessing.

The Starter-Issued Ward uses the same mechanics but remains character-bound and blessed from creation until eventual consumption.
