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


def test_line_below_threshold_is_reported() -> None:
    errors = evaluate(_totals(75, 100, 70, 100))
    assert len(errors) == 1
    assert "line" in errors[0].lower()


def test_branch_below_threshold_is_reported() -> None:
    errors = evaluate(_totals(90, 100, 60, 100))
    assert len(errors) == 1
    assert "branch" in errors[0].lower()


def test_both_below_threshold_reports_both() -> None:
    assert len(evaluate(_totals(50, 100, 50, 100))) == 2


def test_no_branches_does_not_divide_by_zero() -> None:
    # A project with no branches has vacuously-satisfied branch coverage.
    assert evaluate(_totals(90, 100, 0, 0)) == []


def test_exact_thresholds_pass() -> None:
    assert evaluate(_totals(80, 100, 65, 100)) == []
