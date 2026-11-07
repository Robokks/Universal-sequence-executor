# Caraya test cases: Logic VIs (`src/Logic/`) and end-to-end acceptance

Target folder per spec §7: `tests/caraya/`. Hand this file to the `labview-caraya-unit-test` agent. Expected values were computed in Python with double precision, `x += (sp - x) * (1 - exp(-dt/tau))`.

Conventions:
- Every double comparison uses an absolute tolerance of **1e-6** unless the row says otherwise.
- Strings compare exactly and are case-sensitive.
- `SC(...)` is a Step Config with defaults `step_no 1, step_name "S", command_type "HOLD_PRESSURE", pressure_sp_bar 100, flow_sp_lpm 60, displacement_sp_mm 2.5, monitored_io "AI_Pressure_PT101", tolerance_bar 2, dwell_time_ms 1000, timeout_ms 5000, expected_result "PASS"`. Only the overridden fields are listed.
- `PF(p,f,d,ts)` is a Plant Feedback `pressure_bar, flow_lpm, displacement_mm, timestamp_ms`.
- Terminal labels come from spec §4. **Verified** against the built VI where marked [built]. The others are not built yet: check them with `lvai_vi_terminals` before writing the tests.

## 1. `Select Monitored Signal.vi` [built: Step Config, Plant Feedback -> measured, target, valid]

