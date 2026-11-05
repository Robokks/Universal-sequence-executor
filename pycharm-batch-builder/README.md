# Universal LabVIEW Executor — PyCharm Batch Builder v0.6

**Purpose:** A PyCharm-first Python project that organizes AIXML → native-VI generation **in controlled batches**, with VI-specific embedded documentation, mandatory non-overwrite behavior, and distinct evidence for offline checks, LabVIEW native tests and official NI Docker MassCompile. The baseline contains **28 unique AIXML utility VIs** (56 pane variants). The broader design baseline lists 124 separate application VIs, **not implemented here**.

## Start here on the Windows LabVIEW PC

1. Extract this ZIP to a regular directory such as `D:\LabVIEWProjects\UniversalExecutorBatchBuilder`.
2. Open **PyCharm → Open** and select the extracted folder (not an individual Python file).
3. Set interpreter to Python 3.11+; create `.venv` if needed.
4. Open PyCharm **Terminal** and enter:

```powershell
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m lvbatch list
python -m lvbatch prepare --batch U01 --pane 4815
python -m lvbatch check --batch U01
```

**First batch U01:** six utilities, twelve existing test vectors. Outputs appear under `outputs/U01`: staged AIXML, `vi_docs/*.md`, and a manifest containing SHA256 of each source. The staged AIXML root `description` gives intent, connector inputs/outputs, requirements and assumptions, so the VI itself carries this documentation after successful conversion. The original baseline is never modified. In LabVIEW, confirm **VI Properties → Documentation** after conversion.

## Native VIs on a Windows LabVIEW PC (requires installed Zuehlke MCP and running LabVIEW)

Install optional MCP client:

```powershell
python -m pip install -e ".[dev,mcp]"
python -m lvbatch mcp-generate --batch U01 --pane 4815 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
python -m lvbatch mcp-test --batch U01 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
```

**Do not run** the mutating commands until the MCP version, target LabVIEW year, generated pane, class/library dependencies, and scratch directory are checked. Do not run hardware VIs. This project is only the simple, pure utility slice.

The automatic result parser is conservative: missing native output or ambiguous MCP metadata means **FAIL**, never a fabricated pass. Different MCP releases may change their output JSON; confirm tool names/arguments with `lvai_status` and adjust the adapter if needed.

## Native VI composition with NO running LabVIEW — experimental

Zuehlke's bundled `pylabview` can compose a supported subset of AIXML into binary `.vi` files using an isolated Python runtime **without LabVIEW**, but this is not native compilation or behavioral proof. It is **not** the unrelated PyPI packages sometimes called pylabview. Extract an official release containing the bundled runtime or provision its `tools/pylabview/runtime` in the checked-out repository. See [`docs/PYLABVIEW_OFFLINE.md`](docs/PYLABVIEW_OFFLINE.md).

```powershell
python -m lvbatch compose --batch U01 --year 2026 --mcp-checkout "C:\LabVIEWTools\labview-mcp"
```

This writes only into `outputs/U01/native/` and refuses to overwrite an existing VI. Never treat `COMPOSED_UNVERIFIED` as Gold/functional verification.

## NI Docker compilation — optional gate

After six native VI files exist, [NI's official LabVIEW container](https://github.com/ni/labview-for-containers) can MassCompile and report load/compile errors. Its CI license **does not authorize code editing inside the container**. Docker mode is deliberately opt-in and only works when Docker is installed and an appropriate image/host OS/toolchain combination is available.

```powershell
python -m lvbatch docker-compile --batch U01
```

Default: official Linux `nationalinstruments/labview:latest-linux`, LabVIEWCLI `MassCompile -Headless`, no network, scratch-only volume. A Linux image may fail to load Windows-only dependencies; LabVIEW 2026 output requires a compatible LabVIEW release; Docker cannot replace cRIO/FPGA/hardware verification. Full details in [`docs/DOCKER_VALIDATION.md`](docs/DOCKER_VALIDATION.md).

## Testing gates and nonclaims

- Offline check: AIXML well-formed, mandatory description, UID/source net integrity. **Not** an NI type-check.
- Offline composer: emits a `.vi` using research-grade binary tooling. **Not** compilation.
- Docker MassCompile: the real NI LabVIEW engine loads/compiles. **Not** functional correctness.
- LabVIEW MCP test: the real VI is executed with specified inputs and reported outputs. **Software-only**.
- Application acceptance: later requires integration, RT and hardware tests, and independent safety verification.

This project neither modifies GitHub repositories nor installs Docker, LabVIEW or any proprietary third-party binaries. The 124 application VIs and unimplemented Actor Framework actors remain in the reference design documents.

## Connector-pane and icon finishing (LabVIEW 2026)

For compact connector panes (inputs left, outputs right) and consistent per-VI
32x32 icons, follow [Connector and icon runbook](docs/CONNECTOR_ICONS_RUNBOOK.md).
Run `python -m unittest discover -s tests -v` before preparing the reviewed
variants, then use `--layout compact --native-dir native_refined` to preserve the
previously tested `native/` files. Run `mcp-pane-audit` and `mcp-icons` only
after generating and behaviorally testing each reviewed batch. The `mcp-icons`
command backs up native files before applying icons. Each changed VI must be
tested again. Changing terminal indices or pane patterns is an interface change
for any callers; do not silently replace project-linked VIs.

## A01 simulator foundation — software-only behavioral reference

The five planned simulator VIs in A01 require native stateful LabVIEW
implementation; they are not equivalent to the 28 compiled utility designs.
The new [A01 simulator design and native gates](docs/A01_SIMULATOR_DESIGN.md)
provides a deterministic pure-Python behavior reference for simulation runs,
ACKs, controlled time, first-order plant response and fault scenarios.
Run `python -m lvbatch sim-smoke` to generate a local synthetic evidence report
under `outputs/A01/evidence/sim_reference.json`. This builds **zero**
native LabVIEW VIs and cannot reach physical I/O.

## First native A01 application VI — Sim_Clock

After the A01 Python simulator smoke test passes, the first native target
is `Sim_Clock.vi`. Follow the
[A01 native clock runbook](docs/A01_CLOCK_NATIVE_RUNBOOK.md). Use
`a01-clock-prepare`, `check --batch A01`, `compose --batch A01`,
`a01-clock-test`, `mcp-pane-audit` and then `mcp-icons` and retest.
The candidate uses I64 timestamps and rejects invalid time advances and
integer overflow. It is **not yet LabVIEW-verified**. Only this one VI is
staged; the other four A01 native VIs still need designs.
