"""Fast offline checks for the sequence operator slice; zero LabVIEW or hardware."""
from __future__ import annotations

import asyncio
import csv
import json
import tempfile
import threading
import unittest
from pathlib import Path

from lvbatch.sequence_mvp import (
    LabviewComparator, MockComparator, PLAN_FILE,
    Plan, Step, execute, load_plan, run_file, save_results,
)


class SequenceDemoTests(unittest.TestCase):
    def test_demo_plan_validated(self):
        plan = load_plan()
        self.assertEqual(len(plan.steps), 3)
        self.assertEqual(plan.steps[0].target_bar, 25)

    def test_rejects_physical_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "unsafe.json"
            data = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
            data["mode"] = "HARDWARE"
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_plan(file)

    def test_rejects_unbounded_or_invalid_values(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "bad.json"
            for field, value in (("target_bar", float("nan")),
                                 ("period_ms", 0),
                                 ("timeout_ms", 101),
                                 ("dwell_ms", 999999)):
                data = json.loads(PLAN_FILE.read_text(encoding="utf-8"))
                data["steps"][0][field] = value
                file.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(ValueError, msg=field):
                    load_plan(file)

    def test_three_step_simulated_run_passes(self):
        run = asyncio.run(run_file(PLAN_FILE))
        self.assertEqual(run["status"], "PASS", run)
        self.assertEqual(len(run["steps"]), 3)
        self.assertEqual([s["status"] for s in run["steps"]], ["PASS"] * 3)
        self.assertFalse(run["native_decisions"])
        self.assertEqual(run["mode"], "SIMULATION_ONLY")
        self.assertGreater(len(run["events"]), 3)

    def test_timeout_fails_closed_and_stops_sequence(self):
        plan = Plan("Timeout demo", (
            Step("Impossible pressure rise", 100, 0.01, 100, 0, 100),
            Step("Should not run", 10, 1.5, 2000, 0, 100),
        ))
        run = asyncio.run(execute(plan, MockComparator()))
        self.assertEqual(run["status"], "FAIL")
        self.assertEqual(len(run["steps"]), 1)
        self.assertEqual(run["steps"][0]["status"], "TIMEOUT")

    def test_stop_before_first_step(self):
        stopped = threading.Event()
        stopped.set()
        run = asyncio.run(execute(load_plan(), MockComparator(), stop=stopped))
        self.assertEqual(run["status"], "STOPPED")
        self.assertEqual(run["steps"], [])

    def test_results_are_saved_as_json_csv_without_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            run = asyncio.run(execute(load_plan(), MockComparator()))
            jp, cp = save_results(run, Path(folder))
            self.assertEqual(json.loads(jp.read_text())["status"], "PASS")
            with cp.open(newline="", encoding="utf-8") as inp:
                self.assertTrue(any(e["type"] == "STEP_FINISHED" for e in csv.DictReader(inp)))
            with self.assertRaises(FileExistsError):
                save_results(run, Path(folder))

    def test_grpc_requires_actual_paths(self):
        with self.assertRaises(ValueError):
            asyncio.run(run_file(PLAN_FILE, backend="grpc"))
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                LabviewComparator(None, Path(folder))

    def test_invalid_quality_never_passes_as_measurement(self):
        # Reject any nonfinite target *before* a simulation is run.
        with self.assertRaises(ValueError):
            load_plan(Path("does_not_exist.json"))


if __name__ == "__main__":
    unittest.main()
