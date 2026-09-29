"""SIL loop: wires sensors, features and the safety monitor into one run."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ..features.acc import ACCController
from ..features.lka import LKAController
from ..features.safety_monitor import SafetyMonitor, SystemMode
from .scenarios import Scenario
from .sensors import ModeledSensor
from .vehicle import Vehicle, VehicleState

DT = 0.02


@dataclass
class RunLog:
    """Time series plus the derived facts the acceptance criteria evaluate."""

    scenario_id: str
    t: list[float] = field(default_factory=list)
    speed: list[float] = field(default_factory=list)
    accel_cmd: list[float] = field(default_factory=list)
    steer_rate_cmd: list[float] = field(default_factory=list)
    lane_offset: list[float] = field(default_factory=list)
    gap: list[float] = field(default_factory=list)
    time_gap: list[float] = field(default_factory=list)
    mode: list[str] = field(default_factory=list)
    takeover: list[bool] = field(default_factory=list)
    latency_ms: list[float] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def first_event(self, kind: str) -> dict[str, Any] | None:
        return next((e for e in self.events if e["kind"] == kind), None)


def run_scenario(scenario: Scenario, seed: int = 11) -> RunLog:
    vehicle = Vehicle(state=VehicleState(speed=scenario.ego_speed_0), dt=DT)
    acc = ACCController(set_speed=scenario.set_speed)
    lka = LKAController()
    monitor = SafetyMonitor()

    radar_d = ModeledSensor("radar_distance", 50, 60, 0.25, 200, scenario.radar_dropout, seed)
    radar_v = ModeledSensor("radar_rel_speed", 50, 60, 0.15, 200, scenario.radar_dropout, seed + 1)
    cam_off = ModeledSensor("lane_offset", 33, 45, 0.02, 300, scenario.camera_dropout, seed + 2)
    cam_head = ModeledSensor("lane_heading", 33, 45, 0.01, 300, scenario.camera_dropout, seed + 3)

    log = RunLog(scenario_id=scenario.id)
    lead_distance = scenario.lead_distance_0
    lead_speed = scenario.lead_speed_0
    lane_center_y = 0.0
    lane_heading = 0.0
    prev_mode = SystemMode.ACTIVE

    steps = int(scenario.duration_s / DT)
    for i in range(steps):
        t = i * DT
        curvature = scenario.curvature(t)
        lane_heading += curvature * vehicle.state.speed * DT
        lane_center_y += math.sin(lane_heading) * vehicle.state.speed * DT

        if lead_distance is not None:
            lead_accel = scenario.lead_accel(t) if scenario.lead_accel else 0.0
            lead_speed = max(0.0, lead_speed + lead_accel * DT)
            lead_distance += (lead_speed - vehicle.state.speed) * DT

        true_offset = vehicle.state.y - lane_center_y
        true_heading_err = lane_heading - vehicle.state.heading

        s_off = cam_off.sample(t, true_offset)
        s_head = cam_head.sample(t, true_heading_err)
        s_gap = radar_d.sample(t, lead_distance) if lead_distance is not None else None
        s_rel = radar_v.sample(t, lead_speed - vehicle.state.speed) if lead_distance is not None else None

        accel_cmd = acc.step(
            vehicle.state.speed,
            s_gap.value if s_gap else None,
            s_rel.value if s_rel else None,
        )
        steer_cmd = lka.step(
            vehicle.state.speed,
            s_off.value,
            s_head.value,
            vehicle.state.steer_angle,
            curvature,
        )

        hands_on = not (scenario.hands_off_from_s is not None and t >= scenario.hands_off_from_s)
        out = monitor.step(
            DT,
            vehicle.state.speed,
            s_off.age_ms,
            s_off.valid,
            hands_on,
            accel_cmd,
            steer_cmd,
        )
        vehicle.step(out.accel_cmd, out.steer_rate_cmd)

        if out.mode is not prev_mode:
            log.events.append({"kind": f"mode:{out.mode.value}", "t": round(t, 3),
                               "reasons": list(out.reasons)})
            prev_mode = out.mode
        if out.takeover_request and log.first_event("takeover") is None:
            log.events.append({"kind": "takeover", "t": round(t, 3), "reasons": list(out.reasons)})

        log.t.append(t)
        log.speed.append(vehicle.state.speed)
        log.accel_cmd.append(out.accel_cmd)
        log.steer_rate_cmd.append(out.steer_rate_cmd)
        log.lane_offset.append(true_offset)
        log.mode.append(out.mode.value)
        log.takeover.append(out.takeover_request)
        log.latency_ms.append(max(s_off.age_ms, s_gap.age_ms if s_gap else 0.0))
        if lead_distance is not None:
            log.gap.append(lead_distance)
            log.time_gap.append(lead_distance / max(vehicle.state.speed, 0.1))

    return log
