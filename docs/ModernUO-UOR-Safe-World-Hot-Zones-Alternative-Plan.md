# ModernUO UOR Safe-World / PvP Hot-Zones Alternative Implementation Plan

## Objective

This is a **separate alternative shard design** derived from the main UOR implementation plan. It must not overwrite or silently modify the canonical Felucca-first plan.

Keep the same core gameplay mechanics and Classic+ decisions unless this document explicitly overrides them:

- **UOR expansion/platform baseline with T2A-style insta-hit and precasting, no weapon or Wrestling specials, and selected passive UOR mechanics** (Section 4)
- Felucca map only, including the Lost Lands
- 700 skill cap / 225 stat cap
- pre-AoS itemization
- no insurance
- accelerated-but-capped skill gain
- blessed runebooks
- unblessed/stealable keys with recoverable property ownership
- no combat pets in dungeons
- restricted pet PvP
- era-appropriate stealing and ordinary crime plus the approved voluntary `[Intent]` PvP system and cumulative 24-hour murder/red-status rules (Sections 3 and 14); housing, boats, crafting and economy remain classic
- no mandatory vertical progression systems
- phased, concentrated normal-cost residential housing around Britain, with optional higher-cost rural placement
- one rotating outdoor Expedition Region and physical trade route to make roads/wilderness socially relevant without permanently spreading players across the map

### Shard identity and design thesis

This shard should occupy a deliberate space between three common UO freeshard directions:

1. **Classic Felucca/Renaissance shards** that preserve UOR mechanics but expose ordinary PvE players to unsolicited open-world blue-on-blue PvP almost everywhere.
2. **PvE-safe shards** that remove most involuntary PvP but also adopt large parts of modern UO: later expansions, modern itemization, Power Scroll-style progression, artifacts, advanced pet systems and other post-UOR mechanics.
3. **Heavily customized Classic+ shards** that solve retention through custom maps and long-running vertical power systems such as expanded skill caps, pet leveling, permanent mastery trees, aspects/codices or increasingly powerful equipment.

This design intentionally chooses a fourth approach:

> **Classic pre-AoS UO built on a UOR-era platform, with T2A-style combat timing and no special attacks, for players who still want thieves, murderers, full loot, dangerous places and real PvP without involuntary blue-on-blue combat during ordinary PvE.**

The shard should feel recognizable to pre-AoS UO players: select UOR as the global **engine/feature baseline**, but make the Section 4 hybrid combat rules authoritative over stock UOR combat. Change the **geography, synchronization and social structure of activity** without silently changing the combat rules.

#### Pillar 1 — Preserve the Classic UO power ceiling

The era/feature foundation remains UOR; the deliberately hybrid combat exceptions are specified in Section 4:

- 700 total skill cap
- 100.0 ordinary individual skill cap
- 225 stat cap
- pre-AoS itemization
- no insurance
- no AoS resistance/property treadmill
- no mandatory 110/115/120 skill progression
- no permanent Aspect/Codex/mastery-style damage ladder
- no pet-leveling endgame
- no continually escalating combat-item tiers

Characters should become viable substantially faster than historical OSI UO, but the destination remains a **classic completed character**, not an endlessly advancing one.

Core progression principle:

> **A character can eventually finish becoming stronger. The player's life in Britannia should not finish with it.**

Long-term retention should therefore come primarily from:

- difficult PvE encounters
- collections and rare hunting
- crafting and commerce
- housing and visible wealth
- exploration
- Adventure-Ledger/achievement-style mastery if implemented
- social reputation
- titles and prestige
- cosmetics and decorations
- rotating world activity
- optional PvP

Do not solve an endgame-content shortage by silently raising the permanent character-power ceiling.

#### Pillar 2 — Safe-by-default does not mean Trammelized

The shard deliberately protects an innocent player from unsolicited direct blue-on-blue attack through most of Britannia.

It does **not** remove the criminal sandbox.

Throughout the safe world:

- stealing remains **except inside the active Cool Dungeon and explicitly mapped bank theft-protection regions**
- snooping remains everywhere, including the Cool Dungeon
- corpse-right/criminal consequences remain, with only a time-limited per-offender Loot Protection Ward restriction after actual unlawful monster-corpse looting in non-Hot regions
- stolen keys and burglary risk remain where era-appropriate
- criminals/greys remain lawful targets
- murderers/reds remain lawful targets
- existing lawful aggression may continue
- consensual conflict remains possible through the blue-only `[Intent]` toggle, approved guild wars and other explicitly supported systems

Meanwhile, permanent and rotating Hot Zones preserve real Felucca combat:

- unrestricted player-versus-player hostility within the Hot rules
- full item loss under classic death/corpse rules
- genuine theft/criminality remains meaningful; the Section 14 automatic murder-count and 24-hour cumulative-red policy supersedes stock UOR murder reporting/threshold/decay
- meaningful risk premiums
- no artificial arena-only replacement for dangerous world PvP

The identity distinction is therefore:

> **Protection from arbitrary murder, not protection from consequence, crime or danger.**

A safe-world player should still feel that they are playing on **Felucca**, not on a separate consequence-free PvE facet.

#### Pillar 3 — A large world to explore, but a small world to be active in

Classic Britannia is physically too large to feel consistently populated at modest freeshard concurrency if every town, dungeon and wilderness region is treated as equally important at all times.

Do **not** attempt to solve that by permanently placing equivalent bonus content everywhere. That would spread players even farther apart.

Instead:

> **Keep Britannia large, but deliberately concentrate social and economic relevance into a small number of predictable places at any given time.**

The active-world structure should include:

- **Britain / Greater Britain** as the permanent residential, vendor and social capital
- **Hythloth + Fire Island** as a permanent high-risk PvE/PvP cluster
- **Buccaneer's Den** as a permanent public criminal/PvP social cluster
- **one rotating Hot Dungeon** for weekly high-risk convergence
- **one rotating Cool Dungeon** for weekly safe-PvE convergence
- **one rotating Expedition Region** for weekly wilderness/resource convergence
- **one Britain-origin trade route** through the Expedition geography
- **one weekly mainland Virtue Pilgrimage**, using timed Britain departures to synchronize physical travel
- **road movement bonuses** so roads function as infrastructure rather than decorative terrain

These systems should overlap geographically where practical.

For example, a Yew-focused week may intentionally combine:

- Britain → Yew Expedition route
- enhanced gathering in the Yew region
- Britain/Yew Expedition Logistics
- Justice Pilgrimage
- ordinary road-speed incentives

This creates visible traffic from gatherers, cargo runners, pilgrims, homeowners, merchants and ordinary travelers in the same broad area.

Inactive regions remain fully usable at normal baseline value. They should not be nerfed merely because another region is active.

The goal is:

> **Players can go anywhere, but they can reliably know where other players are likely to be.**

#### Pillar 4 — Encourage physical-world interaction without making normal travel tedious

Recall, Gate Travel, blessed runebooks, moongates and boats remain important Classic UO conveniences.

The shard should **not** globally cripple fast travel just to make the map appear busier.

Instead, selected activities deliberately make physical travel part of the gameplay:

- Expedition trade cargo cannot use instant magical travel
- Pilgrimage requires physical travel from Britain to the weekly shrine
- ordered broad checkpoints prevent trivial route bypass
- road-speed bonuses reward using the world's existing infrastructure
- Expedition gathering/logistics create reasons to physically haul resources through towns and roads

The principle is:

> **Create rewarding reasons to travel physically; do not punish ordinary players for using classic travel tools outside those activities.**

#### Pillar 5 — Concentration without mandatory participation

Rotating activity bonuses must be strong enough to change player behavior, but ordinary Britannia must remain valid.

Examples:

- Cool Dungeon provides a modest safe-PvE premium rather than replacing ordinary dungeons.
- Expedition Region provides a strong gathering advantage, while inactive wilderness remains at 100% normal yield.
- Hot Dungeon provides materially higher risk/reward, but safe players are not required to enter it for mandatory character-power progression.
- Pilgrimage provides temporary skill-gain acceleration, not a permanent skill-cap increase.
- Rural housing remains available at a premium after Greater Britain fills rather than prohibiting players who genuinely value isolation.

Avoid systems where missing a weekly rotation leaves a character permanently behind.

#### Pillar 6 — Social density is itself a gameplay reward

For a small shard, encountering other players is part of the content.

Design systems should therefore be evaluated not only by gold/hour or mechanical reward, but by whether they create:

- repeated encounters between recognizable players
- visible activity on roads and in towns
- reasons for casual cooperation
- opportunities for commerce
- social rivalries and race recognition
- public houses/vendors worth visiting
- identifiable gathering places
- community stories

Pilgrimage races, Cool Dungeon weeks, Expedition corridors, Britain-centered housing and predictable PvP destinations are all mechanisms for producing **social density**, not isolated feature checklists.

#### Pillar 7 — Horizontal endgame over endless vertical progression

A finished non-PvP character must still have meaningful long-term goals.

The intended PvE endgame direction is:

- handcrafted high-end group PvE encounters
- dungeon/adventure mastery
- rare and collectible hunting
- treasure/exploration systems
- visible housing trophies and decoration
- prestigious crafting and merchant play
- achievement/Adventure-Ledger-style completion
- rotating weekly challenges/activity
- titles, cosmetics and public recognition
- economy participation and wealth sinks

Power rewards should generally remain within normal UOR ceilings.

This allows the shard to provide a long endgame without turning the ruleset into a perpetual RPG-stat treadmill.

#### Product-positioning summary

The design should be explainable succinctly as:

> **Classic pre-AoS Ultima Online: a UOR feature foundation, T2A-style instant-hit combat without specials, safe-by-default adventuring, preserved Felucca crime and full-loot danger, and rotating activity that brings players together.**

Or, internally, the shortest design test is:

> **Classic UO power. Felucca consequences. PvE agency. Concentrated population. A world worth traveling through.**

When evaluating future features, reject or redesign them if they materially undermine one of those identity pillars without an explicit owner decision.

The **major world-rule difference** is:

> **Britannia is safe from unsolicited direct player violence by default, while clearly defined PvP Hot Zones provide unrestricted classic PvP and substantially better rewards.**

The launch PvP geography is intentionally concentrated:

1. **Hythloth is a permanent PvP Hot Dungeon.**
2. **Exactly one additional major dungeon rotates into Hot status each week.**
3. **Fire Island / Isle of Fire is a permanent open-world PvP Hot Zone.**
4. **Buccaneer's Den and the entire Buccaneer's Den island are a permanent open-world PvP Hot Zone.**
5. **Exactly one additional non-PvP dungeon is the Cool Dungeon of the Week**, receiving a modest safe-play reward bonus to concentrate cooperative/casual PvE **and disabling direct player stealing while it is Cool**.
6. Everywhere else is safe from unsolicited blue-on-blue direct hostility, while **stealing remains enabled except in the active Cool Dungeon and explicitly mapped bank theft-protection regions; snooping remains enabled everywhere** and normal criminal/notoriety consequences remain meaningful. An armed consumable Backpack Ward provides temporary protection only after its first detected theft attempt has resolved.

Because Hythloth is located on Fire Island, the permanent island and permanent dungeon form one dense PvE/PvP risk cluster. Buccaneer's Den forms a second permanent criminal/PvP social cluster, while the weekly rotating dungeon forms the main temporary high-reward PvP destination elsewhere in Britannia.

The intended result is:

**UOR expansion/feature baseline + T2A-style insta-hit/precasting without weapon or Wrestling specials + selected passive UOR improvements + safe-by-default Britannia + preserved thieving/criminality + rotating Cool Dungeon + concentrated full-loot Hot Zones + classic pre-AoS itemization.**

The implementation should favor:

**configuration > shard-specific extension/content code > narrowly scoped changes to existing UOContent > core/server changes only as a last resort.**

Avoid unnecessary forks of ModernUO internals.

### ModernUO extension, add-on and reuse policy

Treat **vanilla ModernUO + UOContent** as the stable baseline, but do not assume every shard feature should be implemented by directly editing the vanilla repository.

ModernUO supports separately compiled content/extension assemblies, and this should be the preferred home for shard-specific systems whenever the existing APIs expose a clean hook.

Implementation policy:

1. **Start with configuration.**  
   If the desired behavior can be achieved through existing era flags, configuration, region definitions, loot tables, spawner definitions or other data-driven mechanisms, use those first.

2. **Audit reusable ModernUO components before writing new code.**  
   Before implementing a major system, check:
   - the official ModernUO script/drop-in repositories;
   - separate ModernUO projects such as spawner/content utilities where relevant;
   - existing UOContent implementations that can be extended or composed rather than copied;
   - reputable RunUO/ServUO implementations as reference material.

3. **Prefer shard-specific assemblies for custom systems.**  
   Systems that can be cleanly isolated should live in their own shard-owned content/extension projects rather than being scattered through upstream source.

   Strong candidates include:
   - Hot/Cool/Expedition/Pilgrimage rotation managers;
   - custom items, NPCs, rewards and activity boards;
   - starter entitlements and account-level shard state;
   - administrative commands and diagnostics;
   - housing-district logic where region/content hooks are sufficient;
   - custom crafting/itemization layers where existing crafting hooks permit it;
   - events, collectibles and other Classic+ content.

4. **Treat old RunUO/ServUO scripts as ports, not drop-in plugins.**  
   The shared lineage makes them valuable references, but compatibility must never be assumed.  
   Any reused code must be audited for:
   - API differences;
   - serialization differences;
   - namespace/type changes;
   - lifecycle/event-hook differences;
   - obsolete era assumptions;
   - unsafe threading/timer patterns;
   - incompatibility with current ModernUO source generation/build structure.

5. **Modify UOContent narrowly when the rule belongs inside an existing gameplay system.**  
   If a system such as crafting, combat, notoriety, pets or spellcasting lacks a clean extension hook, make the smallest well-documented UOContent change necessary rather than duplicating the entire upstream subsystem.

6. **Modify ModernUO core/server only when genuinely unavoidable.**  
   Core changes are appropriate only when the required behavior cannot reasonably be implemented in configuration, content code, an extension assembly or a narrowly scoped UOContent change.

   Likely examples requiring deeper audit include:
   - central hostile-action authorization;
   - movement timing / road-speed support;
   - low-level combat hit/damage hooks;
   - serialization/account-state capabilities not exposed to content;
   - other engine-level behavior without a usable extension point.

7. **Keep upstream divergence measurable.**  
   Every direct UOContent/core modification should have:
   - a documented reason;
   - the upstream file(s) changed;
   - a description of why an extension was insufficient;
   - regression tests;
   - notes for rebasing onto future ModernUO updates.

8. **Do not install third-party code merely because it exists.**  
   Reusable code must be evaluated against this shard's UOR era, security model, performance expectations and design identity.  
   Prefer small, understandable dependencies over large script packs that introduce unrelated mechanics.

9. **Preserve ownership of shard-specific design.**  
   Reusing an add-on should not force the shard to adopt that add-on's gameplay assumptions. Adapt reusable infrastructure to this design rather than changing shard rules simply to match an existing script.

10. **Perform the reuse audit before implementation estimates.**  
    For each major feature, the agent/developer should first classify it as:
    - existing configuration;
    - reusable ModernUO component/drop-in;
    - adaptable RunUO/ServUO reference;
    - new shard-specific extension;
    - narrow UOContent modification;
    - core/server modification.

This hierarchy is both an engineering and maintenance requirement:

> **Use upstream ModernUO as the platform, keep custom gameplay modular, reuse proven code where it genuinely fits, and minimize the permanent fork surface.**

### Classic+ mechanical philosophy

Preserve recognizable UO mechanics while changing **where unsolicited violence is legal**, not turning the game into a consequence-free PvE world.

The world should support three distinct player experiences simultaneously:

- **Safe adventuring:** ordinary PvE, crafting, housing, travel and exploration without unsolicited blue-on-blue attack.
- **Criminal sandbox:** stealing, snooping, burglary/key risk and corpse-right interactions remain broadly preserved; direct player stealing is disabled only in the active Cool Dungeon and explicitly mapped bank theft-protection regions, and prepared players may trigger temporary Backpack Ward protection after a detected attempt. An invisible, persistent Loot Protection Ward prevents repeat unlawful monster-corpse looting by the same offender for a finite period after their first completed offense outside Hot Zones. Snooping and ordinary notoriety/aggression consequences remain.
- **High-risk PvP:** Hot Zones provide unrestricted classic PvP, full-loot danger and materially better economic opportunity.

Core design principle:

> **Safe does not mean crime-free. Safe means an innocent player cannot be attacked without first entering a PvP Hot Zone or becoming a lawful hostile target through the notoriety/aggression system.**

Mechanical/tuning changes retained from the main plan:

- accelerate skill gain substantially relative to historical OSI rates while keeping the 700 total / 100 individual skill caps
- make characters become viable quickly through 90, make 90–95 the final conventional training push, and move 95–100 into the 14-active-day Mastery system
- keep crafting and especially taming slower than ordinary combat/mage skills **before 95** because they create significant economic/PvM power; all enabled skills use the shared Mastery rules at 95+ unless explicitly approved otherwise
- keep blessed runebooks
- reconsider pet bonding only as a restricted convenience mechanic
- evaluate BODs positively as a crafter activity loop rather than defaulting them off
- evaluate narrow PvM-only dexxer/archery/parry improvements **after** measuring the approved UOR-platform/T2A-timing hybrid against tank mages, conventional warriors and bards in PvM
- keep all dungeon monster spawn counts and normal respawn cadence unchanged merely because a dungeon is Hot; **risk bonuses must not make the PvE encounter itself harder through rapid respawn**

Do not introduce AoS-style itemization, permanent damage trees, Aspect/Codex-style character power progression, insurance, soulbound combat gear, mandatory dailies, battle-pass systems or other vertical retention mechanics.

---

## 1. Ruleset Decisions Already Made

Treat these as requirements unless a technical conflict is discovered.

### Era

Target:

**Expansion.UOR / Renaissance**

ModernUO's current expansion enum identifies UOR as expansion ID `2`.

Do not implement:

- AoS combat
- AoS item attributes
- elemental damage/resistance system
- insurance
- Chivalry
- Necromancy
- Bushido
- Ninjitsu
- post-UOR artifacts
- post-UOR crafting systems
- post-UOR monsters unless explicitly added later
- later pet training/progression systems

Use `Core.UOR`, `Core.AOS`, etc. where era checks are required rather than duplicating era comparisons.

---

## 2. World Configuration

The playable world should initially contain:

**Felucca only.**

Felucca includes Britannia and the T2A Lost Lands appropriate to the UOR mechanical baseline.

Disable access to:

- Trammel
- Ilshenar
- Malas
- Tokuno
- Ter Mur
- any other post-UOR facets

Do not create a second safe facet. The safe-world rules in this plan are **region/action policy applied to Felucca itself**, so housing, economy, travel, stealing, criminality and Hot Zones all coexist on one recognizable map.

Configure `expansion.json` for:

- UOR expansion
- Felucca map enabled
- all other facets disabled

Before modifying the file, inspect the exact `expansion.json` schema used by the current ModernUO checkout.

Validate that:

- characters log into Felucca
- Recall/Gate/Moongate systems cannot accidentally reach disabled facets
- staff commands do not reveal normal-player access routes into disabled facets
- spawners and world-generation systems do not depend on disabled facets
- safe-world policy is not implemented by enabling Trammel
- region changes between safe and Hot areas work on the same Felucca facet

---

## 3. Safe-By-Default Britannia, Crime Broadly Preserved, PvP Hot Zones

This plan changes the geography of unsolicited PvP, retains actual theft/criminal/guard mechanics, and **replaces stock UOR murderer thresholds, reporting and decay with the approved voluntary `[Intent]` and cumulative-red rules in Sections 3 and 14**. The optional **Hot-Zone Skill Veteran** title uses the same server-authoritative Hot-area classification with stricter outdoors/no-house/no-boat rules in Section 5.1; it does not modify PvP legality.

### Safe-world default

Outside configured PvP Hot Zones, an ordinary innocent blue may not initiate a harmful action against another **ordinary innocent blue**. A voluntary grey `[Intent]` player is *not* an ordinary protected blue for hostility purposes: anyone may initiate against them, but they do not gain permission to initiate against unrelated ordinary blues. Real criminals/greys and murderer/reds remain freely attackable; an existing opponent-specific lawful fight can continue. See the complete permission and murder matrix below.

Block at minimum:

- direct melee attacks
- ranged weapon attacks
- harmful spells
- player-targeted poison
- explosion potions and other attributable damaging consumables
- player-created harmful fields affecting otherwise protected innocents
- direct harmful barding/player-target mechanics
- player-created traps or damaging objects when attribution is known
- controlled-pet attacks against targets that are not independently legal under the pet policy
- other custom hostile actions added later

Where practical, reject an illegal action before consuming mana, reagents, ammunition or consumables.

**Do not disable PvP globally at the engine level** if doing so would also break Hot Zones, criminal retaliation, guild wars or other legal aggression. Implement a centralized legality check that evaluates target notoriety, active aggression relationships, consensual-war status and Hot-Zone membership.

### What remains legal broadly across Felucca

The safe world is not a no-conflict world.

The following remain active throughout Felucca unless an explicit rule below says otherwise:

- stealing, **outside Hot Zones except inside the active Cool Dungeon, explicitly mapped bank theft-protection regions and against a character during an activated Backpack Ward; Backpack Wards have no theft-protection effect in Hot Zones**
- snooping everywhere, including the Cool Dungeon
- normal criminal flagging
- normal display for actual criminals/reds; separate grey `[Intent]` display for a voluntarily flagged, otherwise-innocent player
- ordinary guarded-town consequences
- lawful attacks against genuine greys/criminals and voluntary `[Intent]` players
- lawful attacks against reds/murderers
- lawful retaliation against an aggressor
- consensual guild-war combat if era-appropriate and explicitly opted into by both sides
- staff-run consensual duel/tournament systems if enabled
- player housing, vendors, boats and ordinary property rules
- full item loss on death according to the shard's normal death/loot rules

### Thieving broadly preserved; Cool Dungeon and bank exceptions

**Outside PvP Hot Zones, ordinary player stealing is enabled throughout Felucca except inside the active Cool Dungeon, in explicitly mapped bank theft-protection regions, or against a character currently protected by an activated Backpack Ward. In Hot Zones, Backpack Wards do not restrict theft or Knocked-Out looting. Snooping remains enabled everywhere, including those regions.**

The Cool Dungeon remains the one rotating theft-free cooperative PvE region. Bank protection is a separate, narrowly scoped exception expressly approved for this redesign: define clear static bank-premises regions with a surveyed nearby apron rather than a radius following banker NPCs. Do not add any other theft-free towns, shops, wilderness areas, dungeons or safe facets simply because unsolicited combat is restricted. Bank protection blocks **direct player Stealing only**; it must not create a PvP sanctuary in Hot Zones, cleanse criminal/aggression timers, change corpse loot, or prevent otherwise lawful guard/grey/red combat. Reject an attempt if either thief or intended victim is inside the bank protection region when the attempt starts or when item transfer would commit; crossing into a protected bank or Cool Dungeon before completion cancels the attempt without moving an item. Snooping is still allowed.


Inside the active Cool Dungeon:

- attempts to use the Stealing skill against player-carried items must be rejected before item transfer or criminal flagging;
- snooping remains allowed;
- ordinary corpse ownership, legitimate rights and rights-expiration rules remain; the narrowly scoped Loot Protection Ward may block repeated **unauthorized monster-corpse transfers by a previously recorded offender**, including while this dungeon is Cool;
- existing criminal, grey, murderer and aggression states remain fully meaningful;
- a thief who committed a crime before entering remains a lawful target according to normal timers;
- leaving the Cool Dungeon immediately restores ordinary stealing eligibility, subject to bank-region and activated-Ward restrictions.

Use normal UOR stealing consequences:

- a thief who commits a criminal theft becomes grey/criminal as appropriate
- any blue who is legally allowed to attack that criminal may do so even in an otherwise safe region
- the criminal may defend themselves against lawful attackers through the normal aggression relationship
- lawful criminal combat must remain legal until the underlying criminal/aggression timers say otherwise
- helping/healing a criminal should use normal UOR notoriety consequences rather than a special safe-zone exemption
- town guards continue to respond according to era-appropriate rules

Safe-world protection must never prevent lawful enforcement against a thief.

### Consumable Backpack Wards — theft detection and anti-harassment

**Approved launch design; replaces the previously discussed Awareness skill and any proposed special Bless, Magic Trap or Magic Untrap stealing behavior.** Do not create Awareness, a reaction/key-sequence minigame, an anti-theft Bless buff, a theft-triggered stun or a Wardbreaker. Existing spells retain their ordinary era-appropriate behavior independently of this feature. Preserve the stock/era-appropriate Stealing success check, item eligibility, skill investment, cooldown, standard theft detection, criminality and guard rules, except for the explicit bank/Cool/Ward restrictions in this section. The Ward does not boost its holder's Stealing-defense skill or change item-transfer success.

**Physical item, perpetual dormancy and preparation**

- A Backpack Ward is an obtainable physical **single-use consumable** requiring no Magery, combat skill or other skill. Its acquisition/crafting sources and price require an economy audit; do not create Ward tiers or character-power progression.
- A Ward is eligible by its physical presence in the character's equipped paperdoll backpack or any nested container, with **no dormant expiration timer, no manual activation, and no consumption on insertion**. An unused Ward initially has `Unprimed` item state. It becomes `Primed` **lazily when the system first needs to record Ward activity for the victim**: either an ordinarily victim-detected, fully resolved theft attempt (including a detected failure), or an ordinarily undetected successful transfer requiring a per-thief counter increment/extra roll. An undetected failed attempt, snooping, merely carrying/moving the item, login and expiration of previous protection do not prime anything. The selected physical Ward is consumed **only if its detection effect triggers**, after the attempt resolves. A Ward outside the equipped backpack (bank, house, ground, corpse, pet pack) does not protect the bearer; moving the *same item* out and back must not erase its prior per-thief history.
- At a qualifying activity event, **acquire an eligible already-primed Ward first**. If none exists, choose one eligible unprimed Ward deterministically (e.g., lowest stable item serial), change that exact item to `Primed`, and immediately use it for this event. Preserve a victim-associated selected-item reference while eligible so inventory rearrangement cannot switch the active Ward or reset counters. Only **one eligible Ward per character may be primed**; spare Wards remain unprimed and cannot contribute rolls or consume together. Do not prime another Ward simply because the first was consumed or because its two-minute protection ended: the next unprotected *qualifying theft activity* primes the next eligible spare. Do not chain Wards during existing protection or stack/extend its timer. Each Ward is a separate persistent physical item; no stacking/merging item identities or per-thief histories.
- A Ward's `Primed` state is visible in its item name/single-click properties (`Backpack Ward — Primed` versus `Backpack Ward — Unprimed`), using stock-client-compatible item properties; backpack owner status also reports whether a Ward is primed and any **active** protection time remaining, never a dormant countdown. A snooper may see the carried Ward and its visible primed/unprimed state, but never per-thief counters or identities. Wards cannot themselves be stolen/removed with Stealing, though ordinary corpse/death looting still applies; they are not blessed or insured. When a primed Ward leaves a character's equipped backpack, suspend its eligibility. If it returns to the same character, recover its recorded history; if another Ward was primed in the meantime, maintain at most one eligible primed Ward by retaining the existing selected item and rendering the returning item unprimed **without deleting its historical counters**. Transfer to a different character never imports the prior victim's counters as that character's progress.

**Attempt order — the activating theft is never prevented or reversed**

1. Validate range, item eligibility, inventory, normal skill cooldown and theft-permitting regions; reject before item transfer if the active Cool Dungeon, mapped bank protection or already-activated Ward protection applies. Revalidate at commit.
2. Resolve ordinary Stealing success/failure and ordinary victim detection. A dormant Ward never alters the success check or prevents its triggering attempt. Complete any legitimate item transfer before Ward activation; a detected successful thief retains the stolen item.
3. Once the ordinary outcome resolves, if the **victim** ordinarily detected this attempt, atomically acquire the currently primed eligible Ward or lazily prime one if available; trigger/consume that Ward immediately. This includes a detected *failed* theft without advancing the successful-theft count. If there is no eligible Ward, preserve ordinary detection without a Ward effect. Bystander-only detection does not cause priming/activation; ordinary independent witness/crime consequences remain.
4. Only after a **successful item transfer** that escaped ordinary victim detection, acquire the currently primed eligible Ward or lazily prime one if available. If found, increment the success count **for that thief's stable account identity on this particular Ward, for this victim**, then perform exactly one extra victim-detection roll: that thief's first success **25%**, second **50%**, third **100% (guaranteed)**. If the roll detects the attempt, notify the victim and trigger/consume that Ward **after** item transfer. No eligible Ward means no extra roll. Do not roll after ordinarily detected transfers or on failures. Different characters on the thief's account share a counter; different accounts do not, regardless of IP.
5. A success that escapes all detection leaves its selected Ward primed with the incremented counter. Undetected *failed* attempts do **not** prime a Ward, advance counts or receive an extra roll. **Three successful thefts guarantees detection per thief account per Ward/victim**, not against all cooperating thieves globally. A new thief starts at 25% even when a different thief's count is already at two. The first attempt is unblocked, **not guaranteed to succeed or remain undetected**.
6. When any thief triggers the Ward, atomically consume **that one primed physical Ward item** and immediately give the **victim** 120 seconds (two real-world minutes) of immunity from *all thieves' new direct Stealing attempts against the equipped backpack and nested contents*. This active protection is attached to the character, not the consumed backpack item, and is checked before skill rolls/transfers; it cannot be stacked, prematurely re-triggered or extended. After expiry, do not automatically prime a spare: the first later qualifying theft activity selects/primes the next Ward if one is carried, or ordinary stealing resumes without a Ward.

**Visibility, crime, persistence and boundary conditions**

- A Ward detection means the *victim* detects the theft: display the corresponding warning and preserve the game's existing detected-theft criminal/notoriety/guard rules. Never add stun, damage or murderer status. A transferred item remains with its thief after detection.
- Protection covers theft from the equipped backpack and its nested contents, not worn equipment, corpse loot, arbitrary separate bags or immunity from lawful combat. The physical Ward is not blessed or insured by this mechanic.
- Persist each Ward's stable item identity, primed/unprimed status, chosen victim's selected Ward reference, and per-**(Ward, victim character, thief account)** successful-theft counters. Moving between carried nested containers, temporarily removing/reinserting the *same* Ward, backpack replacement, logout, region transitions and world save/restart must not erase that Ward's history or accidentally choose a fresh spare. Reconcile stale primed flags or changed ownership deterministically so at most one eligible Ward is primed per character without deleting recorded counts. A different victim starts their own counts rather than inheriting the previous bearer's progress; returning to the original victim restores their history. Delete the consumed Ward's counters on triggering. A genuinely different purchased Ward is new preparation, not a reset of the same item.
- Serialize theft resolution per victim so choosing/priming a Ward, ordinary transfer, thief-specific count/detection and consumption/protection all commit atomically. Two queued or simultaneous thieves cannot prime different spares for the same victim or commit *after* protection begins. Invalid/interrupted attempts must not prime Wards or create duplicates/stray rolls. No attempt may commit after either party enters a bank theft-protection region or Cool Dungeon. Ordinary criminal/aggression rights survive crossing regions.
- Test first successful transfer with three unprimed carried Wards: select exactly one deterministic item, prime it and apply the first 25% roll; repeated success sticks to that item even if backpack contents reorder. Test detected failed theft with all unprimed Wards: select/prime exactly one and immediately consume it after the resolved attempt. Test undetected failure: prime nothing. Test first-time thief after another has two undetected successes: newcomer gets 25%, prior thief's next success guarantees detection. Test after consumption/120-second window: spare remains unprimed until the next qualifying theft activity. Separately test alternating accounts, alternate characters on one account, multiple primed Wards arriving through transfer/reinsertion, corpse loot, item changes, save/restart, visible primed/unprimed labels, cost/supply and normal theft/guard behavior. **25% / 50% / 100% per-thief escalation, lazy priming on recorded activity, no dormant timer, physical consumption on detection and 120-second victim-wide protection** are approved.

### Voluntary PvP Intent, lawful retaliation and 24-hour cumulative murder policy — approved (#40, 20 September 2026)

**Binding rule:** Voluntary intent determines whether a character *offers themselves as an attackable target*; genuine criminality determines legal criminal consequences; an **ordinary blue victim's murder protection** determines whether their killer receives a count. These are separate server-authoritative concepts. Attack permission and murder accountability are separate checks. Section 14 owns the timer/persistence contract. These custom rules supersede stock UOR count thresholds, victim murder-report requirements and count-based red decay, as well as older language elsewhere in the plan requiring "normal UOR murder-count/stat-loss/decay" behavior.

#### Single blue-only intent toggle and appearance

- Provide **one** `PvP Intent` switch (not separate Criminal Intent and Murderous Intent). It can be enabled only when the character is genuinely innocent/blue: no live real criminal flag and no unexpired murderer/red timer. An innocent blue may switch it off for *new encounters* at any time, including during combat. A character with active genuine criminal or red/murderer status **cannot disable the stored intent preference** or use the switch to cleanse that status. Do not allow a real grey/red to enable the switch as a shortcut or reset.
- While enabled and not superseded by real notoriety, display a **grey name with `[Intent]`** using ordinary compatible client presentation. Intent is *not* a genuine criminal flag: it must not trigger guards, criminal-assistance/healing penalties, NPC-criminal restrictions, murder counts, or an automatic red timer. Do not infer actual crime, pet legality or kill classification from hue alone. An intent player is freely attackable but may not initiate against unrelated ordinary blues outside Hot Zones.
- Keep the intent preference in an independent persistent boolean, separate from genuine criminal state and red expiry. Actual grey/red status takes display and rule precedence if the intent participant commits a crime or murder; while genuine status is active, the player cannot turn intent off. When genuine status clears, restore the previously stored preference, subject to any still-live combat relationships. Character death, relog and save/restart must not erase or fabricate the preference.
- Toggling intent never modifies `[IC]` roleplay state, legal theft rights, bank protection, guard regions, starter protection, Loot/Backpack Wards, murder history or pet permissions. Only a real eligible player action changes it; scripts cannot toggle real notoriety.

#### Attack-permission matrix (player-character attacks)

| Attacker → target | Outside a Hot Zone | In a Hot Zone |
|---|---|---|
| Ordinary blue → ordinary blue | Block new initiation; allow an established specifically authorized fight | Initiation permitted |
| Any player → `[Intent]`, real grey or red | Initiation permitted | Initiation permitted |
| `[Intent]`, real grey or red → unrelated ordinary blue | Block initiation; permit **only** established opponent-specific retaliation/consensual exception | Initiation permitted |
| `[Intent]` ↔ `[Intent]` / real grey / red | Initiation permitted | Initiation permitted |

- A blue who explicitly targets an intent, grey or red character with a qualifying offensive action grants **that target only** an opponent-specific retaliation right. If several blues attack, keep independent relationships; never allow the target to attack unrelated blue companions merely due to proximity or notoriety. An innocent blue who is the initiator **does not lose murder protection** by initiating against a grey/red/intent player.
- A qualifying direct attack has a server-authoritative player target: melee, archery, targeted harmful spell, harmful consumable or an explicitly attributed player-targeted custom attack. Area/field/splash contact alone is **not** a consent/retaliation-granting direct attack in the safe world. Block illegal effects against protected blues through the centralized policy, including pets and indirect/delayed harm, before costs where feasible. A real fight established by direct targeting remains authorized even across Cool/safe/Hot boundaries until its genuine aggression relationship expires.
- A freely attackable `[Intent]` character cannot gain initiation rights against ordinary blues merely by wearing the tag; neither can a real criminal/red outside Hot Zones. Guarded towns still enforce **genuine** crimes. An attack on a genuinely grey or intent target, and a legal nonlethal attack within a Hot Zone, do **not by themselves** create genuine criminal status or a murder count. Actual stealing, unauthorized looting and other separate crimes remain criminal under their own rules.
- Hot-Zone unrestricted initiation and full loot remain intact; **Hot-Zone permission does not waive murder counts**. The victim's ordinary-blue classification controls the consequence of a kill. No Hot-Zone bank polygon creates combat safety; those polygons block direct stealing only. Crossing a Hot boundary cannot cleanse aggression or strip murder accountability.

#### Murder-count matrix and the intentionally asymmetric blue advantage

- At each attributable real player death, award exactly **one** automatic murder count to the responsible player when their victim is an **ordinary protected blue** under the encounter classification. It does not depend on who initiated, whether the killer had retaliation rights, whether the death occurred in a Hot Zone, or whether the victim files a murder report. A blue who kills another ordinary blue in a Hot Zone **immediately becomes red**. A real grey or red who kills the blue in genuine self-defense **still receives the count**; the player can retreat, fight without killing, accept death, or accept the additional red time. Do not add a self-defense exception.
- Killing a voluntary `[Intent]` participant whose encounter is recorded as intent-exposed, an actual criminal/grey, or a red/murderer generates **no count**. Attacking or killing an actual grey is never itself criminal or murder, even if their actual grey timer ends mid-fight: established lawful-target classification remains valid for that encounter. Being an ordinary blue **attacker** in a fight does not surrender that blue's own murder protection.
- Two genuinely blue players may both enable `[Intent]` and duel anywhere ordinary hostility is allowed without murder counts. If only one enables intent and an ordinary blue attacks them, the intent player's defensive **kill of that ordinary blue still creates a murder count**. The one-way permission to initiate does not create a kill waiver.
- For PvP guild wars/events, their approved mutual permission may authorize initiation outside Hot Zones but **does not automatically waive murder counts** on an ordinary blue. Both parties should use `[Intent]` for count-free combat, unless a future owner-approved exception explicitly changes that rule. This rule is not affected by faction membership. Do not weaken the separate no-PvP-combat-pet policy: a tag's grey hue by itself never makes the intent target a valid pet target.

#### Turning intent off while combat is active — no retroactive consent manipulation

- A genuine blue can switch intent off immediately as to **uninvolved/new opponents outside Hot Zones**. Existing opponent-specific, already-lawful fights persist for their normal combat/aggression lifetime, including pending spells, poison, projectiles and attributable delayed hits. Existing opponents may continue; toggling does not create a safe-boundary escape or reset either party's combat logout/travel restrictions.
- Record each attacker–victim relationship's **victim murder-protection classification at the first qualifying hostile action**. If the victim was voluntarily intent-exposed then, that opponent may finish the existing encounter without a new murder count even if the victim switches intent off. If the victim was an ordinary blue at encounter start, toggling intent *on* halfway through does not retrospectively cancel murder protection for that opponent. New unrelated attackers use the victim's current effective status at their own encounter start.
- Genuine criminality is not a voluntary opt-out: a currently actual-grey/red victim is a lawful non-murder target, and a timer expiring in the middle of an established fight does not retroactively make their previously lawful opponent a murderer. An actual new crime may supersede earlier voluntary presentation; use recorded relationship, genuine status and authoritative death adjudication rather than client hue. Any encounter/classification conflict must resolve deterministically, with per-pair durable records until ordinary expiry; no retroactive reclassification from re-logging, region transitions or rapid toggling.
- `PvP Intent OFF` should tell the player that old opponents retain permission and the old murder classification until those fights expire. Uninvolved players see the ordinary blue presentation; combat participants must receive reliable legal-target/status feedback. Do not expose private identities or create a global PvP invitation for the former intent player.

#### Count-free and count-generating scenarios

| Encounter / outcome | Murder result |
|---|---|
| Blue attacks red/grey; red/grey retaliates and kills blue, anywhere the fight is lawful | **One count to red/grey, +24 hours**; self-defense does not exempt |
| Red/grey initiates against blue in a Hot Zone and kills blue | **One count, +24 hours** |
| Blue kills ordinary blue in a Hot Zone | **One count; blue becomes red for 24 hours** |
| Blue kills `[Intent]` / real grey / red | **No count** |
| `[Intent]` player kills attacking ordinary blue | **One count; killer becomes red** |
| Two intent players fight and either kills the other | **No count** |
| Opponent kills former intent player during their still-active intent-originated encounter | **No count**, notwithstanding intent OFF |
| Opponent kills actual grey whose criminal timer ended during their existing lawful encounter | **No count** |
| Two ordinary-blue guild-war participants fight; killer kills blue without the victim having intent-exposed that encounter | **One count**, despite consensual attack permission |

#### Attribution, persistence and noncombat integrations

- Every legitimate player-character death produces at most one server-authoritative murder assessment. Attribute harmful spells, poison ticks, persistent fields, explosion/splash, indirect effects and controlled creatures to their responsible player when applicable. The attacker/victim relationship and victim classification must survive the lifespan of delayed damage and normal save/restart; reject extra awards from repeated kill callbacks or multiple reporting events. Do not infer consent from incidental area damage alone.
- Gate both the **action's legality** and the **death's murder consequence** through shared, audited services; never equate `CanInitiatePlayerHostility` with `WouldThisKillBeMurder`. Ordinary criminal/guard/assistance behavior is independent of intent. Preserve player corpses, full loot, region rewards, anti-theft Wards and ordinary property/ownership rules without converting intent into an item-safety mechanic.
- Section 14 defines the real-time cumulative red expiry, historical count ledger, migration and tests. Expose tag/on-off state, current genuine status and red-expiration information through a concise player command/status display; publish clearly that unrestricted Hot-Zone attacks may still produce murder counts. Audit current ModernUO flags and behavior against the pinned commit, then implement these as shard rules, not guessed native setting keys.

### Corpse and property crime

Preserve ordinary UOR corpse ownership, rights determination, rights-expiration and criminality; apply only the narrowly defined **Loot Protection Ward** repeat-offender exception below to unauthorized monster-corpse transfers outside Hot Zones.

Safe-world policy must not silently bless corpses, protect player corpses or remove first-offense theft/burglary gameplay.

Examples:

- a player dying to PvE still drops their normal corpse/items
- looting another player's protected corpse should use the normal era criminality/ownership rules
- stolen house/boat/container keys remain usable according to the explicit key rules
- burglary remains possible where possession of a legitimate key allows access
- committing a crime can make the criminal lawfully attackable anywhere

### Invisible Loot Protection Ward — temporary per-offender monster-corpse anti-harassment

**Approved launch design.** Give every new character one invisible, nonconsumable, character-bound Loot Protection Ward entitlement; grant the same entitlement once to every existing character through an idempotent launch migration. This is a permanent passive rules entitlement, **not** a visible backpack item, a finite starter-age immunity, a skill, a loot-ownership rewrite, or protection that expires after four logged-in hours. It cannot be traded, stolen, dropped, sold, banked, lost on death, duplicated on login or claimed again on resurrection. The Ward item/entitlement never expires or gets consumed; **only individual offender entries expire.** Explain it to players in the Welcome/Rules onboarding and appropriate help/status text without displaying a fake inventory object.

**Eligible crime and victim identification**

- Apply only to **monster corpses in ordinary non-Hot Felucca, including the active Cool Dungeon**, during their existing exclusive/legitimate loot-rights period. Use the pinned ModernUO revision's actual corpse rights/ownership and legality checks; do not create a new damage-ranking or sole-owner system, change eligible parties, or increase rights duration. Existing Wanted Monster direct-to-backpack bounty delivery is independent and unaffected.
- Identify the protected victim character(s) from **actual current legitimate loot-rights holders** of the specific monster corpse. A bona fide contributor/party member who already has lawful permission to take the item is never an offender merely because another rights holder has a Ward. A transfer is eligible only when the actual actor lacked rights and the server would normally classify it as unauthorized/criminal under the audited era rules. If several real rights holders are affected, keep independent victim-character entries for each; do not invent rights for nearby bystanders, last-hit spectators, pets or non-contributors.
- The **first actual unauthorized item or stack transfer** by an unblocked offender completes normally. They keep the stolen loot and receive the ordinary grey/criminal, witness, guard and lawful-retaliation consequences. In that same serialized item-transfer commit, add an offender restriction entry for each qualifying protected victim: `(victim character ID, offender stable account ID, expiresAtUTC = transferCommitUTC + 10 minutes)`. Different characters on the offender's same account share their restriction; distinct offender accounts do not inherit one another's entries merely because they share an IP. The ten-minute duration is the approved initial configuration, subject to later balance testing.
- While an entry is unexpired, its offender account is **blocked before item movement from any monster corpse for which that victim currently has legitimate exclusive loot rights**, provided the attempted transfer itself would be unauthorized. This includes other monster corpses the victim earns after the triggering crime, not merely the originally looted corpse. An attempted loot-all action resolves per item so that one allowed first transfer cannot bulk-transfer a second unauthorized item after the restriction is committed. At each commit, if **any** currently legitimate rights holder on that corpse has an unexpired restriction against the actor account, reject the unlawful transfer; otherwise permit the first criminal transfer and atomically create entries for all affected holders. Ordinary unauthorized corpse-looting attempts by unrelated accounts remain eligible for their own first transfer and entries; no global victim immunity is created.
- Reject blocked transfers without moving, cloning, deleting or reserving an item, **without resetting or extending the existing entry**, and without creating a new criminal act solely from an action disallowed by this special restriction. The offender's prior grey/criminal status and any lawful aggression/guards persist normally. On the fixed server-authoritative expiry, delete/ignore the entry; the offender may then make a new first unauthorized transfer and start a fresh ten-minute entry. Logout, character switching, entering/exiting regions, changing inventory, and server restarts do not accelerate, extend or erase the unexpired entry.

**Boundaries and anti-exploit rules**

- Do not protect **player corpses, pets' or summons' inventory, ground items, unlocked chests, ordinary backpack stealing, legally shared party loot, or public monster corpses after their standard rights expire**. A corpse's original Hot-Zone death/source classification and current legal region must not let a player convert Hot-Zone loot into a safe-area entitlement by dragging, moving or reclassifying a corpse. Inside a PvP Hot Zone the Loot Protection Ward does not prevent ordinary corpse looting, even if an entry already exists; do not stop legitimate Hot-Zone full-loot gameplay. Upon return to ordinary safe-world territory, the same unexpired offender/victim entry remains enforceable for eligible new corpses.
- An offender who themselves has legitimate rights on a future shared corpse may still loot **lawfully**; a Ward must never confiscate or block the offender's own legitimate share. Respect all real rights holders, rights expiry, owner deaths and existing player-corpse rules; protected status is a restriction on the offender's repeat **unlawful** act, not ownership of every item the victim can see.
- Persist and version the character entitlement, account/character entry keys and absolute UTC expiries. Enforce entry lookup and first-transfer insertion atomically with the existing loot/ownership and inventory transfer checks, including nested corpse containers, stack splits and concurrent drag/loot-all actions. Use bounded lazy expiry cleanup plus periodic sweeping and privacy-respecting staff audit logs for repeat offender patterns; no public report button or automatic ban is created.
- Keep this entitlement separate from the **physical consumable Backpack Ward**: no shared priming, theft counters, activation, charges or two-minute backpack protection. Loot Protection does not change Stealing skill calculations and Backpack Wards do not affect monster corpses.

**Economy and UX:** The protection requires no purchase, Magery, combat or manual use. Inform the victim of the first unlawful looting incident and that this offender is restricted until a specified time; inform the blocked offender briefly that repeat unauthorized looting of this player's protected monster corpses is temporarily disallowed without revealing private identities or entry tables. Provide accessible help for the ten-minute rule and its public-corpse/Hot-Zone exceptions. Verify actual rights and crime behavior against the pinned ModernUO code before implementing.

### Consensual guild conflict

Keep era-appropriate guild systems.

If two guilds have explicitly entered a consensual war, their members may initiate combat under approved mutual guild-war permissions even outside Hot Zones, but **the war alone does not waive a murder count for killing an ordinary blue**. Both parties must have an applicable `[Intent]` encounter classification to fight without murder counts. Do not allow unilateral declarations to bypass safe-world protection or guild/faction flags to silently override victim murder classification.

### Central hostile-action service

Implement one authoritative shard-level decision path conceptually equivalent to:

`CanInitiatePlayerHostility(attacker, target, actionContext)`

It should answer whether hostility is legal because of:

1. both players being inside the same active PvP Hot Zone
2. target carrying a valid voluntary grey `[Intent]` exposure
3. target being genuinely grey/criminal or red/murderer
4. an existing opponent-specific legal aggressor/aggressed relationship created by a **qualifying direct-target hostile action**, including an intent-originated encounter after intent is turned off
5. mutually agreed guild-war/event status (initiation permission only; no automatic murder waiver)
6. another explicitly approved rule

When the target is intent/real grey/red outside a Hot Zone, the hostility layer must distinguish **direct targeting** from area-effect contact. An AoE-only hit never manufactures an opponent-specific retaliation relationship. Add an independent `WouldKillCreateMurderCount(killer, victim, encounterContext)` adjudicator: a permitted attack or self-defense action does not waive murder protection for an ordinary blue, including in Hot Zones.

Every player-hostile subsystem should use these common audited paths or ModernUO hooks enforcing the same policy; never derive actual criminality from an intent hue.

Avoid one-off checks scattered across weapons, spells, pets, potions and regions.

---

## 4. Combat Baseline — approved hybrid (18 September 2026)

**Binding decision:** Select `Expansion.UOR` as ModernUO's *global platform/feature era*, keep Felucca only, and implement **T2A-style instant first-hit weapon timing and classic precasting, with NO special attacks**. UOR is an implementation baseline, **not** authorization to enable its original combat specials or replace the explicit rules below. Do not switch globally to `Expansion.T2A` just to get insta-hit: that changes unrelated UOR skill, armor and durability behavior and increases the number of feature exceptions to maintain.

This supersedes older statements in this plan that call for stock UOR combat, disabled insta-hit, Stun Mage play or enabled Renaissance weapon specials. Preserve the other approved safe-world, crafting, travel, reward and progression systems unless this section explicitly changes them. Pin the repository commit before implementation; findings from source research are provisional until revalidated against that commit and in-game tests.

### 4.1 Accepted launch mechanics and exclusions

| System | Launch rule | Implementation / verification |
| --- | --- | --- |
| Global era | UOR (`Expansion.UOR`), Felucca only | Keep expansion and map selection separate; disable later facets independently. |
| Melee first hit | T2A-style insta-hit ON | Use the actual `melee.enableInstaHit` setting if present in the pinned revision; prove resulting behavior in-game. |
| Weapon cooldown | A single authoritative swing deadline | Preserve instant *eligible* first strikes, but do not mint extra swings via repeated equip, unequip, weapon/target cycling, disarm, death or relog. Confirm exact intended first-hit/retarget behavior in tests. |
| Spell precasting | Classic precast weapon/spell interaction | Define cast, held-target, spell release, recovery, equip and unequip timing by reference tests; do not assume insta-hit alone implements all T2A behavior. A 30-second held-target timeout is provisional, not a settled number. |
| Automatic UOR weapon specials | NONE | No Crushing Blow, Concussion Blow or Paralyzing Blow. Audit all hit-resolution paths; an earlier source inspection did not locate all three in the ordinary pre-AoS hit path, but absence is **not** repository-wide proof. |
| Wrestling specials | NONE | Disable Stun and Disarm both on activation/request and on hit execution; clear existing ready-state on load/migration. Ordinary Wrestling and unarmed defense remain. |
| AoS weapon abilities | NONE | `Core.AOS` gating is not a substitute for auditing independent original-UOR special code; disallow later ability systems. |
| Base weapon families | Stock pre-AoS speed, damage and hand requirements initially | Retain sword/axe/polearm, fencing, mace/staff and bow distinctions; don't invent replacement abilities. |
| Ordinary passive skills | Retain Tactics, Anatomy, Strength, mace stamina/armor-wear effects and shield Parrying | Audit era, weapon class and target type; only true maces get the historically appropriate passive attrition effects. |
| Damage/itemization | UOR-era underlying calculations provisionally | Use Section 9 crafting ceilings; no AoS elemental/property systems or accidental double application of bonuses. |
| PvP and PvM | Same baseline combat rules | Introduce PvM-only adjustments only after measured need and explicit approval; don't silently alter player combat to improve monster farming. |

**Configuration guidance, not a complete copy-paste file:** keep UOR expansion ID and Felucca-only map selection in the real `expansion.json` schema. In `modernuo.json`, set `melee.enableInstaHit` to true **inside the existing settings structure** after validating the key against the pinned revision. Review the real keys/defaults for `insurance.enable = false`, `vetRewards.skillCapRewards = false` (mandatory fixed 700 cap) and restricted `taming.enableBonding`; do not create unsupported settings or mistake a silently ignored key for a working feature. Keep combat-special gates in actual supported code/configuration, not imaginary flags.

### 4.2 Instant-hit and precast behavioral contract

Record authoritative `nextSwingAt`, current weapon, current/previous target, equip/unequip events, casting state, held spell, spell release and attacker stamina. Accept a hit only when it is legal both under the swing timer and under the shard's safe-world hostility rules. Target changes must never bypass timer eligibility. Spell release must have a specified rule for weapon auto-unequip and recovery; test against actual intended classic behavior before freezing that rule. An instant opening hit may be strong even with correct sustained cooldowns; measure high-damage halberd/spell burst separately from total damage per minute.

Regression sequences: spawn with weapon equipped; unarmed-to-halberd; precast→equip→hit→release; weapon A→B→A; rapid repeated equip; target A→B→A; missed attacks; low/high stamina; simultaneous spell cast and hit; potion/bandage use; disconnection/relogin; death/resurrection; crossing Hot-zone boundaries while the next swing or spell is pending. Verify **no extra attack is created** beyond the chosen timing policy and no delayed attack crosses a legality boundary improperly. A correct historical emulation is not permission to reproduce a timing exploit.

### 4.3 Passive UOR improvements retained, with measured limits

**Lumberjacking/axes — adopt stock UOR formula initially:** The ModernUO version examined in the September 18 research applies an axe damage modifier of approximately `Lumberjacking / 5` percent, up to a **+20 percentage-point damage modifier at 100.0** when UOR is active. Its additional historical GM-only +10 points appeared gated behind a later expansion in that inspected implementation; independently confirm in the pinned checkout. The modifier is additive with applicable damage modifiers, **not a promise of 20% final post-armor DPS**. Approve +20 at GM for launch; **do not** add the 2001 GM-only spike to +30 without separate approval. Smooth scaling is particularly important because Section 5 makes 95→100 a 14-active-day Mastery path and says 90–95 should already be viable. Verify the actual `WeaponType.Axe` classification of each approved axe; do not give the bonus to unrelated War Axe/mace types by name. A two-handed axe cannot simultaneously be used with a shield. Test whether tank mages can cheaply absorb Lumberjacking and still dominate the intended specializations.

**Poison — retain weapon specialization; defer potentially systemic changes:** Retain eligible poisoned blades, skill-dependent application, poison tiers, normal on-hit delivery and tier-appropriate curing **as implemented and verified**. Preserve a meaningful equipment/resource cost and corrosion reduction for Poisoning if that mechanic actually exists; don't invent a new corrosion system. Audit *separately* poison spell potency, cure probabilities, poisoning damage and whether poison prevents bandage or magical healing. Do not automatically add enhanced mage Poison-spell scaling and healing denial as a package: both can strengthen tank mages as well as dexers. If stock UOR already applies healing denial, document that current behavior and require an owner choice before removing it; don't claim it is already disabled. PvP and PvM cure/heal regression cases are mandatory before any change. Do not make Poisoning a required skill for all competitive mages merely to make poison weapons attractive.

**Archery — keep proven usability fixes, defer blanket numerical buffs:** Audit walking/running fire eligibility, hit chance, firing cadence, bow/crossbow/heavy-crossbow damage and equip delays. Reproduce demonstrable movement/timer correctness fixes. Establish stationary and moving-target results before selectively adjusting **one** of accuracy, speed or damage; do not import all Renaissance buffs simultaneously without evidence. Range, ammunition use and positioning are real differentiation and must be included in comparisons.

**Parrying — preserve defensive specialization:** Retain one-hand/shield tradeoffs. Audit the actual pinned-code per-shield block probability and absorption; don't assume it exactly matches published historical buckler-versus-heavy-shield rates. Evaluate together with the Section 9 crafted shield/colored armor bonuses so total mitigation cannot accidentally stack beyond intended caps. Axe/polearm/two-handed spear builds cannot receive ordinary shield mitigation simultaneously.

**Macing, staves and ordinary weapons:** Retain ordinary true-mace stamina drain/armor wear where implemented; confirm which weapons qualify and whether NPC targets have relevant armor/equipment behavior. Staves are not silently granted true-mace attrition. Retain normal blade poison eligibility; poison is not exclusive to Fencing. Polearms maintain high individual damage and slower attacks; compare insta-hit burst and sustained output. Spears lose Paralyzing Blow, so validate whether ordinary stats and two-hand cost make them worthwhile rather than inventing a new special.

**Tactics, Anatomy, damage spells and other late-UOR changes:** Keep pinned stock shared pre-AoS calculations as the initial control group. Do not automatically import historical later changes to direct-damage spells, GM-only Anatomy damage, defensive spells or spell precasting variations as if they were universally beneficial. Confirm precise implementation, affected target types, and whether changes reinforce the tank mage before proposing them. Preserve 700/100/225 caps and approved nonhistorical skill gain/Mastery.

### 4.4 Build diversity: measure opportunity cost, not theoretical templates

Competitive duel dominance by tank mages is a **test hypothesis**, not a proven universal rule for this shard. Do not promise every seven-GM template equal win rates. Test PvP duels, group PvP, ordinary solo PvM, highly armored monsters, Nemesis endurance fights and expedition bosses independently; score kill time, death rate, downtime, healing/reagent/ammunition consumption, armor wear, gold/hour and party contribution alongside match outcomes.

Reference seven-skill test characters (equivalent equipment investment, levels and player proficiency):

| Character | Template |
| --- | --- |
| Tank mage | Swords, Tactics, Magery, Evaluating Intelligence, Meditation, Resisting Spells, Wrestling |
| Sword/shield warrior | Swords, Tactics, Anatomy, Healing, Resisting Spells, Parrying, Magery |
| Axe specialist | Swords, Tactics, Anatomy, Healing, Resisting Spells, Lumberjacking, Magery |
| Poison fencer | Fencing, Tactics, Anatomy, Healing, Resisting Spells, Poisoning, Magery |
| Macer | Mace Fighting, Tactics, Anatomy, Healing, Resisting Spells, Parrying, Magery |
| Archer | Archery, Tactics, Anatomy, Healing, Resisting Spells, Magery, Hiding |
| Warrior bard | Swords, Tactics, Anatomy, Healing, Resisting Spells, Musicianship, Provocation |

These are **controlled test builds, not promised viable or optimal templates**. Record whether shared Magery or other common skills become de facto mandatory; test alternative allocations as well. A roughly 20% practical PvM reward-efficiency shortfall, or a weapon family with no measurable situational advantage, is an **investigation trigger, not an automatic buff**. If a tank mage dominates all relevant modes, first verify swing/exploit behavior and spell/utility interactions before changing raw weapon damage. If a specialist trades weak dueling for demonstrably strong PvM or group utility, that can be an acceptable identity.

### 4.5 Why UOR stays the global expansion setting

The expansion toggle is broader than combat. Previous ModernUO source review found distinct UOR-versus-T2A branches for axe/Lumberjacking damage, colored-material armor rating, magic armor protection and weapon durability/exceptional-quality bonuses. It also found UOR-gated Wrestling Stun/Disarm; the global UOR switch does **not** imply enabling them here. Confirm actual numerical formulas against the pinned commit, because material AR, magic AR, durability and crafted grade interactions are economically consequential (Sections 9 and 22). Selective combat overrides have a smaller *known* impact than reverting the entire engine to T2A and recreating potentially many noncombat features, but this maintenance advantage remains conditional on the complete branch audit.

A feature's historical introduction date does not prove its `Core.UOR` behavior. Lost Lands belong to the Felucca content target. Blessed runebooks, potion kegs, BODs and restricted pet bonding are explicit shard policies; modern feature flags, loot rewards and actual code gates must be audited individually. Trammel and later facets stay disabled **regardless** of UOR expansion. Preserve ModernUO's actual party/corpse-rights scorer and Section 20.6A Wanted attribution; do not revive the rejected custom 60-second scorer. Keep custom Felucca safe-world hostility independent of any Trammel behavior.

### 4.6 Source-confidence and change-control gates

The September 18 research found an insta-hit configuration key and relevant weapon, armor and Wrestling code paths, but **was not a full commit-pinned audit and did not execute game tests**. The suggestion that the three original auto-procs may be absent in stock ModernUO is **unconfirmed** until a full source audit plus trigger tests. Never implement balancing based on that absence assumption. Preserve original source URL/path/commit and historical publish references in `docs/UOR-ERA-AUDIT.md`; explicitly separate verified code behavior, historically documented behavior, proposed launch choice and unresolved questions. Re-audit after relevant ModernUO updates.

**Implementation priority:** configure → use extension/content hooks → narrowly gate original UOContent Wrestling or weapon logic if required → core change only as last resort. No broad replacement of the combat engine and no invented JSON keys. Baseline results must be measured before adding optional numeric buffs.

---

## 5. Character Rules

Audit and establish explicit shard-level values for:

**Total skill cap:** target classic UOR value, normally `700.0`.

**Individual skill cap:** `100.0` unless an intentional exception is later approved.

**Stat cap:** target classic UOR value, normally `225`.

Do not enable:

- Power Scroll skill caps
- 105–120 skill progression
- stat scrolls
- post-era skill systems

Determine whether ModernUO already supplies these correctly from `Core.UOR`.

If yes, leave the upstream logic intact and add tests/documentation.

If not, fix them in the narrowest appropriate layer.

### Skill gain

Do **not** use historical UOR skill-gain speed as the target. Preserve UOR mechanics and caps while making characters become playable quickly, then move the final path to Grandmaster into a calendar-active **Mastery** system rather than a long macro/resource grind.

The progression philosophy is:

> **Train quickly to competence. Train deliberately to 95. Earn 95–100 through active calendar time and real use of the skill.**

The conventional gain system ends at **95.0**. From 95.0 through 100.0, the skill uses the Mastery system defined below.

#### Standard pre-Mastery target curve — 0.0 to 95.0

For a representative **Standard** skill trained efficiently with no temporary gain bonuses, use these focused-training targets:

| Skill range | Intended feel | Target time for range | Cumulative target |
| --- | --- | ---: | ---: |
| 0.0 → 50.0 | Very fast | **1 hour** | **1 hour** |
| 50.0 → 70.0 | Fast | **1.5 hours** | **2.5 hours** |
| 70.0 → 80.0 | Moderately fast | **2 hours** | **4.5 hours** |
| 80.0 → 90.0 | Average | **3 hours** | **7.5 hours** |
| 90.0 → 95.0 | Slow | **5 hours** | **12.5 hours** |
| 95.0 → 100.0 | Mastery calendar | **14 active Mastery days** | calendar-gated |

A "focused-training hour" means an hour using an appropriate gain-eligible training method at a reasonably efficient cadence with adequate resources, no temporary skill-gain bonus, no skill-cap blockage and no substantial idle time.

These are **measured time targets**, not literal timers for 0–95. Ordinary UO random gain behavior remains in place below 95, with per-skill calibration used to make observed median milestone times approach the targets.

The practical player experience should be:

- 50 comes almost immediately;
- 70 is quick;
- 80 is clearly slower than 70 but still easy to reach;
- 90 represents a fully usable/competitive skill level for ordinary play;
- 90–95 is the last conventional training push;
- 95 is the end of ordinary macro/grind progression;
- 100 is a Mastery achievement earned over active calendar days.

A player should not need GM merely to participate in normal PvE, crafting, gathering or Hot-Zone PvP. Balance content so **90–95 is already highly functional**, while GM provides final optimization, title/prestige and any explicitly designed GM-only craftsmanship unlocks.

#### Preserve era-relative skill difficulty below 95

Do **not** flatten all skills into one universal gain rate from 0–95.

The Second Age / UOR-era distinction between naturally easy, medium and hard skills remains part of the shard's progression identity.

Design principle:

> **Use the Standard curve as the benchmark; calibrate individual skills around it without erasing their historical relative difficulty.**

The shard should preserve an explicit classification such as:

- `Easy`
- `Standard`
- `Hard`
- `VeryHard`
- optional per-skill override

Examples of the intended hierarchy before 95:

- straightforward weapon/combat/support skills remain among the easier skills to advance;
- ordinary utility skills remain moderate;
- resource-consuming crafts may require slower or separately calibrated gain curves where appropriate;
- historically difficult skills such as Animal Taming remain distinctly slower;
- other historically difficult Second Age/UOR skills should retain their harder relative curves after code/data audit.

Do not assume one global probability multiplier will produce the desired hours. Different skills generate eligible checks at very different cadences. Calibrate each profile and, where necessary, individual skills against **observed training time to the milestone**, not merely against a nominal multiplier.

Required pre-95 measurement points:

- 50.0
- 70.0
- 80.0
- 90.0
- 95.0

The Standard curve above is the canonical benchmark. Final Easy/Hard/VeryHard timing scalars require measured testing and owner approval.

#### Mastery threshold — 95.0

At **95.0**, normal random skill gain for that skill stops.

The skill may advance only through Mastery opportunities generated by active calendar time.

The purpose is to remove the incentive to stand in a house macroing or burn enormous crafting/reagent resources through the final five points while still making Grandmaster represent an established character rather than something completed in the first evening.

Mastery is **per skill**.

Multiple skills at 95+ can accumulate Mastery time concurrently. A character with Swords, Tactics, Anatomy and Healing all at 95 should not have to complete four sequential 14-day calendars.

#### Mastery active-day rule

Each skill begins its own rolling Mastery calendar when it first reaches **95.0**.

The calendar is divided into consecutive **24-hour Mastery Periods** for that skill.

For each period:

- if the character logs in at least once during that 24-hour period, the period is **Active**;
- an Active period contributes the full **24 hours of Mastery Time** for that skill;
- after the period has been activated, the character may log out and the period still counts in full;
- if the character never logs in during that period, it contributes **0 Mastery Time**;
- missed periods do not backfill later;
- ordinary offline time in an unactivated period produces no Mastery progress;
- a server save/restart must not lose whether a period was activated.

This is deliberately a **daily-active trigger**, not a logged-in-playtime requirement.

The player does not need to remain online for 24 hours. Logging in during the period is enough to activate that day's Mastery accrual.

Do not use real-world midnight as the boundary. Use the skill's/server-authoritative rolling 24-hour Mastery Period so timezone and midnight-boundary gaming do not determine progression.

#### Mastery Time accounting

Internally, track **Mastery Time** rather than creating generic fixed-cost credits that can be hoarded at a cheap early rate.

Each Active 24-hour period adds 24 hours to that skill's Mastery Time Bank.

The next +0.1 gain consumes the amount of Mastery Time required by the character's **current skill bracket**.

This prevents a player from sitting at 95.0, stockpiling cheap 95-level credits, and then spending them through 99–100.

The UI may describe a matured increment as a **Mastery Credit** or **Mastery Opportunity**, but its cost is always determined by the current bracket when the gain is consumed.

#### 14-active-day Mastery schedule

The 50 increments from 95.0 to 100.0 must require exactly **336 Mastery Hours = 14 Active Mastery Days** if the character activates every consecutive 24-hour period.

Use this launch schedule:

| Skill range | Mastery Time required per +0.1 | Increments | Total Mastery Time |
| --- | ---: | ---: | ---: |
| 95.0 → 96.0 | **4 hours** | 10 | **40 hours** |
| 96.0 → 97.0 | **5 hours** | 10 | **50 hours** |
| 97.0 → 98.0 | **6 hours** | 10 | **60 hours** |
| 98.0 → 99.0 | **8 hours** | 10 | **80 hours** |
| 99.0 → 100.0 | **10 hours 36 minutes** | 10 | **106 hours** |
| **Total** |  | **50** | **336 hours / 14 active days** |

The interval intentionally increases as the player approaches GM.

If the character misses a Mastery Period entirely, expected calendar completion moves back by one day for that missed period.

#### Consuming a matured Mastery opportunity

Having enough Mastery Time does **not** grant +0.1 automatically.

The player must actually use the skill in a normal, gain-eligible way.

Once the Mastery Time Bank contains enough time for the next +0.1:

- each otherwise-valid eligible use has a **10% chance** to grant +0.1;
- failed attempts do **not** consume Mastery Time;
- failed attempts increment a per-opportunity attempt counter;
- the **10th eligible attempt is guaranteed** to grant the +0.1 if the first nine did not;
- on success, consume the bracket's required Mastery Time and reset that opportunity's attempt counter;
- if enough Mastery Time remains for another +0.1, the next Mastery opportunity can begin immediately;
- skill locks, 700 total cap, anti-macro rules and normal gain eligibility still apply;
- a gain blocked by skill lock/cap/invalid difficulty consumes neither Mastery Time nor the opportunity;
- invalid or trivial uses that would not normally be gain-eligible do not count toward the ten attempts.

This keeps the final five points tied to actual skill use while bounding repetitive grind and resource cost.

For crafting and consumable skills, every +0.1 Mastery gain therefore requires at most **10 legitimate eligible attempts**, not hundreds or thousands of resource-consuming attempts.

#### Mastery banking

Mastery Time may accumulate while the skill is waiting for the player to consume an opportunity.

Do not require the player to log in exactly when a 4/5/6/8/10.6-hour interval matures.

A returning player may therefore have enough banked Mastery Time for multiple +0.1 opportunities, but still must trigger each gain separately through eligible use and the 10%-with-10th-attempt-guarantee rule.

Mastery Time:

- belongs to that character and that specific skill;
- cannot be traded or transferred;
- persists through logout, death and restart;
- is destroyed when the character is deleted;
- cannot exceed what was legitimately earned from activated Mastery Periods;
- cannot be earned before that skill reaches 95.0.

#### Temporary skill-gain bonuses at 95+

Skill Gain Balls, Pilgrimage Inspiration and any future temporary gain-rate effects must **not shorten the Mastery calendar or increase Mastery Time accrual**.

The 14-active-day 95–100 gate remains intact.

When a Mastery opportunity is mature, temporary gain bonuses may increase the normal **10% per-eligible-attempt trigger chance** by their existing relative/additive gain modifier, while the **10th eligible attempt remains guaranteed**.

Examples:

- base Mastery trigger: 10%;
- +25% Skill Gain Ball: 12.5% trigger chance;
- +10% Pilgrimage Inspiration: 11% trigger chance;
- +20% Greater Inspiration: 12% trigger chance;
- +25% Ball + +10% Inspiration = +35% relative modifier → 13.5%;
- +25% Ball + +20% Greater Inspiration = +45% relative modifier → 14.5%.

Do not allow bonuses to:

- generate Mastery Time faster;
- activate a missed 24-hour period;
- reduce the bracket's Mastery Time cost;
- bypass the 95 threshold;
- create more than +0.1 from one consumed opportunity.

#### Mastery UI / player communication

The system must be explicit rather than hidden.

When a skill first reaches 95.0, tell the player that ordinary gain has ended and Mastery has begun.

Expose at least:

- current skill value;
- whether the current 24-hour Mastery Period is Active;
- current Mastery Time Bank;
- Mastery Time required for the next +0.1;
- whether a Mastery opportunity is currently ready;
- attempts used on the current ready opportunity (0–9 before guaranteed 10th);
- approximate next period boundary / next available Mastery accrual information;
- confirmation that missed inactive periods do not accrue.

Suggested player-facing explanation:

> **At 95.0, this skill enters Mastery. Log this character in during each 24-hour Mastery Period to earn Mastery Time. When enough time is banked, use the skill normally for a chance to gain +0.1; the 10th eligible attempt is guaranteed. Grandmaster requires 14 active Mastery days from 95.0 if no periods are missed.**

#### Anti-exploit requirements

Prevent at minimum:

- changing the client clock/timezone to alter Mastery periods;
- reconnect spam activating more than one period;
- save/restart duplicating Mastery Time;
- character transfer or rename duplicating state;
- skill decrease/re-raise to 95 duplicating already-earned Mastery Time;
- lowering a skill to obtain cheaper bracket costs and then restoring it without correct accounting;
- hoarding low-bracket generic credits and spending them at higher brackets;
- trivial/non-gain-eligible action spam counting toward the 10-attempt guarantee;
- multiple simultaneous attempts consuming one opportunity twice;
- deleting/recreating characters transferring Mastery state.

If a skill falls below 95 because of an approved game mechanic, preserve its earned Mastery state but suspend further Mastery accrual/consumption until the skill returns to 95 unless a separate loss policy is explicitly approved.

#### Skill-gain tuning workflow

Before final launch tuning:

1. classify every enabled launch skill into an era-relative pre-95 difficulty profile;
2. measure representative 0→50, 50→70, 70→80, 80→90 and 90→95 training times;
3. calibrate the Standard profile toward the canonical 1h / 1.5h / 2h / 3h / 5h bracket targets;
4. verify Easy/Hard/VeryHard skills remain materially distinct before 95;
5. verify 95.0 completely disables ordinary gain and enters Mastery;
6. simulate 50 Mastery increments and confirm the configured schedule totals exactly 336 Mastery Hours;
7. verify one login in an otherwise-offline Mastery Period activates the full period, while no login produces zero Mastery Time;
8. verify multiple 95+ skills accrue concurrently on the same character;
9. measure resource consumption for crafting/consumable skills from 95→100 and confirm each increment requires no more than 10 eligible attempts;
10. verify temporary gain bonuses affect only the matured-opportunity trigger chance, never the calendar gate.

Do **not** attempt to recreate every historical anti-macro quirk.

Audit `Configuration/antimacro.json` and document:

- whether anti-macro is active;
- which skills it affects;
- location allowance;
- reset duration.

Make these settings intentionally configurable. Anti-macro rules should prevent exploitative unattended progression below 95 and invalid-attempt spam above 95 without forcing players to reproduce 1999-era training friction.

### New-character Skill Gain Balls

Every newly created character receives:

- **20 Skill Gain Balls**
- each ball grants **+25% relative skill gain** for **one hour**
- balls are **blessed**
- balls are **character-bound and non-transferable**

The purpose is to give every new character a finite pool of accelerated training without permanently increasing the shard-wide skill-gain rate.

#### Gain behavior

Below 95.0, activating one ball applies a multiplier conceptually equivalent to:

`effectiveSkillGainMultiplier = normalConfiguredSkillGainMultiplier * 1.25`

At 95.0+, the ball does **not** accelerate Mastery Time. It increases only the matured Mastery-opportunity trigger chance from 10% to 12.5% relative while active; the 10th eligible attempt remains guaranteed.

The bonus applies only to otherwise-eligible gain checks/opportunities.

It must **not**:

- raise the 100.0 individual skill cap
- raise the 700.0 total skill cap
- bypass skill locks
- bypass stat/skill-cap checks
- bypass anti-macro restrictions
- create gains when the underlying skill-gain system says no gain is eligible
- change combat damage, spell power, crafting output, taming control chance or any other non-gain mechanic

Crafting and Animal Taming still retain their intentionally slower **pre-95** baseline progression. Below 95, the ball multiplies that configured gain rate by 1.25 rather than replacing it with ordinary combat-skill tuning. At 95+, all skills use the Mastery rules above unless an owner-approved exception is explicitly documented.

#### Duration

One ball provides **60 minutes of logged-in character time**.

Preferred behavior:

- timer begins when the character successfully activates the ball
- timer advances only while that character is logged in
- timer pauses on logout/disconnect
- timer persists correctly through server save/restart
- remaining time is visible to the player
- death/resurrection does not cancel the active bonus

This avoids wasting a limited new-character consumable because of disconnects, maintenance or real-life interruption.

Only **one Skill Gain Ball may be active at a time**.

Using another while a bonus is already active should be rejected without consuming the second ball. Do not stack the multiplier and do not extend/queue time implicitly.

#### Blessed and character-bound

Skill Gain Balls must remain with the character through death.

They must not be transferable to another character or account through:

- direct trade
- ground dropping
- player vendors
- secure containers
- house containers
- pack animals
- pets
- mail/reward systems
- commodity/deed conversion
- any other container or transfer path that can change effective ownership

They may be stored in that same character's bank if the implementation can preserve character ownership reliably. Otherwise, keep them in a protected character-bound container/inventory representation.

A ball must never become normal loot on a corpse.

#### Character creation and deletion

Grant exactly **20** balls once during successful character creation.

Do not grant additional balls on:

- login
- resurrection
- skill loss
- stat loss
- template change
- account relog
- server restart
- rename
- character transfer/relocation

Deleting a character deletes that character's unused balls and active remaining bonus time with it.

Because the balls are character-bound and cannot be extracted, creating and deleting characters must not allow stockpiling them on another character.

Existing characters created before this feature is enabled do **not** automatically receive a retroactive grant unless the owner explicitly performs a one-time migration/grant.

#### Player-facing information

The item or activation UI should clearly state:

- `Skill Gain Bonus: +25%`
- `Duration: 1 hour of logged-in time`
- `Blessed`
- `Character Bound`
- current remaining active bonus time, when applicable

Do not imply that +25% means a guaranteed fixed number of gains; it is a relative multiplier on the shard's normal eligible skill-gain system.

---

### 5.1 Hot-Zone Skill Veteran — approved optional title (#19)

**Status: approved for launch.** A character earns the permanent, optional **`Forged in Danger`** title upon accumulating **160.0 qualifying skill points** above 60.0 while physically training in qualifying PvP Hot Zones. This is a character-specific achievement, never a skill/stat-cap increase, a skill-gain modifier, a combat bonus or a mandatory progression system. Since the shard has not launched, initialize tracking at character creation; no retroactive conversion or completed-character alternative route is required.

**Qualifying location at the actual skill-gain commit**

- Reuse the server-authoritative Hot-Zone membership service; include permanent **Hythloth**, **Fire Island / Isle of Fire**, the entire **Buccaneer's Den island**, and the **one currently active rotating Hot Dungeon**. A dungeon outside its Hot week, the Cool Dungeon, and ordinary safe Britannia never qualify. Hot status must be active at the instant of the skill increase, not merely when an action/training sequence starts.
- The character must be physically in the eligible Hot Zone **and not inside or within the house multi/footprint** of **any player house** (own, friend, guild, stranger, public or private); count interiors, upper floors, accessible roofs, house-associated courtyards and enclosed/attached footprint areas as disqualifying. Use authoritative multi/house checks rather than comparing only the character's region name or house-owner permissions. If the engine's multi geometry is ambiguous, exclude rather than award uncertain house gains.
- The character must **not be aboard any boat**, including a moving, stationary, anchored or docked boat, and including decks and holds. Use actual boat/multi membership or collision/footprint checks; do not treat simply standing in Hot-region water or a vessel's region tag as proof of safe qualifying land. An authoritative exclusion takes precedence over Hot membership, even if a boat/house overlaps a qualifying Hot area.
- Sample the server-side character coordinates and house/boat state **when the underlying skill value is committed**, preventing delayed, queued or long-running skill uses begun on land from earning credit when committed inside a house/boat, and vice versa. The system never changes existing house, boat, PvP, skill-gain or Mastery rules; it only observes eligible real increases.

**Progress accounting — 1600 tenths, not a retraining loop**

- Track per-character `HotSkillVeteranProgressTenths` (0–1600, capped) and a persistent **per-skill lifetime actual-value high-water mark in tenths**, seeded with that skill's actual starting value at character creation. Never derive progress from skill-use attempts, temporary/effective skill bonuses, skill-gain-rate bonuses, elapsed time or displayed titles.
- On **every** actual skill-value change, including safe-area/house/boat gains, administrative or scripted grants, template/skill transfer and skill reductions, update the high-water mark to `max(previousHighWater, newActualSkill)`; it never decreases. In the genuine skill-gain event, first capture the old high-water mark and prior actual value; only eligible normal advancement or an actually consumed 95–100 Mastery +0.1 increment may award credit. Staff/scripted/starting/transferred gains never award credit, but must raise high-water marks to prevent subsequent laundering.
- For an eligible real increase, award in tenths: `max(0, newActualTenths - max(previousHighWaterTenths, oldActualTenths, 600))`, subject to the ordinary 100.0 individual cap and remaining 1600-tenths title cap; then update high-water. This awards **only the newly achieved portion strictly over 60.0**, once per skill, and handles a gain crossing 60.0 without counting its below-threshold portion. Always use integral tenths (or equivalent exact fixed-point skill units) to avoid floating-point boundary/duplicate errors.
- Examples: 40.0→60.0 awards 0; 59.9→60.1 awards 0.1; 60.0→65.0 awards 5.0; 80.0→90.0 awards 10.0; lowering 90.0→60.0 and retraining to 90.0 awards 0; raising 90.0→91.0 afterwards in a qualifying Hot location awards 1.0. Gains anywhere else still set high-water marks and cannot be retrained for Hot credit later.
- Skill Gain Balls and Pilgrimage Inspiration may affect underlying eligible skill-gain **rates** according to their own rules but add no title progress independently. Mastery Period activations, Mastery Hours, banked opportunities and failed attempts do not award title points; only the successful actual +0.1 that is committed in a qualifying Hot location and outside any house/boat does. Do not let Mastery credits be silently awarded as title progress while the character is elsewhere.
- Up to 40.0 points are available per skill (60.0→100.0), so four skills fully developed across this bracket inside qualifying Hot Zones can reach 160.0. The 700 total/100 individual skill caps, locks, normal gain eligibility, pet restrictions and anti-macro remain untouched. No credit is awarded for effective bonuses, GM skill titles, item equipping, player trading, time spent in a region or character creation.

**Title, UX and persistence**

- Display progress as `Hot-Zone Skill Veteran: X.X / 160.0` in the achievement/title UI, explain the above-60.0, outdoors/no-house/no-boat and non-repeatable rules, and clearly name the currently qualifying Hot places. If the title UI is not yet generalized, provide a small self-contained optional-title selection path rather than creating a new combat progression framework.
- At 160.0, unlock **`Forged in Danger`** once, permanently, for the **same character**. The player may equip or hide it; default it to off if optional title display has not been chosen. Death, logout, murder status, guild changes, sailing, house entry or a weekly rotation cannot remove the unlock. It does not replace identity/notoriety labels, change aggression legality, confer access or rewards, or transfer to another character/account.
- Persist and version progress, per-skill highs and unlock through world saves/restarts, death/resurrection and character rename. Character deletion destroys its achievement state; re-creation or alts start anew. Update progress and highs atomically with authoritative skill mutations; detect duplicate gain callbacks and never double-credit a single committed increase.

**Implementation configuration and observability**

```text
achievements.hotSkillVeteran.enabled = true
achievements.hotSkillVeteran.title = "Forged in Danger"
achievements.hotSkillVeteran.requiredPoints = 160.0
achievements.hotSkillVeteran.minimumSkillExclusive = 60.0
achievements.hotSkillVeteran.excludePlayerHouses = true
achievements.hotSkillVeteran.excludeBoats = true
achievements.hotSkillVeteran.trackLifetimeHighWater = true
```

Expose per-character progress/high-water/unlock inspection and a staff correction command with audit logging. Telemetry should distinguish qualifying increases from rejections (below threshold, old high-water, not Hot, house, boat, non-natural modification) without logging every attempted skill use. Review the full regression matrix in Section 23 before launch.

---

## 6. Itemization

The shard should use **classic pre-AoS itemization**.

Desired magical equipment model includes era-appropriate properties such as classic weapon damage/accuracy and armor protection tiers rather than modern property lists.

Explicitly prevent normal gameplay generation of:

- Hit Chance Increase
- Defense Chance Increase
- Damage Increase as an AoS item property
- Lower Mana Cost
- Lower Reagent Cost
- Faster Casting
- Faster Cast Recovery
- Luck
- elemental resist properties
- elemental weapon damage distribution
- skill bonuses
- artifact properties
- insurance-related properties

Audit:

- loot packs
- dungeon chests
- treasure maps
- monster loot
- vendor equipment
- crafted equipment
- magic item generation
- fishing loot
- event/reward systems
- starting equipment

Use ModernUO's era-aware `LootPack` systems wherever possible rather than maintaining duplicate UOR loot tables.

---

### 6.1 Nemesis Monsters — approved horizontal PvE retention (#20)

**Status: approved for launch, after core ruleset/region/reward mechanics are stable.** Extend eligible existing hostile UOR mobiles as occasional named endurance encounters across **eligible wilderness and all dungeons**. This is a natural-spawn variation, not a separate world event, new boss ladder, new pet tier, mandatory Hot-Zone collectible or permanent character-power progression. Use existing mobile, loot, spawner and housing-decoration infrastructure where practical; scope A explicitly includes ordinary safe PvE, weekly Cool, weekly Hot and permanent Hot locations wherever the underlying spawns meet eligibility rules.

**Natural spawn and location policy**

- On creation of an **eligible, naturally spawned** monster, make exactly one server-authoritative **2%** Nemesis conversion roll. The Nemesis **replaces that spawn**; do not create an extra mobile, accelerate respawn, increase configured spawn counts or reroll on login, restart, region crossing, reset or target reacquisition. If an eligible-cluster cap prevents conversion, the ordinary spawn remains ordinary without extra attempts.
- Launch eligibility is a curated whitelist of existing **hostile, nontameable** UOR monster species/spawners in approved wilderness and all dungeons. Exclude normal animals, tameable species, summoned/controlled/player-created mobs, guards, town and beginner-protected spawns, event/quest mobiles, unique bosses and staff/test spawns by default. No Nemesis taming, bonding or transfer path; wilderness pets follow ordinary rules and dungeon combat pets remain prohibited.
- Independently apply the **same 2% chance** in eligible safe, Hot, Cool and inactive areas. Weekly status grants no extra Nemesis chance or trophy chance; never move a Nemesis or alter its origin to manipulate reward status. Do not create a separate Nemesis-only spawn schedule, staff event, announcement, map marker or increased spawner pressure.
- Configure an optional maximum simultaneous Nemesis count **per dungeon and per outdoor spawn cluster**, using existing spawner/region IDs. Apply it atomically to concurrent natural spawn callbacks; do not award a replacement roll, kill credit or prize for hitting the limit. Specific caps are balancing/configuration values after the spawner audit, not an excuse to raise normal monster density.
- Persist Nemesis state, source spawn identity, source region/reward classification, ordinary underlying species, unique monster identity and a claimed-death/reward guard through save/restart where mobile persistence normally applies. Rerolling or changing Hot/Cool status does not reclassify an already-spawned Nemesis or mint additional loot.

**Endurance, not burst damage**

- At creation set maximum HP and starting current HP to **150% of the underlying mobile's normal rolled HP**, rounding safely to a valid integer; preserve existing damage, attack speed, attacks, spells, resistances, loot-classification, skill levels, Strength and other combat properties. Apply the health increase **directly to hit points, not by raising Strength or stats** that could unintentionally alter damage. Validate numerical limits and normal healing/serialization; no heal-based immortality or altered death thresholds.
- No new spells, teleport, paralyze, summoning, special AI or attack abilities at launch. If a species cannot safely accept the extra HP without bugs or unintended encounter behavior, opt that species out or define a reviewed per-species compatibility override; do not silently buff its damage. Nemeses remain susceptible to the approved Section 4 hybrid combat systems and the underlying area's ordinary rules.

**Visible identity; no custom client dependency**

- Assign one curated, era-appropriate species-specific name (e.g. a named lich), a clear Nemesis identification in the displayed label/title and an approved existing hue. Appearance/name are fixed when spawned and persist through restart; never imply a magic-item grade or a mechanical threat not actually present.
- **Attempt subtle approximately 10–15% per-creature visual enlargement only after verifying support in the actual ModernUO + supported-client rendering/animation/targeting stack.** This is a preferred enhancement, **not an assumption that individual UO sprites can be scaled**. If incompatible, use the distinct name/hue, or an existing compatible larger body-art variant for a curated species only if animations, targeting and era art are verified. No required custom assets, modified client, animation corruption, oversized collision/pathing or mismatch between visual and server hitbox.

**Two mutually exclusive reward outcomes**

- On an eligible Nemesis's **one legitimate death**, create one corpse using its **ordinary species loot**, including existing Hot/Cool/regional premiums exactly once under Section 20.17. Do not raise magic-item odds, add equipment tiers or duplicate party-member prizes solely because it is a Nemesis.
- Perform **one independent 25% trophy roll per Nemesis death**. On success, add **one** species-specific, decorative trophy to the ordinary corpse and **no Nemesis consolation gold**. Use approved existing item art and one curated item per species; examples are an orc war banner, inscribed lich skull, daemon horn or dragon wall trophy **only where a legitimate existing art/item representation can be verified**. Trophy species identity is the same across locations; do not create dungeon-specific trophy variants that would overlap a future Wanted-monster/dungeon-currency system.
- On the other **75%** outcome, award **+200% of that creature's ordinary pre-region rolled gold** as an extra, fixed consolation amount, and **no trophy**. Let `G` be the eligible species' original naturally rolled gold (before regional scaling) and `R` its single legitimate existing regional gold multiplier: the corpse's total gold is `G×R + 2×G` on a no-trophy outcome, versus `G×R` with the trophy. In ordinary regions (`R = 1`), no-trophy total is **3× normal gold**. Do not recursively multiply the extra `2×G` by Hot/Cool bonuses; do not apply regional bonuses twice. Gold that is normally zero remains zero—do not invent a baseline or award a consolation based on magical-item value.
- The trophy and gold outcomes are **exclusive**, committed atomically to one ordinary corpse and subject to ordinary corpse access/loot rights. No direct per-attacker inventory drops, multiple party rolls, duplicate corpse generation, despawn rewards, repeated death-event awards, trade-in gold or NPC buyback premium. Trophies are standard tradable, stealable where legal, lootable, housing-displayable items; add server-generated monster name/species and kill-date provenance when supported without making them blessed or economically convertible into extra rewards. NPC liquidation and salvage should not turn them into an extra gold/material faucet.
- The 2% spawn conversion × 25% conditional trophy chance yields an **average of one trophy per 200 eligible natural spawns**, not one per 200 kills of all types in every region; species spawn frequency determines relative collector rarity. Expected Nemesis-only extra gold is `0.75 × 2G = 1.5G` per Nemesis, or roughly **+3% aggregate ordinary pre-region gold** if 2% of a comparable spawn pool converts; profile real species composition and region use rather than treat this estimate as a guaranteed economy result. Do not add a weekly Hot/Cool rate adjustment to compensate for variability.
- Under approved Section 20.6A, a Nemesis of a currently Wanted species generates **one** ordinary-species bounty through the existing ranked-score recipient algorithm; never grant bonus tokens for Nemesis HP or convert/duplicate the separate ordinary-corpse Nemesis trophy.

**Operations, tuning and definition of done**

- Expose `nemesis.enabled`, the 0.02 eligible-spawn chance, 1.50 HP multiplier, 1.00 damage multiplier, 0.25 trophy chance, 2.00 extra-base-gold factor on trophy failure, species/spawner whitelist and exclusions, simultaneous per-area caps, approved names/hues/trophy-art map and independently gated sprite-scale compatibility. Validate ranges and prevent missing art/name mappings from producing broken mobiles or items; default unsupported species to an ordinary spawn.
- Collect aggregate eligible spawns, conversions, cap rejections, live Nemeses, kills/despawns, trophy-by-species rolls/drops, base/region/consolation gold, origin classification and duplicate-event suppression. Use these to evaluate kill time, supply, inflation and species-specific scarcity; tune configuration rather than require live events or daily rotations.
- Definition of done: eligible safe/wilderness/Hot/Cool natural spawns all use the same observed 2% roll; exclusion categories never convert; no extra spawn/respawn; +50% HP with no other combat changes; visible fallback works on stock supported clients; single mutually exclusive 25% trophy or 75% +200% base-gold outcomes; no double region bonus or multiple corpse rewards; provenance and origin survive restart; trophy trade/full-loot/housing behavior works; all coverage in Section 23 passes. Ship after baseline area classification and loot-premium integration are proven.

---

## 7. Full Loot and Item Protection

Players should generally drop carried/equipped possessions on death according to classic UOR rules.

### Knocked Out players, execution and Hot-Zone loot

**Approved design.** When an otherwise genuinely innocent/blue player (including a blue player visibly using `[Intent]` but not actually criminal or red) reaches zero health from attributable player damage, they enter the separate server-authoritative **Knocked Out** state rather than immediately dying. This rule applies in both ordinary safe-world regions and PvP Hot Zones so that blue players have one consistent zero-health experience. It does not replace ordinary death for criminals/reds, NPC-caused deaths, or other non-qualifying death sources.

A Knocked Out player is alive but has no active health bar: they lie on the ground with dead-like presentation, are untargetable, cannot take any damage, cannot be healed/bandaged/cured/resurrected, and all status effects/active combat effects are cleared. Monsters cannot finish or damage them. House bans may relocate the character but do not end the state. Death-only consequences do not occur: no player corpse, resurrection, durability/death penalty, ordinary death state, or death-specific item transfer is created. The state persists with an absolute UTC expiry; it elapses while a character is absent/offline and, once expired, the character wakes at half health immediately on their next valid world/login placement.

Outside Hot Zones, Knock Out does not weaken the safe-world initiation rule. It can occur only in an already lawful, target-specific encounter (for example, a criminal/red's recorded retaliation against the blue who directly attacked them, or an established eligible Intent encounter). On Knock Out, clear the active attack/aggression flags so the blue is no longer an eligible future target merely because of that completed encounter, while retaining an immutable encounter record until resolution for audit, loot and execution adjudication. Only a **genuinely criminal or red character that held those target-specific rights when the Knock Out occurred** may loot that blue. Such Knocked-Out looting requires no Stealing skill check, but it remains a controlled item-transfer event: it honors binding, cargo, starter-issued, keys/property and all other non-transferable-item restrictions; invokes ordinary Backpack Ward behavior; and is logged against the encounter. Unrelated criminals, ordinary blues and Intent-only players receive no safe-world loot entitlement.

Outside Hot Zones, an Execution must also be tied to the recorded eligible encounter and follows the ordinary blue-victim murder adjudication rule. Execution is a deliberate explicit action, not a side effect of damage; if it kills an ordinary protected blue it grants exactly one automatic murder count and adds 24 cumulative real-world red hours, regardless of the original blue's initiation.

**Hot-Zone exception:** player initiation remains unrestricted, but Knock Out still replaces a qualifying blue player's zero-health death. In a Hot Zone, a Knocked Out blue is an open no-skill loot target for **any genuinely criminal or red character**, with no engagement-right requirement. Any player may Execute a Knocked Out blue there; an executioner who kills an ordinary protected blue receives the ordinary automatic murder count and cumulative 24-hour red consequence. Hot-Zone Knocked-Out looting and execution therefore preserve full-risk choice while keeping the blue player's nonlethal zero-health state consistent.

**Backpack Ward Hot-Zone rule:** physical Backpack Wards and their active 120-second protection have **no effect inside a Hot Zone**. A Ward must not block, detect, prime, consume, add an extra detection roll for, or otherwise alter ordinary Stealing or Knocked-Out looting there, even if it was primed or activated before entry. The Ward's ordinary state resumes only for later qualifying non-Hot theft activity; it must not retroactively protect or undo a Hot-Zone transfer. The separate invisible Loot Protection Ward already has no effect on Hot-Zone loot.

Required tests include direct/indirect player attribution, safe-world eligibility, Hot-Zone zero-health behavior, targetability/damage immunity, status clearing, house-ban relocation, logout/restart/UTC expiry, half-health wake-up, safe and Hot execution attribution, legal-looter selection, unrestricted Hot criminal looting, Ward non-effect in Hot Zones, protected-item exclusions, and duplicate/atomic transfer prevention.

Verify:

- player corpse generation
- equipment transfer to corpse
- backpack transfer
- criminal looting
- corpse notoriety
- corpse ownership timers
- stealing from corpses
- decay

Audit all sources of:

- `Blessed`
- `Newbied`
- insured
- non-lootable

items.

Era-appropriate exceptions may remain, but there should not be broad later-era item protection.

Create a short document listing every intentional class of item that survives player death.

### Keys and property access

Keys are an intentional exception to modern convenience. They should remain part of Felucca's theft, burglary and piracy gameplay rather than becoming universally protected utility items.

Required policy:

- **house keys are unblessed**
- **boat keys are unblessed**
- ordinary container/lock keys are unblessed unless a specific era-appropriate exception is documented
- key rings, if enabled, are unblessed and must not become a way to make all contained keys effectively blessed
- keys can be stolen, looted from corpses and otherwise lost under normal Felucca rules
- possession of a house key grants only the access that the key historically represents; it must **never transfer house ownership or administrative authority**
- possessing a key must not grant co-owner status, house transfer rights, lockdown/secure control, ban authority or other ownership powers that are not normally conferred by the key itself
- a house owner must be able to **re-key the house from the house sign without possessing the lost/stolen key**
- re-keying must immediately invalidate every prior original/copy of that house key and issue replacement key(s) according to the shard's housing implementation
- boat keys remain stealable/lootable and should provide normal era-appropriate boat access/control, preserving piracy risk
- where the UOR/ModernUO boat system supports a banked backup key or equivalent recovery path, preserve it so losing a carried boat key creates risk without creating irreversible property loss
- losing a key must never itself transfer ownership of a house or boat

The design principle is:

> **Keys are loot; property ownership is not.**

Document this behavior clearly in player-facing housing/boat rules so players understand that carried keys are valuable and vulnerable.

---

## 8. Pets and Taming

Use UOR-era Animal Taming as the mechanical baseline, but deliberately restrict combat-pet usage so taming does not become the dominant dungeon-PvM or organized-PvP strategy.

The shard's intended role for taming is:

**powerful outdoor/wilderness PvE, mount/pet acquisition and animal trade — not dungeon PvM dominance and not general offensive PvP.**

Explicitly disable or exclude later systems including:

- pet training/progression systems
- pet power scroll systems
- later-era pet slot mechanics where historically inappropriate
- post-UOR tameables

### Dungeon pet restriction

Combat-capable tamed or controlled creatures must not participate in dungeon gameplay.

Required behavior:

- combat pets cannot enter normal dungeon regions
- if a player crosses into a dungeon while followed by a combat pet, the pet must remain outside rather than teleporting across the boundary
- Recall, Gate Travel, teleportation, login relocation, resurrection, server restart or other transport mechanics must not provide a loophole that places a combat pet inside a prohibited dungeon
- if an existing save somehow contains a prohibited combat pet inside a dungeon, relocate it safely outside the dungeon or to an appropriate stable/recovery location rather than allowing continued dungeon use
- combat pets must not be summonable, released and retamed, transferred, traded or otherwise introduced inside a dungeon through a loophole
- the active **Hot Dungeon** is still a dungeon for this rule; its bonuses never override the pet restriction
- outdoor/wilderness PvE remains available to tamers using normal controlled creatures

Ordinary riding mounts may be exempted from the entry restriction if technically practical, but they must not become a combat-pet loophole. A mount or other exempt noncombat animal may not provide meaningful offensive dungeon combat. If ModernUO's creature model makes this distinction unreliable, prefer the simpler rule that controlled creatures cannot accompany players into dungeon regions.

Document the exact creature/category test used to decide whether a controlled creature is prohibited.

### Player-vs-player pet aggression policy

Controlled pets must not be usable as a general offensive PvP strategy.

The core rule is:

> **A controlled pet may attack a player only when that player is independently a genuine lawful grey/criminal or red/murderer target to the pet owner, or is an established owner-specific lawful aggressor under the approved pet policy. Voluntary `[Intent]` grey appearance alone, Faction status and unrestricted Hot-Zone initiation NEVER authorize pet aggression.**

Implement this through ModernUO's authoritative notoriety/aggression state rather than by relying only on client hue rendering.

Required behavior:

- a pet cannot attack an innocent/blue player
- `All Kill`, `Attack`, guard/auto-retaliation or equivalent commands against an innocent/blue target must be rejected while that target is not otherwise a lawful grey/red target to the owner
- a pet may attack a red/murderer
- a pet may attack a **genuine** grey/criminal who is lawfully attackable by the owner; an `[Intent]`-only grey is not a qualifying criminal pet target
- a player who attacks the tamer and thereby becomes a lawful aggressor/grey to that tamer may be attacked by the tamer's pets
- once a lawful aggression relationship exists, continued pet combat should follow the same underlying legal-aggression lifetime ModernUO uses for the owner rather than oscillating solely because a displayed hue changes
- pet auto-retaliation must use the same lawful-target check as direct commands
- a player must not be able to manufacture an illegal pet attack through target cycling, indirect commands, guard mode, guild/faction state, pet transfer or another proxy mechanic

This restriction applies to all controlled combat creatures regardless of strength. Do not create special PvP exceptions for dragons, wyrms, nightmares or weaker pets.

### Faction combat

**Pets do not participate in Faction combat.**

Faction membership, faction enemy status, faction objectives, faction bases or faction combat flags must never by themselves make another player a valid target for a controlled pet.

Specifically:

- a blue/innocent faction enemy cannot be attacked by a pet merely because they are in an opposing faction
- pets must not auto-acquire faction enemies
- faction targeting code must not bypass the shard's pet-PvP legality check
- Faction guards/NPC systems should be audited separately from player-controlled pets
- arenas or faction events intended to represent player-character combat should prohibit combat pets

If an opposing-faction player is independently grey/criminal or red/murderer, the pet may attack **because of that independent notoriety status**, not because of faction membership.

The implementation should make this distinction explicit and testable.

### Organized PvP and events

By default, combat pets should also be disabled in shard-run PvP tournaments/arenas unless an event is explicitly designed around pets.

Do not treat guild/faction/event legality as a generic bypass for the normal pet-PvP rule. Any future exception must be explicit in shard configuration and documented.

### Outdoor PvE

Outside prohibited dungeon regions, normal UOR taming should remain meaningful.

Tamers may use appropriate pets for:

- wilderness monster hunting
- outdoor spawn areas
- outdoor world threats/events unless that event explicitly disables pets
- acquiring and selling mounts/animals
- animal-related exploration and economy

This gives taming a clear niche without making it the default answer to dungeon progression.

### Restricted pet bonding evaluation

Do **not** categorically disable bonding without evaluation. Current-player expectations make permanent loss of a long-used pet a potentially excessive friction point, but bonding must not undo the deliberate restrictions above.

Preferred design to test:

- maximum one bonded pet per character
- bonding requires a meaningful process/time investment
- bonded pets can be resurrected rather than permanently lost
- resurrection carries meaningful cost and/or pet skill loss
- bonding must not grant extra combat power
- bonded status does not permit dungeon entry
- bonded status does not expand legal PvP targets
- bonded status does not permit Faction combat
- bonded pets should not gain modern automatic teleport/recovery conveniences unless explicitly approved
- do not expand tameable power, pet slots, training or progression as part of bonding

Treat the final bonding setting as a tuning decision after testing, not as an era requirement.

### Configuration

Expose the taming policy through shard configuration rather than scattering constants.

At minimum support effective settings equivalent to:

- `taming.combatPetsInDungeons = false`
- `taming.petPvPPolicy = lawfulCriminalTargetsOnly`
- `taming.allowPetAttackReds = true`
- `taming.allowPetAttackGreys = true`
- `taming.allowFactionPetCombat = false`
- `taming.allowPvPTournamentPets = false`
- explicit mount/noncombat-pet dungeon exemption policy, if any
- restricted bonding settings if bonding is approved

Names may differ to match ModernUO conventions, but the policy must be centralized and inspectable.

Audit control-slot behavior because some later ModernUO systems may be expansion-gated separately from creature availability.

Determine exactly which tameable creatures exist in the UOR configuration and document them.

---

## 9. Crafting

Keep crafting approximately UOR-era.

Audit:

- Blacksmithy
- Tailoring
- Carpentry
- Tinkering
- Bowcraft/Fletching
- Inscription
- Alchemy
- Cooking

Remove or disable post-UOR recipes and materials.

No:

- runic reforging
- imbuing
- later expansion resources unless specifically era-appropriate
- later expansion artifact crafting

### Bulk Order Deeds

ModernUO currently exposes `bulk_orders` as an independent feature flag.

BODs should be treated as a desirable classic+ crafter activity loop rather than rejected solely because they are outside a narrow launch-era snapshot. They give GM crafters repeatable goals without creating a mandatory combat power ladder.

**Launch target: enable BODs unless reward/economy auditing finds a concrete balance problem.**

Before enabling:

- audit reward tables for post-era items or excessive economic power
- remove or replace rewards that conflict with the pre-AoS itemization target
- validate resource sinks and gold-equivalent output
- ensure BOD rewards do not become mandatory PvP power

Use the feature flag/configuration layer rather than deleting or deeply forking BOD code.


### 9.1 Artisan Signature Collections — approved horizontal crafting retention

**Status: approved feature.** Add a rare `ArtisanSignature` result to the existing craftsmanship system; this is **not** a ninth quality grade, a new recipe/skill, a magic property, or a new permanent combat-power tier. The dedicated *ModernUO-Crafting-and-Itemization-Design.md* remains authoritative for grade unlocks, probabilities, raw-power ceilings, maker marks, ordinary repairs and ordinary degradation unless this subsection explicitly overrides a signature-specific detail.

**Creation and identity**

- Qualifying **successful Masterwork or Grandmaster** player crafts may receive one additional server-authoritative signature roll **after** the normal single craftsmanship-grade roll and resource consumption. Use a **configurable 5% initial proposal** for each eligible grade, to be validated against actual rarity, resource consumption and player-market demand before launch; it is a tuning parameter, not an extra grade probability or guaranteed output.
- Require a curated item-family/profession catalogue. Begin with era-appropriate weapons, armor, shields and other genuinely durability-tracked crafted equipment; allow signature furniture, clothing or decorative items only where approved art/name variants exist. For an item without native durability, give cosmetic identity **without inventing durability, extra function or combat stats**.
- Reuse existing UOR-compatible art, bounded/approved hues and recognizable names. Examples include an ornate sword, engraved shield, distinctive leatherwork, tailored garment or carved furnishing. The name must describe an ordinary item, not imply an artifact/magic tier. Do not require new assets or post-UOR visuals.
- Retain the actual craftsmanship grade and original **maker's mark**. The maker's attribution is permanent through trade and repair; no player can relabel someone else's item. The signature's cosmetic variant and provenance persist through save/restart, looting, trading and repair.
- One completed craft yields at most one item and one signature result. No rerolling existing items, post-craft signature upgrades, special signature recipes, tool-based signature-probability amplification, free material refunds or cancellation after the result is revealed.

**Exact durability requirement**

- Where an item family supports durability, a signature item has **10× the maximum effective durability of the equivalent Standard-grade item of the same item type and material**. This is a precise Standard-baseline comparison, **not** 10× the already grade-boosted Masterwork/Grandmaster durability and not a second application of the craftsmanship modifier. Example: a comparable Standard sword with 40 maximum durability targets 400 effective maximum on its signature variant, even if its ordinary high-grade version has an independent durability multiplier.
- Initialize current effective durability at that maximum. Damage and normal wear consume the signature's effective durability at the usual rate, so the bonus means approximately ten times the baseline wear budget, not invulnerability.
- **Implementation gate:** audit ModernUO/UOContent numeric durability ranges, client displays, save serialization, damage/repair paths, BOD/value calculations and relevant transformations. If 10× cannot fit safely in native hit-point fields, use server-owned extended durability/wear accounting that preserves the **full intended 10× wear budget**, exposes an accurate durability state to players and does not overflow/clamp silently. Do not promise that a native 400/400 field will work before the audit. A cosmetic representation alone or simply reducing repair frequency through a refillable hidden charge is not an acceptable substitute.
- A signature cannot gain extra damage, armor rating, hit reliability, special abilities, stats or material bonuses **because of** the signature. Keep all ordinary grade/material effects and hard pre-AoS crafted-power ceilings unchanged. The durability change is the sole additional functional benefit.

**Repairs, losses and player economy**

- Keep **ordinary skill-based UOR repair/degradation**: any otherwise qualified crafter may attempt the relevant item repair, not only a Master/Grandmaster. Better relevant skill should retain its ordinary success/deterioration advantage, encouraging voluntary paid specialist repair and repair-contract commerce where supported. Do not add a signature-only repair skill gate, automatic NPC restoration, repair immunity, free repair, fixed repair fees or a custom repair currency.
- Repair may restore **current** effective durability according to normal success rules, but must retain the signature marker, original maker and grade, and obey normal **permanent loss of maximum durability** when applicable. For an extended wear representation, apply permanent max-loss against the effective pool consistently; repeated repairs must never restore a signature to its original effective maximum once it has permanently deteriorated, reset a hidden reserve, multiply remaining life, or regenerate a fresh item.
- Preserve existing material/repair costs and support player-negotiated fees; if a repair-deed path exists, it must preserve signature state and use its ordinary skill/degradation checks rather than bypass them. Disable only any specific broken repair/deed route until fixed, **not** general repair access.
- Signature items remain **fully tradable, stealable when normally legal, lootable on death, vendorable and destructible**, with no blessing or insurance. Their extended longevity must not nullify the ordinary full-loot item sink. A buyer may seek the famous maker or another skilled crafter for maintenance.
- The signature status must **not multiply NPC resale price, the player-vendor advance/reference value, salvage yield, BOD credit, crafting-input value or resource recovery** by ten; no NPC/gold/commodity extraction loop. Follow the underlying ordinary item's normal BOD and conversion eligibility without bonus output. If a normal conversion cannot preserve safety, block that specific conversion on signature items rather than minting unrestricted value.

**Presentation and accessibility**

- Show clear item labeling: ordinary grade + a distinctive signature name/art/hue where supported + maker's mark + accurate current/effective maximum durability. The item's name and appearance are collectible, but it is never an extra magic tier.
- Do not require a new profession, quest, RP status, dungeon access, weekly rotation or staff event to obtain or maintain a signature. Normal materials and crafting opportunities apply. Signature collections are organically player-generated, tradeable and displayable in Greater Britain vendors/houses and guild halls.

**Implementation checks / Definition of Done**

- Only successful eligible Masterwork/Grandmaster crafts invoke a single independent signature roll after the grade is fixed; observed rates match configuration within statistical tolerance and do not alter the existing grade distribution.
- For every approved durable item type/material, a fresh signature has exactly 10× its Standard baseline effective maximum durability with no double-grade stacking; max/current survive trade, death-looting, restart and serialization.
- Ordinary and extended durability backends (if needed) give equivalent **effective wear and permanent-repair-degradation behavior**; repeated repairs cannot restore lost maximum, duplicate wear budget or change grade/maker.
- Ordinary lower-skill repair remains possible under the underlying rules, and higher relevant skill retains its native repair advantage; no special Master-only gate. Repair deeds, if enabled, cannot circumvent the durability model.
- Combat damage, armor, hit chance, material caps and magic-versus-crafted relationships remain identical to the equivalent nonsignature item of the same grade/material, except durability.
- Signature status grants no extra NPC liquidation, vendor advance, BOD, salvage or conversion value; it cannot generate resources or gold through item transformations.
- Full-loot, stealing, trading, decay and legal PvP behavior are ordinary; cosmetic/catalog art is UOR appropriate. Test each supported item family and reject unsupported native durability values instead of silently clipping them.
- Telemetry includes eligible attempts, signatures by item/grade/profession, crafting supply, repair rates/fees if observable, death loss, trade/prices if available, durability degradation and economic extraction attempts.

---

## 10. Economy

Start with a conservative classic economy.

Do not invent major custom economic systems during the initial setup.

Audit and document:

- NPC purchase prices
- NPC resale values
- gold generated by major monster tiers
- treasure chest gold
- treasure map rewards
- commodity/resource values
- house prices
- boat prices
- vendor costs
- spell reagent costs
- training costs
- stable fees

Look specifically for systems that can create unlimited or disproportionate gold through NPC buy/sell loops.

Create an automated or scripted economy sanity check where feasible.

Do not change prices solely because they "look old." Establish baseline behavior first.

---

## 11. Housing — Phased Residential Concentration

Housing is a core population-concentration system on this shard, not merely a property feature.

The launch goal is:

> **Make the shard feel inhabited by concentrating homes, vendors, guild houses and foot traffic into a small number of recognizable residential districts, while keeping housing attainable for ordinary players.**

Use classic Felucca/UOR housing mechanics with the following deliberate placement policy.

### 11.1 One house per account

Launch policy:

**one house per account.**

If ModernUO does not expose this cleanly as configuration, enforce it in shard-specific housing logic with minimal impact on upstream housing code.

The one-house limit should apply to ownership, not merely placement attempts. Transfers must not allow an account to bypass the limit.

### 11.2 Three housing land classes

Do **not** use a binary "district or no housing" model.

Classify Felucca land into three explicit housing categories:

1. **Residential District**
   - normal house/deed cost
   - intended default choice
   - **all normal-cost residential districts are located in Greater Britain; no later normal-cost districts open around other towns**

2. **Rural Wilderness**
   - house placement allowed
   - requires the normal house/deed cost **plus a rural placement premium equal to 100% of the normal house/deed value**
   - effective launch cost: **2.0× normal**
   - intended for players who value isolation enough to pay for it

3. **Protected / No-Housing Land**
   - house placement prohibited regardless of willingness to pay
   - used for dungeon approaches, major roads/chokepoints, important landmarks, event spaces, protected resource areas, Buccaneer's Den island and other gameplay-critical locations

Fire Island is a separate **special always-open residential PvP district** described below. It does not use the ordinary rural surcharge unless explicitly changed later.

The design principle is:

> **Housing is inexpensive in settlements, expensive in the wilderness, and prohibited only where housing would harm gameplay.**

### 11.3 Rural housing permit / surcharge

Allow players to place otherwise-valid classic houses in approved rural wilderness by paying a substantial one-time premium.

Launch rule:

**rural placement effective cost = 2.0× the normal house/deed cost.**

Preferred implementation is **not** to duplicate every classic house deed into a second item type unless ModernUO's architecture makes that cleaner.

Prefer conceptually:

- player possesses/buys the normal house deed or otherwise pays the normal house cost
- when placement target is classified as `RuralWilderness`, the placement flow displays the additional rural cost
- player must explicitly confirm the surcharge
- an additional amount equal to **100% of normal house/deed value** is withdrawn/consumed
- house is then placed using the ordinary underlying house type

A player-facing item or label may call this a **Rural Housing Permit** if that produces clearer UX, but the underlying house should remain the same classic house mechanically.

#### Rural premium is a gold sink

The additional rural premium is **not part of the refundable house value**.

Example:

- normal house/deed value: 50,000 gold
- residential placement cost: 50,000
- rural placement cost: 100,000 total
- rural premium consumed: 50,000
- later demolition/redeeding returns only the normal 50,000-equivalent deed/value according to the approved UOR housing system

Do not refund the rural premium through:

- demolition
- redeeding
- house transfer
- account transfer
- server restart/save-load
- deed conversion
- staff-assisted relocation except explicit reimbursement cases

If a demolished/redeeded house is later placed in rural wilderness again, the rural premium must be paid again.

Do not create a recurring rural rent/tax. The surcharge is a one-time choice, not a retention chore.

#### Rural placement still uses normal housing restrictions

Rural placement must still satisfy:

- ordinary house-footprint validation
- one-house-per-account
- terrain/obstruction checks
- protected/no-housing region checks
- dungeon/road/landmark buffers
- Hot-Zone boundary exclusions where configured
- resource/event/spawn protections
- shoreline/teleporter/chokepoint protections
- all normal ownership/transfer restrictions

Paying the rural premium never overrides a protected region.

#### Rural houses and concentration metrics

Rural houses are deliberately allowed, but they should remain a minority.

Initial design target:

> **Approximately 75–85% of occupied houses should remain inside normal-cost residential districts or the special Fire Island residential district, with roughly 15–25% rural.**

Track separately:

- residential-district houses
- Fire Island residential houses
- rural houses
- rural placements by house type/value
- rural premium gold removed
- rural placement attempts rejected by protected regions
- percentage of total houses that are rural

Launch multiplier:

`housing.ruralCostMultiplier = 2.0`

Make it configurable.

If rural housing becomes so common that settlements feel empty, prefer increasing the multiplier (for example 2.5× or 3.0×) before returning to a blanket rural prohibition.

If almost nobody uses rural housing, leave the system alone unless the owner specifically wants more geographic freedom; the purpose is optionality, not a quota.

Changing the multiplier requires owner approval and should affect **future placements only**, not retroactively charge existing rural homeowners.

### 11.4 Phased Greater Britain district unlocks

Define multiple **Greater Britain** residential districts, but open only enough at launch to support approximately **125–150% of expected initial normal-cost housing demand**.

Example conceptual structure:

- `GreaterBritainA` — open at launch
- `GreaterBritainB` — locked
- `GreaterBritainC` — locked
- `GreaterBritainD` — locked

These are the **only phased normal-cost mainland residential districts the shard will ever open**.

Districts unlock outward within Greater Britain as the shard grows.

Once a Greater Britain district has been opened to player housing, **never close or re-lock it around existing residents** merely because population later falls.

After the final configured Greater Britain district is open, the district-expansion system is finished. Do **not** create or unlock normal-cost residential districts around Cove, Vesper, Yew, Trinsic, Moonglow, Jhelom, the Lost Lands or other areas.

Players who want to place outside the open Greater Britain districts after that point must use the **rural housing placement** system and pay its configured surcharge, unless they are using the separately defined Fire Island housing exception.

This is intentional: normal-cost settlement housing stays permanently concentrated around Britain, while rural placement provides freedom without allowing the settlement footprint to keep spreading across Britannia.

### 11.5 Expansion trigger: density without artificial scarcity

The system must concentrate housing without creating a land monopoly or forcing new players to buy from incumbents.

Target operating range:

- keep currently open districts roughly **75–85% occupied** at the point the next district becomes available
- maintain approximately **15–25% practical spare placement capacity** for new players

Because UO houses vary greatly in footprint, do not rely on raw land area alone.

Track at minimum:

- number of active houses in each district
- configured soft capacity for each district
- recent successful/failed house-placement attempts due specifically to lack of usable space
- distribution of house sizes if practical
- inactive/decaying houses occupying prime lots

Preferred unlock rule while a locked Greater Britain district still remains:

1. if the active Greater Britain district set reaches roughly **80% of configured practical capacity**, mark the **next Greater Britain district** eligible to open; **or**
2. if placement telemetry/staff survey shows that fewer than roughly **20% of reasonable lots remain practically usable**, open the next Greater Britain district even if the simple house-count threshold has not been reached.

Do not use concurrent-online-player count as the primary trigger. Online population is too volatile and can cause unnecessary geographic expansion.

Once the **final Greater Britain district** is open, these thresholds no longer unlock additional normal-cost regions. At that point:

- the district system reports `next district: none`
- no other town receives a normal-cost district
- players seeking new placement outside available Greater Britain lots use rural placement and pay the configured rural surcharge
- Fire Island continues to use its separately defined special housing rules

A staff command may perform each Greater Britain unlock rather than making the process fully automatic, but the system should clearly report when the next Greater Britain district is eligible and when the normal-cost expansion sequence is permanently exhausted.

### 11.6 Normal-cost housing never expands beyond Greater Britain

The complete normal-cost district sequence is:

**Phase A — Greater Britain A**  
Open at launch or as part of the initial launch footprint.

**Phase B — Greater Britain B**  
Unlock only when the active Greater Britain footprint reaches the configured occupancy/placement-pressure threshold.

**Phase C — Greater Britain C**  
Unlock under the same rule.

**Phase D — Greater Britain D / final configured Greater Britain district(s)**  
Unlock under the same rule.

After the final Greater Britain district opens:

> **There are no additional normal-cost mainland residential districts.**

Do not later create normal-cost settlement districts around:

- Cove
- Vesper
- Yew
- Trinsic
- Minoc
- Moonglow
- Jhelom
- Skara Brae
- remote islands
- the Lost Lands
- other wilderness/town regions

Those areas remain either:

- approved **Rural Wilderness**, requiring the rural surcharge; or
- **Protected / No-Housing Land**.

Fire Island remains the explicit special housing-zone exception and is not part of this district-unlock sequence.

This preserves Greater Britain as the permanent residential/social capital even if the shard population becomes much larger.

### 11.7 Use roads and travel corridors to create visible settlement

Shape the Greater Britain residential districts around existing roads and natural travel corridors whenever feasible.

The objective is for a player leaving Britain to encounter:

- houses
- player vendors
- guild compounds
- rune libraries
- public crafting houses
- other players traveling between town and homes

Avoid opening large disconnected wilderness rectangles that recreate the population-dispersion problem this system is intended to solve.

### 11.8 Britain remains the residential/social capital

Britain should remain the default social center at low population.

Keeping **all normal-cost district housing** around Britain should reinforce:

- Britain bank activity
- player-vendor foot traffic
- social encounters
- guild recruitment
- public rune libraries
- event-board visibility
- travel toward rotating Hot content

Do not create multiple equally promoted residential capitals at launch.

### 11.9 Player vendors benefit from the housing restriction

Player vendors remain enabled under normal era-appropriate rules.

The district system should intentionally make vendor locations discoverable through geography rather than spreading vendors across the entire map.

A player should be able to learn that "the Britain suburbs" are the primary shopping area even before a more sophisticated vendor-search system is implemented.

Do not add remote purchasing merely to compensate for intentionally concentrated housing.

### 11.10 Permanent no-housing reserves

Some locations remain unavailable for player-house placement even with the rural surcharge.

Permanently reserve at minimum:

- Buccaneer's Den island
- dungeon entrances and their immediate approaches
- Hot-Zone boundaries where houses could create combat/refuge exploits
- major event regions
- graveyards and other important encounter spaces where housing would obstruct gameplay
- major roads where placement would choke travel
- important scenic/landmark areas
- selected rare-resource areas if housing would allow private control
- shoreline/teleporter transition points where houses would create blocking or extraction exploits

The implementation should use explicit no-housing regions rather than relying only on individual blocked tiles wherever practical.

### 11.11 Fire Island is a special residential PvP district; Buccaneer's Den remains non-residential

Fire Island is an explicit exception to the normal phased-mainland housing model.

At launch:

- **player housing is allowed on Fire Island**
- **player housing remains prohibited on Buccaneer's Den island**
- Fire Island housing is available from launch and does not wait for Greater Britain occupancy thresholds
- Fire Island houses still count toward the shard-wide **one house per account** limit
- a player therefore chooses between a mainland residence and a Fire Island residence unless the house-limit policy is later changed
- Fire Island housing does not count toward the occupancy threshold that unlocks additional mainland housing districts

The intent is to create a dense permanent PvP settlement around the Fire Island/Hythloth ecosystem.

#### Fire Island house placement geography

Do not automatically make every technically buildable Fire Island tile valid.

Survey the island and define one or more explicit `FireIslandResidential` placement regions that:

- preserve roads and travel approaches
- preserve Hythloth's entrance and immediate combat space
- preserve the Daemon/Fire Temple and other important encounter areas
- preserve shoreline/boat landing access
- prevent houses from physically sealing narrow routes
- retain enough open terrain for outdoor PvP and PvE
- avoid placement directly on important resource/spawn locations

The Fire Island residential region is **permanently open at launch** rather than part of the mainland district-unlock sequence.

#### PvP rules around Fire Island houses

A Fire Island house does **not** create a mechanically safe region.

The entire house footprint and interior remain part of the permanent Fire Island PvP Hot Zone for player-hostility legality.

Required behavior:

- unrestricted Hot-Zone PvP remains legal inside a Fire Island house whenever both players are physically inside and otherwise targetable
- stepping onto a house plot does not clear aggression or Hot-Zone status
- entering a house does not grant a special invulnerability flag
- normal UOR house ownership/access controls still apply
- locked doors, friends/co-owners, bans and ejects continue to work according to approved UOR housing behavior
- attackers are not granted magical access through locked private doors simply because the house is in a PvP zone
- house access therefore provides the normal physical refuge/value of owning property, but not a separate safe-zone ruleset
- criminal/murder/aggressor state persists normally across the house boundary
- Recall/Gate restrictions for aggressors remain unchanged
- no bank, remote deposit or automatic loot extraction is added to Fire Island houses

Audit house-ban/eject mechanics carefully so they cannot clear combat state, teleport an aggressor to a protected location, or otherwise create a special escape unavailable under normal UOR rules.

#### Fire Island housing and population concentration

Fire Island housing is intentionally exempt from the mainland concentration restriction because it supports a different goal:

> **create a resident PvP community around the shard's permanent high-risk destination.**

Do not use Fire Island occupancy to justify unlocking additional mainland districts.

Track it separately in housing telemetry.

### 11.12 Housing availability is a launch requirement

Concentration must not become artificial scarcity.

At launch, size the initially open Greater Britain districts so a normal new player should generally be able to place **some reasonable house** at normal cost without purchasing land from another player.

While locked Greater Britain districts remain, prefer opening the next Greater Britain district when the configured occupancy/placement-pressure threshold is reached rather than manufacturing scarcity prematurely.

Once **all configured Greater Britain districts are open**, the normal-cost district supply is intentionally finite. At that point rural housing becomes the permanent expansion/availability valve: a player who cannot find or does not want an available Greater Britain lot may place in approved rural wilderness by paying the rural surcharge.

Do not respond to a full Greater Britain footprint by opening a new normal-cost town district elsewhere.

Do not intentionally delay an eligible Greater Britain unlock merely to inflate house resale values.

### 11.13 Inactive-house turnover

Dense neighborhoods only create population if the houses belong to players who still participate in the shard.

Use meaningful house decay/inactivity rules.

Recommended starting target for testing:

- approximately **45 days without qualifying account activity** before an inactive house reaches the serious-decay/removal path

Prefer account-level qualifying activity over requiring tedious manual house-sign refresh clicks solely to preserve property.

The exact inactivity duration remains an owner-tunable launch value, but the system should not permit indefinitely refreshed prime lots on accounts that otherwise never participate.

Provide appropriate warnings before destruction through whatever in-game/account communication mechanisms are practical.

### 11.14 Classic house mechanics still apply

Housing should support era-appropriate classic houses.

Audit and exclude post-UOR house designs unless intentionally retained later.

Verify:

- placement
- approved-district enforcement
- ownership
- co-owners
- friends
- bans
- lockdowns
- secures
- vendors
- decay
- inactive-account qualification
- demolition
- transfer
- account ownership restriction
- house-key access versus ownership authority
- house-sign re-keying without possession of the compromised key
- invalidation of all prior key copies after re-keying

House-key possession must never transfer ownership. A thief or looter with a valid key may receive only the normal physical-access benefit of that key; the owner retains ownership and can invalidate compromised keys from the house sign.

Do not enable modern customizable housing merely because the modern client supports it unless explicitly approved.

### 11.15 Housing district administration and observability

Provide staff tooling to inspect housing concentration.

A command such as `[HousingDistricts` should report at minimum:

- each district name
- open/locked state
- current house count
- configured soft capacity
- estimated occupancy percentage
- recent placement-failure count attributable to space restrictions
- residential vs rural house counts and percentages
- configured rural cost multiplier
- rural premium gold removed (if lifetime accounting is available)
- next Greater Britain district in expansion order, or `none` once the final district is open
- whether the configured expansion threshold has been reached
- whether the normal-cost district sequence is permanently exhausted

Staff should be able to open the next configured district without a code deployment.

Do not allow normal players to toggle or modify district state.

---
## 12. Travel

Retain classic UO travel:

- Recall
- Gate Travel
- marked runes
- **blessed runebooks**
- public moongates
- boats

Runebooks are a settled requirement rather than an unresolved era choice. Keep normal UOR-style use requirements; do not add zero-Magery recall-from-book behavior unless separately approved.

Verify restrictions involving:

- criminal status
- aggressor status
- overweight characters
- blocked locations
- dungeon restrictions
- houses
- boats
- disabled facets
- boat-key access and recovery behavior

Boat keys remain unblessed and vulnerable to theft/looting. Preserve any era-appropriate banked backup/recovery mechanism supported by the implementation, but do not make the carried key blessed merely for convenience.

A player who has initiated PvP should not be able to bypass the intended UOR aggressor travel restrictions.

---

### 12.1 Shipwreck Salvage — approved maritime collection/retention (#27)

**Status: approved feature.** Extend the era-appropriate existing Message in a Bottle (MiB) / SOS sea-treasure workflow instead of replacing or duplicating the underlying Fishing, SOS, boat, world-map or loot systems. This is a player-driven, non-instanced, finite shared-world exploration activity using existing supported-client art, not a live event, new facet, custom ship model, combat-power tier or new magic-item economy. Audit the exact current ModernUO SOS chest generation/completion path, boat mechanics and era-art catalogue before implementing a narrowly scoped custom extension.

**Chart acquisition and ownership — a bonus on completed ordinary SOS**

- On successful recovery/creation of an **ordinary SOS treasure chest**, make **exactly one independent server-side 25% roll** for **one bonus Wreck Chart** in that chest. Do not roll when the MiB opens, an SOS is acquired/read, a preliminary fishing attempt occurs or a failed/aborted recovery runs. Existing ordinary SOS treasure is unchanged: the chart supplements, never replaces, its original contents. Honor only the authoritative once-per-SOS completion/reward event; duplicate callbacks, duplicate chest-open events, loot moves, reconnect and save/restart cannot generate another chart from the same SOS.
- This is **one chart per four completed SOS chests in expectation**, not a deterministic every-fourth reward or a bonus on every fish. The bonus roll is not multiplied by Expedition fishing/resource bonuses, Hot/Cool reward multipliers, Nemesis rolls or other loot hooks.
- A chart is an ordinary physical **tradable, stealable, lootable, unblessed** treasure item. It may be sold between players and stored under ordinary item/container rules; it is not character- or account-bound, a currency, a deeded combat reward or a blessed instant-travel object. Include readable fixed sextant coordinates and a clear statement of the timed, shared-world salvage terms.
- Assign the chart an immutable unique server ID, valid **Felucca ocean** coordinates and a prevalidated destination when minted. Use a configurable eligible-water coordinate pool or audited sampling of genuinely sailable locations clear of impassable boat geometry, shore-fishing reach, blocked tiles, disabled facets and protected/occupied landmarks. A chart's location cannot be rerolled by reading, trading, putting it in storage, re-logging, renaming, restarting or approaching by different boats. If destination validation unexpectedly fails, refuse activation without consuming the chart and log for staff correction; do not silently reroll on player demand.

**Physical voyage and atomic activation**

- The holder navigates an ordinary boat physically to the chart's sextant location, then uses the chart within a small configurable range of that position while **actually aboard an eligible boat**. Use authoritative boat/multi membership, navigability, map and character position; reject remote activation from land, a backpack elsewhere, a house or a distant vessel. Use existing Fishing eligibility/skill and legal salvage targeting for subsequent recovery; add no bypass of ordinary fishing prerequisites. The chart does not teleport a player, conjure a boat, create an instanced map or turn off existing Recall/Gate/runebooks for ordinary travel. Requiring a boat at the wreck must not impose cargo-style global travel restrictions on unrelated characters.
- Activation atomically consumes/marks the **single chart ID**, records the activating character, a fixed authorized-party snapshot, the site ID/location, activation UTC time, expiry, total actions and recovery state, then creates **one** visible salvage site. Do not reveal a harvestable site until successful activation; a concurrent second use of the same chart must find it spent rather than create a duplicate. On crash during commit, recover exactly one of: unused intact chart with no site, or consumed chart with one persisted site; never both and never neither after a confirmed activation.
- Present the wreck as modest existing-art flotsam/debris (approved barrels, crates, planks or other inert visuals) at the ocean location. No custom underwater gameplay, new large ship art, map marker, invulnerable safe bubble, special ocean spawn pressure, staff event, staff-triggered refresh or automatic monster waves at launch. Rendered decorations cannot function as free resource crates, storage, blocking fortifications, mobile boats or independent lootable copies of the salvage inventory.

**Shared salvage, exclusivity and expiration — sixty real-time minutes**

- The site exposes **4–6 finite, independently claimed Fishing/salvage recoveries**, selected and persisted once at activation. Each action consumes exactly one finite recovery and yields its assigned modest sea-treasure/salvage reward. Keep the total ordinary gold/loot cache below an equivalent ordinary SOS chest after economy testing; do not add a new equipment-power tier or use the Expedition +50% harvest quantity, 3× Logistics carry adjustment, Hot/Cool monster gold/loot premium or fishing-resource modifiers to scale site rewards.
- From activation through minute **30**, only the chart activator and the **distinct party characters authorized at activation and still in the activator's same party when they act** may recover anything. Snapshot character IDs rather than transient party slots; adding a player after activation, leaving/rejoining with a new character, changing party leadership, shared-account alts or relogging cannot expand the protected list. The activator retains access independent of later party dissolution. This grants only site-recovery authorization; no new anti-theft, PvP, boat-access, corpse or ownership protections are created.
- At **30 elapsed minutes**, rights become fully public automatically; any otherwise eligible player physically present may salvage remaining recoveries, including the last decorative prize. At **60 elapsed minutes**, all remaining recovery rights, flotsam, caches and any unclaimed decoration expire permanently; if all recoveries complete earlier, clean up immediately. Both timestamps derive from server UTC and keep advancing through player logout, server downtime, weekly rotation and restart; time never restarts, pauses or resets due to a changed party or holder. Complete/expiry cleanup is idempotent.
- The player's own boat, carried chart, unblessed keys, existing PvP Hot-zone classification, safe-world hostility, theft, criminality, corpse/full-loot and maritime encounter mechanics remain unchanged. In particular the site does not turn ordinary water into a PvP Hot Zone or extend the Hot classification offshore. Ordinary ocean threats still apply.

**One guaranteed rare decoration on full completion — weighted collector rarity**

- For **every wreck that is fully salvaged**, award **exactly one** decorative collectible, no failure roll. On activation, select and persist one hidden prize via a single weighted rarity roll: **Uncommon 60% / Scarce 25% / Rare 12% / Extremely Rare 3%** (total exactly 100%). Choose an item from the configured approved-art catalogue within the selected rarity tier; initial design target **8–12 distinct nautical decorations** with a spread of rarities. Example concepts (not promises of verified item IDs): weathered lantern/barnacled crate, ship's bell/ornate compass, antique figurehead/captain's portrait, jeweled maritime relic. Verify each actual era-safe item art ID and supported-client placement before finalizing. No new art or modified client dependency.
- The prize is attached to the site server-side, **not pre-spawned as a separately stealable or duplicable world object**, and is handed out **only as part of the final, successful recovery action**. The player who legitimately commits that last action receives the prize; the original chart owner is not guaranteed the item if they leave recoveries for the public phase. If backpack weight/item-capacity or delivery validation fails, reject that recovery atomically without consuming its remaining action or the prize; do not drop an untracked duplicate or create an indefinite post-expiry mail/claim entitlement. During the 60-minute lifetime the player may resolve inventory space and retry; if time expires first, unclaimed prize is lost. Failures/crash recovery must never issue two copies.
- Completing an otherwise legitimate wreck **always** gives one selected decoration even when it is the lowest tier. An abandoned/expired wreck does not dispense the guaranteed item if never fully salvaged. The rarity roll never rerolls on logout, server save/restart, party changes, different finishing character or repeated Fishing attempts; completed/expired sites cannot be farmed or restored by recreating visual debris.
- Decorations use approved existing artwork, are purely cosmetic, ordinary **tradable/lootable/stealable** physical items, support house/guild display, and may display `Recovered from a Shipwreck` and verified site/ship/date provenance. No extra combat stats, stats/skill boosts, mounts/pets, spell effects or new crafting ingredient. Set **zero NPC sale/salvage/resource/BOD/reference-advance payout** on custom decoration wrappers to prevent a guaranteed monetary extraction loop, without removing ordinary player-to-player market value. Do not overlap Nemesis species trophies or the separate approved Section 20.6A Wanted-monster dungeon-specific prize catalog.

**Configuration, persistence, observability and launch acceptance**

```text
shipwreck.enabled = true
shipwreck.wreckChartSource = completedOrdinarySosChestOnly
shipwreck.chartChancePerCompletedSos = 0.25
shipwreck.chartReplacesExistingSosLoot = false
shipwreck.chartTradeable = true
shipwreck.activationRequiresBoatAtChartCoordinates = true
shipwreck.siteMinSalvageActions = 4
shipwreck.siteMaxSalvageActions = 6
shipwreck.exclusiveMinutes = 30
shipwreck.siteLifetimeMinutes = 60
shipwreck.guaranteedDecorationOnCompletion = 1
shipwreck.decorationRarityWeights = uncommon:60,scarce:25,rare:12,extremelyRare:3
shipwreck.decorationTargetUniqueVariants = 8-12
shipwreck.monsterSpawnChanges = false
shipwreck.regionLootMultipliers = false
shipwreck.expeditionResourceBonuses = false
```

- Store versioned chart ID, source SOS reward ID, fixed eligible coordinates and spent status; persist active site ID, unique activation ID, source chart, activator/party snapshot, original UTC start/expiry and public-unlock timestamps, remaining action count, every already-claimed reward, predetermined prize ID/tier and final awarded/completed/expired marker. Use atomic compare-and-set/transactional equivalent for chest chart creation, chart activation, each salvage action and final-prize handoff. Restore at most one site per activated chart after restart, and garbage-collect only truly completed/expired sites.
- Add staff-only `ShipwreckStatus`/diagnostics for chart/SOS drop statistics, active sites and expiry, reward counts/tier distribution, invalid-coordinate failures, duplicate guard rejection and expected gold/rare-item supply. Staff force-test actions must be isolated from production loot and never mint unrestricted copies. Do not require weekly rotations or live operational scheduling.
- Before launch, simulate actual fishing/SOS rates and 25% chart supply, 4–6 ordinary reward actions plus 100% collectible, weighted rarity distribution, concurrent salvage, boat/coordinate boundaries, 30/60-minute UTC transitions, restart near the final action and economy impact. Publish exact player-facing chart/salvage instructions, rights and expiry; implement the Section 23 regression matrix. No completion claim until the existing SOS system, coordinates, art IDs and boat/fishing integration have been audited against the current ModernUO version.

---

## 13. Party and Guild Systems

Keep the UOR Party system.

Verify:

- invitations
- party chat
- loot permissions
- membership limits
- player disconnect behavior

Keep era-appropriate guild systems.

Do **not** enable Factions at initial launch.

Factions should be treated as a future content/system rollout rather than part of the minimum shard baseline.

Do not enable post-era guild enhancements simply because ModernUO supports them.

---

## 14. Murder, Criminal and Notoriety Systems — approved custom replacement (#40)

**Binding choice:** Retain genuine UOR crime/theft, criminal assistance, guard and corpse-right behavior where not superseded, but **replace** traditional murder-count reporting/threshold/decay with Section 3's automatic ordinary-blue-victim count and cumulative 24-hour real-time red status. Intent is an independent *voluntary* flag; it never creates actual criminal status. Do not implement the new system by adjusting default UOR short/long murder-count durations or by changing only client name hues.

### Cumulative real-world red timer and historical ledger

- On the first qualifying kill, award exactly one murder count and set `redExpiresAtUTC = nowUTC + 24 hours`. On every additional qualifying kill, atomically set `redExpiresAtUTC = max(nowUTC, previousRedExpiresAtUTC) + 24 hours`. Example: 10 hours remaining → one kill gives 34 hours remaining; two more qualifying kills give 82 hours remaining.
- The real UTC expiry advances through offline time, death, logout, character switching, map/region changes, relog and server downtime. Server save/restart must not reset, pause, duplicate or truncate it. Persist an expiry timestamp rather than a decrementing online-play counter. Handle invalid/overflow timestamps safely.
- Red/murderer status is active **if and only if** the cumulative red expiry is in the future, subject to any separately documented staff moderation status. Once expired, drop red status even if the permanent historical murder tally is high; revert to real grey only if a separate genuine criminal flag is still active, otherwise ordinary blue or stored voluntary `[Intent]`. Do not let historical count, short-term count, long-term count or standard UOR red threshold independently keep or restore murderer status.
- Keep total historical murder count and a durable unique death-ID event history for audit only. The count itself does not create renewed red status, a count-threshold stat-loss/resurrection penalty or a delayed crime once the timer expires. Do not add a new murderer stat-loss penalty without a separately approved policy. Other non-murder death/skill effects remain governed by their own approved rules.
- Award the murder count **automatically once per actual attributable player kill**, never contingent on victim reporting, an old murder-report gump, a bounty claim or the victim's opportunity to file. Audit and suppress legacy count-award paths so reporting cannot award a second count. A staff correction must be authorized, reason-logged and transactional, with no duplicate clock extension.
- A red may not disable a stored `[Intent]` preference while the murderer timer is live. Intent never shortens the timer, and crossing into/out of Hot Zones does not waive a count. A blue/grey who murders an ordinary blue becomes red immediately. Killing intent-exposed or actual-grey/red victims does not produce a count, including when an actual-grey expiry occurs during an established legal fight.

### Audit and implementation requirements

Audit innocent/blue, voluntary intent grey, **genuine** criminal/grey, murderer/red, aggressor/aggressed, guild ally/enemy, guarded regions, criminal assistance/healing, corpse ownership, murder reports/bounties, pet/indirect damage attribution, stat loss and resurrection. Preserve independent criminal-timer expiry and aggression lifetime; use per-opponent encounter snapshots of murder classification and original legal-target exposure, not just current hue or location. Revalidate pending attack/damage effects, forced logout, Hot-to-safe boundaries and simultaneous death callbacks.

Implement a centrally authoritative attack-permission service and separately authoritative death/murder adjudicator; persist intent, criminal state, encounter rights needed for their normal expiry, red UTC deadline, unique processed-kill guard and permanent history. Provide staff-only read/correction diagnostics without generating live kills, arbitrary stat loss or duplicate count events. Do not add post-UOR criminal-power/itemization systems.

**Player messaging:** Explain grey `[Intent]` versus genuine grey crime, the 24-hours-per-kill cumulative rule, automatic murder counts even in self-defense and Hot Zones, and the immediate-off-for-new-fights/existing-opponents-remain-rights rule. A Hot-Zone warning must state that initiation is unrestricted **but murdering an ordinary blue still adds 24 hours**. Show current real status and remaining red time without requiring a modified client.

### Interaction with safe-world rules

- Ordinary-blue vs ordinary-blue initiation is blocked outside Hot Zones unless a specifically approved existing relationship or mutual guild-war exception exists; intent/real grey/red players are lawful targets everywhere.
- An ordinary blue may initiate against a real grey/red/intent target without losing their own murder protection. That target may retaliate against that specific blue, but killing them still adds a count. The red/grey's choice to avoid the count is to withdraw or not finish the blue; **no self-defense murder waiver**.
- Intent OFF takes effect immediately for new opponent relationships, not existing legal fights. The encounter's established victim classification is retained until expiry. A real criminal's timer expiring mid-fight does not retroactively make that prior lawful kill a murder.
- Hot Zones waive the ordinary initiation restriction, not murder consequences. Allowed nonlethal Hot-Zone attacks do not themselves trigger genuine crime; actual theft/loot offenses still do. Guild-war/event permission alone does not waive killing ordinary blues; prospective faction rules must not bypass this contract.
- The genuine criminal status and guard consequences survive Hot boundaries. Do not invent a second parallel *criminal* flag for intent, turn `[IC]` into PvP consent, or automatically create pet-attack rights because `[Intent]` appears grey. Section 3 and the Section 23 PvP matrix are authoritative.

## 15. Weekly World Activity — Expeditions, Pilgrimage and Road Travel

Britannia is intentionally larger than the expected launch population can continuously occupy. Do not try to make every road, forest and town equally active at all times.

Instead, designate exactly **one outdoor Expedition Region each week** and run one primary **physical trade route from Britain through that region**.

Design principle:

> **A large world to explore, but a small world to be active in.**

The Expedition system exists to make wilderness, secondary towns and the roads between them periodically meaningful while preserving Britain as the permanent social/residential capital. It also creates a rotating weekly gathering economy by concentrating resource harvesting and hauling into the same visible corridor.

### 15.1 Exactly one active Expedition Region

At launch:

- exactly one Expedition Region is active at a time
- the region changes weekly on a fixed, announced schedule
- use the same weekly reset boundary as Hot/Cool rotations where practical so players only need to learn one cadence
- avoid immediate repeats when at least two eligible regions exist
- ordinary Britannia outside the active Expedition remains fully usable at normal baseline rules/rewards
- the active Expedition Region receives a **+50% ordinary resource-yield bonus** under the harvesting rules below
- Expedition status does **not** change PvP legality; the safe-world/criminality rules remain authoritative unless part of the route physically crosses an existing Hot Zone
- Expedition status does not globally increase monster spawn rate or difficulty

Candidate Expedition concepts should be broad **corridors/regions**, not arbitrary rectangles. Examples to survey:

- Britain → Yew road and surrounding Yew forest
- Britain → Cove corridor and nearby coast
- Britain → Vesper approaches
- Britain → Minoc road and mountain approaches
- Britain → Trinsic road / southern wilderness
- other classic Britannian corridors only after travel/terrain audit

Do not activate several Expedition Regions at once at low population. That would recreate the dispersion problem this system is meant to solve.

### 15.2 One primary trade route through the active Expedition

Each active Expedition Region has one clearly announced trade route, normally beginning in **Britain** and terminating at a town, outpost or NPC destination in/near the Expedition Region.

Examples:

- Britain → Yew
- Britain → Cove
- Britain → Minoc
- Britain → Trinsic

For Expedition-buff purposes, each weekly route has exactly **two connected towns**:

1. **Britain**, the origin/social hub
2. the configured **destination town** for that week's Expedition

The active Expedition Region/corridor plus those two connected towns form the week's **Expedition Logistics Area**.

The route should deliberately use recognizable roads, crossroads, bridges and wilderness approaches wherever the classic map supports them.

The goal is not merely to make the destination useful. The **journey itself is the activity**.

### 15.3 Physical cargo: no fast-travel transport

A player accepts a trade contract/cargo item in Britain and must physically transport it to the destination.

While carrying active Expedition trade cargo, prohibit transport through:

- Recall
- Gate Travel
- public moongates
- custom teleporters
- other instant-travel systems that would bypass the intended route

Ordinary players who are not carrying trade cargo retain normal shard travel. Do **not** globally nerf Recall/Gate merely to make roads relevant.

Mounts remain allowed unless a specific route has a documented reason to prohibit them.

The launch route system should be primarily overland. Water/boat trade routes can be evaluated later as a separate expansion rather than complicating the initial implementation.

### 15.4 Route checkpoints / corridor validation

Simply disabling Recall is not sufficient if the player can ignore the intended road entirely. Each trade route should define a small number of broad ordered checkpoints or waypoints that validate meaningful physical traversal.

Preferred design:

- origin checkpoint in Britain
- one or two broad midpoint checkpoints at natural crossroads/bridges/inns/road segments
- destination checkpoint
- checkpoints are generous enough that ordinary navigation does not feel like pixel hunting
- no requirement to walk on every literal road tile
- completion requires the checkpoints in order

Where practical, use existing landmarks as waystations rather than adding visually intrusive custom structures.

Do not make the route so rigid that small detours for combat, gathering or helping another player invalidate it.

### 15.5 Cargo ownership and anti-exploit policy

Launch recommendation: Expedition trade cargo is a **character-bound contract cargo object**.

It should:

- remain associated with the accepting character
- persist through normal logout/server restart
- survive ordinary death without becoming a freely transferable commodity
- not be bankable while the contract is active
- not be placeable in house secures/containers
- not be tradable or vendorable
- not be placed on pack animals/pets to bypass carrier restrictions
- not be mailed/reward-transferred to another character
- not be duplicated through stack splitting, container serialization or contract abandonment/reacceptance

The initial safe-world implementation should prioritize **road population and co-play**, not cargo griefing. Therefore direct cargo theft/black-market fencing is **not required at launch**.

Outside the active Cool Dungeon and explicitly mapped bank theft-protection regions, stealing/snooping remain enabled against ordinary eligible items, subject to any activated Backpack Ward, and thieves still create criminal conflict normally. In the active Cool Dungeon or bank protection regions, direct player stealing is disabled while snooping remains allowed. A future explicit cargo-theft/fencing system may be designed only with owner approval after the base route economy is stable.

### 15.6 Death, logout and abandonment

Trade contracts should not be trivially erased or duplicated by lifecycle events.

Recommended launch behavior:

- logout pauses nothing special; cargo remains on the character/account state and resumes on login
- server save/restart preserves cargo, route/checkpoint progress and completion state
- PvE death does not automatically destroy the cargo
- resurrection does not reset route progress
- a player may explicitly abandon the contract, which destroys the cargo and progress with no delivery reward
- abandoned contracts cannot be recovered from corpses/containers
- staff should have a recovery command for corrupted/stuck route state without granting duplicate rewards

If a route rotates while a player still has old cargo, use a clearly defined expiration/grace rule rather than silently converting it to the new route. Recommended starting behavior: existing accepted cargo remains deliverable for **24 hours after weekly rotation**, then expires without reward. Make this configurable.

### 15.7 Expedition gathering bonus

The active Expedition Region is a major weekly gathering destination.

Launch bonus:

- **+50% quantity yield from approved ordinary gathering resources**
- normal resource-node respawn cadence
- no automatic increase to rare-resource tier/chance
- no automatic increase to monster loot
- no new resource tier
- no gathering bonus outside the configured Expedition Region

Conceptually:

`expeditionResourceYieldMultiplier = 1.50`

Apply the multiplier to the **harvest result**, not by accelerating resource regeneration.

Eligible resource systems should be explicitly audited/configured. Expected examples include:

- mining ore
- lumberjacking logs
- skinning hides/leather where the shard treats this as a gathering resource
- fishing resources if the active region meaningfully contains eligible water
- cotton/wool or other approved era-appropriate raw materials where technically appropriate

Do not assume every stackable commodity is a "resource." Gold, monster loot, vendor-purchased reagents, crafted goods and arbitrary stackable items must not receive the gathering multiplier merely because they are portable commodities.

Rounding must be deterministic and must not create a systematic duplication exploit. Prefer fractional accumulation/server-side remainder handling where practical, or another documented unbiased rounding policy.

The +50% bonus is deliberately strong. Its purpose is behavioral: make gatherers choose the same wilderness/roads during a given week rather than dispersing uniformly across Britannia.

Ordinary wilderness outside the active Expedition remains at **100% normal resource yield**. Do not penalize inactive regions.

### 15.8 Expedition Logistics buff — 3× resource carrying capacity

While a player is physically inside the week's **Expedition Logistics Area** — the active Expedition Region/corridor plus Britain and the configured destination town — grant an **Expedition Logistics** buff.

The buff provides:

> **3× effective carrying capacity for approved raw resources only.**

Do **not** literally triple the character's general backpack/weight limit.

Preferred implementation:

- eligible raw resource stacks count as approximately **one-third of their normal weight**
- weapons, armor, gold, reagents, potions, monster loot, crafted goods, furniture, trade-route cargo and other ordinary items retain normal weight
- the reduction applies only to explicitly configured resource item types/categories
- the buff does not increase item-count/container-slot limits
- the buff does not increase pack-animal capacity
- the buff does not multiply another future resource-weight reduction unless explicitly approved

Conceptually:

`effectiveEligibleResourceWeight = normalResourceWeight / 3.0`

This preserves the intended outcome — a gatherer can haul roughly three times as much raw material — without creating a universal 3× loot-carry exploit.

#### Area coverage

The buff is active in:

- Britain
- the week's destination town
- the configured Expedition Region/corridor connecting them

The two towns must come from the currently active route definition rather than being hard-coded globally.

When the Expedition rotates, the Logistics Area rotates with it.

#### Leaving the Logistics Area while heavily loaded

Do not strand a player at a region boundary merely because the buff expires while they are carrying more resources than their normal weight limit.

Resources harvested while the player was eligible for the active Expedition gathering system should receive a server-authoritative **Expedition Resource** provenance tag sufficient to support safe hauling behavior.

Recommended launch behavior:

- an eligible resource stack harvested during the active Expedition can continue receiving its reduced-weight treatment after leaving the Logistics Area
- the reduced-weight treatment ends when that resource is:
  - deposited in a bank
  - placed in a house/container
  - traded to another character
  - dropped to the ground
  - sold to an NPC
  - refined/converted into a materially different resource form, unless that output is explicitly also eligible
  - placed onto a pack animal/pet
- split/merge operations must preserve provenance correctly and cannot create additional reduced-weight quantity
- resources gathered outside the active Expedition do **not** gain the tag merely by being carried into the Logistics Area

This makes the buff useful for actual harvesting/hauling while preventing players from using the Expedition area as a laundering station for old stockpiles.

If provenance tagging proves too invasive for the initial implementation, a short configurable post-exit grace period may be used as a fallback, but do not ship a boundary behavior that instantly immobilizes normally behaving players.

#### Transfer and laundering prevention

The Logistics benefit belongs to the gathering/hauling loop, not permanent item enhancement.

Audit and prevent:

- bringing pre-existing resources into the region to acquire reduced weight
- split/merge duplication of provenance
- converting resources between forms solely to preserve reduced weight indefinitely
- placing reduced-weight resources into nested containers to avoid state cleanup
- moving them to pack animals for multiplicative hauling
- trading to another character while retaining an unintended weight reduction
- logout/restart clearing or duplicating provenance state
- weekly rotation leaving old resources permanently weight-reduced

The exact cleanup/grace semantics must be persistent and server-authoritative.

### 15.9 Trade-route rewards and economy philosophy

Trade routes should provide a worthwhile but non-mandatory reward for the travel time.

Trade-route rewards remain separate from the **+50% Expedition gathering bonus** and **Expedition Logistics** carrying benefit.

Preferred route reward structure:

- configurable gold payment based on route length
- optional modest ordinary-resource/commodity reward
- optional low-rate cosmetic/prestige reward later
- no new combat-power item tier
- no daily-login/streak requirement
- no reward for merely entering the Expedition Region

The route reward must be economy-tested against comparable gold/hour activities. It should be attractive enough to create traffic but not become the dominant low-risk gold faucet.

Suggested balancing principle:

> Longer physical routes may pay more, but route rewards should primarily purchase **activity concentration and world use**, not beat the best dedicated PvM income.

Do not grant a blanket wilderness reward penalty outside the Expedition. Inactive wilderness remains normal 100% value.

### 15.10 Issuance and farming controls

Prevent route rewards from becoming an alt-account or automation faucet.

At minimum:

- every cargo/contract has a unique persistent identifier
- each identifier can reward exactly once
- accepting character is recorded
- checkpoint progress is server authoritative
- completion is server authoritative
- route turn-in consumes/invalidates the cargo atomically before granting reward
- reconnect/restart cannot duplicate completion
- abandoned/expired cargo cannot later be turned in
- staff-created/test cargo is non-rewarding unless explicitly flagged

Do not require an arbitrary one-per-day limit unless economy testing shows it is necessary. Prefer tuning reward value and travel time before adding chores/cooldowns.

### 15.11 Relationship to housing and population concentration

Britain remains the route origin specifically because it reinforces the shard's existing concentration strategy:

- normal-cost housing is Greater-Britain-only
- Britain remains the social/vendor hub
- players gather there to accept cargo
- players then leave together along the same announced road
- the active Expedition periodically pulls population through otherwise underused wilderness and secondary towns
- the +50% resource yield attracts gatherers to the same region
- the 3× resource Logistics benefit encourages those gatherers to haul through Britain, the active corridor and the destination town rather than immediately disengaging from the world

This is intentionally different from opening additional residential capitals. Secondary towns become **weekly destinations**, not permanent population sinks.

Rural houses along an active route may naturally become visible landmarks/player meeting points, but Expedition status gives them no special mechanical privilege.

### 15.12 Relationship to Hot/Cool content

The weekly shard status should advertise all three rotating activity systems together:

- `Weekly Hot Dungeon: <name>`
- `Weekly Cool Dungeon: <name>`
- `Weekly Expedition: <region>`
- `Trade Route: Britain → <destination>`
- `Weekly Pilgrimage: <virtue / shrine>`
- `Next Pilgrimage Departure: <time>`
- `Expedition Resources: +50% yield`
- `Expedition Logistics: 3× resource carrying capacity in the region + connected towns`
- `Expedition Destination Vendor: <destination town>; open for the full Expedition week; personally completed current-week cargo delivery required; one rare purchase/account/week`

The systems serve different populations:

- Hot Dungeon: high-risk PvP/PvE concentration
- Cool Dungeon: safe dungeon PvE concentration
- Expedition/Trade Route: safe-world outdoor travel/exploration concentration

Do not mechanically require the Expedition destination to match the Hot or Cool Dungeon. However, staff/configuration may intentionally choose geographically coherent weekly combinations when that helps make one part of Britannia feel especially alive.

Never make Expedition status override Hot-Zone legality. If a future route crosses a permanent Hot Zone, the player must receive explicit advance warning; launch routes should preferably avoid doing so.

### 15.12A Rare Expedition Destination Vendor — approved town-specific cosmetics (#36)

**Status: approved, with the owner's final Option A purchase rule and Option C inventory rule.** Attach one automated, non-Britain **Rare Expedition Destination Vendor** to the **destination of the single currently active Britain-origin Expedition trade route**. This is an optional horizontal collecting activity and a gold sink, not a new Expedition Region, second route, currency, combat progression system, or GM-operated event. Reuse the existing authoritative route definition, weekly rotation boundary, cargo checkpoint and completed-delivery ledger rather than creating a parallel timer or accepting unverifiable player-held cargo as proof of completion.

**Entire-week presence and geographical scope**

- Spawn or enable exactly one vendor at a configured, surveyed, publicly reachable **in-town position** in the current route's non-Britain destination **for the entire active Expedition week**. The earlier proposal for three two-hour visits is explicitly superseded: **no visit windows, short appearances, spawn lottery or staff spawning**. If the Expedition is enabled, the vendor should be available throughout its active interval, including after normal world saves/restarts. At weekly changeover, deactivate/remove the previous destination vendor and activate the new one transactionally; prevent stale duplicates if rotation or initialization callbacks fire twice. Merchant location and player-facing opening are deterministic and displayed on the weekly Expedition board.
- The vendor derives its town ID and position from the current route's configured destination, not merely the player's region. Britain's origin is **never** eligible as a vendor destination. Survey all active candidate routes before launch and require a valid, accessible vendor mapping; when a route ends at an outpost rather than a town, explicitly designate a corresponding town collection and safe placement or disallow the route until configured. Do not add a route or activate a second town just to support cosmetics.
- Initial **illustrative** collections for eligible destinations: **Yew** woodland/antiquarian (carved furniture, forest relics, ceremonial banners); **Cove** coastal curios (lanterns, shells, fishing furnishings); **Minoc** smithing/mining relics (decorative tools, anvils, mining artifacts); **Trinsic** knightly heraldry (ornamental shields, banners, statues); **Vesper**, *only if configured as an actual trade destination*, merchant luxuries (scales, fine furnishings, trade ornaments). Other future approved destination towns need their own authored thematic registry; these examples do not imply every town is a launch route.
- Each eligible town has its own **stable 6–8-design collection**, with a permanent **core** and a separate pool of rotating rares. As a practical content template, provision **2–4 core designs and at least four distinct rare candidates**, with the exact totals set per town to remain within 6–8 designs. Do not duplicate a collectible design across town collections, cross-sell another town's stock, substitute global generic loot or let an inactive town's vendor remain open. Named examples are art concepts, not promises of unverified existing sprites; validate each graphic, facing, animation if applicable, static placement and era compatibility against actual installed game art before content approval.

**Approved Option C inventory: stable core plus fixed weekly rare selection**

- **Core inventory is always available** whenever that town is the active destination; eligible customers may buy any core item repeatedly with ordinary gold, without a weekly core-item purchase cap. Core designs and prices are town-specific and remain consistent until an explicitly versioned content/balance change. There is no shared finite NPC stock, first-come race or hidden restock schedule.
- At the **start of each Expedition week**, choose **two or three distinct rotating rare designs** from that same destination's approved rare pool; the selection and its prices are fixed for the entire week. The town's rare pool has at least four candidates so repeated visits can reveal different offers. Use configurable per-design weights/rarity tiers, including suitably low weights for exceptionally rare offerings, without advertising an unsupported fixed drop percentage. A listed item is a guaranteed purchase for an eligible buyer who pays; there is no additional post-purchase loot roll. On a later week when the town rotates back, reselect stock from its own pool; repeats may occur naturally unless a configurable non-repeat policy is separately validated.
- Persist a unique authoritative `ExpeditionWeekId`, `DestinationTownId`, selected rare item IDs, prices/content revision and merchant state through save/restart; derive week ID from the shard's Expedition scheduler, not a player's local time or the vendor's spawn timestamp. The same week cannot reroll its stock through restarting, moving, interacting, switching characters, forcing vendor reconstruction or toggling region visibility. Admin overrides must intentionally create an auditable new week/stock generation only under documented rules and must not reset purchase entitlements within a continuing week.

**Approved Option A access and purchase accounting**

- **The purchasing character personally must have completed the current week's configured Britain-origin cargo delivery** via the authoritative successful turn-in record, for that same route/week, **before** any purchase. Accept neither an uncompleted or merely carried cargo contract nor checkpoint arrival alone; accepting a route, another character's completion, previous-week completion, a grace-period delivery belonging to an old week, staff/test rewardless cargo, transferred items or an unrelated Pilgrimage must never qualify. If a valid delivery completes during the current week, access remains active for that same character until rotation; repeated deliveries do not generate more rare purchase allowances.
- The completed-delivery record is **not consumed** by shopping. Every purchase rechecks the current week/destination and character completion state on the server at the actual buy commit; merely opening the merchant's UI or previewing items never grants entitlement. A player may inspect stock before completion but cannot buy; use a clear, nonrevealing 'complete this week's route' message. No remote purchasing: character and merchant must meet normal interaction-range, living/valid-interaction and funds checks. Keep full-loot, notoriety and the zone's underlying PvP/crime rules unchanged; the merchant/UI adds no immunity.
- **One rotating rare item in total per account per Expedition week, across all characters and designs.** A purchaser chooses **one** of that week's two or three rare offers; after a successful rare purchase, all rare offers become unavailable to **every** character on that account until the next actual weekly Expedition rotation. A fresh character, character deletion/rename, multiple completed deliveries, logout, another UI window, switching town via staff relocation or repeated stock availability cannot reset the allowance. Core purchases remain unlimited for independently eligible characters on that account. The account limit counts real successful rare purchases only, not canceled/failed attempts; there is no accidental restriction to one core item.
- Persist entitlement by stable internal account ID and Expedition week ID, and serialize purchase ledger writes with gold deduction and single item creation in one authoritative transaction or idempotent state-machine equivalent. Lock/reconcile simultaneous purchases from separate characters/sessions; on failure roll back gold/entitlement/item consistently, and on disconnect/save/restart never charge twice, mint twice, allow two rare items or consume a rare slot without an item. Forbid a buyback/refund/rebuy workflow that grants extra rare allowances or turns items into gold. A staff correction, if required, must be privileged, scoped, reason-logged and explicitly avoid creating a second purchasable entitlement without authorization.

**Economy, itemization and presentation**

- Payment is **ordinary gold only** at configured town/design prices, paid once per successful transaction. Vendor gold receipts are removed from the economy. No marks, seals, new currency, cargo trade-in, discount from resource-yield/Logistics, reimbursement or automatic reward for standing near the merchant. Prices should be balance-tested against route rewards and collectible resale demand; make the system a net gold sink rather than a fixed-profit cargo loop.
- All merchandise is **cosmetic only**, fully player-tradable and lootable under existing Felucca rules, usable in housing where normal item mechanics allow, and made from vetted existing UOR-compatible artwork. No equipment power, armor/damage/skill bonuses, exceptional production advantages, meaningful container capacity or special access. Set vendor-bought collectibles' NPC resale, buyback, salvage, deed-conversion and crafting-resource extraction values to zero or negligible anti-arbitrage values; the special vendor **never buys items from players**. Do not route these purchases through the player-vendor advance system or provide a mechanism to redeem items for more gold than was removed.
- Display on the existing Expedition activity board: the current trade route, vendor town/in-town directions, **available all Expedition week**, current core/rotating rare catalogue and prices, the character's delivery requirement and the account's remaining rare allowance. Published stock changes only at the weekly boundary or a logged content intervention. Announce the transition with ordinary weekly activity messaging; there is no secret spawn timer, mandatory streak, subscriber-only opportunity or remote sales interface.
- Integrate primarily as shard-specific configuration and a narrow NPC/content extension plus existing authoritative Expedition ledger hooks. Do not rewrite generic vendor, cargo, account or world scheduling core systems unless a source audit proves necessary. Do not depend on new art, modified clients, custom maps or continuous staff operations.

**Suggested configuration (illustrative keys; use the shard's actual config conventions):**

```text
expedition.destinationVendor.enabled = true
expedition.destinationVendor.activeForWholeExpeditionWeek = true
expedition.destinationVendor.originExcluded = Britain
expedition.destinationVendor.purchaseRequiresCurrentWeekCharacterDelivery = true
expedition.destinationVendor.corePurchaseLimitPerAccountPerWeek = unlimited
expedition.destinationVendor.rarePurchasesPerAccountPerWeek = 1
expedition.destinationVendor.rotatingRareOffersMin = 2
expedition.destinationVendor.rotatingRareOffersMax = 3
expedition.destinationVendor.minimumRarePoolPerTown = 4
expedition.destinationVendor.persistWeeklyStock = true
expedition.destinationVendor.npcBuysItems = false
expedition.destinationVendor.currency = gold
expedition.destinationVendor.townCollections = <approved distinct themed item/price/weight registries by configured destination town ID>
expedition.destinationVendor.townPlacements = <surveyed accessible in-town coordinates keyed by destination town ID>
```

**Operational inspection and testing:** Track vendor lifecycle, current week/route/town, valid town registry, stock snapshot, account-limit decisions, completion checks, purchase outcomes, gold removed and rejections without exposing account identity to players. Review the specific test matrix in Section 23 and include this vendor in documentation and launch readiness. **A future change to availability, entitlement, item power or town selection requires explicit approval; this feature is not an invitation to expand the launch route pool.**

---

### 15.13 Weekly Virtue Pilgrimage

Add a weekly **Pilgrimage** activity whose purpose is to create synchronized physical travel from Britain to one classic mainland virtue shrine.

Design principle:

> **Pilgrimage turns travel itself into lightweight social/progression gameplay.**

Each weekly reset selects exactly one **Virtue of the Week** from the approved mainland-continent shrine pool.

Launch candidate pool, subject to exact UOR-map audit:

- Compassion
- Justice
- Sacrifice
- Honor
- Spirituality

Exclude shrines that require leaving the mainland continent. The exact shrine coordinates/region definitions must be verified against the shard's UOR Felucca map before implementation.

#### Britain-only start

Every pilgrimage begins in **Britain**.

A Pilgrim NPC / activity-board interaction in Britain issues a:

`Pilgrimage Scroll of <Virtue>`

The scroll must be:

- blessed
- character-bound
- non-transferable
- non-bankable while active
- non-vendorable
- non-droppable
- non-secureable in houses
- non-placeable on pets/pack animals
- persistent through death, logout and server restart
- associated with the accepting character and the specific weekly virtue/departure window

The scroll should clearly identify:

- current virtue
- target shrine
- active departure-window identifier
- required physical-travel rule
- checkpoint progress if player-facing presentation is practical

The destination should be clearly stated. The objective is shared physical travel, not external-map lookup friction.

#### Timed departure windows

Pilgrimage starts are synchronized.

Launch cadence:

- a **15-minute departure window**
- opens **every 4 hours**
- fixed server-authoritative schedule
- six opportunities per 24 hours
- use UTC or another single documented shard-wide schedule rather than player-local time for race authority
- announce upcoming windows at approximately 10 minutes and 5 minutes before opening
- announce opening
- announce approximately 5 minutes remaining
- announce closing

A character may receive/start that week's pilgrimage **only while a departure window is open**.

The 15-minute window controls **when the pilgrimage may begin**, not how quickly it must be completed. A valid starter may finish after the window closes.

Only one active pilgrimage may exist on a character.

A character that abandons an incomplete pilgrimage may start again during a later departure window that same week.

A character that has successfully completed that week's pilgrimage may not start it again until the next weekly virtue rotation.

#### Physical travel only

While carrying an active Pilgrimage Scroll, prohibit use of:

- Recall
- Gate Travel
- public moongates
- custom instant-travel teleporters
- other transport systems that would bypass the physical route

Mounts remain **allowed**.

Ordinary movement, roads, bridges and wilderness travel remain available.

Death does not invalidate the pilgrimage; the blessed scroll remains with the character and progress persists.

Logout/disconnect does not destroy progress, though real elapsed time naturally makes a top-five race finish less likely.

#### Ordered pilgrimage checkpoints

Each shrine route should define approximately **2–4 broad ordered checkpoints** between Britain and the shrine.

Use:

- roads
- bridges
- crossroads
- inns
- gates
- town approaches
- other recognizable mainland landmarks

Checkpoint regions must be broad enough that ordinary navigation and small combat/gathering detours do not become pixel-hunting exercises.

The objective is to ensure the player meaningfully traverses Britannia and the intended corridor rather than exploiting a geometric shortcut.

Completion requires:

1. valid current-week scroll
2. valid departure-window assignment
3. required checkpoints completed in order
4. arrival within the configured shrine-completion radius
5. server-authoritative completion transaction

Using the wrong shrine must **not** consume the scroll.

#### Pilgrimage race

Every departure window is also a race.

Players who started during the same departure window compete by **valid completion order**, not personal elapsed-time records.

The server creates a unique departure-window/race identifier and atomically records finish order.

Launch rewards:

- **first 5 valid finishers:** `Greater Pilgrim's Inspiration`
  - **+20% relative skill gain**
  - **60 minutes**
- **all later valid finishers:** `Pilgrim's Inspiration`
  - **+10% relative skill gain**
  - **60 minutes**

"Double bonus" means +20% instead of +10%, not two hours.

The first-five count is per departure window.

Race placement must be server authoritative and race slots must be claimed atomically so two simultaneous arrivals cannot both receive the same position.

The top five finishers should receive a concise shard-visible or activity-board announcement. Do not globally announce every later finisher.

Recommended visible result:

`Pilgrimage of Justice — First Pilgrims: <five names>`

Keep a short recent-results history on the Britain activity board/admin status if practical.

Do **not** require a minimum number of starters at launch. If live behavior shows players deliberately using nearly empty off-hour windows solely to guarantee top-five rewards, add a configurable minimum-participant threshold only with owner approval.

#### Skill-gain reward activation

Completing the pilgrimage should grant a **ready-to-activate character status**, not immediately start the one-hour timer.

This prevents the return trip from consuming the training reward.

The player may activate the earned Inspiration when ready to train.

Once activated:

- duration is 60 minutes of **logged-in character time**
- logout pauses the timer
- save/restart preserves remaining duration
- death does not cancel it
- the modifier applies only to otherwise-eligible skill gains
- it does not raise the 100.0 individual cap
- it does not raise the 700.0 total cap
- it does not bypass skill locks
- it does not bypass anti-macro/gain-eligibility rules
- it does not affect combat damage, crafting quality, taming control chance or other non-gain mechanics

Pilgrimage Inspiration stacks **additively** with the new-character Skill Gain Ball.

Examples:

- ordinary Pilgrimage + Skill Gain Ball = **+35% relative skill gain**
- top-five Pilgrimage + Skill Gain Ball = **+45% relative skill gain**

Do not multiply the bonuses together.

Only one unconsumed Pilgrimage Inspiration reward for the current completed weekly pilgrimage needs to be retained.

#### Weekly geographic coherence

Where practical, prefer a Pilgrimage route that reinforces the same broad geography as the current Expedition Region.

Example:

- Expedition: Britain → Yew
- Pilgrimage: Shrine of Justice
- active gathering: Yew region

This is a preference, not a hard dependency. Do not make the weekly-selection system impossible simply because perfect geographic pairing is unavailable.

The goal is to create moments when cargo runners, gatherers, pilgrims, rural homeowners and ordinary travelers all see one another along the same broad part of Britannia.

#### Optional long-term cosmetic record

Track successful pilgrimage completions by virtue for future **non-power** recognition.

Potential future rewards, requiring owner approval:

- `Pilgrim of Britannia` title after completing every eligible mainland virtue
- milestone titles
- decorative shrine/virtue items
- cosmetic robe/sash hues

Do not attach permanent skill-gain, stat, damage or other vertical-power progression to cumulative pilgrimage counts.

### 15.14 Road Travel Bonus

Roads should function as actual travel infrastructure rather than decorative terrain.

Launch rule:

> **Traveling on an approved road gives a modest movement-speed bonus.**

Target launch tuning:

- **on foot:** approximately **+15% movement speed**
- **mounted:** approximately **+10% movement speed**

Conceptual values:

`roadTravel.footSpeedMultiplier = 1.15`

`roadTravel.mountedSpeedMultiplier = 1.10`

The exact implementation may use the nearest stable movement-delay values supported by ModernUO/client movement timing. Do not force arbitrary fractional timing if it causes jitter, desynchronization or speedhack false positives.

#### Eligible roads

Use a server-authoritative audited road definition based on one or both of:

- approved road tile IDs
- explicit road-travel region overlays

Include important bridges/causeways where they are clearly part of the road network.

Do not trust client-reported road state.

The system should tolerate small edge transitions without buff-message spam or visible movement stutter.

#### General-world benefit

The road bonus is a **general world rule**, not only a Pilgrimage or Expedition modifier.

It should benefit:

- ordinary travelers
- Pilgrims
- Expedition trade-cargo carriers
- gatherers hauling through the Expedition corridor
- rural residents traveling to/from Britain and towns

This creates a persistent reason to choose the road network even when no weekly activity explicitly requires a road.

Do not globally reduce off-road movement speed. Wilderness remains normal baseline speed; roads are the bonus.

#### PvP / escape safeguards

Road speed must not become a combat-escape mechanic.

Disable the road movement bonus when:

- the character has an active relevant aggressor/aggressed PvP relationship or equivalent active player-combat state
- the character is inside a permanent or rotating PvP Hot Zone

Merely being red or grey while **not actively in PvP combat** does not by itself disable road travel.

Once active PvP combat/aggression has expired and the player is otherwise eligible, road speed may resume.

If current ModernUO movement/aggression timing requires a short server-authoritative grace period after PvP activity to prevent edge abuse, implement the smallest practical documented grace period.

#### Stacking

Road movement speed does not stack multiplicatively with future custom movement-speed bonuses unless explicitly approved.

If another custom movement bonus exists, define one authoritative movement-speed policy rather than multiplying arbitrary modifiers.

Road speed remains compatible with:

- Pilgrimage Scroll carrying
- Expedition trade cargo
- Expedition Logistics resource carrying

It changes movement only; it does not alter cargo restrictions, checkpoint requirements, stamina rules, weight rules or PvP legality.

#### Player feedback

Prefer a subtle buff/status indicator such as:

`Road Travel — Movement speed increased`

Do not emit chat/system text every time the character crosses individual road-edge tiles.

### 15.15 Player visibility

Players should be able to discover the active route without external websites.

Expose it through:

- login/status summary
- Britain activity board
- `[ShardRules` or equivalent activity/status command
- route-origin NPC/signage
- destination NPC/signage
- optional world-map label if practical without client modification

Suggested messaging:

`This week's Expedition is the Yew Forest. Trade caravans are running from Britain to Yew.`

Do not spam players repeatedly while they travel.

---

## 16. New Player Experience

Because ordinary Britannia is already safe from unsolicited blue-on-blue violence, do **not** add a separate account-age immunity system or a geographically protected starter shard.

New players should learn the actual launch rules from the beginning.

### 16.1 Starter package — immediate playability without character-creation arbitrage

New characters should be able to begin their chosen playstyle immediately without first creating an economic support character or spending the opening session acquiring a basic weapon, armor, reagents or tools.

Design principle:

> **Starter gear removes friction, not progression. It should be immediately useful, strictly ordinary in power, and have no exploitable character-creation resale loop.**

#### Four logged-in hours of starter protection

Issued starter equipment receives temporary **Starter Protection** for the first **4 hours of logged-in time on that character**.

The protection timer:

- advances only while that character is logged in;
- pauses on logout/disconnect;
- persists through save/restart;
- is not reset by death/resurrection;
- is not reset by character rename/template changes;
- is never re-granted because the character lost or destroyed an issued item.

While Starter Protection is active, issued starter equipment:

- does not drop as normal corpse loot;
- remains with the character through death;
- cannot be directly traded;
- cannot be placed on a player vendor;
- cannot be sold to an NPC;
- cannot be smelted, cut, salvaged or otherwise converted into economic materials;
- cannot satisfy BODs;
- cannot be used as a recipe input where doing so would extract transferable value.

After the character reaches **4 logged-in hours**, the death protection ends and ordinary issued equipment becomes subject to normal shard loss/loot rules.

However, the permanent `StarterIssued` economic marker should continue to prevent direct NPC resale, player-vendor sale, BOD use and salvage/resource extraction. Starter-issued gear exists to equip a new character, not to create an infinite item faucet through character deletion/recreation.

Direct trade may remain blocked for `StarterIssued` gear. After protection expires, the item can still change hands through normal world-loss mechanics such as corpse looting if the underlying item would normally be lootable. This is acceptable because the gear is ordinary vendor-quality and requires four logged-in hours before it can enter that risk loop.

Do **not** give starter equipment superior craftsmanship grades, magic tiers or special combat properties.

Starter equipment is always equivalent to **Standard / vendor-quality** equipment.

This ensures the player's first Well-Made crafted item or low-tier magic drop can immediately be exciting.

#### Universal starting package

Every newly created character receives:

- basic clothing appropriate to the selected character setup;
- backpack;
- one small organization pouch/bag;
- scissors;
- the already-settled 20 blessed, character-bound Skill Gain Balls;
- **one free physical Starter-Issued Backpack Ward** with ordinary priming/detection/120-second protection mechanics and no skill requirement;
- the invisible, nonconsumable **Loot Protection Ward entitlement** (server state, not a visible inventory item);
- a concise Welcome/Rules item or equivalent onboarding surface explaining both different Ward systems.

Do **not** automatically grant:

- a mount;
- a runebook;
- high-tier magic equipment;
- high-grade crafted equipment.

A first horse and first runebook should remain small, understandable early goals.

**Free Backpack Ward anti-farming rule:** Grant exactly one Starter-Issued Ward per newly created character, idempotently; it works as an ordinary one-use physical Backpack Ward but is character-bound, unstackable, nontradable, nondroppable, unbankable, unvendorable, non-salvageable and cannot be transferred through pets, shared or other-character containers, mail, another character or an NPC; movement among nested containers inside its own character’s equipped backpack remains allowed and retains normal lazy-priming behavior. Destroy an unused starter Ward on death rather than bless/insure or expose it as transferable corpse loot; consuming it by its actual detection effect is the only normal use. Never replace it on resurrection, relog or starter-package reentry. Creation/deletion cannot extract gold, items or materials from this grant. Regular purchased/crafted Wards retain their separately approved ordinary physical and death-loot rules; the starter-specific restrictions do not silently bind those normal items. The invisible Loot Protection entitlement is not a physical starter consumable and remains present beyond Starter Protection's four logged-in hours; never grant it more than once per character, and migrate existing characters once.

#### Starting gold

Grant approximately **500 gold once per gameplay account**, not once per character.

Store an account-level starter-gold entitlement so:

- deleting the first character does not re-grant it;
- creating additional characters does not create more gold;
- save/restart cannot duplicate it.

If the existing engine has a different unavoidable per-character starting-gold mechanism, replace or neutralize it rather than creating a repeatable character-creation faucet.

#### Melee starter package

A character whose selected starting skills clearly indicate melee receives:

- one appropriate Standard/vendor-quality weapon matching the strongest selected melee weapon skill;
- modest Standard/vendor-quality armor appropriate to the template rather than an endgame suit;
- a Standard shield if the selected skills indicate Parrying;
- **50 starter bandages**.

The objective is that the character can immediately fight an appropriate beginner monster.

#### Archer starter package

An archer receives:

- one Standard/vendor-quality bow or crossbow appropriate to the selected skill/template;
- modest Standard/vendor-quality armor;
- **100 starter arrows or bolts** as appropriate;
- **50 starter bandages**.

#### Mage starter package

A mage receives:

- a basic low-circle spellbook appropriate to launch UOR rules;
- a basic fallback weapon;
- ordinary clothing/robe;
- **50 of each classic reagent**.

Starter reagents are character-bound/non-sellable starter consumables. They may be consumed normally for spellcasting but may not be traded, vendored, dropped for transfer, or converted into economic value merely by character creation.

Do not give a fully completed high-circle spellbook at character creation. Filling and upgrading a spellbook should remain an early economic/social goal.

#### Crafter/gatherer starter package

Characters that actually select a crafting/gathering skill at character creation should receive enough starter material for a meaningful introductory crafting session rather than only a handful of attempts.

Initial tuning targets:

| Profession | Starter material target |
| --- | --- |
| Blacksmith | **250 iron ingots** |
| Tinker | **200 iron ingots** |
| Tailor | **300 cloth + 50 leather** |
| Carpenter | **250 boards** |
| Bowyer/Fletcher | **200 boards + 100 feathers** |
| Scribe | **75 blank scrolls + 50 of each classic reagent** |
| Alchemist | **75 empty bottles + 50 of each relevant classic reagent** |
| Cook | approximately **50–75 basic recipe attempts** worth of ordinary ingredients |
| Other approved launch craft | enough ordinary inputs for approximately **40–60 low-level attempts**, tuned by recipe cost |

Also issue the profession's ordinary Standard/vendor-quality starting tools.

These quantities are onboarding targets and should remain configurable after testing.

#### Starter material anti-exploit rule

Starter raw materials are different from starter gear.

The **raw starter material itself** must be:

- character-bound while unconsumed;
- non-sellable;
- non-tradeable;
- non-player-vendorable;
- non-droppable for another character to acquire;
- unable to be transferred through pets/pack animals;
- unable to be converted back into unrestricted raw resources;
- unable to merge with unrestricted stacks in a way that erases its starter provenance.

Most importantly, starter materials are **not an infinitely refreshable character grant**.

Maintain an account-level entitlement ledger per crafting profession/category:

- each account can receive each profession's starter-material package only once;
- deleting the character does not restore that profession's entitlement;
- recreating another Blacksmith does not issue another Blacksmith material package;
- a separate eligible profession may still claim its own one-time package;
- only a character that selected the relevant profession at creation may consume that entitlement.

This finite account-level grant is the primary protection against creating/deleting crafters for free resources.

#### No `Starter-Crafted` state

There is deliberately **no** `Starter-Crafted` item state.

Once a player consumes starter resources to successfully craft an item, the resulting item is a completely normal crafted item.

It:

- receives the normal craftsmanship-quality roll;
- can roll any craftsmanship grade the character's actual skill has unlocked;
- receives normal maker attribution;
- can be equipped and used normally;
- can be traded normally;
- can be sold to another player normally;
- can be placed on a player vendor normally;
- can be sold to NPCs under ordinary crafted-item resale rules;
- can be looted/lost under ordinary rules;
- can satisfy BOD requirements if it otherwise qualifies;
- can be repaired/salvaged according to ordinary rules;
- carries **no hidden starter provenance** from the inputs.

Design principle:

> **The free resource grant is limited; the player's labor is not devalued.**

If a new smith uses their one-time starter ingots and happens to create a Fine, Masterwork or other valuable item, they did the work and receive the full economic benefit of that item.

Do not solve character-creation exploits by penalizing legitimate crafted output.

#### Starter consumables

Starter bandages, ammunition, reagents and similar directly issued consumables should:

- be usable normally by the receiving character;
- remain character-bound/non-sellable while they retain the starter marker;
- not be directly convertible into saleable raw materials;
- not merge with unrestricted stacks in a way that launders provenance.

They may simply disappear through normal consumption.

For a profession-specific crafting package such as Inscription or Alchemy, starter ingredients may be consumed by that profession and the resulting crafted item is normal under the **No `Starter-Crafted` state** rule above.

#### Starter-package economy target

The package should let a player **play immediately**, not create meaningful wealth by repeatedly creating characters.

Economy validation should therefore measure two separate cases:

1. **legitimate use:** a first-time character uses the package to adventure or craft;
2. **adversarial use:** an experienced player repeatedly creates/deletes characters trying to extract account value.

The second case should produce no sustainable gold/resource faucet because:

- account gold is one-time;
- profession starter resources are one-time per account/profession;
- unconsumed starter items/materials cannot be sold or transferred;
- issued gear is Standard quality and economically restricted;
- the free Backpack Ward cannot leave its character or yield wealth and is not replenished by resurrection/relogin; the invisible Loot Protection entitlement has zero item/economic value;
- only actual crafted output becomes unrestricted.

Required onboarding should explain:

- ordinary Britannia is safe from unsolicited direct attacks by innocent players
- stealing is enabled outside the active Cool Dungeon and mapped bank protection regions, subject to activated Backpack Wards; snooping remains enabled everywhere
- outside protected regions, stealing can turn a player grey and make them lawfully attackable
- the free Starter-Issued Backpack Ward operates like normal purchased Wards: one chosen physical item primes lazily after theft activity, can detect after resolution, and then protects the backpack for two minutes; the third successful theft is guaranteed detected **per thief account on that Ward**
- the invisible permanent Loot Protection Ward allows a first unauthorized monster-corpse item transfer but temporarily blocks that offender account from repeating unlawful looting of the same player’s protected monster corpses for ten minutes; it does not affect public corpses or Hot Zones
- reds/murderers can be attacked anywhere
- Hythloth is permanently Hot
- Fire Island is permanently Hot
- Buccaneer's Den and its entire island are permanently Hot
- one additional dungeon is Hot each week
- one separate non-PvP dungeon is the Cool Dungeon of the Week and receives a modest safe PvE bonus
- one outdoor Expedition Region and its Britain-origin trade route are active each week; trade cargo must be moved physically through the route rather than Recalled/Gated
- entering a Hot Zone exposes the player to unrestricted player attacks and full-loot risk
- Hot Zones pay materially better rewards
- combat pets remain prohibited in dungeons even when a dungeon is Hot
- each newly created character receives 20 blessed, character-bound Skill Gain Balls; each provides +25% relative skill gain for one hour of logged-in time
- weekly Pilgrimage starts in Britain during announced departure windows and requires physical travel to the current mainland shrine
- roads provide a modest travel-speed bonus outside active PvP/Hot Zones

Provide a concise login/status summary and an in-world board in the primary social hub.

Do not reduce ordinary monster difficulty for new players solely because the world is safe from unsolicited PvP.

---


## 16A. Roleplay Points of Interest and Issued Role Gear

The shard should actively lower the friction required to **start roleplaying in the world itself** without creating a separate RP ruleset, a faction grind or a source of tradable free equipment.

Launch scope is deliberately narrow:

1. **Yew Orc Fort — Orc Clan**
2. **Yew Graveyard / Old Yew Crypts — Undead / Cult**
3. **Yew civic / Court area — Yew Militia / Wardens**
4. **Buccaneer's Den — Pirates / Outlaws**

The first three form the shard's intentional **Yew RP Trinity**:

> **Yew Militia ↔ Orc Clan ↔ Undead / Cult**

These are not mechanical factions. They are recognizable social identities placed close enough together that players can naturally create rivalries, alliances, patrols, raids, negotiations and stories.

Buccaneer's Den is the one launch RP identity outside Yew because its permanent Hot-Zone/criminal identity already makes it a natural home for pirate and outlaw roleplay.

Do **not** launch the previously considered Cove, Trinsic, Skara Brae, Moonglow, Britain Theatre or other wardrobe locations. They remain possible future additions only if actual RP participation demonstrates that another permanent hub would improve rather than fragment the community.

### Design principle

> **If a player sees an interesting role and thinks “I want to play that part,” the world should let them become visually and mechanically ready for that role within a minute.**

The issued equipment should therefore be **real usable equipment**, not zero-stat costume props.

However:

> **Roleplay gear is a convenience-quality combat set, not an economic product and not an endgame equipment source.**

It must be good enough to adventure, patrol, defend an RP location or participate in ordinary low/mid-level combat while remaining clearly below high-end crafted gear and high-tier magic equipment.

### Historical / community basis

The launch identities should remain anchored in classic Britannia and long-running UO roleplay traditions:

- the **Yew Orc Fort** was already a major player-orc roleplay location in 1998, including the Shadowclan tradition;
- later UO roleplayers continued to associate Yew with orc territory, Yew defenders/militia and undead/evil activity around its graveyard/crypt geography;
- **Orcs versus Yew Militia** and undead-army roleplay are recognizable classic UO patterns;
- **Buccaneer's Den** has a longstanding Britannian identity as a pirate, outlaw and thieves' haven.

Use this history as inspiration, not as a requirement that players reproduce old guild politics, dialect rules or another shard's exact RP customs.

### Roleplay is encouraged, never required

Do **not** require players to:

- remain in character merely because they enter an RP POI;
- join a guild;
- use a special chat channel;
- adopt a prescribed accent or vocabulary;
- wear issued RP gear to participate in roleplay;
- participate in PvP because their chosen role historically did;
- complete RP dailies, reputation tracks or faction grinds;
- earn permanent character power by roleplaying.

Wearing Orc gear does not mechanically make the character an orc. Wearing Undead gear does not make the character undead. Wearing Militia gear does not grant law-enforcement authority. Wearing Pirate gear does not automatically make the character criminal.

The social role and the shard's hostility/notoriety systems remain separate.

### In-Character `[IC]` status toggle

Provide a simple voluntary **In Character** status that lets a player advertise that they are currently open to roleplay interaction.

Player-facing behavior:

- a character may toggle the state on/off with a simple command such as `[IC` and, if practical, an equivalent context-menu option;
- while enabled, a subtle **`[IC]`** marker appears with that character's ordinary visible name/title presentation (for example in single-click/overhead name information) without replacing notoriety hue, guild abbreviation or normal name data;
- the state persists through logout, death and server restart until the player explicitly toggles it off;
- toggling has no cooldown and costs nothing.

The meaning of the tag is intentionally narrow:

> **`[IC]` means “I am open to being approached in character.” It does not mean “I consent to PvP,” “I am part of a mechanical faction,” or “I must remain in character at all times.”**

The IC state must not:

- change PvP/hostility legality;
- change stealing/criminality/notoriety;
- change guild-war consent;
- change NPC aggression;
- change race/faction/kin status;
- provide rewards, buffs, skill gain or loot bonuses;
- expose hidden/invisible characters differently from ordinary rules;
- prevent the player from toggling it off at any time.

Suggested configuration:

```text
roleplay.icTag.enabled = true
roleplay.icTag.defaultEnabled = false
roleplay.icTag.persistUntilToggled = true
roleplay.icTag.text = [IC]
roleplay.icTag.affectsMechanics = false
```

### RP Gear Chest behavior

Each of the four launch RP POIs receives one permanent, staff-owned themed chest.

Conceptual server class:

`RoleplayGearChest`

The chest must:

- be immovable, non-stealable and non-destroyable;
- persist through save/restart;
- never become empty;
- issue server-defined **full gear bags**, not loose unlimited individual pieces;
- obey the surrounding region's ordinary safe/Hot/Cool/notoriety rules;
- create no safe bubble, invulnerability or hostility exception.

Preferred interaction:

1. player double-clicks the themed chest;
2. the chest shows **at least three distinct themed full-kit bags** for that POI;
3. player claims **one complete Roleplay Gear Bag**;
4. the bag is created in the character's backpack if normal weight/item-count checks permit it;
5. claiming the bag starts that character's RP-gear claim cooldown.

The source templates never leave the chest.

### One full RP kit per rolling 24 hours

A character may claim **one RP Gear Bag total across the entire RP system per rolling 24-hour period**.

This is a global character-level entitlement, not one claim from each chest.

Example:

- claim the Orc kit at 18:00 Monday;
- cannot claim an Undead, Militia or Pirate kit until 18:00 Tuesday.

Use server-authoritative time.

Do not use client clock or timezone.

The cooldown:

- survives logout;
- survives save/restart;
- survives character rename;
- is destroyed with the character;
- **resets immediately when that character dies**;
- cannot be reset merely by dropping, manually destroying, wearing out or otherwise losing the previous gear while alive;
- cannot be bypassed by moving between RP POIs.

The death reset is intentional. Because all existing `RoleplayIssued` gear is destroyed on that death and cannot be transferred or liquidated, death acts as a replacement path rather than a multiplication path. A character who dies may immediately return to any RP chest and claim one new full kit, which then starts a fresh 24-hour cooldown.

At no point may a living character use the death reset to retain an old issued set while claiming a new one. Death cleanup of all `RoleplayIssued` items must complete atomically before the entitlement reset becomes claimable.

The player-facing chest should clearly display the remaining claim time rather than silently refusing access.

Suggested launch setting:

`roleplay.gear.claimCooldownHours = 24`

Do not make this account-wide at launch. The restriction is **one kit per character per 24 hours**. If multi-character farming of bound gear creates a real operational problem despite the non-economic restrictions below, revisit the entitlement scope with owner approval.

### Full-set bags, not an unlimited clothing faucet

Every claim produces one curated bag containing a complete outfit suitable for the selected role. **Each RP chest must offer at least three visually and thematically distinct full-kit bags at launch.**

The bag itself should be temporary packaging. Once opened, it may disappear after moving its contents into the character's backpack.

Do not allow players to repeatedly pull individual helmets, masks, chest pieces or weapons from the wardrobe.

The one-live-set / 24-hour entitlement is the scarcity/control mechanism. A character chooses one of the chest's themed bags per claim; claiming one variant consumes the same global entitlement as any other variant.

A kit may contain, as appropriate:

- clothing;
- headwear/mask;
- boots/gloves;
- armor;
- shield;
- melee or ranged weapon;
- role-appropriate non-consumable visual accessories.

Do **not** include recurring free consumable supplies such as:

- reagents;
- bandages;
- arrows/bolts;
- potions;
- food;
- blank scrolls;
- crafting materials;
- gold;
- tools with extractable economic value.

Those remain part of the normal player economy.

### Functional power target — low/mid-tier crafted equivalent

Issued RP weapons and armor are **real combat equipment**.

Launch target:

> **Equivalent in combat performance to a low-to-mid craftsmanship tier, with `Fine`-equivalent player-crafted equipment as the initial benchmark.**

This means:

- weapon damage is real;
- armor protection is real;
- shields/parry interaction is real;
- normal weapon/armor skill requirements and era mechanics apply;
- equipment has ordinary combat durability unless a role-specific art wrapper requires a separately configured durability profile.

However, issued RP gear:

- has no maker's mark;
- is not considered player-crafted;
- carries no craftsmanship grade for BOD/economy purposes;
- cannot exceed the configured RP power profile;
- cannot roll randomly into Superior/Exceptional/Masterwork/Grandmaster quality;
- cannot receive a magic-item tier;
- cannot receive Slayer properties;
- cannot receive randomized magical properties;
- must remain below high-end crafted gear and well below top-tier magic loot.

Where the crafting system exposes reusable stat profiles, prefer referencing the same **Fine-equivalent functional profile** rather than duplicating combat numbers.

If Fine is later retuned, the RP gear profile should be reviewed so it remains in the intended low/mid band rather than silently becoming stronger than planned.

### Crafting/economy relationship

The gear is intentionally useful, so it will compete somewhat with entry-level equipment. That is acceptable, but it must not replace the player economy.

The intended market relationship is:

- **RP-issued gear:** free, bound, low/mid-tier, fixed appearance, fixed stats, no resale value;
- **crafted gear:** tradeable, sellable, repairable through the normal economy, customizable by item type/material/quality, capable of exceeding RP gear;
- **magic loot:** tradeable/loss-bearing and capable of exceeding crafted raw-power bands at the upper tiers.

The reason to acquire crafted or magic gear remains:

- better performance;
- better quality;
- preferred weapon/armor type;
- material choice;
- durability;
- player trade value;
- maker identity;
- long-term ownership and flexibility.

The wardrobe is therefore a **roleplay onboarding/convenience source**, not a substitute for endgame crafting.

### Character-bound / non-economic item state

Every issued item must carry server-authoritative state conceptually equivalent to:

`RoleplayIssued`
`BoundCharacterSerial = <character>`

The item may be used only by the character to whom it was issued.

At launch, RoleplayIssued items:

- **cannot be directly traded**;
- **cannot be dropped on the ground for another player**;
- **cannot be placed on a player vendor**;
- **cannot be sold to an NPC**;
- **cannot be placed in another character's bank/container**;
- **cannot be placed in a house secure or locked-down container**;
- **cannot be transferred through pets or pack animals**;
- **cannot be mailed or placed into future cross-character delivery systems**;
- **cannot be commodity-deeded or otherwise converted into transferable form**;
- **cannot satisfy BODs**;
- **cannot be smelted, cut, salvaged or recycled into resources**;
- **cannot be used as a crafting ingredient that outputs unrestricted value**;
- **cannot be insured**;
- has **zero NPC/reference liquidation value**;
- has no player-vendor advance value;
- cannot be used to repay or collateralize any player-vendor/market system.

Do not allow stack merging, deed conversion, repair contracts or another transformation path to strip the bound state.

### Death behavior — useful gear without creating a transfer exploit

Roleplay gear should **not be blessed**.

It is functional combat equipment and should not become permanent free insured armor merely because it came from an RP chest.

However, ordinary corpse transfer would allow players to bypass the character-bound rule by intentionally dying to another character.

Launch rule:

> **RoleplayIssued equipment is destroyed on player death instead of becoming transferable corpse loot.**

On death:

- all equipped/carried `RoleplayIssued` gear belonging to that character is deleted;
- it does not appear as lootable equipment on the corpse;
- the RP claim cooldown is **reset immediately** after the death cleanup completes;
- ordinary non-RP equipment follows the shard's normal corpse/full-loot rules.

This preserves death as a real interruption—the equipped set is gone—while allowing the player to resume the role immediately by returning to an RP chest. Because the destroyed set cannot survive the death or be transferred, repeated death/reclaim cycles do not create additional live or tradable inventory.

The system should display a concise warning when claiming a kit:

`Issued roleplay gear is bound to this character and is lost on death. Death resets your RP gear claim so you may choose a replacement set.`

This exception should remain narrowly scoped to RoleplayIssued gear. It must not become a general bound-item or insurance precedent for ordinary combat equipment.

### Durability / repair policy

Use normal durability loss while the item exists.

At launch, RoleplayIssued items may be repaired by the bound character through otherwise valid era-appropriate repair mechanics **only if the repair path does not transfer ownership or create resource/value exploits**.

If the existing repair system cannot safely preserve binding, disable repair on RoleplayIssued gear and rely on the next daily claim after loss/wear.

Do not grant infinite durability.

Do not allow repair deeds or another portable service item to strip the bound marker.

### NPC aggression / disguise / faction safeguards

Roleplay gear changes appearance and combat stats only.

It must not:

- pacify orcs because the wearer has an orc mask;
- make undead friendly;
- grant Yew guard authority;
- make town guards ignore criminal behavior;
- make Buccaneer's Den NPCs friendly;
- alter notoriety;
- alter race;
- alter guild/faction status;
- alter stealing legality;
- alter Hot/Cool/safe-world hostility;
- alter red/grey retaliation rules.

If an art item in upstream UOContent contains a kin/faction/disguise mechanic, create a shard-specific wrapper that uses the art while excluding that mechanic.

### Era-art restriction

The kits should overwhelmingly use item art, clothing, armor, masks and hues appropriate to the UOR-era presentation.

Before adding an item:

1. verify the art exists in the supported client;
2. verify it visually fits UOR;
3. audit the upstream item class for modern stats/special mechanics;
4. use a shard-specific wrapper if the visual art is appropriate but the original class contains later-era behavior.

Do not introduce conspicuously later race armor, artifact visuals or neon expansion aesthetics merely because the client supports them.

### Launch POI 1 — Yew Orc Fort: Orc Clan

POI:

- classic Yew Orc Fort; exact UOR Felucca location/region to be map-audited.

Theme:

- player orcs;
- clan warriors;
- shamans;
- scouts;
- crude tribal fighters.

Player-facing chest concept:

`Orc Clan War Chest`

The chest must offer at least these three distinct full-kit bags at launch:

**Orc Grunt**
- era-appropriate orc mask visual wrapper;
- earth-tone shirt/kilt/sash;
- leather/ringmail-style armor mix;
- boots/gloves;
- crude axe/sword-family melee weapon;
- optional shield where the chosen weapon allows it.

**Orc Shaman**
- orc mask visual wrapper;
- dark/earth-tone robe or rough clothing;
- lighter armor integrated beneath/around the silhouette where practical;
- staff/mace-family real weapon;
- no free reagents or spellbook.

**Orc Raider**
- distinct mask/hue/clothing combination;
- rough leather/ring armor;
- spear/fencing-family or heavy two-handed melee weapon;
- no extra consumables.

The three bags should be visibly distinguishable at a glance. All combat pieces use the same configured RP Fine-equivalent power envelope where applicable; one Orc kit must not become the statistically optimal choice merely because of its theme.

Wearing the kit never grants orc NPC friendship or kin protection.

### Launch POI 2 — Yew Graveyard / Old Yew Crypts: Undead / Cult

POI:

- Yew graveyard and/or immediately associated crypt geography after exact UOR map audit.

Theme:

- undead characters;
- necromantic cultists;
- grave keepers;
- death priests;
- haunted warriors/nobles.

Player-facing chest concept:

`Crypt Reliquary`

The chest must offer at least these three distinct full-kit bags at launch:

**Crypt Knight**
- dark/grey armor;
- deathly or masked headwear using era-appropriate art;
- dark cloak/sash;
- sword-family weapon and shield where appropriate.

**Death Cultist**
- black/grey/dark-red robe/clothing;
- appropriate headwear;
- light armor integrated where visually compatible;
- staff/mace-family real weapon;
- no free reagents, spellbooks or consumables.

**Grave Stalker**
- tattered/dark field clothing;
- leather-oriented armor;
- skull/death-themed headwear where era-appropriate;
- spear/fencing-family or other light real weapon.

The three bags should read as different undead/cult archetypes while remaining inside the same configured RP power envelope. The kit does not make the player undead and does not alter undead monster aggression.

### Launch POI 3 — Yew Militia / Wardens

POI:

- approved Yew civic/Court/road-defense area after exact map audit.

Theme:

- Yew militia;
- forest wardens;
- town watch;
- rangers;
- hunters.

Player-facing chest concept:

`Yew Militia Supply Chest`

The chest must offer at least these three distinct full-kit bags at launch:

**Yew Guardsman**
- Yew-colored surcoat/shirt/sash;
- chain/ring/leather armor as art permits;
- boots/gloves;
- sword/mace-family weapon;
- shield.

**Forest Warden**
- green/brown field clothing;
- leather-oriented armor;
- spear/fencing-family or other practical woodland melee weapon.

**Yew Ranger**
- distinct green/brown scout silhouette;
- leather-oriented armor;
- bow/crossbow-family real weapon;
- no free arrows/bolts, so ammunition remains part of the player economy.

All three bags remain in the same RP power envelope even when weapon archetypes differ. Militia gear does not confer guard powers, legal authority or permission to attack Orc/Undead-costumed blue players.

### Launch POI 4 — Buccaneer's Den: Pirates / Outlaws

POI:

- Buccaneer's Den public criminal/PvP social area; exact chest placement should be visible but should not obstruct bank, docks, roads or combat geometry.

Theme:

- pirates;
- smugglers;
- thieves;
- outlaw sailors;
- criminal crews.

Player-facing chest concept:

`Buccaneer's Slop Chest`

The chest must offer at least these three distinct full-kit bags at launch:

**Corsair**
- bandana/skullcap/headwear;
- sash;
- shirt/vest-style appearance using era-appropriate pieces;
- boots;
- light/medium armor integrated into the silhouette;
- cutlass-like sword-family real weapon.

**Boarding Brute**
- rough sailor/outlaw clothing;
- heavier leather/ring/chain mix where visually appropriate;
- axe/mace-family real weapon;
- distinct silhouette from the Corsair.

**Smuggler**
- dark practical clothing;
- leather armor;
- cloak/sash;
- dagger/fencing-family real weapon.

No free stealing tools, lockpicks, reagents, potions or consumable supplies. All three bags remain in the same configured RP power envelope.

Buccaneer's Den remains a permanent unrestricted Hot Zone. Opening the chest or wearing its gear grants **no protection**.

A blue wearing Pirate gear is still blue. A red wearing Pirate gear remains red.

### Guild Scene Prop Bags

Each of the four RP chests also supports **temporary guild-created RP scenes**.

The purpose is to let an actual group visibly occupy an RP location for an evening without requiring staff to decorate the scene manually and without granting permanent housing, territorial ownership or mechanical bonuses.

Core rule:

> **A Scene Prop Bag may be claimed only by the guild's current leader while at least three additional members of that same guild are physically nearby.**

This means a minimum of **four members of one guild** must be present at the RP POI at claim time:

- the guild leader who operates the chest; plus
- at least **3 other online characters in the same guild**.

Recommended launch proximity:

`roleplay.sceneProps.requiredNearbyGuildMembers = 3`  
`roleplay.sceneProps.nearbyRangeTiles = 12`

Nearby qualifying members must:

- be online;
- be alive;
- be on the same map;
- be within the configured range of the chest/claiming leader;
- belong to the same guild as the leader;
- be distinct characters;
- not count pets, summons, NPC guild members or staff-only entities.

Do not require those three supporting guild members to remain nearby after the claim. Their presence is a **group-formation gate**, not an AFK tether.

If the guild has no currently recognized leader under the underlying guild system, no Scene Prop Bag may be claimed until leadership is valid.

#### Three scene themes per RP chest

Every launch RP chest must offer **exactly three launch Scene Prop Bag themes**, adapted visually to that POI's identity:

1. **Camp / Meeting Scene**
   - campfire/brazier or equivalent;
   - benches, stools, tables or bedroll-style props;
   - crates/sacks/barrels that are decorative only;
   - banners, torches or other gathering-place dressing.

2. **Ritual / Ceremony Scene**
   - candles, braziers, lectern/altar-like table or ritual focal point;
   - skulls, urns, books, offerings or heraldic equivalents where appropriate;
   - banners/standards/torches appropriate to the local role;
   - purely decorative ceremonial dressing.

3. **Conflict / Aftermath Scene**
   - barricade-looking props, shields, weapon racks, broken crates or battlefield dressing;
   - training/guard-post props where more appropriate than gore;
   - torches, standards and debris;
   - no mechanically usable weapons, ammunition or loot containers.

The three bags are **scene archetypes**, not identical item lists. Each RP POI should use art/hues that fit its local identity:

- **Yew Orc Fort:** crude camp / shamanic ritual / raider aftermath;
- **Yew Graveyard:** grave-watch camp / death ritual / haunted aftermath;
- **Yew Militia:** patrol camp / civic or oath ceremony / defensive checkpoint aftermath;
- **Buccaneer's Den:** pirate camp / crew oath or illicit ceremony / dockside raid aftermath.

Each bag should contain enough props to make a recognizable small scene for roughly 4–12 participants without carpeting the area in objects.

#### Claim, transfer, cooldown and active-scene limits

Scene props are not a daily reward faucet. They are temporary group infrastructure.

The Scene Prop system has its **own cooldown**, completely separate from the character's RP costume/gear claim cooldown.

Launch rules:

- a guild may claim **one Scene Prop Bag per rolling 24 hours across the entire RP system**;
- this **24-hour Scene Prop Bag cooldown belongs to the guild**, not to the leader or the character holding the bag;
- the cooldown begins immediately when the guild leader successfully claims a Scene Prop Bag;
- claiming from Yew Orc Fort prevents that same guild from claiming another Scene Prop Bag from Yew Graveyard, Yew Militia or Buccaneer's Den until the guild cooldown expires;
- expiration, destruction, transfer, deployment or early cleanup of the claimed bag/scene does **not** reset or shorten the 24-hour guild cooldown;
- guild-leader death does not reset the Scene Prop Bag cooldown;
- the RP costume/gear cooldown remains a separate per-character entitlement and is unaffected by Scene Prop Bag claims;
- a guild may have **only one active Scene Prop deployment across the RP system at a time**;
- a guild may not claim a new Scene Prop Bag while it still possesses an unopened valid Scene Prop Bag or has an active scene, even if an administrative cooldown reset occurred;
- the guild leader chooses one of the three scene themes when claiming;
- claiming creates one temporary `RoleplayScenePropBag` bound to that **guild and source POI**, with the leader recorded as the original claimant;
- an unopened bag expires after **15 minutes**;
- scene props automatically expire after **4 hours** from deployment;
- save/restart preserves the remaining bag expiry, scene lifetime and guild cooldown rather than resetting any of them.

Suggested launch values:

```text
roleplay.sceneProps.enabled = true
roleplay.sceneProps.requiredGuildLeader = true
roleplay.sceneProps.requiredNearbyGuildMembers = 3
roleplay.sceneProps.nearbyRangeTiles = 12
roleplay.sceneProps.claimCooldownHoursPerGuild = 24
roleplay.sceneProps.maxUnopenedBagsPerGuild = 1
roleplay.sceneProps.maxActiveScenesPerGuild = 1
roleplay.sceneProps.unopenedBagExpiryMinutes = 15
roleplay.sceneProps.sceneLifetimeMinutes = 240
roleplay.sceneProps.themeCountPerPoi = 3
```

Do not make Scene Prop Bag eligibility depend on IC-tag use. The IC tag is individual social signaling; the scene system is a guild group-presence tool.

#### Guild-internal Scene Prop Bag transfer

The guild leader must be the character who **authorizes and claims** a Scene Prop Bag, but the leader does not have to be the person who carries or deploys it.

After claim, the leader may transfer the unopened bag to another **current member of the same guild**.

The bag is therefore:

- **guild-bound**, not permanently leader-bound;
- directly tradeable between current members of its owning guild;
- deployable by the current holder only while that holder is still a member of the owning guild;
- never tradeable to a character outside the owning guild;
- never sellable to an NPC or player vendor;
- never droppable as an unrestricted ground-transfer item;
- never storable in a house, bank, pet, pack animal, mailbox or other location that could bypass guild-membership validation;
- still tied to its original source POI and scene theme after transfer;
- still subject to the original 15-minute unopened-bag expiry after transfer;
- still subject to the owning guild's original 24-hour claim cooldown after transfer.

A transfer does **not**:

- start a new cooldown;
- reset the current cooldown;
- extend bag lifetime;
- permit another guild claim;
- change the bag's source POI;
- change the selected scene theme.

If the current holder leaves or is removed from the owning guild before deployment, the bag becomes unusable and should be deleted at the next safe validation tick rather than becoming transferable property.

At deployment time, revalidate:

- the holder is a current member of `OwningGuildId`;
- the bag is unexpired;
- the guild does not already have another active scene;
- placement is inside the source POI's allowed Scene Area.

The three nearby-guild-member requirement applies at **claim time only**. It does not need to be re-satisfied merely because the guild leader transfers the bag to another member for setup.

#### Placement restrictions

Scene props may be placed only inside a configured **RP Scene Area** around the POI from which the bag was claimed.

They must not be placeable:

- outside that POI's configured scene region;
- inside player houses;
- into containers;
- on boats;
- across dungeon/region boundaries;
- on teleporters/moongates/doors/stairs;
- on or immediately adjacent to critical roads, docks or chokepoints where they obstruct movement;
- in locations that create line-of-sight exploits, safe spots, pathing traps or PvP geometry advantages.

Prefer decorative prop classes with **no collision / no movement blocking** where the client/server presentation permits it.

If a prop necessarily has collision, placement validation must guarantee adequate walkable paths around it.

Buccaneer's Den remains a Hot Zone. Scene props there must be especially conservative about collision and line-of-sight so an RP scene cannot become a combat fortification.

#### Non-economic / non-mechanical prop state

All objects created from Scene Prop Bags are temporary RP decorations.

They must:

- have zero NPC/reference/player-vendor value;
- be non-stealable as economic objects;
- be non-salvageable;
- be non-containerized storage even if their art looks like a chest/crate/barrel;
- contain no usable resources, weapons, armor, reagents, food or consumables;
- grant no buffs, healing, damage, cover, skill gain, crafting bonuses or other gameplay effects;
- not affect notoriety, guild war, faction, NPC aggression or hostility legality;
- not become house lockdowns/secures;
- not be permanently redeeded;
- disappear cleanly at scene expiration without leaving item remnants or extractable contents.

Conceptual state:

`RoleplaySceneProp`  
`OwningGuildId = <guild>`  
`SourcePoiId = <poi>`  
`SceneId = <scene>`  
`ExpiresAt = <server time>`

The bag itself is **transferable only between current members of its owning guild** under the guild-internal transfer rules above. It remains non-sellable, non-bankable, non-ground-transferable to outsiders and non-storable in houses/pets. If the claimant or current holder disconnects after claim but before opening, the short bag-expiry timer still runs.

#### Scene ownership and cleanup

The claiming guild leader authorizes the scene, but ownership belongs conceptually to the **guild scene**, not as a permanent personal asset. A same-guild member who receives the unopened bag may deploy it under the validation rules above.

At minimum:

- the current guild leader may voluntarily dismiss the entire scene early;
- staff may dismiss a scene immediately;
- props automatically delete at expiry;
- original claimant logout does not instantly destroy an active scene;
- original claimant death does not reset/duplicate the scene, create another bag or alter the guild's 24-hour Scene Prop cooldown;
- guild disbanding removes the unopened bag/active scene at the next safe cleanup tick;
- changing guild leadership does not duplicate or reset the guild's Scene Prop entitlement;
- no scene prop can be picked up and carried away as a normal item after placement;
- cleanup of a scene frees the active-scene slot but **does not clear the guild's 24-hour bag-claim cooldown**.

#### Scene-prop anti-exploit requirements

Prevent at minimum:

- one character counting multiple times toward the three-member requirement;
- alts outside the same guild counting as support members;
- dead/offline members counting;
- claiming from multiple POIs simultaneously for the same guild;
- leadership transfer creating an extra active scene or resetting the guild cooldown;
- transferring a Scene Prop Bag to a non-guild character;
- bag transfer resetting/extending its expiry or the guild claim cooldown;
- a holder leaving the guild and retaining/deploying the bag;
- guild disband/re-form loops duplicating a scene or bypassing the cooldown;
- save/restart duplicating bags or props;
- picking up/deeding/stealing props into permanent ownership;
- using decorative containers as storage;
- blocking doors, roads, stairs, docks, moongates or narrow passages;
- creating combat cover/line-of-sight exploits;
- obtaining usable weapons/resources from weapon racks, crates, barrels or similar visual props;
- converting prop art through salvage/crafting/vendor systems;
- using Buccaneer's Den scenes as temporary fortifications.

### Role Guide in every chest

Each chest should display a short read-only **Role Guide** taking less than one minute to read.

It should answer:

1. Who might I be?
2. Why am I at this location?
3. What are two or three easy things I can do in character?
4. Who might be my natural friends or rivals?
5. What is one example greeting or mannerism?

Keep the guidance invitational, not prescriptive.

#### Orc example

Possible prompts:

- defend the fort;
- demand tribute;
- patrol nearby roads;
- trade crude goods;
- distrust Yew militia;
- challenge undead trespassers;
- use rough speech if desired.

Do not require Shadowclan vocabulary or another historical guild's exact language rules.

#### Undead example

Possible prompts:

- haunt the graveyard;
- recruit living cultists;
- demand offerings;
- threaten nearby Yew;
- bargain with or betray the orcs;
- conduct funerary/ritual scenes.

#### Militia example

Possible prompts:

- patrol Yew;
- question suspicious travelers;
- negotiate with or confront orcs;
- protect civilians from undead;
- escort pilgrims/traders;
- organize militia drills.

#### Buccaneer example

Possible prompts:

- recruit a crew;
- boast about raids;
- negotiate illicit deals;
- challenge rival pirates;
- prey socially on visitors without violating shard rules;
- use the permanent Hot Zone for consensual/emergent dangerous outlaw RP.

### RP Directory

Keep discovery intentionally small.

The Roleplay Directory should list only:

- Yew Orc Fort — Orc Clan
- Yew Graveyard / Crypts — Undead / Cult
- Yew Militia — Militia / Wardens
- Buccaneer's Den — Pirates / Outlaws

For each entry show:

- approximate directions;
- role theme;
- whether the surrounding region is currently safe or permanently Hot;
- the one-kit-per-24-hours rule;
- the fact that issued gear is useful but bound, unsellable and lost on death.

Do not provide instant teleportation.

Do not advertise unimplemented future RP hubs in the launch directory.

### 16A.1 Roleplay POI Guestbooks — approved persistent in-world storytelling (#31)

**Status: approved.** Add exactly **four** permanent staff-owned guestbooks at the four *existing* launch RP POIs, near their respective RP Gear Chests, after surveying exact map coordinates and checking that books do not obstruct movement or protected geometry. Do not open another POI, create a new roleplay/faction system, or demand ongoing GM story events to make the books functional.

| Existing POI | Proposed themed guestbook |
|---|---|
| Yew Orc Fort | **Orc Clan Chronicle** |
| Yew Graveyard / Old Yew Crypts | **Book of the Departed** |
| Yew Militia / Wardens at the approved Yew civic/Court location | **Warden's Log** |
| Buccaneer's Den | **Captain's Ledger** |

Use an existing UOR-compatible book graphic/interface where feasible, or a narrow custom paginated book-like interface without requiring modified clients or custom art. Each physical book is immovable, non-stealable, indestructible, persistent and usable only in interaction range. Books are not player-editable `BaseBook` contents: entries live in one server-authoritative append-only journal per POI. Do not let a book be copied, deeded, placed in a backpack or replaced through ordinary world spawner churn. Player-friendly labels and the RP Directory identify the four journals and explain how to write; directory discovery does not provide remote reading/writing or teleportation.

**Reading is completely open.** Any player can read any of the four books without costume, guild, role/faction affiliation, `[IC]` state, character skill, account age or quest completion. Reading does not start a writing cooldown. Viewing a book is a normal vulnerable in-world action; in particular, reading/writing at Buccaneer's Den does not suspend PvP, theft, criminality, movement, full loot or existing interaction restrictions. Do not expose hidden authors' live whereabouts, account identities or other private data through guestbook UI.

**Writing requires exactly the approved minimum, not a full costume.** At submission time the living character must be physically in interaction range of the chosen book and must have **at least two distinct equipment pieces currently worn in different valid equipment slots** whose trusted server-side `RoleplayIssued` flag is intact **and** whose bound-character ID matches the writer. The two pieces can be from any combination of the four RP kit themes and are valid at any of the four books; the writer does not have to claim that POI's kit, wear a full set, belong to a guild, enable `[IC]`, or have scene props deployed. Two items in a backpack, duplicate references to one piece, ordinary lookalike gear, someone else's issued pieces and forged/stripped flags never qualify. Check both when opening a compose interface (for useful feedback) **and again atomically at final server-side submission**; the commit check, not opening-time appearance, determines whether the entry is published. A character whose issued gear was destroyed on death cannot write until they genuinely equip two newly issued pieces. Do not alter normal RP gear issuance, transfer restrictions, wear, death or cooldown mechanics.

**Publication and entry format**

- **Option A approved: publish immediately, moderate retrospectively.** There is no routine staff preapproval queue, automatic content approval delay, daily-entry cap or report-triggered automatic hiding.
- A nonblank entry is at most **280 Unicode characters** after canonical normalization and removal/rejection of unsafe control characters; count consistently on server and client without allowing payload size, newlines or formatting tags to evade limits. Sanitize/escape user text as plain text, not executable markup or privileged book commands. Apply a bounded payload size before Unicode processing.
- Apply **one successful entry per character per rolling 10 minutes, globally across all four books**; set the next-eligible timestamp only after a successful atomic commit. Failed validation does not consume cooldown. Reopen, swap books, rename, logout, death or restart cannot bypass the cooldown. Do not add an additional daily cap.
- Store an immutable unique entry ID, source POI/book ID, writer's persistent character ID (staff-only), a snapshot of the publicly visible character name at posting, authoritative UTC timestamp, normalized original text and visibility/moderation metadata. Ordinary readers see the name snapshot, timestamp and visible text only; a rename does not rewrite old history or allow author impersonation. Entries are **append-only**: normal players cannot edit, replace, reorder or delete their entries after publishing. Staff can hide an entry and, where appropriate after review, restore it, with original contents and actions retained in a staff-only audit trail.
- Store and order commits atomically so double-submit, packet replay, concurrent requests, crash recovery or partial saves cannot create two entries, duplicate a cooldown, drop published content or produce corrupt volumes. Publish confirmation occurs only after the durable journal/cooldown transaction succeeds. The source of truth is the server, not mutable item book pages or a client-submitted author/time/book ID.

**Persistent volumes and reading UX.** Give each journal a bounded active volume (initial proposal: **100 entries**), automatically close it as a read-only archive at capacity and open the next volume. Make older volumes accessible from the same book via pagination/navigation, initially 20 entries per page or another client-appropriate bound. Legitimate archives remain readable by default; do not wipe history at the weekly rotation, character logout or server restart, and do not require a GM to roll volumes over. Hide moderated entries from ordinary archive and active views alike while retaining source records for staff. Index/paginate to avoid loading an unbounded archive into every reader's client; keep storage/backup and moderation-audit retention documented. This is not a scoring, leaderboard, RP points or achievement system.

**Player reporting — approved Option A.** A reader may report an individual immutable entry ID via a lightweight in-book action and, optionally, choose a short predefined reason or bounded free-text reason. The report goes to a **staff-only review queue** and includes the original entry ID, book, author snapshot, reporter identity (staff-only), reason, UTC time and visibility state. Consolidate repeated reports on the same entry; enforce at most one *active* report per reporting account per entry, a reasonable report-request throttle, and idempotent storage to limit spam, without automatically hiding or deleting anything. Reports are not votes: one report or many do not change public visibility or trigger punishments. Staff may inspect the original, dismiss/resolve the report, hide the entry, or restore it; record moderator, reason and time. Reporting does not reveal reporter identity to the author or grant an in-game reward. If no moderator is online, publication and reading keep working normally; reports persist for later review. Existing shard conduct policies determine actual staff actions, not automatic keyword or report-count thresholds.

**Economy, region, and controls.** Writing/reading/reporting awards **zero** gold, loot, skill gain, titles, achievements, faction credit, reputation or other material benefit. Book items, entries, archives and report submissions have zero resale/salvage/collateral value; they cannot be transferred, cloned or used as containers. Staff commands should inspect a POI book, recent entries and reports; hide/restore entries with audit logging; resolve reports; temporarily disable writing for a specific book while preserving public reading and archives; and inspect/fix journal state without recreating or silently deleting history. Never create a safe bubble around a book or relax the surrounding region's Hot/Cool/criminal behavior.

**Configuration, monitoring and release acceptance.** Expose enabled book IDs/locations, `maxEntryCharacters = 280`, `globalWriterCooldownMinutes = 10`, `entriesPerVolume = 100`, `entriesPerPage = 20`, `minimumEquippedOwnIssuedItems = 2`, `publishImmediately = true`, `moderationMode = retrospective`, `playerReportsEnabled = true`, `autoHideOnReports = false`, and a bounded report throttle in shard-specific configuration. Count entries per POI/volume, writer eligibility/cooldown failures, reports received/resolved, staff hides/restores and queue depth; do **not** algorithmically rate RP quality or publicize reporter identities. Audit existing book/Gump/item/multi/equipment/journal serialization and persistence hooks first, prefer a shard-specific service over core rewrites, and pass the dedicated Section 23 regression matrix before launch. The feature must continue working with no routine staff events or daily manual administration.

### Interaction with weekly population-concentration systems

The RP POIs are permanent and do not rotate.

Yew should be favored for occasional geographic overlap with:

- a Yew Expedition week;
- Justice or another map-appropriate Pilgrimage route;
- staff-run story events.

This can naturally place gatherers, pilgrims, militia, orcs and undead in overlapping geography without giving RP participation mandatory rewards.

Buccaneer's Den already has permanent PvP/social concentration and does not need an additional routine reward bonus merely because it is an RP hub.

### PvP, criminality and RP

Role gear never changes hostility legality.

Examples:

- Orc-costumed blue remains protected from unsolicited blue attacks outside Hot Zones unless otherwise independently lawful;
- Undead-costumed red remains a lawful red target;
- Militia costume does not authorize attacking an Orc-costumed innocent;
- Pirate costume does not create criminal status;
- Buccaneer's Den remains Hot regardless of costume;
- direct-target retaliation rules for reds/greys remain authoritative;
- AoE-only contact still does not create direct-retaliation rights under the shard's existing rule.

Players who want mechanically dangerous RP may use:

- Buccaneer's Den;
- Hot Zones;
- red/grey characters;
- consensual guild wars;
- ordinary lawful aggression.

The wardrobe itself never opts another player into PvP.

### No rewards for merely roleplaying

Do not provide:

- gold;
- skill gain;
- resource bonuses;
- loot multipliers;
- faction points;
- RP reputation points;
- achievement farming;
- daily rewards beyond the ability to claim the bound gear kit itself

for wearing RP gear or standing at an RP POI.

The equipment is already the system's tangible convenience benefit.

### Suggested launch configuration

Conceptual configuration:

```text
roleplay.enabled = true

roleplay.gear.enabled = true
roleplay.gear.claimMode = oneGlobalKitPerCharacter
roleplay.gear.claimCooldownHours = 24
roleplay.gear.powerProfile = FineEquivalent
roleplay.gear.magicPropertiesEnabled = false
roleplay.gear.slayerEnabled = false
roleplay.gear.makerMarkEnabled = false

roleplay.gear.characterBound = true
roleplay.gear.directTradeEnabled = false
roleplay.gear.groundTransferEnabled = false
roleplay.gear.bankTransferToOtherCharacterEnabled = false
roleplay.gear.houseStorageEnabled = false
roleplay.gear.petTransferEnabled = false
roleplay.gear.playerVendorEnabled = false
roleplay.gear.npcSaleEnabled = false
roleplay.gear.salvageEnabled = false
roleplay.gear.bodEligible = false
roleplay.gear.craftingInputEnabled = false
roleplay.gear.referenceValue = 0

roleplay.gear.blessed = false
roleplay.gear.destroyOnOwnerDeath = true
roleplay.gear.deathResetsClaimCooldown = true

roleplay.gear.affectsNotoriety = false
roleplay.gear.affectsNpcAggression = false
roleplay.gear.affectsRaceOrFaction = false

roleplay.icTag.enabled = true
roleplay.icTag.defaultEnabled = false
roleplay.icTag.persistUntilToggled = true

roleplay.sceneProps.enabled = true
roleplay.sceneProps.requiredGuildLeader = true
roleplay.sceneProps.requiredNearbyGuildMembers = 3
roleplay.sceneProps.nearbyRangeTiles = 12
roleplay.sceneProps.themeCountPerPoi = 3
roleplay.sceneProps.claimCooldownHoursPerGuild = 24
roleplay.sceneProps.maxUnopenedBagsPerGuild = 1
roleplay.sceneProps.maxActiveScenesPerGuild = 1
roleplay.sceneProps.allowSameGuildBagTransfer = true
roleplay.sceneProps.unopenedBagExpiryMinutes = 15
roleplay.sceneProps.sceneLifetimeMinutes = 240

roleplay.directory.enabled = true

# Approved #31: four permanent in-world journals, ordinary reading and costume-gated writing
roleplay.guestbooks.enabled = true
roleplay.guestbooks.poiIds = YewOrcFort,YewGraveyard,YewMilitia,BuccaneersDen
roleplay.guestbooks.minimumEquippedOwnIssuedItems = 2
roleplay.guestbooks.maxEntryCharacters = 280
roleplay.guestbooks.globalWriterCooldownMinutes = 10
roleplay.guestbooks.entriesPerVolume = 100
roleplay.guestbooks.entriesPerPage = 20
roleplay.guestbooks.publishImmediately = true
roleplay.guestbooks.moderationMode = retrospective
roleplay.guestbooks.playerReportsEnabled = true
roleplay.guestbooks.autoHideOnReports = false
roleplay.guestbooks.rpRewardsEnabled = false
roleplay.rewardsForWearingGear = false
```

Initial POI set:

```text
YewOrcFort       -> OrcClan
YewGraveyard     -> UndeadCult
YewMilitia       -> YewMilitiaWardens
BuccaneersDen    -> PiratesOutlaws
```

Exact coordinates, chest placement, kit catalogs, art IDs and item wrappers require UOR Felucca/client audit before implementation.

### Anti-exploit requirements

Prevent at minimum:

- claiming one kit from each chest inside the same 24-hour window;
- resetting cooldown through anything **other than the intended owner-death reset**;
- resetting cooldown through character rename;
- save/restart duplicating a claim entitlement;
- repeatedly opening one bag to duplicate contents;
- moving bound items into another character's inventory;
- staged death transferring usable RP equipment;
- player-vendor or NPC liquidation;
- player-vendor advance/collateral valuation;
- salvage/smelting/cutting into unrestricted materials;
- BOD completion;
- transformation/deeding removing the `RoleplayIssued` state;
- crafting recipes consuming RP equipment and producing normal unrestricted items;
- repair or enhancement paths stripping the bound marker;
- magic-property enhancement/reforging if any later system exposes such a path;
- stacking/merging mechanics erasing provenance;
- item duplication through container rollback or world-save edge cases.

### Telemetry

Track:

- claims by POI/kit;
- unique characters/accounts claiming each kit;
- claim denials due to cooldown;
- current count of RoleplayIssued items;
- destruction on death;
- durability-related destruction if relevant;
- attempts to sell/trade/salvage/transfer bound gear;
- IC-tag toggles and approximate concurrent IC-tagged population;
- Scene Prop Bag claims by POI/theme/guild;
- remaining Scene Prop Bag cooldown by guild;
- same-guild Scene Prop Bag transfers and invalid transfer attempts;
- claim denials by missing leader/member-count/cooldown/unopened-bag/already-active-scene;
- active scene counts and voluntary/automatic/staff cleanup;
- scene-placement denials by protected/chokepoint/combat-geometry rules;
- optional aggregate activity near the four RP POIs if a low-cost region telemetry hook exists.
- guestbook entries by POI/volume, successful writer count, failed costume/proximity/cooldown checks, report counts/queue depth and staff hide/restore/resolution actions; never publish report identities or RP-quality scores.

Do **not** algorithmically score whether a player is “really roleplaying.”

### Admin support

Provide staff commands/tools to:

- list the four RP POIs and exact coordinates;
- teleport staff to a POI;
- inspect its kit catalog;
- enable/disable a chest;
- reload kit configuration if practical;
- inspect a character's next RP claim time;
- reset a claim cooldown only through an explicit staff command with logging;
- identify `RoleplayIssued` items and their bound character;
- report claims and exploit-denial counters;
- temporarily disable a specific problematic kit/item without disabling the entire RP system.
- inspect/toggle a character's IC state for troubleshooting without treating it as a punishment system;
- inspect active guild RP scenes, source POI, owner guild, theme and expiry;
- dismiss a problematic scene immediately;
- inspect why a guild is ineligible to claim a Scene Prop Bag;
- temporarily disable a scene theme or prop definition without disabling RP gear;
- inspect each permanent guestbook and its archives, browse original/hidden entries and the consolidated player-report queue, hide/restore with reason and durable audit, dismiss/resolve reports, and disable only writing for a problematic book without destroying history or changing PvP legality;

### RP gear regression tests

Verify at minimum:

- exactly the four configured launch RP chests exist after world generation/restart;
- each chest exposes at least three unique themed full-kit bag variants (minimum 12 launch kits total);
- the three Yew locations and Buccaneer's Den use the intended region rules;
- chest contents/templates cannot be removed;
- one claim starts the global per-character 24-hour cooldown;
- another chest cannot issue a second kit during that cooldown;
- logout/restart/rename do not reset the cooldown; owner death destroys the issued set and resets the cooldown exactly once;
- a valid claim after 24 hours succeeds;
- every issued item is bound to the claiming character;
- bound items cannot be traded, dropped for transfer, vendored, stored in house containers or transferred through pets;
- bound items have zero NPC/reference/vendor-advance value;
- bound items cannot be salvaged, smelted, cut, deeded or used in BODs/crafting conversions;
- roleplay weapons deal real configured damage;
- roleplay armor provides real configured protection;
- combat performance matches the approved Fine-equivalent benchmark within expected rounding/era formulas;
- gear cannot roll above the configured RP power profile;
- gear cannot receive magic/slayer properties;
- RP masks do not pacify creatures or alter NPC aggression;
- issued gear is not blessed;
- issued gear is destroyed on owner death;
- death does not create usable RoleplayIssued corpse loot;
- owner death destroys all of that character's RoleplayIssued gear before resetting the claim entitlement;
- immediately after death cleanup, the character can claim one replacement kit and a new 24-hour cooldown begins;
- repeated deaths never allow two live RoleplayIssued sets to coexist on the same character;
- ordinary non-RP gear continues to use normal corpse/full-loot behavior;
- costume/gear use does not change notoriety, race, guild/faction, criminality or PvP legality;
- Buccaneer's Den chest creates no safe bubble;
- item art/hues remain appropriate to the supported UOR client presentation.

### IC-tag and Scene Prop regression tests

Verify at minimum:

- IC tag defaults off for a new character;
- `[IC` (or final configured command) toggles it on/off without affecting mechanics;
- IC state persists through logout, death and restart;
- IC marker does not replace or corrupt notoriety/guild/name presentation;
- IC state grants no hostility, reward, NPC or faction effect;
- each of the four RP chests exposes exactly the three configured launch Scene Prop themes;
- only the current guild leader may **claim** a Scene Prop Bag;
- claim fails with 0, 1 or 2 additional nearby guild members;
- claim succeeds with the leader + 3 distinct qualifying nearby guild members;
- offline, dead, different-guild, pet and NPC entities do not count;
- configured proximity is enforced server-side;
- a successful claim starts a **24-hour guild-level Scene Prop Bag cooldown**;
- that Scene Prop cooldown is independent of every character's costume/gear cooldown;
- the claiming leader can directly transfer the unopened bag to another current member of the same guild;
- same-guild transfer does not change the bag's theme, POI, expiry or guild cooldown;
- transfer to a non-guild member is rejected;
- if the holder leaves the owning guild before deployment, the bag cannot be used and is safely deleted;
- expiration, destruction, deployment, scene cleanup, leader death and leadership transfer do not reset the guild's 24-hour cooldown;
- one guild cannot hold a second unopened Scene Prop Bag or deploy a second active scene anywhere in the RP system;
- unopened scene bag expires at the configured time;
- deployed props expire after the configured scene lifetime through normal play and server restart;
- props cannot leave their source POI Scene Area;
- props cannot enter houses, boats, containers, doors, stairs, roads/chokepoints or other protected placement geometry;
- decorative container art provides no storage;
- weapon/armor/resource-looking props provide no usable item or economic value;
- props cannot be picked up, sold, salvaged, deeded or converted;
- scene deployment never changes PvP legality or NPC/notoriety rules;
- Buccaneer's Den scene props cannot create exploitable blocking/line-of-sight fortifications;
- guild leadership transfer, disbanding and save/restart do not duplicate an active scene/bag or reset the 24-hour guild cooldown;
- leader death/logout does not duplicate scene entitlement or reset the guild cooldown;
- voluntary/staff/automatic cleanup removes every scene prop and releases the guild's active-scene slot exactly once without clearing the claim cooldown.

### Roleplay-system Definition of Done

The launch RP feature is ready when:

- only the **Yew Trinity + Buccaneer's Den** are configured as permanent RP wardrobe POIs;
- each POI has a stable themed chest with **at least three distinct complete themed role kits**;
- the Yew Trinity visibly supports Orc / Undead / Militia identities in nearby geography;
- every issued combat item uses the approved low/mid-tier functional profile;
- while alive, one character can obtain at most one complete RP kit per rolling 24 hours across all four locations; owner death destroys the current issued set and immediately resets that entitlement;
- every issued item is character-bound, non-sellable, non-tradeable and non-salvageable;
- issued gear is lost/destroyed on death rather than blessed or transferable through a corpse;
- ordinary crafting and magic loot still provide clear performance/economic advantages;
- no issued gear changes NPC allegiance, notoriety or hostility legality;
- the RP Directory lists only the four launch identities;
- the optional `[IC]` tag clearly signals openness to in-character interaction and has no mechanical effect;
- every RP chest offers exactly three temporary guild Scene Prop themes: Camp/Meeting, Ritual/Ceremony and Conflict/Aftermath, with POI-appropriate art;
- Scene Prop Bags can be claimed only by a guild leader with at least three additional same-guild members nearby;
- Scene Prop Bags use a separate **24-hour per-guild claim cooldown** that does not interact with the per-character costume/gear cooldown;
- after claim, the leader may transfer the unopened Scene Prop Bag to another current member of the same guild without resetting its expiry or the guild cooldown;
- a guild can have only one unopened Scene Prop Bag and one active RP scene at a time, and every scene automatically expires/cleans up;
- scene props are temporary, non-economic and unable to create movement, storage, combat or line-of-sight exploits;
- exactly four permanent RP guestbooks allow unrestricted reading and immediate costume-gated submissions requiring two distinct equipped own-`RoleplayIssued` pieces; 280-character limit, global 10-minute cooldown, automatic permanent archival, player reports to staff queue without auto-hiding, retrospective audited moderation, zero rewards and unchanged Buccaneer Hot-zone legality;
- exploit tests cover cooldowns, death, transfer, storage, sale, salvage, conversion and save/restart;
- telemetry shows whether each identity is being used;
- future RP POIs require explicit owner approval rather than automatically expanding the network.


## 17. Accounts

Initial account policy:

- automatic account creation may remain enabled for development
- target production maximum: **one gameplay account per IP by default**, configurable
- create and protect an Owner account
- do not commit credentials
- use current secure ModernUO password hashing
- do not weaken account security for compatibility

Recognize that IP limits can affect legitimate households.

Implement the policy so staff can grant explicit account/IP exceptions rather than modifying source code for individual users.

If no exception system exists, design one as shard-specific configuration.

---

## 18. Feature Flags

Review all ModernUO runtime feature flags.

Expected launch values include:

`pvp_combat = true`

`player_trading = true`

`bank_access = true`

`vendor_purchase = true`

`vendor_sell = true`

`player_vendors = true`

`house_placement = true`

`boat_placement = true`

`bulk_orders = true` (target; subject to reward/economy audit)

`pvp_combat` must remain enabled at the engine level if disabling it would prevent Hot-Zone PvP, criminal retaliation or lawful aggression. The shard-specific hostility gate should decide **where and why** a player attack is legal.

Evaluate `passive_detect_hidden` against UOR-era expectations before choosing its launch value.

Evaluate `speedhack_detection` in a test environment and enable it for production if reliable with intended clients.

Do not use feature flags to mask an underlying era or region-legality bug.

---

## 19. Shard-Specific Configuration Layer

Create a shard-specific configuration file rather than scattering constants throughout the source.

Suggested location:

`Distribution/Configuration/shard-rules.json`

and corresponding strongly typed code under something like:

`Projects/UOContent/Custom/<ShardName>/Configuration/`

The exact structure can change to match current ModernUO conventions.

At minimum, make likely-to-change shard policies configurable:

- account limit
- house limit
- housing district definitions and open/locked state
- Greater Britain housing district soft capacities and fixed expansion order
- housing expansion thresholds
- rural-housing multiplier and surcharge/refund policy
- housing land classification (residential / rural / protected)
- permanent no-housing regions and permanent special housing regions
- inactive-house qualification/decay policy
- BOD enablement if not handled solely by feature flags
- `PvP Intent` eligibility/display/persistence and encounter snapshot configuration; real criminal timer; **cumulative 24-hour UTC red expiry per qualifying murder**, unique death guard and history-only murder ledger (no configurable short/long UOR status thresholds)
- skill cap
- stat cap
- pre-95 per-skill / per-profile skill-gain classification preserving UOR/T2A easy-vs-hard relative difficulty
- Standard pre-95 milestone targets: 1h to 50, 2.5h to 70, 4.5h to 80, 7.5h to 90, 12.5h to 95 under focused-training conditions
- pre-95 range-based gain curves for Easy / Standard / Hard / VeryHard profiles and documented per-skill overrides
- Mastery threshold (`95.0`)
- rolling Mastery Period duration (`24h`) and active-period trigger policy
- Mastery Time costs per +0.1: 4h / 5h / 6h / 8h / 10h36m across 95–96 / 96–97 / 97–98 / 98–99 / 99–100
- Mastery active-calendar target (`336h / 14 active days`)
- Mastery eligible-attempt base chance (`10%`) and guaranteed-attempt index (`10`)
- Mastery Time banking/persistence/concurrency rules
- temporary gain-bonus behavior below 95 vs matured Mastery opportunities at 95+
- new-character Skill Gain Ball count, multiplier, duration and transfer policy
- starter-protection duration (launch default: 4 logged-in hours)
- starter-issued gear/consumable economic restrictions
- once-per-account starter-gold amount (launch target: 500)
- profession starter-material quantities
- account-level per-profession starter-material entitlement tracking
- starter-material transfer/merge/provenance restrictions
- ordinary loot/gold multipliers
- faction enablement
- taming dungeon/PvP restrictions
- event/system toggles
- restricted pet-bonding policy
- safe-world hostility policy
- static bank theft-protection polygons (premises and surveyed immediate apron), with independent hostility/guard legality
- Backpack Ward item sources/prices after economy audit, dormant/active timing, victim-detection escalation and Starter-Issued single-grant/economic restrictions
- Loot Protection Ward universal character entitlement/migration, corpse-rights and Hot-Zone eligibility, per-offender UTC entry duration (launch: 10 minutes), cleanup, logging and simultaneous-loot safeguards
- permanent Hot Dungeon region (`Hythloth` launch default)
- rotating Hot Dungeon eligible pool and schedule
- Cool Dungeon eligible pool and schedule
- Expedition Region eligible pool, schedule and route definitions
- Expedition trade cargo/checkpoint/expiration policy
- Expedition trade-route reward tables
- Expedition resource-yield multiplier and eligible gathering categories
- Expedition Logistics resource-weight multiplier, eligible resource categories and provenance/cleanup policy
- Pilgrimage virtue/shrine pool, weekly rotation, departure schedule, race settings, checkpoints and reward values
- road-travel tile/region definitions, movement multipliers and PvP-disable policy
- permanent outdoor PvP regions (`Fire Island` and `Buccaneer's Den island` launch defaults)
- permanent Hot Dungeon reward multipliers
- rotating Hot Dungeon reward multipliers
- Cool Dungeon reward multipliers
- outdoor Hot-Zone reward/resource multipliers
- Hot-Zone boundary/combat-carryover settings
- login/status/announcement behavior
- per-spawner reward opt-out where necessary
- Nemesis eligible species/spawner/region whitelist and opt-outs; per-dungeon/outdoor-cluster caps; names/hues/existing trophy art; optional supported-client sprite-scaling capability; spawn, HP, damage, trophy and consolation-gold parameters
- Wanted contract target/species/dungeon/origin whitelists, deterministic weekly lists, ranked ModernUO looting-rights API adapter, live-recipient scan, two physical currency definitions and per-tier payouts, Britain curator/dungeon-specific existing-art catalogs, transactional backpack/pending delivery and claim IDs
- Shipwreck SOS completion/chart drop hook, valid Felucca water/chart coordinates, boat/multi activation, 30/60-minute rights/timers, finite salvage count, one guaranteed weighted decoration and NPC/resource/economy restrictions

Conceptual launch values should be equivalent to:

- `world.unsolicitedBlueVsBluePvP = false` (ordinary blues only; voluntarily exposed `[Intent]` is a distinct lawful target)
- `pvpIntent.enabled = true` / `pvpIntent.blueOnly = true` / `pvpIntent.displayTag = [Intent]` (illustrative custom keys, NOT stock ModernUO options)
- `pvpIntent.offForNewOpponentsImmediately = true` / `pvpIntent.preserveExistingEncounterRights = true`
- `murder.autoCountOrdinaryBlueVictims = true` / `murder.hoursAddedPerKill = 24` / `murder.timer = cumulativeUTC` / `murder.historicalCountsAffectRedStatus = false`
- `murder.hotZoneBlueVictimWaiver = false` / `murder.selfDefenseBlueVictimWaiver = false` / `murder.guildWarBlueVictimWaiver = false`
- `world.stealingEnabledByDefault = true`
- `world.snoopingEverywhere = true`
- `coolDungeon.stealingEnabled = false`
- `banks.directPlayerStealingEnabled = false` (only explicitly mapped bank theft-protection regions; snooping and legal PvP unchanged)
- `backpackWard.dormantDurationMinutes = null` (no dormant expiration; physical Ward must remain in equipped backpack)
- `backpackWard.additionalDetectionOnSuccessfulTheftsPerThiefAccount = [0.25, 0.50, 1.00]`
- `backpackWard.activatedProtectionSeconds = 120`
- `world.allowAttacksOnCriminalsEverywhere = true`
- `world.allowAttacksOnMurderersEverywhere = true`
- `housing.maxHousesPerAccount = 1`
- `housing.restrictPlacementToDistricts = true`
- `housing.launchDistrictGroup = GreaterBritain`
- `housing.normalCostDistrictsOutsideGreaterBritain = false`
- `housing.afterFinalGreaterBritainDistrict = ruralOnly`
- `housing.expansionOccupancyTarget = 0.80`
- `housing.minimumSpareCapacityTarget = 0.20`
- `housing.ruralHousingEnabled = true`
- `housing.ruralCostMultiplier = 2.0`
- `housing.ruralPremiumRefundable = false`
- `housing.ruralTargetShareMin = 0.15`
- `housing.ruralTargetShareMax = 0.25`
- `housing.autoCloseOpenedDistricts = false`
- `housing.prohibitedRegions` includes `BuccaneersDenIsland`, configured dungeon/road/landmark buffers and other permanent reserves
- `housing.alwaysOpenSpecialDistricts` includes `FireIslandResidential`
- `housing.fireIslandCountsTowardMainlandExpansion = false`
- `housing.inactiveAccountDecayDays = 45` as an initial tuning target
- `skillGainBalls.enabled = true`
- `skillGainBalls.newCharacterCount = 20`
- `skillGainBalls.multiplier = 1.25`
- `skillGainBalls.durationMinutes = 60`
- `skillGainBalls.timerMode = loggedInCharacterTime`
- `skillGainBalls.maxActive = 1`
- `skillGainBalls.blessed = true`
- `skillGainBalls.characterBound = true`
- `skillGainBalls.retroactiveGrant = false`
- `hotZones.permanentDungeon = Hythloth`
- `hotZones.permanentOutdoorRegions = [FireIsland, BuccaneersDenIsland]`
- `hotZones.rotatingDungeon.enabled = true`
- `hotZones.rotatingDungeon.count = 1`
- `coolDungeon.enabled = true`
- `coolDungeon.count = 1`
- `coolDungeon.rewardMultiplier = 1.10`
- `coolDungeon.magicItemChanceMultiplier = 1.10`
- `coolDungeon.accelerateSpawnRate = false`
- `expedition.enabled = true`
- `expedition.count = 1`
- `expedition.resourceYieldMultiplier = 1.50`
- `expedition.resourceRespawnMultiplier = 1.00`
- `expedition.rareResourceChanceMultiplier = 1.00`
- `expedition.logistics.enabled = true`
- `expedition.logistics.resourceCarryMultiplier = 3.0`
- `expedition.logistics.eligibleArea = regionPlusOriginAndDestinationTowns`
- `expedition.logistics.preExistingResourcesGainBenefit = false`
- `expedition.logistics.packAnimalMultiplier = 1.0`
- `expedition.rotationDays = 7`
- `expedition.tradeRoute.origin = Britain`
- `expedition.tradeRoute.fastTravelWithCargo = false`
- `expedition.tradeRoute.requireOrderedCheckpoints = true`
- `expedition.tradeRoute.cargoCharacterBound = true`
- `expedition.tradeRoute.cargoBankable = false`
- `expedition.tradeRoute.cargoTransferable = false`
- `expedition.tradeRoute.postRotationGraceHours = 24`
- `expedition.regionGlobalRewardMultiplier = 1.00`
- `pilgrimage.enabled = true`
- `pilgrimage.origin = Britain`
- `pilgrimage.mainlandShrinesOnly = true`
- `pilgrimage.rotationDays = 7`
- `pilgrimage.departureIntervalHours = 4`
- `pilgrimage.departureWindowMinutes = 15`
- `pilgrimage.maxSuccessfulCompletionsPerCharacterPerWeek = 1`
- `pilgrimage.requireOrderedCheckpoints = true`
- `pilgrimage.fastTravelAllowed = false`
- `pilgrimage.mountsAllowed = true`
- `pilgrimage.raceTopCount = 5`
- `pilgrimage.baseSkillGainBonus = 0.10`
- `pilgrimage.raceSkillGainBonus = 0.20`
- `pilgrimage.skillGainDurationMinutes = 60`
- `pilgrimage.skillGainTimerMode = loggedInCharacterTime`
- `pilgrimage.stackSkillGainBonusesAdditively = true`
- `roadTravel.enabled = true`
- `roadTravel.footSpeedMultiplier = 1.15`
- `roadTravel.mountedSpeedMultiplier = 1.10`
- `roadTravel.disableDuringActivePvPAggression = true`
- `roadTravel.disableInHotZones = true`
- `hotZones.accelerateSpawnRate = false`
- `nemesis.enabled = true` (feature launches only after baseline region/loot rules pass)
- `nemesis.eligibleSpawnChance = 0.02`
- `nemesis.hpMultiplier = 1.50`
- `nemesis.damageMultiplier = 1.00`
- `nemesis.trophyChance = 0.25`
- `nemesis.noTrophyExtraBaseGoldMultiplier = 2.00`
- `nemesis.perCreatureSpriteScale = compatibilityGated` (optional ~1.10–1.15; existing name/hue fallback mandatory)
- `nemesis.extraSpawnsOrRespawnAcceleration = false`
- `wanted.enabled = true` (after baseline and verified ranked-damage API)
- `wanted.scoring.source = ModernUOExistingLootingRightsDamageRanking` (no separate rolling-60-second recorder)
- `wanted.contracts.onlyRotatingHotCool = true` / `wanted.contracts.excludeHythloth = true`
- `wanted.reward.oneStackPerDeath = true` / `wanted.reward.pickFirstLiving = true` / `wanted.reward.regionMultiplier = 1.0`
- `wanted.currency.hot = HotMarks` / `wanted.currency.cool = CoolSeals`

Names may differ to match ModernUO conventions.

Do **not** duplicate values that ModernUO already exposes cleanly in `modernuo.json`.

The shard configuration should contain shard policy, not copies of every ModernUO setting.

---

## 20. PvP Hot Zones and Population Concentration

The map is much larger than an early freeshard population can naturally fill. This design keeps all of Britannia available while making PvP activity predictable and geographically concentrated.

At launch there should be only **three meaningful PvP activity clusters, one concentrated safe dungeon-PvE cluster, and one rotating outdoor Expedition corridor**:

1. **Fire Island + Hythloth** — permanent PvE/PvP risk cluster with strong reward incentives.
2. **Buccaneer's Den island** — permanent criminal/PvP social cluster with little or no automatic PvE reward premium at launch.
3. **The currently rotating Hot Dungeon** — weekly high-reward PvP destination.
4. **The Cool Dungeon of the Week** — weekly safe-world PvE destination with a modest reward bonus intended to promote co-play and make the safe population visible to one another.
5. **The active Expedition Region + Britain trade route** — weekly outdoor travel/exploration corridor that makes one set of roads, wilderness and secondary-town approaches visibly active.

Everything else remains available for safe ordinary play, crime, housing, crafting and exploration. The active Cool Dungeon is the single **rotating** region where direct player stealing is disabled; static bank theft-protection polygons also disable direct theft, and activated Backpack Wards temporarily protect individual prepared victims.

This distinction is intentional: not every permanent PvP zone should carry a major farming bonus. Concentrate high-risk economic incentives primarily in Hythloth/Fire Island and the rotating Hot Dungeon, while Buccaneer's Den provides always-available emergent PvP, thieves, reds, anti-PKs, risky banking/trading and criminal social activity. The Cool Dungeon supplies a parallel, lower-intensity concentration mechanic for players who want safe-world PvE and spontaneous cooperation.

### 20.1 Permanent PvP Hot Dungeon — Hythloth

Make **Hythloth** a permanent unrestricted PvP dungeon.

It never rotates out of Hot status.

Inside Hythloth:

- innocent players may attack other innocent players
- ordinary UOR harmful spells, weapons, potions and combat mechanics work
- full-loot player death works
- stealing remains enabled (Hythloth cannot rotate into Cool); snooping remains enabled everywhere
- genuine criminality and **Section 14 automatic murder counts (+24 cumulative real hours for killing ordinary blues)** operate even though initiation is unrestricted
- normal aggressor Recall/Gate restrictions apply
- combat pets remain prohibited because the shard's no-dungeon-combat-pets rule is unchanged
- Faction pet combat remains prohibited
- monster difficulty, spawn composition and normal respawn cadence remain unchanged by Hot status

Hythloth exists as the **always-available answer to "where can I find open PvP right now?"**

### 20.2 Permanent open-world PvP zone — Fire Island

Make the **entire Fire Island / Isle of Fire surface** the launch-default permanent outdoor PvP Hot Zone.

This is deliberately paired with Hythloth so players traveling to the permanent PvP dungeon pass through the permanent outdoor PvP ecosystem.

Inside the configured Fire Island surface region:

- unrestricted player attacks are enabled
- full-loot death, genuine criminal consequences and **Section 14 cumulative 24-hour murder consequences for ordinary-blue kills** apply
- stealing remains enabled except within mapped bank theft-protection polygons or against an activated-Ward target; snooping remains enabled
- outdoor tamers may use pets for PvE under the existing taming rules
- pets still may not attack innocent/blue players merely because the owner is inside a Hot Zone; the existing pet-PvP policy remains authoritative
- reds/greys remain valid pet targets as already specified
- ordinary outdoor monsters/resources continue to function

#### Fire Island housing

**Allow player housing on Fire Island at launch.**

Fire Island is a special always-open residential PvP district and remains subject to the shard-wide one-house-per-account rule.

Housing must not erase the island's permanent Hot-Zone identity:

- the house footprint/interior remains in the Fire Island Hot Zone
- no special safe-region flag is created by house placement
- normal UOR doors, friends, co-owners, bans, ejects, lockdowns and secures continue to function
- locked private property remains meaningful; unrestricted PvP does not grant attackers access through locked doors
- entering/leaving a house does not clear aggression, criminal or murderer status
- no banking/stabling/remote extraction service is automatically granted by owning a Fire Island house
- placement regions must preserve Hythloth approaches, outdoor combat space, roads, shoreline access and major spawn/event locations

Treat Fire Island housing as part of the permanent PvP ecosystem rather than as a safe extraction loophole.

### 20.3 Permanent open-world PvP zone — Buccaneer's Den island

Make **Buccaneer's Den and the entire island containing it** a permanent unrestricted PvP Hot Zone.

This zone is intentionally different from Fire Island:

- Fire Island/Hythloth is the permanent high-risk PvE destination
- Buccaneer's Den island is the permanent criminal/PvP social destination
- the rotating Hot Dungeon is the weekly high-reward convergence destination

Inside the configured Buccaneer's Den island region:

- unrestricted player attacks are enabled
- full-loot death, genuine criminal consequences and **Section 14 cumulative 24-hour murder consequences for ordinary-blue kills** apply
- stealing remains enabled except within mapped bank theft-protection polygons or against an activated-Ward target; snooping remains enabled everywhere
- reds, greys, thieves, anti-PKs and ordinary blues can all interact under the same Hot-Zone combat rules
- the town itself remains inside the unrestricted PvP Hot Zone; the newly approved bank theft-protection polygon prevents **only direct player stealing**, not combat, full loot, criminal retaliation or other town danger. Do not carve out a combat-safe bank, dock, tavern or vendor bubble
- ordinary NPCs, vendors, bank access and town services should remain era-appropriate rather than being removed merely because the area is dangerous
- ordinary outdoor pets remain subject to the shard's separate pet-PvP legality rules
- no combat-pet exception is created for any dungeon reached from or associated with the island
- normal spawn count and normal respawn cadence remain unchanged

#### Reward policy for Buccaneer's Den

At launch, **do not automatically attach a major global PvE reward multiplier to the Buccaneer's Den island**.

The island's main incentive is that it is:

- an always-known place for spontaneous PvP
- the natural home for thieves, reds and anti-PKs
- a risky social/trading/banking environment
- a staging point for player-organized fights
- a location where players can deliberately seek danger without waiting for a rotation

This avoids splitting PvE farmers between too many permanent bonus zones.

If the island later proves too empty, prefer small targeted incentives before giving it Fire-Island-level farming bonuses. Candidate future incentives include:

- a modest **+10–15% monster gold** bonus
- a Buccaneer's Den-specific cosmetic/rare drop
- periodic criminal/bounty events
- player bounty-board activity
- temporary market/event bonuses

Any such incentive requires explicit owner approval and economy testing.

#### Buccaneer's Den housing

Audit current UOR/ModernUO house placement on the island.

Launch recommendation:

- **disable new player-house placement on Buccaneer's Den island** so the criminal/PvP town remains a public conflict space rather than a private residential settlement
- retain normal public town buildings and NPC services
- do not create private safe houses that undermine the island's permanent PvP identity

If existing world data or a later design decision requires housing there, define door, ban, eject, Recall/Gate and combat-boundary behavior before enabling it.

#### Travel and shoreline boundaries

Audit every way players can enter and leave Buccaneer's Den island:

- boats
- marked runes
- Recall
- Gate Travel
- public moongates/teleporters if present
- docks and shoreline transitions

The entire intended landmass should use one coherent Hot-Zone rule.

Do not accidentally extend the permanent Hot Zone across broad surrounding ocean tiles merely because of a rectangular region definition. Conversely, do not leave thin safe strips on the shoreline that players can exploit during combat.

### 20.4 Rotating PvP Hot Dungeon

In addition to Hythloth, exactly **one other eligible dungeon** is Hot at a time.

Launch rotation:

- fixed weekly boundary
- default rotation day: **Friday**
- seven-day duration
- Hythloth excluded because it is permanently Hot
- no simultaneous second rotating dungeon at launch
- avoid selecting the same dungeon in consecutive weeks when possible
- staff can inspect, force, advance or temporarily disable the rotation without code changes

Candidate pool after region/spawn audit:

- Despise
- Deceit
- Covetous
- Shame
- Wrong
- Destard
- other UOR-appropriate dungeons only after explicit audit

A dungeon that is not currently Hot immediately returns to the safe-world default once combat carryover is resolved.

### 20.5 Cool Dungeon of the Week

Exactly **one eligible non-PvP dungeon** is designated the **Cool Dungeon of the Week**.

Purpose:

> **Concentrate safe-world PvE players into one recognizable dungeon each week so solo players, returning players and casual groups naturally encounter one another and co-play emerges without requiring formal matchmaking.**

The Cool Dungeon remains under the shard's ordinary safe-world hostility rules. It is a **theft-free cooperative PvE exception**, not a separate Trammel facet.

Inside the Cool Dungeon:

- innocent blue-vs-blue unsolicited attacks remain blocked
- **direct player stealing through the Stealing skill is disabled**
- **snooping remains enabled**
- ordinary corpse rights and criminality remain; the Loot Protection Ward only limits repeat unauthorized monster-corpse transfers by a recorded offender in this non-Hot Cool Dungeon
- `[Intent]` participants and real greys/criminals remain lawful attack targets
- reds/murderers remain lawful attack targets
- a blue who **directly targets** an intent/real grey/red with a qualifying offensive action grants that specific opponent lawful retaliation rights; killing that ordinary blue still incurs one murder count and +24h
- AoE/incidental damage alone does **not** grant a red/grey retaliation rights against the source blue
- existing lawful aggression relationships remain valid
- consensual guild-war combat remains governed by the normal shard rules
- combat pets remain prohibited because it is still a dungeon
- monster difficulty, spawn composition, spawn count and respawn cadence remain completely normal

#### Rotation

Launch behavior:

- exactly one Cool Dungeon active at a time
- fixed weekly boundary, preferably the same Friday reset used by the rotating Hot Dungeon for clarity
- seven-day duration
- Cool selection and Hot selection must be **different dungeons**
- Hythloth is never eligible because it is permanently Hot
- avoid selecting the same Cool Dungeon in consecutive weeks when at least two eligible choices exist
- staff can inspect, force, advance or temporarily disable the Cool rotation without code deployment

The Cool pool may use the same broad set of classic dungeons as the Hot pool, but selection must resolve conflicts before activation.

Candidate pool after region/spawn audit:

- Despise
- Deceit
- Covetous
- Shame
- Wrong
- Destard
- other UOR-appropriate dungeons only after explicit audit

#### Cool reward bonus

Initial launch bonus:

- **+10% monster gold / ordinary scalar rewards**
- **+10% relative magic-item generation chance**
- no spawn-rate increase
- no monster-stat increase
- no new loot tier
- no unique combat-power item required
- no daily/streak requirement

The 10% bonus is deliberately much smaller than the Hot Dungeon risk premium.

The intended hierarchy is:

- ordinary safe dungeon: **100%**
- Cool Dungeon: **110%**
- Hot Dungeon: substantially higher risk premium
- Hythloth: permanent high-risk premium

The Cool bonus should be enough to influence where safe PvE players choose to play without making every other safe dungeon economically obsolete.

#### Co-play, not forced grouping

Do not require parties to receive the Cool bonus.

The system should create **proximity and repeated encounters**, not mandatory group composition.

Players may:

- hunt solo
- form ad-hoc parties
- heal/buff/cooperate where normal mechanics allow
- compete for spawns under ordinary safe-world rules
- encounter thieves and criminal behavior as elsewhere

Do not add personal instancing, private copies or per-party phases; those would defeat the population-concentration goal.

#### Cool/Hot conflict rules

A dungeon may never be both Cool and Hot simultaneously.

Selection order should guarantee:

1. permanent Hot areas are excluded from Cool eligibility
2. the active rotating Hot Dungeon is excluded from Cool selection
3. if staff forces a Hot Dungeon that is currently Cool, the Cool system must immediately select/require selection of another eligible dungeon rather than stacking states
4. if staff forces a Cool Dungeon that is currently Hot, reject the action unless Hot status is changed first

Cool status must never override Hot-Zone PvP legality.

### 20.6 Reward philosophy

Safe-world PvE should remain **100% normal baseline reward**. Do not penalize players for choosing safety.

The Cool Dungeon receives a small **safe co-play premium**. Hot Zones should pay a much larger **risk premium** large enough to attract players voluntarily.

Initial tuning targets:

#### Cool Dungeon of the Week
- **+10% monster gold / ordinary scalar rewards**
- **+10% relative magic-item generation chance**
- normal spawn count
- normal respawn cadence

#### Hythloth permanent Hot Dungeon
- **+35% monster gold**
- **+25% relative magic-item generation chance**
- **+50% chance multiplier for approved cosmetic/rare non-power drops**, if such drops exist
- normal spawn count
- normal respawn cadence

#### Rotating Hot Dungeon
- **+50% monster gold**
- **+40% relative magic-item generation chance**
- **+100% chance multiplier for approved cosmetic/rare non-power Hot-zone drops**, if implemented
- normal spawn count
- normal respawn cadence

#### Fire Island surface
- **+25% monster gold**
- **+20% approved ordinary resource yield or rare-resource chance** for resources actually available on the island, after economy testing
- optional increased chance of era-appropriate treasure maps or ordinary rare/cosmetic drops
- normal spawn count
- normal respawn cadence

#### Buccaneer's Den island
- **100% normal monster gold at launch**
- **100% normal resource yield at launch**
- no automatic global PvE multiplier unless later approved
- normal spawn count
- normal respawn cadence

All values are launch tuning targets and must be configurable.

Do not create a new power-item tier. Hot rewards should be more of the shard's normal economy plus optional cosmetic/prestige items.

### 20.6A Wanted Monster System — approved weekly dungeon bounties (#39)

**Status: approved horizontal dungeon-retention feature.** Automatically publish independent Wanted lists for the **single active rotating Hot Dungeon** and the **single distinct active Cool Dungeon**. Existing naturally spawned creatures of each listed species award exactly **one finite bounty per real death**, credited to **one living player** by reusing ModernUO's existing damage/looting-rights ranking. No new rolling-60-second damage-attribution subsystem, no per-party duplication, new combat tier, accelerated respawns, mandatory progression, new client art, or GM-run event. Hythloth stays permanently Hot but is **not** a Wanted destination at launch; ordinary inactive/safe dungeons and surface Hot regions do not issue Wanted bounties.

**Weekly targets and location validation**

- Reuse the existing, server-authoritative Hot/Cool seven-day rotation, effective region boundaries and stable week/rotation ID. Each active dungeon receives **2–3 eligible Wanted monster species/types** from its own *audited natural-spawn pool*. The board in Britain and appropriate public player status UI show both dungeons, all live targets, difficulty tier, tokens/kill, and next rotation. No random hidden objectives or daily roll; persist each week's selections and do not reroll on restarts, manual board refreshes or repeated initialization. A species appearing in the other dungeon does not merge its separate contract/currency.
- Generate weekly lists from species demonstrably available at usable frequency in the configured dungeon. Exclude quest/event/staff/player-spawned monsters, summons, controlled mobs and fabricated variants. An existing boss may be a target only if its normal authentic encounter/spawner reliably exists and is accessible that week; omit boss tier entirely if no suitable boss exists. Do not generate extra Wanted spawns, change monster skills/stats/loot, tighten normal respawn timing, create independent bosses or increase simultaneous monster pressure.
- Mark the authoritative monster spawn origin, original species, eligible spawner identity and original weekly dungeon/contract assignment; award only for a legitimate natural spawn belonging to the relevant active dungeon and a valid contract **at the death instant**. Prevent dragging a monster into a qualifying region, crossing a dungeon boundary, disabling/reactivating a dungeon, or assigning a stale week to create extra payouts. At rotation, preserve only the current authoritative active contracts; old living monsters do not become retroactively eligible for a new contract merely because their species now appears on the board. Select a deterministic, documented policy for monsters whose old contract ends while alive (launch: no bounty after the old week's expiry); snapshot origin/contract to avoid week-spanning abuse. Existing normal corpse rewards and region multipliers still follow their separately approved rules.

**Currencies and fixed payouts**

- A successful Hot contract yields one stack of **Hot Marks**. A successful Cool contract yields one stack of **Cool Seals**. Each is an ordinary unblessed physical, stackable, **tradable, bankable, lootable** item; ordinary Stealing and full-loot rules apply when applicable. They are not Expedition cargo, do not disable Recall/Gate travel and cannot be cross-exchanged or converted to gold at a favorable NPC rate. Both balances persist through weekly rotations via the actual physical items; do not zero balances on rotation or replace the two currencies with a shared generic currency.
- Launch payout per eligible monster death: **Easy = 1**, **Medium = 3**, **Hard = 8**, **Boss = 15** units of the applicable dungeon's currency. Assign difficulty in an explicit per-species/per-encounter whitelist rather than deriving it solely from name, artificial Nemesis HP or current Hot/Cool status. Show the payout on the Wanted board before players enter. Each authentic death issues one fixed stack only; a party of five receives **one** kill's worth in total, not five. These fixed tokens opt out of all regional gold/loot/cosmetic chance multipliers, Expedition bonuses, pet/summon multipliers and magic-item odds. No bounty-gold bonus or stronger gear.

**Approved recipient rule — reuse ModernUO's existing damage scoring; do not build a new window**

- At monster death, consume ModernUO's already recorded damage entries and the **ranked per-player credited-damage ordering underlying `BaseCreature.GetLootingRights()`** (and the standard `Mobile.RegisterDamage()` source attribution). Audit the *actual pinned ModernUO revision* for its API, first-attacker credit, pet/summon ownership handling, expiry and equal-score behavior. Adopt that revision's existing scoring, including its approximately **two-minute inactivity expiry per attacker's aggregated entry** and **25% first-attacker credit bonus** where present. **This intentionally supersedes the earlier proposed strict last-60-seconds-or-combat-start window**; do not implement that custom event stream, and do not change ordinary corpse scoring to approximate it.
- The scorer's output must expose the **complete ordered contributor list**, not merely players whose `HasRight`/corpse-threshold flag is true: a lower-ranked living contributor may need to receive a bounty after higher-ranked contributors die even if that player's damage is below the ordinary loot-right threshold. If `GetLootingRights()` provides only a filtered subset or sorts in a different shape in the pinned revision, create a minimal shard-specific adapter using the **existing scored damage entries and their ordering**; do not duplicate the combat damage recorder or overwrite the game's corpse-right calculation. Document and stabilize ties against that revision's ordering; use a deterministic tie fallback if necessary. Damage credited to the responsible player through existing engine rules is credited once; enforce existing dungeon combat-pet prohibition rather than inventing an exception. Attacks by nonplayers with no legitimate credited player do not receive a payout.
- Walk the ranked list from highest to lowest and select the **first valid living player character at the moment the reward is committed**. Skip dead/ghost/deleted/nonexistent players without reranking or transferring credit to their party or killer. Treat disconnect/logout state according to the engine's real in-world/alive semantics; never invent a replacement recipient based solely on connection status. If no living valid contributor exists, no Wanted currency is minted; normal corpse loot and crime rules continue. A lowest-ranked contributor can win after all higher-ranked contributors die even when their ordinary corpse-looting-right flag is false. No minimum last-hit damage, last-hit override, party-leader assignment, random winner, account-level duplication or separate attendance reward.
- Commit **one** physical reward stack **directly into the selected player's backpack** (not onto the creature's corpse, bank, party members or ground), accompanied by concise notification; keep ordinary corpse loot generation, criminality, looting-rights flags, player-vs-player kill credit, murder reporting, reputation and fame/karma unchanged by the **Wanted feature**; Section 4’s separate Loot Protection Ward may limit repeat unauthorized monster-corpse item transfers outside Hot Zones without changing this scoring or bounty delivery. **Backpack overflow is an implementation safeguard, not permission to select another player:** if a lawful direct insert is impossible, reserve one persistent, unique, character-owned pending bounty and notify the player; retry safe direct backpack delivery on a later eligible inventory action/login, without bypassing carrying limits or generating a second claim. This conservative overflow mechanism is subject to owner refinement before launch and must not grant a new free bank/ground retrieval or turn into transferable, duplicable claim vouchers. For unusual offline recipient handling, reserve the identical selected-character entitlement until a safe delivery opportunity.
- Compute an immutable kill/reward key from authoritative mobile identity plus original contract/week, and atomically guard claim state, chosen recipient and item/pending-entitlement issuance before allowing any duplicate death notification. Ensure world save/restart, rapid double callbacks, reward insertion failure, inventory stack merge and concurrent killing cannot mint the same payout twice or silently lose the claimed stack. Provide staff-only audited recovery for genuine delivery failures, never a public reset button.

**Wanted versus Nemesis; preserve all ordinary rules**

- An approved Nemesis that independently matches the current Wanted species/contract still produces **exactly one normal-species Wanted bounty** using the existing ModernUO scorer; its 50%-extra HP does not raise tier/tokens. Resolve its existing **25% species trophy OR +200% pre-region gold** exclusively on the ordinary corpse as already specified in Section 6.1. The Wanted currency goes only to the selected player's backpack/pending entitlement; a Nemesis trophy, if any, remains normal corpse loot and is not duplicated or converted to a Wanted trophy. No new pet legality, area classification, combat power, reward multiplier or corpse ownership rules.

**Permanent Britain curator and themed housing collections**

- Place one permanent, staff-owned, nonbuying **Monster Trophy Curator in Britain**. It offers separate Hot and Cool catalogs and accepts only the relevant physical currency. Catalog entries are tagged by the **specific dungeon of origin**, so Deceit, Destard and other approved dungeons have identifiable, separate existing-art decoration variants; available items are gated by the original dungeon theme/collection mapping, not by requiring the buyer to repeat a specific week's contract. Configure only feasible art/mappings found during the UOR stock-art audit. A player's saved physical marks/seals are valid after rotations and can purchase their currency's catalog items later.
- Launch tier prices **Easy 40 / Medium 120 / Hard 300 / Boss 600** Hot Marks or Cool Seals (never mixed or interchangeable). Merchandise is decorative-only, tradable, lootable, legally stealable, house-displayable; no bonus stats, exceptional equipment, storage/utility edge, enchantment, new magic tier or special PvP access. Curator does not buy back trophies/currency; ensure no beneficial ordinary NPC resale, salvage, vendor-advance reference value, BOD or other economic extraction. Curator withdrawal of currency and item award are transactional; validate item art and stock/price data, preserve normal inventory capacity, and do not double-spend or produce an item without consuming its cost.

**Configuration, diagnostics and launch safeguards**

```text
wanted.enabled = true
wanted.contracts.onlyCurrentRotatingHotAndCool = true
wanted.contracts.excludePermanentHythloth = true
wanted.contracts.targetsPerDungeonMin = 2
wanted.contracts.targetsPerDungeonMax = 3
wanted.contracts.requireNaturalSpawnOriginAndValidWeek = true
wanted.scoring.source = ModernUOExistingLootingRightsDamageRanking
wanted.scoring.rolling60SecondOverride = false
wanted.scoring.pickFirstLivingContributor = true
wanted.scoring.requireCorpseHasRightForFallback = false
wanted.payout.easy = 1
wanted.payout.medium = 3
wanted.payout.hard = 8
wanted.payout.boss = 15
wanted.reward.oneStackPerMonsterDeath = true
wanted.reward.delivery = selectedPlayerBackpack
wanted.reward.backpackOverflow = persistentPendingSameCharacter  # provisional delivery safeguard
wanted.reward.regionMultiplier = 1.0
wanted.currency.hot = HotMarks
wanted.currency.cool = CoolSeals
wanted.curator.location = Britain
wanted.curator.easyPrice = 40
wanted.curator.mediumPrice = 120
wanted.curator.hardPrice = 300
wanted.curator.bossPrice = 600
```

All configuration keys are conceptual; prefer existing ModernUO conventions and keep this feature a narrow shard-specific extension. Persist week/targets, spawn provenance, reward-claim keys, physical currencies and pending deliveries; audit both economy/token issuance and redemption. Track eligible kills, skipped dead scorers, no-living-recipient cases, delivery/pending failures, token inflow/outflow by type and trophy issuance by dungeon. See the dedicated Section 23 regression matrix; do not launch until art, damage API, loot independence and crash/restart tests pass.

### 20.7 No rapid-respawn difficulty increase

**Hot or Cool status must not globally accelerate monster respawn.**

Do not use the previous normal spawn-rate concept.

A player capable of clearing a room under normal dungeon timing should not suddenly be overwhelmed because the dungeon became Hot or Cool.

If downtime later proves excessive, any respawn optimization must preserve:

- normal maximum simultaneous spawn count
- normal encounter composition
- no re-spawn while the previous wave is still materially engaged
- no increased effective PvE difficulty merely to create activity

Reward players for accepting PvP risk; do not make the underlying PvE unpredictably harder.

### 20.8 Hot-Zone boundary rules

Boundary abuse is one of the highest-risk technical issues in this design.

Required rules:

- a normal innocent-vs-innocent attack may begin only if both attacker and target are inside the same active Hot Zone, unless another lawful hostility reason exists
- players outside the zone cannot safely snipe inward
- players inside the zone cannot damage protected innocents outside the boundary merely by targeting across it
- projectiles, delayed spells, fields, poison and other persistent effects must respect the originating legal aggression relationship
- stepping across the boundary must not instantly erase an existing fight

### 20.9 Combat carryover / anti-boundary escape

A player must not be able to attack in a Hot Zone, cross one tile into safety and become invulnerable.

Preferred implementation:

- when legal player aggression begins in a Hot Zone, persist the normal aggressor/aggressed relationship
- safe-world protection does **not** block continued hostility between those already-related combatants until the normal aggression relationship expires
- unrelated safe-world players cannot join the fight unless the target is independently grey/red or another legal rule permits it
- Recall/Gate restrictions use the normal aggressor state
- do not invent an arbitrarily long additional PvP timer unless existing UOR aggression timing proves insufficient

This allows a fight to finish naturally while preventing Hot-Zone combat from spreading to unrelated players.

### 20.10 Rotation-transition safety

A rotating dungeon can switch from safe to Hot while players are inside it. Handle this explicitly.

Cool rotation by itself does **not** change PvP legality, so Cool activation/deactivation requires no safety relocation. The only dangerous transition is a dungeon becoming Hot.

Before activation:

- announce the upcoming Hot Dungeon at least 30 minutes before the weekly switch
- repeat warnings at sensible intervals such as 10 minutes and 1 minute
- show a region message to characters currently inside

At activation:

- online characters remaining inside become subject to Hot-Zone rules
- characters who were logged out inside while the dungeon was safe should, on next login, be relocated to the dungeon entrance/outside safe side rather than silently spawning into active PvP
- staff/event NPCs and fixed containers are not reward-multiplied unless explicitly opted in

At deactivation:

- no new innocent-vs-innocent aggression may begin once the region becomes safe
- existing aggression relationships may finish through normal combat carryover
- criminal/red status persists normally

### 20.11 Entry communication

No player should enter unrestricted PvP accidentally.

Provide all of:

- login summary naming Hythloth, Fire Island, the current rotating Hot Dungeon and the current Cool Dungeon
- Britain bank/activity board
- `[ShardRules` / player status command output
- clear region-entry message such as `You have entered a PvP Hot Zone. Unrestricted player attacks and full-loot PvP are active here.`
- clear exit message
- distinct map/region labeling where technically practical

For Recall/Gate destinations inside a Hot Zone, warn the caster before travel if practical without making travel cumbersome.

Do not require a repetitive confirmation gump every single time an experienced player crosses the boundary.

### 20.12 Logging out and login placement

Audit logout/login behavior in Hot Zones.

Requirements:

- normal combat logout restrictions remain in force
- logging out must not clear an active aggression relationship in a way that enables immediate safe-boundary abuse
- logging back into Hythloth or Fire Island places the character back into a Hot Zone and displays the Hot warning immediately
- only the **rotation transition from previously-safe to newly-Hot** receives the protective relocation behavior described above

### 20.13 Travel and extraction

Do not add banks, stable masters or remote loot-extraction services inside Hot dungeons solely for convenience.

The value of a Hot-Zone run should include successfully leaving with the loot.

For Fire Island and Buccaneer's Den island:

- preserve ordinary travel methods appropriate to the era
- audit marked runes, Recall, Gate and boat access
- aggressor travel restrictions remain normal
- do not add a special risk-free extraction portal

### 20.14 Thieves in Hot and safe areas

Thieves remain relevant everywhere.

In safe areas:

- theft creates criminal exposure and can generate localized lawful PvP
- the victim and other legally authorized blues may attack the criminal
- the thief may defend through normal aggression rules

In Hot Zones:

- unrestricted player attacks are already legal by zone rule
- theft still produces normal notoriety/criminal consequences
- genuine criminal status and cumulative red timer acquired there continue outside the zone
- a qualifying blue player reaching zero health enters Knocked Out rather than ordinary death; any criminal/red may perform no-skill Knocked-Out looting without engagement-right limits, and any player may Execute subject to the normal ordinary-blue murder count
- physical Backpack Wards, including already-active 120-second protection, have no theft or Knocked-Out-loot effect in a Hot Zone; the invisible Loot Protection Ward likewise does not restrict Hot-Zone loot

Do not make Hot-Zone theft consequence-free merely because combat is already open.

### 20.15 Murderers, greys and anti-PKs

This structure should create a meaningful murderer/anti-PK ecosystem without allowing reds/greys to terrorize the entire safe world.

- reds and greys can be hunted by blues anywhere, including the Cool Dungeon
- reds/greys cannot initiate attacks on innocent blues outside Hot Zones merely because of their own notoriety status
- when a blue directly targets a red/grey with a qualifying offensive action, that red/grey may fight back against that specific blue under the resulting aggression relationship
- AoE-only/incidental damage does not establish that retaliation relationship
- Hythloth, Fire Island and Buccaneer's Den island are permanent places where reds know they can find unrestricted combat
- the rotating Hot Dungeon creates a predictable weekly second front
- Section 14 replaces stock UOR murder thresholds/reporting/decay: **each attributable ordinary-blue kill, including lawful self-defense and Hot-Zone kills, adds exactly one count and 24 cumulative real-world red hours**; historical counts do not independently impose active red/stat-loss penalties

### 20.16 Guild wars and future Factions

Consensual guild wars may authorize attacks outside Hot Zones when both sides explicitly opt in, but do not waive ordinary-blue murder counts; both participants need applicable `[Intent]` exposure to duel count-free.

Factions are still disabled at initial launch.

If Factions are enabled later:

- default to Faction player combat being legal only in configured Hot Zones unless the owner explicitly approves broader consensual faction combat
- controlled pets still do not participate in Faction combat
- do not let faction membership become a hidden bypass around safe-world rules

### 20.17 Hot/Cool reward eligibility and exploit rules

Reward qualification must be tied to the monster/spawner/resource's configured Hot/Cool region, not merely the killer's current coordinates.

Verify that bonuses:

- do not modify player corpse contents
- do not multiply fixed event rewards unless explicitly opted in
- do not stack Hot and Cool multipliers on the same dungeon
- do not stack twice when permanent and rotating region definitions overlap
- use normal pre-AoS loot-generation paths
- cannot be manufactured by dragging monsters across boundaries
- do not affect staff-spawned/test monsters by default
- do not affect unique bosses/event spawners unless explicitly opted in
- do not accelerate spawn rate
- do not create new power tiers

Nemesis variant rewards follow Section 6.1: only ordinary loot receives the single source-region multiplier; a failed trophy roll adds exactly 2× pre-region base gold afterward and never re-multiplies it. Converting a natural mobile never changes its original region eligibility, spawn pressure or Hot/Cool classification.

Hythloth must never also receive the rotating-Hot or Cool multiplier.

The active rotating Hot Dungeon and active Cool Dungeon must always be distinct.

### 20.18 Player visibility and activity concentration

The player should be able to answer **"Where is PvP happening?"** and **"Where are safe PvE players gathering this week?"** in seconds.

At minimum display:

- `Permanent PvP: Fire Island + Hythloth; Buccaneer's Den island`
- `Weekly Hot Dungeon: <name>`
- `Weekly Cool Dungeon: <name>`
- `Weekly Expedition: <region>`
- `Trade Route: Britain → <destination>`
- `Weekly Pilgrimage: <virtue / shrine>`
- `Next Pilgrimage Departure: <time>`
- `Expedition Resources: +50% yield`
- `Expedition Logistics: 3× resource carrying capacity in the region + connected towns`
- current reward premiums
- time until next rotation

Make Britain the default social/information hub:

- weekly activity board covering Hot, Cool and Expedition systems
- weekly Hot, Cool and Expedition rotation announcement
- event notices
- vendor-search access if implemented later
- tournament/event registration if implemented later

Do not create multiple competing social capitals at low population.

### 20.19 PvM dexxer viability and combat-template diversity

Begin with the **approved UOR-platform/T2A-timing hybrid in Section 4**, not generic stock UOR combat. Measure conventional warriors, archers, bards, mages and tank mages in ordinary PvM, heavily armored targets, Nemesis endurance fights and expedition bosses. Include resource expenses, downtime, survival, group contribution and reward/hour; do not infer viability from theoretical DPS alone.

If a weapon family has no relevant advantage or a build is materially behind across realistic activities, inspect weapon timers, poison/cure interactions and specialization opportunity cost before proposing a buff. Roughly 20% lower measured practical PvM reward efficiency is a *diagnostic trigger*, not an automatic increase. Candidate **separately approved PvM-only** responses:

- monster-only Parrying utility against selected incoming damage where coherent with classic defense;
- improved effectiveness of era-appropriate Slayer weapons after Section 9 itemization review;
- modest monster-only Archery adjustments after movement/equip timing correctness is verified;
- encounter mechanics rewarding melee positioning without inventing player-facing weapon specials.

Do not adjust global PvP damage, accuracy, classic insta-hit/precast timing or remove the approved exclusion of all weapon and Wrestling specials as a by-product of PvM tuning. Record owner approval and regression tests for each deviation.

---

## 21. Source Organization

Keep new shard-specific code grouped together wherever practical.

Preferred structure:

`Projects/UOContent/Custom/<ShardName>/`

with logical subdirectories such as:

`Configuration/`  
`Commands/`  
`Systems/`  
`Items/`  
`Mobiles/`  
`Regions/`  
`Events/`  
`Tests/`

Follow existing ModernUO conventions for:

- serialization
- `Configure()` discovery
- `[Constructible]`
- `[SerializationGenerator]`
- access levels
- command registration

Do not introduce a second dependency injection/framework architecture unless there is a compelling reason.

---

## 21. Do Not Rewrite Upstream Systems Without Evidence

For every requested mechanic, classify it as:

**A. Already correct under UOR**

No production code change.

**B. Correct but needs configuration**

Configuration change only.

**C. Existing feature is later-era and needs disabling**

Disable using era check/config/feature flag.

**D. Existing UOR behavior appears incorrect**

Fix narrowly and add regression test.

**E. Intentional shard customization**

Implement in shard-specific code/config and clearly label it as custom rather than historical.

This classification should be recorded in an era-audit document.

---

## 22. Required Era Audit

Before large customization work, create:

`docs/UOR-ERA-AUDIT.md` (era/feature baseline *and* the explicit combat-hybrid exceptions).

Use a table with these columns:

**System | Pinned commit/code path | T2A behavior | UOR behavior | Approved shard choice | Historical evidence vs verified code vs unresolved | Required action / change layer | Automated/manual test coverage**

Enumerate actual checks of `Core.T2A`, `Core.UOR`, `Core.AOS`, `Expansion.T2A`, `Expansion.UOR` and expansion/feature flags throughout the pinned repository. `Core.T2A` may be cumulative and true under UOR; never interpret it as an exclusive T2A-only branch without inspecting the condition. For each relevant branch, classify **retain, override, not applicable or test needed**; capture source path, line/commit and status. Re-audit after updates.

Include an explicit cross-era decision matrix for: insta-hit/equip/target timer, precasting/spell recovery, all auto-procs, Wrestling Stun/Disarm and cleared ready-states; Lumberjacking (+20 stock target versus separate historical +30); Anatomy/Tactics/Strength and direct-damage spells; weapon poison/spell poison/healing/cures/corrosion; bow movement/speed/accuracy; shield Parrying/armor wear; colored-material armor AR and magic armor AR; exceptional and tiered weapon durability; party/scorer/loot rights; runebooks/travel/Lost Lands/maps; housing/access/secure storage; item generation, BODs, spawns, SOS/treasure; skill/stat caps and veteran skill-cap rewards; pets and bonding; feature flags, client capabilities and stock-art compatibility.

Do not mark a finding 'verified' merely because a historical patch note says so or a single source-code search has no match; require the relevant runtime test for critical behavior.

Audit at least:

Combat  
Magery  
Weapons  
Armor  
Archery  
Poisoning  
Wrestling  
Lumberjacking  
Parrying  
Healing  
Skill gain  
Stats  
Death  
Looting  
Murder counts  
Stealing  
Taming  
Crafting  
Magic item generation  
Monster loot  
Travel  
Housing  
Parties  
Guilds  
Factions  
Young system  
BODs  
Insurance  
Pet bonding  
Facets  
Spawns  
Treasure maps  
Fishing / SOS / MiB and shipwreck extension  
NPC vendors

Do not guess when a source-code inspection can answer the question.

---

## 23. Tests

Add automated tests wherever ModernUO's existing test infrastructure makes this reasonable.

At minimum establish regression coverage for the highest-risk rules.

### Era/core mechanics

Verify:

- UOR expansion remains active **as platform baseline**; T2A-style combat is an intentional independent override
- only intended maps are accessible
- T2A-style insta-hit is **enabled** through a real validated setting and passes the timer/retarget/equip contract in Section 4
- both activated Wrestling specials and all three original automatic weapon specials never trigger, including migrated ready-state and relog cases
- AoS insurance is unavailable
- AoS item properties do not generate
- post-era skills/spells do not become available
- skill cap is correct
- stat cap is correct
- pre-95 accelerated skill gain follows configured tuning
- the Standard profile measures approximately 1h to 50, 2.5h cumulative to 70, 4.5h to 80, 7.5h to 90 and 12.5h to 95 under defined focused-training conditions
- every enabled launch skill is assigned an explicit era-relative pre-95 difficulty profile or documented override
- historically easy skills remain materially faster to train than historically hard skills before 95
- crafting and Animal Taming do not accidentally inherit ordinary combat-skill pre-95 curves
- normal random skill gain stops exactly at 95.0 and cannot advance a skill above 95
- reaching 95 initializes persistent per-skill Mastery state exactly once
- each skill uses rolling 24-hour Mastery Periods anchored server-side rather than local midnight/client time
- a login during a period marks it Active and awards that full period's 24 Mastery Hours even if the character subsequently logs out
- a 24-hour period with no login awards 0 Mastery Hours and cannot be backfilled
- multiple skills at 95+ accrue Mastery Time concurrently on the same character
- 95→96 costs 4h per +0.1, 96→97 costs 5h, 97→98 costs 6h, 98→99 costs 8h and 99→100 costs 10h36m
- exactly 50 Mastery increments total 336 Mastery Hours / 14 Active Mastery Days from 95.0 to 100.0
- cheap earlier-bracket Mastery Time cannot be converted into fixed generic credits that bypass higher-bracket costs
- a matured Mastery opportunity has a 10% chance per eligible use and succeeds automatically on the 10th eligible attempt if not earlier
- failed eligible attempts do not consume Mastery Time; successful +0.1 consumes exactly the current bracket cost
- invalid/trivial/blocked uses do not count toward the 10-attempt guarantee
- Mastery survives logout/death/restart without duplication
- Skill Gain Balls and Pilgrimage Inspiration do not shorten Mastery Periods, accelerate Mastery Time accrual or reduce Mastery Time cost
- temporary gain bonuses only modify the matured Mastery-opportunity trigger chance at 95+; the 10th attempt remains guaranteed
- representative Easy/Standard/Hard/VeryHard pre-95 milestone times remain in the intended order after temporary bonuses
- new characters receive exactly 20 Skill Gain Balls once
- activating one ball applies a 1.25× relative multiplier to otherwise-eligible skill gains for 60 minutes of logged-in character time
- Skill Gain Ball time pauses offline and persists through save/restart
- only one ball can be active; a second activation is rejected without consumption
- the ball bonus does not bypass 100/700 caps, skill locks, anti-macro rules or eligibility checks
- crafting/taming retain their slower baseline curves while receiving the same relative 1.25× multiplier
- balls survive death and never appear as corpse loot
- balls cannot be traded, dropped, vendored, secured, moved through pets/pack animals or otherwise transferred to another character/account
- deleting a character destroys its unused balls and remaining active bonus time
- login, resurrection, restart and other lifecycle events do not duplicate the grant
- pre-existing characters receive no automatic retroactive grant unless an explicit migration is run
- blessed runebooks survive death and retain normal UOR travel requirements
- BOD rewards do not leak post-era items
- Artisan Signature crafting, Standard-baseline 10× durability, ordinary skill-based repair/degradation, full loot and zero extra NPC/vendor/salvage value pass the Section 9.1 regression matrix
- Hot-Zone Skill Veteran passes Section 5.1 and the dedicated Section 23 tests: 160.0 only from genuine above-60.0 increases outdoors in current Hot Zones, never in a house/boat, with persistent global high-water protection and cosmetic-only optional title
- Nemesis Monsters pass Section 6.1 and the dedicated Section 23 matrix: Scope A wilderness/all dungeons, unchanged spawn pressure, +50% HP only, 25% trophy versus exclusive +200% pre-region gold, no duplicate regional multiplier or loot
- Roleplay Guestbooks pass Section 16A.1 and Section 23: exactly four persistent journals, two authentic equipped own-issued pieces at submission, immediate 280-character posts, global 10-minute cooldown, archives, audited retrospective moderation, player reports without automatic hiding and no RP rewards or PvP protection
- Rare Expedition Destination Vendor passes Section 15.12A and its Section 23 matrix: current-route town only for the full week, town-exclusive core and fixed 2–3 rotating rares, purchasing-character completed delivery required, unlimited core and exactly one rare purchase per account/week, transactional gold/item/allowance persistence and no power or NPC buyback
- restricted pet bonding does not add combat power
- PvP Intent, automatic blue-victim murder counts and cumulative red status satisfy Sections 3/14 and the separate Section 23 PvP test matrix; no stock murder-report/threshold/decay rule silently takes priority

### Combat-hybrid regression and balance test matrix

Before accepting the build, use a pinned commit and document test inputs and expected outputs. Automated tests should cover:

- correct expansion ID/map independently of the combat override and no silently ignored configuration settings;
- active instant first strike when eligible, preserved shared swing cooldown, no extra hits from equip cycles or target changes, consistent stamina/speed effects and persistence across relog/death;
- precast→equip→first hit→release sequence, casting interruption, held cursor timeout, spell recovery, weapon auto-unequip rule and spell/weapon shared timing (mark provisional parameters pending approval);
- no Crushing/Concussion/Paralyzing or Stun/Disarm execution through any hit/request route, even with stale flags after migration, save or restart; normal Wrestling defense remains;
- +0 to +20 Lumberjacking additive damage modifier at 0/50/70/90/95/100 and zero on non-axe classes; no GM-only +10 spike; validate two-handed and shield legality;
- ordinary Tactics/Anatomy/Strength effects without duplicated grade/magic/Lumberjacking bonuses;
- poisoned weapon eligibility, application, actual on-hit chance, poison tiers, cure success, healing during poison, Poison spell effects and corrosion where implemented; state whether current UOR already blocks healing;
- bow/crossbow/heavy-crossbow walking/standing, equip delay, hit probability, cadence and ammunition; no undocumented numerical buffs;
- Parrying by shield type and total effective AR across colored materials, exceptional/crafted/magic protection; armor/weapon durability including repair and Signature 10× rule;
- ordinary party and corpse-looting rights, Wanted damage ranking and full-loot Hot-Zone behavior unchanged by combat overrides;
- identical safe-world/Hot-Zone legality enforcement for melee, archery, precast release, delayed poison/fields and attack carryover across boundaries;
- historical pre-AoS item properties only, no later skill-cap/veteran reward loophole and correct blessed-runebook, BOD, pet-bonding and Felucca-only outcomes.

Manual PvP: tank mage vs tank mage; tank mage vs sword/shield, axe, poison fencer, macer and archer; specialist vs specialist and small-group encounters. Manual PvM: same classes plus warrior bard against ordinary monsters, armor-heavy monsters, Nemeses and expedition bosses. Record outcomes and expenses; no requirement of universally equal matchups. A ~20% efficiency gap or a family without a niche triggers investigation, **not automatic rebalancing**. No production launch with untested insta-hit/timer or special-attack exclusions.

### Hot-Zone Skill Veteran title — 160 points above 60

Verify at minimum:

- a new character seeds each skill's lifetime high-water from its actual initial value and has 0.0/160.0 progress; title is optional and not enabled automatically;
- Hythloth, Fire Island, Buccaneer's Den island and the current rotating Hot Dungeon count only when their current Hot membership is authoritative; former rotating Hot, current Cool and ordinary safe places do not;
- 40.0→60.0 yields 0, 59.9→60.1 yields 0.1, 60.0→100.0 yields 40.0, and four disjoint 60.0→100.0 eligible skills reach exactly 160.0; numerical precision and cap never award 160.1;
- character-owned, friend-owned, guild-owned, stranger-owned, public/private and Hot-area houses block gains at all supported house levels, rooftops and house footprint/courtyard geometry; crossing a house threshold on the same skill use obeys the position at gain commit;
- anchored, moving, docked and stationary boats, including deck and hold, block gains even when their region qualifies as Hot; stepping off and gaining legitimately on Hot land may count;
- gains in any nonqualifying area, house or boat update global per-skill high-water; lower/retrain below the previous record yields zero when subsequently in Hot, while genuinely exceeding the record outdoors in Hot counts only the new amount;
- administrative/scripted grants, initial skills, transfers, item/effective-skill changes and skill restoration yield no progress, but any actual raises update the high-water; gain callbacks cannot duplicate one committed increase;
- Skill Gain Balls/Pilgrimage add no direct points; Mastery time/credits/failed attempts add none, while a consumed successful +0.1 gain at 95+ can count when physically eligible at commit;
- progress and per-skill highs persist through restart, logout, death, rename and weekly rotation; character deletion removes state and another character never inherits it;
- exact 160.0 permanently unlocks the selectable `Forged in Danger` title once; selection does not change stats, cap, combat/PvP legality, identity color, loot, guild or notoriety, and hiding/showing it does not reset progress;
- inspection, corrections, logs and player-facing descriptions show the threshold and all exclusions accurately.

### Nemesis Monsters — natural spawns, endurance and mutually exclusive rewards

Verify at minimum:

- normal eligible hostile nontameable natural spawns convert at a statistically consistent 2% in approved wilderness, ordinary safe dungeons, active Cool, rotating Hot, Hythloth and other approved Hot geography; changing weekly status does not change the Nemesis conversion rate or add a separate roll;
- towns/beginner zones, guards, ordinary animals, tameables, player summons/controlled creatures, event/quest/unique boss and staff-spawned mobiles are excluded unless separately and explicitly opted in; species lacking valid art mappings safely spawn ordinarily;
- converting replaces one ordinary spawn, does not raise simultaneous count or shorten timer, never rerolls on despawn/region crossing/login/restart, and obeys configured per-dungeon/outdoor-cluster caps even under concurrent spawn callbacks;
- underlying rolled HP 100 becomes 150 starting and maximum HP with safe rounding; damage, Strength, attack speed, spells, AI, resistance, tamability and ordinary loot all remain identical to the baseline; no accidental self-heal/HP overflow or infinite death state;
- label/name and approved hue are visible on each supported stock client. Optional ~10–15% individual visual size works only if tested and compatible; otherwise use the name/hue or verified existing art fallback without changing targeting, pathing or server body size;
- each genuine death creates exactly one corpse and **one** reward roll, never a second reward after duplicate death callback, restart, overlapping region triggers or party contribution; despawns yield no reward;
- exactly 25% of representative Nemesis deaths generate one correctly mapped, species-specific decorative trophy with ordinary gold, **zero** consolation; the other 75% generate zero trophy and +200% of original pre-region rolled gold, including a zero-base-gold test;
- with a 100-gold base roll and `R = 1.0`, trophy outcome is 100 gold + trophy, no-trophy outcome is 300 gold; with `R = 1.5`, trophy outcome is 150 + trophy, no-trophy outcome is 350 (150 + 200), **never 450**; correct rounding and currency caps apply;
- existing Hot/Cool premiums apply only once and use origin/source eligibility; dragging, weekly rotation or Hythloth overlap cannot reroll or multiply consolation; no new magic-loot tier/odds, player-corpse multiplier or retroactive rewarded death;
- trophies remain tradable, legally stealable, lootable, displayable in houses and persistent across world save/restart, with provenance where supported and no unintended NPC resale/salvage payout; species trophies are not location-specific;
- Nemeses do not create tameable super-pets, allow prohibited dungeon combat pets, alter PvP legality, award duplicate party loot or duplicate the separately approved Section 20.6A Wanted-monster bounty;
- metrics and simulation show by-species trophy supply, encounter kill time, extra gold by source region and total expected money-supply impact without replacing population convergence incentives or requiring live operations.

### Wanted Monsters — existing ModernUO scorer, one living recipient and dungeon collections (#39)

Verify at minimum:

- exactly one current rotating Hot and one distinct current Cool dungeon have independent persistent 2–3-target lists, species correspond to real accessible natural spawns, and all targets/payouts are visible on Britain board; no Hythloth/ordinary safe-dungeon/surface bounties at launch; weekly rotation and restart do not reroll a list or double-activate contracts;
- only truly naturally spawned, correctly tagged monsters originating in the eligible dungeon and active contract/week pay; dragged-in, old-week, quest/event/staff/summoned/controlled/player-created, despawned and spoofed species never do; old monsters alive across rotation are not promoted to the new week; bosses offered only for real eligible natural encounters;
- Easy/Medium/Hard/Boss pay exactly 1/3/8/15 units respectively, as **one** Hot Marks stack or **one** Cool Seals stack per death, independent of group size, Nemesis HP, Hot/Cool rewards and Expedition/rare-drop multipliers; monster loot, gold, corpse creation and normal respawn rates remain unchanged;
- pin and audit ModernUO's actual `Mobile.RegisterDamage()` / `BaseCreature.GetLootingRights()` implementation and verify the rank order, existing per-attacker inactivity expiry, first-attacker bonus and pet-owner attribution against sample fights; the deprecated strict rolling-60-second proposal is **not** implemented and normal corpse damage scoring does not change;
- ranking includes low-damage contributors even if their normal corpse `HasRight` flag is false; dead/ghost/deleted contributors at the top are skipped in order until the highest remaining living valid player wins; disconnection follows actual engine in-world/alive semantics; all contributors dead yields no tokens; stable ties do not select multiple winners;
- award is a **single** physical stack directly to the chosen player's backpack, not corpse/ground/bank/leader/party; a full/inaccessible backpack reserves one durable same-character pending reward without bypassing capacity or choosing a different person; retries/world save/restart, merged stacks and repeated delivery never mint twice, and pending tokens become ordinarily lootable only after physical insertion;
- uniquely identified death/contract/week rewards are committed once under duplicate death callbacks, concurrent hits, crashes and world saves; recovery commands cannot reroll awards or mint a second instance; ordinary criminal looting rights, fame/karma, murderer/PvP kill credit and party behavior remain unchanged;
- a matching Nemesis grants one normal Wanted bounty plus its **independent** ordinary-corpse 25% species trophy OR exclusive non-trophy extra gold (never both, no double bounty or token multiplier); species trophies and dungeon-specific curator trophies cannot be mistaken for one another;
- Hot Marks and Cool Seals are separate persistent, normal unblessed/tradable/bankable/lootable physical currencies, remain available after rotation and never cross-convert; Britain curator tier prices are exactly 40/120/300/600 in the correct currency, cosmetic dungeon-themed stock is audited existing UOR art and never confers power;
- curator purchase atomically consumes correct physical currency and creates one trophy with standard capacity/full-loot rules; insufficient funds, concurrent purchases, serialization crashes, resale/salvage/BOD/vendor advance and ordinary NPC buyback cannot duplicate wealth/items; no mandatory GM intervention or manual spawn/stock cycle.

### Shipwreck Salvage — SOS bonus, sea travel, timed access and guaranteed collectible

Verify at minimum:

- an ordinary SOS recovery keeps the complete unmodified original chest reward and makes exactly one independent 25% chance to add one chart at **successful completed chest** creation; opening a MiB, looking at an SOS, a failed Fishing attempt, repeated chest openings, logout/restart, duplicate completion callbacks and Expedition fishing modifiers never award/reroll extra charts;
- representative completed SOS chest samples match 25% charts statistically without claiming a guaranteed every-fourth reward; charts are physical, unblessed, tradable, stealable, lootable and persist their unique IDs/coordinates through item movement, ownership, restart and death;
- every generated chart has a unique, genuinely boat-navigable Felucca ocean destination beyond ordinary shore-fishing access, clear of blocked/protected locations/disabled facets; invalid config fails safely without consuming or rerolling charts;
- only the chart holder aboard a real boat in the configured chart-coordinate radius may activate it; land, distant boat, invalid map, house and spoofed multi/character coordinates fail; normal boat rules, unrelated Recall/Gate/runebooks and sea-zone PvP legality remain unchanged;
- one valid chart atomically consumes once and creates exactly one visible, persistent finite site even under concurrent use, disconnect, crash/restart and double-click; no active site exists for failed activation;
- each site generates and persists 4–6 recoveries, an initial prize ID/tier and independent expiry metadata; rewards are committed once per successful valid fishing action, not per attempt, cannot duplicate on two simultaneous final fish or party events, and are never scaled by Expedition/Hot/Cool/ordinary resource bonuses;
- from minute 0 to immediately before minute 30 only the activator and recorded party members still in the authorized party may fish salvage; later joiners/other parties/unrelated alts cannot, and leaving a party cannot bypass the owner/party restriction;
- at exactly 30 real-time minutes any eligible boater can recover leftover salvage; at 60 minutes remaining actions and prize expire, including after logout/server downtime; all-recovered sites disappear immediately; UTC windows cannot be restarted or paused;
- if all recoveries are completed inside either exclusive or public phase, exactly one existing-art decorative item is delivered to the character committing the final successful action, with tier weights 60/25/12/3 (summing to 100), one of 8–12 audited unique item designs and persistent correct provenance; there is **no** separate failure roll on completed wrecks;
- premature expiry/abandonment never produces the unclaimed decoration, and an inventory-capacity failure leaves final action/prize unconsumed for retry while site is active (never mailing/free-dropping/duplicating the prize); after expiry no claim is possible;
- deco is housing-displayable, lootable/stealable/tradable, has zero NPC/reference/salvage/BOD payout and no stats or combat benefit; art-only site props are non-storage/nonblocking/nonlootable and cannot be moved into inventory;
- only modest ordinary treasure below an ordinary SOS chest is added across all finite salvage actions; simulation of real SOS completions, chart availability, 60/25/12/3 item distribution and gold faucets passes economy review; site does not modify monster spawn pressure, Hot/Cool region classification or broader travel;
- operations inspection lists active chart/site state, remaining recoveries, rights deadline, expiry, completed/expired ID guards and rarity/economy counts, while isolated staff tests do not mint regular production loot.

### Roleplay POI Guestbooks — immediate publication and retrospective reports (#31)

Verify at minimum:

- exactly four staff-owned permanent books at existing Orc Fort, Yew Graveyard/Crypt, Yew Militia/Court and Buccaneer's Den POIs spawn once and persist without duplication, movement, theft, container use or obstruction; directory lists the same four without teleport/remote entry;
- any living player may read active and archived entries without `[IC]`, guild or costume; reading never consumes a writing cooldown; Buccaneer's Den remains fully Hot while either UI is open;
- writer may submit with exactly two **different equipped slots** holding authentic `RoleplayIssued` items bound to them, mixing kits and using any book regardless of kit theme; one, zero, backpack-only, ordinary lookalike, same-item counted twice, foreign-bound or forged gear fails;
- gear and proximity are checked anew at atomic submission: removing a piece, walking away, dying or destroying issued gear between opening and commit rejects publication; equipping two valid issued pieces and standing close to the book permits a legitimate submission regardless of `[IC]` toggle;
- blank/oversized (>280 Unicode characters) and malformed/control/markup payloads are rejected or safely normalized per policy, and escaped content cannot impersonate a book command or compromise client/server rendering;
- successful submissions publish immediately and atomically with source POI, unique ID, server UTC timestamp, author-name snapshot and persistent staff-only author ID; readers cannot choose author/time, overwrite, edit, erase or reorder entries; rename does not mutate existing attributions;
- exactly one global per-character rolling 10-minute cooldown applies to successful submissions at any of four books; hopping books, concurrent packets, double-click/replay, relog, restart and death do not bypass it; rejected submissions do not consume cooldown; there is no daily cap or publication-approval queue;
- concurrent entry submissions and save/restart/crash recovery never double-publish, lose acknowledged entries or desynchronize cooldown/journal, and only one active volume exists per POI;
- volume 100 fills and archives read-only, entry 101 creates volume 2 automatically, indexed pages expose all visible archives across restart, and staff hiding removes an entry from both current and archived ordinary views without deleting its original audit record;
- any reader may report one specific immutable entry ID; a report enters a durable staff review queue, duplicate same-account/entry reports consolidate, spam throttling works and reporter identity stays staff-only; multiple reports never auto-hide, delete, impose punishment or prevent continued writing;
- staff can dismiss/resolve, hide and restore with staff identity/reason/time recorded; hidden entries retain original content for staff, reports survive restart, and no staff availability is required to keep normal publishing/reading working;
- book objects, messages and reports have no NPC/vendor/salvage/collateral value, no buffs/loot/titles/RP score and no access to faction or hostility powers; staff-only disable-writing does not remove reading/history or affect RP gear/Scene Props;
- dedicated diagnostics and per-POI counters verify entry IDs, rejected actions, archive rollover, reported queue and moderation audit without exposing private IDs or deleting historical entries.

### Starter package

Verify:

- newly created characters receive the intended archetype-appropriate Standard/vendor-quality starter equipment;
- each new character receives exactly one free, character-bound Starter-Issued physical Backpack Ward and an invisible permanent Loot Protection entitlement; duplicate create/init/relog/resurrection do not grant either twice, and one-time migration supplies only the invisible entitlement to all existing characters;
- the free Backpack Ward follows normal Ward priming/detection/protection but cannot be traded, dropped, banked, player/NPC-vendored, salvaged, mailed, transferred via pets/containers or merged; death destroys it if unused, with no regrant or extraction from repeated character deletion/creation; ordinary purchased/crafted Ward behavior is unaffected;
- no starter gear receives craftsmanship or magic-item bonuses;
- Starter Protection lasts exactly 4 hours of logged-in character time;
- the timer pauses offline and survives save/restart;
- death/resurrection does not reset or duplicate the protection timer;
- protected starter equipment does not become corpse loot during the protected period;
- issued starter gear cannot be sold to NPCs or player vendors;
- issued starter gear cannot be salvaged/smelted/cut into unrestricted value or used for BOD completion;
- the account receives the configured starter-gold grant exactly once;
- character deletion/recreation cannot repeat the starter-gold grant;
- mage starter package contains exactly 50 of each configured classic reagent;
- melee/archer consumable quantities match configuration;
- each profession starter-material package is granted at most once per account/profession;
- deleting/recreating a crafting character does not replenish that profession's entitlement;
- starter raw materials cannot be traded, sold, dropped for transfer, moved through pets/pack animals, or laundered by stack merging;
- starter raw materials can be legitimately consumed by the intended crafting profession;
- output created from starter raw materials has **no Starter-Crafted state**;
- crafted output immediately uses normal craftsmanship-grade rules;
- crafted output is normally tradeable/sellable/lootable/BOD-eligible when otherwise valid;
- crafted output contains no hidden starter provenance after the craft transaction;
- a quality item produced from starter materials is not downgraded, blocked from market use or stripped of maker attribution;
- adversarial repeated character creation cannot create an unbounded gold/resource/item faucet.

### Keys/property

Verify:

- house keys, boat keys and ordinary lock/container keys remain unblessed and stealable/lootable
- stolen house keys grant access but never ownership/co-owner/transfer/admin rights
- house-sign re-keying invalidates old copies without requiring possession of the compromised key
- boat-key theft and approved backup/recovery behavior work
- key rings do not bless otherwise lootable keys

### Safe-world hostility

Verify outside Hot Zones:

- blue cannot melee blue
- blue cannot shoot blue
- blue cannot cast harmful spells on blue
- blue cannot damage blue with attributable consumables
- blue cannot create harmful-field damage against protected blue targets
- safe-world checks cannot be bypassed with delayed effects, traps or proxy actions
- failed illegal hostility does not unnecessarily consume reagents/ammunition/items where preventable
- stealing still works except in the active Cool Dungeon, mapped bank protection regions or against an activated-Backpack-Ward victim; snooping still works everywhere; Loot Protection blocks only repeated unlawful monster-corpse item transfers by a previously recorded offender in ordinary non-Hot regions

### Backpack Ward and bank theft-protection regression matrix

Verify with normal and GM thieves, new and veteran victims, multiple thieves and a GM-controlled real client:

- no Awareness skill, custom Bless theft protection, Magic Trap/Untrap theft rewrite, Wardbreaker, QTE or Ward stun exists; ordinary spells and stock Stealing success rates remain intact
- carrying Wards makes them eligible indefinitely but does **not** prime them on insertion, relog or protection expiry; the first ordinarily detected attempt or undetected successful transfer requiring a Ward counter selects/primes one Ward, without a skill requirement, timer or manual action; consumption occurs only on detected activity after resolution
- with multiple eligible unprimed Wards, first qualifying activity primes exactly one deterministic stable item; subsequent thefts reuse that primed item regardless of inventory order; spare Wards stay unprimed, never stack/extend protection and do not automatically prime when the previous Ward triggers or protection expires
- legitimate snooping may reveal physical Wards and their visible primed/unprimed states without exposing per-thief counters; Wards cannot themselves be stolen, and snooping remains legal in protected banks/Cool Dungeon
- the first attempt succeeds/fails with unchanged skill checks; if it transfers an item and is then detected, the transferred item stays with the thief
- normal victim detection primes/activates exactly one eligible Ward after any resolved attempt, including a detected failure; bystander-only detection does not prime or trigger it; no Ward means ordinary detection only
- for each separate thief account targeting the same victim with the same Ward, ordinarily **undetected** successful transfers 1/2/3 have exactly 25%/50%/100% extra victim detection; the third success for that thief cannot remain undetected; ordinary victim detection remains independent
- failures do not advance success count or receive an extra Ward roll; undetected failures do not prime any Ward or turn into free item transfers
- two alternating thieves maintain independent counters: a newcomer starts at 25% even if another thief has two successes, while that prior thief retains the 100% third-success guarantee; different characters on one account share a counter
- the Ward activates only **after** the triggering transfer, blocks all later thief attempts on root/nested backpack contents for exactly 120 seconds, does not block normal death/loot or legal combat, and never adds a stun
- simultaneous or queued steal attempts cannot commit multiple transfers after detection/activation; invalid/disconnected/out-of-range/item-moved attempts never duplicate loot or apply stray detection
- theft cannot begin or commit with either endpoint in a mapped bank theft-protection region or active Cool Dungeon; edge crossing cancels correctly; snooping and legal Hot-Zone PvP stay intact, including Buccaneer's Den bank
- primed and unprimed Ward names/properties are visibly distinct to owner and snooper on stock clients; item identity, selected-primed reference and appropriate per-Ward/per-victim/per-thief history persist through relog, backpack swaps, removal/reinsertion, transfers, world save/restart and region crossings; only active immunity has a 120-second server-authoritative timer
- moving/reinserting Wards cannot silently change the chosen primed item, reset its counts or leave multiple eligible primed Wards; an incoming formerly primed Ward is reconciled without deleting its historical counters; two concurrent thieves cannot prime separate Wards or bypass a freshly activated protection window
- ward activation and ordinary detection retain stock guard, crime and notoriety behavior; bank/Cool/Ward restriction does not protect an already-criminal thief from lawful attack

### Loot Protection Ward — corpse-looting regression matrix

Verify with a GM-controlled real client, genuine party/solo kills, multiple offender accounts, same-account alternate characters, Hot/Cool boundaries and save/restart:

- new characters receive an invisible, nonconsumable permanent entitlement; existing characters receive it once by idempotent migration. It uses no backpack slot, cannot be sold/stolen/dropped/consumed, and persists across death, four-hour starter timer, logout and restart; ordinary physical Backpack Wards remain wholly separate;
- genuine corpse rights are sourced from the pinned ModernUO implementation, including shared legitimate holders and expiring rights. A lawful contributor/party member loots normally and never creates or suffers an unlawful-loot restriction merely because someone else also has rights;
- the first actual unauthorized monster-corpse item/stack transfer in the safe world or active Cool Dungeon completes and keeps the item, applies ordinary crime, and atomically creates a 10-minute offender-account entry for each affected legitimate character rights holder; no entry for inspection/opening, failed drag, public corpse or merely witnessing a theft;
- every later unauthorized transfer by that offender account from the original corpse or a different new monster corpse on which the victim currently holds exclusive loot rights is blocked before movement for the remaining entry lifetime, even with same-account alternate thief characters or concurrent loot-all/stack-splitting; legitimate shared-loot transfers remain legal;
- blocked attempts neither steal nor duplicate items, create a new criminal flag solely because of the block, reset the timer nor extend the expiry. A fixed absolute UTC expiry removes the entry so a later first successful offense is permitted and starts a fresh 10 minutes. Repeated failed/blocked tries cannot pin an entry forever;
- a separate offender account initially retains its own ordinary first unauthorized item transfer, without inheriting the first offender's entry. Multi-victim shared rights create independent victim keys; nearby bystanders and non-rights holders never gain entries;
- fully public corpses and expired rights are never protected; player corpses, pets/summons' inventory, ground loot and regular Stealing remain unaffected. Hot-Zone monster corpses and Hot-Zone theft remain ordinary full-risk even during an entry; moving/reclassifying the corpse cannot create a safe-world protection bypass or fake protection;
- existing grey status, guard calls, lawful retaliation and guild/Hot combat remain intact during both blocked attempts and region crossings. This feature never creates combat immunity, blesses items, reverses the first theft or alters Wanted token delivery/loot scorer;
- the same victim/offender entry survives death, logout, alternate characters, region transitions and restart but expires according to its original real-world UTC time; stale entries are garbage-collected without losing permanent entitlements or disclosing private IDs to players;
- simultaneous loot commits, nested corpse containers, loot-all and stack splits allow at most the initial authorized-by-design criminal transfer before the offender restriction commits; rejected/rolled-back moves never create entries, money or duplicates; audit logs identify repeat incidents without automatically banning anybody.

### PvP Intent, genuine crime and cumulative murder regression (#40)

**Use a pinned ModernUO commit, two or more real clients where needed, deterministic server-UTC test clock, controlled character identities and explicit attacker–victim encounter IDs. Test all of the following before rewards or Hot rotations go live.**

1. Only genuine blues can enable one `[Intent]` flag; grey intent is visibly distinguishable from actual crime; actual crime/guards/criminal assistance and `[IC]` remain independent. Active actual grey or red status blocks disabling stored intent and takes display precedence; status resumes the previous stored preference when genuine restrictions expire. State persists death, logout and restart.
2. Outside Hot Zones, block new ordinary-blue↔ordinary-blue hostile initiation; any player may initiate against `[Intent]`, genuine grey or red; a flagged/grey/red cannot initiate against an unrelated ordinary blue, including harmful spells, potions, pet proxies and fields. Legal direct-target aggression grants rights to that specific blue only; incidental AoE grants none.
3. Two intent-flagged players can duel/kill each other without crime or murder. A solo intent participant killing an attacking **ordinary** blue always gets one murder count even though retaliation was lawful. A blue can attack a real grey or red without becoming criminal or surrendering their own murder protection; a red/grey killing that blue, **including defensive kills**, always gets one count and 24 hours.
4. Hot Zones permit ordinary-blue↔blue, grey/red→blue and other initiation. Permitted nonlethal attacks do not automatically confer real criminal status. Killing an ordinary blue by a blue/grey/red gives exactly one count and 24 hours whether attack or self-defense; killing intent-exposed/real-grey/red victims gives none. Distinguish independent theft/loot crimes.
5. Toggle OFF during a valid intent-originated fight: uninvolved blues/new attackers cannot initiate outside Hot Zones; original opponent can continue and kill without a retroactive count. Toggle ON during an ordinary-blue-originated fight does not remove that encounter's murder protection. Multiple simultaneous opponents receive distinct rights/snapshots; unrelated attackers gain none. Death/pending spell, poison, projectile, field, logout, combat-timer expiry and safe/Hot boundary crossing cannot rewrite classification.
6. A genuinely grey target whose criminal timer expires during an existing lawful encounter does not cause a retroactive murder count for the already-authorized opponent. New attacks after expiry obey current ordinary-blue protections unless a separate lawful relationship exists. Genuine status and voluntary hue are never conflated.
7. First qualifying ordinary-blue murder sets red deadline to `nowUTC + 24h`. Ten hours remaining plus a kill yields 34 hours; a second yields 58 hours. Advance real UTC while offline, including save/restart/downtime; no online-only countdown, region cleansing, death-based reset, historic count threshold or delayed stat-loss from the history tally.
8. Red expiry returns player to real criminal grey if independently still criminal, otherwise blue or stored `[Intent]` as applicable; historical counts remain inspectable but never sustain red status. Attempted OFF during real murderer/criminal status fails without clearing other state.
9. Same player death through two callbacks, corpse reopen, victim murder report or delayed duplicate event awards **one** history entry and one 24-hour extension; attributing poison/spells/AoE/controlled-creature damage is deterministic. No kill awards from PvE death, fake/test death or invalid deleted entities.
10. Guild-war/event permission authorizes attack where valid but does not waive the murder count for killing an ordinary blue; both participants must supply applicable intent to waive. No faction membership or pet auto-targeting bypass; guards and banker theft-only zones retain separate rules.
11. Staff diagnostics show current real criminal flag, intent preference, effective hue, per-pair lawful fights/encounter snapshots, red expiry UTC, remaining duration and historical count; staff corrections are privileged, logged, idempotent and do not produce bonus deaths/counts.
12. Player help, login/status and Hot-Zone entry messaging explicitly distinguish attack legality from murder consequences, warn of 24-hour cumulative counts on ordinary-blue kills, and explain safe-new-fights intent OFF with continuing old opponents. Verify supported unmodified client display.

### Intent, genuine criminal retaliation and cumulative murderer status

Verify the complete Section 3/14/23 PvP matrix below. Specifically:

- A genuinely blue character alone may switch on single grey `[Intent]`; intent alone causes no crime, guard response or criminal assistance, and cannot be switched off while real grey/red status is active.
- A blue can attack an intent participant, genuine grey or red anywhere; an intent/grey/red can retaliate against only the specific blue who directly attacked them outside Hot Zones, and killing that blue adds one murder count and 24 hours even in self-defense.
- A genuine thief becomes actually criminal; ward, guards and assistance rules continue to work. An intent-only grey is NOT criminal for these systems, and appearance never grants pet aggression.
- Turning intent OFF makes the former participant safe from *new* attackers outside Hot Zones immediately but does not cancel an opponent's lawful active fight, its original murder classification or combat logout/travel consequences.
- An actual criminal-grey timer expiring mid-fight cannot retroactively turn the prior legal opponent's kill into murder. A blue who switches intent ON after being attacked retains existing encounter murder protection.
- In Hot Zones, any player may initiate, but a blue/grey/red killer of an ordinary blue earns one automatic count and 24 cumulative real-time hours; the same permitted nonlethal attack alone is not a separate crime.
- A murdered ordinary blue cannot grant a waiver merely by having initiated against the killer; no blue-on-red self-defense exception exists.
- Red expiry advances offline, new kills append time, expiry restores blue or live real-grey/intent state, historical counts never maintain red status/stat loss, and old report/bounty callbacks never double-award.
- Player-character pets stay under their approved restriction regardless of intent and Hot-zone hue; genuine criminal help/guard and ordinary looting rights remain intact.

### Housing concentration

Verify:

- open residential districts allow ordinary normal-cost player-house placement
- approved rural wilderness permits placement only after charging the configured rural premium
- a 2.0× rural multiplier produces a total placement cost equal to twice the normal house/deed value
- the rural premium is consumed and is not restored by demolition, redeeding or transfer
- re-placing a redeeded house in rural land charges the rural premium again
- rural payment never bypasses protected/no-housing regions
- closed districts reject placement even when terrain would otherwise be valid
- Greater Britain launch districts provide the intended initial placement pool
- no normal-cost residential districts exist outside Greater Britain
- one-house-per-account is enforced across placement and transfers
- Fire Island permits placement only inside configured `FireIslandResidential` regions and remains always open independently of mainland district state
- Buccaneer's Den island rejects placement regardless of district state
- permanent no-housing reserves cannot be bypassed with house footprint edges, multi placement, transfer, redeed or staff-created deed variants
- once a district is opened, it does not automatically close around existing residents
- district house counts and soft-capacity metrics survive server restart/save-load
- reaching the configured occupancy/spare-capacity threshold correctly marks only the next Greater Britain district eligible to open
- after the final Greater Britain district is open, the system reports no next district and never unlocks another normal-cost town region
- after final Greater Britain saturation, approved placements elsewhere require the rural surcharge except for the explicit Fire Island housing exception
- staff can open the next configured district without a code deployment
- housing expansion does not depend solely on current concurrent-player count
- rural houses are tracked separately from Greater Britain district occupancy and do not suppress a still-pending Greater Britain unlock
- telemetry reports rural-house share and rural-premium gold removed
- inactive-house qualification and warning/decay behavior match the configured policy
- player vendors work normally inside approved housing districts
- house keys/re-keying still follow the explicit unblessed-key rules

### Expedition Regions and trade routes

Verify:

- exactly one Expedition Region and one primary associated trade route are active
- rotation persists through save/restart and avoids immediate repeats when possible
- active Expedition status does not change safe-world PvP legality
- ordinary wilderness outside the Expedition remains at 100% baseline rewards
- approved gathering in the active Expedition Region produces the configured **1.50× quantity yield** over sufficient samples
- Expedition resource bonus changes harvest yield rather than resource-node respawn speed
- rare-resource tier/chance remains baseline unless separately configured
- non-resource items, monster loot and purchased commodities do not receive the +50% gathering bonus
- Britain, the active destination town and the Expedition corridor all grant the Logistics resource-weight behavior
- approved raw resources receive approximately one-third normal weight / 3× effective carrying capacity
- non-resource inventory retains normal weight
- item-count/container-slot limits remain normal
- pre-existing resource stacks carried into the Expedition cannot acquire reduced-weight provenance
- resources actually harvested under the Expedition system retain only the intended hauling benefit after leaving the area
- banking, house storage, trading, dropping, selling, pet transfer and configured refining/transform actions clear or transform Logistics provenance correctly
- splitting/merging stacks cannot duplicate reduced-weight provenance or quantity
- pack animals do not multiply the player's Logistics capacity
- logout/restart and weekly rotation preserve/expire provenance correctly without permanent reduced-weight items
- Expedition status alone does not increase monster difficulty, spawn count or respawn speed
- trade cargo is issued with a unique persistent ID and accepting-character ownership
- cargo cannot be Recalled, Gated, public-moongated or custom-teleported to bypass the route
- ordinary non-cargo travel remains unaffected
- route completion requires configured ordered checkpoints and destination turn-in
- checkpoints are broad enough to allow reasonable road detours
- cargo cannot be banked, traded, vendored, secured in a house, moved to pets/pack animals or transferred to another character
- cargo/progress survives logout, death/resurrection and server restart without duplication
- abandoning cargo destroys its reward eligibility
- post-rotation grace/expiration works exactly as configured
- one cargo identifier can grant a reward only once
- atomic turn-in cannot duplicate rewards through disconnect/restart
- staff/test cargo is non-rewarding unless explicitly enabled
- route rewards are not granted merely for entering the region or reaching destination without valid checkpoint state
- route activity does not create new normal-cost residential districts outside Greater Britain

### Rare Expedition Destination Vendor — full-week town collections, eligibility and purchase limits (#36)

Verify at minimum:

- exactly one vendor is available **continuously from weekly Expedition activation until its end**, only in the current non-Britain route destination at its surveyed accessible location; no old three-times-weekly/two-hour scheduling, no Britain-origin vendor, no extra vendor in inactive towns, and no creation of an extra trade route;
- configured candidate destinations Yew/Cove/Minoc/Trinsic, and Vesper **only if an actual destination**, select their own correct exclusive collections; missing outpost/town mapping fails configuration safely; the actual allowed destination set comes from the real route registry;
- each configured town has 6–8 valid existing-art designs with 2–4 permanent core and at least four distinct rare-pool candidates; no duplicate graphic/design is improperly sold as two town-exclusive collectibles, invalid art IDs are rejected, and cosmetic items add no power or gameplay access;
- all configured core designs remain for sale throughout an active town week; two or three **distinct** rares selected only from that town's rare pool appear for the full week, with correct rarity weights and prices; a listed rare is delivered on purchase without an additional random roll;
- selection, catalogue, vendor presence, week ID and prices persist through world save/restart, logout, vendor rebuild and multiple rotation callbacks without random reroll; a genuine new Expedition week can produce a fresh selection even if the same town recurs;
- the shop may show stock before a delivery but **purchase fails** for cargo acceptance alone, arrived-but-unturned-in cargo, incomplete checkpoints, another character's completion, previous-week/old-grace deliveries, staff/test invalid cargo, canceled contracts, and off-route attempts;
- this exact purchasing character's valid current-week route completion unlocks normal buying until rotation without consuming their completed-delivery ledger or relaxing ordinary cargo physical-travel requirements; a later route turnover immediately stops prior-week eligibility;
- ordinary core purchases remain unlimited per independently eligible character/account subject only to required gold, proximity and normal interaction checks; buying core never consumes a rare slot; repeated deliveries do not increase rare allowance;
- across two characters/sessions on the same account, exactly **one total rare item** can be purchased in the current Expedition week, regardless of rare design, town/vendor state, character deletion/rename, two simultaneous clicks or client reconnection; the next real week restores exactly one rare allowance without retroactive purchases;
- sufficient gold is deducted exactly once and exactly one selected, properly tagged item is created per successful purchase; insufficient gold, invalidated eligibility, full backpack, interruption, canceled UI, disconnect and server crash at each commit boundary produce no duplicate item, double gold charge, orphan item or consumed-but-undelivered entitlement;
- no account may bypass limits via trade/rebuy, refund/buyback, inventory reroll, serialization, GM-driven same-week reconstruction or multiple delivery receipts; approved staff corrections are audited and do not silently reset counters;
- vendor never purchases from players; NPC resale, salvage, deed conversion and item extraction cannot turn purchases into guaranteed profit; gold is a one-way sink, trade items remain ordinarily player-tradable/full-loot and equipment properties/bonuses remain unchanged;
- public board and vendor messages display current destination, all-week availability, item choices/prices, the actual purchasing character's completion requirement and the account's rare allowance, without exposing private IDs; current region PvP/crime, Hot/Cool, gathering and Logistics rules stay unchanged;
- staff can inspect active vendor placement, collection/stock, purchase-eligibility failures, rare ledger and gold-sink totals; effective config, reference docs and world-rotation tests match this subsection, with no staff intervention needed for normal operation.

### Pilgrimage

Verify:

- exactly one Virtue of the Week is active
- only approved mainland-continent shrines can be selected
- pilgrimage can begin only from Britain
- scroll issuance is available only during the configured 15-minute departure window
- departure windows recur every configured 4 hours using server-authoritative schedule/window IDs
- a valid starter may finish after the 15-minute start window closes
- a character can have only one active pilgrimage
- abandoning an incomplete pilgrimage allows a later-window restart
- successful completion prevents another completion on that character until weekly reset
- scroll is blessed, character-bound, non-transferable, non-bankable, non-droppable, non-vendorable, non-secureable and cannot be placed on pets/pack animals
- Recall, Gate, public moongates and custom instant travel are blocked while pilgrimage is active
- mounts remain usable
- death/logout/restart preserve scroll/checkpoint state without duplication
- broad route checkpoints must be completed in order
- wrong-shrine use does not consume the scroll
- valid shrine completion is atomic and recorded exactly once
- completion ranking is server-authoritative per departure-window ID
- exactly the first 5 valid finishers receive +20% Greater Pilgrim's Inspiration
- later valid finishers receive +10% Pilgrim's Inspiration
- simultaneous completions cannot duplicate a top-five slot
- the Inspiration reward is stored ready-to-activate rather than beginning immediately
- activated Inspiration lasts 60 minutes of logged-in character time and pauses offline
- Inspiration does not bypass skill caps, skill locks, anti-macro logic or normal gain eligibility
- +10% Inspiration plus a +25% Skill Gain Ball produces +35% relative gain, not 37.5%
- +20% Greater Inspiration plus a +25% Skill Gain Ball produces +45% relative gain, not 50%
- weekly rotation expires/reconciles old incomplete pilgrimage state according to configured policy

### Road Travel Bonus

Verify:

- approved road tiles/regions activate road travel server-side
- normal off-road movement remains unchanged
- target on-foot bonus is approximately +15% or the nearest stable supported timing
- target mounted bonus is approximately +10% or the nearest stable supported timing
- Pilgrims receive the same road bonus when otherwise eligible
- Expedition trade-cargo carriers receive the same road bonus when otherwise eligible
- Expedition Logistics resource hauling does not alter the road multiplier
- active PvP aggression disables road bonus
- permanent and rotating Hot Zones disable road bonus
- merely being red/grey without active PvP does not disable road bonus
- leaving a road returns movement timing to normal without persistent speed state
- road-edge transitions do not spam messages or create timing exploits
- client/server movement remains synchronized
- intended speedhack detection does not falsely flag legitimate road movement
- road bonus does not stack multiplicatively with unapproved custom movement modifiers

### Permanent Hot Zones

Verify:

- Hythloth is always unrestricted PvP
- Fire Island surface is always unrestricted PvP
- Buccaneer's Den town and island are always unrestricted PvP
- ordinary innocent-vs-innocent attacks work inside those regions
- full-loot death works
- murder/criminal systems still function
- Fire Island house placement is allowed only in approved Fire Island residential areas
- Fire Island house interiors remain Hot-Zone PvP rather than becoming safe regions
- entering/leaving a Fire Island house does not clear aggression/criminal/murderer state
- Buccaneer's Den island house placement is rejected
- combat pets remain prohibited in Hythloth
- outdoor pets on Fire Island and Buccaneer's Den island still obey the separate lawful-target pet-PvP restriction

### Rotating Hot Dungeon

Verify:

- exactly one eligible non-Hythloth dungeon is active
- rotation occurs on schedule
- previous Hot dungeon returns to safe-world rules after deactivation/carryover
- newly Hot dungeon allows unrestricted PvP
- Hythloth is never selected or double-bonused
- offline characters logged out while a dungeon was safe are relocated appropriately if they log in after it becomes Hot
- rotation announcements/status display the correct dungeon and time

### Hot-Zone boundaries

Verify:

- blue outside cannot attack protected blue inside solely across the boundary
- blue inside cannot attack protected blue outside solely across the boundary
- two players already in a valid Hot-Zone aggression relationship can continue that fight after crossing out until normal aggression expires
- unrelated players outside cannot join the carried-over fight unless another legal hostility rule applies
- delayed spells/projectiles/fields respect legal aggression
- Recall/Gate aggressor restrictions are not bypassed by crossing the boundary

### Cool Dungeon of the Week

Verify:

- exactly one eligible Cool Dungeon is active
- Hythloth is never selected as Cool
- the active rotating Hot Dungeon is never also Cool
- Cool selection avoids immediate repeats when possible
- Cool dungeon remains under normal safe-world PvP legality
- direct player stealing is disabled in the Cool Dungeon
- snooping remains enabled in the Cool Dungeon
- ordinary corpse rights and criminality remain, subject only to the per-offender Loot Protection Ward restriction on repeat unlawful monster-corpse transfers
- greys/reds remain lawfully attackable under ordinary rules
- combat pets remain prohibited
- Cool status applies +10% ordinary scalar rewards/gold
- Cool status applies +10% relative magic-item generation chance
- Cool status does not increase monster stats, spawn count or respawn speed
- Cool bonuses cannot be produced by dragging monsters across region boundaries
- forcing Hot status onto the current Cool dungeon cannot produce stacked states
- Cool state survives save/restart and rotates correctly

### Hot rewards

Verify:

- ordinary safe-world PvE remains at 100% baseline rewards
- Cool Dungeon receives only its configured +10% reward and +10% relative magic-item chance bonuses
- Hythloth receives only its permanent Hot multiplier
- rotating Hot dungeon receives only its rotating multiplier
- Fire Island receives only its configured outdoor multiplier
- Buccaneer's Den island remains at baseline rewards unless an explicit separate incentive is enabled
- reward eligibility derives from configured spawn/resource ownership and cannot be manufactured by dragging targets across boundaries
- player corpse loot is never multiplied
- event/staff rewards are not multiplied by default
- no new power-item tier is created
- **Hot or Cool status does not accelerate normal monster respawn or increase simultaneous spawn count**

### Pets/taming

Verify:

- combat-capable controlled pets cannot enter dungeons through walking, Recall/Gate, login relocation, resurrection, transfer, release/retame or other loopholes
- controlled pets cannot attack innocent/blue players even in Fire Island/Hythloth Hot Zones
- controlled pets can attack lawful greys/criminals and reds
- player aggressors who become lawful targets to the tamer can be attacked by pets
- Faction status alone never authorizes pet aggression
- pet auto-retaliation/guard/direct commands all use the same lawful-target validation

Tests should test behavior, not merely constants wherever feasible.

---

## 24. Manual Test Characters

Create documented test templates for manual verification.

At minimum:

**Mage**

GM Magery  
GM Evaluating Intelligence  
GM Meditation  
GM Magic Resist  
plus relevant test skills

**Tank Mage — complete seven-skill reference**

GM Swordsmanship  
GM Tactics  
GM Magery  
GM Evaluating Intelligence  
GM Meditation  
GM Resisting Spells  
GM Wrestling

**Sword/Shield Warrior — complete seven-skill reference**

GM Swordsmanship  
GM Tactics  
GM Anatomy  
GM Healing  
GM Resisting Spells  
GM Parrying  
GM Magery

Test equipment legality: one-handed sword + shield, not shield with a two-handed axe. No Stun/Disarm test character is a valid launch template.

**Swords/Lumberjack**

GM Swords  
GM Tactics  
GM Anatomy  
GM Lumberjacking

**Fencer/Poisoner**

GM Fencing  
GM Tactics  
GM Poisoning

**Macer**

GM Macing  
GM Tactics  
GM Anatomy

**Archer**

GM Archery  
GM Tactics  
GM Anatomy

**Thief**

GM Stealing  
GM Snooping  
GM Hiding  
GM Stealth if available/appropriate

**Tamer**

GM Animal Taming  
GM Animal Lore  
GM Veterinary

Use admin commands to create test conditions rather than changing production skill-gain rates.

---

## 25. PvP Test Matrix

Manually test combat templates in both **safe-world** and **Hot-Zone** contexts.

Templates:

tank mage vs tank mage  
tank mage vs sword/shield warrior  
tank mage vs conventional dexxer  
swords/lumberjack vs mage  
fencer/poisoner vs mage  
macer vs mage  
archer vs mage  
dexxer vs dexxer  
red vs blue  
blue attacking blue  
criminal vs blue  
guild enemy vs guild enemy

### Safe-world matrix

Test:

- blue attacks blue: rejected
- blue harms blue with spells/fields/potions: rejected
- thief steals from blue: allowed if ordinary skill/rules permit
- thief becomes grey: correct
- blue attacks grey: allowed
- grey retaliates: allowed
- blue attacks red: allowed
- red attacks uninvolved blue first: rejected
- red retaliates after lawful blue attack: allowed
- consensual guild-war enemy combat: allowed only when valid
- unrelated third party cannot join a carried-over Hot-Zone fight without independent legality

### Hot-Zone matrix

Run the normal combat matrix inside:

- Hythloth
- Fire Island surface
- Buccaneer's Den island/town
- current rotating Hot Dungeon
- current Cool Dungeon and its +10% safe-PvE bonuses
- current Expedition Region and Britain-origin physical trade route
- Expedition +50% gathering yield and exactly which resource systems qualify
- Expedition Logistics 3× resource-only carrying benefit and the two connected towns
- provenance/cleanup behavior for Expedition-harvested resources when leaving the area
- current Virtue of the Week, Britain start location and Pilgrimage departure schedule
- first-five Pilgrimage race reward versus standard completion reward
- Pilgrimage fast-travel/checkpoint/mount rules
- road movement-speed bonus and PvP/Hot-Zone suppression rules
- cargo fast-travel restrictions, checkpoint behavior and post-rotation expiration

Test:

damage  
swing timing  
spell interruption  
movement  
poison  
healing  
bandages  
potions  
verify Stun always unavailable  
verify Disarm always unavailable  
verify all automatic weapon specials absent  
death  
corpse rights  
looting  
Recall  
Gate  
murder counts  
criminal state  
guard response where applicable

### Boundary matrix

Test:

- entering Hot region
- leaving Hot region
- attacking immediately before crossing
- target crossing before delayed spell impact
- fields overlapping a boundary
- Recall/Gate while aggressed
- logging out/in during aggression
- weekly rotation activation/deactivation while occupied

Record discrepancies.

---

## 26. World/Spawner Audit

Inspect existing spawners under the UOR configuration.

Identify:

- post-UOR monsters appearing in Felucca
- missing classic monsters
- inappropriate loot
- inappropriate NPCs
- inappropriate quests
- event systems running by default
- post-era vendors
- Hythloth region boundaries and every entrance/teleporter
- Fire Island surface boundaries, shoreline transitions and travel arrival points
- Buccaneer's Den island boundaries, town subregions, shoreline transitions, docks and travel arrival points
- all candidate rotating Hot Dungeon region definitions
- all candidate Cool Dungeon region definitions and overlap/conflict validation
- candidate Expedition Region corridors and their roads/bridges/crossroads
- proposed Britain-origin trade routes, ordered checkpoints and destination NPC locations
- exact origin/destination town-region definitions used by Expedition Logistics
- resource systems/items eligible for the +50% yield and 3× resource-carry treatment
- exact mainland virtue-shrine coordinates/regions and candidate Britain-to-shrine checkpoint corridors
- audited road tile IDs/road-region overlays, bridges and movement-timing hooks
- fast-travel mechanisms that could bypass physical cargo traversal
- dungeon subregions that might accidentally fall outside a parent Hot region
- spawners whose monsters can be dragged across Hot boundaries
- Nemesis-eligible natural hostile/nontameable spawners in wilderness and all dungeons, plus safe/Hot/Cool overlap, newbie/town, taming, boss/event/quest and player-created exclusions
- per-species HP rolls, death/corpse/loot generation, origin metadata, named hue/body variants, real per-creature scale support in the supported client, existing trophy art and bounded gold/serialization paths
- ordinary MiB/SOS recovery and chest-completion hooks; SOS chest reward once-only semantics; navigable Felucca ocean coordinates, shoreline range, boat/multi membership and existing treasure/art assets needed for shipwreck sites
- four approved RP POI book placement/art coordinates, existing book/Gump paging and append-only persistence hooks, trustworthy `RoleplayIssued` equipment/bound-owner verification at submission, write cooldown/atomic commits, staff audit and report queue hooks
- safe/Hot overlap errors
- existing and candidate Fire Island house-placement areas, including a proposed `FireIslandResidential` region map
- Hythloth/Fire Temple/road/shoreline/spawn buffers that must remain house-free on Fire Island
- any house-placement regions on Buccaneer's Den island
- all candidate Greater Britain housing district polygons
- road/landmark/dungeon-entry exclusions around those districts
- approximate practical house capacity of each proposed district using representative classic house footprints
- complete ordered set of **all** Greater Britain districts that will ever receive normal-cost placement
- verification that no Cove/Vesper/Yew/Trinsic/other-town normal-cost district definitions exist
- permanent wilderness/landmark/no-housing reserves and the Fire Island special housing exception
- whether staff/event systems create fixed rewards that must opt out of multipliers

For the rotating pool, validate every dungeon as a complete PvP region rather than assuming its entrance region covers all floors/sublevels.

For Fire Island and Buccaneer's Den island, confirm that each configured Hot region covers its intended landmass consistently without accidentally turning broad surrounding ocean routes into PvP unless explicitly desired, and without leaving exploitable safe shoreline strips.

The eventual goal is for a player to understand the world rule from geography:

- **Fire Island/Hythloth = permanently dangerous PvE/PvP cluster**
- **Buccaneer's Den island = permanently dangerous criminal/PvP social cluster**
- **one announced dungeon = temporarily dangerous high-reward cluster**
- **ordinary Britannia = safe from unsolicited blue-on-blue attack, but not from theft/criminal gameplay**

---

## 27. Admin/Developer Tools

Add shard-specific GM commands only where useful for development/testing.

Useful commands may include:

`[ShardRules`

Display current effective shard rules.

`[EraAudit`

Display the configured expansion, active maps and important feature states.

`[TestTemplate <name>`

Configure the invoking test character into one of the predefined PvP templates.

`[ShardDiagnostics`

Report major systems that conflict with the intended era.

`[PvPIntent` / shard-status display

Provide an unmodified-client-compatible player toggle/status path: grey `[Intent]` while voluntary exposure is active, real grey/red override, clear OFF warning about continuing old opponents, current effective notoriety and remaining UTC red time. Do not require modified-client assets, automatically make real criminals blue, or allow a status command to reset combat relationships.

`[PvPStatus` (staff only)

Inspect intent preference, live genuine-crime flag, exact red-expiry timestamp, historical count, processed-death IDs and currently active per-opponent rights/kill-classification snapshots; corrections must be authorized, audited, and cannot extend the same murder twice.

`[HousingDistricts`

Display residential district state, occupancy/capacity metrics, placement pressure and the next eligible expansion district. Provide staff-only subcommands to open the next configured district or explicitly open a named district.

`[NemesisStatus`

Display configured eligible species/spawners and current live Nemeses/caps, spawn conversion statistics, trophy-versus-gold outcomes, original versus regional gold accounting and recent duplicate-event suppression. Provide staff-only test spawn/kill diagnostics without granting production loot or altering natural rarity.

`[WantedStatus`

Show current week, rotating Hot/Cool dungeon IDs, fixed target rosters, natural-spawn origin/contract validity, ModernUO scorer adapter compatibility, duplicate-death suppression, damage-rank/first-living winner diagnostics, pending delivery count, currency minted/spent by tier and curator collection/art validity. Staff-only test kills and corrections must be logged and never produce live rewards or reset production kill IDs.

`[ShipwreckStatus`

Display valid-water/chart generation, completed SOS chest/chart conversion, active site IDs and remaining recoveries, exclusive/public/expiry timestamps, rarity-tier distribution and duplicate/restart rejections. Staff-only inspection and test recovery must not grant production loot.

`[RoleplayGuestbooks`

Staff-only inspection of the four books, active/archive volumes, unique entries, pending/consolidated reports and moderation audits; hide/restore/resolve actions are reason-logged. Book-specific writing disable retains public reading, persistent records and unchanged PvP legality.

`[ExpeditionDestinationVendor`

Display active Expedition week, current route/destination/vendor position, configured collection and rare-pool validity, fixed weekly stock, per-account rare purchase consumption (staff-only), recent purchase rejections and cumulative gold removed. Provide staff-only audited diagnostics for stuck/desynchronized vendor state; routine activation and stocking must be automatic, and forced vendor rebuild cannot refresh stock or purchase allowances within the same week.

`[ExpeditionStatus`

Display the active Expedition Region, trade route, origin/destination, checkpoint definitions, current/next rotation state, resource-yield multiplier, Logistics carry multiplier/area, active Logistics provenance counts where practical, active cargo counts, expired cargo counts and recent reward completions. Provide staff-only force/advance/disable and stuck-cargo recovery operations.

Commands must require appropriate staff access.

Do not expose administrative configuration to normal players.

---

## 28. Logging

At startup, log a concise effective rules summary, for example:

Shard Ruleset: UOR Safe-World / PvP Hot Zones  
Expansion: UOR  
Maps: Felucca  
Safe-World Unsolicited Blue-vs-Blue PvP: Disabled  
Stealing: Enabled except active Cool Dungeon, mapped bank protection or activated Backpack Wards  
Backpack Ward: persistent physical item in backpack, no dormant expiry / 25%-50%-100% additional detection per thief account / consumed on detection / 120s victim-wide post-detection protection  
Loot Protection Ward: invisible permanent character entitlement / first unauthorized non-Hot monster-corpse transfer allowed / 10m per-offender-account restriction on repeat unlawful looting of same rights holder / fixed expiry / public/player/Hot corpses exempt  
Snooping Everywhere: Enabled  
Attack Criminals Everywhere: Enabled  
Attack Murderers Everywhere: Enabled  
PvP Intent: One blue-only voluntary grey `[Intent]` tag; not genuine crime; OFF immediate for new fights, current encounter snapshot/rights retained  
Murder Attribution: Exactly one automatic count per killed ordinary blue, including lawful defense and Hot Zones; no victim report or guild-war waiver  
Murder Red Expiry: Each qualifying kill adds 24 real-time hours to remaining expiry; offline clock continues; historical tally does not maintain red status or count-based stat loss  
Full Loot: Enabled  
Insurance: Disabled  
Pet Bonding: Restricted/Configured  
Dungeon Combat Pets: Disabled  
Pet PvP: Lawful Grey/Red Targets Only  
Faction Pet Combat: Disabled  
Bulk Orders: Enabled  
Skill Cap: 700  
New Character Skill Gain Balls: 20  
Skill Gain Ball Bonus: +25% relative  
Skill Gain Ball Duration: 60 minutes logged-in time  
Skill Gain Ball Transfer: Character-Bound / Blessed  
Hot-Zone Skill Veteran: Enabled / 160.0 skill points earned strictly above 60.0  
Hot-Zone Skill Veteran Exclusions: All player houses and all boats; lifetime high-water anti-retraining  
Hot-Zone Skill Veteran Reward: Optional character title `Forged in Danger`; no power  
Nemesis Monsters: Enabled / 2% of eligible wilderness and dungeon natural spawns; normal spawner cadence  
Nemesis Combat: +50% HP; unchanged damage/skills/abilities; supported-client visual enlargement optional  
Nemesis Rewards: 25% one species trophy OR 75% +200% original pre-region rolled gold (exclusive; ordinary region premium once)  
Wanted Monsters: 2–3 natural target species in each current rotating Hot/Cool dungeon; Hythloth excluded at launch  
Wanted Scoring: Existing ModernUO ranked damage / skip dead contributors / one living winner / no custom 60s recorder  
Wanted Rewards: Hot Marks vs Cool Seals / 1,3,8,15 by difficulty / direct backpack / one stack per death  
Wanted Curator: Britain / separate dungeon-specific cosmetic collections / tier prices 40,120,300,600  
Shipwreck Salvage: 25% bonus chart per completed SOS chest / 4–6 finite recoveries / guaranteed one deco on full completion  
Shipwreck Rights: 30m owner + activation-party, then public until 60m expiry  
Shipwreck Decoration Weights: Uncommon 60%, Scarce 25%, Rare 12%, Extremely Rare 3%  
RP Guestbooks: 4 permanent POI journals / anyone may read / 2 distinct equipped own-issued pieces to write  
RP Guestbook Posting: immediate / 280 characters / one global 10m writer cooldown / automatic archive  
RP Guestbook Reporting: player reports to staff queue / retrospective moderation / no automatic hide or daily cap  
Standard Skill Targets: 1h to 50 / 2.5h to 70 / 4.5h to 80 / 7.5h to 90 / 12.5h to 95  
Mastery Threshold: 95.0  
Mastery Period: rolling 24 hours per skill; login once activates full period  
Mastery Schedule: 4h / 5h / 6h / 8h / 10h36m per +0.1 across 95–96 / 96–97 / 97–98 / 98–99 / 99–100  
Mastery Total: 336 active hours / 14 active days  
Mastery Trigger: 10% per eligible attempt; guaranteed on 10th eligible attempt  
Stat Cap: 225  
House Limit: 1/account  
Housing Placement: Restricted to Approved Districts  
Housing Normal-Cost Districts: Greater Britain Only  
Housing Expansion Target: ~80% practical occupancy  
Housing Spare-Capacity Target: ~20%  
Rural Housing: Enabled  
Rural Housing Cost Multiplier: 2.0x/configured  
Rural Premium Refundable: No  
Rural Housing Share: <runtime percentage>  
Rural Premium Gold Removed: <runtime/lifetime metric if available>  
Open Housing Districts: <runtime list>  
Next Greater Britain Housing District: <name / none; none permanently after final unlock>  
Inactive-House Decay Target: 45 days/configured  
Permanent Hot Dungeon: Hythloth  
Permanent Outdoor Hot Zones: Fire Island; Buccaneer's Den Island  
Rotating Hot Dungeon: <active dungeon / disabled>  
Cool Dungeon: <active dungeon / disabled>  
Hythloth Gold Bonus: +35%  
Hythloth Magic-Item Chance: +25% relative  
Rotating Hot Gold Bonus: +50%  
Rotating Hot Magic-Item Chance: +40% relative  
Cool Dungeon Reward Bonus: +10%  
Cool Dungeon Magic-Item Chance: +10% relative  
Expedition Region: <active region / disabled>  
Expedition Trade Route: Britain -> <destination>  
Expedition Destination Vendor: Active all week in <destination> / town-specific permanent core + 2–3 fixed weekly rare offers  
Destination Vendor Eligibility: Current-week completed delivery by purchasing character / one rare purchase per account per Expedition week / core unlimited  
Destination Vendor Gold Sink: <runtime weekly/lifetime total> / vendor does not buy items  
Expedition Cargo Fast Travel: Disabled  
Expedition Cargo Grace After Rotation: 24h/configured  
Expedition Resource Yield: +50% / 1.50x  
Expedition Resource Respawn: 1.00x / unchanged  
Expedition Logistics Carry Multiplier: 3.0x eligible resources  
Expedition Logistics Area: Britain + active corridor + destination town  
Weekly Pilgrimage: <virtue / shrine>  
Pilgrimage Departure: every 4h / 15m start window  
Pilgrimage Race Winners: first 5 = +20% skill gain / 60m  
Pilgrimage Standard Reward: +10% skill gain / 60m  
Road Travel Foot Bonus: ~15%  
Road Travel Mounted Bonus: ~10%  
Road Travel PvP Suppression: Enabled  
Hot-Zone Spawn Acceleration: Disabled  
Fire Island Housing: Enabled in Approved Residential Regions  
Buccaneer's Den Island Housing: Disabled

Generate these values from actual configuration/runtime rather than hardcoding the log output.

If runtime state contradicts the required ruleset, emit a warning or fail startup for severe conflicts.

Examples:

- UOR configured while AoS insurance is enabled
- safe-world mode active but ordinary blue-vs-blue melee can still begin outside Hot Zones
- Hythloth missing from permanent Hot regions
- more than one rotating Hot Dungeon active at launch
- more than one Cool Dungeon active at launch
- the same dungeon simultaneously marked Hot and Cool
- more than one Expedition Region/primary trade route active at launch
- an Expedition route missing origin/destination/checkpoint definitions
- Expedition resource yield configured above 1.00 while eligible-resource classification is empty/invalid
- Expedition Logistics active without explicit eligible-resource classification
- Expedition Logistics accidentally modifying general backpack capacity or pack-animal capacity
- Pilgrimage virtue resolves to a non-mainland shrine
- overlapping/duplicate Pilgrimage departure-window IDs
- Pilgrimage top-five race slots can be granted non-atomically
- road movement timing conflicts with configured speedhack detection/client movement
- Hot-zone spawn acceleration accidentally enabled
- Nemesis eligibility includes tameables/unique bosses/staff or player-created mobs, invalid trophy-art mapping, impossible area cap or conversion configured to increase spawn pressure
- Wanted contract lists select invalid/unreachable or stale-week species, score adapter only exposes threshold-qualified corpse-right holders instead of all ranked contributors, normal loot rights are overwritten, dead contributors receive tokens, two players get one kill's bounty, token payouts inherit regional multipliers, or pending/curator transactions are not idempotent
- Shipwreck chart generation is wired to an attempt/repeated chest-opening hook, coordinate pool includes un-navigable/shore-reachable sites, visual art produces usable loot, rights/public/expiry timers conflict, rarity weights do not total 100 or unique site/one-time reward IDs cannot persist
- RP guestbook POI count/coordinates disagree with the four existing RP sites, book is movable/blocks paths, server cannot authenticate two distinct equipped own-issued items, journal/cooldown commits are non-atomic, or reports silently auto-hide entries contrary to approved publication rules
- Nemesis HP/stat adjustments or loot configuration inadvertently increase outgoing damage, double regional rewards, or apply consolation gold to trophy drops

---

## 29. Documentation

Create:

`docs/SHARD-RULES.md`

Player-facing rules must clearly explain:

- safe-world default
- stealing except active Cool Dungeon, explicitly mapped bank theft-protection regions and activated Backpack Wards; snooping everywhere
- Backpack Ward: indefinitely eligible physical backpack item, no skill requirement or dormant timer; the first recordable theft activity automatically acquires a previously primed Ward or primes exactly one unprimed carried Ward, with its visible item state and separate unprimed spares; consumed only on detected theft after resolution; each thief account has its own 25%/50%/100% detection progression on ordinarily undetected successes against that Ward/victim, detected failures can trigger it, and 120-second subsequent-theft immunity applies against everyone; no item reversal/stun/Awareness; one free character-bound Starter-Issued Ward is given to each new character, distinct from ordinary purchased/crafted Wards
- Loot Protection Ward: invisible permanent entitlement for all new and migrated existing characters, not a consumable/item; one completed unlawful non-Hot monster-corpse transfer is allowed, then the offender account cannot repeat unauthorized transfers from that victim’s still-rights-protected monster corpses until its ten-minute per-(victim/offender) entry expires without refresh; lawful party/public/player-corpse/Hot-Zone loot unaffected and ordinary crime consequences remain
- one voluntary blue-only `[Intent]` switch: grey `[Intent]` is attackable but NOT a criminal; real grey/red may not switch intent off; OFF protects against new safe-world opponents immediately while existing fights retain rights and recorded murder classification
- real grey/red lawful retaliation is opponent-specific, but a defensive kill of an ordinary blue always earns exactly one automatic murder count
- every murder adds **24 cumulative real-world hours of red status**, including offline; historical counts are records only; killing actual grey/red or intent-exposed opponents gives no murder count
- Hot Zones allow unrestricted initiation but do not waive ordinary-blue murder consequences; valid nonlethal Hot attacks alone are not genuine crimes, and guild-war permission does not waive murder counts
- permanent Fire Island PvP
- permanent Buccaneer's Den island PvP
- permanent Hythloth PvP
- current rotating Hot Dungeon
- full-loot Hot-Zone risk
- new-character Skill Gain Balls: 20 per character, +25% relative gain, 1 hour logged-in time each, blessed and character-bound
- optional `Forged in Danger` title: 160.0 actual skill points earned strictly above 60.0 in eligible Hot Zones, never inside any player house or on a boat; no lowering/retraining credit or power reward
- Nemesis Monsters: rare named endurance variants across eligible wilderness/all dungeons, +50% HP with normal damage, optional subtle visual differentiation, one 25% collectible species trophy OR +200% pre-region gold on non-trophy kills; normal crime/PvP/loot rights still apply and no extra gear tier exists
- Wanted Monsters: current rotating Hot and Cool dungeon each display 2–3 natural species contracts, one living player receives each single token payout by existing ModernUO ranked damage (NOT the rejected rolling-60s model), direct backpack delivery, physical Hot Marks/Cool Seals and Britain's dungeon-specific decorative curator; no new loot/PvP rights or Hythloth contracts at launch
- Shipwreck Salvage: 25% bonus Wreck Chart from a completed ordinary SOS chest; use a real boat at chart sextant coordinates; 30-minute owner/activation-party salvage rights then public until 60-minute expiry; only completed wrecks guarantee one existing-art collectible with 60/25/12/3 rarity distribution; fully lootable/stealable maritime risks remain
- RP POI Guestbooks: anyone may read the four permanent books; writing needs two distinct equipped own-issued costume items, not `[IC]` or a full kit; posts publish immediately with 280-character cap/global 10-minute cooldown; archive volumes are permanent; player reports queue for retrospective staff moderation but never auto-hide; no rewards or PvP immunity
- one-house-per-account rule
- approved housing districts and currently open districts
- rural housing availability and the 2× launch placement cost
- non-refundable nature of the rural placement premium
- protected/no-housing land where the rural premium cannot be used
- why housing is intentionally concentrated
- how/when additional **Greater Britain** districts open and that no normal-cost districts ever open elsewhere
- rural placement as the permanent housing-expansion path after the final Greater Britain district is open
- permanent no-housing regions and permanent special housing regions
- house inactivity/decay policy
- combat carryover across boundaries
- reward premiums
- no combat pets in dungeons
- pet PvP limitations
- unblessed/stealable keys and house re-key behavior

Create:

`docs/UOR-ERA-AUDIT.md`

This should distinguish historical UOR mechanics from deliberate safe-world/Hot-Zone customizations.

Create:

`docs/DEVELOPMENT.md`

Document:

- how to build
- how to launch
- required game data
- configuration files
- test commands
- test account workflow
- backup/save location
- shard-specific code organization
- how to force/advance rotating Hot Dungeon
- how to force/advance Cool Dungeon and resolve Hot/Cool conflicts
- how to force/advance Expedition rotation and recover stuck/corrupted cargo state without duplicating rewards
- how to audit the pinned ModernUO damage-entry/looting-rights ranking, configure and inspect current Wanted contracts, recover pending backpack bounties without duplicates, validate Hot Marks/Cool Seals and dungeon-specific Britain curator stock, and test first-living recipient behavior without changing ordinary corpse rights
- how to configure/survey each destination-town vendor and its unique existing-art collection, validate fixed weekly rare stock, inspect character eligibility and account-limited rare purchases, audit gold removal and recover vendor state without resetting entitlements
- how to inspect effective Hot regions
- how to test region boundaries

Create:

`docs/UPSTREAM-MODERNUO.md`

Track modifications outside shard-specific folders so future ModernUO merges remain manageable.

For every upstream file changed, explain why.

---

## 30. Git Strategy

Before making changes:

1. Confirm working tree state.
2. Record current ModernUO commit/tag.
3. Do not destroy existing user changes.
4. Create logical commits.

Suggested commit sequence:

`chore: establish UOR Felucca-only mechanical baseline`

`docs: add UOR era audit`

`config: add safe-world and hot-zone shard rules`

`fix: correct UOR era discrepancies`

`feat: enforce shard housing and account policies`

`test: add UOR ruleset regression coverage`

Do not put the entire conversion into one giant commit.

---

## 31. Build and Validation

Use the repository's existing build process.

ModernUO currently uses its publish/build tooling rather than ad-hoc compilation.

After each meaningful phase:

- compile
- run relevant automated tests
- launch server
- inspect startup errors/warnings

At the end:

- perform a clean build
- start from a clean test save where appropriate
- connect using the intended UO/ClassicUO client
- complete the PvP/manual test matrix
- test server restart
- verify world persistence
- verify custom serialized entities survive save/reload
- verify no disabled facet is reachable
- inspect logs for errors

Do not declare completion merely because the project compiles.

---

## 32. Implementation Order

Work in this order:

**Phase 1 — Baseline**

Establish clean build and launch.

Record ModernUO version/commit.

Do not customize mechanics yet.

**Phase 2 — Era/map and combat configuration**

Set UOR as the global expansion and Felucca as the only accessible map. Validate real `expansion.json` schema and runtime expansion/map state. Validate and enable `melee.enableInstaHit`; review insurance, veteran skill-cap rewards and bonding flags using actual registered keys. Do not deploy imagined JSON options for specials.

**Phase 3 — Full era audit and minimal combat gates**

Complete the Section 22 cross-era branch audit for the pinned commit before broad customization. Determine what ModernUO already gets right; minimally disable UOR Wrestling Stun/Disarm at request and resolution, remove any confirmed original weapon auto-procs, and run Section 23 swing/precast/special regression tests. Leave all optional numerical buffs off pending comparative tests.

**Phase 4 — Disable later-era content**

Remove access to post-UOR mechanics through configuration, feature flags and era gates.

**Phase 5 — Preserve shared Classic+ mechanics**

Validate the **Section 4 hybrid combat**, baseline build diversity, stats, accelerated skill progression, **new-character Skill Gain Balls**, death/loot, runebooks/travel, keys/property, crafting/BODs, taming restrictions and economy. For housing, audit existing mechanics but defer launch placement geography to the dedicated residential-concentration phase below.

**Phase 6 — Central safe-world hostility, `[Intent]` and automatic murder gate**

Implement/validate the central player-hostility decision path **and the separate Section 14 kill/murder adjudicator**, with an independent stored blue-only intent preference, per-encounter classifications and cumulative red UTC timer. Disable conflicting traditional UOR count/report/status paths before enabling Hot rewards.

Prove:

- ordinary-blue versus ordinary-blue initiation blocked outside Hot Zones; intent-only grey remains attackable without being genuinely criminal
- two intent participants duel without murder; an intent/grey/red who kills an attacking ordinary blue still receives an automatic count and +24 hours, even in lawful self-defense
- Hot initiation remains unrestricted, but an ordinary-blue victim is never exempt from the 24-hour cumulative murder consequence simply because the fight occurred in a Hot Zone
- intent OFF immediately protects against new safe-world encounters without canceling prior opponent rights or retroactively changing murder classification; real criminal/red status prevents turning intent off
- each actual ordinary-blue death awards at most one automatic count; red expiry advances offline and historical count never independently keeps the player red
- stealing/snooping unaffected by the hostility gate itself (separate region/Ward theft validation applies)
- Cool Dungeon independently disables direct player stealing while Cool
- mapped bank theft-protection regions independently disable direct player stealing without creating combat-safe bank bubbles
- Backpack Ward post-resolution detection and 120-second victim protection do not modify ordinary Stealing success or lawful PvP
- Loot Protection permits one real unlawful monster-corpse item transfer, then blocks only that offender account from repeat unlawful looting of the same victim’s still-rights-protected monster corpses for ten minutes outside Hot Zones; it never changes legitimate rights or combat legality
- attacks on `[Intent]` participants and genuine greys/reds work everywhere (pet exceptions remain independent)
- direct-target attacks by a blue against a red/grey create attacker-specific lawful retaliation rights for that red/grey
- multiple blues who directly attack a red/grey each independently become lawful retaliation targets
- AoE/field/splash damage that merely catches a red/grey does not create retaliation rights against the source blue
- the direct-target retaliation rule works identically inside the active Cool Dungeon
- lawful retaliation works
- guild-war initiation exceptions are explicit and do not waive murder counts on ordinary-blue kills unless intent classification also applies

Do this before enabling reward bonuses.

**Phase 6A — Bank theft boundaries and consumable Backpack Wards**

After auditing the actual ModernUO theft/detection/criminal code paths, map each bank's theft-only region; implement start/commit region checks independently of PvP legality. Add the persistent physical Ward item, one-active-at-a-time backpack presence tracking, per-(Ward/victim/thief-account) counters and character-wide 120-second protection; consume the item on triggering detection and hook ordinarily undetected completed successful thefts to that thief account’s own 25%/50%/100% additional victim-detection escalation. Keep ordinary Stealing skill success and snooping unchanged. Execute the Ward/bank regression matrix with multiple thieves, nested inventory, concurrency, guards/Hot-bank behavior, real client inspection and save/restart before shipping the redesign. Do not add Awareness, special Bless/trap spells, stun or a Wardbreaker.

**Phase 6B — Permanent invisible Loot Protection Ward and free starter Backpack Ward**

Audit the pinned ModernUO monster-corpse rights, lawful owner/party permissions, public-rights expiration, criminal flagging, item/stack/loot-all transfer hooks, Hot/Cool origin and source classification, and stable account/character identities. Grant a permanent non-item Loot Protection entitlement to new characters plus an idempotent one-time migration for existing characters. After an actual first unlawful non-Hot monster-corpse item transfer, atomically store ten-minute per-(victim character, offender account) restrictions; block only further unauthorized transfers against that victim's still-protected monster corpses until original UTC expiry, without refreshing on blocked attempts. Keep Hot-Zone/public/player corpses and lawful shared looting unaffected. Grant one Starter-Issued physical Backpack Ward per new character with ordinary effects but starter-only binding/no-economic-extraction rules; show both mechanics in onboarding. Execute the dedicated corpse-looting and starter regression matrices, multiple-account concurrency tests, GM/client walkthroughs, public-rights expiry and Hot-zone tests before enabling.

**Phase 6C — Knocked Out and execution state**

Implement a durable server-authoritative 90-second Knocked Out state for qualifying genuinely blue player zero-health outcomes caused by attributable player damage. Audit zero-health/death hooks, player attribution, targetability, effect cleanup, world placement, house-ban relocation, logout/restart and absolute-UTC expiry. Outside Hot Zones, require the existing target-specific lawful encounter, clear future attack rights on Knock Out, and permit no-skill looting/Execution only through the captured qualifying criminal/red encounter record; Execution of an ordinary blue applies the normal count and cumulative 24-hour red time. Test the state before Hot rewards: no healing/resurrection/damage/monster finish, no ordinary corpse/death consequences, half-health wake-up, protected-item transfer rules, Ward activation, and atomic audit records.

**Phase 7 — Permanent Hot regions**

Implement:

- Hythloth permanent Hot Dungeon
- Fire Island permanent outdoor Hot Zone
- Buccaneer's Den island permanent outdoor Hot Zone
- Fire Island always-open residential district and its protected no-build buffers
- Buccaneer's Den island house-placement prohibition
- entry/exit messaging
- boundary legality
- aggression carryover
- Hot-Zone Knocked Out resolution: any criminal/red may perform no-skill looting without engagement-right limits, any player may Execute, and physical Backpack Wards have no effect on theft or Knocked-Out looting

**Phase 8 — Rotating Hot Dungeon**

Implement weekly selection, announcements, offline-player transition handling and admin override.

Initially use **no reward bonus** until region legality has passed testing.

**Phase 9 — Cool Dungeon of the Week**

Implement the safe weekly convergence rotation:

- exactly one Cool Dungeon
- distinct from Hythloth and current rotating Hot Dungeon
- +10% ordinary scalar rewards/gold
- +10% relative magic-item chance
- no spawn-rate or difficulty changes
- normal safe-world hostility/criminal rules
- direct player stealing disabled while the dungeon is Cool; snooping remains enabled
- login/board/admin visibility

Initially prove selection/conflict behavior before enabling its reward multipliers.

**Phase 10 — Hot/Cool reward premiums**

Add Hythloth, rotating-dungeon, Fire Island and Cool Dungeon reward premiums.

Explicitly keep normal respawn cadence and maximum spawn counts.

**Phase 11 — Concentrated housing districts**

Survey Greater Britain and produce proposed residential district polygons, representative practical-capacity estimates and permanent exclusions.

Implement:

- one house per account
- normal-cost placement in open approved residential districts
- approved rural-wilderness placement with configurable 2× launch cost
- non-refundable rural surcharge accounting
- protected/no-housing land classification that rural payment cannot override
- Greater Britain launch districts
- Greater Britain district soft capacity/occupancy metrics
- one-way Greater Britain-only expansion order with a hard end state
- staff-visible expansion threshold
- permanent no-housing reserves
- Fire Island special residential-placement rules and Buccaneer's Den placement prohibition
- inactive-house qualification/decay policy

Do not define or open normal-cost districts outside Greater Britain. Once the final Greater Britain district is open, all further ordinary mainland placement uses the rural system.

**Phase 12 — Expedition Region and physical trade route**

Implement one weekly outdoor Expedition Region and one Britain-origin physical trade route through it.

Implement:

- exactly one active Expedition Region
- one route origin in Britain and one configured destination town
- broad ordered route checkpoints/waystations
- **+50% approved ordinary resource harvest yield inside the active Expedition Region**
- unchanged resource respawn cadence and rare-tier chances by default
- **Expedition Logistics 3× resource-only carrying capacity** in Britain + active corridor + destination town
- server-authoritative eligible-resource classification and Expedition-harvest provenance/cleanup
- character-bound persistent trade cargo
- Recall/Gate/moongate/teleporter blocking only while trade cargo is carried
- logout/death/restart persistence
- abandon and post-rotation expiration/grace behavior
- unique cargo IDs and atomic one-time turn-in rewards
- login/board/status visibility
- staff force/advance/disable/recovery tooling

Economy-test the +50% gathering bonus, Logistics hauling throughput and trade-route rewards together. Do **not** implement the gathering bonus by accelerating resource respawn.

**Phase 13 — Pilgrimage**

Implement:

- weekly mainland Virtue/shrine rotation
- Britain-only Pilgrim NPC/activity-board start
- 15-minute departure windows every 4 hours
- blessed character-bound Pilgrimage Scroll
- 2–4 broad ordered route checkpoints
- Recall/Gate/moongate/custom-teleport blocking while active
- mounted travel allowed
- once-per-character-per-week successful completion
- abandon/restart in a later window
- server-authoritative per-window finish order
- first 5 finishers = +20% skill gain for 60 minutes
- later finishers = +10% skill gain for 60 minutes
- ready-to-activate logged-in-time Inspiration status
- additive stacking with Skill Gain Balls
- winner announcements and activity-board status
- save/restart/death persistence and anti-duplication

**Phase 14 — Road Travel**

Audit road tiles/regions and movement timing.

Implement:

- approximately +15% on-foot movement on approved roads
- approximately +10% mounted movement on approved roads
- normal baseline movement off road
- use by ordinary travelers, Pilgrims and Expedition cargo carriers
- suppression during active PvP aggression
- suppression inside Hot Zones
- non-stacking movement policy
- speedhack/client-server synchronization validation
- subtle non-spam player status feedback

**Phase 15 — Admin/testing infrastructure**

Diagnostics, Hot-Zone inspection commands, housing-district commands, Expedition commands, Pilgrimage/Road Travel commands and test-character tooling.

**Phase 16 — Regression/manual tests**

Automate critical rules and complete safe/Hot/boundary/Expedition/Pilgrimage/Road Travel matrices.

**Phase 17 — Launch readiness**

Documentation, fresh-world testing, persistence testing, economy simulations and production configuration.

Do not begin cosmetic custom content, custom monsters, custom dungeons or broader progression systems until this baseline is stable. After this gate is met, implement the approved Section 6.1 Nemesis Monsters as a data-driven **variation of existing natural spawns**; audit per-creature visual scaling and use approved name/hue fallback, then prove the exclusive trophy/extra-gold path and regional accounting before enabling in production.

After the same baseline gate, implement approved Section 12.1 Shipwreck Salvage as a **narrow extension of existing SOS/fishing/boat systems**, with art/map audits and atomic persistence/loot/economy tests before production. Do not add chart drops to early fishing attempts or bypass ordinary MiB/SOS treasure generation.

Implement approved Section 20.6A Wanted Monsters after Hot/Cool rotations and ordinary damage/loot rights are stable. Pin and audit the existing ModernUO scoring API, extend it only enough to obtain all ranked contributors, implement deterministic per-kill first-living recipient and one atomic direct-backpack physical payout (with durable same-character overflow reservation). Audit both currency/item/art catalogs and full crash/rotation/economy matrices before enabling production contracts. Do not implement the rejected independent strict rolling-60-second tracker or change ordinary corpse rights.

Implement approved Section 16A.1 RP POI Guestbooks alongside the existing four RP Gear Chests, after authentic issued-gear tracking and the ordinary RP POI placement rules work. Audit supported book/Gump and persistence hooks; prove costume/proximity checks at atomic submission, immediate append-only writes, archive rollover and report-only staff queue without automatic hiding before enabling production writing. Do not add new POIs, roleplay rewards or mandatory preapproval.

---

## 33. Things That Require Owner Approval Before Changing
RP Guestbooks: exactly four fixed RP POI books; open reading; minimum two equipped own-`RoleplayIssued` costume pieces for writing  
RP Guestbook Posts: immediate publish / 280 characters / global 10m writer cooldown / automatic permanent archives  
RP Guestbook Reports: player report queue / retrospective staff decisions / NEVER automatic report-driven hiding  

Do not make arbitrary design decisions about these.

The following are **settled launch rules** and should not be silently weakened:

- global platform expansion UOR, Felucca only; combat override is **T2A-style insta-hit and classic precasting**, no original weapon procs, no Wrestling Stun/Disarm and no AoS abilities
- validated `melee.enableInstaHit = true` and shared swing timer with no equip/target-cycling extra hits; exact precast timer parameters remain a separately documented test/approval decision
- stock pinned-UOR Lumberjacking additive modifier targeting +20 at GM, **no extra GM-only +10** without approval; verify source formula before encoding values
- retain ordinary pre-AoS weapon, poison, mace, shield and archery identities; no new special attacks or automatic extra magic/spell buffs
- preserve fixed 700/100/225 caps; explicitly audit/disable veteran skill-cap rewards, AoS insurance and later itemization
- do not replace the approved loot-rights/damage attribution scorer or safe-world hostility policy when modifying combat

- safe-by-default blue-vs-blue hostility outside Hot Zones
- every newly created character receives 20 blessed, character-bound Skill Gain Balls
- the approved `Forged in Danger` optional title requires 160.0 genuine skill points earned strictly above 60.0 in Hot Zones, never in any player house or aboard a boat; global lifetime skill highs prevent lowering/retraining credit and the unlock grants no combat power
- approved Nemesis Monsters apply to eligible wilderness and all dungeons at 2% natural-spawn conversion with ordinary spawn pressure, +50% HP and unchanged outgoing damage; 25% species trophy OR, exclusively, +200% base gold when no trophy drops; approved stock-client-safe visual differentiation and no new item power tier
- approved Wanted Monsters selects 2–3 natural species in each current rotating Hot/Cool dungeon, excludes Hythloth at launch, awards **one** fixed 1/3/8/15 token stack per death to the first living player in ModernUO's existing ranked damage list (NOT a new 60-second tracker), directly to backpack with nonduplicating same-character overflow reservation; physical Hot Marks/Cool Seals buy separate dungeon-specific cosmetic trophies from Britain at 40/120/300/600, without changing corpse rights, group scaling, regional premiums or combat power
- approved Shipwreck Salvage adds exactly one independent 25% bonus Wreck Chart roll per completed ordinary SOS chest, no displacement of normal SOS loot, a tradable unblessed chart with fixed valid Felucca ocean coordinates and real boat activation, 4–6 finite salvage actions, 30m activation-party exclusivity then public recovery until 60m expiry, and exactly one guaranteed decoration **only on full completion** with rarity weights 60/25/12/3 and no combat/economic extraction bonus
- each Skill Gain Ball provides +25% relative eligible skill gain for 60 minutes of logged-in character time
- pre-95 progression preserves the UOR/T2A-era distinction between easy, standard, hard and very-hard skills rather than using one universal gain curve
- Standard pre-95 focused-training targets are 1h to 50, 2.5h cumulative to 70, 4.5h to 80, 7.5h to 90 and 12.5h to 95
- historically difficult skills retain distinct slower pre-95 curves; temporary gain bonuses modify each skill's own baseline instead of normalizing it
- normal random skill gain stops at 95.0; 95.0–100.0 uses the Mastery system
- Mastery is per skill and multiple 95+ skills accrue concurrently
- each skill uses rolling 24-hour Mastery Periods; logging in once during the period activates the full 24 hours, while a period with no login grants no Mastery Time
- Mastery Time cost per +0.1 is 4h at 95–96, 5h at 96–97, 6h at 97–98, 8h at 98–99 and 10h36m at 99–100
- 95.0→100.0 requires exactly 336 activated Mastery Hours / 14 Active Mastery Days if no periods are missed
- each matured Mastery opportunity has a 10% chance per eligible attempt and is guaranteed on the 10th eligible attempt
- failed attempts do not consume Mastery Time and invalid/blocked uses do not count toward the ten-attempt guarantee
- temporary skill-gain bonuses do not shorten the Mastery calendar; at 95+ they modify only the matured-opportunity trigger chance
- issued starter equipment receives 4 hours of logged-in Starter Protection
- starter-issued gear is Standard/vendor quality and cannot be directly sold, player-vendored, salvaged into economic value or used for BODs
- each new character gets one free character-bound Starter-Issued Backpack Ward (normal consumable effect, no trade/sale/loot/extraction; destroyed unused on death) and an invisible persistent Loot Protection Ward entitlement; existing characters receive the latter through a one-time migration
- mage starter package includes 50 of each classic reagent
- crafting characters receive a meaningful profession-specific starter-material package rather than only a handful of attempts
- starter-material packages are one-time account-level entitlements per profession/category and are not restored by character deletion
- raw starter materials remain bound/non-sellable/non-transferable until consumed
- there is **no Starter-Crafted output state**; legitimate items crafted from starter materials are immediately normal crafted items with full quality rolls and ordinary market/loot/BOD behavior
- Skill Gain Balls cannot stack, transfer or bypass caps/skill locks/anti-macro rules
- stealing enabled except active Cool Dungeon, mapped bank theft-protection regions and activated Backpack Wards; snooping enabled everywhere
- approved Backpack Ward: physical single-use item, no skill prerequisite or dormant expiry while in equipped backpack; item consumed on triggering detection; extra victim detection 25%/50%/100% after successive ordinarily undetected **successful** thefts **per thief account**, with independent progress for other thieves; detected failures can trigger; completed triggering theft stands; 120s subsequent-theft protection from everyone; no Awareness, Bless rewrite, trap/untrap rewrite, stun or Wardbreaker
- approved Loot Protection Ward: permanent invisible character entitlement, first unlawful monster-corpse loot transfer outside Hot Zones allowed with normal crime, then offender-account blocked from that character’s still-rights-protected monster corpses for ten minutes; independent fixed-UTC entries expire without blocked-attempt refresh, rights holders/party/public corpses/Hot-Zone full loot remain otherwise ordinary
- lawful attacks against `[Intent]` participants and genuine greys/reds everywhere; intent is not actual crime
- blue-only intent OFF is immediate for new opponents while live encounter rights and murder protection remain unchanged; real grey/red blocks disabling it
- each qualifying ordinary-blue kill adds exactly one automatic murder count and 24 cumulative real-world red hours even for defense or in Hot Zones; history alone cannot sustain red status
- intent/real-grey/red retaliation outside Hot Zones requires a qualifying direct-target attack from that specific blue; AoE-only damage does not grant retaliation rights, and a defensive kill of that ordinary blue still incurs one count
- Hythloth permanently Hot
- Fire Island permanently Hot
- Buccaneer's Den and its island permanently Hot
- exactly one rotating Hot Dungeon at launch
- exactly one Cool Dungeon at launch
- Hot and Cool dungeon selections must be different
- Cool Dungeon launch bonuses are +10% ordinary rewards and +10% relative magic-item chance
- exactly one outdoor Expedition Region and one Britain-origin primary trade route are active at a time
- Expedition trade cargo must be moved physically; Recall/Gate/moongate/custom instant travel cannot carry it
- Expedition trade cargo is character-bound/non-transferable at launch
- active Expedition Region grants +50% approved ordinary resource harvest quantity at launch
- Expedition resource respawn speed and rare-resource odds remain baseline unless separately approved
- Britain + active Expedition corridor + destination town grant 3× effective carrying capacity for approved resources only
- Expedition Logistics must not triple general inventory capacity or pack-animal capacity
- pre-existing resources cannot be laundered through the Expedition area to gain persistent reduced weight
- trade-route rewards remain separate from Expedition gathering/Logistics benefits
- exactly one mainland Virtue Pilgrimage is active each week
- Pilgrimage starts only in Britain during 15-minute windows every 4 hours
- active Pilgrimage requires physical travel; Recall/Gate/moongates/custom instant travel are blocked while the scroll is active
- Pilgrimage mounts are allowed and routes use broad ordered checkpoints
- each character may successfully complete the weekly Pilgrimage once
- first 5 valid finishers in each departure window earn +20% relative skill gain for 60 minutes; later finishers earn +10% for 60 minutes
- Pilgrimage skill-gain rewards are ready-to-activate, use logged-in time and stack additively with Skill Gain Balls
- approved roads grant approximately +15% movement on foot and +10% mounted
- road movement bonus is disabled during active PvP aggression and inside Hot Zones
- no global Hot-Zone respawn acceleration
- no combat pets in dungeons
- existing pet-PvP restrictions
- Fire Island housing enabled at launch inside approved Fire Island residential regions
- Buccaneer's Den island house placement disabled at launch
- one house per account
- normal-cost house placement concentrated in approved residential districts
- approved rural housing available at a 2.0× effective launch cost
- rural premium is a one-time, non-refundable gold sink
- rural housing remains subject to the one-house-per-account limit and protected-region exclusions
- Greater Britain is the **only** normal-cost mainland residential district family
- once all Greater Britain districts are open, no additional normal-cost districts are ever added; further ordinary mainland placement uses rural housing
- opened districts do not automatically re-close
- housing expansion should preserve roughly 15–25% practical spare placement capacity instead of manufacturing scarcity

Owner approval is required before changing:

- changing starter protection from 4 logged-in hours
- materially changing the starter reagent/resource quantities after launch tuning
- making profession starter-resource grants repeatable rather than once per account/profession
- introducing a Starter-Crafted restriction or otherwise penalizing items legitimately crafted from starter resources
- changing the principle that UOR/T2A easy-vs-hard skill distinctions are preserved
- reclassifying historically difficult skills into an ordinary/easy profile without explicit design approval
- changing the settled Standard pre-95 milestone targets (1h/2.5h/4.5h/7.5h/12.5h cumulative to 50/70/80/90/95) beyond minor calibration necessary to hit those targets
- changing the 95.0 Mastery threshold
- changing the 14-active-day / 336-hour Mastery total
- changing the 4h/5h/6h/8h/10h36m per-0.1 Mastery schedule
- changing the 10% Mastery trigger chance or guaranteed 10th eligible attempt
- allowing temporary skill-gain bonuses to accelerate Mastery Time/calendar accrual
- final Easy/Hard/VeryHard pre-95 calibration scalars after testing
- Power Hour
- stat-gain speed
- reagent availability
- Recall rune restrictions
- changing the approved automatic one-count-per-ordinary-blue-kill rule or **24-hour cumulative real-world red expiry**
- any proposed separate murderer stat-loss penalty (none is added by this system)
- exact Greater Britain launch-district boundaries after in-game survey
- changing the settled rule that normal-cost residential districts exist only in Greater Britain
- exact housing occupancy threshold if live data suggests 80% is inappropriate
- rural housing cost multiplier after launch (2.0× is the settled launch value)
- target rural-housing share if live population-density data suggests 15–25% is inappropriate
- house inactivity/decay duration (45 days is the initial recommendation)
- house placement exceptions outside approved districts, including any expansion of Fire Island residential boundaries
- number of characters/account
- account/IP policy exceptions
- resource respawn speed
- ore/leather/wood resource tiers
- ordinary monster gold multipliers
- Hot-Zone reward percentages
- Fire Island resource bonus
- any future Buccaneer's Den PvE/resource incentive
- rotating Hot Dungeon eligible pool
- Cool Dungeon eligible pool
- weekly Hot/Cool rotation boundary/day
- Expedition Region/route eligible pool and exact weekly route schedule
- trade-route reward amounts and commodity/cosmetic reward tables
- route checkpoint placement after in-game travel audit
- whether Expedition cargo should ever become directly stealable/fenceable in a future criminal-trade system
- changing the settled Expedition resource-yield multiplier from +50% / 1.50×
- changing the settled Expedition Logistics carrying multiplier from 3×
- changing which resource categories qualify for Expedition yield/Logistics benefits
- changing Pilgrimage departure cadence/window from 4 hours / 15 minutes
- changing the first-five Pilgrimage race placement count
- changing standard Pilgrimage +10% or top-five +20% skill-gain rewards
- changing Pilgrimage reward duration from 60 minutes
- changing the approved mainland shrine pool after UOR-map audit
- changing road movement targets from approximately +15% foot / +10% mounted
- allowing road-speed bonus during active PvP aggression or inside Hot Zones
- any future proposal to waive **approved automatic murder counts for ordinary-blue victims in Hot Zones** (currently never waived)
- whether consensual guild wars may occur anywhere or only in Hot Zones
- exact behavior for future Faction combat
- vendor prices
- treasure map rewards
- stealing difficulty
- custom events
- champion-style systems
- holiday rewards
- veteran rewards
- skill/stat starting values
- final restricted pet-bonding enablement and resurrection penalty
- PvM-only dexxer/archery/parry adjustments if metrics show they are needed
- global change to `Expansion.T2A` or replacement of UOR as the platform baseline
- changes to first-hit semantics, precast timeout/recovery, equip delays or the shared swing timer after test baseline approval
- adding any Wrestling/weapon special or additional GM-only Lumberjacking/Anatomy bonus
- enabling poison-healing denial if absent, removing it if stock UOR already has it, adding Poison-spell scaling or simultaneously changing poison damage/cures/healing
- global Archery damage/accuracy/speed buffs rather than independently tested fixes
- material/magic armor AR, durability-tier or crafting-ceiling changes beyond the approved cross-system audit

For each unresolved setting, provide:

**Current ModernUO behavior**

**Historical UOR behavior if known**

**Recommended shard setting**

**Gameplay consequence**

Do not block baseline implementation while waiting for decisions unless the choice makes implementation impossible.

---

## 34. Definition of Done

The initial configuration/customization project is complete when:

The repository builds cleanly.

The server boots cleanly.

UOR is demonstrably the active expansion.

Felucca is the only playable facet.

Lost Lands content appropriate to T2A/UOR is accessible.

Trammel and later facets are inaccessible.

UOR remains the active **platform expansion**, but its stock combat is intentionally overridden by the documented T2A-style insta-hit/precast hybrid.

T2A-style insta-hit is **active** and the shared swing cooldown prevents extra attacks through equipping, cycling, target swaps and relogging. Precast/recovery and weapon auto-unequip behavior meet the approved reference tests.

Every Wrestling Stun/Disarm path and original automatic Crushing/Concussion/Paralyzing path is disabled or demonstrated absent with source audit **and** runtime tests; normal Wrestling remains.

Stock additive Lumberjacking targeting +20 at GM is confirmed; no unapproved GM-only spike or non-axe leakage. Weapon poison, Archery, Parrying and mace pass audited baseline tests, with no implicit blanket buffs.

A complete commit-pinned T2A-versus-UOR branch audit documents selected features, exceptions, source files, unknowns resolved before release and regression coverage; armor/material/durability formulas are reconciled with Section 9 crafting; party/loot rights, travel, housing, BODs, facets, cap rewards and client behavior are audited.

AoS insurance and later itemization do not leak into gameplay.
The approved Artisan Signature feature meets Section 9.1: rare Masterwork/Grandmaster signatures, exact 10× Standard-baseline effective durability where applicable, ordinary repair/full loot and no durability-driven gold-extraction path.
The approved Hot-Zone Skill Veteran feature meets Section 5.1: exactly 160.0 genuine above-60.0 Hot-zone skill points outside all player houses and boats, permanent high-water anti-retraining, persistent cosmetic-only `Forged in Danger` character title.

The approved Nemesis Monsters feature meets Section 6.1: eligible wilderness and all dungeons have 2% replacement spawns without added spawn pressure, +50% HP with no damage increase, visible identity without required client changes, exclusive 25% decorative species trophy or +200% unmultiplied base-gold consolation, ordinary loot/full-loot/regional reward handling, and completed anti-duplication/economy tests.
The approved Wanted Monster feature meets Section 20.6A: each current rotating Hot/Cool dungeon has viable persistent natural-species contracts, existing ranked ModernUO scores select the first living contributor, exactly one fixed physical token payout is directly delivered or reserved for that character, separate Hot/Cool currencies purchase dungeon-specific cosmetic-only trophies, and kill/restart/overflow/redemption exploit tests pass without changing ordinary corpse looting rights.
The approved Shipwreck Salvage feature meets Section 12.1: bonus chart on 25% of completed ordinary SOS chests, a finite physical Felucca-ocean salvage site, 30m exclusive plus 30m public phase, guaranteed one decoration on completed wrecks weighted 60/25/12/3, and chart/site/prize anti-duplication and economy tests.
The approved Roleplay POI Guestbooks feature meets Section 16A.1: four persistent public-readable POI books, genuine two-piece equipped costume check at commit, immediate publishing with 280-character limit and global 10-minute cooldown, automatic archives, player-reported staff queue without auto-hiding, logged hide/restore and no PvP/reward changes.
The approved Backpack Ward and bank theft-protection feature meets Section 4: clearly bounded theft-free bank regions (not combat-safe bubbles), ordinary Stealing and snooping preserved elsewhere, no Awareness or modified Bless/trap spells, indefinite unprimed physical Wards in the backpack with one automatically lazily primed on first recordable theft activity, selected primed item visible and persistent while spares remain unprimed, that item consumed only on triggering detection, 25%/50%/100% after-outcome victim detection tracked independently by thief account on that Ward/victim (detected failures may also trigger), no reversal of triggering theft, and exactly 120 seconds of subsequent-theft protection against every thief; one character-bound free starter Ward is issued with anti-farming restrictions; persistence, concurrency, legality and exploit tests pass.
The approved Loot Protection Ward feature meets Section 4: all characters (including one-time migrated existing characters) possess a permanent invisible nonconsumable entitlement; a first actual unlawful non-Hot monster-corpse item transfer succeeds with normal crime, then ten-minute fixed-expiry offender-account/victim entries block only repeat unauthorized transfers on this victim’s still-protected monster corpses; lawful party rights, public rights expiration, player corpses and Hot-Zone full loot remain unchanged, and concurrency, save/restart, economy and anti-harassment tests pass.

The approved Rare Expedition Destination Vendor feature meets Section 15.12A: the active non-Britain destination has its town-exclusive, all-week merchant; 6–8 existing-art designs per town with stable core and two or three rotating weekly rare offers; purchases require the purchasing character's real current-week cargo completion, unlimited core and one account-wide rare purchase per Expedition week, and atomic gold/allowance/item persistence with zero power or NPC buyback.

Skill/stat caps are correct.

Accelerated pre-95 skill-gain tuning is implemented and measured.

Every enabled launch skill has an explicit documented pre-95 gain-difficulty profile or per-skill override, preserving the intended UOR/T2A relative hierarchy between easy and hard skills.

The Standard profile measures approximately 1 hour to 50, 2.5 cumulative hours to 70, 4.5 to 80, 7.5 to 90 and 12.5 to 95 under the documented focused-training test conditions.

Normal random skill gain cannot raise an enabled skill above 95.0.

Every 95+ skill uses persistent per-skill Mastery state with rolling 24-hour periods; one login activates the whole period, no-login periods award nothing, and multiple skills accrue concurrently.

The Mastery schedule consumes 4h / 5h / 6h / 8h / 10h36m per +0.1 across the five mastery bands and totals exactly 336 Active Mastery Hours / 14 active days from 95.0 to 100.0.

A matured Mastery opportunity succeeds at 10% per otherwise-eligible use and is guaranteed on the 10th eligible attempt; failed attempts do not consume Mastery Time.

Temporary skill-gain bonuses preserve distinct pre-95 difficulty curves and do not shorten Mastery calendar time at 95+.

Every newly created character receives exactly 20 blessed, character-bound Skill Gain Balls.

Each ball provides a 1.25× relative multiplier to otherwise-eligible skill gains for 60 minutes of logged-in character time, with offline pause and save/restart persistence.

Skill Gain Balls cannot stack, transfer, become corpse loot, duplicate through lifecycle events or bypass skill caps, locks, anti-macro rules or normal gain eligibility.

Starter equipment is Standard/vendor quality, protected from ordinary death loss for exactly 4 logged-in hours, and cannot be directly converted into repeatable character-creation economic value.

The once-per-account starter-gold grant cannot be duplicated through character deletion/recreation.

Mage starters receive 50 of each configured classic reagent.

Crafter starter-material packages provide a meaningful introductory supply while remaining finite one-time account-level entitlements per profession.

Unconsumed starter materials cannot be sold/transferred/laundered, but an item legitimately crafted from them becomes an ordinary crafted item immediately: it receives the normal quality roll, has no Starter-Crafted provenance/state and receives full ordinary trade, sale, loot, repair and BOD treatment.

Blessed runebooks work under normal UOR-style requirements.

House, boat and ordinary lock/container keys remain intentionally unblessed; stolen keys create access risk without transferring property ownership, and house-sign re-keying invalidates compromised copies.

Normal-cost mainland housing exists **only** in the phased Greater Britain residential districts; no normal-cost residential districts exist around other towns or regions.

Approved rural wilderness allows housing at the configured 2.0× launch cost, while protected/no-housing land remains unavailable regardless of payment.

The additional rural premium is a non-refundable gold sink; demolition/redeeding returns only the normal underlying house/deed value and rural re-placement charges the premium again.

One house per account is enforced through placement and transfer.

While locked Greater Britain districts remain, the next Greater Britain district becomes eligible when configured occupancy/placement-pressure thresholds are reached; after the final Greater Britain district opens, the sequence ends permanently and further ordinary mainland placement uses rural housing.

Opened housing districts never automatically close around existing residents.

Permanent no-housing reserves protect dungeon approaches, major roads, landmarks and other configured spaces, while Fire Island is an explicit special residential Hot-Zone exception.

Inactive-house turnover works according to the configured account-activity/decay policy.

BODs are enabled only after reward/economy audit.

Pet bonding matches the approved restricted configuration.

Combat-capable controlled pets are excluded from dungeons.

Controlled pets cannot attack innocent/blue players merely because they are in a Hot Zone; they may attack lawful greys/reds/aggressors under the existing pet policy.

Faction status alone never authorizes pet aggression.

Outside Hot Zones, innocent blue players cannot initiate direct harmful actions against innocent blue players.

Stealing remains enabled except in the active Cool Dungeon, mapped bank theft-protection regions or against a victim with activated Backpack Ward protection. Snooping remains enabled everywhere, including those exceptions. Carried physical Wards have no dormant timer and do not alter theft success. On the first recordable theft activity, the server acquires the already-primed eligible Ward if one exists or lazily primes exactly one carried spare; its status is visible, and other carried Wards remain unprimed. The selected item gives 25%/50%/100% additional detection after each **individual thief account’s** first/second/third otherwise undetected successful theft against this Ward/victim; detection consumes only that Ward after the attempt resolves and activates two minutes of victim-wide subsequent-theft protection. Spares do not prime merely when protection ends.

Voluntary grey `[Intent]` and genuinely criminal grey characters can be lawfully attacked by blues anywhere, but only real crime invokes guards/criminal assistance. Both may defend against their specific ordinary-blue attacker; killing that blue always adds a murder count and 24 hours.

Reds/murderers can be attacked by blues anywhere, cannot initiate against unrelated ordinary blues outside Hot Zones and can defend themselves when lawfully attacked; killing an ordinary blue always adds one count and 24 cumulative real-world hours. Red expiry alone controls murderer status, with history retained solely for records.

Genuine criminal/aggression timers survive zone boundaries, and the custom cumulative murder/red timer and encounter classifications follow Sections 3 and 14 across zones.

Hythloth is permanently an unrestricted PvP Hot Dungeon.

Fire Island is permanently an unrestricted outdoor PvP Hot Zone.

Buccaneer's Den and its entire island are permanently unrestricted outdoor PvP Hot Zones.

Fire Island permits player-house placement only within approved `FireIslandResidential` regions, and those houses remain fully inside the permanent PvP Hot Zone.

Buccaneer's Den island rejects player-house placement.

Exactly one eligible non-Hythloth dungeon rotates into unrestricted PvP each week.

Exactly one separate eligible dungeon is the Cool Dungeon of the Week under normal safe-world PvP rules.

The Cool Dungeon and rotating Hot Dungeon are never the same dungeon.

While a dungeon is Cool, direct player stealing through the Stealing skill is disabled; snooping remains enabled, ordinary corpse rights/criminality stay intact subject solely to the per-offender Loot Protection Ward restriction on repeated unauthorized monster-corpse transfers, and existing grey/red/aggression consequences continue normally.

The Cool Dungeon receives +10% ordinary scalar rewards/gold and +10% relative magic-item generation chance, with no monster difficulty, spawn-count or respawn-speed increase.

Exactly one outdoor Expedition Region and one Britain-origin physical trade route are active at a time.

Trade cargo requires physical traversal through configured broad ordered checkpoints and cannot be transported by Recall, Gate, public moongate or custom instant-travel systems.

Ordinary non-cargo travel remains unchanged.

Trade cargo/progress survives lifecycle events without duplication, cannot be transferred/banked/secured/pet-carried, and can reward only once through an atomic server-authoritative turn-in.

The active Expedition Region grants +50% quantity yield for explicitly approved ordinary gathering resources while leaving node respawn cadence and rare-resource odds at baseline unless separately configured.

Britain, the active Expedition corridor and the configured destination town grant 3× effective carrying capacity for explicitly approved raw resources only; general inventory and pack-animal capacity remain normal.

Expedition-harvest provenance prevents pre-existing-resource laundering, survives save/restart correctly, and is cleared/transformed by banking, storage, trade, dropping, sale, pet transfer and configured refinement/conversion paths without duplicating quantity or reduced-weight state.

Trade-route rewards remain separately economy-tested from the gathering and Logistics benefits.

A weekly mainland Virtue Pilgrimage starts only from Britain during server-authoritative 15-minute departure windows every 4 hours.

Pilgrimage Scrolls are blessed, character-bound and persistent; fast travel is blocked while active, mounts are allowed, and 2–4 broad ordered checkpoints enforce meaningful physical traversal.

Each character can successfully complete the weekly Pilgrimage once; abandonment allows a later departure-window restart until completion.

The first five valid finishers per departure window atomically receive a ready-to-activate +20% relative skill-gain reward for 60 minutes of logged-in time, while later valid finishers receive +10% for 60 minutes.

Pilgrimage skill-gain rewards obey caps/locks/anti-macro eligibility and stack additively with the +25% Skill Gain Ball.

Approved roads provide approximately +15% on-foot and +10% mounted movement-speed benefit using stable server/client timing.

Road speed returns to baseline off-road, is disabled during active PvP aggression and inside Hot Zones, and does not create speedhack false positives or client/server movement desynchronization.

Players receive clear entry/exit and login information for Hot Zones, including that initiation is unrestricted but killing an ordinary blue still adds one automatic murder count and 24 cumulative hours.

A player cannot attack in a Hot Zone and gain instant immunity by crossing the boundary; existing legal aggression carries through normally.

Players cannot exploit the boundary to shoot protected innocents across it.

Offline characters are not silently trapped by a safe-to-Hot weekly dungeon transition.

Safe-world PvE remains at normal 100% baseline reward.

Hythloth, rotating Hot Dungeon and Fire Island apply only their configured risk premiums; Buccaneer's Den remains at normal baseline economic rewards unless a separate incentive is explicitly enabled.

Hot rewards cannot be generated by dragging monsters/resources across region boundaries.

Hot or Cool status does **not** accelerate ordinary monster respawn or increase maximum simultaneous spawn pressure.

Full-loot death works where applicable and player corpse loot is never multiplied by Hot bonuses.

Housing/account policies are enforced.

Core rules have regression coverage, including all Section 23 intent/ordinary-blue murder classification, real criminal override, Hot-Zone/self-defense, UTC expiry and double-death-callback cases.

World saves and reloads correctly.

Player-facing shard rules are documented.

All deliberate deviations from stock/historical UOR, especially the intentional **T2A-style hybrid combat**, are explicitly documented, source-audited and covered by tests.

---

## 35. First Agent Task

Begin by **auditing, not rewriting**.

Produce an initial report containing:

1. Current ModernUO git commit/tag.
2. Current build status.
3. Current `expansion.json` state.
4. Current enabled maps.
5. Current relevant feature flags.
6. Whether a world/save already exists.
7. Current character-creation/starting-item hooks suitable for granting character-bound Skill Gain Balls exactly once.
8. Current character-creation equipment/package hooks suitable for archetype-based Standard starter gear, 4-hour logged-in protection and persistent `StarterIssued` restrictions.
9. Current account-persistence hooks suitable for a once-per-account starter-gold entitlement and once-per-account-per-profession starter-material entitlements that survive character deletion.
10. Current item-stack/resource-consumption hooks suitable for bound starter raw materials that cannot be laundered by merging but create completely normal output when legitimately consumed by crafting.
11. Current skill-gain calculation hooks suitable for applying a temporary 1.25× relative multiplier without bypassing caps, locks or anti-macro rules.
12. Enumerate UOR/T2A/AoS era branches and all combat-special paths against the pinned commit (including cumulative `Core.T2A` checks); report verified behavior, unverified absence, chosen override, code-change layer and per-branch regression tests. Specifically locate actual insta-hit/equip/target timer, precast/recovery, `Fists` Stun/Disarm activation and hit resolution, all original automatic weapon procs and later AoS abilities, Lumberjacking formula, poison/healing, Archery, Parrying, armor/material/durability, veteran skill-cap rewards, party/corpse scorer, BODs/travel/housing/loot/client flags.
13. Exact ModernUO hooks used to decide whether one player may harm another, plus separate murderer/reporting/status/count/expiry, per-pair aggression snapshot, player-kill attribution and client intent-tag hooks; identify which legacy short/long decay, reports and stat-loss dependencies must be replaced or isolated for Sections 3/14.
14. Exact code paths for stealing/criminal/notoriety/aggression relationships; normal victim/bystander detection, nested backpack targets, theft validation/commit concurrency, Ward persistence/UI and bank-region boundaries; additionally monster-corpse rights ownership/public expiry, criminal item-transfer/loot-all commit, Hot source classification, per-offender persistence and universal entitlement migration hooks.
15. Region definitions for Hythloth, Fire Island and Buccaneer's Den island/town.
16. Candidate region definitions for the rotating Hot Dungeon pool and Cool Dungeon pool, including conflict/overlap handling.
17. House-placement behavior on Fire Island and Buccaneer's Den island.
18. A proposed Fire Island residential-region overlay that preserves Hythloth/Fire Temple approaches, roads, shoreline access, outdoor PvP space and major spawns.
19. Current generic house-placement/payment/refund hooks and the cleanest shard-specific point to classify placement as residential, rural or protected while supporting an always-open Fire Island exception.
20. A rural-housing implementation proposal showing how to charge a non-refundable surcharge without duplicating every house deed unless necessary.
21. An in-game survey proposal for the complete ordered set of Greater Britain residential districts, including roads, landmarks, dungeon-entry buffers and representative practical capacity.
22. Verification that no normal-cost residential district definitions are proposed for Cove, Vesper, Yew, Trinsic or any other non-Britain region.
23. Travel/shoreline transition points for both permanent PvP islands.
24. Loot-generation hooks suitable for region-specific risk multipliers.
25. Current spawn/respawn code so Hot rewards can be implemented **without** respawn acceleration.
26. Current Recall/Gate/public-moongate/custom-teleporter hooks that can prevent instant travel only for characters carrying Expedition cargo.
27. Candidate Expedition Region corridors and Britain-origin trade routes using existing roads, bridges, crossroads, inns and secondary towns.
28. Current mining/lumberjacking/skinning/fishing/other approved harvesting hooks suitable for a region-owned 1.50× yield multiplier without changing respawn cadence.
29. Current item-weight, stack split/merge, bank/storage/trade/drop/refine and pack-animal hooks suitable for a 3× resource-only Logistics system with server-authoritative provenance.
30. Current item/container serialization hooks suitable for persistent character-bound cargo that cannot be banked/traded/secured/pet-carried or duplicated.
31. Exact mainland-continent virtue shrine locations/regions available on the UOR Felucca map and proposed Britain-to-shrine checkpoint corridors.
32. Current item/state hooks suitable for a blessed character-bound persistent Pilgrimage Scroll and once-per-character weekly completion state.
33. Current travel hooks required to block Recall/Gate/moongate/custom teleport while Pilgrimage is active without affecting ordinary travel.
34. Current skill-gain modifier infrastructure suitable for ready-to-activate +10%/+20% temporary Pilgrimage Inspiration that stacks additively with Skill Gain Balls.
35. Current skill-gain entry points needed to hard-stop ordinary gains at 95.0 and route 95+ gains through a per-skill Mastery service.
36. Current character/account persistence and server-time facilities suitable for rolling 24-hour per-skill Mastery Periods, Active-period flags, Mastery Time banks and attempt counters.
37. Current gain-eligibility checks suitable for ensuring only otherwise-valid skill uses count toward the Mastery 10% roll / guaranteed 10th eligible attempt.
38. Current ModernUO/UOContent skill-gain logic and any UOR/T2A-era per-skill distinctions needed to classify all enabled launch skills into Easy / Standard / Hard / VeryHard or explicit override profiles.
39. Representative historical/current milestone-time baselines for easy versus difficult skills so shard acceleration can preserve relative difficulty rather than flatten it.
40. Current movement-delay, road-tile/land-tile detection, mounted-state and speedhack-detection hooks suitable for server-authoritative road-speed bonuses.
41. Proposed changes separated into configuration, shard-specific code and upstream-code changes.
42. Nemesis natural-spawn conversion/death-reward hooks, per-species whitelist and cap strategy, HP-only modification safety, stock-client per-mobile scaling feasibility with name/hue fallback, existing trophy art and an additive pre-region gold calculation that avoids double region premiums.
43. Existing four RP POI book placement, compatible paged book/Gump and append-only journal persistence; server-side owner-bound `RoleplayIssued` equipment/proximity validation on submit, global cooldown atomicity, archive rollover, player-report deduplication and audited retrospective moderation.
44. Proposed bank theft-only region polygons (including any bank inside Hot Buccaneer's Den), exact start/commit theft-validity hooks and Ward item/snooping/persistence integration with existing theft detection and ordinary criminal consequences.
Then implement the obvious low-risk baseline configuration:

**UOR platform + Felucca-only + later-era features disabled + verified T2A-style insta-hit; gated-off Wrestling/weapon specials; no optional numeric buffs before testing.**
After that, implement safe-world hostility **and the independent intent/murder adjudicator without reward bonuses**; prove the full Section 23 permission-and-death matrix, cumulative UTC timer, intent-off encounters and genuine crime separation before enabling permanent/rotating Hot Zones and the Cool Dungeon rotation. Add Hot/Cool reward multipliers only after region selection and overlap behavior are proven. Implement the Expedition Region/trade-route traversal and persistence rules before tuning route rewards. Implement Pilgrimage state/race authority before its skill-gain rewards, and validate road movement timing/speedhack compatibility before enabling the road bonus in production.

When uncertain whether behavior is historically UOR, inspect ModernUO's implementation and reliable era documentation rather than silently guessing.

Do not replace working ModernUO era-aware systems with custom code solely for stylistic reasons.

The objective is a maintainable **UOR-based safe-world shard with concentrated optional full-loot PvP**, not an unnecessary rewrite of ModernUO.
