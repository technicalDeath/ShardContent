# Action progress bars (first: lumberjacking)

Owner, 2026-11-02: "give actions that take time a progress bar over the character. We'll start with lumberjacking to prove out the concept. When you start lumberjacking we'll show a small progress bar (big enough to fit text) above the character saying "chopping" that fills while the action completes."

Flag: `featureFlags.actionProgressBars`, **off** until the owner says activate.

## What a player sees

- A chop starts, and a small bar appears over the player's own head with **Chopping** written in it.
- The bar fills over exactly the attempt's length, then goes when the logs (or the miss message) arrive. Each attempt of auto-repeat starts a new bar.
- An attempt cut short between swings (the player moved out of reach, the tree ran out, the axe broke) clears the bar at that swing.
- Only the chopper sees the bar; other players see nothing new.

## How it is built

**The attempt's length is known at the start.** A stock attempt picks its swings when it starts: 1, 2, 2, 2 or 3 before AOS (`Lumberjacking.cs` `EffectCounts`). There is one swing every 1.6 s (`EffectDelay`), and the result follows the last swing's sound 0.9 s later (`EffectSoundDelay`, `HarvestSoundTimer`). So an attempt lasts 0.9, 2.5 or 4.1 s. Nothing about the attempt changes.

**Engine hooks** (ModernUO, `Engines/Harvest/Core`):
- `HarvestTimer.Count`: the swings this attempt picked.
- `HarvestSystem.AttemptTimed`: raised as an attempt starts, with its length (`AttemptDuration`: the swing interval times one fewer than the swings, plus the sound delay).
- `HarvestSystem.AttemptAborted`: raised when a swing *before the last* fails its checks. The last swing returns false from `OnHarvesting` too, to hand the result to its sound timer, so it is not a cut-short attempt. The first build missed this, and the bar vanished 0.9 s early every time; the owner saw it.
- Leftover case: if the last swing itself fails its checks, the stock code gives no signal, so the bar fills its last 0.9 s anyway.

**Shard** (`ActionProgressBars.cs`):
- Sends extended command **0xB4** to the player only: `0xBF`, length, `0x00B4`, serial (4 bytes), length in ms (2 bytes; 0 clears), label length (1 byte), ASCII label (at most 24 characters).
- `LabelFor` gives "Chopping" for `Lumberjacking` and nothing for any other system yet; a new action is one line there.

**Client** (ClassicUO `Game/Managers/ActionProgressBars.cs`):
- Drawn after the health bars in `GameScene.DrawUI`, centred over the head, worked out the way the stock overhead health text is.
- Dark background, amber fill, black border, white text with a black outline (unicode font 1). Width is the text plus 8 px each side (at least 64). The owner asked on 2026-11-02 for a tighter bar: it is 18 px tall (was 22), trimming 2 blank font rows top and bottom (`TRIM_Y`), so the letters' outline has 1 px of room. Real-client before and after: `work/player-client/ProgChop/shots/20261102-bar-height-before-after.png`.
- The full bar stays 200 ms, then goes. It is dropped when the mobile dies or leaves view, and cleared at login.
- A stock server never sends 0xB4.

Navrey does not read 0xB4. Bots need no bar.

## Evidence

| Check | Result |
| --- | --- |
| Engine: attempt lengths 1/2/3 swings = 0.9/2.5/4.1 s; a definition with no swing interval lasts its sound delay (`HarvestAttemptDurationTests`) | pass (4) |
| Shard: packet bytes, clear, label cap and plain text, length capped at 65,535 ms, only lumberjacking has a label, flag off (`ActionProgressBarsTests`) | pass, with the rules tests (33) |
| Live, disposable host `progress` on port 2594 beside the farm (engine and shard from the verification build, flag on): Navrey chop | logs arrive about 2.5 s after the target (a two-swing attempt) |
| Real client, first build | bar "Chopping" over the head, filling; the owner saw it vanish before full (the last-swing bug above) |
| Real client, after the fix | seven shots about 1 s apart: fill about 25%, 45%, 85%, then a fresh bar for the next repeat at about 10%, rising again |

