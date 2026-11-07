# Complete AIXML VI Catalog — 28 Reusable Kernel VIs

> **Status:** Generated AIXML and offline graph simulation verified; no LabVIEW native validation. The following are design and test contracts, not certification.

## 1. Catalog conventions

- AIXML source folder: `aixml/4815` or `aixml/4833` (use **one**, according to the actual target connector pane).
- Inputs and outputs use scalar LabVIEW types: `double`, `int32`, `bool`. Engineering units appear in names; they are **not** enforced by type alone.
- All inputs are connector-pane assigned and required; outputs are assigned to the right pane positions and recommended.
- Pure VIs never communicate directly with an instrument and do not set actuator outputs.
- Each VI is intended to be called synchronously by the relevant service in a bounded time.
- The native LabVIEW acceptance tests are still mandatory.

## 2. Inventory

| VI | Service | Requirement(s) | Nodes |
|---|---|---|---:|
| `UE_Relative_Target.vi` | vtu | SRS-F-020 | 1 |
| `UE_Measured_Displacement.vi` | measurement | SRS-F-020 | 1 |
| `UE_Elapsed_Ms.vi` | timing | SRS-F-006 | 1 |
| `UE_Ms_To_Seconds.vi` | timing | SRS-F-006 | 1 |
| `UE_Inclusive_Range.vi` | condition | SRS-F-005 | 1 |
| `UE_Clamp_To_Limits.vi` | condition | SRS-F-021 | 1 |
| `UE_Within_Tolerance.vi` | condition | SRS-F-005 | 3 |
| `UE_Target_Error.vi` | measurement | SRS-F-005 | 1 |
| `UE_Timeout_Reached.vi` | timing | SRS-F-006 | 1 |
| `UE_Stabilization_Reached.vi` | timing | SRS-F-006 | 1 |
| `UE_Dwell_Reached.vi` | timing | SRS-F-006 | 1 |
| `UE_Retry_Allowed.vi` | cycle | SRS-F-010 | 1 |
| `UE_Cycles_Done.vi` | cycle | SRS-F-010 | 1 |
| `UE_Stop_Requested.vi` | supervisor | SRS-F-015 | 1 |
| `UE_Select_Setpoint.vi` | profile | SRS-F-019 | 1 |
| `UE_TriState_Condition.vi` | condition | SRS-F-022 | 2 |
| `UE_Command_Permitted.vi` | bridge | SRS-F-021 | 3 |
| `UE_Capture_Acceptable.vi` | report | SRS-F-008 | 2 |
| `UE_Relative_Target_Check.vi` | vtu | SRS-F-020, SRS-F-021 | 2 |
| `UE_Sweep_Target.vi` | profile | SRS-F-019 | 2 |
| `UE_Hydraulic_Power_kW.vi` | vtu | SRS-F-019 | 2 |
| `UE_Percent_Drop.vi` | measurement | SRS-F-008 | 6 |
| `UE_Load_Fraction.vi` | vtu | SRS-F-008 | 1 |
| `UE_Operating_Point_Ready.vi` | profile | SRS-F-019 | 2 |
| `UE_Can_Advance_Step.vi` | executor | SRS-F-005, SRS-F-022 | 3 |
| `UE_Run_Id_Matches.vi` | bridge | SRS-F-024 | 1 |
| `UE_Feedback_Freshness.vi` | parameter | SRS-F-022 | 4 |
| `UE_Cycle_Event_Duration.vi` | vtu | SRS-F-006 | 1 |

## 3. Per-VI functional design


### 1. `UE_Relative_Target.vi`

**Purpose:** Calculate PC lever target from measured servo position and configurable relative displacement

**Requirement IDs:** SRS-F-020  
**Module / caller:** vtu / Executor / VTU accuracy-sensitivity action

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `reference_mm` | `double` |
| Input | `offset_mm` | `double` |
| Output | `target_mm` | `double` |

