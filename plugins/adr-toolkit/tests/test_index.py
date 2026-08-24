from pathlib import Path

from adr_toolkit.index import _AXIS_ORDER, build_index
from adr_toolkit.manifest import load_manifest
from adr_toolkit.selection import AXIS_ORDER

_FRONTMATTER = """---
status: {status}
date: "2026-07-08"
topic: {topic}
tags: [{tags}]
supersedes: []
related: [{related}]
---
"""


def _write_adr(
    tmp_path: Path,
    filename: str,
    *,
    title: str,
    topic: str,
    tags: str,
    status: str = "Accepted",
    related: str = "",
    context: str = "",
    include_heading: bool = True,
) -> None:
    frontmatter = _FRONTMATTER.format(status=status, topic=topic, tags=tags, related=related)
    heading = f"# {title}\n\n" if include_heading else ""
    context_section = f"## Context\n\n{context}\n\n" if context else ""
    body = f"{frontmatter}{heading}{context_section}## Decision\n\nbody\n"
    (tmp_path / filename).write_text(body)


def test_build_index_groups_by_axis_in_fixed_order(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
    )
    _write_adr(
        tmp_path,
        "0002-use-python.md",
        title="2. Use Python",
        topic="use-python",
        tags="language, python",
    )
    _write_adr(
        tmp_path,
        "0003-use-django.md",
        title="3. Use Django",
        topic="use-django",
        tags="framework, django",
    )

    content = build_index(tmp_path).read_text()

    universal_entry = content.index("[1. Record decisions](0001-record-decisions.md)")
    language_entry = content.index("[2. Use Python](0002-use-python.md)")
    framework_heading = content.index("## Framework")

    assert content.index("## Universal") < content.index("## Language")
    assert content.index("## Language") < framework_heading
    assert universal_entry < content.index("## Language")
    assert language_entry < framework_heading


def test_build_index_only_renders_groups_with_adrs(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
    )

    content = build_index(tmp_path).read_text()

    assert "## Universal" in content
    assert "## Language" not in content
    assert "## Framework" not in content


def test_build_index_renders_status(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
        status="Accepted",
    )

    content = build_index(tmp_path).read_text()

    assert "- [1. Record decisions](0001-record-decisions.md) — _Accepted_" in content


def test_build_index_renders_first_context_sentence_as_summary(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
        context="Decisions need a durable record. More detail follows here that should be dropped.",
    )

    content = build_index(tmp_path).read_text()

    assert "Decisions need a durable record." in content
    assert "More detail follows" not in content


def test_build_index_omits_summary_when_no_context(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
    )

    content = build_index(tmp_path).read_text()

    lines = content.splitlines()
    entry_idx = next(i for i, ln in enumerate(lines) if "1. Record decisions" in ln)
    next_line = lines[entry_idx + 1] if len(lines) > entry_idx + 1 else ""
    # No indented summary line directly follows the entry (blank line or next section instead).
    assert not (next_line.startswith("  ") and "Related:" not in next_line)


def test_build_index_renders_related_in_related_order_limited_to_emitted_topics(
    tmp_path: Path,
) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
        related="keep-docs-current, use-python",
    )
    _write_adr(
        tmp_path,
        "0002-keep-docs-current.md",
        title="2. Keep docs current",
        topic="keep-docs-current",
        tags="universal, docs",
    )
    # Note: "use-python" is referenced in related but never emitted in this dir.

    content = build_index(tmp_path).read_text()

    assert "Related: [2. Keep docs current](0002-keep-docs-current.md)" in content
    assert "use-python" not in content.split("Related:")[1].split("\n")[0]


def test_build_index_omits_related_line_when_related_topic_not_emitted(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
        related="not-emitted-topic",
    )

    content = build_index(tmp_path).read_text()

    assert "Related:" not in content


def test_build_index_ignores_readme_itself(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
    )
    (tmp_path / "README.md").write_text("# Architecture Decision Records\n(old)\n")

    content = build_index(tmp_path).read_text()

    assert "old" not in content
    assert content.count("Record decisions") == 1


def test_index_falls_back_to_filename_when_no_heading(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-untitled.md",
        title="unused",
        topic="untitled",
        tags="universal, adr",
        include_heading=False,
    )

    content = build_index(tmp_path).read_text()

    assert "- [0001-untitled](0001-untitled.md)" in content


def test_build_index_orders_within_group_by_filename(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0002-second.md",
        title="2. Second",
        topic="second",
        tags="universal, adr",
    )
    _write_adr(
        tmp_path,
        "0001-first.md",
        title="1. First",
        topic="first",
        tags="universal, adr",
    )

    content = build_index(tmp_path).read_text()

    assert content.index("1. First") < content.index("2. Second")