Shots (real client, `work/player-client/ProgChop/shots/`): `20261102-144252-bar1.png` (first build, bar a quarter full), `20261102-fix-strip.png` (after the fix, seven crops in a row), `20261102-144525-fix1.png` (whole screen).
Host set-up: `work/progress-bars/setup.ps1`; staff on the client's character: `work/progress-bars/staff.py`.

## Bandaging (2026-11-02, owner: "add progress bar for bandaging, I'd like to see what that looks like")

- **Engine event** `BandageContext.Started(context, delay)`, raised as `BeginHeal` starts a bandage. The length is fixed then. Before AOS, on yourself it is 9.4 s + 0.6 × (120 − Dex)/10; on another it is 3, 4 or 5 s by Dex; resurrecting adds 5 s.
- **Shard:** the healer gets a "Bandaging" bar for that length. A new bandage replaces the bar of the one it cancels.
- **Real client** (Dex 100, so 10.6 s on yourself; the client's auto-use was applying the bandages): the bar fills over the bandage, goes when it heals, and a new bar starts with the next one.
- **Re-recorded with 90 Healing** (`bandaging2.gif`, as a player page at `bandaging-video.html`): 30 hit points out of 100, above the 25% potion trigger. The heal lands as each bar fills (+39 at 11.7 s, +61 at 22.5 s), and auto-use starts the next bandage at once. In the first recording the character had 0 Healing, so before AOS a bandage worked only 1 time in 10 ((Healing + 10) / 100), and a miss heals nothing ("barely help"). Its bars ended with no number, and the +10 in mid-bar was auto-use drinking a heal potion at 15 hit points. The owner caught it.
- **Seen in the shots:** the heal number floats up through the bar, because both sit over the head.
- **Video:** `work/progress-bars/bandaging.gif` (25 s, 5 frames a second, 10 MB, which was too large to show), re-sent as `bandaging-small.gif` (220 x 170 crop, changed-rectangle frames, 1.4 MB). It was made with `work/progress-bars/Record-PlayerClientGif.ps1` and `GifRecorder.cs`, which need nothing installed: screen frames, a palette per frame and a hand-written GIF encoder.

## State (2026-11-02)

- Built and checked live. Flag **off** in source. Nothing committed or deployed.
- **To deploy:**
  1. Rebuild UOContent into `Distribution` (new engine hooks), run the normal deploy, and bump the pin when the engine is committed.
  2. Copy the new `cuo.dll` into `ClassicUO/bin/dist`.
  3. Turn the flag on when the owner says activate.
- **Next actions** are a label each in `LabelFor`, once the owner picks them: mining and fishing would show at once, being harvest systems.

## Phase 1 (2026-11-02, owner: "Do phase 1 and show me video of it when done")

Plan: `Action-Progress-Bars-Plan.md`. Built with the flags OFF in source (`actionProgressBars`, new `gatheredItemPopups`); nothing committed or deployed.

**What changed**
- **Themes:** 0xB4 carries one more byte after the label, the theme (1-8, `ActionProgressBars.Theme`). The client keeps the owner's colours in `Fills`; a client without the byte, or a theme it does not know, keeps amber.
- **New bars:**
  - Mining ("Mining"; "Digging sand" for the sand definition) and Fishing, gathering amber, from the existing `AttemptTimed`.
  - Picking a lock, slate, 3 s; Cooking, blue, 5 s; Spinning, blue, 3 s. These come from the existing start events, with each length read from a stock constant the engine now makes public: `Lockpick.AttemptDelay`, `CookableFood.CookDelay`, `SpinningWheelEvents.SpinDelay`. The four wheels use the shared constant.
  - Chopping stays amber; Bandaging is green.
- **Gathered-item pop-up** (`GatheredItemPopups.cs`, command 0xB5):
  - Engine event `HarvestSystem.ResourceGained(system, from, HarvestedItem)`. It is raised after `Give` succeeds, for the main item and the bonus item. Type, art, hue and amount are read before `Give`, because a pile merges and is deleted. An item `Give` sent elsewhere (a fished-up map goes on a sea serpent) does not count.
  - The client draws the item's art in a 30 px box with "+N" on a faint dark plate. It starts above the bar, so auto-repeat's next bar does not cover it, then rises and fades over 1.6 s.
  - The owner asked mid-build: "Why does it say logs, its supposed to be an icon". The first build drew "Logs +10"; now the picture replaces the word. The name shows only for art the client lacks.
  - Options switch: "Show what you gather over your head".

**Tests**
- Shard: the full suite passes (1,940), including the new bar, theme and pop-up tests.
- Engine: focused UOContent run for harvest, bandage, lockpick, cooking and spinning.

**Live** (disposable host `progress`, port 2594, both flags on, real client; recordings in `work/progress-bars/phase1-*.gif`; joined video `phase1-all.gif`, page `phase1-video.html`):

| Action | Seen |
| --- | --- |
| Chopping a cedar | Amber bar every 0.9-4.1 s; log picture "+10" above it on each success until the tree ran out |
| Mining a rock outcrop | Amber "Mining" every 0.9 s; ore picture "+1" (both ore colours seen); two gains stack a line apart |
| Fishing from the bots' stand at 1441,1739 | Amber "Fishing" 8 s; fish picture "+1" on a catch, nothing on a miss |
| Picking a lock | Slate "Picking lock" 3 s, then "the lock quickly yields" |
| Cooking ribs on a firepit | Blue "Cooking" 5 s per rib, repeating |
| Spinning wool | Blue "Spinning" 3 s per pile, repeating |

**Seen while testing, not caused by this change:**
- A pack over the backpack's own 400-stone cap loses mined ore ("Your backpack is full, so the ore you mined is lost") and stops fishing ("You are carrying as much as you can"). The pop-up correctly stays silent then.
- A chest behind a wall ("Target cannot be seen") and a greyed Mine on high rock both refuse before any bar.

## Phase 2 (2026-11-02, owner: "Yes and yes, and make sure all bars clear if an action is canceled")

Built with the flags OFF in source; nothing committed or deployed.

**New bars**
| Action | Label | Theme | Length | Engine |
| --- | --- | --- | --- | --- |
| Crafting from any craft menu | by the craft: Smithing, Tailoring, Carpentry, Fletching, Tinkering, Grinding (alchemy), Inscribing, Drawing a map, Cooking, Glassblowing, Carving stone | blue | 1.25 s (`CraftEvents.CraftDuration`: the timer ticks at once, then every `CraftSystem.Delay`) | new `CraftEvents.CraftStarted` in both `CraftItem.Craft` paths |
| Flour mill | Milling | blue | 5 s | new `FlourMillEvents.GrindStarted` (east and south mills) |
| Taming | Taming | teal | 9 or 12 s (3 or 4 steps of `AnimalTaming.StepDelay`, picked at the start) | new `AnimalTaming.AttemptTimed` |
| Poisoning | Poisoning | red | 2 s (`Poisoning.PoisonDelay`) | new `Poisoning.PoisonStarted` |

**What you made pops up too** (owner said yes): `CraftEvents.Crafted` raises the made item before it goes into the pack, and `FlourMillEvents.FlourGiven` raises the sack. Both reuse 0xB5, so the client draws the item's picture and "+1". The Options switch now reads "Show what you gather or make over your head".

**Every bar clears when its action is cut short** (owner: "make sure all bars clear if an action is canceled"). Each cut-short path was checked in the engine:
| Action | How the stock code cuts it short | Bar |
| --- | --- | --- |
| Chopping, mining, fishing | a swing fails a check: tool, target, range, resource gone | `AttemptAborted` is now raised at every failed check in `OnHarvesting`, the last swing included (before, only between swings). A failed check at the end (`FinishHarvesting`) is the result itself, with its own message, and the bar is already full there. |
| Bandaging | replaced by a new bandage, or stopped by shard code (being knocked out) | new `BandageContext.Stopped` from `StopHeal`; the finishing tick no longer goes through `StopHeal` |
| Crafting | the crafter can no longer act (frozen, paralysed, dead) | new `CraftEvents.CraftCancelled` |
| Taming | out of range, dead, no path, already tamed, angered, and so on | `AttemptEnded` with `Aborted` |
| Lockpicking, cooking, spinning, milling, poisoning | the stock code has no way to stop these before their result | nothing to clear; the result ends the bar |
| Any action | the player dies, or the mobile leaves the world | the client drops the bar |

**Tests**
- Shard: the full suite passes (1,950), including craft labels and durations, the taming, poisoning and mill lengths, the clear packet, and the craft pop-up names.

**Live** (host `progress`, real client; recordings `work/progress-bars/phase2-*.gif`, joined video `phase2-all.gif`, page `phase2-video.html`):
- Crafting a foot stool: a blue "Carpentry" bar for 1.25 s, then the stool's picture and "+1".
- Milling: a blue "Milling" bar for 5 s, then the flour sack's picture and "+1".
- Taming a horse: a teal "Taming" bar over the attempt; the horse was tamed ("It seems to accept you as master").
- Taming cut short: the tamer was moved out of range mid-attempt, and the bar cleared at the next taming step.
- Poisoning a dagger: a red "Poisoning" bar for 2 s.

## Phase 3 (2026-11-03, owner: "Do phase 3")

Built with the flags OFF in source; nothing committed or deployed.

**New bars**
| Action | Label | Theme | Length | Engine |
| --- | --- | --- | --- | --- |
| Making camp (within 7 tiles of a burning fire) | Making camp | rose | 30 s (`Campfire.SecureDelay`), from the fire's first poll after you arrive | new `Campfire.EntryStarted` / `EntryEnded`, `CampfireEntry.Secured` |
| Digging up a treasure chest | Digging | amber | 25 s (`TreasureMap.DigDuration`: the dig timer ticks at once and then every second; the chest appears 15 below ground at the eleventh tick and rises one a tick) | new `TreasureMap.DigStarted` / `DigStopped` |
| Begging | Begging | slate | 2 s (`Begging.BegDelay`) | new `Begging.BegStarted` |

**The camp bar and the shard's own camp timings agree.** The stock camp is secure 30 s after a player's entry (which bedroll logout needs); camp travel calls a fire secure 30 s after it is lit (`campTravel.secureSeconds` 30.0), and the Welcome guide says 30 seconds (`WelcomeGuide.SecureCampSeconds`, pinned to `Campfire.SecureDelay` by a test). For the player who lights the fire the two start within a second of each other.

**Cut short**
| Action | How the stock code cuts it short | Bar |
| --- | --- | --- |
| Making camp | the player moves more than 7 tiles off, the fire burns down to embers or goes, or the player logs out, before 30 s | `Campfire.EntryEnded` with `Secured` false clears it; an entry that ends after the camp is secure clears nothing |
| Digging | moving, another skill, spell or action, something on the chest's spot | `TreasureMap.DigStopped` from the dig timer's `Terminate` |
| Begging | none: the bow always ends in a result | nothing to clear |

**One bar per player, and a clear takes only its own** (superseded the same day by stacked bars, below). The server now remembers the last bar it sent each player (label and end time). A clear is sent only while that bar is still the stopped action's and still running (`ActionProgressBars.Clears`), so a camp left half made does not take away the chopping bar of a player who went on to chop, and a harvest swing refused while the camp bar runs does not take the camp bar. Every phase 1 and 2 clear now goes the same way.

**Tests**
- Shard: the full suite passes (1,953), including the camp, dig and beg lengths, the camp bar pinned to the Welcome guide's 30 seconds, and the label-scoped clear.
- Engine (UOContent, `Harvest|Bandage|Craft|Tam|Poison|Flour|Camp|Treasure|Begging`): 53 pass.

**Live** (host `progress`, real client; recordings `work/progress-bars/phase3-*.gif`, joined video `phase3-all.gif`, page `phase3-video.html`, published at https://claude.ai/artifact/9VGcrGJjwhLtXvqCbh9wx1; frame sheets `sheet-*.png`):
- Making camp: kindling lit (the camp-travel blue fire), a rose "Making camp" bar for 30 s; it ends with the stock "The camp is now secure" line and the secure-camp buff icon. Camp travel's own "Your camp is secure" line comes about a second earlier, from the fire's age.
- Making camp cut short: an already-secure player leaves and nothing is cleared; back in range a new bar starts; moved off again after about 8 s, the bar goes at once.
- Digging: a decoded level 1 map, a shovel, Mining 100: an amber "Digging" bar for 25 s, ending as the chest is fully up. The fire burning out during the dig did not touch the dig bar.
- Digging cut short: one step away mid-dig gives the stock "You cannot move around while digging up treasure" line and the bar goes at once.
- Begging: a peasant, Begging 100: a slate "Begging" bar for 2 s, then "I feel sorry for thee..." and the gold.

## Stacked bars (2026-11-03, owner: "Now we need bars to stack when multiple are up, so they don't overlap")

**What a player sees.** Each action has its own bar. Bars of actions running at once stack upward from the head in the order they started, the oldest nearest the head, 4 px apart. A bar started again for the same action (the next swing of auto-repeat) keeps its place. A bar that ends or is cut short goes, and the bars above step down into its place. Gathered-item pop-ups start above the whole stack (counted when the pop-up starts, at least one bar's room), so no bar covers them.

**How it is built.**
- Client (`Game/Managers/ActionProgressBars.cs`): the bars are kept per mobile as a list keyed by label. 0xB4 with a length starts or restarts that label's bar; a length of 0 takes away that label's bar only. A clear labelled "-" or with no label (what the server sent before) takes all of that mobile's bars. `STEP` (22: an 18 px bar and its 4 px gap) is what `GatheredItemPopups` leaves for each bar.
- Server (`ActionProgressBars.cs`): it remembers every running bar per player by label (`Dictionary<string, DateTime>`, run-out entries dropped as new ones come). A clear goes only while that label's bar still runs, and it now carries the label, so the client takes away that one. The 0xB4 layout is unchanged.
- Nothing in the engine changed.

**Tests.** The full shard suite passes (1,953), including the per-label clear (`AClearTakesAwayOnlyTheBarOfTheActionThatStopped`, now with two bars up) and the clear carrying its label (`AClearNamesTheBarItTakesAway`).

**Live** (host `progress`, real client with the new `cuo.dll` in `work/progress-bars/dist`; old one kept as `cuo.dll.before-stack`):
- Two bars: kindling lit (rose "Making camp"), then the character hurt so the auto-use bandage starts: green "Bandaging" stacks above the camp bar, with no overlap. The camp secures at 30 s, its bar goes, and Bandaging steps down next to the head. Recording `work/progress-bars/stack-two.gif`, frame sheet `sheet-stack.png`, still `stack-two-bars-zoom.png`.
- Cut short mid-stack (`work/progress-bars/stack_cancel.py`): camp lit at 1442,1633, bandage started above it, then the character moved 10 tiles off before the camp was secure. The camp bar went at once, and Bandaging stepped down and ran on to "You finish applying the bandages". Recording `stack-cancel.gif`, frame sheet `sheet-stack-cancel.png`.
- Joined video `stack-all.gif`, page `stack-video.html`, published at https://claude.ai/artifact/5rYz3p3LjxCEGqCYXWqRzk.
- Seen in passing: the heal number ("+32") floats up from the head through the stack, as it did through the single bar The owner chose to leave it as it is (2026-11-03).

**Spellcasting gets no bar** (owner, 2026-11-03: "let's also skip spellcasting - no bars for it"), so phases 1-3 are the whole feature.

## Deployed (2026-11-03)

Owner, 2026-11-03: "you can commit, deploy, push, etc". Committed and pushed: ModernUO `67b29ab34` (the timed-action events and the equip
request handler), ShardContent `766a954` (pin bumped to it), ClassicUO `da3966573`. Full verification before the commits: UOContent 1,412
passed, shard 1,953 passed (run `20261103T171433959Z-657dc3`). Deployed to dev with `actionProgressBars`, `gatheredItemPopups` and
`dragIntoHands` OFF, after the snapshot `work/save-snapshots/saves-20261103-121627-before-progress-bars-deploy`; a disposable copy of the
deployed dev world loaded cleanly (57,867 items, 13,078 mobiles). The new `cuo.dll` is in `ClassicUO/bin/dist`; the old one is in
`work/cuo-backups/cuo-20261103-121722-before-progress-bars`. The farm host was not touched. Turning the bars on is the owner's call.
