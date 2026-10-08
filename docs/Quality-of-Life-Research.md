# Quality of life for UO Rekindled: recap and research

Researched 2026-10-07 for the owner. Nothing here is built or approved. Each recommendation needs its own plan and sign-off (skill `beta-feature`), and any flag stays off until the owner acknowledges it.

## 1. What we have already done

Everything below is on the dev distribution unless marked off. "QoL" here means anything that cuts tedium, friction for new players, or information gaps.

| Group | Feature | State |
| --- | --- | --- |
| Less tedium | Gathering repeat: mining, lumberjacking and fishing keep going on the chosen target (`harvestAutoRepeat`) | On since 2026-10-05 |
| | Action repeat: taming retries, lockpicking while picks last, spinning wheel, loom and cooking take the whole stack (`actionAutoRepeat`) | On since 2026-10-07 |
| | Crafting "make this many": agreed, planned by itself (Beta 2d) | Not built |
| | Declined by the owner: bandage repeat, loot-all, snooping repeat | |
| New players | Starter package (Bag, scissors, gold once per account, newbied gear, craft materials, Backpack Ward, camping kit); weight budget so every template can walk | On |
| | Faint Memories: 5.0 free skill points, unlock 24 h after creation, 0.2 per use | On since 2026-10-07 |
| | `[Welcome` guide window, opens by itself for a new character; era cooking restored | On |
| Information | Windows for `[SkillClasses`, `[SkillBank`, `[Mastery`, `[IntentStatus`, `[TravelWarning`, Ward double-click | On |
| Progress feel | Skill-gain curve, Skill Bank (0.2 restores, banks any Down loss, Discard), daily Mastery from 90 | On |
| Travel, camping | Campfires (skill-scaled, feedable) | On |
| | Camp travel and the Hot Zone travel warning | On since 2026-10-07 |
| Economy | Tinkers sell, craft and buy back the Ward | On |

Already part of the game, found by the survey: bank-area theft protection (`theftRegions.bankProtectionPolygons`), old-style player vendors, house speech commands, key rings, bank checks, party chat, secure trade, pet "all" commands, skill locks, and **Make Last for crafting** (use the tool, then target the tool; the game already prints that hint).

## 2. How the ideas were judged

**Owner ruling, 2026-10-07:** era fit does not count against a change that is pure quality of life, meaning the same action with the same result, fewer clicks or clearer information. Bank checks are the model: the banker visit stays and only the hauling of gold goes. The first version of this report treated "after the era" as a mark against an idea; that is withdrawn. Era is kept in section 3 as context only. The tests are now:

1. **Does it change a rule or a mechanic?** Pure ease of use passes. Anything that changes outcomes, risk, economy or numbers needs its own ruling, whatever its date.
2. **No power creep.** The classic ceiling holds.
3. **Keeps the reasons to go places and meet people** (banks, vendors, danger, theft). A bank check passes; a bag of sending or vendor search does not.
4. **Keeps thieves and criminals.** No safe zone that removes their targets; no accident traps either.
5. **Does not automate play, and does not make a skill pointless.** The owner already accepted bounded repeats and declined bandages, loot-all and snooping; a tooltip that does Item ID's job would fail here.
6. **Stock first, cheap to build.**

## 3. Era evidence (spring 2000), kept as context

Anchor: Publish 5, "the Renaissance publish", is dated 2000-04-27 on EA's own notes archive (client 2.0.0 on 2000-04-18). Sources disagree on the retail date (Apr 3 versus May 4).

