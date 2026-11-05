"""A01 simulation contracts: no hardware or LabVIEW is needed for these tests."""
import math
import unittest

from lvbatch.sim_reference import (
    Command, Fault, SimModel, SimSession, VirtualClock,
)


def cmd(session, ident="c1", pressure=80, flow=20, lever=100, **kw):
    return Command(ident, session.run_id, pressure, flow, lever, **kw)


class SimulatorContractTests(unittest.TestCase):
    def test_sim_main_is_software_only_and_identifies_every_event(self):
        sim = SimSession("SIM-1")
        self.assertTrue(sim.simulation_only)
        self.assertEqual(sim.events[0]["type"], "SIMULATION_STARTED")
        self.assertTrue(sim.events[0]["synthetic"])
        self.assertEqual(sim.events[0]["run_id"], "SIM-1")

    def test_sim_clock_deterministic_and_rejects_backward_time(self):
        clock = VirtualClock()
        self.assertEqual(clock.advance(100), 100)
        self.assertEqual(clock.advance(0), 100)
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                clock.advance(bad)
        sim = SimSession("sim")
        with self.assertRaises(ValueError):
            sim.advance(-1)
        with self.assertRaises(OverflowError):
            VirtualClock(2**63 - 1).advance(1)

    def test_io_adapter_accepts_once_and_rejects_physical_transport(self):
        sim = SimSession("sim")
        self.assertEqual(sim.submit(cmd(sim))["type"], "ACCEPTED")
        self.assertEqual(sim.submit(cmd(sim))["type"], "DUPLICATE")
        with self.assertRaises(PermissionError):
            sim.submit(cmd(sim, ident="physical", transport="MODBUS_TCP"))
        self.assertEqual(sim.submit(Command("wrong", "other", 1, 1, 1))["type"],
                         "REJECTED")
        with self.assertRaises(ValueError):
            sim.submit(cmd(sim, ident="nan", pressure=math.nan))

    def test_applied_ack_exact_virtual_time(self):
        sim = SimSession("sim", model=SimModel(ack_delay_ms=50))
        self.assertEqual(sim.submit(cmd(sim))["type"], "ACCEPTED")
        sim.advance(49)
        self.assertNotIn("APPLIED", [e["type"] for e in sim.events])
        sim.advance(51)
        applied = [e for e in sim.events if e["type"] == "APPLIED"]
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]["at_ms"], 50)

    def test_first_order_feedback_is_deterministic_and_bounded(self):
        a = SimSession("sim")
        b = SimSession("sim")
        for session in (a, b):
            session.submit(cmd(session, pressure=200, flow=80, lever=300))
            session.advance(500)
        self.assertEqual(a.feedback(), b.feedback())
        reading = a.feedback()
        self.assertGreater(reading["pressure_bar"], 0)
        self.assertLess(reading["pressure_bar"], 100)
        self.assertLess(reading["flow_lpm"], 40)
        self.assertLess(reading["lever_mm"], 200)
        self.assertEqual(reading["quality"], "GOOD")

    def test_fault_trigger_stops_actuator_at_exact_virtual_time(self):
        sim = SimSession("sim")
        sim.submit(cmd(sim))
        sim.schedule_fault(Fault.STUCK_SERVO, 100)
        sim.advance(100)
        frozen = sim.feedback()["lever_mm"]
        sim.advance(2000)
        self.assertEqual(sim.feedback()["lever_mm"], frozen)
        faults = [e for e in sim.events if e["type"] == "FAULT_INJECTED"]
        self.assertEqual(faults[0]["at_ms"], 100)

    def test_sensor_staleness_and_dropout_are_invalid_for_progress(self):
        sim = SimSession("sim", model=SimModel(freshness_limit_ms=250))
        sim.submit(cmd(sim))
        sim.advance(50)
        sim.feedback()
        sim.schedule_fault(Fault.SENSOR_STALE, 100)
        sim.advance(400)
        self.assertEqual(sim.feedback()["quality"], "STALE")
        self.assertEqual(sim.feedback()["sample_ms"], 50)
        sim.schedule_fault(Fault.SENSOR_DROPOUT, sim.clock.now_ms)
        result = sim.feedback()
        self.assertEqual(result["quality"], "INVALID")
        self.assertIsNone(result["pressure_bar"])

    def test_lost_ack_and_host_disconnect(self):
        sim = SimSession("sim")
        sim.schedule_fault(Fault.LOST_ACK, 0)
        self.assertEqual(sim.submit(cmd(sim))["type"], "ACK_SUPPRESSED")
        sim.advance(50)
        self.assertFalse(any(e["type"] == "APPLIED" for e in sim.events))
        sim.schedule_fault(Fault.HOST_DISCONNECT, 50)
        self.assertEqual(sim.submit(cmd(sim, ident="c2"))["type"], "REJECTED")

    def test_saturation_and_invalid_model_values(self):
        sim = SimSession("sim")
        sim.schedule_fault(Fault.SATURATION, 0)
        sim.submit(cmd(sim, pressure=100, flow=40, lever=200))
        sim.advance(10_000)
        sample = sim.feedback()
        self.assertLessEqual(sample["pressure_bar"], 50.01)
        self.assertLessEqual(sample["flow_lpm"], 20.01)
        self.assertLessEqual(sample["lever_mm"], 100.01)
        with self.assertRaises(ValueError):
            SimModel(time_constant_ms=0)
        with self.assertRaises(ValueError):
            SimModel(sensor_resolution=float("nan"))

    def test_simulation_faults_cannot_be_scheduled_in_the_past(self):
        sim = SimSession("sim")
        sim.advance(25)
        with self.assertRaises(ValueError):
            sim.schedule_fault(Fault.LOST_ACK, 10)


if __name__ == "__main__":
    unittest.main()
