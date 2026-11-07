# Universal Sequence Executor (Host, Actor Framework) — Design v2

Status: authoritative build spec. v2 (2026-11-07) replaces the VTU-specific v1: the executor core is
**rig-agnostic**; a test rig (VTU first) is a **plug-in**.
Pattern reference: the user's hand-built Counter sample (`CounterActor/`, `Messages/`, `Launch Message Counter.vi`).
`_legacy/` (Antigravity output) is NOT used.

Scope: **Host only, Actor Framework.** No cRIO/RT code now. The RT sequence executor will later be a **QMH**;
so all sequencing logic lives in plain AF-free VIs (`src/Logic/`, typedef clusters only) that the RT QMH can call unchanged.

## 1. Concept

```
Launch Sequence Executor.vi          UI (event loop, like Launch Message Counter.vi)
  └─ Sequence Executor.lvclass       universal core — knows only CHANNEL NAMES, never "pressure"/"VTU"
       └─ <Rig plug-in>              nested actor, class chosen at runtime from the rig config file
            Rig.lvclass  (abstract base, child of Actor)
              └─ VTU Sim Rig.lvclass (first plug-in: simulated pressure/flow/displacement)
              └─ (later) VTU cRIO Rig, Motor Rig, ...
```

- The executor talks to any rig with two generic messages:
  executor → rig: **Apply Setpoints Msg** (array of {channel, value});
  rig → executor: **Channel Feedback Msg** (array of {channel, value} + timestamp ms).
- Changing rigs = changing the rig config file. No executor code changes.

## 2. Files and formats

Sequence file (e.g. `configs/sequences/vtu_actual_sequence.json`):
```json
{ "sequence_id": "VTU_ACTUAL_SEQUENCE_001", "description": "...",
  "rig_config": "../rigs/vtu_sim.json",
  "steps": [
    { "step_no": 1, "step_name": "Pre-fill & Prime", "command_type": "RAMP_PRESSURE",
      "setpoints":  [ {"channel":"Pressure","value":20}, {"channel":"Flow","value":15}, {"channel":"Displacement","value":0} ],
      "conditions": [ {"channel":"Pressure","target":20,"tolerance":2} ],
      "dwell_time_ms": 1000, "timeout_ms": 5000, "expected_result": "PASS" } ] }
```
`rig_config` is relative to the sequence file's folder.

Rig config (e.g. `configs/rigs/vtu_sim.json`):
```json
{ "rig_id": "VTU_SIM", "description": "Simulated VTU hydraulic rig",
  "plugin_class": "../../plugins/VTU Sim Rig/VTU Sim Rig.lvclass",
  "channels": [ {"name":"Pressure","unit":"bar","min":0,"max":250},
                {"name":"Flow","unit":"lpm","min":0,"max":120},
                {"name":"Displacement","unit":"mm","min":-50,"max":50} ] }
```
`plugin_class` is relative to the rig config file's folder.

## 3. Typedefs (`src/Typedefs/`) — field labels equal JSON keys

| Typedef | Fields |
|---|---|
| Channel Value.ctl | channel String, value DBL |
| Condition.ctl | channel String, target DBL, tolerance DBL |
| Step Config.ctl | step_no I32, step_name String, command_type String, setpoints [Channel Value], conditions [Condition], dwell_time_ms I32, timeout_ms I32, expected_result String |
| Sequence File.ctl | sequence_id String, description String, rig_config String, steps [Step Config] |
| Channel Definition.ctl | name String, unit String, min DBL, max DBL |
| Rig Config.ctl | rig_id String, description String, plugin_class String, channels [Channel Definition] |
| Channel Feedback.ctl | channels [Channel Value], timestamp_ms DBL |
| Step Phase.ctl | enum Idle, Settling, Dwell, Complete (unchanged) |
| Step Result.ctl | step_no I32, step_name String, result String (NOT RUN/RUNNING/PASS/FAIL/ABORTED), reason String, measured DBL, target DBL, duration_ms DBL (unchanged) |

