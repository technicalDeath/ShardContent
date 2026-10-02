# Beta 2a item 1: Ward and Welcome rulings readiness

**Decision:** Built, verified live on a disposable host, and deployed to the dev distribution (2026-10-02). `featureFlags.theftProtection` was already on, so the new rules are live as soon as the dev server next starts. No flag was changed. Closes Beta 2a scope item 1; Mastery and Hythloth remain.

## Rulings
- **F-4 (the mechanic): design B** of [BACKPACK-WARD-DESIGN.md](BACKPACK-WARD-DESIGN.md), as the owner corrected it on 2026-10-01. A thief caught on a *successful* theft is blocked from every theft attempt against the protected character until the Ward ends; each caught thief is blocked separately; thieves the Ward has not caught can still steal. There is no 120-second blanket immunity.
- **Owner "no preference" on the housekeeping choices; recommendations applied:** F-1 keep one starter Ward per new character; F-2 no new Ward source, small selector kept for spares; F-3 account binding removed; F-5 the unused Loot Protection entitlement, its world-load migration and login hook removed, the 10-minute repeat-looting rule kept; F-6 `[Welcome` rewritten; F-7 loot-type fixup removed. Rows are filled in [Alpha-3-Contract-Review.md](Alpha-3-Contract-Review.md).

## What the Ward does now
- **States:** Unprimed (an ordinary item), Primed (tracking thieves, blessed to its holder), Activated (has detected a theft).
- **Priming** is lazy: a detected theft, or an undetected successful one. An undetected failed attempt does not prime.
- **30-minute rolling window**, restarted only by genuine attempts (stock ran the skill roll). Primed resets to Unprimed; Activated is consumed. Blocked attempts, refused attempts and snooping do not restart it.
- **Escalation per thief account:** after an undetected success the Ward detects that account's next successful theft 25% of the time, then 50%, then every time. All characters on an account share the count and the block.
- **Caught** means a successful theft that was detected, by the victim (stock) or by the Ward. A detected *failed* attempt activates the Ward but does not block the thief.
- **Item rules:** moving the Ward to another character resets it fully; a Ward outside the equipped backpack stops acting but its clock keeps running; it can't be stolen; the starter Ward is newbied and bound; a regular Ward is blessed to its holder while tracking.
- **Outdoor Hot Zones:** no effect, as before (no priming, activation, blocking or refresh while the victim is in one).

## Interpretations to confirm
1. **Ward-detected thefts carry the ordinary detected-theft consequences** (the thief turns criminal and is told, bystanders within 8 tiles are told). The old Ward detected without consequences.
2. **The Hot Zone exemption is unchanged**, so a thief caught elsewhere may steal from the same character inside a Hot Zone.
3. **Old Wards in saves load as fresh Unprimed Wards.** Only the starter marking carries over.

## Build
`BackpackWardState.cs` (rules, no game types), `BackpackWardService.cs` (selection, priming, blocking, expiry sweep every 30 s, restart rebuild), `BackpackWard.cs` (item, save version 3), `TheftProtectionService.cs` (hooks, entitlement code removed), `StarterOnboarding.cs` (`[Welcome` text), `ShardRulesCommands.cs` (`[TheftStatus [serial]` for staff).

**ModernUO hook (narrow):** `Stealing.TheftResolved` now passes `rolled`, true only when the skill check ran. Live testing showed stock calls the hook for attempts it refuses before the roll (hands full, not in the guild, newbied item, a shard veto), which looked like failed rolls and kept a Ward's window open. Local ModernUO commit `eba68d2be`, pin bumped in the three places; **not pushed**.

## Verification
- **Unit:** Shard suite 360/360 (31 Ward-state tests, including persistence and the Welcome text). UOContent 1254 pass, 2 fail: the two known failures on ModernUO HEAD (`AdvancedSearchTypesTests.Poison_ReferenceTypeParsedViaTypes`, `FamiliarAITests.HiddenCaster_FamiliarRefusesRetaliation`), not from this work.
- **Live (disposable host, real Navrey clients, real Stealing rolls; drivers `tests/scenarios/ward/ward_live.py`, `ward_probe_live.py`, probe `WardProbe.cs`):**
  - Starter Ward issued Unprimed; `[Welcome` shows the new text.
  - A thief caught on a successful theft is blocked ("You cannot steal from that person right now", `ward-blocked` audited, no roll) while the Ward lasts.
  - A second thief is not blocked, reaches the roll, and is then caught and blocked separately; both stay blocked; a third, uncaught thief still rolls.
  - Escalation: caught by the Ward itself on the 2nd and 3rd undetected success in separate samples (3rd always, per the table), or earlier by stock detection.
  - An undetected failed attempt leaves the Ward Unprimed; a detected failed attempt activates it, catches nobody, and the thief still rolls.
  - Blocked attempts and attempts refused before the roll leave the Ward's last-activity time unchanged; a genuine attempt moves it forward.
  - Hot Zone: a caught thief rolls normally and the Ward does not prime or activate.
  - Expiry in real time, 30-second sweep: Activated Wards consumed ("run its course") and a Primed Ward reset, about 30 minutes after their last genuine attempt.
  - Save/restart: Activated and Primed state, caught thieves and the block survive; remaining time carries across.
  - Probe: a regular Ward is Blessed to its holder only while tracking; moving it to another character resets it fully (Unprimed, Regular, no blessing); at 29 quiet minutes it stays Primed; past 30 the sweep resets it.
  - The dev-world copy, which holds Wards saved under the old model, loaded cleanly on the new build.

## Deploy and rollback
- The dev distribution holds the new build, config and ModernUO DLLs. The dev server was stopped and was not started.
- **Save format change is one-way** (`BackpackWard` version 3). Pre-change snapshot of the distribution and saves: `work/save-snapshots/dist-20261002-112035-pre-ward-b`. Restore it to roll back.
- Player-facing text: the root `README.md` Theft bullet now describes the caught-thief block.

## Readiness limits
- Stock detection (20% of thefts at Stealing 120) usually catches a thief within one to three successes, so the Ward's own roll decides some catches and stock the rest. Both feed the same block.
- Failed-attempt and expiry paths were tested with staff-set skills and, for expiry, a mix of real waiting and an aged-time probe.
- Wards still have no source beyond the starter grant. Whether to add one is a later economy decision.
