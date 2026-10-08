# Tier 1 quality-of-life items: plan for sign-off

Status: **item A signed off 2026-10-07 (chapter tabs, plus the Pets and Dying pages) and built the same day; the F spike was authorized and done (`Buff-Icon-Spike.md`); B, C, D, E, G wait for the owner's answers.** The owner also asked for a larger default game view: about 70% of the window, done through the default profile (`data/client/default-profile.json`) plus a small client change (`game_window_start_fraction`, built into `cuo.dll` 2026-10-07). The chapter tabs got stone tab art the same day. Source: `Quality-of-Life-Research.md` section 5, re-rated under the owner's ruling that pure ease-of-use changes do not need era fit. Two read-only code surveys (server, client) back every fact below; "inferred" marks what no code or test proved.

**Vision check.** All seven items are information, input convenience or communication: no power change, theft and crime untouched, and three of them (help channel, guild chat, the guide) draw players into contact. None removes a reason to travel or visit a banker or vendor.

**Sign-off scope.** The owner asked to start with the guide pages: item A is ready to sign. Items B to G each need the open questions answered and, for F and the chat part of E, a short spike first; each then gets its own short sign-off plan when its turn comes (the `beta-feature` rule).

## Order and shared pieces

1. **A. Guide pages** (no flag, no engine change, no client rebuild).
2. **F spike** (one probe on a disposable host: do buff icons and custom text work in this client?). It decides how B reports the criminal timer.
3. **B. Crime guard rails and the criminal notice** (one narrow ModernUO hook, `Mobile.CriminalChanged`, shared with F).
4. **C. Client defaults and macro set** (`default.json` needs no rebuild; macros, top-bar cleanup and buff auto-open need a client change and a NativeAOT rebuild of `cuo.dll`).
5. **D. Assistant negotiation** (config only).
6. **G. Guild chat** (shard code only).
7. **E. Help channel** (decision first), **F build** after its spike.

Deploys: A, D and G are shard DLL or config. B and F need the ModernUO hook (rebuild `UOContent` into Distribution, bump the pin in three places). C needs the client rebuild and a new `ClassicUO/bin/dist` for players. Flags: none of these is a gameplay flag except as noted; the owner still acknowledges each activation.

---

## A. Guide pages

**Goal.** A new player can learn, inside the game, what the classic game never told them. Exit: six new pages (plus two optional ones) in the guide, correct to the code, reachable without crowding the topic list, every claim pinned by a test, every page seen in the real client.

**Current state.** `WelcomeGuide.Topics` builds ten topics for what is switched on; `GuideWindow` draws one list of topic buttons with a squeeze (`step = min(44, 330 / count)`): 10 topics fit at 33 px, 16 would be 20 px, overlapping the 29 px button art. So the pages need a layout change, not only text. `[SkillClasses` also uses `GuideWindow` with a flat list and keeps it.

**Design.**

*Layout.* Chapter tabs across the top of the guide and, under them, the topics of the chapter on the left (six at most per chapter). Chapters: **Start here** (Welcome, Your first hour, Skill locks 101), **Rules** (Fighting other players, Hot Zones, Backpack Ward, Loot Protection), **Skills** (Training, Mastery, Skill Bank), **Work** (Gathering and repeats, Crafting, Money and shops), **Travel** (Camping, Camp travel), **Commands**. A chapter with no topics (a feature off) is not shown. The window still opens on any topic by key.

*The new pages, and where each fact comes from* (each claim is re-read against its source when the page is written and pinned by a test, as for the existing pages):

| Page | Says | Source |
| --- | --- | --- |
| Your first hour | What is in your pack (Bag, scissors, Ward, Bedroll and Kindling; your gear is newbied and kept at death unless you are a murderer), your three skills, set the locks, 500 gold once per account, Faint Memories unlock after 24 hours, where to spend the first hour, who can attack you | README rules, starter services, flags in `Context` |
| Skill locks 101 | The three settings (Up gains, Down can give points up when another skill gains, Locked neither), where to set them (the arrows in the skills window), the 700 cap, why Skill Bank, Faint Memories and Mastery need Up, a "why is my skill not gaining" checklist | `SkillCheck.Gain`, `MasteryProgression.CanGain`, bank and Faint Memories services |
| Training | How skills gain here (classes and speeds: pointer to `[SkillClasses`), NPC trainers: a human NPC in a town teaches any skill it has at 60.0 or more, up to a third of its skill (at most 42.0, never past your cap), at 1 gold per 0.1 point; right-click the NPC or say its name and "train"; drop **exactly** the price (a partial payment teaches proportionally, overpaying is lost); which kinds of NPC teach which skills | `BaseCreature.cs` teaching code, `OnSpeech.cs`, SBInfo spawn skills (survey, section 6a) |
| Money and shops | `bank`, `balance`, `withdraw N` (up to 5,000 at a time here), `check N` (5,000 to 1,000,000), no deposit command (drag gold into the box), criminals refused; `vendor buy`, `vendor sell` within four tiles; vendors take pack gold then bank gold; `stable` and `claim` (30 gold a pet, no expiry); guards refuse murderers | `Banker.cs`, `VendorAI.cs`, `BaseVendor.cs`, `AnimalTrainer.cs` |
| Crafting | Use the tool, pick from the menu (it lists only what you can make); target the tool itself to repeat the last item; Smelt and Repair live in the Blacksmith menu; the Ward recipe in Tinkering; "make this many" added when it ships | `BaseTool.cs` (the in-game hint already says "Target this tool to make last item"), `T2ACraftToolTarget.cs`, menus, `BackpackWardCraft` |
| Gathering and repeats | What repeats (mining, lumberjacking, fishing; taming, lockpicking, spinning wheel, loom, cooking), what ends it, the pace is the stock pace; text appears only for flags that are on | `Harvest-AutoRepeat-Evidence.md`, `Action-AutoRepeat-Evidence.md` |

