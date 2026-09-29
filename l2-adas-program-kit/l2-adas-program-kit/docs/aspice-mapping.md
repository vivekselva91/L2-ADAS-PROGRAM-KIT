# ASPICE process mapping

How the artifacts in this repository line up with Automotive SPICE process areas.
The point is not certification, it is showing which artifact answers which
assessor question.

| Process | Question an assessor asks | Artifact here |
|---|---|---|
| SYS.1 Requirements elicitation | Where do requirements come from? | `parent` field links each requirement to a stakeholder need |
| SYS.2 System requirements analysis | Are requirements verifiable and attributed? | `data/requirements.yaml`, each with ASIL and verification method |
| SYS.3 Architectural design | Which element implements which requirement? | `allocated_to` field; `adaskit trace` renders the allocation |
| SYS.4 Integration and integration test | Is integration tested against the architecture? | `src/adaskit/sim/runner.py` wires the elements; SCN-001..008 exercise them |
| SYS.5 Qualification test | Is every requirement verified with evidence? | `adaskit trace` coverage table with measured values |
| SWE.1–SWE.6 | Same chain at software level | Controllers and monitor with unit tests in `tests/` |
| SUP.1 Quality assurance | Can a release be blocked objectively? | `adaskit gate`, non-zero exit on NO-GO |
| SUP.8 Configuration management | Is the evidence reproducible? | Fixed seeds; CI regenerates all reports per commit |
| SUP.9 Problem resolution | Are issues root-caused and closed? | `docs/decision-log.md` |
| SUP.10 Change request management | Are changes traceable to a decision? | Decision log entries reference the requirements they move |
| MAN.3 Project management | Are gates and cadence defined? | `docs/program-plan.md` |

## ISO 26262 touchpoints

| Clause area | Artifact |
|---|---|
| Part 3, HARA and ASIL determination | `data/hazards.yaml` plus the S/E/C table in `program/artifacts.py` |
| Part 3, safety goals | `goal_id` per hazard, traced to requirements |
| Part 4, technical safety requirements | ASIL-rated entries in `requirements.yaml` |
| Part 4, safety mechanism | `features/safety_monitor.py` |
| Part 4, verification | Scenario evidence in `adaskit trace` |

ASIL values are derived in code from severity, exposure and controllability
rather than typed in by hand, so a rating cannot drift away from its
justification. `test_asil_table_matches_iso26262` pins the table.
