"""Validation scenarios.

Each scenario names the requirements it exercises, so the test harness can
produce a requirement-to-evidence link rather than a bare pass/fail list.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Scenario:
    id: str
    name: str
    verifies: list[str]
    duration_s: float = 40.0
    ego_speed_0: float = 28.0
    set_speed: float = 30.0
    lead_distance_0: float | None = None
    lead_speed_0: float = 28.0
    lead_accel: Callable[[float], float] | None = None
    curvature: Callable[[float], float] = lambda t: 0.0
    camera_dropout: list[tuple[float, float]] = field(default_factory=list)
    radar_dropout: list[tuple[float, float]] = field(default_factory=list)
    hands_off_from_s: float | None = None
    description: str = ""


def _hard_brake(t: float) -> float:
    """Lead decelerates 28 -> 16 m/s. Deliberately stays inside the ODD so the
    scenario measures ACC braking authority rather than the ODD-floor handover,
    which SCN-007 covers separately (see docs/decision-log.md, DEC-003)."""
    return -4.0 if 12.0 <= t < 15.0 else 0.0


def _curve(t: float) -> float:
    # 300 m radius curve entered at t=10 s, exited at t=30 s.
    return 1 / 300.0 if 10.0 <= t < 30.0 else 0.0


def default_scenarios() -> list[Scenario]:
    return [
        Scenario(
            id="SCN-001",
            name="Free-flow speed hold",
            verifies=["SYS-REQ-001", "SYS-REQ-007", "SYS-REQ-010"],
            lead_distance_0=None,
            description="No lead vehicle. Confirms set-speed tracking and command bounds.",
        ),
        Scenario(
            id="SCN-002",
            name="Steady-state following",
            verifies=["SYS-REQ-002", "SYS-REQ-007"],
            lead_distance_0=60.0,
            lead_speed_0=26.0,
            description="Lead vehicle at constant speed. Confirms the time-gap requirement.",
        ),
        Scenario(
            id="SCN-003",
            name="Lead vehicle hard brake",
            verifies=["SYS-REQ-003", "SYS-REQ-007"],
            lead_distance_0=55.0,
            lead_speed_0=28.0,
            lead_accel=_hard_brake,
            description="Lead brakes at -4 m/s2. Confirms deceleration authority and safe distance.",
        ),
        Scenario(
            id="SCN-004",
            name="Curve lane keeping",
            verifies=["SYS-REQ-004", "SYS-REQ-008"],
            curvature=_curve,
            description="300 m radius curve. Confirms lateral accuracy and steering-rate bound.",
        ),
        Scenario(
            id="SCN-005",
            name="Camera dropout",
            verifies=["SYS-REQ-005", "SYS-REQ-008"],
            camera_dropout=[(15.0, 20.0)],
            curvature=_curve,
            description="5 s camera loss. Confirms lateral disengage and takeover request.",
        ),
        Scenario(
            id="SCN-006",
            name="Hands-off escalation",
            verifies=["SYS-REQ-006"],
            hands_off_from_s=5.0,
            description="Driver hands off from t=5 s. Confirms warning and disengage timing.",
        ),
        Scenario(
            id="SCN-007",
            name="ODD exit on low speed",
            verifies=["SYS-REQ-009"],
            ego_speed_0=10.0,
            set_speed=10.0,
            lead_distance_0=40.0,
            lead_speed_0=6.0,
            lead_accel=lambda t: -0.6 if t > 5 else 0.0,
            description="Traffic slows below the ODD floor. Confirms disengage with takeover.",
        ),
        Scenario(
            id="SCN-008",
            name="Radar dropout while following",
            verifies=["SYS-REQ-002", "SYS-REQ-010"],
            lead_distance_0=60.0,
            lead_speed_0=26.0,
            radar_dropout=[(18.0, 19.0)],
            description="1 s radar loss. Confirms graceful degradation to speed control.",
        ),
    ]
