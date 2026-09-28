# Skill Breadth: Diminishing Returns for Selected Skills

Status: design proposal for a reversible public-test pilot  
Audience: players who value T2A/UOR combat, recognizable skills, a 700.0 total skill cap, and
build discovery  
Working player-facing name: **Skill Breadth**

## Decision

Keep the 700.0 total skill cap, the 100.0 individual cap, all displayed skill values, ordinary
skill-gain rules, and the 95.0–100.0 Mastery system. Change only the numerical combat contribution
of four selected skills for player characters:

1. Anatomy
2. Lumberjacking
3. Evaluating Intelligence
4. Resisting Spells

The first points in these skills buy more of their numerical contribution than the last points.
Grandmaster remains the strongest value in a skill, but is no longer the only efficient stopping
point. Actual skill remains authoritative for success checks, spell access, harvesting, special
actions, curing, resurrection, skill gain, titles, and every categorical threshold.

Do not include Tactics, weapon skills, Magery, Healing, Meditation, Parrying, Poisoning, barding,
taming, crafting, or gathering success in the first release.

This is not a general replacement for UOR formulas. It is a small, legible exception intended to
produce more viable allocations inside the classic skill system.

## Product promise

> Every point still helps. Grandmaster is best at one thing; breadth is better at more things.

The feature succeeds when a veteran can still construct and play a recognizable tank mage, dexer,
axe warrior, resist mage, or bard, while discovering credible 40–80 point variations that are not
merely unfinished versions of 7x GM templates.

The feature must not:

- raise either skill cap;
- add classes, talent trees, respec tokens, itemized skill bonuses, or formal combat roles;
- change spell circles, weapon hit chance, bandage cure/resurrection thresholds, resource access,
  or skill-use success chances;
- make a collection of 30–40 point skills universally optimal;
- conceal the effective values from players;
- make a stock 7x GM character nonviable.

No design can guarantee universal approval. The consensus strategy is therefore conservative:
retain the familiar verbs and caps, make the rule easy to calculate, publish every number, use a
feature flag, and require public-test evidence before permanent adoption.

## The curve

For the affected numerical effects, translate actual player skill `S` into contribution skill `C`:

| Actual skill S | Contribution skill C | Share of GM contribution |
|---:|---:|---:|
| 0.0 | 0.0 | 0% |
| 20.0 | 30.0 | 30% |
| 40.0 | 60.0 | 60% |
| 60.0 | 78.0 | 78% |
| 80.0 | 90.0 | 90% |
| 90.0 | 95.0 | 95% |
| 95.0 | 97.5 | 97.5% |
| 100.0 | 100.0 | 100% |

Interpolate linearly between anchors. In equivalent pseudocode:

```text
0–40:    C = 1.50S
40–60:   C = 60 + 0.90(S - 40)
60–80:   C = 78 + 0.60(S - 60)
80–100:  C = 90 + 0.50(S - 80)
```

Clamp actual input and contribution output to 0–100 for this UOR ruleset. Calculate with decimal
precision and round only where the stock consumer already rounds. Temporary skill modifications
feed the curve through the skill's current `Value`; they do not change the skill's `Base`, cap, or
Mastery state.

The curve deliberately avoids a GM-only proc or cliff. The Mastery range still improves the skill
from 97.5% to 100% of maximum contribution and retains the social value of the Grandmaster title,
but a character is not numerically incomplete at 95.

## Skill behavior

### Anatomy

Use contribution Anatomy only in these player-originated numerical calculations:

- the pre-AoS melee damage modifier currently worth 1% per 5 Anatomy;
- ordinary bandage healing amount where Anatomy contributes to the minimum and maximum healed.

Keep actual Anatomy for:

- bandage cure and resurrection eligibility;
- cure and resurrection success calculations;
- skill-use success and information precision;
- skill gain and Mastery;
- any explicit special-move prerequisite (although Britannia Renaissance disables UOR Wrestling
  Stun/Disarm resolution).

Result: 60 Anatomy contributes as 78 Anatomy for damage and bandage amount: +15.6 percentage points
of the stock Anatomy melee modifier instead of +12.0, while it remains exactly 60 Anatomy for all
thresholds.

### Lumberjacking

Use contribution Lumberjacking only for the stock UOR axe damage modifier. Preserve all of the
following:

- only `WeaponType.Axe` receives the modifier;
- harvesting success, resource access, tool use, and gains use actual Lumberjacking;
- polearms, the War Axe if classified as a mace, and other name-based lookalikes receive no bonus;
- there is no later-era GM-only +10 spike.

