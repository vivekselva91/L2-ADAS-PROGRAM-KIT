from adaskit.program.gate import evaluate_gate
from adaskit.program.report import gate_report, hara_report, interface_report, traceability_report
from adaskit.program.trace import build_matrix
from adaskit.validation.harness import run_campaign


def test_campaign_passes_and_gate_is_go():
    campaign = run_campaign()
    decision = evaluate_gate(campaign)
    failing = [r.scenario.id for r in campaign if not r.passed]
    assert not failing, f"failing scenarios: {failing}"
    assert decision.go


def test_every_requirement_is_verified():
    matrix = build_matrix(run_campaign())
    unverified = [r["id"] for r in matrix["rows"] if r["status"] == "NOT VERIFIED"]
    assert not unverified, f"requirements with no verification evidence: {unverified}"
    assert matrix["metrics"]["coverage_pct"] == 100.0


def test_gate_says_no_when_a_requirement_fails():
    campaign = run_campaign()
    campaign[0].results[0].passed = False
    decision = evaluate_gate(campaign)
    assert not decision.go
    assert decision.blockers


def test_reports_render():
    campaign = run_campaign()
    decision = evaluate_gate(campaign)
    for text in (gate_report(decision, campaign), traceability_report(decision),
                 hara_report(), interface_report()):
        assert text.startswith("#") and len(text) > 200


def test_gate_catches_asil_downgrade():
    """A requirement may not sit below the ASIL of the goal it carries (DEC-005)."""
    from adaskit.program.gate import _asil_mismatches

    matrix = {
        "rows": [{"id": "SYS-REQ-003", "asil": "ASIL-B"}],
        "safety_goals": [
            {"goal_id": "SG-005", "derived_asil": "ASIL-D",
             "declared_requirements": ["SYS-REQ-003"]}
        ],
    }
    assert _asil_mismatches(matrix), "an ASIL-B requirement under an ASIL-D goal must be flagged"

    matrix["rows"][0]["asil"] = "ASIL-D"
    assert not _asil_mismatches(matrix)


def test_live_data_has_no_asil_mismatch():
    from adaskit.program.gate import _asil_mismatches
    assert not _asil_mismatches(build_matrix(run_campaign()))
