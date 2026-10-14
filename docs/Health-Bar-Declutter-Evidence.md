# Health bars: left out at full health, and a clear look for threats (2026-10-13)

Owner request, 2026-10-13: "the client should not show health bars for friendly npcs or players if their health is full ... If a bar goes from not full to full, it should not disappear immediately. It should only disappear after a small timeout (5s) as long as the bar is still full. The goal is less visual clutter and the player can learn that the absence of a bar means full health." Then: "the same way for neutral npcs like animals", "does the hostile's bar have a different treatment than a friendly? It's hard to tell. Would be nice for it to be obvious", and "that red frame looks ugly". Client only (ClassicUO fork); no server rule, flag or engine change. Built, checked in the real client on a disposable host, installed in `ClassicUO/bin/dist` (the new `cuo.dll`); **uncommitted**.

## What the client does now

The bars drawn in the world under characters (the stock `HealthLinesManager`; the shard's default is the line form for every mobile) follow these rules. Health bar windows a player opens on purpose (click, party, paperdoll Status) are not touched.

| Who | At full health | Hurt |
| --- | --- | --- |
| Your own character | no bar | small teal bar |
| Blue (innocent) players and townspeople, green (guildmates, pets), yellow (invulnerable: shopkeepers, bankers) | no bar | small teal bar |
| Grey creatures that are not human-shaped (animals, and wild monsters until they are flagged) | no bar | small teal bar |
| **Anything that could attack you**: criminals, red and orange characters, a monster flagged criminal because it is attacking, a grey human-shaped character (a player with Criminal Intent on, or a staff character) | always a bar, **wider (50 px instead of 34) with an amber fill instead of teal** | the same wide bar, the lost part crimson |

- **The linger:** a friendly or neutral bar that has just reached full health stays **5 seconds** and then goes, but only if the character is still full; losing health puts the bar back at once and the five seconds start again at the next fill. Measured in the real client: bar still there 1.5 s and 4.3 s after the heal, gone at 5.8 s (`FriendlyHealthTracker`, 5,000 ms, wraparound-safe). A character first seen at full health never gets a bar.
- **Targeted characters:** a targeted or last-attacked friend is left out too (one rule for everyone, so a missing bar always means full health). The optional new-target frame (`useNewTargetSystem`, off by default) still draws its own frame.
- **Option:** Options > Mobiles has "Hide full health bars of friendly and neutral characters" (profile key `hide_full_friendly_health`, on by default for everyone, including existing profiles; Default puts it back on).
- **Guide:** a new "Bars and numbers" page on the Start here tab explains it (health bars, then the damage and heal numbers, the buff icons and the item tooltips, which moved there from "Your screen", which had hit its line limit).

## The finding behind "neutral"

The server colours every wild non-human creature **grey**, orcs and sheep alike (`MobileNotoriety`: only an `AlwaysMurderer` creature is red; the rest of the wild ones are `CanBeAttacked`). So the client cannot tell an idle orc from a sheep by colour. In the test an idle orc was grey (no bar at full health, like a sheep) and became **criminal-flagged** once it attacked, which is what turns its bar wide and amber. So: an idle monster that has not engaged anyone has no bar at full health; one that is attacking or flagged does. If you want bars kept on every monster at full health, the server would have to tell the client which creatures are aggressive (a small shard command); say so.

## Evidence

- Client unit tests: `FriendlyHealthTrackerTests` (19: who is quiet by colour and body, the five seconds, losing health, a second character, clock wraparound, pruning); the whole `ClassicUO.UnitTests` project 250 of 250.
- Shard tests: 1384 passed (run `20261013T202059933Z-bfb226`), including the guide page and the topic order.
- Real client, disposable host `hp-check` (characters HbA, HbB; a staff character; a sheep and an orc added and frozen so they stayed put; `[set Hits` and `[TestOnlyHurt` to hurt and heal), shown to the owner: everyone at full health (no bar over the player, the other player or the banker); a friendly player hurt, healed and photographed at 1.5, 4.3, 5.8 and 7.3 seconds; an animal and a hostile orc hurt and healed (the animal's bar went after about 5 s, the hostile's stayed); the red-framed first version, the owner's "ugly" verdict, then the amber version (wide amber against small teal, full and hurt); the new guide page.
- Deployed to the dev distribution (guide change; server stopped).

## Limits

- The nameplates that show with the Names button have their own thin health line; they were not changed.
- "Could attack you" is judged by colour and body shape only (see the finding). A grey human-shaped NPC would count as a threat.
- Not exercised: a pet's bar, a mounted character, a guild war (orange) enemy, and a window other than about 1,300 px wide.
- While staging, HbA's worn gear ended up in its backpack once with no command of mine that explains it; it did not repeat and is not related to this change, but if it ever shows up for a real player it is worth a look.

## Files

ClassicUO: `Game/Managers/FriendlyHealthTracker.cs` (new), `Game/Managers/HealthLinesManager.cs`, `Configuration/Profile.cs` (`HideFullFriendlyHealth`), `Game/UI/Gumps/OptionsGump.cs`, `tests/ClassicUO.UnitTests/Game/Managers/FriendlyHealthTrackerTests.cs`. ShardContent: `WelcomeGuide.GettingStarted.cs` (`SeenTopic`), `WelcomeGuide.cs`, `tests/GuideScreenTopicTests.cs`, `tests/WelcomeGuideTests.cs`.
