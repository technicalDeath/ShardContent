# New mage playtest: what a new player runs into

**2026-10-14.** The assistant played a brand-new Pure Mage (template 11, still Young, no staff help except where noted) for about two hours with a bot that grows a decision tree each time it meets something it cannot handle: `tests/scenarios/new-mage-playtest/mage_bot.py` (run it with `run_bot.ps1`; raw findings go to `work/mage-playtest/notes.jsonl`, the run log to `run.log`). Nothing here has been built or approved; it is a to-do list for the owner to rank.

Character at the start: 74 hit points, 39 mana, Magery 50, Evaluating Intelligence 35, Resisting Spells 35, 500 gold, carrying 130 of 208 stones. Host: a disposable copy of the deployed build, Britain, Felucca.

## What the bot does now (the tree)

Each tick the first rule that acts wins: `r_dead` (walk to the healer as a ghost and accept the offer) > `r_flee` (low health: heal, drink, run) > `r_avoid` (a monster that is not safe prey: fight it from range if there is mana, else step away) > `r_heal` > `r_fight` (magic arrow at safe prey, keep distance) > `r_loot` > `r_resupply` (out of reagents: walk to the mage shop, open the vendor's list, buy) > `r_train` (ask the guild trainers what they teach) > `r_hunt` (walk up to prey) > `r_rest` (heal, Meditate) > `r_explore` (a ring of waypoints, skipping places that have killed it, remembered in `knowledge.json`). Each rule is there because a run got stuck or died without it: the file's header lists them in the order they were added.

## The list

Priority: **A** a new player is likely to die, quit or get stuck without it; **B** wastes a lot of time or confuses; **C** polish. "Evidence" says how it was seen.

### Survival

1. **A. The west road kills a level-one mage and nothing warns about it.** Within about 150 tiles of the Britain gate toward the north-west there are orcs, ratmen, trolls, harpies, bears and a panther; the bot died there more than ten times (positions in the run's death notes, around 1300,1485 and 1330,1559) before it learned the places and stopped walking to them. Idea: a "Where to hunt" page in the Welcome guide's Your first hour (rats, birds, rabbits and hinds just east and south of the town are safe; the north-west wilds are not), beginner hunting grounds as markers in `UORekindled-Britain.csv`, and an overhead warning (or a one-time tip) the first time a player is within a few tiles of a monster that is far stronger than they are. Effort: a day for the text and markers; the warning is a client feature.
2. **A. Monsters follow a new player into Britain and nothing in town stops them.** An orc-like ratman ("Chickeki"), a troll, a harpy and a brown bear each chased the mage inside the walls, once into the square beside the healer (1463,1612). No guard was within 14 tiles of the healer in any check. This also threatens a ghost who walks to the healer. Idea: guards attack monsters that come inside the town (stock guard behavior needs checking), or monsters stop at the gate. Evidence: bot log "cornered by ..." lines at 1469,1619. Needs a design ruling (it changes how Britain plays).
3. **A. A resurrected mage comes back at 10 hit points and about no mana, in the street.** It then rests for about four minutes; every Heal costs mana it does not have. Idea: say what to do on the way back ("Rest or use Meditation; the healer's street is safe"), and consider coming back with more health. Evidence: the log's `resting: mana 1/40, hp 10/74` and the 3 to 4 minute recovery.
4. **B. A ghost is told how to get back, but not where the healer is.** The bot only walked to the right place because it was given the coordinates. Idea: the ghost strip (which already shows the way to the body) also names the nearest healer and points to it; the Britain map already marks "Healer (resurrects you)" at 1471,1611. Evidence: `r_dead`; the offer then opens by itself as a Resurrection gump (CONTINUE or CANCEL) when the ghost is within a few tiles of the healer, which worked.
5. **B. Low-health options for a mage with no mana are unclear.** At 20 to 30 percent health with 0 mana the bot could only run. The starter potions are shown as colors in the headless client; in the real client the potion bar and tooltips name them, so this may be fine for a human, but the bot could not tell which potion heals and lost hit points trying (+3, 0, -7, -3, -10 in five drinks, partly monster hits). Check that the potion bar and the first-time tip make "Heal potion at low health" obvious for a mage (the `autoUse` Heal potion switch helps if it is on).

### Reagents, mana and money

6. **A. The starting reagents last about 30 casts, then casting stops with only "More reagents are needed for this spell."** The bot's starting bag held roughly 30 each of Garlic, Ginseng and Spider's Silk and 30 Sulfurous Ash (what Magic Arrow uses); it was out after about three minutes of hunting. Nothing says where to buy more. Idea: a one-time tip when any reagent is down to 5 ("Reagents are sold at the Mage shop in Britain, about 3 gold each: 1485,1550"), and make the message itself name the missing reagent. Evidence: `[SAY] MageP: More reagents are needed for this spell.`
7. **B. The Mage shop works, but the way in is hidden.** In the headless client the shop opened by saying "<vendor name> buy" next to the shopkeeper (Lauryn); prices: Sulfurous Ash, Spiders' Silk, Nightshade, Mandrake, Ginseng, Garlic 3 gold each, Blood Moss and Black Pearl 5, empty bottle 5, potions 15 to 21 gold. The bot spent 408 of its 500 gold in one visit because it bought 20 of everything. Idea: a "Shopping" line in the guide ("double-click a shopkeeper or say its name and buy"); check what the real client does on a double-click.
8. **B. Mana runs out after about nine Magic Arrows and the way to get it back is not mentioned.** Meditation is there (14 at the start, it trained to 29 in half an hour) and brings mana back much faster than waiting, but nothing tells a new mage. Its failure message, "You cannot focus your concentration.", is also unexplained: it appeared when something hostile was near or the mage had just been hurt. Idea: a first-time caster tip when mana first drops below a quarter ("Meditation: use it while nobody is around to get mana back faster"), and say why it fails ("...with an enemy so close").
9. **C. "You must wait a few moments to use another skill."** Meditation repeated within about ten seconds gives this; harmless, but a player spamming the skill sees it constantly. Check the wording against the era's.
10. **B. The spell bar opens on Circle 6.** In the real client a brand-new mage with Magery 50 gets a bar of eight 20-mana, high-circle spells (screenshot `work/player-client/MageP/shots/20261014-162401-first-screen.png`); `SpellBarGump.HighestCastable` picks the highest circle the skill allows, but a new mage has few mana, few reagents and, as far as the bot could see, a book of early spells. A new player will click these and watch them fail. Idea: open on the first circle with spells the character can actually cast (mana and reagents), or on Circle 1; mark spells that are not in the book.

### Time wasters and noise

11. **B. Every vermin kill opens an empty corpse window.** Rats, birds and the like drop nothing; each corpse still opens by itself (the auto-open default), and the bot logged `corpse ...: []` for almost every kill. The client has a "skip empty corpses" switch that is off. Idea: turn it on in `default-profile.json` (the key is `skip_empty_corpse`, confirmed in a real `profile.json`; the defaults doc's test pins such names).
12. **C. Weight.** The mage starts at 130 to 160 stones of 208 (about three quarters): eleven potions, three scrolls, a bedroll, kindling, a candle, scissors, a recall rune, bags. Not a problem while walking, but a hunt that picks anything up fills the pack. Idea: look at what a mage really needs on the first day (the `StarterWeightBudget` doc already has the budget).
13. **C. The trainers: three of three had nothing for the mage's own skills.** At the Mage shop the Guildmaster-area people offered Inscription, Wrestling, Alchemy and Taste Identification; one (Merill) said nothing at all when asked to train. Magery, Evaluating Intelligence, Meditation and Resisting Spells were not offered (the shard's rule is that a trainer teaches while you know less than a third of what he knows, so the mage is past that for Magery and Resisting; Meditation was at 14 to 29 and still not offered). Idea: make the silent trainer say "I have nothing to teach you", and check whether Meditation should be trainable at 14.

### Not findings (checked and fine)

- Death and recovery work without staff: the ghost walked about 100 tiles to the healer in under a minute and the gump accepted.
- Magic Arrow and Heal cast and train; shop prices and stock are sensible.
- The Welcome guide opens on `[Welcome` with a first-hour page; its text could carry items 1, 6, 7 and 8 above without any code.
- The "Generic Player" grey character the bot kept seeing was the staff test account, not a game problem.

## Things the bot could not or did not cover

Night and darkness (Night Sight), the bank, the second circle onward (the mage never gained the skill to unlock more), a second character in a party, theft, and the real client's own screens beyond the first one. Each would be a new rule in the tree.

## Suggested order

First the no-code items (1, 6, 7, 8 as guide text and map markers), then the reagent and Meditation first-time tips (6, 8), the spell bar default (10), the empty-corpse default (11), and the design rulings the owner has to make (2, 3). Nothing here is activated or planned; say which to take on and I will write the work plans.
