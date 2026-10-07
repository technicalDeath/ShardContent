# Murder reports and Execute: the right to attack is not the right to kill

Status: **built and verified live 2026-10-06 (owner rulings, same day); local only, not deployed.** Rulings:

1. "If a blue is killed by another player and that player does not have rights to attack (e.g. guild war status), they should be presented with the option of reporting the murder." Stock already does this (below), so only the text changed.
2. "A blue who strikes a criminal or one with criminal intent first still should get a report prompt if they are killed. On this shard, blues have the lawful right to kill criminals, murderers, or criminal intent. The other party can fight back, and knock them out, but executing is still a murder in these circumstances." This changes the code: it amends K-5 (see `Alpha-3-Contract-Review.md`).
3. "The whole point of knock out is so that a grey or red can walk away from a fight and not take a murder count" goes in the player text.

## The rules now

**Any killing that is not an Execute** (a death with Knocked Out off, or with no active fight) is stock: the victim is offered the report when the killer had no right to attack them. The killer had it if the victim had Criminal Intent on, was criminal or red, had attacked them first, or was a guild-war enemy (`Notoriety.Compute` is not Innocent, plus the Intent grey). A Hot Zone gives no right (K-5). Fighting back never costs the victim the report: stock records a mutual fight once, in the first attacker's direction, so the first attacker's later hits stay criminal.

**An Execute** (the only way a Knocked Out blue dies) is murder unless the victim had Criminal Intent on or the two were at guild war. It is murder even when the blue attacked first: a blue may lawfully attack a criminal, a murderer or an Intent player, who may fight back and Knock the blue out, but executing the blue still counts and the blue is offered the report. Nobody who is not a criminal or red can Execute (K-4), and a criminal or red victim is never Knocked Out.

## Build

`ExecutionMurderRule` (new). When a blue is Knocked Out, `KnockedOutService` records who an Execute would be murder for. The old record held only attackers whose stock report flag was set (they struck an innocent first); that missed the blue who attacked a criminal, because the criminal's hits are lawful and, since the blue struck first, stock does not even list the criminal in the blue's aggressor list. The new record considers everyone who could Execute (the Knocking-out blow's dealer, the aggressor list, the recent damage records) and keeps each one for whom `IsMurder(unlawfulFirstStrike, victimHadIntentOn, atGuildWar)` holds. `Execute` then marks that executor reportable so the stock gump follows. The automatic-adjudication path (flag off) already treated an ordinary blue victim as murder-protected whatever rights the killer had, so this brings the stock path in line with it. `PvpIntentService.IsGuildWarOrDuel` became public for this.

## Evidence

Disposable host `murder-report`, as deployed (stock reporting, `automaticMurderAdjudication` off). Driver `tests/scenarios/hot-zones/murder_report_live.py`, with the test-only probe `TestOnlyReportFlags` (an aggressor's report flag). Unit: `ExecutionMurderRule.IsMurder` truth table (`KnockedOutTests`) and the guide text (`WelcomeGuideTests`).

| Case | Setup | Before the ruling | After |
| --- | --- | --- | --- |
| R1 | Hot Zone, Kara (no right) strikes blue Vim first, Vim hits back, Kara hits again, Knocks Out and Executes | offered | offered; pressing Okay told Kara "You have been reported for a murder!" |
| R2 | The same, Vim never fights back | offered | offered |
| R3 | Hot Zone, blue Rook strikes criminal Tavi first; Tavi fights back, Knocks Rook out and Executes | **not offered** | **offered** |
| R3b | The same outside a Hot Zone | **not offered** | **offered** |
| R4 | Outside Hot, Nell has Criminal Intent on; criminal Elin attacks, Nell hits back, Elin Executes | not offered | not offered (Intent makes an Execute lawful) |
| R5 | Knocked Out switched off (plain death), Vale strikes blue Vex first, Vex hits back, Vex dies | offered | offered |

Guild war is not run live: it reaches the same decision as Intent (`Notoriety.Compute` is Enemy), and `ExecutionMurderRule` asks the guilds directly (`IsEnemy`), and R4 shows the Intent half of it. Real client (ClassicUO 1.1.0.0, screenshots in `work/player-client/` under `Vale`, `Wren`, scratch): the stock report gump shown to an executed blue ("Would you like to report Pike as a murderer?", Okay and Cancel), and the Fighting and Hot Zones guide pages.

## Player text (`WelcomeGuide.cs`)

- Knocked Out: "Knocked Out is how a fight ends without a killing. A player who is not a criminal or a murderer and is brought down by another player is Knocked Out for 90 seconds instead of dying. While Knocked Out you cannot act, be hurt or be healed, and when it ends you wake with half your health. The winner, even a criminal or a murderer, can simply walk away and takes no murder count, because nobody died. Monsters and other causes still kill normally."
- Execute: "Killing is a choice. While a player is Knocked Out, a criminal or murderer who knocked them out, or who has damaged them recently, may [Execute them. Nobody else can, including a player who is only grey because of Criminal Intent." Then: "An Execute is murder, and the victim can report it, unless the victim had Criminal Intent on or the two were at guild war. That is true even if the victim attacked first: a blue may attack a criminal, a murderer or a player with Criminal Intent on, who may fight back and Knock the blue out, but executing the blue still counts. Reporting gives the killer a murder count. Fighting back never costs you the report, and a Hot Zone does not make a killing lawful." Then the counts, bounty and the Thieves' Guild line.
- Hot Zones: "Fighting in a Hot Zone is free, but it does not make a killing lawful: if someone executes you there, you can still report them as a murderer unless you had Criminal Intent on or were at guild war with them."
- With Knocked Out off the page tells the stock rule instead (a killer with no right to attack can be reported).

## Named limits

- Only an Execute changed. A blue killed any other way (Knocked Out off, or a death with no active fight such as old poison) still follows stock: the killer is reportable only if they struck an innocent first.
- Stock's Thieves' Guild exception is unchanged: guards take no report from a Thieves' Guild member. After a report the same killer and victim cannot be reported again for 10 minutes (`murderSystem.recentlyReportedDelay`).
- Duels are switched off on this shard (`DuelContext.DuelingEnabled = false`), so they never come up and the player text does not mention them. Only enemy guilds make an Execute lawful: executing a guildmate or an ally still counts as murder.
- Intent is read from the victim's state at the executor's last strike (the encounter record, two minutes).
- Earlier evidence that expected the old exemption is superseded: K3 case X5a (`hot_k3_live.py`, now expects murder +1) and the Hythloth observation Y11.

## For the README when this is deployed

Replace the rules section's Execute line ("If you execute an ordinary blue who never attacked you, they can report you for murder") with: "An Execute is murder unless the victim had Criminal Intent on or the two were at guild war. That holds even if the blue attacked first: a blue may attack a criminal, a murderer or a player with Criminal Intent on, who may fight back and Knock the blue out, but executing the blue can be reported. Knocked Out lets a fight end without a death: the winner, even a criminal or red, can walk away with no murder count."
