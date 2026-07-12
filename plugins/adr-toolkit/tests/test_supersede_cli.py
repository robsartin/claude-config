from pathlib import Path

import pytest

from adr_toolkit.supersede_cli import main

_OLD_ADR = """---
status: Accepted
date: "2026-07-01"
topic: use-gradle
tags: [build, java]
supersedes: []
related: []
---
# 3. Use Gradle for the build

## Context

We need a JVM build tool.

## Decision

We adopt Gradle.

## Alternatives considered

- **Maven** — rejected.

## Consequences

- Builds are faster.
"""


def _fixture(tmp_path: Path) -> Path:
    adr_dir = tmp_path / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0003-use-gradle.md").write_text(_OLD_ADR)
    return adr_dir


def test_happy_path_writes_new_flips_old_and_returns_zero(tmp_path: Path) -> None:
    adr_dir = _fixture(tmp_path)

    rc = main(
        [
            "--target",
            str(adr_dir),
            "--old",
            "0003",
            "--title",
            "Use Bazel instead of Gradle",
            "--date",
            "2026-07-11",
        ]
    )

    assert rc == 0
    new_path = adr_dir / "0004-use-bazel-instead-of-gradle.md"
    old_path = adr_dir / "0003-use-gradle.md"
    assert new_path.exists()
    assert 'status: "Superseded by 0004"' in old_path.read_text()
    assert (adr_dir / "README.md").exists()


def test_prints_expected_messages(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    adr_dir = _fixture(tmp_path)

    rc = main(
        [
            "--target",
            str(adr_dir),
            "--old",
            "0003",
            "--title",
            "Use Bazel instead of Gradle",
            "--date",
            "2026-07-11",
        ]
    )

    assert rc == 0
    out = capsys.readouterr().out
    assert "superseded" in out
    assert "wrote" in out
    assert "0004-use-bazel-instead-of-gradle.md" in out
    assert "index" in out


def test_unknown_old_ref_fails_loudly_and_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    adr_dir = _fixture(tmp_path)

    rc = main(
        [
            "--target",
            str(adr_dir),
            "--old",
            "no-such-topic",
            "--title",
            "Use Bazel instead of Gradle",
            "--date",
            "2026-07-11",
        ]
    )

    assert rc == 2
    err = capsys.readouterr().err
    assert "no-such-topic" in err
    assert not (adr_dir / "0004-use-bazel-instead-of-gradle.md").exists()
    # old ADR is untouched
    assert adr_dir.joinpath("0003-use-gradle.md").read_text() == _OLD_ADR


def test_empty_slug_title_fails_loudly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    adr_dir = _fixture(tmp_path)

    rc = main(
        [
            "--target",
            str(adr_dir),
            "--old",
            "0003",
            "--title",
            "!!!",
            "--date",
            "2026-07-11",
        ]
    )

    assert rc == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert not (adr_dir / "0004-.md").exists()


def test_already_superseded_fails_loudly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    adr_dir = _fixture(tmp_path)
    main(
        [
            "--target",
            str(adr_dir),
            "--old",
            "0003",
            "--title",
            "Use Bazel instead of Gradle",
            "--date",
            "2026-07-11",
        ]
    )
    capsys.readouterr()

    rc = main(
        [
            "--target",
            str(adr_dir),
            "--old",
            "0003",
            "--title",
            "Use Buck instead of Gradle",
            "--date",
            "2026-07-12",
        ]
    )

    assert rc == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert not (adr_dir / "0005-use-buck-instead-of-gradle.md").exists()


def test_default_date_is_today(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import datetime

    adr_dir = _fixture(tmp_path)

    class _FixedDate(datetime.date):
        @classmethod
        def today(cls) -> "_FixedDate":
            return cls(2026, 7, 11)

    monkeypatch.setattr(datetime, "date", _FixedDate)

    rc = main(
        [
            "--target",
            str(adr_dir),
            "--old",
            "0003",
            "--title",
            "Use Bazel instead of Gradle",
        ]
    )

    assert rc == 0
    new_path = adr_dir / "0004-use-bazel-instead-of-gradle.md"
    assert 'date: "2026-07-11"' in new_path.read_text()
