from check_coverage import evaluate


def _totals(
    covered_lines: int,
    num_statements: int,
    covered_branches: int,
    num_branches: int,
) -> dict[str, float]:
    return {
        "covered_lines": covered_lines,
        "num_statements": num_statements,
        "covered_branches": covered_branches,
        "num_branches": num_branches,
    }


def test_meeting_both_thresholds_passes() -> None:
    assert evaluate(_totals(90, 100, 70, 100)) == []


def test_line_coverage_below_threshold_is_reported() -> None:
    errors = evaluate(_totals(70, 100, 70, 100))

    assert len(errors) == 1
    assert "line coverage 70.0%" in errors[0]
    assert "80%" in errors[0]


def test_branch_coverage_below_threshold_is_reported() -> None:
    errors = evaluate(_totals(90, 100, 60, 100))

    assert len(errors) == 1
    assert "branch coverage 60.0%" in errors[0]
    assert "65%" in errors[0]


def test_both_below_threshold_reports_both() -> None:
    errors = evaluate(_totals(70, 100, 60, 100))

    assert len(errors) == 2


def test_branch_gate_is_independent_of_the_blended_total() -> None:
    """The point of the gate: a high line rate must not mask a low branch rate.

    coverage.py's fail_under blends both into one number, so this case slips
    through it — 95 lines + 50 branches averages above 80.
    """
    errors = evaluate(_totals(95, 100, 50, 100))

    assert len(errors) == 1
    assert "branch coverage" in errors[0]


def test_exactly_at_threshold_passes() -> None:
    assert evaluate(_totals(80, 100, 65, 100)) == []


def test_no_statements_or_branches_counts_as_fully_covered() -> None:
    assert evaluate(_totals(0, 0, 0, 0)) == []


def test_thresholds_are_overridable() -> None:
    assert evaluate(_totals(70, 100, 60, 100), line_min=70.0, branch_min=60.0) == []
