"""A01 Sim_Clock VI staging and exact native-result decoding, no LabVIEW."""
import json
import tempfile
import unittest
from pathlib import Path

from lvbatch.a01_clock import (compare_native_clock_values, prepare_sim_clock,
                               _read_exact_i64)
from lvbatch.core import check_aixml, project_root


class SimClockNativeCandidateTests(unittest.TestCase):
    def test_clock_source_is_well_formed_and_declared(self):
        root = project_root()
        source = root / "baseline/aixml/app/Sim_Clock.xml"
        self.assertTrue(check_aixml(source, "Sim_Clock.vi")["ok"])
        with source.open(encoding="utf-8") as f:
            raw = f.read()
        self.assertIn('type="int64"', raw)
        self.assertIn("In Range and Coerce", raw)
        self.assertIn("9223372036854775807", raw)

    def test_clock_prepare_isolated_and_connector_positions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "baseline/aixml/app").mkdir(parents=True)
            (root / "baseline/tests").mkdir(parents=True)
            source = project_root()
            for path in ("baseline/aixml/app/Sim_Clock.xml",
                         "baseline/tests/A01_Clock_Native_Vectors.json",
                         "baseline/batch_manifest.json"):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((source / path).read_bytes())
            info = prepare_sim_clock(root=root)
            self.assertEqual(info["native_vis_staged"], 1)
            self.assertEqual(info["component"], "Sim_Clock.vi")
            self.assertEqual(info["items"][0]["connector_pattern"], 4805)
            self.assertEqual(info["items"][0]["connector_map"],
                             {"current_ms": 3, "advance_ms": 2, "next_ms": 1, "valid": 0})
            xml = Path(info["items"][0]["xml"])
            self.assertTrue(check_aixml(xml, "Sim_Clock.vi")["ok"])
            self.assertIn('pane="4805"', xml.read_text(encoding="utf-8"))
            self.assertFalse(Path(info["items"][0]["native_vi"]).exists())
            self.assertIn("native_clock_v1", str(info["items"][0]["native_vi"]))

    def test_lossless_int64_decoder(self):
        cap = 2**63 - 1
        self.assertEqual(_read_exact_i64(str(cap)), cap)
        self.assertEqual(_read_exact_i64(-3), -3)
        for invalid in (True, float(cap), "4.0", str(2**63)):
            with self.assertRaises((TypeError, ValueError)):
                _read_exact_i64(invalid)

    def test_native_result_checks_both_ports_and_exact_large_integer(self):
        row = {"next_ms": str(2**63-1), "valid": True}
        good = {"errorCode": 0, "helperErrorCode": 0, "helperFailed": False,
                "values": {"next_ms": {"type": "I64", "value": str(2**63-1)},
                           "valid": {"type": "Boolean", "value": True}}}
        self.assertTrue(compare_native_clock_values(good, row)[0])
        corrupt = json.loads(json.dumps(good))
        corrupt["values"]["next_ms"]["value"] = str(2**63-2)
        self.assertFalse(compare_native_clock_values(corrupt, row)[0])
        corrupt = json.loads(json.dumps(good))
        corrupt["values"]["valid"]["value"] = "true"
        self.assertFalse(compare_native_clock_values(corrupt, row)[0])
        corrupt = json.loads(json.dumps(good))
        corrupt["helperFailed"] = True
        self.assertFalse(compare_native_clock_values(corrupt, row)[0])


if __name__ == "__main__":
    unittest.main()
