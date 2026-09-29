"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .program.gate import evaluate_gate
from .program.report import gate_report, hara_report, interface_report, traceability_report
from .validation.harness import run_campaign


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="adaskit",
        description="L2 ADAS feature set with ASPICE-style execution artifacts.",
    )
    parser.add_argument(
        "command",
        choices=["validate", "trace", "gate", "hara", "icd", "all"],
        help="validate: run the SIL campaign | trace: traceability matrix | "
             "gate: production-readiness decision | hara: hazard analysis | icd: interfaces",
    )
    parser.add_argument("--out", metavar="DIR", help="write reports to this directory")
    args = parser.parse_args(argv)

    if args.command in ("hara", "icd"):
        text = hara_report() if args.command == "hara" else interface_report()
        _emit(text, args.out, f"{args.command}.md")
        return 0

    campaign = run_campaign()
    decision = evaluate_gate(campaign)

    if args.command in ("validate", "all"):
        for result in campaign:
            mark = "PASS" if result.passed else "FAIL"
            print(f"[{mark}] {result.scenario.id} {result.scenario.name}")
            for criterion in result.results:
                sub = "ok " if criterion.passed else "NOK"
                print(f"       {sub} {criterion.requirement}: "
                      f"{criterion.measured} (limit {criterion.limit})")
    if args.command in ("trace", "all"):
        _emit(traceability_report(decision), args.out, "traceability.md")
    if args.command in ("gate", "all"):
        _emit(gate_report(decision, campaign), args.out, "gate.md")
    if args.command == "all":
        _emit(hara_report(), args.out, "hara.md")
        _emit(interface_report(), args.out, "icd.md")

    print(f"\nGate decision: {'GO' if decision.go else 'NO-GO'}")
    return 0 if decision.go else 1


def _emit(text: str, out_dir: str | None, filename: str) -> None:
    if out_dir:
        path = Path(out_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / filename).write_text(text, encoding="utf-8")
        print(f"wrote {path / filename}")
    else:
        print(text)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
