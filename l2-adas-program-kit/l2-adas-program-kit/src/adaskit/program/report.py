"""Markdown reporting: the artifacts a program review actually consumes."""

from __future__ import annotations

from datetime import datetime, timezone

from ..validation.harness import ScenarioResult
from .artifacts import load_hazards, load_interfaces
from .gate import GateDecision

_MARK = {True: "PASS", False: "FAIL"}


def gate_report(decision: GateDecision, campaign: list[ScenarioResult]) -> str:
    metrics = decision.matrix["metrics"]
    verdict = "GO" if decision.go else "NO-GO"
    lines = [
        f"# {decision.name}",
        "",
        f"**Decision: {verdict}**  |  generated {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "## Gate criteria",
        "",
        "| ID | Criterion | Measured | Target | Result |",
        "|---|---|---|---|---|",
    ]
    for c in decision.criteria:
        lines.append(f"| {c.id} | {c.description} | {c.measured} | {c.target} | {_MARK[c.passed]} |")

    if decision.blockers:
        lines += ["", "## Blockers", ""]
        lines += [f"- **{c.id}**: {c.description} (measured {c.measured}, target {c.target})"
                  for c in decision.blockers]

    lines += [
        "",
        "## Readiness metrics",
        "",
        (f"- Requirements verified: {metrics['requirements_verified']}"
         f"/{metrics['requirements_total']} ({metrics['coverage_pct']}%)"),
        (f"- Requirements passing: {metrics['requirements_passed']}"
         f"/{metrics['requirements_total']} ({metrics['pass_pct']}%)"),
        f"- Safety goals covered: {metrics['safety_goals_covered']}/{metrics['safety_goals_total']}",
        "",
        "## Scenario results",
        "",
        "| Scenario | Name | Verifies | Result |",
        "|---|---|---|---|",
    ]
    for result in campaign:
        lines.append(
            f"| {result.scenario.id} | {result.scenario.name} | "
            f"{', '.join(result.scenario.verifies)} | {_MARK[result.passed]} |"
        )
    return "\n".join(lines) + "\n"


def traceability_report(decision: GateDecision) -> str:
    matrix = decision.matrix
    lines = [
        "# Requirements traceability matrix",
        "",
        "Stakeholder need -> system requirement -> architecture element -> verification evidence.",
        "",
        "| Requirement | Title | ASIL | Allocated to | Hazards | Verified by | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in matrix["rows"]:
        lines.append(
            f"| {row['id']} | {row['title']} | {row['asil']} | {', '.join(row['allocated_to'])} | "
            f"{', '.join(row['hazards']) or '-'} | {', '.join(row['verified_by']) or '-'} | "
            f"{row['status']} |"
        )

    lines += ["", "## Measured evidence", "",
              "| Requirement | Scenario | Measured | Limit | Result |", "|---|---|---|---|---|"]
    for row in matrix["rows"]:
        for ev in row["evidence"]:
            lines.append(
                f"| {row['id']} | {ev['scenario']} | {ev['measured']} | {ev['limit']} | "
                f"{_MARK[ev['passed']]} |"
            )

    lines += ["", "## Safety goals (ISO 26262)", "",
              "| Goal | Hazard | Derived ASIL | Requirements | Covered |", "|---|---|---|---|---|"]
    for goal in matrix["safety_goals"]:
        lines.append(
            f"| {goal['goal_id']} | {goal['hazard']} | {goal['derived_asil']} | "
            f"{', '.join(goal['declared_requirements'])} | {_MARK[goal['covered']]} |"
        )
    return "\n".join(lines) + "\n"


def hara_report() -> str:
    hazards = load_hazards()
    lines = [
        "# Hazard analysis and risk assessment",
        "",
        "ASIL is derived from the ISO 26262-3 S/E/C table in code, so the rating",
        "cannot drift away from its justification.",
        "",
        "| ID | Hazard | Situation | S | E | C | Derived ASIL | Safety goal |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for h in hazards:
        lines.append(
            f"| {h['id']} | {h['hazard']} | {h['situation']} | {h['severity']} | {h['exposure']} | "
            f"{h['controllability']} | **{h['derived_asil']}** | {h['goal_id']}: {h['safety_goal']} |"
        )
    return "\n".join(lines) + "\n"


def interface_report() -> str:
    interfaces = load_interfaces()
    lines = [
        "# Interface control document",
        "",
        "Every signal has a named owner and a defined failure behaviour. Integration",
        "disputes are settled here rather than during a vehicle build.",
        "",
        "| ID | Signal | Producer | Consumer | Owner | Period | Timeout | On timeout |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i in interfaces:
        lines.append(
            f"| {i['id']} | `{i['signal']}` | {i['producer']} | {i['consumer']} | {i['owner']} | "
            f"{i['period_ms']} ms | {i['timeout_ms']} ms | {i['on_timeout']} |"
        )
    return "\n".join(lines) + "\n"
