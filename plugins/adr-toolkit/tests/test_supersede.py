from pathlib import Path

import pytest

from adr_toolkit.supersede import (
    AlreadySupersededError,
    EmptyTitleError,
    OldAdrNotFoundError,
    SupersedeError,
    slugify,
    supersede,
)

_OLD_ADR = """---
status: Accepted
date: "2026-07-01"
topic: use-gradle
tags: [build, java]
supersedes: []
related: [java-conventions]
---
# 3. Use Gradle for the build

## Context

We need a JVM build tool that supports incremental compilation and a plugin ecosystem.
This sentence must survive superseding byte-for-byte.

## Decision

We adopt Gradle as the build tool for all JVM projects.

## Alternatives considered

- **Maven** — rejected because its XML configuration is more verbose.

## Consequences

- Builds are faster thanks to incremental compilation.
"""


def _write_old_adr(adr_dir: Path, filename: str = "0003-use-gradle.md") -> Path:
    adr_dir.mkdir(parents=True, exist_ok=True)
    path = adr_dir / filename
    path.write_text(_OLD_ADR)
    return path


class TestSlugify:
    def test_lowercases_and_hyphenates(self) -> None:
        assert slugify("Use Bazel instead of Gradle") == "use-bazel-instead-of-gradle"

    def test_collapses_punctuation_runs(self) -> None:
        assert slugify("Use  Bazel -- instead!! of Gradle??") == "use-bazel-instead-of-gradle"

    def test_strips_leading_and_trailing_dashes(self) -> None:
        assert slugify("--Already Slugged--") == "already-slugged"

    def test_handles_mixed_case_and_numbers(self) -> None:
        assert slugify("Adopt Python 3.12") == "adopt-python-3-12"


