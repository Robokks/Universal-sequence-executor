# Offline pylabview — actual limits

Source: https://github.com/Zuehlke/labview-mcp/blob/main/docs/aixml-backends.md

Zuehlke includes a **bundled** `pylabview` interpreter and AIXML composer, not an installable stand-alone project dependency. Its `scripts/aixml-pylabview/aixml2vi.py` can build VIs in a supported subset without LabVIEW running; unsupported constructs are refused. It requires the `scripts/aixml-pylabview/parts` donor data and an isolated pylabview runtime (`tools/pylabview/runtime` in source checkout or the equivalent runtime from an official release). It is research-grade. No validation occurs until actual LabVIEW loads/compiles the result.

Steps:
1. Obtain an official `Zuehlke/labview-mcp` release or clone its GitHub repository.
2. Verify the extracted release contains `LabVIEWMCP.exe` plus `scripts/aixml-pylabview/` and the bundled pylabview runtime. Source checkouts may need a provisioning script and a runtime download (not included in this package).
3. In PyCharm: `python -m lvbatch prepare --batch U01 --pane 4815`.
4. In PyCharm: `python -m lvbatch compose --batch U01 --mcp-checkout C:\LabVIEWTools\labview-mcp --year 2026`.
5. Check statuses in `outputs/U01/evidence/offline_compose.json`: expect `COMPOSED_UNVERIFIED`, not native PASS.
6. Follow with Docker MassCompile (if compatible), then the real LabVIEW unit tests before Gold classification.

The same directory must not contain trusted VIs: the CLI refuses overwrite. On older targets, use `--year 2025` only when the composer supports producing compatible files, then confirm with actual LabVIEW 2025 or matching CI image.
