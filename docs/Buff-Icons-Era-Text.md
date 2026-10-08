# Buff bar: era-correct text, the missing UOR effects, and the shard's own icons

Status: **built and checked 2026-10-07; committed (`067e3c1`), pushed and deployed 2026-10-07.** Owner rulings 2026-10-07: the text must be era-accurate and **driven by data**; generate any icons that are needed; make Protection, Reactive Armor and the like show buffs properly; **turn it on at deploy**; include the two small client fixes (the buff window opens by itself, the debug "ID:" line goes). This closes the question raised in `Buff-Icon-Spike.md` (stock tooltips are AoS wording) and delivers the buff-bar half of Tier 1 items F and C (`Tier-1-QoL-Plan.md`).

## 1. What was wrong, and what is true on this shard

The stock server setting `buffIcons.enable` lights every stock buff icon, with the later eras' text (percentages, resistances). On this shard (UOR, non-AoS paths, read from the code):

| Effect | What it really does | Source |
| --- | --- | --- |
| Bless, Strength, Agility, Cunning | Adds a **flat** `1 + Magery / 10` points (11 at 100 Magery) for `6 × Magery / 5` seconds | `SpellHelper.GetOffset`, `GetDuration` |
| Curse, Clumsy, Feeblemind, Weaken | The same flat number taken away. The stock tooltip said "-17%" and listed four resistance penalties | same |
| Protection (UOR) | A cast that is not interrupted by a hit with the registry's chance (tenths of a percent, 0 to 75%), for `Magery × 2` seconds (15 to 240). **Stock adds no icon in UOR** (only the AoS toggle did) | `ProtectionSpell.OnCast`, `Spell.OnCasterHurt` |
| Reactive Armor (UOR) | A pool of 1 to 75 points: a hit smaller than the pool is absorbed and a fifth of it sent back; a hit as big as what is left ends it. No icon in stock | `ReactiveArmorSpell.HandleMeleeHit` |
| Magic Reflect (UOR) | A pool of 8 to 15 points; each reflected spell uses its circle plus one. No icon in stock | `SpellHelper.CheckReflect` |
| Arch Protection (UOR) | Raises armor by `Magery / 10 + 1` for `min(144, Magery × 1.2)` seconds, in an area. No icon in stock | `ArchProtectionSpell` |
| Poison, Polymorph | State on the mobile; no stock icon in UOR | `Mobile.Poison`, `BodyMod` |
| Meditating | Mana regeneration is halved in time (doubled) while meditating, so the stock "Double mana regeneration rate" is true | `RegenRates` |

## 2. How it works

- **`buff-icons.json`** (`data/configuration/`, deployed to `Distribution/Configuration/` by `Deploy-Alpha1Baseline.ps1`) is the table. `stock`: the engine's own icons, each with a title and lines. `states`: icons the shard adds while a state holds. `customIcons`: icons the stock list lacks (name, slot, art id). `unlistedStockIcons: "hide"`: a stock icon not in the table is never shown, so a later era's effect cannot leak in. A loader (`BuffIconRulesLoader`) checks it at startup and stops the server on a bad file; the checks are in `BuffIconRulesTests`.
- **Named values.** A line may use `{buff.Str}`, `{curse.Dex}` (read from the stat mod the spell applied, so the tooltip equals the stat change) or a state's own values (`{points}`, `{chance}`, `{level}`, `{minutes}`, `{caught}`, `{unlock}`). A line whose value is unknown is left out. The vocabulary is `BuffIconCatalog` in `BuffIconRules.cs`.
- **Hook** (`UOContent`, three lines in `PlayerMobile.AddBuff` plus `BuffInfo.Override` and `BuffInfo.Present`, tested in `BuffInfoOverrideTests`): every stock spell, skill and potion adds its icon through `AddBuff`, so the shard rewrites or hides it there.
- **End times** (`UOContent`, read-only, no change in behavior): Protection, Arch Protection and Polymorph each end on a private timer, so each now also notes when it will end at the moment it starts (`ProtectionSpell.TryGetEnd`, `ArchProtectionSpell.TryGetEffect`, which also gives the armor bonus, and `PolymorphSpell.TryGetEnd` and `UnderEffect`). The watch reads those for the countdown. An earlier version worked Protection's end out from the player's Magery the first time it saw the effect, and guessed Polymorph from the body; that is gone.
- **The watch** (`BuffIconService`): once a second, for each online player, every state in the table is read from public game state (spell registries, the absorb pools, `Mobile.Poison`, the Knocked Out, Intent, Ward and Faint Memories services) and the icons are added, updated or removed to match (`Diff`, pure and tested). No spell or service needed to change beyond the three end-time notes above. The icons are kept through death, because the engine strips every other buff then and the watch is what removes these.
- **Text format.** Every icon is sent with the client's generic title (`~1_NOTHING~`) and our text, "Title<br>line<br>line", so title and lines both come from the data. Checked in the client: `<br>` renders as separate lines.
- **Countdown.** Shown only when the state knows its end and it is under about 9 hours: the engine's buff packet holds the time left in a signed 16-bit number of seconds (an unfixed 24-hour Faint Memories countdown read 5:28). Faint Memories says "unlock in about N hours" in its text instead, which changes hourly.
- **Staff:** `[BuffIconStatus` shows the setting, the table sizes and the shard-added icons you have.

