# Universal Sequence Executor (Host, Actor Framework)

A LabVIEW 2026 (64-bit) Actor Framework host that executes a hardware-agnostic test
sequence against a rig plug-in. The rig is a LabVIEW class; the executor sends setpoints,
evaluates conditions on the published feedback, advances the step state machine, and
writes a results CSV.

## Layout

| Path | Content |
|---|---|
| `src/Logic/` | AF-free Logic VIs (parse, read, validate, lookup, evaluate, table, CSV, safe setpoints) |
| `src/Typedefs/` | Shared typedefs (Sequence File, Step Config, Channel Feedback, Step Result, ...) |
| `src/Rig/` | `Rig.lvclass` (abstract actor base): Set Rig Config, Publish Feedback |
| `src/Rig Messages/` | `Apply Setpoints Msg` |
| `plugins/VTU Sim Rig/` | `VTU Sim Rig.lvclass` (the plug-in): Apply Setpoints, Tick, Sim First Order Step, Actor Core tick timer (100 ms), `Messages/Tick Msg` |
| `src/Executor/` | `Sequence Executor.lvclass`: Load/Start/Stop/Emergency Stop/Process Feedback + Configure, Update Displays, Begin/Finish/Abort Sequence, Launch Executor, accessors, Stop Core hook |
| `src/Executor Messages/` | Load / Start / Stop / Emergency Stop / Channel Feedback messages |
| `configs/` | `sequences/vtu_actual_sequence.json` (5-step VTU test), `sequences/vtu_timeout_test.json` (timeout-FAIL case), `rigs/vtu_sim.json` |
| `tests/manual/` | Manual test VIs (full run, stop mid-run, E-stop mid-run, launch/apply-setpoints) |
| `tests/caraya/` | Caraya tests |
| `Sequence Executor Launcher.vi` | The interactive UI (Load / Start / Stop / E-Stop / Exit buttons) |

## How to run

1. Open `Universal_Sequence_Executor_AF.lvproj`.
2. Run `Sequence Executor Launcher.vi`. Press **Load**, then **Start**. Watch Status,
   Step Table, Channel Values and Verdict. **Stop** aborts the current step (safe
   setpoints); **E-Stop** does the same at High priority. **Exit** stops the actor and
   waits for the Stopped Notification.
   > Use the Exit button to close (the Panel Close filter is not registered; see
   > `docs/DESIGN_AF_EXECUTOR.md` §7a).
3. The results CSV is written to `results/` by Finish Sequence, or check the manual test
   VIs under `tests/manual/` (they run headless and write the CSV + traces).

## Verified end-to-end (recorded)

`results/VTU_ACTUAL_SEQUENCE_001_20261109_022913.csv` (all 5 steps PASS):

| step | name | result | measured | target | duration ms |
|---|---|---|---|---|---|
| 1 | Pre-fill & Prime | PASS | 19.467 | 20.0 | 2805 |
| 2 | Pressure Ramp | PASS | 79.720 | 80.0 | 4211 |
| 3 | Operating Point Dwell | PASS | 99.956 | 100.0 | 4808 |
| 4 | Flow Check & Stroke | PASS | 59.914 | 60.0 | 3007 |
| 5 | Depressurize & Safe | PASS | 0.409 | 0.0 | 4309 |

Stop mid-run → step ABORTED "STOPPED BY OPERATOR"; E-Stop (High priority) → ABORTED
"E-STOP"; actor stays alive after both. `results/VTU_TIMEOUT_TEST_20261109_012723.csv`
shows a too-short timeout failing with "Timeout" (duration 502 ms).

## Design and build notes

- Spec: `docs/DESIGN_AF_EXECUTOR.md` (v2, §7 method contracts, §7a as-built deviations).
- AIXML authoring recipe: `docs/HANDOVER.md` §9 (accessors only, no class-wire
  Bundle/Unbundle, stubs then `lvai_swap_subvis`, validate-before-convert, off-pane class
  controls for casts).
- Connector pane rules: `docs/CONNECTOR_PANE_RULES.md` (pattern 4815; measured terminal
  numbering top 7/5, bottom 6/4).
- Agent bridge protocol: `AGENT_PROTOCOL.md`.

## Known deviations (spec §7a)

- `Rig.Channels` exists but is not written; the VTU Sim Rig builds the Channel Feedback
  value directly and passes it to Publish Feedback.
- The rig does not store the Time-Delayed Send notifier; the tick helper ends when the
  actor's queue is released at stop.
- Channel Feedback Msg's sender is named `Send Process Feedback.vi`.
- The launcher's Panel Close filter is not registered; use the Exit button.
- Process Feedback skips Evaluate Step (and the Step Start latch) while Settling with an
  empty channel list, guarding the first empty feedback after Start.
