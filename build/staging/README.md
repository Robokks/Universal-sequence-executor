# build/staging: AIXML drafts for the AF actor phase (DRAFT, not generated)

Prepared offline on 2026-11-07. No LabVIEW, no MCP tools. Nothing under `src\`, the `.lvproj`, `CounterActor\`, `Messages\` or `_legacy\` was touched. The spec is `docs/DESIGN_AF_EXECUTOR.md` §1, 2, 5, 6, 7.

## How the spellings were evidenced

1. **The user's own exports**: `launch.xml`, `add_do.xml`, `step_tick.xml`. They supply the NI dialect: `\3A` in targets, Tunnel/CaseFrame/ShiftReg shape, Event Structure frames, `Casting Utility For Actors.vim`, `Send Normal Stop`, the notifier nodes.
2. **Plugin docs** (`labview-mcp 2.4.0\bin\docs\`): `aixml-reference.md` (curated and generated node-terminal tables, type grammar, Case/Loop/ShiftReg rules, class-seed rule, `Bundle By Name` order), `labview-actor-framework.md`, `af-override-tools.md`.
3. **Offline reads with the plugin's own `vi2aixml.py`** (pylabview, no LabVIEW). Sources:
   - `vi.lib\ActorFramework`: `Launch Nested Actor.vi`, `Time-Delayed Send Message.vi` (+ Core), `Read Caller Enqueuer.vi`, `Read Self Enqueuer.vi`, `Enqueue.vi`, `Enqueue Critical.vi`, `Send Emergency Stop.vi`, `Actor Core.vi`, `Stop Core.vi`.
   - The user's `CounterActor\Configure.vi`, `Stop Core.vi`, `Add.vi` and `Messages\Add\Send Add.vi`.
   - The **already built** `src\Logic\Parse Sequence JSON.vi`, `Plant First Order Step.vi`, `Select Monitored Signal.vi`, and `src\12_Utilities\UE_Within_Tolerance/Elapsed_Ms/Timeout_Reached/Dwell_Reached.vi`.
   - Scopes were read from `Actor.lvclass`, `Message Enqueuer.lvclass` and `Actor Framework.lvlib` as text.
   - That reader writes targets with `:`. The drafts use NI's `\3A` form, as the doc's measured table does (`Actor Framework.lvlib\3AActor.lvclass\3ALaunch Nested Actor.vi`).

## Files

| file | becomes | kind | build route |
|---|---|---|---|
| `executor/Configure.xml` | `Sequence Executor.lvclass:Configure.vi` | static public | `lvai_add_class_method` |
| `executor/Configure Plant Displays.xml` | `…:Configure Plant Displays.vi` | static public (**added**, Q1) | same |
| `executor/Load Sequence.xml` | `…:Load Sequence.vi` | message method | same, then message maker |
| `executor/Start Sequence.xml` | `…:Start Sequence.vi` | message method | same |
| `executor/Stop Sequence.xml` | `…:Stop Sequence.vi` | wrapper for Stop Sequence Msg (**added**) | same |
| `executor/Emergency Stop.xml` | `…:Emergency Stop.vi` | wrapper for Emergency Stop Msg (**added**) | same |
| `executor/Process Feedback.xml` | `…:Process Feedback.vi` | message method | same |
| `executor/Abort Sequence.xml` | `…:Abort Sequence.vi` | method, called by the wrappers | same |
| `executor/Begin Step.xml` | `…:Begin Step.vi` | private static | same |
| `executor/Finish Sequence.xml` | `…:Finish Sequence.vi` | private static | same |
| `executor/Update Displays.xml` | `…:Update Displays.vi` | private static | same |
| `executor/Reset Results.xml` | `…:Reset Results.vi` | private static (**added** helper) | same |
| `executor/ActorCore Hook - Launch Plant.xml` | `…:Launch Plant.vi` = body of the **Actor Core override** | hook | method, then `lvai_create_override "Actor Core"`, then `lvai_af_add_hook shape=series` |
| `executor/StopCore Hook - Signal Stopped.xml` | `…:Signal Stopped.vi` = body of the **Stop Core override** | hook | `lvai_create_override "Stop Core"`, then `lvai_af_add_hook shape=seriesAfter` |
| `simplant/ActorCore Hook - Start Tick.xml` | `Sim Plant.lvclass:Start Tick.vi` (Actor Core override) | hook | series |
| `simplant/StopCore Hook - Stop Tick.xml` | `Sim Plant.lvclass:Stop Tick.vi` (Stop Core override) | hook | seriesAfter |
| `simplant/Set Setpoints.xml` | `Sim Plant.lvclass:Set Setpoints.vi` | message method | method + maker |
| `simplant/Tick.xml` | `Sim Plant.lvclass:Tick.vi` | message method | method + maker |
| `launcher/Launch Sequence Executor.xml` | `<project root>\Launch Sequence Executor.vi` | plain VI | **`lvai_generate_vi_with_events`** (NI's converter silently drops event frames) |
| `MESSAGES.md` | the 7 message classes, payloads, priorities | | `lvai_create_message_class` |
| `TEST_CASES.md` | Caraya cases for the Logic VIs + e2e checklist | | `labview-caraya-unit-test` agent |

**Why the overrides are hooks.** The plugin says: *"AIXML cannot author `Call Parent Class Method`"*. A generated override is eBad. So each override is made with `lvai_create_override` (NI's provider), and its body is a member "hook" VI placed with `lvai_af_add_hook`. Each hook file's header comment gives the exact call. The finished Stop Core equals the user's `CounterActor.lvclass:Stop Core.vi`.

**Suggested build order** (plugin `af-override-tools.md` §1):
1. Logic VIs done.
2. Class private data per spec §5/§6, with typedef binding.
3. Methods (this folder).
4. Typedef pane binding.
5. Messages (`MESSAGES.md`). They must exist before anything that calls a `Send …` VI compiles: `Begin Step`, `Finish`, `Abort`, `Tick`, the launcher. Generate those with placeholders, or after the maker runs.
6. Overrides, then hooks.
7. Launcher.
8. Tests.

**Common conventions in the drafts.** These are copied from `CounterActor` exports.
- Pane 4815: `Actor in` 11, payload 10, `error in` 8, `Actor out` 3, `error out` 0, all `required`.
- Class wires are `ref{UDClassInst}`.
- Private data is read and written with `Unbundle By Name` / `Bundle By Name` (`Bundle By Name` lists fields before `input cluster`, per the doc).
- Class constants are labelled `path` seeds, to be swapped with `lvai_swap_subvis constantsJson`.
- Typedef constants carry the typedef's name as `_name`, for `lvai_bind_typedef_constants`.
- The plugin's class-method route (`lvai_add_class_method` with `dispatchTerminals`, placeholder plus swap for calls to sibling members) still applies. Calls to sibling members are written as `Sequence Executor.lvclass\3A<name>.vi`.

## UNVERIFIED spellings (each is also marked `<!-- UNVERIFIED -->` in the file)

| # | item | where | why unverified / how to check |
|---|---|---|---|
| U1 | Terminal labels of **`Read Sequence File.vi`** (`path`, `error in` → `Sequence File`, `error out`) | Load Sequence | VI not built yet; labels from spec §4 literally. The 3 built Logic VIs match spec labels exactly, so likely. `lvai_vi_terminals` |
| U2 | Terminal labels of **`Evaluate Step.vi`** (`Step Config`, `Plant Feedback`, `Step Phase in`, `step start ms`, `dwell start ms` → `Step Phase out`, `dwell start ms out`, `done`, `passed`, `reason`, `measured`, `target`) | Process Feedback | not built yet |
| U3 | Terminal labels of **`Build Step Table.vi`**: inputs `Sequence File`, `Step Result array`; output **`Step Table`** (a guess; spec says only "2-D string array") | Update Displays | not built yet |
| U4 | Terminal labels of **`Write Results CSV.vi`** (`results folder path`, `sequence_id`, `Step Result array`, `overall verdict`, `error in` → `file path`, `error out`) | Finish Sequence | not built yet |
| U5 | **`Step Phase.ctl` base type** written as `uint16{Idle,Settling,Dwell,Complete}` | Start/Begin/Finish/Abort | `.ctl` not readable offline; the enum may be U8/U32. Values are indices 0..3 |
| U6 | `ref{LV.Digital}{int32}` for Step Index Display | Configure | only `ref{LV.Digital}{double}` is evidenced |
| U7 | conIdx **6, 5, 4** as input slots on pattern 4815 | Configure, Configure Plant Displays | sample proves 11/10/9/8/7 in, 3/0 out only |
| U8 | Writing a chart's `Value` through generic `{LV.Control}` + Variant appends a point per plot (behaviour) | Process Feedback | spelling `write+Value` on `{LV.Control}` is evidenced; the chart behaviour is not |
| U9 | Feedback Chart indicator `style="graph21717"` with `type="cluster{double.Pressure,double.Flow,double.Displacement}"` | launcher | token evidenced only for waveform charts; 3-plot cluster chart not measured |
| U10 | Step Table as a Table control: **no style token known**; drafted as `array.2{string}` indicator | launcher | if a real Table is wanted, drop one by hand, export, read the `style=` |
| U11 | Unwired indicator spelled `inputs="value:"` (Step Table, Feedback Chart) | launcher | only the Control analogue `outputs="value:"` is in the samples |
| U12 | Empty `path` control default `value=""` (Config Path) | launcher | not evidenced; empty → default sequence via `Empty String/Path?` |
| U13 | Time-Delay Override Options enum constant type and value 3 = "Stop all further copies" must match the notifier element type (typedef) | Stop Tick | labels read from NI's own constant offline; typedef binding may be needed |

Evidenced and used, worth knowing:
- `Actor Framework.lvlib\3ATime-Delayed Send Message.vi`, a library member and not in a class. Inputs `Message Enqueuer`, `Message`, `Milliseconds To Wait`, `# Copies (0 = infinite repeat)`, `Message Priority (Normal)`, `error in (no error)`; outputs `Delivery Notifier`, `error out`.
- `…\3AActor.lvclass\3ALaunch Nested Actor.vi`. Inputs `Caller Actor in`, `Nested Actor`, `Auto-stop? (T)`, `Debug Alias`, `error in (no error)`; outputs `Caller Actor out`, `Nested Actor's Enqueuer`, `error out`.
- `…\3AActor.lvclass\3ARead Caller Enqueuer.vi` (`Actor` → `Caller Enqueuer`) and `…\3ARead Self Enqueuer.vi` (`Actor` → `Self Enqueuer`). Both are **protected**, as is Launch Nested Actor, so callers must be members of the actor class.
- There is no `Call Parent Method` spelling to verify: it is never authored (see hooks).

