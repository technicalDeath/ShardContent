# Bot farm client memory (2026-10-20)

The owner's target: half the memory per bot. This records where a headless Navrey client's memory goes, what was changed, what was measured, and the scope of the one-process runner (many bots in one process).

## Result

**Lean12 with the new launch settings: about 45% less memory per bot than the farm's client until now.** Lean12 is Lean11 with the drawing-only sprite data dropped in lean mode (below). In its own 12-minute run it measured 125 MB median private bytes against Lean11's 132 MB (min-max 116-147 against 105-146), and 97 MB private working set against 124 MB. Both walked the route with no errors. The Lean11 comparison against Lean9:

**Lean11 with the new launch settings: 43% less memory per bot than the farm's client until now.** Both were measured on one disposable host, same route, 12 minutes of walking, 24 samples each:

| | Lean9, the farm's settings until now | Lean11, `farm_launch.py` now | Change |
| --- | --- | --- | --- |
| Private bytes, median (min-max) | 226 MB (216-236) | 129.5 MB (102-142) | -43% |
| Private working set at the end | 167 MB | 121 MB | -28% |
| Threads | 42 | 12 | |
| CPU over 12 min | 33.3 s | 26.5 s | (WARP measured +31% in an earlier run; call CPU roughly even) |

For 50 bots that is about 11 GB of private memory against about 6.5 GB, measured early in a session. Long-run growth is not measured: the live Lean9 bot at 262 MB had roamed for a day. The capped walk-planner cache and periodic compaction are what should hold Lean11 near its early figure.

`farm_launch.py` now starts bots on `bin/Lean12` with `DOTNET_GCgen0size=0x1000000` and `FNA3D_D3D11_USE_WARP=1` added to `LEAN_ENV`. This takes effect at the next farm start. Nothing is committed: Navrey and ShardContent both carry the changes in their working trees.

Lean11 is Lean10 plus three trims:
- `StringDictionaryLoader` loads on first use. Nothing in the client reads the string dictionary, and loading it decoded about 170,000 strings (11 MB).
- `UOFileIndex` is 32 bytes instead of 40 (`Width`/`Height` as `short`, `CompressionType` a byte). The `anim*.idx` tables alone hold about 587,000 entries; their arrays fell from 16 to 13 MB.
- The walk planner's tile objects are 18 bytes instead of 24. Its chunk cache drops chunks unread for 2 minutes once it passes 2,048, keeping 1,536. On a 12-minute walk the cap fired and the cache stayed at about 1,550-1,650 chunks. The unit tests cover the eviction order and that fresh chunks are kept (190 pass).

Lean11 also compacts more often than Lean10: it checks every 3 minutes and compacts over 24 MB of fragments. On Lean10's 10-minute check, a bot built up 46 MB of fragments (168 MB private, 124 MB after). At the login screen, Lean11 holds 37 MB of managed heap against Lean10's 52 MB, and 89 MB private against 98 MB.

Lean12 drops the drawing-only sprite data in lean mode (`NAVREY_LEAN=1`); the full client is unchanged:
- The Art, Gump, Light and Texmap sprite caches (`ClassicUO.Renderer/SpriteInfoStore.cs`) hold only the graphics actually asked for, in a dictionary. Before, each kept one slot for every graphic in the data files, about 5 MB in all. A headless client still asks for some, because gump and item sizes come from them.
- The art bounds table is sparse the same way (about 1 MB).
- `PixelPicker` records nothing and reserves nothing. Its pixel masks serve only mouse hit-testing of drawn sprites, and a lean client draws none. That was 256 KB per picker up front, growing with every sprite seen.
At the login screen the managed heap fell from 37 to 29 MB and private working set from 79 to 73 MB.

### How it got there

