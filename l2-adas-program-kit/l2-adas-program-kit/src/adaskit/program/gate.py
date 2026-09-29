"""Production-readiness gate.

A gate is only useful if it can say no. Each criterion is objective and
computed from campaign evidence, and the exit code is non-zero on NO-GO so CI
blocks a release that has not earned one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..validation.harness import ScenarioResult
from .trace import build_matrix


@dataclass
class GateCriterion:
    id: str
    description: str
    measured: str
    target: str
    passed: bool
    blocking: bool = True


@dataclass
class GateDecision:
    name: str
    criteria: list[GateCriterion] = field(default_factory=list)
    matrix: dict[str, Any] = field(default_factory=dict)

    @property
    def go(self) -> bool:
        return all(c.passed for c in self.criteria if c.blocking)

    @property
    def blockers(self) -> list[GateCriterion]:
        return [c for c in self.criteria if c.blocking and not c.passed]


_ASIL_RANK = {"QM": 0, "ASIL-A": 1, "ASIL-B": 2, "ASIL-C": 3, "ASIL-D": 4}


def _asil_mismatches(matrix: dict[str, Any]) -> list[str]:
    """Catch the classic spreadsheet error: a safety goal rated ASIL-D carried by
    a requirement someone typed as ASIL-B. Without decomposition rationale, the
    requirement must be at least as high as its goal."""
    declared = {row["id"]: row["asil"] for row in matrix["rows"]}
    out = []
    for goal in matrix["safety_goals"]:
        goal_rank = _ASIL_RANK[goal["derived_asil"]]
        for rid in goal["declared_requirements"]:
            if _ASIL_RANK.get(declared.get(rid, "QM"), 0) < goal_rank:
                out.append(f"{rid} ({declared.get(rid)}) < {goal['goal_id']} ({goal['derived_asil']})")
    return out


def evaluate_gate(
    campaign: list[ScenarioResult],
    name: str = "SOP readiness gate",
    min_coverage_pct: float = 100.0,
    min_pass_pct: float = 100.0,
) -> GateDecision:
    matrix = build_matrix(campaign)
    metrics = matrix["metrics"]
    asil_failures = [
        row for row in matrix["rows"]
        if row["asil"].startswith("ASIL") and row["status"] != "PASS"
    ]
    scenario_failures = [r.scenario.id for r in campaign if not r.passed]
    asil_mismatches = _asil_mismatches(matrix)

    criteria = [
        GateCriterion(
            "GATE-01", "Every requirement is verified by at least one scenario",
            f"{metrics['coverage_pct']}%", f">= {min_coverage_pct}%",
            metrics["coverage_pct"] >= min_coverage_pct,
        ),
        GateCriterion(
            "GATE-02", "Every requirement passes its acceptance criteria",
            f"{metrics['pass_pct']}%", f">= {min_pass_pct}%",
            metrics["pass_pct"] >= min_pass_pct,
        ),
        GateCriterion(
            "GATE-03", "No ASIL-rated requirement is open",
            f"{len(asil_failures)} open", "0 open", not asil_failures,
        ),
        GateCriterion(
            "GATE-04", "Every safety goal is carried by passing requirements",
            f"{metrics['safety_goals_covered']}/{metrics['safety_goals_total']}",
            "all covered",
            metrics["safety_goals_covered"] == metrics["safety_goals_total"],
        ),
        GateCriterion(
            "GATE-05", "No validation scenario is failing",
            f"{len(scenario_failures)} failing", "0 failing", not scenario_failures,
        ),
        GateCriterion(
            "GATE-06", "No requirement is declared below the ASIL of the goal it carries",
            f"{len(asil_mismatches)} mismatched", "0 mismatched", not asil_mismatches,
        ),
    ]
    return GateDecision(name=name, criteria=criteria, matrix=matrix)
