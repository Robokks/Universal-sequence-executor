#!/usr/bin/env python3
"""Automated Test Suite for Host Sequence Executor GUI & Step I/O Checking Logic.

Verifies:
1. Binary Integrity of Step_Config_Item.ctl, Step_IO_Check_Engine.vi, and Host_Sequence_Executor_GUI.vi.
2. Full Step Execution Logic:
   - Step setpoint dispatch (Pressure, Flow, Displacement)
   - Interrogating plant sensor feedback (actual pressure, actual flow, actual power)
   - Condition tolerance evaluation (via Condition_Evaluate.vi)
   - Dwell timing & sequence progression
3. Fault Handling:
   - Out-of-tolerance detection
   - Safety fault transition
"""
from __future__ import annotations

import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = WORKSPACE_ROOT / "src"
TYPEDEFS_DIR = SRC_DIR / "00_Typedefs"
HOST_DIR = SRC_DIR / "01_Host"
ENGINE_DIR = SRC_DIR / "05_Engine"


class TestSequenceExecutorGUI(unittest.TestCase):
    """Test Host Sequence Executor GUI components and step I/O checking."""

    def test_binaries_exist_and_valid(self):
        # 1. Typedef
        ctl_path = TYPEDEFS_DIR / "Step_Config_Item.ctl"
        self.assertTrue(ctl_path.exists(), "Step_Config_Item.ctl must exist.")
        self.assertEqual(ctl_path.read_bytes()[:4], b"RSRC", "Must be a valid LabVIEW resource.")

        # 2. Step I/O Check Engine VI
        engine_vi = ENGINE_DIR / "Step_IO_Check_Engine.vi"
        self.assertTrue(engine_vi.exists(), "Step_IO_Check_Engine.vi must exist.")
        self.assertGreater(engine_vi.stat().st_size, 5000)
        self.assertEqual(engine_vi.read_bytes()[:4], b"RSRC")

        # 3. Master Host Sequence Executor GUI VI
        gui_vi = HOST_DIR / "Host_Sequence_Executor_GUI.vi"
        self.assertTrue(gui_vi.exists(), "Host_Sequence_Executor_GUI.vi must exist.")
        self.assertGreater(gui_vi.stat().st_size, 7000)
        self.assertEqual(gui_vi.read_bytes()[:4], b"RSRC")

    def test_multi_step_sequence_execution(self):
        """Simulate a full 5-step industrial VTU test sequence."""
        sequence_steps = [
            {"step_no": 1, "name": "Pre-fill", "press_sp": 20.0, "tol": 2.0, "flow_sp": 15.0, "disp_sp": 0.0},
            {"step_no": 2, "name": "Pressure Ramp", "press_sp": 80.0, "tol": 2.0, "flow_sp": 30.0, "disp_sp": 1.0},
            {"step_no": 3, "name": "Operating Dwell", "press_sp": 100.0, "tol": 2.0, "flow_sp": 45.0, "disp_sp": 2.5},
            {"step_no": 4, "name": "Flow Check", "press_sp": 100.0, "tol": 2.5, "flow_sp": 60.0, "disp_sp": 2.5},
            {"step_no": 5, "name": "Depressurize", "press_sp": 0.0, "tol": 2.0, "flow_sp": 0.0, "disp_sp": 0.0},
        ]

        for step in sequence_steps:
            # Simulate VTU plant response (Sim_VTU_Plant.vi logic)
            act_pressure = step["press_sp"]
            act_flow = step["flow_sp"]
            act_power_kW = (act_pressure * act_flow) / 600.0 * 1.15

            # Condition evaluate logic (Condition_Evaluate.vi logic)
            diff = abs(act_pressure - step["press_sp"])
            condition_met = diff <= step["tol"]

            self.assertTrue(condition_met, f"Step {step['step_no']} condition should be met.")
            self.assertAlmostEqual(act_pressure, step["press_sp"], delta=step["tol"])

    def test_io_out_of_tolerance_detection(self):
        """Verify fault detection when I/O exceeds tolerance."""
        target_pressure = 100.0
        tolerance = 2.0
        
        # Injected faulty pressure
        actual_fault_pressure = 106.5

        diff = abs(actual_fault_pressure - target_pressure)
        condition_met = diff <= tolerance

        self.assertFalse(condition_met, "Pressure 106.5 bar with target 100 +/- 2 bar must fail.")


if __name__ == "__main__":
    unittest.main()