**Block diagram construction:** Add reference_mm and offset_mm.

**Functions / nodes in data-flow order:**

1. `Add` — inputs `x:101.value,y:102.value`; outputs `x+y:103.x+y`.

**Preconditions / failure handling:** The servo feedback represents the calibrated PC-lever reference. Hitch-point travel is a separate measured result.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 100, 2 | 102 |
| 150, -20 | 130 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 2. `UE_Measured_Displacement.vi`

**Purpose:** Compute signed displacement between two valid position samples

**Requirement IDs:** SRS-F-020  
**Module / caller:** measurement / VTU hitch response and height measurements

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `final_mm` | `double` |
| Input | `initial_mm` | `double` |
| Output | `delta_mm` | `double` |

**Block diagram construction:** Subtract initial_mm from final_mm. Preserve sign.

**Functions / nodes in data-flow order:**

1. `Subtract` — inputs `x:101.value,y:102.value`; outputs `x-y:103.x-y`.

**Preconditions / failure handling:** Negative output means travel opposite the positive reference direction.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 302, 300 | 2 |
| 289, 300 | -11 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 3. `UE_Elapsed_Ms.vi`

**Purpose:** Compute elapsed monotonic milliseconds, caller guarantees now not earlier than start

**Requirement IDs:** SRS-F-006  
**Module / caller:** timing / Step timer service

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `now_ms` | `double` |
| Input | `start_ms` | `double` |
| Output | `elapsed_ms` | `double` |

**Block diagram construction:** Subtract start_ms from now_ms.

**Functions / nodes in data-flow order:**

1. `Subtract` — inputs `x:101.value,y:102.value`; outputs `x-y:103.x-y`.

**Preconditions / failure handling:** Use timestamps from the same monotonic clock, including wrap/reboot handling upstream.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1200, 1000 | 200 |
| 600, 600 | 0 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 4. `UE_Ms_To_Seconds.vi`

**Purpose:** Convert milliseconds to seconds

**Requirement IDs:** SRS-F-006  
**Module / caller:** timing / Timer/report formatter

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `milliseconds` | `double` |
| Output | `seconds` | `double` |

**Block diagram construction:** Divide milliseconds by a constant 1000.

**Functions / nodes in data-flow order:**

1. `Divide` — inputs `x:101.value,y:102.value`; outputs `x/y:103.x/y`.

**Preconditions / failure handling:** Used for report units; it does not create timing precision.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1500 | 1.5 |
| 0 | 0 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 5. `UE_Inclusive_Range.vi`

**Purpose:** Evaluate a closed engineering range with both boundaries included

**Requirement IDs:** SRS-F-005  
**Module / caller:** condition / Condition Evaluator

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `value` | `double` |
| Input | `minimum` | `double` |
| Input | `maximum` | `double` |
| Output | `in_range` | `bool` |

**Block diagram construction:** Use In Range and Coerce with lower/upper inclusion enabled; report the boolean output.

**Functions / nodes in data-flow order:**

1. `In Range and Coerce` — inputs `upper limit:103.value,x:101.value,lower limit:102.value`; outputs `coerced(x):104.coerced(x),In Range?:104.In Range?`; lower and upper inclusive.

**Preconditions / failure handling:** The calling Parameter Registry must reject invalid/NaN/stale feedback.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 10, 10, 20 | True |
| 20, 10, 20 | True |
| 20.1, 10, 20 | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 6. `UE_Clamp_To_Limits.vi`

**Purpose:** Coerce numeric target into validated bounds and report whether original target was inside

**Requirement IDs:** SRS-F-021  
**Module / caller:** condition / Configuration preview / setpoint planner

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `value` | `double` |
| Input | `minimum` | `double` |
| Input | `maximum` | `double` |
| Output | `clamped` | `double` |
| Output | `original_in_range` | `bool` |

**Block diagram construction:** Use In Range and Coerce; expose both coerced value and membership flag.

**Functions / nodes in data-flow order:**

