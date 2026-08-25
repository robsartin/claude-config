from pathlib import Path

from conftest import emit_slugs


def test_svelte_pulls_the_js_ts_base(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["svelte"])

    assert "svelte-conventions" in found
    # Svelte is a ui-tech pack over the JS/TS language base.
    assert "js-ts-project" in found


def test_accessibility_with_svelte_triggers_the_svelte_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["accessibility", "svelte"])

    assert "accessibility-baseline" in found
    assert "accessibility-in-svelte" in found
    assert "accessibility-in-react" not in found
    assert "accessibility-in-vue" not in found


def test_d3_with_svelte_triggers_the_svelte_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["d3", "svelte"])

    assert "d3-baseline" in found
    assert "d3-with-svelte" in found
    assert "d3-with-react" not in found
    assert "d3-with-vue" not in found


def test_i18n_with_svelte_is_covered_at_the_language_level(tmp_path: Path) -> None:
    """i18n interactions key on language, not ui-tech — as they do for React and Vue.

    Svelte depends on js-ts, so selecting i18n alongside it fires [i18n, js-ts].
    """
    found = emit_slugs(tmp_path, ["i18n", "svelte"])

    assert "i18n-in-js-ts" in found
    assert "i18n-in-svelte" not in found


def test_every_js_ui_tech_keeps_its_own_interactions(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["accessibility", "react", "vue", "svelte"])

    assert "accessibility-in-react" in found
    assert "accessibility-in-vue" in found
    assert "accessibility-in-svelte" in found
    assert found.count("accessibility-baseline") == 1
    assert found.count("js-ts-project") == 1