## 3. The icons

| Icon | Art | Shown when |
| --- | --- | --- |
| Clumsy, Feeblemind, Weaken, Agility, Cunning, Strength, Bless, Curse | stock | the spell is on you; text with the real numbers |
| Night Sight, Hidden, Meditating, Invisible, Incognito, Paralyzed | stock | the engine adds them; plain UOR wording |
| Protection, Arch Protection, Polymorph | stock | the UOR effect is active, with a countdown to its real end (Arch Protection also says how much armor it gave) |
| Reactive Armor, Magic Reflection | stock | the UOR effect is active; they end by use, not time, so they show the points left and update as they are used |
| Poisoned (with the level) | stock | on you |
| Knocked Out (countdown), Criminal | stock (KO, collar) | on you |
| Criminal Intent | **new**, red crossed swords | `[Intent` is on |
| Backpack Ward: Primed / Activated (countdown to expiry) | **new**, green backpack | a Ward in your pack is tracking thieves or has caught one |
| Faint Memories (locked, then ready) | **new**, blue book and spark | you have points left |

Not covered: Hot Zone presence, Skill Bank balance, Mastery (not timed effects; the data can add them later by adding a state to `BuffStateProbes`). Later-era icons (Necromancy, Chivalry and so on) are hidden by the table.

New art: `ShardContent/tools/buff-icon-art/make_buff_icons.py` draws them in the stock icons' look (28 x 28, colour glowing to the middle, white halo, dark outline; green a help, red a harm, blue neither) and writes `data/client/gumps/<art>.gump` and `data/client/buff-extra.txt` from the `customIcons` in the data file. `BuffIconClientFilesTests` checks the table and the picture files.

## 4. Client changes (ClassicUO fork, committed in `15f914288`; new `cuo.dll` built and in `bin/dist`, the previous one backed up in `work/client-dist-backups/2026-10-07-before-buff-icons/`)

- `Data/Client/buff-extra.txt` is appended to the icon table (`BuffTable.cs`); server icon `0x4A6 + k` is line k.
- Custom picture files are now read from the client's own `Data/Gumps` as well as `<UO folder>/Gumps` (`GumpsLoader.LoadOurs`). The fork only looked in the UO folder, the player's own install, which the shard cannot ship files into; found when the new icons drew as gaps.
- The "ID: <name>" line is gone from every buff tooltip, and the three buff texts are no longer forced to Title Case (`BuffGump.cs`, `PacketHandlers.BuffDebuff`).
- The buff window opens once, by itself, for a character that has never had it (`Profile.BuffWindowOffered`, `GameScene.OfferBuffWindow`); after that it stays as the player leaves it, and a saved window still comes back.
- Dist files to copy by hand after a rebuild (noted in `CLAUDE.md`): `cuo.dll`, `cuo.pdb`, `Data/Client/buff-extra.txt`, `Data/Gumps/*.gump`.

## 5. Verification

