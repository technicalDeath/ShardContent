# Alpha 3 agent throughput review

Reviewed September 27, 2026 (America/New_York; generated test reports use UTC).

## September 28 follow-up: Alpha 3 Attempt 2

Investigated before making the changes below. Reviewed the workspace skills, current acceptance ledger/evidence, maintained economy probe/drivers, ModernUO save implementation and Navrey menu implementation. The chat is **Alpha 3 Attempt 2**, `01a0e61a-b0dc-7f93-97c6-5e95660d28ab`. Compacted chat summaries omitted much of its history, so the investigation also read its local session record. No credentials, account records or raw private logs are reproduced here.

### Measured activity and useful progress

The inspected session interval was 2026-09-28 03:41:44–12:13:31 UTC (about 8.5 hours). It contained 1,284 completed command-execution records and 204 file-change records. Among the executed commands, 56 contained `Start-Process` and `ModernUO.dll`, 72 contained client launch commands, 81 contained `Stop-Process`, 50 contained economy-probe build commands, and 145 contained `Start-Sleep`. These are lexical command counts, including retries and compound commands; they are not counts of successful process launches. Separate clock-sleep requests totaled 30.6 minutes. Background process lifetimes and overlapping commands make summing recorded command durations misleading; no total wasted-time percentage is claimed.

The agent delivered substantive work: staff Skill Bank recovery, authorization and save/reload evidence, longer restoration/persistence sequences, a 41-type starter transfer matrix, representative crafting/economy paths, and fixes to actual nested-sale and salvage restrictions. Some retries were justified by those defects. The evidence does not support treating all testing as waste.

### Bottlenecks

- **Fixture preparation was serialized with each tiny runtime case.** New recipes, inspection assertions and even cleanup required repeated probe builds and reloads. Around 08:10 UTC, the transfer fixtures had already passed, but missing cleanup support caused another build/restart solely to remove them. Around 09:32, inability to select legacy craft menus caused further recipe-specific staff callbacks.
- **Autosave waits were avoidable.** At 06:59, 08:12 and 09:51 UTC the agent described waiting for autosave before replacing a fixture or persisting cleanup. The stock administrator `[Save` already calls `AutoSave.Save()`. The successful snapshots sampled from this disposable host wrote in hundredths of a second; waiting for the five-minute schedule dominated those checkpoints. Console-less launches and stopping the admin too early made saving awkward.
- **The required save boundary was poorly specified.** `World.Snapshot` broadcasts completion before `WriteFiles` publishes the snapshot. Safe teardown must await the newer server-side `Writing world save snapshot done` marker, not merely client narration. A save request during an existing save can be ignored; the helper handles that case without claiming the old snapshot includes later cleanup.
- **The acceptance scope kept growing.** Success for one ordinary output or vendor led to another recipe/vendor/restart pass under the broad starter-economy row. Evidence should map distinct entry points, policies and serializers to a finite planned matrix. More examples are useful only when they exercise uncovered behavior; exhaustive per-type automation remains appropriate.
- **Earlier guidance contributed.** The prior prompt and queue emphasized finishing a small acceptance item before continuing. That encouraged repeated complete lifecycles instead of preparing a family of changes and fixtures before a shared runtime campaign. The target chat also interpreted “Stop once you complete your current task” as completing the Alpha 3 objective, then continued selecting scenarios.

### Changes from this investigation

1. Added `tools/save_test_world.py`: explicit Navrey session binding, administrator save request, fresh snapshot prerequisite, bounded new disk-publication verification, old-log/failure rejection and one retry for an already-writing snapshot. It does not launch/stop processes or alter test fixtures. Six simulated-log/client tests exercise those boundaries.
2. Added Navrey `menus` and `menuresponse <localSerial> <serverMenuId> <index>` for legacy item-list and gray menus. Responses use the same path as the UI, preserve server indices/graphic/hue, reject missing/ambiguous menus and repeat answers, and support cancellation. Generic `gumpresponse` excludes these menus to avoid sending the wrong response packet. Focused tests cover selection and cancellation; the client was built in isolated scratch output.
3. Updated `Agent-Implementation-Workflow.md` and the two operational skills: finite behavior matrix, prepare seed/reset/assert/cleanup before deployment, fast focused feedback during implementation, several cases per runtime session, grouped persistence boundaries, explicit save instead of autosave waits, and bounded stop semantics. The rehearsal reference includes tool usage.
4. Added `-NextPerSection` and `-Section` queue views so one broad pending runtime row does not hide independent Hot-zone or skill-audit work. They read the existing ledger and do not change completion status or claim work ownership.

