# L2 ADAS Program Kit

A working L2 ADAS feature set (adaptive cruise, lane keeping, safety monitor) wrapped in the execution artifacts that actually take a feature from an agreed scope to a production-readiness gate: requirements with ASILs, a HARA that derives its own ratings, an interface control document, a SIL validation campaign, a traceability matrix, and a gate that can say no.

The feature code exists so the artifacts have something real to point at. The artifacts are the subject.

```bash
git clone https://github.com/<you>/l2-adas-program-kit.git
cd l2-adas-program-kit
pip install -e ".[dev]"

adaskit validate    # run the SIL campaign, print measured values per requirement
adaskit trace       # requirement -> architecture -> hazard -> evidence
adaskit gate        # production-readiness decision, exit 1 on NO-GO
adaskit all --out out/
```

## Why it is built this way

Most ADAS repositories show a controller and a plot. That demonstrates the part of the job that is already well covered by the engineering team. The hard part of shipping a driver-assistance feature with an OEM is not writing a PID loop, it is answering these questions on demand:

- Which requirement is this test closing, and what did it measure?
- Which safety goal is carried by which requirement, and who owns the interface it depends on?
- Can we ship? On what objective basis?

Those questions are what this repository answers, with tooling instead of a spreadsheet.

## What is in it

**The feature set** (`src/adaskit/features/`) — ACC with time-gap following, Stanley-style lane keeping, and a safety monitor holding every limit derived from a safety goal. The monitor is the ASIL-bearing element; the comfort functions sit behind it. Authority limiting runs on every path including degraded ones, so removing a controller bound does not change the system's outer envelope.

**The simulation** (`src/adaskit/sim/`) — kinematic bicycle model plus sensor models with transport latency, gaussian noise and dropout windows. Integration failures in the field are rarely wrong maths; they are late, noisy or missing signals, so those are the failure modes the models reproduce.

**The program artifacts** (`data/`, `src/adaskit/program/`):

| Artifact | What it does |
|---|---|
| `requirements.yaml` | 10 system requirements, each with ASIL, architecture allocation and verification method |
| `hazards.yaml` | HARA with severity, exposure and controllability per hazard |
| `interfaces.yaml` | ICD: signal owner, period, timeout and failure behaviour |
| `program/artifacts.py` | Derives ASIL from S/E/C using the ISO 26262-3 table, in code |
| `program/trace.py` | Requirement to architecture to hazard to measured evidence |
| `program/gate.py` | Five objective gate criteria, non-zero exit on NO-GO |

**The validation campaign** (`src/adaskit/validation/`) — eight scenarios, each declaring which requirements it verifies. Acceptance criteria are functions, not prose, so requirement coverage is computed rather than claimed.

| Scenario | Exercises | Measured |
|---|---|---|
| SCN-001 Free-flow speed hold | Set-speed tracking, command bounds, latency | 0.00 m/s error, 45 ms p95 |
| SCN-002 Steady-state following | Time gap | 1.70 s against a 1.50 s floor |
| SCN-003 Lead vehicle hard brake | Braking authority, safe distance | 27.97 m minimum gap |
| SCN-004 Curve lane keeping | Lateral accuracy, steering rate | 0.113 m against a 0.300 m limit |
| SCN-005 Camera dropout | Degradation and takeover timing | Disengage at 300 ms |
| SCN-006 Hands-off escalation | Warning and disengage thresholds | Warn 15.0 s, stop 25.0 s |
| SCN-007 ODD exit | Disengage outside the ODD | Disengaged 0.08 s after ODD exit |
| SCN-008 Radar dropout | Degradation to speed control | Time gap held at 1.70 s |

## Four findings worth reading

The validation campaign failed three scenarios on its first run, and the traceability tool caught a fourth problem that no test would have found. What was done about each is in `docs/decision-log.md`, and it is the most useful part of this repository.

