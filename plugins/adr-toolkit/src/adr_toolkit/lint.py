"""ADR content linter: one reusable validator for frontmatter, section, and token rules.

Consolidates what used to be three ad-hoc test files (frontmatter, section-order, and
related-link checks) into a single validator, usable both from the test suite and as a
CI gate via scripts/lint_adrs.py.
"""

import re
from pathlib import Path
from typing import Any

import yaml

from adr_toolkit.planning import topic_of
from adr_toolkit.types import Manifest, StrPath

REQUIRED_FRONTMATTER = ("status", "date", "topic", "tags", "supersedes", "related")
SECTIONS = ("## Context", "## Decision", "## Alternatives considered", "## Consequences")
ALLOWED_TOKENS = frozenset({"project", "package", "date", "number"})

_FRONTMATTER_DELIM = "---\n"
_TOKEN_RE = re.compile(r"\{\{(\w*)\}\}")


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    """Split *text* into (raw frontmatter, body) at the first two ``---`` delimiters.

    Returns None when the delimiters are absent or unterminated, so callers can report
    a single clear violation instead of raising.
    """
    if not text.startswith(_FRONTMATTER_DELIM):
        return None
    try:
        end = text.index("\n---\n", len(_FRONTMATTER_DELIM))
    except ValueError:
        return None
    return text[len(_FRONTMATTER_DELIM) : end], text[end + len("\n---\n") :]


def _lint_frontmatter(path: Path, data: Any, topics: set[str], axis: str) -> list[str]:
    violations: list[str] = []
    if not isinstance(data, dict):
        return [f"{path}: frontmatter did not parse to a mapping"]

    missing = [key for key in REQUIRED_FRONTMATTER if key not in data]
    if missing:
        # Further checks assume the keys exist; bail out rather than KeyError.
        return [f"{path}: frontmatter missing keys {missing}"]

    if data["status"] != "Accepted":
        violations.append(f"{path}: status must be 'Accepted', got {data['status']!r}")
    if data["date"] != "{{date}}":
        violations.append(f"{path}: date must be the literal '{{{{date}}}}' token")
    if data["supersedes"] != []:
        violations.append(f"{path}: supersedes must be an empty list")

    expected_topic = topic_of(path)
    if data["topic"] != expected_topic:
        violations.append(f"{path}: topic {data['topic']!r} != expected {expected_topic!r}")

    tags = data["tags"]
    if not isinstance(tags, list) or not tags:
        violations.append(f"{path}: tags must be a non-empty list, got {tags!r}")
    elif tags[0] != axis:
        violations.append(f"{path}: tags {tags!r} must start with the axis {axis!r}")

    related = data["related"]
    if not isinstance(related, list):
        violations.append(f"{path}: related must be a list, got {related!r}")
    else:
        unknown = [entry for entry in related if entry not in topics]
        if unknown:
            violations.append(f"{path}: related entries {unknown!r} are not known topics")
        if expected_topic in related:
            violations.append(f"{path}: related must not self-reference {expected_topic!r}")
        if len(related) != len(set(related)):
            violations.append(f"{path}: related has duplicate entries")

    return violations


def _lint_sections(path: Path, body: str) -> list[str]:
    violations: list[str] = []
    lines = body.splitlines()
    positions = {
        section: next((i for i, ln in enumerate(lines) if ln == section), -1)
        for section in SECTIONS
    }

    missing = [section for section in SECTIONS if positions[section] < 0]
    if missing:
        violations.append(f"{path}: missing section(s) {missing}")

    found_order = [positions[section] for section in SECTIONS if positions[section] >= 0]
    if found_order != sorted(found_order):
        violations.append(f"{path}: sections out of order {list(positions.values())}")

    alt_pos = positions[SECTIONS[2]]
    if alt_pos >= 0:
        cons_pos = positions[SECTIONS[3]]
        end = cons_pos if cons_pos >= 0 else len(lines)
        alt_body = "\n".join(lines[alt_pos + 1 : end]).strip()
        if not alt_body:
            violations.append(f"{path}: empty Alternatives considered section")

    if "- **Date:**" in body:
        violations.append(f"{path}: leftover Date bullet in body")
    if "- **Status:**" in body:
        violations.append(f"{path}: leftover Status bullet in body")

    return violations


def _lint_tokens(path: Path, text: str) -> list[str]:
    bad_tokens = sorted({name for name in _TOKEN_RE.findall(text) if name not in ALLOWED_TOKENS})
    if bad_tokens:
        return [f"{path}: disallowed template token(s) {bad_tokens}"]
    return []


def lint_packs(packs_dir: StrPath, manifest: Manifest) -> list[str]:
    """Validate every ``*.md`` under *packs_dir* against the ADR content invariants.

    Returns a list of human-readable violation strings (empty when clean).
    """
    packs_root = Path(packs_dir)
    templates = sorted(packs_root.glob("**/*.md"))

    all_topics = {topic_of(path) for path in templates}

    axis_by_topic: dict[str, str] = {}
    for spec in manifest["packs"].values():
        for template in (packs_root / spec["path"]).glob("**/*.md"):
            axis_by_topic[topic_of(template)] = spec["axis"]

    violations: list[str] = []
    for path in templates:
        text = path.read_text()
        split = _split_frontmatter(text)
        if split is None:
            violations.append(f"{path}: missing or unterminated frontmatter delimiter")
            continue
        raw_frontmatter, body = split
        data = yaml.safe_load(raw_frontmatter)
        axis = axis_by_topic.get(topic_of(path), "")

        violations.extend(_lint_frontmatter(path, data, all_topics, axis))
        violations.extend(_lint_sections(path, body))
        violations.extend(_lint_tokens(path, text))

    return violations
