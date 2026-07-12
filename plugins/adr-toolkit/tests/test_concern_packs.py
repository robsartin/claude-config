from pathlib import Path

from conftest import emit_slugs


def test_concern_bases_emit_and_are_opt_in(tmp_path: Path) -> None:
    # A plain CLI without concerns gets none of them.
    cli_only = emit_slugs(tmp_path, ["cli"])
    concern_prefixes = ("internationalization", "observability", "privacy")
    assert not any(s.startswith(concern_prefixes) for s in cli_only)

    with_concerns = emit_slugs(tmp_path / "b", ["cli", "i18n", "observability", "privacy"])
    assert "internationalization-baseline" in with_concerns
    assert "observability-baseline" in with_concerns
    assert "privacy-and-data-handling" in with_concerns


def test_i18n_interaction_matches_selected_language(tmp_path: Path) -> None:
    py = emit_slugs(tmp_path, ["python", "i18n"])
    assert "i18n-in-python" in py
    assert "i18n-on-the-jvm" not in py
    assert "i18n-in-js-ts" not in py

    jvm = emit_slugs(tmp_path / "b", ["kotlin", "i18n"])
    assert "i18n-on-the-jvm" in jvm
    assert "i18n-in-python" not in jvm


def test_observability_spring_boot_interaction(tmp_path: Path) -> None:
    slug_list = emit_slugs(tmp_path, ["spring-boot", "observability"])
    assert "observability-in-spring-boot" in slug_list
    # js-ts obs interaction must NOT appear without js-ts selected
    assert "observability-in-js-ts" not in slug_list
