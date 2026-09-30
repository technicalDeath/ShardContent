# Rekindled Camping Design

**Status:** Proposal for iteration. Nothing here is owner-ruled, built or flagged on. Numbers are provisional until an implementation audit and playtesting.
**Milestone:** Beta 3 — Social layer, hardening and launch candidate. See the
[phased roadmap](ModernUO-UOR-Safe-World-Phased-Implementation-Roadmap.md#beta-3--social-layer-hardening-and-launch-candidate).
Explicitly **out of Alpha 3**; see [Alpha 3 phase boundaries](Alpha-3-Feature-Enablement-Plan.md#phase-boundaries).
**Opened:** 2026-09-29
**Relationship to main shard plan:** Standalone subsystem design. It proposes custom rules, so under the stock-first rule each part needs an explicit owner ruling before any build.

---

## 1. Purpose

The shard is being renamed **Rekindled** (owner confirmed 2026-09-29; the repo, docs and launchers still say Britannia Renaissance). Camping is the skill that best expresses the name: fire, rest, and bringing things back to life.

Camping is nearly dead weight in stock UOR. This design gives it a small, distinctive identity built on flavor and convenience, in the spirit of "felucca without the griefing". It is not a power skill.

Design rules:

1. **Flavor first, power last.** No effect may change PvP outcomes or multiply PvE rewards.
2. **Every part stands alone.** Each item in §4 has its own config flag and can be disabled without corrupting saves.
3. **Stock behavior is the baseline.** Campfire and Bedroll keep their stock secure-camp and safe-logout rules unless a section below says otherwise.
4. **Nothing here is a shortcut around another system.** No teleporting, no dungeon or Hot Zone rule changes, no economy faucets.

---

## 2. Stock behavior today

Verified in the source (`ModernUO/Projects/UOContent/Items/Skill Items/Camping/`). The shard has no custom Camping code.

- **Kindling** (`Kindling.cs`): stackable, 5 stone each. Double-click within 2 tiles. Fails with "not a spot nearby" in any `DungeonRegion` or when none of the four adjacent tiles can hold a fire with line of sight. Then makes a Camping skill check at 0–100; on success it consumes one and places a Campfire.
- **Campfire** (`Campfire.cs`): burns 60 s, dims until 90 s, goes out, and is deleted at 100 s. `SkipSerialization` is true, so campfires do not survive a restart. Players within 7 tiles get a secure-camp entry; after 30 s they see "The camp is now secure." The entry is dropped when they leave range, go offline, or the fire dies.
- **Bedroll** (`Bedroll.cs`): double-click to unroll; double-click again to roll up. If your camp is secure, a 10 s "Logging out via camping" gump appears. Choosing CONTINUE stores the bedroll in your pack, sets `BedrollLogout` and disconnects you.
- `antimacro.json` lists Camping as `true`. Its meaning in that file has not been checked.

Client: ClassicUO computes the skills-gump total itself in `SumTotalSkills` (`StandardSkillsGump.cs`), so a display change is a client patch.

---

## 3. Owner-ruling map

| Area | Ruling needed | Notes |
| --- | --- | --- |
| Rename | Confirmed 2026-09-29 | Doc, repo and README updates still pending |
| Starter kit (§4.1) | Yes | Newbied, loose-in-pack items, existing starter rules |
| Camping outside the 700 cap, starting at 50 (§4.2) | Yes | Needs a server cap hook and a ClassicUO patch |
| Core campfire effects (§4.3) | Yes | Skill-scaled burn time, rekindle, embers |
| Signal fire (§4.4) | Yes | Client patch |
| Thief protection (§5.1) | Yes | Custom rule; plugs into the Cool Dungeon theft-immunity path |
| Persistent fuelable fire (§6) | Yes | New serialization, per-character cap, placement rules |
| Camp stall vendor (§6.3) | Yes, and after housing zoning | Economy feature; not an engine hook |

---

## 4. Core proposals

### 4.1 Starter kit

Every new character receives a stack of Kindling and a Bedroll, loose in the backpack, newbied and permanently bound, and kept through every death, exactly as the other starter items. Quantity is provisional (suggest 3–5 kindling). Confirm that a stack of newbied Kindling stays newbied when it splits or is consumed.

### 4.2 Camping outside the cap, starting at 50

- New characters start at Camping 50.
- Camping does not count toward the 700-point total.
- **Server:** exclude Camping from the total used by the skill-gain cap check in `Projects/Server`. This is a narrow engine hook; follow `ModernUO/CLAUDE.md`.
- **Client:** subtract Camping in ClassicUO's `SumTotalSkills` so the displayed total matches the server.
- **Open:** does Camping still gain? Can it be locked or lowered? Does `[skills`, or anything that reports a total, treat it specially? Does character creation still offer it as a choice, and how do profession templates that grant Camping change?
- **Rejected alternative:** make Kindling always ignite and leave Camping decorative. This avoids the cap work but leaves the skill with no purpose. It remains the fallback if the out-of-cap route is dropped.

### 4.3 Camping effects on the campfire

Provisional, scaled by Camping skill (0–100):

| Effect | Behavior |
| --- | --- |
| Burn time | 100 s at skill 0, rising to about 5 minutes at skill 100 (stock timings as the floor) |
| Rekindle | Adding Kindling to an Extinguishing fire restores burn time; skill scales the amount restored |
| Embers | A burned-out fire leaves an ember item for a short time; using Kindling on it relights the fire with no skill roll and a longer burn |
| Fireside rest | Standing near a lit fire, out of combat, gives a mild stamina and mana regen bonus scaled by skill |

Stock secure-camp and Bedroll safe-logout stay as they are. Dungeon regions keep refusing fires.

### 4.4 Signal fire

Party members see your lit campfire as a marker on their map or radar, and its light is visible from farther away. Information only; no teleport, no power. Needs a small ClassicUO patch.

---

## 5. Layered proposals (choose a few)

Each is independent and flag-gated. None is required by the core package.

### 5.1 Thief protection

A player whose camp is secure (the 30 s state) cannot have items stolen from them; snooping stays allowed. This mirrors the Cool Dungeon precedent. It ends the moment the player enters combat or takes a hostile action, and it protects only the camper, not a thief standing beside them. Read `[TheftStatus` and the existing theft path before building, so the camp check plugs into the same hook.

### 5.2 Night watch

At a lit camp, an overhead alert warns you when a hostile player or monster comes within a set distance. Information only.

### 5.3 Firelight wariness

Undead and nocturnal creatures path around a lit fire. No damage, to-hit or stat penalty. Not applied inside Hot Zones. Any monster-AI change must leave spawn caps and cadence untouched.

### 5.4 Vigil and warm return

- A lit fire is visible to ghosts as a beacon, so a fallen party member can find their body.
- A character resurrected at a lit camp returns with full stamina and a short calm period.

### 5.5 Well rested

Logging out through a Bedroll grants a short, small regen buff at next login.

### 5.6 Cosmetic and collectible

- **Colored flames:** throw a reagent into the fire to change its color; a reagent sink; skill unlocks more colors.
- **Ask the embers:** "gaze" for a lore line or hint; ties into Beta 2 collections as a Tales of Rekindling set (about 20 tales, one per character).
- **Cold ashes:** a burned-out fire leaves ash that Tracking can read as "a camp, recently used, by a small group". No names.
- **Camp titles** for tending many fires; **named camps** shown to the party (needs a text filter).
- **Harmless visitors:** birds and rabbits drift to a lit fire; capped, and separate from spawn caps.

### 5.7 Carry the flame

A torch lit from a campfire holds a living flame for about 30 minutes; touching it to another fire lights it instantly. Overlaps Beta 1 Pilgrimage; coordinate before building.

### 5.8 Housing hearth

A decorative fire pit for player houses that can be lit any time and keeps a chosen flame color. Ships with Beta 2 house zoning.

### 5.9 Events

A seasonal **Rekindling festival** where every campfire burns longer and glows a special color. Uses the event scheduler.

---

## 6. Persistent fires and the camp stall (gated)

### 6.1 Fuelable fire

- Adding Kindling extends the burn, with a maximum scaled by skill: minutes at low skill, up to 24 hours at Grandmaster.
- Persistence is a real change: `Campfire` skips serialization today, so a long-lived fire must be saved and survive restart, and its timer must be wall-clock so a fire burns out on schedule afterward.
- Guardrails: one active long fire per character (suggested); no fires in dungeons, Hot Zones, on town roads, near doors or banks; a minimum spacing between fires.

### 6.2 Kindling as a sink

Kindling weighs 5 stone a unit, so a day-long fire costs a lot of it. That is the natural limiter.

### 6.3 Camp stall vendor

The idea: place a vendor at a campfire. It is an economy feature, not a hook.

- As far as I recall, stock player vendors are tied to houses. **Unverified — audit before design.**
- Interacts with house zoning and district policy (Beta 2), and with road, spawn and town clutter.
- Must answer: what happens to stock and gold when the fire dies (return safely to the owner's bank or pack); theft and killing of the vendor; duplication and item-loss risks; fees.
- Proposed limits if it ships: one stall per fire, existing only while the fire burns, only in whitelisted outdoor areas, unsold goods returned to the owner.
- Not before Beta 2 house zoning is complete.

---

## 7. Rejected

- **Truce ring** (no PvP around a camp): a large rule change that cuts across Hot Zones.
- **Friend summon** (teleport a party member to your camp): bypasses travel, Hot Zones and combat, and collides with Beta 1 travel systems. If ever revisited, it must be consent-based, out of combat, not criminal or Knocked Out, outside Hot Zones and dungeons, with a long cooldown that consumes the fire.
- **Kindling always ignites with Camping decorative:** kept only as the fallback if §4.2 is dropped.

---

## 8. Engineering notes

- **Config:** a new `shard-rules.json` section with a master flag and one flag per part. All default to false, and `alpha3EnablementAcknowledged` is unaffected. Validate in `ShardRulesConfiguration.cs`.
- **Serialization:** any new persistent item follows `ModernUO/CLAUDE.md` (serialization generator, version, `MigrateFrom`). Timers use `[DeserializeTimer]`; long fires are wall-clock.
- **Callbacks:** register shared ModernUO callbacks once, behind a guard, with `+=`.
- **Regions:** honor the existing `DungeonRegion` refusal; add Hot Zone and town-road exclusions from region data, not hard-coded coordinates.
- **Diagnostics:** a staff `[CampStatus` command (active fires, owners, ages, stall state).
- **Tests:** xunit coverage for burn-time scaling, rekindle, ember expiry, cap exclusion, thief-protection break conditions, persistence across save/restart and vendor return-on-death. Client tests for the signal fire and total display.

---

## 9. Dependencies

- Skill cap accounting (`Projects/Server`) and ClassicUO `SumTotalSkills`: §4.2.
- Theft system and the Cool Dungeon theft-immunity path: §5.1.
- Beta 1 Pilgrimage and travel: §5.7.
- Beta 2 house zoning and collections: §5.6, §5.8, §6.3.

## 10. Open owner decisions

1. Which parts of §4 and §5 are in the launch package? Suggested core: skill-scaled burn time, rekindle, embers, signal fire; then two or three flavor items.
2. Does Camping start at 50 and sit outside the 700 cap, or does the fallback apply?
3. Are long fires allowed anywhere outdoors, or only in whitelisted zones? One active fire per character?
4. Does the camp stall exist at all, and if so, after house zoning?
5. Thief protection: yes or no, and does snooping stay allowed?
