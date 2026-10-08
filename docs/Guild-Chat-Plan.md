# Guild chat (Tier 1 item G): plan for sign-off

Status: **signed off by the owner on 2026-10-08 ("Ok, let's move forward with your plan"), taking all six recommendations in section 8 as written (a flag, off at deploy; ghosts may use it; the text is logged and the guide says so; Alliance answers "not available"; a `[g` command; the Commands page only plus a README line at activation). Also decided in the same conversation: the shard keeps the old guild system (design contract section 13, no post-era guild enhancements). Built and verified the same day (evidence: `Guild-Chat-Evidence.md`), then activated on 2026-10-08 on the owner's explicit "activate" and deployed.** Origin: the Tier 1 quality-of-life plan (`Tier-1-QoL-Plan.md`, item G) and the owner's "Let's tackle guild chat".

## 1. Goal and exit criteria

Guild members can talk to each other wherever they are in the world, with the client's own `\` key (and a `[g` command), and nobody outside the guild sees it.

Exit: a message typed with `\` or `[g` reaches every online member of the sender's guild and nobody else; a player with no guild is told so; a muted or Knocked Out player cannot use it; it never triggers a guard call, a pet order, a vendor or a command; it is checked live with two guild members far apart and in the real client; the flag ships off.

## 2. What happens today (read from the code)

- This shard runs the **old guild system** (`Guild.NewGuildSystem` is `Core.SE`, false here): guilds are made with a Guild Deed (12,450 gp at the Provisioner), run from a guildstone, and members are `Guild.Members`. The old system has no chat of its own.
- The ClassicUO fork already has the chat modes: a line starting with `\` is sent as a **Guild**-type message (the client labels it "[Guild]:"), and `|` as an **Alliance** one.
- The server's `PlayerMobile.DoSpeech` only handles those two types when `NewGuildSystem` is on. Here they fall through to ordinary speech, so a `\` message is **said aloud to everyone within 15 tiles, labelled "[Guild][Name]: text", whether or not they are in the speaker's guild, and whether or not the speaker has a guild at all.** It nearly works by accident for a guild standing together, and it never reaches a guildmate who is anywhere else. Because it goes through ordinary speech it also runs the speech listeners: the word "guards" in it calls guards (the guarded region does not look at the message type), a line starting with `[` runs as a command (the command handler does not either), and any pet or vendor within 15 tiles hears it as ordinary speech.
- The engine already has the right sender, `Guild.GuildChat(from, hue, text)`: it sends the line to every online member. The stock new-system `DoSpeech` branch shows the intended behavior (not in a guild: "You are not in a guild!"; remember the speaker's chosen colour; staff within 8 tiles see the line).
- Party chat (`/`) is a separate working system and is left alone.

## 3. Vision and design check

**Vision** ("draw players into contact with one another... build community"): chat inside a guild is the community tool a guild already is for; it does not replace going anywhere, and it keeps thieves, criminals and murderers as they are (a thieves' guild can talk too). **Constraints:** (1) no power or progression change; (2) no new safety or loss rule; (3) it works for a two-person guild; (4) every role can use it; (5) it needs no group. Owner's own tests (2026-10-07): changes a rule or mechanic? no (communication); power creep? no; keeps reasons to go places and meet? yes, nothing is moved or delivered; automates play? no; **stock first:** the behaviour is the engine's own new-system chat, brought to the old system. Era fit is not claimed.

## 4. Design, rule by rule (stock beside each)

| # | Rule | Stock (this build) |
| --- | --- | --- |
| 1 | A `\` (Guild) message from a player in a guild goes to **every online member of that guild, wherever they are, and to nobody else**, shown by the client as "[Guild][Name]: text" in the sender's chosen colour. | Said aloud to everyone within 15 tiles, guild or not |
| 2 | Not in a guild: the sender is told "You are not in a guild." and nothing is sent. | Said aloud |
| 3 | It never reaches the world's speech listeners: no guard call, no pet order, no vendor, no command, no reveal of a hidden sender (the same as the engine's own new-system chat). | All of those can trigger |
| 4 | A muted (Squelched) player cannot use it ("You can not say anything, you have been squelched."). A **Knocked Out** player cannot use it (as for all speech). | Squelch yes, Knocked Out yes (both ordinary speech) |
| 5 | A dead player **can** use it (the commonest use will be "I died at X, need a res"). | n/a |
| 6 | `[g <message>` does the same from the keyboard for players who do not use the `\` key; `[g` alone says how to use it. | none |
| 7 | An Alliance (`|`) message gets "Alliance chat is not available here." and is not said aloud. | Said aloud, labelled "[Alliance]" |
| 8 | Staff of higher rank within 8 tiles of the sender see the line (the engine's own monitoring, kept). | Same, in the new system |
| 9 | Each message is written to the server log (sender, guild, text) for moderation, and the guide says guild chat is logged. | none |
| 10 | With the flag **off**, `\` behaves exactly as today. | n/a |

## 5. Work breakdown

1. **ModernUO, one narrow hook** (the smallest that keeps guard calls and commands out): `PlayerMobile.GuildSpeechHandler`, an optional shard-owned delegate called from `PlayerMobile.DoSpeech` for a Guild or Alliance message before the ordinary speech path runs, returning true when it handled the line. Null keeps the stock path. A test in `PlayerMobileShardHookTests`. This needs the usual cycle: rebuild `UOContent` into `Distribution`, bump the ModernUO pin in the three places, redeploy.
2. **ShardContent**: `GuildChatService` (the rule as a pure function of the sender's state, the routing to `Guild.GuildChat`, the `[g` command, the log line, the texts) registered once behind a guard, and the flag `guildChat` (off, no other requirement) in the validated configuration.
3. **Text**: `[g` and `\` in the guide's Commands page and a sentence in "Your first hour" or Rules if you want one; a README line when it goes on.
4. **Tests**: the rule table, the texts, the flag and its validation, the hook; test-only probe verb to make a guild and to say a Guild-type line as a player (a double-click in the real client cannot be scripted, the probe calls `DoSpeech`).

## 6. Verification

- **Unit:** the rule table (in a guild, no guild, muted, Knocked Out, dead, hidden, Alliance, empty text), texts, flag validation; hook test in UOContent.
- **Live on a disposable host with Navrey:** two guild members far apart (one receives, with the right name and colour), a third player standing next to the sender who is **not** in the guild hears nothing, a guild-less sender is told, a muted sender is refused, "guards" in a guild line calls no guards, a `[` line runs no command, `[g` does the same as `\`, a hidden sender stays hidden, a dead sender is heard, staff within 8 tiles see it, the log line is written, the flag off leaves `\` as it is today.
- **Real client, shown to you:** two real clients, the `\` mode label, the journal line on the far guildmate's screen, the "not in a guild" reply, and the guide's Commands page.
- No save-format change (the chat colour is already saved). No snapshot needed.

## 7. Activation

A new flag, **`guildChat`, off when deployed**, so you can see it on the dev host before it counts. It needs your explicit "activate". With it off nothing changes for players, including `\`.

## 8. Open questions (recommendation first)

1. **A flag, or live at deploy?** Recommended: a flag, off at deploy.
2. **Ghosts may use guild chat?** Recommended: yes (stock's own chat allows it, and "I died here, res me" is its best use). Alternative: living members only hear a ghost if they are dead too.
3. **Log the text of guild chat for moderation?** Recommended: yes, one line per message in the server log, with a sentence in the guide saying so. Alternative: log only that a message was sent (who, which guild, length), which protects privacy and loses the ability to investigate abuse.
4. **Alliance (`|`):** recommended: not now; it answers "not available" rather than shouting "[Alliance]" at bystanders. Alternative: send it to allied guilds too (the old system has an ally list), as a later item.
5. **A `[g` command** as well as the `\` key: recommended yes (cheap, and the test tooling can use it).
6. **Guide:** recommended: the Commands page only, plus a README line at activation. Alternative: a short "Guilds" page.

## 9. Out of scope / deferred

Alliance chat; a message cooldown or flood limit (the stock chat has none); per-member mute or a channel on/off setting (the client's own journal option can hide guild lines); guild ranks that can speak or not (the old system has none); guild message history; the unrelated observation that same-guild members can attack each other under Safe World (`IsGuildWarOrDuel`), which still wants its own ruling.

## 10. Risks and ordering

- The hook edits `PlayerMobile.DoSpeech`'s entry, a hot path for every spoken line, but only for a Guild or Alliance message, and the delegate is null unless the shard fills it: no cost for ordinary speech.
- A deploy needs the engine rebuilt first and the pin bumped (the documented cycle, as for the other hooks).
- Guilds are made with a 12,450 gp deed, so on a young shard few guilds exist at first; that is a fact, not a problem with the chat.
- Build order: the hook and its test, then the service and flag, then the probe, the live pass, the real-client pictures, the evidence and readiness records.
