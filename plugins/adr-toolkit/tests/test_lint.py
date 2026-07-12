"""Unit + integration tests for the ADR content linter.

Consolidates what used to be tests/test_frontmatter.py, tests/test_adr_sections.py, and
tests/test_related.py into exercising a single reusable validator (adr_toolkit.lint).
"""

from pathlib import Path

import yaml

from adr_toolkit.lint import SECTIONS, lint_packs
from adr_toolkit.manifest import load_manifest
from adr_toolkit.types import Manifest
from conftest import REPO, make_manifest, make_pack


def _write(
    path: Path,
    frontmatter: dict[str, object],
    body_sections: dict[str, str] | None = None,
    section_order: list[str] | None = None,
    extra_tail: str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    order = section_order if section_order is not None else list(SECTIONS)
    sections = body_sections or {}
    body_parts = [
        f"{section}\n\n{sections.get(section, f'Body text for {section}.')}\n" for section in order
    ]
    body = "\n".join(body_parts) + "\n" + extra_tail
    text = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n" + body
    path.write_text(text)


def _clean_frontmatter(
    topic: str, axis: str, related: list[str] | None = None
) -> dict[str, object]:
    return {
        "status": "Accepted",
        "date": "{{date}}",
        "topic": topic,
        "tags": [axis],
        "supersedes": [],
        "related": related or [],
    }


def _alpha_path(packs_dir: Path) -> Path:
    return packs_dir / "alpha" / "01-alpha-topic.md"


def _build_clean(tmp_path: Path) -> tuple[Path, Manifest]:
    packs_dir = tmp_path / "packs"
    _write(
        _alpha_path(packs_dir),
        _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"]),
    )
    _write(
        packs_dir / "beta" / "01-beta-topic.md",
        _clean_frontmatter("beta-topic", "language"),
    )
    manifest = make_manifest(
        {
            "alpha": make_pack("universal", path="alpha"),
            "beta": make_pack("language", path="beta"),
        }
    )
    return packs_dir, manifest


def test_clean_packs_have_no_violations(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    assert lint_packs(packs_dir, manifest) == []


def test_missing_frontmatter_key_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    del fm["status"]
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("missing keys" in v for v in violations)


def test_wrong_status_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    fm["status"] = "Proposed"
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("status" in v for v in violations)


def test_wrong_date_token_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    fm["date"] = "2026-01-01"
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("date" in v for v in violations)


def test_non_empty_supersedes_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    fm["supersedes"] = ["0001-something"]
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("supersedes" in v for v in violations)


def test_wrong_topic_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("not-alpha-topic", "universal", related=["beta-topic"])
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("topic" in v for v in violations)


def test_axis_not_first_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    fm["tags"] = ["wrong-axis", "universal"]
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("axis" in v for v in violations)


def test_tags_not_a_list_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    fm["tags"] = "universal"
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("tags" in v for v in violations)


def test_related_target_not_a_real_topic_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["nonexistent-topic"])
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("not known topics" in v for v in violations)


def test_related_self_reference_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["alpha-topic"])
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("self-reference" in v for v in violations)


def test_related_duplicate_entries_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic", "beta-topic"])
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("duplicate" in v for v in violations)


def test_related_not_a_list_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    fm["related"] = "beta-topic"
    _write(_alpha_path(packs_dir), fm)

    violations = lint_packs(packs_dir, manifest)
    assert any("related must be a list" in v for v in violations)


def test_missing_section_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    _write(
        _alpha_path(packs_dir), fm, section_order=["## Context", "## Decision", "## Consequences"]
    )

    violations = lint_packs(packs_dir, manifest)
    assert any("missing section" in v for v in violations)


def test_out_of_order_sections_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    _write(
        _alpha_path(packs_dir),
        fm,
        section_order=[
            "## Context",
            "## Alternatives considered",
            "## Decision",
            "## Consequences",
        ],
    )

    violations = lint_packs(packs_dir, manifest)
    assert any("out of order" in v for v in violations)


def test_empty_alternatives_section_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    _write(_alpha_path(packs_dir), fm, body_sections={"## Alternatives considered": ""})

    violations = lint_packs(packs_dir, manifest)
    assert any("empty Alternatives" in v for v in violations)


def test_leftover_date_bullet_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    _write(_alpha_path(packs_dir), fm, body_sections={"## Consequences": "- **Date:** 2026-01-01"})

    violations = lint_packs(packs_dir, manifest)
    assert any("Date bullet" in v for v in violations)


def test_leftover_status_bullet_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    _write(_alpha_path(packs_dir), fm, body_sections={"## Consequences": "- **Status:** Accepted"})

    violations = lint_packs(packs_dir, manifest)
    assert any("Status bullet" in v for v in violations)


def test_disallowed_token_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    fm = _clean_frontmatter("alpha-topic", "universal", related=["beta-topic"])
    _write(_alpha_path(packs_dir), fm, extra_tail="{{proejct}}\n")

    violations = lint_packs(packs_dir, manifest)
    assert any("token" in v for v in violations)


def test_frontmatter_not_a_mapping_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    _alpha_path(packs_dir).write_text("---\n- a\n- b\n---\n## Context\n\nbody\n")

    violations = lint_packs(packs_dir, manifest)
    assert any("mapping" in v for v in violations)


def test_missing_frontmatter_delimiter_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    _alpha_path(packs_dir).write_text("no frontmatter here\n")

    violations = lint_packs(packs_dir, manifest)
    assert any("frontmatter" in v for v in violations)


def test_unterminated_frontmatter_delimiter_is_reported(tmp_path: Path) -> None:
    packs_dir, manifest = _build_clean(tmp_path)
    _alpha_path(packs_dir).write_text("---\nstatus: Accepted\n")

    violations = lint_packs(packs_dir, manifest)
    assert any("frontmatter" in v for v in violations)


def test_real_packs_are_clean() -> None:
    manifest = load_manifest(REPO / "packs.yaml")
    assert lint_packs(REPO / "packs", manifest) == []