Removed from the core: `Plant Feedback.ctl`, `Plant Setpoints.ctl` (VTU-specific; the VTU plug-in keeps its own private state).

## 4. Logic VIs (`src/Logic/`, AF-free, Caraya-tested)

| VI | In → Out | Behaviour |
|---|---|---|
| Parse Sequence JSON | JSON string, error in → Sequence File, error out | Unflatten From JSON; empty steps → error 5001 "sequence has no steps" |
| Read Sequence File | path, error in → Sequence File, rig config path, error out | reads + parses; rig config path = sequence folder / rig_config |
| Read Rig Config | path, error in → Rig Config, plugin class path, error out | parse; plugin class path = rig folder / plugin_class; no channels → error 5002 |
| Validate Sequence | Sequence File, Rig Config, error in → valid Bool, problems [String], error out | every setpoint/condition channel exists in rig; every setpoint within min/max; tolerance ≥ 0; timeout_ms > 0 (SRS-F-023). Returns problems, not an error. |
| Lookup Channel | Channel Feedback, channel String → value DBL, found Bool | linear search by name (exact match) |
| Evaluate Conditions | conditions [Condition], Channel Feedback → all within Bool, all found Bool, measured DBL, target DBL, missing channel String | AND of `UE_Within_Tolerance` per condition; measured/target = first condition NOT within (else last condition); empty conditions → all within T |
| Evaluate Step | Step Config, Channel Feedback, Step Phase in, step start ms, dwell start ms → Step Phase out, dwell start ms out, done, passed, reason, measured, target | same state machine as v1 using Evaluate Conditions: missing channel → Complete/FAIL "Missing channel <name>"; timeout (checked first) → FAIL "Timeout"; Settling + all within → Dwell (dwell start = now); Dwell + not within → Settling; Dwell + dwell elapsed ≥ dwell_time_ms → PASS. now = feedback.timestamp_ms. Uses UE_Elapsed_Ms, UE_Timeout_Reached, UE_Dwell_Reached. |
| Build Step Table | Sequence File, Step Results → 2-D String | columns: Step, Name, Command, Setpoints ("Pressure=20; Flow=15"), Conditions ("Pressure 20±2"), Dwell ms, Timeout ms, Result, Measured, Target, Duration ms, Reason |
| Write Results CSV | results folder, sequence_id, rig_id, Step Results, overall verdict, error in → file path, error out | as v1 plus rig_id line; creates folder |
| Safe Setpoints | Rig Config → [Channel Value] | every rig channel = 0 clamped into [min,max] (used by Stop/E-Stop/Finish) |

## 5. Rig.lvclass (abstract base, `src/Rig/`, inherits Actor)

Private data: `Rig Config` (Rig Config), `Channels` (current feedback, Channel Feedback).
- `Apply Setpoints.vi` — **dynamic dispatch, must override**; base does nothing.
- `Publish Feedback.vi` (static, protected) — sends Channel Feedback Msg to the caller (Read Caller Enqueuer).
- `Set Rig Config.vi` (static, public) — called by the executor before launch.
Message: `Apply Setpoints Msg` (array of Channel Value) targets Rig.lvclass → dynamic dispatch to the plug-in.

## 6. VTU Sim Rig.lvclass (plug-in, `plugins/VTU Sim Rig/`, inherits Rig)

Private data: `Setpoints` [Channel Value], `State` [Channel Value], `Tick Notifier` (Time-Delay Override Options notifier).
- Override `Apply Setpoints.vi` — store setpoints.
- Actor Core hook — Time-Delayed Send Message (Tick Msg, 100 ms, forever) to self; store notifier. Stop Core hook — stop it.
- `Tick.vi` — each channel: x += (sp − x)(1 − exp(−dt/tau)), dt 0.1 s; tau Pressure 0.8 s, Flow 0.6 s, Displacement 0.3 s, other 0.5 s; then Publish Feedback (timestamp = Tick Count ms).
- `Sim First Order Step.vi` (plug-in internal) — the per-channel math, Caraya-tested (0→100, dt 0.1, tau 0.8 → 11.750309742).

