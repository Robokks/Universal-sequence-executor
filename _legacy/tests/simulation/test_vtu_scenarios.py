#!/usr/bin/env python3
"""Phase 7: System Validation & VTU Reference Acceptance Scenarios.

Executes VTU hydraulic test scenarios:
- Scenario 1: Nominal pressure ramp, servo displacement, hitch load measurement
- Scenario 2: Fault injection: Host disconnect
- Scenario 3: Fault injection: Sensor staleness
"""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "pycharm-batch-builder" / "src"))

from lvbatch.sim_reference import SimSession, Command, Fault


class VTUScenarioValidationTests(unittest.TestCase):
    def test_scenario_1_nominal_pressure_and_displacement(self):
        """VTU Acceptance: Apply pressure setpoint, advance virtual time, verify applied ACK."""
        session = SimSession(run_id="VTU-RUN-001")
        # Command PRV pressure to 120 bar
        cmd = Command(
            run_id="VTU-RUN-001",
            command_id="CMD-01",
            pressure_bar=120.0,
            flow_lpm=40.0,
            lever_mm=2.0,
            transport="SIM"
        )
        ack = session.submit(cmd)
        self.assertEqual(ack["type"], "ACCEPTED")

        # Advance virtual time by 100 ms (past 50 ms ACK delay)
        session.advance(100)
        applied_events = [e for e in session.events if e.get("type") == "APPLIED"]
        self.assertEqual(len(applied_events), 1)
        self.assertEqual(applied_events[0]["command_id"], "CMD-01")

        # Check feedback values
        fb = session.feedback()
        self.assertGreater(fb["pressure_bar"], 0.0)
        self.assertEqual(fb["quality"], "GOOD")

    def test_scenario_2_fault_injection_host_disconnect(self):
        """VTU Acceptance: Inject Host disconnect at 200 ms; verify subsequent actuation is rejected."""
        session = SimSession(run_id="VTU-RUN-002")
        session.schedule_fault(Fault.HOST_DISCONNECT, at_ms=200)

        # Before disconnect: commands succeed
        cmd1 = Command(run_id="VTU-RUN-002", command_id="CMD-OK", pressure_bar=50.0, flow_lpm=20.0, lever_mm=1.0, transport="SIM")
        ack1 = session.submit(cmd1)
        self.assertEqual(ack1["type"], "ACCEPTED")

        # Advance to 300 ms (past disconnect)
        session.advance(300)

        # After disconnect: command requests must be rejected
        cmd2 = Command(run_id="VTU-RUN-002", command_id="CMD-BLOCKED", pressure_bar=80.0, flow_lpm=30.0, lever_mm=2.0, transport="SIM")
        ack2 = session.submit(cmd2)
        self.assertEqual(ack2["type"], "REJECTED")
        self.assertEqual(ack2["reason"], "host disconnected")

    def test_scenario_3_sensor_staleness_rejection(self):
        """VTU Acceptance: Stale sensor data must retain original timestamp."""
        session = SimSession(run_id="VTU-RUN-003")
        # First advance nominal to record valid baseline sample
        session.advance(50)
        fb_good = session.feedback()
        self.assertEqual(fb_good["quality"], "GOOD")

        # Now inject stale sensor fault at 100 ms
        session.schedule_fault(Fault.SENSOR_STALE, at_ms=100)
        session.advance(350)
        fb_stale = session.feedback()
        self.assertEqual(fb_stale["quality"], "STALE")
        # Stale sample retains old timestamp
        age_ms = session.clock.now_ms - fb_stale["sample_ms"]
        self.assertGreaterEqual(age_ms, 250, "Stale sensor sample must have elapsed age >= freshness threshold")


if __name__ == "__main__":
    unittest.main()
