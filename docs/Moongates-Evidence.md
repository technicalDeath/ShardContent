# Moongates page, and the starting-town finding (2026-10-13)

Part of the owner's "keep going with QoL changes" (autonomous, while the owner was away). Help text only: a new Welcome-guide page, **Moongates** (Travel tab), a "Where to go" paragraph on **Your first hour** and the same pointer on the **Welcome** page (the first page a new character sees), and two paragraphs on **Your screen** (numbers over heads, buff icons). No server rule, flag or client code changed.

## The finding that prompted it (needs an owner ruling)

World generation keeps the town NPCs of **Britain only** (`britainOnlySpawnerFiles`: `TownsPeople.json`, `Vendors.json` in `data/world-generation/alpha2b/world-generation.json`). Checked in the generated data (`ModernUO/Distribution/Data/BritanniaRenaissance/Alpha2b/Spawns`): every shopkeeper, banker, healer, trainer and guildmaster type is spawned in `Vendors.json` (x 1296 to 1650, y 1525 to 1826, all inside Britain) or `britain-vendor-overrides.json`; no other spawn file has one (the only other town NPCs are two Town Criers, both in Britain). Resurrecting Wandering Healers are spread over the wilds (179 spawners).

But character creation offers **nine starting towns** (stock `CharacterCreation.FeluccaStartingCities`: Yew, Minoc, Britain, Moonglow, Trinsic, Magincia, Jhelom, Skara Brae, Vesper) and the shard does not restrict the list. A new player who picks any of the other eight begins in a fallen town with no shop, no bank, no healer and no trainer, and the guide never said where to go. Vesper is worse: it has no moongate (`PMList.Felucca` has nine gates and none at Vesper; Minoc's, about 290 tiles from Vesper's starting inn, is the nearest).

**What was done (text only):** the Moongates page and the "Where to go" paragraph say it plainly and say how to get to Britain.

**Ruled 2026-10-13: "Offer only Britain", built: see `Britain-Start-Evidence.md`.** The question was: should new characters be limited to starting in Britain? Options: leave it (the text now explains it); offer only Britain in the creation list (a narrow engine hook on `CharacterCreation.GetStartingCities`, which caches a private array); or accept any choice but place the new character at Britain's inn. Nothing was built for it. It touches the roadmap's town-housing idea (`towns-as-housing-idea`), so it is the owner's call.

## What the new page says, and where each fact comes from

| Statement | Source |
| --- | --- |
| Britain is the only town with shopkeepers, bankers, healers, trainers and guildmasters | the spawn data above |
| The Britain gate stands in open country south of the town, outside the walls; walk north | the gate is at (1336, 1997, 5) (`PMList.Felucca`), the world-generation `britainBounds` end at y 1900, and the real client showed a stone circle in grassland there (`g3-britaingate.png`) |
| Gates at Moonglow, Britain, Jhelom, Yew, Minoc, Trinsic, Skara Brae, New Magincia, Buccaneer's Den; none at Vesper | `PMList.Felucca`; the real client's destination list showed exactly those nine (`g2-gategump.png`); the manifest expects 9 gates (a test pins it) |
| Stand next to the gate, double-click, choose, Okay | `MoongateGump` (the gate must be within 1 tile), real client |
| No use while a criminal, in a fight or casting | `PublicMoongate`'s travel checks (messages 1005561, 1005564, 1049616) |
| It puts you at peace and hides you; following pets within three steps come along | the same method (`Warmode = false`, `Hidden = true`) and `BaseCreature.TeleportPets` (range 3, Guard/Follow/Come orders); the hidden icon showed on arrival |
| Buccaneer's Den is a Hot Zone; a window warns you first | the `BuccaneersDenIsland` Hot Zone region in `shard-rules.json`; `TravelWarningService` through the `SpellHelper.TravelConfirmation` hook (flag `hotZoneTravelWarning`, on); the paragraph appears only while both Hot Zones and the warning are on |
| The Map button; camp travel | the top bar (`MenuBar`), `CampTravelService` |

The two "Your screen" additions: damage and heal numbers (flags `damageNumbers`, `healNumbers`; yellow over you, red over anything else, green +N for a heal, both only for your own fights, switch under Options > Combat-Spells; `Combat-Numbers-Evidence.md`) and **The buff icons** (stock `buffIcons.enable` plus the shard's own states; each named only while its rule exists: Criminal Intent, Backpack Ward, Faint Memories, Hot Zone, secure camp).

## Tests

`GuideGettingStartedTests`: the page's claims, the nine towns, the Hot Zone sentence's gating, the first-hour pointer, and the Travel tab now always holding at least the gates page. `GuideScreenTopicTests`: the numbers and the buff paragraph, each only while its switch is on, and the buff list leaving out what the shard lacks. Shard suite: 1357 passed (run `20261013T183415276Z-d6fb96`).

## Real client (disposable host `help-check`, character begun in Yew)

- Yew's gate: a blue gate in a ring of standing stones; double-click opened the stock destination list ("Pick your destination", Felucca tab, nine towns); choosing Britain and Okay carried the character to Britain's gate, hidden (the second buff icon appeared) (`g1`, `g2`, `g3`).
- The Moongates page (Travel tab, with Camping and Camp travel beside it), read to the end, no clipped line (`m1`, `m2`); the "Where to go" paragraph on Your first hour (`m3`); the Your screen additions (`s1` to `s3`).
- Pictures are in `work/player-client/HelpTrain/shots/` (`20261013-143134-g1-yewgate.png`, `...143146-g2-gategump.png`, `...143208-g3-britaingate.png`, `...143453-m1-travel.png`, `...143508-m2-travel-end.png`, `...143515-m3-firsthour.png`, `20261013-142724-s2-screen.png`, `...142727-s3-screen.png`).
- Deployed to the dev distribution (server stopped).

## Limits

- The stock destination window ("Pick your destination") is not a shard window and does not follow the Gump Style Guide; it was left as it is.
- The destination list names "New Magincia" (the client's own text for that gate). Whether New Magincia belongs in an April 2000 world was not checked.
- Travel from a gate while Intent is on, or the Hot Zone confirmation window itself, was not exercised this time (the confirmation has its own evidence in `Beta-2b-Camp-Travel-Plan.md`).
