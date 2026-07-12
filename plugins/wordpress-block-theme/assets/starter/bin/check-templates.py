#!/usr/bin/env python3
"""Check that all templates are present and properly wired."""
import pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
templates_dir = root / "templates"
expected = {"index", "home", "single", "page", "archive", "search", "404", "front-page"}
errors = []
for name in expected:
    f = templates_dir / f"{name}.html"
    if not f.exists():
        errors.append(f"templates/{name}.html missing")
    else:
        html = f.read_text()
        for needle in ('"slug":"header"', '"slug":"footer"', '"tagName":"main"'):
            if needle not in html:
                errors.append(f"{name}.html: missing {needle}")
for part in ["header", "footer"]:
    if not (root / "parts" / f"{part}.html").exists():
        errors.append(f"parts/{part}.html missing")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(expected)} templates + header/footer present and wired")
