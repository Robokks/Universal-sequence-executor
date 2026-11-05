# Universal Sequence Executor

Engineering workspace for the **Universal LabVIEW Sequence Executor**. The documentation baseline covers a VTU-first configurable test engine, Host/cRIO architecture, Supervisor, Executor, Bridge, HAL, faults, logging, pluggable VIs, and test planning.

**Implementation status:** documented designs and offline AIXML draft utility VIs; **zero native LabVIEW VIs validated**. The source archives produced for PyCharm/AIXML are not yet in this repository. Read [STATUS.md](STATUS.md).

## Documentation
- [Master Architecture](docs/architecture/MASTER_ARCHITECTURE.md)
- [Software Requirements Specification](docs/architecture/SRS.md)
- [Software Design Description](docs/architecture/SDD.md)
- [Software Development Plan](docs/architecture/SDP.md)
- [Complete VI Catalog](docs/labview/02_COMPLETE_VI_CATALOG.md)
- [LabVIEW Integration Guide](docs/labview/04_MODULE_INTEGRATION.md)
- [Test Cases](docs/labview/05_TEST_CASES_AND_ACCEPTANCE.md)
- [PyCharm Quickstart](docs/pycharm/QUICKSTART.md)
- [AIXML / DynasBrain Integration](docs/aixml/09_DYNASBRAIN_REPOSITORY_REVIEW_AND_INTEGRATION.md)

## Importing the previously prepared source archives
Download the ZIPs from the ChatGPT conversation, clone this repository and run `tools/import_packages.ps1` to copy the PyCharm project, AIXML baseline and optional Python simulator into their respective folders. Review files carefully before using `-CommitAndPush`.

## Safety and licenses
This repository contains **engineering drafts**, not validated machine control software. Execute native VIs only in an isolated test environment until hardware interfaces, watchdogs, emergency-stop functions and fault recovery have been independently verified. The repository is public: do not upload confidential rig code/data or credentials.
