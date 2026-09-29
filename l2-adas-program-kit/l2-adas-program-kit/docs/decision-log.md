# Decision log

Decisions that changed scope, design or acceptance criteria. Each entry records
what was decided, why, and what it cost, so a later reviewer does not have to
reconstruct the reasoning from commit history.

---

## DEC-001 — Safety authority lives in the monitor, not the features

**Date:** 2026-02-10 · **Status:** Accepted · **Owner:** Program

**Context.** ACC and LKA both need bounded output. The bounds could live inside
each controller or in a separate element.

**Decision.** The safety monitor owns every limit derived from a safety goal.
ACC and LKA apply their own bounds for comfort, but the monitor re-applies them
on every path including degraded modes.

**Consequence.** The comfort functions can be argued at QM while the monitor
carries ASIL-B. The bounds are duplicated, which is intentional: a test that
removes the controller bound must still pass.

---

## DEC-002 — Lane-signal timeout budgeted at 250 ms, not 300 ms

**Date:** 2026-02-18 · **Status:** Accepted · **Owner:** Systems

**Context.** SYS-REQ-005 requires lateral disengagement within 300 ms of lane
signal loss. The first implementation used a 300 ms monitor timeout and measured
360 ms end to end, failing SCN-005.

**Decision.** Budget the monitor timeout at 250 ms so camera transport latency
(~45 ms) fits inside the requirement rather than on top of it.

**Consequence.** Measured disengage is now 300 ms. The requirement is met
end to end rather than at the monitor boundary. Nuisance disengagement risk
rises slightly on marginal lane markings; accepted pending fleet data.

---

## DEC-003 — ODD floor interaction during hard braking, left open

**Date:** 2026-02-20 · **Status:** Open · **Owner:** Systems / Safety

**Context.** During validation, a lead vehicle braking from 28 m/s to 4 m/s drove
the ego below the 8 m/s ODD floor. The monitor latched DISENGAGED per
SYS-REQ-009, zeroed the acceleration command, and the simulated ego closed on
the lead with no driver intervention modelled.

**Root cause.** Two requirements are individually correct and jointly wrong.
SYS-REQ-009 disengages outside the ODD; SYS-REQ-003 requires the system to keep
a safe distance. Neither says what happens when the ODD exit is *caused by* the
braking event the system is responding to.

**Decision.** Scope the current release to an ODD floor of 8 m/s and document the
limitation. SCN-003 was retargeted to a 28 -> 16 m/s brake so it measures braking
authority; SCN-007 covers the ODD handover separately.

**Follow-up.** A stop-and-go extension needs a new requirement covering handover
during active deceleration, with a hold-brake behaviour until the driver responds.
Tracked for the next vehicle line. This is exactly the kind of finding that should
feed back into the product rather than be patched per OEM.

---

## DEC-004 — Lateral gains tuned by sweep, not by feel

**Date:** 2026-02-22 · **Status:** Accepted · **Owner:** Development

**Context.** The initial gains held 0.69 m of lateral deviation on a 300 m curve
against a 0.30 m requirement. Raising the cross-track gain to 2.6 made it worse:
the loop went unstable and diverged to 885 m.

**Decision.** Sweep the three gains against SCN-004 and select on measured
deviation with steering-rate margin as the tie-breaker. Selected 0.20 / 1.20 /
3.00, giving 0.11 m deviation at a 0.19 rad/s peak rate.

**Consequence.** Lateral accuracy passes with margin, and peak steering rate sits
well under the 0.35 rad/s driver-override limit from SG-002.

---

## DEC-005 — ASIL mismatch between safety goals and requirements

**Date:** 2026-02-24 · **Status:** Accepted · **Owner:** Safety

**Context.** The requirements were hand-labelled ASIL-B during drafting. Once the
HARA derived its ratings from the S/E/C table, three safety goals came out higher
than the requirements carrying them: SG-001 and SG-002 at ASIL-C, SG-004 and
SG-005 at ASIL-D.

**Root cause.** The ratings were typed in before the hazard analysis was complete
and never revisited. Nothing in the process compared the two, which is exactly the
kind of gap that survives to an assessment because both documents look finished.

**Decision.** Raise SYS-REQ-003 and SYS-REQ-006 to ASIL-D, and SYS-REQ-007 and
SYS-REQ-008 to ASIL-C, matching their goals. Add GATE-06 so the gate fails
whenever a requirement sits below the goal it carries.

**Consequence.** The inconsistency cannot reappear silently. If a future change
lowers a requirement or a HARA revision raises a goal, CI blocks the release.
ASIL decomposition remains available later, but it needs written rationale rather
than a quiet downgrade.
