"""Enforce the universal coverage gate: line > 80% AND branch > 65%.

coverage.py's ``fail_under`` is a single blended number and cannot express both,
so this reads ``coverage json`` totals and checks each rate independently. These
constants are the only place the two thresholds are stated.
"""

import json
import sys
from collections.abc import Mapping

LINE_MIN = 80.0
BRANCH_MIN = 65.0


def _rate(covered: float, total: float) -> float:
    """Percentage covered; nothing to cover counts as fully covered."""
    return 100.0 * covered / total if total else 100.0


def evaluate(
    totals: Mapping[str, float],
    line_min: float = LINE_MIN,
    branch_min: float = BRANCH_MIN,
) -> list[str]:
    """Return a list of human-readable errors; empty means the gate passes."""
    errors = []

    line_pct = _rate(totals["covered_lines"], totals["num_statements"])
    if line_pct < line_min:
        errors.append(f"line coverage {line_pct:.1f}% is below {line_min:.0f}%")

    branch_pct = _rate(totals["covered_branches"], totals["num_branches"])
    if branch_pct < branch_min:
        errors.append(f"branch coverage {branch_pct:.1f}% is below {branch_min:.0f}%")

    return errors


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else "coverage.json"
    with open(path) as fh:
        totals = json.load(fh)["totals"]

    errors = evaluate(totals)
    for error in errors:
        print(f"::error::{error}")
    if errors:
        return 1
    line_pct = _rate(totals["covered_lines"], totals["num_statements"])
    branch_pct = _rate(totals["covered_branches"], totals["num_branches"])
    print(f"coverage gate passed (line {line_pct:.1f}%, branch {branch_pct:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
