from pathlib import Path

import pytest

from conftest import emit_real, emit_slugs, slugs


@pytest.mark.parametrize("framework", ["django", "fastapi", "flask"])
def test_should_pull_python_base_and_emit_after_it_when_framework_selected(
    tmp_path: Path, framework: str
) -> None:
    written = emit_real(tmp_path, [framework])

    # python base (language axis) precedes the framework axis.
    assert slugs(written) == [
        "python-project-layout",
        "python-toolchain",
        f"{framework}-conventions",
        f"{framework}-testing-and-operability",
    ]
    for path in written:
        assert "{{" not in path.read_text()


def test_should_fire_python_observability_interaction_when_framework_and_observability_selected(
    tmp_path: Path,
) -> None:
    found = emit_slugs(tmp_path, ["fastapi", "observability"])

    assert "observability-baseline" in found
    assert "observability-in-python" in found
    assert "observability-in-js-ts" not in found


def test_should_not_fire_python_observability_interaction_without_observability(
    tmp_path: Path,
) -> None:
    assert "observability-in-python" not in emit_slugs(tmp_path, ["django"])


def test_should_keep_frameworks_distinct_when_several_selected(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["django", "flask"])

    assert "django-conventions" in found
    assert "flask-conventions" in found
    assert "fastapi-conventions" not in found
    assert found.count("python-toolchain") == 1
