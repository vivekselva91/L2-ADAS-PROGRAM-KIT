# Program plan

The engineering plan for one vehicle line, in the form a joint OEM and supplier
team can actually run against.

## Phase gates

| Gate | Purpose | Exit criteria | Evidence |
|---|---|---|---|
| G0 Feature definition | Agree the feature set and ODD | Requirements baselined, HARA complete, ASILs derived | `data/requirements.yaml`, `adaskit hara` |
| G1 Technical alignment | Fix interfaces and ownership | ICD signed, timing and failure behaviour agreed | `adaskit icd` |
| G2 Integration | Feature running on target | SIL campaign executing, no ASIL requirement unverified | `adaskit validate` |
| G3 Validation complete | Evidence closed | 100% requirement coverage, all criteria passing | `adaskit trace` |
| G4 SOP readiness | Production go/no-go | All gate criteria pass, blockers empty | `adaskit gate` |

## Operating cadence

| Forum | Frequency | Output |
|---|---|---|
| Integration stand-up | Daily | Blocker list with named owners |
| Issue review | Weekly | Root cause, ownership, containment, closure date |
| Gate review | Per gate | GO / NO-GO with evidence attached |
| OEM program review | Bi-weekly | Status, risk, recovery plan, decisions needed |

Every review reads from the same generated artifacts. Status is not retyped into
slides, which is what stops the program and the evidence drifting apart.

## Risk and dependency management

Risks are tracked with owner, trigger, mitigation and a review date. A risk
without a named owner and a trigger is not a risk, it is a worry. Dependencies
between OEM and supplier scope are recorded in the ICD, where each signal has an
owner and a defined failure behaviour.

## Feedback into the platform

Findings from each vehicle line are triaged into one of three buckets: fix in
this program, fix in the platform, or accept and document. DEC-003 is an example
of the third, promoted to a platform requirement for the next line. This is how
customer-specific integration work becomes reusable platform capability instead
of accumulating as per-OEM forks.
