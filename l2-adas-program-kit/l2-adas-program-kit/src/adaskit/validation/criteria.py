"""Acceptance criteria, one function per requirement.

Keeping criteria as code (rather than prose in a test plan) is what lets the
release gate compute requirement coverage automatically: every criterion names
the requirement it closes, and every scenario names the criteria it runs.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..sim.runner import RunLog


@dataclass
class CriterionResult:
    requirement: str
    passed: bool
    measured: str
    limit: str


def _settled(values: list[float], fraction: float = 0.5) -> list[float]:
    start = int(len(values) * fraction)
    return values[start:] or values


def check_set_speed(log: RunLog, set_speed: float) -> CriterionResult:
    error = max(abs(v - set_speed) for v in _settled(log.speed))
    return CriterionResult("SYS-REQ-001", error <= 1.0, f"{error:.2f} m/s", "<= 1.00 m/s")


def check_time_gap(log: RunLog) -> CriterionResult:
    if not log.time_gap:
        return CriterionResult("SYS-REQ-002", True, "no lead vehicle", ">= 1.50 s")
    worst = min(_settled(log.time_gap))
    return CriterionResult("SYS-REQ-002", worst >= 1.5, f"{worst:.2f} s", ">= 1.50 s")


def check_safe_distance(log: RunLog) -> CriterionResult:
    if not log.gap:
        return CriterionResult("SYS-REQ-003", True, "no lead vehicle", "> 0 m")
    worst = min(log.gap)
    return CriterionResult("SYS-REQ-003", worst > 5.0, f"{worst:.2f} m", "> 5.00 m")


def check_lane_accuracy(log: RunLog) -> CriterionResult:
    active = [abs(o) for o, m in zip(log.lane_offset, log.mode) if m == "ACTIVE"]
    worst = max(_settled(active)) if active else 0.0
    return CriterionResult("SYS-REQ-004", worst <= 0.30, f"{worst:.3f} m", "<= 0.300 m")


def check_lateral_disengage(log: RunLog, dropout_start: float) -> CriterionResult:
    event = next((e for e in log.events if e["kind"] == "mode:LATERAL_DEGRADED"), None)
    if event is None:
        return CriterionResult("SYS-REQ-005", False, "no disengage", "<= 300 ms after loss")
    delay_ms = (event["t"] - dropout_start) * 1000.0
    return CriterionResult(
        "SYS-REQ-005", 0 <= delay_ms <= 350.0, f"{delay_ms:.0f} ms", "<= 350 ms after loss"
    )


def check_hands_off(log: RunLog, hands_off_from: float) -> CriterionResult:
    warn = next((e for e in log.events if e["kind"] == "mode:TAKEOVER_REQUESTED"), None)
    stop = next((e for e in log.events if e["kind"] == "mode:DISENGAGED"), None)
    if warn is None or stop is None:
        return CriterionResult("SYS-REQ-006", False, "escalation incomplete", "warn 15 s, stop 25 s")
    warn_dt = warn["t"] - hands_off_from
    stop_dt = stop["t"] - hands_off_from
    ok = 14.5 <= warn_dt <= 16.0 and 24.5 <= stop_dt <= 26.0
    return CriterionResult(
        "SYS-REQ-006", ok, f"warn {warn_dt:.1f} s, stop {stop_dt:.1f} s", "warn 15 s, stop 25 s"
    )


def check_accel_bounds(log: RunLog) -> CriterionResult:
    lo, hi = min(log.accel_cmd), max(log.accel_cmd)
    ok = lo >= -3.5001 and hi <= 2.0001
    return CriterionResult("SYS-REQ-007", ok, f"[{lo:.2f}, {hi:.2f}] m/s2", "[-3.50, 2.00] m/s2")


def check_steer_bounds(log: RunLog) -> CriterionResult:
    worst = max(abs(v) for v in log.steer_rate_cmd)
    return CriterionResult("SYS-REQ-008", worst <= 0.3501, f"{worst:.3f} rad/s", "<= 0.350 rad/s")


def check_odd_exit(log: RunLog) -> CriterionResult:
    below = [t for t, v in zip(log.t, log.speed) if v < 8.0]
    if not below:
        return CriterionResult("SYS-REQ-009", True, "stayed inside ODD", "disengage outside ODD")
    disengaged = next((e for e in log.events if e["kind"] == "mode:DISENGAGED"), None)
    ok = disengaged is not None and disengaged["t"] <= below[0] + 0.1
    return CriterionResult(
        "SYS-REQ-009", ok,
        f"disengaged at {disengaged['t']:.2f} s" if disengaged else "never disengaged",
        f"<= {below[0] + 0.1:.2f} s",
    )


def check_latency(log: RunLog) -> CriterionResult:
    ordered = sorted(log.latency_ms)
    p95 = ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]
    return CriterionResult("SYS-REQ-010", p95 <= 150.0, f"{p95:.0f} ms p95", "<= 150 ms p95")
