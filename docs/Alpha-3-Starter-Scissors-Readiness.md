# Alpha 3 Phase D: Starter scissors readiness

**Decision:** Ready for Alpha 3 enablement, with `alpha3StarterScissors` still disabled. This closes feature readiness only; the combined Phase L activation decision remains outstanding.

## Reused accepted evidence

- The ordinary creation packet matrix used Advanced with Healing selected. The resulting backpack contained exactly one scissors pair, confirming that the post-creation issuance removed the stock Healing pair and issued the marked pair. See [the creation matrix](Alpha-3-Starter-Package-Audit.md#combined-ordinary-creation-packet-matrix-september-27).
- The accepted paired-client 41-type matrix includes `StarterScissors`; direct secure-trade and player-vendor attempts left each bound item in its owner's backpack and outside trade/vendor stock. The tests exercised the production item and container callbacks. No refusal narration was observed; authoritative item state was the assertion.
- The issuance/loss probe invoked creation issuance twice after starting with two stock pairs, then deleted the marked pair, saved and restarted, and verified a subsequent callback did not grant another pair. The account fixture was removed. The unit policy tests already check the exact 14,399/14,400/14,401 second protection threshold.

These accepted creation, transfer, no-regrant, and static threshold results were reviewed and reused without repeating them.

## Current-source review and additional boundary check

`StarterScissorsIssuance` runs once per ordinary-player creation callback, removes exact stock `Scissors` instances from the backpack, and issues a `StarterScissors` with the player's serial. The saved account tag is checked before issuance and remains after loss, so it does not replace destroyed pairs. `StarterScissors.Nontransferable` is permanently true; protection expiry is evaluated separately against the owner's persisted `PlayerMobile.GameTime`. `OnInventoryDeath` and `OnParentDeath` preserve the pair below four hours and use ordinary death rules at or after four hours.

The missing owner movement and real death-routing paths were checked on a separate copy of the disposable host, using a one-use test assembly. The local copy alone had the feature and acknowledgment enabled. Results:

- The actual `Item.OnDroppedInto` callback allowed the owner to move the pair from an owned nested container back to the equipped backpack and refused moving it into a nested container.
- Actual `PlayerMobile.Kill()` at 14,399 seconds left the pair in the backpack. At exactly 14,400 seconds it moved the pair to the corpse.
- After the exact-boundary death, the pair remained permanently bound: `Nontransferable` remained true, `OnDroppedToMobile` refused it, and a positive-price `GenericSellInfo` explicitly rejected both sale and resale.
- The test players and corpses were removed, a world save snapshot completed, the exact scratch process was stopped, and the scratch feature settings and assembly list were restored to their original disabled values.

The death test sets `PlayerMobile.GameTime` to the boundary values directly rather than waiting four wall-clock hours. The accepted creation matrix covers the ordinary Healing-selected client path, and the accepted paired-client matrix covers the actual trade/vendor interaction; the new probe closes owner movement and the time-dependent death routing without duplicating those accepted sessions.

## Readiness limits

No Alpha 3 source or deployed runtime flag was enabled. The pair stays economically bound after death protection expires by design. The time boundary was tested through the real death pipeline using synthetic game-time values; this was not a four-hour wall-clock play session.
