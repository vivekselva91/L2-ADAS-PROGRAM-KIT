"""Runs every scenario and turns the results into requirement-level evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..sim.runner import run_scenario
from ..sim.scenarios import Scenario, default_scenarios
from . import criteria as C


@dataclass
class ScenarioResult:
    scenario: Scenario
    results: list[C.CriterionResult] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)


def _criteria_for(scenario: Scenario, log) -> list[C.CriterionResult]:
    out: list[C.CriterionResult] = []
    for requirement in scenario.verifies:
        if requirement == "SYS-REQ-001":
            out.append(C.check_set_speed(log, scenario.set_speed))
        elif requirement == "SYS-REQ-002":
            out.append(C.check_time_gap(log))
        elif requirement == "SYS-REQ-003":
            out.append(C.check_safe_distance(log))
        elif requirement == "SYS-REQ-004":
            out.append(C.check_lane_accuracy(log))
        elif requirement == "SYS-REQ-005":
            out.append(C.check_lateral_disengage(log, scenario.camera_dropout[0][0]))
        elif requirement == "SYS-REQ-006":
            out.append(C.check_hands_off(log, scenario.hands_off_from_s or 0.0))
        elif requirement == "SYS-REQ-007":
            out.append(C.check_accel_bounds(log))
        elif requirement == "SYS-REQ-008":
            out.append(C.check_steer_bounds(log))
        elif requirement == "SYS-REQ-009":
            out.append(C.check_odd_exit(log))
        elif requirement == "SYS-REQ-010":
            out.append(C.check_latency(log))
    return out


def run_campaign(scenarios: list[Scenario] | None = None) -> list[ScenarioResult]:
    scenarios = scenarios or default_scenarios()
    campaign: list[ScenarioResult] = []
    for scenario in scenarios:
        log = run_scenario(scenario)
        campaign.append(ScenarioResult(scenario, _criteria_for(scenario, log), log.events))
    return campaign


def requirement_status(campaign: list[ScenarioResult]) -> dict[str, dict[str, Any]]:
    """Collapse scenario results into one verdict per requirement."""
    status: dict[str, dict[str, Any]] = {}
    for scenario_result in campaign:
        for result in scenario_result.results:
            entry = status.setdefault(
                result.requirement,
                {"passed": True, "evidence": [], "scenarios": []},
            )
            entry["passed"] = entry["passed"] and result.passed
            entry["scenarios"].append(scenario_result.scenario.id)
            entry["evidence"].append(
                {
                    "scenario": scenario_result.scenario.id,
                    "measured": result.measured,
                    "limit": result.limit,
                    "passed": result.passed,
                }
            )
    return status
