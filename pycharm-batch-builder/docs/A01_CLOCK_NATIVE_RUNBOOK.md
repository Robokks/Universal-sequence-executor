# A01 Sim_Clock.vi — first native application VI

Status: AIXML authored and checked in GitHub CI; **native VI not yet composed
or executed on Windows LabVIEW**. All commands assume the existing LabVIEW
2026 Q3 environment and the provisioned Zuehlke offline composer.

This is **one of five** A01 native VIs. Do not describe all A01 as built.

## Contract

| Connector | Type | Rule |
| --- | --- | --- |
| current_ms | LabVIEW I64 input | Previous virtual timestamp, 0..I64_MAX |
| advance_ms | LabVIEW I64 input | Requested nonnegative virtual increment |
| next_ms | LabVIEW I64 output | Sum if valid; previous timestamp otherwise |
| valid | Boolean output | True only if both inputs nonnegative and no I64 overflow |

Connector geometry: pattern **4805**, input slots **3, 2** on the left and
output slots **1, 0** on the right. The VI is a **pure clock step**, not a
free-running clock; the future Sim_Main caller owns and persists `next_ms`
only when `valid` is true. This avoids hidden global timing state.

For full range, use signed 64-bit integer terminal values — **not DBL** —
because values above 2^53 cannot be represented exactly as DBL.

## Run on Windows / PyCharm

First update the project and prepare only the clock candidate.

```powershell
cd "C:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor"
git pull origin main
cd pycharm-batch-builder

python -m unittest discover -s tests -v
python -m lvbatch sim-smoke
python -m lvbatch a01-clock-prepare --native-dir native_clock_v2
python -m lvbatch check --batch A01
```

Do not use generic `prepare --batch A01`: the other four A01 native AIXML
designs are not yet written. `a01-clock-prepare` deliberately stages only
`Sim_Clock.vi`.

### Recovery from pylabview's 64-bit constant packing error

In the initial revision, the composer failed with
`struct.error: 'q' format requires -9223372036854775808 <= number <= 9223372036854775807`.
The bundled pylabview composer converts integer literals through
`int(float(value))`, which rounds literal `I64_MAX` up to `2^63`.
The AIXML now constructs the exact I64 maximum as
`(2^62 - 1) + 2^62`, where the large source literal is exactly
representable as binary64 and the final arithmetic is in I64.

**After updating Git, use `--native-dir native_clock_v2`** to keep the
failed attempt separate. Rerun `a01-clock-prepare` and
`check --batch A01` before composition. If the generated VI still fails,
keep the full error output for debugging; do not edit the installed LabVIEW
or bundled Zuehlke composer files.

Then compose only the scratch candidate (no running LabVIEW required):

```powershell
python -m lvbatch compose --batch A01 --year 2026 --mcp-checkout "C:\LabVIEWTools\labview-mcp-offline"
```

Expected status is `complete: true` and a single
`Sim_Clock.vi` with `COMPOSED_UNVERIFIED`; this is **not native proof**.
The output file is in `outputs\A01\native_clock_v1\Sim_Clock.vi`.
The composer refuses overwrite. If you need to rebuild, back up the output
file or entire output subfolder first rather than deleting it.

Open the new VI in LabVIEW 2026. Check the unbroken Run arrow, diagram,
terminal types and VI Properties > Documentation.

With LabVIEW and LabVIEW MCP running:

```powershell
python -m lvbatch a01-clock-test --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
python -m lvbatch mcp-pane-audit --batch A01 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
```

The eight native test vectors come from
`baseline/tests/A01_Clock_Native_Vectors.json`: ordinary positive,
zero, negative increment, negative current, signed overflow, exact
maximum boundary and near-max cases.

This script verifies integer outputs **losslessly**: no floating-point
comparison is accepted for I64 values above 2^53. If the MCP transport
converts a large I64 to DBL, the case correctly reports FAIL and must be
investigated; do not lower the acceptance threshold to mask the problem.

After exact native behavior and the pane audit pass, close the affected
VI window (keep LabVIEW running) and set the icon:

```powershell
python -m lvbatch mcp-icons --batch A01 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
python -m lvbatch a01-clock-test --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
```

The icon command backs up the native VI, writes a descriptive SIM icon,
and records read-back evidence. Do not claim completion until icon
verification reports `ok: true` and the final eight native tests all pass.

## Evidence files

- `outputs/A01/evidence/sim_reference.json`: Python model, not LabVIEW.
- `outputs/A01/evidence/offline_lint.json`: stage AIXML structure only.
- `outputs/A01/evidence/offline_compose.json`: binary composition only.
- `outputs/A01/evidence/sim_clock_native.json`: eight LabVIEW runs (expected).
- `outputs/A01/evidence/native_panes.json`: native geometry audit.
- `outputs/A01/evidence/native_icons.json`: icon read-back.

Only 1 of the planned 5 A01 application VIs is in this initial native
candidate. Sim_VTU_Plant, Sim_Fault_Injection, Sim_IO_Adapter and Sim_Main
require additional native design and tests; they remain NOT RUN.

**Safety:** Software simulation only; no real hydraulic or actuator I/O.
Demo limits in the Python reference are not test-rig safety limits.
