from pathlib import Path

from conftest import emit_slugs


def test_swift_language_pack_covers_build_and_quality(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["swift"])

    assert "swift-build-with-spm" in found
    assert "swift-quality-and-tests" in found


def test_swiftui_pulls_the_swift_language_base(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["swiftui"])

    assert "swiftui-conventions" in found
    # SwiftUI is a ui-tech pack over the Swift language base.
    assert "swift-build-with-spm" in found


def test_accessibility_with_swiftui_triggers_the_swiftui_interaction(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["accessibility", "swiftui"])

    assert "accessibility-baseline" in found
    assert "accessibility-in-swiftui" in found
    assert "accessibility-in-compose" not in found


def test_native_ui_with_swiftui_pulls_the_shared_baseline_once(tmp_path: Path) -> None:
    """native-ui depends on accessibility, so the interaction fires without naming it."""
    found = emit_slugs(tmp_path, ["native-ui", "swiftui"])

    assert found.count("accessibility-baseline") == 1
    assert "accessibility-in-swiftui" in found


def test_swift_and_jvm_native_stacks_stay_independent(tmp_path: Path) -> None:
    found = emit_slugs(tmp_path, ["accessibility", "swiftui", "compose"])

    assert "accessibility-in-swiftui" in found
    assert "accessibility-in-compose" in found
    assert "swift-build-with-spm" in found
    assert "jvm-build-with-gradle" in found
