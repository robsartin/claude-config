from pathlib import Path

from conftest import emit_slugs


def test_react_web_frontend_d3_emits_d3react_and_a11yreact_not_d3plain(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["web-frontend", "react", "d3"])

    assert "d3-with-react" in found
    assert "accessibility-in-react" in found
    assert "d3-with-plain-dom" not in found
    # interactions emit last, after react (ui-tech) and d3 (library)
    assert found.index("react-conventions") < found.index("d3-with-react")


def test_d3_plain_js_emits_only_the_plain_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["plain-js", "d3"])

    assert "d3-with-plain-dom" in found
    assert "d3-with-react" not in found
    assert "accessibility-in-react" not in found


def test_react_without_d3_has_no_d3_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["web-frontend", "react"])

    assert "accessibility-in-react" in found
    assert not any(s.startswith("d3-with") for s in found)
