# Alpha 3 Phase J (slice 1): later-era skill gates readiness

**Scope note:** Feature J covers all 58 exposed skill IDs; this record closes only the first agreed slice — the 9 later-era skills (Necromancy through Throwing, IDs 49–57) plus the standalone skill-15 naming ruling. The pre-AoS skill families (combat/magic, bard/animal, stealth/crime, craft/harvest, medical/utility) remain open under J and are not addressed here. `alpha3EnablementAcknowledged` stays false; this closes slice readiness only.

## Reused accepted evidence

- The generic UOR entry-gate machinery (`SkillCheck.IsSkillAvailable`, the four public check callbacks, `SkillsInfo.Random*Skill`) was already built and tested for all 9 later-era skills — `UorUnavailableSkillTests` (9/9), `UorCharacterCreationSkillTests`, `UorLaterSkillSetterTests` (28/28 combined, run `20260928T123417632Z-78f388` and `20260928T123641375Z-948963`). Reused unchanged; this slice only adds item-acquisition-level coverage on top.
- `UorNinjitsuItemGateTests` (Smoke Bomb, Egg Bomb, Fukiya, Leather Ninja Belt use-gating) reused unchanged.

## Current-source review and owner rulings (2026-09-28)

- **Skill ID 15 (Discordance/Enticement):** owner ruled Discordance, as an explicit shard deviation from the strict April 2000 baseline. No code change was needed — `Server/SkillHandlers/Discordance.cs` already implements the Publish-16 debuff mechanic unconditionally, including a distinct pre-AOS branch (`StatMod`s instead of `ResistanceMod`/`DefaultSkillMod`s); there is no Enticement mechanic anywhere to revert from. `ProfessionSkillName: Enticement` only labels the character-creation profession list and has no runtime effect. Documentation/contract classification only. See [Alpha-3-Player-Skill-Audit.md](Alpha-3-Player-Skill-Audit.md), ID 15 and SK-001.
- **Later-era item-acquisition trace:** for each of the 9 skills, traced whether its spellbook/tool/weapon can be obtained under UOR despite the skill itself being unavailable:
  - **Necromancy(49), Mysticism(55):** already properly gated (`SBMage`/`SBVarietyDealer` wrap `NecromancerSpellbook` in `Core.AOS`; `DefInscription` wraps the `MysticSpellbook` recipe in `Core.SA`). No fix needed.
  - **Focus(50), Imbuing(56):** no associated item exists at all (Focus is a pure passive; Imbuing has no dedicated item/tool/spellbook class anywhere in this content set). Not applicable.
  - **Spellweaving(54):** no vendor stock or craft recipe exists for `SpellweavingBook`; only reachable via an ML quest definition or staff `[add`. Not exploitable in ordinary UOR play. No fix needed.
  - **Throwing(57):** `BaseThrown.CanEquip` already refuses pre-`Core.SA` with a player-facing message, and `DefBlacksmithy`'s Boomerang/Cyclone/Soul Glaive recipes are already wrapped in `Core.SA` + `SetNeededExpansion`. Already correct, but untested — added coverage.
  - **Chivalry(51), Bushido(52), Ninjitsu(53) — bug found and fixed (Contract-Review.md J-9):** `SBKeeperOfChivalry`, `SBSamurai` and `SBNinja` sold their respective spellbooks (`BookOfChivalry`, `BookOfBushido`, `BookOfNinjitsu`) with **no era gate at all**, and the stock SE monsters `Ronin`/`EliteNinja` dropped `BookOfBushido`/`BookOfNinjitsu` on death with no gate either. Confirmed via `git -C ShardContent/../ModernUO grep`/spawner-data search that neither `Ronin`/`EliteNinja` nor these three vendor types appear in this shard's Alpha 2b spawner data, so this was not exploitable in the current world — but it was a real latent gap, not a hypothetical one, and the exact class of bug the plan's own J Todo calls out ("reachable later-era item/spell/special paths"). Fixed by wrapping each in the same `Core.AOS`/`Core.SE` guard already used for Necromancy's identical `SBMage` case:
    - `ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBKeeperOfChivalry.cs` — `Core.AOS`
    - `ModernUO/Projects/UOContent/Mobiles/Vendors/SBInfo/SBSamurai.cs`, `SBNinja.cs` — `Core.SE`
    - `ModernUO/Projects/UOContent/Mobiles/Monsters/SE/Ronin.cs`, `EliteNinja.cs` — `Core.SE`

No ShardContent code changes were needed for this slice — every fix lives in the ModernUO fork, gated by era only (no new feature flag), matching the convention already established for Necromancy.

## New verification

- New test file `ModernUO/Projects/UOContent.Tests/Tests/Items/UorLaterEraItemGateTests.cs` (7 cases): UOR vendors stock none of the three books; AoS/SE vendors stock them correctly; `Ronin`/`EliteNinja` drop no book under UOR but do under SE; `Boomerang.CanEquip` refuses under UOR and succeeds under SA.
- Focused run: `work/agent-verification/runs/20260929T003607662Z-d9e08c`, 7/7 passed.
- Broader UOR regression: `work/agent-verification/runs/20260929T003435243Z-41cfc2`, all `FullyQualifiedName~Uor` UOContent tests, 76/76 passed.
- Full Shard suite (unaffected, ShardContent untouched): `work/agent-verification/runs/20260929T003446620Z-85c0f6`, 230/230 passed.

## Gate and validator

No flag changes. These are era gates (`Core.AOS`/`Core.SE`) on stock ModernUO vendor/monster classes, not `ShardRulesConfiguration` feature flags. `alpha3EnablementAcknowledged` remains false.

## Readiness limits

- No live-client pass for any of the 9 skills' actual spell/special use, or for ordinary-client denial when a player lacks the skill. The generic fizzle gate (`Spell.CheckFizzle` → `SkillCheck.IsSkillAvailable`) is source-proven and covered by existing `UorUnavailableSkillTests`, which this slice treats as sufficient given how rarely-reachable these skills are (no spawner presence for any of the fixed vendor/monster types); a live pass was judged not worth the setup cost for this slice.
- This is slice 1 of Feature J only. The 48 pre-AoS skills (IDs 0–48) — the bulk of J's real scope and risk — remain almost entirely untraced and are not covered by this record.