- **Unit:** Shard suite 940 pass (`BuffIconRulesTests`, `BuffIconClientFilesTests`: the shipped file validates, every stock icon the engine adds in UOR has text, later-era icons are not listed, no line mentions resistance or puts a percent on a flat stat, the table and the catalog of states agree, custom ids follow the last stock id, rendering, the stock rewrite, the add/update/remove decision, the validator's complaints, the picture files); `UOContent` suite 1365 pass, 2 skipped as before (`BuffInfoOverrideTests`); client `StartGameWindowSizeTests` from the earlier item pass.
- **Real client, disposable host `qol`, a new character through a new profile** (screenshots in `work/player-client/Cedric/shots/`, scratch): the window opened by itself at first login; Bless (+11 each, countdown), Curse (-11 each), Clumsy, Feeblemind and Weaken read correctly with no "ID:" line; Protection (27% after the character's own skills, countdown 3:10), Reactive Armor (36 points left), Magic Reflection (11 points left), Arch Protection, Poison (Greater), Polymorph, Criminal, Knocked Out (countdown), Ward Primed (countdown 29:12) and Faint Memories were each added, read, and removed when the state ended; the three new icons draw in the stock style; Intent toggled on and off added and removed its icon; death removed Bless and kept the shard icons; two later-era icons added through the engine (Mortal Strike, Enemy of One) were not shown; `[BuffIconStatus` answered.
- **Found and fixed on the way:** the 16-bit countdown (above); the client's custom-art folder (above); a first host build compiled against the dev engine DLLs, which lack the hook (the test host now builds against the staged engine, as the verification runner does).

## 6. Player-facing text for the owner's review

All of it is in `buff-icons.json`; change it there. Titles and lines as shown:

- Clumsy "-N Dexterity."; Feeblemind "-N Intelligence."; Weaken "-N Strength."; Agility "+N Dexterity."; Cunning "+N Intelligence."; Strength "+N Strength."; Bless "+N Strength. +N Dexterity. +N Intelligence."; Curse "-N Strength. -N Dexterity. -N Intelligence."
- Night Sight "You can see in the dark."; Hidden "You are hidden."; Meditating "Your mana regenerates twice as fast."; Invisible "You are invisible."; Incognito "You are disguised."; Paralyzed "You are frozen and cannot move."
- Protection "Each hit has a N% chance of not interrupting your spell."; Arch Protection "Your armor rating is raised by N."; Reactive Armor "Absorbs melee hits and sends a fifth of the damage back. N points left; a hit of that size or more ends it."; Magic Reflection "Reflects spells cast at you. N points left; each spell uses its circle plus one."
- Poisoned "<Level> poison. You lose health until it wears off or you are cured."; Polymorph "You have taken another form."
- Knocked Out "You cannot act until you recover."; Criminal "Guards will attack you, and anyone may attack you."; Criminal Intent "While it is on you appear grey and other players may attack you. Killing a player who has it on is not murder. Type [Intent to turn it off."
- Backpack Ward: Primed "It is tracking thieves who steal from you. After N minutes without a theft attempt it resets."; Activated "A thief it caught cannot steal from you again. Thieves caught: N. After N minutes without a theft attempt it is used up."
- Faint Memories "N free skill points unlock in about H hours. Type [SkillBank to see them." / "N free skill points are ready. Train a skill set to Up and they come back to you. Type [SkillBank to see them."

## 7. Named limits

- Reactive Armor, Magic Reflection and Poison show no countdown: the first two end when used up, and poison ends by its own ticks, not at a set time.
- Criminal shows no countdown: the timer is inside the engine's `Mobile` (not changed here), and a repeated criminal act restarts it silently.
- Icons appear and go within about a second of the state changing. When one in the middle of the bar ends, the others shift left.
- A curse that is not stronger than the curses already on you does nothing, and so adds no icon (stock rule).
- The buff window still has to be opened by players who closed it, from the orb in the Status window or the macro; it opens by itself once.
- The art is mine; the owner may want it redrawn.

## 8. Deploy notes

Order: rebuild `UOContent.csproj` into `Distribution` (the hook), then `Deploy-Alpha1Baseline.ps1` (it copies `buff-icons.json` and sets `buffIcons.enable` True through `modernuo-era-gates.json`). Client: copy the four items in section 4 into the player dist. The root `README.md` rules section should gain a buff bar line at the deploy; the Welcome guide does not mention the bar yet.
