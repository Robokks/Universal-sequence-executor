"""Direct MCP orchestration: deliberately sequential and scratch-only.

Requires pip install -e '.[mcp]'. This is not a substitute for reviewing native VIs.
"""
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import Any
from .core import load_stage, get_tests, record


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


async def _with_server(exe: Path, fn):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    if not exe.is_file():
        raise FileNotFoundError(f"LabVIEW MCP executable missing: {exe}")
    params = StdioServerParameters(command=str(exe), args=[], env=None)
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
                "panePattern": int(pane), "backend": backend,
                "openVI": False, "measurePane": True, "measureDiagram": False,
                "cleanUpDiagram": False, "cleanUpPanel": False,
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
