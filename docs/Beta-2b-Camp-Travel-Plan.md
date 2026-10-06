# Beta 2b item 4: Camp travel and the Hot Zone travel warning, plan and evidence

Status: **built and verified live 2026-10-06 (signed off with the owner's own capacity table, then extended by two owner requests during the build); committed locally, not pushed or deployed. `campingTravel` and `hotZoneTravelWarning` stay off for the owner's separate acknowledgments.** Readiness: [Beta-2b-Camp-Travel-Readiness.md](Beta-2b-Camp-Travel-Readiness.md). Origin: the owner's idea (2026-10-05) that party members can travel to your campfire once it is secure; recorded in the roadmap as its own Beta 2b item with guardrails. Builds on the shipped camping core ([Beta-2b-Camping-Readiness.md](Beta-2b-Camping-Readiness.md)).

> **Superseded in part by two later owner rulings (2026-10-06, recorded at the end of this document):** criminals and murderers **may** use camp travel (only recent player combat stops them), and the shard is named **UO Rekindled** in everything a player reads. Where the design below says a criminal or murderer cannot travel, the ruling wins.

## Goal and exit criteria

A party member can travel to a party member's secure campfire under strict guardrails. Exit: every refusal below is covered by tests and verified live; the feature is behind its own flag, off until the owner acknowledges it; the owner has ruled each part. (The plan expected no ModernUO change; the destination rule and the Hot Zone confirmation each needed a small hook, see the work breakdown.)

## Vision and constraint check (done before design)

- **Vision** ("a single world where deliberate systems concentrate the population... draw players into contact... new reasons to travel"): the destination is a camp, a deliberate gathering point, so it concentrates people. The risk is the opposite clause: a free teleport removes reasons to travel. The guardrails (secure camp, party only, Kindling cost, long cooldown, no escape hatches) keep it a regroup tool, not a travel network.
- **Seven constraints:** classic and no power creep (limited, costly, no combat or PvP gain); thieves, criminals and murderers kept (they cannot use it, so it is no escape route, and it never protects anyone from theft); concentrates population and contact (yes); every playstyle (anyone can light a fire at 50% or better, so no skill gates it); doable alone or in a small group (a party of two works); each role has its own on-ramp (the host needs only a fire, the traveler only Kindling); roles together make each other better (a camp is worth being at).

## Current state (read from the code)

Stock already defines what "travel" means here, and the plan reuses it instead of inventing rules:

| Stock rule (Recall) | Where | Reuse |
| --- | --- | --- |
| Region rules for the origin and the destination (Felucca dungeons, T2A, special areas) | `SpellHelper.CheckTravel(caster, map, loc, RecallFrom / RecallTo)` | Called for both ends |
| A criminal cannot travel ("Thou'rt a criminal and cannot escape so easily") | `Mobile.Criminal` | Same refusal |
| No travel within 30 s of player-versus-player combat | `SpellHelper.CheckCombat` | Same refusal |
| No travel while overloaded | `StaminaSystem.IsOverloaded` | Same refusal |
| Destination tile must be open and not inside a house | `Map.CanSpawnMobile`, `SpellHelper.CheckMulti` | Same checks on the arrival tile |
| Pets travel with the caster | `BaseCreature.TeleportPets` | See question 3 |

Shard rules to add: neither end in a Hot Zone (`OutdoorHotZonePolicy.IsHot`), not Knocked Out (`KnockedOutService.IsKnockedOut`), not a murderer. The secure-camp state already exists: `Campfire.GetEntry(host)?.Safe` is true after 30 s beside a lit fire and goes false when the fire turns to embers. Parties are stock (`Party.Get`). Fires are not saved, so a camp never outlives a restart. Nothing in the stock Bedroll listens for a double-click inside the pack.

## Design

1. **Trigger.** The traveler types `[CampTravel` and gets a list of the secure fires lit by party members (lighter's name, distance). Picking one opens a confirmation ("Travel to X's camp? It costs 2 Kindling and you cannot do it again for 30 minutes.").
   - **Destination (owner ruling):** *any secure fire lit by a member of your party.* A fire counts as secure once it has been lit for 30 seconds (the stock securing time) and is still burning or dim, not embers. The lighter need not be standing there.
2. **Channel.** After confirming, a 5-second wait. Moving, taking damage, casting, or any refusal condition arising cancels it with no cost.
3. **Arrival.** The traveler appears on an open tile within two tiles of the fire, with the stock Recall sound. Both are told ("You arrive at X's camp." / "Y has joined your camp.").
4. **Everything is checked twice**, at the start and again at the moment of arrival: the fire's lighter is still in the traveler's party and the fire is still secure; the fire has a free place left (item 5); the traveler alive, not Knocked Out, not in PvP combat within 30 s, not overloaded (criminals and murderers are allowed: owner ruling 2026-10-06, see the end of the Evidence section); neither end in a Hot Zone; both ends pass the stock `CheckTravel` (so Felucca dungeons are out, in both directions); an arrival tile exists; the traveler has the Kindling; the cooldown has run.
5. **Cost and limits, with travel as a benefit of high Camping (owner direction).** 2 Kindling consumed on arrival; a cooldown of 30 minutes per account (an account tag with a UTC time, so it survives restarts and alternate characters share it). **How many people a fire can take is set by its lighter's real Camping skill (owner's table): 1 arrival at Camping 50, 2 at 60, 3 at 70, 4 at 80, 5 at 90, 6 at Grandmaster; none below 50.** In config: `capacityBaseSkill` 40 and `skillPerArrival` 10, so capacity is floor((skill - 40) / 10), at most `maxArrivals` 6. Read from the lighter's skill when someone travels. The count is for the fire's whole life; feeding does not reset it.
   - **Why:** a flat cap is easy to get around, because a traveler can arrive and light their own fire for the next person. With the cap tied to the lighter's skill, an unskilled party member's fire takes nobody, and a chain of fires only works if each lighter has the skill. Travel becomes something a trained camper gives their party.
6. **Pets (owner ruling):** they travel with you, as Recall does (`BaseCreature.TeleportPets`).
7. **Audit and staff.** Every trip is written to the audit log; `[CampStatus` also shows each fire's lighter, capacity and arrivals, and the caller's cooldown. The lighter, if online, is told when someone arrives.
8. **Hot Zone warning (owner, added during the build).** A camp inside a Hot Zone is tagged `[HOT ZONE]` in the list, and its confirmation opens with a red warning that other players can attack the traveler there; the arrival message repeats it. Going *to* a Hot Zone camp is allowed once warned. Leaving a Hot Zone by camp travel stays refused, as in the signed-off plan.
9. **The lighter is kept informed (owner, added during the build).** While `campingTravel` is on, the lighter of a fire (if online) is told, in plain words and naming the command:
   - when it is lit: "[CampTravel" and how many places their Camping gives (or that Camping 50 is needed);
   - when it becomes secure and party members can travel to it;
   - when it is burning low (and to add Kindling), when it is down to embers (travel stops until relit), when it is relit, and when it has gone out;
   - each time someone arrives ("N of M places used") and when it is full.
10. **Hot Zone confirmation for every kind of travel (owner, added during the build).** A *blue* (innocent: not criminal, not a murderer) player about to be taken **into** a Hot Zone from outside one by **Recall** (scroll, spell, runebook, rune), by **a gate** (Gate Travel spell gates and any other Moongate), or by **camp travel** is warned and must confirm. The confirmation carries a checkbox, "Do not show me this warning again when traveling", stored on the account; `[TravelWarning on|off` shows and changes it, so the choice can be undone. Camp travel already confirms, so it gains the warning text and the checkbox inside its own confirmation. Decisions made while building (all reversible in config or code): travel from one Hot Zone into another is not warned (nothing new to be warned of); murderers and criminals are not warned (they are not blue; camp travel lets them in, unlike Recall); the warning for Recall and gates sits behind its own flag `featureFlags.hotZoneTravelWarning` (off, requires `hotZones`), and the camp-travel warning follows `campingTravel`. Two small ModernUO hooks, null by default so stock behavior is unchanged: a Recall confirmation callback (`SpellHelper.TravelConfirmation`, asked just before the spell uses mana and the scroll, and revived for one call when the player confirms) and a Moongate one (`Moongate.TravelConfirmation`, asked in `BeginConfirmation`, which already exists to prompt before a gate trip).
11. **Flag and config.** New flag `featureFlags.campingTravel`, off in source. A `campTravel` config section: `channelSeconds` 5, `cooldownMinutes` 30, `kindlingCost` 2, `capacityBaseSkill` 40, `skillPerArrival` 10, `maxArrivals` 6, `secureSeconds` 30, `arrivalRange` 2. With the flag off the command says travel is not available.

## Work breakdown (as built)

- **ModernUO** (commit `ac1d0e2c8`, all null or inert by default, so stock behavior is unchanged with the shard code absent):
  - `Campfire.Active` (every existing fire) and `Campfire.CreatedAt` (feeding moves `LitAt`, not `CreatedAt`). The destination rule ("any secure fire lit by a party member", even if the lighter has wandered off) needs a list of fires, and scanning the world is not allowed. Fires are never saved, so the collection needs no rebuild.
  - `SpellHelper.TravelConfirmation`, asked in `RecallSpell.Effect` just before the spell uses mana and the scroll (a confirmed Recall revives the finished spell for one call), in `Moongate.BeginConfirmation` (which already prompts before some gate trips; this covers Gate Travel gates and every plain moongate) and in `MoongateGump` (public moongates, whose list includes Buccaneer's Den inside a Hot Zone).
- **ShardContent:** `CampTravelService.cs` (the eligibility planner as a pure function, the command, the two gumps, the wait, the cooldown tag, per-fire arrival counts, the lighter notices), `TravelWarningService.cs` (the warning rule, the prompt, the account choice and `[TravelWarning`), `OutdoorHotZonePolicy.IsHot(Map, Point3D)`, config sections and flags in `ShardRulesConfiguration.cs` and `shard-rules.json`, `[CampStatus` additions, registration in `ShardBootstrap`, `CampingService` tells travel who fed a fire.
- **Tests:** `CampTravelServiceTests`, `TravelWarningServiceTests`, `UorCampfireTests` (registry, `CreatedAt`), `UorTravelConfirmationTests` (hook null by default, Moongate asks it). Live driver and probe: `tests/scenarios/camp-travel/`.
- **Docs:** this file, the readiness record, the roadmap. The README rules section changes only when a flag is switched on.

## Verification

| ID | Case | How |
| --- | --- | --- |
| U1 | Eligibility planner: every refusal reason, and the happy path | unit |
| U2 | Cost, cooldown and skill-set capacity arithmetic (under 50, then 50 to 100 in steps of 10); config ranges | unit |
| L1 | Happy path: a party member far away travels to a secure camp, pays 2 Kindling, arrives beside the fire | live, three characters |
| L2 | Refused: fire not yet 30 s old; fire at embers; lighter left the party; lighter's party membership checked at arrival | live |
| L3 | Refused: traveler criminal, in PvP combat, overloaded, Knocked Out; either end in a Hot Zone; either end in a Felucca dungeon | live (staff placement) |
| L4 | Channel cancelled by movement and by damage; no Kindling spent; fire dying mid-channel cancels | live |
| L5 | Cooldown refuses a second trip (and an alternate character on the same account); a fire lit at Camping 60 takes exactly 2 and refuses the 3rd; a fire lit by someone under Camping 50 takes none; pets arrive with the traveler | live |
| L6 | Flag off: the command refuses; no lighter notices are sent; nothing else changes | live |
| L7 | The lighter receives each notice at the right moment (lit with the command and capacity, secure, burning low, embers, relit, out, arrival counts, full) | live |
| L8 | A Hot Zone camp is tagged and warned about, travel to it works after the warning, and travel from a Hot Zone is refused | live |
| L9 | A blue player is asked before Recall (rune and runebook) into a Hot Zone and before entering a gate to one; confirming travels, cancelling spends nothing; criminals/murderers, travel inside a Hot Zone and travel to a non-Hot place are not asked; the checkbox stops the prompt on every kind of travel and `[TravelWarning on` brings it back; flag off: no prompt | live |
| U4 | The warning rule: who is asked (blue, destination Hot, origin not Hot, not switched off, flag on) and the saved choice | unit |
| U3 | The notice planner: each transition sends exactly one notice, none when the capacity is zero except the explanation | unit |

A test-only probe (`tests/scenarios/camp-travel/CampTravelProbe.cs`) forms the parties (the test client has no party-invite command), places fires, runes and gates, sets conditions and writes JSON reports. Live runs use a disposable host; the dev saves are not touched.

## Activation

Two flags, both off in source, each its own owner acknowledgment: `campingTravel` (camp travel, its lighter notices and its Hot Zone warning) and `hotZoneTravelWarning` (the warning before Recall and gates). Approving this plan did not switch either on.

## Owner rulings (2026-10-06)

| Question | Ruling |
| --- | --- |
| Trigger | The `[CampTravel` command and gump (no Bedroll hook, no engine change). |
| Cost, cooldown and cap | Not chosen from the options. The owner pointed out that a per-fire cap is easy to get around by arriving and lighting a new fire, and said travel should be **a benefit of having high Camping**. Built as capacity from the lighter's Camping skill (design item 5). |
| Pets | **Travel with you, as Recall does.** |
| Destination | **Any secure fire lit by a member of your party.** |

## Confirmed by the owner (2026-10-06)

- **Capacity from skill:** the owner's own table, 1 arrival at Camping 50, 2 at 60, 3 at 70, 4 at 80, 5 at 90, 6 at Grandmaster; none below 50.
- **"Secure" means** the fire has burned 30 seconds and is still burning or dim; the lighter need not be there.
- **Sign-off:** build it to a readiness record.

## Out of scope and deferred

Travel for non-party players; a bank or cargo check (Beta 2c cargo does not exist yet; it will add a rule); a map marker for camps; Trammel and other maps (Felucca only); a camp-to-camp network; a "return" trip; any change to Recall or Gate other than the Hot Zone confirmation (the owner added that one during the build); static dungeon teleporters, Sacred Journey and boats (not covered by the warning).

## Risks and ordering

- **Dilutes travel** (the vision's "reasons to travel"): the cost, cooldown, per-fire cap and party-only rule are the brake, and every number is config so it can be tightened.
- **Ambush at the camp:** the arrival tile is beside a host who is already there, in a secure, outdoor, non-Hot-Zone place; nobody can be pulled in, only come in.
- **Races:** party leave, the fire dying, the host logging out and the traveler dying during the channel all cancel at the second check.
- **Alternate characters:** the cooldown is per account.
- **Unattended fires:** a traveler can arrive at a fire whose lighter has wandered off; arrival is still a party member's fire, outdoors, not in a Hot Zone or dungeon, and the lighter is told.
- **Pets travel too,** so a loaded pack animal teleports with its owner (owner ruling); the "no cargo" guardrail then covers only Beta 2c trade cargo, which does not exist yet.
- Built in isolation: a new service and flag only, so no other system changes.

## Evidence (2026-10-06)

**Unit:** Shard suite 718/718 and UOContent suite 1362 pass, 2 skipped (final run `20261006T211826956Z-e18b7e`, after the guide audit, the rename, the criminal ruling and the last two wording fixes).
**Live:** disposable host `camp-travel` (flags on; `campTravel` secureSeconds 8 and channelSeconds 3; camping lit 60 s + 1 s per skill point, embers 30 s + 0.5 s per point), three Mace Fighter characters and a staff session, probe and driver in `tests/scenarios/camp-travel/`. One pass of all five stages on the final build: `camp` 92, `notices` 16, `hot` 20, `warn` 36, `off` 4 checks, no failures (`work/camp-travel/final-stages.log`); repeated on the final build with the region names and `[Welcome` text, `camp` 91, `notices` 16, `hot` 20, `warn` 36, `off` 4, no failures (`work/camp-travel/final2.log`). After the criminal ruling and the guide audit the `refusals` (25 checks) and `criminal` (10 checks) stages were run again on the final DLL, no failures (`work/camp-travel/stages-r3.log`). Earlier passes found harness faults only, none in the game (probe set a skill the stat offset moved; a pet that had been told to stay; a Recall rune on an occupied tile; the lit-notice mark taken after the notice).

| ID | Result | How it was shown |
| --- | --- | --- |
| U1 | Pass | `CampTravelServiceTests`: each of 20 conditions refuses on its own with its own reason, the first reason in priority order is the one reported, only leaving a Hot Zone is refused for Hot Zones |
| U2 | Pass | Places 0, 0, 1, 1, 2, 2, 3, 4, 4, 5, 5, 6, 6 at skills 0, 49.9, 50, 59.9, 60, 69.9, 70, 80, 89.9, 90, 99.9, 100, 120; cooldown tag read back; secure rule; every config range |
| U3 | Pass | Each notice told once through a fire's life, none after it is gone, embers never told as secure, own feeding not echoed, the command named in the lit, secure and relit text |
| U4 | Pass | Warning rule (blue, destination Hot, origin not Hot, not switched off, flag on), the saved choice, the flag needs `hotZones` |
| L1 | Pass | A party member far away confirms, waits, arrives within 2 tiles of the fire but not on it, pays 2 Kindling (5 to 3), starts the cooldown; the fire counts 1 arrival |
| L2 | Pass | A fire younger than the secure time refuses ("not secure yet"); a fire at embers refuses; the lighter leaving the party refuses at arrival |
| L3 | Pass | Overloaded, unable to move, recent combat, too little Kindling, leaving a Hot Zone (Buccaneer's Den), leaving a Felucca dungeon (Deceit), a camp inside a dungeon: each refused with its own text and no Kindling spent. Knocked Out: unit test only. **Criminal (owner ruling 2026-10-06):** a criminal in recent player combat is refused, and a criminal outside combat travels and pays; the old criminal and murderer refusals are gone |
| L4 | Pass | Moving, damage, the lighter leaving the party and the fire being deleted each cancel the wait; no Kindling spent, traveler stays |
| L5 | Pass | The cooldown refuses a second trip at no cost; a Camping 65 fire takes exactly 2 (the second arrival tells the lighter the camp is full) and refuses the third ("2 of 2 used"); a fire lit at Camping 45 takes nobody ("needs Camping 50 or higher"); Camping 100 gives 6 places; a following bonded pet arrives beside the traveler and one told to stay does not |
| L6 | Pass | With `CampingTravel` overridden off the command says travel is not available and the lighter is told nothing about a new fire |
| L7 | Pass | The lighter hears, once each and in order: lit (with the command and places), secure (with places left), burning low (78 s in), embers (116 s in), relit when a party member feeds it (with the command), burned out; and each arrival with the count |
| L8 | Pass | A Hot Zone camp is tagged `[HOT ZONE]`; its confirmation warns and offers the checkbox; confirming travels in and the arrival repeats the warning; ticking the box saves the choice on the account (tag `off`) and the next confirmation has no warning; `[TravelWarning on` and `off` change and report it |
| L9 | Pass | Recall (rune) into a Hot Zone asks first: cancelling spends no scroll and goes nowhere, confirming travels and uses one scroll; Recall out of a Hot Zone and from one Hot Zone place to another are not asked; the checkbox saves the choice and stops the prompt, `[TravelWarning on` brings it back; a gate into a Hot Zone asks; a criminal is not asked (the stock leaving-town prompt still appears); a public moongate offering Buccaneer's Den asks; with `HotZoneTravelWarning` overridden off Recall goes straight in |

### New player-facing text (for the owner's review)
- **Command and refusals:** "None of your party has a campfire burning. Party members light one with Kindling, and you can travel to it with [CampTravel once it is secure." / "Camp travel is not available." / "That campfire has burned out." / "That is your own campfire." / "The one who lit that campfire is no longer in your party." / "You cannot travel to a camp in another land." / "That campfire is down to embers. Camp travel needs a burning fire." / "That camp is not secure yet. Its fire must have burned for 30 seconds." / "The one who lit that fire needs Camping 50 or higher before party members can travel to it." / "That camp has no places left (2 of 2 used)." / "You are already at that camp." / "You cannot travel while you are knocked out." / "You cannot travel while you are unable to move." / "You cannot use camp travel to leave a Hot Zone." / "You cannot travel from this place." / "You cannot travel to that camp." / "There is no open ground beside that campfire." / "You cannot use camp travel again for 30 minutes." / "You need 2 Kindling in your backpack to travel." The criminal, combat, overloaded and sigil refusals keep Recall's own words.
- **The list and confirmation:** "Travel to a party member's camp" / "Pick a camp. You will be asked to confirm." / "<Name>'s camp: ready | securing | embers | full | needs more Camping | cooldown | no Kindling | you are here | not now" with a second line "<Town, dungeon, Hot Zone or sextant position>, N tiles away" / "[HOT ZONE]" / "Travel to <Name>'s camp?" / "It costs 2 Kindling, and you cannot use camp travel again for 30 minutes. Stand still for 5 seconds. Bonded pets beside you come too. N of M places left at this camp." / "WARNING: This camp is inside a Hot Zone. Other players can attack you in a Hot Zone, and Wards and Loot Protection do not apply." / "Do not show me this warning again when traveling" / "Travel", "Cancel".
- **The wait and arrival:** "You prepare to travel to <Name>'s camp. Stand still for 5 seconds." / "You move, and the travel is cancelled." / "The pain breaks your concentration, and the travel is cancelled." / "You cannot travel while casting." / "You arrive at <Name>'s camp." / "You are already travelling."
- **To the lighter:** "Your campfire is lit. Once it has burned for 30 seconds, party members can travel to it with [CampTravel (your Camping skill gives N places)." (or "...once your Camping skill is 50 or higher.") / "Your camp is secure. Party members can travel to it with [CampTravel (N of M places left)." / "Your campfire is burning low. Use Kindling beside it to keep it burning." / "Your campfire is down to embers. Party members cannot travel to it until you feed it with Kindling." (or "...Use Kindling beside it to relight it.") / "Your campfire burns brightly again. Party members can travel to it with [CampTravel (N of M places left)." / "Your campfire has burned out. N party members travelled to it." / "<Name> has travelled to your camp (N of M places used). Your camp has no places left."
- **The Hot Zone warning (Recall, gates):** "Hot Zone Warning" / "You are about to travel into a Hot Zone." / "Other players can attack you in a Hot Zone, and Wards and Loot Protection do not apply." / the checkbox / "You decide not to travel." / "That took too long. Try again." / "You will not be warned again before traveling into a Hot Zone. Use [TravelWarning on to turn the warning back on." / "The Hot Zone travel warning is on. Use [TravelWarning off to turn it off." / "The Hot Zone travel warning is off. Use [TravelWarning on to turn it back on." / "Use [TravelWarning on or [TravelWarning off."

- **`[Welcome` guide (a window; each page is the text of that topic):** "UO Rekindled" / "Felucca, without the griefing" / topics "Welcome", "Fighting other players", "Hot Zones", "Your Backpack Ward", "Loot Protection", "Mastery", "Skill Bank", "Camp travel", "Commands" (each shown only for what is switched on) / "Next topic", "Close" / "Type [Welcome to open this guide again." / chat after it opens for a new character: "Welcome to UO Rekindled. Type [Welcome any time to read the guide again." The text of every page is in `WelcomeGuide.cs` (and `CampTravelService.GuideParagraphs` for the Camp travel page); the screenshots show them as a player sees them. The audit that produced the final text is in the next section.

### Owner review additions (2026-10-06)
The owner reviewed the delivered work and asked for three of my follow-up suggestions: a **real-client look at the gumps**, the **camp's place name in the list**, and **discoverability** (`[Welcome`; README and website text held for activation). Results: the list shows the place for each camp (checked live in the real client, Britain and Buccaneer's Den); `[Welcome` is now a guide window (checked in the real client) with camp travel and the Hot Zone warning shown only when on; every gump was viewed in the real ClassicUO client and a real click on Travel ran a trip. The live matrix above was re-run on the final build. Details in the readiness record.

### Owner ruling after delivery (2026-10-06): criminals and murderers may use camp travel
"Criminals and murderers should be able to use campfire travel, just not if you've been recently in combat." Built: the criminal and murderer refusals are removed from the planner (stock Recall still refuses criminals; camp travel deliberately does not), and the existing recent-combat refusal is what stops them, as it stops anyone. "Recent combat" is the stock rule Recall and gates use: attacking a player within the last 30 seconds (`SpellHelper.CheckCombat`); fighting monsters or being chased by guards does not count. Criminals and murderers are not warned before entering a Hot Zone (the warning is for blue players). Unit-tested (the refusal list has no criminal or murderer entry; recent combat still refuses) and live (a criminal in combat is refused with Recall's "heat of battle" text, a criminal outside combat travels and pays 2 Kindling).

### Welcome guide accuracy audit (owner request, 2026-10-06)
"A full pass on all the welcome gump text across all categories to make sure it's accurate to the implementation, and that there is no confusing statements."

**Method.** Every sentence on every page was traced to the code or the config that decides it, and the numbers are now read from that code or config instead of being typed in (`WelcomeGuide.Numbers.Current` reads `shard-rules.json`; the Knocked Out, Ward, Loot Protection and Mastery figures come from `KnockedOutService`, `WardState`, `TheftProtectionService` and `MasteryEngine`). `WelcomeGuideTests` pins each claim (who may attack whom, the Knocked Out length, who may Execute and when the victim may report, the Hot Zone loot rule, the Ward numbers and reset rules, the 10-minute Loot Protection rule, the Mastery allowances and the fewest days from 90.0 to 100.0, the Skill Bank numbers and commands) so a later change to a rule fails a test until the page is corrected. A page or sentence for a feature that is switched off is left out, and the command list shows only commands that work.

**What each page now says (all checked against the code).**
| Page | Content |
| --- | --- |
| Fighting | Outside Hot Zones a player can attack you only with Intent on, if you are criminal or red, or if you are already fighting; the same for you; duels and guild wars also allow it. Intent: the toggle, grey while on, killing an Intent player is not murder, locked while criminal or red. Knocked Out: who, how long (from `KnockedOutService`), what it blocks, wake at half health, monsters still kill. Execute: only a criminal or murderer who knocked the player out, or who damaged them in the last two minutes; a player only grey from Intent may not; the executed player can report the executioner unless they attacked first. Murder: what a report does, five counts make a player red, guards pay the bounty |
| Hot Zones | Which zones, free fighting in the same zone, no Wards or Loot Protection, no extra rewards, who may loot a Knocked Out player (anyone in a Hot Zone, becoming criminal; elsewhere only the criminal or murderer who did it), what is protected, the travel warning when on |
| Your Backpack Ward | What it is and where it works (backpack or a bag in it, not a bank, house, ground or pet), how a thief is caught (your own notice or the Ward's extra chance, 25%, 50%, then certain, per thief), the block on every character until the Ward is used up, the 30-minute quiet window and what resets it, where to get more (price, craft recipe and buy-back from config), double-click to inspect |
| Loot Protection | 10 minutes per offender, any monster corpse you have rights to, what it does not cover, not in Hot Zones |
| Mastery | Why it exists (less grinding, rewards activity), the 90.0 threshold, the 24-hour cycle, allowances 2.0, 1.0 and 0.6, what a valid use is, the fewest days from 90.0 to 100.0, stored allowance, the Up setting, `[MasteryStatus` |
| Skill Bank | How the bank fills (cap 700, bank 300, only from skill-gain displacement), how points come back, a full bank, Locked and Down as bank-entry settings (not the skill arrows), the commands |
| Camp travel | Cost, wait, cooldown "on your account", places counted over the fire's whole life, bonded pets, who may use it (criminals and murderers may; nobody in recent player combat), where it cannot be used |
| Commands | Only commands that are on, one line each |

**Earlier text that was wrong or confusing, now fixed.**
- The Ward and Loot Protection chat text told players to use `[TheftStatus`, a staff command. The pages say to double-click the Ward, and a test fails if any page names a staff command or the old shard name.
- The Execute wording did not match the implementation (owner review): it now says exactly who may Execute and when the victim may report. The owner's "always reportable" is not how K-5 was built; see the readiness record.
- The command list showed `[Intent`, `[Execute` and the others whether or not those rules were on; it now follows the switches.
- Numbers typed into text (Knocked Out seconds, Ward chances and window, Loot Protection minutes) are read from the code that enforces them.
- The Mastery and Skill Bank pages are new, written from `MasteryEngine`, `SkillBankLedger` and the config.

**Confusing wording removed in the second pass** (after reading the pages in the real client): the Skill Bank opening sentence now says a skill that gains "makes room by taking points from a skill you set to Down"; the `[SkillBank` command line says "See your banked skill points and whether each is Locked or Down."

**Real client.** Every page, and every scroll position of the long ones, was photographed in the real ClassicUO client on the disposable host (`work/player-client/CtTrav/shots/r2-*` and `r3-*`, scratch): text wraps cleanly, nothing is clipped, headings are gold, commands are blue, the scrollbar appears only on pages that need one.

### Named limits
See the readiness record.
