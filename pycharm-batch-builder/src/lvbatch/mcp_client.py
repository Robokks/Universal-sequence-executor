"""Direct MCP orchestration: deliberately sequential and scratch-only.

Requires pip install -e '.[mcp]'. This is not a substitute for reviewing native VIs.
"""
from __future__ import annotations
import asyncio
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .core import load_stage, get_tests, record, project_root
from .icon_catalog import icon_spec, BANNER_COLORS


def unpack(response: Any) -> dict:
    """Unwrap JSON tools returned through MCP text responses."""
    for part in getattr(response, "content", []):
        if getattr(part, "type", None) == "text":
            try:
                data = json.loads(part.text)
                if isinstance(data, dict):
                    return data
            except (TypeError, json.JSONDecodeError):
                pass
    return {"unparsed_response": str(response), "ok": False}


def success(data: dict) -> bool:
    if "ok" in data:
        return data["ok"] is True
    if "errorCode" in data:
        return data["errorCode"] == 0
    return False


def mcp_stdio_env() -> dict[str, str] | None:
    """Pass the separately provisioned pylabview bundle to the MCP subprocess.

    The MCP stdio transport deliberately inherits only an allowlisted set of
    environment variables. A parent-shell LABVIEWMCP_PYLABVIEW must therefore
    be forwarded explicitly; env=None silently drops it.
    """
    configured = os.environ.get("LABVIEWMCP_PYLABVIEW", "").strip()
    if not configured:
        return None
    bundle = Path(configured).expanduser()
    if not (bundle / "python.exe").is_file():
        raise FileNotFoundError(
            f"LABVIEWMCP_PYLABVIEW has no python.exe at: {bundle}"
        )
    return {"LABVIEWMCP_PYLABVIEW": str(bundle)}


async def _with_server(exe: Path, fn):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    if not exe.is_file():
        raise FileNotFoundError(f"LabVIEW MCP executable missing: {exe}")
    params = StdioServerParameters(command=str(exe), args=[], env=mcp_stdio_env())
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            return await fn(client)