**An ODD floor that fights a safety requirement** (DEC-003, still open). A lead vehicle braking hard drove the ego below the 8 m/s ODD floor. The monitor correctly latched DISENGAGED per SYS-REQ-009, zeroed the acceleration command, and the ego closed on the lead. Two requirements were individually correct and jointly wrong: neither said what happens when the ODD exit is caused by the braking event the system is responding to. The release is scoped with the limitation documented and a platform requirement raised for the next vehicle line, rather than patched quietly.

**A latency budget booked at the wrong boundary** (DEC-002). SYS-REQ-005 allows 300 ms from lane signal loss to lateral disengagement. The monitor used a 300 ms timeout and measured 360 ms end to end, because camera transport latency sat on top of the budget instead of inside it. Monitor timeout rebudgeted to 250 ms.

**Safety goals rated above the requirements carrying them** (DEC-005). Requirements were hand-labelled ASIL-B during drafting. Once the HARA derived ratings from the S/E/C table, four requirements sat below their own safety goals, two of which were ASIL-D. Both documents looked finished, and nothing compared them. The ratings were corrected and GATE-06 now fails the release whenever a requirement sits below the goal it carries.

**Gains that got worse when pushed harder** (DEC-004). Lateral deviation started at 0.69 m against a 0.30 m requirement. Raising the cross-track gain made the loop unstable and it diverged to 885 m. A three-parameter sweep against SCN-004 selected on measured deviation with steering-rate margin as the tie-breaker: 0.11 m deviation at a 0.19 rad/s peak, inside the 0.35 rad/s driver-override limit.

## Traceability, end to end

```
stakeholder need -> system requirement -> architecture element -> scenario -> measured evidence
                          |
                       hazard -> safety goal -> derived ASIL
```

`adaskit trace` renders all of it, including the measured value and limit behind every PASS. ASILs are derived from the S/E/C table in code rather than typed into a spreadsheet, so a rating cannot drift away from its justification; `test_asil_table_matches_iso26262` pins the table against ISO 26262-3.

## The gate

```
| ID | Criterion | Measured | Target | Result |
| GATE-01 | Every requirement is verified by at least one scenario | 100.0% | >= 100.0% | PASS |
| GATE-02 | Every requirement passes its acceptance criteria | 100.0% | >= 100.0% | PASS |
| GATE-03 | No ASIL-rated requirement is open | 0 open | 0 open | PASS |
| GATE-04 | Every safety goal is carried by passing requirements | 5/5 | all covered | PASS |
| GATE-05 | No validation scenario is failing | 0 failing | 0 failing | PASS |
| GATE-06 | No requirement is declared below the ASIL of the goal it carries | 0 mismatched | 0 mismatched | PASS |
```

`adaskit gate` exits non-zero on NO-GO, so CI blocks a release that has not earned one. A gate that cannot say no is a status meeting.

## Documentation

- `docs/program-plan.md` — phase gates G0 to G4, operating cadence, risk and dependency handling, and how findings feed back into the platform
- `docs/aspice-mapping.md` — which artifact answers which ASPICE process area and ISO 26262 clause
- `docs/decision-log.md` — five decisions with context, consequence and follow-up

## Development

```bash
make dev      # install with test extras
make test     # 21 tests
make lint     # ruff
make reports  # regenerate every artifact into out/
```

CI runs lint, unit tests, the SIL campaign and the gate on every push, and uploads the generated evidence as a build artifact.

## Scope and honesty

This is a portfolio piece, not a production stack. The vehicle model is kinematic, the sensor models are statistical rather than physical, and there is no HIL, no real ECU, no AUTOSAR and no cybersecurity analysis. The requirements set is ten items where a real vehicle line carries thousands. What it does represent faithfully is the shape of the work: how requirements, hazards, interfaces, validation evidence and a release decision hold together, and what it looks like when they disagree.

## License

MIT. See [LICENSE](LICENSE).
