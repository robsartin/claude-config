from pathlib import Path

from conftest import emit_real, slugs


def test_spring_boot_pulls_jvm_base_and_emits_after_it(tmp_path: Path) -> None:
    written = emit_real(tmp_path, ["spring-boot"])

    # jvm base (language axis) precedes spring-boot (framework axis).
    assert slugs(written) == [
        "jvm-build-with-gradle",
        "jvm-quality-and-tests",
        "spring-boot-conventions",
        "spring-boot-testing-and-operability",
    ]
    for path in written:
        assert "{{" not in path.read_text()
