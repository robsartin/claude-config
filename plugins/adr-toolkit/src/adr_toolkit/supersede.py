"""Supersede an existing ADR: write a new ADR and flip the old one's status pointer.

Immutability is the point: an accepted ADR's Context/Decision/Alternatives/Consequences
prose is a historical record and is never edited. Superseding only ever touches the old
ADR's frontmatter (status + link fields); the body is copied through byte-for-byte.
"""

import re
from pathlib import Path
from typing import Any

import yaml

from adr_toolkit.index import build_index
from adr_toolkit.numbering import existing_adr_names, next_number
from adr_toolkit.planning import topic_of
from adr_toolkit.types import StrPath

_FRONTMATTER_DELIM = "---\n"
_NUMBER_REF = re.compile(r"^\d{4}$")
_SLUG_COLLAPSE = re.compile(r"[^a-z0-9]+")
_STUB_SECTIONS = ("Context", "Decision", "Alternatives considered", "Consequences")


class SupersedeError(ValueError):
    """Base class for all errors raised by the supersede workflow."""


class OldAdrNotFoundError(SupersedeError):
    """*old_ref* did not resolve to exactly one ADR in the target directory."""

    def __init__(self, ref: str) -> None:
        self.ref = ref
        super().__init__(f"no such ADR: {ref!r}")


class EmptyTitleError(SupersedeError):
    """*title* slugifies to an empty string, so no valid ADR filename can be built."""

    def __init__(self, title: str) -> None:
        self.title = title
        super().__init__(f"title slugifies to an empty topic: {title!r}")


class AlreadySupersededError(SupersedeError):
    """The old ADR has already been superseded; refuse to supersede it again."""

    def __init__(self, superseded_by: str) -> None:
        self.superseded_by = superseded_by
        super().__init__(f"old ADR is already {superseded_by!r}")


def slugify(title: str) -> str:
    """Lowercase *title*, collapse non-alphanumeric runs to a single '-', strip edges."""
    return _SLUG_COLLAPSE.sub("-", title.lower()).strip("-")


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split *text* into (parsed frontmatter, body). Missing/malformed -> ({}, text)."""
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


def _topic_of_file(path: Path) -> str:
    frontmatter, _ = _split_frontmatter(path.read_text())
    topic = frontmatter.get("topic")
    return str(topic) if isinstance(topic, str) and topic else topic_of(path)


def _resolve_old_adr(adr_dir: Path, old_ref: str) -> Path:
    candidates = sorted(adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"))
    if _NUMBER_REF.fullmatch(old_ref):
        matches = [p for p in candidates if p.name.startswith(f"{old_ref}-")]
    else:
        matches = [p for p in candidates if _topic_of_file(p) == old_ref]
    if len(matches) != 1:
        raise OldAdrNotFoundError(old_ref)
    return matches[0]


def _render_new_adr(
    number: int, title: str, date: str, new_topic: str, tags: list[str], old_topic: str
) -> str:
    frontmatter = "\n".join(
        [
            "---",
            "status: Accepted",
            f'date: "{date}"',
            f"topic: {new_topic}",
            f"tags: [{', '.join(tags)}]",
            f"supersedes: [{old_topic}]",
            f"related: [{old_topic}]",
            "---",
        ]
    )
    sections = "\n\n".join(f"## {name}\n\n_TODO: fill in._" for name in _STUB_SECTIONS)
    return f"{frontmatter}\n# {number}. {title}\n\n{sections}\n"


def _render_old_frontmatter(
    data: dict[str, Any], new_number: int, new_topic: str, old_topic: str
) -> str:
    status = f"Superseded by {new_number:04d}"
    date = data.get("date", "")
    tags = [str(t) for t in (data.get("tags") or [])]
    supersedes = [str(t) for t in (data.get("supersedes") or [])]

    superseded_by = [str(t) for t in (data.get("superseded-by") or [])]
    if new_topic not in superseded_by:
        superseded_by.append(new_topic)

    related = [str(t) for t in (data.get("related") or [])]
    if new_topic not in related:
        related.append(new_topic)

    lines = [
        "---",
        f'status: "{status}"',
        f'date: "{date}"',
        f"topic: {old_topic}",
        f"tags: [{', '.join(tags)}]",
        f"supersedes: [{', '.join(supersedes)}]",
        f"superseded-by: [{', '.join(superseded_by)}]",
        f"related: [{', '.join(related)}]",
        "---",
    ]
    return "\n".join(lines) + "\n"


def supersede(adr_dir: StrPath, old_ref: str, title: str, date: str) -> tuple[Path, Path]:
    """Write a new ADR that supersedes *old_ref*, and flip the old ADR's status pointer.

    *old_ref* resolves against *adr_dir* either as a 4-digit number prefix ("0005"
    matches "0005-*.md") or as a topic slug; raises OldAdrNotFoundError if that does
    not resolve to exactly one file. The old ADR's body (heading + `##` sections) is
    copied through unchanged -- only its frontmatter block is rewritten. Rebuilds the
    README index before returning. Returns (new_adr_path, old_adr_path).
    """
    directory = Path(adr_dir)
    old_path = _resolve_old_adr(directory, old_ref)
    old_frontmatter, old_body = _split_frontmatter(old_path.read_text())
    old_status = str(old_frontmatter.get("status") or "")
    if old_status.startswith("Superseded by "):
        raise AlreadySupersededError(old_status)
    old_topic = str(old_frontmatter.get("topic") or topic_of(old_path))
    tags = [str(t) for t in (old_frontmatter.get("tags") or [])]

    new_topic = slugify(title)
    if not new_topic:
        raise EmptyTitleError(title)

    new_number = next_number(existing_adr_names(directory))
    new_path = directory / f"{new_number:04d}-{new_topic}.md"
    new_path.write_text(_render_new_adr(new_number, title, date, new_topic, tags, old_topic))

    updated_old = (
        _render_old_frontmatter(old_frontmatter, new_number, new_topic, old_topic) + old_body
    )
    old_path.write_text(updated_old)

    build_index(directory)

    return new_path, old_path
