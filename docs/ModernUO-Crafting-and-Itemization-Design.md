# ModernUO Classic+ Crafting and Itemization Design

**Status:** Working design document for iteration. Numeric tuning remains provisional until implementation audit/playtesting.
**Milestone:** Beta 2d — Crafting and itemization. See the
[phased roadmap](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md#beta-2--horizontal-endgame-and-world-content-extensions).
**Relationship to main shard plan:** Standalone subsystem design, referenced (not redefined) by the
[alternative plan](ModernUO-UOR-Safe-World-Hot-Zones-Alternative-Plan.md), whose Section 9.1 (Artisan
Signature Collections) already treats this document as authoritative for grade unlocks, probabilities,
raw-power ceilings, maker marks, and ordinary repair/degradation.
**Primary shard:** UOR / Safe-World + Hot-Zones Classic+ design

---

## 1. Purpose

This system is intended to make player crafting economically and mechanically relevant from the beginning of a character's career through Grandmaster endgame without replacing classic UOR loot, creating an AoS-style property treadmill, or requiring permanent vertical progression beyond the shard's normal 100-skill / 700-total ceiling.

The core itemization rule is:

> **Craftsmanship provides a balanced combination of modest raw power, reliability, efficiency and longevity. Magic items emphasize raw power.**

A player-crafted weapon or armor piece should be capable of being clearly better than a vendor equivalent even when made by a developing crafter.

A highly accomplished crafter should be capable of producing rare and prestigious equipment that remains desirable at endgame.

However:

> **The best possible player-crafted weapon or armor must remain weaker in raw damage/protection than the top two equivalent magic-item tiers.**

This preserves two healthy endgame loops:

- crafters remain permanently relevant;
- high-end monster loot remains exciting.

The design should produce **sidegrades and overlapping power bands**, not a single universal ladder where one source invalidates every other source.

---

## 2. Itemization Identity

### 2.1 Three sources, three roles

#### Vendor equipment

NPC vendors establish the baseline.

Vendor items:

- have normal base damage/protection;
- have normal durability;
- have normal weight/handling;
- carry no craftsmanship-grade bonuses;
- should remain adequate for a new player.

Vendor inventory should not randomly generate the player-crafted craftsmanship grades.

#### Player-crafted equipment

Player-crafted items can receive a **Craftsmanship Grade**.

Craftsmanship may improve:

- raw weapon damage;
- raw armor protection;
- durability;
- weapon handling / hit reliability;
- armor weight / encumbrance;
- shield reliability;
- casting reliability on crafted magical implements;
- tool performance;
- other item-family-specific utility.

Crafted gear therefore has **real combat power**, not merely decorative value.

But its raw-power ceiling is deliberately constrained.

#### Magic loot

Magic weapons and armor primarily increase **raw power**:

- magic weapons increase damage;
- magic armor increases protection.

Under this design, ordinary magic weapon tiers do **not** also receive an Accuracy ladder.

This distinction is intentional:

> **Crafted weapon = some extra damage + better handling/consistency.**
> **Magic weapon = greater raw damage.**

And:

> **Crafted armor = some extra protection + better durability/weight/handling.**
> **Magic armor = greater raw protection.**

This creates meaningful equipment choices instead of one-dimensional best-in-slot progression.

---

## 3. Hard Raw-Power Ceiling

Crafted weapons and armor must gain raw power, but crafting must not invalidate the highest magic loot.

### 3.1 Weapon ceiling

Use the classic conceptual magic weapon ladder:

1. Ruin
2. Might
3. Force
4. Power
5. Vanquishing

The intended relationship is:

`Vendor < common crafted grades < high crafted grades ≈ lower/mid magic tiers < Power < Vanquishing`

The **best crafted weapon's raw damage bonus must remain below Power and Vanquishing**.

A good initial balancing target is for the highest crafted grade to land around the **Force-equivalent raw-damage band**, with its craftsmanship utility differentiating it from a Force weapon.

Illustrative normalized tuning:

| Source / Grade | Raw weapon damage target |
|---|---:|
| Vendor / normal | 100% |
| Well-Made crafted | 102% |
| Fine crafted | 104% |
| Excellent crafted | 106% |
| Superior crafted | 108% |
| Exceptional crafted | 110% |
| Masterwork crafted | 111% |
| Grandmaster crafted | 112% |
| Ruin magic | ~104% |
| Might magic | ~108% |
| Force magic | ~112% |
| Power magic | ~116% |
| Vanquishing magic | ~120% |

These percentages are **design-normalization targets**, not final engine constants.

During implementation, map them to the cleanest UOR-compatible integer damage modifiers available in ModernUO.

### 3.2 Armor ceiling

Use the classic conceptual magic armor ladder:

1. Defense
2. Guarding
3. Hardening
4. Fortification
5. Invulnerability

Intended relationship:

`Vendor < common crafted grades < high crafted grades ≈ lower/mid magic tiers < Fortification < Invulnerability`

The **best crafted armor's raw protection must remain below Fortification and Invulnerability**.

Illustrative normalized tuning:

| Source / Grade | Raw armor protection target |
|---|---:|
| Vendor / normal | 100% |
| Well-Made crafted | 102% |
| Fine crafted | 104% |
| Excellent crafted | 106% |
| Superior crafted | 108% |
| Exceptional crafted | 110% |
| Masterwork crafted | 111% |
| Grandmaster crafted | 112% |
| Defense magic | ~104% |
| Guarding magic | ~108% |
| Hardening magic | ~112% |
| Fortification magic | ~116% |
| Invulnerability magic | ~120% |

Again, exact integer AR values should be resolved through an implementation audit rather than blindly using percentages.

### 3.3 Craft-material stacking

Any crafting-derived raw-power bonus from:

- craftsmanship grade;
- colored ore;
- special lumber;
- leather tiers;
- other future craft materials;

must count toward the **crafted raw-power ceiling**.

A material bonus must not allow a Grandmaster crafted item to exceed the intended cap and quietly become stronger in raw power than Power/Fortification.

Utility bonuses may still distinguish crafted gear beyond that cap.

---

## 4. Craftsmanship Grades

### 4.1 Core principle

A successful craft makes a second server-authoritative **Craftsmanship Quality Roll**.

Crafting skill determines:

1. which grades are unlocked;
2. the probability of producing each unlocked grade.

The system should use the shard's existing UO skill-title thresholds where practical rather than creating a second invisible progression system.

Exact title-to-skill boundaries should be read from the current ModernUO/UOContent implementation during engineering audit.

### 4.2 A new crafter can matter immediately

A character does **not** need Apprentice, Journeyman or Grandmaster skill before creating something better than a vendor item.

From the moment a character can successfully create an item, there should be a meaningful **10% chance** to produce the first superior grade.

That is a settled design goal:

> **A new smith's first successful sword can, on a meaningful minority of crafts, be materially better than the sword sold by the NPC blacksmith.**

This makes crafting economically meaningful during progression instead of being a skill that only "turns on" at 100.0.

### 4.3 Proposed grade ladder

Recommended launch structure:

| Craftsmanship Grade | Unlock concept | Identity |
|---|---|---|
| Standard | Any successful craft | Normal player-crafted baseline |
| Well-Made | Available immediately | First chance to exceed vendor quality |
| Fine | Apprentice-level milestone | Noticeably better workmanship |
| Excellent | Journeyman-level milestone | Reliable mid-tier crafted gear |
| Superior | Expert/Adept-level milestone | High-quality professional work |
| Exceptional | Higher professional milestone | Classic exceptional-quality band |
| Masterwork | Master-level milestone | Rare endgame craftsmanship |
| Grandmaster | Grandmaster only | Rare signature-quality output |

Not every UO skill-title band needs its own item grade.

Title bands that do not unlock a new grade should still shift the output distribution upward toward the better grades the crafter has already unlocked.

### 4.4 Suggested initial quality probabilities

These are balancing starting points, not final values.

The quality system should use a **skill-band-weighted final output distribution**. As crafting skill rises, probability mass moves out of lower grades and into higher grades. This is important: Grandmaster should not merely add a tiny chance for better items while continuing to produce mostly low-quality goods.

Approximate final-grade targets after a successful craft:

| Crafter stage | Standard | Well-Made | Fine | Excellent | Superior | Exceptional | Masterwork | Grandmaster |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Beginning crafter | 90% | 10% | — | — | — | — | — | — |
| Apprentice | 70% | 20% | 10% | — | — | — | — | — |
| Journeyman | 45% | 25% | 20% | 10% | — | — | — | — |
| Expert / Adept | — | 25% | 30% | 30% | 15% | — | — | — |
| Higher professional | — | — | 20% | 30% | 30% | 20% | — | — |
| Master | — | — | — | 15% | 30% | 35% | 20% | — |
| Grandmaster | — | — | — | — | **20%** | **35%** | **35%** | **10%** |

The intended early progression is also explicit: a beginning crafter produces better-than-Standard quality on **10%** of successful crafts, rising to **30%** by Apprentice. At Apprentice, that 30% is split between Well-Made and Fine output rather than adding more than three active qualities.

### Four-quality active-window rule

At **any crafting skill level**, a crafter may produce no more than **four distinct craftsmanship qualities** for a given item family. This is a player-inventory and market-readability rule, not just a balancing preference.

As skill advances, the active quality window moves upward:

- Beginning: Standard / Well-Made;
- Apprentice: Standard / Well-Made / Fine;
- Journeyman: Standard / Well-Made / Fine / Excellent;
- Expert / Adept: Well-Made / Fine / Excellent / Superior;
- Higher professional: Fine / Excellent / Superior / Exceptional;
- Master: Excellent / Superior / Exceptional / Masterwork;
- Grandmaster: Superior / Exceptional / Masterwork / Grandmaster.

When a new upper grade enters a full four-quality window, the lowest grade in that window becomes unavailable. A crafter therefore does not accumulate an ever-growing list of possible quality variants as skill increases.

At Grandmaster, the odds have deliberately **flipped toward high-quality production**:

- **100%** of successful crafts are Superior or better;
- **80%** are Exceptional or better;
- **45%** are Masterwork or Grandmaster;
- Grandmaster-grade output remains a meaningful minority result at **10%**;
- Superior is now the GM's lowest possible result rather than Standard-quality filler.

This progression should feel materially different at each stage. A developing crafter mostly produces ordinary goods with occasional quality spikes; a Grandmaster produces only upper-tier craftsmanship, but still has meaningful variation between professional, prestige and signature-quality results.

Implementation may use a weighted one-roll selection or mathematically equivalent conditional rolls, but the **final observed output distribution** should match the configured targets rather than simply increasing every grade's independent chance. The implementation must also enforce the **maximum-four active quality outcomes** for every skill band.

Goals:

- superior crafted goods appear regularly enough to sustain a market;
- advancing skill progressively suppresses low-grade output and retires the lowest grades as the four-quality window moves upward;
- high-end crafters reliably produce high-quality goods;
- true Grandmaster-grade pieces remain memorable rather than deterministic;
- progressing skill improves output continuously before reaching GM.

All values must be configurable by skill band and grade.

### 4.5 Maker's mark

Higher craftsmanship should reinforce crafter identity.

Recommended:

- allow maker's mark using classic behavior;
- Masterwork and Grandmaster items should prominently retain the maker's identity;
- preserve maker attribution through repair;
- do not allow relabeling another crafter's item.

A famous crafter's output should be recognizable in the economy.

---

## 5. Crafted Weapons

Crafted weapons receive **both**:

1. a modest raw-damage bonus;
2. a craftsmanship/handling bonus.

### 5.1 Raw damage

Use the craftsmanship-grade raw-power table in Section 3.

Grandmaster crafted damage should target roughly the Force-equivalent band and remain lower than Power and Vanquishing.

### 5.2 Handling / hit reliability

Crafted weapons should also represent balance, edge alignment and fit.

Recommended initial handling bonus:

| Grade | Effective weapon-skill bonus for hit calculation only |
|---|---:|
| Standard | +0 |
| Well-Made | +1 |
| Fine | +2 |
| Excellent | +3 |
| Superior | +4 |
| Exceptional | +5 |
| Masterwork | +5 |
| Grandmaster | +6 |

This does **not** actually grant Swordsmanship, Fencing, Macing or Archery skill.

It affects only the attack-success calculation.

It must not:

- contribute to the 700 skill cap;
- unlock abilities;
- satisfy skill checks unrelated to hitting;
- change skill title;
- improve special systems based on actual skill.

### 5.3 Durability

Craftsmanship should also improve longevity.

Illustrative durability targets:

| Grade | Durability modifier |
|---|---:|
| Standard | baseline |
| Well-Made | +10% |
| Fine | +20% |
| Excellent | +30% |
| Superior | +40% |
| Exceptional | +50% |
| Masterwork | +60% |
| Grandmaster | +75% |

Exact values require economy testing.

### 5.4 Magic weapon distinction

Normal magic weapon tiers increase raw damage and should not simultaneously carry the crafted handling bonus.

Therefore:

- a Power sword hits substantially harder;
- a Grandmaster crafted sword is somewhat weaker in raw damage but more accurate/reliable and more durable.

A player can rationally prefer either depending on build, opponent and replacement cost.

This is intentional horizontal itemization.

---

## 6. Crafted Armor

Crafted armor receives:

1. modest raw protection;
2. durability;
3. reduced weight / encumbrance;
4. optionally reduced era-appropriate dexterity or movement penalties where such penalties exist.

### 6.1 Raw protection

Use the Section 3 protection bands.

Grandmaster crafted armor should target roughly the Hardening-equivalent raw-protection band and remain weaker in raw protection than Fortification and Invulnerability.

### 6.2 Durability

Illustrative:

| Grade | Durability modifier |
|---|---:|
| Standard | baseline |
| Well-Made | +10% |
| Fine | +20% |
| Excellent | +30% |
| Superior | +40% |
| Exceptional | +50% |
| Masterwork | +60% |
| Grandmaster | +75% |

### 6.3 Weight / encumbrance

Illustrative resource-independent weight reduction:

| Grade | Weight reduction |
|---|---:|
| Standard | 0% |
| Well-Made | 5% |
| Fine | 8% |
| Excellent | 12% |
| Superior | 16% |
| Exceptional | 20% |
| Masterwork | 22% |
| Grandmaster | 25% |

Do not allow rounding to produce zero-weight armor pieces.

### 6.4 Armor tradeoff

The target comparison is:

**Grandmaster crafted armor**

- meaningful protection increase;
- excellent durability;
- lower weight;
- better handling;

versus:

**Fortification / Invulnerability armor**

- clearly stronger raw protection;
- ordinary handling characteristics.

Neither source should universally invalidate the other.

---

## 7. Shields

Shields should follow the armor philosophy.

Craftsmanship may improve:

- raw defensive value within the crafted protection ceiling;
- durability;
- shield/parry reliability where technically compatible with UOR mechanics;
- weight.

Do not invent an AoS-style block-property system.

Any parry reliability effect should be expressed through the smallest era-compatible modifier and must be tested for PvP impact.

---

## 8. Tinker-Made Crafting Tools

Tinkering becomes a support profession for the entire crafting economy.

### 8.1 Vendor tools

NPC-sold tools are the baseline:

- normal uses;
- no effective crafting-skill bonus;
- no craftsmanship-quality-roll bonus.

### 8.2 Player-made tools

A player-made crafting tool should be materially better than its vendor equivalent even at Standard quality.

Benefits may include:

- more uses;
- a modest effective crafting-skill bonus;
- a relative bonus to craftsmanship-quality rolls.

Recommended initial table:

| Tool grade | Effective craft-skill bonus | Relative quality-roll bonus | Uses |
|---|---:|---:|---:|
| Vendor | +0 | +0% | 100% |
| Standard player-made | +1 | +5% | 110% |
| Well-Made | +1 | +8% | 120% |
| Fine | +2 | +12% | 125% |
| Excellent | +3 | +16% | 130% |
| Superior | +4 | +20% | 140% |
| Exceptional | +4 | +22% | 145% |
| Masterwork | +5 | +25% | 150% |
| Grandmaster | +5 | +30% | 160% |

"Relative quality-roll bonus" is multiplicative to the probability, not percentage points.

Example:

- Masterwork chance = 1.0%;
- Grandmaster tool quality bonus = +30% relative;
- adjusted chance = 1.3%, **not 31%**.

### 8.3 What effective tool skill may do

Tool skill may improve:

- ordinary success chance;
- failure rate;
- perhaps material-loss efficiency if later approved.

It must **not**:

- unlock a craftsmanship grade the character has not personally unlocked;
- unlock a recipe;
- raise the character's title;
- satisfy a hard skill prerequisite;
- count toward the 700 skill cap.

### 8.4 Prevent recursive tool breeding

A high-quality tinker tool must not create an uncontrolled feedback loop where successive generations of tools become easier and easier to make at top quality.

Recommended launch rule:

> **Crafting-tool quality bonuses do not apply to the craftsmanship-grade roll when the output itself is another crafting tool.**

The tool may still improve the ordinary success chance.

Alternative caps may be evaluated later, but recursive quality amplification should not ship.

---

## 9. Inscription — Crafted Scrolls

Scroll quality is a major functional crafted-item path.

### 9.1 Core effect

Higher-quality scrolls reduce fizzle probability by adding **percentage points to spell success chance**.

Illustrative values:

| Scroll grade | Spell-success bonus |
|---|---:|
| Standard | +0 pp |
| Well-Made | +3 pp |
| Fine | +5 pp |
| Excellent | +8 pp |
| Superior | +11 pp |
| Exceptional | +14 pp |
| Masterwork | +17 pp |
| Grandmaster | **+20 pp** |

Example:

`35% normal scroll success + 20 pp Grandmaster quality = 55%`

### 9.2 Zero-Magery use

The system should support the intended fantasy that a very high-quality scroll can allow an unskilled or poorly skilled caster to successfully perform magic that would otherwise be unreliable.

A character with 0 Magery using a Grandmaster-quality scroll can receive up to the full **+20 percentage-point success bonus**.

However, do not let this trivialize the Magery skill by making every high-circle spell universally castable at 20% from 0 skill.

Recommended rule:

- quality modifies the normal scroll-casting success formula;
- low and appropriate middle-circle spells may become castable from extremely low skill;
- explicit hard-minimum restrictions may remain for the most consequential high-circle spells if current UOR mechanics require them;
- Gate Travel, Resurrection and other high-impact utility should be specifically audited before allowing a 0-skill character to reach nonzero success.

This preserves the intended benefit without turning Grandmaster scrolls into a substitute for an entire mage template.

### 9.3 Scope

Scroll craftsmanship changes **casting reliability only**.

It does not change:

- spell damage;
- healing amount;
- spell duration;
- Resist difficulty;
- casting speed;
- mana cost;
- spell circle;
- interrupt rules.

Consumability justifies scrolls having a larger reliability bonus than permanent spellbooks.

---

## 10. Inscription — Crafted Spellbooks

Crafted spellbooks provide a smaller persistent reliability benefit.

### 10.1 Proposed effects

Illustrative:

| Spellbook grade | Spell-success bonus |
|---|---:|
| Standard | +0 pp |
| Well-Made | +1 pp |
| Fine | +2 pp |
| Excellent | +3 pp |
| Superior | +5 pp |
| Exceptional | +6 pp |
| Masterwork | +8 pp |
| Grandmaster | **+10 pp** |

The spellbook must be equipped/held or otherwise be the server-recognized active book for the bonus to apply.

### 10.2 Scroll exclusion

A crafted spellbook's quality bonus applies **only when the spell is being cast from the spellbook / normal memorized-spell path**.

> **If the player casts from a scroll, the spellbook craftsmanship bonus does not apply at all.**

The scroll uses only its own craftsmanship-grade success bonus.

Examples:

- Grandmaster spellbook + ordinary spell cast from the active book: **+10 pp** from the spellbook;
- Grandmaster spellbook + Grandmaster scroll: **+20 pp** from the scroll, **+0 pp** from the spellbook;
- Grandmaster spellbook + Standard scroll: **+0 pp** from the scroll, **+0 pp** from the spellbook.

This keeps scrolls and spellbooks as separate itemization paths and prevents a permanent book bonus from increasing the reliability of consumable scroll casting.

### 10.3 No spell-power bonus

Quality spellbooks affect reliability only.

No:

- extra spell damage;
- faster casting;
- mana regeneration;
- lower mana costs;
- AoS spell-damage properties.

---

## 11. Tailoring and Wearable Crafting

Tailoring should participate in the same quality system.

For armor-class wearable items, use the crafted armor model:

- modest raw protection;
- durability;
- reduced weight;
- reduced encumbrance where era-appropriate.

For functional non-armor wearable crafts, create bonuses only where they make sense in classic UO.

Do not manufacture arbitrary "+stats" on every clothing item solely to make it functional.

A tailoring profession should have desirable functional output, but decorative clothing may remain primarily expressive.

---

## 12. Carpentry, Bowcraft and Other Professions

The system should extend by **functional item family**, not by assigning generic random properties.

### Bowcraft/Fletching

Bows/crossbows use the crafted-weapon model:

- modest raw damage;
- hit reliability;
- durability.

### Carpentry

Functional categories may include:

- containers with modest quality-of-life improvements if safe;
- training/crafting fixtures;
- future ship/house utility;
- crafted shields/weapons where existing content supports them.

Decorative furniture does not require a combat/stat bonus.

### Musical instruments

Higher craftsmanship may:

- improve barding success modestly;
- increase instrument durability/uses.

Do not increase bard effect strength beyond UOR expectations without separate approval.

### Lockpicks

Higher craftsmanship may:

- improve Lockpicking success modestly;
- reduce break chance;
- increase uses.

### Fishing poles

Higher craftsmanship may:

- improve ordinary fishing reliability;
- increase durability;
- potentially interact with fishing-specific content.

Do not increase rare-resource/drop odds unless explicitly approved.

### General rule

> **Every major crafting profession should have meaningful functional goods. Not every decorative item needs an artificial stat bonus.**

---

## 13. Exceptional / BOD Compatibility

The shard is expected to retain UOR-style Bulk Order Deeds after reward/economy audit.

Existing "Exceptional" semantics must remain compatible.

Recommended:

- `CraftsmanshipGrade >= Exceptional` satisfies a BOD asking for Exceptional items;
- preserve an internal compatibility flag if existing BOD code depends on classic `Exceptional` boolean state;
- Masterwork and Grandmaster must not fail an "Exceptional" BOD because they are better than Exceptional.

Do not require rewriting every BOD definition merely to support the expanded grade system.

---

## 14. Magic Weapons

### 14.1 Identity

Magic weapons are the raw-damage path.

Expected classic tiers:

- Ruin
- Might
- Force
- Power
- Vanquishing

### 14.2 No general Accuracy ladder

Under this design, remove/disable ordinary magic Accuracy prefixes if necessary to preserve the distinction.

Magic weapon advantage:

> **damage**

Crafted weapon advantage:

> **some damage + handling + durability**

If existing UOR loot generation strongly assumes Accuracy properties, audit compatibility before removal and document any retained exceptions.

### 14.3 Slayer weapons

Slayer properties can remain a separate situational axis if enabled.

Slayers are acceptable because they are target-specific rather than universally superior.

Audit any stacking of:

- Slayer;
- raw magic damage tier;
- other loot properties.

The system should avoid creating a rare combination that invalidates all crafted gear in every context.

---

## 15. Magic Armor

Expected classic conceptual tiers:

- Defense
- Guarding
- Hardening
- Fortification
- Invulnerability

Magic armor's primary advantage is raw protection.

Crafted armor may overlap lower/middle tiers, but:

> **Fortification and Invulnerability must remain stronger in raw protection than any craft-derived armor configuration.**

Magic armor does not automatically gain the crafted:

- durability;
- weight reduction;
- handling benefits.

That preserves choice.

---

## 16. Crafted + Magic Hybrid Items

Default launch rule:

> **An item is either generated as magic loot or created as crafted gear; do not combine full craftsmanship grade and magic tier on the same item.**

No:

- Grandmaster Vanquishing sword;
- Masterwork Invulnerability plate;
- equivalent full-strength hybrid.

Reason:

Full stacking collapses the sidegrade structure and creates obvious best-in-slot gear.

If a future rare event allows a hybrid, it requires explicit owner approval and a separate power-budget rule.

---

## 17. Repairs and Durability

Craftsmanship grade persists through ordinary repair.

Use normal UOR repair/degradation behavior unless specifically altered.

A quality item should last longer due to its higher durability, not because it is immune to wear.

Repair must not:

- reroll quality;
- raise quality;
- duplicate maker attribution;
- refresh an item into a new pristine object that bypasses normal degradation;
- turn vendor or magic loot into crafted-quality gear.

---

## 18. Death, Loot and Full-Loot Economy

Crafted quality never implies blessing.

Crafted weapons, armor, books, tools and other ordinary items follow the shard's normal item-loss rules.

A rare Grandmaster sword can:

- wear out;
- be lost on death;
- be stolen where normal rules permit;
- be looted;
- change owners.

This is intentional.

The consumption/loss of valuable player-made goods sustains long-term crafting demand.

---

## 19. Vendor Resale, Quality Value and Gold-Faucet Protection

Craftsmanship exists primarily for player use and trade, but better craftsmanship should also have a **meaningful, modest liquidation premium** when sold to town vendors.

That town-vendor purchase value is economically important because it also serves as the reference value for the separate **Player Vendor Advance and Market Tax** feature. In that system, the quality-adjusted town-vendor value is used to determine the player-vendor advance, minimum seller price, retrieval obligation and abandonment economics. The player-vendor feature document remains the source of truth for those transaction rules.

### 19.1 Quality-adjusted town-vendor value

Recommended initial craftsmanship multipliers:

| Craftsmanship grade | Town-vendor value multiplier |
|---|---:|
| Standard | 100% |
| Well-Made | 105% |
| Fine | 110% |
| Excellent | 115% |
| Superior | 120% |
| Exceptional | 125% |
| Masterwork | 135% |
| Grandmaster | 150% |

These values are intentionally much flatter than the item's combat, utility, rarity or player-market progression.

A Grandmaster item may be substantially more desirable to players while receiving only a 50% town-vendor premium over an otherwise equivalent Standard item. The NPC value is a liquidation floor and accounting reference, **not an attempt to estimate true player-market value**.

### 19.2 Player-vendor integration

For an eligible crafted item, calculate the canonical town-vendor value **after** applying the approved craftsmanship multiplier. That quality-adjusted result becomes the town-vendor reference value used by the player-vendor system.

Current linked player-vendor targets are:

- immediate stocking advance: approximately **95%** of the snapshotted town-vendor reference value;
- minimum seller base price: **100%** of that reference value;
- successful sale: the original advance is recaptured from the buyer's base payment before the seller receives the remaining proceeds;
- buyer transaction tax: **+20%** on top of the seller's base price, destroyed as a gold sink;
- unsold retrieval: repay the full snapshotted town-vendor reference value;
- abandonment: seller keeps only the earlier advance and receives no additional payout.

Those mechanics are specified in `ModernUO-Player-Vendor-Advance-and-Market-Tax-Design.md` (not yet written); this document defines only how craftsmanship contributes to the reference value.

### 19.3 Anti-faucet invariant

Quality premiums must never make mass crafting for NPC liquidation a profitable primary business model.

The governing rule is:

> **Expected NPC liquidation value across the full crafting-quality distribution must remain below the expected economic cost of mass-producing the item.**

Economy tests must include:

- resource cost;
- craft failure rate;
- quality probabilities;
- tool cost/consumption;
- material-value modifiers;
- base NPC purchase value;
- craftsmanship-value multiplier;
- expected NPC liquidation value by crafter skill band;
- linked player-vendor advance rate;
- player-market expected value.

If a recipe becomes profitable to mass-produce purely for NPC sale or player-vendor abandonment, adjust base buyback values, quality multipliers, recipe economics or related inputs rather than removing the meaningful quality premium entirely.

---

## 20. Quality-Roll Rules

All quality rolls are server-authoritative.

A quality roll occurs:

1. after recipe eligibility;
2. after successful creation;
3. after normal resource consumption;
4. before final item properties are committed.

The quality selection always resolves to exactly one eligible craftsmanship grade, including Standard. There is no separate "failed quality roll" once item creation has succeeded.

One craft produces one craftsmanship grade.

Do not allow:

- reroll tokens;
- cancel-after-seeing-grade exploits;
- rollback duplication;
- container tricks that repeat the roll;
- client-selected RNG seeds.

Use persistent/server RNG appropriate to the existing codebase.

---

## 21. Tool Bonus Interaction

Apply bonuses in an explicit order.

Recommended:

1. actual character skill determines title/grade unlocks;
2. tool effective-skill bonus may improve normal recipe success;
3. successful item creation occurs;
4. determine highest grade the **actual character skill** has unlocked;
5. load/interpolate the base final-grade distribution for the character's actual skill band;
6. apply the tool's configured **relative** quality modifier without unlocking unavailable grades;
7. normalize the eligible grade weights back to 100%;
8. make one server-authoritative weighted grade selection;
9. apply item-family bonuses;
10. apply crafted raw-power cap.

This prevents a high-end tool from making a novice count as a Master.

---

## 22. Player-Facing Item Labels

Keep labels readable.

Example weapon:

`Grandmaster Crafted Katana`
`crafted by Aric`
`Damage: +12%`
`Balanced: +6 effective Swordsmanship to hit`
`Durability: +75%`

Do not expose unnecessary internal formulas.

For classic aesthetic, exact presentation may use property gumps/inspection text rather than AoS-style dense property lists.

Example scroll:

`Grandmaster Recall Scroll`
`Casting Success: +20 percentage points`
`crafted by Elora`

The UI must distinguish:

- percentage increase;
- percentage-point increase;
- relative chance bonus.

---

## 23. Economic Role by Crafter Stage

### Beginning crafter

A beginning smith can:

- make baseline goods;
- occasionally make Well-Made items;
- sell lucky superior results;
- feel productive before GM.

### Mid-skill crafter

An Apprentice/Journeyman/Expert can:

- produce superior equipment regularly;
- unlock higher quality grades;
- meaningfully supply newer players and replacement gear.

### Master / Grandmaster

A high-end crafter becomes:

- a source of reliable high-quality gear;
- a producer of rare Masterwork/Grandmaster pieces;
- economically recognizable through maker marks;
- a participant in endgame collection/prestige without a permanent power ladder.

The endgame is not "get 120 Blacksmithy."

The endgame is:

> **build a reputation, produce rare work, operate a market, collect tools/materials, fulfill demand and create items people care about losing.**

---

## 24. Relationship to Shard Endgame

This system supports the shard's horizontal-endgame philosophy.

It creates long-term goals through:

- rare-output hunting;
- player reputation;
- merchant/vendor play;
- collection of masterwork pieces;
- item replacement through full loot and durability;
- profession interdependence;
- resource demand from Expedition gathering;
- high-value trade between PvE players, crafters and PvPers.

It does not require:

- 120 skills;
- mastery trees;
- permanent crafting talent trees;
- item-level inflation;
- endlessly escalating materials.

---

## 25. Relationship to Expedition Regions

Expedition Regions provide +50% approved resource yield and 3x effective resource carrying capacity under the main shard plan.

That system should feed crafting without creating exclusive Expedition-only power materials.

At launch:

- normal resources remain usable everywhere;
- Expedition bonuses increase supply/traffic;
- Craftsmanship Grade depends on skill/tools/RNG, not on being inside an Expedition Region;
- do not increase Craftsmanship Grade chance merely because the resource was gathered during an Expedition.

Future cosmetic/special recipes may use Expedition content with owner approval.

---

## 26. Configuration

Recommended conceptual configuration:

```text
craftsmanship.enabled = true

craftsmanship.rawPowerCap.weapon = ForceEquivalent
craftsmanship.rawPowerCap.armor = HardeningEquivalent
craftsmanship.allowCraftedMagicHybrid = false

craftsmanship.newCrafterSuperiorChanceEnabled = true
craftsmanship.quality.maxActiveGradesPerSkillBand = 4

craftsmanship.weapon.handlingBonusEnabled = true
craftsmanship.weapon.durabilityBonusEnabled = true
craftsmanship.armor.weightReductionEnabled = true
craftsmanship.armor.durabilityBonusEnabled = true

craftsmanship.tools.playerMadeBaseBonusEnabled = true
craftsmanship.tools.qualityChanceBonusMode = relative
craftsmanship.tools.bonusUnlocksGrades = false
craftsmanship.tools.applyQualityBonusWhenCraftingTools = false

craftsmanship.scrolls.grandmasterSuccessBonusPercentagePoints = 20
craftsmanship.spellbooks.grandmasterSuccessBonusPercentagePoints = 10
craftsmanship.spellbooks.applyBonusToScrollCasts = false

craftsmanship.bod.exceptionalMinimumGrade = Exceptional

craftsmanship.vendorValue.Standard = 1.00
craftsmanship.vendorValue.WellMade = 1.05
craftsmanship.vendorValue.Fine = 1.10
craftsmanship.vendorValue.Excellent = 1.15
craftsmanship.vendorValue.Superior = 1.20
craftsmanship.vendorValue.Exceptional = 1.25
craftsmanship.vendorValue.Masterwork = 1.35
craftsmanship.vendorValue.Grandmaster = 1.50
craftsmanship.vendorValue.useForPlayerVendorReferenceValue = true

magicWeapons.accuracyTierEnabled = false
```

Each skill-band grade distribution, quality modifier and item-family bonus must also be configurable.

---

## 27. Required Engineering Audit

Before implementation, inspect the current ModernUO/UOContent code for:

1. exact UOR skill-title thresholds;
2. current `ItemQuality` / Exceptional representation;
3. weapon damage-modifier implementation;
4. magic weapon tier implementation;
5. any Accuracy magic-property implementation;
6. armor protection / AR modifiers;
7. magic armor tier implementation;
8. durability/max-hit implementation;
9. repair degradation;
10. colored ore/material bonuses;
11. crafting success formula;
12. tool-use architecture;
13. tool durability/use counts;
14. BOD Exceptional checks;
15. spell-scroll casting-success formula;
16. hard minimum Magery requirements by circle/spell;
17. spellbook item/equipped-book detection;
18. bard instrument quality;
19. lockpick success/breakage;
20. bow/fletching item creation;
21. NPC resale formula and quality-adjusted buyback hooks;
22. maker's mark persistence;
23. save serialization for new craftsmanship grade;
24. item property display / ClassicUO support.

Prefer:

**configuration > shard-specific extension/content > narrowly scoped UOContent changes > core/server changes only as last resort.**

---

## 28. Required Tests

### Crafting grade

Verify:

- a beginning crafter produces Well-Made gear on approximately 10% of successful crafts;
- Apprentice output is approximately 30% better than Standard in total;
- locked grades cannot roll;
- reaching title milestones unlocks intended grades;
- skill increases shift the final output distribution toward higher unlocked grades;
- GM output matches the configured high-quality-heavy distribution;
- no skill band can produce more than four distinct craftsmanship qualities;
- when a new grade enters a full active window, the lowest grade drops out as configured;
- only one grade is produced;
- weighted grade selection and normalization work correctly;
- restart/save does not corrupt grade;
- maker mark persists.

### Raw-power ceiling

Verify:

- every crafted weapon grade has intended raw damage;
- every crafted armor grade has intended raw protection;
- material bonuses count toward craft ceiling;
- no crafted weapon exceeds configured Force-equivalent ceiling;
- no crafted armor exceeds configured Hardening-equivalent ceiling;
- Power and Vanquishing always exceed best crafted raw weapon damage;
- Fortification and Invulnerability always exceed best crafted raw armor protection.

### Weapon utility

Verify:

- hit bonus affects attack-success calculation only;
- actual weapon skill is unchanged;
- 700 skill cap unaffected;
- title/ability checks unaffected;
- durability modifier correct.

### Armor utility

Verify:

- weight reduction applies correctly;
- no zero/negative weight;
- durability correct;
- protection still respects raw-power cap.

### Tools

Verify:

- vendor tool has no custom bonus;
- player-made Standard tool is better than vendor;
- effective skill does not unlock grade/recipe/title;
- quality bonus is relative, not percentage points;
- quality bonus does not recursively apply when crafting tools;
- uses/durability serialize correctly.

### Scrolls

Verify:

- each grade adds intended percentage points;
- 0-Magery behavior matches approved spell-circle policy;
- audited high-circle hard minimums cannot be bypassed unintentionally;
- damage/heal/mana/cast-speed remain unchanged;
- scroll is consumed normally.

### Spellbooks

Verify:

- book must be active/equipped as designed;
- grade adds intended success bonus;
- spellbook quality bonus does not apply to any scroll cast;
- no damage/healing bonus.

### Magic items

Verify:

- magic weapon Accuracy ladder is disabled if that is the final implementation decision;
- raw damage tiers remain correct;
- magic armor tiers remain correct;
- no accidental crafted-quality roll on generated magic loot;
- Slayer interactions remain within approved balance.

### Economy

Verify:

- each craftsmanship grade applies the configured town-vendor-value multiplier correctly;
- expected NPC liquidation value remains below expected mass-production cost for every relevant recipe/skill band;
- player-vendor reference value uses the same quality-adjusted town-vendor value without double-applying the craftsmanship multiplier;
- player-vendor abandonment is never more lucrative than direct NPC liquidation;
- successful player-vendor sale recaptures the original advance as defined by the linked vendor feature;
- quality items remain tradeable/lootable;
- repair does not reroll or upgrade quality;
- full-loot rules preserve item sink.

---

## 29. Telemetry / Balancing Metrics

Track at minimum:

- crafts attempted by profession;
- successful crafts;
- grade distribution by profession and skill band;
- tool quality used;
- resources consumed;
- highest grades created per day/week;
- player-vendor listing/sale prices if available;
- destruction/death-loss of high-grade items if feasible;
- NPC resale gold from crafted items, broken down by craftsmanship grade;
- average quality-adjusted town-vendor value by item family and crafter skill band;
- crafted-item player-vendor advances, sales, retrievals and abandonments if the linked vendor feature is enabled;
- magic-tier drops by comparable equipment family;
- usage rate of crafted vs magic weapons/armor at endgame.

Questions to answer after launch:

- Are GM crafted items rare enough to feel special?
- Does a beginning crafter actually see a superior item often enough to understand the system?
- Do Power/Vanquishing and Fortification/Invulnerability remain exciting?
- Are players choosing crafted gear for utility rather than because it is simply stronger?
- Is Tinkering creating useful profession interdependence?
- Do high-quality scrolls create interesting utility without invalidating Magery?
- Is player crafting a healthy item sink/resource sink rather than a gold faucet?
- Are town-vendor quality premiums noticeable without making NPC liquidation attractive as the primary crafting strategy?
- Does the quality-adjusted reference value create healthy player-vendor stocking behavior rather than junk-listing or abandonment loops?

---

## 30. Settled Design Rules

Treat these as settled unless the owner explicitly changes them:

- every functional player-crafted item family should have a chance to materially outperform its vendor equivalent;
- a beginning crafter can immediately roll the first superior craftsmanship grade at an initial target rate of 10%;
- by Apprentice, approximately 30% of successful crafts should be better than Standard;
- higher existing UO skill-title milestones unlock higher possible craftsmanship grades;
- increasing skill shifts output probability away from low grades and toward higher unlocked grades;
- no crafter skill band may produce more than four distinct craftsmanship qualities; as new high grades enter, low grades drop out of the active window;
- by Grandmaster, most successful crafts are high quality while the Grandmaster grade itself remains rare;
- crafted weapons receive **both raw damage and handling/durability benefits**;
- crafted armor receives **both raw protection and durability/weight/handling benefits**;
- the best crafted weapon remains weaker in raw damage than **Power and Vanquishing**;
- the best crafted armor remains weaker in raw protection than **Fortification and Invulnerability**;
- current balancing target places the crafted raw-power ceiling around **Force / Hardening equivalence**;
- all craft-material raw-power bonuses count toward the crafted raw-power ceiling;
- ordinary magic weapons emphasize raw damage rather than Accuracy;
- ordinary magic armor emphasizes raw protection;
- full-strength crafted + magic hybrid items are disabled at launch;
- player-made crafting tools outperform vendor tools;
- tool skill bonuses cannot unlock grades, titles or recipes;
- tool quality bonuses are relative probability bonuses;
- tool quality does not recursively amplify quality when crafting more tools;
- Grandmaster crafted scroll target is +20 percentage points spell success;
- Grandmaster crafted spellbook target is +10 percentage points spell success for non-scroll casting only;
- crafted spellbook quality bonuses never apply to scroll casts;
- scroll/book reliability bonuses do not increase raw spell power;
- BOD Exceptional compatibility must be preserved;
- crafted quality does not bless an item;
- quality items remain subject to normal loss, repair and economy rules;
- craftsmanship quality receives a meaningful but modest town-vendor-value premium using the current 100% / 105% / 110% / 115% / 120% / 125% / 135% / 150% progression from Standard through Grandmaster;
- the quality-adjusted town-vendor value is the reference value consumed by the linked player-vendor advance system;
- expected NPC liquidation value across the quality distribution must remain below expected mass-production cost;
- decorative items need not receive arbitrary combat stats merely to participate in the crafting system.

---

## 31. Owner Decisions / Open Questions

These should be decided after code audit or playtesting:

1. Exact skill-title thresholds used for each grade unlock.
2. Final craftsmanship-grade names.
3. Exact grade probabilities.
4. Exact raw damage modifier corresponding to each crafted weapon grade.
5. Exact raw protection modifier for crafted armor grades.
6. Whether Grandmaster crafted raw power equals Force/Hardening exactly or sits slightly below it.
7. Final crafted weapon hit-reliability bonuses.
8. Final durability scaling.
9. Final armor weight reduction.
10. Whether crafted armor reduces any era-specific Dex penalties.
11. Exact player-made tool effective-skill bonuses.
12. Exact tool-use multipliers.
13. Exact high-circle spell restrictions for low-Magery Grandmaster-scroll use.
14. Spellbook activation/equipment rule.
15. Whether magic Accuracy prefixes are fully removed or retained only in limited exceptional cases.
16. Slayer stacking and rarity.
17. Which Carpentry/Tailoring non-combat functional item families receive quality effects.
18. Final craftsmanship town-vendor-value multipliers after economy testing (current target: 100% through 150% by grade).
19. Whether Masterwork/Grandmaster items receive special but non-power visual naming/hues.

---

## 32. Definition of Done

This subsystem is ready for launch when:

- beginning crafters produce superior-to-Standard goods on approximately 10% of successful crafts, rising to approximately 30% by Apprentice;
- craftsmanship grades unlock and scale correctly with actual crafting skill;
- player-made crafting tools improve the crafting experience without bypassing progression;
- crafted weapons have modest raw-damage progression plus meaningful handling/durability;
- crafted armor has modest raw-protection progression plus meaningful durability/weight benefits;
- all craft-derived raw power respects a hard cap;
- Power/Vanquishing weapons exceed every crafted weapon in raw damage;
- Fortification/Invulnerability armor exceeds every crafted armor piece in raw protection;
- magic loot still has a clear endgame purpose;
- crafted gear still has clear reasons to be chosen at endgame;
- Grandmaster scrolls/spellbooks improve casting reliability under the approved low-skill/high-circle rules, with spellbook bonuses excluded from scroll casts;
- BODs, repair, death/loot and vendor economy remain compatible;
- quality-adjusted town-vendor values are meaningful but do not make expected NPC liquidation profitable versus crafting cost;
- the linked player-vendor system consumes the same quality-adjusted reference value without duplicate premiums or settlement exploits;
- no AoS-style randomized-property treadmill has been introduced;
- telemetry exists to tune quality rates and economic output after launch.

---

## 33. One-Sentence Design Test

When evaluating a future crafting or itemization feature, ask:

> **Does this make crafters valuable through quality, specialization and economy while preserving high-end magic loot and the Classic UO power ceiling?**

If not, redesign it.
