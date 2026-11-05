"""First A01 native-VI slice: an explicit-state, deterministic Sim_Clock.vi.

Only Sim_Clock is staged. A01 remains a five-VI plan, not implemented.
The isolated, scratch-only output path avoids replacing U01-U04 or other
application VI binaries. Native execution is required to prove correctness.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .core import (check_aixml, get_batch, project_root, read_json, record,
                   sha256, vi_intent)
from .layout import assign_connector, composer_pane_directive, native_subdir


def prepare_sim_clock(native_dir: str = "native_clock_v1", root: Path | None = None) -> dict:
    base = root or project_root()
    allowed = get_batch("A01", base)["vi_names"]
    if "Sim_Clock.vi" not in allowed:
        raise ValueError("A01 manifest does not include Sim_Clock.vi")
    native_dir = native_subdir(native_dir)
    out = base / "outputs" / "A01"
    prior = out / "stage_manifest.json"
    if prior.is_file():
        state = read_json(prior)
        if state.get("component") != "Sim_Clock.vi":
            raise FileExistsError("A01 has a different stage manifest; do not overwrite it")
    original = base / "baseline/aixml/app/Sim_Clock.xml"
    current = ET.parse(original).getroot()
    if current.get("_name") != "Sim_Clock.vi":
        raise ValueError("A01 Sim_Clock source name has changed")
    entry = {
        "inputs": [{"name": "current_ms", "type": "int64"},
                   {"name": "advance_ms", "type": "int64"}],
        "outputs": [{"name": "next_ms", "type": "int64"},
                    {"name": "valid", "type": "bool"}],
        "requirements": ["SRS-F-006", "A01-SIM-002"],
        "notes": ("Pure step: caller stores next_ms only when valid is true. "
                  "Simulation-only virtual time; no wall clock or physical I/O. "
                  "Signed 64-bit overflow and negative times are refused."),
    }
    doc_text = vi_intent(entry, current.get("description") or "")
    current.set("description", doc_text)
    pattern, mapping = assign_connector(current, entry, "compact", "4815")
    stage_folder = out / "clock_v1" / "staged_aixml"
    stage_folder.mkdir(parents=True, exist_ok=True)
    target = stage_folder / "Sim_Clock.xml"
    ET.ElementTree(current).write(target, encoding="utf-8", xml_declaration=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(composer_pane_directive(pattern))
    analysis = check_aixml(target, "Sim_Clock.vi")
    if not analysis["ok"]:
        raise ValueError("Staged AIXML is invalid: " + "; ".join(analysis["issues"]))
    testfile = base / "baseline/tests/A01_Clock_Native_Vectors.json"
    spec = read_json(testfile)
    if not spec["vectors"]:
        raise ValueError("No A01 native clock tests")
    documentation = out / "clock_v1" / "Sim_Clock_DESIGN.md"
    documentation.write_text(
        "# Sim_Clock.vi - A01 native scratch candidate\n\n"
        "Not an initialized, free-running clock: pure explicit-state step, "
        "with state owned by Sim_Main.vi.\n\n"
        "Inputs: current_ms (I64), advance_ms (I64).\n\n"
        "Outputs: next_ms (I64), valid (Boolean).\n\n"
        "valid = current_ms >= 0 and advance_ms >= 0 and "
        "advance_ms <= I64_MAX - current_ms.\n\n"
        "If valid, next_ms = current_ms + advance_ms; otherwise next_ms = current_ms.\n\n"
        "All values are **synthetic milliseconds**; no external timing APIs or hardware.\n\n"
        f"Connector pattern: {pattern}. Terminals: {mapping}.\n\n"
        f"Native test cases: {len(spec['vectors'])}. Native execution NOT RUN.\n",
        encoding="utf-8")
    item = {
        "name": "Sim_Clock.vi", "xml": str(target),
        "native_vi": str(out / native_dir / "Sim_Clock.vi"),
        "sha256": sha256(target), "tests": [t["id"] for t in spec["vectors"]],
        "inputs": entry["inputs"], "outputs": entry["outputs"],
        "connector_pattern": pattern, "connector_map": mapping,
    }
    payload = {
        "batch": "A01", "component": "Sim_Clock.vi", "pane": "4815",
        "layout": "compact", "native_dir": native_dir, "native_vis_planned_in_batch": 5,
        "native_vis_staged": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "state": "AIXML PREPARED: no native LabVIEW execution", "items": [item],
    }
    prior.parent.mkdir(parents=True, exist_ok=True)
    prior.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _read_exact_i64(value: object) -> int:
    if isinstance(value, bool):
        raise TypeError("Boolean is not I64")
    if isinstance(value, int):
        result = value
    elif isinstance(value, str):
        if not value or any(x not in "0123456789-" for x in value) or value.count("-") > 1:
            raise ValueError("I64 response has invalid integer spelling")
        result = int(value, 10)
        if str(result) != value:
            raise ValueError("I64 response is not canonical decimal")
    elif isinstance(value, float) and value.is_integer() and abs(value) <= 2**53:
        result = int(value)
    else:
        raise ValueError("Cannot losslessly compare I64 returned by MCP")
    if result < -(2**63) or result > (2**63 - 1):
        raise ValueError("I64 response outside signed 64-bit range")
    return result


def compare_native_clock_values(reply: dict, vector: dict) -> tuple[bool, str]:
    from .mcp_client import success
    if not success(reply) or reply.get("helperFailed") or reply.get("helperErrorCode") not in (None, 0):
        return False, "MCP/LabVIEW execution returned an error"
    values = reply.get("values") or {}
    next_item, valid_item = values.get("next_ms"), values.get("valid")
    if not isinstance(next_item, dict) or not isinstance(valid_item, dict):
        return False, "Missing typed LabVIEW output values"
    try:
        actual = _read_exact_i64(next_item.get("value"))
        expected = _read_exact_i64(vector["next_ms"])
    except (TypeError, ValueError, OverflowError) as exc:
        return False, str(exc)
    flag = valid_item.get("value")
    if not isinstance(flag, bool):
        return False, "Invalid Boolean output representation"
    if actual != expected or flag is not vector["valid"]:
        return False, f"Value/valid mismatch: got ({actual}, {flag}); expected ({expected}, {vector['valid']})"
    return True, "I64 and Boolean outputs agree exactly"


def test_native_sim_clock(exe: Path, backend: str = "grpc") -> dict:
    from .core import load_stage
    from .mcp_client import _with_server, unpack
    stage = load_stage("A01")
    if stage.get("component") != "Sim_Clock.vi" or len(stage.get("items", [])) != 1:
        raise ValueError("A01 stage is not the isolated Sim_Clock candidate")
    entry = stage["items"][0]
    vi = Path(entry["native_vi"]).resolve()
    out = (project_root() / "outputs/A01").resolve()
    if not vi.is_relative_to(out) or not vi.is_file():
        raise FileNotFoundError(f"Refusing missing/non-scratch Sim_Clock binary: {vi}")
    spec = read_json(project_root() / "baseline/tests/A01_Clock_Native_Vectors.json")
    vectors = spec["vectors"]

    async def runner(client):
        items = []
        for test in vectors:
            args = {"current_ms": str(test["current_ms"]),
                    "advance_ms": str(test["advance_ms"])}
            result = unpack(await client.call_tool("lvai_run_vi_and_read_values", {
                "viPath": str(vi), "inputsJson": json.dumps(args),
                "backend": backend, "timeoutSeconds": 45, "closePanelAfterRun": True,
            }))
            passed, reason = compare_native_clock_values(result, test)
            items.append({"test_id": test["id"], "focus": test["focus"],
                          "status": "PASS" if passed else "FAIL", "reason": reason,
                          "inputs": args,
                          "expected": {"next_ms": str(test["next_ms"]), "valid": test["valid"]},
                          "mcp": result})
        return {
            "batch": "A01", "component": "Sim_Clock.vi", "backend": backend,
            "test_results": items, "passes": sum(x["status"] == "PASS" for x in items),
            "failures": sum(x["status"] == "FAIL" for x in items),
            "not_run": len(vectors) - len(items),
            "native_test_count": len(vectors),
        }
    report = asyncio.run(_with_server(exe, runner))
    record("A01", "sim_clock_native", report)
    return report
