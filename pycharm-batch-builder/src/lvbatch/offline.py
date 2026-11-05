"""Experimental offline composer (Zuehlke's bundled pylabview, not pip install).

Direct composition is possible without LabVIEW; is NOT evidence of compilation.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from .core import load_stage, record


def compose(batch: str, repo: Path, target_year: int = 2026) -> dict:
    if sys.platform != "win32":
        raise RuntimeError("Official bundled pylabview composer route is Windows-oriented")
    if target_year not in (2025, 2026):
        raise ValueError("Allowed target year: 2025, 2026")
    path = repo.resolve()
    script = path / "scripts/aixml-pylabview/aixml2vi.py"
    runtime = path / "tools/pylabview/runtime/python.exe"
    app = path / "tools/pylabview/runtime/app/pylabview/readRSRC.py"
    parts = path / "scripts/aixml-pylabview/parts"
    if not (script.is_file() and runtime.is_file() and app.is_file() and parts.is_dir()):
        raise FileNotFoundError("Zuehlke source checkout needs the provisioned isolated pylabview runtime and parts. "
                                "See docs/PYLABVIEW_OFFLINE.md; never substitute a generic pip package.")
    stage = load_stage(batch)
    rows = []
    for ent in stage["items"]:
        dst = Path(ent["native_vi"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            rows.append({"name": ent["name"], "status": "REFUSED_OVERWRITE"})
            break
        argv = [str(runtime), str(script), "--lv-version", str(target_year - 2000), ent["xml"], str(dst)]
        try:
            result = subprocess.run(argv, cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    encoding="utf-8", errors="replace", timeout=180, check=False)
            status = "COMPOSED_UNVERIFIED" if result.returncode == 0 and dst.exists() else "FAIL"
            rows.append({"name": ent["name"], "status": status,
                         "returncode": result.returncode, "stdout": result.stdout[-2000:],
                         "stderr": result.stderr[-2000:]})
            if status == "FAIL":
                break
        except subprocess.TimeoutExpired:
            rows.append({"name": ent["name"], "status": "TIMEOUT"})
            break
    output = {"batch": batch, "mode": "NO LABVIEW: offline pylabview composition",
              "native_compilation": "NOT_RUN", "items": rows,
              "complete": len(rows) == len(stage["items"]) and all(
                   r["status"] == "COMPOSED_UNVERIFIED" for r in rows)}
    record(batch, "offline_compose", output)
    return output
