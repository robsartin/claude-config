from pathlib import Path

from conftest import emit_real, emit_slugs, slugs


def test_selecting_kotlin_pulls_jvm_base_first(tmp_path: Path) -> None:
    written = emit_real(tmp_path, ["universal", "kotlin"])

    # jvm base ADRs precede the kotlin-specific one.
    assert slugs(written)[-3:] == [
        "jvm-build-with-gradle",
        "jvm-quality-and-tests",
        "kotlin-conventions",
    ]
    for path in written:
        assert "{{" not in path.read_text()


def test_java_and_js_ts_packs_emit(tmp_path: Path) -> None:
    assert emit_slugs(tmp_path, ["java"]) == [
        "jvm-build-with-gradle",
        "jvm-quality-and-tests",
        "java-conventions",
    ]
    assert emit_slugs(tmp_path / "b", ["js-ts"]) == ["js-ts-project", "js-ts-toolchain"]


def test_jvm_base_uses_derived_package_token(tmp_path: Path) -> None:
    written = emit_real(tmp_path, ["jvm"])
    build_adr = next(p for p in written if "jvm-build" in p.name)
    assert "com.robsartin.demo" in build_adr.read_text()
