from pathlib import Path

from conftest import emit_real


def test_python_pack_emits_after_universal_with_no_leftover_tokens(tmp_path: Path) -> None:
    written = emit_real(tmp_path, ["universal", "python"])

    names = [p.name for p in written]
    # Universal (language axis follows universal), then the Python pack.
    assert names[-2:] == [
        "0009-python-project-layout.md",
        "0010-python-toolchain.md",
    ]
    for path in written:
        assert "{{" not in path.read_text()