1. `In Range and Coerce` — inputs `upper limit:103.value,x:101.value,lower limit:102.value`; outputs `coerced(x):104.coerced(x),In Range?:104.In Range?`; lower and upper inclusive.

**Preconditions / failure handling:** Do not silently substitute a clamped actuator target; Bridge should reject invalid motion demands unless policy explicitly authorizes a corrected command.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 6, 0, 5 | 5, False |
| 0, 0, 5 | 0, True |
| -1, 0, 5 | 0, False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 7. `UE_Within_Tolerance.vi`

**Purpose:** Check actual within target plus or minus configured nonnegative tolerance

**Requirement IDs:** SRS-F-005  
**Module / caller:** condition / Step condition evaluator

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `actual` | `double` |
| Input | `target` | `double` |
| Input | `tolerance` | `double` |
| Output | `within_tolerance` | `bool` |

**Block diagram construction:** Compute lower = target - tolerance and upper = target + tolerance. Evaluate actual in inclusive range.

**Functions / nodes in data-flow order:**

1. `Subtract` — inputs `x:102.value,y:103.value`; outputs `x-y:104.x-y`.
2. `Add` — inputs `x:102.value,y:103.value`; outputs `x+y:105.x+y`.
3. `In Range and Coerce` — inputs `upper limit:105.x+y,x:101.value,lower limit:104.x-y`; outputs `coerced(x):106.coerced(x),In Range?:106.In Range?`; lower and upper inclusive.

**Preconditions / failure handling:** Tolerance must be nonnegative and specified in same engineering unit as target/actual.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 100, 100, 1 | True |
| 101, 100, 1 | True |
| 101.01, 100, 1 | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 8. `UE_Target_Error.vi`

**Purpose:** Compute signed target minus feedback error

**Requirement IDs:** SRS-F-005  
**Module / caller:** measurement / Pressure/flow/servo diagnostics

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `target` | `double` |
| Input | `actual` | `double` |
| Output | `error` | `double` |

**Block diagram construction:** Subtract actual feedback from commanded target.

**Functions / nodes in data-flow order:**

1. `Subtract` — inputs `x:101.value,y:102.value`; outputs `x-y:103.x-y`.

**Preconditions / failure handling:** The result is signed; numerical error alone does not establish controller health.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 100, 96 | 4 |
| 10, 12 | -2 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 9. `UE_Timeout_Reached.vi`

**Purpose:** True when elapsed duration equals or exceeds timeout

**Requirement IDs:** SRS-F-006  
**Module / caller:** timing / Step timeout checker

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `elapsed_ms` | `double` |
| Input | `threshold_ms` | `double` |
| Output | `reached` | `bool` |

**Block diagram construction:** Compare elapsed_ms greater than or equal to threshold_ms.

**Functions / nodes in data-flow order:**

1. `Greater Or Equal?` — inputs `x:101.value,y:102.value`; outputs `x >= y?:103.x >= y?`.

**Preconditions / failure handling:** Never reset the timer implicitly here; the scheduler owns timer lifecycle and retry policy.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1000, 1000 | True |
| 999, 1000 | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 10. `UE_Stabilization_Reached.vi`

**Purpose:** True when continuous-in-range duration equals or exceeds stabilization time

**Requirement IDs:** SRS-F-006  
**Module / caller:** timing / Step stabilization checker

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `elapsed_ms` | `double` |
| Input | `threshold_ms` | `double` |
| Output | `reached` | `bool` |

**Block diagram construction:** Compare continuous-in-range elapsed_ms greater than or equal to required_ms.

**Functions / nodes in data-flow order:**

1. `Greater Or Equal?` — inputs `x:101.value,y:102.value`; outputs `x >= y?:103.x >= y?`.

**Preconditions / failure handling:** Any FALSE/UNKNOWN in the monitored conditions resets the continuous-stability interval upstream.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1000, 1000 | True |
| 0, 1000 | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 11. `UE_Dwell_Reached.vi`

