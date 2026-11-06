"""Offline A01 plant helper checks, including independent AIXML graph evaluation.

Neither these tests nor the reference model constitute native LabVIEW evidence.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

from lvbatch.a01_plant import (NAME, SOURCE, VECTORS, BATCH,
                                compare_native_plant, plant_step_reference,
                                prepare_plant_step)
from lvbatch.core import check_aixml, project_root


def evaluate_aixml_step(xml_file: Path, inputs: dict) -> dict:
    """Restricted one-output-per-node evaluator for this single pure graph.

    Evaluates real XML nets in topological order, not just the written formula.
    Any unrecognised primitive or unresolved source fails the test.
    """
    root = ET.parse(xml_file).getroot()
    nets: dict[str, float | bool] = {}

    def endpoints(raw: str) -> dict[str, str]:
        return dict(item.split(":", 1) for item in raw.split(",") if item)

    for element in root:
        if element.tag not in ("Control", "Constant", "Node", "Indicator"):
            continue
        if element.tag == "Control":
            value = inputs[element.get("_name")]
        elif element.tag == "Constant":
            value = (element.get("value") == "true") if element.get("type") == "bool" else float(element.get("value"))
        else:
            arg = {name: nets[source] for name, source in
                   endpoints(element.get("inputs", "")).items()}
            if element.tag == "Indicator":
                value = arg["value"]
            else:
                name = element.get("_name")
                if name == "Greater Or Equal To 0?":
                    value = arg["x"] >= 0
                elif name == "Greater Than 0?":
                    value = arg["x"] > 0
                elif name == "Select":
                    value = arg["t"] if arg["s"] else arg["f"]
                elif name == "Divide":
                    value = arg["x"] / arg["y"]
                elif name == "Subtract":
                    value = arg["x"] - arg["y"]
                elif name == "Exponential":
                    value = math.exp(arg["x"])
                elif name == "Multiply":
                    value = arg["x"] * arg["y"]
                elif name == "Add":
                    value = arg["x"] + arg["y"]
                else:
                    raise AssertionError(f"Unsupported graph node: {name}")
        for source in endpoints(element.get("outputs", "")).values():
            nets[source] = value
        if element.tag == "Indicator":
            inputs[element.get("_name")] = value
    return {name: inputs[name] for name in ("next", "valid")}


class A01PlantStepTests(unittest.TestCase):
    def setUp(self):
        self.base = project_root()
        self.source = self.base / SOURCE
        self.vectors = json.loads((self.base / VECTORS).read_text(encoding="utf-8"))["vectors"]

    def test_source_has_expected_native_graph_and_ports(self):
        check = check_aixml(self.source, NAME)
        self.assertTrue(check["ok"], check["issues"])
        tree = ET.parse(self.source).getroot()
        self.assertIn("software-only", tree.get("description").lower())
        self.assertEqual({c.get("_name") for c in tree.findall("Control")},
                         {"current", "target", "dt_ms", "time_constant_ms"})
        self.assertEqual({c.get("_name") for c in tree.findall("Indicator")}, {"next", "valid"})
        self.assertEqual(len(self.vectors), 16)

    def test_vectors_match_independent_python_formula(self):
        for row in self.vectors:
            with self.subTest(id=row["id"]):
                next_value, valid = plant_step_reference(
                    row["current"], row["target"], row["dt_ms"], row["time_constant_ms"]
                )
                self.assertEqual(valid, row["valid"])
                self.assertTrue(math.isclose(next_value, row["next"],
                                             rel_tol=1e-12, abs_tol=1e-12))

    def test_actual_aixml_graph_matches_independent_vectors(self):
        for row in self.vectors:
            with self.subTest(id=row["id"]):
                inputs = {name: row[name] for name in (
                    "current", "target", "dt_ms", "time_constant_ms"
                )}
                result = evaluate_aixml_step(self.source, inputs)
                self.assertEqual(result["valid"], row["valid"])
                self.assertTrue(math.isclose(result["next"], row["next"],
                                             rel_tol=1e-8, abs_tol=1e-8),
                                f"{row['id']}: actual {result['next']} expected {row['next']}")

    def test_rejects_nonfinite_and_non_numeric_reference_inputs(self):
        bads = (math.inf, -math.inf, math.nan, True, "invalid")
        for bad in bads:
            with self.subTest(value=str(bad)):
                with self.assertRaises(ValueError):
                    plant_step_reference(bad, 50, 10, 500)

    def test_preparation_is_isolated_from_clock_and_declares_pane(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for rel in (SOURCE, VECTORS, "baseline/batch_manifest.json"):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.base / rel, target)
            before = (root / SOURCE).read_bytes()
            clock_stage = root / "outputs/A01/stage_manifest.json"
            clock_stage.parent.mkdir(parents=True, exist_ok=True)
            clock_stage.write_text('{"component":"Sim_Clock.vi"}', encoding="utf-8")
            result = prepare_plant_step("native_plant_test", root=root)
            self.assertEqual(result["batch"], BATCH)
            self.assertEqual(result["native_vis_staged"], 1)
            self.assertEqual(result["items"][0]["connector_pattern"], 4815)
            self.assertEqual(result["items"][0]["connector_map"],
                             {"current": 11, "target": 10, "dt_ms": 9,
                              "time_constant_ms": 8, "next": 3, "valid": 2})
            self.assertFalse(Path(result["items"][0]["native_vi"]).exists())
            self.assertEqual(clock_stage.read_text(encoding="utf-8"),
                             '{"component":"Sim_Clock.vi"}')
            self.assertEqual((root / SOURCE).read_bytes(), before)
            staged = Path(result["items"][0]["xml"])
            self.assertTrue(check_aixml(staged, NAME)["ok"])
            self.assertIn('<?lvmcp pane="4815"?>', staged.read_text(encoding="utf-8"))
            self.assertTrue((root / "outputs/A01P/step_v1/Sim_VTU_Plant_Step_DESIGN.md").is_file())

    def test_native_comparison_fails_closed(self):
        vector = self.vectors[1]
        good = {"ok": True, "helperErrorCode": 0,
                "values": {"next": {"type": "DBL", "value": vector["next"]},
                           "valid": {"type": "Boolean", "value": vector["valid"]}}}
        self.assertTrue(compare_native_plant(good, vector)[0])
        for bad in (
            {},
            {"ok": True, "values": {}},
            {"ok": True, "values": {"next": {"value": float("nan")}, "valid": {"value": True}}},
            {"ok": True, "values": {"next": {"value": vector["next"]}, "valid": {"value": 1}}},
            {"ok": True, "helperFailed": True, "values": good["values"]},
        ):
            self.assertFalse(compare_native_plant(bad, vector)[0])


if __name__ == "__main__":
    unittest.main()