Result: 40 Lumberjacking contributes as 60 and adds 12 percentage points to the stock additive axe
modifier instead of 8. GM remains the stock +20.

### Evaluating Intelligence

Use contribution Evaluating Intelligence wherever pre-AoS direct spell damage compares the
player caster's Evaluating Intelligence with the target's Resisting Spells. Keep actual skill for
all active skill checks, information output, gains, and any categorical requirement.

Do not apply this substitution to Magery casting chance, spell-circle access, duration formulas,
or unrelated later-era spell systems that are disabled by the UOR gates.

### Resisting Spells

Use contribution Resisting Spells wherever an eligible pre-AoS hostile spell calculation compares
the player target's Resisting Spells with player Evaluating Intelligence, including the opposing
value in the ordinary direct-damage scalar and the magnitude calculation for classic stat curses.

Keep actual Resisting Spells for resistance success rolls, gain checks, and categorical thresholds.
Do not silently rewrite each spell that merely mentions Magic Resist; maintain an explicit audited
consumer list.

Evaluating Intelligence and Resisting Spells must launch together and use the same curve. This
preserves parity at equal investment: 60 Eval against 60 Resist remains neutral in the ordinary
direct-damage comparison, just as 100 versus 100 is neutral. Shipping curved Resist with linear
Eval, or vice versa, is prohibited.

## Why these four

These skills are recognizable passive contributors with continuous stock effects and no need to
alter the basic UOR interface. They create breadth on both sides of the classic warrior/mage divide:

- Anatomy makes partial martial and bandage competence credible.
- Lumberjacking rewards an axe commitment without making every weapon user buy it.
- Evaluating Intelligence allows utility mages to retain meaningful offense below GM.
- Resisting Spells allows a player to buy meaningful magical durability without spending a full
  100 points.

The matched spell pair prevents a one-sided global nerf or buff to magery. Lumberjacking provides a
narrow specialist outlet for points freed from Anatomy. Together they test general offense,
specialist offense, healing support, magical offense, and magical defense with one shared rule.

### Explicitly deferred

| Skill | Reason for deferral |
|---|---|
| Tactics | It is the large core weapon-damage scalar, including a penalty below 50. Curving it risks making partial Tactics mandatory on every weapon build and changes familiar damage more dramatically. |
| Weapon skills / Wrestling | Hit and defense chances are contested, highly sensitive, and central to player control. Partial values could create excessive randomness or universal defensive splashes. |
| Magery | Spell-circle access and casting reliability are categorical identity, not a passive multiplier. |
| Healing | Cure and resurrection thresholds are valuable build commitments. Anatomy already tests partial bandage output without erasing those commitments. |
| Meditation | Stock pre-AoS mana regeneration is already nonlinear and controls fight pacing. Change only after real duel-duration data. |
| Parrying | Binary mitigation and equipment restrictions need their own probability design. |
| Poisoning | Poison access and application are categorical and economically consequential. |
| Barding / taming / crafting / gathering | Difficulty gates, creature control, resources, and the economy make front-loading exploitable. |

## Template outcomes

These are design probes, not prescribed classes. Values total 700 unless noted.

### Classic control builds remain valid

- Tank mage: 100 weapon, Tactics, Magery, Eval, Meditation, Resist, Wrestling.
- Sword dexer: 100 Swords, Tactics, Anatomy, Healing, Resist, Parrying, Magery.
- Axe specialist: 100 Swords, Tactics, Anatomy, Healing, Resist, Lumberjacking, Magery.

They retain maximum contribution, reliability, and all thresholds. Their opportunity cost remains
the reason to explore alternatives—not a direct penalty imposed on being GM.

### New credible experiments

- Hybrid axe dexer: 100 Swords, 100 Tactics, 80 Healing, 60 Anatomy, 60 Resist, 40 Lumberjacking,
  100 Magery, 60 Parrying, and 100 Hiding.
  The important micro-package is 60 Anatomy + 40 Lumberjacking: +15.6 Anatomy and +12 axe damage
  points, compared with +20 from GM Anatomy alone, but with weaker bandage thresholds and no GM
  Anatomy identity.
- Resistant field mage: retain 100 Magery and core casting skills, use 40–60 Resist for meaningful
  defense, and spend the recovered points on Wrestling, a weapon, Hiding, Inscription, or a bard
  skill.
- Utility mage: 60 Eval contributes as 78 in the direct-damage comparison but is materially weaker
  than GM against high Resist. The freed 40 points can support a real secondary identity.