**Purpose:** True when time spent in dwell equals or exceeds configured duration

**Requirement IDs:** SRS-F-006  
**Module / caller:** timing / Operating point dwell checker

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `elapsed_ms` | `double` |
| Input | `threshold_ms` | `double` |
| Output | `reached` | `bool` |

**Block diagram construction:** Compare dwell elapsed_ms greater than or equal to required dwell threshold.

**Functions / nodes in data-flow order:**

1. `Greater Or Equal?` — inputs `x:101.value,y:102.value`; outputs `x >= y?:103.x >= y?`.

**Preconditions / failure handling:** Capture may overlap dwell and must be independently coordinated.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 400, 500 | False |
| 500, 500 | True |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 12. `UE_Retry_Allowed.vi`

**Purpose:** True if retry attempts used is lower than configured maximum

**Requirement IDs:** SRS-F-010  
**Module / caller:** cycle / Retry policy evaluator

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `attempts_used` | `int32` |
| Input | `max_attempts` | `int32` |
| Output | `allowed` | `bool` |

**Block diagram construction:** Compare attempts_used less than max_attempts.

**Functions / nodes in data-flow order:**

1. `Less?` — inputs `x:101.value,y:102.value`; outputs `x < y?:103.x < y?`.

**Preconditions / failure handling:** Retries must not change successful completion counters; no automatic retry of unsafe movements.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1, 3 | True |
| 3, 3 | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 13. `UE_Cycles_Done.vi`

**Purpose:** Check whether completed cycles meet requested number

**Requirement IDs:** SRS-F-010  
**Module / caller:** cycle / Group/cycle scheduler

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `completed` | `int32` |
| Input | `requested` | `int32` |
| Output | `done` | `bool` |

**Block diagram construction:** Compare completed >= requested.

**Functions / nodes in data-flow order:**

1. `Greater Or Equal?` — inputs `x:101.value,y:102.value`; outputs `x >= y?:103.x >= y?`.

**Preconditions / failure handling:** The Cycle Manager is responsible for completed/started/failed identities and durable checkpointing.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 5, 5 | True |
| 4, 5 | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 14. `UE_Stop_Requested.vi`

**Purpose:** Combine operator stop request and global fault request

**Requirement IDs:** SRS-F-015  
**Module / caller:** supervisor / Supervisor state transition gate

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `operator_stop` | `bool` |
| Input | `global_fault` | `bool` |
| Output | `must_stop` | `bool` |

**Block diagram construction:** OR operator_stop and global_fault.

**Functions / nodes in data-flow order:**

1. `Or` — inputs `x:101.value,y:102.value`; outputs `x .or. y?:103.x .or. y?`.

**Preconditions / failure handling:** This is a status helper. Emergency protection must bypass actor/queue latency.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| False, False | False |
| True, False | True |
| False, True | True |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 15. `UE_Select_Setpoint.vi`

**Purpose:** Select default or override target according to a validated mode flag

**Requirement IDs:** SRS-F-019  
**Module / caller:** profile / Profile value resolver

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `override_selected` | `bool` |
| Input | `override_target` | `double` |
| Input | `default_target` | `double` |
| Output | `selected_target` | `double` |

**Block diagram construction:** Select override_target if override_selected else default_target.

**Functions / nodes in data-flow order:**

1. `Select` — inputs `t:102.value,s:101.value,f:103.value`; outputs `s? t\3Af:104.s? t\3Af`.

**Preconditions / failure handling:** Override values need explicit approval, limit validation, versioning and traceability.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| True, 150, 100 | 150 |
| False, 150, 100 | 100 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 16. `UE_TriState_Condition.vi`

**Purpose:** Evaluate result as -1 UNKNOWN, 0 FALSE or 1 TRUE; invalid sample never passes

