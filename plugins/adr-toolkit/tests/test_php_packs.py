from pathlib import Path

import pytest

from conftest import emit_real, emit_slugs, slugs

PHP_BASE = ["php-project-layout", "php-quality-and-tests"]


@pytest.mark.parametrize(
    ("framework", "expected"),
    [
        ("laravel", ["laravel-conventions", "laravel-testing-and-operability"]),
        ("symfony", ["symfony-conventions", "symfony-testing-and-operability"]),
    ],
)
def test_should_pull_php_base_first_when_framework_selected(
    tmp_path: Path, framework: str, expected: list[str]
) -> None:
    written = emit_real(tmp_path, [framework])

    # php base (language axis) precedes the framework pack (framework axis).
    assert slugs(written) == PHP_BASE + expected
    for path in written:
        assert "{{" not in path.read_text()


def test_should_emit_only_php_base_when_language_selected_alone(tmp_path: Path) -> None:
    assert emit_slugs(tmp_path, ["php"]) == PHP_BASE


def test_should_emit_i18n_in_php_when_i18n_and_php_selected(tmp_path: Path) -> None:
    with_php = emit_slugs(tmp_path, ["php", "i18n"])
    assert "i18n-in-php" in with_php
    # Pulled in by the framework's depends_on, too.
    assert "i18n-in-php" in emit_slugs(tmp_path / "b", ["laravel", "i18n"])


def test_should_not_emit_i18n_in_php_when_other_language_selected(tmp_path: Path) -> None:
    assert "i18n-in-php" not in emit_slugs(tmp_path, ["python", "i18n"])
    assert "i18n-in-php" not in emit_slugs(tmp_path / "b", ["php"])
