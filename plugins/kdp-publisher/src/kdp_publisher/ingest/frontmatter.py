"""Parse front-matter settings from document first-page labels."""

from kdp_publisher import kdp_rules as r

REQUIRED = ("title", "author", "trim", "paper_type")

_LABELS = {
    "title": "title",
    "subtitle": "subtitle",
    "author": "author",
    "trim": "trim",
    "paper": "paper_type",
    "copyright": "copyright",
}
_PAPER_ALIASES = {
    "cream": "cream-bw",
    "cream-bw": "cream-bw",
    "white": "white-bw",
    "white-bw": "white-bw",
    "color": "standard-color",
    "standard-color": "standard-color",
    "premium": "premium-color",
    "premium-color": "premium-color",
}


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    """Parse labeled lines into settings dict and missing required fields.

    Args:
        lines: List of "Label: value" strings from document first page.

    Returns:
        (fields, missing): fields dict (subset of title/subtitle/author/trim/
            paper_type/copyright) and missing list of required keys not present
            or invalid (subset of title/author/trim/paper_type).
    """
    fields: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        key = _LABELS.get(label.strip().lower())
        value = value.strip()
        if not key or not value:
            continue
        if key == "trim":
            if value.lower() in r.TRIMS_IN:
                fields[key] = value.lower()
        elif key == "paper_type":
            alias = _PAPER_ALIASES.get(value.lower())
            if alias:
                fields[key] = alias
        else:
            fields[key] = value
    missing = [k for k in REQUIRED if k not in fields]
    return fields, missing
