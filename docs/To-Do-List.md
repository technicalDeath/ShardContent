# To-do list

The owner's running list of things to plan and build. Nothing here is signed off or built unless it says so. Each item gets a plan and the owner's sign-off first (`beta-feature` workflow); every flag stays off until the owner says "activate". Newest additions first.

## In progress

- **Mastery from 80, layered on ordinary gain** (owner's idea, 2026-10-08; signed off and built 2026-10-09). Plan `Mastery-Layered-Plan.md`, evidence `Mastery-Layered-Evidence.md`. Guaranteed daily gains from Adept (80) on top of ordinary chance gain: casual Grandmaster in 10 / 15 / 20 / 25 days (Easy / Standard / Hard / VeryHard; allowances 2.0 / 1.4 / 1.0 / 0.8), chance gain from 80 at 0.1 of each class's rate, Faint Memories stops at 80. Unit tests, a live run on a disposable host, real-client pictures and a text audit are done. **Committed (`270c94b`), pushed and deployed to the dev host 2026-10-09** (no flag: the deploy activates it; README updated). Open for the owner: no skill is in the VeryHard class today, so the 25-day tier is empty; the website's Mastery copy is changed only when asked.

- **Guild chat** (Tier 1 G). Signed off, built and verified 2026-10-08 (unit tests, 38 live checks, six real-client pictures), flag `guildChat` ON. Committed, pushed, deployed and activated 2026-10-08 (the engine hook went in with it). `Guild-Chat-Plan.md`, `Guild-Chat-Evidence.md`.

## Added by the owner

- **A quality-of-life pass on telling the player what they can do and how to do it** (added 2026-10-08, the owner's words: "a pass on the quality of life category: telling the player what they can do and how to do it"). *Not planned yet.* In plain terms, a discoverability pass: find what a player cannot find out today and say it, in the right place, once. What already exists, to build on and not repeat: the `[Welcome` guide (it opens by itself for a new character; chapter tabs, "Your first hour", "Skill locks 101", Training, Money and shops, Crafting, Gathering, Pets, Dying, and a Commands page that lists only what is switched on), the status windows (Intent, Travel warning, Ward, Skill Bank, Mastery), the buff icons and the lines the lighter or traveller reads. Things to settle in the plan: who it is for (a brand-new player, a returning one, or both); an audit of every command, window and hidden mechanic against how a player would learn it (a list with "how would they find out?" beside each); where a hint belongs (the guide, a journal line, an overhead hint, a window, a one-time first-use tip, the item's own tooltip); a shared rule for how often a hint repeats (the house lockdown reminder below wants "about once a day" and a switch to turn it off, the same shape); wording in one voice; and how to tell it worked. Overlaps to fold in: the Tier 1 items A (guide pages, built) and B (the criminal notice), the Welcome page's "choose a topic" pointers, and the house lockdown reminder, which is the first hint of this kind.
- **House lockdown reminder** (added 2026-10-08). A player who is in a house they own, puts an item down, and does not lock it down or secure it within about 10 seconds gets a reminder to do so. A cooldown keeps it from nagging: about once a day. *Not planned yet.* Things to settle in the plan: the cooldown per account or per character (the travel warning is per account); which items count (a lone item on the floor, not a container that is already secure, not trash or a placed addon); co-owners and friends (the request says "a house they own"); whether it also reminds for items put in an unsecured container; the words; a way to switch it off. What stock gives: `BaseHouse.LockDown(mobile, item)`, `AddSecure(mobile, item)`, `IsOwner`, `IsInside`, but the engine event for "an item was just dropped in a house" has not been looked for yet (it may need a narrow hook).

## Quality of life (Tier 1 plan, `Tier-1-QoL-Plan.md`)

- **B. Accidental-crime guard rails and the criminal notice:** confirm prompts before helping a grey or red or looting a blue's corpse, and a "you are a criminal for 2 minutes" notice. Needs one small engine hook and a flag; waits on the owner's answers.
- **C. Rest of the client defaults:** a starter macro set, top-bar cleanup, default options. Needs a client rebuild; waits on which defaults and macros.
- **D. Assistant negotiation:** block looping macros, autoloot, restock and auto-bandage agents. An owner policy (a client that never answers is kicked); waits on the disallow list.
- **E. Help channel:** turn chat on with two channels or hide the dead buttons. Waits on a decision.

## Features

- **Crafting "make this many"** (the agreed next item after the action repeat; also Beta 2d).
- **Era cooking Part B:** dough and baking.
- **Beta 2b:** house zoning (`housingGeography`) and the rotating Hot Dungeon (`coolZones`), then persistent camp fires, camp stalls and hearths.
- **Beta 2c:** Expeditions, cargo, Pilgrimage, roads, Nemesis, Salvage, Wanted.

## From the research (`Quality-of-Life-Research.md`), not planned

- Anti-macro decision (now that the repeats are on); pet auto-release outside dungeons; party corpse default; death information.
- Moved up by the owner's 2026-10-07 ruling: tooltips, a BOD book, a Salvage Bag, refuse-trades, craft-window usability.

## Rulings still wanted

- Same-guild members can attack each other under Safe World (`IsGuildWarOrDuel` counts the same guild as allowed).
- Whether the camp-travel blue fire's Frostbite colour is acceptable at night (it reads pale green-yellow); the hue is one number, `campTravel.fireHue`.
