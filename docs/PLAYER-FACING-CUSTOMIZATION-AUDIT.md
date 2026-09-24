# Player-facing customization audit

Recorded: 2026-09-23  
Baseline: UOR, Felucca only, integration-pinned ModernUO commit
`90e8517b9e978a4e36821259888dd62bf634c3ab` (UOR baseline reference
`29a3ab1bd443b9c2a8ff6bf34f4df47d9f837895`)

This audit distinguishes active runtime behavior from planning documents and staff/development
tools. A roadmap item is not an advertised game feature until it has server implementation,
an enabled policy flag, and player-facing messaging where the player needs it.

| Customization or surface | Active state | Player-facing result | Audit outcome |
| --- | --- | --- | --- |
| UOR / Felucca-only baseline | `expansion.json` exposes only Felucca and disables post-UOR feature bits and map selection. | Players are not offered later-era maps or expansion capability. | Accurate. |
| Skill and stat caps | Shard policy is 700 total skill, 100 individual skill, 225 stats. | Server remains authoritative; no conflicting client claim was added. | Accurate. |
| Insurance, veteran rewards, ML quests, pet bonding | The deployment gate writes all six controls as `False`. | No shard-specific player promise or UI was added for those unavailable systems. | Accurate. |
| Original automatic weapon procs | Concussion, Crushing, and Paralyzing hit-resolution branches are removed. | They are not offered by the UOR ConPVP ruleset. | Accurate. |
| Wrestling Stun and Disarm | Requests clear state and send an explicit disabled-on-this-shard message; swings clear stale saved state. | Legacy/third-party clients may retain generic ability buttons, but attempting either move is explained by the server. | Mitigated; server is authoritative. |
| ConPVP duel defaults | The pre-AoS `Combat Abilities` category and its Stun defaults are removed. | The server-side duel rules gump does not advertise the removed moves. | Accurate. |
| Deferred Safe World, Hot/Cool Zones, housing geography, expeditions, pilgrimage, road speed, retention content | Every policy flag is `false`; no runtime implementation is present. | None of these future features is presented in-game. Large planning documents are repository documentation only. | Accurate. |
| `[ShardRulesStatus` | Staff-only diagnostic command reports the active baseline and disabled combat specials. | Administrators receive a truthful status summary; ordinary players do not see it. | Accurate. |
| Navrey `createcharacter` command | Development-agent client command creates a human only on an empty account and uses normal client creation. | It is not a player client feature or server entitlement; the server validates the result. | Accurate. |

## Residual legacy-client limitation

Classic UO clients do not receive a protocol capability flag that says “hide pre-AoS Wrestling
Stun/Disarm.” A generic client can therefore render its own ability book, buttons, or hotkeys
even when the shard has disabled the server behavior. The explicit server rejection is the
portable, authoritative disclosure for every compatible client. Do not describe those moves as
available in shard guides, welcome gumps, vendor books, or web copy unless the policy changes.

## Release check

Before a public release, repeat this audit whenever a policy flag, shard command, login text,
welcome gump, in-game book, vendor dialogue, or client profile is changed. Any new enabled
feature needs both a server-authoritative gate and player-facing wording that matches it.
