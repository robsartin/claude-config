"""Generate a grouped, frontmatter-aware ``README.md`` index of a ``docs/adr/`` directory."""

from pathlib import Path
from typing import Any, NamedTuple

import yaml

from adr_toolkit.planning import topic_of
from adr_toolkit.types import StrPath

_HEADING = "# Architecture Decision Records"
_FRONTMATTER_DELIM = "---\n"

# Fixed rendering order; only axes with at least one ADR produce a section.
_AXIS_ORDER = (
    "universal",
    "language",
    "framework",
    "app-shape",
    "ui-tech",
    "library",
    "concern",
    "interaction",
)
_AXIS_DISPLAY_NAMES = {
    "universal": "Universal",
    "language": "Language",
    "framework": "Framework",
    "app-shape": "App shape",
    "ui-tech": "UI tech",
    "library": "Library",
    "concern": "Concern",
    "interaction": "Interaction",
}


class _AdrEntry(NamedTuple):
    """One parsed ADR, ready to render into the grouped index."""

    filename: str
    title: str
    status: str
    axis: str
    topic: str
    related: list[str]
    summary: str


def build_index(adr_dir: StrPath) -> Path:
    """Write ``README.md`` grouping every ``NNNN-*.md`` ADR by axis, ordered.

    Groups follow a fixed axis order (universal, language, framework, app-shape,
    ui-tech, library, concern, interaction); only axes with at least one ADR are
    rendered. Within a group, ADRs stay in filename order. Deterministic: the same
    input directory always produces the same output.
    """
    root = Path(adr_dir)
    entries = [_parse_adr(path) for path in sorted(root.glob("[0-9]*-*.md"))]
    by_topic = {entry.topic: entry for entry in entries}

    lines = [_HEADING, ""]
    for axis in _AXIS_ORDER:
        group = [entry for entry in entries if entry.axis == axis]
        _render_group(lines, _AXIS_DISPLAY_NAMES[axis], group, by_topic)

    # Anything without a recognized axis (e.g. a pre-existing hand-authored ADR
    # with no frontmatter) still appears, so nothing silently vanishes.
    leftover = [entry for entry in entries if entry.axis not in _AXIS_DISPLAY_NAMES]
    _render_group(lines, "Uncategorized", leftover, by_topic)

    index_path = root / "README.md"
    index_path.write_text("\n".join(lines))
    return index_path


def _render_group(
    lines: list[str], heading: str, group: list["_AdrEntry"], by_topic: dict[str, "_AdrEntry"]
) -> None:
    """Append a `## heading` section for *group* to *lines*; no-op if empty."""
    if not group:
        return
    lines.append(f"## {heading}")
    lines.append("")
    for entry in group:
        lines.extend(_render_entry(entry, by_topic))
    lines.append("")


def _render_entry(entry: _AdrEntry, by_topic: dict[str, _AdrEntry]) -> list[str]:
    status = f" — _{entry.status}_" if entry.status else ""
    rendered = [f"- [{entry.title}]({entry.filename}){status}"]
    if entry.summary:
        rendered.append(f"  {entry.summary}")

    related = [by_topic[topic] for topic in entry.related if topic in by_topic]
    if related:
        links = ", ".join(f"[{r.title}]({r.filename})" for r in related)
        rendered.append(f"  Related: {links}")

    return rendered


def _parse_adr(path: Path) -> _AdrEntry:
    text = path.read_text()
    frontmatter, body = _split_frontmatter(text)

    tags = frontmatter.get("tags")
    related = frontmatter.get("related")

    return _AdrEntry(
        filename=path.name,
        title=_title_of(body, path),
        status=str(frontmatter.get("status", "")),
        axis=str(tags[0]) if isinstance(tags, list) and tags else "",
        topic=str(frontmatter.get("topic", topic_of(path))),
        related=[str(t) for t in related] if isinstance(related, list) else [],
        summary=_first_context_sentence(body),
    )


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split *text* into (parsed frontmatter, body). Missing/malformed → ({}, text)."""
    if not text.startswith(_FRONTMATTER_DELIM):
        return {}, text
    try:
        end = text.index("\n---\n", len(_FRONTMATTER_DELIM))
    except ValueError:
        return {}, text

    raw = text[len(_FRONTMATTER_DELIM) : end]
    body = text[end + len("\n---\n") :]
    data = yaml.safe_load(raw)
    return (data if isinstance(data, dict) else {}), body


def _title_of(body: str, adr: Path) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return adr.stem


def _first_context_sentence(body: str) -> str:
    lines = body.splitlines()
    try:
        start = lines.index("## Context")
    except ValueError:
        return ""

    paragraph: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        paragraph.append(stripped)

    text = " ".join(paragraph)
    if not text:
        return ""

    end_of_sentence = text.find(". ")
    if end_of_sentence != -1:
        return text[: end_of_sentence + 1]
    return text
