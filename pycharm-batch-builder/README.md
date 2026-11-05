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
