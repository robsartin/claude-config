#!/usr/bin/env python3
"""Every font family must have a fallback stack; any self-hosted fontFace must reference an existing file."""
import json, pathlib, sys

root = pathlib.Path(__file__).resolve().parents[1]
data = json.loads((root / "theme.json").read_text())
families = data["settings"]["typography"]["fontFamilies"]
errors = []
for fam in families:
    slug = fam.get("slug", "?")
    stack = fam.get("fontFamily", "")
    if stack.count(",") < 1:
        errors.append(f"'{slug}': fontFamily has no fallback (needs a comma-separated stack)")
    if "sans-serif" not in stack and "serif" not in stack and "monospace" not in stack:
        errors.append(f"'{slug}': fontFamily has no generic family (sans-serif/serif/monospace) at the end")
    for face in fam.get("fontFace", []):
        for src in face.get("src", []):
            rel = src.replace("file:./", "")
            if not (root / rel).exists():
                errors.append(f"'{slug}': fontFace src missing on disk: {rel}")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(families)} font families have fallback stacks; all fontFace files present")
