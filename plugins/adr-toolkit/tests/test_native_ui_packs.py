from pathlib import Path

from conftest import emit_slugs


def test_native_ui_with_compose_pulls_shared_a11y_and_compose_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["native-ui", "compose"])

    # Shared accessibility baseline is pulled (native-ui depends on it).
    assert "accessibility-baseline" in found
    # Compose pulls the jvm base.
    assert "jvm-build-with-gradle" in found
    # accessibility + compose triggers the Compose a11y interaction, not the React one.
    assert "accessibility-in-compose" in found
    assert "accessibility-in-react" not in found


def test_shared_accessibility_baseline_is_emitted_once_for_web_and_native(tmp_path: Path) -> None:
    # Selecting both UI shapes must not duplicate the shared accessibility ADR.
    found = emit_slugs(tmp_path, ["web-frontend", "native-ui"])
    assert found.count("accessibility-baseline") == 1
