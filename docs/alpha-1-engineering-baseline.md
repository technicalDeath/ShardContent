# Alpha 1 engineering baseline

Recorded: 2026-09-23

## Pinned dependency

- ModernUO fork: `technicalDeath/ModernUO`
- UOR baseline reference: `29a3ab1bd443b9c2a8ff6bf34f4df47d9f837895`
- Current Alpha 2 integration commit: `075d7859eb9646ed681a18b064754bb066799812`
- Local SDK: .NET SDK `10.0.401`
- Content assembly: `BritanniaRenaissance.Content.dll`, loaded from
  `ModernUO/Distribution/Assemblies`

## Verified UOR era and world gates

- `data/configuration/expansion.json` is the source-controlled Renaissance/UOR expansion profile.
  Deployment copies it to `Configuration/expansion.json`, where it selects only Felucca. The Lost
  Lands are part of the Felucca facet, so they remain available without enabling another map flag.
- `data/configuration/modernuo-era-gates.json` is the source-controlled patch for stock engine
  settings. Deployment explicitly disables item insurance, veteran rewards and veteran skill-cap
  rewards, ML quests, pet bonding, and the ML pet stand-down behavior.
- The external content assembly validates at startup that the live server is UOR, its map selection
  is only Felucca, and every era-gate setting is false. Startup fails rather than silently serving a
  mixed-era configuration.
- Source audit of the pinned ModernUO confirms the governing paths: `Insurance.Configure()` reads
  `insurance.enable` (AOS default); `RewardSystem.Configure()` reads `vetRewards.enable` and
  `vetRewards.skillCapRewards`; `BaseCreature.Configure()` reads `taming.enableBonding` (LBR
  default) and `taming.petsStandDownOnCommand` (ML default). The UOR profile also advertises no
  later maps, character-list features, housing features, or supported expansion features.

## Verified combat-special exclusions

- The pinned fork removes the four original automatic UOR weapon paths: Concussion Blow from axes
  and polearms, Crushing Blow from two-handed maces, and Paralyzing Blow from two-handed spears.
- UOR Wrestling Stun/Disarm request paths are no-ops that clear state; unarmed swing resolution
  clears stale states before attack resolution; deserialization consumes but clears persisted
  ready-state flags.
- The implementation audit and regression locations are recorded in `docs/UOR-ERA-AUDIT.md`.
- The local listener is `127.0.0.1:2593`; client data is supplied by the local `UOData` directory.
- `modernuo.json` currently has account auto-creation disabled and assistant negotiation disabled.
- House decay and the stock murder system are intentionally unchanged: their shard-specific policy
  is scheduled for later Alpha work. Client verification remains configured for the tested local
  client and is transport compatibility, not an expansion gate.

## Verified extension points

- ModernUO loads external assemblies from `Distribution/Assemblies`.
- `Configure()` runs after logging and before the world loads; it is the correct phase for rules
  loading and command registration.
- `Initialize()` is reserved for later features requiring loaded world or tile data.
- `ConfigurePrompts()` is reserved for first-run console input and is intentionally unused here.
- Only `ServerConfiguration` accessors with source evidence should be used to bind stock engine
  settings. The typed shard rules document does not invent stock ModernUO keys.

## Baseline deliverables

- Source policy: `data/configuration/shard-rules.json`
- Engine era gates: `data/configuration/expansion.json` and
  `data/configuration/modernuo-era-gates.json`
- Runtime policy: `ModernUO/Distribution/Configuration/shard-rules.json` after explicit deployment
- Staff diagnostic command: `[ShardRulesStatus` (includes live era-gate state)
- Deployment: `tools/Deploy-Alpha1Baseline.ps1`
- External assembly registration: the deploy tool preserves the stock entries in
  `Distribution/Data/assemblies.json` and adds `BritanniaRenaissance.Content.dll` when absent.

The policy validates a UOR/Felucca baseline, 700/100/225 caps, the recorded ModernUO commit, and
that every roadmap feature deferred beyond Alpha 1 remains disabled. It does not implement those
rules yet; later Alpha 1 tasks bind each verified policy to its proven ModernUO control point.
