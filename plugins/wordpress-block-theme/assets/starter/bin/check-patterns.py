#!/usr/bin/env python3
"""Every patterns/*.php must declare Title/Slug/Categories headers and contain block markup."""
import pathlib, re, sys
root = pathlib.Path(__file__).resolve().parents[1]
pattern_dir = root / "patterns"
files = sorted(pattern_dir.glob("*.php")) if pattern_dir.exists() else []
errors = []
if not files:
    errors.append("patterns/ has no .php files")
for f in files:
    text = f.read_text()
    for header in ("Title:", "Slug:", "Categories:"):
        if header not in text:
            errors.append(f"{f.name}: missing '{header}' header")
    if not re.search(r'Slug:\s*[a-z0-9-]+/[a-z0-9-]+', text):
        errors.append(f"{f.name}: Slug must be namespaced (e.g. 'starter/{f.stem}')")
    if "wp:" not in text:
        errors.append(f"{f.name}: no block markup")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(files)} pattern(s) valid")
