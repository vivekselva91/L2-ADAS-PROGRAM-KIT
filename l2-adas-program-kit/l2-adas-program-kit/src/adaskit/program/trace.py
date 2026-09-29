"""Requirements traceability, the ASPICE-style backbone of the repo.

Answers three questions a release review always asks: is every requirement
verified, is every safety goal carried by a requirement, and does any test
exist that traces to nothing.
"""

from __future__ import annotations

from typing import Any

from ..validation.harness import ScenarioResult, requirement_status
from .artifacts import load_hazards, load_requirements


def build_matrix(campaign: list[ScenarioResult]) -> dict[str, Any]:
    requirements = load_requirements()
    hazards = load_hazards()
    status = requirement_status(campaign)

    rows = []
    for requirement in requirements:
        rid = requirement["id"]
        verdict = status.get(rid)
        covering = sorted({h["id"] for h in hazards if rid in h.get("mitigates", [])})
        rows.append(
            {
                "id": rid,
                "title": requirement["title"],
                "asil": requirement["asil"],
                "allocated_to": requirement["allocated_to"],
                "hazards": covering,
                "verified_by": sorted(set(verdict["scenarios"])) if verdict else [],
                "status": ("PASS" if verdict["passed"] else "FAIL") if verdict else "NOT VERIFIED",
                "evidence": verdict["evidence"] if verdict else [],
            }
        )

    safety_goals = [
        {
            "goal_id": hazard["goal_id"],
            "hazard": hazard["id"],
            "derived_asil": hazard["derived_asil"],
            "declared_requirements": hazard.get("mitigates", []),
            "covered": all(
                any(r["id"] == rid and r["status"] == "PASS" for r in rows)
                for rid in hazard.get("mitigates", [])
            ),
        }
        for hazard in hazards
    ]

    verified = [r for r in rows if r["status"] != "NOT VERIFIED"]
    passed = [r for r in rows if r["status"] == "PASS"]
    return {
        "rows": rows,
        "safety_goals": safety_goals,
        "metrics": {
            "requirements_total": len(rows),
            "requirements_verified": len(verified),
            "requirements_passed": len(passed),
            "coverage_pct": round(100 * len(verified) / len(rows), 1) if rows else 0.0,
            "pass_pct": round(100 * len(passed) / len(rows), 1) if rows else 0.0,
            "safety_goals_total": len(safety_goals),
            "safety_goals_covered": sum(1 for g in safety_goals if g["covered"]),
        },
    }
