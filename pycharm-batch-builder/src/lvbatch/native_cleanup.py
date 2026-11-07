"""Fail-closed NI-style native block-diagram cleanup for scratch VIs.

The Zuehlke MCP layout tool uses LabVIEW VI Server to move objects and
clean wires and makes its own backup. We additionally snapshot the exact
generated binaries before mutation. Cleanup is NOT functional verification.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import shutil

from .core import load_stage, project_root, record
from .mcp_client import _with_server, unpack


def _targets(batch: str) -> list[Path]:
    batch = batch.upper()
    if batch not in {"U01", "U02", "U03", "U04", "A01"}:
        raise ValueError("Cleanup limited to explicit verified scratch batches")
    stage = load_stage(batch)
    root = (project_root() / "outputs" / batch).resolve()
    paths: list[Path] = []
    for item in stage["items"]:
        path = Path(item["native_vi"]).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.suffix.lower() != ".vi":
            raise ValueError(f"Missing or unsafe VI: {path}")
        if path in paths:
            raise ValueError(f"Duplicate VI destination: {path}")
        paths.append(path)
    if not paths:
        raise ValueError("Empty native stage")
    return paths


def cleanup_batch(batch: str, exe: Path, apply: bool = False) -> dict:
    """Dry-run and optionally apply layout to an explicitly selected scratch batch.

    Layout mutates saved VI diagram geometry only; all computation, connector
    and icon behavior must be retested with real LabVIEW after mutation.
    No automatically inferred physical I/O VIs are eligible.
    """
    batch = batch.upper()
    paths = _targets(batch)
    root = (project_root() / "outputs" / batch).resolve()
    backups = None
    if apply:
        name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backups = root / "cleanup_backups" / name
        backups.mkdir(parents=True, exist_ok=False)
        for vi in paths:
            shutil.copy2(vi, backups / vi.name)

    async def runner(client):
        rows = []
        for vi in paths:
            args = {"viPath": str(vi), "dryRun": True, "verify": True,
                    "render": False, "backend": "grpc", "timeoutSeconds": 240,
                    "routeFans": False}
            planned = unpack(await client.call_tool("lvai_layout_diagram", args))
            row = {"name": vi.name, "dry_run": planned, "applied": False}
            if planned.get("ok") is not True:
                row["error"] = "Native diagram dry-run refused or failed"
                rows.append(row)
                break
            if apply:
                args["dryRun"] = False
                applied = unpack(await client.call_tool("lvai_layout_diagram", args))
                row["result"] = applied
                row["applied"] = applied.get("ok") is True
                if not row["applied"]:
                    row["error"] = "Native diagram layout failed; backup retained"
                    rows.append(row)
                    break
            rows.append(row)
        ok = len(rows) == len(paths) and all(
            r["dry_run"].get("ok") is True and (not apply or r["applied"])
            for r in rows
        )
        return {"batch": batch, "mode": "APPLY" if apply else "DRY_RUN",
                "native_vis": len(paths), "backup_dir": str(backups) if backups else None,
                "ok": ok, "rows": rows,
                "post_cleanup_behavior_tests": "NOT_RUN" if apply else "NOT_APPLICABLE"}

    result = asyncio.run(_with_server(exe, runner))
    record(batch, "native_cleanup", result)
    return result
