# New-player help messages: the candidate list

Written 2026-10-11 at the owner's request ("a list of QoL help improvements in line with the bedroll info and poison info ... just some helpful little messages here and there would go a long way"). It is the first pass of the "tell the player what they can do" item in `To-Do-List.md`. **Nothing here is built or approved.** Each entry says when the player needs it, what the game does today (checked in the code unless marked *to verify*), the proposed text, and how it would be delivered. Wording is a draft for the owner to change.

## What already exists (not repeated here)

The `[Welcome` guide (Your first hour, Skill locks 101, Training, Money and shops, Crafting, Gathering and repeats, Camping, Pets, Dying, the criminal and Hot Zone pages), the buff bar (Poisoned and the new bandage line, Faint Memories, Ward, Intent and the rest), the Hot Zone travel warning, the pet-leaves-the-dungeon notice, the camp fire lines, the poison hint and the grace-window line (live since 2026-10-11), and the camp-secure line with the Bedroll how-to. **The guide says nothing about bandages, stamina, poison or the Journal**, and its Bedroll sentence is on the Camping page only.

## The shape every entry follows (one rule, so it feels like one voice)

- **Say it when it matters, once.** Shown the first time the situation happens to a character, then never again for that character (an account tag per hint, as the poison hint does).
- **Say what to do, not what is wrong.** Name the action: "double-click a bandage, then click yourself".
- **One or two plain sentences,** second person, no jargon, no numbers a player cannot use. Point to `[Welcome` only when a page really covers it.
- **A player switch.** `[Tips off` (and `on`) turns them all off for that character; staff never see them.
- **One flag, one table.** A `newPlayerTips` flag (off until the owner says activate) and one registry (id, trigger, text, once per character) so the wording lives in one place and each hint is unit-tested against the rule that triggers it.

## Tier A: client text only, minutes each, no server code, always on

The client already prints these lines; the shard can replace the text through `Data/Client/Clilocs.txt` (how the camp-secure line was done). They show every time, so they must be short and always true.

| # | Situation | Today | Proposed text |
| --- | --- | --- | --- |
| A1 | A bandage works poorly or not at all (`500968`) | "You apply the bandages, but they barely help." Healing 0 gives about 1 success in 10; it shows for a failed roll or a heal cut to under 1 by slips. Nothing says why. | "You apply the bandages, but they barely help. Healing skill decides how often bandages work, and every bandage you finish can raise it." (Checked: finishing a bandage tests both Healing and Anatomy for gain.) |
| A2 | The player is hit while bandaging (`500961`) | "Your fingers slip!" Each slip cuts the heal by 4 hit points before the 1-point floor. | "Your fingers slip! Being hit while you bandage makes the bandage heal less." |
| A3 | Bandaging a full-health target (`500955`) | "That being is not damaged!" Fine, but a new player training Healing does not know to find a wounded target. | "That being is not damaged. Bandages need someone hurt: a wounded friend, pet or yourself." |

## Tier B: one-time tips from a small watch, the same shape as the poison hint

Each needs a trigger the shard can already see (a once-a-second watch over online players, or an existing shard hook), plus the registry above.

