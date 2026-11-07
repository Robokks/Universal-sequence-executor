# HANDOVER — Universal Sequence Executor (Host, Actor Framework)

**Snapshot: 2026-11-07, 16:30.** For any AI agent (Claude, Codex, DeepSeek, Antigravity) or engineer continuing the work.
Environment: Windows 10, **LabVIEW 2026 64-bit (26.3.1f1)**, Actor Framework from vi.lib, Caraya installed.
Spec: **`docs/DESIGN_AF_EXECUTOR.md` (v2) is authoritative.** This file = state + rules + next steps.
Code: local `C:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor-AF`, git branch **`af-host`** on
https://github.com/Robokks/Universal-sequence-executor (do NOT push to `main` — it holds the separate QMH project).
Backup zip: `C:\Users\DynaAdmin\PycharmProjects\Backups\Universal-sequence-executor-AF_20261107_1627.zip`.

---

## 0. Rules (non-negotiable)

1. **Nothing counts as done until it ran in LabVIEW** and the real output was recorded (values, CSV contents, JUnit counts). No "PASS" from Python or from reading code.
2. **`_legacy/` is not source.** `_legacy/` root = Antigravity output (fake: text files disguised as .vi/.lvclass, placeholder diagrams, false "142/142 PASS"). `_legacy/v1/` = our own superseded VTU-specific v1 — reference only.
3. Never hand-write `.vi` / `.ctl` / `.lvclass` files. Create and edit them through LabVIEW (AIXML conversion / VI scripting via the LabVIEW MCP server).
4. Do not modify the user's AF reference sample: `CounterActor/`, `Messages/`, `Launch Message Counter.vi`, `Test Actor Messaging.vi`. Copy its style.
5. **One agent on LabVIEW at a time.** Parallel use of the single LabVIEW instance has crashed it. A **modal error dialog blocks all automation** until a human clicks it — wire every error terminal in helper VIs.
6. Do not invent fields, terminals or behaviour. If the spec doesn't say it, ask the user.

## 1. Goal and scope (agreed with the user)

- A **universal** (rig-agnostic) sequence executor. The core only knows **channel names**; a test rig is a **plug-in**. **VTU is the first plug-in**, not the core. (v1 had VTU baked into the core; the user rejected it.)
- **Host only, Actor Framework.** No cRIO/RT now.
- Later, the **RT executor will be a QMH** (not AF). Therefore all sequencing logic is in **AF-free plain VIs** in `src/Logic/` (typedef clusters only) so the RT QMH can reuse them unchanged.
- Rig for now: **simulated VTU** (Pressure, Flow, Displacement). No hardware.

## 2. Architecture

```
Launch Sequence Executor.vi        UI event loop (modelled on Launch Message Counter.vi)
  └─ Sequence Executor.lvclass     universal core, inherits Actor
       └─ <rig plug-in>            class path read from configs/rigs/*.json, loaded at runtime
            Rig.lvclass            abstract base, inherits Actor   (src/Rig/)
              └─ VTU Sim Rig.lvclass                               (plugins/VTU Sim Rig/)
```
- Executor → rig: `Apply Setpoints Msg` = array of {channel, value} (targets Rig, dynamic dispatch to the plug-in).
- Rig → executor: `Channel Feedback Msg` = {channels [{channel, value}], timestamp_ms}. VTU Sim Rig ticks itself every 100 ms.
- Step: apply setpoints → Settling until ALL conditions within tolerance → Dwell for dwell_time_ms → PASS. Whole step > timeout_ms → FAIL "Timeout". Leaving tolerance in Dwell → back to Settling. Missing channel → FAIL. "now" = feedback timestamp.
- Load validates the sequence against the rig's channel list and limits before allowing Start.

## 3. Current state — file by file