## Open questions / decisions for the user or build agent

- **Q1, Configure split.** Spec has one `Configure.vi` with 8 refs + notifier + folder. That is 14 terminals, more than the 12 slots of pattern 4815. Drafted as `Configure.vi` (Status, Step Index, Step Table, Verdict, Stopped Notification, Results Folder) plus `Configure Plant Displays.vi` (Pressure, Flow, Displacement, Chart). Alternatives: a cluster of refs, or a larger pane pattern.
- **Q2, added helpers.** `Reset Results.vi` (shared by Load/Start), `Stop Sequence.vi` and `Emergency Stop.vi` (no-payload wrappers so the maker yields the spec's message names), and `Update Displays` with a `Status` string input.
- **Q3, message names.** The maker's defaults are `Process Feedback Msg` / `Send Process Feedback.vi` and `Tick Msg`. Spec says `Feedback Msg` and `Plant Tick Msg`. Either rename the methods (`Feedback.vi`, `Plant Tick.vi`) or accept the defaults. The drafts use the defaults.
- **Q4, E-Stop "critical priority" is not reachable** from user code. The public enum is Low/Normal/High, and `Enqueue Critical.vi` is community scope. The drafts send at **High**. A spec change is needed, or accept it.
- **Q5, error wire on the Actor Core series hooks.** The plugin warns: with `wireError=true`, a failed Launch Nested Actor / Time-Delayed Send makes the actor end silently and the next Send fails with 1556. With `false` the error is dropped. The drafts assume `true`.
- **Q6, Begin Step timing.** Step Start ms = Last Feedback timestamp (spec). If Start arrives before the first Feedback Msg (within about 100 ms of launch), the timestamp is 0 and the step times out at once. Option: use Tick Count when `Last Feedback.timestamp_ms` = 0.
- **Q7, Abort when idle.** The drafts always send safe setpoints and show `<reason> (no sequence running)`. Spec says safe setpoints only "if Running".
- **Q8, Evaluate Step edge semantics.** These are not fixed by the spec: `Step Phase in` = Idle/Complete; `dwell_time_ms` = 0; whether the sample that enters Dwell can also complete it. The test drafts assume it cannot.
- **Q9, monitored_io matching** is case-sensitive in the built `Select Monitored Signal.vi`. Keep it, or normalise?
- **Q10, Build Step Table number formatting** (decimals for Target/Tol/Measured/Duration) and behaviour on a results/steps length mismatch are not specified.
- **Q11, launcher location.** Results folder and default config are derived from `Strip Path(Current VI's Path)`. This assumes the launcher is saved in the project root (as `Launch Message Counter.vi` is).
- **Q12, Stop Tick.** NI's Core releases the delivery notifier itself after the stop notification, so the extra `Release Notifier` in the hook may return a benign error (left unwired).
- **Q13, comments.** Each draft carries `<!-- … -->` XML comments. If NI's validator objects to comments before the `<VI>` root, strip them before `lvai_check_aixml`.
- Status strings use ASCII " - " instead of the spec's em dash, to avoid non-ASCII in `value`.

## Offline lint done here

All 19 XML files parse. uids are unique per file. Every consumed net is produced in the same file. Every Case/Event output tunnel is wired in every frame. That is a structural check only; nothing was validated by LabVIEW.