No gameplay feature gates were activated, acceptance cells closed, active servers/clients restarted, or messages sent to the running agent. Its scenario/evidence files were left alone. The new save helper and menu commands have automated validation; live save/menu acceptance remains for the next planned client campaign, using a client built from the new source. No end-to-end speedup has yet been measured.

Validation: all 187 Navrey unit tests passed, including the two new menu tests; all six save-helper tests passed; queue section selection and uniqueness checks passed; repository diff whitespace checks passed. The client build and test outputs are isolated under `work/navrey-throughput-validation` and no deployed client binary was replaced. Initial restore attempted unavailable network access; rerunning against the existing `work/nuget` cache succeeded. The skill validator could not import PyYAML in the bundled Python, so the small skill edits were reviewed directly; their frontmatter was unchanged.

## Finding

The agents have implemented substantial behavior and found real defects. Progress toward release is slower than the volume of activity suggests because build/test setup is repeatedly reconstructed, work stops at small checkpoints, and broad acceptance items remain open while results are copied between documents. Existing batching guidance described these problems but did not provide an executable build path.

This is a qualitative review of chat history, source instructions and the current ledger, not a measured breakdown of all elapsed time. Chat turn durations include interruptions and waiting; they are not CPU or productive-work measurements.

## Evidence reviewed

- **Complete alpha 3**, thread `01a0e5a4-ac97-7c30-b3eb-03f01df412d5`: recent implementation, test commands, owner corrections and handoff messages.
- **Alpha 3 Implementation**, thread `01a0e2bc-c357-77f2-8c53-317888c8d205`: recent status report, outdoor/housing work, earlier starter-package passes and the prior workflow review.
- Repository-owned Britannia Renaissance, ShardContent workflow and Navrey shard-test skills; applicable repository instructions; Alpha 3 roadmap, implementation ledger and evidence documents; ModernUO and shard project build targets.
- The local loop-harness skill and Navrey login/container guides were also inspected for conflicting workflow defaults. The review did not establish that the loop harness caused the observed stalls; its scheduling and goal settings were left alone.

## Recurring bottlenecks and remedies

| Observed pattern | Evidence and effect | Implemented remedy |
| --- | --- | --- |
| Stale shared references | The latest Skill Bank pass first tested against shared DLLs missing current source hooks, then tried multiple scratch reference paths. An earlier integration pass repeated the stale-reference failure. | `Invoke-AgentVerification.ps1` always incrementally builds current ModernUO source and stages the exact reference layout before shard tests. |
| Repeated build plumbing failures | The BOD work hit loaded shared DLLs, missing `SolutionDir`/`skills.json`, and an empty redirected intermediate directory with `--no-restore`. Another pass flattened shard output and broke reference resolution. | The runner sets an absolute isolated engine `OutDir`, the correct `SolutionDir`, preserves restored project intermediates and shard output layout, checks fixtures, and forces `SkipShardContentDeploy=true`. |
| Setup repeated for small slices | Earlier starter categories received separate scratch-server issuance/persistence rehearsals. The existing workflow review already identified repeated launch, staging, cleanup and documentation overhead. | The ledger now gives concrete grouped acceptance batches. The workflow routes to a reusable test command and keeps related client scenarios in one session. A general server launcher was not added: safe account/world lifecycle still depends on the test's data risk. |
| Checkpoint treated as completion | Several turns in `Complete alpha 3` announced the next gate, then ended after a small fix or status/documentation update while independent work remained. The latest malformed-payload pass ended with staff recovery still open. | Explicit continuation guidance: for a phase-completion request, record a checkpoint and take the next unblocked batch. Honor actual pauses and system limits. |
| One decision repeatedly dominates the handoff | The skill ID 15 choice was repeated across multiple final responses even though other skill rows and features were unblocked. Phase placement also required repeated corrections. | The existing ledger remains the decision record. The queue tool separates decisions, deferred work and actionable entries; execution guidance limits each decision's blocking scope. Beta 2 zoning/dungeon boundaries remain explicit. |
| Status duplicated in mandatory skills | The orientation skill mixed durable integration constraints with changing issuance, persistence and test results. Reading it was required before every workspace task. | Reduced its body from about 2,649 to 1,390 whitespace-delimited words (about 48%). Moved conditional integration detail into `references/feature-integration.md`; current results remain in the existing evidence documents. |
| General gameplay instructions conflict with controlled testing | Navrey's login guide says never to start a second client and automatically starts healing/listening. Those defaults conflict with two-client trade/PvP matrices and reproducible health/timing tests. This is an instruction risk, not a proven cause of a particular failed test. | The shard-test skill now explains intentional paired clients with separate accounts/files/process IDs and omits unrelated autonomous play routines during controlled tests. |
| “Implemented” obscures unfinished acceptance | The skill inventory still has many pending rows across 58 exposed IDs. Starter economy, Hot combat boundaries and Skill Bank release scenarios remain open. These are substantive work, not just a final toggle. | Added ordered finish conditions and evidence destinations to the existing ledger. The queue reads that ledger directly, so it does not create a second status database or misleading completion percentage. |

