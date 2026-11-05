# Repository status — 2026-11-05

## What is committed
- Master architecture, SRS, SDD and SDP drafts in `docs/architecture/`.
- Detailed LabVIEW project structure, 124-VI design catalog, block diagram guide, module integration, VTU mapping, requirement traceability, test cases (82 planned), inventory and initial working-slice guide in `docs/labview/`.
- PyCharm batch-builder quickstart and validation status in `docs/pycharm/`.
- AIXML/DynasBrain integration review in `docs/aixml/`.
- Python simulator documentation and design-pattern comparison in `docs/python/`.

## What is NOT yet committed
- The PyCharm source-code package (`src/lvbatch`), associated AIXML baseline, runtime test fixtures and generated evidence are **available as separate download artifacts in the ChatGPT conversation**, but have **not yet been imported into this repository**.
- Python executor source and tests are similarly not yet imported.
- No native LabVIEW `.vi`, `.lvclass` or `.lvproj` files have been created or validated for this project.

## Why
This repository was initially empty. Documentation was uploaded first; the local source archives cannot be transferred directly using the current GitHub text-file operations. Use `tools/import_packages.ps1` with the downloaded source ZIPs from the conversation, review the staged changes, and opt in to a commit/push.

## Development verification gates
1. Offline AIXML syntax/graph validation is not LabVIEW validation.
2. Offline binary VI composition is not proof of loadability or correct execution.
3. NI LabVIEW MassCompile checks loading/compilation but not application behavior.
4. Native LabVIEW tests must verify behavior and interface contracts.
5. Hardware/cRIO integration requires independent fault and safety verification.

Do not commit private project VIs or proprietary test procedures into this **public** repository without permission.