**Requirement IDs:** SRS-F-022  
**Module / caller:** condition / Condition Engine state mapper

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `sample_valid` | `bool` |
| Input | `condition_met` | `bool` |
| Output | `state_code` | `int32` |

**Block diagram construction:** Select 1 for met and 0 for unmet; then override result with -1 when sample_valid is false.

**Functions / nodes in data-flow order:**

1. `Select` — inputs `t:103.value,s:102.value,f:104.value`; outputs `s? t\3Af:105.s? t\3Af`.
2. `Select` — inputs `t:105.s? t\3Af,s:101.value,f:106.value`; outputs `s? t\3Af:107.s? t\3Af`.

**Preconditions / failure handling:** Code -1=UNKNOWN, 0=FALSE, 1=TRUE. UNKNOWN must not be accepted as success.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| False, True | -1 |
| True, False | 0 |
| True, True | 1 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 17. `UE_Command_Permitted.vi`

**Purpose:** Combine mode, resource ownership, interlock and fault checks for normal command authorization

**Requirement IDs:** SRS-F-021  
**Module / caller:** bridge / Bridge preauthorization helper

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `mode_authorized` | `bool` |
| Input | `resource_owned` | `bool` |
| Input | `interlocks_satisfied` | `bool` |
| Input | `no_fault` | `bool` |
| Output | `permitted` | `bool` |

**Block diagram construction:** Conjoin mode_authorized, resource_owned, interlocks_satisfied and no_fault using chained Select nodes with FALSE constants.

**Functions / nodes in data-flow order:**

1. `Select` — inputs `t:102.value,s:101.value,f:105.value`; outputs `s? t\3Af:106.s? t\3Af`.
2. `Select` — inputs `t:103.value,s:106.s? t\3Af,f:107.value`; outputs `s? t\3Af:108.s? t\3Af`.
3. `Select` — inputs `t:104.value,s:108.s? t\3Af,f:109.value`; outputs `s? t\3Af:110.s? t\3Af`.

**Preconditions / failure handling:** Bridge must still validate owner token, lease epoch, command ID, resource limits and controller readiness.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| True, True, True, True | True |
| True, False, True, True | False |
| True, True, True, False | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 18. `UE_Capture_Acceptable.vi`

**Purpose:** Accept a completed capture only when samples exist, feedback is valid and buffer succeeded

**Requirement IDs:** SRS-F-008  
**Module / caller:** report / Report Capture result gate

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `samples_present` | `bool` |
| Input | `feedback_valid` | `bool` |
| Input | `buffer_ok` | `bool` |
| Output | `acceptable` | `bool` |

**Block diagram construction:** Conjoin samples_present, feedback_valid and buffer_ok.

**Functions / nodes in data-flow order:**

1. `Select` — inputs `t:102.value,s:101.value,f:104.value`; outputs `s? t\3Af:105.s? t\3Af`.
2. `Select` — inputs `t:103.value,s:105.s? t\3Af,f:106.value`; outputs `s? t\3Af:107.s? t\3Af`.

**Preconditions / failure handling:** Capture queue overflow or missing data must be visible to test evaluation.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| True, True, True | True |
| True, False, True | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 19. `UE_Relative_Target_Check.vi`

**Purpose:** Resolve relative servo motion then check authorized physical travel range

**Requirement IDs:** SRS-F-020, SRS-F-021  
**Module / caller:** vtu / VTU servo command preflight

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `servo_reference_mm` | `double` |
| Input | `delta_mm` | `double` |
| Input | `min_target_mm` | `double` |
| Input | `max_target_mm` | `double` |
| Output | `requested_target_mm` | `double` |
| Output | `within_limits` | `bool` |

**Block diagram construction:** Compute requested target from servo feedback plus delta; independently test target against inclusive configured travel bounds.

**Functions / nodes in data-flow order:**

1. `Add` — inputs `x:101.value,y:102.value`; outputs `x+y:105.x+y`.
2. `In Range and Coerce` — inputs `upper limit:104.value,x:105.x+y,lower limit:103.value`; outputs `coerced(x):106.coerced(x),In Range?:106.In Range?`; lower and upper inclusive.