Optional (recommended): **Pets** (never attack players, shrunk in dungeons, released by hand outside) and **Dying** (corpse, healers and ankhs, kept items, Knocked Out): the two rules most likely to surprise a new player. They are not in the Tier 1 list; the owner decides.

*Gating.* Pages for a feature that is off are left out, as now. `Context` gains `HarvestRepeat` and `ActionRepeat` (and a starter-package flag).

**Work breakdown.**
1. `GuideWindow`: chapter model and tabs; `[SkillClasses` unchanged. Tests for chapter coverage (every topic in exactly one chapter, at most six a chapter, no empty tab).
2. New file `GuideGettingStarted.cs` with the six (eight) topic builders; `WelcomeGuide.Topics` and `Commands` updated; the Welcome page points a newcomer to "Your first hour".
3. `WelcomeGuideTests` additions pinning each claim, and the existing rules (no staff command, no old shard name, no tagline repeat).
4. Evidence record `Guide-Getting-Started-Pages.md` with the claim-to-source audit table and the new player text for review.
5. README guide line updated.

**Verification.** Unit tests (claims, gating, layout counts). Live on a disposable host: a new character's guide opens on Welcome, the chapter tabs and every new page are read through Navrey. **Real client:** every new page and the tabs are photographed and sent to the owner. Nothing here needs a restart of a shared server beyond the normal deploy.

**Activation.** No flag. It ships with the next deploy of the shard DLL.

**Open questions (recommendation first).** (1) Chapter tabs, not paging arrows. (2) Add Pets and Dying: yes. (3) Per-skill training tips ("train Swordsmanship by fighting X"): not in this item; a later "what can I train at my skill?" window could be derived from the code (craft skill ranges, resource and creature thresholds) instead of hand-written advice, since the usual sources could not be reached. (4) Keep the new-character auto-open on Welcome with the pointer: yes.

**Out of scope.** Per-skill advice, a bestiary, a world atlas (information tools for a later pass), any rule change.

**Risks.** Page text goes stale when a rule changes: the tests tie each claim to code or config. The training page's price and cap come from stock code; if the shard later changes training the test fails.

---

## B. Accidental-crime guard rails and the criminal notice

**Goal.** A new player does not turn grey by accident, and a player who does knows what it means and for how long. Deliberate crime (stealing, attacking) is untouched.

**Current state (survey).** A player becomes criminal through `Mobile.CriminalAction` (`Mobile.cs:4591`); the flag lasts 2 minutes (`ExpireCriminalDelay`, `Mobile.cs:1865`) and expires silently. The only messages are "You've committed a criminal act!!" and, in guarded regions, "Guards can now be called on you!". Accident routes: helping a grey or red (helper turns criminal; healing, curing, bandages, spells), looting a blue player's corpse or a monster corpse inside its two-minute window (the stock corpse double-click already prints a warning; the crime fires per item on lift), and attacking a blue NPC. Consequences players are never told about: healers refuse a criminal, the banker refuses ("I will not do business with a criminal!"), Recall and gates refuse. `BuffIcon.CriminalStatus` exists and no stock code uses it. `TravelWarningService` is the pattern (confirmation gump with a "do not ask again" account tag).

