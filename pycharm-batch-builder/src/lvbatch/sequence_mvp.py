"""Minimal vertical-slice sequence engine: JSON -> simulated feedback -> verdicts -> evidence.

No physical drivers or controls. Optionally evaluate two actual native U02
LabVIEW VIs through the already-working NI gRPC MCP service. A mock backend
exists for local development and is never reported as native verification.
"""
from __future__ import annotations

import asyncio
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import threading
from typing import Any, Callable, Protocol
from uuid import uuid4

from .core import project_root
from .sim_reference import Command, SimSession

PLAN_FILE = project_root() / "baseline/demo_sequence.json"


@dataclass(frozen=True)
class Step:
    name: str
    target_bar: float
    tolerance_bar: float
    timeout_ms: int
    dwell_ms: int
    period_ms: int


@dataclass(frozen=True)
class Plan:
    name: str
    steps: tuple[Step, ...]


def load_plan(path: Path | str = PLAN_FILE) -> Plan:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"mode", "name", "steps"}:
        raise ValueError("Invalid plan schema")
    if data["mode"] != "SIMULATION_ONLY":
        raise ValueError("Physical mode is forbidden")
    name = data["name"]
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
        raise ValueError("Invalid sequence name")
    raw = data["steps"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= 100:
        raise ValueError("A sequence requires 1..100 steps")
    result = []
    for i, row in enumerate(raw, 1):
        if not isinstance(row, dict) or set(row) != {
                "name", "target_bar", "tolerance_bar", "timeout_ms", "dwell_ms", "period_ms"}:
            raise ValueError(f"Step {i}: invalid fields")
        label = row["name"]
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
            raise ValueError(f"Step {i}: invalid name")
        for key, minimum, maximum in (
                ("target_bar", 0, 100), ("tolerance_bar", 0.01, 20)):
            v = row[key]
            if isinstance(v, bool) or not isinstance(v, (float, int)):
                raise ValueError(f"Step {i}: {key} must be numeric")
            if not math.isfinite(v) or not minimum <= v <= maximum:
                raise ValueError(f"Step {i}: {key} out of simulation range")
        for key, low, high in (
                ("timeout_ms", 100, 60000), ("dwell_ms", 0, 60000),
                ("period_ms", 25, 500)):
            v = row[key]
            if isinstance(v, bool) or not isinstance(v, int) or not low <= v <= high:
                raise ValueError(f"Step {i}: {key} out of range")
        if (row["dwell_ms"] > row["timeout_ms"] or
                row["timeout_ms"] % row["period_ms"] != 0 or
                row["dwell_ms"] % row["period_ms"] != 0):
            raise ValueError(f"Step {i}: incompatible dwell/timeout/period")
        result.append(Step(label.strip(), float(row["target_bar"]),
                           float(row["tolerance_bar"]), row["timeout_ms"],
                           row["dwell_ms"], row["period_ms"]))
    return Plan(name.strip(), tuple(result))


class Comparator(Protocol):
    async def within(self, actual: float, target: float, tolerance: float) -> bool: ...
    async def timed_out(self, elapsed: int, timeout: int) -> bool: ...


class MockComparator:
    async def within(self, actual: float, target: float, tolerance: float) -> bool:
        return abs(actual - target) <= tolerance

    async def timed_out(self, elapsed: int, timeout: int) -> bool:
        return elapsed >= timeout


class LabviewComparator:
    """Invoke real U02 binary VIs. Missing typed Boolean output means ERROR."""
    def __init__(self, client: Any, native_dir: Path):
        from .core import project_root
        directory = native_dir.resolve()
        expected_root = (project_root() / "outputs" / "U02").resolve()
        if not directory.is_relative_to(expected_root):
            raise ValueError("Native VIs must be inside U02 scratch outputs")
        self.client = client
        self.files = {}
        for name in ("UE_Within_Tolerance.vi", "UE_Timeout_Reached.vi"):
            p = directory / name
            if not p.is_file():
                raise FileNotFoundError(f"Missing real LabVIEW VI: {p}")
            self.files[name] = str(p)

    async def _run(self, vi: str, inputs: dict, output_name: str) -> bool:
        from .mcp_client import unpack
        result = unpack(await self.client.call_tool("lvai_run_vi_and_read_values", {
            "viPath": self.files[vi],
            "inputsJson": json.dumps({k: str(v) for k, v in inputs.items()}),
            "backend": "grpc", "timeoutSeconds": 45, "closePanelAfterRun": True
        }))
        terminal = (result.get("values") or {}).get(output_name)
        if (result.get("errorCode") != 0 or result.get("helperFailed") or
                result.get("helperErrorCode") not in (None, 0) or
                not isinstance(terminal, dict) or
                terminal.get("type") != "Boolean" or
                not isinstance(terminal.get("value"), bool)):
            raise RuntimeError(f"LabVIEW VI verification failed: {vi}: {result}")
        return terminal["value"]

    async def within(self, actual: float, target: float, tolerance: float) -> bool:
        return await self._run("UE_Within_Tolerance.vi",
                               {"actual": actual, "target": target,
                                "tolerance": tolerance}, "within_tolerance")

    async def timed_out(self, elapsed: int, timeout: int) -> bool:
        return await self._run("UE_Timeout_Reached.vi",
                               {"elapsed_ms": elapsed, "threshold_ms": timeout}, "reached")


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


async def execute(plan: Plan, comparator: Comparator, backend: str = "mock", *,
                  stop: threading.Event | None = None,
                  pause: threading.Event | None = None,
                  emit: Callable[[dict], None] | None = None,
                  delay_s: float = 0) -> dict:
    if backend not in ("mock", "grpc"):
        raise ValueError("Unrecognized comparator backend")
    if not 0 <= delay_s <= 1:
        raise ValueError("Invalid display delay")
    run_id = "MVP-" + uuid4().hex
    record = {"run_id": run_id, "plan": plan.name, "mode": "SIMULATION_ONLY",
              "backend": backend, "native_decisions": backend == "grpc",
              "started_at": _stamp(), "ended_at": None, "status": "RUNNING",
              "steps": [], "events": []}
    sim = SimSession(run_id)
    stop = stop or threading.Event()
    pause = pause or threading.Event()

    def publish(kind: str, step_idx: int, step: str, virtual_ms: int, **details):
        e = {"at": _stamp(), "run_id": run_id, "step_index": step_idx,
             "step_name": step, "type": kind, "virtual_ms": virtual_ms,
             "synthetic": True, **details}
        record["events"].append(e)
        if emit:
            emit(e)

    publish("RUN_STARTED", 0, "", sim.clock.now_ms, status="RUNNING")
    try:
        for index, step in enumerate(plan.steps, 1):
            if stop.is_set():
                record["status"] = "STOPPED"
                break
            start_ms = sim.clock.now_ms
            ack = sim.submit(Command("CMD-" + str(index), sim.run_id,
                                     step.target_bar, 0, 0))
            if ack["type"] != "ACCEPTED":
                raise RuntimeError("Simulated command was rejected")
            publish("STEP_STARTED", index, step.name, start_ms,
                    target_bar=step.target_bar, status="RUNNING")
            dwell_start = None
            result = "TIMEOUT"
            while True:
                if stop.is_set():
                    result = "STOPPED"
                    break
                while pause.is_set() and not stop.is_set():
                    await asyncio.sleep(0.05)
                if stop.is_set():
                    result = "STOPPED"
                    break
                sim.advance(step.period_ms)
                elapsed = sim.clock.now_ms - start_ms
                reading = sim.feedback()
                if reading["quality"] != "GOOD":
                    result = "INVALID_FEEDBACK"
                    break
                actual = reading["pressure_bar"]
                inside = await comparator.within(actual, step.target_bar,
                                                 step.tolerance_bar)
                if inside:
                    if dwell_start is None:
                        dwell_start = sim.clock.now_ms
                    if sim.clock.now_ms - dwell_start >= step.dwell_ms:
                        result = "PASS"
                else:
                    dwell_start = None
                publish("SAMPLE", index, step.name, sim.clock.now_ms,
                        actual_bar=actual, target_bar=step.target_bar,
                        status="RUNNING", quality=reading["quality"])
                # Evaluate timeout AFTER dwell so an exact-boundary success passes.
                if result == "PASS":
                    break
                if await comparator.timed_out(elapsed, step.timeout_ms):
                    result = "TIMEOUT"
                    break
                if delay_s:
                    await asyncio.sleep(delay_s)
            entry = {"index": index, "name": step.name,
                     "status": result, "elapsed_ms": sim.clock.now_ms - start_ms}
            record["steps"].append(entry)
            publish("STEP_FINISHED", index, step.name, sim.clock.now_ms, status=result)
            if result != "PASS":
                record["status"] = "STOPPED" if result == "STOPPED" else "FAIL"
                break
        else:
            record["status"] = "PASS"
    except Exception as exc:
        record["status"] = "ERROR"
        publish("RUN_ERROR", 0, "", sim.clock.now_ms, status="ERROR",
                detail=f"{type(exc).__name__}: {exc}")
    record["ended_at"] = _stamp()
    publish("RUN_FINISHED", 0, "", sim.clock.now_ms, status=record["status"])
    return record


def save_results(record: dict, directory: Path | None = None) -> tuple[Path, Path]:
    folder = directory or project_root() / "outputs" / "MVP"
    folder.mkdir(parents=True, exist_ok=True)
    name = record["run_id"]
    if not name.startswith("MVP-") or not name[4:].isalnum():
        raise ValueError("Invalid run ID")
    json_path = folder / (name + ".json")
    csv_path = folder / (name + "_events.csv")
    with json_path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
    with csv_path.open("x", encoding="utf-8", newline="") as stream:
        fields = ["at", "run_id", "step_index", "step_name", "type",
                  "virtual_ms", "status", "actual_bar", "target_bar", "detail"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(record["events"])
    return json_path, csv_path


async def run_file(plan_path: Path, backend: str = "mock",
                   exe: Path | None = None, vi_dir: Path | None = None,
                   **kwargs) -> dict:
    plan = load_plan(plan_path)
    if backend == "mock":
        return await execute(plan, MockComparator(), "mock", **kwargs)
    if backend != "grpc" or exe is None or vi_dir is None:
        raise ValueError("gRPC mode requires both --exe and --native-dir")
    from .mcp_client import _with_server
    async def runner(client):
        comparator = LabviewComparator(client, vi_dir)
        return await execute(plan, comparator, "grpc", **kwargs)
    return await _with_server(exe, runner)