**Preconditions / failure handling:** Return original requested target even if out of bounds. The action must reject it instead of clamping motion.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 50, 2, 0, 100 | 52, True |
| 95, 10, 0, 100 | 105, False |
| 0, 0, 0, 100 | 0, True |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 20. `UE_Sweep_Target.vi`

**Purpose:** Compute start plus index times increment for a validated linear sweep

**Requirement IDs:** SRS-F-019  
**Module / caller:** profile / Pressure/flow sweep generator

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `start_value` | `double` |
| Input | `step_size` | `double` |
| Input | `point_index` | `double` |
| Output | `target` | `double` |

**Block diagram construction:** Multiply step_size by point_index then add start_value.

**Functions / nodes in data-flow order:**

1. `Multiply` — inputs `x:103.value,y:102.value`; outputs `x*y:104.x*y`.
2. `Add` — inputs `x:101.value,y:104.x*y`; outputs `x+y:105.x+y`.

**Preconditions / failure handling:** Operating-point count, step direction and controller compatibility are configuration concerns.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 10, 5, 3 | 25 |
| 100, -10, 2 | 80 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 21. `UE_Hydraulic_Power_kW.vi`

**Purpose:** Calculate ideal hydraulic power from pressure bar and volumetric flow L/min

**Requirement IDs:** SRS-F-019  
**Module / caller:** vtu / Hydraulic Power test measurement

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `pressure_bar` | `double` |
| Input | `flow_lpm` | `double` |
| Output | `hydraulic_kw` | `double` |

**Block diagram construction:** Multiply pressure_bar by measured flow_lpm; divide result by 600.

**Functions / nodes in data-flow order:**

1. `Multiply` — inputs `x:101.value,y:102.value`; outputs `x*y:103.x*y`.
2. `Divide` — inputs `x:103.x*y,y:104.value`; outputs `x/y:105.x/y`.

**Preconditions / failure handling:** Formula is ideal hydraulic power in kW (differential bar * L/min / 600); not electrical input or shaft output power.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 100, 60 | 10 |
| 200, 0 | 0 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 22. `UE_Percent_Drop.vi`

**Purpose:** Compute 100 times (initial minus final) divided by initial only for initial > 0

**Requirement IDs:** SRS-F-008  
**Module / caller:** measurement / Lift maintenance calculation / reports

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `initial` | `double` |
| Input | `final` | `double` |
| Output | `percent_drop` | `double` |
| Output | `valid` | `bool` |

**Block diagram construction:** Check initial > 0; choose safe divisor (initial or 1); calculate ((initial-final)/divisor)*100; zero result and report invalid if initial is not positive.

**Functions / nodes in data-flow order:**

1. `Greater?` — inputs `x:101.value,y:103.value`; outputs `x > y?:104.x > y?`.
2. `Select` — inputs `t:101.value,s:104.x > y?,f:105.value`; outputs `s? t\3Af:106.s? t\3Af`.
3. `Subtract` — inputs `x:101.value,y:102.value`; outputs `x-y:107.x-y`.
4. `Divide` — inputs `x:107.x-y,y:106.s? t\3Af`; outputs `x/y:108.x/y`.
5. `Multiply` — inputs `x:108.x/y,y:109.value`; outputs `x*y:110.x*y`.
6. `Select` — inputs `t:110.x*y,s:104.x > y?,f:111.value`; outputs `s? t\3Af:112.s? t\3Af`.

**Preconditions / failure handling:** The boolean valid flag must be checked before using percent result. Negative drop denotes an increase.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 100, 90 | 10, True |
| 0, 5 | 0, False |
| 20, 22 | -10, True |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 23. `UE_Load_Fraction.vi`

**Purpose:** Calculate a configured fraction of previously measured reference load

