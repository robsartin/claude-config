from pathlib import Path

from adr_toolkit.scaffold import scaffold
from conftest import make_manifest, make_pack


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _adr(axis: str, title: str) -> str:
    return (
        "---\n"
        "status: Accepted\n"
        'date: "2026-07-08"\n'
        f"tags: [{axis}]\n"
        "supersedes: []\n"
        "related: []\n"
        "---\n"
        f"# {{{{number}}}}. {title}\n"
    )


def test_scaffold_resolves_deps_interactions_orders_and_indexes(tmp_path: Path) -> None:
    packs = tmp_path / "packs"
    _write(packs / "universal" / "use-tdd.md", _adr("universal", "Use TDD"))
    _write(packs / "js-ts" / "js-ts.md", _adr("language", "Use TypeScript"))
    _write(packs / "react" / "react.md", _adr("ui-tech", "Use React"))
    _write(packs / "d3" / "d3.md", _adr("library", "Use D3"))
    _write(packs / "d3-react" / "d3-react.md", _adr("interaction", "D3 in React"))

    manifest = make_manifest(
        {
            "universal": make_pack("universal", path="universal"),
            "js-ts": make_pack("language", path="js-ts"),
            "react": make_pack("ui-tech", path="react", depends_on=["js-ts"]),
            "d3": make_pack("library", path="d3"),
            "d3-react": make_pack("interaction", path="d3-react"),
        },
        interactions=[{"when": ["d3", "react"], "adr": "d3-react"}],
    )
    target = tmp_path / "docs" / "adr"
    target.mkdir(parents=True)

    # User selects universal + react (pulls js-ts) + d3; d3+react triggers interaction.
    written, index = scaffold(packs, manifest, ["universal", "react", "d3"], {}, target)

    assert [p.name for p in written] == [
        "0001-use-tdd.md",
        "0002-js-ts.md",
        "0003-react.md",
        "0004-d3.md",
        "0005-d3-react.md",
    ]
    assert index == target / "README.md"
    assert index.read_text().count("- [") == 5
