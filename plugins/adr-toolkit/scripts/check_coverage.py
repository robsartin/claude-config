"""Enforce the U5 coverage gate: line > 80% AND branch > 65%, as two thresholds.

coverage.py's ``fail_under`` is a single blended number and cannot express both,
so this reads ``coverage json`` totals and checks each rate independently.
"""

import json
import sys
from collections.abc import Mapping

LINE_MIN = 80.0
BRANCH_MIN = 65.0


def evaluate(
    totals: Mapping[str, float],
    line_min: float = LINE_MIN,
    branch_min: float = BRANCH_MIN,
) -> list[str]:
    """Return a list of human-readable errors; empty means the gate passes."""
    errors = []

    statements = totals["num_statements"]
    line_pct = 100.0 * totals["covered_lines"] / statements if statements else 100.0
    if line_pct < line_min:
        errors.append(f"line coverage {line_pct:.1f}% is below {line_min:.0f}%")

    branches = totals["num_branches"]
    branch_pct = 100.0 * totals["covered_branches"] / branches if branches else 100.0
    if branch_pct < branch_min:
        errors.append(f"branch coverage {branch_pct:.1f}% is below {branch_min:.0f}%")

    return errors


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else "coverage.json"
    totals = json.load(open(path))["totals"]  # noqa: SIM115

    errors = evaluate(totals)
    for error in errors:
        print(f"::error::{error}")
    if errors:
        return 1
    print(
        f"coverage gate passed "
        f"(line {100.0 * totals['covered_lines'] / max(totals['num_statements'], 1):.1f}%, "
        f"branch {100.0 * totals['covered_branches'] / max(totals['num_branches'], 1):.1f}%)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