## 7. Sequence Executor.lvclass (`src/Executor/`, inherits Actor)

Private data: `Sequence` (Sequence File), `Rig Config` (Rig Config), `Results` [Step Result], `Loaded`, `Running` Bool, `Step Index` I32, `Phase` (Step Phase), `Step Start ms`, `Dwell Start ms` DBL, `Last Feedback` (Channel Feedback), `Rig Enqueuer` (Message Enqueuer), `Results Folder` Path, `Overall Verdict` String, display refs (Status, Step Index, Step Table, Channel Values (2-D string), Verdict, Feedback Chart), `Stopped Notification` (Boolean notifier).

- `Configure.vi` / `Configure Displays.vi` — refs, notifier, results folder.
- Stop Core hook — Send Notification TRUE (like CounterActor).
- `Load Sequence.vi` (path) — refuse while Running. Read Sequence File → Read Rig Config → Validate Sequence. Any error/invalid → Status "LOAD ERROR: …" (no error returned). Else: if a rig is running, send it Normal Stop; Get LV Class Default Value (plugin class path) → To More Specific Class (Rig) → Set Rig Config → **Launch Nested Actor** (Auto Stop T) → store Rig Enqueuer; Results all NOT RUN; Loaded T; Status "LOADED <id> on <rig_id> (<n> steps)".
- `Start Sequence.vi` — needs Loaded and not Running; reset results; index 0; Running T; Begin Step.
- `Begin Step.vi` — result RUNNING, Phase Settling, `Step Start ms = -1`, send Apply Setpoints Msg (step setpoints).
- `Process Feedback.vi` (Channel Feedback) — store; update channel display + chart; if Running: if Step Start = −1 latch it to feedback timestamp; Evaluate Step; on done record result and advance or Finish.
- `Finish Sequence.vi` — Running F; verdict PASS iff every result == expected_result; write CSV; Apply Safe Setpoints; Status "COMPLETE: <verdict> — <file>".
- `Abort Sequence.vi` (reason) — current step ABORTED, Apply Safe Setpoints, Running F, verdict "ABORTED".
- Methods called from Do.vi never return errors for operator mistakes (show in Status instead). Display writes ignore invalid refs.

Executor messages (`src/Executor Messages/`): Load Sequence Msg (path), Start Sequence Msg, Stop Sequence Msg (Abort "STOPPED BY OPERATOR"), Emergency Stop Msg (Abort "E-STOP", sent at **High** priority — AF has no public Critical), Channel Feedback Msg (Channel Feedback).
Rig messages (`src/Rig Messages/`): Apply Setpoints Msg. VTU plug-in messages (`plugins/VTU Sim Rig/Messages/`): Tick Msg.

## 8. Build notes

- Actor Core / Stop Core overrides: `lvai_create_override` + `lvai_af_add_hook` (AIXML cannot author Call Parent Method). Launcher: `lvai_generate_vi_with_events` (plain converter drops event frames).
- Typedef bind helper must chain the error through the Replace loop before Save (see docs/HANDOVER.md §8).

## 9. Verification

- Caraya tests for every Logic VI and Sim First Order Step.
- End to end: launcher, Load `configs/sequences/vtu_actual_sequence.json`, Start → all 5 steps PASS (worst case step 5 ≈ 4.4 s < 5 s timeout), CSV in `results/`; Stop / E-Stop mid-run → ABORTED + safe setpoints, actor alive; Exit → Stopped cleanly.
- Universality check: a second rig config with different channel names loads and validates without any executor change (a sequence that references an unknown channel is rejected by Validate Sequence).