**Requirement IDs:** SRS-F-008  
**Module / caller:** vtu / Maintenance-of-lift test preparation

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `reference_load_N` | `double` |
| Input | `fraction` | `double` |
| Output | `commanded_load_N` | `double` |

**Block diagram construction:** Multiply reference_load_N by configured fraction.

**Functions / nodes in data-flow order:**

1. `Multiply` — inputs `x:101.value,y:102.value`; outputs `x*y:103.x*y`.

**Preconditions / failure handling:** Example 90% load is represented as 0.90, not 90; source reference must have valid capture status.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1000, 0.9 | 900 |
| 100, 0 | 0 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 24. `UE_Operating_Point_Ready.vi`

**Purpose:** Combine pressure, flow and mode validity for a combined VTU point

**Requirement IDs:** SRS-F-019  
**Module / caller:** profile / VTU sweep condition group

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `pressure_achieved` | `bool` |
| Input | `flow_achieved` | `bool` |
| Input | `mode_valid` | `bool` |
| Output | `ready` | `bool` |

**Block diagram construction:** Conjoin pressure_achieved, flow_achieved and mode_valid.

**Functions / nodes in data-flow order:**

1. `Select` — inputs `t:102.value,s:101.value,f:104.value`; outputs `s? t\3Af:105.s? t\3Af`.
2. `Select` — inputs `t:103.value,s:105.s? t\3Af,f:106.value`; outputs `s? t\3Af:107.s? t\3Af`.

**Preconditions / failure handling:** Actual readiness also requires data quality, controller availability and configured per-point behavior.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| True, True, True | True |
| True, False, True | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 25. `UE_Can_Advance_Step.vi`

**Purpose:** Combine signal quality, required feedback, stabilization and no-fault gate

**Requirement IDs:** SRS-F-005, SRS-F-022  
**Module / caller:** executor / Executor step advancement guard

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `quality_valid` | `bool` |
| Input | `feedback_condition` | `bool` |
| Input | `stabilized` | `bool` |
| Input | `no_fault` | `bool` |
| Output | `advance` | `bool` |

**Block diagram construction:** Conjoin quality_valid, feedback_condition, stabilized and no_fault.

**Functions / nodes in data-flow order:**

1. `Select` — inputs `t:102.value,s:101.value,f:105.value`; outputs `s? t\3Af:106.s? t\3Af`.
2. `Select` — inputs `t:103.value,s:106.s? t\3Af,f:107.value`; outputs `s? t\3Af:108.s? t\3Af`.
3. `Select` — inputs `t:104.value,s:108.s? t\3Af,f:109.value`; outputs `s? t\3Af:110.s? t\3Af`.

**Preconditions / failure handling:** Timeout, dwell and command applied ACK are separate scheduler prerequisites.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| True, True, True, True | True |
| False, True, True, True | False |
| True, True, False, True | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 26. `UE_Run_Id_Matches.vi`

**Purpose:** Reject a stale command or result whose integer demonstration run identifier differs

**Requirement IDs:** SRS-F-024  
**Module / caller:** bridge / Bridge/Logger stale event filter

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `incoming_run_id` | `int32` |
| Input | `active_run_id` | `int32` |
| Output | `same_run` | `bool` |

**Block diagram construction:** Compare incoming_run_id and active_run_id for equality.

**Functions / nodes in data-flow order:**

1. `Equal?` — inputs `x:101.value,y:102.value`; outputs `x = y?:103.x = y?`.

**Preconditions / failure handling:** Integer IDs are demonstration only; implement a collision-resistant run/sequence identity in production.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 99, 99 | True |
| 98, 99 | False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 27. `UE_Feedback_Freshness.vi`

**Purpose:** Measure feedback age using monotonic clock and check nonnegative age not exceeding maximum

**Requirement IDs:** SRS-F-022  
**Module / caller:** parameter / Parameter Registry freshness computation

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `now_ms` | `double` |
| Input | `sample_ms` | `double` |
| Input | `max_age_ms` | `double` |
| Output | `age_ms` | `double` |
| Output | `fresh` | `bool` |

