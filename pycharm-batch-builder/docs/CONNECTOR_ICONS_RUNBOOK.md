# Native connector panes and VI icons — LabVIEW 2026

This pipeline uses the **existing** LabVIEW MCP v2.4.1 and the separately provisioned
`C:\LabVIEWTools\labview-mcp-offline` composer. Do not alter NI's installed files.

## Root cause and design contract

The original U01/U02 AIXML used `conIdx` 11, 10 and 9 for controls and 3, 2 for
indicators: that layout is correct **only on connector pattern 4815**.
The offline composer may otherwise inherit a **4833** default, where the same
indices live on different sides. A VI can run all behavioral tests while having
an unsuitable connector pane. Correctness of computation is not proof of
subVI interface quality.

`prepare --layout compact` pins a measured native pattern in a trailing
`<?lvmcp pane="..."?>` processing instruction and rewrites the staged,
never the baseline, `conIdx` assignments.

| Inputs | Outputs | Pattern | Input indices (top to bottom) | Output indices |
| --- | --- | --- | --- | --- |
| 1 | 1 | 4801 | 1 | 0 |
| 2 | 1 | 4802 | 2, 1 | 0 |
| 2 | 2 | 4805 | 3, 2 | 1, 0 |
| 3 | 1 | 4810 | 5, 4, 3 | 2 |
| 3 | 2 | 4810 | 5, 4, 3 | 2, 1 |
| 4 | 1 | 4815 | 11, 10, 9, 8 | 3 |
| 4 | 2 | 4815 | 11, 10, 9, 8 | 3, 2 |

All mappings come from Zuehlke's measured `docs/connector-pane-patterns.tsv`,
not an invented numbering scheme. Other sizes fall back to explicitly pinned
4815 only when at most four controls and four indicators fit; larger sizes
are refused until their pane is designed.

## Keep your previously tested VIs safe

In PyCharm's terminal, run from
`C:\Users\DynaAdmin\PycharmProjects\Universal-sequence-executor\pycharm-batch-builder`.
Use these **separately for U01 and U02**. The reviewed output goes in
`outputs\U01\native_refined` or `outputs\U02\native_refined`, and the
previously tested `native\` directory remains unchanged.

```powershell
# Run Python tests FIRST; one older unit test regenerates the U01 stage manifest.
python -m unittest discover -s tests -v

python -m lvbatch prepare --batch U01 --pane 4815 --layout compact --native-dir native_refined
python -m lvbatch check --batch U01
python -m lvbatch compose --batch U01 --year 2026 --mcp-checkout "C:\LabVIEWTools\labview-mcp-offline"
python -m lvbatch mcp-test --batch U01 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
python -m lvbatch mcp-pane-audit --batch U01 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
```

Review `outputs\U01\evidence\native_panes.json`. This report records
the actual pane measurements and NI style guidance from the MCP service.
**It is an audit, not an automatic style PASS.** Check real terminal
positions/assignments against `stage_manifest.json`; stop if they disagree.

After reviewing, close the affected VIs in LabVIEW (leave the LabVIEW
application itself running), and set the icons:

```powershell
python -m lvbatch mcp-icons --batch U01 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
python -m lvbatch mcp-test --batch U01 --backend grpc --exe "C:\LabVIEWTools\labview-mcp-v2.4.1\bin\LabVIEWMCP.exe"
```

The icon tool makes a local pre-change backup under
`outputs\U01\icon_backups\<UTC timestamp>\` and records read-back results in
`outputs\U01\evidence\native_icons.json`. `ok: true` means every icon
was read back successfully; do not assume success without that result.
U01/U02 have descriptive 32×32 icons and batch-specific banner colors.
**Regenerating a VI resets its icon; run mcp-icons last.**

Repeat with `--batch U02` and `native_refined` when U01 is accepted.

## Safety and compatibility

* Do not overwrite existing tested `native/*.vi` files. The composer
  deliberately refuses overwrites.
* Connector **index or pattern changes may break existing subVI callers**.
  The reviewed copies are interface-version changes. Regenerate or relink
  callers only after accepting the new connector contract.
* A `PASS` for tests does not verify the native pane and vice versa.
* An icon update changes the VI file, but should not change computation.
  Rerun behavioral tests after the icon operation.
* The NI gRPC backend can ignore the trailing pylabview-specific pane marker,
  so direct `mcp-generate` explicitly uses `connector_pattern` in its
  `panePattern` argument.
* AIXML cannot store the native icon; icons require the postprocessing tool.
