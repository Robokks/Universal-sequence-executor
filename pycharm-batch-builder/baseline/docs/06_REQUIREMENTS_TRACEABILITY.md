# Requirement-to-VI Traceability

**Baseline:** SRS v0.2. The AIXML package addresses **only selected portions** of the requirements. It is not a complete SRS implementation.

| SRS ID | AIXML kernel implementation(s) | Status |
|---|---|---|
| `SRS-F-005` | `UE_Inclusive_Range`, `UE_Within_Tolerance`, `UE_Target_Error`, `UE_Can_Advance_Step` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-006` | `UE_Elapsed_Ms`, `UE_Ms_To_Seconds`, `UE_Timeout_Reached`, `UE_Stabilization_Reached`, `UE_Dwell_Reached`, `UE_Cycle_Event_Duration` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-008` | `UE_Capture_Acceptable`, `UE_Percent_Drop`, `UE_Load_Fraction` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-010` | `UE_Retry_Allowed`, `UE_Cycles_Done` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-015` | `UE_Stop_Requested` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-019` | `UE_Select_Setpoint`, `UE_Sweep_Target`, `UE_Hydraulic_Power_kW`, `UE_Operating_Point_Ready` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-020` | `UE_Relative_Target`, `UE_Measured_Displacement`, `UE_Relative_Target_Check` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-021` | `UE_Clamp_To_Limits`, `UE_Command_Permitted`, `UE_Relative_Target_Check` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-022` | `UE_TriState_Condition`, `UE_Can_Advance_Step`, `UE_Feedback_Freshness` | Offline-only reusable helpers; full requirement not yet satisfied |
| `SRS-F-024` | `UE_Run_Id_Matches` | Offline-only reusable helpers; full requirement not yet satisfied |

## 2. Major requirements NOT implemented by these AIXML files

- Rig/test/group/step authoring and versioned configuration validation.
- Nested sequential/parallel schedule execution, joins, resource lock manager and checkpoints.
- Full Host/cRIO transport, manual/auto mode selection, Host disconnect watchdog.
- Operator popup UI, ACK timers and network transport.
- Real Bridge command dispatch, command ID, authorizer token, lease/epoch, device limit enforcement.
- Registered plugin lifecycle, Actor Framework class structure or QMH service loops.
- Independent RT fault supervision and safety system.
- Report Capture VI including buffering, averaging, periodic snapshots and filesystem persistence.
- VTU hardware adapter implementation and the complete nine VTU test sequences.
- LabVIEW version-specific and cRIO executable verification.

## 3. Audit evidence chain

`SRS ID → design note → AIXML file and SHA-256 → offline test vector → LabVIEW MCP check/validate result → native VI test result → integration test → VTU acceptance test`.

Use `manifest.json`, `tests/AIXML_Test_Cases.csv` and `results/Native_Validation_Log.csv` for traceability.

## 4. Open design decisions

- Exact LabVIEW 2025/2026 host target and deployed cRIO model/toolchain.
- Actual default connector pane pattern from `lvai_connector_pane`.
- Whether Actor Framework or QMH is adopted for runtime services; pure helpers remain portable.
- Rig-specific safe states, pressure/flow/servo limits, sensor failure policy, allowable feedback ages.
- Unit and quality typedef schema, signed configuration publication and plugin package constraints.
- Final VTU test acceptance wording from the primary Excel workbook.
