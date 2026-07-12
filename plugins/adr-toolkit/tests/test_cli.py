from pathlib import Path

import pytest

from adr_toolkit.cli import main


def test_cli_scaffolds_adrs_with_derived_context(tmp_path: Path) -> None:
    packs = tmp_path / "packs"
    (packs / "universal").mkdir(parents=True)
    (packs / "universal" / "use-tdd.md").write_text(
        "# {{number}}. Use TDD for {{project}}\nPackage: {{package}}\nDate: {{date}}\n"
    )
    manifest = tmp_path / "packs.yaml"
    manifest.write_text("packs:\n  universal:\n    axis: universal\n    path: universal\n")
    target = tmp_path / "repo" / "docs" / "adr"
    target.mkdir(parents=True)

    rc = main(
        [
            "--manifest",
            str(manifest),
            "--packs-dir",
            str(packs),
            "--target",
            str(target),
            "--project",
            "mise",
            "--date",
            "2026-07-07",
            "--pack",
            "universal",
        ]
    )

    assert rc == 0
    assert (target / "0001-use-tdd.md").read_text() == (
        "# 1. Use TDD for mise\nPackage: com.robsartin.mise\nDate: 2026-07-07\n"
    )
    assert (target / "README.md").exists()


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    packs = tmp_path / "packs"
    (packs / "universal").mkdir(parents=True)
    (packs / "universal" / "01-record.md").write_text("# {{number}}. Record\n")
    (packs / "universal" / "02-use-tdd.md").write_text("# {{number}}. TDD\n")
    manifest = tmp_path / "packs.yaml"
    manifest.write_text("packs:\n  universal:\n    axis: universal\n    path: universal\n")
    target = tmp_path / "repo" / "docs" / "adr"
    return packs, manifest, target


def _args(packs: Path, manifest: Path, target: Path) -> list[str]:
    return [
        "--manifest",
        str(manifest),
        "--packs-dir",
        str(packs),
        "--target",
        str(target),
        "--project",
        "demo",
        "--date",
        "2026-07-09",
        "--pack",
        "universal",
    ]


def test_plan_prints_topics_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packs, manifest, target = _fixture(tmp_path)

    rc = main([*_args(packs, manifest, target), "--plan"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "0001  record" in out
    assert "0002  use-tdd" in out
    assert not target.exists()


def test_exclude_skips_the_topic(tmp_path: Path) -> None:
    packs, manifest, target = _fixture(tmp_path)

    rc = main([*_args(packs, manifest, target), "--exclude", "record"])

    assert rc == 0
    assert (target / "0001-use-tdd.md").exists()
    assert not (target / "0002-record.md").exists()


def test_unmatched_exclude_fails_loudly_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packs, manifest, target = _fixture(tmp_path)

    rc = main([*_args(packs, manifest, target), "--exclude", "no-such-topic"])

    assert rc == 2
    err = capsys.readouterr().err
    assert "no-such-topic" in err
    assert not target.exists()


def test_unmatched_exclude_fails_under_plan_too(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packs, manifest, target = _fixture(tmp_path)

    rc = main([*_args(packs, manifest, target), "--exclude", "no-such-topic", "--plan"])

    assert rc == 2
    captured = capsys.readouterr()
    assert "no-such-topic" in captured.err
    # No partial plan listing was printed before failing.
    assert captured.out == ""


def test_unknown_pack_fails_loudly_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    packs, manifest, target = _fixture(tmp_path)

    rc = main(
        [
            "--manifest",
            str(manifest),
            "--packs-dir",
            str(packs),
            "--target",
            str(target),
            "--project",
            "demo",
            "--date",
            "2026-07-09",
            "--pack",
            "no-such-pack",
        ]
    )

    assert rc == 2
    assert "no-such-pack" in capsys.readouterr().err
    assert not target.exists()