- Ranger or warrior-bard: 60 Anatomy supplies credible damage and bandage amount while 40 points
  help fund an actual utility skill; the character still needs the utility skill's real thresholds.

Before release, enumerate exact 700-point versions of at least 24 templates: six classic controls,
six partial-Anatomy builds, four axe variants, four partial-Eval mages, and four partial-Resist
builds. Do not count a build as distinct when it only moves points between skills that do not affect
the tested encounter.

## Balance model

### Point efficiency is intentional, free power is not

At 40 points, a selected passive skill supplies 60% of its maximum numerical contribution. This is
the feature. The remaining 60 points purchase the last 40% plus thresholds, reliability, GM status,
and any unaffected uses of the actual skill.

The balance unit is the complete 700-point template, not one skill in isolation. A hybrid must give
up points from somewhere real. Every comparison must therefore name both complete templates and
the encounter being tested.

### Guardrails

- Contribution values never exceed the stock GM contribution.
- There are no new random procs, cooldowns, activated abilities, or item requirements.
- Player skill curves do not alter NPC or uncontrolled-creature skill values.
- Controlled creatures receive no curved contribution through their owner.
- A player-originated effect uses the player curve even against an NPC; a creature-originated
  effect remains stock. This gives player builds one understandable rule without globally retuning
  the bestiary.
- All four substitutions must be centralized in shard-owned code and individually feature-gated.
- The umbrella `skillBreadth` flag is valid only when the matched Eval/Resist pair has the same
  enabled state and curve revision.
- The server logs its curve revision and enabled consumers at startup.
- Disabling the flag restores stock behavior without modifying stored character skills.

### Principal risks and counters

1. **Every build splashes 40 Resist.** Compare 0, 20, 40, 60, 80, and 100 Resist against common
   spell sequences. If 40 dominates both 0 and 60 after accounting for the alternative 40 points,
   reduce the 40 anchor from 60 to 55; do not add a hidden counter-system.
2. **Tank mages gain more than warriors.** Eval and Resist are symmetrical, but freed points may
   compound with Wrestling or weapon defense. Test full tank-mage templates against dexers and
   pure mages, not spell damage alone.
3. **Axe damage becomes burst-heavy.** Test final post-armor damage and kill sequences. The target
   is more build choice, not a shorter universal time-to-kill.
4. **Partial Anatomy gives too much healing and damage together.** If it crowds out GM Anatomy,
   reduce only its bandage-amount contribution before changing the shared curve.
5. **Many shallow skills replace 7x GM.** The pilot affects only four skills, two of which form an
   opposing pair and one of which is axe-only. Do not expand the list until telemetry shows several
   stable stopping points rather than a universal 40-point floor.
6. **Rules feel custom or opaque.** Publish the anchor table in the website rules and expose an
   in-game read-only command. Never market hidden decimals as discovery.

## Player communication

Use era-compatible language and avoid modern class/role terminology.

Suggested rules text:

> Anatomy, Lumberjacking, Evaluating Intelligence, and Resisting Spells grant more of their combat
> benefit in their earlier ranks. Every point remains useful, and Grandmaster remains strongest.
> Skill checks and special requirements still use the number shown on your skill list.

Add `[SkillBreadth` as a read-only player command. It reports:

- whether the feature is enabled;
- the curve revision;
- the four affected skills;
- the character's actual and contribution value for each;
- one sentence explaining that requirements and success checks use actual skill.

Do not alter the skill-gump number or pretend the player possesses a higher skill. “Contribution”
must always be labeled as such.

## Implementation boundary

New behavior belongs in `ShardContent/src/BritanniaRenaissance.Content/`. Add one pure,
side-effect-free curve service and expose only narrow ModernUO delegates at the stock calculation
sites that cannot be safely wrapped from the content assembly.

Preferred API shape:

```text
SkillBreadthService.GetContribution(player, skillName, consumer)
```

The `consumer` is explicit—melee damage, bandage amount, axe damage, classic spell comparison, or
classic curse magnitude—so a future call site cannot accidentally curve success chance or access.

Any ModernUO fork change must be limited to delegate hooks that accept the mobile, skill name,
consumer, and stock value and return the contribution value. Stock behavior is the fallback when
no handler is installed. Do not duplicate complete weapon, bandage, or spell implementations in
the shard assembly.

Configuration should include:

