from pathlib import Path

from adr_toolkit.emit import emit
from adr_toolkit.types import Manifest
from conftest import make_manifest, make_pack


def test_emit_writes_numbered_adr_into_target(tmp_path: Path) -> None:
    packs = tmp_path / "packs"
    (packs / "universal").mkdir(parents=True)
    (packs / "universal" / "use-tdd.md").write_text("# {{number}}. Use TDD\nDate: {{date}}\n")
    target = tmp_path / "repo" / "docs" / "adr"
    target.mkdir(parents=True)

    manifest = make_manifest({"universal": make_pack("universal", path="universal")})

    written = emit(packs, manifest, ["universal"], {"date": "2026-07-07"}, target)

    assert written == [target / "0001-use-tdd.md"]
    assert (target / "0001-use-tdd.md").read_text() == "# 1. Use TDD\nDate: 2026-07-07\n"


def test_emit_appends_after_existing_adrs(tmp_path: Path) -> None:
    packs = tmp_path / "packs"
    (packs / "universal").mkdir(parents=True)
    (packs / "universal" / "use-tdd.md").write_text("# {{number}}. Use TDD\n")
    target = tmp_path / "docs" / "adr"
    target.mkdir(parents=True)
    (target / "0001-record-decisions.md").write_text("# 1. Record decisions\n")

    written = emit(packs, manifest_for("universal"), ["universal"], {}, target)

    assert written == [target / "0002-use-tdd.md"]
    assert (target / "0002-use-tdd.md").read_text() == "# 2. Use TDD\n"


def test_emit_orders_by_numeric_prefix_and_strips_it_from_slug(tmp_path: Path) -> None:
    packs = tmp_path / "packs"
    (packs / "universal").mkdir(parents=True)
    (packs / "universal" / "01-record-decisions.md").write_text("# {{number}}. Record\n")
    (packs / "universal" / "02-use-tdd.md").write_text("# {{number}}. TDD\n")
    target = tmp_path / "docs" / "adr"
    target.mkdir(parents=True)

    written = emit(packs, manifest_for("universal"), ["universal"], {}, target)

    assert [p.name for p in written] == ["0001-record-decisions.md", "0002-use-tdd.md"]


def test_emit_creates_target_dir_when_missing(tmp_path: Path) -> None:
    packs = tmp_path / "packs"
    (packs / "universal").mkdir(parents=True)
    (packs / "universal" / "use-tdd.md").write_text("# {{number}}. TDD\n")
    target = tmp_path / "repo" / "docs" / "adr"  # does not exist yet

    written = emit(packs, manifest_for("universal"), ["universal"], {}, target)

    assert written == [target / "0001-use-tdd.md"]
    assert (target / "0001-use-tdd.md").exists()


def test_emit_skips_excluded_topics_without_gaps(tmp_path: Path) -> None:
    packs = tmp_path / "packs"
    (packs / "universal").mkdir(parents=True)
    (packs / "universal" / "01-record.md").write_text("# {{number}}. Record\n")
    (packs / "universal" / "02-use-tdd.md").write_text("# {{number}}. TDD\n")
    (packs / "universal" / "03-license.md").write_text("# {{number}}. License\n")
    target = tmp_path / "docs" / "adr"

    written = emit(packs, manifest_for("universal"), ["universal"], {}, target, exclude=["use-tdd"])

    assert [p.name for p in written] == ["0001-record.md", "0002-license.md"]


def manifest_for(*pack_ids: str) -> Manifest:
    return make_manifest({pid: make_pack("universal", path=pid) for pid in pack_ids})