## Tools and usage

From the workspace root, or use the script's absolute path from another directory:

```powershell
# One feature's tests, with matching current-source references:
& ./ShardContent/tools/Invoke-AgentVerification.ps1 -Suite Shard -Filter 'FullyQualifiedName~SkillBankLedgerTests'
& ./ShardContent/tools/Invoke-AgentVerification.ps1 -Suite UOContent -Filter 'FullyQualifiedName~Uor'

# Full shard regression at a milestone:
& ./ShardContent/tools/Invoke-AgentVerification.ps1 -Suite Shard

# Existing ledger views:
& ./ShardContent/tools/Get-Alpha3WorkQueue.ps1
& ./ShardContent/tools/Get-Alpha3WorkQueue.ps1 -View Decisions -AsJson
```

Add `-Restore` to verification for a checkout without restored dependencies. `-Suite All` runs both complete suites and deliberately rejects a filter shared ambiguously between them. The runner records per-step time/exit status, repository HEAD and dirty-file lists, staged assembly hashes, logs and TRX results under `work/agent-verification/runs`. It rejects zero executed tests. Raw outputs remain local scratch evidence.

An exclusive file lease prevents simultaneous invocations of this runner from colliding in shared build intermediates. It does not lock out manual builds or source edits by other agents; coordinate those while verification runs. The incremental output directory is for build/test use, not a running server. No server is launched or shut down by the runner.

## Validation performed

| Check | Result |
| --- | --- |
| First current-source isolated Skill Bank run | 24/24 passed; engine build 20.87 seconds, shard build/test 4.65 seconds |
| Focused ModernUO UOR, SkillEvents and starter BOD run | 74/74 passed; build 7.88 seconds, tests 2.68 seconds |
| Full ShardContent suite through warmed runner | 216/216 passed; incremental engine build 1.49 seconds, shard build/test 1.59 seconds |
| Empty test filter | Correctly failed despite dotnet returning success for zero matches |
| Concurrent invocation while lease held | Correctly refused before build |
| `All` plus filter | Correctly rejected before build |
| Ledger extraction | 38 existing checklist entries; actionable/decision/deferred views and source line mapping verified |

Passing run directories are `20260928T031813911Z-154331`, `20260928T032006035Z-49cd6b` and `20260928T032147763Z-152686` under `work/agent-verification/runs`. The deliberate no-match guard test is a failed report, not a regression. These timings establish that the helper works and reuses incremental output; they do not establish an overall agent speedup percentage.

PowerShell syntax, skill metadata, reference links and whitespace were checked. The bundled Python skill validator could not run because this runtime lacks PyYAML; metadata and links were checked separately instead.

## Remaining limits

Alpha 3 is still not complete. These changes remove repeated setup and clarify how to finish its existing gates; they do not substitute unit tests for the required client/economy/persistence evidence. Skill ID 15 and final activation remain owner decisions. Existing feature flags, shared runtime files, saves and accounts were not changed by this work. Existing uncommitted gameplay work was preserved. No other chat was resumed or messaged.

## Follow-up investigation and implementation

The owner requested completion of the investigation and a report before further implementation. The follow-up first inspected older starter/Skill Bank turns, current validation gates, scratch probe source, the new tools and the existing Navrey Python API without changing files. Findings were reported in chat before edits began. Validation of the proposed Navrey example subsequently exposed a Windows import failure; that correction was also reported before fixing it.

### Additional findings