**Design.**
- **Confirm before:** (1) helping a criminal or murderer, (2) lifting from a blue's corpse, and (3) optionally attacking a blue NPC. Because the engine gives no resume hook, each prompt refuses the act, shows a gump naming the victim and the consequences, and on "Yes" records a short approval (about 60 seconds, in memory) so the retried action passes. Hooks already exist in shard code: `AllowBeneficialHandler`, `Corpse.LootEligibility` (pre-lift, already used by `TheftProtectionService`), `AllowHarmful`. One "do not ask again" account setting per kind, `[CrimeWarning`.
- **Notice:** one narrow ModernUO hook, `Mobile.CriminalChanged(mobile, now)`, raised from the `Criminal` setter. The shard uses it to say once per episode: "You are a criminal for 2 minutes: guards in towns will attack you; healers, bankers, Recall and gates refuse you", and a short "You are no longer a criminal". It also feeds the buff icon (item F).
- Stealing is not prompted: it is the deliberate path.

**Work.** ModernUO hook and test; `CrimeWarningService.cs` (the prompts, the approvals, the notice); window text; tests; guide Fighting page and Commands; README line.

**Verification.** Unit tests for the decision table and approvals. Live: a blue helps a grey (prompt, refuse, approve, success, criminal with notice and expiry); loot a blue corpse; "do not ask again"; Intent-on target is not a crime; thieves unaffected. Real client: the gump, the notice line, and the expiry line.

**Activation.** A new flag `crimeGuardRails`, off until acknowledged (prompts change what players experience); the notice rides with it.

**Open questions.** Which prompts by default: helping and corpse looting yes; attacking blue NPCs only after audit lines show it happens. Default on for new characters, off for old ones? Recommendation: on for everyone, one-time "do not ask again".

**Risks.** Gump-then-retry is slightly clumsier than a true confirm; pet crimes flag the owner and cannot be intercepted (stated in the guide). A criminal in a Hot Zone is unaffected.

---

## C. Client defaults and the macro set

**Partly done 2026-10-07:** the 70% game view (`game_window_start_fraction`), the buff window opening by itself once, and the "ID:" line removed are built into the client (`Guide-Getting-Started-Pages.md` section 4, `Buff-Icons-Era-Text.md` section 4). The macro set, the top-bar cleanup and the other defaults below remain.

**Goal.** A new player's first login has sensible options and a small useful macro set; dead interface is removed.

**Current state (survey).** New profiles come from `Data/Profiles/default.json` if present, else code defaults; absent keys take the code default, so a minimal file works. Profiles are keyed by server name and the rename already reset every player's profile, so a seeded file reaches everyone once; later changes to existing players would need a versioned migration. Macros are seeded by hardcoded `CreateDefaultMacros` (needs a rebuild); there is no dress or undress macro and no loop. Dead interface: the top-bar "Global Chat" button prints "GlobalChat not implemented yet.", the Chat button opens an empty window, and `settings.json` points at a Razor plugin path that does not exist (an error logged at every start). `settings.admin.json` holds an admin password and must never ship.

**Design.** `default.json` (no rebuild): auto-open doors on, info bar on (name, hits, mana, stamina, weight, which matters with the starter weight rules), always run on, corpse grid loot on (display only, no bulk action), health bar over mobiles optional, pathfinding off (already). Client change plus rebuild: a default macro set (Last Target, Target Self, Next Target, bandage self, war or peace toggle, open door, close health bars; keys that do not collide with the stock set), hide the dead top-bar buttons, drop the missing plugin entry, auto-open the buff window (needed by F). No loops and no assistant features.

**Work.** `default.json`; `Profile`/`MacroManager`/top-bar edits in the ClassicUO fork; NativeAOT publish and copy to `bin/dist` (backup under `work/`); dist cleanup list (no admin file, no test profiles, no logs, no pdb).

**Verification.** A fresh profile on a disposable host: every default is read back from `profile.json`; macros listed in the macro gump; real-client screenshots of the options, the macro gump and the top bar.

**Activation.** None: it ships with the client. Players reach it at their next login (profile reset by the rename).

**Open questions.** Which defaults (recommended list above); which macros and keys; click-to-pathfind stays off (my recommendation, your decision); whether to ship the client more widely (how remote players get the client and `UOData` is not covered by anything in the workspace).

**Risks.** Existing profiles keep their old values after this one-time reach; `cuo.dll` and Navrey diverge (Navrey is not updated); a rebuild needs the documented procedure.

---

## D. Assistant negotiation

**Goal.** Third-party assistants cannot give looping macros, autoloot, auto-bandage or restock agents to those who use them, while attended play with plain macros is unaffected.

**Current state (survey).** `assistants.enableNegotiation` is `False` in the deployed `modernuo.json`; `assistants.json` allows all 25 features and is not in `ShardContent/data`, so the deploy script never touches it. With negotiation on, the server sends the handshake at login and starts a 30-second timer: a client that never answers gets a warning gump and is **kicked about 15 seconds later** (`kickOnFailure=false` does not prevent it, by reading the code). The workspace ClassicUO fork and Navrey both answer the handshake themselves after about 5 seconds, so they pass; it cannot be determined here whether other clients do. Only failures are logged.