| Path | Content | State |
|---|---|---|
| `Universal_Sequence_Executor_AF.lvproj` | folders 12_Utilities, Logic (auto-populating `src/Logic`), Typedefs, Samples, Plugins; classes | opens clean (no Error 74, no missing items) as of 16:15 |
| `configs/sequences/vtu_actual_sequence.json` | 5-step VTU sequence, **generic v2 format** (setpoints + conditions by channel, `rig_config`) | ✅ valid JSON, UTF-8 **without BOM** |
| `configs/rigs/vtu_sim.json` | VTU rig: rig_id, plugin_class (relative path), 3 channels with unit/min/max | ✅ valid JSON, no BOM |
| `configs/actual_vtu_sequence.json` | old v1 format, source of the conversion | not used |
| `src/Typedefs/` | Channel Value, Condition, Step Config, Sequence File, Channel Definition, Rig Config, Channel Feedback, Step Phase (U16 enum Idle/Settling/Dwell/Complete), Step Result | ✅ v2, array elements bound, verified from files. Plain typedefs (not strict). |
| `src/12_Utilities/` | 28 UE_* utility VIs (all DBL). Used: UE_Within_Tolerance (actual,target,tolerance→within_tolerance), UE_Elapsed_Ms (now_ms,start_ms→elapsed_ms), UE_Timeout_Reached / UE_Dwell_Reached (elapsed_ms,threshold_ms→reached) | ✅ genuine, kept |
| `src/Executor/Sequence Executor.lvclass` | v2 private data (spec §7), **0 methods** | ✅ data verified; ⬜ methods not built |
| `src/Rig/Rig.lvclass` | fields Rig Config, Channels; `Apply Setpoints.vi` (dynamic, pass-through), `Set Rig Config.vi` (static) | ✅ verified. ⚠ "Require descendants to override" flag NOT set — set it in the IDE (member → Properties). ⬜ `Publish Feedback.vi` not built (needs executor's Channel Feedback Msg). |
| `plugins/VTU Sim Rig/VTU Sim Rig.lvclass` | inherits Rig; fields Setpoints, State [Channel Value], Tick Notifier (AF Time-Delay Override Options notifier); `Apply Setpoints.vi` override stores setpoints | ✅ verified (inheritance, dynamic dispatch). ⬜ Tick, Actor Core/Stop Core hooks, Sim First Order Step not built |
| `src/Logic/` | **EMPTY.** The generic v2 rework was stopped before writing anything. | ⬜ **next task** |
| `_legacy/v1/Logic/` | the 7 v1 Logic VIs (VTU-specific, were verified by running under v1). Now BROKEN against v2 typedefs. | reference only: same state machine / tolerance / CSV logic to port |
| `tests/caraya/` | 5 v1 test VIs + heartbeat file from a stopped test agent | ❌ obsolete (test v1 VIs) — delete or move to `_legacy/v1/tests/` |
| `build/staging/` | offline AIXML drafts for v1 executor/sim-plant methods + launcher, MESSAGES.md, TEST_CASES.md, README.md (UNVERIFIED list) | ⚠ written for v1 names (Plant Feedback, Sim Plant). Reuse the structure, adapt to v2 channel model. Never validated by LabVIEW. |
| `results/` | not created yet | — |

## 4. What was proven (v1, by real LabVIEW runs)

These are no longer in `src/`, but they prove the techniques work in this environment:
- `Unflatten From JSON` into a typedef cluster with labels = JSON keys works (5 steps parsed, step values correct).
- Step state machine (Settling/Dwell/Complete, timeout priority over dwell, re-settle on leaving tolerance) behaved exactly as spec on 7 cases.
- First-order sim: 0→100, dt 0.1, tau 0.8 → 11.7503097 ✔.
- CSV writer created the folder and wrote a real file; Create Folder "already exists" error 10 must be cleared.
- Sim timing budget: worst step (5) ≈ 4.4 s settle+dwell vs 5 s timeout → all 5 steps should PASS.

## 5. Next steps (in this order)

1. **Logic VIs v2** in `src/Logic/` per spec §4: Parse Sequence JSON, Read Sequence File, Read Rig Config, Validate Sequence, Lookup Channel, Evaluate Conditions, Evaluate Step, Build Step Table, Write Results CSV, Safe Setpoints. Plus `plugins/VTU Sim Rig/Sim First Order Step.vi` (spec §6). Port logic from `_legacy/v1/Logic/`. Verify each by running (cases in spec §4 + `build/staging/TEST_CASES.md`).
2. **Messages:** Load Sequence Msg (path), Start Sequence Msg, Stop Sequence Msg, Emergency Stop Msg (High priority), Channel Feedback Msg (Channel Feedback) in `src/Executor Messages/`; Apply Setpoints Msg in `src/Rig Messages/`; Tick Msg in `plugins/VTU Sim Rig/Messages/`. Use the AF message maker (`lvai_create_message_class`).
3. **Rig:** `Publish Feedback.vi` (protected; Read Caller Enqueuer → Send Channel Feedback).
4. **VTU Sim Rig:** Actor Core hook (Time-Delayed Send Message: Tick Msg to self, 100 ms, forever; store notifier), Stop Core hook (stop it), `Tick.vi` (Sim First Order Step dt 0.1 → Publish Feedback, timestamp = Tick Count ms).
5. **Executor methods** per spec §7: Configure, Configure Displays, Stop Core hook (Send Notification TRUE), Load Sequence (read + validate + Get LV Class Default Value → To More Specific (Rig) → Set Rig Config → Launch Nested Actor, Auto Stop T), Start Sequence, Begin Step (Step Start = −1), Process Feedback (latch Step Start on first feedback, Evaluate Step, advance/finish), Finish Sequence (verdict, CSV, safe setpoints), Abort Sequence, Update Displays, Reset Results.
6. **Launcher** `Launch Sequence Executor.vi` (project root). Controls: Sequence Path, Load, Start, Stop Sequence, E-Stop, Exit. Indicators: Status, Current Step, Step Table, Channel Values, Verdict, Feedback Chart. Exit/Panel Close → Send Normal Stop + Wait on Stopped Notification (5000 ms), exactly like the Counter sample.
7. **Caraya tests** for all Logic VIs and Sim First Order Step in `tests/caraya/`.
8. **Acceptance (spec §9):** run launcher → Load `configs/sequences/vtu_actual_sequence.json` → Start → 5/5 PASS, verdict PASS, CSV in `results/`. Stop and E-Stop mid-run → ABORTED + safe setpoints, actor alive. Exit → stopped cleanly. Universality: a second rig JSON with other channel names loads with no executor change; a sequence with an unknown channel is rejected at Load.
9. Write a new `README.md` (old one is `_legacy/README_antigravity.md`).

## 6. Design rules that are easy to get wrong

- Methods called from a `Do.vi` must **not return errors for operator mistakes** (bad path, start before load, start while running, invalid sequence). Report in Status, return no error — otherwise AF stops the actor.
- Display writes must ignore invalid refs (so headless smoke tests work).
- `Begin Step` sets `Step Start ms = −1`; `Process Feedback` latches the first feedback timestamp → no instant timeout if Start precedes the first feedback.
- E-Stop at **High** priority (AF has no public Critical).
- Relative paths in JSON: `rig_config` relative to the sequence file folder; `plugin_class` relative to the rig file folder.
- JSON files must be written **without BOM** (PowerShell 5.1 `Set-Content -Encoding utf8` adds one).

## 7. LabVIEW automation gotchas (all observed in this project)

- **AIXML cannot author "Call Parent Class Method"** → create Actor Core / Stop Core overrides with `lvai_create_override` and put the body in a hook VI via `lvai_af_add_hook` (Actor Core: series; Stop Core: seriesAfter).
- **NI's AIXML converter drops event-structure frames** → generate the launcher with `lvai_generate_vi_with_events` and check every event case exists afterwards.
- **Typedef bind race:** the shipped bind helper can Save/Close before Replace finishes → Error 1055 dialog and a file without the typedef. Fix: chain the error wire through a shift register across the Replace loop so Save waits for it.
- `lvai_create_class` re-adds the Samples classes as duplicates at My Computer level after each class → next open fails with **Error 74**. Remove the duplicates (project closed) after every class creation.
- Closing a project that is open but not active can save a stale copy over the `.lvproj` (once dropped the Plugins folder). Re-check the `.lvproj` after closes.
- `lvai_add_class_method` ignores `mustOverride`.
- LabVIEW crashed once during class field binding (files were already saved). After a crash: restart, re-check files, don't redo blindly. `lvai_ensure_labview` restart clears `Documents\LabVIEW Data\LVAutoSave\archives`.
- Bundle By Name on a class wire fails pre-validation; converting with `validateFirst: false` produced executable VIs.

## 8. Open questions for the user

1. Strict typedefs instead of plain?
2. Real VTU acceptance values (setpoints, tolerances, timeouts) must come from the approved workbook (`vtu.pdf` / test owner); the JSON values are examples.
3. RT QMH port: cRIO model, I/O, timing budget, Host↔RT transport — not started.
