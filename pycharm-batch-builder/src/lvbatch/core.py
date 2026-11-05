"""Batch selection, VI documentation, offline checks, staging and audit records.

Never mutate original baseline files. Native VI generation always targets outputs/.
No safety-rated or hardware control code is executed by this package.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_batches(root: Path | None = None) -> dict:
    return read_json((root or project_root()) / "baseline/batch_manifest.json")


def get_batch(batch_id: str, root: Path | None = None) -> dict:
    for row in load_batches(root)["batches"]:
        if row["batch"].upper() == batch_id.upper():
            return row
    raise ValueError(f"Unknown batch: {batch_id}")


def load_catalog(root: Path | None = None, pane: str = "4815") -> dict:
    data = read_json((root or project_root()) / "baseline/manifest.json")
    return {row["name"]: row for row in data["definitions"] if row["pane"] == pane}


def get_tests(root: Path | None = None) -> list[dict]:
    path = (root or project_root()) / "baseline/tests/AIXML_Test_Cases.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return [{**row, "inputs": json.loads(row["Input Values"]),
             "expected": json.loads(row["Expected Outputs"])} for row in rows]


def vi_intent(entry: dict, old_description: str) -> str:
    """This becomes the VI Properties > Documentation description through AIXML.

    Keep detailed notes in the sibling .md to avoid inflating a VI description.
    """
    inputs = ", ".join(f"{x['name']} ({x['type']})" for x in entry["inputs"])
    outputs = ", ".join(f"{x['name']} ({x['type']})" for x in entry["outputs"])
    return (f"INTENT: {old_description.strip()}. INPUTS: {inputs}. OUTPUTS: {outputs}. "
            f"DESIGN CONSTRAINT: {entry['notes']} REQUIREMENTS: "
            f"{', '.join(entry['requirements'])}. No physical hardware side effects. "
            "Acceptance requires native LabVIEW compilation and behavioral testing.")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_aixml(path: Path, expected_name: str | None = None) -> dict:
    """Supplemental safe syntactic checks, NOT native LabVIEW type checking."""
    result = {"source": str(path), "issues": [], "warnings": []}
    try:
        raw = path.read_text(encoding="utf-8-sig")
        if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", raw, re.I):
            raise ValueError("External entities/DTD forbidden")
        root = ET.fromstring(raw)
        if root.tag != "VI":
            result["issues"].append("AIXML root must be <VI>")
        if expected_name and root.get("_name") != expected_name:
            result["issues"].append("VI name does not match manifest")
        if not root.get("description"):
            result["issues"].append("Missing mandatory VI intent description")
        uids = {}
        for el in root.iter():
            uid = el.get("uid")
            if uid:
                if uid in uids:
                    result["issues"].append(f"Duplicate uid {uid}")
                uids[uid] = el
        valid_nets = set()
        for el in root.iter():
            for item in (el.get("outputs") or "").split(","):
                if ":" in item and item.split(":", 1)[1]:
                    valid_nets.add(item.split(":", 1)[1])
        for el in root.iter():
            uid = el.get("uid")
            par = el.get("uid_parent")
            if par not in (None, "root") and par not in uids:
                result["issues"].append(f"Unknown uid_parent {par} of {uid}")
            if el.tag in ("Control", "Indicator", "Constant") and el.get("value") is None:
                result["issues"].append(f"Missing value on {el.tag} {uid}")
            for item in (el.get("inputs") or "").split(","):
                if ":" in item:
                    net = item.split(":", 1)[1]
                    if net and net not in valid_nets:
                        result["issues"].append(f"Missing net source: {net}")
    except (ET.ParseError, OSError, UnicodeError, ValueError) as exc:
        result["issues"].append(f"Cannot parse AIXML: {exc}")
    result["ok"] = not result["issues"]
    return result


def prepare_batch(batch_id: str, pane: str = "4815", root: Path | None = None) -> dict:
    root = root or project_root()
    batch = get_batch(batch_id, root)
    catalog = load_catalog(root, pane)
    out = root / "outputs" / batch_id.upper()
    staged = out / "staged_aixml"
    docs = out / "vi_docs"
    staged.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in batch["vi_names"]:
        stem = Path(name).stem
        if stem not in catalog:
            raise ValueError(f"No AIXML available for {name}. This batch needs a new design.")
        entry = catalog[stem]
        source = root / "baseline" / entry["path"]
        current = ET.parse(source).getroot()
        old_description = current.get("description") or ""
        doc = vi_intent(entry, old_description)
        current.set("description", doc)
        target = staged / f"{stem}.xml"
        ET.ElementTree(current).write(target, encoding="utf-8", xml_declaration=True)
        if not check_aixml(target, name)["ok"]:
            raise ValueError(f"Offline AIXML check failed for {target}")
        examples = [t for t in get_tests(root) if t["VI Name"] == stem]
        txt = [f"# {name}", "", "## VI intent", old_description, "", "## LabVIEW VI description", doc,
               "", "## Input connector terminals", ""]
        txt += [f"- `{x['name']}` — `{x['type']}`" for x in entry["inputs"]]
        txt += ["", "## Output connector terminals", ""]
        txt += [f"- `{x['name']}` — `{x['type']}`" for x in entry["outputs"]]
        txt += ["", "## Engineering assumptions / error handling", entry["notes"], "",
                "## Traceability", ", ".join(entry["requirements"]), "",
                "## Test cases", "", "| Test ID | Inputs | Expected outputs |", "|---|---|---|"]
        txt += [f"| {t['Test ID']} | `{t['inputs']}` | `{t['expected']}` |" for t in examples]
        txt += ["", "## Verification gates", "- Offline AIXML structure checked",
                "- Native LabVIEW executable state: **NOT RUN**", "- Native behavior tests: **NOT RUN**",
                "- Container MassCompile: **NOT RUN**", "- Hardware acceptance: **NOT RUN**", ""]
        (docs / f"{stem}.md").write_text("\n".join(txt), encoding="utf-8")
        rows.append({"name": name, "xml": str(target), "native_vi": str(out / "native" / name),
                     "sha256": sha256(target), "tests": [x["Test ID"] for x in examples],
                     "inputs": entry["inputs"], "outputs": entry["outputs"]})
    payload = {"batch": batch_id.upper(), "pane": pane, "created_utc": datetime.now(timezone.utc).isoformat(),
               "state": "AIXML PREPARED: no native LabVIEW verification", "items": rows}
    (out / "stage_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def load_stage(batch_id: str, root: Path | None = None) -> dict:
    file = (root or project_root()) / "outputs" / batch_id.upper() / "stage_manifest.json"
    if not file.is_file():
        raise FileNotFoundError(f"Run: python -m lvbatch prepare --batch {batch_id}")
    return read_json(file)


def record(batch_id: str, stage: str, values: dict, root: Path | None = None) -> Path:
    path = (root or project_root()) / "outputs" / batch_id.upper() / "evidence"
    path.mkdir(parents=True, exist_ok=True)
    p = path / f"{stage}.json"
    p.write_text(json.dumps(values, indent=2, default=str), encoding="utf-8")
    return p
