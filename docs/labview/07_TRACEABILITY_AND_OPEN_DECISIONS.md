# 07 — Traceability, Approved Decisions & Design Review

> **Draft implementation design V0.3 (2026-11-05)**. Based on SRS/SDD/SDP V0.2. These are proposed names and connector patterns, **not existing native `.vi` binaries**. Ratings, timing budgets, approved pressure/motion limits and protective responses require the responsible controls/safety engineers' sign-off. This package contains no executable rig-control logic.


## Agreed architectural facts retained from V0.2
- One universal engine supports multiple test-rig types, nested tests/groups/sequences, profile operating points, cycles, sequential and parallel execution.
- Host configures and publishes test packages; selected target stores an immutable local package and runs Host-resident or cRIO-resident executor semantics.
- Manual and Auto commands both use a Bridge; mode changes require prior stop.
- Dedicated event log and report capture VIs; test-specific fault and shutdown sequence (one each per test).
- Global fault interrupts all active parallel execution; independent hardware safety remains separate.
- VTU uses servo-driven PC lever (configurable relative 2 mm **example**), independently sensed hydraulic hitch, VFD flow PID and PRV pressure PID; sweeps can vary pressure/flow separately or together.
- Both custom operation and custom full-test VIs supported via common managed interface.

## Proposed implementation choices (not approved yet)
- Module `.lvlib` boundaries, file/VI names, internal QMH and loop decomposition in documents 01–04.
- Configuration serialization schema, protected publication mechanism and runtime message envelope.
- Plugin worker pool strategy, RT call preallocation and cancellation responsiveness goals.
- Timer granularities, feedback freshness windows, buffer sizes, retry thresholds and actual loop scheduling.
- Checkpoint durability strategy and authorized restart procedure.
- Fault sequence action restrictions and safe fallback selection must be approved per rig.

## SRS-to-design / test anchors
| Requirement family | Primary design modules | Example verification |
|---|---|---|
| SRS-F-001…004 Rig/Test/Groups/Commands | Host Editor, Config, Engine, Bridge | UT-SEQ-005, UT-SEQ-010 |
| SRS-F-005…007 Conditions/Timing/Popup | Condition Engine, Step Tick, Popup | UT-CON-001…012, UT-SEQ-001…013 |
| SRS-F-008…010 Capture/Event/Cycles | Logging, Cycle, Checkpoints | UT-DAT-001…009, UT-SEQ-008 |
| SRS-F-011 Plugins | Plugin Manager/Workers | UT-SUP-006…010 |
| SRS-F-012…016 Modes/Fault/Shutdown | Supervisor, RT Checker, Bridge | UT-BRG-005…010, UT-SUP-001…013 |
| SRS-F-017…020 Target/Sweep/Servo | Config, transport, RT loops, VTU plugins | VTU-001…008 |
| SRS-F-021…025 Ownership/Quality/Validation/Traceability/Plugin | Bridge, Registry, Config, Event Logger, Plugin | UT-BRG, UT-CON, UT-CFG, UT-SUP |
| SRS-Q-001…005 Quality constraints | RT isolation, watchdog, immutable config, queues, checkpoints | UT-SUP-003, UT-DAT-006…007 |

## Required pre-implementation sign-offs
1. **Architecture:** Approve actual resource-owner semantics, exception taxonomy, executor states, plugin lifecycle and shutdown authority.
2. **Controls:** Approve control modes, PID implementation approach, servo coordinate mapping, physical limits, sensor freshness and saturation handling.
3. **Safety:** Analyze hazards and approve fail-safe hardware, RT fallback and all fault/shutdown behaviors; verify emergency stop independently.
4. **IT/security:** Approve Host/target access, service permissions, secure config publication, audit requirements and network transport.
5. **Test engineering:** Confirm authoritative VTU test procedures/acceptance values, report formulas, periodic capture requirements and fixture variants.
6. **Development:** Confirm LabVIEW version, Real-Time Module, cRIO and driver compatibility, dependencies and actual build/runtime packaging.

## Scope of this package
This is an **implementation-ready design specification**, not a valid LabVIEW source project and not verification evidence. LabVIEW-compatible type definitions, connector panes, compiled VIs, module `.lvlib` files, `.lvproj` and `.rtexe` must be created, integrated, measured and verified on the real system.