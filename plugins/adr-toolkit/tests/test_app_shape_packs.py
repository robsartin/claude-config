from pathlib import Path

from conftest import emit_real, emit_slugs, slugs


def test_cli_and_service_packs_emit(tmp_path: Path) -> None:
    assert emit_slugs(tmp_path, ["cli"]) == ["cli-conventions"]
    assert emit_slugs(tmp_path / "b", ["service"]) == ["service-conventions"]


def test_web_frontend_pulls_shared_accessibility_baseline(tmp_path: Path) -> None:
    written = emit_real(tmp_path, ["web-frontend"])
    # accessibility is a shared dependency, so it emits before web-frontend.
    assert slugs(written) == ["accessibility-baseline", "web-frontend-baseline"]
    for path in written:
        assert "{{" not in path.read_text()
