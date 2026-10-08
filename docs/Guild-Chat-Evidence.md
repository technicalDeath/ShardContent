# Guild chat (evidence and readiness)

Status: **built and verified 2026-10-08; ACTIVATED, committed, pushed and deployed 2026-10-08** on the owner's "Commit, push, deploy and activate". The plan and the owner's sign-off are in `Guild-Chat-Plan.md` (all six recommendations approved on 2026-10-08). The flag **`guildChat` is on** (enabled on the owner's explicit "activate"). The shard keeps the old guild system (design contract section 13; the new one was considered and rejected the same day).

## 1. What was built

| Where | Change |
| --- | --- |
| ModernUO `PlayerMobile.cs` | One optional hook, `GuildSpeechHandler`, asked from `DoSpeech` for a Guild or Alliance line outside the new guild system, before the ordinary speech path. Null (or false) keeps the stock path. The new guild system keeps its own chat and never asks. Test: `PlayerMobileShardHookTests` (5 tests) |
| `GuildChatService.cs` (new) | The rule `Decide`, the routing to `Guild.GuildChat`, the `[g` command, the staff monitor, the log line, the texts. Registered once behind a guard; the previous handler, if any, is kept |
| `ShardRulesConfiguration.cs`, `shard-rules.json` | Flag `guildChat` (on since 2026-10-08, no other requirement) |
| `WelcomeGuide.cs` | The Commands page lists `[g` (and the `\` key) and says guild chat is logged, only when the flag is on |
| Test tooling | `TestOnlyProbe` verb `[TestOnlyGuild` (found a guild, no guildstone); `tests/scenarios/guild-chat/guild_chat_live.py` |

## 2. The rules as built

- A Guild line (`\`, or `[g text`) from a player in a guild goes to every online member of that guild wherever they are, and to the sender, in the colour the client chose (remembered for `[g`); to nobody else.
- No guild: "You are not in a guild." A squelched player: "You can not say anything, you have been squelched." A Knocked Out player: "You cannot speak while you are Knocked Out." An Alliance line: "Alliance chat is not available here." An empty line sends nothing and says nothing.
- A ghost can use it; a hidden speaker is not revealed (the line never reaches the speech path); the line never reaches the speech listeners, so it cannot call guards or run a command.
- Staff of higher rank within 8 tiles see the line as `[Guild]: text`, as the engine's own chat shows them.
- Every sent line is written to the server log (`guild-chat message`, with the speaker, the guild and the text); refused lines are not. The guide says "Guild chat is logged for moderation."
- With the flag off, `\` behaves as before and `[g` answers "Guild chat is not available." (the flag is on in the shipped file)

## 3. Verification

**Unit tests** (run `20261008T203424112Z-63fe88`): UOContent 1374 pass (5 new), Shard 1050 pass (25 new, `GuildChatTests`): the rule table in every combination, the refusal texts, the colour, the log line, the guide line (no angle brackets, which the window would swallow as a tag), the flag file and its validation.

**Live, disposable host, Navrey:** 

**Real client:** 

## 4. Player text for review

Only with the flag on:
- Commands page: "[g - Talk to your guild wherever its members are: type [g and then your message (the \ key does the same). Guild chat is logged for moderation."
- `[g` alone: "Type [g followed by your message to talk to your guild, or start a line with the \ key. Guild chat is logged for moderation."
- Refusals: the four texts above (the squelch text is the engine's own).

**README** (applied at activation, after the Camp travel line): "**Guild chat.** `\` or `[g <message>` talks to every online member of your guild wherever they are. It is logged for moderation. Alliance chat is not available."

## 5. Named limits

- Alliance chat (`|`) is not available; the old system's ally list is not used.
- No flood limit or cooldown (the stock chat has none).
- A Knocked Out player cannot speak, as for all speech.
- Guilds are founded with a Guild Deed (12,450 gp) in a house, so there will be few guilds at first.
- The same-guild attack observation under Safe World is a separate ruling (not part of this item).

## 6. Shipping

Activated on the owner's explicit "activate" (2026-10-08): `guildChat` is `true` in `shard-rules.json` and the README has the Guild chat line. Deployed with the engine rebuilt first (the hook): ModernUO committed as `674e0c2ed`, the pin moved in the three places, `UOContent` rebuilt into `Distribution`, then `Deploy-Alpha1Baseline.ps1`. No save-format change.
