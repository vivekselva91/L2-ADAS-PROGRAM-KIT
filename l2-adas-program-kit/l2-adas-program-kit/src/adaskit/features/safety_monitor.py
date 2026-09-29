"""Safety monitor: the ASIL-bearing element of the architecture.

Everything the HARA produced as a safety goal is enforced here rather than
inside the feature controllers. That separation is the point: the comfort
functions can be QM, while the monitor that bounds their authority carries the
ASIL and can be argued independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SystemMode(str, Enum):
    ACTIVE = "ACTIVE"
    LATERAL_DEGRADED = "LATERAL_DEGRADED"
    TAKEOVER_REQUESTED = "TAKEOVER_REQUESTED"
    DISENGAGED = "DISENGAGED"


ODD_SPEED_MIN = 8.0   # SYS-REQ-009
ODD_SPEED_MAX = 36.0
# SYS-REQ-005 allows 300 ms from signal loss to disengage. Camera transport
# latency is ~45 ms, so the monitor budgets 250 ms to leave margin end to end.
LANE_TIMEOUT_MS = 250.0
HANDS_OFF_WARN_S = 15.0  # SYS-REQ-006
HANDS_OFF_DISENGAGE_S = 25.0
ACCEL_MIN, ACCEL_MAX = -3.5, 2.0  # SG-001 / SYS-REQ-007
STEER_RATE_LIMIT = 0.35  # SG-002 / SYS-REQ-008


@dataclass
class MonitorOutputs:
    mode: SystemMode
    accel_cmd: float
    steer_rate_cmd: float
    takeover_request: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class SafetyMonitor:
    mode: SystemMode = SystemMode.ACTIVE
    hands_off_s: float = 0.0
    _latched_disengage: bool = False

    def step(
        self,
        dt: float,
        ego_speed: float,
        lane_signal_age_ms: float,
        lane_valid: bool,
        hands_on: bool,
        accel_cmd: float,
        steer_rate_cmd: float,
    ) -> MonitorOutputs:
        reasons: list[str] = []
        self.hands_off_s = 0.0 if hands_on else self.hands_off_s + dt

        lateral_blind = (not lane_valid) or lane_signal_age_ms > LANE_TIMEOUT_MS
        odd_violation = not (ODD_SPEED_MIN <= ego_speed <= ODD_SPEED_MAX)
        hands_off_warn = self.hands_off_s > HANDS_OFF_WARN_S
        hands_off_stop = self.hands_off_s > HANDS_OFF_DISENGAGE_S

        if odd_violation:
            reasons.append("SYS-REQ-009: speed outside ODD")
            self._latched_disengage = True
        if hands_off_stop:
            reasons.append("SYS-REQ-006: hands off beyond disengage limit")
            self._latched_disengage = True

        if self._latched_disengage:
            mode = SystemMode.DISENGAGED
        elif lateral_blind:
            reasons.append("SYS-REQ-005: lane signal lost beyond timeout")
            mode = SystemMode.LATERAL_DEGRADED
        elif hands_off_warn:
            reasons.append("SYS-REQ-006: hands off beyond warning threshold")
            mode = SystemMode.TAKEOVER_REQUESTED
        else:
            mode = SystemMode.ACTIVE
        self.mode = mode

        # Authority limiting happens on every path, including degraded ones.
        safe_accel = max(ACCEL_MIN, min(ACCEL_MAX, accel_cmd))
        safe_steer = max(-STEER_RATE_LIMIT, min(STEER_RATE_LIMIT, steer_rate_cmd))
        if mode in (SystemMode.LATERAL_DEGRADED, SystemMode.DISENGAGED):
            safe_steer = 0.0
        if mode is SystemMode.DISENGAGED:
            safe_accel = 0.0

        takeover = mode in (
            SystemMode.TAKEOVER_REQUESTED,
            SystemMode.LATERAL_DEGRADED,
            SystemMode.DISENGAGED,
        )
        return MonitorOutputs(mode, safe_accel, safe_steer, takeover, reasons)
