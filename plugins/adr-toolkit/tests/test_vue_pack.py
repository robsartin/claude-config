from pathlib import Path

from conftest import emit_slugs


def test_vue_pulls_the_js_ts_base(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["vue"])

    assert "vue-conventions" in found
    # Vue is a ui-tech pack over the JS/TS language base.
    assert "js-ts-project" in found


def test_accessibility_with_vue_triggers_the_vue_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["accessibility", "vue"])

    assert "accessibility-baseline" in found
    assert "accessibility-in-vue" in found
    assert "accessibility-in-react" not in found


def test_d3_with_vue_triggers_the_vue_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["d3", "vue"])

    assert "d3-baseline" in found
    assert "d3-with-vue" in found
    assert "d3-with-react" not in found


def test_i18n_with_vue_is_covered_at_the_language_level(tmp_path: Path) -> None:
    """i18n interactions key on language, not ui-tech — as they do for React.

    Vue depends on js-ts, so selecting i18n alongside it fires [i18n, js-ts].
    There is deliberately no i18n-vue pack, mirroring the absent i18n-react.
    """
    found = emit_slugs(tmp_path, ["i18n", "vue"])

    assert "i18n-in-js-ts" in found
    assert "i18n-in-vue" not in found


def test_selecting_vue_and_react_together_keeps_each_interaction_distinct(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["accessibility", "vue", "react"])

    assert "accessibility-in-vue" in found
    assert "accessibility-in-react" in found
    assert found.count("accessibility-baseline") == 1