| # | Situation | Today | Proposed text | Trigger |
| --- | --- | --- | --- | --- |
| B1 | **Out of arrows** | An archer with no ammunition keeps "swinging" and nothing happens, with no message (`BaseRanged.OnFired` returns false silently; seen in a live test). Arrows that miss lie on the ground where they fell; some that hit end up on the monster. | "You are out of arrows. Arrows that miss fall to the ground near the target, so pick them up, or buy more from a bowyer." | A bow equipped, war mode on, no arrows in pack or quiver, at most once a minute after the first time |
| B2 | **Badly hurt, bandages in the pack** | Nothing tells a new player how to heal. | "You are badly hurt. Double-click a bandage, then click yourself to heal. It works better the higher your Healing skill is." | Hits under a third, in combat, a Bandage in the pack, never shown before |
| B3 | **Poisoned, with cure potions in the pack** (an upgrade to the live poison hint) | The hint names the potion but not that the player already holds some. | "You are poisoned, and you have 5 Lesser Cure potions: double-click one to drink it. It may take a second try." (The potion cures Lesser poison 75% of the time.) | The existing poison hint, wording chosen by the pack |
| B4 | **First death** | The `Dying` page covers it; the moment itself says only that you are dead. | "You have died. Go to a healer in town, or ask another player to resurrect you, then take your things from your corpse. Your starting gear stays with you." | The player-death event the shard already hooks |
| B5 | **First resurrection** | The corpse and its timing are only in the guide. | "Your belongings are on your corpse. It turns to bones after about seven minutes and is gone about seven minutes after that, so go back for it soon." (The timings are from the Dying page audit.) | Resurrection |
| B6 | **First log-off away from a safe place** | A normal logout leaves the character standing where it was for the region's logout delay and it can be attacked; your own house (as owner or friend, with no recent fight), a Bedroll at a secure camp, and any region flagged no-logout-delay with no fight on you skip it (which regions carry that flag was not checked, see C6). Nothing says so at the moment. | "When you log out here your character stays in the world for a few minutes and can be attacked. Log out in your own house, or at a secure camp with your Bedroll." | The first login, and the first time the player is far from any town; the Log Out button itself cannot be intercepted without an engine hook |
| B7 | **First time carrying a lot of gold** | A thief can take it from the pack, not the bank. | "Gold in your pack can be stolen; gold in your bank box cannot. Say 'bank' next to a banker to put it away." | Pack gold first reaches about 2,000 |
| B8 | **First time a pet is tamed** | The pet-feeding rule is on the `Pets` page only: a tamed pet loses 10 of 100 loyalty every hour and is released at 0; feeding it food it likes can raise it by 10 per item. | "Your new pet gets hungry. Feed it food it likes now and then (double-click the food, then click the pet), or it will wander off after about ten hours." | Taming success |
| B9 | **The first long hint** | System messages fade in a few seconds; the poison hint and these are long. | One extra line the first time any hint is shown: "Messages fade quickly. The Journal button at the top keeps them." | The first hint of any kind |
| B10 | **Low stamina in a fight** | Swing speed depends on stamina (and running costs it); the shard's novice floor hides it for new characters, but not for anyone past it. Nothing says so. | "You are tired, so you swing more slowly. Stand still for a moment to get your wind back." | Stamina under a quarter, in combat, never shown |

## Tier C: needs a decision or an engine hook

| # | Situation | Why it is not Tier B | What to do |
| --- | --- | --- | --- |
| C1 | **Skill stops rising from the same spot** | The stock anti-macro limiter refuses repeat gains at one location or target and says nothing, so a new player thinks the skill broke. The engine returns false silently. | A small engine hook that reports the refusal, then "You are not learning anything new here. Move to another spot, or try a different target." Needs the settings (location size, allowance) checked first. |
| C2 | **Becoming a criminal** | The planned Tier 1 item B ("You are a criminal for 2 minutes") is not built. | Build it with B's confirm prompts for helping a grey or looting a blue's corpse. |
| C3 | **House lockdown reminder** | On the list already (owner, 2026-10-08), with its own once-a-day shape. | Fold into the registry as one more entry once the registry exists. |
| C4 | **Hot Zone entry on foot** | There is a "you have left" line (`OutdoorHotZoneBoundaryService`) and the travel warning for Recall, gates and camp travel. Walking in is only the boundary service's entry line, if any. | Check what an entering player reads, and add a one-time "you are in a Hot Zone: blue players can attack each other here" if it is missing. |
| C5 | **The logout moment itself** | The Log Out button disconnects at once; the shard cannot say anything then. | Rely on B6 and the guide; or a staff-free engine hook before the disconnect (only if B6 proves not enough). |
| C6 | **Inn logout** | *To verify:* the code makes a region logout instant only for its own flags; whether the Britain inns count was not checked. | Check, then add to B6's text if true. |

## Suggested order

1. **Tier A (A1 to A3)** now: three lines in `Clilocs.txt`, no code, checked in the real client by lighting a bandage fight with a fresh character.
2. **The registry and `[Tips`**, with **B1, B2, B3 and B4** first (the ones a new archer or warrior meets in the first hour), then B5 to B10.
3. **Tier C** as each decision is made; C2 and C3 are already on the list.

## Open questions for the owner

1. Is "once per character, with a `[Tips off`" the right shape, or should some of them repeat (B1, out of arrows, is the likeliest to be wanted every time)?
2. Should the tips show for a veteran's new alternate character too, or only the account's first? (A per-account tag would show them once per account.)
3. Wording: any change to the voice, and whether to name skills and numbers ("Healing 60") or keep them plain.
4. Is B6's text acceptable (it tells new players their sleeping character can be attacked, which is true and unlike a safe-logout world)?