```json
{
  "featureFlags": {
    "skillBreadth": false
  },
  "skillBreadth": {
    "curveRevision": 1,
    "anchors": [
      { "actual": 0.0, "contribution": 0.0 },
      { "actual": 40.0, "contribution": 60.0 },
      { "actual": 60.0, "contribution": 78.0 },
      { "actual": 80.0, "contribution": 90.0 },
      { "actual": 100.0, "contribution": 100.0 }
    ]
  }
}
```

The checked-in production/default profile remains disabled until the public-test gate passes.
Reject malformed anchors, decreasing output, output above 100, a missing 0/100 endpoint, or a
configuration that enables only one member of the Eval/Resist pair.

## Verification

### Automated tests

- Exact curve output at 0, 20, 40, 60, 80, 90, 95, and 100.
- Monotonic output for every tenth from 0.0 to 100.0.
- No contribution above 100 and no negative contribution.
- Feature-off results are byte-for-byte stock at every integration point.
- NPC and controlled-creature calculations remain stock.
- Anatomy changes melee modifier and bandage amount only; cure/resurrection gates remain stock.
- Lumberjacking changes only axe damage; harvesting and every non-axe class remain stock.
- Eval and Resist use identical curve revisions and remain neutral at equal actual skill.
- Spell casting chance, circles, skill checks, gains, and Mastery remain stock.
- Curse magnitude is curved only at the explicitly audited classic call sites.
- Temporary skill modifiers use current `Value`; `Base`, cap, and Mastery data are untouched.
- Save/restart changes no character state because the feature stores no per-character data.

### Deterministic combat matrix

Record distributions, not anecdotes, using fixed equipment and stats:

- Anatomy 0/40/60/80/100 across representative swords, maces, fencing weapons, and bows.
- Lumberjacking 0/20/40/60/80/100 across every approved axe plus negative controls for polearms,
  the War Axe, and non-axes.
- Eval versus Resist at every 0/40/60/80/100 cross-pair for each enabled direct-damage circle and
  each audited curse.
- Bandage amount at Anatomy 0/40/60/80/100 with fixed Healing; independently verify cure and
  resurrection gates on both sides of their thresholds.
- PvP post-armor damage, burst sequences, mana spent per kill, bandage throughput, duel duration,
  and draw/stalemate rate.
- PvM time-to-kill and resource consumption against low, middle, and high-end UOR creatures.

### Human public-test gate

Run at least two published test windows with instant test-template adjustment and no permanent
character migration. Recruit veteran PvPers, dexer specialists, mage specialists, PvM players, and
players who prefer noncombat utility. Publish exact formulas before the test.

Do not permanently enable the feature unless all are true:

- no single allocation among 40, 60, 80, or 100 appears in more than 60% of affected competitive
  templates;
- at least three distinct stopping points appear in credible, repeatedly played templates;
- stock 7x GM controls retain credible wins and are not treated as trap builds;
- median matched-duel duration remains within 15% of the stock control unless players strongly
  prefer and explicitly approve the new pacing;
- axe burst does not add a reliable one-cycle kill unavailable to its stock control;
- partial Resist does not become a near-universal tax;
- PvM gold/resource throughput for the strongest new template remains within 10% of the strongest
  stock control absent a separate economy decision;
- a post-test survey shows at least 70% of participants prefer the pilot to stock, and no major
  audience cohort falls below 60%;
- qualitative feedback describes additional choices, not merely additional power.

The survey thresholds are a release gate, not a claim of universal preference.

## Rollout

1. **Simulation:** implement the pure curve and deterministic formula harness with the runtime
   feature flag off.
2. **Staff test:** validate consumers, negative controls, commands, logs, and stock restoration.
3. **Public Test I:** run the proposed curve exactly as published; gather complete-template data.
4. **One revision maximum:** adjust anchors or the Anatomy bandage consumer once, publish the
   change, and repeat the same matrix. Avoid tuning repeatedly toward whichever group spoke last.
5. **Launch candidate:** enable for a time-boxed four-week season with a declared rollback date.
6. **Permanent decision:** retain, revise in another announced test, or disable. Disabling is safe
   because actual skills and caps never changed.

During the launch-candidate period, offer ordinary in-game skill atrophy and training; do not add
instant production respecs solely for this feature. Announce the complete rule before players lock
their templates.

## Expansion rule

After a successful season, consider at most one additional skill family per release. Tactics,
Meditation, and Parrying each require a separate design and public test. Never infer that the shared
curve is appropriate merely because a skill has a numeric effect.

The long-term aim is not “more skills per character.” It is a UOR build landscape in which 40, 60,
80, and 100 can each be deliberate answers, Grandmaster remains meaningful, and the best answer
depends on what the player wants that character to do.