| Client, farm launch settings | Private bytes, login screen | Private bytes in the world, median of 24 samples over 12 min of walking | Private working set in the world, at the end | CPU over the 12 min | Threads |
| --- | --- | --- | --- | --- | --- |
| Lean9 (the farm's client until now) | 176 MB | 215.5 MB (206-266) | 175 MB | 25.7 s | 42 |
| Lean10: compaction + gen0 cap, GPU driver | 148-152 MB | 185 MB (171-207), -14% | 129 MB, -26% | 25.5 s | 42 |
| Lean10: compaction + gen0 cap + WARP | 94 MB | 146 MB (118-171), -32% | 118 MB, -33% | 33.6 s, +31% | 12 |

All three walked the same loop and arrived where they were sent. WARP costs CPU: 4.7% of one core per bot against 3.6%, about half a core more for 50 bots. RAM, not CPU, is what limits the farm. The 12-minute probe does not show long-run growth. The live Lean9 bot at 262 MB had roamed for hours, against 215 MB here.

This run used a shorter route than the final comparison above, so its Lean9 figure (215.5 MB) is lower than that one's (226 MB).

The farm's launch settings are `NAVREY_LEAN=1`, `FNA3D_FORCE_DRIVER=D3D11`, `DOTNET_GCConserveMemory=9`, `DOTNET_TieredPGO=0`, fps 8 and a 320x240 window (`farm_launch.py`). A live Lean9 bot measured mid-run on 2026-10-19 held 262 MB private.

Three changes, one in code and two in the launch environment:

1. **Compaction (code, `Navrey/src/ClassicUO.Client/Agent/MemoryTrim.cs`).** Loading the UO data files leaves about 60 MB of free fragments in the managed heap, mostly on the large object heap, which the GC never compacts on its own. One compacting collection on the first frame cuts the heap from 126 to 52 MB and pauses for about 15 ms. A second runs 15 s after entering the world, and further ones run whenever more than 24 MB is fragmented, checked every 3 minutes (Lean10 used 32 MB and 10 minutes). Each is logged as a `[MEM]` line; `NAVREY_COMPACT=0` turns it off.
2. **Gen0 budget, `DOTNET_GCgen0size=0x1000000` (16 MB).** By default the budget scales with the CPU's cache, and on this machine it kept about 50 MB committed and empty. 4 MB measured the same as 16 MB, so 16 MB is used to keep gen0 collections infrequent. The runtime reads this from the environment only; `runtimeconfig.json` has no public name for it.
3. **WARP, `FNA3D_D3D11_USE_WARP=1`.** FNA3D creates its D3D11 device on Windows' software rasterizer instead of the NVIDIA driver. A headless client never draws, so it renders nothing either way, but the NVIDIA user-mode driver (`nvwgf2umx.dll`, plus the shader compiler `nvgpucomp64.dll`) held about 55 MB private and 29 threads per client. With WARP, native memory falls from 84 to 29 MB, threads from 49 to 20, and no `nv*` module is loaded.

Also measured and rejected: FNA3D's SDLGPU driver (275 MB at the login screen) and OpenGL (137 MB private but 105 MB private working set, against D3D11's 87 MB; with WARP both are lower again). `DOTNET_GCConserveMemory=7` alone gave 175 MB, against 159 MB for the gen0 cap.

Correction: the 2026-10-14 farm notes say GC environment settings (gen0size, ConserveMemory) "give nothing". Measured at the login screen they do: the gen0 cap is worth about 25 MB once the fragments are compacted. Before compaction, fragmentation hid it.

## Where the rest goes

A WARP client at the login screen (94 MB private):

- **Managed heap, 52 MB: all game data, the same in every bot.** UOFileIndex tables 16 MB (19 arrays), 170,000 strings 11 MB (asset names; no world is loaded yet), sprite info 5 MB, tiledata 3 MB, sounds 1 MB.
- **GC overhead, about 12 MB.**
- **Native, about 29 MB.** Runtime, JIT (only 3,600 methods and 430 KB of IL compiled, so a few MB), SDL3, FNA3D with WARP, FAudio, 20 thread stacks.

In the world, each bot adds its own state on top: the map chunks and objects around it, mobiles, items and the walk planner's tile cache (19 MB on a bot that had roamed for hours).

So after these changes, about 80 MB of a bot's roughly 146 MB is the same in every bot: game data, the runtime and the native libraries. Only one process can hold that once. That is the case for the one-process runner below.

