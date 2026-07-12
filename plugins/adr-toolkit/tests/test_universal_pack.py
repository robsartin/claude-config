from pathlib import Path

from conftest import emit_real


def test_universal_pack_emits_eight_ordered_adrs_with_no_leftover_tokens(tmp_path: Path) -> None:
    written = emit_real(tmp_path, ["universal"])

    assert [p.name for p in written] == [
        "0001-record-architecture-decisions.md",
        "0002-use-test-driven-development.md",
        "0003-pr-based-trunk-workflow.md",
        "0004-mikado-method-for-changes.md",
        "0005-ci-is-the-merge-gate.md",
        "0006-keep-documentation-current.md",
        "0007-license-and-copyright.md",
        "0008-security-baseline.md",
    ]
    for path in written:
        assert "{{" not in path.read_text()
    # The license ADR references {{project}}, which must be substituted.
    assert "demo" in (written[6]).read_text()
