#!/usr/bin/env python3
"""front-page.html must exist, wire header/footer, and reference at least one theme pattern."""
import pathlib, re, sys
root = pathlib.Path(__file__).resolve().parents[1]
f = root / "templates" / "front-page.html"
errors = []
if not f.exists():
    errors.append("templates/front-page.html missing")
else:
    html = f.read_text()
    for needle in ('"slug":"header"', '"slug":"footer"'):
        if needle not in html:
            errors.append(f"front-page.html: missing {needle}")
    if not re.search(r'"slug":"[a-z0-9-]+/', html):
        errors.append("front-page.html: references no theme pattern (expected wp:pattern with a namespaced slug)")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("OK: front-page wires header/footer and a theme pattern")