| id | Step Config | Plant Feedback | measured | target | valid |
|---|---|---|---|---|---|
| SMS-1 | SC() | PF(97.5, 11, 1.2, 0) | 97.5 | 100 | T |
| SMS-2 | SC(monitored_io "AI_Flow_FT102") | PF(97.5, 58.25, 1.2, 0) | 58.25 | 60 | T |
| SMS-3 | SC(monitored_io "AI_Displacement_LVDT103") | PF(97.5, 58.25, 2.4, 0) | 2.4 | 2.5 | T |
| SMS-4 | SC(monitored_io "AI_Temp_TT999") | PF(97.5, 58.25, 2.4, 0) | 0 | 0 | **F** |
| SMS-5 | SC(monitored_io "") | PF(1,2,3,0) | 0 | 0 | F |
| SMS-6 | SC(monitored_io "ai_pressure_pt101") | PF(1,2,3,0) | 0 | 0 | F (pins today's case-sensitive match; see README Q9) |

## 2. `Parse Sequence JSON.vi` [built: JSON string, error in -> Sequence File, error out]

| id | input | expected |
|---|---|---|
| PSJ-1 | contents of `configs/actual_vtu_sequence.json` | no error; `sequence_id` "VTU_ACTUAL_SEQUENCE_001"; `total_steps` 5; size(steps) 5; steps[0].step_name "Pre-fill & Prime"; steps[1].pressure_sp_bar 80; steps[2].dwell_time_ms 3000; steps[3].monitored_io "AI_Flow_FT102"; steps[3].tolerance_bar 2.5; steps[4].timeout_ms 5000; steps[4].expected_result "PASS" |
| PSJ-2 | `{"sequence_id":"EMPTY","description":"","total_steps":0,"steps":[]}` | error out status T, **code 5001**, source contains `sequence has no steps` |
| PSJ-3 | `{"sequence_id":"NOSTEPS","description":"x","total_steps":0}` (no `steps` key) | code **5001** (steps defaults to empty). If Unflatten instead raises its own missing-key error, record that code; spec only names 5001 for empty steps |
| PSJ-4 | `{` (malformed) | status T, code ≠ 0 and ≠ 5001 (Unflatten From JSON error) |
| PSJ-5 | valid one-step JSON, error in = [T, 42, "upstream"] | error out = [T, 42, "upstream"] (passes through, no 5001 on top) |
| PSJ-6 | one step with every field, extra unknown key `"comment":"x"` | no error; fields mapped (non-strict Unflatten) |

## 3. `Read Sequence File.vi` [not built: path, error in -> Sequence File, error out]

| id | input | expected |
|---|---|---|
| RSF-1 | `<project>\configs\actual_vtu_sequence.json` | same as PSJ-1 |
| RSF-2 | `<temp>\does_not_exist.json` | status T, code 7 (file not found) |
| RSF-3 | temp file holding PSJ-2 text | code 5001 |

## 4. `Plant First Order Step.vi` [built: current Plant Feedback, Plant Setpoints, dt s, now ms -> new Plant Feedback]

tau: pressure 0.8 s, flow 0.6 s, displacement 0.3 s. alpha = 1 - exp(-dt/tau). For dt 0.1: alpha_P = 0.117503097415, alpha_F = 0.153518275109, alpha_D = 0.283468689426.

| id | current PF | setpoints (P,F,D) | dt s | now ms | expected new PF |
|---|---|---|---|---|---|
| FOS-1 | (0,0,0,0) | (100,0,0) | 0.1 | 1000 | p **11.750309742**, f 0, d 0, ts 1000 |
| FOS-2 | (0,0,0,0) | (0,100,0) | 0.1 | 0 | f **15.351827511** |
| FOS-3 | (0,0,0,0) | (0,0,10) | 0.1 | 0 | d **2.834686894** |
| FOS-4 | (10,20,1,5) | (50,40,2) | 0.1 | 1234.5 | (**14.700123897**, **23.070365502**, **1.283468689**, 1234.5) |
| FOS-5 | (100,0,0,0) | (0,0,0) | 0.1 | 0 | p **88.249690258** |
| FOS-6 | (11.750309742,0,0,0), i.e. the output of FOS-1 fed back | (100,0,0) | 0.1 | 0 | p **22.119921693**, equal to one call with dt 0.2 |
| FOS-7 | apply 10 times from 0 | (100,0,0) | 0.1 | n/a | p **71.349520314** = 100(1-e^-1.25) |
| FOS-8 | (42,7,1.5,9) | (42,7,1.5) | 0.1 | 77 | unchanged values, ts 77 (steady state) |
| FOS-9 | (5,6,7,0) | (100,100,100) | 0 | 3 | unchanged values, ts 3 (dt 0 means alpha 0) |
| FOS-10 | (50,0,0,0) | (100,0,0) | 0.1 | 0 | p **55.875154871** |

## 5. `Evaluate Step.vi` [not built]

Inputs: Step Config, Plant Feedback, Step Phase in, step start ms, dwell start ms. Outputs: Step Phase out, dwell start ms out, done, passed, reason, measured, target.

Step SC() (P, target 100, tol 2, dwell 1000, timeout 5000). step start ms = 1000 in every row. The UE helpers it uses (offline export of `src/12_Utilities`) are both edge-inclusive: `UE_Within_Tolerance` is `In Range and Coerce` with `includeLow`/`includeHigh`, so `target-tol <= x <= target+tol`. `UE_Timeout_Reached` and `UE_Dwell_Reached` both use `elapsed >= threshold`.

| id | phase in | dwell start in | PF.pressure | PF.ts | phase out | dwell start out | done | passed | reason | measured | target |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EVS-1 settling, outside | Settling | 0 | 50 | 1500 | Settling | 0 (unchanged) | F | F | "" | 50 | 100 |
| EVS-2 lower edge enters dwell | Settling | 0 | **98.0** | 1500 | Dwell | **1500** | F | F | "" | 98 | 100 |
| EVS-3 upper edge enters dwell | Settling | 0 | **102.0** | 1500 | Dwell | 1500 | F | F | "" | 102 | 100 |
| EVS-4 just below lower edge | Settling | 0 | 97.999 | 1500 | Settling | 0 | F | F | "" | 97.999 | 100 |
| EVS-5 just above upper edge | Settling | 0 | 102.001 | 1500 | Settling | 0 | F | F | "" | | |
| EVS-6 dwell running | Dwell | 1500 | 99 | 2499 | Dwell | 1500 | F | F | "" | | |
| EVS-7 dwell complete, exact | Dwell | 1500 | 99 | **2500** | Complete | 1500 | **T** | **T** | "" (or empty-equivalent) | 99 | 100 |
| EVS-8 leaves tolerance in dwell | Dwell | 1500 | 97 | 2000 | **Settling** | (any, not asserted) | F | F | "" | 97 | |
| EVS-9 re-enter after EVS-8 (restart) | Settling | (from EVS-8) | 99 | 2100 | Dwell | **2100** | F | F | | | |
| EVS-10 old start would have passed | Dwell | 2100 | 99 | 3000 | Dwell | 2100 | **F** (only 900 ms since restart, although 1500 since the first entry) | F | | | |
| EVS-11 restarted dwell completes | Dwell | 2100 | 99 | 3100 | Complete | 2100 | T | T | | | |
| EVS-12 timeout while settling | Settling | 0 | 50 | **6000** (elapsed 5000 = timeout) | Complete | | T | F | **"Timeout"** | 50 | 100 |
| EVS-13 1 ms before timeout | Settling | 0 | 50 | 5999 | Settling | | F | F | "" | | |
| EVS-14 **timeout and dwell on the same sample** | Dwell | 5000 | 99 | 6000 (elapsed 5000 >= 5000 AND dwell 1000 >= 1000) | Complete | | T | **F** | **"Timeout"** (timeout has priority) | 99 | 100 |
| EVS-15 timeout while in dwell, in tolerance | Dwell | 5500 | 99 | 6000 | Complete | | T | F | "Timeout" | | |
| EVS-16 unknown IO | Settling | 0 | 99 | 1500 | Complete (recommended) | | **T** | **F** | **"Unknown monitored IO"** | 0 | 0 |
| EVS-17 flow channel, tol 2.5 | Settling, SC(monitored_io "AI_Flow_FT102", flow_sp_lpm 60, tolerance_bar 2.5), PF.flow 57.5 | 0 | | 1500 | Dwell | 1500 | F | F | | 57.5 | 60 |
| EVS-18 displacement channel | Settling, SC(monitored_io "AI_Displacement_LVDT103", displacement_sp_mm 2.5, tolerance_bar 0.1), PF.d 2.6 | 0 | | 1500 | Dwell | 1500 | F | F | | 2.6 | 2.5 |

Not fixed by the spec (README Q8): phase in `Idle` or `Complete`, and `dwell_time_ms` 0 (pass on the entering sample, or one sample later). EVS-2/3 assume the entering sample does **not** also complete a 1000 ms dwell. Settle these before writing the tests.

## 6. `Build Step Table.vi` [not built: Sequence File, Step Result array -> 2-D string array]

| id | input | expected |
|---|---|---|
| BST-1 | actual sequence + 5 NOT RUN results | 5 rows x 12 columns; row 0 col 0 "1", col 1 "Pre-fill & Prime", col 2 "RAMP_PRESSURE", col 3 "AI_Pressure_PT101", col 8 "NOT RUN"; row 3 col 3 "AI_Flow_FT102" |
| BST-2 | same, results[1] = PASS, measured 79.7197, duration 4300 | row 1 col 8 "PASS"; col 9 and col 10 non-empty. Number format is not fixed by spec 4 (README Q10), so assert exact text only after the format is decided |
| BST-3 | sequence with 0 steps, empty results | empty 2-D array (0 rows) |
| BST-4 | 5 steps, results array of 3 (length mismatch) | 5 rows, missing results shown as empty/"NOT RUN". Behaviour to be decided (README Q10) |

Column order (spec): Step, Name, Command, Monitored IO, Target, Tol, Dwell ms, Timeout ms, Result, Measured, Duration ms, Reason.

## 7. `Write Results CSV.vi` [not built: results folder path, sequence_id, Step Result array, overall verdict, error in -> file path, error out]

| id | input | expected |
|---|---|---|
| WRC-1 | folder `<temp>\caraya_results_<random>` (does **not** exist), id "VTU_ACTUAL_SEQUENCE_001", 5 PASS results, verdict "PASS" | folder created; file exists; name matches `^VTU_ACTUAL_SEQUENCE_001_\d{8}_\d{6}\.csv$`; file text contains "PASS" and all 5 step names; no error |
| WRC-2 | existing folder | no error, new file |
| WRC-3 | error in = [T, 99, "x"] | no file written, error out = input |
| WRC-4 | folder on an invalid drive (`Q:\nope`) | status T (any file I/O code), no crash |

Clean up the temp folders after each test.

## 8. End-to-end acceptance: `configs/actual_vtu_sequence.json` through the real actor tree

Run `Launch Sequence Executor.vi`, press Load (empty Config Path means the default file), then Start, and wait.

Simulated expectation: a Python model of plant plus executor, 100 ms ticks, setpoints applied from the first tick after Begin Step, edge-inclusive tolerance, `>=` timers.

| step | name | monitored | settle ms | expected duration ms | timeout ms | margin ms | measured at PASS |
|---|---|---|---|---|---|---|---|
| 1 | Pre-fill & Prime | P -> 20 ±2 | 1900 | 2900 | 5000 | 2100 | ≈19.47 |
| 2 | Pressure Ramp | P -> 80 ±2 | 2800 | 4300 | 8000 | 3700 | ≈79.72 |
| 3 | Operating Point Dwell | P -> 100 ±2 | 1900 | 4900 | 10000 | 5100 | ≈99.96 |
| 4 | Flow Check & Stroke | F -> 60 ±2.5 | 1100 | 3100 | 8000 | 4900 | ≈59.91 |
| 5 | Depressurize & Safe | P -> 0 ±1.5 | 3400 | 4400 | 5000 | **600** (tightest) | ≈0.41 |

Total ≈ 19.6 s. With one extra tick of message latency per step, durations grow by about 100 ms. Step 5 still has about 500 ms of margin.

Checklist:
- [ ] After Load: Status `LOADED VTU_ACTUAL_SEQUENCE_001 (5 steps)`; table 5 rows, all `NOT RUN`.
- [ ] Load with a bad path: Status starts `LOAD ERROR:`, the actor is still alive (a following Load with a good path works).
- [ ] Start before Load: Status `START REFUSED - load a sequence first`, no error, the actor is still alive.
- [ ] During the run: Status `RUNNING`; Current Step goes 1→5; the running row shows `RUNNING`; the numerics and the chart update about every 100 ms.
- [ ] Each step goes `PASS`, with duration within ±300 ms of the table above and below its timeout_ms.
- [ ] At the end: Verdict `PASS`; Status `COMPLETE: PASS - report <path>`; one new file `results\VTU_ACTUAL_SEQUENCE_001_YYYYMMDD_HHMMSS.csv` holding 5 rows, all PASS.
- [ ] Plant setpoints back at (0,0,0) after completion (pressure decays toward 0).
- [ ] Stop Sequence during step 2: step 2 `ABORTED`, reason `STOPPED BY OPERATOR`, steps 3-5 `NOT RUN`, Verdict `ABORTED`, plant decays to 0, a new Start runs again from step 1.
- [ ] E-Stop during step 3: same, with reason `E-STOP`. Measure the time from click to Status change (should be < 200 ms even with feedback traffic queued, because it goes at High priority).
- [ ] Start while running: `START REFUSED - sequence already running`, the run continues.
- [ ] Exit during a run, and separately the window close (X): the VI returns within 5 s, `Stopped cleanly` T, `error out` no error, no VIs left running (Sim Plant stopped by auto-stop, tick stopped).
- [ ] Run twice in a row in the same LabVIEW session: second launch works (notifier released, nothing left in memory).
