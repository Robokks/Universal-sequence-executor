"""A01 deterministic, software-only simulator reference (NOT a native LabVIEW VI).

Reference behavior for Sim_Main, Sim_IO_Adapter, Sim_VTU_Plant,
Sim_Fault_Injection, and Sim_Clock. No hardware adapters are imported,
opened, or called. The constants are illustrative simulation parameters,
NOT real rig limits or safety thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math


class Fault(str, Enum):
    NONE = "none"
    SENSOR_STALE = "sensor_stale"
    SENSOR_DROPOUT = "sensor_dropout"
    LOST_ACK = "lost_ack"
    STUCK_SERVO = "stuck_servo"
    SATURATION = "saturation"
    PLUGIN_STALL = "plugin_stall"
    HOST_DISCONNECT = "host_disconnect"
    DISK_FULL = "disk_full"


def _finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


@dataclass(frozen=True)
class SimModel:
    """Illustrative synthetic range and response properties; not rig data."""
    pressure_max_bar: float = 100.0
    flow_max_lpm: float = 40.0
    lever_max_mm: float = 200.0
    time_constant_ms: float = 500.0
    ack_delay_ms: int = 50
    sensor_resolution: float = 0.01
    freshness_limit_ms: int = 250

    def __post_init__(self):
        for name in ("pressure_max_bar", "flow_max_lpm", "lever_max_mm",
                     "time_constant_ms", "sensor_resolution"):
            if _finite(name, getattr(self, name)) <= 0:
                raise ValueError(f"{name} must be positive")
        for name in ("ack_delay_ms", "freshness_limit_ms"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")


@dataclass
class VirtualClock:
    now_ms: int = 0

    def advance(self, delta_ms: int) -> int:
        if isinstance(delta_ms, bool) or not isinstance(delta_ms, int) or delta_ms < 0:
            raise ValueError("Virtual time advance must be a nonnegative integer (ms)")
        if self.now_ms + delta_ms >= 2**63:
            raise OverflowError("Virtual clock exhausted 63-bit range")
        self.now_ms += delta_ms
        return self.now_ms


@dataclass(frozen=True)
class Command:
    command_id: str
    run_id: str
    pressure_bar: float
    flow_lpm: float
    lever_mm: float
    transport: str = "SIM"


@dataclass(frozen=True)
class FaultTrigger:
    at_ms: int
    fault: Fault

    def __post_init__(self):
        if isinstance(self.at_ms, bool) or not isinstance(self.at_ms, int) or self.at_ms < 0:
            raise ValueError("Fault trigger must be a nonnegative virtual timestamp")


@dataclass
class SimSession:
    """Deterministic reference model. Explicitly cannot connect to physical I/O."""
    run_id: str
    model: SimModel = field(default_factory=SimModel)
    clock: VirtualClock = field(default_factory=VirtualClock)
    simulation_only: bool = field(default=True, init=False)
    _targets: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    _actual: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    _seen_commands: set[str] = field(default_factory=set)
    _ack_pending: list[tuple[int, str]] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    faults: set[Fault] = field(default_factory=set)
    _scheduled: list[FaultTrigger] = field(default_factory=list)
    _last_good_timestamp: int = 0

    def __post_init__(self):
        if not self.run_id or not isinstance(self.run_id, str):
            raise ValueError("Simulation run_id is required")
        self.events.append({"type": "SIMULATION_STARTED", "run_id": self.run_id,
                            "at_ms": self.clock.now_ms, "synthetic": True})

    def schedule_fault(self, fault: Fault, at_ms: int) -> None:
        if not isinstance(fault, Fault) or fault == Fault.NONE:
            raise ValueError("Select a defined, non-NONE fault")
        trigger = FaultTrigger(at_ms, fault)
        if at_ms < self.clock.now_ms:
            raise ValueError("Cannot schedule fault in the past")
        self._scheduled.append(trigger)
        self._scheduled.sort(key=lambda t: t.at_ms)

    def clear_fault(self, fault: Fault) -> None:
        self.faults.discard(fault)

    def submit(self, command: Command) -> dict:
        if not isinstance(command, Command):
            raise TypeError("Command payload must use the explicit simulation contract")
        if command.transport != "SIM":
            raise PermissionError("Physical transports are forbidden in the simulator")
        if not command.command_id or command.run_id != self.run_id:
            return self._event("REJECTED", command.command_id, reason="run_id/command_id mismatch")
        if Fault.HOST_DISCONNECT in self.faults:
            return self._event("REJECTED", command.command_id, reason="host disconnected")
        if command.command_id in self._seen_commands:
            return self._event("DUPLICATE", command.command_id)
        raw = [_finite("pressure_bar", command.pressure_bar),
               _finite("flow_lpm", command.flow_lpm),
               _finite("lever_mm", command.lever_mm)]
        limits = [self.model.pressure_max_bar, self.model.flow_max_lpm,
                  self.model.lever_max_mm]
        self._targets = [max(0.0, min(v, lim)) for v, lim in zip(raw, limits)]
        self._seen_commands.add(command.command_id)
        self._ack_pending.append((self.clock.now_ms + self.model.ack_delay_ms,
                                  command.command_id))
        if Fault.LOST_ACK in self.faults:
            return self._event("ACK_SUPPRESSED", command.command_id)
        return self._event("ACCEPTED", command.command_id)

    def _event(self, kind: str, command_id: str, **extra) -> dict:
        event = {"type": kind, "command_id": command_id, "run_id": self.run_id,
                 "at_ms": self.clock.now_ms, "synthetic": True, **extra}
        self.events.append(event)
        return event

    def _tick_plant(self, delta_ms: int) -> None:
        if delta_ms <= 0 or Fault.STUCK_SERVO in self.faults:
            return
        alpha = -math.expm1(-delta_ms / self.model.time_constant_ms)
        max_values = [self.model.pressure_max_bar, self.model.flow_max_lpm,
                      self.model.lever_max_mm]
        for i, requested in enumerate(self._targets):
            if Fault.SATURATION in self.faults:
                requested = min(requested, max_values[i] * 0.5)
            self._actual[i] += alpha * (requested - self._actual[i])

    def advance(self, delta_ms: int) -> int:
        if isinstance(delta_ms, bool) or not isinstance(delta_ms, int) or delta_ms < 0:
            raise ValueError("Virtual time advance must be a nonnegative integer (ms)")
        target = self.clock.now_ms + delta_ms
        if target >= 2**63:
            raise OverflowError("Virtual clock exhausted 63-bit range")
        # Split on exact fault trigger timestamps so a scheduled fault is
        # applied to subsequent plant evolution, never retroactively.
        while True:
            while self._scheduled and self._scheduled[0].at_ms == self.clock.now_ms:
                trig = self._scheduled.pop(0)
                self.faults.add(trig.fault)
                self._event("FAULT_INJECTED", trig.fault.value)
            if self.clock.now_ms >= target:
                break
            due = self._scheduled[0].at_ms if self._scheduled else target
            next_time = min(due, target)
            segment = next_time - self.clock.now_ms
            self._tick_plant(segment)
            self.clock.advance(segment)
        remaining = []
        for deadline, command_id in self._ack_pending:
            if deadline <= self.clock.now_ms:
                if Fault.LOST_ACK in self.faults:
                    self._event("ACK_SUPPRESSED", command_id)
                else:
                    self._event("APPLIED", command_id)
            else:
                remaining.append((deadline, command_id))
        self._ack_pending = remaining
        return self.clock.now_ms

    def feedback(self) -> dict:
        now = self.clock.now_ms
        if Fault.SENSOR_DROPOUT in self.faults:
            return {"run_id": self.run_id, "at_ms": now,
                    "sample_ms": self._last_good_timestamp,
                    "quality": "INVALID", "synthetic": True,
                    "pressure_bar": None, "flow_lpm": None, "lever_mm": None}
        if Fault.SENSOR_STALE in self.faults:
            stamp = self._last_good_timestamp
            quality = "STALE" if now - stamp > self.model.freshness_limit_ms else "GOOD"
        else:
            stamp, quality = now, "GOOD"
            self._last_good_timestamp = now
        q = self.model.sensor_resolution
        numbers = [round(v / q) * q for v in self._actual]
        return {"run_id": self.run_id, "at_ms": now, "sample_ms": stamp,
                "quality": quality, "synthetic": True,
                "pressure_bar": numbers[0], "flow_lpm": numbers[1],
                "lever_mm": numbers[2]}