**Block diagram construction:** Compute age = now_ms - sample_ms. Check age >= 0 and age in [0, max_age_ms]. Return age and fresh flag.

**Functions / nodes in data-flow order:**

1. `Subtract` — inputs `x:101.value,y:102.value`; outputs `x-y:104.x-y`.
2. `Greater Or Equal?` — inputs `x:104.x-y,y:105.value`; outputs `x >= y?:106.x >= y?`.
3. `In Range and Coerce` — inputs `upper limit:103.value,x:104.x-y,lower limit:107.value`; outputs `coerced(x):108.coerced(x),In Range?:108.In Range?`; lower and upper inclusive.
4. `Select` — inputs `t:108.In Range?,s:106.x >= y?,f:109.value`; outputs `s? t\3Af:110.s? t\3Af`.

**Preconditions / failure handling:** Caller must verify sensor quality and common monotonic clock. Host time cannot be subtracted directly from RT ticks.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1000, 900, 100 | 100, True |
| 1000, 899, 100 | 101, False |
| 1000, 1001, 100 | -1, False |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


### 28. `UE_Cycle_Event_Duration.vi`

**Purpose:** Compute feedback-event duration in milliseconds from a shared monotonic clock

**Requirement IDs:** SRS-F-006  
**Module / caller:** vtu / TPL lift/lower cycle time measurement

| Connector | Name | LabVIEW type |
|---|---|---|
| Input | `end_ms` | `double` |
| Input | `start_ms` | `double` |
| Output | `duration_ms` | `double` |

**Block diagram construction:** Subtract event start tick from event end tick.

**Functions / nodes in data-flow order:**

1. `Subtract` — inputs `x:101.value,y:102.value`; outputs `x-y:103.x-y`.

**Preconditions / failure handling:** Event timestamp capture and direction qualification occur outside the helper.

**Offline test vectors:**

| Inputs in connector order | Expected outputs in connector order |
|---|---|
| 1050, 1000 | 50 |
| 1000, 1000 | 0 |

**Integration acceptance:** `lvai_check_aixml` pass; `lvai_validate_aixml` pass; native VI executable; connector pane verified; test vectors pass using the real LabVIEW runtime.


## 4. Cross-VI integration patterns

### 4.1 VTU Accuracy and Sensitivity

1. Servo feedback is captured as reference; `UE_Relative_Target_Check` resolves a relative PC lever command.
2. Reject `within_limits=false` before Bridge command submission.
3. The physical Servo controller executes motion independently.
4. Capture actual initial/final hitch heights and use `UE_Measured_Displacement`.
5. Use the test-specific procedure/criteria to calculate result; a 2 mm command is an **example** not a fixed value.

### 4.2 VTU Pressure and Flow Sweep

1. `UE_Sweep_Target` computes one requested operating point; the Host may configure pressure-only/flow-only/combined sweeps.
2. The Bridge validates the setpoint and grants command authority to RT controller blocks.
3. The Condition Engine checks `UE_Within_Tolerance`, `UE_Feedback_Freshness`, `UE_TriState_Condition` and `UE_Operating_Point_Ready`.
4. `UE_Stabilization_Reached` and `UE_Dwell_Reached` gate progression.
5. `UE_Hydraulic_Power_kW` calculates a **measured** hydraulic estimate where applicable.
6. Faults and invalid feedback preempt via supervisor and independent RT protection.

### 4.3 Lift maintenance

1. Retrieve valid previously measured reference load and call `UE_Load_Fraction` with fractional target such as 0.90.
2. Report initial and final hitch measurements with signed displacement.
3. Optionally calculate percentage drop using `UE_Percent_Drop` and check its `valid` indicator.
4. A scheduler handles 30-minute holds and periodic captures; no loop or timer service is authored in AIXML here.

