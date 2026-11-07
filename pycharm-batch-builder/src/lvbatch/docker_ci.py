"""NI headless LabVIEW container MassCompile, for verification only.

Never runs implicitly: Docker is optional, big, and requires matching VI version/toolkits.
The Docker image includes NI LabVIEW, not Zuehlke's MCP service.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from .core import load_stage, record


def masscompile(batch: str, image: str = "nationalinstruments/labview:latest-linux",
                lvpath: str = "/usr/local/natinst/LabVIEW-2026-64/labview",
                timeout: int = 1800) -> dict:
    stage = load_stage(batch)
    # Avoid injection of shell fragments in image/path; command is a fixed argument list.
    if image != "nationalinstruments/labview:latest-linux":
        raise ValueError("Only the reviewed NI 2026 latest-linux image is configured")
    native = Path(stage["items"][0]["native_vi"]).parent
    if not native.exists() or any(not Path(x["native_vi"]).is_file() for x in stage["items"]):
        raise FileNotFoundError("All target VIs must first exist in scratch native/ folder")
    # Docker Desktop on Windows should be in Linux-containers mode.
    argv = ["docker", "run", "--rm", "--network", "none", "-v", f"{native.resolve()}:/workspace",
            image, "LabVIEWCLI", "-LogToConsole", "TRUE", "-OperationName", "MassCompile",
            "-DirectoryToCompile", "/workspace", "-LabVIEWPath", lvpath, "-Headless"]
    try:
        result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=timeout, check=False)
        verdict = {"batch": batch, "kind": "NI LabVIEWCLI MassCompile", "exit_code": result.returncode,
                   "status": "PASS" if result.returncode == 0 else "FAIL",
                   "stdout_tail": result.stdout[-20000:], "stderr_tail": result.stderr[-12000:],
                   "notes": "MassCompile is not behavior testing or cRIO safety verification"}
    except (FileNotFoundError, subprocess.TimeoutExpired) as err:
        verdict = {"batch": batch, "kind": "NI LabVIEWCLI MassCompile", "status": "NOT_RUN",
                   "error": str(err)}
    record(batch, "docker_masscompile", verdict)
    return verdict
