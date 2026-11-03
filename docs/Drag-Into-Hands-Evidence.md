# Dragging into full hands swaps

Owner, 2026-11-02: "when you attempt to drag something into your hands, but your hands are full, the game should automatically unequip the item in your hands to free them up".

Flag: `featureFlags.dragIntoHands`, **off** until the owner says activate.

## What a player sees

Before, a hand item dragged onto your own paperdoll while your hands were full was refused and bounced back, with "You can only wield one weapon at a time." or "You already have something in both hands.". Now:
- Whatever is in the way goes into your backpack, and the new item is in your hands.
- What counts as in the way follows the stock hand rules: a two-handed weapon needs both hands; a one-handed weapon cannot share with a two-handed weapon; a shield or light shares with a one-handed weapon.
- If the pack cannot take the old item, or the new one still cannot be equipped (too little Strength, say), nothing changes and the item bounces back with the stock message.
- Armor, clothing and jewellery keep the stock rule. Dropping onto someone else's paperdoll is unchanged.

## How it is built

- **Engine:** `IncomingItemPackets.EquipRequestHandler` (ModernUO `Network/Packets/IncomingItemPackets.cs`), a stand-in for `EquipReq`'s `to.EquipItem(item)`. Null keeps stock.
- **Shard:** `DragIntoHands.cs` hands a drop onto your own paperdoll of a OneHanded or TwoHanded layer item to `WorldActions.Equip`. That is the same "put it on as a player would" rule the left-click menus already use: it clears the way into the pack and puts things back if the equip is refused.
- Every way of equipping by drag uses the same request: the paperdoll, the combat bar's equipment strip and Navrey's `equip`.

## Evidence

| Check | Result |
| --- | --- |
| Unit: hand layers on your own paperdoll swap; armor, clothing and rings do not; another's paperdoll and the flag off keep stock; flag off (`DragIntoHandsTests`) | pass (162 with the world-actions and rules tests) |
| Real client, disposable host `progress` (port 2594, flag on): hatchet (two-handed) in hand, dagger dragged from the grid backpack onto the paperdoll | dagger in hand, hatchet in the pack, no refusal message |
| Real client: hatchet dragged back | hatchet in hand, dagger in the pack |

Shots (real client): `work/player-client/ProgChop/shots/20261102-145452-swapped.png`, `20261102-145506-swapped-back.png`.

## State (2026-11-02)

Built and checked live. Flag off. Uncommitted. Deploying needs the engine rebuilt into `Distribution` and the pin bumped when the engine is committed.

## Deployed (2026-11-03, with the progress bars)

Owner, 2026-11-03: "you can commit, deploy, push, etc". Committed and pushed: ModernUO `67b29ab34` (the timed-action events and the equip
request handler), ShardContent `766a954` (pin bumped to it), ClassicUO `da3966573`. Full verification before the commits: UOContent 1,412
passed, shard 1,953 passed (run `20261103T171433959Z-657dc3`). Deployed to dev with `actionProgressBars`, `gatheredItemPopups` and
`dragIntoHands` OFF, after the snapshot `work/save-snapshots/saves-20261103-121627-before-progress-bars-deploy`; a disposable copy of the
deployed dev world loaded cleanly (57,867 items, 13,078 mobiles). The new `cuo.dll` is in `ClassicUO/bin/dist`; the old one is in
`work/cuo-backups/cuo-20261103-121722-before-progress-bars`. The farm host was not touched. Turning the bars on is the owner's call.

## Enabled (2026-11-03)

Owner, 2026-11-03: "Turn all three on". `actionProgressBars`, `gatheredItemPopups` and `dragIntoHands` are on in
`data/configuration/shard-rules.json` and deployed to dev, after the snapshot
`work/save-snapshots/saves-20261103-142450-before-progress-bars-on`. Full shard suite before the deploy: 1,953 passed (run
`20261103T192430653Z-2e9edf`). The README rules section has a line for each. `worldActions` stays off, and the farm host was not touched.
