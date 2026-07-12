from pathlib import Path

from adr_toolkit.manifest import load_manifest


def test_load_manifest_reads_yaml(tmp_path: Path) -> None:
    path = tmp_path / "packs.yaml"
    path.write_text("packs:\n  tdd:\n    axis: universal\n    path: universal\n")

    manifest = load_manifest(path)

    assert manifest["packs"]["tdd"] == {"axis": "universal", "path": "universal"}