**Design.** Turn negotiation on; disallow LoopedMacros, UseOnceAgent, RestockAgent, SellAgent, BuyAgent, AutolootAgent, BoneCutterAgent, JScriptMacros, AutoBandage, RandomTargets, ClosestTargets, EnemyTargetShare and SpellTargetShare; leave display and input helpers (auto-open doors, light and weather filters, overhead health) allowed. Move both files under `ShardContent/data/configuration` and have the deploy script write them so source and deployed cannot drift. Log successful responders (a three-line ModernUO edit) so staff can see who runs an assistant.

**Verification.** Unit test of the config; live: the fork client stays connected past 60 seconds with negotiation on; the log line shows the responder. The no-answer kick is stock code and is not exercised.

**Activation.** The owner acknowledges (it is a policy: a non-answering client is removed). **Open questions.** The exact disallow list; whether the kick for non-answering clients is wanted (it effectively limits players to clients that answer, which is a blessed-client rule). **Risks.** It binds only tools that announce themselves; AutoHotkey, OCR and AI agents sit outside it.

---

## G. Guild chat

**Goal.** Guild members can talk across the world.

**Current state (survey).** The old guild system has no chat in this era; the client already sends `\ text` as a guild message, but the server broadcasts it to everyone within 15 tiles and it never reaches remote guildmates (inferred; confirm live). `Guild.GuildChat(from, text)` exists, works without the new guild system and sends to every online member.

**Design.** Intercept speech of the guild type (and a `[g <message>` command), block the local broadcast and route it to `Guild.GuildChat`, honoring `Squelched` and writing a low-volume audit line. Shard code only; no engine edit.

**Verification.** Unit tests for routing; live with two guild members far apart; real-client screenshot of the line. **Activation.** None, or a small flag if the owner wants one. **Open questions.** Alliance chat is not included. **Observation, not in scope:** same-guild members can attack each other under SafeWorld because `IsGuildWarOrDuel` treats same-guild as allowed; worth a ruling separately.

---

## E. Help channel

**Goal.** A place to ask for help.

**Current state (survey).** `chat.enabled` is `False`. The client asks to open chat at every login and the server answers "The chat system has been disabled." (all 51 journals checked show it). The stock chat has a "Newbie Help" channel always created. Turning chat on makes the client try to join a channel called "General" at login, producing one stray message unless one exists. Gaps in stock chat: staff squelch does not mute it, no logging, no reachable ban, anyone can create channels.

**Design (needs a decision).** Option 1: enable chat with two channels, "General" and "Newbie Help", plus three shard additions (squelch respected, audit lines, channel creation limited to staff). Option 2: leave chat off and remove the noise from the client (item C hides the dead buttons; the login message stays server-side unless the packet handler is replaced). Recommendation: option 1 once there is a population to talk to; option 2 now.

**Open questions.** Which option; a volunteer Companion role is a community decision, not code.

---

## F. Buff-icon status bar (spike first)

**Built 2026-10-07 (owner sign-off with additions: data-driven, new icons, fix the UOR defensive spells, on at deploy, client fixes included):** see `Buff-Icons-Era-Text.md`. This replaces the build described below for the stock text, the missing UOR effects and the shard's own states (Knocked Out, Criminal, Intent, Ward, Faint Memories). Still open from this item: the criminal timer's countdown (needs the `Mobile.CriminalChanged` hook planned for B), and the root `README.md` buff-bar line at deploy.

**Goal.** A persistent, glanceable display of the shard's own states: Knocked Out countdown, Intent on or off, criminal timer, Ward state, secure camp, Faint Memories ready.

**Current state (survey).** `buffIcons.enable` is a plain server setting, `False` here, and enabling it also lights every stock buff icon (Bless, Curse, Hide, Paralyze, ...), a design choice. The client needs no feature bit for packet 0xDF. Only the 189 stock icons have art; candidates by name only: Knockout, CriminalStatus (unused by stock), Warding or Protection, Perfection or Honored. Custom text through a generic argument cliloc (1042971 and four others) is believed to work but is untested; the buff window is not opened automatically (a client change, item C); buffs are not saved, so the shard re-adds them at login.

**Spike (this comes before any plan).** On a disposable host: enable the setting, add one buff through a probe, photograph it in the real client, and confirm the art, the title text, the countdown and the icon positions. The plan for F is written from what the spike shows.

**Activation.** The owner decides whether stock buff icons come on with it.

---

## Decisions for the owner

1. Sign off item A: yes or no; chapter tabs; add Pets and Dying; keep Welcome as the auto-open page.
2. For B to G: answers to the open questions above, when you want each planned. Suggested: B (default-on prompts for helping and corpse looting), C (the default list and macros), D (the disallow list), G (yes), E (option 1 or 2).
3. Authorize the F spike (a disposable-host test only; no flag).
