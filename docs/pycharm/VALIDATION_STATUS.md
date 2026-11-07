# Validation report — v0.6

| Gate | Result | Evidence |
|---|---|---|
| Python unit tests | PASS 8/8 | `python -m unittest discover -s tests -v` |
| Baseline AIXML syntax / net checks | PASS 56/56 | Unit test iterates 28 definitions × 2 pane layouts |
| U01 staged AIXML / VI documentation | PASS 6/6 | `outputs/U01/stage_manifest.json`, `outputs/U01/vi_docs/` |
| U01 offline lint | PASS 6/6 | `outputs/U01/evidence/offline_lint.json` |
| AIXML → `.vi` offline composer | NOT RUN | Zuehlke isolated runtime not present on this machine |
| LabVIEW MCP native generation | NOT RUN | Windows LabVIEW installation/MCP not connected to this execution session |
| NI Docker MassCompile | NOT RUN | NI Docker image not pulled; no native VIs yet |
| Native LabVIEW behavior tests | NOT RUN | VI files not generated/compiled |
| RT target and physical hardware | NOT RUN | Out of scope |

**These are not production acceptance results.** The broader 124 application-VI design is a future implementation scope; only the first 28 utility AIXML designs are present. Native `.vi` status must not be promoted to VERIFIED until LabVIEW's own build and behavior tests pass.