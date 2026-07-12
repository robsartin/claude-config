#!/usr/bin/env python3
"""Every core/group that declares style.spacing.padding/margin must carry a
matching inline style="..." on its wrapper div — a bare div with declared
spacing parses as valid block markup but silently drops that spacing at
render time (see references/block-markup-rules.md, rule 1)."""
import json
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parents[1]

SIDES = ("top", "right", "bottom", "left")

GROUP_COMMENT_RE = re.compile(r'<!--\s*wp:group\s+(\{.*?\})\s*(?:/)?-->', re.DOTALL)
DIV_RE = re.compile(r'<div class="wp-block-group[^"]*"(?:\s+style="([^"]*)")?')


def declared_sides(spacing, prop):
    """Return list of (side, value) for a spacing prop (padding/margin), where
    a single non-dict value applies to all four sides."""
    value = spacing.get(prop)
    if value is None:
        return []
    if isinstance(value, dict):
        return [(side, value[side]) for side in SIDES if side in value]
    return [(side, value) for side in SIDES]


def find_groups(text):
    """Yield (attrs_json_str, attrs_dict) for every wp:group block comment."""
    for m in GROUP_COMMENT_RE.finditer(text):
        raw = m.group(1)
        try:
            attrs = json.loads(raw)
        except ValueError:
            continue
        yield m, raw, attrs


def check_file(path):
    text = path.read_text()
    errors = []
    checked = 0
    for m, raw, attrs in find_groups(text):
        style = attrs.get("style", {})
        spacing = style.get("spacing", {})
        needed = []
        for prop in ("padding", "margin"):
            for side, _value in declared_sides(spacing, prop):
                needed.append(f"{prop}-{side}")
        if not needed:
            continue  # legitimately bare: no spacing declared
        checked += 1
        # Find the group's opening div, searched after the block comment.
        div_match = DIV_RE.search(text, m.end())
        if not div_match:
            errors.append(
                f"{path.name}: group `{raw}` declares spacing but no "
                "wp-block-group div found"
            )
            continue
        inline_style = div_match.group(1) or ""
        missing = [prop for prop in needed if f"{prop}:" not in inline_style]
        if missing:
            errors.append(
                f"{path.name}: group `{raw}` declares "
                f"{', '.join(needed)} but its div's inline style "
                f"(\"{inline_style}\") is missing {', '.join(missing)}"
            )
    return checked, errors


def main():
    globs = [
        (root / "patterns").glob("*.php"),
        (root / "templates").glob("*.html"),
        (root / "parts").glob("*.html"),
    ]
    files = sorted({f for g in globs for f in g})
    errors = []
    total_checked = 0
    for f in files:
        checked, file_errors = check_file(f)
        total_checked += checked
        errors.extend(file_errors)
    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"OK: {total_checked} group(s) consistent")


if __name__ == "__main__":
    main()
