"""Adaptive cruise control: speed hold plus time-gap following."""

from __future__ import annotations

from dataclasses import dataclass

ACCEL_MIN = -3.5  # SYS-REQ-007
ACCEL_MAX = 2.0
TIME_GAP_S = 1.6  # target, above the 1.5 s floor in SYS-REQ-002
STANDSTILL_GAP_M = 5.0


@dataclass
class ACCController:
    set_speed: float = 30.0
    kp_speed: float = 0.45
    kp_gap: float = 0.32
    kd_gap: float = 0.85

    def step(self, ego_speed: float, gap_m: float | None, rel_speed: float | None) -> float:
        """Return a bounded acceleration command.

        With no valid lead measurement the controller degrades to plain speed
        control, which is the documented behaviour for a radar timeout
        (ICD-RADAR-01, on_timeout: degrade_to_speed_control).
        """
        speed_cmd = self.kp_speed * (self.set_speed - ego_speed)
        if gap_m is None or rel_speed is None:
            return _bound(speed_cmd)

        desired_gap = STANDSTILL_GAP_M + TIME_GAP_S * ego_speed
        gap_error = gap_m - desired_gap
        follow_cmd = self.kp_gap * gap_error + self.kd_gap * rel_speed
        # Follow the more conservative of the two objectives.
        return _bound(min(speed_cmd, follow_cmd))


def _bound(value: float) -> float:
    return max(ACCEL_MIN, min(ACCEL_MAX, value))
