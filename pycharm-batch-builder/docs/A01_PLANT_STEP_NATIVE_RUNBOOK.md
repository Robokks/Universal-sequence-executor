# A01P -- Sim_VTU_Plant_Step.vi (native LabVIEW candidate)

**Status: source AIXML and 16 independent vectors in GitHub; native VI compilation and execution NOT RUN.**

A01P is a **separate scratch-only helper batch** for developing the mathematical core
of A01's planned `Sim_VTU_Plant.vi`. This is NOT a sixth accepted A01
application VI and is NOT the full three-channel plant. It applies a single
finite first-order response to synthetic, preclamped input values. It does not
command real actuators, access test-rig equipment, connect to NI DAQmx, or
implement a safety controller.

## Contract

Inputs (four DBL, pattern 4815, indices 11, 10, 9, 8):

- `current`: previous measured synthetic channel value, finite.
- `target`: synthetic, PRECLAMPED command channel value, finite.
- `dt_ms`: simulation time advance, finite, >= 0.
- `time_constant_ms`: positive, finite response constant.

Outputs (pattern 4815, indices 3 and 2):

- `next`: `current + (1 - exp(-dt_ms / time_constant_ms)) * (target - current)`.
- `valid`: FALSE for negative `dt_ms` or nonpositive `time_constant_ms`; when
  invalid, `next=current`.

This implementation uses LabVIEW's `Exponential` primitive and DBL arithmetic.
Python's independent reference uses `-expm1(-x)`, which is more accurate for
very small `x`. The 16 native vectors enforce relative and absolute tolerance
1e-8. NaN/Inf are rejected by the Python reference but the native graph relies
on finite caller inputs; this precondition requires a future native guard
before integrating into a safety-relevant application.

**Caller responsibilities:** run all three VTU channels separately, clamp
setpoints to a model, apply half-limit saturation or stuck-servo faults,
split steps on fault timestamps, own the previous and next state, and publish
feedback quality. These are NOT yet implemented in the helper.

## Run from the existing PyCharm project on your LabVIEW PC

Keep the existing U01-U04 `native_refined` VIs, A01 `Sim_Clock.vi`,
and their evidence untouched.

```powershell
cd "C:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor"
git status
git pull --ff-only origin main
cd pycharm-batch-builder

$exe = "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
$env:LABVIEWMCP_PYLABVIEW = "C:\LabVIEWTools\labview-mcp-offline\tools\pylabview\runtime"

& $exe --pylv-status
python -m unittest discover -s tests -v
python -m lvbatch sim-smoke
python -m lvbatch a01-plant-prepare --native-dir native_plant_v1
python -m lvbatch check --batch A01P
Get-ChildItem ".\outputs\A01P\native_plant_v1" -Filter *.vi -ErrorAction SilentlyContinue
```

Only if the A01P check says PASS, the scratch folder has no .vi files, and
LabVIEW 2026 is already running:

```powershell
python -m lvbatch mcp-generate --batch A01P --pane 4815 --backend grpc --exe $exe
```

This is a mutation of a **new** .vi file. If MCP reports failure after writing
a VI, do not rerun into the same output folder; preserve it and switch to
`native_plant_v2` via a new preparation.

After native generation reports `ok:true` for the one staged VI:

```powershell
python -m lvbatch a01-plant-test --backend grpc --exe $exe
python -m lvbatch mcp-pane-audit --batch A01P --backend grpc --exe $exe
```

Native acceptance requires: one native file exists; LabVIEW reports executable
state 1; all 16 real VI input/output tests pass; connector pane indices and
type contracts are audited. Check VI Properties > Documentation.

Only after those gates and closing the open VI panel, add the icon and test again:

```powershell
python -m lvbatch mcp-icons --batch A01P --backend grpc --exe $exe
python -m lvbatch a01-plant-test --backend grpc --exe $exe
```

The batch is **NOT accepted** if NI conversion, executor state, pane audit,
or any native vector fails. Do not relabel Python model/graph tests as native
evidence.

## Evidence

- `baseline/aixml/app/Sim_VTU_Plant_Step.xml`: source graph.
- `baseline/tests/A01_Plant_Step_Native_Vectors.json`: 16 test cases.
- `outputs/A01P/step_v1/Sim_VTU_Plant_Step_DESIGN.md`: staged documentation.
- `outputs/A01P/evidence/mcp_generation.json`: generation result.
- `outputs/A01P/evidence/sim_plant_step_native.json`: real native test outputs.
- `outputs/A01P/evidence/native_panes.json`: geometry and style audit.

This does not resolve the two exact I64 `Sim_Clock.vi` cases that remain
blocked by MCP transport precision. Those are a separate acceptance task.

## Next after acceptance

Integrate the accepted scalar helper into the full A01 state-owned
`Sim_VTU_Plant.vi`, then build `Sim_Fault_Injection.vi`,
`Sim_IO_Adapter.vi` and `Sim_Main.vi` using synthetic-only interfaces.
