# Universal LabVIEW Sequence Executor - working simulation-only vertical slice

Status: Python sequence runner and desktop operator GUI implemented. GitHub Actions tests the complete mock/synthetic workflow. The optional native LabVIEW comparator is coded but still needs execution on the user's Windows LabVIEW 2026 PC. The native LabVIEW sequence engine and front panel are NOT built.

## What works in this release

- A strict JSON sequence definition with explicit SIMULATION_ONLY mode; no physical I/O.
- Three pressure setpoints: 25, 50 and 10 bar.
- Step scheduling, feedback monitoring, dwell, timeout, pass/fail and stop.
- Temporary Tkinter operator interface with Start, Pause, Resume, Stop and status.
- Deterministic first-order synthetic feedback from the A01 Python reference.
- JSON and CSV run records with unique IDs and no overwrite.
- Two decision backends: mock Python offline mode, and grpc mode that calls the actual already-verified U02 LabVIEW utility VIs. Only those decision VIs run in LabVIEW; the orchestrator and desktop UI are Python.

## Windows PyCharm: quick start

In the project root:

    cd "C:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor"
    git pull origin main
    cd pycharm-batch-builder
    python -m unittest discover -s tests -v
    python -m lvbatch demo-run --backend mock
    python -m lvbatch demo-gui

demo-gui requires a Windows desktop Python installation with Tkinter.
The mock backend is NOT native LabVIEW evidence.

Outputs are created locally under outputs/MVP:
- MVP-<unique-id>.json
- MVP-<unique-id>_events.csv

## Execute decision VIs in real LabVIEW

With LabVIEW 2026 open and the existing MCP service available:

    python -m lvbatch demo-run --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe" --native-dir ".\outputs\U02\native_refined"

    python -m lvbatch demo-gui --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe" --native-dir ".\outputs\U02\native_refined"

This strictly invokes UE_Within_Tolerance.vi and UE_Timeout_Reached.vi
in the U02 scratch output, requiring real typed Boolean LabVIEW outputs.
There is no silent fallback to Python if the NI gRPC call fails.

## NI code conventions and post-generation cleanup

Follow NI's VI/library development recommendations:

1. Left-to-right block diagrams with short, legible wires and small subVIs.
2. Input terminals left / output terminals right, clear connector panes.
3. Meaningful names, control descriptions, a clear icon and VI documentation.
4. Error in / error out clusters for new application and I/O subVIs.
5. Explicit ownership of state, typed error and data contracts.
6. Native compilation, run state, behavior and error-path tests are mandatory.
7. After cleanup, verify the subVI callers' connector wiring again.

NI references:
https://www.ni.com/en/support/documentation/supplemental/21/driver-and-vi-library-development-guidelines.html
https://knowledge.ni.com/KnowledgeArticleDetails?id=kA03q000000x20uCAA
https://www.ni.com/docs/en-US/bundle/labview/page/using-error-clusters.html

The mcp-generate command now requests diagram and panel cleanup on new
native VI generation. The offline pylabview composer still cannot call
LabVIEW's native diagram cleanup without running Windows LabVIEW.

After offline composition: first preview, then apply on explicit request.

    python -m lvbatch native-cleanup --batch A01 --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"

    python -m lvbatch native-cleanup --batch A01 --apply --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"

The command accepts only staged scratch native VI paths, backs up originals
before mutation in outputs/A01/cleanup_backups, verifies diagram changes,
and writes outputs/A01/evidence/native_cleanup.json.
After layout, perform connector audit, icon readback and ALL native
functional tests again. Diagram cleanup is not computation verification.

## Native completion still pending

- A01 Sim_Clock.vi was composed and passed 6/8 native MCP cases. Two
  extreme I64 cases remain unresolved because the MCP input helper rounds
  large integer inputs. The ActiveX diagnostic returned 0x80080005.
  Do not label the VI accepted.
- A native LabVIEW top-level sequence runner, operator GUI, typed state
  machine, queues, hardware interfaces, plugin framework and report VIs
  are NOT yet built. The frozen architecture lists 124 application VIs.
- This software is explicitly SIMULATION ONLY, not suitable for driving
  hydraulic actuators, motors or safety equipment.

The next native phase must replace the temporary Python runner with a
NI-style QMH or explicit state machine and a native LabVIEW front panel,
then run real compilation and behavior checks on Windows LabVIEW 2026.