| Feature | Earliest date | At UO:R? |
| --- | --- | --- |
| In-client macros: Last Target, Next Target, Target Self, Arm/Disarm, Delay, WaitForTarget, CloseGumps, AttackLast | 1999-08-25/26 | Yes |
| Per-character macros, saved window positions | 2000-01-18 | Yes |
| Always Run, Save Desktop | 2000-03-16 | Yes |
| Skill locks (up/down/stop) | 1999-11-23 | Yes |
| Runebooks | 1999-11-23 | Yes |
| Key rings | by 1998-04 | Yes |
| Bank checks | 2000-03-08 | Yes |
| Secure trade; houses with sign and trash barrel; player vendors | 1998 to 2000 | Yes |
| Party and party chat | live 2000-04-27 | Yes |
| Pet "all" commands | 1999-05-25 | Yes |
| Anti-macro skill-gain code | 2000-03-08 (Publish 4); crafts, Mining exempt | Yes |
| Chat window and conferences | referenced in 1999 patch notes; first date not found | Probably (unverified) |
| Craft menus with Make Last | tinker menu 1999-05; blacksmith menu with Make Last, Smelt, Repair is dated Aug 2000 | Uncertain |
| Stat locks | 2002 (Publish 16) | No |
| Bulk order deeds | 2001-11 | No (the shard's smith BODs are an owner-approved deviation) |
| Bag of sending | 2002 | No |
| Item property tooltips | 2003 (Age of Shadows) | No |
| Universal craft gump with "Last 10" | 2001-11 | No |
| Vendor search, insurance, buff icons | later | No |

OSI tolerated in-client macros and one licensed assistant, fought injector programs (1998), and throttled skill gain against botting (2000). No 2000-era Rules of Conduct text was found, and UOGuide, Stratics and the Wayback Machine could not be fetched, so some dates rest on search snippets.

## 4. Three findings that matter more than any single feature

**4.1 Anti-macro is off.** `antimacro.json` has `Enabled: false` in the deployed config. The era had it from Publish 4. With the gathering and action repeats now on, the stock throttle (two gain-eligible attempts per skill per target or 5x5 tile per 5 minutes) would stop gains in Lumberjacking, Fishing, Taming and Lockpicking loops, while Mining, Cooking and crafting are exempt in the fork's config. Skill Bank, Faint Memories and Mastery also run only on allowed uses. This is a decision, not a feature: leave it off (current, no throttle at all), or turn it on and exempt the skills the repeats cover. The repeats are bounded by resource and target, so unattended farming is not unlimited today.

**4.2 Assistant negotiation is off.** ModernUO ships a Razor-style feature handshake (`Assistants/AssistantHandler.cs`, `assistants.enableNegotiation` is `False`); `assistants.json` allows all 25 features. Turning it on, with looping macros, autoloot, auto-bandage, restock/sell/buy agents and closest/random targeting disallowed, uses code we already have and needs no build. It only binds tools that announce themselves; AutoHotkey, OCR and AI agents sit outside it. Popular shards pair a blessed client with this model: Outlands bans most assistants and ships its own, UO Forever allows several but bans unattended gathering, taming and looting, and the T2A shards allow Razor but ban unattended gathering.

**4.3 The client is ours.** Because the fork is the owner's, a "fair for everyone" client is possible: the era macro set built in (no loops), counters that update without opening containers, sensible defaults for new players, and click-to-pathfind defaulted off so roads and travel stay the experience.

## 5. Recommendations (re-rated 2026-10-07 under the owner's ruling)

### What changed in the ratings

| Idea | Before | Now | Why |
| --- | --- | --- | --- |
| Item property tooltips | Left out (AoS-era) | **Tier 2** | Pure information. Feasible: the server side is `opl.enable`; the client needs the character-list tooltip bit, which in ClassicUO also switches on the paperdoll's extra spellbook buttons. The owner's fork can split the two. Must not show what Item ID, Arms Lore or Taste ID gate |
| Buff icons | Left out (post-era) | **Tier 1** | Pure information, and the shard now has states that appear only as messages or windows: Knocked Out, Intent, criminal timer, Ward, camp. `buffIcons.enable` is an ordinary server setting. Needs a prototype to confirm custom text in this client |
| BOD book | Left out (post-era) | **Tier 2** | Only a container for deeds the shard already has; the gate is the Inscribe recipe (`DefInscription.cs:439`, `Core.AOS`) |
| Salvage Bag | Left out (ML) | **Tier 2** | Bulk smelting and cloth cutting with the same yields; a shard guard against bound items exists |
| Refuse-trades toggle | Not listed (HS) | **Tier 2, small** | Context-menu toggle that stops trade-request spam; no rule change |
| Guild chat | Left out (SE) | **Tier 1** | Communication that builds community. The stock chat only exists with the whole new guild system, so the shard would add a small command instead |
| Universal craft gump (Make Now, Last 10) | Left out (2001) | **Tier 2, inside Beta 2d** | Ease of use, but the stock switch is global and also drops the legacy flows and adds gem jewelry (a mechanic change), so it must be done as a UI over the shard's own recipes, not by flipping the setting |
| Recall by name (`[Recall <rune>`) | Left out | **Tier 2, optional** | Same spell, reagents and checks, only the book gump is skipped. It must call the same travel hooks (warning, camp rules) |
| Stock chat window | Needed an era check | **Tier 1 decision** | The era question no longer matters; it is a yes or no |
| Grid containers, spell bar, counters, always run, auto-open doors | Partly mixed | **Tier 1 (client defaults)** | Display and input only |
| Damage numbers | Left out | **Optional, client only** | Pure information, but it does nothing for the new-player friction and can shift how combat is read |
| Click-to-pathfind | Default off | **Decision** | It changes no rule, but it automates walking, and roads, Pilgrimage and camp travel rely on travel being a choice; it also enables unattended walking |

Still out, because of what they change and not when they came: vendor search (economy and traffic), bag of sending (removes bank trips), account-wide gold (economy, and replaces checks), auto-stable on logout (removes offline pet risk), insurance (death economy), vendor rental (housing economy), 12-charge runebooks (numbers), a Young zone or safe no-theft hub (mechanics), autoloot, loot-all, auto-bandage and auto-heal (automation, and the owner declined them), looping macros and restock agents.

### Tier 1: very high fit, low cost, no new power

1. **First-steps and information pages in the guide.** "Your first hour", "Skill locks 101" (new players struggle with locks), "Where to train" (NPC trainers, what each class trains to), "Banks, vendors and checks" (the speech commands `bank`, `balance`, `check`, `vendor buy` already work), "Crafting and Make Last", "Gathering and repeats". Every shard studied lists information gaps and steep learning curves among the reasons new players quit. Infrastructure exists (`GuideWindow`).
2. **Accidental-crime guard rails.** A confirmation before an action that would turn a blue grey (looting a blue's corpse, and the other stock criminal acts), with a one-time "do not ask again" like the travel warning, plus a clear "you committed a criminal act: the victim, how long" notice. Outlands ships both. Deliberate crime stays untouched. The travel-warning pattern is already built.
3. **A client with sensible defaults and the macro set.** Last/Next Target, Target Self, WaitForTarget, Arm/Disarm and dress sets, Open Door, Delay, a bandage macro (the macro, not an auto-heal), item counters, spell bar, grid containers if the fork has them (unverified), Always Run, click-to-pathfind off; no looping.
4. **Turn on assistant negotiation** with the disallow list in 4.2.
5. **A help channel.** The stock chat is disabled here; decide whether to enable it, and whether a volunteer Companion role is wanted (a community decision, not code).
6. **A buff-icon status bar for the shard's own states** (Knocked Out countdown, Intent on or off, criminal timer, Ward state, secure camp, Faint Memories ready). New in this version of the report: it replaces messages that scroll away with a persistent, glanceable display.
7. **Guild chat** as a simple command (the old guild system has none).

### Tier 2: good, but needs a plan or a ruling

8. **Item tooltips**, including shard facts (Ward status, bound or newbied, crafter, durability). Needs a small client-fork change and an audit that nothing shown replaces Item ID, Arms Lore, Taste ID, Animal Lore or Anatomy.
9. **Crafting "make this many"** (agreed for Beta 2d; Make Last already exists) and the **craft gump UX** decision, together in the 2d plan.
10. **BOD book, Salvage Bag, refuse-trades toggle.**
11. **The anti-macro decision** (4.1).
12. **Pet friction.** Pets are shrunk entering a dungeon and released by hand outside. An automatic release outside would remove a step; it needs a ruling because of the pet restrictions.
13. **Party corpse looting.** In this build a party member can loot your corpse without becoming criminal (`PartyMemberInfo.CanLoot` defaults true). Joining a party needs consent, so it is mostly benign; check it against Loot Protection and the Ward text. A rule to confirm, not a QoL feature.
14. **Recall by name**, optional, through the same travel hooks.
15. **Information on death:** a line with the body's sextant coordinates, not item return.
16. **Housing on-ramp** (rental credit or payment plan), after the housing phase.

### Tier 3: leave out

See "Still out" above. The anti-paralysis pouch is also left out: it only matters in PvP and Hot Zones are the only place.

## 6. Decisions to bring to the owner

1. Anti-macro: leave off, or turn on with the repeat skills exempt?
2. Assistant negotiation: turn on, and with which disallow list?
3. Which Tier 1 items to plan first? Suggested order: guide pages (1), crime guard rails (2), client defaults with negotiation (3 and 4), buff-icon status bar (6), help channel and guild chat (5 and 7).
4. Enable the stock chat window: yes or no.
5. Click-to-pathfind in the fork: on or off.
6. Rulings on the pet release outside dungeons and the party corpse default.
7. Tooltips and buff icons each need a short prototype before a plan (client display, custom text, and for tooltips the pre-AoS content and the skill audit).

## 7. What could not be verified

- Reddit, forums.uo.com, Stratics, UOGuide, UOAlive and the Wayback Machine were unreachable: many demand claims are from search snippets and mark "offered by shards", not "requested by players". No vote counts were found.
- The Outlands disabled-feature list, UO Renaissance's rules and Demise's rules are from search extracts only.
- Whether ClassicAssist, Orion and UOSteam honor ModernUO's handshake (the code targets Razor CE).
- Whether the ClassicUO desktop client has grid containers and the web client's agents (documented for the web client only).
- The first date of the chat conference system, and the exact macro set of April 2000 (only Aug 1999 and Mar 2000 changes are documented).
- Buff icons: that this client shows them without an expansion bit (the setting is plain server code, but it has not been tried here), and how to show shard text (custom states need a cliloc with an argument).
- Tooltips: whether `opl.enable` alone gives correct pre-AoS tooltips (not tested), what each property would reveal, and the effect of splitting the client's tooltip and paperdoll-book bits (`ClientFeatures.cs:57-59`).
- Live behaviour of anything in the survey: it was a code read. The survey's note that `actionAutoRepeat` is false is out of date; it was enabled on 2026-10-07.

## 8. Sources (principal)

- EA's publish notes archive: https://uo.com/wiki/ultima-online-wiki/technical/previous-publishes/ (Publish 1 to 14 and the 1999-08-25 notes)
- UO Second Age patch-note mirror: https://wiki.uosecondage.com/ (1998 to 2000 patch notes)
- ClassicUO wiki and releases: https://github.com/ClassicUO/ClassicUO/wiki and https://github.com/ClassicUO/ClassicUO/releases
- UO Outlands: https://wiki.uooutlands.com/New_Player_Guide, https://wiki.uooutlands.com/Options, https://wiki.uooutlands.com/Commands, https://uooutlands.com/rules/
- UO Forever: https://uoforever.com/wiki/index.php/Server_Commands, https://uoforever.com/rules/
- Vendor-search objection (2014): https://www.uoforum.com/threads/player-vendor-search.40740/
- UO Second Age and UO Lost Lands rules: https://uosecondage.com/rules, https://uolostlands.com/pages/about/
- Local code: `ModernUO/Projects/UOContent/Assistants/`, `Skills/AntiMacroSystem.cs`, `Engines/Craft/T2A/`, `Engines/Party/PartyMemberInfo.cs`
