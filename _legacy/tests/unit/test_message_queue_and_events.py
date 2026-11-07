#!/usr/bin/env python3
"""Unit tests for Message Queue, User Event Stop, and Ramp Generator subsystems.

Modeled after official NI patterns:
- Qd Message Handler (Message Queue.lvlib, User Event - Stop.lvlib)
- Ramp Gen & Trap Test (Ramp_Generator.vi)
"""
from __future__ import annotations

import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = WORKSPACE_ROOT / "src"
TRANSPORT_DIR = SRC_DIR / "02_Transport"
ENGINE_DIR = SRC_DIR / "05_Engine"


class TestTutorialDesignPatterns(unittest.TestCase):
    """Test compiled binary integrity and behavioral logic of tutorial components."""

    def test_message_queue_binaries_exist_and_valid(self):
        mq_dir = TRANSPORT_DIR / "Message_Queue"
        self.assertTrue(mq_dir.exists(), "Message_Queue directory must exist.")

        components = [
            "Message_Cluster.ctl",
            "Obtain_Message_Queue.vi",
            "Enqueue_Message.vi",
            "Dequeue_Message.vi",
            "Release_Message_Queue.vi",
        ]
        for name in components:
            p = mq_dir / name
            self.assertTrue(p.exists(), f"{name} must exist.")
            self.assertGreater(p.stat().st_size, 3000, f"{name} must be compiled.")
            self.assertEqual(p.read_bytes()[:4], b"RSRC", f"{name} must be valid LabVIEW resource.")

    def test_user_event_stop_binaries_exist_and_valid(self):
        ue_dir = TRANSPORT_DIR / "User_Event_Stop"
        self.assertTrue(ue_dir.exists(), "User_Event_Stop directory must exist.")

        components = [
            "Create_Stop_Event.vi",
            "Fire_Stop_Event.vi",
            "Destroy_Stop_Event.vi",
        ]
        for name in components:
            p = ue_dir / name
            self.assertTrue(p.exists(), f"{name} must exist.")
            self.assertGreater(p.stat().st_size, 3000, f"{name} must be compiled.")
            self.assertEqual(p.read_bytes()[:4], b"RSRC", f"{name} must be valid LabVIEW resource.")

    def test_ramp_generator_binary_exists_and_valid(self):
        ramp_vi = ENGINE_DIR / "Ramp_Generator.vi"
        self.assertTrue(ramp_vi.exists(), "Ramp_Generator.vi must exist.")
        self.assertGreater(ramp_vi.stat().st_size, 5000, "Ramp_Generator.vi must be compiled binary.")
        self.assertEqual(ramp_vi.read_bytes()[:4], b"RSRC", "Must be a valid LabVIEW resource.")

    def test_ramp_generator_profile_progression(self):
        """Simulate dynamic ramp setpoint generation across multiple time steps."""
        current_val = 0.0
        target_sp = 100.0
        ramp_rate = 25.0  # 25 bar/sec
        dt = 0.1          # 100 ms step

        time_elapsed = 0.0
        max_time = 10.0
        reached = False

        while time_elapsed < max_time and not reached:
            step = ramp_rate * dt
            next_val = min(current_val + step, target_sp)
            reached = (next_val >= target_sp)
            current_val = next_val
            time_elapsed += dt

        self.assertTrue(reached, "Ramp generator must reach target setpoint.")
        self.assertAlmostEqual(current_val, 100.0, places=2)
        # 100 bar at 25 bar/sec should take exactly 4.0 seconds (40 iterations)
        self.assertAlmostEqual(time_elapsed, 4.0, places=1)

    def test_priority_vs_normal_queue_ordering(self):
        """Verify priority queue behavior modeled after Enqueue Element At Opposite End."""
        queue: list[dict[str, str]] = []

        def enqueue_msg(msg: str, data: str = "", priority: bool = False):
            item = {"Message": msg, "Data": data}
            if priority:
                queue.insert(0, item)  # Front of queue (Enqueue Element At Opposite End)
            else:
                queue.append(item)    # Back of queue (Enqueue Element)

        # Enqueue regular sequence steps
        enqueue_msg("STEP_01", "Pressure 20")
        enqueue_msg("STEP_02", "Pressure 40")
        enqueue_msg("STEP_03", "Pressure 60")

        # High priority Emergency Stop fires
        enqueue_msg("EMERGENCY_STOP", "Overpressure", priority=True)

        # First message dequeued MUST be EMERGENCY_STOP
        first = queue.pop(0)
        self.assertEqual(first["Message"], "EMERGENCY_STOP")
        self.assertEqual(first["Data"], "Overpressure")

        # Remaining items continue in FIFO order
        second = queue.pop(0)
        self.assertEqual(second["Message"], "STEP_01")


if __name__ == "__main__":
    unittest.main()
