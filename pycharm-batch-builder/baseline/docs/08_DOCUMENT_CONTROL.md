# Document Control, Review, Configuration and Release Notes

| Field | Value |
|---|---|
| Project | Universal LabVIEW Profile and Sequence Executor |
| Configuration baseline | Architecture / SRS / SDD / SDP v0.2; implementation VI blueprint v0.3 |
| Package identifier | UE-AIXML-CORE-0.4.0-DRAFT |
| Package date | 2026-11-05 |
| Source of AIXML grammar | Zuehlke/labview-mcp `docs/aixml-reference.md` |
| Source document Git blob SHA | `fee4db454e42e2180717714d7527bce1bafa5a4f` |
| Source workflow Git blob SHA | `b6d7ec9dd63cba555ac63e3a2db36ba23888d99b` |
| Responsible architect | To be assigned |
| LabVIEW implementer | To be assigned |
| Controls reviewer | To be assigned |
| QA / verification owner | To be assigned |
| Functional approval | Pending |
| Safety approval | Pending |
| Release authorization | NOT GRANTED |

## Revision history

| Revision | Description | Status |
|---|---|---|
| V0.2 | Universal logical architecture and requirements | Draft reference |
| V0.3 | VI inventory, detailed LabVIEW build guide, Python simulator | Draft implementation blueprint |
| V0.4-AIXML | 28 pure VI specifications, 2 pane variants, static tests and native conversion runbook | Offline-verified engineering handoff |
| V0.4.1-DOC | Reviewed private DynasBrain repo; added integration architecture, limitations, acceptance tests and Codex pre/postflight | Documentation-only update |

## Configuration management

- `manifest.json` contains one SHA-256 checksum per AIXML file, connector-pane variant and interface contract.
- Generated AIXML is reproducible using `python generator/build_aixml.py`.
- Regenerate the catalog with `python generator/build_docs.py` and offline report with `python tests/validate_offline.py`.
- If any VI interface changes, update required SRS IDs, test cases, manifest and downstream actor integration references. Version the package accordingly.
- Do not regenerate or overwrite existing production LabVIEW VIs using AIXML unless preserving typedef/class/member ownership is understood and independently verified.

## Design review checklist

- [ ] Confirm target LabVIEW and LabVIEW MCP versions.
- [ ] Verify connector-pane pattern with target installation.
- [ ] Confirm that XML-generated pure helpers will use plain controls until typedef binding is added deliberately.
- [ ] Run all native MCP validation / generation / execution tests.
- [ ] Review exact VTU acceptance criteria and engineering limits.
- [ ] Approve Actor Framework vs QMH pilot outcome.
- [ ] Approve Bridge resource ownership and fault response design.
- [ ] Verify RT task priorities, bounded queues, watchdog and safe shutdown.
- [ ] Sign off simulation, HIL and physical fault injection.

## Known issues and deferred scope

1. Source AIXML is not a native VI and cannot confirm NI code-generation compatibility offline without a suitable backend.
2. The repository's empirically derived AIXML dialect may change across LabVIEW/AI-addon versions.
3. Units and sensor quality are metadata supplied by enclosing application; helper parameters are scalars.
4. Actor Framework message classes, .lvproj and .lvclass files require native creation/verification.
5. Physical VTU controller, safety and fault response logic are outside this package.
6. 66 unique graph tests do not cover every floating-point, concurrency or hardware fault scenario.

## Change request format

**Change ID:** CR-...  
**Reason / affected SRS:** ...  
**Affected VI files and hashes:** ...  
**Native test impact:** ...  
**Rig safety impact:** ...  
**Approvals:** ...
