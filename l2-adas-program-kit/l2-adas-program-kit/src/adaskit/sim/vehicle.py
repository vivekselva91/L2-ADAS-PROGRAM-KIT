"""Kinematic bicycle model of the ego vehicle.

Deliberately simple: the point of this repo is the path from requirement to
release evidence, not vehicle dynamics fidelity. The model is good enough to
make lane-keeping and following behaviour observable and testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

WHEELBASE_M = 2.8


@dataclass
class VehicleState:
    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0
    speed: float = 25.0
    steer_angle: float = 0.0

    def copy(self) -> VehicleState:
        return VehicleState(self.x, self.y, self.heading, self.speed, self.steer_angle)


@dataclass
class Vehicle:
    state: VehicleState = field(default_factory=VehicleState)
    dt: float = 0.02

    def step(self, accel_cmd: float, steer_rate_cmd: float) -> VehicleState:
        s = self.state
        s.steer_angle = _clamp(s.steer_angle + steer_rate_cmd * self.dt, -0.45, 0.45)
        s.speed = max(0.0, s.speed + accel_cmd * self.dt)
        s.heading += (s.speed / WHEELBASE_M) * math.tan(s.steer_angle) * self.dt
        s.x += s.speed * math.cos(s.heading) * self.dt
        s.y += s.speed * math.sin(s.heading) * self.dt
        return s


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