- In the sampled `Complete alpha 3` history, 13 of 28 visible build/test shell invocations returned nonzero. This sample excludes nested tool calls and mixes setup failures with other failures; it is evidence of recurring friction, not an overall failure rate or wasted-time estimate.
- `ShardRulesConfiguration` rejects Skill Bank, starter craft and starter combat flags under normal configuration. Earlier client tests enabled these in memory through temporary probes, including `work/alpha3-skillbank-client-probe/Alpha3SkillBankClientProbe.cs` and `work/alpha3-craft-probe/Alpha3CraftProbe.cs`. That makes a reusable, carefully scoped rehearsal setup more valuable than another general launcher. The normal validation blockers remain intact.
- The first queue implementation classified standing “keep flags disabled” requirements and final release prerequisites as actionable. It also followed historical document order instead of execution order. Those classifications could direct the next agent back to bookkeeping or premature activation discussion.
- Commit IDs plus dirty filenames did not identify the contents tested or detect source edits during a run. This is a limitation for evidence reuse in the shared checkout, even though this review did not demonstrate an actual concurrent-edit failure.
- `Improve blacksmithing UX` was waiting on user input when inspected. Its active sidebar badge was not evidence of an ongoing competing build. There is no basis here to claim that another agent was currently locking the build.
- Navrey already contained explicit-path commands, state readers and bounded waits in `cli/uo`. However, the documented example failed immediately on Windows because `locks.py` imported Unix-only `fcntl`. The existence of a library did not establish that it was usable on this host. This is a confirmed technical defect discovered during validation, not an established explanation for every earlier manual test loop.

### Changes made after reporting

1. **Queue correction.** Added invariant and release-gate states/views to the existing ledger, ordered actionable results by execution order, and added `-Next`. Split the large Skill Bank item into recovery, gain/cap/ordering and persistence tasks. The first selected task is now staff recovery. No feature was marked complete except for separating the already-recorded malformed-payload result from remaining work. The current views contain 14 actionable entries, one owner decision, one deferred entry, two standing invariants and five release gates; these are not equal-sized units of progress.
2. **Verification provenance.** Schema-2 reports record the SDK/helper/shard DLL hashes and before/after source fingerprints. `AgentVerificationInputs.ps1` combines HEAD, the scoped working-tree diff and hashes of nonignored new input files. A changed fingerprint rejects the result. Reported scopes cover source/build/configuration and stock test data, not ignored packages, UO assets or saves. It detects a persisted change across the snapshots; it is not a continuous source lock and cannot detect a change reverted between snapshots.
3. **Reusable client guidance.** Added `Navrey/.agents/skills/navrey-shard-test/references/rehearsal-sessions.md`, with an explicit-path API example, bounded outcome checks, heartbeat versus snapshot freshness, and a compact scenario/evidence record. It distinguishes normal configuration from test-only overrides and explains how to preserve reusable probes without adding them to ordinary deployment.
4. **Windows API unblock.** `Navrey/cli/uo/locks.py` now conditionally uses Windows nonblocking byte-range locks while retaining Unix flock. The lock byte is outside the PID header so other processes can inspect the holder. Windows takeover is refused because forceful termination would bypass scenario cleanup; release the exact prior script first. Explicit session paths remain required because the Python defaults still use `/tmp`. The locking primitive follows the [Python msvcrt documentation](https://docs.python.org/3/library/msvcrt.html).

### Follow-up verification

- Schema-2 ShardContent runner: 24/24 Skill Bank tests passed with stable fingerprints, report `20260928T033108834Z-62557e`.
- Schema-2 ModernUO runner: 4/4 Smith BOD reward tests passed with stable fingerprints, report `20260928T033302589Z-fd43ae`.
- `tools/tests/Test-AgentVerificationInputs.ps1`: stable-source reuse, out-of-scope/ignored exclusions, tracked edits, staging equivalence, untracked addition and untracked content changes passed in a disposable repository.
- Queue views, execution ordering and all ledger line references passed checks.
- `Navrey/cli/uo/test_locks.py`: six Windows checks passed, including cross-process exclusion, readable holder PID, independent clients, reacquisition after release/process exit and refusal of forced takeover.
- The complete existing Python helper test discovery passed 48/48, including the six new lock checks and existing avoidance/escape tests.
- The exact documented Python example and bounded wait passed against synthetic command/state/log files. This is API verification, not a live gameplay test. Unix flock was retained but was not executed on this Windows host.

The remaining substantial infrastructure opportunity is a maintained disposable-host/scenario fixture for the release matrices. This task did not invent a new deployment or activation path to stand in for it. Future work should promote reviewed, reproducible scenarios as each feature matrix is completed, using the now-working client API.