def generate(batch: str, exe: Path, backend: str = "grpc", pane: str = "4815") -> dict:
    """Create VIs one at a time and fail closed. Target must be new scratch output.

    The Zuehlke MCP tools are mutating. No existing .vi may be overwritten.
    """
    stage = load_stage(batch)
    if stage["pane"] != pane:
        raise ValueError("Pane mismatch: prepare a fresh stage with the selected pane")
    if backend not in ("grpc", "pylabview"):
        raise ValueError("Select grpc or pylabview explicitly; no implicit fallback")

    async def runner(client):
        status = unpack(await client.call_tool("lvai_status", {}))
        items = []
        for entry in stage["items"]:
            destination = Path(entry["native_vi"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                items.append({"name": entry["name"], "ok": False,
                              "error": "Refused overwrite of existing VI"})
                break
            check = unpack(await client.call_tool("lvai_check_aixml", {
                "aiXmlFilePath": entry["xml"], "fix": False, "newVi": True}))
            if check.get("errors") or check.get("ok") is False:
                items.append({"name": entry["name"], "ok": False, "check": check})
                break
            # For offline composition use the separately documented direct pylabview route.
            # lvai_generate_vi on pylabview is partly dependent on a running LabVIEW for
            # execution-state/pane checks, so do not treat offline output as native-pass.
            result = unpack(await client.call_tool("lvai_generate_vi", {
                "aiXmlFilePath": entry["xml"], "viPath": str(destination),
                "panePattern": int(entry.get("connector_pattern", pane)), "backend": backend,
                "openVI": False, "measurePane": True, "measureDiagram": False,
                "cleanUpDiagram": True, "cleanUpPanel": True,
                "timeoutSeconds": 180}))
            items.append({"name": entry["name"], "ok": success(result), "result": result,
                          "vi_exists": destination.exists()})
            if not success(result) or not destination.exists():
                break
        return {"mcp_status": status, "batch": batch, "backend": backend,
                "kind": "native-generation-with-compilation-gate", "results": items,
                "ok": len(items) == len(stage["items"]) and all(x["ok"] for x in items)}
    result = asyncio.run(_with_server(exe, runner))
    record(batch, "mcp_generation", result)
    return result



def set_batch_icons(batch: str, exe: Path, backend: str = "grpc") -> dict:
    """Apply per-VI 32x32 icons to generated scratch VIs, with local backups.

    AIXML composition cannot encode icons. Icons are a deliberately separate
    finishing step, after native tests, because recomposition erases them.
    """
    stage = load_stage(batch)
    root = (project_root() / "outputs" / batch.upper()).resolve()
    items = stage["items"]
    icons = []
    for item in items:
        vi = Path(item["native_vi"]).resolve()
        if not vi.is_relative_to(root) or not vi.is_file():
            raise ValueError(f"Refusing to modify a missing or non-scratch VI: {vi}")
        icons.append({"viPath": str(vi), **icon_spec(vi.stem)})

    # Snapshot ALL native VI files before any icon mutation, for rollback.
    folder = root / "icon_backups" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True, exist_ok=False)
    for item in items:
        vi = Path(item["native_vi"]).resolve()
        shutil.copy2(vi, folder / vi.name)

    async def runner(client):
        response = await client.call_tool("lvai_set_vi_icon", {
            "iconsJson": json.dumps(icons),
            "backend": backend,
            "bannerColor": BANNER_COLORS.get(batch.upper(), "006699"),
            "backgroundColor": "FFFFFF",
            "borderColor": "000000",
            "timeoutSeconds": 300,
        })
        answer = unpack(response)
        return {
            "batch": batch.upper(),
            "backup_dir": str(folder),
            "requested": len(icons),
            "ok": answer.get("ok") is True and not answer.get("failed"),
            "response": answer,
        }

    result = asyncio.run(_with_server(exe, runner))
    record(batch, "native_icons", result)
    return result


def audit_batch_panes(batch: str, exe: Path, backend: str = "grpc") -> dict:
    """Record actual connector geometry from the LabVIEW MCP read-only tool.

    A functional VI test does not prove a usable connector pane. The raw
    geometry/style verdict is preserved for a reviewer; it is not silently
    converted into a 'passed' result.
    """
    stage = load_stage(batch)
    root = (project_root() / "outputs" / batch.upper()).resolve()

    async def runner(client):
        rows = []
        for item in stage["items"]:
            vi = Path(item["native_vi"]).resolve()
            if not vi.is_relative_to(root) or not vi.is_file():
                rows.append({"name": item["name"], "error": "Missing or unsafe VI path"})
                continue
            response = await client.call_tool("lvai_connector_pane", {
                "viPath": str(vi), "backend": backend, "timeoutSeconds": 120
            })
            text_items = [part.text for part in getattr(response, "content", [])
                          if getattr(part, "type", None) == "text"]
            rows.append({
                "name": item["name"],
                "expected_pattern": item.get("connector_pattern"),
                "expected_connectors": item.get("connector_map", {}),
                "tool_error": bool(getattr(response, "isError", False)),
                "raw_observation": "\n".join(text_items),
            })
        return {"batch": batch.upper(), "audit_only": True, "items": rows}

    result = asyncio.run(_with_server(exe, runner))
    record(batch, "native_panes", result)
    return result


def _extract_value(values: dict, label: str):
    val = values.get(label)
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return None


def _equal(actual, expected) -> bool:
    if actual is None:
        return False
    if isinstance(expected, bool):
        return isinstance(actual, bool) and actual == expected
    if isinstance(expected, (float, int)) and not isinstance(expected, bool):
        if isinstance(actual, bool):
            return False
        try:
            return abs(float(actual) - float(expected)) <= 1e-8 * max(1, abs(float(expected)))
        except (TypeError, ValueError):
            return False
    return actual == expected


def native_test(batch: str, exe: Path, backend: str = "grpc") -> dict:
    stage = load_stage(batch)
    examples = get_tests()
    names = {Path(ent["native_vi"]).stem for ent in stage["items"]}
    covered = {e["VI Name"] for e in examples}
    if not names or not names.issubset(covered):
        raise ValueError(
            "Generic mcp-test has no test vectors for some staged VIs. "
            "For A01 Sim_Clock, use: python -m lvbatch a01-clock-test "
            '--exe "C:\\LabVIEWTools\\labview-mcp-v2.4.1\\bin\\LabVIEWMCP.exe"'
        )
    async def runner(client):
        rows = []
        for entry in stage["items"]:
            vi = Path(entry["native_vi"])
            if not vi.is_file():
                rows.append({"name": entry["name"], "status": "NOT_RUN", "reason": "VI not generated"})
                continue
            for tc in [x for x in examples if x["VI Name"] == vi.stem]:
                if len(tc["inputs"]) != len(entry["inputs"]) or len(tc["expected"]) != len(entry["outputs"]):
                    rows.append({"test_id": tc["Test ID"], "status": "FAIL", "error": "contract mismatch"})
                    continue
                inputs = {x["name"]: str(v).lower() if isinstance(v,bool) else str(v)
                          for x, v in zip(entry["inputs"], tc["inputs"])}
                reply = unpack(await client.call_tool("lvai_run_vi_and_read_values", {
                    "viPath": str(vi), "inputsJson": json.dumps(inputs),
                    "backend": backend, "timeoutSeconds": 45, "closePanelAfterRun": True}))
                values = reply.get("values") or {}
                actual = [_extract_value(values, port["name"]) for port in entry["outputs"]]
                passed = success(reply) and reply.get("helperErrorCode") in (None, 0) and all(
                    _equal(a, e) for a, e in zip(actual, tc["expected"]))
                rows.append({"test_id": tc["Test ID"], "vi": vi.name,
                             "status": "PASS" if passed else "FAIL", "inputs": inputs,
                             "actual": actual, "expected": tc["expected"], "mcp": reply})
        return {"batch": batch, "test_results": rows, "passes": sum(r["status"] == "PASS" for r in rows),
                "failures": sum(r["status"] == "FAIL" for r in rows),
                "not_run": sum(r["status"] == "NOT_RUN" for r in rows)}
    output = asyncio.run(_with_server(exe, runner))
    record(batch, "native_behavior", output)
    return output