def test_build_index_treats_unterminated_frontmatter_as_body(tmp_path: Path) -> None:
    (tmp_path / "0001-broken.md").write_text("---\nstatus: Accepted\n# 1. Broken\n")

    content = build_index(tmp_path).read_text()

    # No closing delimiter to parse tags from, so no real axis group — but the ADR
    # must still appear (under Uncategorized) rather than silently vanish.
    assert "## Universal" not in content
    assert "## Uncategorized" in content
    assert "[1. Broken](0001-broken.md)" in content


def test_build_index_omits_summary_when_context_section_is_last_line(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
    )
    # Context header with no following body at all (not even the helper's blank line).
    raw = (tmp_path / "0001-record-decisions.md").read_text()
    raw = raw.replace("## Decision\n\nbody\n", "")
    (tmp_path / "0001-record-decisions.md").write_text(raw + "## Context")

    content = build_index(tmp_path).read_text()

    lines = content.splitlines()
    entry_idx = next(i for i, ln in enumerate(lines) if "1. Record decisions" in ln)
    next_line = lines[entry_idx + 1] if len(lines) > entry_idx + 1 else ""
    assert not (next_line.startswith("  ") and "Related:" not in next_line)


def test_build_index_is_deterministic(tmp_path: Path) -> None:
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
        context="Decisions need a durable record.",
        related="keep-docs-current",
    )
    _write_adr(
        tmp_path,
        "0002-keep-docs-current.md",
        title="2. Keep docs current",
        topic="keep-docs-current",
        tags="universal, docs",
    )

    first = build_index(tmp_path).read_text()
    second = build_index(tmp_path).read_text()

    assert first == second


def test_frontmatterless_adr_appears_under_uncategorized(tmp_path: Path) -> None:
    # A pre-existing hand-authored ADR with no frontmatter must not vanish.
    (tmp_path / "0001-legacy-decision.md").write_text("# 1. A legacy decision\n\nbody\n")
    content = build_index(tmp_path).read_text()
    assert "## Uncategorized" in content
    # No status suffix when status is unknown, and it links to the file.
    assert "- [1. A legacy decision](0001-legacy-decision.md)\n" in content
    assert " — _" not in content.split("## Uncategorized", 1)[1]


def test_unknown_axis_tag_goes_to_uncategorized(tmp_path: Path) -> None:
    (tmp_path / "0001-x.md").write_text(
        "---\nstatus: Accepted\ntopic: x\ntags: [made-up-axis]\nrelated: []\n---\n# 1. X\n"
    )
    content = build_index(tmp_path).read_text()
    assert "## Uncategorized" in content
    assert "- [1. X](0001-x.md) — _Accepted_" in content


def test_project_axis_groups_hand_authored_adrs_first(tmp_path: Path) -> None:
    # Hand-authored, repo-specific ADRs tag themselves `project`; they belong at the
    # top of the index, above the pack-emitted baseline — not in Uncategorized.
    _write_adr(
        tmp_path,
        "0001-record-decisions.md",
        title="1. Record decisions",
        topic="record-decisions",
        tags="universal, adr",
    )
    _write_adr(
        tmp_path,
        "0018-graph-engine.md",
        title="18. Use Gremlin as the graph engine",
        topic="graph-engine",
        tags="project, graph",
    )

    content = build_index(tmp_path).read_text()

    assert "## Uncategorized" not in content
    assert content.index("## Project") < content.index("## Universal")
    assert content.index(
        "[18. Use Gremlin as the graph engine](0018-graph-engine.md)"
    ) < content.index("## Universal")


def test_project_axis_does_not_absorb_the_uncategorized_fallback(tmp_path: Path) -> None:
    # Adding a real `project` group must leave Uncategorized as the genuine
    # catch-all for ADRs with no or unrecognized axis.
    _write_adr(
        tmp_path,
        "0001-graph-engine.md",
        title="1. Use Gremlin as the graph engine",
        topic="graph-engine",
        tags="project, graph",
    )
    (tmp_path / "0002-legacy.md").write_text("# 2. A legacy decision\n\nbody\n")

    content = build_index(tmp_path).read_text()

    assert content.index("## Project") < content.index("## Uncategorized")
    assert "- [2. A legacy decision](0002-legacy.md)" in content.split("## Uncategorized", 1)[1]


def test_project_axis_is_index_only_and_not_a_pack_axis() -> None:
    # The index's axis list deliberately diverges from selection's: "project" exists
    # purely for hand-authored ADRs, so no pack declares it and the pack linter
    # (which only walks packs/) never sees a project ADR. If a pack ever adopts the
    # axis, selection.AXIS_ORDER must gain it too or order_packs will raise.
    manifest = load_manifest(Path(__file__).resolve().parents[1] / "packs.yaml")

    assert "project" not in {spec["axis"] for spec in manifest["packs"].values()}
    assert "project" not in AXIS_ORDER
    assert _AXIS_ORDER[0] == "project"
    assert set(_AXIS_ORDER) - {"project"} == set(AXIS_ORDER)