class TestResolveOld:
    def test_resolves_by_number_prefix(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        new_path, old_path = supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")

        assert old_path.name == "0003-use-gradle.md"
        assert new_path.name == "0004-use-bazel-instead-of-gradle.md"

    def test_resolves_by_topic_slug(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        new_path, old_path = supersede(adr_dir, "use-gradle", "Use Bazel instead", "2026-07-11")

        assert old_path.name == "0003-use-gradle.md"
        assert new_path.name == "0004-use-bazel-instead.md"

    def test_missing_ref_raises(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        with pytest.raises(OldAdrNotFoundError) as excinfo:
            supersede(adr_dir, "no-such-topic", "New title", "2026-07-11")

        assert excinfo.value.ref == "no-such-topic"

    def test_ambiguous_number_raises(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir, "0003-use-gradle.md")
        _write_old_adr(adr_dir, "0003-duplicate.md")

        with pytest.raises(OldAdrNotFoundError):
            supersede(adr_dir, "0003", "New title", "2026-07-11")


class TestNewAdr:
    def test_filename_and_number(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        new_path, _ = supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")

        assert new_path.exists()
        assert new_path.name == "0004-use-bazel-instead-of-gradle.md"

    def test_frontmatter_and_heading(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        new_path, _ = supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        content = new_path.read_text()

        assert "status: Accepted" in content
        assert 'date: "2026-07-11"' in content
        assert "topic: use-bazel-instead-of-gradle" in content
        assert "tags: [build, java]" in content
        assert "supersedes: [use-gradle]" in content
        assert "related: [use-gradle]" in content
        assert "# 4. Use Bazel instead of Gradle" in content

    def test_stub_has_all_four_sections(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        new_path, _ = supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        content = new_path.read_text()

        sections = ("## Context", "## Decision", "## Alternatives considered", "## Consequences")
        for section in sections:
            assert section in content
        assert content.count("_TODO: fill in._") == 4


class TestOldAdr:
    def test_status_becomes_superseded_by(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        old_path = _write_old_adr(adr_dir)

        supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        content = old_path.read_text()

        assert 'status: "Superseded by 0004"' in content

    def test_superseded_by_added_and_related_appended(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        old_path = _write_old_adr(adr_dir)

        supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        content = old_path.read_text()

        assert "superseded-by: [use-bazel-instead-of-gradle]" in content
        assert "related: [java-conventions, use-bazel-instead-of-gradle]" in content

    def test_old_body_text_is_byte_for_byte_unchanged(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        old_path = _write_old_adr(adr_dir)
        original_body = _OLD_ADR.split("\n---\n", 1)[1]

        supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        content = old_path.read_text()

        assert content.endswith(original_body)
        assert "This sentence must survive superseding byte-for-byte." in content

    def test_related_dedup_when_new_topic_already_present(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir(parents=True)
        path = adr_dir / "0003-use-gradle.md"
        path.write_text(
            _OLD_ADR.replace(
                "related: [java-conventions]",
                "related: [java-conventions, use-bazel-instead-of-gradle]",
            )
        )

        supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        content = path.read_text()

        related_line = next(line for line in content.splitlines() if line.startswith("related:"))
        assert related_line == "related: [java-conventions, use-bazel-instead-of-gradle]"


class TestOldAdrWithoutFrontmatter:
    def test_rewritten_old_frontmatter_uses_filename_derived_topic(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        adr_dir.mkdir(parents=True)
        old_path = adr_dir / "0003-use-gradle.md"
        old_body = (
            "# 3. Use Gradle for the build\n\n"
            "## Context\n\nNo frontmatter here.\n\n"
            "## Decision\n\nWe adopt Gradle.\n\n"
            "## Alternatives considered\n\n- **Maven** — rejected.\n\n"
            "## Consequences\n\n- Builds are faster.\n"
        )
        old_path.write_text(old_body)

        new_path, _ = supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        content = old_path.read_text()

        assert "topic: use-gradle" in content
        assert 'status: "Superseded by 0004"' in content
        assert content.endswith(old_body)
        assert new_path.exists()


class TestAlreadySuperseded:
    def test_second_supersede_raises(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")

        with pytest.raises(AlreadySupersededError) as excinfo:
            supersede(adr_dir, "0003", "Use Buck instead of Gradle", "2026-07-12")

        assert excinfo.value.superseded_by == "Superseded by 0004"

    def test_second_supersede_leaves_old_file_unchanged(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        old_path = _write_old_adr(adr_dir)

        supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")
        after_first = old_path.read_text()

        with pytest.raises(AlreadySupersededError):
            supersede(adr_dir, "0003", "Use Buck instead of Gradle", "2026-07-12")

        assert old_path.read_text() == after_first
        assert sorted(p.name for p in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md")) == [
            "0003-use-gradle.md",
            "0004-use-bazel-instead-of-gradle.md",
        ]


class TestErrorHierarchy:
    def test_old_adr_not_found_error_is_a_supersede_error(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        with pytest.raises(SupersedeError):
            supersede(adr_dir, "no-such-topic", "New title", "2026-07-11")

    def test_empty_slug_title_raises_empty_title_error(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        with pytest.raises(EmptyTitleError):
            supersede(adr_dir, "0003", "!!!", "2026-07-11")

    def test_empty_slug_title_writes_nothing(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        with pytest.raises(EmptyTitleError):
            supersede(adr_dir, "0003", "!!!", "2026-07-11")

        assert sorted(p.name for p in adr_dir.glob("*.md")) == ["0003-use-gradle.md"]
        assert not (adr_dir / "README.md").exists()


class TestIndexRebuilt:
    def test_index_lists_both_old_and_new(self, tmp_path: Path) -> None:
        adr_dir = tmp_path / "adr"
        _write_old_adr(adr_dir)

        new_path, old_path = supersede(adr_dir, "0003", "Use Bazel instead of Gradle", "2026-07-11")

        index = (adr_dir / "README.md").read_text()
        assert new_path.name in index
        assert old_path.name in index
