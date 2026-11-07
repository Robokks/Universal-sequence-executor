# A01 — Simulator foundation: implementation contract and native-build gates

Status: **Python reference implemented; 21 total Python regression tests and A01 smoke test passed on GitHub Actions. Native LabVIEW VIs NOT BUILT.**
Source baseline: VI Blueprint V0.3 / Batch Manifest A01, five application VIs.

## Purpose and scope

A01 is the software-only test target for the Universal LabVIEW Sequence Executor.
It enables later registry, bridge, executor and supervisor tests without real equipment.
It **must never open a physical I/O device**; simulated output is always tagged
`synthetic: true`. Example model ranges below are NOT certified physical limits.

A01 contains the five application VIs named in the baseline. Unlike pure U01-U04
utilities, their production designs require state, typed events, lifecycle and
possibly loops/queues. The Python reference is an **oracle for behavior**, not a
replacement for native LabVIEW blocks and not an AIXML-to-VI conversion.

| Native VI from catalog | Proposed interface | Reference behavior / acceptance |
| --- | --- | --- |
| `Sim_Main.vi` | simulated parameters + virtual clock -> session identity | Start one simulation-only session, no device connection; stop/cleanup required before integration |
| `Sim_IO_Adapter.vi` | command + simulated state -> ACCEPTED/APPLIED/rejected events + feedback | command ID deduplication, run ID verification, delayed ACK and synthetic quality timestamps |
| `Sim_VTU_Plant.vi` | pressure/flow/lever setpoints + model + previous state + dt -> new state | bounded first-order plant, saturation, configurable quantization |
| `Sim_Fault_Injection.vi` | fault kind + trigger virtual time + state -> modified simulation behaviors | deterministic sensor stale/dropout, lost ACK, stuck servo, saturation, plugin stall, host disconnect and disk-full scenarios |
| `Sim_Clock.vi` | previous monotonic time + nonnegative advance -> next time | virtual monotonic integer milliseconds; negative/overflow rejected |

**Proposed interface fields are for design review**. They do not supersede
existing typedefs, frozen connector contracts, or the baseline's hardware
safety policies. Map to approved LabVIEW typedefs before generating full VIs.

## Reference behavior

Implementation: `src/lvbatch/sim_reference.py`, Python stdlib only.

1. `SimSession(run_id)` creates a synthetic, simulation-only state.
2. `submit(Command(..., transport="SIM"))` emits ACCEPTED/REJECTED/DUPLICATE,
   stores bounded setpoints, and schedules a deterministic delayed APPLIED ACK.
   Physical transports are rejected before any simulated actuation.
3. `advance(delta_ms)` advances virtual time; it splits the update at exact
   fault and ACK timestamps, applying a first-order state transition within
   each fault-free segment. No real wall-clock sleeping.
4. `feedback()` returns quantized pressure/flow/lever and quality + sample
   time. Dropout returns INVALID and null samples; stale samples preserve their
   old source timestamp. Consumers must reject samples whose age is over their
   configured freshness threshold.
5. `schedule_fault(Fault.* , at_ms)` activates faults at a deterministic
   virtual timestamp. PLUGIN_STALL and DISK_FULL are recorded and made
   available for higher-level supervisor/logger integration; they do not yet
   simulate those services.

The sample model uses illustrative limits of 100 bar, 40 L/min and 200 mm,
a 500 ms first-order time constant and 50 ms ACK delay. **They are not VTU
equipment specifications.** Real rig parameters require engineering approval
before any physical use.

## Run on PyCharm (no LabVIEW)

From `pycharm-batch-builder`:

```powershell
python -m unittest discover -s tests -v
python -m lvbatch sim-smoke
```

The second command saves `outputs/A01/evidence/sim_reference.json`, with
`phase: "A01_PYTHON_REFERENCE_ONLY"` and `native_vis_built: 0`.
The path is a local, ignored evidence folder; to archive it for release
the team must intentionally package and version the evidence.

## Native LabVIEW A01 build order

1. **Sim_Clock.vi** — signed monotonic timestamp with explicit initialized
   state, negative/overflow rejection, no wall-clock dependence.
2. **Sim_VTU_Plant.vi** — pure `dt`/previous-state-to-next-state function;
   compare against Python at 0/50/500/2000 ms, saturation and stuck servo.
3. **Sim_Fault_Injection.vi** — inject faults at exact virtual timestamps;
   compare with Python for stale/dropout/ACK failure.
4. **Sim_IO_Adapter.vi** — run identity, command IDs, ACK queue, type-safe
   artificial transport and sample publication.
5. **Sim_Main.vi** — explicit initialize/execute/stop lifecycle; wire only
   simulated adapters and later accepted registry/bridge contracts.

Use a scratch LabVIEW project. Do not disguise empty VIs as implemented.
Every new VI requires its own AIXML (or native scripting implementation),
type and connector approval, native compile/load, functional tests, pane
audit, icon read-back and post-icon tests. Reference cases A01-SIM-001..010 are recorded in
\`baseline/tests/A01_Simulator_Reference_Test_Cases.csv\`. These are new
reference-level cases, not additions to the approved master manifest; native
status remains NOT_RUN until actual LabVIEW execution.

## Blockers before A01 native build can be accepted

- Approve native typedefs for command, ACK, sensor quality/timestamps, run ID,
  model config and fault state.
- Decide on simulation single-loop ownership/queue lifetime and stop policy.
- Decide deterministic virtual clock units and overflow behavior.
- Explicitly prohibit any physical controller command path while SIM mode.
- Add named A01 test case rows and failure injection acceptance criteria.
- Demonstrate native model-reference parity and no unhandled broken run arrows.

This work is strictly a simulation scaffold. Hardware integration, protection,
real-time execution and VTU acceptance remain **NOT RUN**.