The trims that stay with separate processes (the string dictionary, the UOFileIndex tables and the tile cache) are built in Lean11; see Result. After them, a Lean11 bot is about 130 MB in the world. About 65 MB of that is the same in every bot: game data of about 37 MB, plus the runtime and native libraries.

## One-process runner: scope

### What it would save

In one process, the game data (about 52 MB managed), the runtime and native libraries (about 29 MB) and their GC overhead exist once. So does the walk planner's tile cache, which is map geometry and the same for every bot on a facet; it held 19 MB on a bot that had roamed for hours. Each bot would cost only its world state.

This is an estimate, not a measurement. The census suggests about 30-45 MB per bot: the world objects in the game root (about 9 MB on a long-running bot), chunk pools (about 13 MB), agent state, a share of GC slack and a few threads. The shared part would be about 150-250 MB: one copy of the game data and libraries, the tile cache for everywhere the bots roam, and one GC budget.

| 50 bots | Per bot | Total |
| --- | --- | --- |
| Lean9, long-running (the farm until now) | about 262 MB | about 13 GB |
| Separate processes, Lean10 + gen0 cap + WARP | 146 MB measured early | about 7.3 GB |
| Separate processes, Lean11 | 129.5 MB measured early | about 6.5 GB |
| Separate processes, Lean12 (the farm's client from now on) | 125 MB measured early, more in long runs | about 6.2 GB and up |
| One process | about 30-45 MB + 150-250 MB shared | about 1.7-2.5 GB |
| 5 processes of 10 bots | the same, shared part five times | about 2.9-3.5 GB |

Treat the per-bot figure as roughly ±50% until Phase 0 below measures it. One GC serving 50 game loops is the main unknown. A full collection of a heap of about 2 GB pauses every bot in the process at once, possibly for hundreds of milliseconds. Server GC would shorten the pauses but costs much more memory.

### Two ways to build it

**A. One assembly load context per bot (no refactor of the client).** A small host process creates one `AssemblyLoadContext` per bot and loads `cuo.dll` and the ClassicUO assemblies into each, so each bot gets its own copy of every static. That sidesteps the client's static state (below) entirely. But it shares little: each context loads its own copy of the game data and JIT-compiles its own copy of the client code. Only the runtime and the native libraries' private data are shared, which is perhaps 15-20 MB per bot. That is not worth the risk on its own.

**B. Shared game data, one world per bot (refactor).** The game data (`UOFileManager` and the loaders) is loaded once and shared read-only; each bot gets its own `GameController`, `World`, network client, agent host and files. This is the design that gets the saving. What it touches:

- `Client.Game` is a static singleton referenced 1,100 times in the client (12 times in the agent layer).
- 116 mutable static fields, 62 static auto-properties and 213 static readonly fields across the client, many of the readonly ones holding mutable collections. Of these, 28 / 10 / 30 are in the agent layer (for example `PathGrid._static`, which could stay shared: it is map geometry, the same for every bot on one facet).
- Each one must be classed as shared game data (stays static, made read-only or thread-safe) or per-bot state (moved onto a per-bot context object).
- Process-wide things the client assumes it owns: the working directory (settings.json and .env are read from it), environment variables (5 reads), SDL (initialised once per process; its event queue is global, so one bot's game loop could poll another's window events), FNA's static `Game` loop, the console.
- Graphics: one D3D11 device (WARP) for all bots, or none. A bot never draws, so a shared device, or a null renderer in FNA, would remove per-bot graphics entirely.

### Crashes and isolation

The owner's point stands for managed failures. A C# exception is caught where it is raised, and a per-bot `try`/`catch` at each bot's entry points keeps one bot's bug from ending the others. The client starts 5 threads and 9 tasks; each thread entry needs a catch-all that stops only that bot (an unhandled exception on any thread ends the process). Tasks do not end the process.

What a catch cannot contain, and would take every bot in the process down at once:

- a native fault in SDL, FNA3D, FAudio or the graphics driver (access violation);
- a stack overflow (never catchable in .NET);
- running out of memory, or one bot's leak growing the shared heap;
- a deadlock or a long block on a shared lock, which stalls every bot's game loop if they share a thread or a lock.

On the farm so far, client deaths have been rare; the supervisor restarts dead clients every 20 s, and that restart would now restart every bot in the process. Running, say, 5 processes of 10 bots each keeps most of the saving and limits a crash to a tenth of the farm.

### Phases

0. **Spike (decides whether to go on).** Two bots in one process with the shared game data, enough to log in and walk; measure the marginal memory of the second bot. Stop here if it is not well under the separate-process figure.
1. **Per-bot context.** Move `Client.Game` and the per-bot statics onto a context object passed through, or made ambient per bot thread. Shared game data stays static and read-only.
2. **Host.** `navrey-host --bots <roster>`: one process, N bots, each with its own command, log, state and world files exactly as now, so the brains, the supervisor and the `uo` library do not change. Per-bot catch-alls, per-bot restart inside the process, and a health line per bot.
3. **Farm rollout.** `farm_launch.py` starts K host processes instead of N clients. The supervisor restarts a bot inside its host, and a dead host as a whole. Canary first (5 bots), then the farm.
4. **Verification.** The existing farm A/B and the simulator (`sim/`) for brain behaviour; per-bot walk, fight, death and relog scenarios in one process; a fault-injection test (a thrown exception in one bot's command, packet handler and walk thread) showing the others carry on.

## Recommendation

1. **Done:** the farm runs Lean12 with the gen0 cap and WARP at its next start (`farm_launch.py`). That is about 45% less per bot in 12-minute tests, near the 50% target. Watch the first long farm run: if a bot climbs well past about 150 MB over hours, find out what grows before building more.
2. **The rest of the way with separate processes** is small game-data work. The animation index tables (13 MB) could load per body on first use, and the sprite caches are already sparse (Lean12). Perhaps another 10 MB.
3. **The one-process runner** is the only route to a large further cut, an estimated 70-85% below Lean9. It is a refactor of the client's static state, plus a host and a supervisor change. Build the Phase 0 spike first: two bots in one process, measuring the second bot's cost. Go on only if that is well under 60 MB. If it is, run 5 processes of 10 bots, so a crash costs a tenth of the farm.

## Raw measurements

All 2026-10-20 on this PC (NVIDIA GeForce RTX 5060), .NET 10.0.401, with the farm's launch settings unless noted. Login-screen probes pointed at a closed port; in-world probes ran on a disposable host (`memprobe`, since removed).

- Login screen, repo settings (fps 60, large window), no ConserveMemory: Lean10 no compaction 228 MB private (heap 127 MB, 60 MB fragmented); with compaction 204 MB (heap 52 MB).
- Login screen, farm settings: Lean9 176 MB (heap 62, GC committed 90, native 85); Lean10 + gen0 cap 148-152 MB (native 84-88, 49 threads); + WARP 94 MB (heap 52, GC committed 64, native 29, 20 threads).
- Gen0 knob at the login screen, repo settings: 16 MB gen0 159 MB, 4 MB gen0 158 MB, ConserveMemory=7 175 MB.
- Drivers at the login screen, Lean10 + gen0 cap: D3D11 152 MB (private working set 87 MB), OpenGL 137 MB (105 MB), SDLGPU 275 MB, D3D11 on WARP 94 MB (76 MB).
- JIT: 3,628 methods, 432 KB of IL compiled, 0.7 s; 38 assemblies loaded.
- Compaction pauses: 11-20 ms. In the world the second compaction (15 s after entering) took the heap from 76 to 63 MB on the WARP bot. No periodic compaction fired in 12 minutes: the threshold is 32 MB of fragments, and the most seen was 21.
- Client static state (for the one-process scope): 116 mutable static fields, 62 static auto-properties, 213 static readonly fields; `Client.Game` referenced 1,100 times; 5 `new Thread`, 9 `Task.Run`/`StartNew`, no `Environment.Exit`.
