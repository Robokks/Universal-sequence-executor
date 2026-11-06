"""A01 scalar synthetic plant step -- native-VI candidate, not whole plant.

The production Sim_VTU_Plant.vi will orchestrate THREE channels, limits, faults,
state lifetime, and I/O ownership. This intentionally tiny pure helper permits
native LabVIEW arithmetic validation without real hydraulic hardware.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from .core import check_aixml, get_batch, project_root, read_json, record, sha256
from .layout import assign_connector, composer_pane_directive, native_subdir

BATCH = "A01P"
NAME = "Sim_VTU_Plant_Step.vi"
VECTORS = "baseline/tests/A01_Plant_Step_Native_Vectors.json"
SOURCE = "baseline/aixml/app/Sim_VTU_Plant_Step.xml"


def plant_step_reference(current: float, target: float, dt_ms: float,
                         time_constant_ms: float) -> tuple[float, bool]:
    """Independent math reference; synthetic finite scalar inputs only."""
    values = (current, target, dt_ms, time_constant_ms)
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) for v in values):
        raise ValueError("A01 plant inputs must be finite numeric scalars")
    if dt_ms < 0 or time_constant_ms <= 0:
        return float(current), False
    alpha = -math.expm1(-dt_ms / time_constant_ms)
    return float(current) + alpha * (target - current), True


def prepare_plant_step(native_dir: str = "native_plant_v1",
                       root: Path | None = None) -> dict:
    base = root or project_root()
    if "Sim_VTU_Plant.vi" not in get_batch("A01", base)["vi_names"]:
        raise ValueError("A01 master manifest is missing Sim_VTU_Plant.vi")
    native_dir = native_subdir(native_dir)
    src = base / SOURCE
    aixml = ET.parse(src).getroot()
    if aixml.get("_name") != NAME:
        raise ValueError("Native helper source VI name differs from A01P contract")
    entry = {
        "inputs": [
            {"name": "current", "type": "double"},
            {"name": "target", "type": "double"},
            {"name": "dt_ms", "type": "double"},
            {"name": "time_constant_ms", "type": "double"},
        ],
        "outputs": [
            {"name": "next", "type": "double"},
            {"name": "valid", "type": "bool"},
        ],
    }
    pattern, mapping = assign_connector(aixml, entry, "compact", "4815")
    description = (
        "INTENT: Software-only one-channel first-order plant calculation. "
        "INPUTS: current and target (DBL finite, preclamped by caller), "
        "dt_ms and time_constant_ms (DBL). OUTPUTS: next (DBL), valid (Boolean). "
        "VALIDITY: dt >= 0 and tau > 0; if invalid next=current and valid=false. "
        "ALGORITHM: next=current+(1-exp(-dt/tau))*(target-current). "
        "STATE: owned by caller; never access real hydraulic equipment. "
        "REQUIREMENTS: A01-SIM-001, A01-SIM-004. "
        "Not full Sim_VTU_Plant.vi; caller must run three channels, enforce "
        "limits, handle stuck/saturation faults and persist state. "
        "Native LabVIEW behavior and exact connector binding require verification."
    )
    aixml.set("description", description)
    out = base / "outputs" / BATCH
    stage = out / "step_v1" / "staged_aixml"
    stage.mkdir(parents=True, exist_ok=True)
    target = stage / "Sim_VTU_Plant_Step.xml"
    ET.ElementTree(aixml).write(target, encoding="utf-8", xml_declaration=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(composer_pane_directive(pattern))
    validation = check_aixml(target, NAME)
    if not validation["ok"]:
        raise ValueError("Invalid staged AIXML: " + "; ".join(validation["issues"]))
    spec = read_json(base / VECTORS)
    if spec.get("vi") != NAME or len(spec.get("vectors", [])) < 12:
        raise ValueError("Missing or incomplete A01P native test vectors")
    docpath = out / "step_v1" / "Sim_VTU_Plant_Step_DESIGN.md"
    docpath.write_text(
        "# Sim_VTU_Plant_Step.vi -- A01 pure scalar helper\n\n"
        "**Not the complete 3-channel Sim_VTU_Plant.vi**.\n\n"
        "Purpose: apply an independent first-order response to one synthetic "
        "pressure, flow or lever channel. Repeat per channel in a future stateful "
        "Sim_VTU_Plant caller. Do not connect to physical I/O.\n\n"
        "Inputs: current, target (preclamped finite DBL), dt_ms (DBL nonnegative), "
        "time_constant_ms (DBL positive).\n\n"
        "Outputs: next (DBL), valid (Boolean).\n\n"
        "Algorithm: next = current + (1-exp(-dt_ms/tau))*(target-current). "
        "On invalid dt or tau: next=current, valid=false.\n\n"
        "Finite and preclamped current/target are **caller preconditions**. "
        "Input NaN/Inf behavior is NOT native-accepted. "
        "Double math uses 1-exp(-x), whereas Python reference uses -expm1(-x). "
        "Small dt can lose relative precision; acceptance vectors specify tolerance.\n\n"
        f"Connector pane: {pattern}; indices: {mapping}.\n\n"
        "Caller responsibilities: three channels; sample timestamps; explicit "
        "state lifetime; half-limit saturation; frozen response when stuck; "
        "fault-time splitting; safe simulation-only transport.\n\n"
        f"Native vector count: {len(spec['vectors'])}. "
        "VI executable state, functional execution and pane audit: **NOT RUN**.\n",
        encoding="utf-8",
    )
    item = {
        "name": NAME,
        "xml": str(target),
        "native_vi": str(out / native_dir / NAME),
        "sha256": sha256(target),
        "tests": [row["id"] for row in spec["vectors"]],
        "inputs": entry["inputs"],
        "outputs": entry["outputs"],
        "connector_pattern": pattern,
        "connector_map": mapping,
    }
    manifest = {
        "batch": BATCH,
        "component": NAME,
        "source_application": "A01/Sim_VTU_Plant.vi",
        "pane": "4815",
        "layout": "compact",
        "native_dir": native_dir,
        "native_vis_staged": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "state": "AIXML PREPARED; native LabVIEW NOT RUN",
        "items": [item],
    }
    (out / "stage_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def compare_native_plant(reply: dict, vector: dict) -> tuple[bool, str]:
    """Require real typed MCP outputs, never treat missing evidence as PASS."""
    from .mcp_client import success
    if not success(reply) or reply.get("helperFailed") or reply.get("helperErrorCode") not in (None, 0):
        return False, "MCP/LabVIEW returned error"
    values = reply.get("values")
    if not isinstance(values, dict):
        return False, "Missing typed values"
    nxt = values.get("next")
    valid = values.get("valid")
    if not isinstance(nxt, dict) or not isinstance(valid, dict):
        return False, "Missing named output terminals"
    actual = nxt.get("value")
    flag = valid.get("value")
    if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual):
        return False, "Next value is not a finite numeric scalar"
    if not isinstance(flag, bool):
        return False, "valid is not native Boolean"
    if flag is not vector["valid"]:
        return False, f"valid mismatch: {flag} != {vector['valid']}"
    if not math.isclose(actual, vector["next"], rel_tol=1e-8, abs_tol=1e-8):
        return False, f"next mismatch: {actual} != {vector['next']}"
    return True, "Native numeric and Boolean outputs match independent reference"


def test_native_plant_step(exe: Path, backend: str = "grpc") -> dict:
    from .core import load_stage
    from .mcp_client import _with_server, unpack
    stage = load_stage(BATCH)
    if stage.get("component") != NAME or len(stage.get("items", [])) != 1:
        raise ValueError("A01P stage does not point to only the plant helper")
    vi = Path(stage["items"][0]["native_vi"]).resolve()
    out = (project_root() / "outputs" / BATCH).resolve()
    if not vi.is_relative_to(out) or not vi.is_file():
        raise FileNotFoundError("Missing or non-scratch native plant helper VI")
    vectors = read_json(project_root() / VECTORS)["vectors"]

    async def runner(client):
        rows = []
        for vector in vectors:
            inputs = {key: str(vector[key]) for key in
                      ("current", "target", "dt_ms", "time_constant_ms")}
            reply = unpack(await client.call_tool("lvai_run_vi_and_read_values", {
                "viPath": str(vi), "inputsJson": json.dumps(inputs),
                "backend": backend, "timeoutSeconds": 45,
                "closePanelAfterRun": True,
            }))
            passed, reason = compare_native_plant(reply, vector)
            rows.append({
                "test_id": vector["id"],
                "status": "PASS" if passed else "FAIL",
                "reason": reason,
                "inputs": inputs,
                "expected": {"next": vector["next"], "valid": vector["valid"]},
                "mcp": reply,
            })
        return {
            "batch": BATCH,
            "component": NAME,
            "backend": backend,
            "native_test_count": len(vectors),
            "passes": sum(r["status"] == "PASS" for r in rows),
            "failures": sum(r["status"] == "FAIL" for r in rows),
            "not_run": 0,
            "test_results": rows,
        }

    report = asyncio.run(_with_server(exe, runner))
    record(BATCH, "sim_plant_step_native", report)
    return report
